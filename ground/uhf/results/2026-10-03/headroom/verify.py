"""Recompute the bounded native headroom and telemetry proof offline."""
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

radio = read('radio/result.json')
h = radio['status']['headroom']
assert radio['error'] is None and radio['cleanup_errors'] == []
assert radio['status']['rx_async_events'] == radio['status']['tx_async_events'] == {}
assert radio['status']['accepted'] == radio['status']['emitted'] == 3
assert radio['status']['expired'] == radio['status']['queued'] == 0
assert all(radio['udp_delta'][k] == 0 for k in ('InErrors', 'RcvbufErrors', 'SndbufErrors'))
assert h['samples'] == radio['status']['output_samples'] and h['samples'] > 30_000_000
assert h['forwarded_clipped'] > 0 and h['forward_peak_before'] > .25
assert h['telemetry_clipped'] == h['invalid'] == 0
assert h['forward_peak_after'] <= .250001 and h['output_peak'] <= .400001
assert not re.search(r'underflows occurred|overflows occurred|Traceback|cmd time errors',
                     (p / 'radio/console.log').read_text())
capture = read('capture.json')
assert capture['errors'] == [] and capture['dropped_decode_windows'] == 0
assert capture['decoder_exitcode'] == 0
stimulus = read('uplink-probe.json')
assert stimulus['error'] is None and stimulus['tx_async_events'] == {}
assert stimulus['uplink_peaks'] == {'5000': .015, '11000': .15}

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

spectrum = rows('repeater-spectrum.jsonl')
silent = [r for r in spectrum if r['expected_tone_hz'] == 0 and 1 < r['tx_relative_seconds'] % 6 < 5]
tones = {}
for hz in (5000, 11000):
    key = str(hz)
    active = [r for r in spectrum if r['expected_tone_hz'] == hz and 1 < r['tx_relative_seconds'] % 6 < 5]
    on = statistics.median(r['tones'][key]['power'] for r in active)
    off = statistics.median(r['tones'][key]['power'] for r in silent)
    tones[key] = dict(on_off_db=10 * math.log10(on / off),
                      spectral_snr_db=statistics.median(r['tones'][key]['snr_db'] for r in active),
                      peak_hz=statistics.median(r['tones'][key]['peak_hz'] for r in active))
    assert abs(tones[key]['peak_hz'] - hz) < 500

native = (p / 'native-software.log').read_text()
assert 'PASS_GNU_RADIO_NATIVE_HEADROOM' in native
assert 'PASS_NATIVE_FILTERED_FORWARDING_PLUS_BINARY_INJECTION' in native
assert 'Ran 9 tests' in (p / 'software-tests.txt').read_text()
assert '\nOK\n' in (p / 'software-tests.txt').read_text()
assert (p / 'amsat-git-status.txt').read_text() == ''
cleanup = (p / 'cleanup.txt').read_text()
assert 'claimed: False' in cleanup and 'RADIO_CONTROL_CLOSED' in cleanup
assert cleanup.count('state DOWN') == 2
assert capture['fpga_sha256'] in cleanup
build = read('build.json')
assert build['core_test'].startswith('PASS_CORE_')
for name, digest in build['sources'].items():
    assert hashlib.sha256((p / 'tools' / name).read_bytes()).hexdigest() == digest
for name, digest in read('tools-sha256.json').items():
    assert hashlib.sha256((p / 'tools' / name).read_bytes()).hexdigest() == digest

result = dict(
    status='PASS_BOUNDED_NATIVE_HEADROOM_WITH_FRESH_UHF_TELEMETRY',
    stream_seconds=radio['elapsed_seconds'], settings=radio['settings'], actual=radio['actual'],
    headroom=h, forwarded_clipped_fraction=h['forwarded_clipped'] / h['samples'],
    rx_async_events=radio['status']['rx_async_events'], tx_async_events=radio['status']['tx_async_events'],
    udp_delta=radio['udp_delta'], tones=tones, fresh_packets=3, identities=identities,
    all_original_bytes_matched_at_ihu_can_socket_rf_yamcs=True,
    software_tests=9, native_arithmetic_and_gnuradio_packet_mix_passed=True,
    native_module_sha256=build['module_sha256'],
    physical_setup='Operator-confirmed LibreSDR TXA through DC blocks and approximately40dB attenuation to SDRB antenna_in; downlink remains antennas',
    implementation='Opt-in compiled GNU Radio two-input mixer replaces Add in the optional application; no additional stream blocks, Python work callbacks or radio image changes',
    limits=[
        'One60.6second stress check; this is not endurance qualification or a permanent cure for all U/O workloads.',
        'Aggregate clip counts do not isolate individual tone slots or establish calibrated RF power, analog input headroom or self-interference.',
        'Weak-signal transparency and phase preservation are proven in software. RF tones were detected; RF gain linearity and multi-signal/SSB distortion remain unqualified.',
        'This is a hard magnitude bound, not an AGC. Frequent limiting at the stress gains is unsuitable evidence for linear amateur service.',
        'All-antenna uplink and voice/SSB still require separate bounded checks after physical antenna restoration.',
        'Real IHU packets were triggered over USB by the host; no autonomous IHU scheduling or uplink commands.',
        'Yamcs archive byte identity is verified; the previously paused EPS display was not updated for this run.',
        'AMSAT source, boot, FPGA, rootfs libraries and LTE image remain unchanged. Default application path retains the prior adder unless --forward-peak is supplied.'])
(p / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
