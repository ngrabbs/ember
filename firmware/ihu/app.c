#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>
#include "pico/stdlib.h"
#include "pico/stdio_usb.h"
#include "pico/unique_id.h"
#include "pico/rand.h"
#include "services.h"
#include "app.h"
#include "wire.h"
#include "lte_link.h"
#include "uhf_client.h"
#include "device_registry.h"
#include "build_identity.h"
#include "firmware_info.h"
#include "payload_protocol.h"
static uc_state uhf_client;
#include "native_telemetry.h"
#include "mode_policy.h"
#ifndef IHU_FLIGHT_CONFIGURATION
#define IHU_FLIGHT_CONFIGURATION 0
#endif
static ip_state policy;
static bool console_reply;
enum { IHU_FAULT_CAPACITY = 16 };
static struct {uint32_t at;uint8_t code;} faults[IHU_FAULT_CAPACITY];
static unsigned fault_count;
static void record_fault(uint8_t code,uint32_t at){unsigned i=fault_count++%IHU_FAULT_CAPACITY;faults[i].at=at;faults[i].code=code;}

#include "uplink_ping.h"
#include "../shared/ember_protocol/protocol.h"
static ember_state uplink_engine;
static cf_reader uplink_fragments;
static struct {bool active,gps_waiting,gps_reading;ul_packet request;uint8_t target;uint32_t peer,gps_since;} fire_uplink;
#define FIRE_TRANSACTION_CAPACITY 256
static struct {uint32_t epoch,id;} fire_keys[FIRE_TRANSACTION_CAPACITY];
static unsigned fire_keys_used;
static void submit(uint8_t type,const uint8_t *payload,size_t size);
static bool (*link_reply_sink)(const uint8_t *,size_t);
static void fire_restore(void);

