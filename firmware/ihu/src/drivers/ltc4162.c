#include "drivers/ltc4162.h"

#include <stdint.h>
#include <stdbool.h>
#include <limits.h>

#include "pico/stdlib.h"
#include "hardware/i2c.h"

#include "config/pinmap.h"

/* ------------------------------------------------------------------
 * Register addresses (LTC4162-L datasheet Rev. F, Table 1)
 * ----------------------------------------------------------------*/
#define REG_CONFIG_BITS          0x14   /* CONFIG_BITS_REG — R/W */
#define REG_JEITA_T1             0x1F   /* JEITA cold-side threshold — R/W */
#define REG_JEITA_T6             0x24   /* JEITA hot-side threshold  — R/W */
#define REG_CHARGER_CONFIG_BITS  0x29   /* CHARGER_CONFIG_BITS_REG — R/W */
#define REG_CHARGER_STATE        0x34   /* enum active state */
#define REG_CHARGE_STATUS        0x35   /* enum charge-loop status */
#define REG_SYSTEM_STATUS        0x39   /* system-level status bits */

/* Datasheet defaults for jeita_t1 and jeita_t6 (table 6, p. 25). */
#define JEITA_T1_DEFAULT         16117  /* ~0 °C breakpoint  */
#define JEITA_T6_DEFAULT         4970   /* ~60 °C breakpoint */
#define REG_VBAT             0x3A   /* battery voltage telemetry */
#define REG_VIN              0x3B   /* input voltage telemetry */
#define REG_VOUT             0x3C   /* output voltage telemetry */
#define REG_IBAT             0x3D   /* battery current telemetry (signed) */
#define REG_IIN              0x3E   /* input current telemetry (signed) */

/* CONFIG_BITS_REG (0x14) — bit positions per datasheet page 39.
 * Range is [5:1]; bit 0 is unused. Defaults are all zero. */
#define CFG_MPPT_EN              (1u << 1)
#define CFG_FORCE_TELEMETRY_ON   (1u << 2)  /* keep ADC running always */
#define CFG_TELEMETRY_SPEED_HIGH (1u << 3)  /* 1 = ~10 Hz, 0 = ~0.2 Hz */
#define CFG_RUN_BSR              (1u << 4)
#define CFG_SUSPEND_CHARGER      (1u << 5)

/* CHARGER_CONFIG_BITS_REG (0x29) — bit positions per datasheet p. 42.
 * Defaults: en_jeita=1, en_c_over_x_term=0. */
#define CHG_CFG_EN_JEITA         (1u << 0)
#define CHG_CFG_EN_C_OVER_X_TERM (1u << 2)

/* ------------------------------------------------------------------
 * LSB scaling factors (LTC4162-L datasheet Rev. F, Table 2)
 *
 * VBAT is reported per cell — multiply by IHU_EPS_BATTERY_CELLS for
 * total pack voltage. Currents are derived as (raw_LSB_voltage /
 * sense_resistor) so they scale with the board's sense resistors.
 * ----------------------------------------------------------------*/
#define VBAT_LSB_UV_PER_CELL     192.4f      /* µV per LSB, per cell */
#define VIN_LSB_MV                 1.649f    /* mV per LSB */
#define VOUT_LSB_MV                1.653f    /* mV per LSB */
#define ISENSE_LSB_UV              1.466f    /* µV per LSB across sense R */

/* ------------------------------------------------------------------
 * Low-level I2C — single-register 16-bit read/write, LSB-first per
 * the LTC4162's SMBus-style word protocol. Both directions are
 * little-endian; the reference rp2040-freertos-ihu driver got reads
 * right but had writes inverted (MSB-first), which was a bug.
 * ----------------------------------------------------------------*/
static bool read_word(i2c_inst_t *i2c, uint8_t addr, uint8_t reg, uint16_t *out) {
    /* Phase 1: write the register pointer with no stop (repeated start). */
    int w = i2c_write_blocking(i2c, addr, &reg, 1, true);
    if (w != 1) {
        return false;
    }
    /* Phase 2: read 2 bytes — LTC4162 returns LSB then MSB. */
    uint8_t buf[2];
    int r = i2c_read_blocking(i2c, addr, buf, 2, false);
    if (r != 2) {
        return false;
    }
    *out = ((uint16_t)buf[1] << 8) | (uint16_t)buf[0];
    return true;
}

