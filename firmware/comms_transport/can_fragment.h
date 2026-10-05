#ifndef EMBER_CAN_FRAGMENT_H
#define EMBER_CAN_FRAGMENT_H
#include "uart_link.h"
#define CF_CHUNK 4
#define CF_GAP_MS 500
#define CF_FRAMES ((UL_WIRE_MAX + CF_CHUNK - 1) / CF_CHUNK)
#define CF_IHU_ID 0x710
#define CF_COMMS_ID 0x711
#define CF_CHAIN 0x72
#define CF_CHAIN_ACK 0x73
#define CF_BUSY 5
#define CF_LINK_UNKNOWN 6
#define CF_BAD_PACKET 7

typedef struct { uint16_t id; uint8_t size, data[8]; } cf_frame;
typedef struct {
    uint8_t wire[UL_WIRE_MAX];
    size_t used;
    uint16_t token;
    uint8_t next;
    bool active;
    uint32_t last, errors, timeouts;
} cf_reader;
static inline void cf_expire(cf_reader *r,uint32_t now) {
    if(r->active && (uint32_t)(now-r->last)>=CF_GAP_MS) {
        r->active=false;r->used=0;++r->timeouts;
    }
}
static inline bool cf_fragment(const uint8_t *wire,size_t size,uint16_t id,
                               uint16_t token,unsigned index,cf_frame *out) {
    size_t offset=(size_t)index*CF_CHUNK;
    if(!size || size>UL_WIRE_MAX || offset>=size || id>0x7ff || index>=CF_FRAMES)return false;
    size_t count=size-offset;if(count>CF_CHUNK)count=CF_CHUNK;
    out->id=id;out->size=(uint8_t)(4+count);
    out->data[0]=(uint8_t)(0x10|(index==0?1:0)|(offset+count==size?2:0));
    ul_p16(out->data+1,token);out->data[3]=(uint8_t)index;memcpy(out->data+4,wire+offset,count);
    return true;
}
static inline bool cf_feed(cf_reader *r,const cf_frame *f,uint16_t id,uint32_t now) {
    cf_expire(r,now);
    if(f->id!=id)return false;
    if(f->size<5 || f->size>8 || (f->data[0]&0xfc)!=0x10) {
        ++r->errors;r->active=false;return false;
    }
    bool start=(f->data[0]&1)!=0,end=(f->data[0]&2)!=0;
    uint16_t token=ul_u16(f->data+1);uint8_t index=f->data[3];size_t count=f->size-4;
    if(start) {
        if(index || r->active) {++r->errors;r->active=false;return false;}
        r->active=true;r->used=0;r->token=token;r->next=0;
    }
    if(!r->active || token!=r->token || index!=r->next || r->used+count>UL_WIRE_MAX ||
       (!end && count!=CF_CHUNK)) {
        ++r->errors;r->active=false;return false;
    }
    memcpy(r->wire+r->used,f->data+4,count);r->used+=count;++r->next;r->last=now;
    if(end) {r->active=false;return true;}return false;
}
#endif
