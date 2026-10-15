/* Y24 ordered-board bring-up: deliberately no transmit/clock-enable commands. */
#include <stdio.h>
#include "pico/stdlib.h"
#include "hardware/adc.h"
#include "hardware/i2c.h"
#include "hardware/spi.h"

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

/* Read-only SPI transactions: never issue a write, RTS, or mode change. */
static uint8_t can_read(unsigned cs, uint8_t reg) {
    uint8_t tx[] = {0x03, reg, 0}, rx[3] = {0};
    gpio_put(cs, false);
    sleep_us(2);
    spi_write_read_blocking(spi0, tx, rx, 3);
    sleep_us(2);
    gpio_put(cs, true);
    return rx[2];
}

static bool configuration_mode(uint8_t stat, uint8_t ctrl) {
    return (stat & 0xe0) == 0x80 && (ctrl & 0xe0) == 0x80;
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
    output(6, false);  /* CAN_SPI_SCK */
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
    spi_init(spi0, 100000);
    spi_set_format(spi0, 8, SPI_CPOL_0, SPI_CPHA_0, SPI_MSB_FIRST);
    gpio_set_function(4, GPIO_FUNC_SPI);
    gpio_set_function(6, GPIO_FUNC_SPI);
    gpio_set_function(7, GPIO_FUNC_SPI);
    sleep_ms(10); /* Hardware reset held low well beyond minimum pulse width. */
    gpio_put(8, true);
    gpio_put(9, true);
    sleep_ms(10); /* Oscillator startup; mode is checked rather than assumed. */
    unsigned count = 0;
    bool afailed = false, bfailed = false;
    while (true) {
        bool clocks_disabled = disable_clocks();
        uint8_t as = can_read(14, 0x0e), ac = can_read(14, 0x0f);
        uint8_t bs = can_read(15, 0x0e), bc = can_read(15, 0x0f);
        bool aok = configuration_mode(as, ac), bok = configuration_mode(bs, bc);
        /* Unexpected state is latched safe until the next reboot. */
        afailed |= !aok; bfailed |= !bok;
        if (afailed) gpio_put(8, false);
        if (bfailed) gpio_put(9, false);
        printf("[y24-safe-v2] #%u TX=0 RX=0 CAN_A/B=standby "
               "Si5351_disable=%s ADC1_raw=%u\n", ++count,
               clocks_disabled ? "verified_0xFF" : "NOT_VERIFIED",
               (unsigned)adc_read());
        printf("[can] A STAT=%02X CTRL=%02X %s; B STAT=%02X CTRL=%02X %s\n",
               as, ac, !afailed ? "CONFIG" : "FAIL_RESET_HELD",
               bs, bc, !bfailed ? "CONFIG" : "FAIL_RESET_HELD");
        sleep_ms(1000);
    }
}
