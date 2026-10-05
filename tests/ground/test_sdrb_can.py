"""Transport interoperability and real EPS packet replay; no hardware opened."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import ExitStack
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'ground/ember'))
from sdrb_can import Envelope, Reassembler, Service, fragments, parse_envelope
import sdrb_can


@unittest.skipUnless(sys.platform == 'linux' and os.environ.get('EMBER_TEST_VCAN'),
                     'requires an explicitly supplied virtual CAN interface')
class SocketCANFilterTests(unittest.TestCase):
    def test_kernel_receives_only_ihu_standard_data(self):
        interface = os.environ['EMBER_TEST_VCAN']
        self.assertTrue(interface.startswith('embervcan'), 'virtual test bus only')
        socket = sdrb_can.socket
        with socket.socket(socket.PF_CAN, socket.SOCK_RAW, socket.CAN_RAW) as rx, \
                socket.socket(socket.PF_CAN, socket.SOCK_RAW, socket.CAN_RAW) as tx:
            rx.setsockopt(socket.SOL_CAN_RAW, socket.CAN_RAW_FILTER,
                          sdrb_can.struct.pack('=II', sdrb_can.IHU_ID,
                                              sdrb_can.IHU_FILTER_MASK))
            rx.settimeout(.5)
            rx.bind((interface,)); tx.bind((interface,))
            for identifier in (0x711, 0x80000710, 0x40000710, 0x710):
                tx.send(sdrb_can.CAN_FRAME.pack(identifier, 1, b'x'))
            identifier, dlc, data = sdrb_can.CAN_FRAME.unpack(rx.recv(16))
            self.assertEqual((identifier, dlc, data[:dlc]), (0x710, 1, b'x'))
            with self.assertRaises(TimeoutError):
                rx.recv(16)


class AdapterTests(unittest.TestCase):
    def setUp(self):
        report = json.loads((ROOT / 'system/ground_station/evidence/queued-eps-20261003-01/report.json').read_text())
        self.raw = bytes.fromhex(report['host']['queued'][0]['hex'])
        self.sender = int.from_bytes(self.raw[20:24], 'big')
        self.records = []
        self.service = Service(1234, self.records.append)
        self.hello = Envelope(1, 1, self.sender, self.sender, 1, b'')
        self.packet = Envelope(1, 0x72, self.sender, self.sender, 2, self.raw)

    def deliver(self, packet):
        r = Reassembler()
        out = None
        for i, frame in enumerate(fragments(packet.wire(), packet.request & 0xffff)):
            out = r.feed(0x710, frame, i * .002)
        self.assertEqual(r.errors, 0)
        self.assertEqual(out, packet)
        return self.service.handle(out)

    def test_real_eps_and_application_response(self):
        self.assertEqual(self.deliver(self.hello).kind, 2)
        reply = self.deliver(self.packet)
        self.assertEqual((reply.kind, reply.sender, reply.origin, reply.request, reply.payload),
                         (0x73, 1234, self.sender, 2, self.raw))
        self.assertEqual(parse_envelope(reply.wire()), reply)
        p = self.records[0]['decoded']['payload']
        self.assertEqual((p['battery_mv'], p['battery_ua']), (7995, -88986))
        self.assertFalse(self.records[0]['rf_started'])
        self.assertEqual(self.records[0]['hex'], self.raw.hex())

    def test_duplicate_conflict_and_reset(self):
        self.deliver(self.hello)
        first = self.deliver(self.packet)
        self.assertEqual(self.deliver(self.packet), first)
        self.assertEqual(len(self.records), 1)
        bad = Envelope(1, 0x72, self.sender, self.sender, 2, b'bad')
        self.assertEqual(self.deliver(bad).payload, b'\x03')
        self.deliver(Envelope(1, 1, 55, 55, 3, b''))
        self.assertEqual(self.deliver(self.packet).kind, 0x7f)

    def test_reject_control_bad_crc_and_producer(self):
        self.deliver(self.hello)
        for kind in (0x74, 0x76, 0x78):
            p = Envelope(1, kind, self.sender, self.sender, 5, b'')
            self.assertEqual(self.deliver(p).payload, b'\x02')
        raw = bytearray(self.raw); raw[-1] ^= 1
        self.assertEqual(self.deliver(Envelope(1, 0x72, self.sender, self.sender, 6, bytes(raw))).payload, b'\x07')
        self.deliver(Envelope(1, 1, 55, 55, 7, b''))
        self.assertEqual(self.deliver(Envelope(1, 0x72, 55, 55, 8, self.raw)).payload, b'\x07')
        self.assertEqual(self.records, [])

    def test_storage_failure_does_not_acknowledge(self):
        def fail(record):
            raise OSError('disk full')
        self.service.record = fail
        self.deliver(self.hello)
        self.assertEqual(self.deliver(self.packet).payload, b'\x06')
        self.assertEqual(self.service.accepted, 0)

    def test_socket_monitor_sends_nothing_and_responder_is_opt_in(self):
        frames = [sdrb_can.CAN_FRAME.pack(0x710, len(f), f.ljust(8, b'\0'))
                  for p in (self.hello, self.packet)
                  for f in fragments(p.wire(), p.request & 0xffff)]
        for respond in (False, True):
            bus = MagicMock()
            bus.__enter__.return_value = bus
            bus.recv.side_effect = frames + [KeyboardInterrupt()]
            with tempfile.TemporaryDirectory() as tmp, ExitStack() as stack:
                # macOS has no SocketCAN constants; mock only the syscall boundary.
                for name in ('PF_CAN', 'CAN_RAW', 'SOL_CAN_RAW', 'CAN_RAW_FILTER'):
                    stack.enter_context(patch.object(sdrb_can.socket, name, 1, create=True))
                stack.enter_context(patch.object(sdrb_can.socket, 'socket', return_value=bus))
                stack.enter_context(patch.object(sdrb_can.time, 'sleep'))
                stack.enter_context(patch('builtins.print'))
                stack.enter_context(patch.object(sdrb_can.fcntl, 'flock'))
                output = Path(tmp)/'run'
                with self.assertRaises(KeyboardInterrupt):
                    sdrb_can.serve('can1', 60, output, respond)
                rows = [json.loads(x) for x in (output/'packets.jsonl').read_text().splitlines()]
                self.assertEqual(len(rows), 1)
                self.assertEqual(rows[0]['hex'], self.raw.hex())
                self.assertEqual(rows[0]['application_replies_enabled'], respond)
                if respond:
                    self.assertGreater(bus.send.call_count, 0)
                    r = Reassembler()
                    packets = []
                    for i, call in enumerate(bus.send.call_args_list):
                        can_id, dlc, data = sdrb_can.CAN_FRAME.unpack(call.args[0])
                        self.assertEqual(can_id, 0x711)
                        out = r.feed(0x710, data[:dlc], i*.002)
                        if out:
                            packets.append(out)
                    self.assertEqual([p.kind for p in packets], [2, 0x73])
                    self.assertEqual(packets[-1].payload, self.raw)
                else:
                    bus.send.assert_not_called()

    def test_missing_duplicate_timeout_route_token_and_recovery(self):
        fs = list(fragments(self.packet.wire(), 2))
        for fault in ('missing', 'duplicate', 'timeout', 'token'):
            r = Reassembler()
            self.assertIsNone(r.feed(0x710, fs[0], 0))
            data, now = (fs[2], .002) if fault == 'missing' else (fs[0], .002) if fault == 'duplicate' else (fs[1], .5)
            if fault == 'token':
                data, now = fs[1][:1] + b'\x00\x03' + fs[1][3:], .002
            self.assertIsNone(r.feed(0x710, data, now))
            self.assertGreater(r.errors + r.timeouts, 0)
            for i, f in enumerate(fs):
                out = r.feed(0x710, f, 1 + i * .002)
            self.assertEqual(out, self.packet)
        r = Reassembler()
        for f in fs:
            self.assertIsNone(r.feed(0x80000710, f, 0))
        for i, f in enumerate(fragments(self.packet.wire(), 3)):
            self.assertIsNone(r.feed(0x710, f, i * .002))
        self.assertEqual(r.errors, 1)

    def test_c_firmware_interoperability_all_payload_sizes(self):
        compiler = shutil.which('cc')
        self.assertIsNotNone(compiler, 'C compiler required for interoperability check')
        source = r'''
#include <stdio.h>
#include "can_fragment.h"
int main(void) {
    for(unsigned n=1;n<=240;++n) {
        ul_packet p={.version=1,.type=0x70,.sender=0x10203040,
                     .origin=0x10203040,.request=0x12345678,.size=n};
        for(unsigned i=0;i<n;++i)p.payload[i]=(uint8_t)i;
        uint8_t wire[UL_WIRE_MAX];size_t size=ul_encode(&p,wire);
        printf("%u ",n);for(size_t i=0;i<size;++i)printf("%02x",wire[i]);puts("");
        for(unsigned i=0;i<CF_FRAMES;++i) {
            cf_frame f;if(!cf_fragment(wire,size,CF_IHU_ID,0x5678,i,&f))break;
            printf("F ");for(unsigned j=0;j<f.size;++j)printf("%02x",f.data[j]);puts("");
        }
    }
}
'''
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp)/'vectors.c'; exe = Path(tmp)/'vectors'
            src.write_text(source)
            subprocess.run([compiler, '-std=c11', '-Wall', '-Wextra', '-Werror',
                            '-I', str(ROOT/'firmware/comms_transport'), str(src), '-o', str(exe)], check=True)
            lines = subprocess.check_output([str(exe)], text=True).splitlines()
        reader = None
        for line in lines:
            tag, hexdata = line.split()
            if tag != 'F':
                n = int(tag)
                expected = Envelope(1, 0x70, 0x10203040, 0x10203040, 0x12345678, bytes(range(n)))
                self.assertEqual(expected.wire().hex(), hexdata)
                self.assertEqual(parse_envelope(bytes.fromhex(hexdata)), expected)
                frames = iter(fragments(bytes.fromhex(hexdata), 0x5678))
                reader = Reassembler(); index = 0
            else:
                frame = bytes.fromhex(hexdata)
                self.assertEqual(next(frames), frame)
                out = reader.feed(0x710, frame, index * .002); index += 1
                if out:
                    self.assertEqual(out, expected)


if __name__ == '__main__':
    unittest.main()
