#include <assert.h>
#include <math.h>
#include <string.h>
#include "drivers/ltc4162.h"
static uint16_t regs[128];
static unsigned pointer, writes, reads, held;
static int fail_reg=-1;
static bool lock_ok=true;
bool ihu_i2c0_lock(unsigned ms) { assert(ms==1000 && !held); if(!lock_ok)return false; held=1; return true; }
void ihu_i2c0_unlock(void) { assert(held); held=0; }
void sleep_ms(unsigned ms) { assert(held && ms==100); }
int i2c_write_timeout_us(i2c_inst_t *i, uint8_t addr,const uint8_t *p,size_t n,bool nostop,uint32_t timeout) {
 (void)i; assert(held && addr==0x68 && timeout==10000);
 assert(n==1 || n==3); pointer=p[0]; assert(pointer<128);
 if(n==1) { assert(nostop); return 1; }
 assert(!nostop); writes++; regs[pointer]=(uint16_t)p[1]|((uint16_t)p[2]<<8); return 3;
}
int i2c_read_timeout_us(i2c_inst_t *i,uint8_t addr,uint8_t *p,size_t n,bool nostop,uint32_t timeout) {
 (void)i; assert(held && addr==0x68 && n==2 && !nostop && timeout==10000); reads++;
 if((int)pointer==fail_reg)return -1;
 p[0]=regs[pointer]&255; p[1]=regs[pointer]>>8; return 2;
}
static void close_to(float a,float b) { assert(fabsf(a-b)<.001f); }
int main(void) {
 i2c_inst_t i={0}; ltc4162_telemetry_t t, sentinel;
 memset(&sentinel,0x55,sizeof sentinel); t=sentinel;
 regs[0x43]=2; regs[0x4a]=1; regs[0x3a]=21322; regs[0x3b]=65535;
 regs[0x3c]=4952; regs[0x3d]=64947; regs[0x3e]=81; regs[0x3f]=13252;
 regs[0x40]=9078; regs[0x41]=1234;
 assert(ltc4162_present(&i,0x68));
 assert(ltc4162_read_telemetry(&i,0x68,&t));
 close_to(t.v_bat,8.2047056f); close_to(t.v_in,-.001649f); close_to(t.v_out,8.185656f);
 close_to(t.i_bat_ma,-86.3474f); close_to(t.i_in_ma,11.8746f); close_to(t.die_temp_c,20.518f);
 assert(t.raw.thermistor_voltage==9078 && t.raw.bsr==1234 && writes==0 && !held);
 regs[0x4a]=0; t=sentinel; assert(!ltc4162_read_telemetry(&i,0x68,&t)); assert(!memcmp(&t,&sentinel,sizeof t));
 ltc4162_raw_t raw; assert(ltc4162_read_raw(&i,0x68,&raw) && raw.telemetry_status==0);
 regs[0x4a]=1; regs[0x43]=0x0402; assert(!ltc4162_read_telemetry(&i,0x68,&t));
 regs[0x43]=3; assert(!ltc4162_read_telemetry(&i,0x68,&t));
 regs[0x43]=0; assert(ltc4162_read_telemetry(&i,0x68,&t));
 fail_reg=0x41; memset(&raw,0x55,sizeof raw); ltc4162_raw_t old=raw;
 assert(!ltc4162_read_raw(&i,0x68,&raw) && !memcmp(&raw,&old,sizeof raw) && !held);
 fail_reg=0x39; assert(!ltc4162_present(&i,0x68) && !held); fail_reg=-1;
 lock_ok=false; unsigned before=reads; assert(!ltc4162_read_raw(&i,0x68,&raw) && reads==before); lock_ok=true;
 regs[0x14]=0x802a;
#if IHU_EPS_ALLOW_CHARGER_WRITES
 assert(ltc4162_init(&i,0x68) && regs[0x14]==0x802e && writes==1);
#else
 assert(!ltc4162_init(&i,0x68)); assert(!ltc4162_kick(&i,0x68));
 assert(!ltc4162_set_jeita_enabled(&i,0x68,false)); assert(!ltc4162_set_ntc_bypass(&i,0x68,true));
 assert(writes==0 && regs[0x14]==0x802a);
#endif
 assert(!held); return 0;
}
