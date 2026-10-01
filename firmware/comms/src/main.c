/*
 * ember comms board — application entry point.
 *
 * Brings up Pico stdio (USB CDC and UART0 on GP0/GP1), creates the v0.1
 * tasks, and
 * hands control to the FreeRTOS scheduler. The first task to run is the
 * boot self-test: it safes every output pin, then reports what hardware
 * it can actually find (i2c0 bus scan, Si5351A status probe, RX
 * baseband DC bias) before anything else touches the board.
 *
 * The board also answers the IHU as an I2C slave on the CSKB
 * housekeeping bus (hk_slave_task), so the IHU can ping it and read a
 * status block the same way it reads the EPS charger.
 *
 * The TX/RX state machines, the BPSK bitstream path, and the SPI
 * transport to the IHU hook in here as further comms_*_task_start()
 * calls. Structure mirrors firmware/ihu so the two boards stay legible
 * to the same reader.
 *
 * Diagnostics:
 *   - 3 slow LED blinks at boot, BEFORE vTaskStartScheduler() runs, so
 *     you can confirm main() reached the end even if the scheduler
 *     fails to start.
 *   - vApplicationStackOverflowHook / vApplicationMallocFailedHook
 *     fast-blink the LED forever if either fires — converts the usual
 *     "Pico just sits there" failure mode into a visible signal.
 */

#include <stdio.h>

#include "FreeRTOS.h"
#include "task.h"
#include "pico/stdlib.h"

#include "config/pinmap.h"
#include "tasks/blink_task.h"
#include "tasks/console_task.h"
#include "tasks/hk_slave_task.h"
#include "tasks/selftest_task.h"

/* Task priorities — lowest to highest. tskIDLE_PRIORITY == 0.
 * The self-test runs one priority above the periodic tasks so its boot
 * report is not interleaved with heartbeats; it deletes itself when
 * done and the board settles back to round-robin at the base level.
 *
 * The TX bitstream task will need to sit above all of these when it
 * lands — symbol timing is the one hard real-time deadline on this
 * board. */
#define COMMS_TASK_PRIORITY_BLINK    (tskIDLE_PRIORITY + 1)
#define COMMS_TASK_PRIORITY_CONSOLE  (tskIDLE_PRIORITY + 1)
#define COMMS_TASK_PRIORITY_HK       (tskIDLE_PRIORITY + 1)
#define COMMS_TASK_PRIORITY_SELFTEST (tskIDLE_PRIORITY + 2)

/* Pre-scheduler "we got here" blink: 3 slow on/off pulses on GP25. */
static void pre_scheduler_led_check(void) {
    gpio_init(COMMS_LED_GPIO);
    gpio_set_dir(COMMS_LED_GPIO, GPIO_OUT);
    for (int i = 0; i < 3; ++i) {
        gpio_put(COMMS_LED_GPIO, 1);
        sleep_ms(150);
        gpio_put(COMMS_LED_GPIO, 0);
        sleep_ms(150);
    }
}

/* Fast-blink the LED forever. Used by the panic hooks. */
static void __attribute__((noreturn)) panic_blink_forever(void) {
    gpio_init(COMMS_LED_GPIO);
    gpio_set_dir(COMMS_LED_GPIO, GPIO_OUT);
    for (;;) {
        gpio_put(COMMS_LED_GPIO, 1);
        busy_wait_us_32(80000);
        gpio_put(COMMS_LED_GPIO, 0);
        busy_wait_us_32(80000);
    }
}

void vApplicationStackOverflowHook(TaskHandle_t xTask, char *pcTaskName) {
    (void)xTask;
    printf("\n[comms][PANIC] stack overflow in task '%s'\n", pcTaskName);
    panic_blink_forever();
}

void vApplicationMallocFailedHook(void) {
    printf("\n[comms][PANIC] FreeRTOS heap exhausted (pvPortMalloc returned NULL)\n");
    panic_blink_forever();
}

int main(void) {
    stdio_init_all();

    /* Visible "main() reached" signal — independent of scheduler state. */
    pre_scheduler_led_check();

    /* These two lines reliably reach the UART, but on USB they are sent
     * before the host has enumerated, so expect to lose them there. The
     * self-test's banner is the one that waits for a console. */
    printf("\n[comms] booting (build " __DATE__ " " __TIME__ ")\n");

    if (comms_selftest_task_start(COMMS_TASK_PRIORITY_SELFTEST) != pdPASS) {
        printf("[comms][FATAL] selftest task creation failed\n");
        panic_blink_forever();
    }
    if (comms_console_task_start(COMMS_TASK_PRIORITY_CONSOLE) != pdPASS) {
        printf("[comms][FATAL] console task creation failed\n");
        panic_blink_forever();
    }
    if (comms_blink_task_start(COMMS_TASK_PRIORITY_BLINK) != pdPASS) {
        printf("[comms][FATAL] blink task creation failed\n");
        panic_blink_forever();
    }
    if (comms_hk_slave_task_start(COMMS_TASK_PRIORITY_HK) != pdPASS) {
        printf("[comms][FATAL] hk slave task creation failed\n");
        panic_blink_forever();
    }

    printf("[comms] tasks created, starting scheduler\n");
    vTaskStartScheduler();

    /* vTaskStartScheduler should never return; if it does the heap is
     * exhausted or some configASSERT tripped. */
    printf("[comms][FATAL] scheduler returned\n");
    panic_blink_forever();
}
