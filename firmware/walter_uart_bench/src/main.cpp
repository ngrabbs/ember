#include <Arduino.h>
#include <driver/gpio.h>
#include <esp_system.h>
#include "uart_link.h"
static HardwareSerial comms(0);
static ul_reader reader;
static uint32_t boot,rx_bytes,tx_bytes,requests,rejections;
struct Line {char data[32];size_t used=0;bool discard=false;};
static Line usb;
static void status() {
    Serial.printf("STATUS role=WALTER_UART_PEER fw=uart-framed-v1 boot=%lu rx=44 tx=43 baud=115200 "
                  "rx_bytes=%lu tx_bytes=%lu requests=%lu rejections=%lu cobs=%lu crc=%lu format=%lu "
                  "overflow=%lu gaps=%lu modem=HELD_RESET uptime_ms=%lu\n",
                  (unsigned long)boot,(unsigned long)rx_bytes,(unsigned long)tx_bytes,(unsigned long)requests,
                  (unsigned long)rejections,(unsigned long)reader.framing_errors,(unsigned long)reader.crc_errors,
                  (unsigned long)reader.format_errors,(unsigned long)reader.overflows,(unsigned long)reader.gaps,
                  (unsigned long)millis());
}
static void command(const char *s) {
    if(!strcmp(s,"status"))status();
    else if(!strcmp(s,"help"))Serial.println("COMMANDS status | help; UART is COBS/CRC bench HELLO/ECHO only");
    else if(*s)Serial.println("ERROR unknown command");
}
void setup() {
    gpio_hold_dis(GPIO_NUM_45);digitalWrite(45,LOW);pinMode(45,OUTPUT);gpio_hold_en(GPIO_NUM_45);
    boot=esp_random();if(!boot)boot=1;
    Serial.begin(115200);comms.begin(115200,SERIAL_8N1,44,43);
    Serial.println("READY Walter framed UART bench; modem held reset");
}
void loop() {
    uint32_t now=millis();ul_packet packet,reply;
    for(unsigned i=0;i<128 && comms.available();++i) {
        uint8_t byte=(uint8_t)comms.read();++rx_bytes;
        if(ul_feed(&reader,byte,now,&packet)) {
            ++requests;ul_reply(&packet,boot,&reply);if(reply.type==UL_ERROR)++rejections;
            uint8_t wire[UL_WIRE_MAX];size_t size=ul_encode(&reply,wire);
            tx_bytes+=comms.write((uint8_t)0);tx_bytes+=comms.write(wire,size);
            // No per-frame USB logging: UART progress must not wait on USB host.
        }
    }
    ul_expire(&reader,now);
    for(unsigned i=0;i<32 && Serial.available();++i) {
        int ch=Serial.read();
        if(ch=='\r' || ch=='\n') {
            if(usb.discard)Serial.println("ERROR command too long");
            else {usb.data[usb.used]=0;command(usb.data);}
            usb.used=0;usb.discard=false;
        } else if(!usb.discard) {
            if(ch && usb.used+1<sizeof(usb.data))usb.data[usb.used++]=(char)ch;
            else usb.discard=true;
        }
    }
    delay(1);
}
