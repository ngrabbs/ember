#include <assert.h>
#include <string.h>
#include "drivers/ltc4162.h"
static uint16_t regs[128];
static unsigned pointer,held,writes;
static int fail_write=-1;
static bool bad_pec;
bool ihu_i2c0_lock(unsigned ms) { assert(ms==1000 && !held);held=1;return true; }
void ihu_i2c0_unlock(void) { assert(held);held=0; }
void sleep_ms(unsigned ms) { (void)ms;assert(0); }
int i2c_write_timeout_us(i2c_inst_t *i,uint8_t a,const uint8_t *p,size_t n,bool ns,uint32_t t) {
 (void)i;assert(held&&a==0x68&&t==10000);pointer=p[0];assert(pointer<128);
 if(n==1){assert(ns);return 1;}
 assert(n==3&&!ns);writes++;if((int)pointer==fail_write)return -1;
 regs[pointer]=(uint16_t)p[1]|((uint16_t)p[2]<<8);return 3;
}
int i2c_read_timeout_us(i2c_inst_t *i,uint8_t a,uint8_t *p,size_t n,bool ns,uint32_t t) {
 (void)i;assert(held&&a==0x68&&n==3&&!ns&&t==10000);
 p[0]=regs[pointer]&255;p[1]=regs[pointer]>>8;
 const uint8_t b[]={0xd0,(uint8_t)pointer,0xd1,p[0],p[1]}; unsigned crc=0;
 for(unsigned j=0;j<5;j++){crc^=(unsigned)b[j]<<8;for(unsigned k=0;k<8;k++){crc<<=1;if(crc&0x10000)crc^=0x10700;}crc&=65535;}
 p[2]=(uint8_t)(crc>>8);if(bad_pec)p[2]^=1;return 3;
}
static void setup(i2c_inst_t *i) {
 memset(regs,0,sizeof regs);fail_write=-1;bad_pec=false;
 regs[0x29]=5;regs[0x1a]=31;regs[0x1b]=31;
 regs[0x43]=0x20e2;regs[0x4a]=1;regs[0x3a]=21280;regs[0x3b]=6477;
 regs[0x3f]=13500;regs[0x40]=500;
 assert(ltc4162_bench_recover(i,0x68));
 assert(regs[0x14]==44&&regs[0x29]==5&&regs[0x1a]==0);
 assert(regs[0x1f]==16117&&regs[0x24]==4970);
}
int main(void) {
 i2c_inst_t i={0};setup(&i);
 assert(ltc4162_bench_start(&i,0x68,100));
 assert(regs[0x14]==12&&regs[0x29]==4&&regs[0x1a]==0&&regs[0x1b]==23);
 assert(regs[0x1f]==32767&&regs[0x24]==1);
 assert(!ltc4162_bench_start(&i,0x68,1000)); /* cannot extend */
 assert(ltc4162_bench_service(&i,0x68,60099,false)&&regs[0x14]==12);
 assert(ltc4162_bench_service(&i,0x68,60100,false));
 assert(regs[0x14]==44&&regs[0x29]==5&&regs[0x1b]==31&&regs[0x24]==4970);
 setup(&i);assert(ltc4162_bench_start(&i,0x68,0xfffffff0u));
 assert(ltc4162_bench_service(&i,0x68,59984u,false)&&regs[0x14]==44); /* wrap */
 setup(&i);assert(ltc4162_bench_start(&i,0x68,0));
 assert(ltc4162_bench_service(&i,0x68,1,true)&&regs[0x14]==44);
 setup(&i);regs[0x3a]=22000;unsigned before=writes;
 assert(!ltc4162_bench_start(&i,0x68,0)&&writes==before);
 setup(&i);assert(ltc4162_bench_start(&i,0x68,0));regs[0x4a]=0;
 assert(ltc4162_bench_service(&i,0x68,1000,false)&&regs[0x14]==44);
 setup(&i);fail_write=0x24;assert(!ltc4162_bench_start(&i,0x68,0));assert(regs[0x14]==44);
 fail_write=-1;assert(ltc4162_bench_service(&i,0x68,1,true));
 setup(&i);bad_pec=true;before=writes;assert(!ltc4162_bench_start(&i,0x68,0)&&writes==before);
 bad_pec=false;
 setup(&i);assert(ltc4162_bench_start(&i,0x68,0));
 assert(ltc4162_bench_recover(&i,0x68)&&regs[0x14]==44&&regs[0x29]==5&&regs[0x24]==4970);
 assert(!held);return 0;
}
