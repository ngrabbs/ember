#pragma once
#include "uart_link.h"
#include "wire.h"
/* Report actual mode/configuration. Flight routines remain inactive stubs. */
static inline size_t health_packet(uint8_t *b,bool system,uint32_t boot,
        uint16_t sequence,uint32_t uptime,uint32_t period,uint32_t accepted,uint32_t rejected,uint8_t mode,uint8_t configuration) {
    size_t payload=system?W_SIZE_SYSTEM_STATUS:W_SIZE_HEARTBEAT;
    size_t n=W_PAYLOAD+payload+2;memset(b,0,n);
    ul_p16(b,W_TM_IDENTITY);ul_p16(b+2,0xc000|(sequence&0x3fff));ul_p16(b+4,n-7);
    b[W_SCHEMA_VERSION]=W_VERSION;b[W_KIND]=W_KINDS_TELEMETRY;
    ul_p16(b+W_MESSAGE_ID,system?W_ID_SYSTEM_STATUS:W_ID_HEARTBEAT);
    b[W_SOURCE]=W_ENDPOINTS_IHU;b[W_TARGET]=W_ENDPOINTS_GROUND;
    ul_p32(b+W_SOURCE_BOOT_ID,boot);ul_p32(b+W_UPTIME_MS,uptime);ul_p16(b+W_PAYLOAD_LENGTH,payload);
    if(system) {
        b[W_PAYLOAD+W_SYSTEM_STATUS_MODE]=mode;
        b[W_PAYLOAD+W_SYSTEM_STATUS_CONFIGURATION]=configuration;
        ul_p32(b+W_PAYLOAD+W_SYSTEM_STATUS_TELEMETRY_PERIOD_MS,period);
        ul_p32(b+W_PAYLOAD+W_SYSTEM_STATUS_ACCEPTED_COMMANDS,accepted);
        ul_p32(b+W_PAYLOAD+W_SYSTEM_STATUS_REJECTED_COMMANDS,rejected);
    } else {
        b[W_PAYLOAD+W_HEARTBEAT_MODE]=mode;
        b[W_PAYLOAD+W_HEARTBEAT_CONFIGURATION]=configuration;
        ul_p32(b+W_PAYLOAD+W_HEARTBEAT_TELEMETRY_PERIOD_MS,period);
    }
    ul_p16(b+n-2,ul_crc(b,n-2));return n;
}
