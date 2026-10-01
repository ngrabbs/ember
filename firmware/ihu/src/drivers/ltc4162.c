#include "drivers/ltc4162.h"

#include <stdint.h>
#include <stdbool.h>
#include <limits.h>

#include "pico/stdlib.h"
#include "hardware/i2c.h"

#include "config/pinmap.h"
#include "config/i2c0_bus.h"

/* ------------------------------------------------------------------
 * Register addresses (LTC4162-L datasheet Rev. A, Table 1)
 * ----------------------------------------------------------------*/
#define REG_CONFIG_BITS          0x14   /* CONFIG_BITS_REG — R/W */
#define REG_JEITA_T1             0x1F   /* JEITA cold-side threshold — R/W */
#define REG_JEITA_T6             0x24   /* JEITA hot-side threshold  — R/W */
#define REG_CHARGER_CONFIG_BITS  0x29   /* CHARGER_CONFIG_BITS_REG — R/W */

/* Datasheet defaults for jeita_t1 and jeita_t6 (table 6, p. 25). */
#define JEITA_T1_DEFAULT         16117  /* ~0 °C breakpoint  */
#define JEITA_T6_DEFAULT         4970   /* ~60 °C breakpoint */
/* CONFIG_BITS_REG (0x14) — bit positions per datasheet page 39.
 * Range is [5:1]; bit 0 is unused. Defaults are all zero. */
#define CFG_MPPT_EN              (1u << 1)
#define CFG_FORCE_TELEMETRY_ON   (1u << 2)  /* keep ADC running always */
#define CFG_TELEMETRY_SPEED_HIGH (1u << 3)  /* 1 = ~11 ms conversions, 0 = ~5 s */
#define CFG_RUN_BSR              (1u << 4)
#define CFG_SUSPEND_CHARGER      (1u << 5)

/* CHARGER_CONFIG_BITS_REG (0x29) — bit positions per datasheet p. 42.
 * Defaults: en_jeita=1, en_c_over_x_term=0. */
#define CHG_CFG_EN_JEITA         (1u << 0)
#define CHG_CFG_EN_C_OVER_X_TERM (1u << 2)

/* ------------------------------------------------------------------
 * LSB scaling factors (LTC4162-L datasheet Rev. A, Table 1)
 *
 * VBAT is signed and reported per cell — multiply by IHU_EPS_BATTERY_CELLS for
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
/* SMBus PEC: CRC-8 polynomial x^8+x^2+x+1, init 0, no reflection/XOR.
 * Include both address/direction bytes, command and low/high data bytes. */
static uint8_t pec_byte(uint8_t crc, uint8_t byte) {
    crc ^= byte;
    for (unsigned bit = 0; bit < 8; ++bit)
        crc = (uint8_t)((crc << 1) ^ ((crc & 0x80u) ? 0x07u : 0u));
    return crc;
}

static bool read_word(i2c_inst_t *i2c, uint8_t addr, uint8_t reg, uint16_t *out) {
    /* Phase 1: write the register pointer with no stop (repeated start). */
    int w = i2c_write_timeout_us(i2c, addr, &reg, 1, true, 10000);
    if (w != 1) {
        return false;
    }
    /* ACK both data bytes to request the optional PEC, then NACK PEC. */
    uint8_t buf[3];
    int r = i2c_read_timeout_us(i2c, addr, buf, 3, false, 10000);
    if (r != 3) {
        return false;
    }
    uint8_t crc = pec_byte(0, (uint8_t)(addr << 1));
    crc = pec_byte(crc, reg);
    crc = pec_byte(crc, (uint8_t)((addr << 1) | 1u));
    crc = pec_byte(crc, buf[0]);
    crc = pec_byte(crc, buf[1]);
    if (crc != buf[2]) return false;
    *out = ((uint16_t)buf[1] << 8) | (uint16_t)buf[0];
    return true;
}

