/* Fault injection for the bounded clock window; no hardware access. */
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#define i2c0 0
static uint8_t regs[256], pointer;
static unsigned calls, fail_at, enable_count, expected_drive;
static uint64_t now, enabled_at, duration;
static bool tx_level, tx_plan, comparison, rx_level;
static bool no_lock, abort_input, lose_lock, bad_readback;
static void gpio_put(unsigned pin, bool value) {
    if (pin==10) {
        if (value) assert(tx_plan && regs[3]==255);
        tx_level=value;
    } else if (pin==11) {rx_level=value;} else assert(((pin==11||pin==16)&&!value)||((pin==2||pin==3)&&value));
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
        assert(regs[16]==(0x4c|expected_drive)&&regs[17]==0x80&&regs[18]==0x80);
        if (tx_plan) {
            assert(tx_level && regs[29]==15);
            if(comparison) assert(regs[27]==1 && regs[30]==128 && regs[33]==0);
            else assert(regs[27]==25 && regs[30]==122 && regs[33]==22);
            assert(regs[43]==1 && regs[45]==1 && regs[46]==0 && !(regs[22]&0x40));
        } else {
            assert(!tx_level && regs[29]==0x0e&&regs[45]==0x26&&regs[27]==1&&regs[43]==1);
            assert(regs[22]&0x40);
        }
        assert(!(regs[149]&0x80)&&!(regs[15]&12));
        ++enable_count;enabled_at=now;
    }
    if(v[0]==3 && v[1]==0xfd) {
        assert(!tx_level && regs[16]==0x80 && regs[17]==0x4d && regs[18]==0x80);
        assert(regs[27]==5 && regs[29]==15 && regs[30]==102 && regs[33]==2);
        assert(regs[51]==1 && regs[53]==1 && regs[54]==0);
        ++enable_count;enabled_at=now;
    }
    if(v[0]==3&&v[1]==255&&regs[3]==0xfd)duration=now-enabled_at;
    regs[v[0]]=v[1];return 2;
}
static int i2c_read_timeout_us(int bus,int addr,uint8_t *v,int n,bool hold,int timeout) {
    assert(bus==0&&addr==0x60&&n==1&&!hold&&timeout==2000);++calls;
    if(calls==fail_at)return -1;
    *v=regs[pointer];
    if(pointer==0&&(no_lock||(lose_lock&&enable_count)))*v|=0x20;
    if(pointer==50&&bad_readback)*v^=1;
    return 1;
}
static bool disable_clocks(void) {
    uint8_t tx[]={3,255},r=3,v;
    return i2c_write_timeout_us(0,0x60,tx,2,false,2000)==2 &&
      i2c_write_timeout_us(0,0x60,&r,1,true,2000)==1 &&
      i2c_read_timeout_us(0,0x60,&v,1,false,2000)==1&&v==255;
}
static bool alarm_fail;
typedef int alarm_id_t;
static alarm_id_t add_alarm_in_ms(unsigned ms, int64_t (*cb)(alarm_id_t,void*), void *u, bool past) {
    assert(ms==2000 && cb && !u && !past);return alarm_fail ? -1 : 1;
}
static bool cancel_alarm(alarm_id_t id) {assert(id==1);return true;}
#include "clock_test.h"
static void reset(void) {
    memset(regs,0,sizeof(regs));regs[3]=255;regs[183]=0xd2;
    calls=fail_at=enable_count=expected_drive=0;now=enabled_at=duration=0;
    no_lock=abort_input=lose_lock=bad_readback=tx_level=tx_plan=comparison=false;
}
#include "rx_test.h"
static unsigned captures;
static bool capture_ok(void) {++captures;assert(!tx_level);sleep_ms(512);return true;}
static bool capture_abort(void) {return false;}
int main(void) {
    reset();assert(rx_window(true,capture_ok));
    assert(captures==1 && !tx_level && !rx_level && regs[3]==255 && regs[17]==0x80);
    assert(duration>=10000000 && duration<10020000);
    unsigned total=calls;
    for(unsigned i=1;i<=total;i++) {
        reset();fail_at=i;assert(!rx_window(true,capture_ok));
        assert(!tx_level && !rx_level && (regs[3]==255 || regs[17]==0x80));
        assert(now<10200000);
    }
    reset();no_lock=true;assert(!rx_window(true,capture_ok)&&!enable_count);
    reset();bad_readback=true;assert(!rx_window(true,capture_ok)&&!enable_count);
    reset();abort_input=true;assert(!rx_window(true,capture_ok));
    reset();lose_lock=true;assert(!rx_window(true,capture_ok));
    reset();assert(!rx_window(true,capture_abort));
    reset();captures=0;assert(rx_window(false,capture_ok)&&!enable_count&&captures==1);
    total=calls;
    for(unsigned i=1;i<=total;i++) {
        reset();fail_at=i;assert(!rx_window(false,capture_ok));
        assert(!tx_level && !rx_level && regs[3]==255);
    }
    puts("PASS: RX clock plan, TX exclusion, ADC callback, timeout, abort, lock/readback and I2C fault sweep");
}
