#pragma once
#include <stdbool.h>
#include <stdint.h>
#include "../ihu/mode_policy.h"
#define DEMO_DEBOUNCE_MS 250u
#define DEMO_ANTENNA_MS 10000u
#define DEMO_RF_MS 15000u
typedef struct {
    ip_state policy;
    bool raw[2], stable[2], health, released, antenna, rf, checkout;
    uint32_t changed[2], release_ms;
} demo_state;
void demo_init(demo_state *s, uint32_t now, bool a, bool b);
void demo_tick(demo_state *s, uint32_t now, bool a, bool b);
const char *demo_start(demo_state *s);
const char *demo_checkout(demo_state *s);
const char *demo_approve(demo_state *s);
void demo_safe(demo_state *s, const char *reason);
void demo_health(demo_state *s, bool ok);
