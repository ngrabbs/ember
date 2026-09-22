/*
 * Comms board housekeeping driver (IHU side).
 *
 * The comms board answers on the shared CSKB housekeeping I2C bus at
 * COMMS_HK_I2C_ADDR, presenting a small register file — the same
 * shape as the LTC4162 on the EPS, so this driver reads the same way
 * ltc4162.c does and the two sit side by side in the EPS/comms
 * monitor tasks without special cases.
 *
 * The register map itself is defined once, in
 * firmware/shared/comms_hk_proto.h, and included by both firmware
 * trees. Nothing here duplicates an offset or a bit position.
 *
 * Every function takes the i2c0 bus lock for the duration of one
 * logical transaction — see config/i2c0_bus.h for why that matters
 * now that two tasks poll this bus.
 *
 * Datasheet equivalent: firmware/comms/src/tasks/hk_slave_task.c
 */

#pragma once

#include <stdbool.h>
#include <stdint.h>

#include "hardware/i2c.h"

#include "comms_hk_proto.h"

/* Decoded status block — one poll's worth of comms-board state. */
typedef struct {
    /* Identity, checked on every read. */
    uint8_t  who_am_i;
    uint8_t  proto_ver;
    uint8_t  fw_ver;          /* major<<4 | minor */

    uint8_t  status;          /* raw COMMS_HK_ST_* bitfield */

    /* Decoded status bits, so callers don't re-derive masks. */
    bool     selftest_done;
    bool     si5351_present;
    bool     pll_locked;
    bool     rx_bb_ok;
    bool     tx_active;
    bool     wdt_reboot;
    bool     fault;

    /* Per-check self-test detail: COMMS_HK_CHECK_PASS/WARN/FAIL. */
    uint8_t  check_si5351;
    uint8_t  check_rx_bb;

    uint8_t  i2c_devs;        /* devices on the comms board's own bus */
    uint8_t  tasks;           /* FreeRTOS task count over there */
    uint8_t  si5351_raw;      /* Si5351A register 0, undecoded */

    uint32_t uptime_s;
    uint32_t free_heap;
    uint16_t rx_bb_mv;        /* RX baseband DC bias, millivolts */
    uint16_t xact_count;      /* transactions the comms board has served */
} comms_link_status_t;

/* Does anything ACK at the comms board's address?
 *
 * Address-level only — it says a device is there, not that it is the
 * comms board or that its firmware is sane. comms_link_read_status()
 * is the answer to that. Cheap enough to call before every poll so a
 * disconnected board reports "absent" instead of "read failed". */
bool comms_link_present(i2c_inst_t *i2c, uint8_t addr);

/* Read and decode the whole status block in one burst.
 *
 * Returns false on an I2C error, or if WHO_AM_I / PROTO_VER do not
 * match what this build expects — a wrong device at that address, or
 * two firmware trees that have drifted, are both cases where the
 * decoded fields would be fiction. `out` is still filled in on a
 * version mismatch (the raw identity bytes are valid), so the caller
 * can report exactly what it found; check out->who_am_i to tell the
 * two failure modes apart. */
bool comms_link_read_status(i2c_inst_t *i2c, uint8_t addr,
                            comms_link_status_t *out);

/* Round-trip ping: write `token` to the scratch register, read it
 * back, and confirm it matches.
 *
 * This is the real liveness test. A bare address probe only proves
 * something is pulling SDA low at the right moment; the echo proves
 * the write path, the comms board's slave ISR, and the read path all
 * work end to end. Cheap — one 5-byte write and one 4-byte read.
 *
 * On success, *rtt_us gets the round-trip time in microseconds
 * (may be NULL). Returns false on any I2C error or a mismatched echo;
 * *echoed, when non-NULL, gets whatever actually came back so a
 * mismatch can be reported rather than just denied. */
bool comms_link_ping(i2c_inst_t *i2c, uint8_t addr, uint32_t token,
                     uint32_t *echoed, uint32_t *rtt_us);

/* "PASS" / "WARN" / "FAIL" for a COMMS_HK_CHECK_* value. */
const char *comms_link_check_string(uint8_t check);