#include "power_packet.h"
#include "health_packet.h"
#include "device_packet.h"
#include "uhf_run.h"
static dr_status devices[DR_COUNT];
static struct {bool valid;uint32_t observed;uint8_t payload[FI_SIZE];} identities[2];
static struct {bool active;uint8_t index,next;uint16_t nonce;uint32_t sent,last;} discovery;
static ur_state uhf_run;
static uint32_t uhf_last_result;
static uint32_t uhf_console_requests[UC_CAPACITY];
static void log_output(const char *fmt,...){
    if(!stdio_usb_connected())return;
    va_list args;
    if(console_reply){va_start(args,fmt);ihu_vprintf(console_reply,fmt,args);va_end(args);return;}
    if(ip_enabled(&policy,IP_CLI_DEBUG)){ihu_printf(false,"CLI_DEBUG ");va_start(args,fmt);ihu_vprintf(console_reply,fmt,args);va_end(args);}
    if(ip_enabled(&policy,IP_UMB_DEBUG)){ihu_printf(false,"UMB_DEBUG ");va_start(args,fmt);ihu_vprintf(console_reply,fmt,args);va_end(args);}
}
#define LOG(...) log_output(__VA_ARGS__)
#define ROLE_NAME "IHU_MCU"
static uint8_t target_index=DR_COMMS_INDEX;
#define target_lte (target_index==DR_LTE_INDEX)
#define target_payload (target_index==DR_PAYLOAD_INDEX)
#define TX_ID (dr_devices[target_index].request_id)
#define RX_ID (dr_devices[target_index].reply_id)
static uint32_t request_timeout_ms(uint8_t type){
    if(type==PL_FIRE_CHECK)return 12000;
    if(type==CF_SEND_PACKET)return 22000;
    return 5000;
}
static mcp_state can;
static cf_reader fragments;
static ul_reader can_reader;
static uint32_t boot,peer,request_id,matched,unknown,busy_drops;
static uint32_t admitted_requests,refused_requests;
static bool loopback_test;
static struct {bool active,console;ul_packet packet;uint32_t started;} pending;
static struct {
    bool active;
    uint8_t wire[UL_WIRE_MAX];size_t size;
    uint16_t token,route;unsigned index;uint32_t last;
} output;
enum {SENSOR_HEALTH, SENSOR_JSON, SENSOR_ADC, SENSOR_TELEMETRY, SENSOR_GPS, SENSOR_GPS_TELEMETRY, SENSOR_FIRE_GPS};
static struct {bool active,console,from_run;unsigned kind,route;uint32_t generation;uint32_t run;} sensor_job;
static uint32_t output_generation[IP_OUTPUT_COUNT],run_generation;
static bool request_sensor(unsigned kind,unsigned route,bool enable);
static void sensor_complete(const ihu_sensor_result *r);
static uint16_t telemetry_sequence;
static uint32_t eps_readout_count,boot_ready_ms;
static size_t status_packet(uint8_t *b,const uint8_t *request);
static void cdh_receive(const ul_packet *request);
static void cdh_pump(uint32_t now);
static uint32_t now_ms(void) {return to_ms_since_boot(get_absolute_time());}
static void firmware_status(void) {
    LOG("FIRMWARE role=%s version=%s git=%s dirty=%u boot=%" PRIu32 "\n",ROLE_NAME,FW_VERSION,FW_GIT,FW_DIRTY,boot);
}
static void mode_status(void);
static void outputs_status(void);
static void status(void) {
    firmware_status();
    mode_status();outputs_status();
    LOG("CAN_TARGET name=%s request=%03x reply=%03x\n",dr_devices[target_index].name,TX_ID,RX_ID);
    char id[2*PICO_UNIQUE_BOARD_ID_SIZE_BYTES+1];pico_get_unique_board_id_string(id,sizeof(id));
    LOG("STATUS role=%s fw=%s id=%s boot=%" PRIu32 " peer=%" PRIu32
        " can_ready=%d mode=%02x cnf=%02x,%02x,%02x bitrate=500000 tec=%u rec=%u eflg=%02x"
        " tx_ok=%" PRIu32 " tx_fail=%" PRIu32 " tx_timeout=%" PRIu32 " rx=%" PRIu32
        " rx_bad=%" PRIu32 " rx_overflow=%" PRIu32 " fragments_bad=%" PRIu32 " fragments_timeout=%" PRIu32
        " matched=%" PRIu32 " unknown=%" PRIu32 " busy_drops=%" PRIu32 " pending=%d uptime_ms=%" PRIu32,
        ROLE_NAME,FW_VERSION,id,boot,peer,can.ready,ihu_can_register(0x0e)&0xe0,ihu_can_register(0x2a),ihu_can_register(0x29),ihu_can_register(0x28),
        ihu_can_register(0x1c),ihu_can_register(0x1d),ihu_can_register(0x2d),can.tx_ok,can.tx_fail,can.tx_timeout,can.rx,
        can.rx_bad,can.rx_overflow,fragments.errors,fragments.timeouts,matched,unknown,busy_drops,pending.active,now_ms());
    LOG(" uhf_pending=%u",uc_count(&uhf_client));
    LOG(" uhf_mode=%u cycles=%" PRIu32 " submitted=%" PRIu32,uhf_run.state,uhf_run.cycles,uhf_run.submitted);
    LOG("\n");
}
static bool queue(const ul_packet *p) {
    if(output.active)return false;
    size_t size=ul_encode(p,output.wire);if(!size)return false;
    output.route=TX_ID;output.size=size;output.token=(uint16_t)p->request;output.index=0;output.last=now_ms()-2;output.active=true;return true;
}
static bool uplink_queue(const ul_packet *reply) {
    if(link_reply_sink)return link_reply_sink(reply->payload,reply->size);
    if(!queue(reply))return false;
    output.route=UP_REPLY_ID;
    return true;
}
static void fire_restore(void){target_index=fire_uplink.target;peer=fire_uplink.peer;fire_uplink.active=false;fire_uplink.gps_waiting=false;fire_uplink.gps_reading=false;}
static void fire_unavailable(uint8_t payload_reason){
    if(!fire_uplink.active)return;
    ul_packet reply={.version=1,.type=UP_RESULT,.sender=boot,
        .origin=fire_uplink.request.sender,.request=fire_uplink.request.request,.size=43};
    uint8_t *b=reply.payload;memset(b,0,43);
    ul_p16(b,W_TM_IDENTITY);ul_p16(b+2,0xc000|(telemetry_sequence++&0x3fff));ul_p16(b+4,36);
    b[6]=1;b[7]=2;ul_p16(b+8,W_ID_COMMAND_RESPONSE);b[10]=2;b[11]=1;
    memcpy(b+12,fire_uplink.request.payload+12,8);ul_p32(b+20,boot);ul_p32(b+24,now_ms());ul_p16(b+28,11);
    ul_p16(b+30,W_ID_PAYLOAD_FIRE_CHECK);b[32]=W_STAGE_EXECUTION_FAILED;
    ul_p16(b+33,W_REASON_NOT_AVAILABLE);ul_p32(b+37,payload_reason);ul_p16(b+41,ul_crc(b,41));
    (void)uplink_queue(&reply);
    fire_restore();
}
static bool uplink_emit(const uint8_t *p,size_t n,void *context){
    const ul_packet *request=context;
    if(up_native_status(request->payload,request->size) || (up_native_cdh(request->payload,request->size) && ul_u16(request->payload+8)==3)){
        if(p[W_KIND]!=W_KINDS_TELEMETRY || ul_u16(p+W_MESSAGE_ID)!=W_ID_SYSTEM_STATUS)return true;
        ul_packet reply={.version=1,.type=UP_RESULT,.sender=boot,.origin=request->sender,.request=request->request};
        reply.size=(uint16_t)status_packet(reply.payload,request->payload);
        return uplink_queue(&reply);
    }
    if(n!=43 || p[W_KIND]!=W_KINDS_RESPONSE)return false;
    if(p[W_PAYLOAD+W_COMMAND_RESPONSE_STAGE]!=W_STAGE_COMPLETED)return true;
    ul_packet reply={.version=1,.type=UP_RESULT,.sender=boot,
                     .origin=request->sender,.request=request->request,.size=(uint16_t)n};
    memcpy(reply.payload,p,n);
    if(!uplink_queue(&reply))return false;
    LOG("UPLINK_PING COMPLETED epoch=%" PRIu32 " transaction=%" PRIu32 " response_hex=",
        ul_u32(p+12),ul_u32(p+16));
    for(size_t i=0;i<n;i++){LOG("%02x",p[i]);}LOG("\n");return true;
}
static void uplink_start_fire(const ul_packet *p){
    uint32_t epoch=ul_u32(p->payload+12),id=ul_u32(p->payload+16);
    for(unsigned i=0;i<fire_keys_used;i++)if(fire_keys[i].epoch==epoch && fire_keys[i].id==id)return;
    if(fire_keys_used==FIRE_TRANSACTION_CAPACITY)return;
    fire_keys[fire_keys_used].epoch=epoch;fire_keys[fire_keys_used++].id=id;
    /* Addressed commands take precedence over an observational probe. */
    discovery.active=false;
    LOG("UPLINK_FIRE admitted epoch=%" PRIu32 " transaction=%" PRIu32 "\n",epoch,id);
    fire_uplink.active=true;fire_uplink.request=*p;fire_uplink.target=target_index;fire_uplink.peer=peer;
    target_index=DR_PAYLOAD_INDEX;peer=0;memset(&fragments,0,sizeof(fragments));
    submit(UL_HELLO,NULL,0);
}
static void uplink_receive(const cf_frame *frame,uint32_t now){
    static ul_packet p;
    if(!cf_feed(&uplink_fragments,frame,UP_REQUEST_ID,now))return;
    if(!up_envelope(&uplink_fragments,&p)||p.type!=UP_PING||p.origin!=p.sender||(!up_native_ping(p.payload,p.size)&&!up_native_fire(p.payload,p.size)&&!up_native_status(p.payload,p.size)&&!up_native_cdh(p.payload,p.size)))return;
    if(!ip_test(&policy))return;
    if((sensor_job.active && !up_native_status(p.payload,p.size) && !up_native_cdh(p.payload,p.size)) || output.active||(can.pending&&!discovery.active)){LOG("UPLINK_PING rejected=BUSY\n");return;}
    if(up_native_fire(p.payload,p.size)){
        if(fire_uplink.active || pending.active || uc_count(&uhf_client) || uhf_run.state==UR_RUNNING){LOG("UPLINK_FIRE rejected=BUSY\n");return;}
        uplink_start_fire(&p);return;
    }
    if(fire_uplink.active)return;
    if(up_native_cdh(p.payload,p.size)){cdh_receive(&p);return;}
    ember_command(&uplink_engine,p.payload,p.size,now,uplink_emit,&p);
}
static void pump_tx(uint32_t now) {
    static uint32_t observed_errors;ihu_can_poll_tx(&can,now);
    uint32_t errors=can.tx_fail+can.tx_timeout;
    if(errors!=observed_errors) {
        observed_errors=errors;record_fault(W_IHU_FAULT_CODE_CAN_TX_ERROR,now);
        output.active=false;LOG("CAN_TX outcome=UNKNOWN reason=FRAME_TX_FAILED\n");
        // Pending application request times out; a CAN hardware outcome is not an app result.
        return;
    }
    if(output.active && !can.pending && (uint32_t)(now-output.last)>=2) {
        cf_frame frame;
        if(!cf_fragment(output.wire,output.size,output.route,output.token,output.index,&frame)) {output.active=false;return;}
        if(ihu_can_send(&can,&frame)) {
            ++output.index;output.last=now;
            if((size_t)output.index*CF_CHUNK>=output.size)output.active=false;
        }
    }
}
static bool envelope_from_fragments(uint32_t now,ul_packet *p) {
    bool found=false;
    // New envelope starts with a fresh bounded parser, independent of CAN pacing.
    memset(&can_reader,0,sizeof(can_reader));
    for(size_t i=0;i<fragments.used;++i)if(ul_feed(&can_reader,fragments.wire[i],now,p))found=true;
    return found;
}
static void send_error(const ul_packet *p,uint8_t reason) {
    ul_packet out={0};out.version=1;out.type=UL_ERROR;out.sender=boot;out.origin=p->origin;out.request=p->request;
    out.size=1;out.payload[0]=reason;if(!queue(&out))++busy_drops;
}
static void receive_impl(const ul_packet *p) {
    if(p->type==CF_UHF_ADMITTED || p->type==CF_UHF_RESULT || p->type==CF_UHF_REJECTED) {
        if(!uc_receive(&uhf_client,p))return;
        dr_seen(&devices[DR_COMMS_INDEX],now_ms(),p->sender);
        if(p->type!=CF_UHF_ADMITTED)uhf_last_result=now_ms();
        if(p->payload[1]!=UHF_OK && uhf_run.state==UR_RUNNING) {
            ur_stop(&uhf_run,UR_FAULT);LOG("UHF_RUN FAULT remote_status=%u\n",p->payload[1]);
        }
        if(pending.active && uhf_is_request(pending.packet.type) && pending.packet.request==p->request)pending.active=false;
        ++matched;
        LOG("UHF request=%" PRIu32 " outcome=%s status=%u bytes=%u digest=%08" PRIx32 " ground_ack=0 outstanding=%u\n",
            p->request,p->type==CF_UHF_ADMITTED?"QUEUED":p->type==CF_UHF_REJECTED?"REJECTED":
            p->payload[1]==UHF_OK?"RF_TX_COMPLETE":p->payload[1]==UHF_CANCELLED?"CANCELLED":"RF_TX_FAILED",
            p->payload[1],ul_u16(p->payload+2),ul_u32(p->payload+4),uc_count(&uhf_client));
        return;
    }
    if(pending.active && p->origin==boot && p->request==pending.packet.request) {
        bool hello=pending.packet.type==UL_HELLO;
        uint8_t expected=hello?UL_HELLO_ACK:pending.packet.type==CF_CHAIN?CF_CHAIN_ACK:
            pending.packet.type==CF_RF_WINDOW?CF_RF_WINDOW_ACK:pending.packet.type==CF_SEND_PACKET?CF_MODEM_ACCEPTED:pending.packet.type==CF_LINK_STATUS?CF_LINK_STATUS_ACK:pending.packet.type==CF_LINK_DIAG?CF_LINK_DIAG_ACK:pending.packet.type==UL_FIRMWARE_INFO?UL_FIRMWARE_INFO_ACK:pending.packet.type==CF_MODEM_FIRMWARE?CF_MODEM_FIRMWARE_ACK:pending.packet.type==PL_STATUS?PL_STATUS_ACK:pending.packet.type==PL_HEARTBEAT?PL_HEARTBEAT_ACK:pending.packet.type==PL_FIRE_CHECK?PL_FIRE_RESULT:UL_ECHO_ACK;
        if(p->version!=1 || (!hello && p->sender!=peer)) {

            pending.active=false;peer=0;++unknown;LOG("RESULT outcome=UNKNOWN reason=PEER_RESET_OR_VERSION\n");return;
        }
        if(p->type==UL_ERROR && p->size==1) {

            pending.active=false;
            if(fire_uplink.active && pending.packet.type==PL_FIRE_CHECK &&
               pending.packet.size==PL_GPS_SIZE && p->payload[0]==4){
                /* Older payloads reject the extension before starting capture. */
                submit(PL_FIRE_CHECK,NULL,0);
                return;
            }
            bool uncertain=p->payload[0]==CF_LINK_UNKNOWN || p->payload[0]==UL_ERR_MODEM_UNKNOWN;
            if(uncertain) {++unknown;peer=0;}
            else ++refused_requests;
            LOG("RESULT request=%" PRIu32 " outcome=%s reason=%u\n",p->request,uncertain?"UNKNOWN_REMOTE_LINK":"PEER_REJECTED",p->payload[0]);
            if(!uncertain)fire_unavailable(p->payload[0]);
            return;
        }
        bool identity=pending.packet.type==UL_FIRMWARE_INFO || pending.packet.type==CF_MODEM_FIRMWARE;
        bool diag=pending.packet.type==CF_LINK_DIAG;
        bool health=pending.packet.type==CF_LINK_STATUS || diag;
        bool fire=pending.packet.type==PL_FIRE_CHECK;
        bool payload_report=pending.packet.type==PL_STATUS || pending.packet.type==PL_HEARTBEAT;
        bool tagged=fire && pending.packet.size==PL_GPS_SIZE && p->size==PL_GPS_TAGGED_SIZE;
        if(p->type!=expected || p->size!=(identity?FI_SIZE:fire?(tagged?PL_GPS_TAGGED_SIZE:PL_FIRE_SIZE):payload_report?PL_REPORT_SIZE:health?(diag?LTE_DIAG_SIZE:16):pending.packet.size) || (!health && !identity && !payload_report && !fire && memcmp(p->payload,pending.packet.payload,p->size)) || (identity && (!fi_valid(p->payload,p->size) || (pending.packet.type==UL_FIRMWARE_INFO && ul_u32(p->payload+24)!=p->sender))))return;
        if(fire){
            uint8_t base[PL_FIRE_SIZE];
            memcpy(base,p->payload,sizeof(base));
            if(tagged){
                if(p->payload[PL_FIRE_SIZE]>PL_GPS_STALE ||
                   (base[3] && (base[3]!=11 || base[1]!=2)))return;
                base[3]=0;
            }
            if(!pl_fire_valid(base,sizeof(base),p->sender))return;
        }
        if(payload_report && !pl_report_valid(p->payload,p->size,p->sender))return;
        if(payload_report)LOG("PAYLOAD_REPORT boot=%" PRIu32 " uptime_ms=%" PRIu32 " requests=%" PRIu32 " replies=%" PRIu32 " rejected=%" PRIu32 " fragment_errors=%" PRIu32 "\n",ul_u32(p->payload+4),ul_u32(p->payload+8),ul_u32(p->payload+12),ul_u32(p->payload+16),ul_u32(p->payload+20),ul_u32(p->payload+24));
        if(health)LOG("LTE_STATUS state=%u step=%u error=%u registered=%u window_ms=%" PRIu32 " modem_accepted=%" PRIu32 " rejected=%" PRIu32 "\n",p->payload[0],p->payload[1],p->payload[2],p->payload[3],ul_u32(p->payload+4),ul_u32(p->payload+8),ul_u32(p->payload+12));
        if(diag)LOG("LTE_DIAG version=%u last_cereg=%u send_cereg=%u failure_cereg=%u command=%u failure_command=%u failure_state=%u flags=%u cme=%" PRIu32 " send_elapsed_ms=%" PRIu32 " registration_losses=%" PRIu32 " last_cereg_ms=%" PRIu32 " uart_send_request=%" PRIu32 " error_kind=%u\n",
            p->payload[16],p->payload[17],p->payload[18],p->payload[19],p->payload[20],p->payload[21],p->payload[22],p->payload[23],ul_u32(p->payload+24),ul_u32(p->payload+28),ul_u32(p->payload+32),ul_u32(p->payload+36),ul_u32(p->payload+40),p->payload[45]);
        if(identity) {
            LOG("FIRMWARE_REPLY peer=%" PRIu32 " version=%u.%u.%u dirty=%u\n",p->sender,p->payload[0],p->payload[1],p->payload[2],p->payload[3]);
        }
        if(identity && target_lte) {
            unsigned index=pending.packet.type==CF_MODEM_FIRMWARE;
            identities[index].valid=true;identities[index].observed=now_ms();
            memcpy(identities[index].payload,p->payload,FI_SIZE);
            LOG("DEVICE_FIRMWARE component=%s version=%u.%u.%u dirty=%u boot=%" PRIu32 " git=",index?"WALTER":"LTE_CAN",p->payload[0],p->payload[1],p->payload[2],p->payload[3],ul_u32(p->payload+24));
            for(unsigned i=4;i<24;i++)LOG("%02x",p->payload[i]);
            LOG("\n");
        }
        if(hello)peer=p->sender;
        dr_seen(&devices[target_index],now_ms(),p->sender);

        pending.active=false;++matched;
        LOG("RESULT request=%" PRIu32 " outcome=%s peer=%" PRIu32 " bytes=%u hex=",p->request,
            hello?"CAN_HELLO_CONFIRMED":fire?"PAYLOAD_FIRE_RESULT":payload_report?(p->type==PL_STATUS_ACK?"PAYLOAD_STATUS":"PAYLOAD_HEARTBEAT"):identity?"FIRMWARE_IDENTITY":p->type==CF_RF_WINDOW_ACK?"RF_WINDOW_ACCEPTED":
            p->type==CF_MODEM_ACCEPTED?"MODEM_ACCEPTED":p->type==CF_LINK_STATUS_ACK?"LTE_STATUS":p->type==CF_LINK_DIAG_ACK?"LTE_DIAG":p->type==CF_CHAIN_ACK?"WALTER_BENCH_RETURN":"CAN_ECHO_MATCHED",peer,p->size);
        for(size_t i=0;i<p->size;++i) {LOG("%02x",p->payload[i]);}
        LOG("\n");
        if(fire)LOG("FIRE_CHECK result=%s mode=%s check_id=%" PRIu32 "\n",p->payload[1]==2?"unknown":p->payload[1]?"fire":"no_fire",p->payload[2]==1?"STATIC_STUB":"ALGORITHM",ul_u32(p->payload+12));
        if(fire_uplink.active){
            if(hello){
                if(link_reply_sink){fire_uplink.gps_waiting=true;fire_uplink.gps_since=now_ms();}
                else submit(PL_FIRE_CHECK,NULL,0);
                return;
            }
            if(fire){
                unsigned payload_size=tagged?W_SIZE_PAYLOAD_FIRE_TAGGED:W_SIZE_PAYLOAD_FIRE_RESULT;
                ul_packet reply={.version=1,.type=UP_RESULT,.sender=boot,.origin=fire_uplink.request.sender,
                    .request=fire_uplink.request.request,.size=W_PAYLOAD+payload_size+2};
                uint8_t *b=reply.payload;
                ul_p16(b,W_TM_IDENTITY);ul_p16(b+2,0xc000|(telemetry_sequence++&0x3fff));ul_p16(b+4,reply.size-7);
                b[6]=1;b[7]=1;ul_p16(b+8,tagged?W_ID_PAYLOAD_FIRE_TAGGED:W_ID_PAYLOAD_FIRE_RESULT);b[10]=2;b[11]=1;
                memcpy(b+12,fire_uplink.request.payload+12,8);ul_p32(b+20,boot);ul_p32(b+24,now_ms());ul_p16(b+28,payload_size);
                b[30]=p->payload[0];b[31]=2;b[32]=p->payload[1];b[33]=p->payload[2];memcpy(b+38,p->payload+4,12);
                if(tagged){
                    memcpy(b+W_PAYLOAD+W_PAYLOAD_FIRE_TAGGED_GPS_STATUS,p->payload+PL_FIRE_SIZE,PL_GPS_SIZE);
                    b[W_PAYLOAD+W_PAYLOAD_FIRE_TAGGED_ANALYSIS_ERROR]=p->payload[3];
                }
                ul_p16(b+reply.size-2,ul_crc(b,reply.size-2));
                (void)uplink_queue(&reply);
                fire_restore();
            }
        }
        return;
    }
    if(p->type==UL_HELLO_ACK || p->type==UL_ECHO_ACK || p->type==CF_CHAIN_ACK ||
       p->type==CF_RF_WINDOW_ACK || p->type==CF_MODEM_ACCEPTED || p->type==CF_LINK_STATUS_ACK || p->type==CF_LINK_DIAG_ACK || p->type==UL_FIRMWARE_INFO_ACK || p->type==CF_MODEM_FIRMWARE_ACK || p->type==PL_STATUS_ACK || p->type==PL_HEARTBEAT_ACK || p->type==PL_FIRE_RESULT || p->type==UL_ERROR)return;
    if(p->version!=1) {send_error(p,UL_ERR_VERSION);return;}
    if(p->origin!=p->sender) {send_error(p,UL_ERR_REQUEST);return;}
    ul_packet reply;ul_reply(p,boot,&reply);if(!queue(&reply))++busy_drops;
}
static void receive(const ul_packet *p){
    bool previous=console_reply;
    console_reply=pending.active && pending.console && p->origin==boot && p->request==pending.packet.request;
    uint32_t matched_before=matched;
    for(unsigned i=0;i<UC_CAPACITY;i++)if(p->origin==boot && p->request && uhf_console_requests[i]==p->request)console_reply=true;
    receive_impl(p);
    if(matched!=matched_before && (p->type==CF_UHF_RESULT || p->type==CF_UHF_REJECTED))
        for(unsigned i=0;i<UC_CAPACITY;i++)if(uhf_console_requests[i]==p->request)uhf_console_requests[i]=0;
    console_reply=previous;
}
static void submit(uint8_t type,const uint8_t *payload,size_t size) {
    if(!ip_test(&policy)){++refused_requests;LOG("REJECT reason=FLIGHT_ROUTINE_STUB\n");return;}
    if((uhf_is_request(type) && !ip_enabled(&policy,IP_UHF_TELEM)) ||
       (type==CF_SEND_PACKET && !ip_enabled(&policy,IP_LTE_TELEM))){
        ++refused_requests;LOG("REJECT reason=OUTPUT_DISABLED\n");return;
    }
    bool lte_only=type==CF_SEND_PACKET || type==CF_RF_WINDOW || type==CF_LINK_STATUS || type==CF_LINK_DIAG || type==CF_MODEM_FIRMWARE;
    if(target_payload && type!=UL_HELLO && type!=UL_ECHO && type!=UL_FIRMWARE_INFO &&
       type!=PL_STATUS && type!=PL_HEARTBEAT && type!=PL_FIRE_CHECK) {
        ++refused_requests;LOG("REJECT reason=PAYLOAD_READ_ONLY_SERVICES\n");return;
    }
    if((lte_only && !target_lte) || (type==UL_FIRMWARE_INFO && !target_lte && !target_payload && !link_reply_sink) ||
       ((type==PL_STATUS || type==PL_HEARTBEAT || type==PL_FIRE_CHECK) && !target_payload) ||
       (uhf_is_request(type) && target_index!=DR_COMMS_INDEX)) {
        ++refused_requests;LOG("REJECT reason=WRONG_TARGET use_hello_transceiver_lte_or_payload\n");return;
    }
    if(uhf_is_request(type) && uc_count(&uhf_client)==UC_CAPACITY) {++refused_requests;LOG("REJECT reason=UHF_TRACKER_FULL\n");return;}
    if((ihu_can_register(0x0e)&0xe0)!=0) {++refused_requests;LOG("REJECT reason=NORMAL_MODE_REQUIRED\n");return;}
    if(pending.active || output.active) {++refused_requests;LOG("REJECT reason=BUSY\n");return;}
    if(type!=UL_HELLO && !peer) {++refused_requests;LOG("REJECT reason=HELLO_REQUIRED\n");return;}
    if(request_id==UINT32_MAX) {++refused_requests;LOG("REJECT reason=REQUEST_ID_EXHAUSTED\n");return;}
    memset(&pending.packet,0,sizeof(pending.packet));pending.packet.version=1;pending.packet.type=type;
    pending.packet.sender=boot;pending.packet.origin=boot;pending.packet.request=++request_id;
    pending.packet.size=(uint16_t)size;if(size)memcpy(pending.packet.payload,payload,size);
    if(!queue(&pending.packet)) {++refused_requests;LOG("REJECT reason=QUEUE\n");return;}
    if(uhf_is_request(type))(void)uc_start(&uhf_client,&pending.packet,peer,now_ms());
    pending.console=console_reply;
    if(uhf_is_request(type) && console_reply)
        for(unsigned i=0;i<UC_CAPACITY;i++)if(uhf_client.items[i].active && uhf_client.items[i].packet.request==request_id)uhf_console_requests[i]=request_id;
    ++admitted_requests;pending.active=true;pending.started=now_ms();LOG("SUBMITTED request=%" PRIu32 " type=%u bytes=%zu\n",request_id,type,size);
}
static void eps_json(void) {
    if(pending.active || output.active || can.pending) {LOG("REJECT reason=BUSY\n");return;}
    (void)request_sensor(SENSOR_JSON,0,false);
}
static void eps_adc(bool enable) {
    if(pending.active || output.active || can.pending) {LOG("REJECT reason=BUSY\n");return;}
    (void)request_sensor(SENSOR_ADC,0,enable);
}
static bool eps_telemetry(unsigned lte) {
    if((lte==2&&!ip_enabled(&policy,IP_UHF_TELEM)) || (lte==1&&!ip_enabled(&policy,IP_LTE_TELEM))){
        LOG("REJECT reason=OUTPUT_DISABLED\n");return false;
    }
    if(pending.active || output.active || can.pending || !peer || (ihu_can_register(0x0e)&0xe0)) {
        LOG("REJECT reason=BUSY_OR_CAN_NOT_READY\n");return false;
    }
    return request_sensor(SENSOR_TELEMETRY,lte,false);
}
static void health_telemetry(bool system,unsigned lte) {
    uint8_t packet[W_PAYLOAD+W_SIZE_SYSTEM_STATUS+2];
    size_t n=health_packet(packet,system,boot,telemetry_sequence,now_ms(),
        uhf_run.state==UR_RUNNING?uhf_run.period:0,admitted_requests,refused_requests,policy.mode,policy.configuration);
    telemetry_sequence=(telemetry_sequence+1)&0x3fff;
    submit(lte==2?CF_UHF_SEND:lte?CF_SEND_PACKET:CF_CHAIN,packet,n);
}

