#include "drivers/comms_link.h"

#include <string.h>

#include "pico/stdlib.h"
#include "hardware/i2c.h"

#include "config/i2c0_bus.h"

/* Per-transaction I2C timeout. The comms board answers out of a RAM
 * buffer in its ISR, so a healthy reply is microseconds; anything
 * approaching this means the bus is stretched or wedged, and we want
 * the poll to fail and say so rather than block the monitor task. */
#define COMMS_LINK_I2C_TIMEOUT_US   10000

/* ------------------------------------------------------------------
 * Raw register access — both halves of a transaction under one lock
 * ----------------------------------------------------------------*/

/* Write the register pointer, repeated-START, read `len` bytes.
 * Caller holds the bus lock. */
static bool read_regs_locked(i2c_inst_t *i2c, uint8_t addr,
                             uint8_t reg, uint8_t *buf, size_t len) {
    int w = i2c_write_timeout_us(i2c, addr, &reg, 1, true,
                                 COMMS_LINK_I2C_TIMEOUT_US);
    if (w != 1) {
        return false;
    }
    int r = i2c_read_timeout_us(i2c, addr, buf, len, false,
                                COMMS_LINK_I2C_TIMEOUT_US);
    return r == (int)len;
}

/* Write `len` bytes starting at `reg`. Caller holds the bus lock.
 * The pointer and the data go out as ONE I2C write — the comms slave
 * takes the first byte of any write as the register pointer, so
 * splitting them into two transactions would leave the pointer
 * re-armed and the data written to the wrong place. */
static bool write_regs_locked(i2c_inst_t *i2c, uint8_t addr,
                              uint8_t reg, const uint8_t *data, size_t len) {
    uint8_t frame[1 + 4];
    if (len > sizeof(frame) - 1) {
        return false;
    }
    frame[0] = reg;
    memcpy(&frame[1], data, len);

    int w = i2c_write_timeout_us(i2c, addr, frame, len + 1, false,
                                 COMMS_LINK_I2C_TIMEOUT_US);
    return w == (int)(len + 1);
}

/* ------------------------------------------------------------------
 * Public API
 * ----------------------------------------------------------------*/

bool comms_link_present(i2c_inst_t *i2c, uint8_t addr) {
    if (!ihu_i2c0_lock(IHU_I2C0_LOCK_TIMEOUT_MS)) {
        return false;
    }
    uint8_t rx;
    int ret = i2c_read_timeout_us(i2c, addr, &rx, 1, false,
                                  COMMS_LINK_I2C_TIMEOUT_US);
    ihu_i2c0_unlock();
    return ret >= 0;
}

bool comms_link_read_status(i2c_inst_t *i2c, uint8_t addr,
                            comms_link_status_t *out) {
    uint8_t buf[COMMS_HK_STATUS_BLOCK_LEN];

    memset(out, 0, sizeof(*out));

    if (!ihu_i2c0_lock(IHU_I2C0_LOCK_TIMEOUT_MS)) {
        return false;
    }
    bool ok = read_regs_locked(i2c, addr, COMMS_HK_REG_WHO_AM_I,
                               buf, sizeof(buf));
    ihu_i2c0_unlock();

    if (!ok) {
        return false;
    }

    /* Identity first — everything below is only meaningful if the
     * thing that answered is the comms board speaking our map. */
    out->who_am_i  = buf[COMMS_HK_REG_WHO_AM_I];
    out->proto_ver = buf[COMMS_HK_REG_PROTO_VER];
    out->fw_ver    = buf[COMMS_HK_REG_FW_VER];

    if (out->who_am_i != COMMS_HK_WHO_AM_I_VALUE ||
        out->proto_ver != COMMS_HK_PROTO_VERSION) {
        return false;
    }

    out->status = buf[COMMS_HK_REG_STATUS];
    out->selftest_done  = (out->status & COMMS_HK_ST_SELFTEST_DONE)  != 0;
    out->si5351_present = (out->status & COMMS_HK_ST_SI5351_PRESENT) != 0;
    out->pll_locked     = (out->status & COMMS_HK_ST_PLL_LOCKED)     != 0;
    out->rx_bb_ok       = (out->status & COMMS_HK_ST_RX_BB_OK)       != 0;
    out->tx_active      = (out->status & COMMS_HK_ST_TX_ACTIVE)      != 0;
    out->wdt_reboot     = (out->status & COMMS_HK_ST_WDT_REBOOT)     != 0;
    out->fault          = (out->status & COMMS_HK_ST_FAULT)          != 0;

    uint8_t st = buf[COMMS_HK_REG_SELFTEST];
    out->check_si5351 = (st >> COMMS_HK_SELFTEST_SI5351_SHIFT) & COMMS_HK_SELFTEST_MASK;
    out->check_rx_bb  = (st >> COMMS_HK_SELFTEST_RX_BB_SHIFT)  & COMMS_HK_SELFTEST_MASK;

    out->i2c_devs   = buf[COMMS_HK_REG_I2C_DEVS];
    out->tasks      = buf[COMMS_HK_REG_TASKS];
    out->si5351_raw = buf[COMMS_HK_REG_SI5351_STATUS];

    out->uptime_s   = comms_hk_get_u32(buf, COMMS_HK_REG_UPTIME_S);
    out->free_heap  = comms_hk_get_u32(buf, COMMS_HK_REG_FREE_HEAP);
    out->rx_bb_mv   = comms_hk_get_u16(buf, COMMS_HK_REG_RX_BB_MV);
    out->xact_count = comms_hk_get_u16(buf, COMMS_HK_REG_XACT_COUNT);

    return true;
}

bool comms_link_ping(i2c_inst_t *i2c, uint8_t addr, uint32_t token,
                     uint32_t *echoed, uint32_t *rtt_us) {
    uint8_t tx[4];
    uint8_t rx[4] = {0};

    comms_hk_put_u32(tx, 0, token);

    if (!ihu_i2c0_lock(IHU_I2C0_LOCK_TIMEOUT_MS)) {
        return false;
    }

    /* Both halves under one lock: a preemption between them would let
     * another poller move the comms board's register pointer, and we
     * would read back somebody else's bytes and call it a failed ping. */
    absolute_time_t t0 = get_absolute_time();
    bool ok = write_regs_locked(i2c, addr, COMMS_HK_REG_SCRATCH, tx, sizeof(tx))
           && read_regs_locked(i2c, addr, COMMS_HK_REG_SCRATCH, rx, sizeof(rx));
    absolute_time_t t1 = get_absolute_time();

    ihu_i2c0_unlock();

    if (!ok) {
        return false;
    }

    uint32_t back = comms_hk_get_u32(rx, 0);
    if (echoed) { *echoed = back; }
    if (rtt_us) { *rtt_us = (uint32_t)absolute_time_diff_us(t0, t1); }

    return back == token;
}

const char *comms_link_check_string(uint8_t check) {
    switch (check) {
    case COMMS_HK_CHECK_PASS: return "PASS";
    case COMMS_HK_CHECK_WARN: return "WARN";
    case COMMS_HK_CHECK_FAIL: return "FAIL";
    default:                  return "?";
    }
}
