#pragma once
#include <stdbool.h>
#include <stdint.h>

/* Optional millisecond cadence. No catch-up queue, I/O, or receiver knowledge. */
#define AT_DEFAULT_SECONDS 20u
#define AT_MIN_SECONDS 5u
#define AT_MAX_SECONDS 3600u
typedef struct {
    bool enabled;
    uint32_t period_ms, next_ms, due, skipped, submitted, failed;
} at_state;
typedef enum {AT_NONE, AT_SKIP, AT_READ} at_action;

static inline bool at_enable(at_state *s, uint32_t seconds, uint32_t now) {
    if(seconds<AT_MIN_SECONDS || seconds>AT_MAX_SECONDS)return false;
    s->period_ms=seconds*1000u;s->next_ms=now+s->period_ms;s->enabled=true;
    return true;
}
static inline void at_disable(at_state *s) {s->enabled=false;}
static inline bool at_due(const at_state *s, uint32_t now) {
    return s->enabled && (uint32_t)(now-s->next_ms)<UINT32_C(0x80000000);
}
static inline at_action at_poll(at_state *s, uint32_t now, bool idle) {
    /* The configured interval is well below half of the uint32 clock range. */
    if(!at_due(s,now))return AT_NONE;
    s->next_ms=now+s->period_ms;++s->due;
    if(!idle) {++s->skipped;return AT_SKIP;}
    return AT_READ;
}
