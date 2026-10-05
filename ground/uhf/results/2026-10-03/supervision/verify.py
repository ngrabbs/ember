"""Recompute process controls and the final bounded RF gate; retain failed attempts."""
import base64,hashlib,json
from datetime import datetime
from pathlib import Path
p=Path(__file__).resolve().parent

def read(name):return json.loads((p/name).read_text())
def rows(name):return [json.loads(x) for x in (p/name).read_text().splitlines()]
def check_stopped(state):
 assert state['state']=='STOPPED' and state['error'] is None
 assert all(x['returncode']==0 for x in state['children'].values())

for folder,manifest in [('tools','tools-sha256.json'),('tools-final','tools-final-sha256.json')]:
 for name,digest in read(manifest).items():assert hashlib.sha256((p/folder/name).read_bytes()).hexdigest()==digest
assert read('software-checks.json')['final_supervisor_suite']==dict(passed=7,failed=0,log='supervisor-final-tests.txt',source='tools-final/test_supervisor.py')
assert 'Ran 7 tests' in (p/'supervisor-final-tests.txt').read_text() and '\nOK\n' in (p/'supervisor-final-tests.txt').read_text()
old=read('session.json')['runs'];assert len(old)==2
check_stopped(old[0]['sdrb']);check_stopped(old[0]['ground'])
assert old[0]['sdrb']['run_id']!=old[1]['sdrb']['run_id']
assert old[1]['sdrb']['state']=='FAILED' and old[1]['sdrb']['error']=='forward exited unexpectedly: 0'
assert all(x['returncode']==0 for x in old[1]['sdrb']['children'].values())
for n in (1,2):
 assert read(f'run-{n}/ground/receiver/decoder.json')['decoded_count']==0
 assert read(f'run-{n}/sdrb/radio/result.json')['status']['emitted']==2
 assert 10<read(f'run-{n}/ground/receiver/capture.json')['samples']/2000000<12
assert 'Stopping user@1000.service' in (p/'logout-diagnosis.txt').read_text()
failed=read('run-3/sdrb/radio/result.json');s3=read('run-3/sdrb/supervisor.json')
assert s3['state']=='FAILED' and 'radio exited unexpectedly: 1'==s3['error']
assert failed['status']['accepted']==0 and failed['status']['tx_async_events']['underflow']==1
assert failed['status']['tx_async_events']['time_error']>0 and failed['cleanup_errors']==[]
assert read('attempt-3/session.json')['error'] is not None
session=read('attempt-4/session.json');assert session['error'] is None
run=session['runs'][0];check_stopped(run['sdrb']);check_stopped(run['ground'])
radio=read('run-4/sdrb/radio/result.json');s=radio['status']
assert radio['error'] is None and radio['cleanup_errors']==[]
assert s['accepted']==s['emitted']==2 and s['queued']==s['expired']==s['queue_full']==0
assert s['rx_async_events']==s['tx_async_events']=={}
assert all(radio['udp_delta'][k]==0 for k in ('InErrors','RcvbufErrors','SndbufErrors'))
h=s['headroom'];assert h['invalid']==h['telemetry_clipped']==0 and h['forward_peak_after']<=.250001 and h['output_peak']<=.370001
capture=read('run-4/ground/receiver/capture.json')
assert capture['errors']==[] and capture['dropped_decode_windows']==0 and capture['decoder_exitcode']==0
assert not capture['iq_saved'] and capture['capture_elapsed_seconds']>60
assert abs(capture['capture_elapsed_seconds']-capture['sample_seconds'])<.1
canstatus=read('run-4/sdrb/can/status.json');assert canstatus['fragment_errors']==canstatus['fragment_timeouts']==0
forward=read('run-4/sdrb/forward/status.json')
assert forward['accepted']==forward['service_admitted']==2
assert forward['local_tx_failed']==forward['queue_full']==forward['untransmitted']==0 and forward['worker_stopped']
ihu=read('run-4/ihu/result.json');assert ihu['error'] is None and ihu['count']==2 and ihu['host_telemetry_triggers']==0
assert 'AUTOTELEM enabled=0' in ihu['timer_off_reply']
assert ihu['initial_status']['boot']==ihu['final_status']['boot']==1505720111
original=rows('run-4/ihu/packets.jsonl');can=rows('run-4/sdrb/can/packets.jsonl');rf=read('run-4/ground/receiver/decoder.json')['packets']
assert len(original)==len(can)==len(rf)==2
assert {x['hex'] for x in original}=={x['hex'] for x in can}=={x['hex'] for x in rf}
assert all(not x['application_replies_enabled'] for x in can)
interval=original[1]['ihu_uptime_ms']-original[0]['ihu_uptime_ms'];assert abs(interval-20000)<=100
archive=read('archive.json')['packet'];identities=[]
for row in rf:
 raw=bytes.fromhex(row['hex']);digest=hashlib.sha256(raw).hexdigest()
 tx=read(f"run-4/sdrb/forward/tx-{row['sequence']:03}.json")
 assert tx['hex']==row['hex'] and tx['sha256']==row['sha256']==digest
 at=datetime.fromisoformat(row['received_utc'])
 hits=[x for x in archive if x['link']=='eps-uhf-in' and base64.b64decode(x['packet'])==raw and abs((datetime.fromisoformat(x['receptionTime'].replace('Z','+00:00'))-at).total_seconds())<1]
 assert len(hits)==1
 identities.append(dict(inner_sequence=row['decoded']['sequence'],sha256=digest,yamcs_reception=hits[0]['receptionTime']))
