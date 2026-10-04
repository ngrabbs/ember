/* EPS polling shares the housekeeping I2C0 mutex with the comms task.
 * Default operation is read-only. A failed/invalid poll clears the latest
 * snapshot; successful copies are protected by a FreeRTOS critical section.
 * ADC validity does not imply a new ADC conversion on every five-second poll.
 */

#pragma once

#include <stdbool.h>

#include "FreeRTOS.h"
#include "task.h"

#include "drivers/ltc4162.h"

BaseType_t ihu_eps_monitor_task_start(UBaseType_t priority);

/* Copy the most recent valid telemetry snapshot into `out`.
 * Returns false if the EPS task hasn't completed a successful
 * poll yet, or the most recent poll failed. Safe to call from any task. */
bool ihu_eps_get_latest_telemetry(ltc4162_telemetry_t *out);

/* Suppress / re-enable the periodic per-poll telemetry print.
 * The poll itself still runs (snapshot stays fresh for `eps`),
 * only the console output is silenced. */
void ihu_eps_set_quiet(bool quiet);
