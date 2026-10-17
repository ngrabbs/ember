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
static unsigned delayed_reads, data_high_count, idle_sleeps;
static bool main_running;
static bool data_test_active, console_abort;
static bool bad_can, alias_cs, drop_frame, corrupt_frame, refuse_mode;
static uint8_t regs[2][128];
static bool bad_id, bad_dlc, extended_frame, remote_frame;
#define i2c0 0
static int levels[30], directions[30], initialized[30], call, fail_at;
static uint8_t readback = 255;
static jmp_buf done;
static void gpio_init(unsigned p) {initialized[p]=1; levels[p]=-1;}
static void gpio_put(unsigned p, bool v) {assert(initialized[p]);
 if(data_test_active) {assert(p!=10 || !v); assert(p!=11 || !v); if(p==16 && v) ++data_high_count;}
 levels[p]=v;
 if((p==8||p==9)&&!v) {unsigned k=p==8?0:1;regs[k][14]=128;regs[k][15]=135;}
}
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
 if(tx[0]==3) {for(int k=2;k<n;k++) rx[k]=(bad_can||delayed_reads)?255:r[tx[1]+k-2];
 if(delayed_reads) --delayed_reads;return n;}
 unsigned addr=tx[1]; uint8_t v=tx[2];
 if(addr==0x0f) {
  assert((v&0xe0)==0x80||(v&0xe0)==0x40||(v&0xe0)==0x60||(v&0xe0)==0);
  if(!refuse_mode) {r[0x0e]=v&0xe0;r[addr]=v;}
 } else {
  r[addr]=v;
  if(addr==0x30&&(v&8)) {
   assert((r[0x0e]&0xe0)==0x40 || (r[0x0e]&0xe0)==0);
   if((r[0x0e]&0xe0)==0) {r[0x2c]|=4;r[0x30]&=~8;return n;}
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
static int getchar_timeout_us(unsigned t) {assert(t==0);return console_abort ? 1 : -1;}
typedef int alarm_id_t;
static alarm_id_t add_alarm_in_ms(unsigned ms, int64_t (*cb)(alarm_id_t,void*), void *u, bool past) {(void)ms;(void)cb;(void)u;(void)past;return 1;}
static bool cancel_alarm(alarm_id_t id) {(void)id;return true;}
static uint32_t get_rand_32(void) {return 12345;}
static void adc_init(void) {}
static void adc_gpio_init(unsigned p) {assert(p==27);}
static void adc_select_input(unsigned p) {assert(p==1);}
static unsigned adc_read(void) {return 2048;}
static void stdio_init_all(void) {}
static void sleep_ms(int ms) {assert(ms==1000||ms==10||ms==1||ms==2||ms==20||ms==200); if(ms==1000 || (ms==1 && main_running && ++idle_sleeps==1000)) longjmp(done,1);}
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
 main_running=true;idle_sleeps=0;
 if (!setjmp(done)) firmware_main();
 main_running=false;
 unsigned low[]={2,10,11,16,6,7}, high[]={3,8,9,14,15,12};
 for(unsigned i=0;i<sizeof(low)/sizeof(*low);i++) assert(directions[low[i]]&&levels[low[i]]==0);
 for(unsigned i=0;i<sizeof(high)/sizeof(*high);i++) assert(directions[high[i]]&&levels[high[i]]==1);
 assert((regs[0][14]&0xe0)==0);assert(rf_bus_close());
 data_test_active=true; data_high_count=0; call=0; fail_at=0;
 data_input_test(); assert(data_high_count>0 && levels[16]==0 && levels[10]==0);
 data_high_count=0; call=0; fail_at=1;
 data_input_test(); assert(data_high_count==0 && levels[16]==0);
 fail_at=0; console_abort=true;
 data_input_test(); assert(data_high_count==0 && levels[16]==0);
 console_abort=false; data_test_active=false;
 assert(configuration_mode(0x80,0x87));
 assert(!configuration_mode(0xff,0xff));
 assert(!configuration_mode(0,0));
 assert(!configuration_mode(0x80,0));
 assert(rf_bus_open());
 cf_frame discovery_query;assert(dr_request(DR_COMMS_NODE,77,999,&discovery_query));
 regs[0][0x61]=(uint8_t)(discovery_query.id>>3);regs[0][0x62]=(uint8_t)(discovery_query.id<<5);
 regs[0][0x65]=8;memcpy(&regs[0][0x66],discovery_query.data,8);regs[0][0x2c]|=1;
 assert(can_idle_poll());assert(levels[10]==0 && levels[11]==0 && levels[2]==0);
 assert(regs[0][0x31]==((DR_RESPONSE_BASE+DR_COMMS_NODE)>>3));
 assert(ul_u16(&regs[0][0x38])==77 && ul_u32(&regs[0][0x3a])==12345);
 assert(rf_bus_close());
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
 assert(rf_service_window(true));assert(rf_queue.count==0 && levels[10]==0 && levels[2]==1);
 console_abort=true;assert(rf_service_window(true));console_abort=false;
 assert(rf_service());assert(rf_queue.count==0 && levels[10]==0 && levels[2]==1);
 assert(listen_a(false, false, false)); assert(listen_a(true, false, false)); assert(listen_a(true, false, true)); assert(levels[2]==1&&levels[3]==1);
 unsigned attempts; uint8_t last[4];
 delayed_reads=8; assert(wait_can_ready(&attempts,last)&&attempts==2);
 assert(levels[2]==1&&levels[3]==1);
 bad_can=true;
 assert(!wait_can_ready(&attempts,last)&&attempts==20);
 assert(levels[8]==0&&levels[9]==0&&last[0]==255&&last[2]==255);
 bad_can=false; assert(wait_can_ready(&attempts,last)&&attempts==1);
 bad_can=true;
 main_running=true;idle_sleeps=0;
 if (!setjmp(done)) firmware_main();
 main_running=false;
 assert(levels[8]==0&&levels[9]==0&&levels[2]==1&&levels[3]==1);
 assert(!directions[4]&&!directions[18]&&!directions[19]);
 return 0;
}
'''
with tempfile.TemporaryDirectory() as directory:
    root = pathlib.Path(directory)
    (root/'stub.h').write_text(stub)
    (root/'build_identity.h').write_text('#define FW_MAJOR 0u\n#define FW_MINOR 22u\n#define FW_PATCH 0u\n#define FW_DIRTY 1u\n#define FW_VERSION "0.22.0"\n#define FW_GIT "0123456789012345678901234567890123456789"\n')
    for name in ['pico/stdlib.h', 'hardware/adc.h', 'hardware/i2c.h', 'hardware/spi.h', 'pico/rand.h']:
        path = root/name
        path.parent.mkdir(exist_ok=True)
        path.write_text('#include "stub.h"\n')
    (root/'check.c').write_text(harness)
    subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror','-I'+str(root),'-I'+str(src),'-I'+str(src.parent/'comms_transport'),str(root/'check.c'),'-o',str(root/'check')],check=True)
    subprocess.run([str(root/'check')],check=True)
print('PASS: ordered pad nets, safe output initialization, clock-disable faults, CS independence, loopback payload/timeout/mode faults')
