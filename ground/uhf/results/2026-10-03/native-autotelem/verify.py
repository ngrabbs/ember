"""Verify native scheduling, closed USB endpoint, UHF delivery and cleanup."""
import base64,hashlib,json,re
from datetime import datetime
from pathlib import Path
p=Path(__file__).resolve().parent

def read(name):return json.loads((p/name).read_text())
def rows(name):return [json.loads(x) for x in (p/name).read_text().splitlines()]

radio=read('radio/result.json');capture=read('capture.json');s=radio['status']
assert read('session.json')['error'] is None and read('session.json')['ground_returncode']==0
assert radio['error'] is None and radio['cleanup_errors']==[]
assert s['accepted']==s['emitted']==4 and s['queued']==s['expired']==0
assert s['rx_async_events']==s['tx_async_events']=={}
assert all(radio['udp_delta'][k]==0 for k in ('InErrors','RcvbufErrors','SndbufErrors'))
assert not re.search(r'underflows occurred|overflows occurred|Traceback|cmd time errors',(p/'radio/console.log').read_text())
h=s['headroom'];assert h['invalid']==h['telemetry_clipped']==h['forwarded_clipped']==0
assert h['forward_peak_after']<=.250001 and h['output_peak']<=.400001
assert capture['errors']==[] and capture['dropped_decode_windows']==0 and capture['decoder_exitcode']==0
cs=read('can/status.json');assert cs['fragment_errors']==cs['fragment_timeouts']==0
f=read('forward/status.json')
assert f['accepted']==f['service_admitted']==4 and f['local_tx_failed']==f['queue_full']==f['untransmitted']==0
assert f['worker_stopped']
pre=read('firmware/postflash-preflight.json');assert pre['passed'] and pre['boot_disabled'] and pre['manual_still_works_with_timer_disabled']
identity=read('firmware/build-identity.json');assert identity['flash_readback_verified'] and identity['flash_id']=='DF641455DB822427'
for source,name in [('firmware/can_feather_bench/main.c','main.c'),('firmware/can_feather_bench/autotelem.h','autotelem.h'),('firmware/can_feather_bench/CMakeLists.txt','CMakeLists.txt')]:
    assert hashlib.sha256((p/'tools'/name).read_bytes()).hexdigest()==identity['files'][source]
