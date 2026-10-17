/* Native COMMS heartbeat in a version3 differential-BPSK bench frame. */
#pragma once
#include <stdint.h>
#include <stddef.h>
#include <string.h>
#define BPSK_BAUD 1200u
#define BPSK_FRAME_SIZE 101u
/* Largest current native telemetry is POWER_STATUS (128 bytes).
 * 191 RF bytes take 1.274s, within the 1.5s payload / 2s hard mute limits. */
#define BPSK_NATIVE_MAX 128u
#define BPSK_FRAME_MAX (BPSK_NATIVE_MAX+63u)
static void bp16(uint8_t *p,uint16_t v){p[0]=v>>8;p[1]=v;}
static void bp32(uint8_t *p,uint32_t v){p[0]=v>>24;p[1]=v>>16;p[2]=v>>8;p[3]=v;}
static uint16_t bp_crc16(const uint8_t *p,size_t n){uint16_t c=0xffff;while(n--){c^=(uint16_t)*p++<<8;for(unsigned i=0;i<8;i++)c=(c&0x8000)?(uint16_t)((c<<1)^0x1021):(uint16_t)(c<<1);}return c;}
static uint32_t bp_crc32(const uint8_t *p,size_t n){uint32_t c=0xffffffff;while(n--){c^=*p++;for(unsigned i=0;i<8;i++)c=(c>>1)^((c&1)?0xedb88320:0);}return c^0xffffffff;}
static size_t bpsk_frame(uint8_t *out,size_t capacity,uint32_t boot,uint32_t sequence,uint32_t uptime_ms){
 if(capacity<BPSK_FRAME_SIZE||!boot)return 0;
 memset(out,0x55,32);const uint8_t sync[]={0x1a,0xcf,0xfc,0x1d};memcpy(out+32,sync,4);
 uint8_t *body=out+36;body[0]=3;bp32(body+1,sequence);bp16(body+5,38);
 uint8_t *p=body+7;memset(p,0,38);
 bp16(p,0x0901);bp16(p+2,0xc000|(sequence&0x3fff));bp16(p+4,31);
 p[6]=1;p[7]=1;bp16(p+8,5);p[10]=3;p[11]=1;
 bp32(p+20,boot);bp32(p+24,uptime_ms);bp16(p+28,6);
 p[30]=2;p[31]=1; /* COMMISSIONING, GROUND_TEST, manual period0. */
 bp16(p+36,bp_crc16(p,36));bp32(body+45,bp_crc32(body,45));
 memset(out+85,0,16);return BPSK_FRAME_SIZE;
}
