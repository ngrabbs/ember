import unittest
from unittest.mock import Mock
import numpy as np

from codec import encode
from link_gateway import DOWNLINK, RATE, Recent, forward_window, admit_command, waveform
from modem import frame


def packet(name, sequence, payload=None):
    command = name != 'HEARTBEAT'
    return encode(name, sequence=sequence, source=1 if command else 2,
                  target=2 if command else 1, source_boot_id=7, uptime_ms=4,
                  transaction_epoch=5 if command else 0, transaction_id=6 if command else 0,
                  payload=payload or {})


class LinkGatewayTests(unittest.TestCase):
    def test_admitted_ping_is_bounded_and_replay_is_suppressed(self):
        wire = packet('PING', 9)
        seq, key = admit_command(wire)
        self.assertEqual((seq, key), (9, (5, 6)))
        self.assertEqual(admit_command(packet('REQUEST_STATUS',10)), (10, (5, 6)))
        iq = waveform(wire, seq)
        self.assertLess(len(iq), RATE)
        self.assertLessEqual(float(np.max(np.abs(iq))), .200001)
        seen = Recent(1, 600)
        self.assertTrue(seen.admit(key, 0))
        self.assertFalse(seen.admit(key, 1))
        self.assertFalse(seen.admit((9, 9), 599))
        self.assertTrue(seen.admit((9, 9), 600))
        with self.assertRaises(ValueError):
            admit_command(wire[:-1])
        with self.assertRaises(ValueError):
            admit_command(packet('HEARTBEAT', 5, dict(mode=4, configuration=1, telemetry_period_ms=10000)))

    def test_all_native_commands_fit_a_single_uplink(self):
        commands = {
            'REQUEST_TELEMETRY': {'data_group': 1},
            'STATUS_CAPTURE': {},
            'STATUS_FETCH': {'capture_id': 1},
            'PAYLOAD_FIRE_CHECK': {},
            'IHU_REBOOT': {},
            'SET_HEARTBEAT': {'enabled': 1},
            'SET_UHF_TELEMETRY_SCHEDULE': {'listen_seconds': 540, 'telemetry_seconds': 60},
            'SET_UHF_TELEMETRY': {'enabled': 1},
            'SET_UHF_TELEMETRY_SET': {'telemetry_set': 1},
        }
        for name, args in commands.items():
            with self.subTest(name=name):
                wire = packet(name, 9, args)
                self.assertEqual(admit_command(wire), (9, (5, 6)))
                self.assertLess(len(waveform(wire, 9)), RATE)

    def test_unsolicited_telemetry_forwards_original_packet_once(self):
        wire = packet('HEARTBEAT', 5, dict(mode=4, configuration=1, telemetry_period_ms=10000))
        bits = np.unpackbits(np.frombuffer(frame(wire, 20), np.uint8))
        symbols = np.repeat(1-2*(np.cumsum(bits)%2).astype(float), RATE//1200)
        raw = np.zeros(4*RATE, np.complex64)
        raw[RATE:RATE+len(symbols)] = symbols*np.exp(-2j*np.pi*7000*np.arange(len(symbols))/RATE)
        sink, seen = Mock(), Recent(8, 30)
        self.assertEqual(forward_window(raw, sink, seen), 1)
        self.assertEqual(forward_window(raw, sink, seen), 0)
        sink.sendto.assert_called_once_with(wire, DOWNLINK)
