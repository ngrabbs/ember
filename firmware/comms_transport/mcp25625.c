#include "mcp25625.h"
#include "pico/stdlib.h"
#include "hardware/spi.h"
#define CS 19
#define RESET 18
#define STANDBY 16
static void select(void) {gpio_put(CS,0);}
static void release(void) {gpio_put(CS,1);}
uint8_t mcp_register(uint8_t reg) {
    uint8_t cmd[2]={0x03,reg},value;
    select();spi_write_blocking(spi1,cmd,2);spi_read_blocking(spi1,0,&value,1);release();return value;
}
static void write_regs(uint8_t reg,const uint8_t *data,size_t size) {
    uint8_t cmd[2]={0x02,reg};select();spi_write_blocking(spi1,cmd,2);
    spi_write_blocking(spi1,data,size);release();
}
static void write_reg(uint8_t reg,uint8_t value) {write_regs(reg,&value,1);}
static void modify(uint8_t reg,uint8_t mask,uint8_t value) {
    uint8_t cmd[4]={0x05,reg,mask,value};select();spi_write_blocking(spi1,cmd,4);release();
}
bool mcp_mode(mcp_state *s,uint8_t mode) {
    if(s->pending || (mode!=0 && mode!=0x40 && mode!=0x80))return false;
    // One-shot: a missing bus ACK must not cause indefinite hardware retries.
    write_reg(0x0f,(uint8_t)(mode|0x08));
    uint64_t until=time_us_64()+100000;
    while(time_us_64()<until) {
        if((mcp_register(0x0e)&0xe0)==mode)return true;
        sleep_us(100);
    }
    s->ready=false;return false;
}
bool mcp_init(mcp_state *s) {
    memset(s,0,sizeof(*s));
    gpio_init(CS);gpio_put(CS,1);gpio_set_dir(CS,GPIO_OUT);
    gpio_init(STANDBY);gpio_put(STANDBY,0);gpio_set_dir(STANDBY,GPIO_OUT);
    gpio_init(17);gpio_put(17,1);gpio_set_dir(17,GPIO_OUT); // TX0 RTS inactive.
    gpio_init(22);gpio_set_dir(22,GPIO_IN);gpio_pull_up(22);
    gpio_init(23);gpio_set_dir(23,GPIO_IN);
    gpio_init(RESET);gpio_put(RESET,0);gpio_set_dir(RESET,GPIO_OUT);
    sleep_ms(1);gpio_put(RESET,1);sleep_ms(10);
    spi_init(spi1,1000000);spi_set_format(spi1,8,SPI_CPOL_0,SPI_CPHA_0,SPI_MSB_FIRST);
    gpio_set_function(14,GPIO_FUNC_SPI);gpio_set_function(15,GPIO_FUNC_SPI);gpio_set_function(8,GPIO_FUNC_SPI);
    uint8_t cmd=0xc0;select();spi_write_blocking(spi1,&cmd,1);release();sleep_ms(10);
    if((mcp_register(0x0e)&0xe0)!=0x80)return false;
    // 16 MHz oscillator, 500 kbit/s: 16 TQ, SJW 1, sample at 9/16.
    write_reg(0x2a,0x00);write_reg(0x29,0xf0);write_reg(0x28,0x86);
    write_reg(0x2b,0);write_reg(0x2c,0);write_reg(0x0c,0);write_reg(0x0d,0);
    write_reg(0x60,0x64);write_reg(0x70,0x60); // Receive all; RX0 rollover to RX1.
    write_reg(0x30,0);write_reg(0x40,0);write_reg(0x50,0);
    s->ready=mcp_register(0x2a)==0 && mcp_register(0x29)==0xf0 && mcp_register(0x28)==0x86;
    // Remain in configuration until an explicit USB `normal` or `selftest`.
    return s->ready;
}
void mcp_poll_tx(mcp_state *s,uint32_t now) {
    if(!s->pending)return;
    uint8_t ctrl=mcp_register(0x30);
    if(!(ctrl&8)) {
        if(ctrl&0x70)++s->tx_fail;else if(mcp_register(0x2c)&4)++s->tx_ok;else ++s->tx_fail;
        modify(0x2c,4,0);s->pending=false;
    } else if((uint32_t)(now-s->sent_at)>=50) {
        modify(0x0f,0x10,0x10);modify(0x30,8,0);modify(0x0f,0x10,0);
        s->pending=false;++s->tx_timeout;
    }
}
bool mcp_send(mcp_state *s,const cf_frame *f) {
    uint8_t mode=mcp_register(0x0e)&0xe0;
    if(!s->ready || s->pending || (mode!=0 && mode!=0x40) || f->id>0x7ff || f->size>8)return false;
    uint8_t buf[13]={0};buf[0]=(uint8_t)(f->id>>3);buf[1]=(uint8_t)(f->id<<5);
    buf[4]=f->size;memcpy(buf+5,f->data,f->size);
    write_reg(0x30,0);modify(0x2c,4,0);write_regs(0x31,buf,5+f->size);
    uint8_t cmd=0x81;select();spi_write_blocking(spi1,&cmd,1);release();
    s->pending=true;s->sent_at=to_ms_since_boot(get_absolute_time());return true;
}
bool mcp_receive(mcp_state *s,cf_frame *f) {
    uint8_t errors=mcp_register(0x2d);
    if(errors&0xc0) {++s->rx_overflow;modify(0x2d,0xc0,0);}
    uint8_t flags=mcp_register(0x2c);unsigned which;
    if(flags&1)which=0;else if(flags&2)which=1;else return false;
    uint8_t reg=which?0x71:0x61,cmd[2]={0x03,reg},buf[13];
    select();spi_write_blocking(spi1,cmd,2);spi_read_blocking(spi1,0,buf,sizeof(buf));release();
    modify(0x2c,(uint8_t)(1u<<which),0);++s->rx;
    if((buf[1]&0x18) || (buf[4]&0x40) || (buf[4]&0xf)>8) {++s->rx_bad;return false;}
    f->id=(uint16_t)((buf[0]<<3)|(buf[1]>>5));f->size=buf[4]&0xf;memcpy(f->data,buf+5,f->size);return true;
}
