/* Exercise real CAN reassembly, native validation, admission/history and drain. */
#include <assert.h>
#include <stdio.h>
#include "hello.h"
#include "device_registry.h"
#include "rf_bridge.h"
#include "firmware_identity.h"
#define spi0 0
static uint32_t responder_boot=456;
static uint8_t regs[128],packet_frame[BPSK_FRAME_MAX];
static size_t packet_frame_size;
static uint64_t ticks;
static unsigned bursts,fail_burst,reply_count;
static bool abort_console,reply_ok=true;
static ul_packet replies[64];
static uint64_t time_us_64(void){return ticks+=1000;}
static bool configuration_mode(uint8_t s,uint8_t c){return (s&0xe0)==0x80 && (c&0xe0)==0x80;}
static uint8_t can_read(unsigned cs,unsigned reg){assert(cs==14);return regs[reg];}
static void can_write(unsigned cs,unsigned reg,uint8_t v){assert(cs==14);regs[reg]=v;}
static void can_modify(unsigned reg,uint8_t mask,uint8_t v){regs[reg]=(regs[reg]&~mask)|(v&mask);}
static bool can_mode(unsigned cs,uint8_t mode){assert(cs==14);regs[14]=regs[15]=mode;return true;}
static void gpio_put(unsigned pin,bool level){(void)pin;(void)level;}
static void sleep_us(unsigned us){assert(us==2);}
static void sleep_ms(unsigned ms){ticks+=ms*1000;}
static int getchar_timeout_us(unsigned timeout){assert(timeout==0);return abort_console?'x':-1;}
static int spi_write_read_blocking(int spi,const uint8_t *tx,uint8_t *rx,int n){
 assert(spi==0 && n==15 && tx[0]==3);memcpy(rx+2,regs+tx[1],n-2);return n;
}
static bool can_send_frame(const cf_frame *f,uint64_t end){(void)f;(void)end;return true;}
static bool hello_send(const uint8_t *wire,size_t size,uint32_t request,uint64_t end){
 (void)end;ul_reader r={0};ul_packet p={0};unsigned count=0;
 for(size_t i=0;i<size;i++)if(ul_feed(&r,wire[i],0,&p))++count;
 assert(count==1 && p.request==request && reply_count<64);replies[reply_count++]=p;return reply_ok;
}
static bool bpsk_emit(uint64_t deadline){(void)deadline;return true;}
static bool clock_window_drive(bool tx,bool comparison,bool (*emit)(uint64_t),unsigned drive){
 assert(tx && !comparison && emit==bpsk_emit && drive==1);
 assert((regs[14]&0xe0)==0x80 && packet_frame_size>63);
 ++bursts;return bursts!=fail_burst;
}
#include "rf_service.h"
static void inject(const ul_packet *p){
 uint8_t wire[UL_WIRE_MAX];size_t n=ul_encode(p,wire);cf_frame f;
 for(unsigned i=0;cf_fragment(wire,n,CF_IHU_ID,p->request,i,&f);i++){
  regs[0x61]=f.id>>3;regs[0x62]=f.id<<5;regs[0x63]=regs[0x64]=0;
  regs[0x65]=f.size;memcpy(regs+0x66,f.data,f.size);regs[0x2c]=1;
  assert(can_idle_poll());
 }
}
static ul_packet request(unsigned id){
 uint8_t frame[BPSK_FRAME_MAX];assert(bpsk_frame(frame,sizeof(frame),123,7,456));
 ul_packet p={.version=1,.type=CF_UHF_SEND,.sender=123,.origin=123,.request=id,.size=38};
 memcpy(p.payload,frame+43,38);p.payload[W_SOURCE]=W_ENDPOINTS_IHU;
 bp16(p.payload+36,bp_crc16(p.payload,36));return p;
}
int main(void){
 regs[0x29]=0xf0;regs[0x28]=0x86;regs[14]=regs[15]=0x80;
 assert(rf_bus_open());
 assert(rf_service_window(RF_ON_DEMAND) && bursts==0); /* idle is silent */
 ul_packet p=request(1);inject(&p);
 assert(rf_queue.count==1 && bursts==0 && replies[0].type==CF_UHF_ADMITTED);
 inject(&p);assert(rf_queue.count==1 && bursts==0); /* duplicate admission */
 assert(rf_service_window(RF_ON_DEMAND));assert(rf_bus_open());
 assert(bursts==2 && rf_queue.count==0 && replies[2].type==CF_UHF_RESULT && replies[2].payload[1]==UHF_OK);
 inject(&p);assert(rf_queue.count==0 && bursts==2 && replies[3].type==CF_UHF_RESULT);
 p.payload[0]^=1;inject(&p);assert(!rf_queue.count && replies[4].payload[1]==UHF_INVALID);
 p=request(2);fail_burst=bursts+2;inject(&p);
 assert(!rf_service_window(RF_ON_DEMAND));assert(!rf_queue.count && replies[6].payload[1]==UHF_FAILED);
 assert(rf_bus_open());inject(&p);assert(!rf_queue.count && replies[7].payload[1]==UHF_FAILED);
 unsigned previous=bursts;assert(rf_service_window(RF_ON_DEMAND) && bursts==previous); /* no retry */
 p=request(3);fail_burst=0;inject(&p);abort_console=true;
 assert(rf_service_window(RF_ON_DEMAND));abort_console=false;assert(rf_bus_open());
 assert(!rf_queue.count && bursts==previous && replies[9].payload[1]==UHF_CANCELLED);
 p=request(4);p.type=UL_ECHO;inject(&p);assert(!rf_queue.count && bursts==previous);
 regs[14]=0x80;assert(!can_idle_poll()); /* unhealthy CAN never admits */
 puts("PASS: on-demand admission/transmission, idle silence, duplicate history, native validation, failure/no retry, cancel, unhealthy CAN");
 return 0;
}