static bool write_word(i2c_inst_t *i2c, uint8_t addr, uint8_t reg, uint16_t value) {
    uint8_t buf[3];
    buf[0] = reg;
    buf[1] = (uint8_t)(value & 0xFF);          /* LSB first */
    buf[2] = (uint8_t)((value >> 8) & 0xFF);   /* then MSB  */
    int w = i2c_write_blocking(i2c, addr, buf, 3, false);
    return w == 3;
}

/* ------------------------------------------------------------------
 * Public API
 * ----------------------------------------------------------------*/

bool ltc4162_present(i2c_inst_t *i2c, uint8_t addr) {
    /* Zero-length write — peripheral ACKs the address byte or NACKs.
     * The Pico SDK returns PICO_ERROR_GENERIC on NACK, 0 on ACK. */
    int r = i2c_write_blocking(i2c, addr, NULL, 0, false);
    return r >= 0;
}

bool ltc4162_init(i2c_inst_t *i2c, uint8_t addr) {
    /* Set force_telemetry_on; leave suspend/MPPT/etc. at defaults
     * (all zero). Side effect: writing CONFIG_BITS clears latched
     * fault state from any prior charger session. */
    return write_word(i2c, addr, REG_CONFIG_BITS, CFG_FORCE_TELEMETRY_ON);
}

bool ltc4162_set_jeita_enabled(i2c_inst_t *i2c, uint8_t addr, bool enabled) {
    uint16_t val;
    if (!read_word(i2c, addr, REG_CHARGER_CONFIG_BITS, &val)) {
        return false;
    }
    if (enabled) {
        val |= CHG_CFG_EN_JEITA;
    } else {
        val &= (uint16_t)~CHG_CFG_EN_JEITA;
    }
    return write_word(i2c, addr, REG_CHARGER_CONFIG_BITS, val);
}

bool ltc4162_set_ntc_bypass(i2c_inst_t *i2c, uint8_t addr, bool enabled) {
    /* Use values that satisfy `jeita_t1 > thermistor_voltage > jeita_t6`
     * for any sane thermistor_voltage reading, in BOTH signed and
     * unsigned interpretations of the comparison:
     *   t1 = 0x7FFF = 32767     (max positive in either interpretation)
     *   t6 = 0x0001 = 1         (smallest positive, lower than any
     *                            realistic thermistor_voltage reading;
     *                            avoids 0 in case the chip does
     *                            strict-greater-than)
     * The chip's ADC won't physically read negative thermistor_voltage,
     * so anything above 0 is fine for the lower bound. */
    uint16_t t1 = enabled ? 0x7FFFu : (uint16_t)JEITA_T1_DEFAULT;
    uint16_t t6 = enabled ? 0x0001u : (uint16_t)JEITA_T6_DEFAULT;
    if (!write_word(i2c, addr, REG_JEITA_T1, t1)) return false;
    if (!write_word(i2c, addr, REG_JEITA_T6, t6)) return false;
    return true;
}

bool ltc4162_kick(i2c_inst_t *i2c, uint8_t addr) {
    /* Read current CONFIG_BITS so we preserve force_telemetry_on,
     * MPPT, etc. — only briefly assert suspend_charger on top. */
    uint16_t base;
    if (!read_word(i2c, addr, REG_CONFIG_BITS, &base)) {
        return false;
    }
    if (!write_word(i2c, addr, REG_CONFIG_BITS, base | CFG_SUSPEND_CHARGER)) {
        return false;
    }
    /* 100 ms is plenty for the state machine to register the
     * suspend transition. Block-sleep here: this function is
     * meant to be called from a normal task context. */
    sleep_ms(100);
    return write_word(i2c, addr, REG_CONFIG_BITS, base & (uint16_t)~CFG_SUSPEND_CHARGER);
}

