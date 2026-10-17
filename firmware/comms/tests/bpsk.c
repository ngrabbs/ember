#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include "bpsk_packet.h"
static uint64_t now, late_at, abort_at;
static bool clock_deadline_fired;
static unsigned writes;
static uint64_t timestamps[BPSK_FRAME_MAX*8];
static bool values[BPSK_FRAME_MAX*8];
static uint64_t time_us_64(void){++now;if(late_at && now==late_at)now+=300;return now;}
static int getchar_timeout_us(unsigned t){assert(t==0);return abort_at && now>=abort_at ? 'x':-1;}
static void gpio_put(unsigned pin,bool v){assert(pin==16);assert(writes<BPSK_FRAME_MAX*8);timestamps[writes]=now;values[writes++]=v;}
#include "bpsk_emit.h"
static void reset(void){now=late_at=abort_at=0;writes=0;clock_deadline_fired=false;}
int main(int argc,char **argv){
 (void)argv;
 assert(!bpsk_frame(packet_frame,100,1,1,1));assert(!bpsk_frame(packet_frame,101,0,1,1));
 assert(bp_crc32((const uint8_t*)"123456789",9)==0xcbf43926);
 assert(bp_crc16((const uint8_t*)"123456789",9)==0x29b1);
 assert(bpsk_frame(packet_frame,sizeof(packet_frame),0x12345678,19,123456)==101);
 if(argc>1){for(unsigned i=0;i<101;i++)printf("%02x",packet_frame[i]);puts("");return 0;}
 reset();assert(bpsk_emit(1500000));assert(writes==808 && now<674000);
 bool previous=false;
 for(unsigned i=0;i<writes;i++){
  assert((values[i]^previous)==((packet_frame[i/8]>>(7-i%8))&1));previous=values[i];
  if(i)assert(timestamps[i]-timestamps[i-1]>=830 && timestamps[i]-timestamps[i-1]<=836);
 }
 reset();abort_at=20000;assert(!bpsk_emit(1500000)&&now<21000);
 reset();late_at=100001;assert(!bpsk_emit(1500000));
 reset();clock_deadline_fired=true;assert(!bpsk_emit(1500000)&&writes==0);
 reset();assert(!bpsk_emit(10000)&&now<12000);
 packet_frame_size=BPSK_FRAME_MAX;reset();assert(bpsk_emit(1500000));
 assert(writes==BPSK_FRAME_MAX*8 && now>1273000 && now<1274000);
 reset();abort_at=1100000;assert(!bpsk_emit(1500000));
 packet_frame_size=BPSK_FRAME_MAX+1;reset();assert(!bpsk_emit(1500000)&&writes==0);
 packet_frame_size=BPSK_FRAME_SIZE;
 reset();assert(phase_hold_emit(1500000));assert(writes==10 && now>=1000000 && now<1000020);
 for(unsigned i=0;i<10;i++){assert(values[i]==(bool)(i&1));if(i)assert(timestamps[i]-timestamps[i-1]>=99995 && timestamps[i]-timestamps[i-1]<=100005);}
 reset();abort_at=20000;assert(!phase_hold_emit(1500000)&&now<21000);
 reset();late_at=100001;assert(!phase_hold_emit(1500000));
 reset();clock_deadline_fired=true;assert(!phase_hold_emit(1500000)&&writes==0);
 reset();assert(!phase_hold_emit(950000)&&now<950020);
 puts("PASS: packet CRCs, DBPSK mapping, symbol timing, console abort, lateness and deadlines");
}
