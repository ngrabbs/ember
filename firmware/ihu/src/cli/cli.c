#include "cli/cli.h"

#include <stdio.h>
#include <string.h>
#include <stdint.h>
#include <stdbool.h>
#include <stdlib.h>

#include "FreeRTOS.h"
#include "task.h"
#include "pico/stdlib.h"
#include "pico/bootrom.h"
#include "hardware/watchdog.h"
#include "hardware/i2c.h"

#include "config/pinmap.h"
#include "config/i2c0_bus.h"
#include "drivers/ltc4162.h"
#include "drivers/comms_link.h"
#include "tasks/console_task.h"
#include "tasks/comms_monitor_task.h"
#include "tasks/eps_monitor_task.h"

#define CLI_TASK_NAME           "cli"
#define CLI_TASK_STACK_WORDS    768
#define CLI_LINE_MAX            96
#define CLI_MAX_ARGS            8
#define CLI_POLL_PERIOD_MS      20
#define CLI_PROMPT              "ihu> "

/* ------------------------------------------------------------------
 * Command table
 * ----------------------------------------------------------------*/

typedef void (*cli_handler_fn)(int argc, char *argv[]);

typedef struct {
    const char     *name;
    const char     *help;
    cli_handler_fn  fn;
} cli_command_t;

static void cmd_help(int argc, char *argv[]);
static void cmd_stats(int argc, char *argv[]);
static void cmd_eps(int argc, char *argv[]);
static void cmd_comms(int argc, char *argv[]);
static void cmd_kick(int argc, char *argv[]);
static void cmd_ntc_bypass(int argc, char *argv[]);
static void cmd_quiet(int argc, char *argv[]);
static void cmd_loud(int argc, char *argv[]);
static void cmd_reboot(int argc, char *argv[]);

static const cli_command_t cli_commands[] = {
    { "help",       "list available commands",                       cmd_help       },
    { "stats",      "uptime, task count, free heap",                 cmd_stats      },
    { "eps",        "EPS telemetry  (eps raw  for register dump)",   cmd_eps        },
    { "comms",      "comms board status (comms ping | comms raw)",   cmd_comms      },
    { "kick",       "pulse suspend_charger to restart LTC4162",      cmd_kick       },
    { "ntc-bypass", "ntc-bypass on|off — widen jeita to bypass NTC", cmd_ntc_bypass },
    { "quiet",      "suppress periodic heartbeat + telemetry print", cmd_quiet      },
    { "loud",       "re-enable periodic background output",          cmd_loud       },
    { "reboot",     "soft-reset the IHU via the watchdog",           cmd_reboot     },
};
#define CLI_NUM_COMMANDS (sizeof(cli_commands) / sizeof(cli_commands[0]))

/* ------------------------------------------------------------------
 * Command implementations
 * ----------------------------------------------------------------*/

static void cmd_help(int argc, char *argv[]) {
    (void)argc; (void)argv;
    printf("commands:\n");
    for (size_t i = 0; i < CLI_NUM_COMMANDS; ++i) {
        printf("  %-10s %s\n", cli_commands[i].name, cli_commands[i].help);
    }
}

static void cmd_stats(int argc, char *argv[]) {
    (void)argc; (void)argv;
    TickType_t uptime_ticks = xTaskGetTickCount();
    uint32_t uptime_ms = (uint32_t)(uptime_ticks * portTICK_PERIOD_MS);
    printf("uptime    : %lu ms (%lu s)\n",
           (unsigned long)uptime_ms, (unsigned long)(uptime_ms / 1000));
    printf("tasks     : %lu\n", (unsigned long)uxTaskGetNumberOfTasks());
    printf("free heap : %u bytes\n", (unsigned)xPortGetFreeHeapSize());
    printf("min heap  : %u bytes (lowest ever)\n",
           (unsigned)xPortGetMinimumEverFreeHeapSize());
}

/* Raw register dump — uses the public driver if we wanted to add a
 * read-arbitrary helper, but for v0.1 we just re-do the same I2C
 * reads the eps task does and print hex. Useful for sanity-checking
 * the LSB-first byte order on new registers. */
