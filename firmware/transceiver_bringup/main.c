/* Y24 ordered-board bring-up: internal loopback and bounded CAN A receive windows; RF stays muted. */
#include <stdio.h>
#include "pico/stdlib.h"
#include "hardware/adc.h"
#include "hardware/i2c.h"
#include "hardware/spi.h"
#include "pico/rand.h"
#include "hello.h"
static uint32_t responder_boot;

static void output(unsigned pin, bool level) {
    gpio_init(pin);
    gpio_put(pin, level); /* Set latch before enabling output. */
    gpio_set_dir(pin, GPIO_OUT);
}

/* A successful readback confirms register state, not measured RF silence. */
static bool disable_clocks(void) {
    uint8_t command[] = {3, 0xff};
    uint8_t reg = 3, value = 0;
    if (i2c_write_timeout_us(i2c0, 0x60, command, 2, false, 2000) != 2)
        return false;
    if (i2c_write_timeout_us(i2c0, 0x60, &reg, 1, true, 2000) != 1)
        return false;
    if (i2c_read_timeout_us(i2c0, 0x60, &value, 1, false, 2000) != 1)
        return false;
    return value == 0xff;
}

#include "clock_test.h"
#include "bpsk_packet.h"
#include "bpsk_emit.h"
#include "rf_bridge.h"
static void bpsk_test(unsigned drive) {
    static uint32_t sequence;
    size_t size=bpsk_frame(packet_frame,sizeof(packet_frame),responder_boot,
                           sequence++,(uint32_t)(time_us_64()/1000));
    if(!size)return;
    packet_frame_size=size;
    printf("[bpsk] prepared native COMMS heartbeat packet_hex=");
    for(unsigned i=43;i<81;i++)printf("%02x",packet_frame[i]);
    printf("\n");
    printf("[bpsk] drive_mA=%u\n",2*(drive+1));
    bool ok=clock_window_drive(true,false,bpsk_emit,drive);
    printf("[bpsk] complete=%u frame_bytes=%u TX=0\n",ok,(unsigned)size);
}

/* Data-input measurement only: never enables a clock or RF path. */
static void data_input_test(void) {
    gpio_put(10, false);
    gpio_put(11, false);
    gpio_put(16, false);
    if (!disable_clocks()) {
        printf("[data_test] refused: clock disable not verified\n");
        return;
    }
    printf("[data_test] 10Hz data pattern, max5s, TX/RX=0 clocks=off\n");
    uint64_t start = time_us_64();
    while (time_us_64() - start < 5000000) {
        if (getchar_timeout_us(0) >= 0) break;
        gpio_put(16, ((time_us_64() - start) / 50000) & 1u);
        sleep_ms(1);
    }
    gpio_put(16, false);
    bool disabled = disable_clocks();
    printf("[data_test] end data=0 TX/RX=0 clocks_disabled=%u\n", disabled);
}

/* SPI mode 0, with explicit chip-select setup/hold delays. */
static uint8_t can_read(unsigned cs, uint8_t reg) {
    uint8_t tx[] = {0x03, reg, 0}, rx[3] = {0};
    gpio_put(cs, false);
    sleep_us(2);
    spi_write_read_blocking(spi0, tx, rx, 3);
    sleep_us(2);
    gpio_put(cs, true);
    return rx[2];
}

static bool configuration_mode(uint8_t stat, uint8_t ctrl) {
    return (stat & 0xe0) == 0x80 && (ctrl & 0xe0) == 0x80;
}

static void can_write(unsigned cs, uint8_t reg, uint8_t value) {
    uint8_t tx[] = {0x02, reg, value}, rx[3];
    gpio_put(cs, false);
    sleep_us(2);
    spi_write_read_blocking(spi0, tx, rx, 3);
    sleep_us(2);
    gpio_put(cs, true);
}

static bool can_mode(unsigned cs, uint8_t mode) {
    /* Mode selection used by bounded tests. One-shot on, CAN CLKOUT off. */
    if (mode != 0x80 && mode != 0x40 && mode != 0x60 && mode != 0) return false;
    can_write(cs, 0x0f, mode | 0x08);
    for (unsigned n = 0; n < 100; ++n) {
        if ((can_read(cs, 0x0e) & 0xe0) == mode &&
            (can_read(cs, 0x0f) & 0xe0) == mode) return true;
        sleep_ms(1);
    }
    return false;
}

