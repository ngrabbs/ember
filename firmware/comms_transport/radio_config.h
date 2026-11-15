#pragma once
#include "uart_link.h"

enum {
    RADIO_CONFIG_SCHEMA = 2,
    RADIO_PROFILE_DBPSK_1200_V3 = 1,
    RADIO_PROFILE_DBPSK_DL1500_V3 = 2,
    RADIO_CONFIG_SUPPORTED = 3,
    RADIO_TRIAL_STABLE = 0, RADIO_TRIAL_STAGED, RADIO_TRIAL_ACTIVE,
    RADIO_TRIAL_CONFIRMED, RADIO_TRIAL_ROLLED_BACK,
    RADIO_CONFIG_READBACK = 0, RADIO_CONFIG_APPLIED, RADIO_CONFIG_REJECTED,
    RADIO_CONFIG_CONFIRMED,
    RADIO_PROFILE_SWITCH_MS = 5000,
    RADIO_PROFILE_TRIAL_MS = 45000,
    RADIO_BEHAVIOR_RX_ONLY = 1,
    RADIO_BEHAVIOR_LINK_ACTIVE = 2,
    RADIO_CONFIG_DEFAULT = 5,
    RADIO_CONFIG_ACTIVE = 15,
    RADIO_CONFIG_BOOT = 25,
    RADIO_CONFIG_CANDIDATE = 29,
    RADIO_CONFIG_TRIAL_STATE = 30,
    RADIO_CONFIG_TOKEN = 31,
    RADIO_CONFIG_REMAINING = 35,
    RADIO_CONFIG_RESULT = 39,
    RADIO_CONFIG_SIZE = 40,
    RADIO_CONFIG_RX_LO = 0,
    RADIO_CONFIG_TX_CARRIER = 4,
    RADIO_CONFIG_SYMBOL_RATE = 8,
};

static inline void radio_config_profile(uint8_t *data,uint32_t rx_lo,uint32_t tx_carrier,uint16_t baud){
    ul_p32(data+RADIO_CONFIG_RX_LO,rx_lo);
    ul_p32(data+RADIO_CONFIG_TX_CARRIER,tx_carrier);
    ul_p16(data+RADIO_CONFIG_SYMBOL_RATE,baud);
}

static inline const char *radio_profile_name(uint8_t profile){
    switch(profile){
    case RADIO_PROFILE_DBPSK_1200_V3:return "DBPSK_1200_V3";
    case RADIO_PROFILE_DBPSK_DL1500_V3:return "DBPSK_DL1500_V3";
    default:return "NONE";
    }
}

static inline uint16_t radio_profile_baud(uint8_t profile){
    return profile==RADIO_PROFILE_DBPSK_DL1500_V3 ? 1500 : 1200;
}
