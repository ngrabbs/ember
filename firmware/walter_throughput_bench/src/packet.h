#pragma once
#include <stdint.h>
#include <stddef.h>
#include <string.h>
namespace bench {
static constexpr size_t HEADER=32,MAX_PACKET=1024;
inline void put16(uint8_t *p,uint16_t v){p[0]=v>>8;p[1]=v;}
inline void put32(uint8_t *p,uint32_t v){p[0]=v>>24;p[1]=v>>16;p[2]=v>>8;p[3]=v;}
inline uint32_t crc32(const uint8_t *p,size_t n){
 uint32_t crc=0xffffffffu;
 for(size_t i=0;i<n;++i){crc^=p[i];for(unsigned j=0;j<8;++j)crc=(crc>>1)^(0xedb88320u&(0u-(crc&1u)));}
 return ~crc;
}
inline bool make_packet(uint8_t *p,size_t n,uint32_t run,uint32_t seq,uint32_t ms,uint32_t boot){
 if((n!=128 && n!=512 && n!=1024)||!run||!boot)return false;
 memset(p,0,n);memcpy(p,"ELTB",4);p[4]=1;put16(p+6,HEADER);put32(p+8,run);put32(p+12,seq);
 put32(p+16,ms);put16(p+20,n);put32(p+28,boot);
 for(size_t i=HEADER;i<n;++i)p[i]=(uint8_t)(run+seq+i);
 put32(p+24,crc32(p,n));return true;
}
}
