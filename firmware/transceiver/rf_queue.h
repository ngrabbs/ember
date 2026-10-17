#pragma once
#include "uhf_link.h"
#define RQ_CAPACITY 4
#define RQ_HISTORY 8
/* Single owner. Bounded volatile queue; no automatic retry after uncertain RF. */
typedef struct {ul_packet packet;uint8_t status;} rq_item;
typedef struct {
    rq_item items[RQ_CAPACITY],history[RQ_HISTORY];
    unsigned count,history_count,history_next;
    uint32_t origin,highwater;
} rq_state;
static inline void rq_finish(rq_state *q,uint8_t status) {
    if(!q->count)return;
    q->history[q->history_next]=q->items[0];q->history[q->history_next].status=status;
    q->history_next=(q->history_next+1)%RQ_HISTORY;
    if(q->history_count<RQ_HISTORY)q->history_count++;
    memmove(q->items,q->items+1,(--q->count)*sizeof(q->items[0]));
}
static inline uint8_t rq_admit(rq_state *q,const ul_packet *p,uint8_t *status) {
    *status=UHF_OK;
    if(!p->origin || !p->request){*status=UHF_INVALID;return CF_UHF_REJECTED;}
    if(q->origin!=p->origin) {
        if(q->count){*status=UHF_FULL;return CF_UHF_REJECTED;}
        memset(q,0,sizeof(*q));q->origin=p->origin;
    }
    for(unsigned group=0;group<2;group++)for(unsigned i=0;i<(group?q->history_count:q->count);i++) {
        rq_item *item=group?&q->history[i]:&q->items[i];
        if(item->packet.request!=p->request)continue;
        if(item->packet.type!=p->type || item->packet.size!=p->size || memcmp(item->packet.payload,p->payload,p->size)) {
            *status=UHF_CONFLICT;return CF_UHF_REJECTED;
        }
        *status=item->status;return group?CF_UHF_RESULT:CF_UHF_ADMITTED;
    }
    if(p->request<=q->highwater){*status=UHF_STALE;return CF_UHF_REJECTED;}
    if(q->count==RQ_CAPACITY){*status=UHF_FULL;return CF_UHF_REJECTED;}
    q->items[q->count++]=(rq_item){.packet=*p,.status=UHF_OK};q->highwater=p->request;
    return CF_UHF_ADMITTED;
}