/* IHU reports an observed identity; it never impersonates the LTE device. */
static void identity_telemetry(unsigned component) {
    if(!identities[component].valid || (uint32_t)(now_ms()-identities[component].observed)>180000) {
        LOG("REJECT reason=IDENTITY_MISSING_OR_STALE query_LTE_again\n");return;
    }
    uint8_t p[W_PAYLOAD+W_SIZE_LTE_CAN_FIRMWARE+2]={0};size_t n=sizeof(p);
    ul_p16(p,W_TM_IDENTITY);ul_p16(p+2,0xc000|(telemetry_sequence++&0x3fff));ul_p16(p+4,n-7);
    p[W_SCHEMA_VERSION]=W_VERSION;p[W_KIND]=W_KINDS_TELEMETRY;
    ul_p16(p+W_MESSAGE_ID,component?W_ID_LTE_MODEM_FIRMWARE:W_ID_LTE_CAN_FIRMWARE);
    p[W_SOURCE]=W_ENDPOINTS_IHU;p[W_TARGET]=W_ENDPOINTS_GROUND;
    ul_p32(p+W_SOURCE_BOOT_ID,boot);ul_p32(p+W_UPTIME_MS,now_ms());
    ul_p16(p+W_PAYLOAD_LENGTH,W_SIZE_LTE_CAN_FIRMWARE);
    memcpy(p+W_PAYLOAD,identities[component].payload,FI_SIZE);
    ul_p32(p+W_PAYLOAD+FI_SIZE,now_ms()-identities[component].observed);
    ul_p16(p+n-2,ul_crc(p,n-2));submit(CF_UHF_SEND,p,n);
}
static void device_telemetry(void) {
    uint8_t packet[W_PAYLOAD+W_SIZE_DEVICE_STATUS+2];
    bool paused=loopback_test;
    size_t n=device_packet(packet,devices,paused,boot,telemetry_sequence++,now_ms());
    submit(CF_UHF_SEND,packet,n);
}
static void uhf_run_pump(uint32_t now) {
    if(uhf_run.state!=UR_RUNNING)return;
    if(!ip_enabled(&policy,IP_UHF_TELEM) || !peer || !can.ready || (ihu_can_register(0x0e)&0xe0) || ur_link_changed(&uhf_run,can.tx_fail,can.tx_timeout) || ihu_can_register(0x2d)) {
        ur_stop(&uhf_run,UR_FAULT);LOG("UHF_RUN FAULT link_not_ready\n");return;
    }
    bool ready=!sensor_job.active && !discovery.active && !pending.active && !output.active && !can.pending && !uc_count(&uhf_client) &&
        (uint32_t)(now-uhf_last_result)>=250;
    int stage=ur_due(&uhf_run,now,ready);
    if(uhf_run.state==UR_EXPIRED)LOG("UHF_RUN EXPIRED submitted=%" PRIu32 " cycles=%" PRIu32 "\n",uhf_run.submitted,uhf_run.cycles);
    if(stage<0)return;
    if(stage<2)health_telemetry(stage==1,2);else if(stage==2)(void)eps_telemetry(2);else device_telemetry();
    if(pending.active && uhf_is_request(pending.packet.type) && stage!=2)ur_submitted(&uhf_run);
    else if(!sensor_job.active) {ur_stop(&uhf_run,UR_FAULT);LOG("UHF_RUN FAULT producer_or_submission\n");}
}
static void devices_status(void) {
    uint32_t now=now_ms();
    for(unsigned i=0;i<DR_COUNT;i++) {
        dr_age(&devices[i],now);
        const struct dr_definition *d=&dr_devices[i];dr_status *v=&devices[i];
        LOG("DEVICE name=%s interface=%s node=%u address=%02x revision=%s state=%s seen=%u age_ms=%" PRIu32 " boot=%" PRIu32 " timeouts=%" PRIu32 "\n",
            d->name,d->interface==DR_CAN?"CAN_A":"I2C1",d->node,d->address,d->future?"planned":"current",
            dr_states[v->state],v->seen,v->seen?(uint32_t)(now-v->last_seen):0,v->boot,v->timeouts);
    }
}
static bool devices_receive(const cf_frame *frame,uint32_t now) {
    if(frame->id<=DR_RESPONSE_BASE || frame->id>DR_RESPONSE_BASE+4)return false;
    if(discovery.active && (uint32_t)(now-discovery.sent)<DR_TIMEOUT_MS &&
       dr_matches(frame,dr_devices[discovery.index].node,discovery.nonce)) {
        dr_seen(&devices[discovery.index],now,ul_u32(frame->data+4));
        /* Discovery observes identity; application HELLO remains explicit. */
        LOG("DEVICE_FOUND name=%s boot=%" PRIu32 "\n",dr_devices[discovery.index].name,devices[discovery.index].boot);
        discovery.active=false;
    }
    return true;
}
static void devices_pump(uint32_t now) {
    for(unsigned i=0;i<DR_COUNT;i++)dr_age(&devices[i],now);
    if(discovery.active && (uint32_t)(now-discovery.sent)>=DR_TIMEOUT_MS) {
        ++devices[discovery.index].timeouts;discovery.active=false;
    }
    /* Background checks never compete with application packets or half-duplex RF. */
    if(discovery.active || pending.active || output.active || can.pending || uc_count(&uhf_client) ||
       (uhf_run.state==UR_RUNNING && uhf_run.cycle && uhf_run.stage<4) || loopback_test ||
       (uint32_t)(now-discovery.last)<2000)return;
    discovery.last=now;unsigned i=discovery.next;discovery.next=(i+1)%DR_COUNT;
    if(dr_devices[i].interface==DR_I2C) {
        /* Full EPS sampling belongs to housekeeping_pump(), not discovery. */
        return;
    }
    if(!can.ready || (ihu_can_register(0x0e)&0xe0) || ihu_can_register(0x2d)) {
        devices[i].state=DR_FAULT;return;
    }
    if(discovery.nonce==UINT16_MAX)return; /* No nonce reuse within a boot. */
    cf_frame f;
    if(dr_request(dr_devices[i].node,++discovery.nonce,boot,&f) && ihu_can_send(&can,&f)) {
        discovery.active=true;discovery.index=i;discovery.sent=now;
    } else devices[i].state=DR_FAULT;
}

