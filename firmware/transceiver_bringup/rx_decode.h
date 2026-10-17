/* Bounded, capture-only DBPSK detector. No dispatch, CAN forwarding or RF output.
 * 8 kS/s real ADC, 1200 baud; integer mixing, eight symbol timing hypotheses.
 * Search 400..2600 Hz in 25 Hz steps. Returns only the first CRC-valid frame.
 * This is a bench acquisition envelope, not full-band frequency acquisition. */
#pragma once
#include <stdbool.h>
#include <stdint.h>
#include <stddef.h>
#include <string.h>
#include "bpsk_packet.h"
static const int16_t rd_sine[256] = {
0,804,1608,2410,3212,4011,4808,5602,6393,7179,7962,8739,9512,10278,11039,11793,12539,13279,14010,14732,15446,16151,16846,17530,18204,18868,19519,20159,20787,21403,22005,22594,23170,23731,24279,24811,25329,25832,26319,26790,27245,27683,28105,28510,28898,29268,29621,29956,30273,30571,30852,31113,31356,31580,31785,31971,32137,32285,32412,32521,32609,32678,32728,32757,32767,32757,32728,32678,32609,32521,32412,32285,32137,31971,31785,31580,31356,31113,30852,30571,30273,29956,29621,29268,28898,28510,28105,27683,27245,26790,26319,25832,25329,24811,24279,23731,23170,22594,22005,21403,20787,20159,19519,18868,18204,17530,16846,16151,15446,14732,14010,13279,12539,11793,11039,10278,9512,8739,7962,7179,6393,5602,4808,4011,3212,2410,1608,804,0,-804,-1608,-2410,-3212,-4011,-4808,-5602,-6393,-7179,-7962,-8739,-9512,-10278,-11039,-11793,-12539,-13279,-14010,-14732,-15446,-16151,-16846,-17530,-18204,-18868,-19519,-20159,-20787,-21403,-22005,-22594,-23170,-23731,-24279,-24811,-25329,-25832,-26319,-26790,-27245,-27683,-28105,-28510,-28898,-29268,-29621,-29956,-30273,-30571,-30852,-31113,-31356,-31580,-31785,-31971,-32137,-32285,-32412,-32521,-32609,-32678,-32728,-32757,-32767,-32757,-32728,-32678,-32609,-32521,-32412,-32285,-32137,-31971,-31785,-31580,-31356,-31113,-30852,-30571,-30273,-29956,-29621,-29268,-28898,-28510,-28105,-27683,-27245,-26790,-26319,-25832,-25329,-24811,-24279,-23731,-23170,-22594,-22005,-21403,-20787,-20159,-19519,-18868,-18204,-17530,-16846,-16151,-15446,-14732,-14010,-13279,-12539,-11793,-11039,-10278,-9512,-8739,-7962,-7179,-6393,-5602,-4808,-4011,-3212,-2410,-1608,-804
};
typedef struct { uint8_t packet[240]; unsigned size, frequency; uint32_t sequence; } rd_result;
typedef struct {
 uint32_t sync; unsigned bits, bytes, wanted; uint8_t body[251];
 int32_t re,im,prev_re,prev_im; bool previous, collecting;
} rd_lane;
static uint16_t rd_u16(const uint8_t *p){return (uint16_t)((p[0]<<8)|p[1]);}
static uint32_t rd_u32(const uint8_t *p){return ((uint32_t)p[0]<<24)|((uint32_t)p[1]<<16)|((uint32_t)p[2]<<8)|p[3];}
static bool rd_bit(rd_lane *s, unsigned bit, rd_result *out) {
 if(!s->collecting){
  s->sync=(s->sync<<1)|bit;
  if(s->sync==0x1acffc1d){s->collecting=true;s->bits=s->bytes=s->wanted=0;memset(s->body,0,sizeof(s->body));}
  return false;
 }
 s->body[s->bytes]=(uint8_t)((s->body[s->bytes]<<1)|bit);
 if(++s->bits<8)return false;
 s->bits=0;++s->bytes;
 if(s->bytes==7){
  unsigned n=rd_u16(s->body+5);
  if(s->body[0]!=3||n<32||n>240){s->collecting=false;s->sync=0;return false;}
  s->wanted=7+n+4;
 }
 if(!s->wanted||s->bytes<s->wanted)return false;
 s->collecting=false;s->sync=0;
 unsigned n=s->wanted-11;const uint8_t *p=s->body+7;
 if(bp_crc32(s->body,s->wanted-4)!=rd_u32(s->body+s->wanted-4))return false;
 /* Native framing and CRC only. Restrict to telemetry fixtures for now. */
 if(rd_u16(p)!=0x0901||(rd_u16(p+2)&0xc000)!=0xc000||rd_u16(p+4)!=n-7||
    p[6]!=1||p[7]!=1||rd_u16(p+28)!=n-32||bp_crc16(p,n-2)!=rd_u16(p+n-2))return false;
 out->size=n;out->sequence=rd_u32(s->body+1);memcpy(out->packet,p,n);return true;
}
/* Optional callback between frequency candidates keeps control/service bounded. */
typedef bool (*rd_continue)(void);
static bool rd_decode(const uint16_t *samples,size_t count,rd_result *out,rd_continue proceed){
 if(!samples||!out||count!=32768)return false;
 uint32_t sum=0;
 for(size_t i=0;i<count;i++){if(!samples[i]||samples[i]>=4095)return false;sum+=samples[i];}
 int32_t mean=(int32_t)(sum/count);
 for(unsigned hz=400;hz<=2600;hz+=25){
  if(proceed&&!proceed())return false;
  /* Single diagnostic owner; keep workspace off the Pico stack. */
  static rd_lane lanes[8];memset(lanes,0,sizeof(lanes));uint32_t phase=0,step=(uint32_t)(((uint64_t)hz<<32)/8000);
  for(size_t i=0;i<count;i++,phase+=step){
   int32_t v=(int32_t)samples[i]-mean;
   /* Divide mixer output before accumulation to bound differential products. */
   int32_t re=v*rd_sine[((phase>>24)+64)&255]/256;
   int32_t im=v*rd_sine[phase>>24]/256;
   for(unsigned t=0;t<8;t++){
    rd_lane *s=&lanes[t];unsigned tick=(unsigned)i*6;
    if(tick<t*5)continue;
    if(i && (tick-t*5)/40 != (tick-6<t*5?0:(tick-6-t*5)/40)){
     if(s->previous && rd_bit(s,(int64_t)s->re*s->prev_re+(int64_t)s->im*s->prev_im<0,out)){
      out->frequency=hz;return true;
     }
     s->prev_re=s->re;s->prev_im=s->im;s->previous=true;s->re=s->im=0;
    }
    s->re+=re;s->im+=im;
   }
  }
 }
 return false;
}
