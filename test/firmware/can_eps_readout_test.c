#include <assert.h>
#include <string.h>
#include "hardware/i2c.h"
static i2c_inst_t bus;
#define i2c0 (&bus)
#define GPIO_FUNC_I2C 3
static void i2c_init(i2c_inst_t *i,unsigned hz) {assert(i==i2c0 && hz==100000);}
static void gpio_set_function(unsigned pin,unsigned fn) {assert((pin==4 || pin==5) && fn==GPIO_FUNC_I2C);}
static void gpio_pull_up(unsigned pin) {assert(pin==4 || pin==5);}
#include "../../firmware/can_feather_bench/eps_readout.h"
static unsigned pointer,reads;
static int fail=-1;
static bool corrupt;
int i2c_write_timeout_us(i2c_inst_t *i,uint8_t addr,const uint8_t *p,size_t n,bool nostop,uint32_t timeout) {
    assert(i==i2c0 && addr==0x68 && n==1 && nostop && timeout==10000);
    pointer=p[0];return 1; /* Any register write would fail this assertion. */
}
int i2c_read_timeout_us(i2c_inst_t *i,uint8_t addr,uint8_t *p,size_t n,bool nostop,uint32_t timeout) {
    assert(i==i2c0 && addr==0x68 && n==3 && !nostop && timeout==10000);++reads;
    if((int)pointer==fail)return -1;
    p[0]=0xff;p[1]=0xff;
    /* Independent polynomial long division; golden VIN frame has PEC 0x2e. */
    const uint8_t bytes[]={0xd0,(uint8_t)pointer,0xd1,p[0],p[1]};unsigned crc=0;
    for(unsigned j=0;j<sizeof bytes;++j) {
        crc^=(unsigned)bytes[j]<<8;
        for(unsigned k=0;k<8;++k) {crc<<=1;if(crc&0x10000)crc^=0x10700;}
        crc&=0xffff;
    }
    p[2]=crc>>8;if(pointer==0x3b)assert(p[2]==0x2e);
    if(corrupt)p[0]^=1;return 3;
}
int main(void) {
    eps_bus_init();ltc4162_raw_t r,old;uint8_t failed=0;
    assert(eps_read(&r,&failed) && reads==19 && r.vin==65535 && r.telemetry_status==65535);
    memset(&r,0x55,sizeof r);old=r;fail=0x41;
    assert(!eps_read(&r,&failed) && failed==0x41 && !memcmp(&r,&old,sizeof r));
    fail=-1;corrupt=true;
    assert(!eps_read(&r,&failed) && failed==0x14 && !memcmp(&r,&old,sizeof r));
    corrupt=false;assert(eps_read(&r,&failed));return 0;
}