static bool independent_registers(void) {
    if (!configuration_mode(can_read(14, 0x0e), can_read(14, 0x0f)) ||
        !configuration_mode(can_read(15, 0x0e), can_read(15, 0x0f))) return false;
    /* TXB0D0 is inactive data RAM; no TXREQ is set by this test. */
    uint8_t a = can_read(14, 0x36), b = can_read(15, 0x36);
    can_write(14, 0x36, 0x55); can_write(15, 0x36, 0xaa);
    bool ok = can_read(14, 0x36) == 0x55 && can_read(15, 0x36) == 0xaa;
    can_write(14, 0x36, 0xaa); can_write(15, 0x36, 0x55);
    ok &= can_read(14, 0x36) == 0xaa && can_read(15, 0x36) == 0x55;
    can_write(14, 0x36, a); can_write(15, 0x36, b);
    return ok && can_read(14, 0x36) == a && can_read(15, 0x36) == b;
}

/* Return a stage code: 0 pass, 1 config, 2 loopback mode, 3 timeout,
 * 4 frame mismatch, 5 return-to-config. Caller holds reset on any failure. */
static uint8_t loop_received[2][13];
static unsigned loopback(unsigned cs, uint8_t tag) {
    if (!can_mode(cs, 0x80)) return 1;
    can_write(cs, 0x2a, 0); can_write(cs, 0x29, 0xf0); can_write(cs, 0x28, 0x86);
    can_write(cs, 0x2b, 0); /* Interrupts disabled; poll flags. */
    can_write(cs, 0x2c, 0);
    can_write(cs, 0x60, 0x60); can_write(cs, 0x70, 0x60); /* Accept all. */
    can_write(cs, 0x30, 0);
    /* Standard ID 0x321, DLC 8, distinguishable payload for each controller. */
    uint8_t frame[] = {0x64, 0x20, 0, 0, 8, tag, 0, 0xff, 0x55, 0xaa, 0x12, 0x34, 0x78};
    for (unsigned i = 0; i < sizeof(frame); ++i) can_write(cs, 0x31+i, frame[i]);
    if (!can_mode(cs, 0x40)) return 2;
    /* TXREQ only after confirmed internal loopback; STBY stays asserted. */
    can_write(cs, 0x30, 0x08);
    unsigned n;
    for (n = 0; n < 100; ++n) {
        if ((can_read(cs, 0x2c) & 0x05) == 0x05 && !(can_read(cs, 0x30) & 8)) break;
        sleep_ms(1);
    }
    if (n == 100) return 3;
    uint8_t *received = loop_received[cs == 14 ? 0 : 1];
    for (unsigned i = 0; i < sizeof(frame); ++i) {
        received[i] = can_read(cs, 0x61+i);
    }
    /* Standard data frame: EID bytes and SIDL EID bits are not meaningful. */
    bool match = received[0] == frame[0] && (received[1] & 0xf8) == frame[1]
                 && (received[4] & 0x4f) == 8;
    for (unsigned i = 5; i < sizeof(frame); ++i) match &= received[i] == frame[i];
    if (!match) return 4;
    can_write(cs, 0x2c, 0);
    if (!can_mode(cs, 0x80)) return 5;
    return 0;
}

static void can_modify(uint8_t reg, uint8_t mask, uint8_t value) {
    uint8_t tx[] = {5, reg, mask, value}, rx[4];
    gpio_put(14, false); sleep_us(2);
    spi_write_read_blocking(spi0, tx, rx, 4);
    sleep_us(2); gpio_put(14, true);
}

static bool hello_send(const uint8_t *wire, size_t size, uint32_t request,
                       uint64_t deadline) {
    for (unsigned index = 0; index < CF_FRAMES; ++index) {
        cf_frame f;
        if (!cf_fragment(wire, size, CF_COMMS_ID, (uint16_t)request, index, &f)) return false;
        if (time_us_64() >= deadline || (can_read(14, 0x0e)&0xe0) != 0) return false;
        can_write(14, 0x30, 0); can_modify(0x2c, 4, 0);
        uint8_t tx[] = {(uint8_t)(f.id>>3), (uint8_t)(f.id<<5), 0, 0, f.size};
        for (unsigned i=0;i<5;++i) can_write(14, 0x31+i, tx[i]);
        for (unsigned i=0;i<f.size;++i) can_write(14, 0x36+i, f.data[i]);
        can_write(14, 0x30, 8); /* One-shot TX; no indefinite retries. */
        bool done = false;
        for (unsigned poll=0;poll<50 && time_us_64()<deadline;++poll) {
            uint8_t ctrl = can_read(14, 0x30);
            if (!(ctrl&8)) {done = !(ctrl&0x70) && (can_read(14, 0x2c)&4); break;}
            sleep_ms(1);
        }
        if (!done) {can_write(14, 0x30, 0); return false;}
        if ((index+1)*CF_CHUNK >= size) return true;
        sleep_ms(2);
    }
    return false;
}

