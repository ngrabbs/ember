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

            /* The hk= field reports the housekeeping link from this
             * side, and splits the two failures that otherwise look
             * identical from the IHU:
             *
             *   hk=down     the slave never initialised — a firmware
             *               problem on THIS board
             *   hk=0 xacts  the slave is up and listening but has
             *               never been clocked — wiring, not firmware
             *
             * Without this you need the boot banner to tell them
             * apart, and by the time anyone is debugging the link the
             * banner has long scrolled off. */
            printf("[comms] heartbeat #%lu  uptime=%lu ms  tasks=%lu  "
                   "free_heap=%u  hk=%s %u xacts\n",
                   (unsigned long)tick++,
                   (unsigned long)uptime_ms,
                   (unsigned long)task_count,
                   (unsigned)xPortGetFreeHeapSize(),
                   comms_hk_slave_is_up() ? "up" : "DOWN",
                   (unsigned)comms_hk_slave_xact_count());
        }
        vTaskDelay(pdMS_TO_TICKS(CONSOLE_PERIOD_MS));
    }
}

BaseType_t comms_console_task_start(UBaseType_t priority) {
    return xTaskCreate(console_task, CONSOLE_TASK_NAME,
                       CONSOLE_TASK_STACK_WORDS, NULL, priority, NULL);
}