static void selftest(void) {
    if(pending.active || output.active || can.pending) {LOG("REJECT reason=BUSY\n");return;}
    cf_frame frame={.id=0x712,.size=8,.data={0x45,0x4d,0x42,0x45,0x52,0,0x55,0xaa}};
    loopback_test=ihu_can_mode(&can,0x40) && ihu_can_send(&can,&frame);
    LOG("SELFTEST started=%d kind=LOCAL_LOOPBACK no_peer_proof=1\n",loopback_test);
}
static void outputs_status(void){
    LOG("OUTPUTS cli_debug=%u cli_telem=%u umb_debug=%u umb_telem=%u uhf_telem=%u lte_telem=%u\n",
        ip_enabled(&policy,0),ip_enabled(&policy,1),ip_enabled(&policy,2),ip_enabled(&policy,3),ip_enabled(&policy,4),ip_enabled(&policy,5));
}
static void mode_status(void){
    LOG("MODE configuration=%s mode=%s simulated=%u flight_routines=STUB reason=%s\n",
        policy.configuration==IP_GROUND_TEST?"GROUND_TEST":"FLIGHT",ip_modes[policy.mode],
        ip_test(&policy)&&policy.mode!=IP_SAFE,policy.reason);
}
static void stop_stream(unsigned channel){
    ++output_generation[channel];
    if(channel==IP_UHF_TELEM)ur_stop(&uhf_run,UR_STOPPED);
    /* Do not revoke a solicited fire-check reply. Previously admitted remote
     * packets may finish; no new periodic submission may follow an OFF. */
    if(pending.active && ((channel==IP_UHF_TELEM&&uhf_is_request(pending.packet.type))||
       (channel==IP_LTE_TELEM&&pending.packet.type==CF_SEND_PACKET))){
        output.active=false;pending.active=false;record_fault(W_IHU_FAULT_CODE_TELEMETRY_TIMEOUT_OR_CANCELLED,now_ms());
    }
}
static void policy_command(const char *s){
    if(!strcmp(s,"outputs")){outputs_status();return;}
    if(!strcmp(s,"mode")){mode_status();return;}
    if(!strcmp(s,"faults")){
        unsigned n=fault_count<IHU_FAULT_CAPACITY?fault_count:IHU_FAULT_CAPACITY;
        LOG("FAULTS total=%u retained=%u persistent=0\n",fault_count,n);
        for(unsigned j=0;j<n;j++){unsigned i=(fault_count-n+j)%IHU_FAULT_CAPACITY;LOG("FAULT code=%u uptime_ms=%" PRIu32 "\n",faults[i].code,faults[i].at);}
        return;
    }
    if(!strncmp(s,"mode ",5)){
        if(sensor_job.active || pending.active || output.active || can.pending || uc_count(&uhf_client) || fire_uplink.active){LOG("REJECT reason=BUSY\n");return;}
        unsigned mode;
        for(mode=1;mode<=IP_NOMINAL;mode++){
            const char *names[]={"boot","startup","commissioning","safe","nominal"};
            if(!strcmp(s+5,names[mode]))break;
        }
        const char *reason=ip_mode(&policy,mode);
        if(reason){LOG("REJECT reason=%s\n",reason);return;}
        ur_stop(&uhf_run,UR_STOPPED);mode_status();outputs_status();return;
    }
    char name[16],value[4],extra;
    if(sscanf(s,"output %15s %3s %c",name,value,&extra)!=2 || (strcmp(value,"on")&&strcmp(value,"off"))){
        LOG("REJECT reason=USAGE_output_NAME_on_or_off\n");return;
    }
    unsigned channel;
    for(channel=0;channel<IP_OUTPUT_COUNT;channel++)if(!strcmp(name,ip_outputs[channel]))break;
    const char *reason=ip_set_output(&policy,channel,!strcmp(value,"on"));
    if(reason){LOG("REJECT reason=%s\n",reason);return;}
    if(!strcmp(value,"off"))stop_stream(channel);
    outputs_status();
}
enum { EPS_POLL_MS=5000, EPS_STALE_MS=6500 };
static struct {
    ltc4162_raw_t eps;
    bool valid,attempted,seen,poll_pending;
    uint8_t failed_register;
    enum eps_error error;
    uint32_t sampled,last,polls_during_gps,max_good_gap_ms;
} housekeeping;
/* Solicited snapshot: age is explicit and failed/missing EPS is never healthy. */
static size_t status_packet(uint8_t *b,const uint8_t *request){
    const size_t n=56;memset(b,0,n);
    ul_p16(b,W_TM_IDENTITY);ul_p16(b+2,0xc000|(telemetry_sequence++&0x3fff));ul_p16(b+4,n-7);
    b[6]=1;b[7]=1;ul_p16(b+8,W_ID_IHU_STATUS);b[10]=2;b[11]=1;
    if(request)memcpy(b+12,request+12,8);
    ul_p32(b+20,boot);ul_p32(b+24,now_ms());ul_p16(b+28,24);
    b[30]=1;b[31]=policy.mode;b[32]=policy.configuration;b[33]=policy.outputs;
    ul_p32(b+34,boot_ready_ms);b[38]=can.ready;b[39]=ihu_can_register(0x2d);
    b[40]=housekeeping.attempted;b[41]=housekeeping.valid;
    ul_p32(b+42,housekeeping.valid?now_ms()-housekeeping.sampled:UINT32_MAX);
    /* Raw readout is retained elsewhere; voltage is unavailable if conversion is unverified. */
    ul_p32(b+46,0x80000000u);
    for(unsigned i=0;i<DR_COUNT;i++)dr_age(&devices[i],now_ms());
    b[50]=devices[DR_COMMS_INDEX].state;b[51]=devices[DR_PAYLOAD_INDEX].state;b[52]=devices[DR_LTE_INDEX].state;
    b[53]=0; /* Health-gated mission enablement is not implemented. */
    ul_p16(b+54,ul_crc(b,54));return n;
}
static bool reboot_scheduled;static uint32_t reboot_at;
/* One frozen five-record bank; an explicit new capture replaces it. */
static struct {
 bool active,valid;uint8_t count;uint32_t id,last;
 ul_packet request;uint8_t records[80];
 struct {uint32_t epoch,id,source,capture;} keys[64];unsigned used;
} cdh;
static void cdh_header(uint8_t *b,size_t n,const ul_packet *request,uint8_t kind,uint16_t id,unsigned payload){
 memset(b,0,n);ul_p16(b,W_TM_IDENTITY);ul_p16(b+2,0xc000|(telemetry_sequence++&0x3fff));ul_p16(b+4,n-7);
 b[6]=1;b[7]=kind;ul_p16(b+8,id);b[10]=2;b[11]=1;
 if(request)memcpy(b+12,request->payload+12,8);
 ul_p32(b+20,boot);ul_p32(b+24,now_ms());ul_p16(b+28,payload);
}
static bool cdh_send(ul_packet *reply){
 ul_p16(reply->payload+reply->size-2,ul_crc(reply->payload,reply->size-2));
 return uplink_queue(reply);
}
static void cdh_error(const ul_packet *request,unsigned stage,unsigned reason){
 ul_packet reply={.version=1,.type=UP_RESULT,.sender=boot,.origin=request->sender,.request=request->request,.size=43};
 cdh_header(reply.payload,43,request,2,W_ID_COMMAND_RESPONSE,11);
 ul_p16(reply.payload+30,ul_u16(request->payload+8));reply.payload[32]=(uint8_t)stage;ul_p16(reply.payload+33,(uint16_t)reason);
 (void)cdh_send(&reply);
}
static void cdh_records(const ul_packet *request){
 ul_packet reply={.version=1,.type=UP_RESULT,.sender=boot,.origin=request->sender,.request=request->request,.size=120};
 cdh_header(reply.payload,120,request,1,W_ID_STATUS_RECORDS,88);
 reply.payload[30]=1;reply.payload[31]=5;reply.payload[32]=16;reply.payload[33]=1;ul_p32(reply.payload+34,cdh.id);
 memcpy(reply.payload+38,cdh.records,80);(void)cdh_send(&reply);
}
static void cdh_receive(const ul_packet *request){
 unsigned id=ul_u16(request->payload+8);
 if(id==6){
  if(policy.mode!=IP_SAFE || policy.outputs){cdh_error(request,1,W_REASON_MODE_NOT_ALLOWED);return;}
  if(reboot_scheduled || cdh.active || pending.active || uhf_run.state==UR_RUNNING){cdh_error(request,1,W_REASON_BUSY);return;}
  ul_packet reply={.version=1,.type=UP_RESULT,.sender=boot,.origin=request->sender,.request=request->request,.size=43};
  cdh_header(reply.payload,43,request,2,W_ID_COMMAND_RESPONSE,11);ul_p16(reply.payload+30,6);
  reply.payload[32]=2;ul_p32(reply.payload+37,5000);
  if(cdh_send(&reply)){reboot_scheduled=true;reboot_at=now_ms();}
  return;
 }
 if(id==3){
  if(request->payload[30]!=W_DATA_GROUP_SYSTEM){++uplink_engine.rejected;cdh_error(request,1,W_REASON_INVALID_PARAMETER);}
  else ember_command(&uplink_engine,request->payload,request->size,now_ms(),uplink_emit,(void *)request);
  return;
 }
 if(id==5){
  if(!cdh.valid){cdh_error(request,3,W_REASON_NOT_AVAILABLE);return;}
  if(ul_u32(request->payload+30)!=cdh.id){cdh_error(request,1,W_REASON_INVALID_PARAMETER);return;}
  cdh_records(request);return;
 }
 uint32_t epoch=ul_u32(request->payload+12),tx=ul_u32(request->payload+16),source=ul_u32(request->payload+20);
 for(unsigned i=0;i<cdh.used;i++)if(cdh.keys[i].epoch==epoch && cdh.keys[i].id==tx){
  if(cdh.keys[i].source!=source || cdh.keys[i].capture!=cdh.id)cdh_error(request,1,W_REASON_TRANSACTION_CONFLICT);
  else if(cdh.valid)cdh_records(request);
  else cdh_error(request,1,W_REASON_BUSY);
  return;
 }
 if(cdh.active || cdh.used==64 || cdh.id==UINT32_MAX){cdh_error(request,1,W_REASON_BUSY);return;}
 ++cdh.id;cdh.keys[cdh.used].epoch=epoch;cdh.keys[cdh.used].id=tx;
 cdh.keys[cdh.used].source=source;cdh.keys[cdh.used++].capture=cdh.id;
 cdh.active=true;cdh.valid=false;cdh.count=0;cdh.last=now_ms();cdh.request=*request;
 cdh_pump(now_ms());
}
static void cdh_pump(uint32_t now){
 if(reboot_scheduled && (uint32_t)(now-reboot_at)>=5000){reboot_scheduled=false;ihu_reboot();}
 if(!cdh.active || (cdh.count && (uint32_t)(now-cdh.last)<1000))return;
 if((cdh.count && (uint32_t)(now-cdh.last)>1100) || (cdh.count==4 && output.active)){
  cdh.active=false;cdh.valid=false;cdh_error(&cdh.request,3,W_REASON_EXECUTION_ERROR);return;
 }
 uint8_t status[56];status_packet(status,cdh.request.payload);uint8_t *v=cdh.records+16*cdh.count;
 ul_p16(v,cdh.count+1);ul_p32(v+2,now);
 v[6]=status[31];v[7]=status[32];v[8]=status[33];v[9]=status[38];v[10]=status[39];v[11]=status[41];memcpy(v+12,status+42,4);
 cdh.last=now;if(++cdh.count==5){cdh.active=false;cdh.valid=true;cdh_records(&cdh.request);}
}
static void housekeeping_pump(uint32_t now){
    if((uint32_t)(now-housekeeping.last)<EPS_POLL_MS || pending.active || output.active || can.pending ||
       discovery.active || uplink_fragments.active || fire_uplink.active || uc_count(&uhf_client) || uhf_run.state==UR_RUNNING)return;
    if(sensor_job.active)return;
    housekeeping.last=now;
    (void)request_sensor(SENSOR_HEALTH,0,false);
}
static const char *eps_error_name(enum eps_error error){
    switch(error){
    case EPS_TIMEOUT: return "I2C_TIMEOUT";
    case EPS_CHECKSUM: return "PEC_CHECKSUM";
    case EPS_I2C_ERROR: return "I2C_ERROR";
    default: return "OK";
    }
}
static void health_result(const ihu_sensor_result *r){
    bool was_valid=housekeeping.valid;
    housekeeping.valid=r->ok;
    housekeeping.error=r->eps_error;
    if(r->between_gps_chunks)++housekeeping.polls_during_gps;
    if(r->ok){
        if(housekeeping.seen){
            uint32_t gap=r->sampled-housekeeping.sampled;
            if(gap>housekeeping.max_good_gap_ms)housekeeping.max_good_gap_ms=gap;
        }
        housekeeping.seen=true;
        housekeeping.eps=r->raw;
        housekeeping.sampled=r->sampled;
        dr_seen(&devices[DR_EPS_I2C_INDEX],r->sampled,0);
    }else{
        housekeeping.failed_register=r->failed;
        devices[DR_EPS_I2C_INDEX].state=DR_FAULT;
        if(!housekeeping.attempted||was_valid){
            record_fault(W_IHU_FAULT_CODE_EPS_READ_FAILED,now_ms());
            ihu_printf(false,"EPS_READ outcome=FAILED register=%02x reason=%s\n",
                       r->failed,eps_error_name(r->eps_error));
        }
    }
    housekeeping.attempted=true;
    if(!stdio_usb_connected())return;
    if(ip_enabled(&policy,IP_CLI_TELEM))ihu_printf(false,"CLI_TELEM mode=%s eps_valid=%u comms=%s lte=%s payload=%s\n",
        ip_modes[policy.mode],housekeeping.valid,dr_states[devices[DR_COMMS_INDEX].state],dr_states[devices[DR_LTE_INDEX].state],dr_states[devices[DR_PAYLOAD_INDEX].state]);
    if(ip_enabled(&policy,IP_UMB_TELEM))ihu_printf(false,"{\"profile\":\"ihu-health-v1\",\"mode\":%u,\"configuration\":%u,\"uptime_ms\":%" PRIu32 ",\"eps_valid\":%u,\"eps_sample_ms\":%" PRIu32 ",\"comms_state\":%u,\"lte_state\":%u,\"payload_state\":%u}\n",
        policy.mode,policy.configuration,now_ms(),housekeeping.valid,housekeeping.sampled,devices[DR_COMMS_INDEX].state,devices[DR_LTE_INDEX].state,devices[DR_PAYLOAD_INDEX].state);
}
static void fire_submit_gps(const gps_result *gps){
    uint8_t tag[PL_GPS_SIZE]={0};
    bool fix=gps && gps->status==GPS_FIX;
    tag[0]=fix?PL_GPS_FIX:PL_GPS_UNAVAILABLE;
    tag[1]=gps?gps->satellites:0;
    ul_p32(tag+2,fix?(int32_t)(gps->latitude*1e7):INT32_MIN);
    ul_p32(tag+6,fix?(int32_t)(gps->longitude*1e7):INT32_MIN);
    ul_p32(tag+10,fix && gps->altitude_valid?(int32_t)(gps->altitude*1000):INT32_MIN);
    /* Account for one 1 Hz receiver epoch and CAN delivery before capture. */
    ul_p32(tag+14,fix?1100:UINT32_MAX);
    fire_uplink.gps_waiting=false;
    fire_uplink.gps_reading=false;
    submit(PL_FIRE_CHECK,tag,sizeof(tag));
}
#if IHU_UHF_STARTUP
static void uhf_startup_gps_complete(const gps_result *gps,uint32_t sampled);
#endif
static bool request_sensor(unsigned kind,unsigned route,bool enable){
    if(sensor_job.active || housekeeping.poll_pending){LOG("REJECT reason=SENSOR_BUSY\n");return false;}
    sensor_job.active=true;sensor_job.kind=kind;sensor_job.route=route;sensor_job.console=console_reply;
    sensor_job.from_run=kind==SENSOR_TELEMETRY && route==2 && uhf_run.state==UR_RUNNING;
    sensor_job.generation=output_generation[route==2?IP_UHF_TELEM:IP_LTE_TELEM];sensor_job.run=run_generation;
    enum ihu_sensor_op op=(kind==SENSOR_GPS || kind==SENSOR_GPS_TELEMETRY || kind==SENSOR_FIRE_GPS)?IHU_SENSOR_READ_GPS:kind==SENSOR_ADC?IHU_SENSOR_SET_ADC:IHU_SENSOR_READ_EPS;
    if(!ihu_sensor_submit(op,enable)){sensor_job.active=false;LOG("REJECT reason=SENSOR_BUSY\n");return false;}
#ifdef IHU_HOST_TEST
    ihu_sensor_result r;if(ihu_sensor_receive(&r))sensor_complete(&r);
#endif
    return true;
}
static void sensor_complete(const ihu_sensor_result *r){
    if(!sensor_job.active)return;
    bool saved=console_reply;console_reply=sensor_job.console;
    unsigned kind=sensor_job.kind,route=sensor_job.route;
    bool from_run=sensor_job.from_run;
    if(from_run && uhf_run.state==UR_RUNNING && (uint32_t)(now_ms()-uhf_run.started)>=uhf_run.duration)
        ur_stop(&uhf_run,UR_EXPIRED);
    sensor_job.active=false;
#if IHU_UHF_STARTUP
    if(kind==SENSOR_GPS_TELEMETRY)uhf_startup_gps_complete(&r->gps,r->sampled);
    else
#endif
    if(kind==SENSOR_FIRE_GPS){
        if(fire_uplink.active && fire_uplink.gps_reading)fire_submit_gps(&r->gps);
    }else if(kind==SENSOR_GPS){
        if(r->gps.status==GPS_FIX)
            LOG("GPS status=FIX latitude_deg=%.6f longitude_deg=%.6f satellites=%u\n",r->gps.latitude,r->gps.longitude,r->gps.satellites);
        else if(r->gps.status==GPS_NO_FIX)LOG("GPS status=NO_FIX satellites=%u\n",r->gps.satellites);
        else LOG("GPS status=%s address=0x10\n",r->gps.status==GPS_BUS_ERROR?"I2C_ERROR":"NO_DATA");
    }else if(kind==SENSOR_HEALTH)health_result(r);
    else if(kind==SENSOR_ADC)LOG("EPS_ADC outcome=%s requested=%d config_before=%04x config_after=%04x\n",r->ok?"VERIFIED":"UNKNOWN",r->enable,r->before,r->after);
    else if(!r->ok){
        LOG("EPS_READ outcome=FAILED register=%02x reason=%s\n",r->failed,eps_error_name(r->eps_error));
        if(from_run && uhf_run.state==UR_RUNNING && sensor_job.run==run_generation){
            ur_stop(&uhf_run,UR_FAULT);LOG("UHF_RUN FAULT producer_or_submission\n");
        }
    } else if(kind==SENSOR_JSON){
        LOG("{\"profile\":\"ltc4162-l-readout-v1\",\"uptime_ms\":%" PRIu32 ",\"registers\":{",r->sampled);
        bool first=true;
#define PRINT(name,address) LOG("%s\"" #name "\":%u",first?"":",",r->raw.name);first=false;
        LTC4162_READOUT_REGISTERS(PRINT)
#undef PRINT
        LOG("}}\n");
    } else {
        unsigned channel=route==2?IP_UHF_TELEM:IP_LTE_TELEM;
        if(!ip_enabled(&policy,channel) || sensor_job.generation!=output_generation[channel] ||
           (from_run && (uhf_run.state!=UR_RUNNING || sensor_job.run!=run_generation))){
            LOG("REJECT reason=OUTPUT_DISABLED_OR_RUN_STOPPED\n");
        } else {
            dr_seen(&devices[DR_EPS_I2C_INDEX],r->sampled,0);
            uint8_t packet[W_PAYLOAD+W_SIZE_POWER_STATUS+2];
            size_t n=power_packet(packet,&r->raw,boot,telemetry_sequence,now_ms(),++eps_readout_count);
            telemetry_sequence=(telemetry_sequence+1)&0x3fff;
            submit(route==2?CF_UHF_SEND:route?CF_SEND_PACKET:CF_CHAIN,packet,n);
            if(from_run){if(pending.active)ur_submitted(&uhf_run);else ur_stop(&uhf_run,UR_FAULT);}
        }
    }
    console_reply=saved;
}

