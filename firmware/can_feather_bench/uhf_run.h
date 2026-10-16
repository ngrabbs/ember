#pragma once
#include <stdbool.h>
#include <stdint.h>
#include <string.h>
/* Volatile, explicit finite run. No boot enable, catch-up bursts, or retry. */
enum {UR_IDLE,UR_RUNNING,UR_EXPIRED,UR_STOPPED,UR_FAULT};
typedef struct {
    uint8_t state,stage;bool cycle;
    uint32_t started,duration,period,next,cycles,submitted,skipped;
} ur_state;
static inline bool ur_start(ur_state *s,uint32_t seconds,uint32_t period,uint32_t now) {
    if(s->state==UR_RUNNING || !seconds || seconds>120 || period<5 || period>60)return false;
    memset(s,0,sizeof(*s));s->state=UR_RUNNING;s->started=now;s->duration=seconds*1000;s->period=period*1000;return true;
}
static inline void ur_stop(ur_state *s,uint8_t state) {s->state=state;s->cycle=false;}
/* Returns next producer index0..2 only when transport has no outstanding work. */
static inline int ur_due(ur_state *s,uint32_t now,bool ready) {
    if(s->state!=UR_RUNNING)return -1;
    uint32_t elapsed=now-s->started;
    if(elapsed>=s->duration){ur_stop(s,UR_EXPIRED);return -1;}
    if(!ready)return -1;
    if(s->cycle && s->stage==3){s->cycle=false;s->stage=0;}
    if(!s->cycle) {
        if(elapsed<s->next)return -1;
        if(s->next && elapsed-s->next>=s->period)s->skipped+=(elapsed-s->next)/s->period;
        s->next=elapsed+s->period;s->cycle=true;s->stage=0;++s->cycles;
    }
    return s->stage;
}
static inline void ur_submitted(ur_state *s) {++s->stage;++s->submitted;}
