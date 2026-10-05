"""Verify finite HT bench telemetry; operator repeater observation is separate."""
import base64,hashlib,json,re
from datetime import datetime
from pathlib import Path
p=Path(__file__).resolve().parent

def read(name):return json.loads((p/name).read_text())
def rows(name):return [json.loads(x) for x in (p/name).read_text().splitlines()]

radio=read('radio/result.json');window=read('window.json');capture=read('capture.json')
assert window['requested_seconds']==180 and not window['completed']
assert read('session.json')['error']=='Ground receiver ended before test window'
assert read('session.json')['ground_returncode']==0
assert radio['elapsed_seconds']>=180
assert radio['error'] is None and radio['cleanup_errors']==[]
s=radio['status']
assert s['accepted']==s['emitted']==9 and s['queued']==s['expired']==0
assert s['rx_async_events']==s['tx_async_events']=={}
assert all(radio['udp_delta'][k]==0 for k in ('InErrors','RcvbufErrors','SndbufErrors'))
assert not re.search(r'underflows occurred|overflows occurred|Traceback|cmd time errors',(p/'radio/console.log').read_text())
h=s['headroom'];assert h['invalid']==h['telemetry_clipped']==0
assert h['forward_peak_after']<=.250001 and h['output_peak']<=.400001
assert h['samples']==s['output_samples']
assert capture['errors']==[] and capture['dropped_decode_windows']==0 and capture['decoder_exitcode']==0
assert read('can/status.json')['fragment_errors']==read('can/status.json')['fragment_timeouts']==0
f=read('forward/status.json')
assert f['accepted']==f['service_admitted']==9 and f['local_tx_failed']==f['queue_full']==f['untransmitted']==0
assert f['worker_stopped']
ihu=rows('ihu/packets.jsonl');can=rows('can/packets.jsonl');rf=read('decoder.json')['packets']
assert len(ihu)==len(can)==len(rf)==9
assert read('ihu/result.json')['error'] is None
originals={x['hex']:x for x in ihu};can_by_hex={x['hex']:x for x in can}
assert set(originals)==set(can_by_hex)=={x['hex'] for x in rf}
archive=read('archive.json')['packet'];identities=[]
for packet in rf:
    raw=bytes.fromhex(packet['hex']);digest=hashlib.sha256(raw).hexdigest()
    original=originals[packet['hex']];tx=read(f"forward/tx-{packet['sequence']:03}.json")
    assert original['request']==can_by_hex[packet['hex']]['request']
    assert tx['hex']==packet['hex'] and original['sha256']==tx['sha256']==packet['sha256']==digest
    at=datetime.fromisoformat(packet['received_utc'])
    matches=[x for x in archive if x['link']=='eps-uhf-in' and base64.b64decode(x['packet'])==raw and abs((datetime.fromisoformat(x['receptionTime'].replace('Z','+00:00'))-at).total_seconds())<1]
    assert len(matches)==1
    identities.append(dict(inner_sequence=packet['decoded']['sequence'],sha256=digest,yamcs_reception=matches[0]['receptionTime']))
cleanup=(p/'cleanup.txt').read_text()
assert 'claimed: False' in cleanup and 'LIBRESDR_FREE' in cleanup and 'RADIO_CONTROL_CLOSED' in cleanup
assert cleanup.count('state DOWN')==2 and capture['fpga_sha256'] in cleanup
assert (p/'amsat-git-status.txt').read_text()==''
for name,digest in read('tools-sha256.json').items():assert hashlib.sha256((p/'tools'/name).read_bytes()).hexdigest()==digest
observation=read('operator_observation.json')
assert observation['observed_forwarding'] and observation['observed_continuity_during_test']
result=dict(status='HT_FORWARDING_OPERATOR_OBSERVED_TELEMETRY_AND_STREAM_PASS_OBSERVATION_WINDOW_ENDED_EARLY',
    physical_setup='Operator confirmed UHF antennas on both radios; external HT uplink and RTL-SDR downlink observation requested. LibreSDR receive-only.',
    operator_observation=observation,test_window=window,orchestration=read('session.json'),settings=radio['settings'],actual=radio['actual'],radio_stream_seconds=radio['elapsed_seconds'],
    fresh_packets=9,all_original_bytes_matched_at_ihu_can_socket_rf_yamcs=True,identities=identities,
    rx_async_events=s['rx_async_events'],tx_async_events=s['tx_async_events'],udp_delta=radio['udp_delta'],headroom=h,
    ground_capture=capture,
    limits=['The ground receiver lifetime started before radio setup and exhausted before the advertised180s observation window. The window ended early; radio stream duration is verified separately.',
            'External HT transmit timing, modulation and received RTL-SDR signal/audio were not recorded by these applications; operator observation is separate.',
            'Telemetry receiver captures its own low-rate band; this does not independently measure translated HT spectral quality.',
            'Finite three-minute window; not indefinite or SSB qualification.',
            'Optional bench time limits extended to600s; no AMSAT core/image/FPGA/rootfs changes.',
            'Yamcs archive verified; the old paused EPS proof display was not advanced.'])
(p/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
