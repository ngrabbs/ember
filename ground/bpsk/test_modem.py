import struct
import subprocess
import tempfile
import unittest
import zlib
from pathlib import Path
import numpy as np
from modem import frame,decode,recover_bits,decode_native
from codec import encode, DICTIONARY
from generate_c import generate
ROOT=Path(__file__).resolve().parents[2]

class ModemTests(unittest.TestCase):
    def setUp(self):
        self.packet=encode('HEARTBEAT',sequence=19,source=3,target=1,source_boot_id=0x12345678,
                           uptime_ms=123456,payload=dict(mode=2,configuration=1,telemetry_period_ms=0))
        self.raw=frame(self.packet,19)
    def iq(self,raw=None,offset=0,phase=0,shift=0,noise=.03,conjugate=False):
        bits=np.unpackbits(np.frombuffer(self.raw if raw is None else raw,np.uint8))
        symbols=1-2*(np.cumsum(bits)%2).astype(float)
        a=np.r_[np.zeros(2400+shift),np.repeat(symbols,40),np.zeros(2400)]
        rng=np.random.default_rng(123)
        a=a*np.exp(1j*(phase+2*np.pi*offset*np.arange(len(a))/48000))
        a+=noise*(rng.normal(size=len(a))+1j*rng.normal(size=len(a)))
        return a.conj() if conjugate else a
    def test_c_python_identity(self):
        with tempfile.TemporaryDirectory() as td:
            exe=str(Path(td)/'packet')
            subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror','-I'+str(ROOT/'firmware/transceiver_bringup'),str(ROOT/'firmware/transceiver_bringup/tests/bpsk.c'),'-o',exe],check=True)
            subprocess.run([exe],check=True)
            self.assertEqual(subprocess.check_output([exe,'vector'],text=True).strip(),self.raw.hex())
    def test_offsets_timing_phase_noise(self):
        for offset in [-10000,-8000,0,5375,10000]:
            for shift in [0,7,23]:
                with self.subTest(offset=offset,shift=shift):
                    r=decode(self.iq(offset=offset,phase=2.7,shift=shift))
                    self.assertEqual([x['hex'] for x in r],[self.packet.hex()])
    def test_conjugate_and_window_boundary(self):
        a=self.iq(offset=-8100,phase=np.pi,conjugate=True)
        r=decode(np.r_[np.zeros(46000),a,np.zeros(48000)])
        self.assertEqual([x['hex'] for x in r],[self.packet.hex()])
    def test_rejection(self):
        bad=bytearray(self.raw);bad[55]^=1
        self.assertEqual(decode(self.iq(raw=bad)),[])
        self.assertEqual(decode(self.iq(raw=self.raw[:65])),[])
        # A valid outer CRC must not bypass a bad native CRC.
        bad[81:85]=struct.pack('>I',zlib.crc32(bad[36:81]))
        self.assertEqual(recover_bits(np.unpackbits(np.frombuffer(bad,np.uint8))),[])
        rng=np.random.default_rng(4)
        self.assertEqual(decode(rng.normal(size=48000)+1j*rng.normal(size=48000)),[])
    def test_non_antipodal_is_diagnostic_only(self):
        bits=np.unpackbits(np.frombuffer(self.raw,np.uint8))
        levels=np.cumsum(bits)%2
        iq=np.r_[np.zeros(2400),np.repeat(np.exp(1j*levels*np.pi/3),40),np.zeros(2400)]
        self.assertEqual(decode(iq),[])
        result=decode(iq,phase_diagnostic=True)
        self.assertEqual([x['hex'] for x in result],[self.packet.hex()])
        self.assertEqual(result[0]['decoder'],'phase-transition-diagnostic')
    def test_all_telemetry_boundaries(self):
        for message in DICTIONARY['messages']:
            if message['kind']!='telemetry':continue
            packet=encode(message['name'],sequence=20,source=2,target=1,source_boot_id=123,
                uptime_ms=456,payload={f['name']:0 for f in message['fields']})
            for offset in (0,46000,89000):
                with self.subTest(message=message['name'],offset=offset):
                    iq=np.r_[np.zeros(offset),self.iq(raw=frame(packet,20),offset=-8100),np.zeros(48000)]
                    self.assertEqual([x['hex'] for x in decode(iq)],[packet.hex()])
    def test_generated_dictionary_current(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'wire.h';generate(path)
            self.assertEqual(path.read_bytes(),(ROOT/'firmware/transceiver_bringup/native_wire.h').read_bytes())
    def test_firmware_identity_matches_c_and_full_git(self):
        with tempfile.TemporaryDirectory() as td:
            d=Path(td);sha='0123456789abcdef0123456789abcdef01234567'
            (d/'build_identity.h').write_text('#define FW_MAJOR 0u\n#define FW_MINOR 22u\n#define FW_PATCH 0u\n#define FW_DIRTY 1u\n#define FW_GIT "'+sha+'"\n')
            (d/'test.c').write_text('#include <stdio.h>\n#include "firmware_identity.h"\nint main(void){uint8_t p[128];size_t n=firmware_packet(p,123,7,456);fwrite(p,1,n,stdout);return 0;}')
            subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror','-Wno-unused-function','-I'+td,'-I'+str(ROOT/'firmware/transceiver_bringup'),str(d/'test.c'),'-o',str(d/'test')],check=True)
            packet=subprocess.check_output([str(d/'test')])
            payload=dict(version_major=0,version_minor=22,version_patch=0,dirty=1)
            payload.update({f'git_sha_{i}':int(sha[i*8:i*8+8],16) for i in range(5)})
            self.assertEqual(packet,encode('COMMS_FIRMWARE',sequence=7,source=3,target=1,source_boot_id=123,uptime_ms=456,payload=payload))
    def test_two_packets(self):
        second=frame(self.packet,20)
        r=decode(np.r_[self.iq(),self.iq(raw=second)])
        self.assertEqual({x['sequence'] for x in r},{19,20})

if __name__=='__main__':unittest.main()
