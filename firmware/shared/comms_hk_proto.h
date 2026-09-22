/*
 * ember housekeeping I2C protocol — IHU (master) ↔ comms board (slave).
 *
 * Shared by BOTH firmware trees. firmware/ihu and firmware/comms each
 * add firmware/shared to their include path, so there is exactly one
 * definition of the register map and neither side can drift.
 *
 *   #include "comms_hk_proto.h"
 *
 * ── Why a register map and not a packet protocol ──────────────────
 *
 * The IHU already speaks "write a register pointer, repeated-START,
 * read N bytes" to the LTC4162 on the EPS. Making the comms board look
 * like one more chip on the same housekeeping bus means the IHU's
 * `comms` command is the same shape as its `eps` command, the same
 * bus-error handling covers both, and a bench i2cdetect/i2cdump finds
 * the comms board without any custom tooling.
 *
 * ── Transaction format ───────────────────────────────────────────
 *
 *   Read:   S ADDR+W  reg  Sr ADDR+R  d0 d1 ... dn  P
 *   Write:  S ADDR+W  reg  d0 d1 ... dn  P
 *
 * The register pointer auto-increments after every byte and wraps at
 * COMMS_HK_REG_COUNT, so the whole status block is one burst read and
 * an over-long read wraps back to the top instead of stalling the bus.
 * A pointer written past the end of the map is masked into it by the
 * same wrap. The reserved tail (0x18..0x1F) reads as 0x00.
 *
 * ── Endianness ───────────────────────────────────────────────────
 *
 * Multi-byte fields are LITTLE-endian (low byte at the low address).
 * Both ends are RP2040, so this is the native order on both sides and
 * it matches the LSB-first convention the LTC4162 already uses on this
 * bus. Do not memcpy a struct across — read the bytes and assemble
 * them, which is what comms_hk_get_u16()/u32() below are for.
 *
 * ── Versioning ───────────────────────────────────────────────────
 *
 * COMMS_HK_WHO_AM_I_VALUE identifies the device; COMMS_HK_PROTO_VERSION
 * identifies this register map. Bump the proto version when a field
 * moves or changes meaning, never when a field is added to the
 * reserved tail. The IHU checks both on every poll, so a mismatched
 * pair of binaries is reported rather than silently misparsed.
 */

#pragma once

#include <stdint.h>

/* ------------------------------------------------------------------
 * Bus address
 *
 * 7-bit. Lives on the shared CSKB housekeeping bus (H1.41 SDA_SYS /
 * H1.43 SCL_SYS) alongside the EPS LTC4162 at 0x68. 0x42 is outside
 * both I2C reserved ranges (000 0xxx and 111 1xxx) and collides with
 * nothing else in the stack:
 *
 *   0x42  comms board      (this)
 *   0x60  Si5351A          (comms-board-local bus only, not on CSKB)
 *   0x68  LTC4162-L        (EPS)
 * ----------------------------------------------------------------*/
#define COMMS_HK_I2C_ADDR           0x42

/* ------------------------------------------------------------------
 * Register map
 * ----------------------------------------------------------------*/

#define COMMS_HK_REG_WHO_AM_I       0x00  /* u8  ro — COMMS_HK_WHO_AM_I_VALUE */
#define COMMS_HK_REG_PROTO_VER      0x01  /* u8  ro — COMMS_HK_PROTO_VERSION */
#define COMMS_HK_REG_FW_VER         0x02  /* u8  ro — major<<4 | minor */
#define COMMS_HK_REG_STATUS         0x03  /* u8  ro — COMMS_HK_ST_* bitfield */
#define COMMS_HK_REG_SELFTEST       0x04  /* u8  ro — packed 2-bit check results */
#define COMMS_HK_REG_I2C_DEVS       0x05  /* u8  ro — devices on the comms-local bus */
#define COMMS_HK_REG_TASKS          0x06  /* u8  ro — FreeRTOS task count */
#define COMMS_HK_REG_SI5351_STATUS  0x07  /* u8  ro — Si5351A register 0, raw */
#define COMMS_HK_REG_UPTIME_S       0x08  /* u32 ro — seconds since boot */
#define COMMS_HK_REG_FREE_HEAP      0x0C  /* u32 ro — xPortGetFreeHeapSize() */
#define COMMS_HK_REG_RX_BB_MV       0x10  /* u16 ro — RX baseband DC bias, mV */
#define COMMS_HK_REG_XACT_COUNT     0x12  /* u16 ro — I2C transactions served */
#define COMMS_HK_REG_SCRATCH        0x14  /* u32 rw — echo register, see below */
/* 0x18..0x1F reserved — read as 0x00, writes ignored. */

