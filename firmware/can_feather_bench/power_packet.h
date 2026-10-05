#pragma once
#include <limits.h>
#include "uart_link.h"
#include "wire.h"
#include "../shared/ltc4162_registers.h"
/* Integer fixed-point conversions; signed ADC words retain their polarity. */
static inline int32_t power_round(int32_t numerator,int32_t denominator) {
    return numerator<0?-((-numerator+denominator/2)/denominator):(numerator+denominator/2)/denominator;
}
static inline size_t power_packet(uint8_t *packet,const ltc4162_raw_t *raw,
                                 uint32_t boot,uint16_t sequence,uint32_t readout_ms,uint32_t count) {
    size_t size=W_PAYLOAD+W_SIZE_POWER_STATUS+2;memset(packet,0,size);
    ul_p16(packet,W_TM_IDENTITY);ul_p16(packet+2,0xc000|(sequence&0x3fff));ul_p16(packet+4,size-7);
    packet[W_SCHEMA_VERSION]=W_VERSION;packet[W_KIND]=W_KINDS_TELEMETRY;
    ul_p16(packet+W_MESSAGE_ID,W_ID_POWER_STATUS);packet[W_SOURCE]=W_ENDPOINTS_IHU;packet[W_TARGET]=W_ENDPOINTS_GROUND;
    ul_p32(packet+W_SOURCE_BOOT_ID,boot);ul_p32(packet+W_UPTIME_MS,readout_ms);
    ul_p16(packet+W_PAYLOAD_LENGTH,W_SIZE_POWER_STATUS);uint8_t *p=packet+W_PAYLOAD;
    p[W_POWER_STATUS_PAYLOAD_VERSION]=1;p[W_POWER_STATUS_PROVENANCE]=W_EPS_PROVENANCE_IHU_NATIVE;
    p[W_POWER_STATUS_LINK]=W_EPS_LINK_LIVE;p[W_POWER_STATUS_READOUT_PRESENT]=1;p[W_POWER_STATUS_READOUT_VALID]=1;
    unsigned cells=raw->chem_cells&15;bool adc=raw->telemetry_status&1;
    bool valid=adc && ((raw->chem_cells>>8)&15)<=3 && (!cells || cells==2);
    p[W_POWER_STATUS_CONVERSION_VALID]=valid;p[W_POWER_STATUS_ADC_VALID]=adc;
    p[W_POWER_STATUS_CONFIGURED_CELLS]=2;p[W_POWER_STATUS_DETECTED_CELLS]=cells;
    /* bridge_session_id=0: no ground wrapper. Sense resistor values remain assumptions. */
    ul_p32(p+W_POWER_STATUS_READOUT_COUNT,count);ul_p32(p+W_POWER_STATUS_IHU_READOUT_UPTIME_MS,readout_ms);
    ul_p32(p+W_POWER_STATUS_RSNSB_MICROOHMS,10000);ul_p32(p+W_POWER_STATUS_RSNSI_MICROOHMS,10000);
#define VALUE(field,expression) ul_p32(p+W_POWER_STATUS_##field,(uint32_t)(valid?(expression):INT32_MIN))
    VALUE(BATTERY_MV,power_round((int16_t)raw->vbat*3848,10000));
    VALUE(INPUT_MV,power_round((int16_t)raw->vin*1649,1000));
    VALUE(OUTPUT_MV,power_round((int16_t)raw->vout*1653,1000));
    VALUE(BATTERY_UA,power_round((int16_t)raw->ibat*1466,10));
    VALUE(INPUT_UA,power_round((int16_t)raw->iin*1466,10));
    VALUE(DIE_TEMP_MC,power_round((int16_t)raw->die_temp*43,2)-264400);
#undef VALUE
    const uint16_t words[]={
#define WORD(name,address) raw->name,
        LTC4162_READOUT_REGISTERS(WORD)
#undef WORD
    };
    for(unsigned i=0;i<sizeof(words)/sizeof(words[0]);++i)ul_p16(p+W_POWER_STATUS_RAW_CONFIG_BITS+2*i,words[i]);
    ul_p16(packet+size-2,ul_crc(packet,size-2));return size;
}
