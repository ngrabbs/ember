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
#if ROLE_IHU
#include "eps_readout.h"
#endif
#define LOG(...) do {if(stdio_usb_connected())printf(__VA_ARGS__);} while(0)
#define ROLE_NAME (ROLE_IHU?"IHU_MCU":"COMMS_MCU")
#define TX_ID (ROLE_IHU?CF_IHU_ID:CF_COMMS_ID)
#define RX_ID (ROLE_IHU?CF_COMMS_ID:CF_IHU_ID)
#define REQUEST_TIMEOUT 5000
static mcp_state can;
static cf_reader fragments;
static ul_reader can_reader;
static uint32_t boot,peer,request_id,matched,unknown,busy_drops;
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
#endif
static uint32_t now_ms(void) {return to_ms_since_boot(get_absolute_time());}
static void status(void) {
    char id[2*PICO_UNIQUE_BOARD_ID_SIZE_BYTES+1];pico_get_unique_board_id_string(id,sizeof(id));
    LOG("STATUS role=%s fw=can-bench-v1 id=%s boot=%" PRIu32 " peer=%" PRIu32
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
static bool valid_heartbeat(const ul_packet *p) {
    const uint8_t *b=p->payload;size_t n=p->size;
    return n==W_PAYLOAD+W_SIZE_HEARTBEAT+2 && ul_u16(b)==W_TM_IDENTITY && (ul_u16(b+2)>>14)==3 &&
        (size_t)ul_u16(b+4)+7==n && b[W_SCHEMA_VERSION]==W_VERSION && b[W_KIND]==W_KINDS_TELEMETRY &&
        ul_u16(b+W_MESSAGE_ID)==W_ID_HEARTBEAT && b[W_SOURCE]==W_ENDPOINTS_IHU && b[W_TARGET]==W_ENDPOINTS_GROUND &&
        ul_u32(b+W_SOURCE_BOOT_ID)==p->sender && ul_u16(b+W_PAYLOAD_LENGTH)==W_SIZE_HEARTBEAT &&
        ul_crc(b,n-2)==ul_u16(b+n-2);
}
static void uart_submit(uint8_t type) {
    memset(&chain.uart,0,sizeof(chain.uart));chain.uart.version=1;chain.uart.type=type;
    chain.uart.sender=boot;chain.uart.origin=boot;chain.uart.request=++uart_id;
    if(type==UL_ECHO) {chain.uart.size=chain.incoming.size;memcpy(chain.uart.payload,chain.incoming.payload,chain.incoming.size);}
    uint8_t wire[UL_WIRE_MAX];size_t n=ul_encode(&chain.uart,wire);
    uart_putc_raw(uart0,0);uart_write_blocking(uart0,wire,n);chain.started=now_ms();
}
static void chain_fail(uint8_t reason) {
    send_error(&chain.incoming,reason);chain.active=false;walter_peer=0;++chain_unknown;
    LOG("CHAIN outcome=UNKNOWN reason=%u\n",reason);
}
static void uart_receive(const ul_packet *p) {
    if(!chain.active || p->version!=1 || p->origin!=boot || p->request!=chain.uart.request)return;
    bool hello=chain.uart.type==UL_HELLO;
    if(p->type!=(hello?UL_HELLO_ACK:UL_ECHO_ACK) || p->size!=chain.uart.size ||
       (!hello && p->sender!=walter_peer) || memcmp(p->payload,chain.uart.payload,p->size)) {
        chain_fail(CF_LINK_UNKNOWN);return;
    }
    if(hello) {walter_peer=p->sender;uart_submit(UL_ECHO);return;}
    ul_packet out=chain.incoming;out.type=CF_CHAIN_ACK;out.sender=boot;
    if(!queue(&out)) {chain_fail(CF_BUSY);return;}
    chain.active=false;++chain_ok;
    LOG("CHAIN request=%" PRIu32 " outcome=WALTER_BENCH_RETURN bytes=%u walter=%" PRIu32 "\n",out.request,out.size,walter_peer);
}
#endif
static void receive(const ul_packet *p) {
    if(pending.active && p->origin==boot && p->request==pending.packet.request) {
        bool hello=pending.packet.type==UL_HELLO;
        uint8_t expected=hello?UL_HELLO_ACK:pending.packet.type==CF_CHAIN?CF_CHAIN_ACK:UL_ECHO_ACK;
        if(p->version!=1 || (!hello && p->sender!=peer)) {
            pending.active=false;peer=0;++unknown;LOG("RESULT outcome=UNKNOWN reason=PEER_RESET_OR_VERSION\n");return;
        }
        if(p->type==UL_ERROR && p->size==1) {
            pending.active=false;
            bool uncertain=p->payload[0]==CF_LINK_UNKNOWN;
            if(uncertain) {++unknown;peer=0;}
            LOG("RESULT request=%" PRIu32 " outcome=%s reason=%u\n",p->request,uncertain?"UNKNOWN_REMOTE_LINK":"PEER_REJECTED",p->payload[0]);return;
        }
        if(p->type!=expected || p->size!=pending.packet.size || memcmp(p->payload,pending.packet.payload,p->size))return;
        if(hello)peer=p->sender;
        pending.active=false;++matched;
        LOG("RESULT request=%" PRIu32 " outcome=%s peer=%" PRIu32 " bytes=%u hex=",p->request,
            hello?"CAN_HELLO_CONFIRMED":p->type==CF_CHAIN_ACK?"WALTER_BENCH_RETURN":"CAN_ECHO_MATCHED",peer,p->size);
        for(size_t i=0;i<p->size;++i) {LOG("%02x",p->payload[i]);}
        LOG("\n");return;
    }
    if(p->type==UL_HELLO_ACK || p->type==UL_ECHO_ACK || p->type==CF_CHAIN_ACK || p->type==UL_ERROR)return;
    if(p->version!=1) {send_error(p,UL_ERR_VERSION);return;}
    if(p->origin!=p->sender) {send_error(p,UL_ERR_REQUEST);return;}
#if !ROLE_IHU
    if(p->type==CF_CHAIN) {
        if(chain.active || output.active || uart_id>=UINT32_MAX-1) {send_error(p,CF_BUSY);return;}
        if(!valid_heartbeat(p)) {send_error(p,CF_BAD_PACKET);return;}
        chain.active=true;chain.incoming=*p;uart_submit(walter_peer?UL_ECHO:UL_HELLO);return;
    }
#endif
    ul_packet reply;ul_reply(p,boot,&reply);if(!queue(&reply))++busy_drops;
}
static void submit(uint8_t type,const uint8_t *payload,size_t size) {
    if((mcp_register(0x0e)&0xe0)!=0) {LOG("REJECT reason=NORMAL_MODE_REQUIRED\n");return;}
    if(pending.active || output.active) {LOG("REJECT reason=BUSY\n");return;}
    if(type!=UL_HELLO && !peer) {LOG("REJECT reason=HELLO_REQUIRED\n");return;}
    if(request_id==UINT32_MAX) {LOG("REJECT reason=REQUEST_ID_EXHAUSTED\n");return;}
    memset(&pending.packet,0,sizeof(pending.packet));pending.packet.version=1;pending.packet.type=type;
    pending.packet.sender=boot;pending.packet.origin=boot;pending.packet.request=++request_id;
    pending.packet.size=(uint16_t)size;if(size)memcpy(pending.packet.payload,payload,size);
    if(!queue(&pending.packet)) {LOG("REJECT reason=QUEUE\n");return;}
    pending.active=true;pending.started=now_ms();LOG("SUBMITTED request=%" PRIu32 " type=%u bytes=%zu\n",request_id,type,size);
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
static void heartbeat(void) {
    uint8_t p[W_PAYLOAD+W_SIZE_HEARTBEAT+2]={0};size_t size=sizeof(p);
    ul_p16(p,W_TM_IDENTITY);ul_p16(p+2,(uint16_t)(0xc000|telemetry_sequence));
    telemetry_sequence=(uint16_t)((telemetry_sequence+1)&0x3fff);ul_p16(p+4,(uint16_t)(size-7));
    p[W_SCHEMA_VERSION]=W_VERSION;p[W_KIND]=W_KINDS_TELEMETRY;ul_p16(p+W_MESSAGE_ID,W_ID_HEARTBEAT);
    p[W_SOURCE]=W_ENDPOINTS_IHU;p[W_TARGET]=W_ENDPOINTS_GROUND;ul_p32(p+W_SOURCE_BOOT_ID,boot);
    ul_p32(p+W_UPTIME_MS,now_ms());ul_p16(p+W_PAYLOAD_LENGTH,W_SIZE_HEARTBEAT);
    p[W_PAYLOAD+W_HEARTBEAT_MODE]=W_MODE_SAFE;p[W_PAYLOAD+W_HEARTBEAT_CONFIGURATION]=W_CONFIGURATION_GROUND_TEST;
    ul_p32(p+W_PAYLOAD+W_HEARTBEAT_TELEMETRY_PERIOD_MS,0); // Manual emission, not a periodic scheduler.
    ul_p16(p+size-2,ul_crc(p,size-2));submit(CF_CHAIN,p,size);
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
    else if(!strcmp(s,"telemetry"))heartbeat();
    else if(!strcmp(s,"eps json"))eps_json();
#endif
    else if(!strcmp(s,"help"))LOG("COMMANDS status | selftest | normal | hello | ping N%s\n",ROLE_IHU?" | telemetry | eps json":"");
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
        if(chain.active && (uint32_t)(now-chain.started)>=UL_REQUEST_MS)chain_fail(CF_LINK_UNKNOWN);
#endif
        for(unsigned i=0;i<2 && mcp_receive(&can,&frame);++i) {
            if(loopback_test && frame.id==0x712) {
                const uint8_t expected[8]={0x45,0x4d,0x42,0x45,0x52,0,0x55,0xaa};
                LOG("SELFTEST outcome=%s kind=LOCAL_LOOPBACK\n",frame.size==8 && !memcmp(frame.data,expected,8)?"PASS":"FAIL");
                loopback_test=false;
            } else if(cf_feed(&fragments,&frame,RX_ID,now) && envelope_from_fragments(now,&packet))receive(&packet);
        }
        cf_expire(&fragments,now);pump_tx(now);
        if(pending.active && (uint32_t)(now-pending.started)>=REQUEST_TIMEOUT) {
            LOG("RESULT request=%" PRIu32 " outcome=UNKNOWN reason=TIMEOUT\n",pending.packet.request);
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
