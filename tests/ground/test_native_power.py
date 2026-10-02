"""Decode firmware-native EPS packets with the independent ground codec."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'ground/ember'))
from codec import decode,encode,validate_arguments,PacketError
from lte_receiver import validate as validate_lte
from generate_c import generate
from ltc4162_decode import D,decode as decode_eps

class NativePower(unittest.TestCase):
    def test_c_packets_against_real_eps_readouts(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory);generate(path/'wire.h')
            (path/'main.c').write_text('''
#include <stdio.h>
#include "power_packet.h"
int main(void) {
    ltc4162_raw_t raw;
#define READ(name,address) {unsigned value;if(scanf("%u",&value)!=1 || value>65535)return 1;raw.name=value;}
    LTC4162_READOUT_REGISTERS(READ)
#undef READ
    uint8_t packet[240];size_t n=power_packet(packet,&raw,123,16383,456,7);
    for(size_t i=0;i<n;++i)printf("%02x",packet[i]);return 0;
}
''')
            binary=path/'test'
            subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror',
                            '-I'+str(path),'-I'+str(ROOT/'firmware/can_feather_bench'),
                            '-I'+str(ROOT/'firmware/comms_transport'),str(path/'main.c'),'-o',str(binary)],check=True)
            logs=json.loads((ROOT/'system/ground_station/evidence/ihu-eps-battery-adc-20261002.json').read_text())
            samples=[json.loads(row['response']) for row in logs if row['command']=='eps json']
            for sample in samples:
                values=' '.join(str(sample['registers'][r['name']]) for r in D['registers'])
                wire=bytes.fromhex(subprocess.check_output([str(binary)],input=values.encode()).decode())
                self.assertEqual(len(wire),128)
                packet=decode(wire);validate_arguments(packet);p=packet['payload']
                self.assertEqual(validate_lte(wire),packet)
                wrapped=dict(p,provenance=1,bridge_session_id=123)
                wrong=encode('POWER_STATUS',sequence=1,source=2,target=1,source_boot_id=123,uptime_ms=456,payload=wrapped)
                with self.assertRaises(PacketError):validate_lte(wrong)
                damaged=bytearray(wire);damaged[-1]^=1
                with self.assertRaises(PacketError):validate_lte(damaged)
                self.assertEqual((packet['sequence'],packet['header']['source_boot_id']),(16383,123))
                self.assertEqual((p['provenance'],p['bridge_session_id'],p['readout_count']),(2,0,7))
                for name,value in sample['registers'].items():self.assertEqual(p['raw_'+name],value)
                expected=decode_eps(sample,cells=2,rsnsb_ohms=.01,rsnsi_ohms=.01)
                self.assertEqual(bool(p['conversion_valid']),expected['conversion_valid'])
                pairs={'battery_mv':'battery_pack_v','input_mv':'input_v','output_mv':'output_v',
                       'battery_ua':'battery_ma','input_ua':'input_ma','die_temp_mc':'die_temp_c'}
                for field,name in pairs.items():
                    if expected['conversion_valid']:
                        self.assertLessEqual(abs(p[field]-expected['engineering'][name]*1000),.51)
                    else:self.assertEqual(p[field],-2147483648)
