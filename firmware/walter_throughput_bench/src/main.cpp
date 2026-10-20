#include <Arduino.h>
#include <driver/gpio.h>
#include <esp_system.h>
#include "engine.h"
#include "bench_identity.h"
static HardwareSerial modem(1);
static char output[16384];static size_t head=0,tail=0;static uint32_t dropped=0;
static void queue(const char *text){
 size_t n=strlen(text);size_t free=(tail+sizeof(output)-head-1)%sizeof(output);
 if(n+1>free){++dropped;return;}
 for(size_t i=0;i<n;++i){output[head]=text[i];head=(head+1)%sizeof(output);}
 output[head]='\n';head=(head+1)%sizeof(output);
}
struct Board final:bench::IO {
 int read()override{return modem.read();}
 size_t space()override{return modem.availableForWrite();}
 void write(const uint8_t *p,size_t n)override{modem.write(p,n);}
 void reset(bool held)override{gpio_hold_dis(GPIO_NUM_45);digitalWrite(45,held?LOW:HIGH);gpio_hold_en(GPIO_NUM_45);}
 void event(const char *line)override{queue(line);}
};
static Board board;static bench::Engine *engine;
static void version(){
 char line[256];snprintf(line,sizeof(line),"{\"event\":\"identity\",\"role\":\"WALTER_THROUGHPUT_TEMP\",\"version\":\"0.1.0\",\"git\":\"%s\",\"source_sha256\":\"%s\",\"uart_baud\":115200,\"log_drops\":%lu}",BENCH_GIT,BENCH_SOURCE_SHA256,(unsigned long)dropped);queue(line);
}
static void command(char *line){
 unsigned seconds,bytes,pps;unsigned long id;char extra;char name[24];uint32_t now=millis();
 if(!strcmp(line,"version"))version();
 else if(!strcmp(line,"status")){version();engine->status(now);}
 else if(!strcmp(line,"off"))engine->off("usb_off");
 else if(sscanf(line,"on %u %c",&seconds,&extra)==1)engine->on(now,seconds);
 else if(sscanf(line,"run %lu %u %u %u %c",&id,&bytes,&pps,&seconds,&extra)==4)engine->run(now,(uint32_t)id,bytes,pps,seconds);
 else if(sscanf(line,"query %23s %c",name,&extra)==1)engine->query(now,name);
 else engine->error("unknown_command");
}
void setup(){
 gpio_hold_dis(GPIO_NUM_45);digitalWrite(45,LOW);pinMode(45,OUTPUT);gpio_hold_en(GPIO_NUM_45);
 // COMMS UART is deliberately not initialized: this temporary image accepts USB only.
 modem.setTxBufferSize(512);modem.begin(115200,SERIAL_8N1,14,48);modem.setPins(14,48,47,21);
 modem.setHwFlowCtrlMode(UART_HW_FLOWCTRL_CTS_RTS,64);
 Serial.begin(115200);static bench::Engine instance(board,esp_random());engine=&instance;engine->begin();version();
}
void loop(){
 engine->tick(millis());static char line[96];static size_t used=0;static bool discard=false;
 for(unsigned i=0;i<128&&Serial.available();++i){int ch=Serial.read();
  if(ch=='\r'||ch=='\n'){
   if(!discard&&used){line[used]=0;command(line);}else if(discard)engine->error("usb_line_overflow");
   used=0;discard=false;
  }else if(!discard){if(ch>0&&used+1<sizeof(line))line[used++]=(char)ch;else discard=true;}
 }
 if(Serial&&head!=tail){size_t n=Serial.availableForWrite();size_t count=head>=tail?head-tail:sizeof(output)-tail;
  if(n>count)n=count;
  if(n){size_t sent=Serial.write((const uint8_t *)output+tail,n);tail=(tail+sent)%sizeof(output);}}
 delay(1);
}
