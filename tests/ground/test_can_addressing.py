"""Exercise the actual Feather command/receive handlers with mocked hardware."""
import pathlib
import subprocess
import sys
import tempfile
import unittest
ROOT=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'ground/ember'))
from generate_c import generate
from codec import decode

SDK=r'''
#pragma once
#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>
#include <string.h>
#define GPIO_OUT 1
#define GPIO_FUNC_UART 2
#define GPIO_FUNC_I2C 3
#define UART_PARITY_NONE 0
#define PICO_ERROR_TIMEOUT -1
#define PICO_UNIQUE_BOARD_ID_SIZE_BYTES 8
#define uart0 0
#define i2c1 1
static uint32_t fake_now=20000;
static inline uint32_t get_absolute_time(void){return fake_now;}
static inline uint32_t to_ms_since_boot(uint32_t t){return t;}
static inline bool stdio_usb_connected(void){return true;}
static inline void stdio_init_all(void){}
static inline void pico_get_unique_board_id_string(char *p,size_t n){if(n) *p=0;}
static inline uint32_t get_rand_32(void){return 123;}
static inline void gpio_init(int p){(void)p;}
static inline void gpio_set_dir(int p,int d){(void)p;(void)d;}
static inline void gpio_set_function(int p,int f){(void)p;(void)f;}
static inline void gpio_pull_up(int p){(void)p;}
static inline void gpio_put(int p,bool b){(void)p;(void)b;}
static inline void sleep_us(int n){(void)n;}
static inline int getchar_timeout_us(int n){(void)n;return -1;}
static inline void uart_init(int p,int b){(void)p;(void)b;}
static inline void uart_putc_raw(int p,int b){(void)p;(void)b;}
static inline void uart_write_blocking(int p,const uint8_t *b,size_t n){(void)p;(void)b;(void)n;}
static inline void uart_set_hw_flow(int p,bool a,bool b){(void)p;(void)a;(void)b;}
static inline void uart_set_format(int p,int a,int b,int c){(void)p;(void)a;(void)b;(void)c;}
static inline void uart_set_fifo_enabled(int p,bool b){(void)p;(void)b;}
static inline bool uart_is_readable(int p){(void)p;return false;}
static inline int uart_getc(int p){(void)p;return 0;}
static inline void i2c_init(int p,int b){(void)p;(void)b;}
static inline int i2c_write_timeout_us(int p,int a,const uint8_t*b,size_t n,bool s,int t){(void)p;(void)a;(void)b;(void)n;(void)s;(void)t;return -1;}
static inline int i2c_read_timeout_us(int p,int a,uint8_t*b,size_t n,bool s,int t){(void)p;(void)a;(void)b;(void)n;(void)s;(void)t;return -1;}
'''
DRIVER=r'''
bool mcp_init(mcp_state*s){s->ready=true;return true;}
bool mcp_mode(mcp_state*s,uint8_t m){(void)s;(void)m;return true;}
bool mcp_send(mcp_state*s,const cf_frame*f){(void)s;(void)f;return true;}
void mcp_poll_tx(mcp_state*s,uint32_t now){(void)s;(void)now;}
bool mcp_receive(mcp_state*s,cf_frame*f){(void)s;(void)f;return false;}
uint8_t mcp_register(uint8_t r){(void)r;return 0;}
static ul_packet queued(void){ul_packet p={0};ul_reader r={0};bool found=false;for(size_t i=0;i<output.size;i++)if(ul_feed(&r,output.wire[i],fake_now,&p))found=true;assert(found);return p;}
int main(void){
 boot=11;can.ready=true;
#if ROLE_IHU
 ip_init(&policy,IP_GROUND_TEST);ip_finish_boot(&policy,true,false,false);
 command("output uhf_telem on");command("output lte_telem on");
 command("hello comms");assert(TX_ID==0x710 && RX_ID==0x711 && pending.active);
 ul_packet ack=pending.packet;ack.type=UL_HELLO_ACK;ack.sender=22;
 output.active=false;receive(&ack);assert(peer==22 && devices[DR_COMMS_INDEX].boot==22);
 command("hello lte");assert(TX_ID==0x720 && RX_ID==0x721 && pending.active && !peer);
 bool selected=target_lte;command("hello comms");assert(target_lte==selected); /* busy */
 ack=pending.packet;ack.type=UL_HELLO_ACK;ack.sender=33;
 cf_frame frame;uint8_t wire[UL_WIRE_MAX];size_t n=ul_encode(&ack,wire);
 for(unsigned i=0;i<(n+3)/4;i++){assert(cf_fragment(wire,n,CF_COMMS_ID,1,i,&frame));assert(!cf_feed(&fragments,&frame,RX_ID,fake_now));}
 assert(!fragments.used);output.active=false;receive(&ack);
 assert(peer==33 && devices[DR_COMMS_INDEX].boot==22 && devices[DR_LTE_INDEX].boot==33);
 submit(CF_UHF_SEND,NULL,0);assert(!pending.active && !output.active);
 command("uhf run 120 10");assert(uhf_run.state!=UR_RUNNING);
 command("lte firmware");assert(pending.active && queued().type==UL_FIRMWARE_INFO);
 ack=pending.packet;ack.type=UL_FIRMWARE_INFO_ACK;ack.sender=33;ack.size=FI_SIZE;
 fi_payload(ack.payload,33,100);output.active=false;receive(&ack);assert(identities[0].valid);
 command("hello comms");ack=pending.packet;ack.type=UL_HELLO_ACK;ack.sender=22;output.active=false;receive(&ack);
 assert(peer==22);command("lte status");assert(!pending.active);
 command("uhf lte firmware");assert(pending.active && queued().type==CF_UHF_SEND);
 assert(ul_u16(queued().payload+W_MESSAGE_ID)==W_ID_LTE_CAN_FIRMWARE);
 assert(native_telemetry_valid(queued().payload,queued().size,boot));
 ul_packet encoded=queued();printf("IDENTITY_PACKET ");for(unsigned i=0;i<encoded.size;i++)printf("%02x",encoded.payload[i]);puts("");
 output.active=false;pending.active=false;memset(&uhf_client,0,sizeof(uhf_client));
 fake_now+=180001;command("uhf lte firmware");assert(!pending.active);

 command("hello payload");assert(TX_ID==CF_PAYLOAD_REQUEST_ID && RX_ID==CF_PAYLOAD_REPLY_ID && !peer);
 ack=pending.packet;ack.type=UL_HELLO_ACK;ack.sender=44;output.active=false;receive(&ack);
 assert(peer==44 && devices[DR_PAYLOAD_INDEX].boot==44);
 command("payload ident");assert(pending.active && queued().type==UL_FIRMWARE_INFO);
 ack=pending.packet;ack.type=UL_FIRMWARE_INFO_ACK;ack.sender=44;ack.size=FI_SIZE;
 fi_payload(ack.payload,44,100);output.active=false;receive(&ack);assert(!pending.active);
 assert(ul_u32(identities[0].payload+24)==33); /* Payload identity must not overwrite LTE identity. */
 command("payload status");assert(pending.active && queued().type==PL_STATUS);
 ack=pending.packet;ack.type=PL_STATUS_ACK;ack.sender=44;ack.size=PL_REPORT_SIZE;
 memset(ack.payload,0,ack.size);ack.payload[0]=1;ack.payload[1]=4;ack.payload[2]=1;
 ul_p32(ack.payload+4,45);output.active=false;receive(&ack);assert(pending.active); /* wrong boot */
 ul_p32(ack.payload+4,44);receive(&ack);assert(!pending.active);
 command("payload heartbeat");assert(pending.active && queued().type==PL_HEARTBEAT);
 ack=pending.packet;ack.type=PL_HEARTBEAT_ACK;ack.sender=44;ack.size=PL_REPORT_SIZE;
 memset(ack.payload,0,ack.size);ack.payload[0]=1;ack.payload[1]=4;ack.payload[2]=1;
 ul_p32(ack.payload+4,44);output.active=false;receive(&ack);assert(!pending.active);
 command("payload fire-check");assert(pending.active && queued().type==PL_FIRE_CHECK);
 ack=pending.packet;ack.type=PL_FIRE_RESULT;ack.sender=44;ack.size=PL_FIRE_SIZE;
 memset(ack.payload,0,ack.size);ack.payload[0]=1;ack.payload[2]=1;ul_p32(ack.payload+4,44);ul_p32(ack.payload+12,1);
 output.active=false;ack.payload[1]=2;receive(&ack);assert(pending.active);
 ack.payload[1]=0;receive(&ack);assert(!pending.active);
 /* Real RF handler must handshake, ask payload, then return correlated native result. */
 uint8_t tc[32]={0};ul_p16(tc,0x1900);ul_p16(tc+2,0xc000);ul_p16(tc+4,25);tc[6]=1;tc[10]=1;tc[11]=2;
 ul_p16(tc+8,1028);ul_p32(tc+12,77);ul_p32(tc+16,88);ul_p32(tc+20,99);ul_p16(tc+30,ul_crc(tc,30));
 assert(up_native_fire(tc,32));tc[31]^=1;assert(!up_native_fire(tc,32));tc[31]^=1;
 ul_packet rf={.version=1,.type=UP_PING,.sender=55,.origin=55,.request=7,.size=32};memcpy(rf.payload,tc,32);
 uint8_t rw[UL_WIRE_MAX];size_t rn=ul_encode(&rf,rw);cf_frame ff;
 memset(&discovery,0,sizeof(discovery));discovery.active=true; /* addressed command preempts discovery */
 for(unsigned i=0;i<(rn+3)/4;i++){assert(cf_fragment(rw,rn,UP_REQUEST_ID,7,i,&ff));uplink_receive(&ff,fake_now);}
 assert(!discovery.active && fire_uplink.active && pending.active && queued().type==UL_HELLO);
 ack=pending.packet;ack.type=UL_HELLO_ACK;ack.sender=44;output.active=false;receive(&ack);
 assert(fire_uplink.active && pending.active && queued().type==PL_FIRE_CHECK);
 ack=pending.packet;ack.type=PL_FIRE_RESULT;ack.sender=44;ack.size=PL_FIRE_SIZE;
 memset(ack.payload,0,ack.size);ack.payload[0]=1;ack.payload[2]=1;ul_p32(ack.payload+4,44);ul_p32(ack.payload+12,2);
 output.active=false;receive(&ack);assert(!fire_uplink.active && !pending.active && output.route==UP_REPLY_ID);
 ul_packet rr=queued();assert(up_fire_completed(&rr,&rf));rr.payload[32]=2;assert(!up_fire_completed(&rr,&rf));
 output.active=false;
 for(unsigned i=0;i<(rn+3)/4;i++){assert(cf_fragment(rw,rn,UP_REQUEST_ID,7,i,&ff));uplink_receive(&ff,fake_now);}
 assert(!pending.active); /* no second execution of same RF transaction */
 submit(CF_SEND_PACKET,NULL,0);submit(CF_CHAIN,NULL,0);submit(CF_UHF_SEND,NULL,0);
 assert(!pending.active && !output.active);
 command("hello comms");ack=pending.packet;ack.type=UL_HELLO_ACK;ack.sender=22;
 output.active=false;receive(&ack);assert(peer==22);
 memset(devices,0,sizeof(devices));
 dr_seen(&devices[0],fake_now,0);dr_seen(&devices[2],fake_now-30000,22);
 devices[3].state=DR_FAULT;
 command("uhf devices");encoded=queued();assert(native_telemetry_valid(encoded.payload,encoded.size,boot));
 printf("DEVICE_PACKET ");for(unsigned i=0;i<encoded.size;i++)printf("%02x",encoded.payload[i]);puts("");
 output.active=false;pending.active=false;memset(&uhf_client,0,sizeof(uhf_client));
 uhf_run.state=UR_RUNNING;uhf_run.cycle=true;uhf_run.stage=2;
 discovery.next=3;discovery.last=0;devices_pump(fake_now);assert(!discovery.active);
 uhf_run.stage=4;devices_pump(fake_now);assert(discovery.active && discovery.index==3);
 dr_status wrap={0};dr_seen(&wrap,UINT32_MAX-10,44);dr_age(&wrap,30000);assert(wrap.state==DR_STALE);

#else
 assert(TX_ID==0x721 && RX_ID==0x720);
 ul_packet query={.version=1,.type=UL_FIRMWARE_INFO,.origin=22,.sender=22,.request=99};
 receive(&query);ul_packet ack=queued();assert(ack.type==UL_FIRMWARE_INFO_ACK && ack.sender==11);
 assert(fi_valid(ack.payload,ack.size) && ul_u32(ack.payload+24)==11 && !chain.active);
 output.active=false;query.type=CF_MODEM_FIRMWARE;receive(&query);assert(chain.active && chain.uart.type==UL_HELLO);
 ul_packet w=chain.uart;w.type=UL_HELLO_ACK;w.sender=44;uart_receive(&w);
 assert(chain.uart.type==UL_FIRMWARE_INFO && chain.active);
 w=chain.uart;w.type=UL_FIRMWARE_INFO_ACK;w.sender=44;w.size=FI_SIZE;fi_payload(w.payload,44,777);uart_receive(&w);
 ack=queued();assert(!chain.active && ack.type==CF_MODEM_FIRMWARE_ACK && ul_u32(ack.payload+24)==44);
 cf_frame q,r;assert(dr_request(2,1,22,&q));assert(!dr_respond(&q,DR_LTE_NODE,boot,&r));
 assert(dr_request(3,1,22,&q));assert(dr_respond(&q,DR_LTE_NODE,boot,&r));assert(r.id==0x703);
#endif
 return 0;
}
'''
class AddressingTests(unittest.TestCase):
 def test_real_handlers_both_roles(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=pathlib.Path(tmp);(p/'sdk.h').write_text(SDK)
   for name in ['pico/stdlib.h','pico/stdio_usb.h','pico/unique_id.h','pico/rand.h','hardware/uart.h','hardware/i2c.h']:
    h=p/name;h.parent.mkdir(exist_ok=True);h.write_text('#include "sdk.h"\n')
   (p/'build_identity.h').write_text('#define FW_VERSION "0.8.0"\n#define FW_MAJOR 0\n#define FW_MINOR 8\n#define FW_PATCH 0\n#define FW_DIRTY 0\n#define FW_GIT "0123456789012345678901234567890123456789"\n')
   generate(p/'wire.h')
   source=p/'test.c';source.write_text('#include <assert.h>\n#define main embedded_main\n#include "'+str(ROOT/'firmware/ihu/main.c')+'"\n#undef main\n'+DRIVER)
   for role in (0,1):
    binary=p/f'role{role}'
    subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror',f'-DROLE_IHU={role}','-I'+str(p),'-I'+str(ROOT/'firmware/comms_transport'),str(source),str(ROOT/'firmware/shared/ember_protocol/protocol.c'),'-o',str(binary)],check=True)
    output=subprocess.check_output([str(binary)],text=True)
    if role:
     wire=next(line.split()[1] for line in output.splitlines() if line.startswith('IDENTITY_PACKET '))
     decoded=decode(bytes.fromhex(wire))
     self.assertEqual(decoded['name'],'LTE_CAN_FIRMWARE')
     self.assertEqual(decoded['header']['source_boot_id'],11)
     self.assertEqual(decoded['payload']['reported_boot_id'],33)
     self.assertEqual(decoded['payload']['reported_uptime_ms'],100)
     self.assertEqual(decoded['payload']['version_minor'],8)
     self.assertEqual(decoded['payload']['observation_age_ms'],0)

     wire=next(line.split()[1] for line in output.splitlines() if line.startswith('DEVICE_PACKET '))
     packet=decode(bytes.fromhex(wire));fields=packet['payload']
     self.assertEqual(packet['name'],'DEVICE_STATUS')
     self.assertEqual(fields['eps_state'],1)
     self.assertEqual(fields['comms_state'],2)
     self.assertEqual(fields['comms_age_ms'],30000)
     self.assertEqual(fields['lte_state'],3)
     self.assertEqual(fields['payload_seen'],0)
     self.assertEqual(fields['payload_age_ms'],4294967295)
