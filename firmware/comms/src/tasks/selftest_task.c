#include "tasks/selftest_task.h"

#include <stdio.h>
#include <string.h>

#include "FreeRTOS.h"
#include "task.h"
#include "pico/stdlib.h"
#include "pico/unique_id.h"
#if LIB_PICO_STDIO_USB
#include "pico/stdio_usb.h"
#endif
#include "hardware/adc.h"
#include "hardware/gpio.h"
#include "hardware/i2c.h"
#include "hardware/watchdog.h"

#include "config/pinmap.h"
#include "si5351a.h"

/* printf with floats plus the bus scan; 768 words matches what the IHU
 * eps task needed for the same mix. */
#define SELFTEST_TASK_STACK_WORDS   768
#define SELFTEST_TASK_NAME          "selftest"

/* Let the console attach before the banner goes out — without this the
 * first lines land in the void and bring-up looks like a dead board.
 *
 * USB CDC we can ask about directly, so the cap is generous and costs
 * nothing when a host is already there. UART has nothing to ask, so it
 * is a flat settle. Both are bounded: a board sitting on a bench power
 * supply with no console attached still has to finish its self-test. */
#define SELFTEST_USB_WAIT_MS        3000
#define SELFTEST_USB_POLL_MS          50
#define SELFTEST_UART_SETTLE_MS     1500

/* Some host terminals drop the first bytes sent immediately after the
 * CDC connection comes up (the SDK does the same thing for its own
 * PICO_STDIO_USB_CONNECT_WAIT_TIMEOUT_MS path). */
#define SELFTEST_POST_CONNECT_MS      50

/* Averaged to knock down ADC noise — the bias check only cares about
 * the DC level, and the RP2040 SAR is noisy enough at 12 bits that a
 * single sample can move the reading by a few tens of millivolts. */
#define RX_BASEBAND_SAMPLES         64

static comms_selftest_result_t s_result;
static volatile bool           s_complete = false;

bool comms_selftest_get_result(comms_selftest_result_t *out) {
    if (!s_complete) {
        return false;
    }
    *out = s_result;
    return true;
}

static const char *check_str(comms_check_t c) {
    switch (c) {
    case COMMS_CHECK_PASS: return "PASS";
    case COMMS_CHECK_WARN: return "WARN";
    default:               return "FAIL";
    }
}

/* ------------------------------------------------------------------
 * Step 1 — safe the outputs
 *
 * Runs before any detection. Every pin below drives something real;
 * leaving one floating between reset and the first command is how you
 * get a random-phase carrier or a spurious IRQ at the IHU.
 * ----------------------------------------------------------------*/
static void safe_outputs(void) {
    /* COMMS_IRQ is active-low with its pull-up on the IHU side. Set the
     * output level BEFORE switching the pin to an output, so it never
     * glitches low on the way. */
    gpio_init(COMMS_IRQ_GPIO);
    gpio_put(COMMS_IRQ_GPIO, COMMS_IRQ_DEASSERTED);
    gpio_set_dir(COMMS_IRQ_GPIO, GPIO_OUT);

    /* XOR modulator data input — low means "no phase inversion". */
    gpio_init(COMMS_BPSK_DATA_GPIO);
    gpio_put(COMMS_BPSK_DATA_GPIO, 0);
    gpio_set_dir(COMMS_BPSK_DATA_GPIO, GPIO_OUT);

    /* T/R control (and the TX LED on the current board). Low = receive,
     * which is also where the board pull-down parks it. */
    gpio_init(COMMS_TX_ACTIVE_GPIO);
    gpio_put(COMMS_TX_ACTIVE_GPIO, 0);
    gpio_set_dir(COMMS_TX_ACTIVE_GPIO, GPIO_OUT);

    gpio_init(COMMS_RX_ACTIVE_GPIO);
    gpio_put(COMMS_RX_ACTIVE_GPIO, 0);
    gpio_set_dir(COMMS_RX_ACTIVE_GPIO, GPIO_OUT);

    /* Power indicator — on as soon as firmware is running. */
    gpio_init(COMMS_PWR_IND_GPIO);
    gpio_put(COMMS_PWR_IND_GPIO, 1);
    gpio_set_dir(COMMS_PWR_IND_GPIO, GPIO_OUT);

    printf("[comms] outputs safed: BPSK_DATA=0 TX_ACTIVE=0 (RX) COMMS_IRQ=1 (de-asserted)\n");
}

/* ------------------------------------------------------------------
 * Step 2a — i2c0 bus scan
 * ----------------------------------------------------------------*/

/* I2C reserved addresses per the spec: 000 0xxx and 111 1xxx.
 * Skip them so we don't probe weirdness like the general-call address. */
static bool i2c_addr_is_reserved(uint8_t addr) {
    return (addr & 0x78) == 0 || (addr & 0x78) == 0x78;
}

