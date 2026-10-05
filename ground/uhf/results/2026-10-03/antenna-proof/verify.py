"""Verify antenna telemetry and preserve the failed forwarding gate separately."""
import base64
import hashlib
import json
import math
import re
import statistics
from datetime import datetime
from pathlib import Path

p = Path(__file__).resolve().parent
def read(name):
    return json.loads((p / name).read_text())
def rows(name):
    return [json.loads(x) for x in (p / name).read_text().splitlines()]
def spectrum(name):
    data = rows(name)
    off = [r for r in data if r['expected_tone_hz'] == 0 and 1 < r['tx_relative_seconds'] % 6 < 5]
    result = {}
    for hz in (5000, 11000):
        key = str(hz)
        on = [r for r in data if r['expected_tone_hz'] == hz and 1 < r['tx_relative_seconds'] % 6 < 5]
        result[key] = dict(
            on_off_db=10 * math.log10(statistics.median(r['tones'][key]['power'] for r in on) /
                                    statistics.median(r['tones'][key]['power'] for r in off)),
            spectral_snr_db=statistics.median(r['tones'][key]['snr_db'] for r in on),
            peak_hz=statistics.median(r['tones'][key]['peak_hz'] for r in on))
    return result

radio = read('radio/result.json')
assert radio['error'] is None and radio['cleanup_errors'] == []
assert radio['status']['rx_async_events'] == radio['status']['tx_async_events'] == {}
assert radio['status']['accepted'] == radio['status']['emitted'] == 3
assert radio['status']['queued'] == radio['status']['expired'] == 0
assert all(radio['udp_delta'][k] == 0 for k in ('InErrors', 'RcvbufErrors', 'SndbufErrors'))
assert not re.search(r'underflows occurred|overflows occurred|Traceback|cmd time errors',
                     (p / 'radio/console.log').read_text())
h = radio['status']['headroom']
assert h['invalid'] == h['telemetry_clipped'] == 0
assert h['forward_peak_after'] <= .250001 and h['output_peak'] <= .400001
assert h['samples'] == radio['status']['output_samples']
for folder in ('', 'direct-01/', 'direct-02/'):
    c = read(folder + 'capture.json')
    assert c['errors'] == [] and c['dropped_decode_windows'] == 0 and c['decoder_exitcode'] == 0
    t = read(folder + 'uplink-probe.json')
    assert t['error'] is None and t['tx_async_events'] == {}

ihu = rows('ihu/packets.jsonl')
can = rows('can/packets.jsonl')
rf = read('decoder.json')['packets']
assert len(ihu) == len(can) == len(rf) == 3
originals = {r['hex']: r for r in ihu}
can_by_hex = {r['hex']: r for r in can}
assert set(originals) == set(can_by_hex) == {r['hex'] for r in rf}
archive = read('archive.json')['packet']
identities = []
for packet in rf:
    tx = read(f"forward/tx-{packet['sequence']:03}.json")
    original = originals[packet['hex']]
    assert original['request'] == can_by_hex[packet['hex']]['request']
    assert tx['hex'] == packet['hex']
    digest = hashlib.sha256(bytes.fromhex(packet['hex'])).hexdigest()
    assert original['sha256'] == tx['sha256'] == packet['sha256'] == digest
    at = datetime.fromisoformat(packet['received_utc'])
    matches = [a for a in archive if a['link'] == 'eps-uhf-in'
               and base64.b64decode(a['packet']).hex() == packet['hex']
               and abs((datetime.fromisoformat(a['receptionTime'].replace('Z', '+00:00')) - at).total_seconds()) < 1]
    assert len(matches) == 1
    identities.append(dict(inner_sequence=packet['decoded']['sequence'], sha256=digest,
                           yamcs_reception=matches[0]['receptionTime']))

translated = spectrum('repeater-spectrum.jsonl')
ground_control = spectrum('direct-02/repeater-spectrum.jsonl')
forwarding_pass = all(t['on_off_db'] > 10 and t['spectral_snr_db'] > 15 for t in translated.values())
assert forwarding_pass is False
assert all(t['on_off_db'] > 10 and t['spectral_snr_db'] > 15 for t in ground_control.values())
input_capture = read('input-02/result.json')
assert input_capture['samples'] == 76800 * 24
candidate = [r for r in input_capture['measurements'] if abs(r['tones']['5000']['peak_hz'] - 4200) < 100
             and r['tones']['5000']['snr_db'] > 10]
