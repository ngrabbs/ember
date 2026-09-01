/*
 * Console task — periodic heartbeat to USB CDC stdio so the operator
 * can confirm the firmware is alive and watch task scheduling.
 *
 * For v0.1 this is a one-way print. A real CLI (line buffer +
 * command dispatcher) lands later under Workstream D in
 * firmware/ihu/README.md.
 */

#pragma once

#include <stdbool.h>

#include "FreeRTOS.h"
#include "task.h"

BaseType_t ihu_console_task_start(UBaseType_t priority);

/* Suppress / re-enable the periodic heartbeat line. Useful when
 * typing at the CLI so log spam doesn't step on the prompt. */
void ihu_console_set_quiet(bool quiet);
bool ihu_console_is_quiet(void);