static void dump_ltc4162_register(uint8_t reg, const char *name) {
    uint8_t buf[2];

    /* Pointer write and data read under one lock — the monitor tasks
     * poll this same bus, and a poll landing between the two phases
     * would hand us back one of its registers instead of ours. */
    if (!ihu_i2c0_lock(IHU_I2C0_LOCK_TIMEOUT_MS)) {
        printf("  0x%02X %-18s i2c0 busy (lock timeout)\n", reg, name);
        return;
    }
    int w = i2c_write_blocking(IHU_I2C_EPS_INSTANCE, IHU_EPS_LTC4162_ADDR,
                               &reg, 1, true);
    int r = (w == 1)
        ? i2c_read_blocking(IHU_I2C_EPS_INSTANCE, IHU_EPS_LTC4162_ADDR,
                            buf, 2, false)
        : 0;
    ihu_i2c0_unlock();

    if (w != 1) {
        printf("  0x%02X %-18s I2C write failed\n", reg, name);
        return;
    }
    if (r != 2) {
        printf("  0x%02X %-18s I2C read failed\n", reg, name);
        return;
    }
    uint16_t v = ((uint16_t)buf[1] << 8) | (uint16_t)buf[0];
    printf("  0x%02X %-18s 0x%04X (%5u)\n", reg, name, v, v);
}

static void cmd_eps(int argc, char *argv[]) {
    bool raw = (argc >= 2) && (strcmp(argv[1], "raw") == 0);

    if (raw) {
        printf("LTC4162 raw registers (addr=0x%02X):\n", IHU_EPS_LTC4162_ADDR);
        dump_ltc4162_register(0x14, "config_bits");
        dump_ltc4162_register(0x1F, "jeita_t1");
        dump_ltc4162_register(0x24, "jeita_t6");
        dump_ltc4162_register(0x29, "chgr_config_bits");
        dump_ltc4162_register(0x34, "charger_state");
        dump_ltc4162_register(0x35, "charge_status");
        dump_ltc4162_register(0x39, "system_status");
        dump_ltc4162_register(0x3A, "vbat");
        dump_ltc4162_register(0x3B, "vin");
        dump_ltc4162_register(0x3C, "vout");
        dump_ltc4162_register(0x3D, "ibat");
        dump_ltc4162_register(0x3E, "iin");
        dump_ltc4162_register(0x3F, "die_temp");
        dump_ltc4162_register(0x40, "thermistor_v");
        dump_ltc4162_register(0x42, "jeita_region");
        printf("  (thermistor_v > 21684 = open_thermistor -> ntc_pause)\n");
        printf("  (defaults: jeita_t1=16117, jeita_t6=4970)\n");
        printf("  (ntc-bypass on: jeita_t1=0x7FFF=32767, jeita_t6=0x0001=1)\n");
        return;
    }

    ltc4162_telemetry_t t;
    if (!ihu_eps_get_latest_telemetry(&t)) {
        printf("no telemetry snapshot yet — wait for the first eps-mon poll\n");
        return;
    }
    printf("state       : %s\n", ltc4162_state_string(t.charger_state));
    printf("charge      : %s\n", ltc4162_charge_status_string(t.charge_status));
    printf("system_stat : 0x%04X\n", t.system_status);
    printf("V_IN        : %6.3f V\n", t.v_in);
    printf("V_OUT       : %6.3f V\n", t.v_out);
    printf("V_BAT       : %6.3f V\n", t.v_bat);
    printf("I_IN        : %+7.1f mA\n", t.i_in_ma);
    printf("I_BAT       : %+7.1f mA (positive = charging into battery)\n",
           t.i_bat_ma);
}


/* ------------------------------------------------------------------
 * comms — the other end of the housekeeping bus
 * ----------------------------------------------------------------*/

/* `comms raw` — dump the comms board's register file as hex.
 *
 * Reads the whole map in one burst so what you see is one coherent
 * moment, rather than 32 separately-timed bytes. Deliberately NOT
 * decoded: this is the view you want when the decoded output looks
 * wrong and you need to know whether the problem is the wire or the
 * parser. */
