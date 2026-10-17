#pragma once
#include "uart_link.h"
/* Read-only identity, never opens an RF window. Version/SHA + boot + uptime. */
#define UL_FIRMWARE_INFO 0x18
#define UL_FIRMWARE_INFO_ACK 0x19
#define CF_MODEM_FIRMWARE 0x7c
#define CF_MODEM_FIRMWARE_ACK 0x7d
#define FI_SIZE 32u
static inline uint8_t fi_hex(char c) {return c>='a'?(uint8_t)(c-'a'+10):(uint8_t)(c-'0');}
static inline void fi_payload(uint8_t *p,uint32_t boot,uint32_t uptime) {
    p[0]=FW_MAJOR;p[1]=FW_MINOR;p[2]=FW_PATCH;p[3]=FW_DIRTY;
    for(unsigned i=0;i<20;i++)p[4+i]=(fi_hex(FW_GIT[2*i])<<4)|fi_hex(FW_GIT[2*i+1]);
    ul_p32(p+24,boot);ul_p32(p+28,uptime);
}
static inline bool fi_valid(const uint8_t *p,size_t n) {
    return n==FI_SIZE && p[3]<=1 && ul_u32(p+24)!=0;
}
