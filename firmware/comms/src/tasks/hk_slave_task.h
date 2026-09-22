/*
 * Housekeeping I2C slave task — the comms board's answer to "are you
 * alive, and what do you see?"
 *
 * The IHU is master on the shared CSKB housekeeping bus and already
 * polls the EPS charger there. This task makes the comms board look
 * like one more addressable device on that bus: it answers at
 * COMMS_HK_I2C_ADDR and serves a small register file describing what
 * the boot self-test found and how the board is doing since.
 *
 * Register map, bus address, and byte order are defined once in
 * firmware/shared/comms_hk_proto.h and shared with the IHU tree.
 *
 * ── How it is split ──────────────────────────────────────────────
 *
 * The register file is served from an ISR, because an I2C slave has no
 * choice: the master clocks bytes out whenever it likes and the slave
 * has microseconds to respond. The ISR therefore does nothing but copy
 * bytes to and from a RAM buffer — no printf, no I2C of its own, no
 * FreeRTOS calls.
 *
 * Everything that is slow or blocking — reading the self-test result,
 * asking FreeRTOS for the heap and task count — happens in the task
 * body, which refreshes that buffer on a timer. So the IHU always
 * reads a value that is at most COMMS_HK_REFRESH_MS old, and never
 * waits on this board to go compute one.
 *
 * ── What it deliberately does not do ─────────────────────────────
 *
 * There are no command registers. The only writable field is the
 * scratch echo. Commanding the transmitter belongs on the SPI link
 * with framing and a CRC behind it, not on a housekeeping bus where a
 * single corrupted byte could key the PA.
 */

#pragma once

#include <stdbool.h>
#include <stdint.h>

#include "FreeRTOS.h"
#include "task.h"

BaseType_t comms_hk_slave_task_start(UBaseType_t priority);

/* Number of I2C transactions the master has completed with us since
 * boot. Zero means the IHU has never successfully talked to this
 * board — useful in the console heartbeat as a link-liveness readout
 * that needs no cooperation from the other end. */
uint16_t comms_hk_slave_xact_count(void);

/* True once the slave peripheral is configured and answering. */
bool comms_hk_slave_is_up(void);
