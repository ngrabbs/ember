#pragma once
#include "can_fragment.h"
/* Additive development discovery; never authorizes RF or changes a device mode. */
#define DR_QUERY_ID 0x700
#define DR_RESPONSE_BASE 0x700
#define DR_VERSION 1
#define DR_TIMEOUT_MS 1000u
#define DR_STALE_MS 30000u
#define DR_COMMS_NODE 2
#define DR_COMMS_INDEX 2
#define DR_LTE_NODE 3
#define DR_LTE_INDEX 3
#define DR_PAYLOAD_NODE 4
#define DR_PAYLOAD_INDEX 4
#define DR_COUNT 5
#define DR_EPS_I2C_INDEX 0
#define DR_CAN 1
#define DR_I2C 2
static const struct dr_definition {
    const char *name;
    uint8_t interface,node,address;
    bool future;
    uint16_t request_id,reply_id;
} dr_devices[DR_COUNT]={
    {"EPS",DR_I2C,0,0x68,false,0,0},
    {"EPS_NEXT",DR_CAN,1,0,true,0,0},
    {"COMMS",DR_CAN,DR_COMMS_NODE,0,false,CF_IHU_ID,CF_COMMS_ID},
    {"LTE",DR_CAN,DR_LTE_NODE,0,false,CF_LTE_REQUEST_ID,CF_LTE_REPLY_ID},
    {"PAYLOAD",DR_CAN,DR_PAYLOAD_NODE,0,false,CF_PAYLOAD_REQUEST_ID,CF_PAYLOAD_REPLY_ID}
};
enum {DR_NOT_SEEN,DR_ONLINE,DR_STALE,DR_FAULT};
static const char *const dr_states[]={"NOT_SEEN","ONLINE","STALE","FAULT"};
typedef struct {uint8_t state;bool seen;uint32_t last_seen,boot,timeouts;} dr_status;
static inline void dr_seen(dr_status *s,uint32_t now,uint32_t boot) {
    s->seen=true;s->state=DR_ONLINE;s->last_seen=now;s->boot=boot;
}
static inline void dr_age(dr_status *s,uint32_t now) {
    if(s->state==DR_ONLINE && (uint32_t)(now-s->last_seen)>=DR_STALE_MS)s->state=DR_STALE;
}
static inline bool dr_request(uint8_t node,uint16_t nonce,uint32_t boot,cf_frame *f) {
    if(node<1 || node>4 || !nonce || !boot)return false;
    memset(f,0,sizeof(*f));f->id=DR_QUERY_ID;f->size=8;
    f->data[0]=DR_VERSION;f->data[1]=node;ul_p16(f->data+2,nonce);ul_p32(f->data+4,boot);return true;
}
static inline bool dr_respond(const cf_frame *in,uint8_t node,uint32_t boot,cf_frame *out) {
    if(in->id!=DR_QUERY_ID || in->size!=8 || in->data[0]!=DR_VERSION ||
       in->data[1]!=node || node<1 || node>4 || !boot || !ul_u16(in->data+2) || !ul_u32(in->data+4))return false;
    *out=*in;out->id=DR_RESPONSE_BASE+node;ul_p32(out->data+4,boot);return true;
}
static inline bool dr_matches(const cf_frame *f,uint8_t node,uint16_t nonce) {
    return node>=1 && node<=4 && nonce && f->id==DR_RESPONSE_BASE+node && f->size==8 &&
        f->data[0]==DR_VERSION && f->data[1]==node && ul_u16(f->data+2)==nonce && ul_u32(f->data+4);
}
