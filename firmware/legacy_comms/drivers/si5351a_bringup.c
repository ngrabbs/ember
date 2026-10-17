/*
 * si5351a_bringup.c — Bring-up test for Si5351A on Raspberry Pi Pico
 *
 * Wiring (Pico → Si5351A breakout):
 *   GP4 (pin 6)  → SDA
 *   GP5 (pin 7)  → SCL
 *   3V3 (pin 36) → VIN
 *   GND (pin 38) → GND
 *
 * What this does:
 *   1. Initializes Si5351A with CLK0=145.667 MHz, CLK1=145.9 MHz
 *   2. Prints status over USB serial
 *   3. Provides a simple serial menu to toggle outputs and change frequency
 *
 * Build with Pico SDK (CMakeLists.txt example below).
 *
 * Expected TinySA observations:
 *   - CLK0: strong peak at 145.667 MHz, harmonics at 291.3, 437.0, 582.7 MHz
 *     (the 437 MHz harmonic is what the tripler will select!)
 *   - CLK1: strong peak at 145.9 MHz
 *   - Both outputs are square waves, so expect visible odd harmonics
 */

#include <stdio.h>
#include "pico/stdlib.h"
#include "hardware/i2c.h"
#include "si5351a.h"

/* I2C configuration */
#define I2C_PORT    i2c0
#define I2C_SDA_PIN 4
#define I2C_SCL_PIN 5
#define I2C_FREQ_HZ 400000  /* 400 kHz fast mode */

static si5351_dev_t si5351;

static void print_banner(void) {
    printf("\n");
    printf("╔══════════════════════════════════════════════╗\n");
    printf("║  Si5351A Comms Board Bring-Up                ║\n");
    printf("║  CLK0: 145.667 MHz (TX, x3 = 437 MHz)        ║\n");
    printf("║  CLK1: 145.900 MHz (RX LO)                   ║\n");
    printf("╚══════════════════════════════════════════════╝\n");
    printf("\n");
}

static void print_menu(void) {
    printf("Commands:\n");
    printf("  0  Toggle CLK0 (TX carrier) on/off\n");
    printf("  1  Toggle CLK1 (RX LO) on/off\n");
    printf("  +  Increase CLK0 by 100 kHz\n");
    printf("  -  Decrease CLK0 by 100 kHz\n");
    printf("  r  Reset to default frequencies\n");
    printf("  s  Print current status\n");
    printf("  ?  Show this menu\n");
    printf("\n");
}

/*
 * Track current PLL A parameters so we can adjust frequency.
 * Default: a=34, b=24, c=25 → VCO = 874.0 MHz → CLK0 = 145.667 MHz
 *
 * To shift by 100 kHz at the output:
 *   Output delta = 100 kHz
 *   VCO delta = 100 kHz * 6 = 600 kHz
 *   PLL ratio delta = 600 kHz / 25 MHz = 0.024
 *
 * We use c=1000 for fine stepping:
 *   b/c step of 24/1000 = 0.024 → 600 kHz VCO → 100 kHz output
 *
 * Rescale defaults: 34 + 24/25 = 34 + 960/1000
 */
static uint32_t plla_a = 34;
static uint32_t plla_b = 960;
static uint32_t plla_c = 1000;
static bool clk0_on = true;
static bool clk1_on = true;

static void print_status(void) {
    /* Calculate and display actual frequency */
    double vco = 25.0 * ((double)plla_a + (double)plla_b / (double)plla_c);
    double clk0_mhz = vco / 6.0;
    double tx_mhz = clk0_mhz * 3.0;

    printf("CLK0: %.4f MHz  (x3 = %.4f MHz)  [%s]\n",
           clk0_mhz, tx_mhz, clk0_on ? "ON" : "OFF");
    printf("CLK1: 145.9000 MHz                [%s]\n",
           clk1_on ? "ON" : "OFF");
    printf("PLL A: VCO = %.4f MHz  (a=%lu, b=%lu, c=%lu)\n",
           vco, (unsigned long)plla_a, (unsigned long)plla_b, (unsigned long)plla_c);
    printf("\n");
}