assert 'OK' in (p/'firmware/flash.log').read_text() and 'OK' in (p/'firmware/backup.log').read_text()
i=read('ihu/result.json');assert i['error'] is None and i['count']==3 and i['host_telemetry_triggers']==0
assert i['initial_status']['boot']==pre['boot']==i['final_status']['boot']
assert 'AUTOTELEM enabled=0' in i['timer_off_reply'] and 'submitted=3' in i['timer_off_reply']
assert 'eps telemetry' not in (p/'ihu/ihu.txt').read_text()
closed=read('closed-usb/result.json');assert closed['passed'] and closed['host_telemetry_triggers']==0 and closed['usb_console_closed_seconds']>=25
assert closed['before']['submitted']==3 and closed['after']['submitted']==4 and closed['after']['enabled']==0
assert closed['after']['failed']==closed['after']['skipped']==0 and closed['boot']==pre['boot']
final_text=(p/'firmware/final-ihu-status.txt').read_text()
final_auto=re.search(r'AUTOTELEM ([^\r\n]+)',final_text)[1]
final_auto={k:int(v) for k,v in re.findall(r'(\w+)=(\d+)',final_auto)}
assert final_auto['enabled']==0 and final_auto['submitted']==final_auto['due']==4
assert final_auto['pending']==final_auto['failed']==final_auto['skipped']==0
assert final_auto['uptime_ms']-closed['after']['uptime_ms']>20000
ihu=rows('ihu/packets.jsonl');can=rows('can/packets.jsonl');rf=read('decoder.json')['packets']
assert len(ihu)==3 and len(can)==len(rf)==4
originals={x['hex']:x for x in ihu};can_by_hex={x['hex']:x for x in can}
assert set(originals)<=set(can_by_hex)=={x['hex'] for x in rf}
assert all(not x['application_replies_enabled'] for x in can)
intervals=[b['ihu_uptime_ms']-a['ihu_uptime_ms'] for a,b in zip(ihu,ihu[1:])]
assert all(abs(x-20000)<=100 for x in intervals)
archive=read('archive.json')['packet'];identities=[]
for packet in rf:
    raw=bytes.fromhex(packet['hex']);digest=hashlib.sha256(raw).hexdigest()
    tx=read(f"forward/tx-{packet['sequence']:03}.json")
    assert tx['hex']==packet['hex'] and tx['sha256']==packet['sha256']==digest
    assert packet['decoded']['header']['source_boot_id']==pre['boot']
    if packet['hex'] in originals:
        original=originals[packet['hex']];assert original['request']==can_by_hex[packet['hex']]['request'] and original['sha256']==digest
        evidence='IHU timer submission and returned bytes/CAN/socket/RF/Yamcs'
    else:
        assert packet['decoded']['sequence']==4
        uptime=packet['decoded']['header']['uptime_ms']
        assert closed['before']['uptime_ms']<uptime<closed['after']['uptime_ms']
        evidence='Native counter advanced during closed USB interval; CAN/socket/RF/Yamcs byte identity'
    at=datetime.fromisoformat(packet['received_utc'])
    matches=[x for x in archive if x['link']=='eps-uhf-in' and base64.b64decode(x['packet'])==raw and abs((datetime.fromisoformat(x['receptionTime'].replace('Z','+00:00'))-at).total_seconds())<1]
    assert len(matches)==1
    identities.append(dict(inner_sequence=packet['decoded']['sequence'],sha256=digest,yamcs_reception=matches[0]['receptionTime'],source_evidence=evidence))
cleanup=(p/'cleanup.txt').read_text()
assert 'claimed: False' in cleanup and 'LIBRESDR_FREE' in cleanup and 'RADIO_CONTROL_CLOSED' in cleanup
assert cleanup.count('state DOWN')==2 and capture['fpga_sha256'] in cleanup
assert (p/'amsat-git-status.txt').read_text()==''
for name,digest in read('tools-sha256.json').items():assert hashlib.sha256((p/'tools'/name).read_bytes()).hexdigest()==digest
result=dict(status='NATIVE_IHU_AUTOTELEM_CLOSED_USB_UHF_YAMCS_PASS',
    firmware=identity,period_seconds=20,native_packets=4,host_telemetry_triggers=0,
    native_intervals_ms=intervals,identities=identities,usb_console_closed_seconds=closed['usb_console_closed_seconds'],
    disabled_quiet_ms=final_auto['uptime_ms']-closed['after']['uptime_ms'],
    settings=radio['settings'],actual=radio['actual'],radio_stream_seconds=radio['elapsed_seconds'],
    rx_async_events=s['rx_async_events'],tx_async_events=s['tx_async_events'],udp_delta=radio['udp_delta'],headroom=h,
    final_state='Native IHU timer disabled, radios released, CAN0/1 down; no startup services enabled.',
    limits=['IHU CAN bench firmware; not yet the production FreeRTOS flight scheduler.',
            'Timer uses the existing CF_CHAIN peer/COMMS/Walter bench acknowledgement path; it needs normal CAN and a HELLO. No SDRB-aware firmware or protocol changes.',
            'First three packets have IHU returned-byte evidence; fourth has native counter/closed USB timing plus CAN/RF/archive identities, because USB logging was absent.',
            'USB endpoint/DTR closed; physical cable and supplies remained attached.',
            'Finite transponder-mode telemetry test; no new HT/SSB, RF power, outage or endurance qualification.',
            'Yamcs archive identities verified; old paused EPS display not advanced.'])
(p/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
