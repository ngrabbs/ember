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
static bool tx_level, tx_plan, comparison;
static bool no_lock, abort_input, lose_lock, bad_readback;
static void gpio_put(unsigned pin, bool value) {
    if (pin==10) {
        if (value) assert(tx_plan && regs[3]==255);
        tx_level=value;
    } else assert(((pin==11||pin==16)&&!value)||((pin==2||pin==3)&&value));
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
static bool alarm_fail;
typedef int alarm_id_t;
static alarm_id_t add_alarm_in_ms(unsigned ms, int64_t (*cb)(alarm_id_t,void*), void *u, bool past) {
    assert(ms==2000 && cb && !u && !past);return alarm_fail ? -1 : 1;
}
static bool cancel_alarm(alarm_id_t id) {assert(id==1);return true;}
#include "clock_test.h"
static void reset(void) {
    memset(regs,0,sizeof(regs));regs[3]=255;regs[183]=0xd2;
    calls=fail_at=enable_count=0;now=enabled_at=duration=0;
    no_lock=abort_input=lose_lock=bad_readback=tx_level=tx_plan=comparison=false;
}
static bool payload_ok(uint64_t deadline) {assert(tx_level && deadline>now);sleep_ms(674);return true;}
static bool payload_abort(uint64_t deadline) {(void)deadline;return false;}
static bool payload_timeout(uint64_t deadline) {(void)deadline;sleep_ms(2000);clock_deadline_callback(1,NULL);assert(!tx_level);return true;}
int main(void) {
    reset();tx_plan=true;assert(clock_window_run(true,false,payload_ok));
    assert(!tx_level && duration==674000 && regs[3]==255);unsigned payload_calls=calls;
    for(unsigned i=1;i<=payload_calls;i++) {
        reset();tx_plan=true;fail_at=i;assert(!clock_window_run(true,false,payload_ok));
        assert(!tx_level && (regs[3]==255 || regs[16]==0x80));
    }
    reset();tx_plan=true;assert(!clock_window_run(true,false,payload_abort)&&!tx_level);
    reset();tx_plan=true;assert(!clock_window_run(true,false,payload_timeout)&&!tx_level);
    reset();tx_plan=true;alarm_fail=true;assert(!clock_window_run(true,false,payload_ok)&&!enable_count&&!tx_level);alarm_fail=false;

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
    reset();tx_plan=true;assert(tx_tone_test());assert(!tx_level&&duration==10000000);
    count=calls;
    for(unsigned i=1;i<=count;i++) {
        reset();tx_plan=true;fail_at=i;assert(!tx_tone_test());
        assert(!tx_level);assert(now<=10100000);
    }
    reset();tx_plan=true;no_lock=true;assert(!tx_tone_test()&&!tx_level&&!enable_count);
    reset();tx_plan=true;abort_input=true;assert(!tx_tone_test()&&!tx_level&&duration==0);
    reset();tx_plan=true;lose_lock=true;assert(!tx_tone_test()&&!tx_level&&duration==0);
    reset();tx_plan=comparison=true;assert(tx_comparison_test());assert(!tx_level&&duration==10000000);
    count=calls;
    for(unsigned i=1;i<=count;i++) {
        reset();tx_plan=comparison=true;fail_at=i;assert(!tx_comparison_test());
        assert(!tx_level && now<=10100000);
    }
    const unsigned loads[] = {6, 8, 10};
    for (unsigned n=0;n<3;n++) {
        reset();assert(clock_load_test(loads[n]));
        assert(regs[183]==0xd2 && !tx_level && duration==10000000);
        count=calls;
        for(unsigned i=1;i<=count;i++) {
            reset();fail_at=i;assert(!clock_load_test(loads[n]));
            assert(!tx_level && regs[183]==0xd2);
            assert(regs[3]==255 || regs[16]==0x80);
        }
    }
    reset();assert(!clock_load_test(7)&&enable_count==0);
    reset();abort_input=true;assert(!clock_load_test(6)&&regs[183]==0xd2);
    reset();no_lock=true;assert(!clock_load_test(8)&&regs[183]==0xd2);
    puts("PASS: clock timing, register plan, I2C fault sweep, lock/readback failures, abort, shutdown");
}
