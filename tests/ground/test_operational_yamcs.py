"""Unified configuration, route exclusivity and preservation of legacy history."""
import importlib.util
from pathlib import Path
import re
import tempfile
import unittest
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('operational',ROOT/'ground/yamcs/prepare_operational.py')
op=importlib.util.module_from_spec(spec);spec.loader.exec_module(op)

class OperationalYamcs(unittest.TestCase):
    def test_consolidation_is_idempotent_and_routes_commands_once(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime=Path(temp);config=runtime/'src/main/yamcs/etc';config.mkdir(parents=True)
            (runtime/'src/main/yamcs/mdb').mkdir()
            (config/'yamcs.yaml').write_text('instances:\n  - ember\n  - ember-lte\n  - ember-uhf\n  - ember-payload\n  - myproject\nsecretKey: preserve\n')
            old='services: []\ndataLinks: []\nmdb: []\nstreamConfig:\n  tm:\n    - name: tm_realtime\n      processor: realtime\n  tc:\n    - name: tc_realtime\n      processor: realtime\nyamcs-web:\n  displayBucket: ember_displays\n'
            (config/'yamcs.ember.yaml').write_text(old)
            (config/'yamcs.ember-lte.yaml').write_text('legacy untouched')
            op.prepare(runtime);first=(config/'yamcs.ember.yaml').read_bytes()
            op.prepare(runtime);self.assertEqual(first,(config/'yamcs.ember.yaml').read_bytes())
            self.assertEqual((config/'yamcs.yaml').read_text(),'instances:\n  - ember\nsecretKey: preserve\n')
            self.assertEqual((config/'yamcs.ember-lte.yaml').read_text(),'legacy untouched')
            text=first.decode()
            for port in range(10016,10021):self.assertEqual(text.count('port: '+str(port)+'\n'),1)
            self.assertIn('stream: tc_payload',text);self.assertIn('stream: tc_usb',text)
            patterns=re.findall('tcPatterns: \\["(.*?)"\\]',text)
            for cmd in ('PING','REQUEST_STATUS','REQUEST_TELEMETRY','SET_PARAMETER','PAYLOAD_PING','PAYLOAD_IDENT','PAYLOAD_STATUS_QUERY','PAYLOAD_HEARTBEAT_QUERY'):
                self.assertEqual(sum(bool(re.fullmatch(p,'/ember/'+cmd)) for p in patterns),1)
            self.assertEqual(sum(bool(re.fullmatch(p,'/ember/UNROUTED')) for p in patterns),0)
            self.assertIn('resultDomain: usb',text);self.assertIn('resultDomain: spacecraft',text)
            tree=ET.parse(runtime/'src/main/yamcs/mdb/ember.xml')
            self.assertEqual(len(tree.findall('.//{'+op.NS+'}MetaCommand')),8)
            self.assertEqual(len(tree.findall('.//{'+op.NS+'}Parameter')),188)

    def test_legacy_history_has_no_hardware_routes(self):
        with tempfile.TemporaryDirectory() as temp:
            r=Path(temp);c=r/'src/main/yamcs/etc';c.mkdir(parents=True)
            (r/'src/main/yamcs/mdb').mkdir()
            body='services: []\ndataLinks: []\nmdb: []\nstreamConfig:\n  tc:\n    - name: tc_realtime\n      processor: realtime\nyamcs-web:\n  displayBucket: ember_displays\n'
            (c/'yamcs.ember.yaml').write_text(body)
            (c/'yamcs.ember-lte.yaml').write_text(body)
            (c/'yamcs.yaml').write_text('instances:\n  - ember\n  - ember-lte\n')
            op.prepare(r,('ember-lte',))
            history=(c/'yamcs.ember-lte.yaml').read_text()
            self.assertIn('dataLinks: []',history)
            self.assertIn('tcPatterns: ["(?!)"]',history)
            self.assertIn('  - ember-lte\n',(c/'yamcs.yaml').read_text())

    def test_native_lte_health_allowlist(self):
        from codec import encode,PacketError
        from lte_receiver import validate
        for name,payload in [('HEARTBEAT',{'mode':3,'configuration':1,'telemetry_period_ms':0}),
                             ('SYSTEM_STATUS',{'mode':3,'configuration':1,'telemetry_period_ms':0,'accepted_commands':1,'rejected_commands':0})]:
            packet=encode(name,sequence=1,source=2,target=1,source_boot_id=22,uptime_ms=100,payload=payload)
            self.assertEqual(validate(packet)['name'],name)
            bad=bytearray(packet);bad[-1]^=1
            with self.assertRaises(PacketError):validate(bad)
            transaction=encode(name,sequence=1,source=2,target=1,source_boot_id=22,uptime_ms=100,transaction_epoch=1,transaction_id=1,payload=payload)
            with self.assertRaises(PacketError):validate(transaction)
