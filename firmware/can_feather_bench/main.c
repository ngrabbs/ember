#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
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
static uc_state uhf_client;
#include "native_telemetry.h"
#if ROLE_IHU
#include "eps_readout.h"
#include "uplink_ping.h"
#include "../usb_bench/protocol.h"
static ember_state uplink_engine;
static cf_reader uplink_fragments;
#include "power_packet.h"
#include "health_packet.h"
#include "device_packet.h"
#include "lte_queue.h"
#include "autotelem.h"
#include "uhf_run.h"
static dr_status devices[DR_COUNT];
static struct {bool valid;uint32_t observed;uint8_t payload[FI_SIZE];} identities[2];
static struct {bool active;uint8_t index,next;uint16_t nonce;uint32_t sent,last;} discovery;
static ur_state uhf_run;
static uint32_t uhf_last_result;
#endif
#define LOG(...) do {if(stdio_usb_connected())printf(__VA_ARGS__);} while(0)
#define ROLE_NAME (ROLE_IHU?"IHU_MCU":"LTE_CAN_MCU")
#if ROLE_IHU
static bool target_lte;
#define TX_ID (dr_devices[target_lte?DR_LTE_INDEX:DR_COMMS_INDEX].request_id)
#define RX_ID (dr_devices[target_lte?DR_LTE_INDEX:DR_COMMS_INDEX].reply_id)
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
static struct {bool active;ul_packet packet;uint32_t started;} pending;
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
static lq_state telemetry_queue;
static bool queue_owned;
static bool queue_send_ready;
static at_state auto_telem;
#endif
static uint32_t now_ms(void) {return to_ms_since_boot(get_absolute_time());}
static void firmware_status(void) {
    LOG("FIRMWARE role=%s version=%s git=%s dirty=%u boot=%" PRIu32 "\n",ROLE_NAME,FW_VERSION,FW_GIT,FW_DIRTY,boot);
}
static void status(void) {
    firmware_status();
#if ROLE_IHU
    LOG("CAN_TARGET name=%s request=%03x reply=%03x\n",target_lte?"LTE":"COMMS",TX_ID,RX_ID);
#endif
    char id[2*PICO_UNIQUE_BOARD_ID_SIZE_BYTES+1];pico_get_unique_board_id_string(id,sizeof(id));
    LOG("STATUS role=%s fw=can-bench-v8 id=%s boot=%" PRIu32 " peer=%" PRIu32
        " can_ready=%d mode=%02x cnf=%02x,%02x,%02x bitrate=500000 tec=%u rec=%u eflg=%02x"
        " tx_ok=%" PRIu32 " tx_fail=%" PRIu32 " tx_timeout=%" PRIu32 " rx=%" PRIu32
        " rx_bad=%" PRIu32 " rx_overflow=%" PRIu32 " fragments_bad=%" PRIu32 " fragments_timeout=%" PRIu32
        " matched=%" PRIu32 " unknown=%" PRIu32 " busy_drops=%" PRIu32 " pending=%d uptime_ms=%" PRIu32,
        ROLE_NAME,id,boot,peer,can.ready,mcp_register(0x0e)&0xe0,mcp_register(0x2a),mcp_register(0x29),mcp_register(0x28),
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
    if(!up_envelope(&uplink_fragments,&p)||p.type!=UP_PING||p.origin!=p.sender||!up_native_ping(p.payload,p.size))return;
    if(output.active||can.pending){LOG("UPLINK_PING rejected=BUSY\n");return;}
    ember_command(&uplink_engine,p.payload,p.size,now,uplink_emit,&p);
}
#endif
static void pump_tx(uint32_t now) {
    uint32_t errors=can.tx_fail+can.tx_timeout;mcp_poll_tx(&can,now);
    if(can.tx_fail+can.tx_timeout!=errors) {
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
#if ROLE_IHU
static void queued_reply(const ul_packet *p,bool valid) {
    if(!queue_owned)return;
    queue_owned=false;
    if(!valid) {lq_hold(&telemetry_queue,LQ_HOLD_UNKNOWN);return;}
    if(p->type==CF_LINK_STATUS_ACK) {
        if(telemetry_queue.enabled)queue_send_ready=lq_status(&telemetry_queue,p->payload,now_ms());
        else telemetry_queue.state=LQ_IDLE;
    } else if(p->type==CF_MODEM_ACCEPTED)lq_result(&telemetry_queue,0,now_ms());
    else if(p->type==UL_ERROR) {
        if(telemetry_queue.state==LQ_SEND)lq_result(&telemetry_queue,p->payload[0],now_ms());
        else lq_hold(&telemetry_queue,LQ_HOLD_UNKNOWN);
    }
}
#define QUEUED_REPLY(p,valid) queued_reply(p,valid)
#else
#define QUEUED_REPLY(p,valid) ((void)0)
#endif
static void receive(const ul_packet *p) {
    if(p->type==CF_UHF_ADMITTED || p->type==CF_UHF_RESULT || p->type==CF_UHF_REJECTED) {
        if(!uc_receive(&uhf_client,p))return;
#if ROLE_IHU
        dr_seen(&devices[DR_COMMS_INDEX],now_ms(),p->sender);
        if(p->type!=CF_UHF_ADMITTED)uhf_last_result=now_ms();
        if(p->payload[1]!=UHF_OK && uhf_run.state==UR_RUNNING) {
            ur_stop(&uhf_run,UR_FAULT);LOG("UHF_RUN FAULT remote_status=%u\n",p->payload[1]);
        }
#endif
        if(pending.active && pending.packet.type==CF_UHF_SEND && pending.packet.request==p->request)pending.active=false;
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
            pending.packet.type==CF_RF_WINDOW?CF_RF_WINDOW_ACK:pending.packet.type==CF_SEND_PACKET?CF_MODEM_ACCEPTED:pending.packet.type==CF_LINK_STATUS?CF_LINK_STATUS_ACK:pending.packet.type==CF_LINK_DIAG?CF_LINK_DIAG_ACK:pending.packet.type==UL_FIRMWARE_INFO?UL_FIRMWARE_INFO_ACK:pending.packet.type==CF_MODEM_FIRMWARE?CF_MODEM_FIRMWARE_ACK:UL_ECHO_ACK;
        if(p->version!=1 || (!hello && p->sender!=peer)) {
            QUEUED_REPLY(p,false);
            pending.active=false;peer=0;++unknown;LOG("RESULT outcome=UNKNOWN reason=PEER_RESET_OR_VERSION\n");return;
        }
        if(p->type==UL_ERROR && p->size==1) {
            QUEUED_REPLY(p,true);
            pending.active=false;
            bool uncertain=p->payload[0]==CF_LINK_UNKNOWN || p->payload[0]==UL_ERR_MODEM_UNKNOWN;
            if(uncertain) {++unknown;peer=0;}
            else ++refused_requests;
            LOG("RESULT request=%" PRIu32 " outcome=%s reason=%u\n",p->request,uncertain?"UNKNOWN_REMOTE_LINK":"PEER_REJECTED",p->payload[0]);return;
        }
        bool identity=pending.packet.type==UL_FIRMWARE_INFO || pending.packet.type==CF_MODEM_FIRMWARE;
        bool diag=pending.packet.type==CF_LINK_DIAG;
        bool health=pending.packet.type==CF_LINK_STATUS || diag;
        if(p->type!=expected || p->size!=(identity?FI_SIZE:health?(diag?LTE_DIAG_SIZE:16):pending.packet.size) || (!health && !identity && memcmp(p->payload,pending.packet.payload,p->size)) || (identity && (!fi_valid(p->payload,p->size) || (pending.packet.type==UL_FIRMWARE_INFO && ul_u32(p->payload+24)!=p->sender))))return;
        if(health)LOG("LTE_STATUS state=%u step=%u error=%u registered=%u window_ms=%" PRIu32 " modem_accepted=%" PRIu32 " rejected=%" PRIu32 "\n",p->payload[0],p->payload[1],p->payload[2],p->payload[3],ul_u32(p->payload+4),ul_u32(p->payload+8),ul_u32(p->payload+12));
        if(diag)LOG("LTE_DIAG version=%u last_cereg=%u send_cereg=%u failure_cereg=%u command=%u failure_command=%u failure_state=%u flags=%u cme=%" PRIu32 " send_elapsed_ms=%" PRIu32 " registration_losses=%" PRIu32 " last_cereg_ms=%" PRIu32 " uart_send_request=%" PRIu32 " error_kind=%u\n",
            p->payload[16],p->payload[17],p->payload[18],p->payload[19],p->payload[20],p->payload[21],p->payload[22],p->payload[23],ul_u32(p->payload+24),ul_u32(p->payload+28),ul_u32(p->payload+32),ul_u32(p->payload+36),ul_u32(p->payload+40),p->payload[45]);
#if ROLE_IHU
        if(identity) {
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
        dr_seen(&devices[target_lte?DR_LTE_INDEX:DR_COMMS_INDEX],now_ms(),p->sender);
#endif
        QUEUED_REPLY(p,true);
        pending.active=false;++matched;
        LOG("RESULT request=%" PRIu32 " outcome=%s peer=%" PRIu32 " bytes=%u hex=",p->request,
            hello?"CAN_HELLO_CONFIRMED":p->type==CF_RF_WINDOW_ACK?"RF_WINDOW_ACCEPTED":
            p->type==CF_MODEM_ACCEPTED?"MODEM_ACCEPTED":p->type==CF_LINK_STATUS_ACK?"LTE_STATUS":p->type==CF_LINK_DIAG_ACK?"LTE_DIAG":p->type==CF_CHAIN_ACK?"WALTER_BENCH_RETURN":"CAN_ECHO_MATCHED",peer,p->size);
        for(size_t i=0;i<p->size;++i) {LOG("%02x",p->payload[i]);}
        LOG("\n");return;
    }
    if(p->type==UL_HELLO_ACK || p->type==UL_ECHO_ACK || p->type==CF_CHAIN_ACK ||
       p->type==CF_RF_WINDOW_ACK || p->type==CF_MODEM_ACCEPTED || p->type==CF_LINK_STATUS_ACK || p->type==CF_LINK_DIAG_ACK || p->type==UL_FIRMWARE_INFO_ACK || p->type==CF_MODEM_FIRMWARE_ACK || p->type==UL_ERROR)return;
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
static void submit(uint8_t type,const uint8_t *payload,size_t size) {
#if ROLE_IHU
    bool lte_only=type==CF_SEND_PACKET || type==CF_RF_WINDOW || type==CF_LINK_STATUS || type==CF_LINK_DIAG || type==UL_FIRMWARE_INFO || type==CF_MODEM_FIRMWARE;
    if((lte_only && !target_lte) || (type==CF_UHF_SEND && target_lte)) {
        ++refused_requests;LOG("REJECT reason=WRONG_TARGET use_hello_comms_or_hello_lte\n");return;
    }
#endif
    if(type==CF_UHF_SEND && uc_count(&uhf_client)==UC_CAPACITY) {++refused_requests;LOG("REJECT reason=UHF_TRACKER_FULL\n");return;}
    if((mcp_register(0x0e)&0xe0)!=0) {++refused_requests;LOG("REJECT reason=NORMAL_MODE_REQUIRED\n");return;}
    if(pending.active || output.active) {++refused_requests;LOG("REJECT reason=BUSY\n");return;}
    if(type!=UL_HELLO && !peer) {++refused_requests;LOG("REJECT reason=HELLO_REQUIRED\n");return;}
    if(request_id==UINT32_MAX) {++refused_requests;LOG("REJECT reason=REQUEST_ID_EXHAUSTED\n");return;}
    memset(&pending.packet,0,sizeof(pending.packet));pending.packet.version=1;pending.packet.type=type;
    pending.packet.sender=boot;pending.packet.origin=boot;pending.packet.request=++request_id;
    pending.packet.size=(uint16_t)size;if(size)memcpy(pending.packet.payload,payload,size);
    if(!queue(&pending.packet)) {++refused_requests;LOG("REJECT reason=QUEUE\n");return;}
    if(type==CF_UHF_SEND)(void)uc_start(&uhf_client,&pending.packet,peer,now_ms());
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
static void auto_status(void) {
    LOG("AUTOTELEM enabled=%d period_ms=%" PRIu32 " next_ms=%" PRIu32
        " due=%" PRIu32 " skipped=%" PRIu32 " submitted=%" PRIu32 " failed=%" PRIu32
        " pending=%d uptime_ms=%" PRIu32 "\n",auto_telem.enabled,auto_telem.period_ms,
        auto_telem.next_ms,auto_telem.due,auto_telem.skipped,auto_telem.submitted,
        auto_telem.failed,pending.active,now_ms());
}
static void auto_pump(uint32_t now) {
    if(!at_due(&auto_telem,now))return;
    bool idle=!pending.active && !output.active && !can.pending && can.ready && peer &&
        request_id<UINT32_MAX && !telemetry_queue.enabled && !queue_owned &&
        (mcp_register(0x0e)&0xe0)==0;
    at_action action=at_poll(&auto_telem,now,idle);
    if(action==AT_SKIP) {LOG("AUTOTELEM_SKIP reason=BUSY_OR_CAN_NOT_READY\n");}
    else if(action==AT_READ) {
        if(eps_telemetry(false)) {
            ++auto_telem.submitted;
            LOG("AUTOTELEM_SUBMITTED request=%" PRIu32 " sequence=%u\n",request_id,
                (unsigned)((telemetry_sequence-1)&0x3fff));
        } else ++auto_telem.failed;
    }
}
static void queue_status(void) {
    lq_packet *front=lq_front(&telemetry_queue);
    LOG("LTE_QUEUE enabled=%d count=%u capacity=%u state=%u hold=%u attempts=%u accepted=%" PRIu32 " full=%" PRIu32 " retries=%" PRIu32 "\n",
        telemetry_queue.enabled,telemetry_queue.count,LQ_CAPACITY,telemetry_queue.state,telemetry_queue.hold,
        front?front->attempts:0,telemetry_queue.accepted,telemetry_queue.full,telemetry_queue.retries);
}
static void eps_enqueue(void) {
    // EPS reads are synchronous; do not stall an in-flight CAN exchange.
    if(pending.active || output.active || can.pending) {LOG("REJECT reason=BUSY\n");return;}
    if(telemetry_queue.count==LQ_CAPACITY) {++telemetry_queue.full;LOG("REJECT reason=LTE_QUEUE_FULL\n");return;}
    ltc4162_raw_t raw;uint8_t failed=0;
    if(!eps_read(&raw,&failed)) {LOG("EPS_READ outcome=FAILED register=%02x reason=I2C_OR_PEC\n",failed);return;}
    uint8_t packet[W_PAYLOAD+W_SIZE_POWER_STATUS+2];
    size_t n=power_packet(packet,&raw,boot,telemetry_sequence,now_ms(),++eps_readout_count);
    if(!lq_push(&telemetry_queue,packet,n,now_ms())) {LOG("REJECT reason=LTE_QUEUE\n");return;}
    LOG("EPS_QUEUED sequence=%u count=%u bytes=%zu hex=",telemetry_sequence,telemetry_queue.count,n);
    for(size_t i=0;i<n;++i)LOG("%02x",packet[i]);
    LOG("\n");telemetry_sequence=(telemetry_sequence+1)&0x3fff;
}
static void queue_pump(uint32_t now) {
    if(!telemetry_queue.enabled || pending.active || output.active || can.pending ||
       !peer || (mcp_register(0x0e)&0xe0))return;
    if(queue_send_ready) {
        queue_send_ready=false;
        // If disabled between status and submission, retain without sending.
        lq_packet *front=lq_front(&telemetry_queue);
        if(front) {submit(CF_SEND_PACKET,front->bytes,front->size);queue_owned=pending.active;}
    } else if(lq_poll(&telemetry_queue,now)) {submit(CF_LINK_STATUS,NULL,0);queue_owned=pending.active;}
    if((telemetry_queue.state==LQ_SEND || telemetry_queue.state==LQ_STATUS) && !queue_owned)
        lq_hold(&telemetry_queue,LQ_HOLD_UNKNOWN);
}
static void health_telemetry(bool system,unsigned lte) {
    uint8_t packet[W_PAYLOAD+W_SIZE_SYSTEM_STATUS+2];
    size_t n=health_packet(packet,system,boot,telemetry_sequence,now_ms(),
        uhf_run.state==UR_RUNNING?uhf_run.period:auto_telem.enabled?auto_telem.period_ms:0,admitted_requests,refused_requests);
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
    bool paused=auto_telem.enabled || telemetry_queue.enabled || loopback_test;
    size_t n=device_packet(packet,devices,paused,boot,telemetry_sequence++,now_ms());
    submit(CF_UHF_SEND,packet,n);
}
static void uhf_run_pump(uint32_t now) {
    if(uhf_run.state!=UR_RUNNING)return;
    if(!peer || !can.ready || (mcp_register(0x0e)&0xe0) || ur_link_changed(&uhf_run,can.tx_fail,can.tx_timeout) || mcp_register(0x2d)) {
        ur_stop(&uhf_run,UR_FAULT);LOG("UHF_RUN FAULT link_not_ready\n");return;
    }
    bool ready=!discovery.active && !pending.active && !output.active && !can.pending && !uc_count(&uhf_client) &&
        (uint32_t)(now-uhf_last_result)>=250;
    int stage=ur_due(&uhf_run,now,ready);
    if(uhf_run.state==UR_EXPIRED)LOG("UHF_RUN EXPIRED submitted=%" PRIu32 " cycles=%" PRIu32 "\n",uhf_run.submitted,uhf_run.cycles);
    if(stage<0)return;
    if(stage<2)health_telemetry(stage==1,2);else if(stage==2)(void)eps_telemetry(2);else device_telemetry();
    if(pending.active && pending.packet.type==CF_UHF_SEND)ur_submitted(&uhf_run);
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
       (uhf_run.state==UR_RUNNING && uhf_run.cycle && uhf_run.stage<4) || auto_telem.enabled || telemetry_queue.enabled || loopback_test ||
       (uint32_t)(now-discovery.last)<2000)return;
    discovery.last=now;unsigned i=discovery.next;discovery.next=(i+1)%DR_COUNT;
    if(dr_devices[i].interface==DR_I2C) {
        uint16_t config;
        if(eps_word(LTC4162_REG_config_bits,&config))dr_seen(&devices[i],now_ms(),0);
        else devices[i].state=DR_FAULT;
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
static void command(const char *s) {
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
    else if(!strcmp(s,"hello") || !strcmp(s,"hello comms") || !strcmp(s,"hello lte")) {
        if(pending.active || output.active || can.pending || uc_count(&uhf_client) ||
           auto_telem.enabled || telemetry_queue.enabled || queue_owned || queue_send_ready || discovery.active) {
            LOG("REJECT reason=BUSY_TARGET_SWITCH\n");return;
        }
        target_lte=!strcmp(s,"hello lte");peer=0;
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
    else if(!strcmp(s,"telemetry"))health_telemetry(false,false);
    else if(!strcmp(s,"eps json"))eps_json();
    else if(!strcmp(s,"eps adc on"))eps_adc(true);
    else if(!strcmp(s,"eps adc off"))eps_adc(false);
    else if(!strcmp(s,"eps telemetry"))eps_telemetry(false);
    else if(!strcmp(s,"telem status"))auto_status();
    else if(!strcmp(s,"telem off")) {at_disable(&auto_telem);auto_status();}
    else if(!strcmp(s,"telem on") || !strncmp(s,"telem on ",9)) {
        unsigned long seconds=AT_DEFAULT_SECONDS;
        if(s[8]) {
            char *end;seconds=strtoul(s+9,&end,10);
            if(s[9]<'0' || s[9]>'9' || *end || seconds<AT_MIN_SECONDS || seconds>AT_MAX_SECONDS) {
                LOG("REJECT reason=TELEM_PERIOD_RANGE min_seconds=%u max_seconds=%u\n",AT_MIN_SECONDS,AT_MAX_SECONDS);return;
            }
        }
        if(!can.ready || !peer || (mcp_register(0x0e)&0xe0) || telemetry_queue.enabled) {
            LOG("REJECT reason=NORMAL_CAN_HELLO_AND_LTE_QUEUE_OFF_REQUIRED\n");return;
        }
        (void)at_enable(&auto_telem,(uint32_t)seconds,now_ms());auto_status();
    }
    else if(!strcmp(s,"uhf stop")) {
        ur_stop(&uhf_run,UR_STOPPED);LOG("UHF_RUN STOPPED outstanding=%u accepted_packets_may_finish=1\n",uc_count(&uhf_client));
    }
    else if(!strncmp(s,"uhf run ",8)) {
        unsigned duration,period;char extra;
        if(sscanf(s+8,"%u %u %c",&duration,&period,&extra)!=2 || target_lte || !can.ready || !peer ||
           (mcp_register(0x0e)&0xe0) || pending.active || output.active || can.pending ||
           uc_count(&uhf_client) || auto_telem.enabled || telemetry_queue.enabled ||
           !ur_start(&uhf_run,duration,period,now_ms())) {
            LOG("REJECT reason=RUN_RANGE_OR_LINK_BUSY duration=1..120 period=5..60\n");return;
        }
        ur_link_snapshot(&uhf_run,can.tx_fail,can.tx_timeout);
        LOG("UHF_RUN START duration_s=%u period_s=%u boot_resume=0\n",duration,period);
    }
    else if(!strcmp(s,"uhf lte firmware"))identity_telemetry(0);
    else if(!strcmp(s,"uhf modem firmware"))identity_telemetry(1);
    else if(!strcmp(s,"uhf devices"))device_telemetry();
    else if(!strcmp(s,"uhf heartbeat"))health_telemetry(false,2);
    else if(!strcmp(s,"uhf system"))health_telemetry(true,2);
    else if(!strcmp(s,"uhf eps"))eps_telemetry(2);
    else if(!strcmp(s,"heartbeat lte"))health_telemetry(false,true);
    else if(!strcmp(s,"system lte"))health_telemetry(true,true);
    else if(!strcmp(s,"eps lte"))eps_telemetry(true);
    else if(!strcmp(s,"eps enqueue"))eps_enqueue();
    else if(!strcmp(s,"lte queue status"))queue_status();
    else if(!strcmp(s,"lte queue on")) {telemetry_queue.enabled=true;queue_status();}
    else if(!strcmp(s,"lte queue off")) {
        telemetry_queue.enabled=false;
        if(queue_send_ready) {queue_send_ready=false;telemetry_queue.state=LQ_IDLE;}
        queue_status();
    } else if(!strcmp(s,"lte queue drop")) {
        if(!lq_drop(&telemetry_queue))LOG("REJECT reason=QUEUE_EMPTY_OR_ACTIVE\n");
        else queue_status();
    }
    else if(!strcmp(s,"lte firmware"))submit(UL_FIRMWARE_INFO,NULL,0);
    else if(!strcmp(s,"lte modem firmware"))submit(CF_MODEM_FIRMWARE,NULL,0);
    else if(!strcmp(s,"lte diagnostics"))submit(CF_LINK_DIAG,NULL,0);
    else if(!strcmp(s,"lte status"))submit(CF_LINK_STATUS,NULL,0);
    else if(!strncmp(s,"lte ",4)) {
        char *end;unsigned long seconds=strtoul(s+4,&end,10);
        if(!s[4] || *end || seconds>120) {LOG("REJECT reason=RF_WINDOW_RANGE\n");return;}
        uint8_t p[4];ul_p32(p,seconds);submit(CF_RF_WINDOW,p,4);
    }
#endif
    else if(!strcmp(s,"help"))LOG("COMMANDS version | status | selftest | normal | hello | ping N%s\n",ROLE_IHU?" | hello comms | hello lte | lte firmware | lte modem firmware | devices | devices scan | uhf run SECONDS PERIOD | uhf stop | uhf devices | uhf heartbeat | uhf system | uhf eps | telemetry | eps json | eps adc on/off | eps telemetry | telem on [seconds]/off/status | lte N | lte status | lte diagnostics | heartbeat lte | system lte | eps lte | eps enqueue | lte queue on/off/status/drop":"");
    else if(*s)LOG("ERROR unknown command\n");
}
int main(void) {
    stdio_init_all();boot=get_rand_32();if(!boot)boot=1;mcp_init(&can);
#if ROLE_IHU
    eps_bus_init();
    ember_init(&uplink_engine,boot);
#endif
    if(can.ready)(void)mcp_mode(&can,0);
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
        cf_expire(&fragments,now);pump_tx(now);
        for(unsigned i=0;i<UC_CAPACITY;i++) {
            uc_item *x=&uhf_client.items[i];
            if(x->active && (uint32_t)(now-x->started)>=UC_RESULT_MS) {
                LOG("UHF request=%" PRIu32 " outcome=UNKNOWN reason=RESULT_TIMEOUT ground_ack=0\n",x->packet.request);x->active=false;++unknown;
#if ROLE_IHU
                if(uhf_run.state==UR_RUNNING){ur_stop(&uhf_run,UR_FAULT);LOG("UHF_RUN FAULT result_timeout\n");}
#endif
            }
        }
        if(pending.active && (uint32_t)(now-pending.started)>=(pending.packet.type==CF_SEND_PACKET?REQUEST_TIMEOUT:5000)) {
            QUEUED_REPLY(NULL,false);
            LOG("RESULT request=%" PRIu32 " outcome=UNKNOWN reason=TIMEOUT\n",pending.packet.request);
            if(pending.packet.type==CF_UHF_SEND)for(unsigned i=0;i<UC_CAPACITY;i++)
                if(uhf_client.items[i].packet.request==pending.packet.request)uhf_client.items[i].active=false;
            pending.active=false;peer=0;++unknown;
        }
#if ROLE_IHU
        queue_pump(now_ms());
#endif
        for(unsigned i=0;i<40;++i) {
            int ch=getchar_timeout_us(0);if(ch==PICO_ERROR_TIMEOUT)break;
            if(ch=='\r' || ch=='\n') {if(discard)LOG("ERROR command too long\n");else {line[used]=0;command(line);}used=0;discard=false;}
            else if(!discard) {if(ch && used+1<sizeof(line))line[used++]=(char)ch;else discard=true;}
        }
#if ROLE_IHU
        // Process console off/status commands before considering a due read.
        auto_pump(now_ms());
        uhf_run_pump(now_ms());
        devices_pump(now_ms());
#endif
        if((uint32_t)(now-blink)>=500) {blink=now;led=!led;gpio_put(13,led);}sleep_us(500);
    }
}
