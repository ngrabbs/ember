"""Recompute conducted-uplink and original-packet delivery evidence offline."""
import base64,hashlib,json,math,re,statistics
from datetime import datetime
from pathlib import Path

p=Path(__file__).resolve().parent
def read(path):return json.loads((p/path).read_text())
def rows(path):return [json.loads(x) for x in (p/path).read_text().splitlines()]
def tones(path):
    data=rows(path)
    silent=[r for r in data if r['expected_tone_hz']==0 and 1<r['tx_relative_seconds']%6<5]
    result={}
    for frequency in (5000,11000):
        active=[r for r in data if r['expected_tone_hz']==frequency and 1<r['tx_relative_seconds']%6<5]
        key=str(frequency)
        on=statistics.median(r['tones'][key]['power'] for r in active)
        off=statistics.median(r['tones'][key]['power'] for r in silent)
        result[key]=dict(on_off_db=10*math.log10(on/off),
            median_active_snr_db=statistics.median(r['tones'][key]['snr_db'] for r in active),
            median_peak_hz=statistics.median(r['tones'][key]['peak_hz'] for r in active),
            active_measurements=len(active),silent_measurements=len(silent))
    return result

archive=read('archive-final.json')['packet']
profiles=[]
for name,generated,received in [('03',8,8),('04',4,0),('05',3,3),('08',3,3),('09',3,3)]:
    radio=read(f'radio-{name}/result.json');capture=read(f'rx-{name}/capture.json')
    rf=read(f'rx-{name}/decoder.json')['packets']
    ihu=rows(f'ihu-{name}/packets.jsonl');can=rows(f'can-{name}/packets.jsonl')
    assert len(ihu)==len(can)==generated and len(rf)==received
    originals={r['hex']:r for r in ihu};can_by_hex={r['hex']:r for r in can}
    assert set(originals)==set(can_by_hex)
    identities=[]
    for packet in rf:
        tx=read(f"forward-{name}/tx-{packet['sequence']:03}.json")
        original=originals[packet['hex']];c=can_by_hex[packet['hex']]
        assert original['request']==c['request']
        assert original['hex']==c['hex']==tx['hex']==packet['hex']
        digest=hashlib.sha256(bytes.fromhex(packet['hex'])).hexdigest()
        assert original['sha256']==tx['sha256']==packet['sha256']==digest
        at=datetime.fromisoformat(packet['received_utc'])
        matches=[a for a in archive if a['link']=='eps-uhf-in'
            and base64.b64decode(a['packet']).hex()==packet['hex']
            and abs((datetime.fromisoformat(a['receptionTime'].replace('Z','+00:00'))-at).total_seconds())<1]
        assert len(matches)==1
        identities.append(dict(outer_sequence=packet['sequence'],inner_sequence=packet['decoded']['sequence'],
            sha256=digest,yamcs_reception=matches[0]['receptionTime']))
    assert radio['error'] is None and not radio['cleanup_errors'] and not radio['status']['tx_async_events']
    assert radio['status']['accepted']==radio['status']['emitted']==generated
    assert radio['status']['expired']==radio['status']['queued']==0
    log=(p/f'radio-{name}/console.log').read_text()
    reported_rx_overflows=sum(map(int,re.findall(r'(\d+) overflows occurred',log)))
    if name=='08':
        assert radio['udp_delta']['InErrors']==radio['udp_delta']['RcvbufErrors']==28
        assert reported_rx_overflows==6
    else:
        assert all(radio['udp_delta'][k]==0 for k in ('InErrors','RcvbufErrors','SndbufErrors'))
        assert not re.search(r'underflows occurred|overflows occurred|Traceback|RfnocError|cmd time errors',log)
    assert capture['errors']==[] and capture['dropped_decode_windows']==0 and capture['decoder_exitcode']==0
    stimulus=read(f'rx-{name}/uplink-probe.json')
    assert stimulus['error'] is None and not stimulus['tx_async_events']
    assert 'Network is down' not in (p/f'can-{name}/console.log').read_text()
    measurements=tones(f'rx-{name}/repeater-spectrum.jsonl')
    if name in ('05','08','09'):
        assert all(r['on_off_db']>10 and r['median_active_snr_db']>15
            and abs(r['median_peak_hz']-int(f))<500 for f,r in measurements.items())
    else:assert all(r['on_off_db']<6 for r in measurements.values())
    if name=='09':assert radio['status']['rx_async_events']=={}
    limiter=radio['status'].get('forward_limiter')
    if name=='08':
        assert limiter and limiter['error'] is None and limiter['limit']==.25 and math.isclose(limiter['component_limit']*math.sqrt(2),.25)
        assert limiter['samples']>=radio['status']['output_samples']
    profiles.append(dict(name=name,settings=radio['settings'],stream_seconds=radio['elapsed_seconds'],
        generated=generated,received_and_archived=received,reported_rx_overflows=reported_rx_overflows,
        udp_delta=radio['udp_delta'],tones=measurements,
        qualifies_clean_stream=name!='08',tx_async_events=radio['status']['tx_async_events'],
        rx_async_events=radio['status'].get('rx_async_events'),
        forward_limiter=limiter,identities=identities))

