"""Environment isolation, idempotent preparation and preserved history."""
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
    def fixture(self,r):
        c=r/'src/main/yamcs/etc';c.mkdir(parents=True)
        (r/'src/main/yamcs/mdb').mkdir()
        body='services: []\ndataLinks: []\nmdb: []\nstreamConfig:\n  tm:\n    - name: tm_realtime\n      processor: realtime\n  tc:\n    - name: tc_realtime\n      processor: realtime\nyamcs-web:\n  displayBucket: ember_displays\n'
        (c/'yamcs.ember.yaml').write_text(body)
        (c/'yamcs.ember-lte.yaml').write_text(body)
        (c/'yamcs.yaml').write_text('instances:\n  - ember\n  - ember-lte\nsecretKey: preserve\n')
        return c,body

    def test_two_environments_are_idempotent_and_cannot_cross_route(self):
        with tempfile.TemporaryDirectory() as temp:
            r=Path(temp);c,body=self.fixture(r)
            op.prepare(r);flight=(c/'yamcs.ember.yaml').read_text();bench=(c/'yamcs.ember-bench.yaml').read_text()
            op.prepare(r)
            self.assertEqual(flight,(c/'yamcs.ember.yaml').read_text())
            self.assertEqual(bench,(c/'yamcs.ember-bench.yaml').read_text())
            self.assertEqual((c/'yamcs.yaml').read_text(),'instances:\n  - ember\n  - ember-bench\nsecretKey: preserve\n')
            self.assertEqual((c/'yamcs.ember-lte.yaml').read_text(),body)
            self.assertIn('port: 10018',flight);self.assertIn('port: 10019',flight)
            self.assertNotIn('UdpTcDataLink',flight)
            self.assertNotIn('10020',flight)
            self.assertIn('port: 10020',bench);self.assertIn('port: 10028',bench)
            self.assertNotIn('10018',bench);self.assertNotIn('10019',bench)
            self.assertNotIn('10016',flight+bench);self.assertNotIn('10017',flight+bench)
            self.assertIn('displayBucket: ember_bench_displays',bench)
            pattern=re.findall('tcPatterns: \\["(.*?)"\\]',bench)[0]
            self.assertTrue(re.fullmatch(pattern,'/ember/PAYLOAD_STATUS_QUERY'))
            self.assertFalse(re.fullmatch(pattern,'/ember/PING'))
            for file,count in [('ember.xml',0),('ember-bench.xml',4)]:
                tree=ET.parse(r/'src/main/yamcs/mdb'/file)
                self.assertEqual(len(tree.findall('.//{'+op.NS+'}MetaCommand')),count)
                self.assertEqual(len(tree.findall('.//{'+op.NS+'}Parameter')),188)

    def test_legacy_history_has_no_hardware_routes(self):
        with tempfile.TemporaryDirectory() as temp:
            r=Path(temp);c,_=self.fixture(r);op.prepare(r,('ember-lte',))
            history=(c/'yamcs.ember-lte.yaml').read_text()
            self.assertIn('dataLinks: []',history)
            self.assertIn('tcPatterns: ["(?!)"]',history)

    def test_native_lte_health_allowlist(self):
        from codec import encode,PacketError
        from lte_receiver import validate
        for name,payload in [('HEARTBEAT',{'mode':3,'configuration':1,'telemetry_period_ms':0}),('SYSTEM_STATUS',{'mode':3,'configuration':1,'telemetry_period_ms':0,'accepted_commands':1,'rejected_commands':0})]:
            packet=encode(name,sequence=1,source=2,target=1,source_boot_id=22,uptime_ms=100,payload=payload)
            self.assertEqual(validate(packet)['name'],name)
            bad=bytearray(packet);bad[-1]^=1
            with self.assertRaises(PacketError):validate(bad)

    def test_bench_display_navigation_stays_in_bench(self):
        import sys
        sys.path.insert(0,str(ROOT/'ground/yamcs'))
        from generate_displays import generate
        with tempfile.TemporaryDirectory() as temp:
            generate(temp,instance='ember-bench')
            s=(Path(temp)/'Payload.opi').read_text()
            self.assertIn('ember-bench__realtime',s);self.assertNotIn('c=ember__realtime',s)
            for name in ('Payload.opi','Devices.opi','Comms-Firmware.opi'):
                root=ET.parse(Path(temp)/name).getroot()
                width=int(root.findtext('width'))
                for widget in root.findall('widget'):
                    self.assertLessEqual(int(widget.findtext('x','0'))+int(widget.findtext('width','0')),width,name)
