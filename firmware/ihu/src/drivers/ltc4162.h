/*
 * LTC4162-L lithium-ion charger driver (IHU side).
 *
 * The chip lives on the EPS board; the IHU talks to it over the
 * shared CSKB H1 I2C bus. This driver is intentionally read-mostly
 * for v0.1 — we sample telemetry and decode status. The single write
 * we do (CONFIG_BITS at init) sets force_telemetry_on so the ADC
 * runs even when the charger is idle. Charge-current, MPPT, and
 * voltage-limit configuration is owned by the EPS-side firmware on
 * the flight build; on the v0.1 proto board the IHU is the only
 * MCU on the bus so it handles the minimum init.
 *
 * Datasheet: Analog Devices LTC4162-L Rev. A
 * (local copy at hardware/eps/components/LTC4162/LTC4162-L.pdf)
 */

#pragma once

#include <stdbool.h>
#include <stdint.h>

#include "hardware/i2c.h"

/* CHARGER_STATE (register 0x34) — mutually-exclusive enum values
 * (NOT bit positions). The chip reports exactly one of these at a
 * time. Compare the raw register value directly. */
typedef enum {
    LTC4162_STATE_IDLE                  = 0,
    LTC4162_STATE_BAT_SHORT_FAULT       = 1,
    LTC4162_STATE_BAT_MISSING_FAULT     = 2,
    LTC4162_STATE_MAX_CHARGE_TIME_FAULT = 4,
    LTC4162_STATE_C_OVER_X_TERM         = 8,
    LTC4162_STATE_TIMER_TERM            = 16,
    LTC4162_STATE_NTC_PAUSE             = 32,
    LTC4162_STATE_CC_CV_CHARGE          = 64,
    LTC4162_STATE_PRECHARGE             = 128,
    LTC4162_STATE_CHARGER_SUSPENDED     = 256,
    LTC4162_STATE_BATTERY_DETECTION     = 2048,
    LTC4162_STATE_BAT_DETECT_FAILED     = 4096,
} ltc4162_state_t;

/* SYSTEM_STATUS (register 0x39, bits [8:0]) — true bit flags,
 * multiple can be asserted simultaneously. */
#define LTC4162_SYS_INTVCC_GT_2P8V       (1u << 0)
#define LTC4162_SYS_VIN_GT_4P2V          (1u << 1)
#define LTC4162_SYS_VIN_GT_VBAT          (1u << 2)
#define LTC4162_SYS_VIN_OVLO             (1u << 3)
#define LTC4162_SYS_THERMAL_SHUTDOWN     (1u << 4)
#define LTC4162_SYS_NO_RT                (1u << 5)
/* bit 6 reserved */
#define LTC4162_SYS_CELL_COUNT_ERR       (1u << 7)
#define LTC4162_SYS_EN_CHG               (1u << 8)

/* CHARGE_STATUS (register 0x35) — mutually-exclusive enum, only
 * meaningful while the charger is actively running. */
typedef enum {
    LTC4162_CHARGE_STATUS_OFF              = 0,
    LTC4162_CHARGE_STATUS_CONSTANT_VOLTAGE = 1,
    LTC4162_CHARGE_STATUS_CONSTANT_CURRENT = 2,
    LTC4162_CHARGE_STATUS_IIN_LIMIT_ACTIVE = 4,
    LTC4162_CHARGE_STATUS_VIN_UVCL_ACTIVE  = 8,
    LTC4162_CHARGE_STATUS_THERMAL_REG      = 16,
    LTC4162_CHARGE_STATUS_ILIM_REG         = 32,
} ltc4162_charge_status_t;

/* Engineering-units telemetry snapshot.
 *
 * IBAT is signed: positive when current flows INTO the battery
 * (charging), negative when flowing OUT (discharging). VIN/VOUT/VBAT
 * are unsigned per the datasheet, but the driver returns them as
 * floats for caller convenience. */
