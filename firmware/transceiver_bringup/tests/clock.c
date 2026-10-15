/* Fault injection for the bounded clock window; no hardware access. */
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#define i2c0 0
static uint8_t regs[256], pointer;
static unsigned calls, fail_at, enable_count;
static uint64_t now, enabled_at, duration;
static bool no_lock, abort_input, lose_lock, bad_readback;
static void gpio_put(unsigned pin, bool value) {
    assert(((pin==10||pin==11||pin==16)&&!value)||((pin==2||pin==3)&&value));
}
static void sleep_ms(unsigned ms) {now += ms*1000;}
static uint64_t time_us_64(void) {return now;}
static int getchar_timeout_us(unsigned us) {assert(!us);return abort_input?'x':-1;}
static int i2c_write_timeout_us(int bus,int addr,const uint8_t *v,int n,bool hold,int timeout) {
    assert(bus==0&&addr==0x60&&timeout==2000); ++calls;
    if(calls==fail_at)return -1;
    if(n==1) {assert(hold);pointer=*v;return 1;}
    assert(n==2&&!hold);
    if(v[0]==3 && v[1]==0xfe) {
        assert(regs[16]==0x4c&&regs[17]==0x80&&regs[18]==0x80);
        assert(regs[29]==0x0e&&regs[45]==0x26&&regs[27]==1&&regs[43]==1);
        assert(!(regs[149]&0x80)&&!(regs[15]&12)&&(regs[22]&0x40));
        ++enable_count;enabled_at=now;
    }
    if(v[0]==3&&v[1]==255&&regs[3]==0xfe)duration=now-enabled_at;
    regs[v[0]]=v[1];return 2;
}
static int i2c_read_timeout_us(int bus,int addr,uint8_t *v,int n,bool hold,int timeout) {
    assert(bus==0&&addr==0x60&&n==1&&!hold&&timeout==2000);++calls;
    if(calls==fail_at)return -1;
    *v=regs[pointer];
    if(pointer==0&&(no_lock||(lose_lock&&enable_count)))*v|=0x20;
    if(pointer==42&&bad_readback)*v^=1;
    return 1;
}
static bool disable_clocks(void) {
    uint8_t tx[]={3,255},r=3,v;
    return i2c_write_timeout_us(0,0x60,tx,2,false,2000)==2 &&
      i2c_write_timeout_us(0,0x60,&r,1,true,2000)==1 &&
      i2c_read_timeout_us(0,0x60,&v,1,false,2000)==1&&v==255;
}
#include "clock_test.h"
static void reset(void) {
    memset(regs,0,sizeof(regs));regs[3]=255;regs[183]=0xd2;
    calls=fail_at=enable_count=0;now=enabled_at=duration=0;
    no_lock=abort_input=lose_lock=bad_readback=false;
}
int main(void) {
    reset();clock_status();reset();assert(clock_test());
    assert(enable_count==1&&duration==10000000&&regs[3]==255&&regs[16]==0x80);
    assert(regs[183]==0xd2);unsigned count=calls;
    /* Every individual I2C failure: never reports success; attempts shutdown. */
    for(unsigned i=1;i<=count;i++) {
        reset();fail_at=i;assert(!clock_test());
        assert(regs[3]==255||regs[16]==0x80);
        assert(now<=10100000);
    }
    reset();no_lock=true;assert(!clock_test()&&!enable_count);
    reset();bad_readback=true;assert(!clock_test()&&!enable_count);
    reset();abort_input=true;assert(!clock_test()&&regs[3]==255&&duration==0);
    reset();lose_lock=true;assert(!clock_test()&&regs[3]==255&&duration==0);
    puts("PASS: clock timing, register plan, I2C fault sweep, lock/readback failures, abort, shutdown");
}
