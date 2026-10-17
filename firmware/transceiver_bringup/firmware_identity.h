#pragma once
#include "build_identity.h"
#include "native_wire.h"
#include "bpsk_packet.h"
static inline uint8_t fw_hex(char c) {return c>='a'?(uint8_t)(c-'a'+10):(uint8_t)(c-'0');}
static inline size_t firmware_packet(uint8_t *p,uint32_t boot,uint32_t sequence,uint32_t uptime) {
    const size_t n=W_PAYLOAD+W_SIZE_COMMS_FIRMWARE+2;
    memset(p,0,n);bp16(p,W_TM_IDENTITY);bp16(p+2,0xc000|(sequence&0x3fff));bp16(p+4,n-7);
    p[W_SCHEMA_VERSION]=W_VERSION;p[W_KIND]=W_KINDS_TELEMETRY;
    bp16(p+W_MESSAGE_ID,W_ID_COMMS_FIRMWARE);p[W_SOURCE]=W_ENDPOINTS_COMMS;p[W_TARGET]=W_ENDPOINTS_GROUND;
    bp32(p+W_SOURCE_BOOT_ID,boot);bp32(p+W_UPTIME_MS,uptime);bp16(p+W_PAYLOAD_LENGTH,W_SIZE_COMMS_FIRMWARE);
    p[W_PAYLOAD]=FW_MAJOR;p[W_PAYLOAD+1]=FW_MINOR;p[W_PAYLOAD+2]=FW_PATCH;p[W_PAYLOAD+3]=FW_DIRTY;
    for(unsigned i=0;i<20;i++)p[W_PAYLOAD+4+i]=(fw_hex(FW_GIT[i*2])<<4)|fw_hex(FW_GIT[i*2+1]);
    bp16(p+n-2,bp_crc16(p,n-2));return n;
}
