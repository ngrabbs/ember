#include "tasks/comms_monitor_task.h"

#include <stdio.h>
#include <stdint.h>
#include <stdbool.h>

#include "FreeRTOS.h"
#include "task.h"
#include "pico/stdlib.h"

#include "config/pinmap.h"
#include "config/i2c0_bus.h"
#include "drivers/comms_link.h"

#define COMMS_POLL_PERIOD_MS    5000
#define COMMS_TASK_STACK_WORDS  640
#define COMMS_TASK_NAME         "comms-mon"

/* Offset so the comms poll does not land on the same tick as the EPS
 * poll. Both run at 5 s; without this they would contend for the bus
 * lock every single cycle, and one would always be reported with the
 * other's lock wait folded into its timing. */
#define COMMS_POLL_PHASE_MS     2500

/* Same contract as the EPS snapshot: updated only from this task,
 * word-sized loads and stores on RP2040, and read by the CLI as a
 * diagnostic. A torn read here would cost one misprinted line, not
 * correctness of anything the flight software acts on. */
static comms_link_status_t s_last_status;
static comms_link_health_t s_health;
static volatile bool       s_quiet = false;

bool ihu_comms_get_latest_status(comms_link_status_t *out) {
    if (!s_health.ever_seen) {
        return false;
    }
    *out = s_last_status;
    return true;
}

void ihu_comms_get_health(comms_link_health_t *out) { *out = s_health; }
void ihu_comms_set_quiet(bool quiet)                { s_quiet = quiet; }

/* ------------------------------------------------------------------
 * Pretty-printer
 * ----------------------------------------------------------------*/
static void print_status(const comms_link_status_t *s, uint32_t rtt_us) {
    printf("[comms] fw=v%u.%u  up=%lu s  tasks=%u  heap=%lu B  rtt=%lu us\n",
           (unsigned)(s->fw_ver >> 4), (unsigned)(s->fw_ver & 0xF),
           (unsigned long)s->uptime_s, (unsigned)s->tasks,
           (unsigned long)s->free_heap, (unsigned long)rtt_us);

    if (!s->selftest_done) {
        printf("[comms]   self-test has not completed yet\n");
        return;
    }

    printf("[comms]   si5351=%s (raw=0x%02X, %s)  rx-bb=%s (%u mV)  "
           "i2c-devs=%u\n",
           comms_link_check_string(s->check_si5351), s->si5351_raw,
           s->pll_locked ? "PLLs locked" : "PLL unlocked",
           comms_link_check_string(s->check_rx_bb),
           (unsigned)s->rx_bb_mv, (unsigned)s->i2c_devs);

    /* TX_ACTIVE also drives the T/R switch, so this is the IHU's only
     * independent read on whether the comms board is putting RF on the
     * antenna. Worth a line of its own every time it is set. */
    if (s->tx_active) {
        printf("[comms]   TX ACTIVE — T/R switch in transmit\n");
    }
    if (s->wdt_reboot) {
        printf("[comms]   note: comms board last reset by WATCHDOG TIMEOUT\n");
    }
    if (s->fault) {
        printf("[comms]   ALERT: comms board reports a self-test FAIL\n");
    }
}

/* ------------------------------------------------------------------
 * Task body
 * ----------------------------------------------------------------*/
static void comms_monitor_task(void *pvParameters) {
    (void)pvParameters;

    /* i2c0 is brought up in main() by ihu_i2c0_bus_init(), before any
     * task runs — we just need to be after the EPS task's boot scan so
     * the console output stays in a sensible order. */
    vTaskDelay(pdMS_TO_TICKS(4000 + COMMS_POLL_PHASE_MS));

    printf("[comms] polling comms board at 0x%02X @ %d s cadence\n",
           COMMS_HK_I2C_ADDR, COMMS_POLL_PERIOD_MS / 1000);

    /* Seeded from the tick count so a reboot of either board produces
     * visibly different tokens in the log — makes a stale echo obvious
     * instead of coincidentally correct. */
    uint32_t token = 0xE3B70000u ^ (uint32_t)xTaskGetTickCount();

    for (;;) {
        ++s_health.polls;
        ++token;

        uint32_t echoed = 0;
        uint32_t rtt_us = 0;
        bool ping_ok = comms_link_ping(IHU_I2C_EPS_INSTANCE, COMMS_HK_I2C_ADDR,
                                       token, &echoed, &rtt_us);

        comms_link_status_t st;
        bool status_ok = ping_ok
            && comms_link_read_status(IHU_I2C_EPS_INSTANCE,
                                      COMMS_HK_I2C_ADDR, &st);

        bool was_up = s_health.link_up;

        if (status_ok) {
            s_last_status       = st;
            s_health.link_up    = true;
            s_health.ever_seen  = true;
            s_health.failures   = 0;
            s_health.last_ok_ms = (uint32_t)(xTaskGetTickCount() * portTICK_PERIOD_MS);
            s_health.last_rtt_us = rtt_us;

            /* A link that just came back is worth saying out loud even
             * when the periodic print is silenced — it is a state
             * change, not routine telemetry. */
            if (!was_up) {
                printf("[comms] link UP — comms board answering at 0x%02X\n",
                       COMMS_HK_I2C_ADDR);
            }
            if (!s_quiet) {
                print_status(&st, rtt_us);
            }
        } else {
            s_health.link_up = false;
            ++s_health.failures;

            /* Report the transition, then go quiet. A board that is
             * simply not plugged in should not fill the console with
             * the same line every 5 seconds — `comms` still shows the
             * failure count on demand. */
            if (was_up || s_health.failures == 1) {
                /* Ask the bus which failure this is rather than
                 * inferring it from out-params the ping leaves
                 * untouched on an I2C error — "echoed == 0" is a
                 * perfectly legal echo value. */
                if (!ping_ok && !comms_link_present(IHU_I2C_EPS_INSTANCE,
                                                    COMMS_HK_I2C_ADDR)) {
                    printf("[comms] link DOWN — no response at 0x%02X "
                           "(check SDA_HK/SCL_HK wiring and comms board power)\n",
                           COMMS_HK_I2C_ADDR);
                } else if (!ping_ok) {
                    printf("[comms] link DOWN — device ACKs at 0x%02X but the "
                           "echo came back wrong: sent 0x%08lX got 0x%08lX\n",
                           COMMS_HK_I2C_ADDR,
                           (unsigned long)token, (unsigned long)echoed);
                } else {
                    printf("[comms] link DOWN — ping OK but status read "
                           "failed (wrong device at 0x%02X, or proto version "
                           "mismatch: this IHU speaks v%u)\n",
                           COMMS_HK_I2C_ADDR, (unsigned)COMMS_HK_PROTO_VERSION);
                }
            }
        }

        vTaskDelay(pdMS_TO_TICKS(COMMS_POLL_PERIOD_MS));
    }
}

BaseType_t ihu_comms_monitor_task_start(UBaseType_t priority) {
    return xTaskCreate(comms_monitor_task, COMMS_TASK_NAME,
                       COMMS_TASK_STACK_WORDS, NULL, priority, NULL);
}
