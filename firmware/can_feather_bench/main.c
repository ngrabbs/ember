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
#include "native_telemetry.h"
#if ROLE_IHU
#include "eps_readout.h"
#include "power_packet.h"
#include "health_packet.h"
#include "lte_queue.h"
#include "autotelem.h"
#endif
#define LOG(...) do {if(stdio_usb_connected())printf(__VA_ARGS__);} while(0)
#define ROLE_NAME (ROLE_IHU?"IHU_MCU":"COMMS_MCU")
#define TX_ID (ROLE_IHU?CF_IHU_ID:CF_COMMS_ID)
#define RX_ID (ROLE_IHU?CF_COMMS_ID:CF_IHU_ID)
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
    uint16_t token;unsigned index;uint32_t last;
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
static void status(void) {
    char id[2*PICO_UNIQUE_BOARD_ID_SIZE_BYTES+1];pico_get_unique_board_id_string(id,sizeof(id));
    LOG("STATUS role=%s fw=can-bench-v3 id=%s boot=%" PRIu32 " peer=%" PRIu32
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
    LOG("\n");
}
static bool queue(const ul_packet *p) {
    if(output.active)return false;
    size_t size=ul_encode(p,output.wire);if(!size)return false;
    output.size=size;output.token=(uint16_t)p->request;output.index=0;output.last=now_ms()-2;output.active=true;return true;
}
static void pump_tx(uint32_t now) {
    uint32_t errors=can.tx_fail+can.tx_timeout;mcp_poll_tx(&can,now);
    if(can.tx_fail+can.tx_timeout!=errors) {
        output.active=false;LOG("CAN_TX outcome=UNKNOWN reason=FRAME_TX_FAILED\n");
        // Pending application request times out; a CAN hardware outcome is not an app result.
        return;
    }
    if(output.active && !can.pending && (uint32_t)(now-output.last)>=2) {
        cf_frame frame;
        if(!cf_fragment(output.wire,output.size,TX_ID,output.token,output.index,&frame)) {output.active=false;return;}
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
    return chain.incoming.type==CF_RF_WINDOW?UL_RF_WINDOW:chain.incoming.type==CF_SEND_PACKET?UL_SEND_PACKET:chain.incoming.type==CF_LINK_STATUS?UL_LINK_STATUS:chain.incoming.type==CF_LINK_DIAG?UL_LINK_DIAG:UL_ECHO;
}
static void uart_receive(const ul_packet *p) {
    if(!chain.active || p->version!=1 || p->origin!=boot || p->request!=chain.uart.request)return;
    bool hello=chain.uart.type==UL_HELLO;
    if(!hello && p->sender==walter_peer && p->type==UL_ERROR && p->size==1) {chain_fail(p->payload[0]);return;}
    uint8_t expected=hello?UL_HELLO_ACK:chain.uart.type==UL_RF_WINDOW?UL_RF_WINDOW_ACK:
        chain.uart.type==UL_SEND_PACKET?UL_MODEM_ACCEPTED:chain.uart.type==UL_LINK_STATUS?UL_LINK_STATUS_ACK:chain.uart.type==UL_LINK_DIAG?UL_LINK_DIAG_ACK:UL_ECHO_ACK;
    bool diag=chain.uart.type==UL_LINK_DIAG;
    bool health=chain.uart.type==UL_LINK_STATUS || diag;
    if(p->type!=expected || p->size!=(health?(diag?LTE_DIAG_SIZE:16):chain.uart.size) ||
       (!hello && p->sender!=walter_peer) || (!health && memcmp(p->payload,chain.uart.payload,p->size))) {
        chain_fail(CF_LINK_UNKNOWN);return;
    }
    if(hello) {walter_peer=p->sender;uart_submit(chain_uart_type());return;}
    ul_packet out=chain.incoming;out.type=out.type==CF_RF_WINDOW?CF_RF_WINDOW_ACK:
        out.type==CF_SEND_PACKET?CF_MODEM_ACCEPTED:out.type==CF_LINK_STATUS?CF_LINK_STATUS_ACK:out.type==CF_LINK_DIAG?CF_LINK_DIAG_ACK:CF_CHAIN_ACK;out.sender=boot;
    if(health) {out.size=p->size;memcpy(out.payload,p->payload,p->size);}
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
    if(pending.active && p->origin==boot && p->request==pending.packet.request) {
        bool hello=pending.packet.type==UL_HELLO;
        uint8_t expected=hello?UL_HELLO_ACK:pending.packet.type==CF_CHAIN?CF_CHAIN_ACK:
            pending.packet.type==CF_RF_WINDOW?CF_RF_WINDOW_ACK:pending.packet.type==CF_SEND_PACKET?CF_MODEM_ACCEPTED:pending.packet.type==CF_LINK_STATUS?CF_LINK_STATUS_ACK:pending.packet.type==CF_LINK_DIAG?CF_LINK_DIAG_ACK:UL_ECHO_ACK;
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
        bool diag=pending.packet.type==CF_LINK_DIAG;
        bool health=pending.packet.type==CF_LINK_STATUS || diag;
        if(p->type!=expected || p->size!=(health?(diag?LTE_DIAG_SIZE:16):pending.packet.size) || (!health && memcmp(p->payload,pending.packet.payload,p->size)))return;
        if(health)LOG("LTE_STATUS state=%u step=%u error=%u registered=%u window_ms=%" PRIu32 " modem_accepted=%" PRIu32 " rejected=%" PRIu32 "\n",p->payload[0],p->payload[1],p->payload[2],p->payload[3],ul_u32(p->payload+4),ul_u32(p->payload+8),ul_u32(p->payload+12));
        if(diag)LOG("LTE_DIAG version=%u last_cereg=%u send_cereg=%u failure_cereg=%u command=%u failure_command=%u failure_state=%u flags=%u cme=%" PRIu32 " send_elapsed_ms=%" PRIu32 " registration_losses=%" PRIu32 " last_cereg_ms=%" PRIu32 " uart_send_request=%" PRIu32 " error_kind=%u\n",
            p->payload[16],p->payload[17],p->payload[18],p->payload[19],p->payload[20],p->payload[21],p->payload[22],p->payload[23],ul_u32(p->payload+24),ul_u32(p->payload+28),ul_u32(p->payload+32),ul_u32(p->payload+36),ul_u32(p->payload+40),p->payload[45]);
        if(hello)peer=p->sender;
        QUEUED_REPLY(p,true);
        pending.active=false;++matched;
        LOG("RESULT request=%" PRIu32 " outcome=%s peer=%" PRIu32 " bytes=%u hex=",p->request,
            hello?"CAN_HELLO_CONFIRMED":p->type==CF_RF_WINDOW_ACK?"RF_WINDOW_ACCEPTED":
            p->type==CF_MODEM_ACCEPTED?"MODEM_ACCEPTED":p->type==CF_LINK_STATUS_ACK?"LTE_STATUS":p->type==CF_LINK_DIAG_ACK?"LTE_DIAG":p->type==CF_CHAIN_ACK?"WALTER_BENCH_RETURN":"CAN_ECHO_MATCHED",peer,p->size);
        for(size_t i=0;i<p->size;++i) {LOG("%02x",p->payload[i]);}
        LOG("\n");return;
    }
    if(p->type==UL_HELLO_ACK || p->type==UL_ECHO_ACK || p->type==CF_CHAIN_ACK ||
       p->type==CF_RF_WINDOW_ACK || p->type==CF_MODEM_ACCEPTED || p->type==CF_LINK_STATUS_ACK || p->type==CF_LINK_DIAG_ACK || p->type==UL_ERROR)return;
    if(p->version!=1) {send_error(p,UL_ERR_VERSION);return;}
    if(p->origin!=p->sender) {send_error(p,UL_ERR_REQUEST);return;}
#if !ROLE_IHU
    if(p->type==CF_CHAIN || p->type==CF_SEND_PACKET || p->type==CF_RF_WINDOW || p->type==CF_LINK_STATUS || p->type==CF_LINK_DIAG) {
        if(chain.active || output.active || uart_id>=UINT32_MAX-1) {send_error(p,CF_BUSY);return;}
        if(p->type==CF_RF_WINDOW?(p->size!=4 || ul_u32(p->payload)>120):(p->type==CF_LINK_STATUS || p->type==CF_LINK_DIAG)?p->size!=0:!valid_telemetry(p)) {send_error(p,CF_BAD_PACKET);return;}
        chain.active=true;chain.incoming=*p;uart_submit(walter_peer?chain_uart_type():UL_HELLO);return;
    }
#endif
    ul_packet reply;ul_reply(p,boot,&reply);if(!queue(&reply))++busy_drops;
}
static void submit(uint8_t type,const uint8_t *payload,size_t size) {
    if((mcp_register(0x0e)&0xe0)!=0) {++refused_requests;LOG("REJECT reason=NORMAL_MODE_REQUIRED\n");return;}
    if(pending.active || output.active) {++refused_requests;LOG("REJECT reason=BUSY\n");return;}
    if(type!=UL_HELLO && !peer) {++refused_requests;LOG("REJECT reason=HELLO_REQUIRED\n");return;}
    if(request_id==UINT32_MAX) {++refused_requests;LOG("REJECT reason=REQUEST_ID_EXHAUSTED\n");return;}
    memset(&pending.packet,0,sizeof(pending.packet));pending.packet.version=1;pending.packet.type=type;
    pending.packet.sender=boot;pending.packet.origin=boot;pending.packet.request=++request_id;
    pending.packet.size=(uint16_t)size;if(size)memcpy(pending.packet.payload,payload,size);
    if(!queue(&pending.packet)) {++refused_requests;LOG("REJECT reason=QUEUE\n");return;}
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
static bool eps_telemetry(bool lte) {
    if(pending.active || output.active || can.pending || !peer || (mcp_register(0x0e)&0xe0)) {
        LOG("REJECT reason=BUSY_OR_CAN_NOT_READY\n");return false;
    }
    ltc4162_raw_t raw;uint8_t failed=0;
    if(!eps_read(&raw,&failed)) {LOG("EPS_READ outcome=FAILED register=%02x reason=I2C_OR_PEC\n",failed);return false;}
    uint8_t packet[W_PAYLOAD+W_SIZE_POWER_STATUS+2];
    size_t n=power_packet(packet,&raw,boot,telemetry_sequence,now_ms(),++eps_readout_count);
    telemetry_sequence=(telemetry_sequence+1)&0x3fff;submit(lte?CF_SEND_PACKET:CF_CHAIN,packet,n);
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
static void health_telemetry(bool system,bool lte) {
    uint8_t packet[W_PAYLOAD+W_SIZE_SYSTEM_STATUS+2];
    size_t n=health_packet(packet,system,boot,telemetry_sequence,now_ms(),
        auto_telem.enabled?auto_telem.period_ms:0,admitted_requests,refused_requests);
    telemetry_sequence=(telemetry_sequence+1)&0x3fff;
    submit(lte?CF_SEND_PACKET:CF_CHAIN,packet,n);
}

#endif
static void selftest(void) {
    if(pending.active || output.active || can.pending) {LOG("REJECT reason=BUSY\n");return;}
    cf_frame frame={.id=0x712,.size=8,.data={0x45,0x4d,0x42,0x45,0x52,0,0x55,0xaa}};
    loopback_test=mcp_mode(&can,0x40) && mcp_send(&can,&frame);
    LOG("SELFTEST started=%d kind=LOCAL_LOOPBACK no_peer_proof=1\n",loopback_test);
}
static void command(const char *s) {
    if(!strcmp(s,"status"))status();
    else if(!strcmp(s,"selftest"))selftest();
    else if(!strcmp(s,"normal")) {
        if(pending.active || output.active || can.pending)LOG("REJECT reason=BUSY\n");
        else {bool ok=mcp_mode(&can,0);LOG("CAN_NORMAL ready=%d\n",ok);peer=0;}
    } else if(!strcmp(s,"hello"))submit(UL_HELLO,NULL,0);
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
    else if(!strcmp(s,"lte diagnostics"))submit(CF_LINK_DIAG,NULL,0);
    else if(!strcmp(s,"lte status"))submit(CF_LINK_STATUS,NULL,0);
    else if(!strncmp(s,"lte ",4)) {
        char *end;unsigned long seconds=strtoul(s+4,&end,10);
        if(!s[4] || *end || seconds>120) {LOG("REJECT reason=RF_WINDOW_RANGE\n");return;}
        uint8_t p[4];ul_p32(p,seconds);submit(CF_RF_WINDOW,p,4);
    }
#endif
    else if(!strcmp(s,"help"))LOG("COMMANDS status | selftest | normal | hello | ping N%s\n",ROLE_IHU?" | telemetry | eps json | eps adc on/off | eps telemetry | telem on [seconds]/off/status | lte N | lte status | lte diagnostics | heartbeat lte | system lte | eps lte | eps enqueue | lte queue on/off/status/drop":"");
    else if(*s)LOG("ERROR unknown command\n");
}
int main(void) {
    stdio_init_all();boot=get_rand_32();if(!boot)boot=1;mcp_init(&can);
#if ROLE_IHU
    eps_bus_init();
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
            if(loopback_test && frame.id==0x712) {
                const uint8_t expected[8]={0x45,0x4d,0x42,0x45,0x52,0,0x55,0xaa};
                LOG("SELFTEST outcome=%s kind=LOCAL_LOOPBACK\n",frame.size==8 && !memcmp(frame.data,expected,8)?"PASS":"FAIL");
                loopback_test=false;
            } else if(cf_feed(&fragments,&frame,RX_ID,now) && envelope_from_fragments(now,&packet))receive(&packet);
        }
        cf_expire(&fragments,now);pump_tx(now);
        if(pending.active && (uint32_t)(now-pending.started)>=(pending.packet.type==CF_SEND_PACKET?REQUEST_TIMEOUT:5000)) {
            QUEUED_REPLY(NULL,false);
            LOG("RESULT request=%" PRIu32 " outcome=UNKNOWN reason=TIMEOUT\n",pending.packet.request);
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
#endif
        if((uint32_t)(now-blink)>=500) {blink=now;led=!led;gpio_put(13,led);}sleep_us(500);
    }
}
