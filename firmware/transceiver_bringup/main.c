/* Y24 ordered-board bring-up: internal loopback and bounded CAN A receive windows; RF stays muted. */
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

/* SPI mode 0, with explicit chip-select setup/hold delays. */
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

static void can_write(unsigned cs, uint8_t reg, uint8_t value) {
    uint8_t tx[] = {0x02, reg, value}, rx[3];
    gpio_put(cs, false);
    sleep_us(2);
    spi_write_read_blocking(spi0, tx, rx, 3);
    sleep_us(2);
    gpio_put(cs, true);
}

static bool can_mode(unsigned cs, uint8_t mode) {
    /* Mode selection used by bounded tests. One-shot on, CAN CLKOUT off. */
    if (mode != 0x80 && mode != 0x40 && mode != 0x60 && mode != 0) return false;
    can_write(cs, 0x0f, mode | 0x08);
    for (unsigned n = 0; n < 100; ++n) {
        if ((can_read(cs, 0x0e) & 0xe0) == mode &&
            (can_read(cs, 0x0f) & 0xe0) == mode) return true;
        sleep_ms(1);
    }
    return false;
}

static bool independent_registers(void) {
    if (!configuration_mode(can_read(14, 0x0e), can_read(14, 0x0f)) ||
        !configuration_mode(can_read(15, 0x0e), can_read(15, 0x0f))) return false;
    /* TXB0D0 is inactive data RAM; no TXREQ is set by this test. */
    uint8_t a = can_read(14, 0x36), b = can_read(15, 0x36);
    can_write(14, 0x36, 0x55); can_write(15, 0x36, 0xaa);
    bool ok = can_read(14, 0x36) == 0x55 && can_read(15, 0x36) == 0xaa;
    can_write(14, 0x36, 0xaa); can_write(15, 0x36, 0x55);
    ok &= can_read(14, 0x36) == 0xaa && can_read(15, 0x36) == 0x55;
    can_write(14, 0x36, a); can_write(15, 0x36, b);
    return ok && can_read(14, 0x36) == a && can_read(15, 0x36) == b;
}

/* Return a stage code: 0 pass, 1 config, 2 loopback mode, 3 timeout,
 * 4 frame mismatch, 5 return-to-config. Caller holds reset on any failure. */
static uint8_t loop_received[2][13];
static unsigned loopback(unsigned cs, uint8_t tag) {
    if (!can_mode(cs, 0x80)) return 1;
    can_write(cs, 0x2a, 0); can_write(cs, 0x29, 0xf0); can_write(cs, 0x28, 0x86);
    can_write(cs, 0x2b, 0); /* Interrupts disabled; poll flags. */
    can_write(cs, 0x2c, 0);
    can_write(cs, 0x60, 0x60); can_write(cs, 0x70, 0x60); /* Accept all. */
    can_write(cs, 0x30, 0);
    /* Standard ID 0x321, DLC 8, distinguishable payload for each controller. */
    uint8_t frame[] = {0x64, 0x20, 0, 0, 8, tag, 0, 0xff, 0x55, 0xaa, 0x12, 0x34, 0x78};
    for (unsigned i = 0; i < sizeof(frame); ++i) can_write(cs, 0x31+i, frame[i]);
    if (!can_mode(cs, 0x40)) return 2;
    /* TXREQ only after confirmed internal loopback; STBY stays asserted. */
    can_write(cs, 0x30, 0x08);
    unsigned n;
    for (n = 0; n < 100; ++n) {
        if ((can_read(cs, 0x2c) & 0x05) == 0x05 && !(can_read(cs, 0x30) & 8)) break;
        sleep_ms(1);
    }
    if (n == 100) return 3;
    uint8_t *received = loop_received[cs == 14 ? 0 : 1];
    for (unsigned i = 0; i < sizeof(frame); ++i) {
        received[i] = can_read(cs, 0x61+i);
    }
    /* Standard data frame: EID bytes and SIDL EID bits are not meaningful. */
    bool match = received[0] == frame[0] && (received[1] & 0xf8) == frame[1]
                 && (received[4] & 0x4f) == 8;
    for (unsigned i = 5; i < sizeof(frame); ++i) match &= received[i] == frame[i];
    if (!match) return 4;
    can_write(cs, 0x2c, 0);
    if (!can_mode(cs, 0x80)) return 5;
    return 0;
}

