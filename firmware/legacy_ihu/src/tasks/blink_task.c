#include "tasks/blink_task.h"

#include "FreeRTOS.h"
#include "task.h"
#include "pico/stdlib.h"

#include "config/pinmap.h"

/* 1 Hz heartbeat: 500 ms on, 500 ms off. */
#define BLINK_HALF_PERIOD_MS    500
#define BLINK_TASK_STACK_WORDS  256
#define BLINK_TASK_NAME         "blink"

static void blink_task(void *pvParameters) {
    (void)pvParameters;

    gpio_init(IHU_LED_GPIO);
    gpio_set_dir(IHU_LED_GPIO, GPIO_OUT);

    bool led_on = false;
    for (;;) {
        led_on = !led_on;
        gpio_put(IHU_LED_GPIO, led_on);
        vTaskDelay(pdMS_TO_TICKS(BLINK_HALF_PERIOD_MS));
    }
}

BaseType_t ihu_blink_task_start(UBaseType_t priority) {
    return xTaskCreate(blink_task, BLINK_TASK_NAME,
                       BLINK_TASK_STACK_WORDS, NULL, priority, NULL);
}
