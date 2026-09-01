/*
 * si5351a.h — Minimal Si5351A driver for CubeSat comms board bring-up
 *
 * Configures two clock outputs:
 *   CLK0: 145.667 MHz  (TX carrier, tripled to 437 MHz)
 *   CLK1: 145.900 MHz  (RX local oscillator)
 *
 * Uses raw I2C register writes — no external library dependencies.
 * Reference: Skyworks AN619 (Si5351 register map)
 *
 * Target: RP2040 (Raspberry Pi Pico) with Pico SDK
 */

#ifndef SI5351A_H
#define SI5351A_H

#include <stdint.h>
#include <stdbool.h>

/* Si5351A I2C address (active-low ADDR pin, default = GND) */
#define SI5351A_ADDR 0x60

/* Key register addresses (AN619) */
#define SI5351_REG_STATUS        0
#define SI5351_REG_OUTPUT_EN     3
#define SI5351_REG_CLK0_CTRL    16
#define SI5351_REG_CLK1_CTRL    17
#define SI5351_REG_CLK2_CTRL    18
#define SI5351_REG_MSNA_BASE    26  /* PLL A multisynth parameters */
#define SI5351_REG_MSNB_BASE    34  /* PLL B multisynth parameters */
#define SI5351_REG_MS0_BASE     42  /* Multisynth 0 (CLK0) */
#define SI5351_REG_MS1_BASE     50  /* Multisynth 1 (CLK1) */
#define SI5351_REG_PLL_RESET   177
#define SI5351_REG_XTAL_LOAD   183

/* Clock control register bits */
#define SI5351_CLK_PDN         (1 << 7)  /* Power down */
#define SI5351_CLK_INT_MODE    (1 << 6)  /* Integer mode (lower jitter) */
#define SI5351_CLK_SRC_PLLA    (0 << 5)  /* PLL A source */
#define SI5351_CLK_SRC_PLLB    (1 << 5)  /* PLL B source */
#define SI5351_CLK_INV         (1 << 4)  /* Invert output */
#define SI5351_CLK_SRC_MS      (3 << 2)  /* Select multisynth as clock source */
#define SI5351_CLK_SRC_XTAL    (0 << 2)  /* Select XTAL as clock source (default) */
#define SI5351_CLK_DRV_8MA     (3 << 0)  /* 8 mA drive strength (max) */
#define SI5351_CLK_DRV_6MA     (2 << 0)
#define SI5351_CLK_DRV_4MA     (1 << 0)
#define SI5351_CLK_DRV_2MA     (0 << 0)

/* Crystal load capacitance */
#define SI5351_XTAL_LOAD_8PF   (1 << 6)
#define SI5351_XTAL_LOAD_10PF  (2 << 6)

/* PLL reset bits */
#define SI5351_PLL_RESET_A     (1 << 5)
#define SI5351_PLL_RESET_B     (1 << 7)

/*
 * Multisynth parameter block (8 registers per PLL or output divider)
 *
 * The Si5351 uses a fractional divider: ratio = a + b/c
 * These are encoded into three 20-bit/18-bit values: P1, P2, P3
 *
 *   P1 = 128 * a + floor(128 * b / c) - 512
 *   P2 = 128 * b - c * floor(128 * b / c)
 *   P3 = c
 *
 * For integer mode (b=0): P1 = 128*a - 512, P2 = 0, P3 = 1
 */
typedef struct {
    uint32_t p1;
    uint32_t p2;
    uint32_t p3;
} si5351_params_t;

/*
 * Calculated parameters for the comms board frequencies.
 *
 * Crystal: 25 MHz (standard Si5351A breakout)
 *
 * === CLK0: 145.667 MHz (TX, tripled to ~437 MHz) ===
 *
 * PLL A: 25 MHz × (35 + 0/1) = 875 MHz   (integer mode, VCO in 600-900 range)
 * MS0:   875 / 6 = 145.8333... MHz
 *
 * Hmm, that's not exactly 145.667. Let's find a better combo.
 *
 * Target: 145.667 MHz × 3 = 437.0 MHz (desired TX freq)
 * So we actually need 437.0 / 3 = 145.6667 MHz
 *
 * PLL A VCO = 145.6667 × 6 = 874.0 MHz
 *   PLL mult = 874.0 / 25 = 34.96 = 34 + 24/25
 *   a=34, b=24, c=25
 *   VCO = 25 × (34 + 24/25) = 25 × 34.96 = 874.0 MHz  ✓
 * MS0 divider = 6 (integer)
 *   Output = 874.0 / 6 = 145.6667 MHz  ✓
 *   × 3 = 437.0 MHz  ✓
 *
 * === CLK1: 145.900 MHz (RX LO) ===
 *
 * PLL B VCO = 145.9 × 6 = 875.4 MHz
 *   PLL mult = 875.4 / 25 = 35.016 = 35 + 2/125
 *   a=35, b=2, c=125
 *   VCO = 25 × (35 + 2/125) = 25 × 35.016 = 875.4 MHz  ✓
 * MS1 divider = 6 (integer)
 *   Output = 875.4 / 6 = 145.9 MHz  ✓
 *
 * Note: IARU coordination will assign actual frequencies. These are
 * starting values. To change the TX frequency, adjust PLL A's b/c
 * ratio. The output = 25 * (a + b/c) / MS_div, then tripled.
 */

/* Forward declarations — implement with your I2C HAL */
typedef struct {
    /* Platform-specific I2C handle. On Pico SDK this is i2c_inst_t* */
    void *i2c;
} si5351_dev_t;

/*
 * Initialize Si5351A: disable all outputs, set crystal load, configure
 * PLL A (CLK0/TX) and PLL B (CLK1/RX), set output dividers, enable outputs.
 *
 * Call once at startup. Returns 0 on success, -1 on I2C error.
 */
int si5351_init(si5351_dev_t *dev);

/*
 * Enable or disable individual clock outputs.
 * Useful for T/R switching — disable CLK0 during RX to reduce leakage.
 */
int si5351_enable_clk(si5351_dev_t *dev, uint8_t clk, bool enable);

/*
 * Set CLK0 frequency by adjusting PLL A numerator/denominator.
 * freq_hz = 25e6 * (a + b/c) / ms_div * (tripler not included)
 * For quick bench testing of different TX frequencies.
 */
int si5351_set_clk0_freq(si5351_dev_t *dev, uint32_t a, uint32_t b, uint32_t c);

#endif /* SI5351A_H */
