#include "config/i2c0_bus.h"

#include "FreeRTOS.h"
#include "semphr.h"
#include "pico/stdlib.h"
#include "hardware/gpio.h"
#include "hardware/i2c.h"

#include "config/pinmap.h"

static SemaphoreHandle_t s_bus_mutex = NULL;

void ihu_i2c0_bus_init(void) {
    i2c_init(IHU_I2C_EPS_INSTANCE, IHU_I2C_EPS_HZ);
    gpio_set_function(IHU_I2C_EPS_SDA_GPIO, GPIO_FUNC_I2C);
    gpio_set_function(IHU_I2C_EPS_SCL_GPIO, GPIO_FUNC_I2C);
    /* On-MCU pull-ups for bench bring-up. Flight EPS has dedicated
     * 4.7 k pull-ups; enabling these is harmless (they're 50-80 k weak). */
    gpio_pull_up(IHU_I2C_EPS_SDA_GPIO);
    gpio_pull_up(IHU_I2C_EPS_SCL_GPIO);

    s_bus_mutex = xSemaphoreCreateMutex();
    /* No recovery path if this fails — it means the heap was exhausted
     * before a single task existed. main()'s caller checks for NULL by
     * way of every lock attempt failing, and the console says so. */
}

bool ihu_i2c0_lock(uint32_t timeout_ms) {
    if (s_bus_mutex == NULL) {
        return false;
    }
    return xSemaphoreTake(s_bus_mutex, pdMS_TO_TICKS(timeout_ms)) == pdTRUE;
}

void ihu_i2c0_unlock(void) {
    if (s_bus_mutex != NULL) {
        xSemaphoreGive(s_bus_mutex);
    }
}
