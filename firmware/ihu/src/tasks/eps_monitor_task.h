/*
 * EPS monitor task — owns the i2c0 bus to the EPS subsystem.
 *
 * v0.1 responsibilities:
 *   1. Initialize the i2c0 peripheral and pin functions.
 *   2. One-time bus scan at boot — logs any device that ACKs.
 *      Sanity check that pull-ups are present and the EPS is alive.
 *   3. Periodically read LTC4162 charger telemetry (V_BAT, V_IN,
 *      V_OUT, I_BAT, I_IN, charger state, system status) and
 *      pretty-print to the UART console.
 *
 * Future: poll MR25H40-style EEPROM / sensor breakouts on the same
 * bus; serialize all transactions behind an i2c0 mutex once we have
 * more than one consumer.
 */

#pragma once

#include <stdbool.h>

#include "FreeRTOS.h"
#include "task.h"

#include "drivers/ltc4162.h"

BaseType_t ihu_eps_monitor_task_start(UBaseType_t priority);

/* Copy the most recent valid telemetry snapshot into `out`.
 * Returns false if the EPS task hasn't completed a successful
 * poll yet (e.g. LTC4162 wasn't detected, or first poll still
 * pending). Safe to call from any task. */
bool ihu_eps_get_latest_telemetry(ltc4162_telemetry_t *out);

/* Suppress / re-enable the periodic per-poll telemetry print.
 * The poll itself still runs (snapshot stays fresh for `eps`),
 * only the console output is silenced. */
void ihu_eps_set_quiet(bool quiet);
