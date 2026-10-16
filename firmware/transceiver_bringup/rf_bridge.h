#pragma once
#include "can_fragment.h"
#include "bpsk_packet.h"
#include "native_wire.h"
#include "lte_link.h"
/* Bounded admission: one IHU-native telemetry packet inside CF_CHAIN or CF_SEND_PACKET.
 * No commands, synthetic replacement packets, or implied RF acknowledgment. */
static inline bool bridge_telemetry(const cf_reader *f,uint8_t packet[BPSK_NATIVE_MAX],size_t *size,uint32_t *request) {
    ul_reader r={0};ul_packet in={0};unsigned count=0;
    for(size_t i=0;i<f->used;i++)if(ul_feed(&r,f->wire[i],0,&in))++count;
    if(count!=1 || r.used || r.discard || r.crc_errors || r.framing_errors ||
       r.format_errors || r.overflows || in.version!=UL_VERSION || (in.type!=CF_CHAIN && in.type!=CF_SEND_PACKET) ||
       in.sender!=in.origin || (uint16_t)in.request!=f->token || in.size< W_PAYLOAD+2 || in.size>BPSK_NATIVE_MAX)return false;
    const uint8_t *p=in.payload;
    uint16_t id=ul_u16(p+W_MESSAGE_ID);
    size_t payload=id==W_ID_HEARTBEAT?W_SIZE_HEARTBEAT:
        id==W_ID_SYSTEM_STATUS?W_SIZE_SYSTEM_STATUS:
        id==W_ID_POWER_STATUS?W_SIZE_POWER_STATUS:
        id==W_ID_COMM_STATUS?W_SIZE_COMM_STATUS:0;
    if(!payload || in.size!=W_PAYLOAD+payload+2 ||
       ul_u16(p)!=W_TM_IDENTITY || (ul_u16(p+2)>>14)!=3 ||
       (size_t)ul_u16(p+4)+7!=in.size || p[W_SCHEMA_VERSION]!=W_VERSION ||
       p[W_KIND]!=W_KINDS_TELEMETRY || p[W_SOURCE]!=W_ENDPOINTS_IHU ||
       p[W_TARGET]!=W_ENDPOINTS_GROUND || !in.sender ||
       ul_u32(p+W_SOURCE_BOOT_ID)!=in.sender || ul_u32(p+W_TRANSACTION_EPOCH) ||
       ul_u32(p+W_TRANSACTION_ID) || ul_u16(p+W_PAYLOAD_LENGTH)!=payload ||
       bp_crc16(p,in.size-2)!=ul_u16(p+in.size-2))return false;
    memcpy(packet,p,in.size);*size=in.size;*request=in.request;return true;
}
static inline size_t bridge_frame(uint8_t out[BPSK_FRAME_MAX],const uint8_t *packet,size_t size,uint32_t sequence) {
    if(!size || size>BPSK_NATIVE_MAX)return 0;
    memset(out,0x55,32);const uint8_t sync[]={0x1a,0xcf,0xfc,0x1d};memcpy(out+32,sync,4);
    out[36]=3;bp32(out+37,sequence);bp16(out+41,(uint16_t)size);memcpy(out+43,packet,size);
    bp32(out+43+size,bp_crc32(out+36,7+size));memset(out+47+size,0,16);
    return size+63;
}
