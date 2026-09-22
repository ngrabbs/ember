/*
 * i2c0 housekeeping bus ownership.
 *
 * i2c0 is the shared CSKB housekeeping bus (H1.41 SDA_SYS / H1.43
 * SCL_SYS). Until now the EPS monitor task was its only periodic user
 * and the CLI reached around it for one-shot register dumps — which
 * already raced, but rarely enough to get away with.
 *
 * With the comms board answering on the same bus there are two
 * periodic pollers, and the race stops being theoretical: the RP2040
 * I2C block holds one transaction's state at a time, so a preemption
 * between the register-pointer write and the repeated-START read
 * splices two transactions together and both sides get garbage. It
 * does not fail loudly — it returns plausible-looking wrong numbers,
 * which on a telemetry bus is the worst kind of bug.
 *
 * So every transaction on i2c0 goes between ihu_i2c0_lock() and
 * ihu_i2c0_unlock(). The lock covers a whole logical transaction
 * (pointer write AND the read that follows), not each SDK call.
 *
 * The mutex is created before the scheduler starts, so any task can
 * take it from its first line without a creation race.
 */

#pragma once

#include <stdbool.h>

#include "FreeRTOS.h"

/* Bring up the i2c0 peripheral, its pins, and the bus mutex.
 * Call once from main() BEFORE vTaskStartScheduler(). */
void ihu_i2c0_bus_init(void);

/* Take the bus for one logical transaction. Returns false if the lock
 * could not be acquired within `timeout_ms` — treat that exactly like
 * an I2C error, because something is wedged and the data you would
 * have read is not trustworthy either way.
 *
 * Do not call before ihu_i2c0_bus_init(); it returns false rather
 * than asserting, so a caller that gets the ordering wrong sees a bus
 * failure rather than a hard fault. */
bool ihu_i2c0_lock(uint32_t timeout_ms);

/* Release the bus. Only call after a successful ihu_i2c0_lock(). */
void ihu_i2c0_unlock(void);

/* Default wait for a housekeeping transaction. Generous — the longest
 * thing anyone does on this bus is the boot-time 126-address scan,
 * which at 100 kHz with everything NACKing takes well under a second. */
#define IHU_I2C0_LOCK_TIMEOUT_MS   1000

/* The bus scan holds the lock for its whole sweep so a poll cannot
 * interleave with it and confuse the "who answered" result. */
#define IHU_I2C0_SCAN_TIMEOUT_MS   3000
