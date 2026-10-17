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
#include "payload_protocol.h"
static uc_state uhf_client;
#include "native_telemetry.h"
#define LOG(...) do {if(stdio_usb_connected())printf(__VA_ARGS__);} while(0)
#define ROLE_NAME "WALTER_MCU"
#define TX_ID CF_LTE_REPLY_ID
#define RX_ID CF_LTE_REQUEST_ID
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
static ul_reader uart_reader;
static uint32_t walter_peer,uart_id,chain_ok,chain_unknown;
static struct {bool active;ul_packet incoming,uart;uint32_t started;} chain;
static uint32_t now_ms(void) {return to_ms_since_boot(get_absolute_time());}
static void firmware_status(void) {
    LOG("FIRMWARE role=%s version=%s git=%s dirty=%u boot=%" PRIu32 "\n",ROLE_NAME,FW_VERSION,FW_GIT,FW_DIRTY,boot);
}
static void status(void) {
    firmware_status();
    char id[2*PICO_UNIQUE_BOARD_ID_SIZE_BYTES+1];pico_get_unique_board_id_string(id,sizeof(id));
    LOG("STATUS role=%s fw=%s id=%s boot=%" PRIu32 " peer=%" PRIu32
        " can_ready=%d mode=%02x cnf=%02x,%02x,%02x bitrate=500000 tec=%u rec=%u eflg=%02x"
        " tx_ok=%" PRIu32 " tx_fail=%" PRIu32 " tx_timeout=%" PRIu32 " rx=%" PRIu32
        " rx_bad=%" PRIu32 " rx_overflow=%" PRIu32 " fragments_bad=%" PRIu32 " fragments_timeout=%" PRIu32
        " matched=%" PRIu32 " unknown=%" PRIu32 " busy_drops=%" PRIu32 " pending=%d uptime_ms=%" PRIu32,
        ROLE_NAME,FW_VERSION,id,boot,peer,can.ready,mcp_register(0x0e)&0xe0,mcp_register(0x2a),mcp_register(0x29),mcp_register(0x28),
        mcp_register(0x1c),mcp_register(0x1d),mcp_register(0x2d),can.tx_ok,can.tx_fail,can.tx_timeout,can.rx,
        can.rx_bad,can.rx_overflow,fragments.errors,fragments.timeouts,matched,unknown,busy_drops,pending.active,now_ms());
    LOG(" walter_peer=%" PRIu32 " chain_active=%d chain_ok=%" PRIu32 " chain_unknown=%" PRIu32,
        walter_peer,chain.active,chain_ok,chain_unknown);
    LOG(" uhf_pending=%u",uc_count(&uhf_client));
    LOG("\n");
}
static bool queue(const ul_packet *p) {
    if(output.active)return false;
    size_t size=ul_encode(p,output.wire);if(!size)return false;
    output.route=TX_ID;output.size=size;output.token=(uint16_t)p->request;output.index=0;output.last=now_ms()-2;output.active=true;return true;
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
static void receive_impl(const ul_packet *p) {
    if(p->type==CF_UHF_ADMITTED || p->type==CF_UHF_RESULT || p->type==CF_UHF_REJECTED) {
        if(!uc_receive(&uhf_client,p))return;
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
        if(hello)peer=p->sender;

        pending.active=false;++matched;
        LOG("RESULT request=%" PRIu32 " outcome=%s peer=%" PRIu32 " bytes=%u hex=",p->request,
            hello?"CAN_HELLO_CONFIRMED":fire?"PAYLOAD_FIRE_RESULT":payload_report?(p->type==PL_STATUS_ACK?"PAYLOAD_STATUS":"PAYLOAD_HEARTBEAT"):identity?"FIRMWARE_IDENTITY":p->type==CF_RF_WINDOW_ACK?"RF_WINDOW_ACCEPTED":
            p->type==CF_MODEM_ACCEPTED?"MODEM_ACCEPTED":p->type==CF_LINK_STATUS_ACK?"LTE_STATUS":p->type==CF_LINK_DIAG_ACK?"LTE_DIAG":p->type==CF_CHAIN_ACK?"WALTER_BENCH_RETURN":"CAN_ECHO_MATCHED",peer,p->size);
        for(size_t i=0;i<p->size;++i) {LOG("%02x",p->payload[i]);}
        LOG("\n");
        return;
    }
    if(p->type==UL_HELLO_ACK || p->type==UL_ECHO_ACK || p->type==CF_CHAIN_ACK ||
       p->type==CF_RF_WINDOW_ACK || p->type==CF_MODEM_ACCEPTED || p->type==CF_LINK_STATUS_ACK || p->type==CF_LINK_DIAG_ACK || p->type==UL_FIRMWARE_INFO_ACK || p->type==CF_MODEM_FIRMWARE_ACK || p->type==PL_STATUS_ACK || p->type==PL_HEARTBEAT_ACK || p->type==PL_FIRE_RESULT || p->type==UL_ERROR)return;
    if(p->version!=1) {send_error(p,UL_ERR_VERSION);return;}
    if(p->origin!=p->sender) {send_error(p,UL_ERR_REQUEST);return;}
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
    ul_packet reply;ul_reply(p,boot,&reply);if(!queue(&reply))++busy_drops;
}
static void receive(const ul_packet *p){
    receive_impl(p);
}
static void submit(uint8_t type,const uint8_t *payload,size_t size) {
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
    ++admitted_requests;pending.active=true;pending.started=now_ms();LOG("SUBMITTED request=%" PRIu32 " type=%u bytes=%zu\n",request_id,type,size);
}
static void selftest(void) {
    if(pending.active || output.active || can.pending) {LOG("REJECT reason=BUSY\n");return;}
    cf_frame frame={.id=0x712,.size=8,.data={0x45,0x4d,0x42,0x45,0x52,0,0x55,0xaa}};
    loopback_test=mcp_mode(&can,0x40) && mcp_send(&can,&frame);
    LOG("SELFTEST started=%d kind=LOCAL_LOOPBACK no_peer_proof=1\n",loopback_test);
}

static void command_impl(const char *s) {
    if(!strcmp(s,"version"))firmware_status();
    else if(!strcmp(s,"status"))status();
    else if(!strcmp(s,"selftest"))selftest();
    else if(!strcmp(s,"normal")) {
        if(pending.active || output.active || can.pending || uc_count(&uhf_client))LOG("REJECT reason=BUSY\n");
        else {bool ok=mcp_mode(&can,0);LOG("CAN_NORMAL ready=%d\n",ok);peer=0;}
    }
    else if(!strcmp(s,"hello"))submit(UL_HELLO,NULL,0);
    else if(!strncmp(s,"ping ",5)) {
        char *end;unsigned long n=strtoul(s+5,&end,10);
        if(!s[5] || *end || !n || n>240) {LOG("REJECT reason=SIZE\n");return;}
        uint8_t p[240];for(size_t i=0;i<n;++i)p[i]=(uint8_t)i;submit(UL_ECHO,p,n);
}
    else if(!strcmp(s,"help"))LOG("COMMANDS version | status | selftest | normal | hello | ping N%s\n","");
    else if(*s)LOG("ERROR unknown command\n");
}
static void command(const char *s){
    command_impl(s);
}
int main(void) {
    stdio_init_all();boot=get_rand_32();if(!boot)boot=1;mcp_init(&can);
    if(can.ready)(void)mcp_mode(&can,0);
    uart_init(uart0,115200);gpio_set_function(0,GPIO_FUNC_UART);gpio_set_function(1,GPIO_FUNC_UART);
    gpio_pull_up(1);uart_set_hw_flow(uart0,false,false);uart_set_format(uart0,8,1,UART_PARITY_NONE);uart_set_fifo_enabled(uart0,true);
    gpio_init(13);gpio_set_dir(13,GPIO_OUT);char line[40];size_t used=0;bool discard=false,led=false;uint32_t blink=0;
    while(true) {
        uint32_t now=now_ms();ul_packet packet;cf_frame frame;
        for(unsigned i=0;i<128 && uart_is_readable(uart0);++i) {
            uint8_t ch=uart_getc(uart0);if(ul_feed(&uart_reader,ch,now,&packet))uart_receive(&packet);
        }
        // HELLO handling can synchronously start an ECHO and set started to a
        // newer time. Refresh before unsigned subtraction or the stale loop
        // timestamp would look like a full timer wrap and expire the new request.
        now=now_ms();
        ul_expire(&uart_reader,now);
        if(chain.active && (uint32_t)(now-chain.started)>=(chain.uart.type==UL_SEND_PACKET?17000:UL_REQUEST_MS))chain_fail(CF_LINK_UNKNOWN);
        for(unsigned i=0;i<2 && mcp_receive(&can,&frame);++i) {
            if(frame.id==DR_QUERY_ID) {
                cf_frame response;
                if(!can.pending && !output.active && dr_respond(&frame,DR_LTE_NODE,boot,&response))
                    (void)mcp_send(&can,&response);
                continue;
            }
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
                LOG("UHF request=%" PRIu32 " outcome=UNKNOWN reason=RESULT_TIMEOUT ground_ack=0\n",x->packet.request);x->active=false;++unknown;
            }
        }
        if(pending.active && (uint32_t)(now-pending.started)>=(pending.packet.type==CF_SEND_PACKET?REQUEST_TIMEOUT:5000)) {

            LOG("RESULT request=%" PRIu32 " outcome=UNKNOWN reason=TIMEOUT\n",pending.packet.request);
            if(uhf_is_request(pending.packet.type))for(unsigned i=0;i<UC_CAPACITY;i++)
                if(uhf_client.items[i].packet.request==pending.packet.request)uhf_client.items[i].active=false;
            pending.active=false;peer=0;++unknown;
        }
        for(unsigned i=0;i<40;++i) {
            int ch=getchar_timeout_us(0);if(ch==PICO_ERROR_TIMEOUT)break;
            if(ch=='\r' || ch=='\n') {if(discard)LOG("ERROR command too long\n");else {line[used]=0;command(line);}used=0;discard=false;}
            else if(!discard) {if(ch && used+1<sizeof(line))line[used++]=(char)ch;else discard=true;}
        }
        if((uint32_t)(now-blink)>=500) {blink=now;led=!led;gpio_put(13,led);}sleep_us(500);
    }
}
