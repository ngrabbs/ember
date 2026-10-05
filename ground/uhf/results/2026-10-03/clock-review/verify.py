"""Verify recorded clock-profile evidence; performs no radio or network access."""
import base64,hashlib,json,re
from datetime import datetime
from pathlib import Path
p=Path(__file__).resolve().parent
archive=json.loads((p/'archive-final.json').read_text())['packet']
radio=json.loads((p/'radio-04/result.json').read_text())
capture=json.loads((p/'rx-04/capture.json').read_text())
rf=json.loads((p/'rx-04/decoder.json').read_text())['packets']
can=[json.loads(x) for x in (p/'can-04/packets.jsonl').read_text().splitlines()]
ihu=re.findall(r'RESULT request=(\d+) outcome=WALTER_BENCH_RETURN peer=\d+ bytes=128 hex=([0-9a-f]+)',(p/'ihu.txt').read_text())
assert len(can)==len(ihu)==len(rf)==6
identities=[]
for c,(request,hexdata),r in zip(can,ihu,rf):
    tx=json.loads((p/f"forward-04/tx-{r['sequence']:03}.json").read_text())
    assert c['request']==int(request)
    assert c['hex']==hexdata==tx['hex']==r['hex']
    assert tx['sha256']==r['sha256']==hashlib.sha256(bytes.fromhex(hexdata)).hexdigest()
    at=datetime.fromisoformat(r['received_utc'])
    matches=[a for a in archive if a['link']=='eps-uhf-in' and base64.b64decode(a['packet']).hex()==r['hex'] and abs((datetime.fromisoformat(a['receptionTime'].replace('Z','+00:00'))-at).total_seconds())<1]
    assert len(matches)==1,(r['sequence'],matches)
    identities.append(dict(outer_sequence=r['sequence'],inner_sequence=r['decoded']['sequence'],sha256=r['sha256'],yamcs_reception=matches[0]['receptionTime']))
assert radio['error'] is None and not radio['cleanup_errors']
assert radio['status']['emitted']==radio['status']['accepted']==6
assert radio['status']['queued']==radio['status']['expired']==0
assert not radio['status']['tx_async_events']
assert radio['udp_delta']['InErrors']==radio['udp_delta']['RcvbufErrors']==radio['udp_delta']['SndbufErrors']==0
log=(p/'radio-04/console.log').read_text()
assert not re.search(r'underflows occurred|overflows occurred|Traceback|RfnocError',log)
assert capture['errors']==[] and capture['dropped_decode_windows']==0 and capture['decoder_exitcode']==0
assert json.loads((p/'forward-04/status.json').read_text())['service_admitted']==6
assert not json.loads((p/'can-04/status.json').read_text())['application_replies_enabled']
prep=[json.loads(x)['preparation_seconds'] for x in (p/'radio-04/events.jsonl').read_text().splitlines() if json.loads(x)['event']=='QUEUED']
root=p.parents[2]
files=['radio_service.py','packet_radio.py','binary_injector.py','libresdr_live_rx.py','libresdr_rx.py','test_packet_radio.py']
source_hashes={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in files}
assert source_hashes['radio_service.py']==hashlib.sha256((p/'radio_service-final-tested.py').read_bytes()).hexdigest()
result=dict(status='PASS_BOUNDED_TRANSPONDER_NO_STREAM_ERRORS_AND_SIX_FRESH_PACKETS',
 duration_seconds=radio['elapsed_seconds'],sdrb_rate_hz=radio['actual']['rx_rate'],samples_per_symbol=512,
 libresdr_master_clock_hz=capture['master_clock_hz'],libresdr_hardware_decimation=capture['hardware_decimation'],
 tx_async_events=radio['status']['tx_async_events'],reported_rx_overflows=0,udp_receive_errors=0,
 submitted=6,received=6,byte_identical_at_ihu_can_socket_rf_yamcs=True,identities=identities,
 preparation_seconds=dict(min=min(prep),max=max(prep)),source_sha256=source_hashes,software_tests_passed=14,
 baseline_sdrb_commit='543d3f6d77d278e19badd728d8e32d6f974b2586',upstream_uhd_commit='308126a479ca19dfaebfe4784b375e608788d763',
 changes=['Automatic master clocks; post-configuration shared-clock readback','614400S/s profile;512 samples/symbol; matched analog bandwidth','8000byte local CHDR frames;1024 RX samples/packet','250ms timed TX startup','Tone-table waveform preparation','Recorded TX async events and Linux UDP counters','1.35x weak-burst envelope admission with unchanged CRC validation; telemetry peak0.12'],
 earlier_radio03=dict(duration_seconds=111.57523704499908,submitted=6,received_live=3,additional_offline_recoveries=2,stream_errors=0,packet_peak=.08),
 limits=['93.24second integrated antenna bench observation; not indefinite reliability qualification','Does not qualify1.5/4.608MS/s or arbitrary CPU load','No independent amateur RF uplink forwarding test','No physical external-reference selection or FPGA/core/boot changes'],
 excluded_attempts={'radio-01':'Existing receiver output directory; zero admitted packets','radio-02':'CAN duration130 exceeded monitor bound120; zero admitted packets; separate clean radio observation'})
(p/'result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
