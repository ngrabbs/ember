/*
 * Boot self-test task — the first thing the comms board does after the
 * scheduler starts, and the only thing that touches hardware before the
 * board is allowed to do anything else.
 *
 * It runs once, prints a boot report to the console, publishes the
 * result for other tasks to read, and deletes itself.
 *
 * Three jobs, in order:
 *
 *   1. Safe the outputs. Every RP2040 pin that drives something on this
 *      board is put in a known state before anything else runs — the
 *      XOR modulator input low, the T/R control low (RX), COMMS_IRQ
 *      de-asserted high so the IHU does not see a spurious data-ready.
 *
 *   2. Detect what is actually populated. The Si5351A is the only
 *      digitally addressable part on the board, so an i2c0 bus scan
 *      plus a read-only status probe is most of the story. The RX
 *      baseband DC bias on ADC1 covers the analog half: the MCP6022
 *      gain stage idles at mid-supply, so reading ~1.65 V there means
 *      the RX chain is populated and powered.
 *
 *   3. Report. One line per check, then a pass/fail summary.
 *
 * It deliberately does NOT configure or enable the Si5351A outputs.
 * CLK0 feeds the XOR modulator and the tripler, so enabling it puts a
 * carrier into the PA; that belongs behind an explicit command, not in
 * the boot path.
 */

#pragma once

#include <stdbool.h>
#include <stdint.h>

#include "FreeRTOS.h"
#include "task.h"

#include "si5351a.h"

/* Outcome of one boot check. */
typedef enum {
    COMMS_CHECK_PASS = 0,  /* found, and healthy */
    COMMS_CHECK_WARN,      /* found, but not what we expected */
    COMMS_CHECK_FAIL,      /* not found */
} comms_check_t;

/* Snapshot of the boot report, published once the self-test finishes. */
typedef struct {
    bool            complete;        /* self-test has run to completion */
    bool            watchdog_reboot; /* previous reset was a watchdog timeout */
    uint8_t         i2c_device_count;
    comms_check_t   si5351;
    si5351_status_t si5351_status;
    comms_check_t   rx_baseband;
    float           rx_baseband_v;   /* measured DC bias, volts */
} comms_selftest_result_t;

BaseType_t comms_selftest_task_start(UBaseType_t priority);

/* Copy the boot report into `out`. Returns false if the self-test has
 * not finished yet. Safe to call from any task. */
bool comms_selftest_get_result(comms_selftest_result_t *out);