static bool write_word(i2c_inst_t *i2c, uint8_t addr, uint8_t reg, uint16_t value) {
#if !IHU_EPS_ALLOW_CHARGER_WRITES && !IHU_EPS_TIMED_BENCH_TEST
    (void)i2c; (void)addr; (void)reg; (void)value;
    return false;
#else
#if IHU_EPS_TIMED_BENCH_TEST && !IHU_EPS_ALLOW_CHARGER_WRITES
    if (reg != 0x14 && reg != 0x29 && reg != 0x1a && reg != 0x1b && reg != 0x1f && reg != 0x24) return false;
#endif
    uint8_t buf[3];
    buf[0] = reg;
    buf[1] = (uint8_t)(value & 0xFF);          /* LSB first */
    buf[2] = (uint8_t)((value >> 8) & 0xFF);   /* then MSB  */
    int w = i2c_write_timeout_us(i2c, addr, buf, 3, false, 10000);
    return w == 3;
#endif
}

/* ------------------------------------------------------------------
 * Public API
 *
 * Every entry point takes the i2c0 bus lock for the duration of one
 * logical transaction and releases it before returning; read_word()
 * and write_word() above never lock, so they can be composed inside a
 * single held lock without needing a recursive mutex.
 *
 * "One logical transaction" means the whole sequence a caller needs to
 * be coherent — the observational register set, or the read-modify-write
 * in kick() — not each individual SDK call. See config/i2c0_bus.h.
 * ----------------------------------------------------------------*/

bool ltc4162_present(i2c_inst_t *i2c, uint8_t addr) {
    if (!ihu_i2c0_lock(IHU_I2C0_LOCK_TIMEOUT_MS)) {
        return false;
    }
    uint16_t status;
    bool ok = read_word(i2c, addr, LTC4162_REG_system_status, &status);
    ihu_i2c0_unlock();
    return ok;
}

bool ltc4162_init(i2c_inst_t *i2c, uint8_t addr) {
    if (!ihu_i2c0_lock(IHU_I2C0_LOCK_TIMEOUT_MS)) {
        return false;
    }
    /* Preserve existing configuration; writes require an explicit build option. */
    uint16_t config;
    bool ok = read_word(i2c, addr, REG_CONFIG_BITS, &config)
           && write_word(i2c, addr, REG_CONFIG_BITS, config | CFG_FORCE_TELEMETRY_ON);
    ihu_i2c0_unlock();
    return ok;
}

bool ltc4162_set_jeita_enabled(i2c_inst_t *i2c, uint8_t addr, bool enabled) {
    /* Read-modify-write: the lock spans both halves so a concurrent
     * writer cannot land between them and get its bits discarded. */
    if (!ihu_i2c0_lock(IHU_I2C0_LOCK_TIMEOUT_MS)) {
        return false;
    }
    uint16_t val;
    bool ok = read_word(i2c, addr, REG_CHARGER_CONFIG_BITS, &val);
    if (ok) {
        if (enabled) {
            val |= CHG_CFG_EN_JEITA;
        } else {
            val &= (uint16_t)~CHG_CFG_EN_JEITA;
        }
        ok = write_word(i2c, addr, REG_CHARGER_CONFIG_BITS, val);
    }
    ihu_i2c0_unlock();
    return ok;
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

    /* Both limits under one lock — a window where t1 is widened but t6
     * is not is a JEITA config the chip would briefly act on. */
    if (!ihu_i2c0_lock(IHU_I2C0_LOCK_TIMEOUT_MS)) {
        return false;
    }
    bool ok = write_word(i2c, addr, REG_JEITA_T1, t1)
           && write_word(i2c, addr, REG_JEITA_T6, t6);
    ihu_i2c0_unlock();
    return ok;
}

bool ltc4162_kick(i2c_inst_t *i2c, uint8_t addr) {
    /* The lock is held across the whole pulse, including the 100 ms
     * dwell. Releasing it in the middle would let another poller read
     * CONFIG_BITS with suspend_charger asserted and report the charger
     * as suspended, which is true for 100 ms and misleading forever
     * after in a log. 100 ms is well inside the lock timeout. */
    if (!ihu_i2c0_lock(IHU_I2C0_LOCK_TIMEOUT_MS)) {
        return false;
    }

    /* Read current CONFIG_BITS so we preserve force_telemetry_on,
     * MPPT, etc. — only briefly assert suspend_charger on top. */
    uint16_t base;
    bool ok = read_word(i2c, addr, REG_CONFIG_BITS, &base)
           && write_word(i2c, addr, REG_CONFIG_BITS, base | CFG_SUSPEND_CHARGER);
    if (ok) {
        /* 100 ms is plenty for the state machine to register the
         * suspend transition. Block-sleep here: this function is
         * meant to be called from a normal task context. */
        sleep_ms(100);
        ok = write_word(i2c, addr, REG_CONFIG_BITS,
                        base & (uint16_t)~CFG_SUSPEND_CHARGER);
    }

    ihu_i2c0_unlock();
    return ok;
}

