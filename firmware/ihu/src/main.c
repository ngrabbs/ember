/*
 * IHU — application entry point.
 *
 * Brings up Pico stdio (UART on GP0/GP1), creates the three v0.1 tasks
 * (console heartbeat, LED blink, I2C bus scan), and hands control
 * to the FreeRTOS scheduler.
 *
 * New tasks (SPI to comms, EPS telemetry, command dispatch, watchdog
 * feed) hook in here as separate ihu_*_task_start() calls.
 *
 * Diagnostics:
 *   - 3 slow LED blinks at boot, BEFORE vTaskStartScheduler() runs,
 *     so you can confirm main() reached the end even if the scheduler
 *     fails to start.
 *   - vApplicationStackOverflowHook / vApplicationMallocFailedHook
 *     fast-blink the LED forever if either fires — converts the
 *     usual "Pico just sits there" failure mode into a visible signal.
 */

#include <stdio.h>

#include "FreeRTOS.h"
#include "task.h"
#include "pico/stdlib.h"

#include "config/pinmap.h"
#include "cli/cli.h"
#include "tasks/blink_task.h"
#include "tasks/console_task.h"
#include "tasks/eps_monitor_task.h"

/* Task priorities — lowest to highest. tskIDLE_PRIORITY == 0.
 * All v0.1 tasks at the same low priority; round-robin time slicing
 * handles fairness. Raise individual tasks once we have hard timing
 * requirements (e.g., SPI link service). */
#define IHU_TASK_PRIORITY_BLINK   (tskIDLE_PRIORITY + 1)
#define IHU_TASK_PRIORITY_CONSOLE (tskIDLE_PRIORITY + 1)
#define IHU_TASK_PRIORITY_EPS     (tskIDLE_PRIORITY + 1)
#define IHU_TASK_PRIORITY_CLI     (tskIDLE_PRIORITY + 2)  /* one above the periodic tasks */

/* Pre-scheduler "we got here" blink: 3 slow on/off pulses on GP25. */
static void pre_scheduler_led_check(void) {
    gpio_init(IHU_LED_GPIO);
    gpio_set_dir(IHU_LED_GPIO, GPIO_OUT);
    for (int i = 0; i < 3; ++i) {
        gpio_put(IHU_LED_GPIO, 1);
        sleep_ms(150);
        gpio_put(IHU_LED_GPIO, 0);
        sleep_ms(150);
    }
}

/* Lock the LED on solid, then loop forever. Used by the panic hooks. */
static void __attribute__((noreturn)) panic_blink_forever(void) {
    gpio_init(IHU_LED_GPIO);
    gpio_set_dir(IHU_LED_GPIO, GPIO_OUT);
    for (;;) {
        gpio_put(IHU_LED_GPIO, 1);
        busy_wait_us_32(80000);
        gpio_put(IHU_LED_GPIO, 0);
        busy_wait_us_32(80000);
    }
}

void vApplicationStackOverflowHook(TaskHandle_t xTask, char *pcTaskName) {
    (void)xTask;
    printf("\n[ihu][PANIC] stack overflow in task '%s'\n", pcTaskName);
    panic_blink_forever();
}

void vApplicationMallocFailedHook(void) {
    printf("\n[ihu][PANIC] FreeRTOS heap exhausted (pvPortMalloc returned NULL)\n");
    panic_blink_forever();
}

int main(void) {
    stdio_init_all();

    /* Visible "main() reached" signal — independent of scheduler state. */
    pre_scheduler_led_check();

    printf("\n[ihu] booting (build " __DATE__ " " __TIME__ ")\n");

    if (ihu_console_task_start(IHU_TASK_PRIORITY_CONSOLE) != pdPASS) {
        printf("[ihu][FATAL] console task creation failed\n");
        panic_blink_forever();
    }
    if (ihu_blink_task_start(IHU_TASK_PRIORITY_BLINK) != pdPASS) {
        printf("[ihu][FATAL] blink task creation failed\n");
        panic_blink_forever();
    }
    if (ihu_eps_monitor_task_start(IHU_TASK_PRIORITY_EPS) != pdPASS) {
        printf("[ihu][FATAL] eps monitor task creation failed\n");
        panic_blink_forever();
    }
    if (ihu_cli_task_start(IHU_TASK_PRIORITY_CLI) != pdPASS) {
        printf("[ihu][FATAL] cli task creation failed\n");
        panic_blink_forever();
    }

    printf("[ihu] tasks created, starting scheduler\n");
    vTaskStartScheduler();

    /* vTaskStartScheduler should never return; if it does the heap is
     * exhausted or some configASSERT tripped. */
    printf("[ihu][FATAL] scheduler returned\n");
    panic_blink_forever();
}
