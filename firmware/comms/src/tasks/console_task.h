/*
 * Console task — periodic heartbeat to stdio so the operator can
 * confirm the firmware is alive and watch task scheduling.
 *
 * For v0.1 this is a one-way print. A real CLI (line buffer + command
 * dispatcher, as in firmware/ihu/src/cli/) lands alongside the TX/RX
 * state machines — see Workstream C in the board README.
 */

#pragma once

#include <stdbool.h>

#include "FreeRTOS.h"
#include "task.h"

BaseType_t comms_console_task_start(UBaseType_t priority);

/* Suppress / re-enable the periodic heartbeat line. Useful when
 * watching RF bring-up output so log spam doesn't step on it. */
void comms_console_set_quiet(bool quiet);
bool comms_console_is_quiet(void);
