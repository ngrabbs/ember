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
static uint16_t messages[64];
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
 assert(bursts<64);messages[bursts++]=ul_u16(packet_frame+43+W_MESSAGE_ID);
 return bursts!=fail_burst;
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
 assert(messages[0]==W_ID_COMMS_FIRMWARE && messages[1]==W_ID_HEARTBEAT);
 p=request(2);fail_burst=bursts+1;inject(&p);
 assert(!rf_service_window(RF_ON_DEMAND));assert(!rf_queue.count && replies[6].payload[1]==UHF_FAILED);
 assert(rf_bus_open());inject(&p);assert(!rf_queue.count && replies[7].payload[1]==UHF_FAILED);
 unsigned previous=bursts;assert(rf_service_window(RF_ON_DEMAND) && bursts==previous); /* no retry */
 p=request(3);fail_burst=0;inject(&p);abort_console=true;
 assert(rf_service_window(RF_ON_DEMAND));abort_console=false;assert(rf_bus_open());
 assert(!rf_queue.count && bursts==previous && replies[9].payload[1]==UHF_CANCELLED);
 p=request(4);p.type=UL_ECHO;inject(&p);assert(!rf_queue.count && bursts==previous);
 /* A new on-demand operation sends data only, even after cancellation/failure. */
 p=request(5);inject(&p);previous=bursts;
 assert(rf_service_window(RF_ON_DEMAND));assert(rf_bus_open());
 assert(bursts==previous+1 && messages[previous]==W_ID_HEARTBEAT);
 /* An explicit identity request is exactly one COMMS-owned packet, with history. */
 p=request(6);p.type=CF_UHF_FIRMWARE;p.size=0;inject(&p);previous=bursts;
 assert(rf_service_window(RF_ON_DEMAND));assert(rf_bus_open());
 assert(bursts==previous+1 && messages[previous]==W_ID_COMMS_FIRMWARE);
 assert(replies[reply_count-1].payload[1]==UHF_OK && !ul_u16(replies[reply_count-1].payload+2));
 inject(&p);assert(!rf_queue.count && bursts==previous+1);
 p.request=7;inject(&p);previous=bursts;
 assert(rf_service_window(RF_ON_DEMAND));assert(rf_bus_open());
 assert(bursts==previous+1 && messages[previous]==W_ID_COMMS_FIRMWARE);
 p.request=8;p.size=1;inject(&p);assert(!rf_queue.count && replies[reply_count-1].payload[1]==UHF_INVALID);
 /* A fresh IHU origin does not clear COMMS's boot-scoped announcement. */
 p=request(1);p.sender=p.origin=124;bp32(p.payload+W_SOURCE_BOOT_ID,124);
 bp16(p.payload+p.size-2,bp_crc16(p.payload,p.size-2));inject(&p);previous=bursts;
 assert(rf_service_window(RF_ON_DEMAND));assert(rf_bus_open());
 assert(bursts==previous+1 && messages[previous]==W_ID_HEARTBEAT);
 /* Simulate a COMMS reboot; explicit first identity satisfies the announcement. */
 firmware_announced=false;rf_queue=(rq_state){0};++responder_boot;
 p=request(1);p.type=CF_UHF_FIRMWARE;p.size=0;inject(&p);previous=bursts;
 assert(rf_service_window(RF_ON_DEMAND));assert(rf_bus_open());
 assert(firmware_announced && bursts==previous+1 && messages[previous]==W_ID_COMMS_FIRMWARE);
 p=request(2);inject(&p);previous=bursts;
 assert(rf_service_window(RF_ON_DEMAND));assert(rf_bus_open());
 assert(bursts==previous+1 && messages[previous]==W_ID_HEARTBEAT);
 /* A failed identity is never recorded as announced or automatically retried. */
 firmware_announced=false;rf_queue=(rq_state){0};++responder_boot;
 p=request(1);fail_burst=bursts+1;inject(&p);previous=bursts;
 assert(!rf_service_window(RF_ON_DEMAND));assert(rf_bus_open());
 assert(!firmware_announced && bursts==previous+1 && replies[reply_count-1].payload[1]==UHF_CANCELLED);
 inject(&p);assert(!rf_queue.count && bursts==previous+1);
 p=request(2);p.type=CF_UHF_FIRMWARE;p.size=0;fail_burst=bursts+1;inject(&p);
 assert(!rf_service_window(RF_ON_DEMAND));assert(rf_bus_open());
 assert(!firmware_announced && replies[reply_count-1].payload[1]==UHF_FAILED);
 /* Boot state resets also restore the automatic prefix for ordinary telemetry. */
 firmware_announced=false;rf_queue=(rq_state){0};++responder_boot;fail_burst=0;
 p=request(1);inject(&p);previous=bursts;
 assert(rf_service_window(RF_ON_DEMAND));assert(rf_bus_open());
 assert(bursts==previous+2 && messages[previous]==W_ID_COMMS_FIRMWARE && messages[previous+1]==W_ID_HEARTBEAT);
 /* Opening a diagnostic batch window does not reset the boot announcement. */
 p=request(2);inject(&p);previous=bursts;assert(rf_bus_close());
 assert(rf_service());assert(rf_bus_open());
 assert(bursts==previous+1 && messages[previous]==W_ID_HEARTBEAT);
 regs[14]=0x80;assert(!can_idle_poll()); /* unhealthy CAN never admits */
 puts("PASS: boot-scoped identity, explicit identity/replay/failure, origin changes, on-demand admission/transmission, idle silence, duplicate history, native validation, failure/no retry, cancel, unhealthy CAN");
 return 0;
}