static uint8_t i2c_bus_scan(void) {
    uint8_t found = 0;

    printf("[comms] scanning i2c0 (sda=GP%d scl=GP%d @ %u Hz)\n",
           COMMS_I2C_SDA_GPIO, COMMS_I2C_SCL_GPIO, (unsigned)COMMS_I2C_HZ);

    for (uint8_t addr = 0; addr < 0x80; ++addr) {
        if (i2c_addr_is_reserved(addr)) {
            continue;
        }
        uint8_t rx;
        if (i2c_read_blocking(COMMS_I2C_INSTANCE, addr, &rx, 1, false) >= 0) {
            printf("[comms]   found device at 0x%02X%s\n", addr,
                   addr == SI5351A_ADDR ? " (Si5351A)" : "");
            ++found;
        }
    }

    if (found == 0) {
        printf("[comms] no devices responded — check pull-ups (R1/R2), +3V3, wiring\n");
    }
    return found;
}

/* ------------------------------------------------------------------
 * Step 2b — Si5351A status probe (read-only)
 * ----------------------------------------------------------------*/
static comms_check_t probe_si5351(si5351_status_t *status) {
    si5351_dev_t dev = { .i2c = COMMS_I2C_INSTANCE };

    if (si5351_probe(&dev, status) != 0) {
        printf("[si5351a] not responding at 0x%02X\n", SI5351A_ADDR);
        return COMMS_CHECK_FAIL;
    }

    printf("[si5351a] present at 0x%02X  status=0x%02X  rev=%u\n",
           SI5351A_ADDR, status->raw_status, (unsigned)status->revid);

    /* SYS_INIT should have cleared long before we get here. If it has
     * not, the part is powered but not running — usually a missing or
     * dead 25 MHz crystal, since the internal init waits on it. */
    if (status->sys_init) {
        printf("[si5351a]   SYS_INIT still set — device not ready "
               "(check Y1 25 MHz crystal and C4/C5 load caps)\n");
        return COMMS_CHECK_WARN;
    }

    /* Neither PLL has been configured yet, so this reports their state on
     * the power-on default dividers. Both locked is the useful case: the
     * PLLs can only lock if the 25 MHz crystal (Y1) is actually
     * oscillating, which makes this a free oscillator health check.
     * Unlocked here is not a fault on its own — it only becomes one if
     * it persists after si5351_init(). */
    printf("[si5351a]   PLLA %s  PLLB %s  (power-on defaults; both locked "
           "means Y1 25 MHz is oscillating)\n",
           status->lol_a ? "unlocked" : "locked",
           status->lol_b ? "unlocked" : "locked");

    if (status->lol_a || status->lol_b) {
        printf("[si5351a]   not conclusive yet — re-check lock after "
               "si5351_init() before suspecting the crystal\n");
    }

    return COMMS_CHECK_PASS;
}

/* ------------------------------------------------------------------
 * Step 2c — RX baseband DC bias
 *
 * The MCP6022 gain stage is biased to mid-supply so it can swing both
 * ways on a single rail. With no signal in, its output sits at that
 * bias point, which makes the idle DC level a direct read on whether
 * the analog RX chain is populated and powered.
 * ----------------------------------------------------------------*/
static comms_check_t measure_rx_baseband(float *out_volts) {
    adc_init();
    adc_gpio_init(COMMS_RX_BASEBAND_GPIO);
    adc_select_input(COMMS_RX_BASEBAND_ADC_CH);

    uint32_t accum = 0;
    for (int i = 0; i < RX_BASEBAND_SAMPLES; ++i) {
        accum += adc_read();
    }

    float volts = ((float)accum / RX_BASEBAND_SAMPLES)
                  * (COMMS_ADC_VREF_V / COMMS_ADC_FULL_SCALE);
    *out_volts = volts;

    float error = volts - COMMS_RX_BASEBAND_BIAS_V;
    if (error < 0) {
        error = -error;
    }

    printf("[rx-bb] GP%d (ADC%d) idle bias = %.3f V  (expect %.2f ±%.2f V)\n",
           COMMS_RX_BASEBAND_GPIO, COMMS_RX_BASEBAND_ADC_CH, (double)volts,
           (double)COMMS_RX_BASEBAND_BIAS_V, (double)COMMS_RX_BASEBAND_TOL_V);

    if (error <= COMMS_RX_BASEBAND_TOL_V) {
        return COMMS_CHECK_PASS;
    }

    /* Near either rail is the interesting case. Note that an ADC pin with
     * nothing attached floats and commonly drifts to a rail, so on a bare
     * Pico or a partially populated board this reads as a fault when
     * really it is just an unconnected input — check continuity from the
     * MCP6022 output to GP27 before chasing the analog stage. */
    printf("[rx-bb]   off nominal — %s\n",
           volts < COMMS_RX_BASEBAND_BIAS_V
               ? "GP27 floating (nothing driving it), MCP6022 unpowered/"
                 "unpopulated, or R10/R11 bias divider open"
               : "GP27 floating (nothing driving it), stage saturated, or "
                 "bias divider shorted to +3V3");
    return COMMS_CHECK_WARN;
}