static void cmd_comms_raw(void) {
    uint8_t buf[COMMS_HK_REG_COUNT];
    uint8_t reg = 0x00;

    if (!ihu_i2c0_lock(IHU_I2C0_LOCK_TIMEOUT_MS)) {
        printf("i2c0 busy (lock timeout)\n");
        return;
    }
    int w = i2c_write_blocking(IHU_I2C_EPS_INSTANCE, COMMS_HK_I2C_ADDR,
                               &reg, 1, true);
    int r = (w == 1)
        ? i2c_read_blocking(IHU_I2C_EPS_INSTANCE, COMMS_HK_I2C_ADDR,
                            buf, sizeof(buf), false)
        : 0;
    ihu_i2c0_unlock();

    if (w != 1) {
        printf("no ACK from comms board at 0x%02X\n", COMMS_HK_I2C_ADDR);
        return;
    }
    if (r != (int)sizeof(buf)) {
        printf("short read from 0x%02X (%d of %u bytes)\n",
               COMMS_HK_I2C_ADDR, r, (unsigned)sizeof(buf));
        return;
    }

    printf("comms register file (addr=0x%02X, %u bytes):\n",
           COMMS_HK_I2C_ADDR, (unsigned)sizeof(buf));
    for (size_t i = 0; i < sizeof(buf); i += 8) {
        printf("  0x%02X:", (unsigned)i);
        for (size_t j = 0; j < 8; ++j) {
            printf(" %02X", buf[i + j]);
        }
        printf("\n");
    }
    printf("  who_am_i=0x%02X (expect 0x%02X)  proto=v%u (this IHU speaks v%u)\n",
           buf[COMMS_HK_REG_WHO_AM_I], COMMS_HK_WHO_AM_I_VALUE,
           (unsigned)buf[COMMS_HK_REG_PROTO_VER],
           (unsigned)COMMS_HK_PROTO_VERSION);
}

/* `comms ping` — one round trip, on demand.
 *
 * Uses the tick count as the token so two pings in a row cannot
 * accidentally match each other: a stale value left in the scratch
 * register from the previous ping would otherwise read as a pass. */
static void cmd_comms_ping(void) {
    uint32_t token  = 0xA5000000u ^ (uint32_t)xTaskGetTickCount();
    uint32_t echoed = 0;
    uint32_t rtt_us = 0;

    if (comms_link_ping(IHU_I2C_EPS_INSTANCE, COMMS_HK_I2C_ADDR,
                        token, &echoed, &rtt_us)) {
        printf("pong from 0x%02X — token 0x%08lX echoed, %lu us round trip\n",
               COMMS_HK_I2C_ADDR, (unsigned long)token, (unsigned long)rtt_us);
        return;
    }

    if (!comms_link_present(IHU_I2C_EPS_INSTANCE, COMMS_HK_I2C_ADDR)) {
        printf("no response at 0x%02X — comms board unpowered, not wired to\n"
               "SDA_HK/SCL_HK, or its hk-slave task did not start\n",
               COMMS_HK_I2C_ADDR);
    } else {
        printf("device ACKs at 0x%02X but the echo came back wrong:\n"
               "  sent 0x%08lX, got 0x%08lX\n"
               "that is a wrong device at this address, or a bus integrity\n"
               "problem (pull-ups, wire length, contention)\n",
               COMMS_HK_I2C_ADDR,
               (unsigned long)token, (unsigned long)echoed);
    }
}

