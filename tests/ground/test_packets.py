import importlib.util
import json
from pathlib import Path
import struct
import unittest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("ember_codec", ROOT / "ground/ember/codec.py")
codec = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(codec)
VECTORS = json.loads((ROOT / "ground/ember/vectors.json").read_text())


def repair_crc(packet):
    return bytes(packet[:-2]) + struct.pack(">H", codec.crc16(packet[:-2]))


class PacketTests(unittest.TestCase):
    def test_crc_check_value(self):
        self.assertEqual(codec.crc16(b"123456789"), 0x29b1)

    def test_fixed_vectors(self):
        for vector in VECTORS:
            with self.subTest(name=vector["input"]["name"]):
                expected = vector["input"]
                wire = bytes.fromhex(vector["hex"])
                self.assertEqual(codec.encode(**expected), wire)
                decoded = codec.decode(wire)
                self.assertEqual(decoded["name"], expected["name"])
                self.assertEqual(decoded["sequence"], expected["sequence"])
                self.assertEqual(decoded["payload"], expected["payload"])
                for field in ("source", "target", "source_boot_id", "uptime_ms"):
                    self.assertEqual(decoded["header"][field], expected[field])
                self.assertEqual(decoded["header"]["transaction_epoch"], expected.get("transaction_epoch", 0))
                self.assertEqual(decoded["header"]["transaction_id"], expected.get("transaction_id", 0))
                codec.validate_arguments(decoded)

    def test_corruption_truncation_and_trailing_bytes(self):
        wire = bytes.fromhex(VECTORS[0]["hex"])
        bad = bytearray(wire)
        bad[35] ^= 1
        for packet in (bytes(bad), wire[:-1], wire + b"\x00", b"", bytes(241)):
            with self.subTest(packet=packet.hex()):
                with self.assertRaises(codec.PacketError):
                    codec.decode(packet)

    def test_valid_crc_does_not_bypass_header_checks(self):
        wire = bytes.fromhex(VECTORS[0]["hex"])
        # CCSDS version, type, APID, segmentation, schema, kind, source,
        # transaction pairing, boot ID, payload length, message ID.
        mutations = [(0, 0x39), (0, 0x09), (1, 2), (2, 0x80),
                     (6, 2), (7, 9), (10, 9), (19, 0), (28, 1), (9, 0xff)]
        for offset, value in mutations:
            with self.subTest(offset=offset):
                bad = bytearray(wire)
                bad[offset] = value
                with self.assertRaises(codec.PacketError):
                    codec.decode(repair_crc(bad))
        bad = bytearray(wire)
        bad[20:24] = bytes(4)
        with self.assertRaises(codec.PacketError):
            codec.decode(repair_crc(bad))

    def test_command_ids_are_scoped_by_kind(self):
        spec = dict(VECTORS[0]["input"], name="PING", payload={})
        decoded = codec.decode(codec.encode(**spec))
        self.assertEqual(decoded["name"], "PING")
        self.assertEqual(codec.message_for("telemetry", 1)["name"], "SYSTEM_STATUS")

    def test_invalid_arguments_are_decodable_for_rejection(self):
        for payload in ({"parameter_id": 1, "value": 99},
                        {"parameter_id": 1, "value": 60001},
                        {"parameter_id": 65535, "value": 2000}):
            spec = dict(VECTORS[0]["input"], payload=payload)
            decoded = codec.decode(codec.encode(**spec))
            with self.assertRaises(codec.PacketError):
                codec.validate_arguments(decoded)
        for value in (100, 60000):
            spec = dict(VECTORS[0]["input"], payload={"parameter_id": 1, "value": value})
            codec.validate_arguments(codec.decode(codec.encode(**spec)))

    def test_encoder_rejects_overflow_missing_fields_and_bad_identity(self):
        base = VECTORS[0]["input"]
        changes = ({"sequence": 16384}, {"sequence": -1},
                   {"transaction_id": 0}, {"source_boot_id": 0},
                   {"source": 2}, {"target": 3},
                   {"payload": {"parameter_id": 1}},
                   {"payload": {"parameter_id": 1, "value": 2**32}})
        for change in changes:
            with self.subTest(change=change):
                with self.assertRaises(codec.PacketError):
                    codec.encode(**dict(base, **change))


if __name__ == "__main__":
    unittest.main()
