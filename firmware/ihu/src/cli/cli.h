/*
 * IHU command-line interface.
 *
 * Reads characters from the UART stdio (GP1 RX) into a line buffer,
 * dispatches whole lines to a registered command table on Enter,
 * and echoes characters back to the user as they type.
 *
 * Output from the CLI shares the same UART with the heartbeat /
 * telemetry log lines. The `quiet` command toggles the heartbeat
 * off so the prompt stays clean while you're typing; `loud` turns
 * it back on. (LTC4162 telemetry polls still print — they're rare
 * enough and the data is the whole point of having a console.)
 *
 * Commands implemented in v0.1:
 *   help              list all commands
 *   stats             uptime, free heap, task count
 *   eps               latest LTC4162 telemetry snapshot
 *   eps raw           raw I2C register dump (hex)
 *   quiet | loud      suppress / re-enable periodic heartbeat
 *   reboot            soft reset via Pico SDK watchdog
 */

#pragma once

#include "FreeRTOS.h"
#include "task.h"

BaseType_t ihu_cli_task_start(UBaseType_t priority);
