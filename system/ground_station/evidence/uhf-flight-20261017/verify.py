from pathlib import Path
import json,re,base64,collections
from urllib.request import urlopen
r=Path(__file__).resolve().parent
result=json.loads((r/'rx-native.json').read_text());packets=result['packets'];console=(r/'comms.txt').read_text();ihu=(r/'ihu.txt').read_text()
expected=re.findall(r'packet_hex=([0-9a-f]+)',console)
assert len(expected)==13 and len(packets)==13,(len(expected),len(packets))
assert not result['errors'],result['errors']
assert collections.Counter(expected)==collections.Counter(p['hex'] for p in packets)
assert 'UHF_RUN EXPIRED submitted=12 cycles=3' in ihu,ihu[-2500:]
assert '[uhf] STOP queued=0 TX=0' in console
assert 'Si5351_disable=verified_0xFF' in console
api='http://192.168.1.251:8090/api'
rows=json.load(urlopen(api+'/archive/ember/packets?start=2026-10-17T16:00:00Z&limit=100'))['packets']
byhex=collections.defaultdict(list)
for row in rows:byhex[base64.b64decode(row['packet']).hex()].append(row)
matches=[]
for packet in packets:
 rows=byhex[packet['hex']]
 assert len(rows)==1 and rows[0]['link']=='uhf-tm-in',rows
 matches.append({'name':packet['decoded']['name'],'native_sequence':packet['decoded']['sequence'],'rf_sequence':packet['sequence'],'hex':packet['hex'],'archive_reception':rows[0]['receptionTime'],'link':rows[0]['link']})
counts=dict(collections.Counter(p['decoded']['name'] for p in packets))
report={'tested_utc':result['ended_utc'],'route':'IHU native packets -> CAN A -> EMBER COMMS board DBPSK -> LibreSDR -> ember/realtime uhf-tm-in','yamcs_main_commit':'a5db3a0','comms_version':'0.30.0','comms_source':'aff7509ca707547508208f902ef635b928a25cd4','receiver_version':result['receiver_build']['version'],'receiver_sha256':result['receiver_build']['sha256'],'frequency_hz':result['frequency_hz'],'receiver_gain':result['gain'],'receiver_channel':result['channel'],'receiver_antenna':result['antenna'],'ihu_run_seconds':30,'ihu_period_seconds':10,'native_packets_submitted':12,'comms_identity_packets':1,'rf_decoded':len(packets),'yamcs_byte_matches':len(matches),'counts':counts,'receiver_errors':result['errors'],'pipeline_metrics':result.get('pipeline_metrics'),'lower_drive_trial':{'clock_drive_ma':2,'frame_completed':True,'strictly_decoded':0,'note':'Retained failed standalone heartbeat trial; not part of full-run delivery count.'},'standalone_repeat':{'clock_drive_ma':4,'strictly_decoded':1,'yamcs_link':'uhf-tm-in'},'cleanup':{'ihu_run_expired':True,'ihu_stop_confirmed':'UHF_RUN STOPPED' in ihu,'comms_service_stopped':True,'clock_outputs_disabled_verified':True,'post_test_can_hello_confirmed':'outcome=CAN_HELLO_CONFIRMED' in ihu.split('> hello comms')[-1],'bench_bridge_restored':True},'limits':['Finite bench downlink check, not endurance or flight modulation qualification.','No UHF command sent from Yamcs; no flight TC route added.','Board/receiver firmware comes from the existing transceiver bring-up deployment, not a firmware update in main.','EPS battery reading remains near zero; no charger settings changed.'],'matches':matches,'raw_iq_host_path':'ngrabbs@192.168.1.251:/home/ngrabbs/work/ember-y24-bpsk/runs/ember-flight-20261017-03/raw-192k.cf32'}
(r/'result.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='matches'},indent=2))
