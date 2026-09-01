/*
 * si5351a.c — Si5351A driver implementation (Pico SDK I2C)
 *
 * Configures:
 *   CLK0: 145.667 MHz via PLL A (TX carrier → tripled to 437 MHz)
 *   CLK1: 145.900 MHz via PLL B (RX local oscillator)
 *
 * Both use integer multisynth divider = 6 for cleanest output.
 * PLL frequencies are set via fractional feedback divider.
 */

#include "si5351a.h"
#include "hardware/i2c.h"
#include <string.h>

/* ── I2C helpers ───────────────────────────────────────────── */

static int si5351_write_reg(si5351_dev_t *dev, uint8_t reg, uint8_t val) {
    uint8_t buf[2] = {reg, val};
    int ret = i2c_write_blocking((i2c_inst_t *)dev->i2c, SI5351A_ADDR, buf, 2, false);
    return (ret == 2) ? 0 : -1;
}

static int si5351_read_reg(si5351_dev_t *dev, uint8_t reg, uint8_t *val) {
    int ret = i2c_write_blocking((i2c_inst_t *)dev->i2c, SI5351A_ADDR, &reg, 1, true);
    if (ret != 1) return -1;
    ret = i2c_read_blocking((i2c_inst_t *)dev->i2c, SI5351A_ADDR, val, 1, false);
    return (ret == 1) ? 0 : -1;
}

static int si5351_write_params(si5351_dev_t *dev, uint8_t base_reg,
                               uint32_t p1, uint32_t p2, uint32_t p3) {
    /*
     * 8-register block layout (AN619 Table 3):
     *   base+0: P3[15:8]
     *   base+1: P3[7:0]
     *   base+2: 0 | 0 | P1[17:16] (bits 1:0)
     *   base+3: P1[15:8]
     *   base+4: P1[7:0]
     *   base+5: P3[19:16] | P2[19:16]
     *   base+6: P2[15:8]
     *   base+7: P2[7:0]
     */
    uint8_t buf[9];
    buf[0] = base_reg;
    buf[1] = (p3 >> 8) & 0xFF;
    buf[2] = p3 & 0xFF;
    buf[3] = ((p1 >> 16) & 0x03);
    buf[4] = (p1 >> 8) & 0xFF;
    buf[5] = p1 & 0xFF;
    buf[6] = ((p3 >> 12) & 0xF0) | ((p2 >> 16) & 0x0F);
    buf[7] = (p2 >> 8) & 0xFF;
    buf[8] = p2 & 0xFF;

    int ret = i2c_write_blocking((i2c_inst_t *)dev->i2c, SI5351A_ADDR, buf, 9, false);
    return (ret == 9) ? 0 : -1;
}

/* ── Multisynth parameter calculation ──────────────────────── */

/*
 * Compute P1, P2, P3 for a fractional divider ratio = a + b/c
 *
 * From AN619:
 *   P1 = 128 * a + floor(128 * b / c) - 512
 *   P2 = 128 * b - c * floor(128 * b / c)
 *   P3 = c
 */
static si5351_params_t calc_params(uint32_t a, uint32_t b, uint32_t c) {
    si5351_params_t p;
    uint32_t floor_128b_c = (128 * b) / c;
    p.p1 = 128 * a + floor_128b_c - 512;
    p.p2 = 128 * b - c * floor_128b_c;
    p.p3 = c;
    return p;
}

/* Integer divider: a + 0/1 → P1 = 128*a - 512, P2 = 0, P3 = 1 */
static si5351_params_t calc_params_int(uint32_t a) {
    return calc_params(a, 0, 1);
}

/* ── Initialization ────────────────────────────────────────── */