/* Size of the register file, and the modulus the comms board's
 * register pointer wraps at. Kept a power of two so that wrap is a
 * mask rather than a division in the slave ISR. */
#define COMMS_HK_REG_COUNT          0x20

/* One burst read from 0x00 of this many bytes gets the entire live
 * status block (everything except the scratch echo). */
#define COMMS_HK_STATUS_BLOCK_LEN   0x14

/* ------------------------------------------------------------------
 * Identity
 * ----------------------------------------------------------------*/

/* 0xEC — "EmberComms". Chosen so a stuck bus reading all-ones (0xFF)
 * or all-zeros (0x00) cannot be mistaken for a live board. */
#define COMMS_HK_WHO_AM_I_VALUE     0xEC

#define COMMS_HK_PROTO_VERSION      0x01

/* Firmware version reported in COMMS_HK_REG_FW_VER, major<<4 | minor. */
#define COMMS_HK_FW_VERSION         0x01   /* v0.1 */

/* ------------------------------------------------------------------
 * COMMS_HK_REG_STATUS bits
 * ----------------------------------------------------------------*/

#define COMMS_HK_ST_SELFTEST_DONE   (1u << 0)  /* boot self-test has published */
#define COMMS_HK_ST_SI5351_PRESENT  (1u << 1)  /* clock gen ACKed on its bus */
#define COMMS_HK_ST_PLL_LOCKED      (1u << 2)  /* both PLLs locked (Y1 alive) */
#define COMMS_HK_ST_RX_BB_OK        (1u << 3)  /* RX baseband bias in tolerance */
#define COMMS_HK_ST_TX_ACTIVE       (1u << 4)  /* T/R line asserted — RF is on */
#define COMMS_HK_ST_WDT_REBOOT      (1u << 5)  /* last reset was a watchdog timeout */
/* bit 6 reserved */
#define COMMS_HK_ST_FAULT           (1u << 7)  /* at least one self-test FAIL */

/* ------------------------------------------------------------------
 * COMMS_HK_REG_SELFTEST — two bits per check
 *
 * Values are comms_check_t: 0 = PASS, 1 = WARN, 2 = FAIL. Packed so a
 * single byte carries the per-check detail that the STATUS bitfield
 * flattens to pass/fail.
 * ----------------------------------------------------------------*/

#define COMMS_HK_SELFTEST_SI5351_SHIFT   0
#define COMMS_HK_SELFTEST_RX_BB_SHIFT    2
#define COMMS_HK_SELFTEST_MASK           0x3

#define COMMS_HK_CHECK_PASS         0
#define COMMS_HK_CHECK_WARN         1
#define COMMS_HK_CHECK_FAIL         2

/* ------------------------------------------------------------------
 * COMMS_HK_REG_SCRATCH — the ping echo
 *
 * The only writable register. The IHU writes an arbitrary 32-bit token
 * and reads it back; a match proves the full round trip — the IHU's
 * write path, the comms slave ISR, and the IHU's read path — rather
 * than just "something on the bus ACKed an address", which is all a
 * bare address probe tells you.
 *
 * The comms board never interprets the value. It resets to
 * COMMS_HK_SCRATCH_RESET at boot, which doubles as a "comms rebooted
 * since my last ping" indicator for the IHU.
 * ----------------------------------------------------------------*/
#define COMMS_HK_SCRATCH_RESET      0x00000000u

/* ------------------------------------------------------------------
 * Little-endian accessors
 *
 * Both sides read the register file as a flat byte array; these keep
 * the assembly identical on each end and make the byte order explicit
 * at every call site.
 * ----------------------------------------------------------------*/

static inline uint16_t comms_hk_get_u16(const uint8_t *buf, uint8_t reg) {
    return (uint16_t)buf[reg] | ((uint16_t)buf[reg + 1] << 8);
}

static inline uint32_t comms_hk_get_u32(const uint8_t *buf, uint8_t reg) {
    return (uint32_t)buf[reg]
         | ((uint32_t)buf[reg + 1] << 8)
         | ((uint32_t)buf[reg + 2] << 16)
         | ((uint32_t)buf[reg + 3] << 24);
}

static inline void comms_hk_put_u16(uint8_t *buf, uint8_t reg, uint16_t v) {
    buf[reg]     = (uint8_t)(v & 0xFF);
    buf[reg + 1] = (uint8_t)(v >> 8);
}

static inline void comms_hk_put_u32(uint8_t *buf, uint8_t reg, uint32_t v) {
    buf[reg]     = (uint8_t)(v & 0xFF);
    buf[reg + 1] = (uint8_t)((v >> 8)  & 0xFF);
    buf[reg + 2] = (uint8_t)((v >> 16) & 0xFF);
    buf[reg + 3] = (uint8_t)((v >> 24) & 0xFF);
}
