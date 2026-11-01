"""Read-only comparison of two Yamcs UHF record-set reports and archived bytes."""
import argparse,base64,hashlib,json,urllib.parse,urllib.request
from codec import decode

def compare_records(first,last,first_command,last_command):
 a=decode(first);b=decode(last)
 assert a['name']==b['name']=='STATUS_RECORDS','Wrong telemetry type'
 assert a['header']['source_boot_id']==b['header']['source_boot_id'],'IHU reset during retention'
 assert a['payload']['capture_id']==b['payload']['capture_id'],'Different capture sets'
 assert first[38:118]==last[38:118],'Stored record bytes changed'
 assert len(first)==len(last)==120 and a['payload']['count']==b['payload']['count']==5,'Wrong count/packet size'
 assert a['payload']['record_size']==b['payload']['record_size']==16,'Wrong record size'
 intervals=[]
 for i in range(1,6):
  assert a['payload'][f'record{i}_sequence']==i,'Missing or duplicate sequence'
  if i>1:
   dt=(a['payload'][f'record{i}_uptime_ms']-a['payload'][f'record{i-1}_uptime_ms'])%2**32
   assert 900<=dt<=1100,'Sampling interval outside one-second scheduling tolerance'
   intervals.append(dt)
 # Require a real >=60s interval BETWEEN independent ground transactions too.
 first_attrs={v['name']:v['value'] for v in first_command['attr']}
 last_attrs={v['name']:v['value'] for v in last_command['attr']}
 for attrs in (first_attrs,last_attrs):
  assert attrs['ember-outcome']['stringValue']=='COMPLETED','Command did not complete'
  assert int(attrs['ember-elapsed-ms']['stringValue'])<=35000,'Command exceeded requirement'
 age=(b['header']['uptime_ms']-a['payload']['record5_uptime_ms'])%2**32
 assert age>=60000,'Retention age below60s'
 # IHU timestamps also prove >=60s between the initial delivery and later fetch.
 delivered_gap=(b['header']['uptime_ms']-a['header']['uptime_ms'])%2**32
 assert delivered_gap>=60000,'Fetch occurred less than60s after original response'
 return dict(status='PASS',boot=a['header']['source_boot_id'],capture_id=a['payload']['capture_id'],records=5,
  exact_equal_bytes=80,sha256=hashlib.sha256(first[38:118]).hexdigest(),sample_intervals_ms=intervals,
  retained_age_ms=age,response_gap_ms=delivered_gap)

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--capture-command',required=True);p.add_argument('--fetch-command',required=True)
 p.add_argument('--base',default='http://127.0.0.1:8090');p.add_argument('--output');args=p.parse_args()
 def api(path):
  with urllib.request.urlopen(args.base+path,timeout=10) as f:return json.load(f)
 packets=api('/api/archive/ember/packets?limit=500')['packets'];entries=[];raw=[]
 for command_id in (args.capture_command,args.fetch_command):
  entry=api('/api/archive/ember/commands/'+urllib.parse.quote(command_id,safe=''))
  attrs={v['name']:v['value'] for v in entry['attr']};request=decode(base64.b64decode(attrs['binary']['binaryValue']))
  candidates=[]
  for packet in packets:
   if packet.get('link')!='uhf-tm-in':continue
   wire=base64.b64decode(packet['packet']);tm=decode(wire)
   if tm['name']=='STATUS_RECORDS' and all(tm['header'][k]==request['header'][k] for k in ('transaction_epoch','transaction_id')):candidates.append(wire)
  assert len(candidates)==1,'Expected one unique matching UHF packet'
  entries.append(entry);raw.append(candidates[0])
 assert decode(base64.b64decode(next(v['value']['binaryValue'] for v in entries[0]['attr'] if v['name']=='binary')))['name']=='STATUS_CAPTURE'
 assert decode(base64.b64decode(next(v['value']['binaryValue'] for v in entries[1]['attr'] if v['name']=='binary')))['name']=='STATUS_FETCH'
 result=compare_records(*raw,*entries)
 result.update(capture_command=args.capture_command,fetch_command=args.fetch_command)
 if args.output:
  with open(args.output,'w') as f:json.dump(dict(result=result,history=entries,packet_hex=[v.hex() for v in raw]),f,indent=2)
 print(json.dumps(result,indent=2))
if __name__=='__main__':main()
