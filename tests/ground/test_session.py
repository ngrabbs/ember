import base64
import copy
import json
from pathlib import Path
import sys
import unittest
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'ground' / 'ember'))
from codec import encode
from eps_bridge import State
from session import DICTIONARY_HASH, FORMAT, fetch_packets, playback, summary


def record(raw, at='2026-10-02T12:00:01Z', name='HEARTBEAT', link='udp-in'):
    return dict(packet=base64.b64encode(raw).decode(), size=len(raw),
                id=dict(name='/ember/' + name), link=link, sequenceNumber=1,
                generationTime=at, receptionTime=at)


def heartbeat():
    return encode('HEARTBEAT', sequence=16383, source=2, target=1,
                  source_boot_id=7, uptime_ms=1000,
                  payload=dict(mode=3, configuration=1, telemetry_period_ms=1000))


def session(records):
    return dict(format=FORMAT, dictionary_sha256=DICTIONARY_HASH, origin='test fixture',
                start='2026-10-02T12:00:00Z', stop='2026-10-02T12:00:10Z', packets=records)


class SessionTests(unittest.TestCase):
    def test_continuation_preserves_filters_and_orders_reception(self):
        calls = []
        def request(url):
            q = parse_qs(urlparse(url).query)
            calls.append(q)
            if q['name'] == ['/ember/POWER_STATUS']:
                return dict(packets=[])
            if 'next' not in q:
                return dict(packets=[record(heartbeat(), '2026-10-02T12:00:02Z')], continuationToken='page2')
            return dict(packets=[record(heartbeat())])
        result = fetch_packets('http://test', 'start', 'stop', page_size=1, request=request)
        self.assertEqual(result[0]['receptionTime'], '2026-10-02T12:00:01Z')
        self.assertEqual(len(result), 2)
        self.assertEqual({k:v for k,v in calls[1].items() if k != 'next'}, calls[0])
        self.assertEqual(calls[1]['next'], ['page2'])

    def test_repeated_token_fails_instead_of_looping(self):
        with self.assertRaisesRegex(ValueError, 'repeated'):
            fetch_packets('http://test', 'start', 'stop', request=lambda _:dict(continuationToken='same'))

    def test_corrupt_later_packet_emits_nothing(self):
        raw = bytearray(heartbeat())
        raw[-1] ^= 1
        output = []
        with self.assertRaises(ValueError):
            playback(session([record(heartbeat()), record(raw)]), emit=output.append)
        self.assertEqual(output, [])

    def test_replay_timing_and_original_metadata(self):
        data = session([record(heartbeat()), record(heartbeat(), '2026-10-02T12:00:03Z')])
        output, sleeps = [], []
        playback(data, speed=2, emit=output.append, sleep=sleeps.append, monotonic=lambda:0)
        self.assertEqual(sleeps, [1])
        item = json.loads(output[0])
        self.assertEqual(item['mode'], 'OFFLINE_REPLAY')
        self.assertEqual(item['decoded']['sequence'], 16383)
        self.assertEqual(item['recorded_reception_time'], data['packets'][0]['receptionTime'])

    def test_invalid_eps_readouts_remain_invalid(self):
        state = State(cells=2, rsnsb=.01, rsnsi=.01, session=9)
        raw = state.packet(state.started)
        result = summary(session([record(raw, name='POWER_STATUS', link='eps-uart-in')]))
        self.assertEqual(result['streams'][0]['quality'],
                         dict(invalid_or_stale_readout=1, conversion_unavailable=1))

    def test_metadata_dictionary_and_time_mismatch_rejected(self):
        data = session([record(heartbeat())])
        bad = copy.deepcopy(data)
        bad['packets'][0]['size'] += 1
        with self.assertRaises(ValueError): summary(bad)
        bad = copy.deepcopy(data)
        bad['dictionary_sha256'] = 'wrong'
        with self.assertRaises(ValueError): summary(bad)
        bad = copy.deepcopy(data)
        bad['packets'][0]['generationTime'] = bad['stop']
        with self.assertRaises(ValueError): summary(bad)

    def test_command_packet_not_replayed(self):
        raw = encode('SET_PARAMETER', sequence=0, source=1, target=2, source_boot_id=7,
                     uptime_ms=1000, transaction_epoch=1, transaction_id=1,
                     payload=dict(parameter_id=1, value=2000))
        with self.assertRaisesRegex(ValueError, 'housekeeping'):
            playback(session([record(raw, name='SET_PARAMETER')]))


if __name__ == '__main__':
    unittest.main()