assert len(candidate) >= 5
weak = dict(candidate_measurements=len(candidate),
            candidate_frequency_hz=statistics.median(r['tones']['5000']['peak_hz'] for r in candidate),
            median_candidate_snr_db=statistics.median(r['tones']['5000']['snr_db'] for r in candidate),
            first_seconds=candidate[0]['seconds'], last_seconds=candidate[-1]['seconds'],
            max_5000_window_snr_db=max(r['tones']['5000']['snr_db'] for r in input_capture['measurements']),
            max_11000_window_snr_db=max(r['tones']['11000']['snr_db'] for r in input_capture['measurements']))
assert 'ValueError: block_detail::n_output_items' in (p / 'input-01/console.log').read_text()
assert 'PASS_SINK_INPUT_COUNTER' in (p / 'sink-counter-test.txt').read_text()
cleanup = (p / 'cleanup.txt').read_text()
assert 'claimed: False' in cleanup and 'LIBRESDR_FREE' in cleanup and 'RADIO_CONTROL_CLOSED' in cleanup
assert cleanup.count('state DOWN') == 2
assert read('capture.json')['fpga_sha256'] in cleanup
assert (p / 'amsat-git-status.txt').read_text() == ''
for name, digest in read('tools-sha256.json').items():
    assert hashlib.sha256((p / 'tools' / name).read_bytes()).hexdigest() == digest

result = dict(
    status='TELEMETRY_PASS_ANTENNA_FORWARDING_GATE_FAILED',
    physical_setup='Operator-confirmed antennas restored on LibreSDR TXA and SDRB antenna_in; SDRB TX1 Direct and LibreSDR RX antennas unchanged',
    operator_reported_antennas=dict(libresdr='stock antennas; bands unverified',sdrb='tiny Wi-Fi/900 MHz antenna',separation_inches=12),
    settings=radio['settings'], actual=radio['actual'], stream_seconds=radio['elapsed_seconds'],
    fresh_packets=3, all_original_bytes_matched_at_ihu_can_socket_rf_yamcs=True, identities=identities,
    rx_async_events=radio['status']['rx_async_events'], tx_async_events=radio['status']['tx_async_events'],
    udp_delta=radio['udp_delta'], headroom=h,
    translated_tones=translated, antenna_forwarding_pass=forwarding_pass,
    ground_local_tones=ground_control, receive_only_weak_candidate=weak,
    conclusion='Fresh telemetry remains clean over the antenna downlink, but the antenna uplink-forwarding gate did not pass. Receive-only SDRB shows a weak repeated candidate consistent with the previously measured uplink frequency offset. Antenna/link margin and duplex isolation remain unresolved; SSB check held.',
    next_step='Identify uplink antenna models/bands and spacing, inspect the physical feeds, then agree one bounded check after a concrete setup change.',
    limits=[
        'One59.88second transponder check; no SSB/voice, endurance or uplink-command qualification.',
        'Two24second local-ground tone checks: the first accompanied an invalid SDRB helper run, the second the corrected receiver-only capture. Local tones can include TX leakage and do not prove antenna efficiency or radiated power.',
        'First SDRB receive-only helper used nitems_written on a sink and aborted; retained as invalid evidence. Corrected helper uses nitems_read and completed24seconds with1843200samples.',
        'Receiver-only time is not aligned to ground TX timestamps; the late11kHz slot has limited overlap. The weak5kHz candidate is not a calibrated gain or self-interference measurement.',
        'Reported stream-error qualification applies to the transponder service. The diagnostic receiver-only helper lacks explicit RX async counters.',
        'No driver/clock, AMSAT core, boot, FPGA or rootfs library changes. Previous conducted results do not qualify this antenna setup.',
        'Yamcs archive byte identity is verified; the previously paused EPS proof display was not updated.'])
(p / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