#include "rf_service.h"

/* Console l=listen-only, n=receive with ACK; both bounded to ten seconds. */
static bool listen_a(bool acknowledge, bool reply_hello, bool forward_rf) {
    /* Single foreground owner; keep large CAN work buffers off the Pico stack. */
    static cf_reader fragments;memset(&fragments,0,sizeof(fragments));
    static uint8_t bridge_packet[BPSK_NATIVE_MAX];size_t bridge_size=0;uint32_t bridge_request=0;bool bridge_ready=false;
    bool reply_attempted = false, reply_ok = false;
    uint32_t reply_request = 0;
    uint8_t mode = acknowledge ? 0 : 0x60;
    if (!configuration_mode(can_read(14, 0x0e), can_read(14, 0x0f))) return false;
    if (can_read(14, 0x2a) != 0 || can_read(14, 0x29) != 0xf0 ||
        can_read(14, 0x28) != 0x86) return false;
    can_write(14, 0x2c, 0); can_write(14, 0x2d, 0);
    can_write(14, 0x60, 0x64); /* RX0 rollover into RX1. */
    can_write(14, 0x30, 0); can_write(14, 0x40, 0); can_write(14, 0x50, 0);
    if (!can_mode(14, mode)) return false;
    gpio_put(2, false); /* All TX buffers inactive before connecting to bus. */
    if(forward_rf)printf("[bridge] ARMED one IHU telemetry packet, max10s CAN wait, one RF burst\n");
    printf("[listen_A] START 500000bit/s 10s ACK=%u HELLO_reply=%u\n", acknowledge, reply_hello);
    uint64_t end = time_us_64() + 10000000;
    unsigned frames = 0;
    static uint8_t captured[CF_FRAMES][13];
    bool mode_ok = true;
    while (time_us_64() < end) {
        if(forward_rf && getchar_timeout_us(0)>=0)break;
        if ((can_read(14, 0x0e) & 0xe0) != mode) {mode_ok = false; break;}
        uint8_t flags = can_read(14, 0x2c);
        for (unsigned buffer = 0; buffer < 2; ++buffer) {
            if (!(flags & (1u << buffer))) continue;
            uint8_t base = buffer ? 0x71 : 0x61;
            uint8_t read_tx[15] = {3, base}, read_rx[15];
            gpio_put(14, false); sleep_us(2);
            spi_write_read_blocking(spi0, read_tx, read_rx, 15);
            sleep_us(2); gpio_put(14, true);
            if (frames < CF_FRAMES)
                for (unsigned i = 0; i < 13; ++i) captured[frames][i] = read_rx[i+2];
            can_modify(0x2c, (uint8_t)(1u<<buffer), 0);
            uint8_t *data = read_rx+2;
            if (((reply_hello && !reply_attempted) || forward_rf) && !(data[1]&0x18) &&
                !(data[4]&0x40) && (data[4]&15)<=8) {
                cf_frame f = {.id = (uint16_t)((data[0]<<3)|(data[1]>>5)), .size=data[4]&15};
                memcpy(f.data, data+5, f.size);
                if (cf_feed(&fragments, &f, CF_IHU_ID, (uint32_t)(time_us_64()/1000))) {
                    static uint8_t wire[UL_WIRE_MAX];
                    size_t size = reply_hello ? hello_response(&fragments, responder_boot, wire, &reply_request) : 0;
                    if(forward_rf)bridge_ready=bridge_telemetry(&fragments,bridge_packet,&bridge_size,&bridge_request);
                    if (size) {
                        reply_attempted = true;
                        reply_ok = hello_send(wire, size, reply_request, end);
                        if (!reply_ok) {mode_ok=false; break;}
                    }
                }
            }
            ++frames;
            if(bridge_ready)break;

        }
        if (!mode_ok || bridge_ready) break;
        sleep_ms(1);
    }
    gpio_put(2, true); /* Stop physical reception before changing modes. */
    uint8_t errors = can_read(14, 0x2d);
    bool restored = can_mode(14, 0x80);
    for (unsigned f = 0; f < frames && f < CF_FRAMES; ++f) {
        printf("[listen_A] raw");
        for (unsigned i = 0; i < 13; ++i) printf(" %02X", captured[f][i]);
        printf("\n");
    }
    printf("[listen_A] END frames=%u EFLG=%02X mode_ok=%u restored=%u\n",
           frames, errors, mode_ok, restored);
    if (reply_hello) printf("[hello_A] boot=%lu request=%lu attempted=%u tx_complete=%u\n",
                            (unsigned long)responder_boot, (unsigned long)reply_request,
                            reply_attempted, reply_ok);
    if(forward_rf) {
        if(!mode_ok || !restored || errors || !bridge_ready) {
            printf("[bridge] NO_RF accepted=%u errors=%02X\n",bridge_ready,errors);
            return mode_ok && restored;
        }
        printf("[bridge] CAN request=%lu packet_hex=",(unsigned long)bridge_request);
        for(unsigned i=0;i<bridge_size;i++)printf("%02x",bridge_packet[i]);
        printf("\n");
        packet_frame_size=bridge_frame(packet_frame,bridge_packet,bridge_size,bridge_request);
        if(!packet_frame_size)return false;
        bool sent=clock_window_drive(true,false,bpsk_emit,1);
        printf("[bridge] RF_complete=%u request=%lu TX=0 no_ground_ack=1\n",sent,(unsigned long)bridge_request);
        return sent;
    }
    return mode_ok && restored;
}

