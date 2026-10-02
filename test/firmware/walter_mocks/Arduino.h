#pragma once
#include <stdint.h>
#include <stddef.h>
#include <string>
#include <stdio.h>
#include <string.h>
#define LOW 0
#define HIGH 1
#define OUTPUT 1
#define SERIAL_8N1 0
#define UART_HW_FLOWCTRL_CTS_RTS 3
extern uint32_t test_time;
extern int test_reset;
inline uint32_t millis() {return test_time;}
inline void delay(unsigned n) {test_time+=n;}
inline void pinMode(unsigned,unsigned) {}
inline void digitalWrite(unsigned pin,int value) {if(pin==45)test_reset=value;}
class HardwareSerial {
public:
    std::string input,output;
    HardwareSerial(unsigned) {}
    void begin(unsigned,unsigned=0,int=-1,int=-1) {}
    void setTxBufferSize(unsigned) {}
    void setPins(int,int,int,int) {}
    void setHwFlowCtrlMode(unsigned,unsigned) {}
    int available() {return input.size();}
    int read() {if(input.empty())return -1;int ch=(uint8_t)input[0];input.erase(0,1);return ch;}
    size_t write(uint8_t ch) {output.push_back(ch);return 1;}
    size_t write(const uint8_t *data,size_t n) {output.append((const char*)data,n);return n;}
    void print(const char *s) {output+=s;}
    void println(const char *s) {output+=s;output+='\n';}
    template<class... Args> void printf(const char*,Args...) {}
};
extern HardwareSerial Serial;