#ifndef IHU_UHF_STARTUP
#define IHU_UHF_STARTUP 0
#endif
#ifndef IHU_BOOT_RX_ONLY
#define IHU_BOOT_RX_ONLY 0
#endif
#if IHU_UHF_STARTUP
#include "uhf_startup.h"
#endif

static void command_impl(const char *s) {
    if(!strcmp(s,"gps")){
        (void)request_sensor(SENSOR_GPS,0,false);return;
    }
#if IHU_UHF_STARTUP
    if(!strcmp(s,"eps status")){
        const char *state=!housekeeping.attempted?"NOT_CHECKED":!housekeeping.valid?"READ_FAILED":
            now_ms()-housekeeping.sampled>EPS_STALE_MS?"STALE":"OK";
        LOG("EPS state=%s bus=I2C1 address=0x68\n",state);
        if(housekeeping.attempted && !housekeeping.valid)
            LOG("EPS_READ outcome=FAILED register=%02x reason=%s\n",housekeeping.failed_register,eps_error_name(housekeeping.error));
        if(housekeeping.seen)
            LOG("EPS last_good_age_ms=%" PRIu32 " stale_limit_ms=%u max_good_gap_ms=%" PRIu32
                " polls_during_gps=%" PRIu32 "\n",now_ms()-housekeeping.sampled,
                (unsigned)EPS_STALE_MS,housekeeping.max_good_gap_ms,housekeeping.polls_during_gps);
        return;
    }
    if(!strcmp(s,"eps json")){
        /* Keep the next housekeeping read inside the live EPS deadline. */
        if(uhf_startup.stage!=UHF_STARTUP_FAILED && now_ms()-housekeeping.last>=4000){
            LOG("REJECT reason=SENSOR_BUSY\n");return;
        }
        (void)request_sensor(SENSOR_JSON,0,false);
        return;
    }
    if(!strcmp(s,"startup") || !strcmp(s,"radio")){
        if(!strcmp(s,"startup"))uhf_startup_history(true);
        mode_status();
        LOG("RADIO behavior=%s uplinks=%" PRIu32 " replies=%" PRIu32 " tx_ok=%" PRIu32 " dropped=%" PRIu32 " heartbeat_ms=%u\n",
            uhf_startup.stage==UHF_STARTUP_ACTIVE?"LINK_ACTIVE":(uhf_startup.stage==UHF_STARTUP_LISTEN || uhf_startup.stage==UHF_STARTUP_ACTIVATE)?"RX_ONLY":
            uhf_startup.stage==UHF_STARTUP_BEACON?"STARTUP_CW":"MUTED",
            uhf_startup_uplinks,uhf_startup_replies,uhf_startup_tx_ok,uhf_startup_drops,uhf_startup.stage==UHF_STARTUP_ACTIVE && uhf_startup.heartbeat_enabled?BD_HEARTBEAT_MS:0);
        LOG("UHF_TELEMETRY enabled=%u listen_seconds=%u telemetry_seconds=%u set=%s\n",
            uhf_startup_schedule.enabled,uhf_startup_schedule.listen_seconds,uhf_startup_schedule.telemetry_seconds,
            uhf_startup_schedule.packet_set==W_UHF_TELEMETRY_SET_FULL?"FULL":"BASIC");
        return;
    }
    if(!strcmp(s,"mode safe") || !strcmp(s,"uhf stop")){
        uhf_startup_fail("Operator stop");mode_status();return;
    }
    if(!strcmp(s,"help")){
        LOG("COMMANDS startup | status | mode | version | faults | rtos\n");
        LOG("DIAGNOSTICS eps status | eps json | gps | radio | outputs\n");
        LOG("CONTROLS mode safe | uhf stop\n");return;
    }
    if(strcmp(s,"status") && strcmp(s,"version") && strcmp(s,"mode") && strcmp(s,"outputs") &&
       strcmp(s,"faults") && strcmp(s,"rtos")){
        LOG("REJECT reason=UHF_STARTUP_READ_ONLY\n");return;
    }
#endif
    if(!strncmp(s,"output ",7) || !strcmp(s,"outputs") || !strncmp(s,"mode",4) || !strcmp(s,"faults")){
        policy_command(s);return;
    }
    if(sensor_job.active && strcmp(s,"rtos") && strcmp(s,"status") && strcmp(s,"version") && strcmp(s,"help") &&
       strcmp(s,"devices") && strcmp(s,"uhf stop")) {LOG("REJECT reason=SENSOR_BUSY\n");return;}
    if(!ip_test(&policy) && strcmp(s,"status") && strcmp(s,"version") && strcmp(s,"help") && strcmp(s,"rtos") && strcmp(s,"devices") && strcmp(s,"eps json")){
        LOG("REJECT reason=FLIGHT_ROUTINE_STUB\n");return;
    }
    if(fire_uplink.active && strcmp(s,"rtos") && strcmp(s,"status") && strcmp(s,"version") && strcmp(s,"help")){
        LOG("REJECT reason=RF_FIRE_CHECK_ACTIVE\n");return;
    }
    if(uhf_run.state==UR_RUNNING && strcmp(s,"rtos") && strcmp(s,"status") && strcmp(s,"devices") && strcmp(s,"uhf stop")) {
        LOG("REJECT reason=UHF_RUN_ACTIVE use_status_or_uhf_stop\n");return;
    }
    if(!strcmp(s,"version"))firmware_status();
    else if(!strcmp(s,"status"))status();
    else if(!strcmp(s,"rtos"))ihu_runtime_status();
    else if(!strcmp(s,"devices"))devices_status();
    else if(!strcmp(s,"devices scan")) {discovery.last=now_ms()-2000;LOG("DEVICE_SCAN scheduled background=1\n");}
    else if(!strcmp(s,"selftest"))selftest();
    else if(!strcmp(s,"normal")) {
        if(pending.active || output.active || can.pending || uc_count(&uhf_client))LOG("REJECT reason=BUSY\n");
        else {bool ok=ihu_can_mode(&can,0);LOG("CAN_NORMAL ready=%d\n",ok);peer=0;}
    }
    else if(!strcmp(s,"hello") || !strcmp(s,"hello transceiver") || !strcmp(s,"hello comms") || !strcmp(s,"hello lte") || !strcmp(s,"hello payload")) {
        if(sensor_job.active || pending.active || output.active || can.pending || uc_count(&uhf_client) ||
           discovery.active || uhf_run.state==UR_RUNNING) {
            LOG("REJECT reason=BUSY_TARGET_SWITCH\n");return;
        }
        target_index=!strcmp(s,"hello payload")?DR_PAYLOAD_INDEX:!strcmp(s,"hello lte")?DR_LTE_INDEX:DR_COMMS_INDEX;peer=0;
        memset(&fragments,0,sizeof(fragments));memset(&can_reader,0,sizeof(can_reader));
        submit(UL_HELLO,NULL,0);
    }
    else if(!strncmp(s,"ping ",5)) {
        char *end;unsigned long n=strtoul(s+5,&end,10);
        if(!s[5] || *end || !n || n>240) {LOG("REJECT reason=SIZE\n");return;}
        uint8_t p[240];for(size_t i=0;i<n;++i)p[i]=(uint8_t)i;submit(UL_ECHO,p,n);
}
    else if(!strcmp(s,"payload fire-check"))submit(PL_FIRE_CHECK,NULL,0);
    else if(!strcmp(s,"payload ident")) {if(target_payload)submit(UL_FIRMWARE_INFO,NULL,0);else LOG("REJECT reason=PAYLOAD_TARGET_REQUIRED\n");}
    else if(!strcmp(s,"payload status"))submit(PL_STATUS,NULL,0);
    else if(!strcmp(s,"payload heartbeat"))submit(PL_HEARTBEAT,NULL,0);
    else if(!strcmp(s,"eps json"))eps_json();
    else if(!strcmp(s,"eps adc on"))eps_adc(true);
    else if(!strcmp(s,"eps adc off"))eps_adc(false);
    else if(!strcmp(s,"uhf stop")) {
        ++run_generation;ur_stop(&uhf_run,UR_STOPPED);LOG("UHF_RUN STOPPED outstanding=%u accepted_packets_may_finish=1\n",uc_count(&uhf_client));
    }
    else if(!strncmp(s,"uhf run ",8)) {
        unsigned duration,period;char extra;
        if(sscanf(s+8,"%u %u %c",&duration,&period,&extra)!=2 || target_index!=DR_COMMS_INDEX || !can.ready || !peer ||
           (ihu_can_register(0x0e)&0xe0) || pending.active || output.active || can.pending ||
           uc_count(&uhf_client) || !ip_enabled(&policy,IP_UHF_TELEM) ||
           !ur_start(&uhf_run,duration,period,now_ms())) {
            LOG("REJECT reason=RUN_RANGE_OR_LINK_BUSY duration=1..120 period=5..60\n");return;
        }
        ur_link_snapshot(&uhf_run,can.tx_fail,can.tx_timeout);
        ++run_generation;LOG("UHF_RUN START duration_s=%u period_s=%u boot_resume=0\n",duration,period);
    }
    else if(!strcmp(s,"uhf transceiver firmware") || !strcmp(s,"uhf comms firmware"))submit(CF_UHF_FIRMWARE,NULL,0);
    else if(!strcmp(s,"uhf lte firmware"))identity_telemetry(0);
    else if(!strcmp(s,"uhf modem firmware"))identity_telemetry(1);
    else if(!strcmp(s,"uhf devices"))device_telemetry();
    else if(!strcmp(s,"uhf heartbeat"))health_telemetry(false,2);
    else if(!strcmp(s,"uhf system"))health_telemetry(true,2);
    else if(!strcmp(s,"uhf eps"))eps_telemetry(2);
    else if(!strcmp(s,"heartbeat lte"))health_telemetry(false,true);
    else if(!strcmp(s,"system lte"))health_telemetry(true,true);
    else if(!strcmp(s,"eps lte"))eps_telemetry(true);
    else if(!strcmp(s,"lte firmware")) {if(target_lte)submit(UL_FIRMWARE_INFO,NULL,0);else LOG("REJECT reason=LTE_TARGET_REQUIRED\n");}
    else if(!strcmp(s,"lte modem firmware"))submit(CF_MODEM_FIRMWARE,NULL,0);
    else if(!strcmp(s,"lte diagnostics"))submit(CF_LINK_DIAG,NULL,0);
    else if(!strcmp(s,"lte status"))submit(CF_LINK_STATUS,NULL,0);
    else if(!strncmp(s,"lte ",4)) {
        char *end;unsigned long seconds=strtoul(s+4,&end,10);
        if(!s[4] || *end || seconds>120) {LOG("REJECT reason=RF_WINDOW_RANGE\n");return;}
        uint8_t p[4];ul_p32(p,seconds);submit(CF_RF_WINDOW,p,4);
    }
    else if(!strcmp(s,"help"))LOG("COMMANDS version | status | rtos | selftest | normal | hello | ping N%s\n"," | hello transceiver | hello lte | hello payload | payload fire-check | payload ident | payload status | payload heartbeat | lte firmware | lte modem firmware | devices | devices scan | uhf run SECONDS PERIOD | uhf stop | uhf transceiver firmware | uhf devices | uhf heartbeat | uhf system | uhf eps | mode [safe/startup/commissioning/nominal] | outputs | output NAME on/off | faults | gps | eps json | eps adc on/off | lte N | lte status | lte diagnostics | heartbeat lte | system lte | eps lte");
    else if(*s)LOG("ERROR unknown command\n");
}
static void command(const char *s){
    bool previous=console_reply;console_reply=true;
    command_impl(s);
    console_reply=previous;
}
void ihu_app_init(void) {
    boot=get_rand_32();if(!boot)boot=1;ihu_can_init(&can);
    ip_init(&policy,IHU_FLIGHT_CONFIGURATION?IP_FLIGHT:IP_GROUND_TEST);
    ember_init(&uplink_engine,boot);
    ip_finish_boot(&policy,can.ready,false,false);
    if(!can.ready)record_fault(W_IHU_FAULT_CODE_CAN_BOOT_CHECK,now_ms());
    boot_ready_ms=now_ms();
#if IHU_UHF_STARTUP
    link_reply_sink=uhf_startup_store_response;
    uhf_startup_schedule.enabled=UHF_STARTUP_TELEMETRY_DEFAULT_ENABLED;
    uhf_startup_schedule.packet_set=UHF_STARTUP_TELEMETRY_DEFAULT_SET;
    uhf_startup_schedule.listen_seconds=UHF_STARTUP_LISTEN_DEFAULT_S;
    uhf_startup_schedule.telemetry_seconds=UHF_STARTUP_TELEMETRY_DEFAULT_S;
    uhf_startup.usb=stdio_usb_connected();
    uhf_startup_stage(UHF_STARTUP_LOCAL,boot_ready_ms);
    housekeeping.last=boot_ready_ms-EPS_POLL_MS;
    uhf_startup_event("BOOT: GROUND_TEST / UHF");
    uhf_startup_event("BOOT -> SAFE: outputs off");
    uhf_startup_event("Checking local CAN controller...");
#endif
}
void ihu_app_command(const char *line){command(line);}
void ihu_app_step(bool scheduled) {
    ihu_sensor_result result;
    while(ihu_sensor_receive(&result)){
        if(result.health){
            housekeeping.poll_pending=false;
            health_result(&result);
        }else sensor_complete(&result);
    }
#if IHU_UHF_STARTUP
    uhf_startup_step();
    uint32_t uhf_startup_now=now_ms();
    cf_frame uhf_startup_frame;
    for(unsigned i=0;i<16 && ihu_can_receive(&can,&uhf_startup_frame);i++)uhf_startup_receive(&uhf_startup_frame,uhf_startup_now);
    uhf_startup_link_pump(now_ms());
    (void)scheduled;
    return;
#endif
        uint32_t now=now_ms();ul_packet packet;cf_frame frame;
        for(unsigned i=0;i<16 && ihu_can_receive(&can,&frame);++i) {
            if(frame.id==UP_REQUEST_ID){uplink_receive(&frame,now);continue;}
            if(devices_receive(&frame,now))continue;
            if(loopback_test && frame.id==0x712) {
                const uint8_t expected[8]={0x45,0x4d,0x42,0x45,0x52,0,0x55,0xaa};
                LOG("SELFTEST outcome=%s kind=LOCAL_LOOPBACK\n",frame.size==8 && !memcmp(frame.data,expected,8)?"PASS":"FAIL");
                loopback_test=false;
            } else if(cf_feed(&fragments,&frame,RX_ID,now) && envelope_from_fragments(now,&packet))receive(&packet);
        }
        /* receive() may submit a new request using now_ms(). Refresh before
         * unsigned elapsed checks: an older loop timestamp would underflow and
         * expire newly submitted RF work immediately. */
        now=now_ms();
        cf_expire(&fragments,now);pump_tx(now);cdh_pump(now);
        for(unsigned i=0;i<UC_CAPACITY;i++) {
            uc_item *x=&uhf_client.items[i];
            if(x->active && (uint32_t)(now-x->started)>=UC_RESULT_MS) {
                record_fault(W_IHU_FAULT_CODE_TELEMETRY_TIMEOUT_OR_CANCELLED,now);bool previous=console_reply;
                console_reply=uhf_console_requests[i]==x->packet.request;uhf_console_requests[i]=0;
                LOG("UHF request=%" PRIu32 " outcome=UNKNOWN reason=RESULT_TIMEOUT ground_ack=0\n",x->packet.request);x->active=false;++unknown;
                console_reply=previous;
                if(uhf_run.state==UR_RUNNING){ur_stop(&uhf_run,UR_FAULT);LOG("UHF_RUN FAULT result_timeout\n");}
            }
        }
        if(pending.active && (uint32_t)(now-pending.started)>=request_timeout_ms(pending.packet.type)) {

            record_fault(W_IHU_FAULT_CODE_TELEMETRY_TIMEOUT_OR_CANCELLED,now);bool previous=console_reply;console_reply=pending.console;
            LOG("RESULT request=%" PRIu32 " outcome=UNKNOWN reason=TIMEOUT\n",pending.packet.request);
            console_reply=previous;
            if(uhf_is_request(pending.packet.type))for(unsigned i=0;i<UC_CAPACITY;i++)
                if(uhf_client.items[i].packet.request==pending.packet.request)uhf_client.items[i].active=false;
            pending.active=false;peer=0;++unknown;
        }
        if(fire_uplink.active && !pending.active)fire_restore();


    if(scheduled){
        housekeeping_pump(now_ms());
        uhf_run_pump(now_ms());
        devices_pump(now_ms());
    }
}
