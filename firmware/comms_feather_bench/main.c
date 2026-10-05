#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "pico/stdlib.h"
#include "pico/unique_id.h"
#include "pico/rand.h"
#include "hardware/uart.h"
#include "uart_link.h"

static uint32_t boot,peer,next_request,tx_bytes,rx_bytes,matched,rejected,unknown,unsolicited;
static ul_reader reader;
static struct {bool active;ul_packet packet;uint32_t started;} pending;
static uint32_t now_ms(void) {return to_ms_since_boot(get_absolute_time());}
static void status(void) {
    char id[2*PICO_UNIQUE_BOARD_ID_SIZE_BYTES+1];pico_get_unique_board_id_string(id,sizeof(id));
    printf("STATUS role=COMMS_MCU board=CAN_FEATHER fw=uart-framed-v1 id=%s boot=%" PRIu32
           " peer=%" PRIu32 " tx=0 rx=1 baud=115200 tx_bytes=%" PRIu32 " rx_bytes=%" PRIu32
           " matched=%" PRIu32 " rejected=%" PRIu32 " unknown=%" PRIu32 " unsolicited=%" PRIu32
           " pending=%d cobs=%" PRIu32 " crc=%" PRIu32 " format=%" PRIu32 " overflow=%" PRIu32
           " gaps=%" PRIu32 " uptime_ms=%" PRIu32 "\n",id,boot,peer,tx_bytes,rx_bytes,matched,rejected,
           unknown,unsolicited,pending.active,reader.framing_errors,reader.crc_errors,reader.format_errors,
           reader.overflows,reader.gaps,now_ms());
}
static void transmit(const uint8_t *wire,size_t size) {
    uart_putc_raw(uart0,0); // Discard partial boot chatter before this envelope.
    uart_write_blocking(uart0,wire,size);tx_bytes+=(uint32_t)size+1;
}
static void submit(uint8_t type,const uint8_t *data,size_t size) {
    if(pending.active) {puts("REJECT reason=BUSY capacity=1");return;}
    if(type!=UL_HELLO && !peer) {puts("REJECT reason=HELLO_REQUIRED");return;}
    if(next_request==UINT32_MAX) {puts("REJECT reason=REQUEST_ID_EXHAUSTED reset_required=1");return;}
    memset(&pending.packet,0,sizeof(pending.packet));
    pending.packet.version=UL_VERSION;pending.packet.type=type;pending.packet.sender=boot;
    pending.packet.origin=boot;pending.packet.request=++next_request;pending.packet.size=(uint16_t)size;
    if(size)memcpy(pending.packet.payload,data,size);
    uint8_t wire[UL_WIRE_MAX];size_t n=ul_encode(&pending.packet,wire);
    pending.active=true;pending.started=now_ms();transmit(wire,n);
    printf("SUBMITTED request=%" PRIu32 " type=%u payload_bytes=%zu outcome=LOCAL_UART_WRITE\n",next_request,type,size);
}
static int hex_digit(char c) {
    if(c>='0' && c<='9')return c-'0';
    if(c>='a' && c<='f')return c-'a'+10;
    if(c>='A' && c<='F')return c-'A'+10;
    return -1;
}
static size_t parse_hex(const char *s,uint8_t *out,size_t max) {
    size_t n=strlen(s);if(!n || n%2 || n/2>max)return 0;
    for(size_t i=0;i<n/2;++i) {int a=hex_digit(s[2*i]),b=hex_digit(s[2*i+1]);if(a<0 || b<0)return 0;out[i]=(uint8_t)((a<<4)|b);}
    return n/2;
}
static void command(const char *s) {
    if(!strcmp(s,"status"))status();
    else if(!strcmp(s,"hello"))submit(UL_HELLO,NULL,0);
    else if(!strcmp(s,"help"))puts("COMMANDS status | hello | echo N (1..240) | packet HEX | raw HEX (bench fault injection)");
    else if(!strncmp(s,"echo ",5)) {
        char *end;unsigned long n=strtoul(s+5,&end,10);
        if(!s[5] || *end || n<1 || n>UL_PAYLOAD_MAX) {puts("REJECT reason=SIZE");return;}
        uint8_t data[UL_PAYLOAD_MAX];for(size_t i=0;i<n;++i)data[i]=(uint8_t)i;submit(UL_ECHO,data,n);
    } else if(!strncmp(s,"packet ",7) || !strncmp(s,"raw ",4)) {
        bool raw=s[0]=='r';uint8_t bytes[UL_WIRE_MAX];size_t n=parse_hex(s+(raw?4:7),bytes,raw?UL_WIRE_MAX:UL_PAYLOAD_MAX);
        if(!n) {puts("REJECT reason=HEX_OR_SIZE");return;}
        if(raw) {if(pending.active)puts("REJECT reason=BUSY capacity=1");else {transmit(bytes,n);puts("RAW_SENT bench_only=1");}}
        else submit(UL_ECHO,bytes,n);
    } else if(*s)puts("ERROR unknown command");
}
static void receive(const ul_packet *p) {
    printf("RX_FRAME sender=%" PRIu32 " origin=%" PRIu32 " request=%" PRIu32 " type=%u size=%u hex=",
           p->sender,p->origin,p->request,p->type,p->size);
    for(size_t i=0;i<p->size;++i)printf("%02x",p->payload[i]);
    puts("");
    if(!pending.active || p->origin!=boot || p->request!=pending.packet.request) {
        ++unsolicited;puts("IGNORED reason=NO_MATCHING_REQUEST");return;
    }
    if(p->version!=UL_VERSION) {++unsolicited;puts("IGNORED reason=VERSION");return;}
    if(pending.packet.type!=UL_HELLO && p->sender!=peer) {
        ++unknown;pending.active=false;peer=0;puts("RESULT outcome=UNKNOWN reason=PEER_RESET hello_required=1");return;
    }
    bool hello=pending.packet.type==UL_HELLO;
    if(p->type==UL_ERROR && p->size==1) {
        ++rejected;pending.active=false;
        printf("RESULT request=%" PRIu32 " outcome=PEER_REJECTED reason=%u\n",p->request,p->payload[0]);return;
    }
    if(p->type!=(hello?UL_HELLO_ACK:UL_ECHO_ACK) || p->size!=pending.packet.size ||
       memcmp(p->payload,pending.packet.payload,p->size)) {
        ++unsolicited;puts("IGNORED reason=TYPE_OR_PAYLOAD_MISMATCH");return;
    }
    if(hello)peer=p->sender;
    ++matched;pending.active=false;
    printf("RESULT request=%" PRIu32 " outcome=%s peer=%" PRIu32 " payload_bytes=%u\n",
           p->request,hello?"HELLO_CONFIRMED":"BENCH_ECHO_MATCHED",peer,p->size);
}
int main(void) {
    stdio_init_all();boot=get_rand_32();if(!boot)boot=1;
    uart_init(uart0,115200);gpio_set_function(0,GPIO_FUNC_UART);gpio_set_function(1,GPIO_FUNC_UART);gpio_pull_up(1);
    uart_set_hw_flow(uart0,false,false);uart_set_format(uart0,8,1,UART_PARITY_NONE);uart_set_fifo_enabled(uart0,true);
    gpio_init(13);gpio_set_dir(13,GPIO_OUT);
    char line[560];size_t used=0;bool discard=false,led=false;uint32_t blink=0;
    puts("READY COMMS framed UART bench; modem control unavailable; type hello");
    while(true) {
        uint32_t now=now_ms();
        ul_packet packet;
        for(unsigned i=0;i<128 && uart_is_readable(uart0);++i) {
            uint8_t byte=uart_getc(uart0);++rx_bytes;if(ul_feed(&reader,byte,now,&packet))receive(&packet);
        }
        ul_expire(&reader,now);
        if(pending.active && (uint32_t)(now-pending.started)>=UL_REQUEST_MS) {
            printf("RESULT request=%" PRIu32 " outcome=UNKNOWN reason=TIMEOUT hello_required=1\n",pending.packet.request);
            pending.active=false;peer=0;++unknown;
        }
        for(unsigned i=0;i<128;++i) {
            int ch=getchar_timeout_us(0);if(ch==PICO_ERROR_TIMEOUT)break;
            if(ch=='\r' || ch=='\n') {if(discard)puts("ERROR command too long");else {line[used]=0;command(line);}used=0;discard=false;}
            else if(!discard) {if(ch && used+1<sizeof(line))line[used++]=(char)ch;else discard=true;}
        }
        if((uint32_t)(now-blink)>=500) {blink=now;led=!led;gpio_put(13,led);}sleep_ms(1);
    }
}
