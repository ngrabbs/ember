"""Host fault injection and ordered-PCB pin-map checks; no hardware access."""
import json
import pathlib
import subprocess
import tempfile

src = pathlib.Path(__file__).resolve().parents[1]
repo = src.parents[1]
pads = json.loads((repo / 'hardware/comms/verification/review_20261004_final/pads-all.json').read_text())
expected = {'J6': {4:'CAN_A_STBY',5:'CAN_B_STBY',6:'CAN_SPI_MISO',9:'CAN_SPI_SCK',10:'CAN_SPI_MOSI',11:'CAN_A_RESETn',12:'CAN_B_RESETn',14:'TX_ACTIVE',15:'RX_ACTIVE',16:'3V3_IND',19:'CAN_A_CSn',20:'CAN_B_CSn'}, 'J7': {9:'RX_BASEBAND',14:'I2C_SCL',15:'I2C_SDA',16:'CAN_B_INTn',17:'CAN_A_INTn',20:'BPSK_DATA'}}
for ref, mapping in expected.items():
    actual = {int(p['number']): p['net'].split('/')[-1] for p in pads[ref]['pads']}
    for pin, net in mapping.items():
        assert actual[pin] == net, (ref, pin, actual[pin], net)

stub = r'''
#pragma once
#include <stdbool.h>
#include <stdint.h>
#include <assert.h>
#include <setjmp.h>
#define GPIO_OUT 1
#define GPIO_FUNC_I2C 3
#define GPIO_FUNC_SPI 1
#define spi0 0
#define SPI_CPOL_0 0
#define SPI_CPHA_0 0
#define SPI_MSB_FIRST 0
static bool bad_can, alias_cs, drop_frame, corrupt_frame, refuse_mode;
static uint8_t regs[2][128];
static bool bad_id, bad_dlc, extended_frame, remote_frame;
#define i2c0 0
static int levels[30], directions[30], initialized[30], call, fail_at;
static uint8_t readback = 255;
static jmp_buf done;
static void gpio_init(unsigned p) {initialized[p]=1; levels[p]=-1;}
static void gpio_put(unsigned p, bool v) {assert(initialized[p]); levels[p]=v;}
static void gpio_set_dir(unsigned p, int v) {assert(levels[p]>=0); directions[p]=v;}
static void gpio_set_function(unsigned p, int v) {assert(((p==20||p==21)&&v==3)||((p==4||p==6||p==7)&&v==1));}
static void i2c_init(int i, int hz) {assert(i==0&&hz==100000);}
static int i2c_write_timeout_us(int i,int a,const uint8_t *b,int n,bool hold,int t) {
 assert(i==0&&a==0x60&&t==2000); ++call;
 assert((n==2&&b[0]==3&&b[1]==255&&!hold)||(n==1&&b[0]==3&&hold));
 return call==fail_at?-1:n;
}
static int i2c_read_timeout_us(int i,int a,uint8_t*b,int n,bool hold,int t) {
 assert(i==0&&a==0x60&&n==1&&!hold&&t==2000); ++call; *b=readback;
 return call==fail_at?-1:n;
}
static void spi_init(int i,int hz) {assert(i==0&&hz==1000000);}
static void spi_set_format(int i,int bits,int pol,int pha,int order) {assert(i==0&&bits==8&&pol==0&&pha==0&&order==0);}
static void sleep_us(int us) {assert(us==2);}
static int spi_write_read_blocking(int i,const uint8_t *tx,uint8_t *rx,int n) {
 assert(i==0&&(((n==3&&(tx[0]==3||tx[0]==2))||(n==15&&tx[0]==3))||(n==4&&tx[0]==5))&&tx[1]<128);
 assert((levels[14]==0&&levels[15]==1)||(levels[15]==0&&levels[14]==1));
 assert(levels[3]==1&&levels[10]==0);
 if(levels[2]==0) assert((regs[0][14]&0xe0)==0x60||(regs[0][14]&0xe0)==0);
 if(levels[2]==0) assert(!(regs[0][0x30]&8)&&!(regs[0][0x40]&8)&&!(regs[0][0x50]&8));
 unsigned which=alias_cs?0:(levels[14]==0?0:1);
 uint8_t *r=regs[which];
 if(tx[0]==5) {r[tx[1]]=(r[tx[1]]&~tx[2])|(tx[3]&tx[2]);return n;}
 if(tx[0]==3) {for(int k=2;k<n;k++) rx[k]=bad_can?255:r[tx[1]+k-2];return n;}
 unsigned addr=tx[1]; uint8_t v=tx[2];
 if(addr==0x0f) {
  assert((v&0xe0)==0x80||(v&0xe0)==0x40||(v&0xe0)==0x60||(v&0xe0)==0);
  if(!refuse_mode) {r[0x0e]=v&0xe0;r[addr]=v;}
 } else {
  r[addr]=v;
  if(addr==0x30&&(v&8)) {
   assert((r[0x0e]&0xe0)==0x40);
   if(!drop_frame) {
    for(unsigned j=0;j<13;j++) r[0x61+j]=r[0x31+j];
    r[0x63]=0x3b; r[0x64]=0xf6; r[0x62]|=3; /* Inapplicable EID bits. */
    if(corrupt_frame) r[0x66]^=1;
    if(bad_id) r[0x61]^=1;
    if(bad_dlc) r[0x65]=7;
    if(extended_frame) r[0x62]|=8;
    if(remote_frame) r[0x62]|=16;
    r[0x2c]|=5;r[0x30]&=~8;
   }
  }
 }
 return n;
}
static uint64_t time_us_64(void) {static uint64_t now; return now+=10000;}
static int getchar_timeout_us(unsigned t) {assert(t==0);return -1;}
static uint32_t get_rand_32(void) {return 12345;}
static void adc_init(void) {}
static void adc_gpio_init(unsigned p) {assert(p==27);}
static void adc_select_input(unsigned p) {assert(p==1);}
static unsigned adc_read(void) {return 2048;}
static void stdio_init_all(void) {}
static void sleep_ms(int ms) {assert(ms==1000||ms==10||ms==1||ms==2); if(ms==1000) longjmp(done,1);}
'''
harness = r'''
#define main firmware_main
#include "main.c"
#undef main
int main(void) {
 for (int fault=0; fault<=3; ++fault) {
  call=0; fail_at=fault;
  assert(disable_clocks()==(fault==0));
 }
 call=0; fail_at=0; readback=0; assert(!disable_clocks());
 call=0; readback=255; assert(disable_clocks());
 call=0; fail_at=1; assert(!disable_clocks());
 regs[0][14]=regs[1][14]=128; regs[0][15]=regs[1][15]=135;
 if (!setjmp(done)) firmware_main();
 unsigned low[]={10,11,16,6,7}, high[]={2,3,8,9,14,15,12};
 for(unsigned i=0;i<sizeof(low)/sizeof(*low);i++) assert(directions[low[i]]&&levels[low[i]]==0);
 for(unsigned i=0;i<sizeof(high)/sizeof(*high);i++) assert(directions[high[i]]&&levels[high[i]]==1);
 assert(configuration_mode(0x80,0x87));
 assert(!configuration_mode(0xff,0xff));
 assert(!configuration_mode(0,0));
 assert(!configuration_mode(0x80,0));
 assert(independent_registers());
 alias_cs=true; assert(!independent_registers()); alias_cs=false;
 assert(loopback(14,0xa1)==0); assert(loopback(15,0xb2)==0);
 drop_frame=true; assert(loopback(14,0xa1)==3); drop_frame=false;
 corrupt_frame=true; assert(loopback(14,0xa1)==4); corrupt_frame=false;
 bad_id=true; assert(loopback(14,0xa1)==4); bad_id=false;
 bad_dlc=true; assert(loopback(14,0xa1)==4); bad_dlc=false;
 extended_frame=true; assert(loopback(14,0xa1)==4); extended_frame=false;
 remote_frame=true; assert(loopback(14,0xa1)==4); remote_frame=false;
 assert(can_mode(14,0x80));
 refuse_mode=true; assert(loopback(14,0xa1)==2); refuse_mode=false;
 assert(!can_mode(14,0xa0));
 assert(loopback(14,0xa1)==0);
 assert(listen_a(false, false)); assert(listen_a(true, false)); assert(levels[2]==1&&levels[3]==1);
 bad_can=true;
 if (!setjmp(done)) firmware_main();
 assert(levels[8]==0&&levels[9]==0&&levels[2]==1&&levels[3]==1);
 assert(!directions[4]&&!directions[18]&&!directions[19]);
 return 0;
}
'''
with tempfile.TemporaryDirectory() as directory:
    root = pathlib.Path(directory)
    (root/'stub.h').write_text(stub)
    for name in ['pico/stdlib.h', 'hardware/adc.h', 'hardware/i2c.h', 'hardware/spi.h', 'pico/rand.h']:
        path = root/name
        path.parent.mkdir(exist_ok=True)
        path.write_text('#include "stub.h"\n')
    (root/'check.c').write_text(harness)
    subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror','-I'+str(root),'-I'+str(src),'-I'+str(src.parent/'comms_transport'),str(root/'check.c'),'-o',str(root/'check')],check=True)
    subprocess.run([str(root/'check')],check=True)
print('PASS: ordered pad nets, safe output initialization, clock-disable faults, CS independence, loopback payload/timeout/mode faults')
