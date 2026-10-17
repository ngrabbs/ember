#pragma once
#include "uart_link.h"
/* Payload v1 diagnostic services. HELLO/ECHO and firmware identity reuse UL. */
#define PL_STATUS 0x94
#define PL_STATUS_ACK 0x95
#define PL_HEARTBEAT 0x96
#define PL_HEARTBEAT_ACK 0x97
#define PL_FIRE_CHECK 0x98
#define PL_FIRE_RESULT 0x99
#define PL_FIRE_SIZE 16u
/* version, result (0=no fire,1=fire), mode (1=stub,2=algorithm), reserved,
 * then big endian boot, uptime_ms, nonzero check_id. */
static inline bool pl_fire_valid(const uint8_t *p,size_t n,uint32_t boot) {
    return n==PL_FIRE_SIZE && p[0]==1 && p[1]<=1 && (p[2]==1 || p[2]==2) && !p[3] &&
        boot && ul_u32(p+4)==boot && ul_u32(p+12);
}
#define PL_REPORT_SIZE 28u
/* Big endian: version8, node8, ready8, reserved8, then uint32 boot,
 * daemon uptime_ms, requests, replies queued, rejections, fragment errors.
 * A heartbeat is requested, never emitted unsolicited. */
static inline bool pl_report_valid(const uint8_t *p,size_t n,uint32_t boot) {
    return n==PL_REPORT_SIZE && p[0]==1 && p[1]==4 && p[2]==1 && !p[3] &&
        boot && ul_u32(p+4)==boot;
}
