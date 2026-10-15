/* Y24 ordered-board bring-up: deliberately no transmit/clock-enable commands. */
#include <stdio.h>
#include "pico/stdlib.h"
#include "hardware/adc.h"
#include "hardware/i2c.h"

static void output(unsigned pin, bool level) {
    gpio_init(pin);
    gpio_put(pin, level); /* Set latch before enabling output. */
    gpio_set_dir(pin, GPIO_OUT);
}

/* A successful readback confirms register state, not measured RF silence. */
static bool disable_clocks(void) {
    uint8_t command[] = {3, 0xff};
    uint8_t reg = 3, value = 0;
    if (i2c_write_timeout_us(i2c0, 0x60, command, 2, false, 2000) != 2)
        return false;
    if (i2c_write_timeout_us(i2c0, 0x60, &reg, 1, true, 2000) != 1)
        return false;
    if (i2c_read_timeout_us(i2c0, 0x60, &value, 1, false, 2000) != 1)
        return false;
    return value == 0xff;
}

int main(void) {
    output(10, false); /* TX_ACTIVE: hardware mute asserted. */
    output(11, false); /* RX_ACTIVE */
    output(16, false); /* BPSK_DATA */
    output(8, false);  /* CAN_A_RESETn */
    output(9, false);  /* CAN_B_RESETn */
    output(2, true);   /* CAN_A_STBY */
    output(3, true);   /* CAN_B_STBY */
    output(14, true);  /* CAN_A_CSn */
    output(15, true);  /* CAN_B_CSn */
    output(6, false);  /* CAN_SPI_SCK: no SPI transactions */
    output(7, false);  /* CAN_SPI_MOSI */
    output(12, true);  /* 3V3_IND */
    gpio_init(4);      /* CAN_SPI_MISO remains input. */
    gpio_init(18);     /* CAN_A_INTn */
    gpio_init(19);     /* CAN_B_INTn */
    i2c_init(i2c0, 100000);
    gpio_set_function(20, GPIO_FUNC_I2C);
    gpio_set_function(21, GPIO_FUNC_I2C);
    /* Use board pull-ups; do not feed an unpowered board via internal pull-ups. */
    adc_init();
    adc_gpio_init(27);
    adc_select_input(1);
    stdio_init_all();
    unsigned count = 0;
    while (true) {
        bool clocks_disabled = disable_clocks();
        printf("[y24-safe-v1] #%u TX=0 RX=0 CAN_A/B=reset+standby "
               "Si5351_disable=%s ADC1_raw=%u\n", ++count,
               clocks_disabled ? "verified_0xFF" : "NOT_VERIFIED",
               (unsigned)adc_read());
        sleep_ms(1000);
    }
}
