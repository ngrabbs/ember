#pragma once
#include "uart_link.h"
/* Dedicated UHF bench semantics: neither LTE acceptance nor ground delivery. */
#define CF_UHF_SEND 0x80
#define CF_UHF_ADMITTED 0x81
#define CF_UHF_RESULT 0x82
#define CF_UHF_REJECTED 0x83
/* Zero-payload request: COMMS constructs its own native firmware packet. */
#define CF_UHF_FIRMWARE 0x84
static inline bool uhf_is_request(uint8_t type) {
    return type==CF_UHF_SEND || type==CF_UHF_FIRMWARE;
}
#define UHF_OK 0
#define UHF_FULL 1
#define UHF_INVALID 2
#define UHF_STALE 3
#define UHF_CONFLICT 4
#define UHF_FAILED 5
#define UHF_CANCELLED 6
#define UHF_DISABLED 7
#define UHF_REPLY_SIZE 8
static inline uint32_t uhf_digest(const uint8_t *p,size_t n) {
    uint32_t c=0xffffffff;while(n--){c^=*p++;for(unsigned i=0;i<8;i++)c=(c>>1)^((c&1)?0xedb88320:0);}return c^0xffffffff;
}
static inline void uhf_reply(const ul_packet *in,uint32_t boot,uint8_t type,uint8_t status,ul_packet *out) {
    memset(out,0,sizeof(*out));out->version=1;out->type=type;out->sender=boot;
    out->origin=in->origin;out->request=in->request;out->size=UHF_REPLY_SIZE;
    out->payload[0]=1;out->payload[1]=status;ul_p16(out->payload+2,in->size);
    ul_p32(out->payload+4,uhf_digest(in->payload,in->size));
}
static inline bool uhf_matches(const ul_packet *reply,const ul_packet *sent,uint32_t peer) {
    return reply->version==1 && peer && reply->sender==peer && reply->origin==sent->origin &&
        reply->request==sent->request && reply->size==UHF_REPLY_SIZE && reply->payload[0]==1 &&
        ul_u16(reply->payload+2)==sent->size && ul_u32(reply->payload+4)==uhf_digest(sent->payload,sent->size);
}
