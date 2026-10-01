#include <stdio.h>
#include "pico/stdlib.h"
#include "pico/stdio_usb.h"
#include "pico/stdio/driver.h"
#include "pico/rand.h"
#include "hardware/uart.h"
#include "protocol.h"
#include "framing.h"

static ember_state state;
static bool send_packet(const uint8_t *p, size_t n, void *unused) {
    (void)unused;
    if (!stdio_usb_connected()) return false;
    uint8_t frame[W_MAX_PACKET+2];
    size_t size=cobs_encode(p,n,frame,sizeof(frame));
    if (!size) return false;
    stdio_usb.out_chars((const char *)frame,(int)size);
    return true; /* handed to bounded SDK USB writer, not a delivery ACK */
}
int main(void) {
    uart_init(uart0,115200); gpio_set_function(0,GPIO_FUNC_UART); gpio_set_function(1,GPIO_FUNC_UART);
    stdio_usb_init(); ember_init(&state,get_rand_32());
    char banner[96]; snprintf(banner,sizeof(banner),"EMBER USB bench-v1 GROUND_TEST boot=%lu\r\n",(unsigned long)state.boot);
    uart_puts(uart0,banner);
    uint8_t encoded[W_MAX_PACKET+1], decoded[W_MAX_PACKET];
    size_t used=0; bool discard=false, was_connected=false;
    uint64_t frame_start=0, next_periodic=0;
    while (true) {
        uint64_t now=time_us_64();
        bool connected=stdio_usb_connected();
        if (connected!=was_connected) { used=0; discard=false; next_periodic=now; was_connected=connected; }
        if (used && now-frame_start>500000) { used=0; discard=true; state.dropped++; }
        char block[64]; int received=stdio_usb.in_chars(block,sizeof(block));
        for (int i=0;i<received;i++) {
            uint8_t byte=(uint8_t)block[i];
            if (!byte) {
                if (used && !discard) {
                    size_t n=cobs_decode(encoded,used,decoded,sizeof(decoded));
                    uint32_t old_period=state.period;
                    if (n) ember_command(&state,decoded,n,(uint32_t)(now/1000),send_packet,NULL);
                    else state.dropped++;
                    if (state.period!=old_period) next_periodic=now+(uint64_t)state.period*1000;
                }
                used=0; discard=false;
            } else if (!discard) {
                if (!used) frame_start=now;
                if (used==sizeof(encoded)) { used=0; discard=true; state.dropped++; }
                else encoded[used++]=byte;
            }
        }
        if (connected && now>=next_periodic) {
            ember_periodic(&state,(uint32_t)(now/1000),send_packet,NULL);
            next_periodic=now+(uint64_t)state.period*1000;
        }
        sleep_us(500);
    }
}