static void cmd_comms(int argc, char *argv[]) {
    if (argc >= 2 && strcmp(argv[1], "ping") == 0) {
        cmd_comms_ping();
        return;
    }
    if (argc >= 2 && strcmp(argv[1], "raw") == 0) {
        cmd_comms_raw();
        return;
    }
    if (argc >= 2) {
        printf("usage: comms [ping|raw]\n");
        return;
    }

    comms_link_health_t h;
    ihu_comms_get_health(&h);

    comms_link_status_t s;
    if (!ihu_comms_get_latest_status(&s)) {
        printf("link        : DOWN — comms board has never answered\n");
        printf("polls       : %lu (all failed)\n", (unsigned long)h.polls);
        printf("  try 'comms ping' for a one-shot probe with diagnostics\n");
        return;
    }

    /* Snapshot age matters more than the values when the link is down:
     * every field below is the last known good one, and without the age
     * a dead board looks like a healthy board frozen in time. */
    uint32_t now_ms = (uint32_t)(xTaskGetTickCount() * portTICK_PERIOD_MS);
    printf("link        : %s (last good %lu s ago, %lu us rtt)\n",
           h.link_up ? "UP" : "DOWN",
           (unsigned long)((now_ms - h.last_ok_ms) / 1000),
           (unsigned long)h.last_rtt_us);
    if (!h.link_up) {
        printf("              %lu consecutive failed polls — values below are stale\n",
               (unsigned long)h.failures);
    }
    printf("fw / proto  : v%u.%u / v%u\n",
           (unsigned)(s.fw_ver >> 4), (unsigned)(s.fw_ver & 0xF),
           (unsigned)s.proto_ver);
    printf("uptime      : %lu s  (tasks=%u, free heap=%lu B)\n",
           (unsigned long)s.uptime_s, (unsigned)s.tasks,
           (unsigned long)s.free_heap);
    printf("self-test   : %s\n",
           s.selftest_done ? "complete" : "NOT COMPLETE");
    printf("si5351a     : %s  (raw status 0x%02X, PLLs %s)\n",
           comms_link_check_string(s.check_si5351), s.si5351_raw,
           s.pll_locked ? "locked" : "UNLOCKED");
    printf("rx baseband : %s  (%u mV, expect ~1650)\n",
           comms_link_check_string(s.check_rx_bb), (unsigned)s.rx_bb_mv);
    printf("i2c devices : %u on the comms board's own bus\n",
           (unsigned)s.i2c_devs);
    printf("tx active   : %s\n",
           s.tx_active ? "YES — T/R switch in transmit" : "no (receive)");
    printf("xacts served: %u  (polls from this IHU: %lu)\n",
           (unsigned)s.xact_count, (unsigned long)h.polls);
    if (s.wdt_reboot) {
        printf("note        : comms board last reset by WATCHDOG TIMEOUT\n");
    }
    if (s.fault) {
        printf("ALERT       : comms board reports a self-test FAIL\n");
    }
}

static void cmd_quiet(int argc, char *argv[]) {
    (void)argc; (void)argv;
    ihu_console_set_quiet(true);
    ihu_eps_set_quiet(true);
    ihu_comms_set_quiet(true);
    printf("background output suppressed (use 'loud' to re-enable)\n");
    printf("  (telemetry still polling — use 'eps' for on-demand readout)\n");
}

static void cmd_loud(int argc, char *argv[]) {
    (void)argc; (void)argv;
    ihu_console_set_quiet(false);
    ihu_eps_set_quiet(false);
    ihu_comms_set_quiet(false);
    printf("background output re-enabled\n");
}

static void cmd_kick(int argc, char *argv[]) {
    (void)argc; (void)argv;
    if (ltc4162_kick(IHU_I2C_EPS_INSTANCE, IHU_EPS_LTC4162_ADDR)) {
        printf("LTC4162 kicked — suspend_charger pulsed, state machine re-evaluating\n");
    } else {
        printf("LTC4162 kick I2C write failed\n");
    }
}