cleanup=(p/'cleanup-final.txt').read_text()
assert 'claimed: False' in cleanup and 'LIBRESDR_FREE' in cleanup and 'RADIO_CONTROL_CLOSED' in cleanup
assert cleanup.count('state DOWN')==2 and cleanup.count('ActiveState=inactive')==cleanup.count('UnitFileState=disabled')==2
assert 'Linger=yes' in cleanup and 'Linger=no' in cleanup
assert capture['fpga_sha256'] in cleanup
assert '0023d715da1fbd80a8f4bd3e64e59d2fe2409736e2ad622c4cfe5ac3e010d99e' in cleanup
assert 'b893aece99f12be0753eaeecfac528fb69265ee48959e51db2bd6d0773ddbcf5' in cleanup
assert (p/'amsat-git-status-final.txt').read_text()==''
result=dict(status='SUPERVISED_NATIVE_TELEMETRY_PASS_STARTUP_RELIABILITY_OPEN',
 software_owner_tests=7,final_native_packets=2,host_telemetry_triggers=0,native_interval_ms=interval,identities=identities,
 radio_stream_seconds=radio['elapsed_seconds'],ground_capture_seconds=capture['capture_elapsed_seconds'],
 rx_async_events=s['rx_async_events'],tx_async_events=s['tx_async_events'],udp_delta=radio['udp_delta'],headroom=h,
 settings=radio['settings'],actual=radio['actual'],
 process_controls=['Explicit start/stop and new manual restart identity passed live.',
 'Deliberately stopping the owned forwarder stopped SDRB radio/CAN without retry.',
 'A real TX startup fault also stopped the entire SDRB role without retry.'],
 earlier_attempts=[dict(runs=[1,2],rf_gate='FAIL',reason='Pi user manager stopped 10 seconds after last SSH logout; each SDRB emitted 2 packets but receiver decoded none.'),
 dict(run=3,rf_gate='FAIL',reason='TX startup underflow=1 and time_error=144; no packet arm occurred. Ground captured 24.13 seconds after linger correction.')],
 changes=['Pi account lingering enabled; UHF units remain disabled at boot.',
 'Passive CAN reader and adapter now initialize before the unchanged timed RF flow.',
 'Receiver capture metadata includes monotonic elapsed time; no IQ is saved in persistent mode.'],
 final_state='IHU timer off, both UHF services inactive/disabled, CAN0/1 down, radio owners released; Pi lingering yes, SDRB lingering no.',
 limits=['One 63.59-second final stream does not establish restart/endurance reliability or fix every underrun.',
 'The startup fault root cause is not established. Startup ordering was changed before one subsequent successful check; no radio DSP/clock/core edit.',
 'SDRB session must remain logged in; no persistent login policy was enabled there.',
 'Native cadence remains bench firmware, opt-in and boot-off; production FreeRTOS scheduler/recovery is separate.',
 'No new HT/SSB or calibrated RF measurement; old paused EPS display was not advanced.',
 'Attempted RuntimeMaxSec runtime property was rejected by both systemd installations. Final check used named one-run fallback stop guards; no property backstop was claimed.',
 'SDRB wall-clock run names use its incorrect 2024 date; chronology and durations use client/ground dates and monotonic time.'])
(p/'result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(status=result['status'],packets=result['final_native_packets'],radio_seconds=result['radio_stream_seconds'],ground_seconds=result['ground_capture_seconds'],identities=identities),indent=2))
