/* Receive-only bench window; AN619 rev0.8, 25MHz reference.
 * PLLA = 25*(34+4/5) = 870MHz, MS1 /6 =145MHz; tripler ->435MHz.
 * RX_ACTIVE is an indicator. TX_ACTIVE=0 selects RX and mutes the TX path.
 * No packet parsing or command dispatch. No automatic retry. */
#pragma once
static bool rx_stop(void) {
    gpio_put(10, false); gpio_put(11, false); gpio_put(16, false);
    bool disabled = disable_clocks();
    bool down0 = clock_write(16, 0x80, true);
    bool down1 = clock_write(17, 0x80, true);
    bool down2 = clock_write(18, 0x80, true);
    return disabled && down0 && down1 && down2;
}
static bool rx_window(bool lo, bool (*capture)(void)) {
    bool ok = false;
    uint8_t status = 0xff;
    if (!rx_stop()) goto cleanup;
    if (lo) {
        if (!clock_read(0, &status) || (status & 0x88)) goto cleanup;
        for (unsigned reg=16; reg<=23; ++reg)
            if (!clock_write(reg, 0x80, true)) goto cleanup;
        if (!clock_modify(15, 0x0c, 0) || !clock_modify(149, 0x80, 0) ||
            !clock_modify(22, 0x40, 0) || !clock_modify(24, 0x0c, 0) ||
            !clock_write(166, 0, true)) goto cleanup;
        /* P1=3942, P2=2, P3=5; MS1 P1=256, P2=0, P3=1. */
        const uint8_t pll[] = {0,5,0,0x0f,0x66,0,0,2};
        const uint8_t ms[] = {0,1,0,1,0,0,0,0};
        for (unsigned i=0; i<8; ++i)
            if (!clock_write(26+i, pll[i], true) ||
                !clock_write(50+i, ms[i], true)) goto cleanup;
        /* CLK1 only, PLLA, integer /6, 4mA initial bench setting. */
        if (!clock_write(17, 0x4d, true) || !clock_write(177, 0x20, false)) goto cleanup;
        bool locked = false;
        for (unsigned i=0; i<100; ++i) {
            sleep_ms(1);
            if (!clock_read(0, &status)) goto cleanup;
            if (!(status & 0xa8)) {locked = true; break;}
        }
        if (!locked || !clock_write(3, 0xfd, true)) goto cleanup;
        gpio_put(11, true);
    }
    uint64_t start = time_us_64(), end = start + 10000000;
    bool captured = false;
    ok = true;
    while (time_us_64() < end) {
        uint8_t enabled;
        if (getchar_timeout_us(0) >= 0 ||
            !clock_read(3, &enabled) || enabled != (lo ? 0xfd : 0xff) ||
            (lo && (!clock_read(0, &status) || (status & 0xa8)))) {ok=false; break;}
        if (!captured && time_us_64()-start >= 1000000) {
            captured=true;
            if (!capture()) {ok=false; break;}
        }
        sleep_ms(10);
    }
    ok = ok && captured;
cleanup:
    {
        bool stopped = rx_stop();
        printf("[rx_test] lo=%u complete=%u shutdown_verified=%u status=%02X TX=0 RX=0\n",
               lo, ok, stopped, status);
        return ok && stopped;
    }
}
