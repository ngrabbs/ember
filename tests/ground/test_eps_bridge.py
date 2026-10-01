"""Real captured readouts, bounded UART parsing, validity and generated wire contract."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'ground/ember'))
from codec import decode, PacketError
from eps_bridge import State, Lines, UNAVAILABLE, NEVER
from generate_mdb import generate

SAMPLE = json.loads((ROOT/'system/ground_station/evidence/ltc4162-input-10v7-20261001.json').read_text())[0]


class EPS(unittest.TestCase):
    def state(self):
        return State(cells=2, rsnsb=.01, rsnsi=.01, session=123)

    def test_real_packet(self):
        s = self.state()
        self.assertTrue(s.accept(json.dumps(SAMPLE).encode(), 10))
        p = decode(s.packet(10.1))
        self.assertEqual(p['name'], 'POWER_STATUS')
        self.assertEqual(p['header']['message_id'], 16)
        self.assertLessEqual(len(s.packet(10.1)), 240)
        v = p['payload']
        self.assertEqual(v['input_mv'], 10681)
        self.assertEqual(v['battery_mv'], 8184)
        self.assertLess(v['battery_ua'], 0)
        self.assertEqual(v['raw_ibat'], 65513)
        self.assertEqual(v['ihu_readout_uptime_ms'], SAMPLE['uptime_ms'])
        self.assertEqual(v['bridge_session_id'], 123)
        self.assertEqual(v['sense_values_verified'], 0)
        self.assertEqual(v['provenance'], 1)
        wire = bytearray(s.packet(10.1)); wire[40] ^= 1
        with self.assertRaises(PacketError): decode(wire)

    def test_quality_transitions(self):
        s = self.state()
        p = s.payload(1)
        self.assertEqual(p['readout_age_ms'], NEVER)
        self.assertEqual(p['readout_present'], 0)
        self.assertEqual(p['input_mv'], UNAVAILABLE)
        s.accept(json.dumps(SAMPLE).encode(), 10)
        for link in ('DISCONNECTED', 'READ_TIMEOUT', 'INVALID_READOUT'):
            s.link = link
            p = s.payload(12)
            self.assertEqual(p['readout_valid'], 0)
            self.assertEqual(p['conversion_valid'], 0)
            self.assertEqual(p['input_mv'], UNAVAILABLE)
            self.assertEqual(p['raw_vin'], SAMPLE['registers']['vin'])
            self.assertEqual(p['readout_count'], 1)
            self.assertEqual(p['readout_age_ms'], 2000)
        s.accept(json.dumps(SAMPLE).encode(), 15)
        self.assertEqual(s.payload(16)['readout_valid'], 1)
        self.assertEqual(s.payload(28)['readout_valid'], 0)
        self.assertEqual(s.payload(28)['input_mv'], UNAVAILABLE)

    def test_adc_and_cell_validity(self):
        for key, value in [('telemetry_status',0), ('chem_cells',0x20e3), ('chem_cells',0x24e2)]:
            sample = copy.deepcopy(SAMPLE); sample['registers'][key] = value
            s = self.state()
            self.assertTrue(s.accept(json.dumps(sample).encode(),10))
            p=s.payload(11)
            self.assertEqual(p['readout_valid'],1)
            self.assertEqual(p['conversion_valid'],0)
            self.assertEqual(p['input_mv'],UNAVAILABLE)

    def test_malformed_readout(self):
        bad=[]
        for k,v in [('uptime_ms',True),('uptime_ms',-1),('profile','wrong'),('registers',[])]:
            sample=copy.deepcopy(SAMPLE);sample[k]=v;bad.append(json.dumps(sample).encode())
        sample=copy.deepcopy(SAMPLE);del sample['registers']['vin'];bad.append(json.dumps(sample).encode())
        bad += [b'{"profile":"x","profile":"y"}', b'{garbage}', b'{"uptime_ms":NaN}']
        for line in bad:
            s=self.state();self.assertFalse(s.accept(line,10));self.assertIsNone(s.last_at)
        self.assertTrue(self.state().accept(b'IHU> '+json.dumps(SAMPLE).encode(),10))

    def test_line_bounds_and_split(self):
        r=Lines();self.assertEqual(list(r.feed(b'x'*5000)),[]);self.assertLessEqual(len(r.buffer),2048)
        self.assertEqual(list(r.feed(b'\rnoise\n')), [b'noise'])
        wire=json.dumps(SAMPLE).encode();self.assertEqual(list(r.feed(wire[:100])),[])
        self.assertEqual(list(r.feed(wire[100:]+b'\r\n')), [wire])

    def test_mdb_scaling_expiration_and_header_provenance(self):
        with tempfile.TemporaryDirectory() as d:
            generate(d)
            root=ET.parse(Path(d)/'ember.xml').getroot();ns={'x':'http://www.omg.org/spec/XTCE/20180204'}
            term=root.find(".//x:FloatParameterType[@name='POWER_STATUS_input_mv_type']//x:Term",ns)
            self.assertEqual(float(term.attrib['coefficient']),.001)
            validity=root.find(".//x:FloatParameterType[@name='POWER_STATUS_input_mv_type']/x:ValidRange",ns)
            self.assertEqual(validity.attrib['validRangeAppliesToCalibrated'],'false')
            self.assertEqual(int(validity.attrib['minExclusive']),UNAVAILABLE)
            rate=root.find(".//x:SequenceContainer[@name='POWER_STATUS']/x:DefaultRateInStream",ns)
            self.assertEqual(float(rate.attrib['minimumValue']),1)
            c=root.find(".//x:SequenceContainer[@name='HEARTBEAT']",ns)
            alias=c.find(".//x:ParameterRefEntry[@parameterRef='HEARTBEAT_uptime_ms']//x:FixedValue",ns)
            self.assertEqual(alias.text,'192')


if __name__=='__main__': unittest.main()
