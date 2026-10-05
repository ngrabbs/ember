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
for folder in ('',):
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
forwarding_pass = all(t['on_off_db'] > 10 and t['spectral_snr_db'] > 15 for t in translated.values())
cleanup = (p / 'cleanup.txt').read_text()
assert 'claimed: False' in cleanup and 'LIBRESDR_FREE' in cleanup and 'RADIO_CONTROL_CLOSED' in cleanup
assert cleanup.count('state DOWN') == 2
assert read('capture.json')['fpga_sha256'] in cleanup
assert (p / 'amsat-git-status.txt').read_text() == ''
for name, digest in read('tools-sha256.json').items():
    assert hashlib.sha256((p / 'tools' / name).read_bytes()).hexdigest() == digest

baseline = json.loads((p.parent/'antenna-uhf-swap/result.json').read_text())
comparison_keys=('rate','rx_frequency','rx_gain','tx_frequency','tx_gain','forward_scale','forward_peak','packet_peak','passband','transition')
assert all(radio['settings'][k]==baseline['settings'][k] for k in comparison_keys)
result = dict(
    status='ANTENNA_FORWARDING_PASS' if forwarding_pass else 'TELEMETRY_PASS_BOTH_UHF_ANTENNAS_FORWARDING_GATE_FAILED',
    physical_setup='Operator confirmed UHF antennas on SDRB and LibreSDR, following the request to fit LibreSDR TXA; last reported spacing approximately12inches; no models or calibrated efficiency supplied',
    settings=radio['settings'], actual=radio['actual'], stream_seconds=radio['elapsed_seconds'],
    fresh_packets=3, all_original_bytes_matched_at_ihu_can_socket_rf_yamcs=True, identities=identities,
    rx_async_events=radio['status']['rx_async_events'], tx_async_events=radio['status']['tx_async_events'],
    udp_delta=radio['udp_delta'], headroom=h, translated_tones=translated,
    antenna_forwarding_pass=forwarding_pass, previous_translated_tones=baseline['translated_tones'],
    radio_settings_unchanged=True,
    conclusion='With UHF antennas on both radios,3/3 fresh telemetry packets remained byte-identical through Yamcs with clean stream counters. Forwarded tone on/off contrast was still below1dB; the antenna forwarding gate did not pass. SSB remains pending.',
    next_step='Verify actual LibreSDR TXA output level using an available RF analyzer, then resolve source/receive link margin and duplex isolation. No further automatic gain or rate sweep.',
    limits=['Single finite check, not SSB/voice or endurance qualification.',
        'Operator-confirmed UHF antennas; prior spacing was12inches, not newly measured. No antenna model, calibrated RF power or isolation measurement.',
        'No AMSAT core, clock/driver, boot, FPGA or rootfs library changes; default adder behavior unchanged.',
        'Yamcs archive byte identity checked; the previously paused EPS display was not updated.'])
(p/'result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
