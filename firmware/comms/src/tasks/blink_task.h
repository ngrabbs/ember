/*
 * Blink task — toggles the Pico module's onboard LED on a fixed
 * cadence so a glance at the board confirms the comms firmware booted
 * and the FreeRTOS scheduler is alive.
 *
 * Deliberately uses GP25 on the module rather than the board's
 * TX_ACTIVE / RX_ACTIVE LEDs: those two indicate RF state and must
 * stay truthful, and GP25 also works on a bare Pico for bench work.
 */

#pragma once

#include "FreeRTOS.h"
#include "task.h"

/* Create and start the blink task. Returns pdPASS on success. */
BaseType_t comms_blink_task_start(UBaseType_t priority);
