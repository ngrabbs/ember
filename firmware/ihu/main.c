#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>
#include "pico/stdlib.h"
#include "pico/stdio_usb.h"
#include "pico/unique_id.h"
#include "pico/rand.h"
#include "hardware/uart.h"
#include "mcp25625.h"
#include "wire.h"
#include "lte_link.h"
#include "uhf_client.h"
#include "device_registry.h"
#include "build_identity.h"
#include "firmware_info.h"
#include "payload_protocol.h"
static uc_state uhf_client;
#include "native_telemetry.h"
#if ROLE_IHU
#include "eps_readout.h"
#include "mode_policy.h"
#ifndef IHU_FLIGHT_CONFIGURATION
#define IHU_FLIGHT_CONFIGURATION 0
#endif
static ip_state policy;
static bool console_reply;
static struct {uint32_t at;uint8_t code;} faults[16];
static unsigned fault_count;
static void record_fault(uint8_t code,uint32_t at){unsigned i=fault_count++%16;faults[i].at=at;faults[i].code=code;}

#include "uplink_ping.h"
#include "../usb_bench/protocol.h"
static ember_state uplink_engine;
static cf_reader uplink_fragments;
static struct {bool active;ul_packet request;uint8_t target;uint32_t peer;} fire_uplink;
static struct {uint32_t epoch,id;} fire_keys[16];
static unsigned fire_keys_used;
static void submit(uint8_t type,const uint8_t *payload,size_t size);
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
#endif
#if ROLE_IHU
static void log_output(const char *fmt,...){
    if(!stdio_usb_connected())return;
    va_list args;
    if(console_reply){va_start(args,fmt);vprintf(fmt,args);va_end(args);return;}
    if(ip_enabled(&policy,IP_CLI_DEBUG)){printf("CLI_DEBUG ");va_start(args,fmt);vprintf(fmt,args);va_end(args);}
    if(ip_enabled(&policy,IP_UMB_DEBUG)){printf("UMB_DEBUG ");va_start(args,fmt);vprintf(fmt,args);va_end(args);}
}
#define LOG(...) log_output(__VA_ARGS__)
#else
#define LOG(...) do {if(stdio_usb_connected())printf(__VA_ARGS__);} while(0)
#endif
#define ROLE_NAME (ROLE_IHU?"IHU_MCU":"LTE_CAN_MCU")
#if ROLE_IHU
static uint8_t target_index=DR_COMMS_INDEX;
#define target_lte (target_index==DR_LTE_INDEX)
#define target_payload (target_index==DR_PAYLOAD_INDEX)
#define TX_ID (dr_devices[target_index].request_id)
#define RX_ID (dr_devices[target_index].reply_id)
#else
#define TX_ID CF_LTE_REPLY_ID
#define RX_ID CF_LTE_REQUEST_ID
#endif
#define REQUEST_TIMEOUT 22000
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
#if !ROLE_IHU
static ul_reader uart_reader;
static uint32_t walter_peer,uart_id,chain_ok,chain_unknown;
static struct {bool active;ul_packet incoming,uart;uint32_t started;} chain;
#else
static uint16_t telemetry_sequence;
static uint32_t eps_readout_count;
#endif
static uint32_t now_ms(void) {return to_ms_since_boot(get_absolute_time());}
static void firmware_status(void) {
    LOG("FIRMWARE role=%s version=%s git=%s dirty=%u boot=%" PRIu32 "\n",ROLE_NAME,FW_VERSION,FW_GIT,FW_DIRTY,boot);
}
#if ROLE_IHU
static void mode_status(void);
static void outputs_status(void);
#endif
static void status(void) {
    firmware_status();
#if ROLE_IHU
    mode_status();outputs_status();
    LOG("CAN_TARGET name=%s request=%03x reply=%03x\n",dr_devices[target_index].name,TX_ID,RX_ID);
#endif
    char id[2*PICO_UNIQUE_BOARD_ID_SIZE_BYTES+1];pico_get_unique_board_id_string(id,sizeof(id));
    LOG("STATUS role=%s fw=%s id=%s boot=%" PRIu32 " peer=%" PRIu32
        " can_ready=%d mode=%02x cnf=%02x,%02x,%02x bitrate=500000 tec=%u rec=%u eflg=%02x"
        " tx_ok=%" PRIu32 " tx_fail=%" PRIu32 " tx_timeout=%" PRIu32 " rx=%" PRIu32
        " rx_bad=%" PRIu32 " rx_overflow=%" PRIu32 " fragments_bad=%" PRIu32 " fragments_timeout=%" PRIu32
        " matched=%" PRIu32 " unknown=%" PRIu32 " busy_drops=%" PRIu32 " pending=%d uptime_ms=%" PRIu32,
        ROLE_NAME,FW_VERSION,id,boot,peer,can.ready,mcp_register(0x0e)&0xe0,mcp_register(0x2a),mcp_register(0x29),mcp_register(0x28),
        mcp_register(0x1c),mcp_register(0x1d),mcp_register(0x2d),can.tx_ok,can.tx_fail,can.tx_timeout,can.rx,
        can.rx_bad,can.rx_overflow,fragments.errors,fragments.timeouts,matched,unknown,busy_drops,pending.active,now_ms());
#if !ROLE_IHU
    LOG(" walter_peer=%" PRIu32 " chain_active=%d chain_ok=%" PRIu32 " chain_unknown=%" PRIu32,
        walter_peer,chain.active,chain_ok,chain_unknown);
#endif
    LOG(" uhf_pending=%u",uc_count(&uhf_client));
#if ROLE_IHU
    LOG(" uhf_mode=%u cycles=%" PRIu32 " submitted=%" PRIu32,uhf_run.state,uhf_run.cycles,uhf_run.submitted);
#endif
    LOG("\n");
}
static bool queue(const ul_packet *p) {
    if(output.active)return false;
    size_t size=ul_encode(p,output.wire);if(!size)return false;
    output.route=TX_ID;output.size=size;output.token=(uint16_t)p->request;output.index=0;output.last=now_ms()-2;output.active=true;return true;
}
#if ROLE_IHU
static void fire_restore(void){target_index=fire_uplink.target;peer=fire_uplink.peer;fire_uplink.active=false;}
static bool uplink_emit(const uint8_t *p,size_t n,void *context){
    const ul_packet *request=context;
    if(n!=43 || p[W_KIND]!=W_KINDS_RESPONSE)return false;
    if(p[W_PAYLOAD+W_COMMAND_RESPONSE_STAGE]!=W_STAGE_COMPLETED)return true;
    ul_packet reply={.version=1,.type=UP_RESULT,.sender=boot,
                     .origin=request->sender,.request=request->request,.size=(uint16_t)n};
    memcpy(reply.payload,p,n);
    if(!queue(&reply))return false;
    output.route=UP_REPLY_ID;
    LOG("UPLINK_PING COMPLETED epoch=%" PRIu32 " transaction=%" PRIu32 " response_hex=",
        ul_u32(p+12),ul_u32(p+16));
    for(size_t i=0;i<n;i++){LOG("%02x",p[i]);}LOG("\n");return true;
}
static void uplink_receive(const cf_frame *frame,uint32_t now){
    static ul_packet p;
    if(!cf_feed(&uplink_fragments,frame,UP_REQUEST_ID,now))return;
    if(!up_envelope(&uplink_fragments,&p)||p.type!=UP_PING||p.origin!=p.sender||(!up_native_ping(p.payload,p.size)&&!up_native_fire(p.payload,p.size)))return;
    if(!ip_test(&policy))return;
    if(output.active||(can.pending&&!discovery.active)){LOG("UPLINK_PING rejected=BUSY\n");return;}
    if(up_native_fire(p.payload,p.size)){
        if(fire_uplink.active || pending.active || uc_count(&uhf_client) || uhf_run.state==UR_RUNNING){LOG("UPLINK_FIRE rejected=BUSY\n");return;}
        uint32_t epoch=ul_u32(p.payload+12),id=ul_u32(p.payload+16);
        for(unsigned i=0;i<fire_keys_used;i++)if(fire_keys[i].epoch==epoch && fire_keys[i].id==id)return;
        if(fire_keys_used==16)return;
        fire_keys[fire_keys_used].epoch=epoch;fire_keys[fire_keys_used++].id=id;
        /* Addressed commands take precedence over an observational probe. */
        discovery.active=false;
        LOG("UPLINK_FIRE admitted epoch=%" PRIu32 " transaction=%" PRIu32 "\n",epoch,id);
        fire_uplink.active=true;fire_uplink.request=p;fire_uplink.target=target_index;fire_uplink.peer=peer;
        target_index=DR_PAYLOAD_INDEX;peer=0;memset(&fragments,0,sizeof(fragments));
        submit(UL_HELLO,NULL,0);return;
    }
    if(fire_uplink.active)return;
    ember_command(&uplink_engine,p.payload,p.size,now,uplink_emit,&p);
}
#endif
static void pump_tx(uint32_t now) {
    uint32_t errors=can.tx_fail+can.tx_timeout;mcp_poll_tx(&can,now);
    if(can.tx_fail+can.tx_timeout!=errors) {
#if ROLE_IHU
        record_fault(3,now);
#endif
        output.active=false;LOG("CAN_TX outcome=UNKNOWN reason=FRAME_TX_FAILED\n");
        // Pending application request times out; a CAN hardware outcome is not an app result.
        return;
    }
    if(output.active && !can.pending && (uint32_t)(now-output.last)>=2) {
        cf_frame frame;
        if(!cf_fragment(output.wire,output.size,output.route,output.token,output.index,&frame)) {output.active=false;return;}
        if(mcp_send(&can,&frame)) {
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
#if !ROLE_IHU
static bool valid_telemetry(const ul_packet *p) {
    return native_telemetry_valid(p->payload,p->size,p->sender);
}
static void uart_submit(uint8_t type) {
    memset(&chain.uart,0,sizeof(chain.uart));chain.uart.version=1;chain.uart.type=type;
    chain.uart.sender=boot;chain.uart.origin=boot;chain.uart.request=++uart_id;
    if(type!=UL_HELLO) {chain.uart.size=chain.incoming.size;memcpy(chain.uart.payload,chain.incoming.payload,chain.incoming.size);}
    uint8_t wire[UL_WIRE_MAX];size_t n=ul_encode(&chain.uart,wire);
    uart_putc_raw(uart0,0);uart_write_blocking(uart0,wire,n);chain.started=now_ms();
}
static void chain_fail(uint8_t reason) {
    send_error(&chain.incoming,reason);chain.active=false;walter_peer=0;++chain_unknown;
    LOG("CHAIN outcome=UNKNOWN reason=%u\n",reason);
}
static uint8_t chain_uart_type(void) {
    return chain.incoming.type==CF_MODEM_FIRMWARE?UL_FIRMWARE_INFO:chain.incoming.type==CF_RF_WINDOW?UL_RF_WINDOW:chain.incoming.type==CF_SEND_PACKET?UL_SEND_PACKET:chain.incoming.type==CF_LINK_STATUS?UL_LINK_STATUS:chain.incoming.type==CF_LINK_DIAG?UL_LINK_DIAG:UL_ECHO;
}
static void uart_receive(const ul_packet *p) {
    if(!chain.active || p->version!=1 || p->origin!=boot || p->request!=chain.uart.request)return;
    bool hello=chain.uart.type==UL_HELLO;
    if(!hello && p->sender==walter_peer && p->type==UL_ERROR && p->size==1) {chain_fail(p->payload[0]);return;}
    uint8_t expected=hello?UL_HELLO_ACK:chain.uart.type==UL_RF_WINDOW?UL_RF_WINDOW_ACK:
        chain.uart.type==UL_SEND_PACKET?UL_MODEM_ACCEPTED:chain.uart.type==UL_LINK_STATUS?UL_LINK_STATUS_ACK:chain.uart.type==UL_LINK_DIAG?UL_LINK_DIAG_ACK:chain.uart.type==UL_FIRMWARE_INFO?UL_FIRMWARE_INFO_ACK:UL_ECHO_ACK;
    bool identity=chain.uart.type==UL_FIRMWARE_INFO;
    bool diag=chain.uart.type==UL_LINK_DIAG;
    bool health=chain.uart.type==UL_LINK_STATUS || diag;
    if(p->type!=expected || p->size!=(identity?FI_SIZE:health?(diag?LTE_DIAG_SIZE:16):chain.uart.size) ||
       (!hello && p->sender!=walter_peer) || (!health && !identity && memcmp(p->payload,chain.uart.payload,p->size)) ||
       (identity && (!fi_valid(p->payload,p->size) || ul_u32(p->payload+24)!=p->sender))) {
        chain_fail(CF_LINK_UNKNOWN);return;
    }
    if(hello) {walter_peer=p->sender;uart_submit(chain_uart_type());return;}
    ul_packet out=chain.incoming;out.type=out.type==CF_RF_WINDOW?CF_RF_WINDOW_ACK:
        out.type==CF_SEND_PACKET?CF_MODEM_ACCEPTED:out.type==CF_LINK_STATUS?CF_LINK_STATUS_ACK:out.type==CF_LINK_DIAG?CF_LINK_DIAG_ACK:out.type==CF_MODEM_FIRMWARE?CF_MODEM_FIRMWARE_ACK:CF_CHAIN_ACK;out.sender=boot;
    if(health || identity) {out.size=p->size;memcpy(out.payload,p->payload,p->size);}
    if(!queue(&out)) {chain_fail(CF_BUSY);return;}
    chain.active=false;++chain_ok;
    LOG("CHAIN request=%" PRIu32 " outcome=%s bytes=%u walter=%" PRIu32 "\n",out.request,
        out.type==CF_RF_WINDOW_ACK?"RF_WINDOW_ACCEPTED":out.type==CF_MODEM_ACCEPTED?"MODEM_ACCEPTED":out.type==CF_LINK_STATUS_ACK?"LTE_STATUS":"WALTER_BENCH_RETURN",out.size,walter_peer);
}
#endif
static void receive_impl(const ul_packet *p) {
    if(p->type==CF_UHF_ADMITTED || p->type==CF_UHF_RESULT || p->type==CF_UHF_REJECTED) {
        if(!uc_receive(&uhf_client,p))return;
#if ROLE_IHU
        dr_seen(&devices[DR_COMMS_INDEX],now_ms(),p->sender);
        if(p->type!=CF_UHF_ADMITTED)uhf_last_result=now_ms();
        if(p->payload[1]!=UHF_OK && uhf_run.state==UR_RUNNING) {
            ur_stop(&uhf_run,UR_FAULT);LOG("UHF_RUN FAULT remote_status=%u\n",p->payload[1]);
        }
#endif
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
            bool uncertain=p->payload[0]==CF_LINK_UNKNOWN || p->payload[0]==UL_ERR_MODEM_UNKNOWN;
            if(uncertain) {++unknown;peer=0;}
            else ++refused_requests;
            LOG("RESULT request=%" PRIu32 " outcome=%s reason=%u\n",p->request,uncertain?"UNKNOWN_REMOTE_LINK":"PEER_REJECTED",p->payload[0]);return;
        }
        bool identity=pending.packet.type==UL_FIRMWARE_INFO || pending.packet.type==CF_MODEM_FIRMWARE;
        bool diag=pending.packet.type==CF_LINK_DIAG;
        bool health=pending.packet.type==CF_LINK_STATUS || diag;
        bool fire=pending.packet.type==PL_FIRE_CHECK;
        bool payload_report=pending.packet.type==PL_STATUS || pending.packet.type==PL_HEARTBEAT;
        if(p->type!=expected || p->size!=(identity?FI_SIZE:fire?PL_FIRE_SIZE:payload_report?PL_REPORT_SIZE:health?(diag?LTE_DIAG_SIZE:16):pending.packet.size) || (!health && !identity && !payload_report && !fire && memcmp(p->payload,pending.packet.payload,p->size)) || (identity && (!fi_valid(p->payload,p->size) || (pending.packet.type==UL_FIRMWARE_INFO && ul_u32(p->payload+24)!=p->sender))))return;
        if(fire && !pl_fire_valid(p->payload,p->size,p->sender))return;
        if(payload_report && !pl_report_valid(p->payload,p->size,p->sender))return;
        if(payload_report)LOG("PAYLOAD_REPORT boot=%" PRIu32 " uptime_ms=%" PRIu32 " requests=%" PRIu32 " replies=%" PRIu32 " rejected=%" PRIu32 " fragment_errors=%" PRIu32 "\n",ul_u32(p->payload+4),ul_u32(p->payload+8),ul_u32(p->payload+12),ul_u32(p->payload+16),ul_u32(p->payload+20),ul_u32(p->payload+24));
        if(health)LOG("LTE_STATUS state=%u step=%u error=%u registered=%u window_ms=%" PRIu32 " modem_accepted=%" PRIu32 " rejected=%" PRIu32 "\n",p->payload[0],p->payload[1],p->payload[2],p->payload[3],ul_u32(p->payload+4),ul_u32(p->payload+8),ul_u32(p->payload+12));
        if(diag)LOG("LTE_DIAG version=%u last_cereg=%u send_cereg=%u failure_cereg=%u command=%u failure_command=%u failure_state=%u flags=%u cme=%" PRIu32 " send_elapsed_ms=%" PRIu32 " registration_losses=%" PRIu32 " last_cereg_ms=%" PRIu32 " uart_send_request=%" PRIu32 " error_kind=%u\n",
            p->payload[16],p->payload[17],p->payload[18],p->payload[19],p->payload[20],p->payload[21],p->payload[22],p->payload[23],ul_u32(p->payload+24),ul_u32(p->payload+28),ul_u32(p->payload+32),ul_u32(p->payload+36),ul_u32(p->payload+40),p->payload[45]);
#if ROLE_IHU
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
#endif
        if(hello)peer=p->sender;
#if ROLE_IHU
        dr_seen(&devices[target_index],now_ms(),p->sender);
#endif

        pending.active=false;++matched;
        LOG("RESULT request=%" PRIu32 " outcome=%s peer=%" PRIu32 " bytes=%u hex=",p->request,
            hello?"CAN_HELLO_CONFIRMED":fire?"PAYLOAD_FIRE_RESULT":payload_report?(p->type==PL_STATUS_ACK?"PAYLOAD_STATUS":"PAYLOAD_HEARTBEAT"):identity?"FIRMWARE_IDENTITY":p->type==CF_RF_WINDOW_ACK?"RF_WINDOW_ACCEPTED":
            p->type==CF_MODEM_ACCEPTED?"MODEM_ACCEPTED":p->type==CF_LINK_STATUS_ACK?"LTE_STATUS":p->type==CF_LINK_DIAG_ACK?"LTE_DIAG":p->type==CF_CHAIN_ACK?"WALTER_BENCH_RETURN":"CAN_ECHO_MATCHED",peer,p->size);
        for(size_t i=0;i<p->size;++i) {LOG("%02x",p->payload[i]);}
        LOG("\n");
#if ROLE_IHU
        if(fire)LOG("FIRE_CHECK result=%s mode=%s check_id=%" PRIu32 "\n",p->payload[1]?"fire":"no_fire",p->payload[2]==1?"STATIC_STUB":"ALGORITHM",ul_u32(p->payload+12));
        if(fire_uplink.active){
            if(hello){submit(PL_FIRE_CHECK,NULL,0);return;}
            if(fire){
                ul_packet reply={.version=1,.type=UP_RESULT,.sender=boot,.origin=fire_uplink.request.sender,
                    .request=fire_uplink.request.request,.size=52};
                uint8_t *b=reply.payload;memset(b,0,52);
                ul_p16(b,W_TM_IDENTITY);ul_p16(b+2,0xc000|(telemetry_sequence++&0x3fff));ul_p16(b+4,45);
                b[6]=1;b[7]=1;ul_p16(b+8,W_ID_PAYLOAD_FIRE_RESULT);b[10]=2;b[11]=1;
                memcpy(b+12,fire_uplink.request.payload+12,8);ul_p32(b+20,boot);ul_p32(b+24,now_ms());ul_p16(b+28,20);
                b[30]=1;b[31]=2;b[32]=p->payload[1];b[33]=p->payload[2];memcpy(b+38,p->payload+4,12);
                ul_p16(b+50,ul_crc(b,50));
                if(queue(&reply))output.route=UP_REPLY_ID;
                fire_restore();
            }
        }
#endif
        return;
    }
    if(p->type==UL_HELLO_ACK || p->type==UL_ECHO_ACK || p->type==CF_CHAIN_ACK ||
       p->type==CF_RF_WINDOW_ACK || p->type==CF_MODEM_ACCEPTED || p->type==CF_LINK_STATUS_ACK || p->type==CF_LINK_DIAG_ACK || p->type==UL_FIRMWARE_INFO_ACK || p->type==CF_MODEM_FIRMWARE_ACK || p->type==PL_STATUS_ACK || p->type==PL_HEARTBEAT_ACK || p->type==PL_FIRE_RESULT || p->type==UL_ERROR)return;
    if(p->version!=1) {send_error(p,UL_ERR_VERSION);return;}
    if(p->origin!=p->sender) {send_error(p,UL_ERR_REQUEST);return;}
#if !ROLE_IHU
    if(p->type==UL_FIRMWARE_INFO) {
        if(p->size || !p->sender || !p->request){send_error(p,UL_ERR_PAYLOAD);return;}
        ul_packet reply=*p;reply.sender=boot;reply.type=UL_FIRMWARE_INFO_ACK;reply.size=FI_SIZE;
        fi_payload(reply.payload,boot,now_ms());if(!queue(&reply))++busy_drops;return;
    }
    if(p->type==CF_CHAIN || p->type==CF_SEND_PACKET || p->type==CF_RF_WINDOW || p->type==CF_LINK_STATUS || p->type==CF_LINK_DIAG || p->type==CF_MODEM_FIRMWARE) {
        if(chain.active || output.active || uart_id>=UINT32_MAX-1) {send_error(p,CF_BUSY);return;}
        if(p->type==CF_RF_WINDOW?(p->size!=4 || ul_u32(p->payload)>120):(p->type==CF_LINK_STATUS || p->type==CF_LINK_DIAG || p->type==CF_MODEM_FIRMWARE)?p->size!=0:!valid_telemetry(p)) {send_error(p,CF_BAD_PACKET);return;}
        chain.active=true;chain.incoming=*p;uart_submit(walter_peer?chain_uart_type():UL_HELLO);return;
    }
#endif
    ul_packet reply;ul_reply(p,boot,&reply);if(!queue(&reply))++busy_drops;
}
static void receive(const ul_packet *p){
#if ROLE_IHU
    bool previous=console_reply;
    console_reply=pending.active && pending.console && p->origin==boot && p->request==pending.packet.request;
    uint32_t matched_before=matched;
    for(unsigned i=0;i<UC_CAPACITY;i++)if(p->origin==boot && p->request && uhf_console_requests[i]==p->request)console_reply=true;
#endif
    receive_impl(p);
#if ROLE_IHU
    if(matched!=matched_before && (p->type==CF_UHF_RESULT || p->type==CF_UHF_REJECTED))
        for(unsigned i=0;i<UC_CAPACITY;i++)if(uhf_console_requests[i]==p->request)uhf_console_requests[i]=0;
    console_reply=previous;
#endif
}
static void submit(uint8_t type,const uint8_t *payload,size_t size) {
#if ROLE_IHU
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
    if((lte_only && !target_lte) || (type==UL_FIRMWARE_INFO && !target_lte && !target_payload) ||
       ((type==PL_STATUS || type==PL_HEARTBEAT || type==PL_FIRE_CHECK) && !target_payload) ||
       (uhf_is_request(type) && target_index!=DR_COMMS_INDEX)) {
        ++refused_requests;LOG("REJECT reason=WRONG_TARGET use_hello_transceiver_lte_or_payload\n");return;
    }
#endif
    if(uhf_is_request(type) && uc_count(&uhf_client)==UC_CAPACITY) {++refused_requests;LOG("REJECT reason=UHF_TRACKER_FULL\n");return;}
    if((mcp_register(0x0e)&0xe0)!=0) {++refused_requests;LOG("REJECT reason=NORMAL_MODE_REQUIRED\n");return;}
    if(pending.active || output.active) {++refused_requests;LOG("REJECT reason=BUSY\n");return;}
    if(type!=UL_HELLO && !peer) {++refused_requests;LOG("REJECT reason=HELLO_REQUIRED\n");return;}
    if(request_id==UINT32_MAX) {++refused_requests;LOG("REJECT reason=REQUEST_ID_EXHAUSTED\n");return;}
    memset(&pending.packet,0,sizeof(pending.packet));pending.packet.version=1;pending.packet.type=type;
    pending.packet.sender=boot;pending.packet.origin=boot;pending.packet.request=++request_id;
    pending.packet.size=(uint16_t)size;if(size)memcpy(pending.packet.payload,payload,size);
    if(!queue(&pending.packet)) {++refused_requests;LOG("REJECT reason=QUEUE\n");return;}
    if(uhf_is_request(type))(void)uc_start(&uhf_client,&pending.packet,peer,now_ms());
    #if ROLE_IHU
    pending.console=console_reply;
    if(uhf_is_request(type) && console_reply)
        for(unsigned i=0;i<UC_CAPACITY;i++)if(uhf_client.items[i].active && uhf_client.items[i].packet.request==request_id)uhf_console_requests[i]=request_id;
#endif
    ++admitted_requests;pending.active=true;pending.started=now_ms();LOG("SUBMITTED request=%" PRIu32 " type=%u bytes=%zu\n",request_id,type,size);
}
#if ROLE_IHU
static void eps_json(void) {
    if(pending.active || output.active || can.pending) {LOG("REJECT reason=BUSY\n");return;}
    ltc4162_raw_t raw;uint8_t failed=0;
    if(!eps_read(&raw,&failed)) {LOG("EPS_READ outcome=FAILED register=%02x reason=I2C_OR_PEC\n",failed);return;}
    LOG("{\"profile\":\"ltc4162-l-readout-v1\",\"uptime_ms\":%" PRIu32 ",\"registers\":{",now_ms());
    bool first=true;
#define PRINT(name,address) LOG("%s\"" #name "\":%u",first?"":",",raw.name);first=false;
    LTC4162_READOUT_REGISTERS(PRINT)
#undef PRINT
    LOG("}}\n");
}
static void eps_adc(bool enable) {
    if(pending.active || output.active || can.pending) {LOG("REJECT reason=BUSY\n");return;}
    uint16_t before=0,after=0;bool ok=eps_force_adc(enable,&before,&after);
    LOG("EPS_ADC outcome=%s requested=%d config_before=%04x config_after=%04x\n",ok?"VERIFIED":"UNKNOWN",enable,before,after);
}
static bool eps_telemetry(unsigned lte) {
    if((lte==2&&!ip_enabled(&policy,IP_UHF_TELEM)) || (lte==1&&!ip_enabled(&policy,IP_LTE_TELEM))){
        LOG("REJECT reason=OUTPUT_DISABLED\n");return false;
    }
    if(pending.active || output.active || can.pending || !peer || (mcp_register(0x0e)&0xe0)) {
        LOG("REJECT reason=BUSY_OR_CAN_NOT_READY\n");return false;
    }
    ltc4162_raw_t raw;uint8_t failed=0;
    if(!eps_read(&raw,&failed)) {LOG("EPS_READ outcome=FAILED register=%02x reason=I2C_OR_PEC\n",failed);return false;}
    dr_seen(&devices[DR_EPS_I2C_INDEX],now_ms(),0);
    uint8_t packet[W_PAYLOAD+W_SIZE_POWER_STATUS+2];
    size_t n=power_packet(packet,&raw,boot,telemetry_sequence,now_ms(),++eps_readout_count);
    telemetry_sequence=(telemetry_sequence+1)&0x3fff;submit(lte==2?CF_UHF_SEND:lte?CF_SEND_PACKET:CF_CHAIN,packet,n);
    return pending.active;
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
    if(!ip_enabled(&policy,IP_UHF_TELEM) || !peer || !can.ready || (mcp_register(0x0e)&0xe0) || ur_link_changed(&uhf_run,can.tx_fail,can.tx_timeout) || mcp_register(0x2d)) {
        ur_stop(&uhf_run,UR_FAULT);LOG("UHF_RUN FAULT link_not_ready\n");return;
    }
    bool ready=!discovery.active && !pending.active && !output.active && !can.pending && !uc_count(&uhf_client) &&
        (uint32_t)(now-uhf_last_result)>=250;
    int stage=ur_due(&uhf_run,now,ready);
    if(uhf_run.state==UR_EXPIRED)LOG("UHF_RUN EXPIRED submitted=%" PRIu32 " cycles=%" PRIu32 "\n",uhf_run.submitted,uhf_run.cycles);
    if(stage<0)return;
    if(stage<2)health_telemetry(stage==1,2);else if(stage==2)(void)eps_telemetry(2);else device_telemetry();
    if(pending.active && uhf_is_request(pending.packet.type))ur_submitted(&uhf_run);
    else {ur_stop(&uhf_run,UR_FAULT);LOG("UHF_RUN FAULT producer_or_submission\n");}
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
    if(!can.ready || (mcp_register(0x0e)&0xe0) || mcp_register(0x2d)) {
        devices[i].state=DR_FAULT;return;
    }
    if(discovery.nonce==UINT16_MAX)return; /* No nonce reuse within a boot. */
    cf_frame f;
    if(dr_request(dr_devices[i].node,++discovery.nonce,boot,&f) && mcp_send(&can,&f)) {
        discovery.active=true;discovery.index=i;discovery.sent=now;
    } else devices[i].state=DR_FAULT;
}

#endif
static void selftest(void) {
    if(pending.active || output.active || can.pending) {LOG("REJECT reason=BUSY\n");return;}
    cf_frame frame={.id=0x712,.size=8,.data={0x45,0x4d,0x42,0x45,0x52,0,0x55,0xaa}};
    loopback_test=mcp_mode(&can,0x40) && mcp_send(&can,&frame);
    LOG("SELFTEST started=%d kind=LOCAL_LOOPBACK no_peer_proof=1\n",loopback_test);
}
#if ROLE_IHU
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
    if(channel==IP_UHF_TELEM)ur_stop(&uhf_run,UR_STOPPED);
    /* Do not revoke a solicited fire-check reply. Previously admitted remote
     * packets may finish; no new periodic submission may follow an OFF. */
    if(pending.active && ((channel==IP_UHF_TELEM&&uhf_is_request(pending.packet.type))||
       (channel==IP_LTE_TELEM&&pending.packet.type==CF_SEND_PACKET))){
        output.active=false;pending.active=false;record_fault(4,now_ms());
    }
}
static void policy_command(const char *s){
    if(!strcmp(s,"outputs")){outputs_status();return;}
    if(!strcmp(s,"mode")){mode_status();return;}
    if(!strcmp(s,"faults")){
        unsigned n=fault_count<16?fault_count:16;
        LOG("FAULTS total=%u retained=%u persistent=0\n",fault_count,n);
        for(unsigned j=0;j<n;j++){unsigned i=(fault_count-n+j)%16;LOG("FAULT code=%u uptime_ms=%" PRIu32 "\n",faults[i].code,faults[i].at);}
        return;
    }
    if(!strncmp(s,"mode ",5)){
        if(pending.active || output.active || can.pending || uc_count(&uhf_client) || fire_uplink.active){LOG("REJECT reason=BUSY\n");return;}
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
static struct {ltc4162_raw_t eps;bool valid,attempted;uint32_t sampled,last;} housekeeping;
static void housekeeping_pump(uint32_t now){
    if((uint32_t)(now-housekeeping.last)<5000 || pending.active || output.active || can.pending ||
       discovery.active || uplink_fragments.active || fire_uplink.active || uc_count(&uhf_client) || uhf_run.state==UR_RUNNING)return;
    housekeeping.last=now;uint8_t failed=0;
    bool was_valid=housekeeping.valid;
    housekeeping.valid=eps_read(&housekeeping.eps,&failed);
    if(housekeeping.valid){housekeeping.sampled=now_ms();dr_seen(&devices[DR_EPS_I2C_INDEX],housekeeping.sampled,0);}
    else {devices[DR_EPS_I2C_INDEX].state=DR_FAULT;if(!housekeeping.attempted||was_valid)record_fault(2,now_ms());}
    housekeeping.attempted=true;
    if(!stdio_usb_connected())return;
    if(ip_enabled(&policy,IP_CLI_TELEM))printf("CLI_TELEM mode=%s eps_valid=%u comms=%s lte=%s payload=%s\n",
        ip_modes[policy.mode],housekeeping.valid,dr_states[devices[DR_COMMS_INDEX].state],dr_states[devices[DR_LTE_INDEX].state],dr_states[devices[DR_PAYLOAD_INDEX].state]);
    if(ip_enabled(&policy,IP_UMB_TELEM))printf("{\"profile\":\"ihu-health-v1\",\"mode\":%u,\"configuration\":%u,\"uptime_ms\":%" PRIu32 ",\"eps_valid\":%u,\"eps_sample_ms\":%" PRIu32 ",\"comms_state\":%u,\"lte_state\":%u,\"payload_state\":%u}\n",
        policy.mode,policy.configuration,now_ms(),housekeeping.valid,housekeeping.sampled,devices[DR_COMMS_INDEX].state,devices[DR_LTE_INDEX].state,devices[DR_PAYLOAD_INDEX].state);
}
#endif

static void command_impl(const char *s) {
#if ROLE_IHU
    if(!strncmp(s,"output ",7) || !strcmp(s,"outputs") || !strncmp(s,"mode",4) || !strcmp(s,"faults")){
        policy_command(s);return;
    }
    if(!ip_test(&policy) && strcmp(s,"status") && strcmp(s,"version") && strcmp(s,"help") && strcmp(s,"devices") && strcmp(s,"eps json")){
        LOG("REJECT reason=FLIGHT_ROUTINE_STUB\n");return;
    }
    if(fire_uplink.active && strcmp(s,"status") && strcmp(s,"version") && strcmp(s,"help")){
        LOG("REJECT reason=RF_FIRE_CHECK_ACTIVE\n");return;
    }
#endif
#if ROLE_IHU
    if(uhf_run.state==UR_RUNNING && strcmp(s,"status") && strcmp(s,"devices") && strcmp(s,"uhf stop")) {
        LOG("REJECT reason=UHF_RUN_ACTIVE use_status_or_uhf_stop\n");return;
    }
#endif
    if(!strcmp(s,"version"))firmware_status();
    else if(!strcmp(s,"status"))status();
#if ROLE_IHU
    else if(!strcmp(s,"devices"))devices_status();
    else if(!strcmp(s,"devices scan")) {discovery.last=now_ms()-2000;LOG("DEVICE_SCAN scheduled background=1\n");}
#endif
    else if(!strcmp(s,"selftest"))selftest();
    else if(!strcmp(s,"normal")) {
        if(pending.active || output.active || can.pending || uc_count(&uhf_client))LOG("REJECT reason=BUSY\n");
        else {bool ok=mcp_mode(&can,0);LOG("CAN_NORMAL ready=%d\n",ok);peer=0;}
    }
#if ROLE_IHU
    else if(!strcmp(s,"hello") || !strcmp(s,"hello transceiver") || !strcmp(s,"hello comms") || !strcmp(s,"hello lte") || !strcmp(s,"hello payload")) {
        if(pending.active || output.active || can.pending || uc_count(&uhf_client) ||
           discovery.active || uhf_run.state==UR_RUNNING) {
            LOG("REJECT reason=BUSY_TARGET_SWITCH\n");return;
        }
        target_index=!strcmp(s,"hello payload")?DR_PAYLOAD_INDEX:!strcmp(s,"hello lte")?DR_LTE_INDEX:DR_COMMS_INDEX;peer=0;
        memset(&fragments,0,sizeof(fragments));memset(&can_reader,0,sizeof(can_reader));
        submit(UL_HELLO,NULL,0);
    }
#else
    else if(!strcmp(s,"hello"))submit(UL_HELLO,NULL,0);
#endif
    else if(!strncmp(s,"ping ",5)) {
        char *end;unsigned long n=strtoul(s+5,&end,10);
        if(!s[5] || *end || !n || n>240) {LOG("REJECT reason=SIZE\n");return;}
        uint8_t p[240];for(size_t i=0;i<n;++i)p[i]=(uint8_t)i;submit(UL_ECHO,p,n);
}
#if ROLE_IHU
    else if(!strcmp(s,"payload fire-check"))submit(PL_FIRE_CHECK,NULL,0);
    else if(!strcmp(s,"payload ident")) {if(target_payload)submit(UL_FIRMWARE_INFO,NULL,0);else LOG("REJECT reason=PAYLOAD_TARGET_REQUIRED\n");}
    else if(!strcmp(s,"payload status"))submit(PL_STATUS,NULL,0);
    else if(!strcmp(s,"payload heartbeat"))submit(PL_HEARTBEAT,NULL,0);
    else if(!strcmp(s,"eps json"))eps_json();
    else if(!strcmp(s,"eps adc on"))eps_adc(true);
    else if(!strcmp(s,"eps adc off"))eps_adc(false);
    else if(!strcmp(s,"uhf stop")) {
        ur_stop(&uhf_run,UR_STOPPED);LOG("UHF_RUN STOPPED outstanding=%u accepted_packets_may_finish=1\n",uc_count(&uhf_client));
    }
    else if(!strncmp(s,"uhf run ",8)) {
        unsigned duration,period;char extra;
        if(sscanf(s+8,"%u %u %c",&duration,&period,&extra)!=2 || target_index!=DR_COMMS_INDEX || !can.ready || !peer ||
           (mcp_register(0x0e)&0xe0) || pending.active || output.active || can.pending ||
           uc_count(&uhf_client) || !ip_enabled(&policy,IP_UHF_TELEM) ||
           !ur_start(&uhf_run,duration,period,now_ms())) {
            LOG("REJECT reason=RUN_RANGE_OR_LINK_BUSY duration=1..120 period=5..60\n");return;
        }
        ur_link_snapshot(&uhf_run,can.tx_fail,can.tx_timeout);
        LOG("UHF_RUN START duration_s=%u period_s=%u boot_resume=0\n",duration,period);
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
#endif
    else if(!strcmp(s,"help"))LOG("COMMANDS version | status | selftest | normal | hello | ping N%s\n",ROLE_IHU?" | hello transceiver | hello lte | hello payload | payload fire-check | payload ident | payload status | payload heartbeat | lte firmware | lte modem firmware | devices | devices scan | uhf run SECONDS PERIOD | uhf stop | uhf transceiver firmware | uhf devices | uhf heartbeat | uhf system | uhf eps | mode [safe/startup/commissioning/nominal] | outputs | output NAME on/off | faults | eps json | eps adc on/off | lte N | lte status | lte diagnostics | heartbeat lte | system lte | eps lte":"");
    else if(*s)LOG("ERROR unknown command\n");
}
static void command(const char *s){
#if ROLE_IHU
    bool previous=console_reply;console_reply=true;
#endif
    command_impl(s);
#if ROLE_IHU
    console_reply=previous;
#endif
}
int main(void) {
    stdio_init_all();boot=get_rand_32();if(!boot)boot=1;mcp_init(&can);
#if ROLE_IHU
    ip_init(&policy,IHU_FLIGHT_CONFIGURATION?IP_FLIGHT:IP_GROUND_TEST);
    eps_bus_init();
    ember_init(&uplink_engine,boot);
#endif
    if(can.ready)(void)mcp_mode(&can,0);
#if ROLE_IHU
    /* No qualified persistent flight history exists yet: FLIGHT stays restricted. */
    ip_finish_boot(&policy,can.ready,false,false);
    if(!can.ready)record_fault(1,now_ms());
#endif
#if !ROLE_IHU
    uart_init(uart0,115200);gpio_set_function(0,GPIO_FUNC_UART);gpio_set_function(1,GPIO_FUNC_UART);
    gpio_pull_up(1);uart_set_hw_flow(uart0,false,false);uart_set_format(uart0,8,1,UART_PARITY_NONE);uart_set_fifo_enabled(uart0,true);
#endif
    gpio_init(13);gpio_set_dir(13,GPIO_OUT);char line[40];size_t used=0;bool discard=false,led=false;uint32_t blink=0;
    while(true) {
        uint32_t now=now_ms();ul_packet packet;cf_frame frame;
#if !ROLE_IHU
        for(unsigned i=0;i<128 && uart_is_readable(uart0);++i) {
            uint8_t ch=uart_getc(uart0);if(ul_feed(&uart_reader,ch,now,&packet))uart_receive(&packet);
        }
        // HELLO handling can synchronously start an ECHO and set started to a
        // newer time. Refresh before unsigned subtraction or the stale loop
        // timestamp would look like a full timer wrap and expire the new request.
        now=now_ms();
        ul_expire(&uart_reader,now);
        if(chain.active && (uint32_t)(now-chain.started)>=(chain.uart.type==UL_SEND_PACKET?17000:UL_REQUEST_MS))chain_fail(CF_LINK_UNKNOWN);
#endif
        for(unsigned i=0;i<2 && mcp_receive(&can,&frame);++i) {
#if ROLE_IHU
            if(frame.id==UP_REQUEST_ID){uplink_receive(&frame,now);continue;}
            if(devices_receive(&frame,now))continue;
#else
            if(frame.id==DR_QUERY_ID) {
                cf_frame response;
                if(!can.pending && !output.active && dr_respond(&frame,DR_LTE_NODE,boot,&response))
                    (void)mcp_send(&can,&response);
                continue;
            }
#endif
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
        cf_expire(&fragments,now);pump_tx(now);
        for(unsigned i=0;i<UC_CAPACITY;i++) {
            uc_item *x=&uhf_client.items[i];
            if(x->active && (uint32_t)(now-x->started)>=UC_RESULT_MS) {
#if ROLE_IHU
                record_fault(4,now);bool previous=console_reply;
                console_reply=uhf_console_requests[i]==x->packet.request;uhf_console_requests[i]=0;
#endif
                LOG("UHF request=%" PRIu32 " outcome=UNKNOWN reason=RESULT_TIMEOUT ground_ack=0\n",x->packet.request);x->active=false;++unknown;
#if ROLE_IHU
                console_reply=previous;
                if(uhf_run.state==UR_RUNNING){ur_stop(&uhf_run,UR_FAULT);LOG("UHF_RUN FAULT result_timeout\n");}
#endif
            }
        }
        if(pending.active && (uint32_t)(now-pending.started)>=(pending.packet.type==CF_SEND_PACKET?REQUEST_TIMEOUT:5000)) {

#if ROLE_IHU
            record_fault(4,now);bool previous=console_reply;console_reply=pending.console;
#endif
            LOG("RESULT request=%" PRIu32 " outcome=UNKNOWN reason=TIMEOUT\n",pending.packet.request);
#if ROLE_IHU
            console_reply=previous;
#endif
            if(uhf_is_request(pending.packet.type))for(unsigned i=0;i<UC_CAPACITY;i++)
                if(uhf_client.items[i].packet.request==pending.packet.request)uhf_client.items[i].active=false;
            pending.active=false;peer=0;++unknown;
        }
#if ROLE_IHU
        if(fire_uplink.active && !pending.active)fire_restore();

#endif
        for(unsigned i=0;i<40;++i) {
            int ch=getchar_timeout_us(0);if(ch==PICO_ERROR_TIMEOUT)break;
            if(ch=='\r' || ch=='\n') {if(discard)LOG("ERROR command too long\n");else {line[used]=0;command(line);}used=0;discard=false;}
            else if(!discard) {if(ch && used+1<sizeof(line))line[used++]=(char)ch;else discard=true;}
        }
#if ROLE_IHU
        // Process console off/status commands before considering a due read.
        housekeeping_pump(now_ms());
        uhf_run_pump(now_ms());
        devices_pump(now_ms());
#endif
        if((uint32_t)(now-blink)>=500) {blink=now;led=!led;gpio_put(13,led);}sleep_us(500);
    }
}
