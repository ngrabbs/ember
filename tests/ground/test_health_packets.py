"""Decode native MCU health packets independently and enforce forwarding bounds."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'ground/ember'))
from codec import decode, PacketError
from generate_c import generate
from lte_receiver import validate


class HealthPackets(unittest.TestCase):
    def test_c_native_packets_and_allowlist(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory);generate(path/'wire.h')
            (path/'main.c').write_text('''
#include <stdio.h>
#include "health_packet.h"
#include "native_telemetry.h"
int main(void) {
    uint8_t b[128];
    for(int system=0;system<2;++system) {
        size_t n=health_packet(b,system,123,16383,456,20000,42,3);
        if(!native_telemetry_valid(b,n,123) || native_telemetry_valid(b,n,124))return 1;
        for(size_t i=0;i<n;++i)printf("%02x",b[i]);puts("");
        b[n-1]^=1;if(native_telemetry_valid(b,n,123))return 2;b[n-1]^=1;
        ul_p32(b+W_TRANSACTION_ID,1);ul_p16(b+n-2,ul_crc(b,n-2));
        if(native_telemetry_valid(b,n,123))return 3;
    }
    return 0;
}
''')
            binary=path/'test'
            subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror',
                '-I'+str(path),'-I'+str(ROOT/'firmware/can_feather_bench'),
                '-I'+str(ROOT/'firmware/comms_transport'),str(path/'main.c'),'-o',str(binary)],check=True)
            wires=[bytes.fromhex(line) for line in subprocess.check_output([binary],text=True).splitlines()]
            for wire,name,length in zip(wires,('HEARTBEAT','SYSTEM_STATUS'),(38,46)):
                packet=decode(wire);self.assertEqual(packet['name'],name)
                self.assertEqual(validate(wire),packet)
                self.assertEqual(len(wire),length)
                self.assertEqual(packet['sequence'],16383)
                self.assertEqual(packet['header']['source_boot_id'],123)
                self.assertEqual(packet['header']['uptime_ms'],456)
                self.assertEqual(packet['payload']['telemetry_period_ms'],20000)
                damaged=bytearray(wire);damaged[-1]^=1
                with self.assertRaises(PacketError):validate(damaged)
            self.assertEqual(decode(wires[1])['payload']['accepted_commands'],42)
            self.assertEqual(decode(wires[1])['payload']['rejected_commands'],3)
