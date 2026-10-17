/* Bench ingress validation only. Never forwards, executes or transmits.
 * Cache lasts one COMMS boot, is not authentication or persistent anti-replay.
 * No eviction: fail closed after 16 distinct accepted transactions. */
#pragma once
#include "rx_decode.h"
#include "native_wire.h"
typedef struct {uint32_t epoch,id,boot;} rp_key;
typedef struct {rp_key keys[16];unsigned used;} rp_cache;
static const char *rp_check(rp_cache *cache,const uint8_t *p,unsigned n){
 if(!cache||!p||n!=32)return "REJECT_SIZE";
 if(rd_u16(p)!=0x1900 || (rd_u16(p+2)&0xc000)!=0xc000 || rd_u16(p+4)!=n-7 ||
    p[W_SCHEMA_VERSION]!=W_VERSION || p[W_KIND]!=W_KINDS_COMMAND ||
    rd_u16(p+W_PAYLOAD_LENGTH)!=0 || bp_crc16(p,n-2)!=rd_u16(p+n-2))return "REJECT_FRAME";
 if(p[W_SOURCE]!=W_ENDPOINTS_GROUND || p[W_TARGET]!=W_ENDPOINTS_IHU)return "REJECT_ROUTE";
 if(rd_u16(p+W_MESSAGE_ID)!=W_ID_PING && rd_u16(p+W_MESSAGE_ID)!=W_ID_PAYLOAD_FIRE_CHECK)return "REJECT_COMMAND";
 uint32_t epoch=rd_u32(p+W_TRANSACTION_EPOCH),id=rd_u32(p+W_TRANSACTION_ID),boot=rd_u32(p+W_SOURCE_BOOT_ID);
 if(!epoch||!id||!boot)return "REJECT_IDENTITY";
 for(unsigned i=0;i<cache->used;i++)if(cache->keys[i].epoch==epoch&&cache->keys[i].id==id)
  return cache->keys[i].boot==boot ? "PING_DUPLICATE" : "REJECT_TRANSACTION_CONFLICT";
 if(cache->used>=16)return "REJECT_CACHE_FULL";
 cache->keys[cache->used++]=(rp_key){epoch,id,boot};
 return "PING_ACCEPTED";
}
