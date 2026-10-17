#pragma once
#include "uart_link.h"
#include "wire.h"
/* Explicit native IHU telemetry allowlist, shared by both forwarding hops. */
static inline bool native_telemetry_valid(const uint8_t *b,size_t n,uint32_t sender) {
    if(n<W_PAYLOAD+2)return false;
    uint16_t id=ul_u16(b+W_MESSAGE_ID);
    size_t payload=id==W_ID_HEARTBEAT?W_SIZE_HEARTBEAT:
        id==W_ID_SYSTEM_STATUS?W_SIZE_SYSTEM_STATUS:
        id==W_ID_POWER_STATUS?W_SIZE_POWER_STATUS:0;
    return payload && n==W_PAYLOAD+payload+2 && ul_u16(b)==W_TM_IDENTITY &&
        (ul_u16(b+2)>>14)==3 && (size_t)ul_u16(b+4)+7==n &&
        b[W_SCHEMA_VERSION]==W_VERSION && b[W_KIND]==W_KINDS_TELEMETRY &&
        b[W_SOURCE]==W_ENDPOINTS_IHU && b[W_TARGET]==W_ENDPOINTS_GROUND &&
        ul_u32(b+W_SOURCE_BOOT_ID) && (!sender || ul_u32(b+W_SOURCE_BOOT_ID)==sender) &&
        !ul_u32(b+W_TRANSACTION_EPOCH) && !ul_u32(b+W_TRANSACTION_ID) &&
        ul_u16(b+W_PAYLOAD_LENGTH)==payload && ul_crc(b,n-2)==ul_u16(b+n-2);
}
