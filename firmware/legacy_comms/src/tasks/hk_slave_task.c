#include "tasks/hk_slave_task.h"

#include <stdio.h>
#include <string.h>

#include "FreeRTOS.h"
#include "task.h"
#include "pico/stdlib.h"
#include "pico/i2c_slave.h"
#include "hardware/gpio.h"
#include "hardware/i2c.h"
#include "hardware/irq.h"
#include "hardware/watchdog.h"

#include "config/pinmap.h"
#include "comms_hk_proto.h"
#include "tasks/selftest_task.h"

#define HK_SLAVE_TASK_NAME          "hk-slave"
#define HK_SLAVE_TASK_STACK_WORDS   512

/* How often the task rebuilds the register file. Fast enough that the
 * IHU's 5 s poll never sees a value more than one refresh stale, slow
 * enough to be free. */
#define COMMS_HK_REFRESH_MS         1000

/* ------------------------------------------------------------------
 * The register file
 *
 * One flat byte array, laid out exactly as comms_hk_proto.h describes.
 * Written by the task, read by the ISR; the scratch echo goes the
 * other way. Nothing else in the firmware touches it.
 * ----------------------------------------------------------------*/
static volatile uint8_t s_regs[COMMS_HK_REG_COUNT];

/* Slave-side transaction state. Only ever touched from the I2C ISR, so
 * it needs no guarding of its own. */
static struct {
    uint8_t reg_ptr;      /* auto-incrementing register pointer */
    bool    ptr_pending;  /* next received byte is the pointer, not data */
    volatile uint16_t xacts;  /* written in the ISR, read from task context */
} s_bus;

static volatile bool s_up = false;

uint16_t comms_hk_slave_xact_count(void) { return s_bus.xacts; }
bool     comms_hk_slave_is_up(void)      { return s_up; }

/* Scratch is the one writable window. Keeping the test in one place
 * means a future writable register is a one-line change here and
 * cannot be added by accident. */
static bool reg_is_writable(uint8_t reg) {
    return reg >= COMMS_HK_REG_SCRATCH
        && reg <  COMMS_HK_REG_SCRATCH + 4;
}

/* ------------------------------------------------------------------
 * ISR — runs on every byte the master clocks. Keep it boring.
 *
 * The SDK calls this from the I2C IRQ on whichever core ran
 * i2c_slave_init(). Budget is under ~25 us at 400 kHz per the
 * pico_i2c_slave docs, so: no printf, no FreeRTOS API, no loops that
 * are not bounded by the FIFO.
 * ----------------------------------------------------------------*/
static void hk_slave_handler(i2c_inst_t *i2c, i2c_slave_event_t event) {
    switch (event) {
    case I2C_SLAVE_RECEIVE:
        /* Master is writing to us. The first byte of any write is the
         * register pointer — that is what makes the read form
         * (write pointer, repeated-START, read) work. */
        while (i2c_get_read_available(i2c)) {
            uint8_t b = i2c_read_byte_raw(i2c);
            if (s_bus.ptr_pending) {
                /* Masked into the map, so a pointer past the end wraps
                 * to a real register instead of leaving the pointer in
                 * a state the increment below cannot reason about.
                 * COMMS_HK_REG_COUNT is a power of two, so this is an
                 * AND, not a division, in the ISR. */
                s_bus.reg_ptr     = (uint8_t)(b % COMMS_HK_REG_COUNT);
                s_bus.ptr_pending = false;
            } else {
                if (reg_is_writable(s_bus.reg_ptr)) {
                    s_regs[s_bus.reg_ptr] = b;
                }
                /* Advance even on a rejected write so a burst write
                 * that straddles read-only space still lands its
                 * writable bytes at the right offsets. */
                s_bus.reg_ptr = (uint8_t)((s_bus.reg_ptr + 1) % COMMS_HK_REG_COUNT);
            }
        }
        break;

    case I2C_SLAVE_REQUEST:
        /* Master is reading. Exactly ONE byte per request, never a
         * FIFO stuff.
         *
         * RD_REQ fires when the master wants a byte and the TX FIFO is
         * empty; the hardware stretches SCL until we supply one. If we
         * filled the 16-byte FIFO instead, a master that read fewer
         * bytes than we queued would leave the rest sitting there, and
         * the NEXT transaction would be served those stale bytes from
         * the old pointer position. The controller does flush the FIFO
         * on the resulting TX_ABRT, but "the error path cleans up
         * after us" is not a protocol. One byte per request has no
         * such window. */
        i2c_write_byte_raw(i2c, s_regs[s_bus.reg_ptr]);
        s_bus.reg_ptr = (uint8_t)((s_bus.reg_ptr + 1) % COMMS_HK_REG_COUNT);
        break;

    case I2C_SLAVE_FINISH:
        /* STOP or repeated-START. Arm the pointer for the next write
         * phase and count the transaction.
         *
         * A repeated-START also lands here, so the read form counts as
         * two: the pointer write and the data read. That is fine — the
         * IHU only uses this as a monotonic "the link is carrying
         * traffic" counter, not as a request tally. */
        s_bus.ptr_pending = true;
        ++s_bus.xacts;
        break;
    }
}

