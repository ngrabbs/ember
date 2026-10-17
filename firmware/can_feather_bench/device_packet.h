#pragma once
#include "device_registry.h"
#include "wire.h"
/* Registry v1 fixes field order to EPS, EPS_NEXT, COMMS, LTE, PAYLOAD.
 * Never-seen age is UINT32_MAX; seen remains authoritative. */
static inline size_t device_packet(uint8_t *p,dr_status *devices,bool paused,
                                  uint32_t boot,uint16_t sequence,uint32_t now) {
    _Static_assert(DR_COUNT==5 && W_SIZE_DEVICE_STATUS==72,"Registry wire layout changed");
    size_t n=W_PAYLOAD+W_SIZE_DEVICE_STATUS+2;memset(p,0,n);
    ul_p16(p,W_TM_IDENTITY);ul_p16(p+2,0xc000|(sequence&0x3fff));ul_p16(p+4,n-7);
    p[W_SCHEMA_VERSION]=W_VERSION;p[W_KIND]=W_KINDS_TELEMETRY;
    ul_p16(p+W_MESSAGE_ID,W_ID_DEVICE_STATUS);
    p[W_SOURCE]=W_ENDPOINTS_IHU;p[W_TARGET]=W_ENDPOINTS_GROUND;
    ul_p32(p+W_SOURCE_BOOT_ID,boot);ul_p32(p+W_UPTIME_MS,now);
    ul_p16(p+W_PAYLOAD_LENGTH,W_SIZE_DEVICE_STATUS);
    uint8_t *q=p+W_PAYLOAD;*q++=1;*q++=paused;
    for(unsigned i=0;i<DR_COUNT;i++) {
        dr_status *s=&devices[i];dr_age(s,now);
        *q++=s->state;*q++=s->seen;
        ul_p32(q,s->seen?(uint32_t)(now-s->last_seen):UINT32_MAX);q+=4;
        ul_p32(q,s->boot);q+=4;ul_p32(q,s->timeouts);q+=4;
    }
    ul_p16(p+n-2,ul_crc(p,n-2));return n;
}