typedef struct {
    float    v_bat;          /* V — total pack voltage (cells * per-cell) */
    float    v_in;           /* V — solar / charger input voltage */
    float    v_out;          /* V — bus output voltage */
    float    i_bat_ma;       /* mA — signed; + charging, - discharging */
    float    i_in_ma;        /* mA — input current draw */
    uint16_t charger_state;  /* raw 0x34 — compare against ltc4162_state_t */
    uint16_t charge_status;  /* raw 0x35 — compare against ltc4162_charge_status_t */
    uint16_t system_status;  /* raw 0x39 — bitmask, decode via LTC4162_SYS_*  */
} ltc4162_telemetry_t;

/* Probe the chip with a zero-length I2C write (address-only). */
bool ltc4162_present(i2c_inst_t *i2c, uint8_t addr);

/* One-time init: writes CONFIG_BITS = force_telemetry_on so the
 * telemetry ADC runs even when the charger is suspended (e.g. on
 * battery-only operation with no V_IN). Idempotent. Returns true
 * if the write was ACKed. */
bool ltc4162_init(i2c_inst_t *i2c, uint8_t addr);

/* Enable or disable the JEITA temperature-qualified charging system.
 *
 * Default-on at chip power-up. The chip refuses to enter cc_cv_charge
 * if the NTC pin reading is outside the JEITA temperature window —
 * which on a board with no thermistor populated means the charger
 * sits in ntc_pause forever. For bench bring-up without a thermistor,
 * call with `enabled = false`. Re-enable once a real NTC is wired.
 *
 * Read-modify-write — preserves other bits in CHARGER_CONFIG_BITS_REG. */
bool ltc4162_set_jeita_enabled(i2c_inst_t *i2c, uint8_t addr, bool enabled);

/* Force the charger state machine to re-evaluate by pulsing the
 * suspend_charger bit (set, brief delay, clear). Useful for shaking
 * the chip out of a latched non-charging state like ntc_pause after
 * fixing the underlying condition (e.g. disabling JEITA, swapping
 * the thermistor, etc.). Idempotent and safe to call at any time. */
bool ltc4162_kick(i2c_inst_t *i2c, uint8_t addr);

/* Software workaround for boards without a working NTC thermistor
 * circuit. The chip's hardware ntc_pause exit condition is
 * `jeita_t6 < thermistor_voltage < jeita_t1` — even with
 * en_jeita = 0, the chip still gates ntc_pause on these thresholds.
 *
 * When `enabled = true`, this widens the JEITA temperature window to
 * the full int16 range:
 *   jeita_t1 = INT16_MAX (no reading is colder)
 *   jeita_t6 = INT16_MIN (no reading is hotter)
 * so any thermistor_voltage that passes the hardware open_thermistor
 * check (< 21684) lets the chip exit ntc_pause and start charging.
 *
 * When `enabled = false`, restores the datasheet defaults:
 *   jeita_t1 = 16117 (~0 °C)
 *   jeita_t6 = 4970  (~60 °C)
 *
 * Note: the hardware open_thermistor check (thermistor_voltage > 21684)
 * is in the chip silicon and CANNOT be bypassed. You still need
 * something on the NTC pin that puts its voltage below open_thermistor.
 * Even a single resistor to GND (without a matching NTCBIAS resistor)
 * gives a thermistor_voltage near 0, which is below 21684. */
bool ltc4162_set_ntc_bypass(i2c_inst_t *i2c, uint8_t addr, bool enabled);

/* Read all telemetry registers into `out`. Returns false on any I2C
 * transaction error; in that case `out` is left untouched. */
bool ltc4162_read_telemetry(i2c_inst_t *i2c, uint8_t addr,
                            ltc4162_telemetry_t *out);

/* Short human label for a raw CHARGER_STATE value. */
const char *ltc4162_state_string(uint16_t charger_state);

/* Short human label for a raw CHARGE_STATUS value (or "off"). */
const char *ltc4162_charge_status_string(uint16_t charge_status);
