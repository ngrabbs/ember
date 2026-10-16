#pragma once
#include "uhf_link.h"
#define UC_CAPACITY 4
#define UC_RESULT_MS 30000u
typedef struct {bool active,admitted;uint32_t peer,started;ul_packet packet;} uc_item;
typedef struct {uc_item items[UC_CAPACITY];} uc_state;
static inline unsigned uc_count(const uc_state *s) {
    unsigned n=0;for(unsigned i=0;i<UC_CAPACITY;i++)n+=s->items[i].active;return n;
}
static inline bool uc_start(uc_state *s,const ul_packet *p,uint32_t peer,uint32_t now) {
    if(!peer)return false;
    for(unsigned i=0;i<UC_CAPACITY;i++)if(!s->items[i].active) {
        s->items[i]=(uc_item){.active=true,.peer=peer,.started=now,.packet=*p};return true;
    }
    return false;
}
static inline bool uc_receive(uc_state *s,const ul_packet *reply) {
    if(reply->type!=CF_UHF_ADMITTED && reply->type!=CF_UHF_RESULT && reply->type!=CF_UHF_REJECTED)return false;
    uint8_t status=reply->payload[1];
    if((reply->type==CF_UHF_ADMITTED && status!=UHF_OK) ||
       (reply->type==CF_UHF_RESULT && status!=UHF_OK && status!=UHF_FAILED && status!=UHF_CANCELLED) ||
       (reply->type==CF_UHF_REJECTED && (status!=UHF_DISABLED && (status<UHF_FULL || status>UHF_CONFLICT))))return false;
    for(unsigned i=0;i<UC_CAPACITY;i++) {
        uc_item *x=&s->items[i];
        if(!x->active || !uhf_matches(reply,&x->packet,x->peer))continue;
        if(reply->type==CF_UHF_ADMITTED)x->admitted=true;else x->active=false;
        return true;
    }
    return false;
}