input_capture=read('input-05/result.json')
input_tones={str(tone):[r for r in input_capture['measurements'] if abs(r['peak_hz']-tone)<100 and r['snr_db']>30]
    for tone in (4200,10200)}
assert all(len(r)>2 for r in input_tones.values())
failed=read('radio-06/result.json')
assert failed['error'] and failed['status']['tx_async_events'].get('underflow')
assert failed['status']['tx_async_events'].get('time_error')
assert len(rows('ihu-06/packets.jsonl'))==3
assert len(read('rx-06/decoder.json')['packets'])==0
clock=read('timekeeper.json');assert abs(clock['ratio']-1)<.02
assert 'PASS_NATIVE_FILTERED_FORWARDING_PLUS_BINARY_INJECTION' in (p/'native-mix.log').read_text()
assert 'Ran 9 tests' in (p/'software-tests.txt').read_text() and 'OK' in (p/'software-tests.txt').read_text()
failed_batch=read('radio-07/result.json')
assert failed_batch['error'] and failed_batch['status']['accepted']==0
assert failed_batch['elapsed_seconds']<5
assert (p/'amsat-git-status.txt').read_text()==''
cleanup=(p/'cleanup.txt').read_text()
assert 'claimed: False' in cleanup and 'RADIO_CONTROL_CLOSED' in cleanup
assert 'state DOWN' in cleanup
assert '7f0e329b4724e0d919a06b9924aaa3c77305b6f25038deebd6171657ac7c8a99' in cleanup
for name,digest in read('tools-sha256.json').items():
    assert hashlib.sha256((p/'tools'/name).read_bytes()).hexdigest()==digest

result=dict(status='PASS_BOUNDED_CONDUCTED_UPLINK_FORWARDING_PLUS_FRESH_TELEMETRY',
    physical_setup='Operator-confirmed LibreSDR TXA/channel0 through DC blocks and approximately40dB attenuation to SDRB antenna_in; downlink remains antennas',
    tested_application='radio_service.py with forward_scale16,250ms TX priming, explicit RX/TX async counts and fail-closed errors; no limiter in active sample path',
    profiles=profiles,telemetry_generated=24,telemetry_received_and_archived=17,
    final_application_generated=3,final_application_received_and_archived=3,
    all_received_packets_byte_identical_at_ihu_can_socket_rf_yamcs=True,hardware_timekeeper=clock,
    software_tests_passed=9,native_software_filter_and_packet_mix_passed=True,
    conclusion='Conducted uplink is detectable at SDRB. Raising digital forwarding scale from .5 to16 made both translated tones observable while fresh telemetry reached Yamcs. This resolves the bounded bench forwarding gate, not flight reliability.',
    excluded_diagnostics={
        'duplex-iq-01':'Extra file/FIR branches produced TX underflow and continuous late-command errors; RF output invalid despite tones in software IQ.',
        'duplex-iq-02':'One-second priming did not cure instrumented graph errors; RX overflow and TX underflow/late commands. Excluded from error-free stream claims.',
        'radio-08':'Native limiter with one-second priming delivered tones and3/3 packets but logged six RX overflows and28UDP receive-buffer drops; not a clean stream qualification. Removed from active application.',
        'radio-06':'Unbatched Python limiter caused underflow, late TX commands, RX overflows and control timeout; stopped without admitting packets. Excluded from final qualification.',
        'radio-07':'Batching the Python limiter still hit a startup underflow/late commands; fail-closed TX event handling stopped the session in1.42seconds before readiness or IHU triggers.',
        'radio-04':'Lowering SDRB TX gain70 to40 lost all four telemetry packets; does not isolate self-interference.'},
    limits=['Two gain-only tone/packet checks,05 and09; final application checked in one finite stream. Native limiter08 delivered packets but had RX/UDP errors and is excluded from the clean-profile claim.',
        'No all-antenna uplink proof, calibrated RF power, voice/SSB test, uplink commands, FEC or endurance qualification.',
        'Host USB triggers real IHU telemetry; no native autonomous IHU scheduler.',
        'Input gain/forward scale require bench-specific link budgeting and manual amplitude headroom checks. No qualified limiter/AGC in active application; strong input remains unqualified.',
        'No AMSAT core, FPGA, boot, LTE or Yamcs dictionary changes.'])
(p/'result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ('profiles','excluded_diagnostics','hardware_timekeeper')},indent=2))
