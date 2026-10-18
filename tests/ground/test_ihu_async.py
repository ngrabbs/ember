"""Exercise delayed EPS completion against OFF, stop, expiry and target changes."""
import pathlib
import subprocess
import tempfile
import unittest
from test_can_addressing import SDK,DRIVER
from generate_c import generate
ROOT=pathlib.Path(__file__).resolve().parents[2]
CHECKS=r'''
int main(void){
 boot=11;can.ready=true;target_index=DR_COMMS_INDEX;peer=22;
 ip_init(&policy,IP_GROUND_TEST);ip_finish_boot(&policy,true,false,false);
 host_sensor_defer=true;
 command("output uhf_telem on");command("uhf eps");
 assert(sensor_job.active && !pending.active && !output.active);
 command("hello lte");assert(target_index==DR_COMMS_INDEX);
 command("mode nominal");assert(policy.mode==IP_SAFE);
 command("output uhf_telem off");command("output uhf_telem on");
 host_sensor.ok=true;host_sensor_defer=false;ihu_app_step(false);
 assert(!sensor_job.active && !pending.active && !output.active); /* OFF generation wins over a later ON. */
 host_sensor_defer=true;
 command("uhf run 60 10");uhf_run.stage=2;uhf_run.cycle=true;
 uhf_run_pump(fake_now);assert(sensor_job.active && uhf_run.stage==2);
 command("uhf stop");host_sensor.ok=true;host_sensor_defer=false;ihu_app_step(false);
 assert(!pending.active && !output.active && uhf_run.state==UR_STOPPED);
 host_sensor_defer=true;command("uhf run 60 10");uhf_run.stage=2;uhf_run.cycle=true;
 uhf_run_pump(fake_now);assert(sensor_job.active);
 command("uhf stop");host_sensor.ok=false;host_sensor_defer=false;ihu_app_step(false);
 assert(uhf_run.state==UR_STOPPED && !pending.active); /* A late failure cannot resurrect a stopped run as FAULT. */
 host_sensor_defer=true;command("uhf run 1 5");uhf_run.stage=2;uhf_run.cycle=true;
 uhf_run_pump(fake_now);assert(sensor_job.active);
 fake_now+=1000;host_sensor.ok=true;host_sensor_defer=false;ihu_app_step(false);
 assert(!pending.active && !output.active && uhf_run.state==UR_EXPIRED);
 host_sensor_defer=true;command("uhf run 60 10");uhf_run.stage=2;uhf_run.cycle=true;
 uhf_run_pump(fake_now);assert(sensor_job.active);
 host_sensor.ok=true;host_sensor_defer=false;ihu_app_step(false);
 assert(pending.active && output.active && queued().type==CF_UHF_SEND);
 assert(uhf_run.stage==3 && uhf_run.submitted==1); /* Advance once, after actual submission. */
 pending.active=false;output.active=false;memset(&uhf_client,0,sizeof(uhf_client));ur_stop(&uhf_run,UR_STOPPED);
 unsigned faults_before=fault_count;can.tx_fail=1;
 /* Worker snapshots can observe an error before the actor's TX pump. */
 pump_tx(fake_now);assert(fault_count==faults_before+1);pump_tx(fake_now);assert(fault_count==faults_before+1);
 puts("ASYNC_PASS");return 0;
}
'''
class AsyncEpsTests(unittest.TestCase):
    def test_delayed_completion_and_revocation(self):
        with tempfile.TemporaryDirectory() as temp:
            p=pathlib.Path(temp);(p/'sdk.h').write_text(SDK)
            for name in ['pico/stdlib.h','pico/stdio_usb.h','pico/unique_id.h','pico/rand.h','hardware/i2c.h']:
                h=p/name;h.parent.mkdir(exist_ok=True);h.write_text('#include "sdk.h"\n')
            (p/'build_identity.h').write_text('#define FW_VERSION "0.15.0"\n#define FW_MAJOR 0\n#define FW_MINOR 15\n#define FW_PATCH 0\n#define FW_DIRTY 0\n#define FW_GIT "0123456789012345678901234567890123456789"\n')
            generate(p/'wire.h')
            source=p/'test.c';source.write_text('#include <assert.h>\n#include "'+str(ROOT/'firmware/ihu/app.c')+'"\n'+DRIVER.split('int main(void)')[0]+CHECKS)
            binary=p/'test'
            subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror','-DIHU_HOST_TEST','-I'+str(p),'-I'+str(ROOT/'firmware/comms_transport'),str(source),str(ROOT/'firmware/shared/ember_protocol/protocol.c'),'-o',str(binary)],check=True)
            self.assertIn('ASYNC_PASS',subprocess.check_output([str(binary)],text=True))
