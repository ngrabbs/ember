/*
 * Blink task — toggles the onboard Pico LED on a fixed cadence so a
 * glance at the board confirms the IHU firmware booted and the
 * FreeRTOS scheduler is alive.
 */

#pragma once

#include "FreeRTOS.h"
#include "task.h"

/* Create and start the blink task. Returns pdPASS on success. */
BaseType_t ihu_blink_task_start(UBaseType_t priority);