int si5351_init(si5351_dev_t *dev) {
    int rc;

    /* Wait for Si5351 to be ready (status register bit 7 = SYS_INIT) */
    uint8_t status;
    do {
        rc = si5351_read_reg(dev, SI5351_REG_STATUS, &status);
        if (rc != 0) return -1;
    } while (status & 0x80);

    /* Disable all outputs while configuring */
    rc = si5351_write_reg(dev, SI5351_REG_OUTPUT_EN, 0xFF);
    if (rc != 0) return -1;

    /* Power down all CLKs */
    rc = si5351_write_reg(dev, SI5351_REG_CLK0_CTRL, SI5351_CLK_PDN);
    if (rc != 0) return -1;
    rc = si5351_write_reg(dev, SI5351_REG_CLK1_CTRL, SI5351_CLK_PDN);
    if (rc != 0) return -1;
    rc = si5351_write_reg(dev, SI5351_REG_CLK2_CTRL, SI5351_CLK_PDN);
    if (rc != 0) return -1;

    /* Set crystal load capacitance (most breakout boards use 8 pF or 10 pF) */
    rc = si5351_write_reg(dev, SI5351_REG_XTAL_LOAD,
                          SI5351_XTAL_LOAD_8PF | 0x12); /* 0x12 = reserved default bits */
    if (rc != 0) return -1;

    /*
     * ═══ PLL A: 874.0 MHz (for CLK0 = 145.667 MHz TX) ═══
     *
     * VCO = 25 MHz × (34 + 24/25) = 874.0 MHz
     */
    si5351_params_t plla = calc_params(34, 24, 25);
    rc = si5351_write_params(dev, SI5351_REG_MSNA_BASE, plla.p1, plla.p2, plla.p3);
    if (rc != 0) return -1;

    /*
     * ═══ PLL B: 875.4 MHz (for CLK1 = 145.9 MHz RX LO) ═══
     *
     * VCO = 25 MHz × (35 + 2/125) = 875.4 MHz
     */
    si5351_params_t pllb = calc_params(35, 2, 125);
    rc = si5351_write_params(dev, SI5351_REG_MSNB_BASE, pllb.p1, pllb.p2, pllb.p3);
    if (rc != 0) return -1;

    /*
     * ═══ MS0: divide by 6 (integer) → 874.0 / 6 = 145.667 MHz ═══
     */
    si5351_params_t ms0 = calc_params_int(6);
    rc = si5351_write_params(dev, SI5351_REG_MS0_BASE, ms0.p1, ms0.p2, ms0.p3);
    if (rc != 0) return -1;

    /*
     * ═══ MS1: divide by 6 (integer) → 875.4 / 6 = 145.9 MHz ═══
     */
    si5351_params_t ms1 = calc_params_int(6);
    rc = si5351_write_params(dev, SI5351_REG_MS1_BASE, ms1.p1, ms1.p2, ms1.p3);
    if (rc != 0) return -1;

    /*
     * Configure clock outputs:
     *   CLK0: PLL A source, multisynth source, integer mode, 8 mA drive
     *   CLK1: PLL B source, multisynth source, integer mode, 8 mA drive
     *
     * IMPORTANT: CLK_SRC_MS (bits 3:2 = 11) selects the multisynth divider
     * as the clock source. Without this, bits 3:2 default to 00 (XTAL
     * passthrough) and the multisynth output never reaches the pin.
     *
     * Note: MS divider is integer (6), but PLL feedback is fractional.
     * Setting CLK_INT_MODE on the output enables integer mode for the
     * multisynth divider, which gives cleaner output.
     */
    rc = si5351_write_reg(dev, SI5351_REG_CLK0_CTRL,
                          SI5351_CLK_SRC_PLLA | SI5351_CLK_INT_MODE |
                          SI5351_CLK_SRC_MS | SI5351_CLK_DRV_8MA);
    if (rc != 0) return -1;

    rc = si5351_write_reg(dev, SI5351_REG_CLK1_CTRL,
                          SI5351_CLK_SRC_PLLB | SI5351_CLK_INT_MODE |
                          SI5351_CLK_SRC_MS | SI5351_CLK_DRV_8MA);
    if (rc != 0) return -1;

    /* Reset both PLLs to lock */
    rc = si5351_write_reg(dev, SI5351_REG_PLL_RESET,
                          SI5351_PLL_RESET_A | SI5351_PLL_RESET_B);
    if (rc != 0) return -1;

    /* Enable CLK0 and CLK1, keep CLK2 disabled */
    /* Output enable register: 0 = enabled, 1 = disabled */
    rc = si5351_write_reg(dev, SI5351_REG_OUTPUT_EN, 0xFC);  /* bits 0,1 = 0 (enabled) */
    if (rc != 0) return -1;

    return 0;
}

/* ── Runtime control ───────────────────────────────────────── */

int si5351_enable_clk(si5351_dev_t *dev, uint8_t clk, bool enable) {
    if (clk > 2) return -1;

    uint8_t val;
    int rc = si5351_read_reg(dev, SI5351_REG_OUTPUT_EN, &val);
    if (rc != 0) return -1;

    if (enable)
        val &= ~(1 << clk);   /* Clear bit = enable */
    else
        val |= (1 << clk);    /* Set bit = disable */

    return si5351_write_reg(dev, SI5351_REG_OUTPUT_EN, val);
}

int si5351_set_clk0_freq(si5351_dev_t *dev, uint32_t a, uint32_t b, uint32_t c) {
    /* Update PLL A feedback divider for new CLK0 frequency.
     * New freq = 25e6 * (a + b/c) / 6
     *
     * Example: for 146.0 MHz → VCO = 876 MHz → a=35, b=1, c=25
     *          for 145.0 MHz → VCO = 870 MHz → a=34, b=4, c=5
     */
    si5351_params_t plla = calc_params(a, b, c);
    int rc = si5351_write_params(dev, SI5351_REG_MSNA_BASE,
                                 plla.p1, plla.p2, plla.p3);
    if (rc != 0) return -1;

    /* Reset PLL A to relock */
    return si5351_write_reg(dev, SI5351_REG_PLL_RESET, SI5351_PLL_RESET_A);
}
