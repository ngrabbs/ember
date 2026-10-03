#ifndef EMBER_LTE_QUEUE_H
#define EMBER_LTE_QUEUE_H
#include "uart_link.h"
#include "lte_link.h"
/* Bench policy: volatile FIFO, explicit RF windows, modem acceptance only.
 * Never replay an ambiguous submission. Retain held packets for inspection. */
#define LQ_CAPACITY 4
#define LQ_MAX_ATTEMPTS 3
#define LQ_MAX_AGE_MS 300000u
enum {LQ_IDLE, LQ_STATUS, LQ_SEND, LQ_HELD};
enum {LQ_HOLD_NONE, LQ_HOLD_UNKNOWN, LQ_HOLD_REJECTED, LQ_HOLD_EXHAUSTED, LQ_HOLD_EXPIRED};
typedef struct {
    uint8_t bytes[UL_PAYLOAD_MAX];uint16_t size;
    uint32_t captured;uint8_t attempts;
} lq_packet;
typedef struct {
    lq_packet packets[LQ_CAPACITY];unsigned head,count;
    uint8_t state,hold;bool enabled;
    uint32_t next,accepted,full,retries;
} lq_state;
static inline bool lq_due(uint32_t now,uint32_t when) {return (int32_t)(now-when)>=0;}
static inline lq_packet *lq_front(lq_state *q) {return q->count?&q->packets[q->head]:NULL;}
static inline bool lq_push(lq_state *q,const uint8_t *p,size_t n,uint32_t now) {
    if(!n || n>UL_PAYLOAD_MAX)return false;
    if(q->count==LQ_CAPACITY) {++q->full;return false;}
    lq_packet *slot=&q->packets[(q->head+q->count)%LQ_CAPACITY];
    memcpy(slot->bytes,p,n);slot->size=(uint16_t)n;slot->captured=now;slot->attempts=0;
    if(!q->count)q->next=now;
    ++q->count;return true;
}
static inline void lq_hold(lq_state *q,uint8_t reason) {q->state=LQ_HELD;q->hold=reason;}
static inline bool lq_poll(lq_state *q,uint32_t now) {
    if(!q->enabled || !q->count || q->state!=LQ_IDLE)return false;
    if((uint32_t)(now-lq_front(q)->captured)>=LQ_MAX_AGE_MS) {lq_hold(q,LQ_HOLD_EXPIRED);return false;}
    if(!lq_due(now,q->next))return false;
    q->state=LQ_STATUS;return true;
}
static inline bool lq_status(lq_state *q,const uint8_t *status,uint32_t now) {
    if(q->state!=LQ_STATUS || !q->count)return false;
    // READY, currently registered, and enough time for the bounded send.
    if(status[0]!=6 || status[3]!=1 || ul_u32(status+4)<16000) {
        q->state=LQ_IDLE;q->next=now+2000;return false;
    }
    if(lq_front(q)->attempts>=LQ_MAX_ATTEMPTS) {lq_hold(q,LQ_HOLD_EXHAUSTED);return false;}
    ++lq_front(q)->attempts;q->state=LQ_SEND;return true;
}
static inline void lq_result(lq_state *q,uint8_t reason,uint32_t now) {
    if(q->state!=LQ_SEND || !q->count)return;
    if(!reason) {
        ++q->accepted;q->head=(q->head+1)%LQ_CAPACITY;--q->count;
        q->state=LQ_IDLE;q->hold=LQ_HOLD_NONE;q->next=now+1000;
    } else if(reason==UL_ERR_NOT_READY || reason==UL_ERR_BUSY) {
        // These explicit responses occur before modem submission.
        if(lq_front(q)->attempts>=LQ_MAX_ATTEMPTS)lq_hold(q,LQ_HOLD_EXHAUSTED);
        else {++q->retries;q->state=LQ_IDLE;q->next=now+(1000u<<lq_front(q)->attempts);}
    } else lq_hold(q,reason==UL_ERR_MODEM_REJECTED?LQ_HOLD_REJECTED:LQ_HOLD_UNKNOWN);
}
static inline bool lq_drop(lq_state *q) {
    if(!q->count || q->state==LQ_STATUS || q->state==LQ_SEND)return false;
    q->head=(q->head+1)%LQ_CAPACITY;--q->count;q->state=LQ_IDLE;q->hold=0;
    if(q->count)q->next=lq_front(q)->captured;
    return true;
}
#endif
