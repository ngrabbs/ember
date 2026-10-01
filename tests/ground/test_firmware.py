"""Compile the actual C endpoint on the host, decode its packets independently."""
import ctypes
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ground/ember"))
from codec import crc16, decode, encode
from framing import FrameReader, decode_frame, encode_frame


class FirmwareTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        compiler = shutil.which("cc")
        if not compiler:
            raise unittest.SkipTest("host C compiler unavailable")
        cls.temp = tempfile.TemporaryDirectory()
        path = Path(cls.temp.name)
        subprocess.run([sys.executable, str(ROOT / "ground/ember/generate_c.py"), str(path / "wire.h")], check=True)
        (path / "size.c").write_text('#include "protocol.h"\nsize_t state_size(void) { return sizeof(ember_state); }\n')
        source = ROOT / "firmware/usb_bench"
        subprocess.run([compiler, "-std=c11", "-Wall", "-Wextra", "-Werror", "-shared", "-fPIC",
                        "-I" + str(path), "-I" + str(source), str(source / "protocol.c"),
                        str(source / "framing.c"), str(path / "size.c"), "-o", str(path / "endpoint.so")], check=True)
        cls.lib = ctypes.CDLL(str(path / "endpoint.so"))
        cls.lib.state_size.restype = ctypes.c_size_t
        cls.callback_type = ctypes.CFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p)
        cls.lib.ember_init.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
        cls.lib.ember_command.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t,
                                         ctypes.c_uint32, cls.callback_type, ctypes.c_void_p]
        cls.lib.cobs_encode.argtypes = cls.lib.cobs_decode.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p, ctypes.c_size_t]
        cls.lib.cobs_encode.restype = cls.lib.cobs_decode.restype = ctypes.c_size_t

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def setUp(self):
        self.state = ctypes.create_string_buffer(self.lib.state_size())
        self.lib.ember_init(self.state, 7)

    def command(self, name="SET_PARAMETER", transaction=1, **payload):
        return encode(name, sequence=0, source=1, target=2, transaction_epoch=123,
                      transaction_id=transaction, source_boot_id=123, uptime_ms=1, payload=payload)

    def send(self, packet):
        received = []
        @self.callback_type
        def capture(pointer, size, context):
            received.append(decode(ctypes.string_at(pointer, size)))
            return True
        self.lib.ember_command(self.state, packet, len(packet), 1000, capture, None)
        return received

    def test_c_parameter_query_and_duplicate(self):
        first = self.send(self.command(parameter_id=1, value=2000))
        self.assertEqual([r["payload"]["stage"] for r in first], [0, 2])
        again = self.send(self.command(parameter_id=1, value=2000))
        self.assertEqual([r["payload"] for r in first], [r["payload"] for r in again])
        conflict = self.send(self.command(parameter_id=1, value=3000))
        self.assertEqual(conflict[0]["payload"]["reason"], 9)
        status = self.send(self.command("REQUEST_STATUS", transaction=2))
        self.assertEqual(status[1]["payload"]["telemetry_period_ms"], 2000)
        self.assertEqual(status[1]["payload"]["accepted_commands"], 2)
        self.assertTrue(all(r["header"]["transaction_id"] == 2 for r in status))

    def test_c_invalid_unknown_and_corrupt(self):
        invalid = self.send(self.command(parameter_id=1, value=99))
        self.assertEqual(invalid[0]["payload"]["reason"], 2)
        packet = bytearray(self.command("PING", transaction=2))
        packet[8:10] = b"\x00\xff"
        packet[-2:] = crc16(packet[:-2]).to_bytes(2, "big")
        self.assertEqual(self.send(bytes(packet))[0]["payload"]["reason"], 1)
        packet[-1] ^= 1
        self.assertEqual(self.send(bytes(packet)), [])
        for size in range(32):
            self.assertEqual(self.send(bytes(packet[:size])), [])

    def test_framing_vectors_boundaries_and_recovery(self):
        self.assertEqual(encode_frame(b"\x11\x00\x22"), b"\x02\x11\x02\x22\x00")
        for packet in (bytes(240), bytes(range(240)), self.command(parameter_id=1, value=2000)):
            expected = encode_frame(packet)
            out = ctypes.create_string_buffer(242)
            size = self.lib.cobs_encode(packet, len(packet), out, 242)
            self.assertEqual(out.raw[:size], expected)
            decoded = ctypes.create_string_buffer(240)
            size = self.lib.cobs_decode(expected[:-1], len(expected)-1, decoded, 240)
            self.assertEqual(decoded.raw[:size], packet)
            self.assertEqual(decode_frame(expected[:-1]), packet)
        reader = FrameReader()
        self.assertEqual(reader.feed(b"x" * 300 + b"\x00"), [])
        frame = encode_frame(self.command("PING"))
        self.assertEqual(reader.feed(frame[:3]), [])
        self.assertEqual(reader.feed(frame[3:] + frame), [self.command("PING"), self.command("PING")])
        self.assertEqual(reader.errors, 1)


if __name__ == "__main__":
    unittest.main()