/* ------------------------------------------------------------------
 * Register file refresh — the slow half, in task context
 * ----------------------------------------------------------------*/

/* comms_check_t and the wire encoding are deliberately separate enums
 * so the protocol does not silently change if the local one is
 * reordered. */
static uint8_t encode_check(comms_check_t c) {
    switch (c) {
    case COMMS_CHECK_PASS: return COMMS_HK_CHECK_PASS;
    case COMMS_CHECK_WARN: return COMMS_HK_CHECK_WARN;
    default:               return COMMS_HK_CHECK_FAIL;
    }
}

/* Publish a freshly-built copy into the live register file.
 *
 * The ISR can fire in the middle of a burst read, so a half-updated
 * uptime would ship two bytes from the old value and two from the new.
 * Masking the I2C IRQ for the duration of the copy makes the update
 * atomic from the master's point of view. The window is a ~20 byte
 * memcpy — far shorter than the inter-byte gap at any I2C rate, so no
 * transaction is at risk of being dropped.
 *
 * SCRATCH is copied out of the live file first and back in after: it
 * belongs to the master, and clobbering it here would break the echo. */
static void publish(const uint8_t *staged) {
    /* Before i2c_slave_init() there is no handler on this IRQ and no
     * ISR to race with, so masking it would only risk enabling a
     * vector that points at nothing. Copy straight through. */
    if (!s_up) {
        for (uint8_t i = 0; i < COMMS_HK_REG_SCRATCH; ++i) {
            s_regs[i] = staged[i];
        }
        return;
    }

    /* NOTE: irq_set_enabled() acts on the calling core's NVIC, and
     * i2c_slave_init() enabled this IRQ on whichever core ran it. That
     * is the same core today because the kernel is built single-core
     * (see FreeRTOSConfig.h). If SMP is ever turned on, this task and
     * the slave ISR must be pinned to the same core or this critical
     * section silently stops being one. */
    uint irq = (COMMS_HK_I2C_INSTANCE == i2c0) ? I2C0_IRQ : I2C1_IRQ;

    irq_set_enabled(irq, false);
    for (uint8_t i = 0; i < COMMS_HK_REG_SCRATCH; ++i) {
        s_regs[i] = staged[i];
    }
    irq_set_enabled(irq, true);
}

