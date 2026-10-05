#include <Arduino.h>
#include <driver/gpio.h>
#include <esp_system.h>
#include "uart_link.h"
#include "lte_link.h"
#include "wire.h"
#include "cereg.h"
static HardwareSerial comms(0),modem(1);
static ul_reader reader;
static uint32_t boot,peer,deadline,wait_until,at_started,at_timeout,requests,accepted,rejected;
enum State {OFF,BOOT_WAIT,CONFIGURE,REGISTER,SOCKET_CONFIG,SOCKET_OPEN,READY,SEND};
static State state=OFF;
static unsigned step;
static uint8_t last_error,registered;
static uint8_t cereg_status=255;
static uint8_t diagnostic[LTE_DIAG_SIZE];
static uint32_t rf_started;
static char modem_line[192];static size_t line_used;static bool line_discard;
static bool at_busy,payload_sent,send_pending;
static char response[2048];static size_t used;
static ul_packet pending;
static char usb[40];static size_t usb_used;static bool usb_discard;
static bool due(uint32_t now,uint32_t when) {return (int32_t)(now-when)>=0;}
static void reply(const ul_packet &request,uint8_t type,uint8_t reason=0) {
    ul_packet out=request;out.sender=boot;out.type=type;
    if(type==UL_ERROR) {out.size=1;out.payload[0]=reason;++rejected;}
    uint8_t wire[UL_WIRE_MAX];size_t n=ul_encode(&out,wire);
    comms.write((uint8_t)0);comms.write(wire,n);
}
static void off(void) {
    gpio_hold_dis(GPIO_NUM_45);digitalWrite(45,LOW);gpio_hold_en(GPIO_NUM_45);
    at_busy=false;state=OFF;registered=0;cereg_status=255;line_used=0;line_discard=false;
    if(send_pending) {reply(pending,UL_ERROR,UL_ERR_MODEM_UNKNOWN);send_pending=false;}
}
static uint8_t command_id(const char *command) {
    if(!strcmp(command,"AT"))return 1;
    if(strstr(command,"AT+CMEE="))return 2;
    if(strstr(command,"AT+CFUN="))return 3;
    if(strstr(command,"AT+SQNBANDSEL="))return 4;
    if(strstr(command,"AT+CGDCONT="))return 5;
    if(strstr(command,"AT+CEREG"))return 6;
    if(strstr(command,"AT+COPS"))return 7;
    if(strstr(command,"AT+SQNSCFG="))return 8;
    if(strstr(command,"AT+SQNSD="))return 9;
    if(strstr(command,"AT+SQNSSENDEXT="))return 10;
    return 255;
}
static void reset_diagnostic(void) {
    memset(diagnostic,0,sizeof(diagnostic));diagnostic[16]=LTE_DIAG_VERSION;
    diagnostic[17]=diagnostic[18]=diagnostic[19]=255;
    ul_p32(diagnostic+24,UINT32_MAX);
}
static void failure_snapshot(void) {
    diagnostic[19]=cereg_status;diagnostic[21]=diagnostic[20];diagnostic[22]=state;
    diagnostic[23]|=4;
}
static void observe_modem_byte(char ch) {
        if(ch=='\r' || ch=='\n') {
            if(!line_discard && line_used) {
                modem_line[line_used]=0;
                uint8_t parsed;
                if(parse_cereg(modem_line,&parsed)) {
                    if(registered && parsed!=1 && parsed!=5)ul_p32(diagnostic+32,ul_u32(diagnostic+32)+1);
                    cereg_status=parsed;registered=(parsed==1 || parsed==5);
                    diagnostic[17]=parsed;ul_p32(diagnostic+36,millis()-rf_started);
                }
                const char *error=strstr(modem_line,"+CME ERROR:");
                if(error || !strcmp(modem_line,"ERROR")) {
                    const char *detail=error?error+11:modem_line;
                    while(*detail==' ')++detail;
                    unsigned number;char extra;
                    bool numeric=error && sscanf(detail,"%u %c",&number,&extra)==1;
                    diagnostic[45]=error?(numeric?2:3):1;
                    ul_p32(diagnostic+24,numeric?number:UINT32_MAX);
                    size_t length=strlen(detail);if(length>47) {length=47;diagnostic[23]|=32;}
                    memset(diagnostic+48,0,48);memcpy(diagnostic+48,detail,length);diagnostic[44]=(uint8_t)length;
                }
            }
            line_used=0;line_discard=false;
        } else if(!line_discard) {
            if(line_used+1<sizeof(modem_line))modem_line[line_used++]=ch;else line_discard=true;
        }
}
static void at(const char *command,uint32_t timeout=6000) {
    while(modem.available())observe_modem_byte((char)modem.read());
    diagnostic[20]=command_id(command);
    used=0;response[0]=0;at_started=millis();at_timeout=timeout;at_busy=true;payload_sent=false;
    // CR terminates AT commands; a following LF can become binary send data.
    modem.print(command);modem.print("\r");
}
static void configuration(void) {
    static const char *const commands[]={"AT","AT+CMEE=2","AT+CFUN=0",
        "AT+SQNBANDSEL=0,\"standard\",\"13\"","AT+CGDCONT=1,\"IP\",\"srsapn\"",
        "AT+CEREG=2","AT+COPS?","AT+CFUN=1"};
    if(step<sizeof(commands)/sizeof(commands[0]))at(commands[step++]);
    else {state=REGISTER;wait_until=millis();}
}
static bool valid_packet(const ul_packet &p) {
    const uint8_t *b=p.payload;size_t n=p.size;if(n<W_PAYLOAD+2)return false;
    uint16_t id=ul_u16(b+W_MESSAGE_ID);
    size_t payload=id==W_ID_POWER_STATUS?W_SIZE_POWER_STATUS:id==W_ID_HEARTBEAT?W_SIZE_HEARTBEAT:0;
    return payload && n==W_PAYLOAD+payload+2 && ul_u16(b)==W_TM_IDENTITY && (ul_u16(b+2)>>14)==3 &&
        (size_t)ul_u16(b+4)+7==n && b[W_SCHEMA_VERSION]==W_VERSION && b[W_KIND]==W_KINDS_TELEMETRY &&
        b[W_SOURCE]==W_ENDPOINTS_IHU && b[W_TARGET]==W_ENDPOINTS_GROUND && ul_u32(b+W_SOURCE_BOOT_ID) &&
        ul_u16(b+W_PAYLOAD_LENGTH)==payload && ul_crc(b,n-2)==ul_u16(b+n-2);
}
static void receive(const ul_packet &p) {
    ++requests;
    if(p.version!=1 || p.origin!=p.sender || !p.sender || !p.request) {reply(p,UL_ERROR,UL_ERR_REQUEST);return;}
    if(p.type==UL_HELLO) {peer=p.sender;reply(p,UL_HELLO_ACK);return;}
    if(p.type==UL_ECHO) {reply(p,UL_ECHO_ACK);return;}
    if(p.sender!=peer) {reply(p,UL_ERROR,UL_ERR_REQUEST);return;}
    if(p.type==UL_LINK_STATUS || p.type==UL_LINK_DIAG) {
        if(p.size) {reply(p,UL_ERROR,UL_ERR_PAYLOAD);return;}
        ul_packet result=p;result.size=p.type==UL_LINK_DIAG?LTE_DIAG_SIZE:16;
        memcpy(result.payload,diagnostic,result.size);memset(result.payload,0,16);
        result.payload[0]=state;result.payload[1]=step;result.payload[2]=last_error;result.payload[3]=registered;
        ul_p32(result.payload+4,state==OFF?0:(due(millis(),deadline)?0:deadline-millis()));
        ul_p32(result.payload+8,accepted);ul_p32(result.payload+12,rejected);
        reply(result,p.type==UL_LINK_DIAG?UL_LINK_DIAG_ACK:UL_LINK_STATUS_ACK);return;
    }
    if(p.type==UL_RF_WINDOW) {
        if(p.size!=4 || ul_u32(p.payload)>120) {reply(p,UL_ERROR,UL_ERR_PAYLOAD);return;}
        uint32_t seconds=ul_u32(p.payload);
        if(!seconds) {off();reply(p,UL_RF_WINDOW_ACK);return;}
        if(state!=OFF) {reply(p,UL_ERROR,UL_ERR_BUSY);return;}
        deadline=millis()+seconds*1000;wait_until=millis()+12000;step=0;state=BOOT_WAIT;
        rf_started=millis();reset_diagnostic();
        last_error=0;registered=0;cereg_status=255;line_used=0;line_discard=false;
        gpio_hold_dis(GPIO_NUM_45);digitalWrite(45,HIGH);gpio_hold_en(GPIO_NUM_45);
        reply(p,UL_RF_WINDOW_ACK);return;
    }
    if(p.type==UL_SEND_PACKET) {
        if(!valid_packet(p)) {reply(p,UL_ERROR,UL_ERR_PAYLOAD);return;}
        if(send_pending) {reply(p,UL_ERROR,UL_ERR_BUSY);return;}
        if(at_busy) {reply(p,UL_ERROR,UL_ERR_NOT_READY);return;}
        // Consume pending registration URCs before admission. at() also drains
        // UART input; checking before that drain admitted stale READY sends.
        while(modem.available())observe_modem_byte((char)modem.read());
        if(state!=READY || !registered || at_busy || (int32_t)(deadline-millis())<16000) {reply(p,UL_ERROR,UL_ERR_NOT_READY);return;}
        diagnostic[18]=cereg_status;diagnostic[23]&=8;
        diagnostic[19]=255;diagnostic[21]=diagnostic[22]=diagnostic[44]=diagnostic[45]=0;
        memset(diagnostic+48,0,48);ul_p32(diagnostic+24,UINT32_MAX);
        ul_p32(diagnostic+28,millis()-rf_started);ul_p32(diagnostic+40,p.request);
        pending=p;send_pending=true;state=SEND;
        char command[64];snprintf(command,sizeof(command),"AT+SQNSSENDEXT=1,%u,0",p.size);at(command,15000);return;
    }
    reply(p,UL_ERROR,UL_ERR_TYPE);
}
static void final_response(bool ok) {
    at_busy=false;
    if(!ok)failure_snapshot();
    if(state==SEND) {
        if(ok && payload_sent) {diagnostic[23]|=2;reply(pending,UL_MODEM_ACCEPTED);++accepted;send_pending=false;state=READY;}
        else {last_error=1;reply(pending,UL_ERROR,UL_ERR_MODEM_REJECTED);send_pending=false;off();}
        return;
    }
    if(!ok) {last_error=1;off();return;}
    if(state==CONFIGURE)configuration();
    else if(state==REGISTER) {
        if(registered) {
            state=SOCKET_CONFIG;at("AT+SQNSCFG=1,1,300,90,100,1");
        } else wait_until=millis()+3000;
    } else if(state==SOCKET_CONFIG) {
        state=SOCKET_OPEN;at("AT+SQNSD=1,1,51000,\"172.16.0.1\",0,51001,1,0,0",15000);
    } else if(state==SOCKET_OPEN) {diagnostic[23]|=8;state=READY;}
    else if(state==READY)wait_until=millis()+3000;
}
static void poll_modem(uint32_t now) {
    if(state!=OFF && due(now,deadline)) {failure_snapshot();last_error=2;off();return;}
    if(state==BOOT_WAIT && due(now,wait_until)) {state=CONFIGURE;configuration();}
    if(state==REGISTER && !at_busy) {
        if(registered) {state=SOCKET_CONFIG;at("AT+SQNSCFG=1,1,300,90,100,1");}
        else if(due(now,wait_until))at("AT+CEREG?");
    }
    // Recover cached registration during a READY window without submitting
    // telemetry. RF deadline remains fixed, including these bounded queries.
    if(state==READY && !registered && !at_busy && due(now,wait_until))at("AT+CEREG?");
    for(unsigned i=0;i<256 && modem.available();++i) {
        char ch=(char)modem.read();
        observe_modem_byte(ch);
        if(!at_busy)continue;
        if(used+1>=sizeof(response)) {failure_snapshot();last_error=3;off();return;}
        response[used++]=ch;response[used]=0;
        if(state==SEND && !payload_sent && ch=='>') {modem.write(pending.payload,pending.size);payload_sent=true;diagnostic[23]|=1;}
        if(strstr(response,"\r\nOK\r\n")) {final_response(true);break;}
        if(strstr(response,"\r\nERROR\r\n") || (strstr(response,"\r\n+CME ERROR:") && ch=='\n')) {
            final_response(false);break;
        }
    }
    if(at_busy && (uint32_t)(millis()-at_started)>=at_timeout) {failure_snapshot();last_error=4;off();}
}
static void status(void) {
    Serial.printf("STATUS role=WALTER_LTE_BENCH fw=lte-bench-v2 boot=%lu peer=%lu state=%u cereg=%u radio_window_ms=%lu requests=%lu "
        "modem_accepted=%lu rejected=%lu cobs=%lu crc=%lu overflow=%lu gaps=%lu\n",
        (unsigned long)boot,(unsigned long)peer,(unsigned)state,(unsigned)cereg_status,
        (unsigned long)(state==OFF?0:deadline-millis()),(unsigned long)requests,(unsigned long)accepted,
        (unsigned long)rejected,(unsigned long)reader.framing_errors,(unsigned long)reader.crc_errors,
        (unsigned long)reader.overflows,(unsigned long)reader.gaps);
}
void setup() {
    gpio_hold_dis(GPIO_NUM_45);digitalWrite(45,LOW);pinMode(45,OUTPUT);gpio_hold_en(GPIO_NUM_45);
    reset_diagnostic();
    boot=esp_random();if(!boot)boot=1;
    Serial.begin(115200);comms.setTxBufferSize(512);comms.begin(115200,SERIAL_8N1,44,43);
    modem.setTxBufferSize(512);modem.begin(115200,SERIAL_8N1,14,48);modem.setPins(14,48,47,21);
    modem.setHwFlowCtrlMode(UART_HW_FLOWCTRL_CTS_RTS,64);
    Serial.println("READY Walter LTE bench; radio held reset until bounded RF_WINDOW request");
}
void loop() {
    uint32_t now=millis();ul_packet p;
    for(unsigned i=0;i<128 && comms.available();++i)if(ul_feed(&reader,(uint8_t)comms.read(),now,&p))receive(p);
    ul_expire(&reader,now);poll_modem(millis());
    for(unsigned i=0;i<40 && Serial.available();++i) {
        int ch=Serial.read();
        if(ch=='\r' || ch=='\n') {
            if(!usb_discard) {usb[usb_used]=0;if(!strcmp(usb,"status"))status();else if(!strcmp(usb,"off"))off();}
            usb_used=0;usb_discard=false;
        } else if(!usb_discard) {
            if(ch && usb_used+1<sizeof(usb))usb[usb_used++]=(char)ch;else usb_discard=true;
        }
    }
    delay(1);
}