static void cmd_ntc_bypass(int argc, char *argv[]) {
    if (argc < 2 || (strcmp(argv[1], "on") != 0 && strcmp(argv[1], "off") != 0)) {
        printf("usage: ntc-bypass on|off\n");
        printf("  on  : widen jeita_t1/t6 to int16 range — NTC reading\n");
        printf("        always satisfies the ntc-pause exit condition\n");
        printf("  off : restore datasheet defaults (jeita_t1=16117, jeita_t6=4970)\n");
        printf("note: thermistor_voltage must still be < 21684 to pass the\n");
        printf("      hardware open_thermistor check. A resistor on NTC->GND\n");
        printf("      is enough; matched RNTCBIAS not required for bypass.\n");
        return;
    }
    bool enable = (strcmp(argv[1], "on") == 0);
    if (ltc4162_set_ntc_bypass(IHU_I2C_EPS_INSTANCE,
                               IHU_EPS_LTC4162_ADDR, enable)) {
        printf("NTC bypass %s — kicking charger to re-evaluate\n",
               enable ? "ENABLED (jeita window widened)"
                      : "DISABLED (defaults restored)");
        ltc4162_kick(IHU_I2C_EPS_INSTANCE, IHU_EPS_LTC4162_ADDR);
    } else {
        printf("ntc-bypass write failed\n");
    }
}

static void cmd_reboot(int argc, char *argv[]) {
    (void)argc; (void)argv;
    printf("rebooting via watchdog in 100 ms...\n");
    /* Drain UART TX so the message actually lands. */
    vTaskDelay(pdMS_TO_TICKS(50));
    watchdog_reboot(0, 0, 100);
    /* This loop is only reached if the reboot didn't take. */
    for (;;) { tight_loop_contents(); }
}

/* ------------------------------------------------------------------
 * Line parsing and dispatch
 * ----------------------------------------------------------------*/

static void dispatch(char *line) {
    /* Tokenize on whitespace. Modifies line in place. */
    char *argv[CLI_MAX_ARGS];
    int   argc = 0;
    char *saveptr = NULL;
    char *tok = strtok_r(line, " \t", &saveptr);
    while (tok && argc < CLI_MAX_ARGS) {
        argv[argc++] = tok;
        tok = strtok_r(NULL, " \t", &saveptr);
    }
    if (argc == 0) {
        return;
    }
    for (size_t i = 0; i < CLI_NUM_COMMANDS; ++i) {
        if (strcmp(argv[0], cli_commands[i].name) == 0) {
            cli_commands[i].fn(argc, argv);
            return;
        }
    }
    printf("unknown command: %s  (try 'help')\n", argv[0]);
}

/* ------------------------------------------------------------------
 * Task body — non-blocking UART poll, line buffer, echo, dispatch
 * ----------------------------------------------------------------*/

static void cli_task(void *pvParameters) {
    (void)pvParameters;

    char    line[CLI_LINE_MAX];
    size_t  len = 0;

    /* Wait until the console task has printed its banner and the EPS
     * task has done its bus scan, so the first prompt is below them. */
    vTaskDelay(pdMS_TO_TICKS(3500));
    printf("\nCLI ready — type 'help'\n%s", CLI_PROMPT);

    for (;;) {
        int c = getchar_timeout_us(0);
        if (c == PICO_ERROR_TIMEOUT) {
            vTaskDelay(pdMS_TO_TICKS(CLI_POLL_PERIOD_MS));
            continue;
        }

        if (c == '\r' || c == '\n') {
            putchar('\n');
            line[len] = '\0';
            if (len > 0) {
                dispatch(line);
            }
            len = 0;
            printf("%s", CLI_PROMPT);
            fflush(stdout);
        } else if (c == '\b' || c == 0x7F) {     /* backspace / DEL */
            if (len > 0) {
                --len;
                /* Erase the character on the user's terminal. */
                printf("\b \b");
                fflush(stdout);
            }
        } else if (c == 0x03) {                  /* Ctrl-C: cancel line */
            len = 0;
            printf("^C\n%s", CLI_PROMPT);
            fflush(stdout);
        } else if (c >= 0x20 && c < 0x7F) {      /* printable */
            if (len < CLI_LINE_MAX - 1) {
                line[len++] = (char)c;
                putchar((char)c);
                fflush(stdout);
            }
            /* Silently drop characters past the buffer cap. */
        }
        /* All other control chars ignored. */
    }
}

BaseType_t ihu_cli_task_start(UBaseType_t priority) {
    return xTaskCreate(cli_task, CLI_TASK_NAME,
                       CLI_TASK_STACK_WORDS, NULL, priority, NULL);
}
