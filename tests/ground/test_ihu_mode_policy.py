"""Mode/output policy through the real IHU parser, transport gates and quiet replies."""
import pathlib
import subprocess
import tempfile
import unittest
from test_can_addressing import SDK, DRIVER
from generate_c import generate

ROOT=pathlib.Path(__file__).resolve().parents[2]
CHECKS=r'''
int main(void){
 boot=11;can.ready=true;
 ip_init(&policy,IP_GROUND_TEST);assert(policy.mode==IP_BOOT && !policy.outputs);
 for(unsigned c=0;c<IP_OUTPUT_COUNT;c++)assert(ip_set_output(&policy,c,true));
 ip_finish_boot(&policy,true,false,false);assert(policy.mode==IP_SAFE && !policy.outputs);
 log_output("UNSOLICITED_SENTINEL\n");
 housekeeping_pump(fake_now);assert(fault_count==1); /* EPS failure recorded without output. */
 command("outputs");command("mode");
 assert(!ip_set_output(&policy,IP_CLI_TELEM,true));fake_now+=5000;
 pending.active=true;housekeeping_pump(fake_now);assert(housekeeping.last!=fake_now);pending.active=false;
 housekeeping_pump(fake_now);assert(housekeeping.last==fake_now && fault_count==1);
 assert(!ip_set_output(&policy,IP_CLI_TELEM,false));
 assert(!ip_set_output(&policy,IP_UMB_TELEM,true));fake_now+=5000;housekeeping_pump(fake_now);
 assert(!ip_set_output(&policy,IP_UMB_TELEM,false));
 command("hello transceiver");assert(pending.active && pending.console && queued().type==UL_HELLO && target_index==DR_COMMS_INDEX);
 pending.active=false;output.active=false;can.pending=false;
 command("hello comms");assert(pending.active && pending.console && queued().type==UL_HELLO && target_index==DR_COMMS_INDEX);
 ul_packet p=pending.packet;p.sender=22;p.type=UL_HELLO_ACK;output.active=false;
 receive(&p);assert(!pending.active && peer==22);
 command("uhf heartbeat");assert(!pending.active && !output.active);
 command("uhf comms firmware");assert(!pending.active && !output.active);
 target_index=DR_LTE_INDEX;peer=33;
 command("eps lte");assert(!pending.active);
 /* Gate the transport itself, not only the console spelling. */
 submit(CF_SEND_PACKET,NULL,0);assert(!pending.active);
 target_index=DR_COMMS_INDEX;peer=22;
 for(unsigned c=0;c<IP_OUTPUT_COUNT;c++){
  assert(!ip_set_output(&policy,c,true));
  for(unsigned j=0;j<IP_OUTPUT_COUNT;j++)assert(ip_enabled(&policy,j)==(j==c));
  assert(!ip_set_output(&policy,c,false));
 }
 command("output uhf_telem on");
 command("uhf heartbeat");assert(pending.active);ul_packet u=queued();
 ul_packet admitted={0};uhf_reply(&u,22,CF_UHF_ADMITTED,UHF_OK,&admitted);
 output.active=false;receive(&admitted);assert(!pending.active);
 uhf_reply(&u,22,CF_UHF_RESULT,UHF_OK,&admitted);receive(&admitted);assert(!uc_count(&uhf_client));
 command("uhf transceiver firmware");assert(pending.active && queued().type==CF_UHF_FIRMWARE && !queued().size);
 u=queued();uhf_reply(&u,22,CF_UHF_ADMITTED,UHF_OK,&admitted);output.active=false;receive(&admitted);
 assert(!pending.active && uc_count(&uhf_client)==1);
 uhf_reply(&u,22,CF_UHF_RESULT,UHF_OK,&admitted);receive(&admitted);assert(!uc_count(&uhf_client));
 target_index=DR_LTE_INDEX;command("uhf comms firmware");assert(!pending.active);target_index=DR_COMMS_INDEX;
 command("uhf comms firmware");assert(pending.active);command("output uhf_telem off");
 assert(!pending.active && !output.active);memset(&uhf_client,0,sizeof(uhf_client));
 command("output uhf_telem on");
 command("uhf run 120 10");assert(uhf_run.state==UR_RUNNING);
 command("output uhf_telem off");assert(uhf_run.state==UR_STOPPED && !policy.outputs);
 pending.active=true;pending.packet.type=CF_UHF_SEND;output.active=true;
 command("output uhf_telem off");assert(!pending.active && !output.active);
 for(unsigned mode=IP_STARTUP;mode<=IP_NOMINAL;mode++){
  assert(!ip_set_output(&policy,IP_UMB_TELEM,true));
  assert(!ip_mode(&policy,mode));assert(policy.mode==mode && !policy.outputs);
 }
 command("mode nominal");assert(policy.mode==IP_NOMINAL && policy.configuration==IP_GROUND_TEST);
 command("output cli_debug on extra");assert(!policy.outputs);
 command("output all on");assert(!policy.outputs);
 command("telem on");command("lte queue on");assert(!pending.active && !policy.outputs);
 ip_init(&policy,IP_FLIGHT);ip_finish_boot(&policy,true,false,false);
 assert(policy.mode==IP_SAFE && !strcmp(policy.reason,"HISTORY_UNAVAILABLE"));
 for(unsigned c=0;c<IP_OUTPUT_COUNT;c++)assert(ip_set_output(&policy,c,true));
 assert(ip_mode(&policy,IP_STARTUP));assert(ip_mode(&policy,IP_COMMISSIONING));assert(ip_mode(&policy,IP_NOMINAL));
 command("hello payload");command("lte 60");assert(!pending.active && !output.active);
 assert(!ip_mode(&policy,IP_SAFE));
 ip_finish_boot(&policy,false,true,true);assert(policy.mode==IP_SAFE);
 ip_finish_boot(&policy,true,true,false);assert(policy.mode==IP_SAFE);
 ip_finish_boot(&policy,true,true,true);assert(policy.mode==IP_STARTUP); /* classification only: no routine enabled */
 assert(!ip_test(&policy) && !policy.outputs);
 ip_init(&policy,99);ip_finish_boot(&policy,true,true,true);assert(policy.mode==IP_SAFE);
 ip_init(&policy,IP_GROUND_TEST);ip_finish_boot(&policy,true,false,false);
 assert(!ip_set_output(&policy,IP_CLI_DEBUG,true));assert(!ip_set_output(&policy,IP_UMB_DEBUG,true));
 log_output("BOTH_DEBUG_SENTINEL\n");
 ip_init(&policy,IP_GROUND_TEST);assert(!policy.outputs);
 puts("POLICY_PASS");return 0;
}
'''
class IhuModePolicy(unittest.TestCase):
    def test_real_parser_and_gates(self):
        with tempfile.TemporaryDirectory() as temp:
            p=pathlib.Path(temp);(p/'sdk.h').write_text(SDK)
            for name in ['pico/stdlib.h','pico/stdio_usb.h','pico/unique_id.h','pico/rand.h','hardware/uart.h','hardware/i2c.h']:
                h=p/name;h.parent.mkdir(exist_ok=True);h.write_text('#include "sdk.h"\n')
            (p/'build_identity.h').write_text('#define FW_VERSION "0.14.0"\n#define FW_MAJOR 0\n#define FW_MINOR 14\n#define FW_PATCH 0\n#define FW_DIRTY 0\n#define FW_GIT "0123456789012345678901234567890123456789"\n')
            generate(p/'wire.h')
            source=p/'test.c'
            source.write_text('#include <assert.h>\n#define main embedded_main\n#include "'+str(ROOT/'firmware/ihu/main.c')+'"\n#undef main\n'+DRIVER.split('int main(void)')[0]+CHECKS)
            binary=p/'test'
            subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror','-DROLE_IHU=1','-I'+str(p),'-I'+str(ROOT/'firmware/comms_transport'),str(source),str(ROOT/'firmware/usb_bench/protocol.c'),'-o',str(binary)],check=True)
            output=subprocess.check_output([str(binary)],text=True)
            self.assertNotIn('UNSOLICITED_SENTINEL',output)
            self.assertIn('outcome=CAN_HELLO_CONFIRMED',output)
            self.assertIn('outcome=RF_TX_COMPLETE',output)
            self.assertIn('CLI_DEBUG BOTH_DEBUG_SENTINEL',output)
            self.assertIn('UMB_DEBUG BOTH_DEBUG_SENTINEL',output)
            self.assertIn('CLI_TELEM mode=SAFE',output)
            self.assertIn('\"profile\":\"ihu-health-v1\"',output)
            self.assertIn('POLICY_PASS',output)
