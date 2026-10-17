"""Bench bridge correlation, unknown outcomes and isolated Yamcs generation."""
import importlib.util
from pathlib import Path
import struct
import sys
import tempfile
import time
import unittest
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'ground/ember'))
from codec import encode,decode
from payload_bridge import Bridge,Console,UnknownOutcome,observed


class FakeConsole:
    boot=11;uptime=100;sampled=time.monotonic()
    def __init__(self):self.calls=0;self.unknown=False
    def command(self,text):return ''
    def execute(self,name,size,on_submit):
        self.calls+=1;on_submit()
        if self.unknown:raise UnknownOutcome('timeout')
        raw=bytes([1,0,1,0])+struct.pack('>3I',42,200,1) if name=='PAYLOAD_FIRE_CHECK' else bytes(range(size)) if name=='PAYLOAD_PING' else bytes([1,4,1,0])+struct.pack('>6I',42,200,3,2,0,0)
        return raw,42,5


def command(name='PAYLOAD_PING',transaction=7,**payload):
    return encode(name,sequence=1,source=1,target=2,transaction_epoch=8,transaction_id=transaction,
                  source_boot_id=8,uptime_ms=0,payload=payload)


class PayloadGroundTests(unittest.TestCase):
    def test_correlated_ihu_results_and_duplicate_no_execution(self):
        console=FakeConsole();packets=[];bridge=Bridge(console,packets.append)
        wire=command(bytes=32);bridge.handle(wire)
        decoded=list(map(decode,packets))
        self.assertEqual([p['name'] for p in decoded],['COMMAND_RESPONSE','PAYLOAD_PING_RESULT','COMMAND_RESPONSE'])
        self.assertEqual([decoded[i]['payload']['stage'] for i in (0,2)],[0,2])
        self.assertTrue(all(p['header']['transaction_epoch']==8 and p['header']['transaction_id']==7 for p in decoded))
        self.assertEqual(decoded[1]['payload']['reported_boot_id'],42)
        bridge.handle(wire);self.assertEqual(console.calls,1)
        bridge.handle(command(bytes=33));self.assertEqual(console.calls,1)
        bridge.handle(command('PAYLOAD_STATUS_QUERY',transaction=9))
        self.assertEqual(decode(packets[-2])['payload']['report_kind'],1)

    def test_fire_result_is_correlated_stub_and_duplicates_do_not_repeat(self):
        console=FakeConsole();packets=[];bridge=Bridge(console,packets.append)
        wire=command('PAYLOAD_FIRE_CHECK');bridge.handle(wire);bridge.handle(wire)
        self.assertEqual(console.calls,1)
        r=decode(packets[1]);self.assertEqual(r['name'],'PAYLOAD_FIRE_RESULT')
        self.assertEqual(r['payload']['result'],0);self.assertEqual(r['payload']['execution_mode'],1)
        for bad in (bytes(16), bytes([1,2,1,0])+struct.pack('>3I',42,0,1),
                    bytes([1,0,1,0])+struct.pack('>3I',43,0,1)):
            with self.assertRaises(UnknownOutcome):observed('PAYLOAD_FIRE_CHECK',bad,42,0,1)

    def test_after_dispatch_timeout_remains_unknown(self):
        console=FakeConsole();console.unknown=True;packets=[];bridge=Bridge(console,packets.append)
        wire=command(bytes=8);bridge.handle(wire)
        self.assertEqual(len(packets),1)
        self.assertEqual(decode(packets[0])['payload']['stage'],0)
        bridge.handle(wire);self.assertEqual(console.calls,1)

    def test_bad_arguments_and_report_identity(self):
        console=FakeConsole();packets=[];bridge=Bridge(console,packets.append)
        bridge.handle(command(bytes=241))
        self.assertEqual(console.calls,0)
        self.assertEqual(decode(packets[0])['payload']['reason'],2)
        with self.assertRaises(UnknownOutcome):observed('PAYLOAD_STATUS_QUERY',bytes(28),42,0,1)
        with self.assertRaises(UnknownOutcome):observed('PAYLOAD_IDENT',bytes(32),42,0,1)

    def test_target_switch_retries_only_explicit_refusal(self):
        class SelectionConsole(Console):
            def __init__(self, refusal):self.refusal=refusal;self.calls=[]
            def command(self,text,*args):
                self.calls.append(text)
                if text=='hello payload' and self.calls.count(text)==1:raise self.refusal
                if text=='ping 1':return 'RESULT request=1 outcome=CAN_ECHO_MATCHED peer=42 bytes=1 hex=00'
                return ''
        console=SelectionConsole(RuntimeError('REJECT reason=BUSY_TARGET_SWITCH'))
        self.assertEqual(console.execute('PAYLOAD_PING',1,lambda:None)[0],b'\x00')
        self.assertEqual(console.calls.count('hello payload'),2)
        console=SelectionConsole(UnknownOutcome('ambiguous reply'))
        with self.assertRaises(UnknownOutcome):console.execute('PAYLOAD_PING',1,lambda:None)
        self.assertEqual(console.calls.count('hello payload'),1)
        self.assertNotIn('ping 1',console.calls)

    def test_prepare_is_idempotent_and_preserves_existing_sources(self):
        spec=importlib.util.spec_from_file_location('prepare_payload',ROOT/'ground/yamcs/prepare_payload.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as temp:
            runtime=Path(temp);config=runtime/'src/main/yamcs/etc';config.mkdir(parents=True)
            (runtime/'src/main/yamcs/mdb').mkdir()
            old=config/'yamcs.ember-uhf.yaml'
            body='services: []\ndataLinks: []\nmdb:\n  - type: xtce\n    args:\n      file: mdb/ember-uhf.xml\n'
            old.write_text(body);(config/'yamcs.yaml').write_text('instances:\n  - ember-uhf\n')
            original=runtime/'src/main/java/com/example/ember/WireProfile.java';original.parent.mkdir(parents=True);original.write_text('preserve deployed source')
            module.prepare(runtime);first=(config/'yamcs.ember-payload.yaml').read_bytes()
            module.prepare(runtime)
            self.assertEqual((config/'yamcs.ember-payload.yaml').read_bytes(),first)
            self.assertEqual((config/'yamcs.yaml').read_text().count('  - ember-payload\n'),1)
            self.assertEqual(old.read_text(),body)
            self.assertEqual(original.read_text(),'preserve deployed source')

    def test_payload_mdb_has_only_payload_commands(self):
        from generate_mdb import generate,NS
        with tempfile.TemporaryDirectory() as temp:
            generate(temp,command_filter={'PAYLOAD_PING','PAYLOAD_IDENT','PAYLOAD_STATUS_QUERY','PAYLOAD_HEARTBEAT_QUERY'})
            tree=ET.parse(Path(temp)/'ember.xml')
            names={n.attrib['name'] for n in tree.findall('.//{'+NS+'}MetaCommand')}
            self.assertEqual(names,{'PAYLOAD_PING','PAYLOAD_IDENT','PAYLOAD_STATUS_QUERY','PAYLOAD_HEARTBEAT_QUERY'})

class SerialEpsMonitor(unittest.TestCase):
    def test_eps_and_commands_share_one_console_with_provenance(self):
        import json
        from payload_bridge import EpsMonitor
        sample=json.loads((ROOT/'system/ground_station/evidence/ltc4162-input-10v7-20261001.json').read_text())[0]
        class SharedConsole(FakeConsole):
            def __init__(self):super().__init__();self.order=[]
            def command(self,text,**kwargs):self.order.append(text);return json.dumps(sample)
            def execute(self,name,size,on_submit):self.order.append(name);return super().execute(name,size,on_submit)
        console=SharedConsole();packets=[]
        monitor=EpsMonitor(console,packets.append,cells=2,rsnsb=.01,rsnsi=.01)
        monitor.poll();Bridge(console,packets.append).handle(command(bytes=8));monitor.poll()
        self.assertEqual(console.order,['eps json','PAYLOAD_PING','eps json'])
        power=decode(packets[-1]);self.assertEqual(power['name'],'POWER_STATUS')
        self.assertEqual(power['payload']['provenance'],1)
        self.assertEqual(power['payload']['readout_valid'],1)
        self.assertEqual(power['payload']['readout_count'],2)

    def test_disconnect_propagates_for_service_reconnect(self):
        from payload_bridge import EpsMonitor
        class Disconnected:
            def command(self,*a,**k):raise OSError('disconnected')
        monitor=EpsMonitor(Disconnected(),lambda p:None,cells=2,rsnsb=.01,rsnsi=.01)
        with self.assertRaises(OSError):monitor.poll()


if __name__=='__main__':unittest.main()