/* Readiness means responsive CAN configuration registers, not a rail measurement.
 * Twenty attempts give roughly five seconds for power/oscillator settling.
 * No bus participation is enabled here. Exhaustion leaves both resets low. */
static bool wait_can_ready(unsigned *attempts, uint8_t last[4]) {
    gpio_put(2, true); gpio_put(3, true);
    gpio_put(14, true); gpio_put(15, true);
    for (*attempts = 1; *attempts <= 20; ++*attempts) {
        gpio_put(8, false); gpio_put(9, false);
        sleep_ms(10);
        (void)disable_clocks();
        gpio_put(8, true); gpio_put(9, true);
        sleep_ms(20);
        bool ready = true;
        for (unsigned sample = 0; sample < 2; ++sample) {
            last[0] = can_read(14, 0x0e); last[1] = can_read(14, 0x0f);
            last[2] = can_read(15, 0x0e); last[3] = can_read(15, 0x0f);
            ready &= configuration_mode(last[0], last[1]) && configuration_mode(last[2], last[3]);
            if (sample == 0) sleep_ms(20);
        }
        if (ready) return true;
        gpio_put(8, false); gpio_put(9, false);
        if (*attempts < 20) sleep_ms(200);
    }
    *attempts = 20;
    return false;
}

int main(void) {
    output(10, false); /* TX_ACTIVE: hardware mute asserted. */
    output(11, false); /* RX_ACTIVE */
    output(16, false); /* BPSK_DATA */
    output(8, false);  /* CAN_A_RESETn */
    output(9, false);  /* CAN_B_RESETn */
    output(2, true);   /* CAN_A_STBY */
    output(3, true);   /* CAN_B_STBY */
    output(14, true);  /* CAN_A_CSn */
    output(15, true);  /* CAN_B_CSn */
    output(6, false);  /* CAN_SPI_SCK */
    output(7, false);  /* CAN_SPI_MOSI */
    output(12, true);  /* 3V3_IND */
    gpio_init(4);      /* CAN_SPI_MISO remains input. */
    gpio_init(18);     /* CAN_A_INTn */
    gpio_init(19);     /* CAN_B_INTn */
    i2c_init(i2c0, 100000);
    gpio_set_function(20, GPIO_FUNC_I2C);
    gpio_set_function(21, GPIO_FUNC_I2C);
    /* Use board pull-ups; do not feed an unpowered board via internal pull-ups. */
    adc_init();
    adc_gpio_init(27);
    adc_select_input(1);
    stdio_init_all();
    responder_boot = get_rand_32();
    if (!responder_boot) responder_boot = 1;
    spi_init(spi0, 1000000);
    spi_set_format(spi0, 8, SPI_CPOL_0, SPI_CPHA_0, SPI_MSB_FIRST);
    gpio_set_function(4, GPIO_FUNC_SPI);
    gpio_set_function(6, GPIO_FUNC_SPI);
    gpio_set_function(7, GPIO_FUNC_SPI);
    unsigned count = 0, startup_attempts = 0;
    uint8_t startup_last[4] = {0};
    bool startup_ready = wait_can_ready(&startup_attempts, startup_last);
    bool registers_ok = startup_ready && independent_registers();
    unsigned aloop = 6, bloop = 6; /* 6 = skipped after independent-register failure. */
    if (registers_ok) {
        aloop = loopback(14, 0xa1);
        if (aloop) gpio_put(8, false);
        bloop = loopback(15, 0xb2);
    }
    bool afailed = !registers_ok || aloop, bfailed = !registers_ok || bloop;
    if (afailed) gpio_put(8, false);
    if (bfailed) gpio_put(9, false);
    while (true) {
        int command = getchar_timeout_us(0);
        if ((command == 'l' || command == 'n' || command == 'h') && !afailed) {
            if (!listen_a(command != 'l', command == 'h', false)) {gpio_put(2, true); gpio_put(8, false); afailed = true;}
        }
        if (command == 'g' && !afailed) {
            if(!rf_service()) {gpio_put(2,true);gpio_put(8,false);afailed=true;}
        }
        if (command == 'f' && !afailed) {
            if(!listen_a(true,false,true)) {gpio_put(2,true);gpio_put(8,false);afailed=true;}
        }
        if (command == 's') clock_status();
        if (command == 'd') data_input_test();
        if (command == 'b') bpsk_test(0);
        if (command == 'B') bpsk_test(1);
        if (command == 'j' || command == 'k' || command == 'm') {
            unsigned drive = command == 'j' ? 1 : command == 'k' ? 2 : 3;
            printf("[phase_drive] drive_mA=%u r16=%02X ten100ms states, 1s RF, timer mute2s\n",
                   2*(drive+1), 0x4c|drive);
            (void)clock_window_drive(true,false,phase_hold_emit,drive);
        }
        if (command == 'q') {
            printf("[phase_pll] nominal437.5MHz PLL875MHz ratio35 drive4mA, 1s RF, timer mute2s\n");
            (void)clock_window_drive(true,true,phase_hold_emit,1);
        }
        if (command == 'p') {
            printf("[phase_hold] ten alternating 100ms states, 1s RF, timer mute2s\n");
            (void)clock_window_run(true,false,phase_hold_emit);
        }
        if (command == 'c') {
            printf("[clock_test] preparing CLK0 10MHz, max 10s, TX/RX=0; any input aborts\n");
            (void)clock_test();
        }
        if (command == 't') {
            printf("[tx_tone] preparing 437MHz CW target, max 10s; any input aborts\n");
            (void)tx_tone_test();
        }
        if (command == 'u') {
            printf("[tx_tone] preparing 437.5MHz comparison, PLL ratio35, max10s\n");
            (void)tx_comparison_test();
        }
        if (command == '6' || command == '8' || command == '0') {
            unsigned pf = command == '0' ? 10 : (unsigned)(command - '0');
            printf("[clock_load] preparing temporary %upF, muted 10MHz, max10s\n", pf);
            (void)clock_load_test(pf);
        }
        bool clocks_disabled = disable_clocks();
        uint8_t as = can_read(14, 0x0e), ac = can_read(14, 0x0f);
        uint8_t bs = can_read(15, 0x0e), bc = can_read(15, 0x0f);
        bool aok = configuration_mode(as, ac), bok = configuration_mode(bs, bc);
        /* Unexpected state is latched safe until the next reboot. */
        afailed |= !aok; bfailed |= !bok;
        if (afailed) gpio_put(8, false);
        if (bfailed) gpio_put(9, false);
        printf("[y24-safe-v19] #%u TX=0 RX=0 CAN_A/B=standby "
               "Si5351_disable=%s ADC1_raw=%u\n", ++count,
               clocks_disabled ? "verified_0xFF" : "NOT_VERIFIED",
               (unsigned)adc_read());
        printf("[can] A STAT=%02X CTRL=%02X %s; B STAT=%02X CTRL=%02X %s\n",
               as, ac, !afailed ? "CONFIG" : "FAIL_RESET_HELD",
               bs, bc, !bfailed ? "CONFIG" : "FAIL_RESET_HELD");
        printf("[startup] ready=%u attempts=%u last_A=%02X/%02X last_B=%02X/%02X\n",
               startup_ready, startup_attempts, startup_last[0], startup_last[1], startup_last[2], startup_last[3]);
        printf("[selftest] independent_registers=%s loopback_A=%u loopback_B=%u (0=PASS)\n",
               registers_ok ? "PASS" : "FAIL", aloop, bloop);
        for (unsigned k = 0; k < 2; ++k) {
            printf("[loop_rx_%c]", k ? 'B' : 'A');
            for (unsigned j = 0; j < 13; ++j) printf(" %02X", loop_received[k][j]);
            printf("\n");
        }
        sleep_ms(1000);
    }
}
