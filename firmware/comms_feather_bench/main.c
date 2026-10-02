#include <inttypes.h>
#include <stdio.h>
#include <string.h>
#include "pico/stdlib.h"
#include "pico/unique_id.h"
#include "hardware/uart.h"

static uint32_t tx_bytes, rx_bytes, probes;

static void status(void) {
    char id[2 * PICO_UNIQUE_BOARD_ID_SIZE_BYTES + 1];
    pico_get_unique_board_id_string(id, sizeof(id));
    printf("STATUS role=COMMS_MCU board=CAN_FEATHER fw=uart-bench-v1 id=%s "
           "uart=0 tx=0 rx=1 baud=115200 tx_bytes=%" PRIu32 " rx_bytes=%" PRIu32
           " probes=%" PRIu32 " uptime_ms=%" PRIu32 "\n",
           id, tx_bytes, rx_bytes, probes, to_ms_since_boot(get_absolute_time()));
}

static void command(const char *line) {
    if (!strcmp(line, "status")) {
        status();
    } else if (!strcmp(line, "probe")) {
        char frame[80];
        int n = snprintf(frame, sizeof(frame), "EMBER_UART_PING v1 %" PRIu32 "\n", ++probes);
        uart_write_blocking(uart0, (const uint8_t *)frame, (size_t)n);
        tx_bytes += (uint32_t)n;
        printf("PROBE submitted=%" PRIu32 " bytes=%d result=UART_WRITTEN_NOT_PEER_ACK\n", probes, n);
    } else if (!strcmp(line, "help")) {
        puts("COMMANDS status | probe | help; probe is diagnostic text, not a modem/RF command");
    } else if (*line) {
        puts("ERROR unknown command");
    }
}

int main(void) {
    stdio_init_all();
    uart_init(uart0, 115200);
    gpio_set_function(0, GPIO_FUNC_UART);
    gpio_set_function(1, GPIO_FUNC_UART);
    gpio_pull_up(1);
    uart_set_hw_flow(uart0, false, false);
    uart_set_format(uart0, 8, 1, UART_PARITY_NONE);
    uart_set_fifo_enabled(uart0, true);
    gpio_init(13);
    gpio_set_dir(13, GPIO_OUT);
    char line[32];
    size_t used = 0;
    bool discard = false;
    uint64_t next_blink = 0;
    bool led = false;
    puts("READY EMBER COMMS Feather UART bench; USB logs only; type status or help");
    while (true) {
        // Only USB stdin controls probe transmission; no automatic UART writes.
        for (int i = 0; i < 32; ++i) {
            int ch = getchar_timeout_us(0);
            if (ch == PICO_ERROR_TIMEOUT) break;
            if (ch == '\r' || ch == '\n') {
                if (!discard) { line[used] = 0; command(line); }
                else puts("ERROR command too long");
                used = 0;
                discard = false;
            } else if (!discard) {
                if (used + 1 < sizeof(line)) line[used++] = (char)ch;
                else discard = true;
            }
        }
        uint8_t rx[32];
        size_t count = 0;
        while (count < sizeof(rx) && uart_is_readable(uart0)) rx[count++] = uart_getc(uart0);
        if (count) {
            rx_bytes += (uint32_t)count;
            printf("UART_RX bytes=%zu hex=", count);
            for (size_t i = 0; i < count; ++i) printf("%02x", rx[i]);
            puts("");
        }
        uint64_t now = time_us_64() / 1000;
        if (now >= next_blink) {
            led = !led;
            gpio_put(13, led);
            next_blink = now + 500;
        }
        sleep_ms(1);
    }
}
