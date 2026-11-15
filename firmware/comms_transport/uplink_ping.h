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
/* Same bounded zero-argument envelope; separate command allowlist. */
static inline bool up_native_fire(const uint8_t *p,size_t n){
 if(n!=32 || ul_u16(p+8)!=1028)return false;
 uint8_t copy[32];memcpy(copy,p,32);ul_p16(copy+8,1);ul_p16(copy+30,ul_crc(copy,30));
 return ul_crc(p,30)==ul_u16(p+30) && up_native_ping(copy,32);
}
static inline bool up_native_status(const uint8_t *p,size_t n){
 if(n!=32 || ul_u16(p+8)!=2)return false;
 uint8_t copy[32];memcpy(copy,p,32);ul_p16(copy+8,1);ul_p16(copy+30,ul_crc(copy,30));
 return ul_crc(p,30)==ul_u16(p+30) && up_native_ping(copy,32);
}
/* Structurally valid arguments reach the IHU even when their value is unsupported. */
static inline bool up_native_args(const uint8_t *p,size_t n,unsigned args){
 return n==32+args && ul_u16(p)==0x1900 && (ul_u16(p+2)&0xc000)==0xc000 &&
  ul_u16(p+4)==n-7 && p[6]==1 && p[7]==0 && p[10]==1 && p[11]==2 &&
  ul_u32(p+12) && ul_u32(p+16) && ul_u32(p+20) && ul_u16(p+28)==args && ul_crc(p,n-2)==ul_u16(p+n-2);
}
static inline bool up_native_cdh(const uint8_t *p,size_t n){
 if(n<32 || n>36)return false;
 unsigned id=ul_u16(p+8),args=id==3?1:(id==4||id==6)?0:id==5?4:99;
 return up_native_args(p,n,args);
}
static inline bool up_records_completed(const ul_packet *reply,const ul_packet *sent){
 const uint8_t *p=reply->payload;unsigned command=ul_u16(sent->payload+8);
 if(!up_native_cdh(sent->payload,sent->size) || (command!=4 && command!=5) ||
  reply->version!=1 || reply->type!=UP_RESULT || !reply->sender || reply->origin!=sent->sender ||
  reply->request!=sent->request || reply->size!=120 || ul_u16(p)!=0x0901 ||
  (ul_u16(p+2)&0xc000)!=0xc000 || ul_u16(p+4)!=113 || p[6]!=1 || p[7]!=1 ||
  ul_u16(p+8)!=59 || p[10]!=2 || p[11]!=1 || ul_u32(p+20)!=reply->sender ||
  memcmp(p+12,sent->payload+12,8) || ul_u16(p+28)!=88 || p[30]!=1 || p[31]!=5 ||
  p[32]!=16 || p[33]!=1 || !ul_u32(p+34) || ul_crc(p,118)!=ul_u16(p+118) ||
  (command==5 && ul_u32(p+34)!=ul_u32(sent->payload+30)))return false;
 for(unsigned i=0;i<5;i++){
  const uint8_t *v=p+38+16*i;
  if(ul_u16(v)!=i+1 || v[6]>4 || (v[7]!=1 && v[7]!=2) || v[9]>1 || v[11]>1)return false;
  if(i){uint32_t dt=ul_u32(v+2)-ul_u32(v-14);if(dt<900 || dt>1100)return false;}
 }
 return true;
}
static inline bool up_cdh_rejected(const ul_packet *reply,const ul_packet *sent){
 const uint8_t *p=reply->payload;
 return up_native_cdh(sent->payload,sent->size) && reply->version==1 && reply->type==UP_RESULT &&
  reply->sender && reply->origin==sent->sender && reply->request==sent->request && reply->size==43 &&
  ul_u16(p)==0x0901 && (ul_u16(p+2)&0xc000)==0xc000 && ul_u16(p+4)==36 && p[6]==1 && p[7]==2 &&
  ul_u16(p+8)==49 && p[10]==2 && p[11]==1 && ul_u32(p+20)==reply->sender &&
  !memcmp(p+12,sent->payload+12,8) && ul_u16(p+28)==11 && ul_u16(p+30)==ul_u16(sent->payload+8) &&
  ((p[32]==1 && (ul_u16(p+33)==2 || ul_u16(p+33)==3 || ul_u16(p+33)==5 || ul_u16(p+33)==9)) ||
   (p[32]==3 && (ul_u16(p+33)==7 || ul_u16(p+33)==8))) &&
  !ul_u16(p+35) && !ul_u32(p+37) && ul_crc(p,41)==ul_u16(p+41);
}
static inline bool up_reboot_scheduled(const ul_packet *reply,const ul_packet *sent){
 const uint8_t *p=reply->payload;
 return up_native_cdh(sent->payload,sent->size) && ul_u16(sent->payload+8)==6 && reply->version==1 &&
  reply->type==UP_RESULT && reply->sender && reply->origin==sent->sender && reply->request==sent->request &&
  reply->size==43 && ul_u16(p)==0x0901 && (ul_u16(p+2)&0xc000)==0xc000 && ul_u16(p+4)==36 &&
  p[6]==1 && p[7]==2 && ul_u16(p+8)==49 && p[10]==2 && p[11]==1 && ul_u32(p+20)==reply->sender &&
  !memcmp(p+12,sent->payload+12,8) && ul_u16(p+28)==11 && ul_u16(p+30)==6 && p[32]==2 &&
  !ul_u16(p+33) && !ul_u16(p+35) && ul_u32(p+37)==5000 && ul_crc(p,41)==ul_u16(p+41);
}
static inline bool up_status_completed(const ul_packet *reply,const ul_packet *sent){
 const uint8_t *p=reply->payload;
 return (up_native_status(sent->payload,sent->size) || (up_native_cdh(sent->payload,sent->size) && ul_u16(sent->payload+8)==3 && sent->payload[30]==1)) && reply->version==1 &&
  reply->type==UP_RESULT && reply->sender && reply->origin==sent->sender &&
  reply->request==sent->request && reply->size==56 && ul_u16(p)==0x0901 &&
  (ul_u16(p+2)&0xc000)==0xc000 && ul_u16(p+4)==49 && p[6]==1 && p[7]==1 &&
  ul_u16(p+8)==58 && p[10]==2 && p[11]==1 && ul_u32(p+20)==reply->sender &&
  !memcmp(p+12,sent->payload+12,8) && ul_u16(p+28)==24 && p[30]==1 &&
  p[31]<=4 && (p[32]==1 || p[32]==2) && p[38]<=1 && p[40]<=1 && p[41]<=1 &&
  p[50]<=3 && p[51]<=3 && p[52]<=3 && p[53]==0 && ul_crc(p,54)==ul_u16(p+54);
}
static inline bool up_fire_completed(const ul_packet *reply,const ul_packet *sent){
 const uint8_t *p=reply->payload;
 return reply->version==1 && reply->type==UP_RESULT && reply->sender && reply->origin==sent->sender &&
  reply->request==sent->request && reply->size==52 && ul_u16(p)==0x0901 &&
  (ul_u16(p+2)&0xc000)==0xc000 && ul_u16(p+4)==45 && p[6]==1 && p[7]==1 &&
  ul_u16(p+8)==57 && p[10]==2 && p[11]==1 && ul_u32(p+20)==reply->sender &&
  !memcmp(p+12,sent->payload+12,8) && ul_u16(p+28)==20 &&
  (p[30]==1 || p[30]==2) && p[31]==2 && p[32]<=(p[30]==1?1:2) &&
  (p[33]==1 || p[33]==2) && (p[32]!=2 || p[33]==2) && !ul_u32(p+34) &&
  ul_u32(p+38) && ul_u32(p+46) && ul_crc(p,50)==ul_u16(p+50);
}
/* Explicit execution failure is a terminal response, never a NO_FIRE result. */
static inline bool up_fire_failed(const ul_packet *reply,const ul_packet *sent){
 const uint8_t *p=reply->payload;
 return up_native_fire(sent->payload,sent->size) && reply->version==1 &&
  reply->type==UP_RESULT && reply->sender && reply->origin==sent->sender &&
  reply->request==sent->request && reply->size==43 && ul_u16(p)==0x0901 &&
  (ul_u16(p+2)&0xc000)==0xc000 && ul_u16(p+4)==36 && p[6]==1 && p[7]==2 &&
  ul_u16(p+8)==49 && p[10]==2 && p[11]==1 && ul_u32(p+20)==reply->sender &&
  !memcmp(p+12,sent->payload+12,8) && ul_u16(p+28)==11 && ul_u16(p+30)==1028 &&
  p[32]==3 && ul_u16(p+33)==7 && !ul_u16(p+35) &&
  ul_crc(p,41)==ul_u16(p+41);
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