static void refresh_regs(void) {
    uint8_t staged[COMMS_HK_REG_SCRATCH];
    memset(staged, 0, sizeof(staged));

    staged[COMMS_HK_REG_WHO_AM_I]  = COMMS_HK_WHO_AM_I_VALUE;
    staged[COMMS_HK_REG_PROTO_VER] = COMMS_HK_PROTO_VERSION;
    staged[COMMS_HK_REG_FW_VER]    = COMMS_HK_FW_VERSION;

    uint8_t status = 0;
    if (watchdog_caused_reboot()) {
        status |= COMMS_HK_ST_WDT_REBOOT;
    }
    /* TX_ACTIVE doubles as the T/R switch control, so its output level
     * is the authoritative "is RF on the antenna" answer — better than
     * a firmware flag that could disagree with the pin. */
    if (gpio_get_out_level(COMMS_TX_ACTIVE_GPIO)) {
        status |= COMMS_HK_ST_TX_ACTIVE;
    }

    comms_selftest_result_t st;
    if (comms_selftest_get_result(&st)) {
        status |= COMMS_HK_ST_SELFTEST_DONE;

        if (st.si5351_status.present) {
            status |= COMMS_HK_ST_SI5351_PRESENT;
        }
        /* Both PLLs locked is the free crystal-health check the
         * self-test already makes — the PLLs cannot lock without Y1
         * oscillating. */
        if (st.si5351_status.present
            && !st.si5351_status.lol_a && !st.si5351_status.lol_b) {
            status |= COMMS_HK_ST_PLL_LOCKED;
        }
        if (st.rx_baseband == COMMS_CHECK_PASS) {
            status |= COMMS_HK_ST_RX_BB_OK;
        }
        if (st.si5351 == COMMS_CHECK_FAIL || st.rx_baseband == COMMS_CHECK_FAIL) {
            status |= COMMS_HK_ST_FAULT;
        }

        staged[COMMS_HK_REG_SELFTEST] =
              (uint8_t)(encode_check(st.si5351)      << COMMS_HK_SELFTEST_SI5351_SHIFT)
            | (uint8_t)(encode_check(st.rx_baseband) << COMMS_HK_SELFTEST_RX_BB_SHIFT);

        staged[COMMS_HK_REG_I2C_DEVS]      = st.i2c_device_count;
        staged[COMMS_HK_REG_SI5351_STATUS] = st.si5351_status.raw_status;

        /* Volts → millivolts. Clamped rather than wrapped: a floating
         * ADC pin can read outside the rails' nominal range, and a
         * wrapped u16 would look like a plausible reading. */
        float mv = st.rx_baseband_v * 1000.0f;
        if (mv < 0.0f)       { mv = 0.0f; }
        if (mv > 65535.0f)   { mv = 65535.0f; }
        comms_hk_put_u16(staged, COMMS_HK_REG_RX_BB_MV, (uint16_t)mv);
    }
    staged[COMMS_HK_REG_STATUS] = status;

    staged[COMMS_HK_REG_TASKS] = (uint8_t)uxTaskGetNumberOfTasks();

    uint32_t uptime_s = (uint32_t)(xTaskGetTickCount() * portTICK_PERIOD_MS) / 1000u;
    comms_hk_put_u32(staged, COMMS_HK_REG_UPTIME_S, uptime_s);
    comms_hk_put_u32(staged, COMMS_HK_REG_FREE_HEAP, (uint32_t)xPortGetFreeHeapSize());
    comms_hk_put_u16(staged, COMMS_HK_REG_XACT_COUNT, s_bus.xacts);

    publish(staged);
}

/* ------------------------------------------------------------------
 * Task body
 * ----------------------------------------------------------------*/
static void hk_slave_task(void *pvParameters) {
    (void)pvParameters;

    /* Let the self-test finish its bus scan and publish first, so the
     * very first register file the IHU can read is already populated
     * rather than a block of zeros that looks like a sick board. The
     * cap matches the console task's — a self-test that never
     * completes costs us the initial contents, not the link. */
    for (int waited = 0; waited < 15000; waited += 100) {
        comms_selftest_result_t ignored;
        if (comms_selftest_get_result(&ignored)) {
            break;
        }
        vTaskDelay(pdMS_TO_TICKS(100));
    }

    memset((void *)s_regs, 0, sizeof(s_regs));
    comms_hk_put_u32((uint8_t *)s_regs, COMMS_HK_REG_SCRATCH, COMMS_HK_SCRATCH_RESET);
    s_bus.ptr_pending = true;
    refresh_regs();

    /* i2c1 is ours alone — nothing else on this board touches it, so
     * no bus mutex is needed here (unlike i2c0, which the self-test
     * owns for the Si5351A). */
    i2c_init(COMMS_HK_I2C_INSTANCE, COMMS_HK_I2C_HZ);
    gpio_set_function(COMMS_HK_I2C_SDA_GPIO, GPIO_FUNC_I2C);
    gpio_set_function(COMMS_HK_I2C_SCL_GPIO, GPIO_FUNC_I2C);
    /* Bus pull-ups live on the EPS side (R4/R5, 4.7k). These weak
     * internal ones (50-80k) are harmless in parallel and keep the bus
     * defined on a bench setup with nothing else attached. */
    gpio_pull_up(COMMS_HK_I2C_SDA_GPIO);
    gpio_pull_up(COMMS_HK_I2C_SCL_GPIO);

    i2c_slave_init(COMMS_HK_I2C_INSTANCE, COMMS_HK_I2C_ADDR, hk_slave_handler);
    s_up = true;

    printf("[hk] i2c slave up: addr=0x%02X on i2c1 (sda=GP%d scl=GP%d), "
           "%u-byte register map\n",
           COMMS_HK_I2C_ADDR, COMMS_HK_I2C_SDA_GPIO, COMMS_HK_I2C_SCL_GPIO,
           (unsigned)COMMS_HK_REG_COUNT);

    for (;;) {
        vTaskDelay(pdMS_TO_TICKS(COMMS_HK_REFRESH_MS));
        refresh_regs();
    }
}

BaseType_t comms_hk_slave_task_start(UBaseType_t priority) {
    return xTaskCreate(hk_slave_task, HK_SLAVE_TASK_NAME,
                       HK_SLAVE_TASK_STACK_WORDS, NULL, priority, NULL);
}
