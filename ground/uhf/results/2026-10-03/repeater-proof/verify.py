"""Offline correlation; separates telemetry delivery from repeater RF proof."""
import base64,hashlib,json,math,re,statistics
from datetime import datetime
from pathlib import Path
p=Path(__file__).resolve().parent
archive=json.loads((p/'archive-final.json').read_text())['packet']
profiles=[]
def rows(path):return [json.loads(x) for x in path.read_text().splitlines()]
def tone_summary(path):
    records=rows(path);summary={}
    silent=[r for r in records if r['expected_tone_hz']==0 and 1<r['tx_relative_seconds']%6<5]
    for tone in (5000,11000):
        active=[r for r in records if r['expected_tone_hz']==tone and 1<r['tx_relative_seconds']%6<5]
        key=str(tone)
        on=statistics.median(r['tones'][key]['power'] for r in active)
        off=statistics.median(r['tones'][key]['power'] for r in silent)
        summary[key]=dict(on_off_db=10*math.log10(on/off),median_active_snr_db=statistics.median(r['tones'][key]['snr_db'] for r in active),
            active_measurements=len(active),silent_measurements=len(silent))
    return summary
for name in ('01','02'):
    radio=json.loads((p/f'radio-{name}/result.json').read_text())
    rx=json.loads((p/f'rx-{name}/capture.json').read_text())
    rf=json.loads((p/f'rx-{name}/decoder.json').read_text())['packets']
    ihu=rows(p/f'ihu-{name}/packets.jsonl');can=rows(p/f'can-{name}/packets.jsonl')
    assert len(ihu)==len(can)==len(rf)==8
    identities=[]
    for original,c,r in zip(ihu,can,rf):
        tx=json.loads((p/f"forward-{name}/tx-{r['sequence']:03}.json").read_text())
        assert original['request']==c['request']
        assert original['hex']==c['hex']==tx['hex']==r['hex']
        assert original['sha256']==tx['sha256']==r['sha256']==hashlib.sha256(bytes.fromhex(r['hex'])).hexdigest()
        at=datetime.fromisoformat(r['received_utc'])
        matches=[a for a in archive if a['link']=='eps-uhf-in' and base64.b64decode(a['packet']).hex()==r['hex'] and abs((datetime.fromisoformat(a['receptionTime'].replace('Z','+00:00'))-at).total_seconds())<1]
        assert len(matches)==1
        identities.append(dict(outer_sequence=r['sequence'],inner_sequence=r['decoded']['sequence'],sha256=r['sha256'],yamcs_reception=matches[0]['receptionTime']))
    assert radio['error'] is None and not radio['cleanup_errors'] and not radio['status']['tx_async_events']
    assert radio['status']['emitted']==radio['status']['accepted']==8
    assert radio['status']['expired']==radio['status']['queued']==0
    for key in ('InErrors','RcvbufErrors','SndbufErrors'):assert radio['udp_delta'][key]==0
    assert not re.search(r'underflows occurred|overflows occurred|Traceback|RfnocError',(p/f'radio-{name}/console.log').read_text())
    assert rx['errors']==[] and rx['dropped_decode_windows']==0 and rx['decoder_exitcode']==0
    uplink=json.loads((p/f'rx-{name}/uplink-probe.json').read_text())
    assert uplink['error'] is None and not uplink['tx_async_events']
    summary=tone_summary(p/f'rx-{name}/repeater-spectrum.jsonl')
    assert all(v['on_off_db']<6 for v in summary.values())
    canlog=(p/f'can-{name}/console.log').read_text()
    profiles.append(dict(name=name,stream_seconds=radio['elapsed_seconds'],ihu_interval_seconds=8,generated=8,received_and_archived=8,
        sdrb_rx_gain=radio['settings']['rx_gain'],uplink_tx_gain=uplink['actual']['gain'],stream_errors=0,tones=summary,identities=identities,
        can_shutdown='Interface brought down before finite monitor ended; ENETDOWN reported' if 'Network is down' in canlog else 'No ENETDOWN observed'))
direct={name:tone_summary(p/f'direct-{name}/repeater-spectrum.jsonl') for name in ('01','02','03')}
assert all(v['on_off_db']>25 for v in direct['02'].values())
assert all(v['on_off_db']>25 for v in direct['03'].values())
inputs={}
for name in ('02','03'):
    data=json.loads((p/f'input-{name}/result.json').read_text())
    inputs[name]=dict(settings=data['settings'],samples=data['samples'],max_peak_snr_db=max(r['snr_db'] for r in data['measurements']),
        median_rms=statistics.median(r['rms'] for r in data['measurements']))
    assert inputs[name]['max_peak_snr_db']<20
assert 'CAN_MONITOR_EXIT=0' in (p/'can-cleanup-check.txt').read_text()
assert 'Ran 16 tests' in (p/'software-tests.txt').read_text() and 'OK' in (p/'software-tests.txt').read_text()
assert 'claimed: False' in (p/'cleanup.txt').read_text() and 'RADIO_CONTROL_CLOSED' in (p/'cleanup.txt').read_text()
assert (p/'amsat-git-status.txt').read_text()==''
result=dict(can_natural_stop_check_passed=True,status='PASS_TELEMETRY_CADENCE_AND_BOUNDED_STREAMS__RF_REPEATER_NOT_DEMONSTRATED',
    telemetry_packets=16,byte_identical_at_ihu_can_socket_rf_yamcs=True,software_tests_passed=16,
    profiles=profiles,direct_uplink_measurements=direct,sdrb_receive_only=inputs,
    conclusion='Known uplink detected locally at LibreSDR; neither SDRB RX1 nor RX2 input capture detects a stable tone through the current antenna setup. RF input/feed/route remains unresolved; no repeater qualification.',
    limits=['Two separate approximately94second streams, not a continuous187second reliability run',
        'Host USB triggers existing IHU EPS/CAN packets; no native autonomous IHU scheduler',
        'Local LibreSDR self-reception does not establish signal level at SDRB antenna connector',
        'CAN teardown order generated ENETDOWN after all packets; preserve logs and stop monitor before taking interface down',
        'No AMSAT core/FPGA/boot, LTE or native Yamcs dictionary changes'],
    excluded_attempts={'input-01':'Receive capture began before a direct-check CLI was available; lacks aligned stimulus. Not a source-off/on comparison.'})
(p/'result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ('profiles','direct_uplink_measurements','sdrb_receive_only')},indent=2))
