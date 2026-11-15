#pragma once
#include "uart_link.h"

enum {
    RADIO_CONFIG_SCHEMA = 1,
    RADIO_PROFILE_DBPSK_1200_V3 = 1,
    RADIO_BEHAVIOR_RX_ONLY = 1,
    RADIO_BEHAVIOR_LINK_ACTIVE = 2,
    RADIO_CONFIG_DEFAULT = 5,
    RADIO_CONFIG_ACTIVE = 15,
    RADIO_CONFIG_BOOT = 25,
    RADIO_CONFIG_SIZE = 29,
    RADIO_CONFIG_RX_LO = 0,
    RADIO_CONFIG_TX_CARRIER = 4,
    RADIO_CONFIG_SYMBOL_RATE = 8,
};

static inline void radio_config_profile(uint8_t *data,uint32_t rx_lo,uint32_t tx_carrier,uint16_t baud){
    ul_p32(data+RADIO_CONFIG_RX_LO,rx_lo);
    ul_p32(data+RADIO_CONFIG_TX_CARRIER,tx_carrier);
    ul_p16(data+RADIO_CONFIG_SYMBOL_RATE,baud);
}
