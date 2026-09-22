#include "tasks/console_task.h"

#include <stdio.h>

#include "FreeRTOS.h"
#include "task.h"
#include "pico/stdlib.h"

#include "tasks/hk_slave_task.h"
#include "tasks/selftest_task.h"

#define CONSOLE_PERIOD_MS        5000
#define CONSOLE_TASK_STACK_WORDS 512
#define CONSOLE_TASK_NAME        "console"

/* Hold off until the self-test has published its report, so a heartbeat
 * cannot land in the middle of the boot banner. Waiting on the actual
 * result rather than a guessed delay keeps this correct however long
 * the self-test spends waiting for a USB CDC host to show up.
 *
 * Capped so a self-test that somehow never finishes costs us the
 * heartbeat's ordering, not the heartbeat itself. */
#define CONSOLE_SELFTEST_WAIT_MS 15000
#define CONSOLE_SELFTEST_POLL_MS   100

static volatile bool s_quiet = false;

void comms_console_set_quiet(bool quiet) { s_quiet = quiet; }
bool comms_console_is_quiet(void)        { return s_quiet; }

static void console_task(void *pvParameters) {
    (void)pvParameters;

    comms_selftest_result_t ignored;
    for (int waited = 0; waited < CONSOLE_SELFTEST_WAIT_MS;
         waited += CONSOLE_SELFTEST_POLL_MS) {
        if (comms_selftest_get_result(&ignored)) {
            break;
        }
        vTaskDelay(pdMS_TO_TICKS(CONSOLE_SELFTEST_POLL_MS));
    }

    uint32_t tick = 0;
    for (;;) {
        if (!s_quiet) {
            TickType_t uptime_ticks = xTaskGetTickCount();
            uint32_t uptime_ms = (uint32_t)(uptime_ticks * portTICK_PERIOD_MS);
            UBaseType_t task_count = uxTaskGetNumberOfTasks();

            /* ihu= is the housekeeping-link transaction count. It is
             * the one number here that says something about the other
             * end of the stack: still 0 after the IHU has booted means
             * the bus is not carrying traffic, and it needs no
             * cooperation from the IHU to be useful. */
            printf("[comms] heartbeat #%lu  uptime=%lu ms  tasks=%lu  "
                   "free_heap=%u  ihu=%u xacts\n",
                   (unsigned long)tick++,
                   (unsigned long)uptime_ms,
                   (unsigned long)task_count,
                   (unsigned)xPortGetFreeHeapSize(),
                   (unsigned)comms_hk_slave_xact_count());
        }
        vTaskDelay(pdMS_TO_TICKS(CONSOLE_PERIOD_MS));
    }
}

BaseType_t comms_console_task_start(UBaseType_t priority) {
    return xTaskCreate(console_task, CONSOLE_TASK_NAME,
                       CONSOLE_TASK_STACK_WORDS, NULL, priority, NULL);
}
