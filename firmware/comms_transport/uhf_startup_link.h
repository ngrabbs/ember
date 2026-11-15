#pragma once
#include "can_fragment.h"

/* Dedicated conducted-test route. Never enabled in normal firmware profiles. */
enum { BD_PROBE=0x750, BD_FIRE, BD_STOP, BD_READY, BD_RX, BD_FAILED, BD_KEEP,
       BD_UP_ID, BD_DOWN_ID, BD_TX_OK, BD_TX_FAILED, BD_LINK, BD_LINKED, BD_CONFIG_QUERY, BD_CONFIG_REPLY, BD_PROFILE_SET, BD_PROFILE_CONFIRM };
enum { BD_PACKET=0xb0, BD_CONFIG=0xb1, BD_PACKET_MAX=128, BD_HEARTBEAT_MS=10000,
       BD_TX_TIMEOUT_MS=3500 };
enum { BD_ANTENNA_MS=10000, BD_SILENCE_MS=15000, BD_ARM_MS=30000,
       BD_CW_LIMIT_MS=18000, BD_RX_TIMEOUT_MS=12000,
       BD_KEEP_PERIOD_MS=200, BD_KEEP_TIMEOUT_MS=750 };
static inline cf_frame bd_frame(unsigned id, uint32_t token, uint32_t radio_boot) {
    cf_frame f={.id=(uint16_t)id,.size=8};
    ul_p32(f.data,token);ul_p32(f.data+4,radio_boot);return f;
}
static inline bool bd_matches(const cf_frame *f,uint32_t token,uint32_t radio_boot) {
    return f->size==8 && token && ul_u32(f->data)==token &&
           ul_u32(f->data+4)==radio_boot;
}
typedef struct {uint32_t token,armed;bool spent;} bd_radio;
static inline bool bd_arm(bd_radio *s,uint32_t token,uint32_t now) {
    if(!token || s->spent || (s->token && s->token!=token))return false;
    if(!s->token){s->token=token;s->armed=now;}
    return (uint32_t)(now-s->armed)<BD_ARM_MS;
}
static inline bool bd_take(bd_radio *s,uint32_t now) {
    uint32_t elapsed=now-s->armed;
    if(s->spent || !s->token || elapsed<BD_SILENCE_MS || elapsed>=BD_ARM_MS)return false;
    s->spent=true;return true;
}
/* Opaque RF packet envelopes are addressed to the other boot. Validate only
 * transport framing here, leaving native packet semantics to the IHU. */
static inline bool bd_envelope(const cf_reader *f,ul_packet *out,uint32_t from,uint32_t to,uint8_t type){
    ul_reader r={0};unsigned count=0;
    for(size_t i=0;i<f->used;i++)if(ul_feed(&r,f->wire[i],0,out))++count;
    return count==1 && !r.used && !r.discard && !r.framing_errors && !r.format_errors &&
        !r.crc_errors && !r.overflows && out->version==1 && out->type==type &&
        out->sender==from && out->origin==to && out->request &&
        (uint16_t)out->request==f->token && out->size && out->size<=BD_PACKET_MAX;
}

static inline bool bd_packet(const cf_reader *f,ul_packet *out,uint32_t from,uint32_t to){
    return bd_envelope(f,out,from,to,BD_PACKET);
}
