/* Bounded CLK0 bench tests, Skyworks AN619 rev 0.8.
 * 25 MHz crystal -> PLLA x32 = 800 MHz -> MS0 /80 = 10 MHz.
 * Retain existing crystal load setting: external C1/C2 require measurement.
 * TX variant: PLLA 874 MHz /6 -> tripler target 437 MHz.
 * Only explicit TX test asserts TX_ACTIVE. I2C transfers have 2 ms timeouts. */
#pragma once
static bool clock_read(uint8_t reg, uint8_t *value) {
    return i2c_write_timeout_us(i2c0, 0x60, &reg, 1, true, 2000) == 1 &&
           i2c_read_timeout_us(i2c0, 0x60, value, 1, false, 2000) == 1;
}
static bool clock_write(uint8_t reg, uint8_t value, bool verify) {
    uint8_t tx[] = {reg, value}, actual;
    if (i2c_write_timeout_us(i2c0, 0x60, tx, 2, false, 2000) != 2) return false;
    return !verify || (clock_read(reg, &actual) && actual == value);
}
static bool clock_modify(uint8_t reg, uint8_t mask, uint8_t value) {
    uint8_t old;
    return clock_read(reg, &old) && clock_write(reg, (old & ~mask) | (value & mask), true);
}
static bool clock_stop(void) {
    bool disabled = disable_clocks();
    /* Independent output-power-down attempt even if disable/readback failed. */
    bool down = clock_write(16, 0x80, true);
    return disabled && down;
}
static void clock_status(void) {
    const uint8_t registers[] = {0, 3, 16, 17, 18, 183};
    printf("[clock_status]");
    for (unsigned i=0; i<sizeof(registers); ++i) {
        uint8_t v;
        if (clock_read(registers[i], &v)) printf(" r%u=%02X", registers[i], v);
        else printf(" r%u=ERROR", registers[i]);
    }
    printf("\n");
}
/* Return true only after a full window and verified shutdown. No auto retry. */
static bool clock_window(bool transmit, bool integer_comparison) {
    gpio_put(10, false); gpio_put(11, false); gpio_put(16, false);
    gpio_put(2, true); gpio_put(3, true);
    bool ok = false;
    uint8_t status = 0xff;
    if (!disable_clocks()) goto cleanup;
    if (!clock_read(0, &status) || (status & 0x88)) goto cleanup;
    /* Unused CLK1/CLK2 powered down. CLK0 remains disabled until lock check. */
    for (unsigned reg=16; reg<=23; ++reg)
        if (!clock_write(reg, 0x80, true)) goto cleanup;
    if (!clock_modify(15, 0x0c, 0) ||
        !clock_modify(149, 0x80, 0) || !clock_modify(22, 0x40, transmit ? 0 : 0x40) ||
        !clock_modify(24, 3, 0) || !clock_write(165, 0, true)) goto cleanup;
    /* P1=128*a-512, P2=0, P3=1 for integer ratios. */
    const uint8_t pll[] = {0, 1, 0, 0x0e, 0, 0, 0, 0};
    const uint8_t ms[]  = {0, 1, 0, 0x26, 0, 0, 0, 0};
    /* 25MHz*(34+24/25)=874MHz: P1=3962, P2=22, P3=25. */
    const uint8_t tx_pll[] = {0, 25, 0, 0x0f, 0x7a, 0, 0, 22};
    /* 875MHz = 25MHz*35, no fractional remainder; odd ratio keeps FBA_INT=0. */
    const uint8_t comparison_pll[] = {0, 1, 0, 0x0f, 0x80, 0, 0, 0};
    const uint8_t *selected_pll = transmit ? (integer_comparison ? comparison_pll : tx_pll) : pll;
    const uint8_t tx_ms[] = {0, 1, 0, 1, 0, 0, 0, 0};
    for (unsigned i=0; i<8; ++i)
        if (!clock_write(26+i, selected_pll[i], true) ||
            !clock_write(42+i, (transmit ? tx_ms : ms)[i], true)) goto cleanup;
    /* MS0 integer, PLLA, own multisynth, 2 mA drive. */
    if (!clock_write(16, 0x4c, true) || !clock_write(177, 0x20, false)) goto cleanup;
    bool locked = false;
    for (unsigned i=0; i<100; ++i) {
        sleep_ms(1);
        if (!clock_read(0, &status)) goto cleanup;
        if (!(status & 0xa8)) {locked = true; break;}
    }
    if (!locked) goto cleanup;
    if (transmit) {
        /* Select TX with CLK0 still disabled, then allow switch settling. */
        gpio_put(10, true);
        sleep_ms(1);
    }
    /* Timer starts BEFORE enable. Nothing prints while output is active. */
    uint64_t end = time_us_64() + 10000000;
    if (!clock_write(3, 0xfe, true)) goto cleanup;
    ok = true;
    while (time_us_64() < end) {
        uint8_t enabled;
        if (!clock_read(0, &status) || (status & 0xa8) ||
            !clock_read(3, &enabled) || enabled != 0xfe) {ok = false; break;}
        int command = getchar_timeout_us(0);
        if (command >= 0) {ok = false; break;} /* Any input aborts. */
        sleep_ms(10);
    }
cleanup:
    { bool stopped = clock_stop();
      gpio_put(10, false); /* Always restore mute, including I2C failure. */
      printf("[%s] complete=%u shutdown_verified=%u status=%02X TX=0\n",
             transmit ? "tx_tone" : "clock_test", ok, stopped, status);
      return ok && stopped; }
}

static bool clock_test(void) {return clock_window(false, false);}
static bool tx_tone_test(void) {return clock_window(true, false);}
static bool tx_comparison_test(void) {return clock_window(true, true);}

/* Temporary crystal-load comparison; never enables TX, always attempts restore. */
static bool clock_load_test(unsigned pf) {
    gpio_put(10, false); gpio_put(11, false); gpio_put(16, false);
    uint8_t selected, original = 0;
    if (pf == 6) selected = 0x52;
    else if (pf == 8) selected = 0x92;
    else if (pf == 10) selected = 0xd2;
    else return false;
    if (!clock_stop() || !clock_read(183, &original)) return false;
    bool configured = clock_write(183, selected, true);
    bool ok = false;
    if (configured) {
        sleep_ms(200);
        ok = clock_test();
    }
    /* Clock window already shuts down; repeat before touching crystal loading. */
    bool stopped = clock_stop();
    bool restored = clock_write(183, original, true);
    if (!restored) (void)clock_write(183, original, true); /* Best-effort retry. */
    printf("[clock_load] pf=%u original=%02X configured=%u complete=%u stopped=%u restored=%u\n",
           pf, original, configured, ok, stopped, restored);
    return configured && ok && stopped && restored;
}