bool ltc4162_read_raw(i2c_inst_t *i2c, uint8_t addr, ltc4162_raw_t *out) {
    if (!out || !ihu_i2c0_lock(IHU_I2C0_LOCK_TIMEOUT_MS)) return false;
    ltc4162_raw_t sample;
    bool ok = true;
#define READ_FIELD(name, reg) if (ok) ok = read_word(i2c, addr, reg, &sample.name);
    LTC4162_READOUT_REGISTERS(READ_FIELD)
#undef READ_FIELD
    ihu_i2c0_unlock();
    if (ok) *out = sample;
    return ok;
}

bool ltc4162_read_telemetry(i2c_inst_t *i2c, uint8_t addr,
                            ltc4162_telemetry_t *out) {
    ltc4162_raw_t raw;
    if (!out || !ltc4162_read_raw(i2c, addr, &raw)) return false;
    unsigned chemistry = (raw.chem_cells >> 8) & 0x0f;
    unsigned cells = raw.chem_cells & 0x0f;
    /* Zero cells is documented when the charger is disabled. In that case
     * use the configured board count, never silently guess a different count. */
    if (!(raw.telemetry_status & 1u) || chemistry > 3 ||
        (cells && cells != IHU_EPS_BATTERY_CELLS)) return false;
    ltc4162_telemetry_t sample = {.raw = raw};
    sample.v_bat = (float)(int16_t)raw.vbat * IHU_EPS_BATTERY_CELLS * VBAT_LSB_UV_PER_CELL / 1e6f;
    sample.v_in = (float)(int16_t)raw.vin * VIN_LSB_MV / 1000.0f;
    sample.v_out = (float)(int16_t)raw.vout * VOUT_LSB_MV / 1000.0f;
    sample.i_bat_ma = (float)(int16_t)raw.ibat * ISENSE_LSB_UV / (IHU_EPS_RSNSB_OHMS * 1000.0f);
    sample.i_in_ma = (float)(int16_t)raw.iin * ISENSE_LSB_UV / (IHU_EPS_RSNSI_OHMS * 1000.0f);
    sample.die_temp_c = (float)(int16_t)raw.die_temp * 0.0215f - 264.4f;
    sample.charger_state = raw.charger_state;
    sample.charge_status = raw.charge_status;
    sample.system_status = raw.system_status;
    *out = sample;
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

#if IHU_EPS_TIMED_BENCH_TEST
static const uint8_t bench_regs[] = {0x14, 0x29, 0x1a, 0x1b, 0x1f, 0x24};
static uint16_t bench_saved[6];
static uint32_t bench_since;
static bool bench_active, bench_ready;
static bool bench_write(i2c_inst_t *i2c, uint8_t addr, uint8_t reg, uint16_t v) {
    uint16_t check;
    return write_word(i2c,addr,reg,v) && read_word(i2c,addr,reg,&check) && check==v;
}
/* Lock must be held. Attempt each recovery write even if a previous one fails.
 * Keep charging suspended if settings cannot be verified; retry next service. */
static bool bench_restore(i2c_inst_t *i2c, uint8_t addr) {
    bool ok=bench_write(i2c,addr,0x14,bench_saved[0]|CFG_SUSPEND_CHARGER);
    for (unsigned n=2;n<6;++n) {
        bool step=bench_write(i2c,addr,bench_regs[n],bench_saved[n]); ok=step&&ok;
    }
    bool step=bench_write(i2c,addr,0x29,bench_saved[1]); ok=step&&ok;
    /* Saved CONFIG always has suspend set: never resume after a test. */
    if (ok) bench_active=false;
    return ok;
}
#endif

bool ltc4162_bench_recover(i2c_inst_t *i2c, uint8_t addr) {
#if !IHU_EPS_TIMED_BENCH_TEST
    (void)i2c; (void)addr; return false;
#else
    if (!ihu_i2c0_lock(IHU_I2C0_LOCK_TIMEOUT_MS)) return false;
    uint16_t cfg, chg;
    bool ok=read_word(i2c,addr,0x14,&cfg) && read_word(i2c,addr,0x29,&chg);
    if (ok) {
        ok=bench_write(i2c,addr,0x14,cfg|CFG_SUSPEND_CHARGER);
        /* Temperature recovery only after verified suspension. */
        if (ok) {
            bool a=bench_write(i2c,addr,0x1f,JEITA_T1_DEFAULT);
            bool b=bench_write(i2c,addr,0x24,JEITA_T6_DEFAULT);
            bool c=bench_write(i2c,addr,0x29,chg|CHG_CFG_EN_JEITA);
            bool d=bench_write(i2c,addr,0x1a,0); /* minimum servo */
            ok=a&&b&&c&&d;
        }
    }
    bench_active=false; bench_ready=ok;
    ihu_i2c0_unlock(); return ok;
#endif
}

bool ltc4162_bench_start(i2c_inst_t *i2c, uint8_t addr, uint32_t now_ms) {
#if !IHU_EPS_TIMED_BENCH_TEST
    (void)i2c; (void)addr; (void)now_ms; return false;
#else
    if (!ihu_i2c0_lock(IHU_I2C0_LOCK_TIMEOUT_MS)) return false;
    if (!bench_ready || bench_active) { ihu_i2c0_unlock(); return false; }
    uint16_t chem, adc, vbat, vin, die, ntc;
    bool ok=read_word(i2c,addr,0x43,&chem) && read_word(i2c,addr,0x4a,&adc)
         && read_word(i2c,addr,0x3a,&vbat) && read_word(i2c,addr,0x3b,&vin)
         && read_word(i2c,addr,0x3f,&die) && read_word(i2c,addr,0x40,&ntc);
    /* LAD, two cells or suspended autodetection zero; ADC valid, 7..8.3 V
     * pack, 9..12 V input, die below 45 C, no open/zero NTC ADC. */
    ok=ok && ((chem>>8)&15)==0 && ((chem&15)==0 || (chem&15)==2)
       && (adc&1) && vbat>=18192 && vbat<=21569 && vin>=5458 && vin<=7277
       && die<14391 && ntc>1 && ntc<21684;
    for (unsigned n=0;ok&&n<6;++n) ok=read_word(i2c,addr,bench_regs[n],&bench_saved[n]);
    ok=ok && (bench_saved[0]&CFG_SUSPEND_CHARGER) && bench_saved[2]<=31 && bench_saved[3]<=31;
    if (ok) {
        bench_active=true; bench_since=now_ms;
        /* Suspend stays set until every modified setting reads back. */
        ok=bench_write(i2c,addr,0x29,bench_saved[1]&~CHG_CFG_EN_JEITA)
           && bench_write(i2c,addr,0x1a,0)
           && bench_write(i2c,addr,0x1b,bench_saved[3]<23 ? bench_saved[3] : 23)
           && bench_write(i2c,addr,0x1f,0x7fff)
           && bench_write(i2c,addr,0x24,1)
           && bench_write(i2c,addr,0x14,bench_saved[0]&~CFG_SUSPEND_CHARGER);
        if (!ok) { bench_ready=bench_restore(i2c,addr); }
    }
    ihu_i2c0_unlock(); return ok;
#endif
}

bool ltc4162_bench_service(i2c_inst_t *i2c, uint8_t addr, uint32_t now_ms, bool stop) {
#if !IHU_EPS_TIMED_BENCH_TEST
    (void)i2c; (void)addr; (void)now_ms; (void)stop; return false;
#else
    if (!ihu_i2c0_lock(IHU_I2C0_LOCK_TIMEOUT_MS)) return false;
    bool ok=bench_ready;
    if (bench_active) {
        uint16_t chem, adc, vbat, die;
        bool healthy=read_word(i2c,addr,0x43,&chem) && read_word(i2c,addr,0x4a,&adc)
                  && read_word(i2c,addr,0x3a,&vbat) && read_word(i2c,addr,0x3f,&die)
                  && ((chem>>8)&15)==0 && ((chem&15)==0 || (chem&15)==2)
                  && (adc&1) && vbat>=18192 && vbat<=21569 && die<14391;
        if (stop || !healthy || (uint32_t)(now_ms-bench_since)>=60000u)
            ok=bench_restore(i2c,addr);
    }
    ihu_i2c0_unlock(); return ok;
#endif
}
