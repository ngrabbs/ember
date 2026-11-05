#pragma once
#include "can_fragment.h"

/* Dedicated conducted-test route. Never enabled in normal firmware profiles. */
enum { BD_PROBE=0x750, BD_FIRE, BD_STOP, BD_READY, BD_RX, BD_FAILED, BD_KEEP };
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