/* Console l=listen-only, n=receive with ACK; both bounded to ten seconds. */
static bool listen_a(bool acknowledge) {
    uint8_t mode = acknowledge ? 0 : 0x60;
    if (!configuration_mode(can_read(14, 0x0e), can_read(14, 0x0f))) return false;
    if (can_read(14, 0x2a) != 0 || can_read(14, 0x29) != 0xf0 ||
        can_read(14, 0x28) != 0x86) return false;
    can_write(14, 0x2c, 0); can_write(14, 0x2d, 0);
    can_write(14, 0x60, 0x64); /* RX0 rollover into RX1. */
    can_write(14, 0x30, 0); can_write(14, 0x40, 0); can_write(14, 0x50, 0);
    if (!can_mode(14, mode)) return false;
    gpio_put(2, false); /* All TX buffers inactive before connecting to bus. */
    printf("[listen_A] START 500000bit/s 10s ACK=%u no_application_TX\n", acknowledge);
    uint64_t end = time_us_64() + 10000000;
    unsigned frames = 0;
    uint8_t captured[32][13];
    bool mode_ok = true;
    while (time_us_64() < end) {
        if ((can_read(14, 0x0e) & 0xe0) != mode) {mode_ok = false; break;}
        uint8_t flags = can_read(14, 0x2c);
        for (unsigned buffer = 0; buffer < 2; ++buffer) {
            if (!(flags & (1u << buffer))) continue;
            uint8_t base = buffer ? 0x71 : 0x61;
            uint8_t read_tx[15] = {3, base}, read_rx[15];
            gpio_put(14, false); sleep_us(2);
            spi_write_read_blocking(spi0, read_tx, read_rx, 15);
            sleep_us(2); gpio_put(14, true);
            if (frames < 32)
                for (unsigned i = 0; i < 13; ++i) captured[frames][i] = read_rx[i+2];
            /* BIT MODIFY clears only the consumed receive flag. */
            uint8_t tx[] = {5, 0x2c, (uint8_t)(1u << buffer), 0}, rx[4];
            gpio_put(14, false); sleep_us(2);
            spi_write_read_blocking(spi0, tx, rx, 4);
            sleep_us(2); gpio_put(14, true);
            ++frames;

        }
        sleep_ms(1);
    }
    gpio_put(2, true); /* Stop physical reception before changing modes. */
    uint8_t errors = can_read(14, 0x2d);
    bool restored = can_mode(14, 0x80);
    for (unsigned f = 0; f < frames && f < 32; ++f) {
        printf("[listen_A] raw");
        for (unsigned i = 0; i < 13; ++i) printf(" %02X", captured[f][i]);
        printf("\n");
    }
    printf("[listen_A] END frames=%u EFLG=%02X mode_ok=%u restored=%u\n",
           frames, errors, mode_ok, restored);
    return mode_ok && restored;
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
    spi_init(spi0, 1000000);
    spi_set_format(spi0, 8, SPI_CPOL_0, SPI_CPHA_0, SPI_MSB_FIRST);
    gpio_set_function(4, GPIO_FUNC_SPI);
    gpio_set_function(6, GPIO_FUNC_SPI);
    gpio_set_function(7, GPIO_FUNC_SPI);
    sleep_ms(10); /* Hardware reset held low well beyond minimum pulse width. */
    gpio_put(8, true);
    gpio_put(9, true);
    sleep_ms(10); /* Oscillator startup; mode is checked rather than assumed. */
    unsigned count = 0;
    bool registers_ok = independent_registers();
    unsigned aloop = 6, bloop = 6; /* 6 = skipped after independent-register failure. */
    if (registers_ok) {
        aloop = loopback(14, 0xa1);
        if (aloop) gpio_put(8, false);
        bloop = loopback(15, 0xb2);
    }
    bool afailed = !registers_ok || aloop, bfailed = !registers_ok || bloop;
    if (afailed) gpio_put(8, false);
    if (bfailed) gpio_put(9, false);
    while (true) {
        int command = getchar_timeout_us(0);
        if ((command == 'l' || command == 'n') && !afailed) {
            if (!listen_a(command == 'n')) {gpio_put(2, true); gpio_put(8, false); afailed = true;}
        }
        bool clocks_disabled = disable_clocks();
        uint8_t as = can_read(14, 0x0e), ac = can_read(14, 0x0f);
        uint8_t bs = can_read(15, 0x0e), bc = can_read(15, 0x0f);
        bool aok = configuration_mode(as, ac), bok = configuration_mode(bs, bc);
        /* Unexpected state is latched safe until the next reboot. */
        afailed |= !aok; bfailed |= !bok;
        if (afailed) gpio_put(8, false);
        if (bfailed) gpio_put(9, false);
        printf("[y24-safe-v4] #%u TX=0 RX=0 CAN_A/B=standby "
               "Si5351_disable=%s ADC1_raw=%u\n", ++count,
               clocks_disabled ? "verified_0xFF" : "NOT_VERIFIED",
               (unsigned)adc_read());
        printf("[can] A STAT=%02X CTRL=%02X %s; B STAT=%02X CTRL=%02X %s\n",
               as, ac, !afailed ? "CONFIG" : "FAIL_RESET_HELD",
               bs, bc, !bfailed ? "CONFIG" : "FAIL_RESET_HELD");
        printf("[selftest] independent_registers=%s loopback_A=%u loopback_B=%u (0=PASS)\n",
               registers_ok ? "PASS" : "FAIL", aloop, bloop);
        for (unsigned k = 0; k < 2; ++k) {
            printf("[loop_rx_%c]", k ? 'B' : 'A');
            for (unsigned j = 0; j < 13; ++j) printf(" %02X", loop_received[k][j]);
            printf("\n");
        }
        sleep_ms(1000);
    }
}
