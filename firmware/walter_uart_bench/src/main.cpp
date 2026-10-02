#include <Arduino.h>
#include <driver/gpio.h>

// Application link to COMMS. The Sequans UART is not initialized.
static HardwareSerial comms(0);
static uint32_t rx_bytes, tx_bytes, pings, errors;
struct Line {
    char data[80];
    size_t used = 0;
    bool discard = false;
};
static Line uart_line, usb_line;

static void status() {
    Serial.printf("STATUS role=WALTER_UART_PEER fw=uart-peer-v1 rx=44 tx=43 baud=115200 "
                  "rx_bytes=%lu tx_bytes=%lu pings=%lu errors=%lu modem=HELD_RESET uptime_ms=%lu\n",
                  (unsigned long)rx_bytes, (unsigned long)tx_bytes, (unsigned long)pings,
                  (unsigned long)errors, (unsigned long)millis());
}

static void uart_command(const char *text) {
    const char *prefix = "EMBER_UART_PING v1 ";
    if (strncmp(text, prefix, strlen(prefix))) { ++errors; return; }
    const char *number = text + strlen(prefix);
    size_t n = strlen(number);
    if (!n || n > 10) { ++errors; return; }
    for (size_t i = 0; i < n; ++i) {
        if (number[i] < '0' || number[i] > '9') { ++errors; return; }
    }
    char reply[80];
    int size = snprintf(reply, sizeof(reply), "EMBER_UART_PONG v1 %s\n", number);
    tx_bytes += comms.write((const uint8_t *)reply, (size_t)size);
    ++pings;
    Serial.printf("PEER_ACK probe=%s\n", number);
}

static void usb_command(const char *text) {
    if (!strcmp(text, "status")) status();
    else if (!strcmp(text, "help")) Serial.println("COMMANDS status | help; UART responds to EMBER_UART_PING v1 N");
    else if (*text) Serial.println("ERROR unknown command");
}

static void feed(Line &line, char ch, bool uart) {
    if (ch == '\r' || ch == '\n') {
        if (line.discard) {
            if (uart) ++errors;
            else Serial.println("ERROR command too long");
        } else if (line.used) {
            line.data[line.used] = 0;
            if (uart) uart_command(line.data);
            else usb_command(line.data);
        }
        line.used = 0;
        line.discard = false;
    } else if (!line.discard) {
        if (line.used + 1 < sizeof(line.data) && ch != 0) line.data[line.used++] = ch;
        else line.discard = true;
    }
}

void setup() {
    // Vendor identifies GPIO45 as active-low modem reset. Hold it low throughout
    // this diagnostic, so cellular/GNSS operation is not part of the UART test.
    gpio_hold_dis(GPIO_NUM_45);
    digitalWrite(45, LOW);
    pinMode(45, OUTPUT);
    gpio_hold_en(GPIO_NUM_45);
    Serial.begin(115200);  // Native USB hardware CDC; no UART0 console logs.
    comms.begin(115200, SERIAL_8N1, 44, 43);
    Serial.println("READY Walter COMMS UART responder; modem held in reset");
}

void loop() {
    for (int i = 0; i < 64 && comms.available(); ++i) {
        ++rx_bytes;
        feed(uart_line, (char)comms.read(), true);
    }
    for (int i = 0; i < 32 && Serial.available(); ++i) feed(usb_line, (char)Serial.read(), false);
    delay(1);
}
