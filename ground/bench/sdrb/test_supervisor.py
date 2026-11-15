"""Linux process-owner tests with fake children; never opens CAN or UHD."""
import json,os,signal,subprocess,sys,tempfile,time,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
MOCK='''import json,os,signal,sys,time
from pathlib import Path
out=Path(sys.argv[sys.argv.index('--output')+1]);out.mkdir()
def stop(*_):
    (out/'final.json').write_text(json.dumps({'graceful':True}));sys.exit(0)
signal.signal(signal.SIGTERM,stop)
time.sleep(float(os.environ.get('MOCK_READY_DELAY','0')))
print('UHF_RX_READY mock',flush=True)
start=time.monotonic()
while True:
    if os.environ.get('MOCK_FAIL') and time.monotonic()-start>1:sys.exit(7)
    if os.environ.get('MOCK_QUOTA') and not (out/'big').exists():(out/'big').write_bytes(bytes(17*1024**2))
    time.sleep(.05)
'''
class Supervisor(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.app=self.root/'app';self.app.mkdir();(self.app/'libresdr_live_rx.py').write_text(MOCK)
        self.config=self.root/'config.json';self.config.write_text(json.dumps(dict(role='ground',state_dir=str(self.root/'state'),runs_dir=str(self.root/'runs'),app_dir=str(self.app),ember_dir=str(self.root),keep_runs=1,quota_mib=16)))
    def cli(self,command,env=None,check=True,**kwargs):
        return subprocess.run([sys.executable,str(HERE/'supervisor.py'),command,'--config',str(self.config),*kwargs.get('args',[])],env=env,capture_output=True,text=True,timeout=20,check=check)
    def state(self):return json.loads((self.root/'state/status.json').read_text())
    def until(self,state):
        end=time.monotonic()+5
        while time.monotonic()<end:
            if self.state()['state']==state:return self.state()
            time.sleep(.05)
        self.fail(self.state())
    def tearDown(self):
        self.cli('stop',check=False);self.tmp.cleanup()
    def test_start_exclusive_stop_and_manual_restart(self):
        self.cli('start');first=self.state();self.assertEqual(first['state'],'RUNNING')
        self.assertNotEqual(self.cli('start',check=False).returncode,0)
        self.cli('stop');self.assertEqual(self.state()['state'],'STOPPED')
        self.assertTrue(json.loads((Path(first['run'])/'receiver/final.json').read_text())['graceful'])
        self.cli('start');self.assertNotEqual(first['run_id'],self.state()['run_id']);self.cli('stop')
        self.cli('start');self.assertEqual(len(list((self.root/'runs').iterdir())),2)
    def test_component_failure_stops_without_retry(self):
        self.cli('start',env=dict(os.environ,MOCK_FAIL='1'));s=self.until('FAILED')
        self.assertIn('receiver exited unexpectedly: 7',s['error']);time.sleep(.3)
        self.assertEqual(len(list((self.root/'runs').iterdir())),1)
        self.cli('start');self.assertEqual(self.state()['state'],'RUNNING')
    def test_storage_quota_fails_and_cleans_child(self):
        self.cli('start',env=dict(os.environ,MOCK_QUOTA='1'),check=False)
        s=self.until('FAILED');self.assertIn('quota',s['error'])
        self.assertTrue((Path(s['run'])/'receiver/final.json').exists())
    def test_owner_death_signals_child_and_stale_control_can_restart(self):
        self.cli('start');s=self.state();child=s['children']['receiver']['pid']
        os.kill(s['pid'],signal.SIGKILL)
        end=time.monotonic()+5
        while time.monotonic()<end and not (Path(s['run'])/'receiver/final.json').exists():time.sleep(.05)
        self.assertTrue((Path(s['run'])/'receiver/final.json').exists())
        self.assertEqual(json.loads(self.cli('status').stdout)['state'],'OWNER_LOST')
        self.cli('start');self.assertEqual(self.state()['state'],'RUNNING')
    def test_non_socket_control_is_preserved(self):
        state=self.root/'state';state.mkdir(mode=0o700);(state/'control.sock').write_text('preserve')
        self.assertNotEqual(self.cli('start',check=False).returncode,0)
        self.assertEqual((state/'control.sock').read_text(),'preserve')
    def test_finite_lease_is_after_readiness(self):
        self.cli('start',env=dict(os.environ,MOCK_READY_DELAY='.3'),args=['--seconds','1'])
        self.assertEqual(self.state()['state'],'RUNNING');started=time.monotonic()
        s=self.until('STOPPED');self.assertEqual(s['reason'],'lease_expired')
        self.assertGreater(time.monotonic()-started,.7)
    def test_sdrb_component_fault_stops_radio_before_can(self):
        config=json.loads(self.config.read_text());config.update(role='sdrb',can_monitor=str(self.app/'unused.py'));self.config.write_text(json.dumps(config))
        mock=self.app/'component.py'
        mock.write_text('''import signal,sys,time
from pathlib import Path
name,out=sys.argv[1:];p=Path(out);p.mkdir()
def stop(*_):
    (p/'stopped').write_text(str(time.monotonic()));sys.exit(0)
signal.signal(signal.SIGTERM,stop)
print('READY',flush=True)
if name=='forward':time.sleep(.5);sys.exit(7)
while True:time.sleep(.05)
''')
        launcher=self.root/'launch.py'
        launcher.write_text('''import argparse,sys
from pathlib import Path
sys.path.insert(0,sys.argv[1]);import supervisor
def plan(c,run):
    return [(name,[sys.executable,str(Path(c['app_dir'])/'component.py'),name,str(run/name)],'READY') for name in ('radio','can','forward')]
supervisor.commands=plan
sys.exit(supervisor.serve(argparse.Namespace(config=Path(sys.argv[2]),transmit=True,seconds=3)))
''')
        r=subprocess.run([sys.executable,str(launcher),str(HERE),str(self.config)],capture_output=True,text=True,timeout=10)
        self.assertEqual(r.returncode,1);s=self.state();self.assertIn('forward exited unexpectedly',s['error'])
        run=Path(s['run']);self.assertLess(float((run/'radio/stopped').read_text()),float((run/'can/stopped').read_text()))

if __name__=='__main__':unittest.main()
