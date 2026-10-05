#ifndef EMBER_UART_LINK_H
#define EMBER_UART_LINK_H
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <string.h>
/* Bench protocol v1: all multibyte fields are big endian. No modem semantics. */
#define UL_VERSION 1
#define UL_PAYLOAD_MAX 240
#define UL_HEADER 18
#define UL_RAW_MAX (UL_HEADER + UL_PAYLOAD_MAX + 2)
#define UL_ENCODED_MAX (UL_RAW_MAX + UL_RAW_MAX / 254 + 1)
#define UL_WIRE_MAX (UL_ENCODED_MAX + 1)
#define UL_HELLO 1
#define UL_HELLO_ACK 2
#define UL_ECHO 0x70
#define UL_ECHO_ACK 0x71
#define UL_ERROR 0x7f
#define UL_ERR_VERSION 1
#define UL_ERR_TYPE 2
#define UL_ERR_REQUEST 3
#define UL_ERR_PAYLOAD 4
#define UL_GAP_MS 250
#define UL_REQUEST_MS 2000

typedef struct {
    uint8_t version, type;
    uint32_t sender, origin, request;
    uint16_t size;
    uint8_t payload[UL_PAYLOAD_MAX];
} ul_packet;
typedef struct {
    uint8_t data[UL_ENCODED_MAX];
    size_t used;
    bool discard;
    uint32_t last, framing_errors, crc_errors, format_errors, overflows, gaps;
} ul_reader;
static inline uint16_t ul_u16(const uint8_t *p) { return (uint16_t)((p[0]<<8)|p[1]); }
static inline uint32_t ul_u32(const uint8_t *p) { return ((uint32_t)ul_u16(p)<<16)|ul_u16(p+2); }
static inline void ul_p16(uint8_t *p,uint16_t v) { p[0]=(uint8_t)(v>>8);p[1]=(uint8_t)v; }
static inline void ul_p32(uint8_t *p,uint32_t v) { ul_p16(p,(uint16_t)(v>>16));ul_p16(p+2,(uint16_t)v); }
static inline uint16_t ul_crc(const uint8_t *p,size_t n) {
    uint16_t c=0xffff;
    for(size_t i=0;i<n;++i) { c^=(uint16_t)p[i]<<8;for(unsigned j=0;j<8;++j)c=(uint16_t)((c&0x8000)?(c<<1)^0x1021:c<<1); }
    return c;
}
/* Full COBS, including 0xff blocks (unlike the smaller USB bench profile). */
static inline size_t ul_cobs_encode(const uint8_t *p,size_t n,uint8_t *out) {
    size_t at=0,w=1;uint8_t code=1;
    for(size_t i=0;i<n;++i) {
        if(!p[i]) { out[at]=code;at=w++;code=1; }
        else { out[w++]=p[i];if(++code==255) {out[at]=code;at=w++;code=1;} }
    }
    out[at]=code;return w;
}
static inline size_t ul_cobs_decode(const uint8_t *p,size_t n,uint8_t *out) {
    size_t i=0,w=0;
    while(i<n) {
        uint8_t c=p[i++];
        if(!c || i+(size_t)c-1>n)return 0;
        for(unsigned j=1;j<c;++j) { if(!p[i] || w==UL_RAW_MAX)return 0;out[w++]=p[i++]; }
        if(c!=255 && i<n) {if(w==UL_RAW_MAX)return 0;out[w++]=0;}
    }
    return w;
}
static inline size_t ul_encode(const ul_packet *p,uint8_t *wire) {
    if(p->size>UL_PAYLOAD_MAX || !p->sender || !p->origin || !p->request)return 0;
    uint8_t raw[UL_RAW_MAX];raw[0]=0x45;raw[1]=0x55;raw[2]=p->version;raw[3]=p->type;
    ul_p32(raw+4,p->sender);ul_p32(raw+8,p->origin);ul_p32(raw+12,p->request);ul_p16(raw+16,p->size);
    memcpy(raw+UL_HEADER,p->payload,p->size);size_t n=UL_HEADER+p->size;
    ul_p16(raw+n,ul_crc(raw,n));size_t w=ul_cobs_encode(raw,n+2,wire);wire[w++]=0;return w;
}
static inline void ul_expire(ul_reader *r,uint32_t now) {
    if(r->used && (uint32_t)(now-r->last)>=UL_GAP_MS) {r->used=0;r->discard=true;++r->gaps;}
}
/* True only for a structurally intact CRC-verified envelope. Version/type
 * are checked by the service, permitting correlated explicit rejection. */
static inline bool ul_feed(ul_reader *r,uint8_t ch,uint32_t now,ul_packet *p) {
    ul_expire(r,now);r->last=now;
    if(ch) {
        if(!r->discard) {
            if(r->used==UL_ENCODED_MAX) {r->used=0;r->discard=true;++r->overflows;}
            else r->data[r->used++]=ch;
        }
        return false;
    }
    if(r->discard || !r->used) {r->used=0;r->discard=false;return false;}
    uint8_t raw[UL_RAW_MAX];size_t n=ul_cobs_decode(r->data,r->used,raw);r->used=0;
    if(!n) {++r->framing_errors;return false;}
    if(n<UL_HEADER+2 || raw[0]!=0x45 || raw[1]!=0x55 || ul_u16(raw+16)>UL_PAYLOAD_MAX ||
       n!=(size_t)UL_HEADER+ul_u16(raw+16)+2 || !ul_u32(raw+4) || !ul_u32(raw+8) || !ul_u32(raw+12)) {
        ++r->format_errors;return false;
    }
    if(ul_crc(raw,n-2)!=ul_u16(raw+n-2)) {++r->crc_errors;return false;}
    p->version=raw[2];p->type=raw[3];p->sender=ul_u32(raw+4);p->origin=ul_u32(raw+8);
    p->request=ul_u32(raw+12);p->size=ul_u16(raw+16);memcpy(p->payload,raw+UL_HEADER,p->size);return true;
}
/* Stateless, idempotent bench responder: repeats echo bytes without executing
 * commands. Replies retain origin/request and expose the responder boot ID. */
static inline void ul_reply(const ul_packet *in,uint32_t boot,ul_packet *out) {
    memset(out,0,sizeof(*out));out->version=UL_VERSION;out->sender=boot;out->origin=in->origin;out->request=in->request;
    uint8_t reason=0;
    if(in->version!=UL_VERSION)reason=UL_ERR_VERSION;
    else if(in->type!=UL_HELLO && in->type!=UL_ECHO)reason=UL_ERR_TYPE;
    else if(in->origin!=in->sender)reason=UL_ERR_REQUEST;
    else if((in->type==UL_HELLO && in->size) || (in->type==UL_ECHO && !in->size))reason=UL_ERR_PAYLOAD;
    if(reason) {out->type=UL_ERROR;out->size=1;out->payload[0]=reason;}
    else if(in->type==UL_HELLO)out->type=UL_HELLO_ACK;
    else {out->type=UL_ECHO_ACK;out->size=in->size;memcpy(out->payload,in->payload,in->size);}
}
#endif
