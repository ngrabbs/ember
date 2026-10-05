#pragma once
#include "hardware/i2c.h"
#include "../shared/ltc4162_registers.h"

/* Observational reader, matching the existing IHU's SMBus/PEC protocol.
 * Explicit ADC override changes only force_telemetry_on, never charge policy.
 * Feather SDA/GPIO2 and SCL/GPIO3 use I2C1. */
static void eps_bus_init(void) {
    i2c_init(i2c1,100000);
    gpio_set_function(2,GPIO_FUNC_I2C);gpio_set_function(3,GPIO_FUNC_I2C);
    gpio_pull_up(2);gpio_pull_up(3);
}
static uint8_t eps_pec(uint8_t crc,uint8_t byte) {
    crc^=byte;
    for(unsigned bit=0;bit<8;++bit)crc=(uint8_t)((crc<<1)^((crc&0x80)?7:0));
    return crc;
}
static bool eps_word(uint8_t reg,uint16_t *out) {
    const uint8_t addr=0x68;uint8_t data[3];
    if(i2c_write_timeout_us(i2c1,addr,&reg,1,true,10000)!=1)return false;
    if(i2c_read_timeout_us(i2c1,addr,data,3,false,10000)!=3)return false;
    uint8_t crc=eps_pec(0,addr<<1);crc=eps_pec(crc,reg);
    crc=eps_pec(crc,(addr<<1)|1);crc=eps_pec(crc,data[0]);crc=eps_pec(crc,data[1]);
    if(crc!=data[2])return false;
    *out=(uint16_t)(data[0]|(uint16_t)data[1]<<8);return true;
}
static bool eps_read(ltc4162_raw_t *out,uint8_t *failed_register) {
    ltc4162_raw_t next;
#define READ(name,address) if(!eps_word(address,&next.name)) {*failed_register=address;return false;}
    LTC4162_READOUT_REGISTERS(READ)
#undef READ
    *out=next;return true;
}
static bool eps_force_adc(bool enable,uint16_t *before,uint16_t *after) {
    if(!eps_word(LTC4162_REG_config_bits,before))return false;
    uint16_t wanted=enable?(*before|4u):(*before&~4u);
    if(wanted!=*before) {
        uint8_t data[3]={LTC4162_REG_config_bits,(uint8_t)wanted,(uint8_t)(wanted>>8)};
        if(i2c_write_timeout_us(i2c1,0x68,data,3,false,10000)!=3)return false;
    }
    return eps_word(LTC4162_REG_config_bits,after) && *after==wanted;
}
