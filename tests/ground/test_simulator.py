import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ground/ember"))
from codec import PacketError, crc16, decode, encode
from simulator import Endpoint


class EndpointTests(unittest.TestCase):
    def setUp(self):
        self.endpoint = Endpoint(clock=lambda: 12.0, boot_id=7)

    def command(self, name="SET_PARAMETER", transaction=1, sequence=0, **payload):
        return encode(name, sequence=sequence, source=1, target=2,
                      transaction_epoch=123, transaction_id=transaction,
                      source_boot_id=123, uptime_ms=1000, payload=payload)

    def reports(self, wire):
        return [decode(packet) for packet in self.endpoint.handle(wire)]

    def test_set_parameter_results_and_periodic_data(self):
        reports = self.reports(self.command(parameter_id=1, value=2000))
        self.assertEqual([r["payload"]["stage"] for r in reports], [0, 2])
        self.assertEqual(reports[-1]["payload"]["value"], 2000)
        self.assertEqual(self.endpoint.accepted, 1)
        for report in reports:
            self.assertEqual(report["header"]["transaction_epoch"], 123)
            self.assertEqual(report["header"]["transaction_id"], 1)
        periodic = [decode(p) for p in self.endpoint.periodic()]
        self.assertEqual(periodic[0]["payload"]["telemetry_period_ms"], 2000)
        self.assertEqual(periodic[0]["header"]["transaction_id"], 0)
        self.assertEqual(periodic[-1]["payload"]["rssi_dbm"], -32768)

    def test_queries_return_correlated_data_before_completion(self):
        for name, payload, telemetry in (
            ("REQUEST_STATUS", {}, "SYSTEM_STATUS"),
            ("REQUEST_TELEMETRY", {"data_group": 48}, "COMM_STATUS")):
            with self.subTest(name=name):
                self.endpoint = Endpoint(boot_id=7)
                reports = self.reports(self.command(name, **payload))
                self.assertEqual([r["name"] for r in reports],
                                 ["COMMAND_RESPONSE", telemetry, "COMMAND_RESPONSE"])
                self.assertTrue(all(r["header"]["transaction_id"] == 1 for r in reports))

    def test_duplicate_does_not_execute_and_conflict_preserves_cache(self):
        first = self.reports(self.command(parameter_id=1, value=2000))
        repeat = self.reports(self.command(sequence=1, parameter_id=1, value=2000))
        self.assertEqual([r["payload"] for r in first], [r["payload"] for r in repeat])
        self.assertNotEqual(first[0]["sequence"], repeat[0]["sequence"])
        self.assertEqual(self.endpoint.accepted, 1)
        conflict = self.reports(self.command(parameter_id=1, value=3000))
        self.assertEqual(conflict[0]["payload"]["stage"], 1)
        self.assertEqual(conflict[0]["payload"]["reason"], 9)
        self.assertEqual(self.endpoint.period, 2000)
        again = self.reports(self.command(parameter_id=1, value=2000))
        self.assertEqual(again[-1]["payload"]["value"], 2000)
        self.assertEqual(self.endpoint.accepted, 1)

    def test_invalid_and_unknown_commands_rejected(self):
        bad = self.reports(self.command(parameter_id=1, value=99))
        self.assertEqual(bad[0]["payload"]["reason"], 2)
        self.assertEqual(self.endpoint.period, 1000)
        unknown = bytearray(self.command("PING", transaction=2))
        unknown[8:10] = b"\x00\xff"
        unknown[-2:] = crc16(unknown[:-2]).to_bytes(2, "big")
        with self.assertRaises(PacketError):
            decode(unknown)
        reports = self.reports(unknown)
        self.assertEqual(reports[0]["payload"]["command_id"], 255)
        self.assertEqual(reports[0]["payload"]["reason"], 1)

    def test_corruption_is_dropped_without_response(self):
        wire = bytearray(self.command(parameter_id=1, value=2000))
        wire[-1] ^= 1
        self.assertEqual(self.endpoint.handle(wire), [])
        self.assertEqual(self.endpoint.crc_errors, 1)
        self.assertEqual(self.endpoint.accepted, 0)

    def test_cache_bound_and_reset_contract(self):
        for transaction in range(1, 66):
            self.endpoint.handle(self.command("PING", transaction=transaction))
        self.assertEqual(len(self.endpoint.cache), 64)
        self.assertNotIn((1, 123, 1), self.endpoint.cache)
        reset = Endpoint(boot_id=8)
        self.assertEqual(reset.period, 1000)
        self.assertFalse(reset.cache)
        self.assertNotEqual(reset.boot_id, self.endpoint.boot_id)


if __name__ == "__main__":
    unittest.main()
