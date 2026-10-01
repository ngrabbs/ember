"""Exercise the production driver against a bounded SMBus mock and the ground decoder."""
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('decoder', ROOT/'ground/ember/ltc4162_decode.py')
decoder=importlib.util.module_from_spec(spec)
spec.loader.exec_module(decoder)

class ReadoutTests(unittest.TestCase):
    def test_production_c_driver(self):
        for writes in (0,1):
            with self.subTest(writes=writes), tempfile.TemporaryDirectory() as d:
                binary=str(Path(d)/'test')
                subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror',f'-DIHU_EPS_ALLOW_CHARGER_WRITES={writes}',
                    '-I'+str(ROOT/'test/firmware/ltc4162_mocks'),'-I'+str(ROOT/'firmware/ihu/src'),
                    '-I'+str(ROOT/'firmware/shared'),str(ROOT/'firmware/ihu/src/drivers/ltc4162.c'),
                    str(ROOT/'test/firmware/ltc4162_driver_test.c'),'-lm','-o',binary],check=True)
                subprocess.run([binary],check=True)

    def test_timed_bench_driver(self):
        with tempfile.TemporaryDirectory() as d:
            binary=str(Path(d)/'bench')
            subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror',
                '-DIHU_EPS_ALLOW_CHARGER_WRITES=0','-DIHU_EPS_TIMED_BENCH_TEST=1',
                '-I'+str(ROOT/'test/firmware/ltc4162_mocks'),'-I'+str(ROOT/'firmware/ihu/src'),
                '-I'+str(ROOT/'firmware/shared'),str(ROOT/'firmware/ihu/src/drivers/ltc4162.c'),
                str(ROOT/'test/firmware/ltc4162_bench_test.c'),'-lm','-o',binary],check=True)
            subprocess.run([binary],check=True)

    def sample(self):
        r={f['name']:0 for f in decoder.D['registers']}
        r.update(telemetry_status=1,chem_cells=2,vbat=21322,vin=65535,vout=4952,ibat=64947,iin=81,die_temp=13252)
        return {'profile':decoder.D['profile'],'registers':r}

    def decode(self,s):
        return decoder.decode(s,cells=2,rsnsb_ohms=.01,rsnsi_ohms=.01)

    def test_signed_scaling(self):
        e=self.decode(self.sample())['engineering']
        for name,value in {'battery_pack_v':8.2047056,'input_v':-.001649,'output_v':8.185656,
                           'battery_ma':-86.3474,'input_ma':11.8746,'die_temp_c':20.518}.items():
            self.assertAlmostEqual(e[name],value,places=5)

    def test_invalid_adc_and_mismatched_chemistry_cells(self):
        for field,value in [('telemetry_status',0),('chem_cells',0x402),('chem_cells',3)]:
            s=self.sample(); s['registers'][field]=value
            self.assertIsNone(self.decode(s)['engineering'])
        s=self.sample(); s['registers']['chem_cells']=0
        self.assertTrue(self.decode(s)['cells_from_board_config'])
        self.assertTrue(self.decode(s)['conversion_valid'])

    def test_malformed_word(self):
        for value in (-1,65536,True):
            s=self.sample(); s['registers']['vbat']=value
            with self.assertRaises(ValueError): self.decode(s)

    def test_captured_hardware_power_transition(self):
        evidence=ROOT/'system/ground_station/evidence'
        off=json.loads((evidence/'ltc4162-battery-adc-off-20261001.json').read_text())
        self.assertFalse(self.decode(off)['conversion_valid'])
        self.assertIsNone(self.decode(off)['engineering'])
        powered=json.loads((evidence/'ltc4162-input-power-20261001.json').read_text())
        self.assertEqual(len(powered),3)
        for s in powered:
            d=self.decode(s)
            self.assertTrue(d['conversion_valid'])
            self.assertEqual((d['chemistry'],d['detected_cells']),('LAD',2))
            self.assertAlmostEqual(d['engineering']['battery_pack_v'],8.206,places=3)
            self.assertLess(d['engineering']['battery_ma'],0)
        self.assertAlmostEqual(self.decode(powered[0])['engineering']['input_v'],8.215318,places=6)

    def test_generated_header_is_current(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/'registers.h'
            subprocess.run(['python3',str(ROOT/'ground/ember/generate_ltc4162.py'),str(out)],check=True)
            self.assertEqual(out.read_text(),(ROOT/'firmware/shared/ltc4162_registers.h').read_text())

if __name__=='__main__': unittest.main()
