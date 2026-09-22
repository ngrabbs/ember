/*
 * Comms monitor task — the IHU's periodic ping of the comms board.
 *
 * Mirrors eps_monitor_task: poll one device on the shared CSKB
 * housekeeping I2C bus on a fixed cadence, publish a snapshot the CLI
 * can read on demand, and print a line per poll unless silenced.
 *
 * Two things happen per cycle:
 *
 *   1. A round-trip ping. A 32-bit token goes out to the comms board's
 *      scratch register and has to come back unchanged. That exercises
 *      the write path, the comms slave ISR, and the read path — unlike
 *      an address probe, which only proves something ACKed.
 *
 *   2. A status block read: self-test outcome, Si5351A presence and
 *      PLL lock, RX baseband bias, uptime, heap, task count.
 *
 * Link state is tracked across polls so a board that drops off the bus
 * is reported once, when it happens, rather than as one identical
 * error line every cycle forever.
 *
 * This task shares i2c0 with eps_monitor_task. Every transaction goes
 * through the bus lock in config/i2c0_bus.h — see the note there.
 */

#pragma once

#include <stdbool.h>
#include <stdint.h>

#include "FreeRTOS.h"
#include "task.h"

#include "drivers/comms_link.h"

BaseType_t ihu_comms_monitor_task_start(UBaseType_t priority);

/* Rolled-up view of the link, for the CLI. */
typedef struct {
    bool     ever_seen;      /* the comms board has answered at least once */
    bool     link_up;        /* the most recent poll succeeded */
    uint32_t polls;          /* polls attempted */
    uint32_t failures;       /* consecutive failures; reset on success */
    uint32_t last_ok_ms;     /* IHU uptime at the last good poll */
    uint32_t last_rtt_us;    /* round-trip time of the last good ping */
} comms_link_health_t;

/* Copy the most recent status snapshot into `out`. Returns false if
 * the comms board has never answered — the snapshot may otherwise be
 * stale, but it is the last known good one, same contract as
 * ihu_eps_get_latest_telemetry(). */
bool ihu_comms_get_latest_status(comms_link_status_t *out);

/* Copy the link health counters. Always succeeds. */
void ihu_comms_get_health(comms_link_health_t *out);

/* Suppress / re-enable the periodic per-poll print. The poll itself
 * keeps running, so the snapshot stays fresh for the `comms` command. */
void ihu_comms_set_quiet(bool quiet);
