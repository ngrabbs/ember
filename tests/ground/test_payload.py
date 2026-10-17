"""Payload wire interoperability and malformed-request recovery."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'firmware/payload'))
from protocol import (Packet, Reassembler, REPORT, REQUEST_ID, REPLY_ID, discovery,
                      fragments, HELLO, ECHO, ECHO_ACK, IDENT, STATUS, HEARTBEAT, ERROR, FIRE_CHECK, FIRE_RESULT, FIRE_REPORT)
from payload import Service

IDENTITY = dict(version='0.1.0', git='0123456789abcdef0123456789abcdef01234567', dirty=1)


class PayloadTests(unittest.TestCase):
    def setUp(self):
        self.clock = 10.0
        self.service = Service(IDENTITY, boot=42, now=lambda: self.clock)

    def request(self, kind, data=b'', sender=11, version=1):
        return self.service.handle(Packet(kind, sender, sender, 7, data, version))

    def test_discovery_is_addressed_and_correlated(self):
        import struct
        for node in (1, 2, 3):
            self.assertIsNone(discovery(struct.pack('>BBHI', 1, node, 9, 11), 42))
        self.assertEqual(discovery(bytes.fromhex('010400090000000b'), 42), bytes.fromhex('010400090000002a'))
        for bad in ('010400000000000b', '0104000900000000', '020400090000000b', '0104'):
            self.assertIsNone(discovery(bytes.fromhex(bad), 42))

    def test_readonly_services_require_hello_and_keep_identity(self):
        self.assertEqual(self.request(STATUS).kind, ERROR)
        self.request(HELLO)
        self.clock += 2
        response = self.request(ECHO, bytes(range(240)))
        self.assertEqual(response.kind, ECHO_ACK)
        self.assertEqual(response.payload, bytes(range(240)))
        self.assertEqual((response.sender, response.origin, response.request), (42, 11, 7))
        ident = self.request(IDENT)
        self.assertEqual(len(ident.payload), 32)
        self.assertEqual(ident.payload[:4], bytes([0, 1, 0, 1]))
        self.assertEqual(ident.payload[4:24], bytes.fromhex(IDENTITY['git']))
        for kind in (STATUS, HEARTBEAT):
            report = REPORT.unpack(self.request(kind).payload)
            self.assertEqual(report[:6], (1, 4, 1, 0, 42, 2000))
        self.assertEqual(self.request(STATUS, sender=12).kind, ERROR)
        self.assertEqual(self.request(HELLO, b'bad').payload, b'\x04')
        self.assertEqual(self.request(ECHO).payload, b'\x04')
        self.assertEqual(self.request(0x80).payload, b'\x02')
        self.assertEqual(self.request(HELLO, version=2).payload, b'\x01')

    def test_fire_check_is_explicit_stub_and_session_gated(self):
        self.assertEqual(self.request(FIRE_CHECK).kind, ERROR)
        self.request(HELLO)
        reply=self.request(FIRE_CHECK)
        self.assertEqual(reply.kind,FIRE_RESULT)
        self.assertEqual(FIRE_REPORT.unpack(reply.payload),(1,0,1,0,42,0,1))
        self.assertEqual(self.request(FIRE_CHECK,b'bad').kind,ERROR)
        self.assertEqual(self.request(FIRE_CHECK,sender=99).kind,ERROR)
        self.assertEqual(FIRE_REPORT.unpack(self.request(FIRE_CHECK).payload)[-1],2)

    def test_reassembly_rejects_corruption_and_recovers(self):
        packet = Packet(ECHO, 11, 11, 0x12345678, bytes(range(240)))
        parts = list(fragments(packet))
        reader = Reassembler()
        self.assertIsNone(reader.feed(REQUEST_ID | 0x80000000, parts[0], 0))
        reader.feed(REQUEST_ID, parts[0], 0)
        reader.feed(REQUEST_ID, parts[2], .01)
        self.assertEqual(reader.errors, 1)
        reader.feed(REQUEST_ID, parts[0], 1)
        reader.expire(1.5)
        self.assertEqual(reader.timeouts, 1)
        for part in parts:
            result = reader.feed(REQUEST_ID, part, 2)
        self.assertEqual(result, packet)
        corrupted = bytearray(parts[-1]); corrupted[-2] ^= 1
        for part in parts[:-1] + [bytes(corrupted)]:
            result = reader.feed(REQUEST_ID, part, 3)
        self.assertIsNone(result)
        self.assertEqual(reader.errors, 2)
        for part in parts:
            result = reader.feed(REQUEST_ID, part, 4)
        self.assertEqual(result, packet)

    def test_matches_actual_c_envelope_and_fragment_codec(self):
        source = r'''
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include "device_registry.h"
#include "uplink_ping.h"
int main(int argc,char **argv) {
 assert(CF_PAYLOAD_REQUEST_ID!=UP_REQUEST_ID && CF_PAYLOAD_REPLY_ID!=UP_REPLY_ID);
 assert(argc==2);uint8_t wire[UL_WIRE_MAX];size_t size=strlen(argv[1])/2;
 for(size_t i=0;i<size;i++){char h[3]={argv[1][i*2],argv[1][i*2+1],0};wire[i]=(uint8_t)strtoul(h,0,16);}
 ul_reader reader={0};ul_packet packet={0};unsigned found=0;
 for(size_t i=0;i<size;i++)found+=ul_feed(&reader,wire[i],0,&packet);
 assert(found==1);uint8_t encoded[UL_WIRE_MAX];size_t n=ul_encode(&packet,encoded);
 assert(n==size && !memcmp(wire,encoded,n));
 for(unsigned i=0;i<(n+3)/4;i++){cf_frame f;assert(cf_fragment(wire,n,CF_PAYLOAD_REQUEST_ID,(uint16_t)packet.request,i,&f));
 for(unsigned j=0;j<f.size;j++)printf("%02x",f.data[j]);puts("");}
 assert(dr_devices[DR_PAYLOAD_INDEX].node==4 && dr_devices[DR_PAYLOAD_INDEX].reply_id==0x741);
 cf_frame q,r;assert(dr_request(4,9,11,&q));assert(dr_respond(&q,4,42,&r));assert(r.id==0x704);
 return 0;
}
'''
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            (directory / 'test.c').write_text(source)
            binary = directory / 'codec'
            subprocess.run(['cc', '-std=c11', '-Wall', '-Wextra', '-Werror',
                            '-I' + str(ROOT / 'firmware/comms_transport'),
                            str(directory / 'test.c'), '-o', str(binary)], check=True)
            for data in (b'', bytes(240), bytes(range(240)), b'\xff' * 240):
                packet = Packet(ECHO, 11, 11, 0xffffffff, data)
                actual = subprocess.check_output([str(binary), packet.encode().hex()], text=True)
                self.assertEqual(actual.splitlines(), [part.hex() for part in fragments(packet)])


if __name__ == '__main__':
    unittest.main()