static void adjust_clk0(int direction) {
    /*
     * Each step: b += 24 → 600 kHz VCO → 100 kHz output
     * direction: +1 = increase, -1 = decrease
     */
    int32_t new_b = (int32_t)plla_b + direction * 24;

    /* Handle rollover */
    if (new_b >= (int32_t)plla_c) {
        plla_a++;
        new_b -= plla_c;
    } else if (new_b < 0) {
        plla_a--;
        new_b += plla_c;
    }
    plla_b = (uint32_t)new_b;

    /* Check VCO range (600-900 MHz) */
    double vco = 25.0 * ((double)plla_a + (double)plla_b / (double)plla_c);
    if (vco < 600.0 || vco > 900.0) {
        printf("ERROR: VCO would be %.1f MHz (out of 600-900 range)\n", vco);
        /* Undo */
        if (direction > 0) {
            plla_b -= 24;
            if (plla_b > plla_c) { plla_a--; plla_b += plla_c; }
        } else {
            plla_b += 24;
            if (plla_b >= plla_c) { plla_a++; plla_b -= plla_c; }
        }
        return;
    }

    si5351_set_clk0_freq(&si5351, plla_a, plla_b, plla_c);
    print_status();
}

static void reset_defaults(void) {
    plla_a = 34;
    plla_b = 960;
    plla_c = 1000;
    si5351_set_clk0_freq(&si5351, plla_a, plla_b, plla_c);
    clk0_on = true;
    clk1_on = true;
    si5351_enable_clk(&si5351, 0, true);
    si5351_enable_clk(&si5351, 1, true);
    printf("Reset to defaults.\n");
    print_status();
}

int main(void) {
    /* Initialize Pico stdio (USB serial) */
    stdio_init_all();

    /* Wait for USB serial connection */
    sleep_ms(2000);

    print_banner();

    /* Initialize I2C */
    i2c_init(I2C_PORT, I2C_FREQ_HZ);
    gpio_set_function(I2C_SDA_PIN, GPIO_FUNC_I2C);
    gpio_set_function(I2C_SCL_PIN, GPIO_FUNC_I2C);
    gpio_pull_up(I2C_SDA_PIN);
    gpio_pull_up(I2C_SCL_PIN);

    printf("I2C initialized on GP%d (SDA), GP%d (SCL) at %d Hz\n",
           I2C_SDA_PIN, I2C_SCL_PIN, I2C_FREQ_HZ);

    /* Initialize Si5351A */
    si5351.i2c = I2C_PORT;

    printf("Initializing Si5351A...\n");
    int rc = si5351_init(&si5351);
    if (rc != 0) {
        printf("ERROR: Si5351A init failed! Check wiring:\n");
        printf("  SDA → GP%d, SCL → GP%d\n", I2C_SDA_PIN, I2C_SCL_PIN);
        printf("  VIN → 3V3, GND → GND\n");
        printf("  I2C address: 0x%02X\n", SI5351A_ADDR);
        while (1) {
            sleep_ms(1000);
        }
    }

    printf("Si5351A initialized successfully!\n\n");
    print_status();
    print_menu();

    /* Main loop: serial command interface */
    while (1) {
        int ch = getchar_timeout_us(100000);  /* 100 ms timeout */
        if (ch == PICO_ERROR_TIMEOUT) continue;

        switch (ch) {
        case '0':
            clk0_on = !clk0_on;
            si5351_enable_clk(&si5351, 0, clk0_on);
            printf("CLK0 %s\n", clk0_on ? "ON" : "OFF");
            break;
        case '1':
            clk1_on = !clk1_on;
            si5351_enable_clk(&si5351, 1, clk1_on);
            printf("CLK1 %s\n", clk1_on ? "ON" : "OFF");
            break;
        case '+':
        case '=':
            adjust_clk0(+1);
            break;
        case '-':
            adjust_clk0(-1);
            break;
        case 'r':
        case 'R':
            reset_defaults();
            break;
        case 's':
        case 'S':
            print_status();
            break;
        case '?':
        case 'h':
        case 'H':
            print_menu();
            break;
        default:
            break;
        }
    }

    return 0;
}
