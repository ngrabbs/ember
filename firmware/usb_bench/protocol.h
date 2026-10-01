#pragma once
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include "wire.h"

typedef bool (*ember_send_fn)(const uint8_t *, size_t, void *);
typedef struct { uint8_t kind, size; uint16_t id; uint8_t payload[18]; } ember_report;
typedef struct {
    bool valid;
    uint32_t epoch, transaction;
    uint16_t command, size;
    uint8_t arguments[W_MAX_PAYLOAD], count;
    ember_report reports[3];
} ember_cache_entry;
typedef struct {
    uint32_t boot, period, accepted, rejected, rx, tx, crc_errors, dropped;
    uint16_t sequence;
    unsigned next_cache;
    ember_cache_entry cache[64];
} ember_state;

uint16_t ember_crc(const uint8_t *, size_t);
void ember_init(ember_state *, uint32_t);
void ember_command(ember_state *, const uint8_t *, size_t, uint32_t, ember_send_fn, void *);
void ember_periodic(ember_state *, uint32_t, ember_send_fn, void *);