/* ------------------------------------------------------------------
 * Boot report
 * ----------------------------------------------------------------*/
static void print_banner(void) {
    /* Flash unique ID — lets a bench log say which Pico produced it. */
    char id_str[2 * PICO_UNIQUE_BOARD_ID_SIZE_BYTES + 1];
    pico_get_unique_board_id_string(id_str, sizeof(id_str));

    printf("\n");
    printf("==================================================\n");
    printf(" ember comms board — RP2040 transceiver controller\n");
    printf(" firmware v0.1   build %s %s\n", __DATE__, __TIME__);
    printf(" board id %s\n", id_str);
    printf(" reset: %s\n", watchdog_caused_reboot() ? "WATCHDOG TIMEOUT" : "power-on / external");
    printf("==================================================\n");
}

/* Bounded wait for a console on the far end. Counting elapsed
 * milliseconds rather than comparing tick counts keeps this correct
 * across a tick-counter wrap. */
static void wait_for_console(void) {
#if LIB_PICO_STDIO_USB
    for (int waited = 0; waited < SELFTEST_USB_WAIT_MS; waited += SELFTEST_USB_POLL_MS) {
        if (stdio_usb_connected()) {
            vTaskDelay(pdMS_TO_TICKS(SELFTEST_POST_CONNECT_MS));
            return;
        }
        vTaskDelay(pdMS_TO_TICKS(SELFTEST_USB_POLL_MS));
    }
#else
    vTaskDelay(pdMS_TO_TICKS(SELFTEST_UART_SETTLE_MS));
#endif
}

static uint32_t now_ms(void) {
    return to_ms_since_boot(get_absolute_time());
}

static void selftest_task(void *pvParameters) {
    (void)pvParameters;

    /* Wall-clock stamps, not tick counts: this task runs above the
     * periodic tasks, so anything that blocks here without yielding
     * stalls the whole board, and the elapsed-time line below is what
     * makes that visible instead of mysterious. */
    uint32_t t_start = now_ms();
    wait_for_console();
    uint32_t t_console = now_ms();

    memset(&s_result, 0, sizeof(s_result));
    s_result.watchdog_reboot = watchdog_caused_reboot();

    print_banner();

    safe_outputs();

    /* i2c0 comes up once here and stays up — the Si5351A is the only
     * thing on it, and this task is the only owner until a clock
     * control task exists. Add a bus mutex when that changes. */
    i2c_init(COMMS_I2C_INSTANCE, COMMS_I2C_HZ);
    gpio_set_function(COMMS_I2C_SDA_GPIO, GPIO_FUNC_I2C);
    gpio_set_function(COMMS_I2C_SCL_GPIO, GPIO_FUNC_I2C);
    gpio_pull_up(COMMS_I2C_SDA_GPIO);
    gpio_pull_up(COMMS_I2C_SCL_GPIO);

    uint32_t t_banner = now_ms();
    s_result.i2c_device_count = i2c_bus_scan();
    uint32_t t_scan = now_ms();
    s_result.si5351 = probe_si5351(&s_result.si5351_status);
    uint32_t t_probe = now_ms();
    s_result.rx_baseband = measure_rx_baseband(&s_result.rx_baseband_v);
    uint32_t t_adc = now_ms();

    printf("--------------------------------------------------\n");
    printf("[comms] selftest: si5351a=%s  rx-baseband=%s  i2c-devices=%u\n",
           check_str(s_result.si5351), check_str(s_result.rx_baseband),
           (unsigned)s_result.i2c_device_count);
    printf("[comms] clock outputs left DISABLED — CLK0 drives the XOR "
           "modulator and PA, so TX stays off until commanded\n");

    /* Each figure includes the console I/O done during that stage. If the
     * total dwarfs the sum of the real work, the time went into printf
     * blocking on a USB host that is enumerated but not draining. */
    printf("[comms] timing: console-wait=%lu banner=%lu scan=%lu "
           "si5351=%lu rx-bb=%lu  total=%lu ms\n",
           (unsigned long)(t_console - t_start),
           (unsigned long)(t_banner  - t_console),
           (unsigned long)(t_scan    - t_banner),
           (unsigned long)(t_probe   - t_scan),
           (unsigned long)(t_adc     - t_probe),
           (unsigned long)(now_ms()  - t_start));
    printf("--------------------------------------------------\n");

    s_result.complete = true;
    s_complete = true;

    /* One-shot: the report is published, the stack goes back to the heap. */
    vTaskDelete(NULL);
}

BaseType_t comms_selftest_task_start(UBaseType_t priority) {
    return xTaskCreate(selftest_task, SELFTEST_TASK_NAME,
                       SELFTEST_TASK_STACK_WORDS, NULL, priority, NULL);
}
