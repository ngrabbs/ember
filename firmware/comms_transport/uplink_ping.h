#pragma once
#include "can_fragment.h"
/* Dedicated reverse route; separate from COMMS/LTE downlink exchanges. */
#define UP_REQUEST_ID 0x730
#define UP_REPLY_ID 0x731
#define UP_PING 0x90
#define UP_RESULT 0x91
static inline bool up_native_ping(const uint8_t *p,size_t n){
 return n==32 && ul_u16(p)==0x1900 && (ul_u16(p+2)&0xc000)==0xc000 && ul_u16(p+4)==25 &&
  p[6]==1 && p[7]==0 && ul_u16(p+8)==1 && p[10]==1 && p[11]==2 &&
  ul_u32(p+12) && ul_u32(p+16) && ul_u32(p+20) && !ul_u16(p+28) && ul_crc(p,30)==ul_u16(p+30);
}
static inline bool up_envelope(const cf_reader *f,ul_packet *out){
 ul_reader r={0};unsigned count=0;
 for(size_t i=0;i<f->used;i++)if(ul_feed(&r,f->wire[i],0,out))++count;
 return count==1 && !r.used && !r.discard && !r.framing_errors && !r.crc_errors && !r.format_errors && !r.overflows &&
  out->version==1 && out->sender && out->origin && out->request && (uint16_t)out->request==f->token;
}
static inline bool up_completed(const ul_packet *reply,const ul_packet *sent){
 const uint8_t *p=reply->payload;
 return reply->version==1 && reply->type==UP_RESULT && reply->sender && reply->origin==sent->sender &&
  reply->request==sent->request && reply->size==43 && ul_u16(p)==0x0901 &&
  (ul_u16(p+2)&0xc000)==0xc000 && ul_u16(p+4)==36 && p[6]==1 && p[7]==2 &&
  ul_u16(p+8)==49 && p[10]==2 && p[11]==1 && ul_u32(p+20)==reply->sender &&
  !memcmp(p+12,sent->payload+12,8) && ul_u16(p+28)==11 && ul_u16(p+30)==1 &&
  p[32]==2 && !ul_u16(p+33) && !ul_u16(p+35) && !ul_u32(p+37) && ul_crc(p,41)==ul_u16(p+41);
}