bool ltc4162_read_telemetry(i2c_inst_t *i2c, uint8_t addr,
                            ltc4162_telemetry_t *out) {
    uint16_t v_bat_raw, v_in_raw, v_out_raw;
    uint16_t i_bat_raw, i_in_raw;
    uint16_t state, status, sys;

    if (!read_word(i2c, addr, REG_VBAT,          &v_bat_raw)) return false;
    if (!read_word(i2c, addr, REG_VIN,           &v_in_raw))  return false;
    if (!read_word(i2c, addr, REG_VOUT,          &v_out_raw)) return false;
    if (!read_word(i2c, addr, REG_IBAT,          &i_bat_raw)) return false;
    if (!read_word(i2c, addr, REG_IIN,           &i_in_raw))  return false;
    if (!read_word(i2c, addr, REG_CHARGER_STATE, &state))     return false;
    if (!read_word(i2c, addr, REG_CHARGE_STATUS, &status))    return false;
    if (!read_word(i2c, addr, REG_SYSTEM_STATUS, &sys))       return false;

    /* IBAT/IIN are 2's-complement signed — the explicit int16_t cast
     * sign-extends correctly regardless of host endianness. */
    int16_t i_bat_signed = (int16_t)i_bat_raw;
    int16_t i_in_signed  = (int16_t)i_in_raw;

    /* VBAT register reports per-cell voltage in steps of VBAT_LSB_UV_PER_CELL.
     * Total pack voltage = raw * (cells * step_uV) / 1e6. */
    out->v_bat = (float)v_bat_raw *
                 ((float)IHU_EPS_BATTERY_CELLS * VBAT_LSB_UV_PER_CELL) / 1e6f;
    out->v_in  = (float)v_in_raw  * VIN_LSB_MV  / 1000.0f;
    out->v_out = (float)v_out_raw * VOUT_LSB_MV / 1000.0f;

    /* I = V_sense / R_sense. Sense voltage = raw * ISENSE_LSB_UV (µV);
     * dividing by R (ohms) gives current in µA — convert to mA. */
    out->i_bat_ma = ((float)i_bat_signed * ISENSE_LSB_UV) /
                    (IHU_EPS_RSNSB_OHMS * 1000.0f);
    out->i_in_ma  = ((float)i_in_signed  * ISENSE_LSB_UV) /
                    (IHU_EPS_RSNSI_OHMS * 1000.0f);

    out->charger_state = state;
    out->charge_status = status;
    out->system_status = sys;
    return true;
}

/* CHARGER_STATE uses mutually-exclusive enum values (NOT bit
 * positions). Each label maps to a single raw value per datasheet
 * page 42. */
const char *ltc4162_state_string(uint16_t charger_state) {
    switch ((ltc4162_state_t)charger_state) {
        case LTC4162_STATE_IDLE:                  return "idle";
        case LTC4162_STATE_BAT_SHORT_FAULT:       return "bat-short-fault";
        case LTC4162_STATE_BAT_MISSING_FAULT:     return "bat-missing-fault";
        case LTC4162_STATE_MAX_CHARGE_TIME_FAULT: return "max-charge-time-fault";
        case LTC4162_STATE_C_OVER_X_TERM:         return "c-over-x-term";
        case LTC4162_STATE_TIMER_TERM:            return "timer-term";
        case LTC4162_STATE_NTC_PAUSE:             return "ntc-pause";
        case LTC4162_STATE_CC_CV_CHARGE:          return "cc-cv-charge";
        case LTC4162_STATE_PRECHARGE:             return "precharge";
        case LTC4162_STATE_CHARGER_SUSPENDED:     return "charger-suspended";
        case LTC4162_STATE_BATTERY_DETECTION:     return "battery-detection";
        case LTC4162_STATE_BAT_DETECT_FAILED:     return "bat-detect-failed";
    }
    return "unknown";
}

const char *ltc4162_charge_status_string(uint16_t charge_status) {
    switch ((ltc4162_charge_status_t)charge_status) {
        case LTC4162_CHARGE_STATUS_OFF:              return "off";
        case LTC4162_CHARGE_STATUS_CONSTANT_VOLTAGE: return "constant-voltage";
        case LTC4162_CHARGE_STATUS_CONSTANT_CURRENT: return "constant-current";
        case LTC4162_CHARGE_STATUS_IIN_LIMIT_ACTIVE: return "iin-limit-active";
        case LTC4162_CHARGE_STATUS_VIN_UVCL_ACTIVE:  return "vin-uvcl-active";
        case LTC4162_CHARGE_STATUS_THERMAL_REG:      return "thermal-reg";
        case LTC4162_CHARGE_STATUS_ILIM_REG:         return "ilim-reg-active";
    }
    return "unknown";
}
