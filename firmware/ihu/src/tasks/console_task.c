#include "tasks/console_task.h"

#include <stdio.h>

#include "FreeRTOS.h"
#include "task.h"
#include "pico/stdlib.h"

#define CONSOLE_PERIOD_MS       5000
#define CONSOLE_TASK_STACK_WORDS 512
#define CONSOLE_TASK_NAME       "console"

static volatile bool s_quiet = false;

void ihu_console_set_quiet(bool quiet) { s_quiet = quiet; }
bool ihu_console_is_quiet(void)        { return s_quiet; }

static void console_task(void *pvParameters) {
    (void)pvParameters;

    /* Give USB CDC enumeration a moment so the first heartbeat lands
     * in the host's terminal instead of getting eaten before the
     * device shows up. */
    vTaskDelay(pdMS_TO_TICKS(1500));
    printf("[ihu] console up — FreeRTOS scheduler running\n");

    uint32_t tick = 0;
    for (;;) {
        if (!s_quiet) {
            TickType_t uptime_ticks = xTaskGetTickCount();
            uint32_t uptime_ms = (uint32_t)(uptime_ticks * portTICK_PERIOD_MS);
            UBaseType_t task_count = uxTaskGetNumberOfTasks();

            printf("[ihu] heartbeat #%lu  uptime=%lu ms  tasks=%lu  free_heap=%u\n",
                   (unsigned long)tick++,
                   (unsigned long)uptime_ms,
                   (unsigned long)task_count,
                   (unsigned)xPortGetFreeHeapSize());
        }
        vTaskDelay(pdMS_TO_TICKS(CONSOLE_PERIOD_MS));
    }
}

BaseType_t ihu_console_task_start(UBaseType_t priority) {
    return xTaskCreate(console_task, CONSOLE_TASK_NAME,
                       CONSOLE_TASK_STACK_WORDS, NULL, priority, NULL);
}
