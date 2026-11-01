"""Exercise the real actor's read-only query, frozen bank and reset scheduling."""
import pathlib,subprocess,tempfile,unittest
from test_can_addressing import SDK,DRIVER
from generate_c import generate
ROOT=pathlib.Path(__file__).resolve().parents[2]
CHECKS=r'''
static ul_packet request(unsigned id,unsigned arg){
 ul_packet p={.version=1,.type=UP_PING,.sender=22,.origin=22,.request=id};
 p.size=id==3?33:id==5?36:32;uint8_t *b=p.payload;
 ul_p16(b,0x1900);ul_p16(b+2,0xc001);ul_p16(b+4,p.size-7);b[6]=1;
 ul_p16(b+8,id);b[10]=1;b[11]=2;ul_p32(b+12,7);ul_p32(b+16,id);ul_p32(b+20,8);
 ul_p16(b+28,p.size-32);if(id==3)b[30]=(uint8_t)arg;if(id==5)ul_p32(b+30,arg);
 ul_p16(b+p.size-2,ul_crc(b,p.size-2));return p;
}
int main(void){
 boot=11;can.ready=true;ember_init(&uplink_engine,boot);
 ip_init(&policy,IP_GROUND_TEST);ip_finish_boot(&policy,true,false,false);
 ul_packet p=request(3,1);assert(up_native_cdh(p.payload,p.size));
 cdh_receive(&p);ul_packet reply=queued();assert(up_status_completed(&reply,&p));
 assert(policy.mode==IP_SAFE && policy.outputs==0);output.active=false;
 p=request(3,255);cdh_receive(&p);reply=queued();assert(up_cdh_rejected(&reply,&p));
 assert(reply.payload[32]==1 && ul_u16(reply.payload+33)==2 && policy.mode==IP_SAFE && !policy.outputs);
 output.active=false;p=request(4,0);cdh_receive(&p);assert(cdh.active && cdh.count==1 && !output.active);
 for(unsigned i=0;i<4;i++){fake_now+=1000;cdh_pump(fake_now);}
 assert(cdh.valid && !cdh.active && cdh.count==5 && cdh.id==1);
 reply=queued();assert(up_records_completed(&reply,&p));uint8_t original[80];memcpy(original,reply.payload+38,80);
 output.active=false;cdh_receive(&p);reply=queued();assert(cdh.id==1 && !memcmp(reply.payload+38,original,80));
 output.active=false;fake_now+=60001;p=request(5,1);cdh_receive(&p);reply=queued();
 assert(up_records_completed(&reply,&p) && !memcmp(reply.payload+38,original,80));
 assert(ul_u32(reply.payload+24)-ul_u32(reply.payload+104)>=60000);
 output.active=false;p=request(5,2);cdh_receive(&p);reply=queued();assert(up_cdh_rejected(&reply,&p));
 assert(cdh.id==1 && cdh.valid && !memcmp(cdh.records,original,80));
 output.active=false;p=request(4,0);ul_p32(p.payload+16,99);ul_p16(p.payload+30,ul_crc(p.payload,30));
 cdh_receive(&p);assert(cdh.active && cdh.id==2);fake_now+=1101;cdh_pump(fake_now);
 assert(!cdh.active && !cdh.valid);reply=queued();assert(up_cdh_rejected(&reply,&p));
 output.active=false;p=request(6,0);policy.mode=IP_NOMINAL;cdh_receive(&p);reply=queued();assert(up_cdh_rejected(&reply,&p));
 assert(!reboot_scheduled);output.active=false;policy.mode=IP_SAFE;cdh_receive(&p);reply=queued();
 assert(up_reboot_scheduled(&reply,&p) && reboot_scheduled && host_reboots==0);
 output.active=false;fake_now+=4999;cdh_pump(fake_now);assert(!host_reboots);
 fake_now++;cdh_pump(fake_now);assert(host_reboots==1 && !reboot_scheduled);
 puts("CDH_PASS: actual actor valid/invalid query, frozen capture, exact delayed retrieval, duplicate suppression, timing failure and reset interlock");return 0;
}
'''
class CdhCapture(unittest.TestCase):
 def test_actual_actor(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=pathlib.Path(tmp);(p/'sdk.h').write_text(SDK)
   for name in ['pico/stdlib.h','pico/stdio_usb.h','pico/unique_id.h','pico/rand.h','hardware/i2c.h']:
    f=p/name;f.parent.mkdir(exist_ok=True);f.write_text('#include "sdk.h"\n')
   (p/'build_identity.h').write_text('#define FW_VERSION "0.16.0"\n#define FW_MAJOR 0\n#define FW_MINOR 16\n#define FW_PATCH 0\n#define FW_DIRTY 0\n#define FW_GIT "0123456789012345678901234567890123456789"\n')
   generate(p/'wire.h');src=p/'test.c'
   src.write_text('#include <assert.h>\n#include "'+str(ROOT/'firmware/ihu/app.c')+'"\n'+DRIVER.split('int main(void)')[0]+CHECKS)
   subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror','-DIHU_HOST_TEST','-I'+str(p),'-I'+str(ROOT/'firmware/comms_transport'),str(src),str(ROOT/'firmware/shared/ember_protocol/protocol.c'),'-o',str(p/'test')],check=True)
   self.assertIn('CDH_PASS',subprocess.check_output([str(p/'test')],text=True))
