#pragma once
#include "can_fragment.h"
#include "bpsk_packet.h"
/* Narrow bench admission: one IHU-native heartbeat inside CF_CHAIN.
 * No commands, synthetic replacement packets, or implied RF acknowledgment. */
static inline bool bridge_heartbeat(const cf_reader *f,uint8_t packet[38],uint32_t *request) {
    ul_reader r={0};ul_packet in={0};unsigned count=0;
    for(size_t i=0;i<f->used;i++)if(ul_feed(&r,f->wire[i],0,&in))++count;
    if(count!=1 || r.used || r.discard || r.crc_errors || r.framing_errors ||
       r.format_errors || r.overflows || in.version!=UL_VERSION || in.type!=CF_CHAIN ||
       in.sender!=in.origin || (uint16_t)in.request!=f->token || in.size!=38)return false;
    const uint8_t *p=in.payload;
    if(ul_u16(p)!=0x0901 || (ul_u16(p+2)>>14)!=3 || ul_u16(p+4)!=31 ||
       p[6]!=1 || p[7]!=1 || ul_u16(p+8)!=5 || p[10]!=2 || p[11]!=1 ||
       ul_u32(p+20)!=in.sender || ul_u16(p+28)!=6 ||
       bp_crc16(p,36)!=ul_u16(p+36))return false;
    memcpy(packet,p,38);*request=in.request;return true;
}
static inline void bridge_frame(uint8_t out[BPSK_FRAME_SIZE],const uint8_t packet[38],uint32_t sequence) {
    memset(out,0x55,32);const uint8_t sync[]={0x1a,0xcf,0xfc,0x1d};memcpy(out+32,sync,4);
    out[36]=3;bp32(out+37,sequence);bp16(out+41,38);memcpy(out+43,packet,38);
    bp32(out+81,bp_crc32(out+36,45));memset(out+85,0,16);
}
