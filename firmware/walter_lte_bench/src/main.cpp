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
static void observe_modem_byte(char ch) {
        if(ch=='\r' || ch=='\n') {
            if(!line_discard && line_used) {
                modem_line[line_used]=0;
                if(parse_cereg(modem_line,&cereg_status))registered=(cereg_status==1 || cereg_status==5);
            }
            line_used=0;line_discard=false;
        } else if(!line_discard) {
            if(line_used+1<sizeof(modem_line))modem_line[line_used++]=ch;else line_discard=true;
        }
}
static void at(const char *command,uint32_t timeout=6000) {
    while(modem.available())observe_modem_byte((char)modem.read());
    used=0;response[0]=0;at_started=millis();at_timeout=timeout;at_busy=true;payload_sent=false;
    modem.print(command);modem.print("\r\n");
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
        ul_u16(b+4)+7==n && b[W_SCHEMA_VERSION]==W_VERSION && b[W_KIND]==W_KINDS_TELEMETRY &&
        b[W_SOURCE]==W_ENDPOINTS_IHU && b[W_TARGET]==W_ENDPOINTS_GROUND && ul_u32(b+W_SOURCE_BOOT_ID) &&
        ul_u16(b+W_PAYLOAD_LENGTH)==payload && ul_crc(b,n-2)==ul_u16(b+n-2);
}
static void receive(const ul_packet &p) {
    ++requests;
    if(p.version!=1 || p.origin!=p.sender || !p.sender || !p.request) {reply(p,UL_ERROR,UL_ERR_REQUEST);return;}
    if(p.type==UL_HELLO) {peer=p.sender;reply(p,UL_HELLO_ACK);return;}
    if(p.type==UL_ECHO) {reply(p,UL_ECHO_ACK);return;}
    if(p.sender!=peer) {reply(p,UL_ERROR,UL_ERR_REQUEST);return;}
    if(p.type==UL_LINK_STATUS) {
        if(p.size) {reply(p,UL_ERROR,UL_ERR_PAYLOAD);return;}
        ul_packet result=p;result.size=16;memset(result.payload,0,16);
        result.payload[0]=state;result.payload[1]=step;result.payload[2]=last_error;result.payload[3]=registered;
        ul_p32(result.payload+4,state==OFF?0:(due(millis(),deadline)?0:deadline-millis()));
        ul_p32(result.payload+8,accepted);ul_p32(result.payload+12,rejected);
        reply(result,UL_LINK_STATUS_ACK);return;
    }
    if(p.type==UL_RF_WINDOW) {
        if(p.size!=4 || ul_u32(p.payload)>120) {reply(p,UL_ERROR,UL_ERR_PAYLOAD);return;}
        uint32_t seconds=ul_u32(p.payload);
        if(!seconds) {off();reply(p,UL_RF_WINDOW_ACK);return;}
        if(state!=OFF) {reply(p,UL_ERROR,UL_ERR_BUSY);return;}
        deadline=millis()+seconds*1000;wait_until=millis()+12000;step=0;state=BOOT_WAIT;
        last_error=0;registered=0;cereg_status=255;line_used=0;line_discard=false;
        gpio_hold_dis(GPIO_NUM_45);digitalWrite(45,HIGH);gpio_hold_en(GPIO_NUM_45);
        reply(p,UL_RF_WINDOW_ACK);return;
    }
    if(p.type==UL_SEND_PACKET) {
        if(!valid_packet(p)) {reply(p,UL_ERROR,UL_ERR_PAYLOAD);return;}
        if(send_pending) {reply(p,UL_ERROR,UL_ERR_BUSY);return;}
        if(state!=READY || at_busy || (int32_t)(deadline-millis())<16000) {reply(p,UL_ERROR,UL_ERR_NOT_READY);return;}
        pending=p;send_pending=true;state=SEND;
        char command[64];snprintf(command,sizeof(command),"AT+SQNSSENDEXT=1,%u,0",p.size);at(command,15000);return;
    }
    reply(p,UL_ERROR,UL_ERR_TYPE);
}
static void final_response(bool ok) {
    at_busy=false;
    if(state==SEND) {
        if(ok && payload_sent) {reply(pending,UL_MODEM_ACCEPTED);++accepted;send_pending=false;state=READY;}
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
    } else if(state==SOCKET_OPEN)state=READY;
}
static void poll_modem(uint32_t now) {
    if(state!=OFF && due(now,deadline)) {last_error=2;off();return;}
    if(state==BOOT_WAIT && due(now,wait_until)) {state=CONFIGURE;configuration();}
    if(state==REGISTER && !at_busy) {
        if(registered) {state=SOCKET_CONFIG;at("AT+SQNSCFG=1,1,300,90,100,1");}
        else if(due(now,wait_until))at("AT+CEREG?");
    }
    for(unsigned i=0;i<256 && modem.available();++i) {
        char ch=(char)modem.read();
        observe_modem_byte(ch);
        if(!at_busy)continue;
        if(used+1>=sizeof(response)) {last_error=3;off();return;}
        response[used++]=ch;response[used]=0;
        if(state==SEND && !payload_sent && ch=='>') {modem.write(pending.payload,pending.size);payload_sent=true;}
        if(strstr(response,"\r\nOK\r\n")) {final_response(true);break;}
        if(strstr(response,"\r\nERROR\r\n") || (strstr(response,"\r\n+CME ERROR:") && ch=='\n')) {
            final_response(false);break;
        }
    }
    if(at_busy && (uint32_t)(millis()-at_started)>=at_timeout) {last_error=4;off();}
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
