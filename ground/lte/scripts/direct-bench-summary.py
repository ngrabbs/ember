#!/usr/bin/env python3
"""Compare USB admission outcomes with receiver records; no one-way latency claim."""
import argparse,json
from pathlib import Path

def summarize(sender,receiver,run):
 tx=[x for x in sender if x.get('run')==run];starts=[x for x in tx if x.get('event')=='run_start'];ends=[x for x in tx if x.get('event')=='run_done']
 if len(starts)!=1 or len(ends)!=1:raise ValueError('Need exactly one run_start/run_done')
 start,end=starts[0],ends[0];boot=start['boot'];size=start['bytes'];duration=start['seconds']
 ids=lambda kind:{x['seq']for x in tx if x.get('event')==kind}
 attempted,accepted,rejected,unknown=(ids(k)for k in ['attempt','accepted','rejected','unknown'])
 if accepted&rejected or accepted&unknown or rejected&unknown:raise ValueError('Conflicting terminal outcomes')
 if attempted!=accepted|rejected|unknown:raise ValueError('Incomplete attempt outcomes')
 for field,values in [('offered',attempted),('accepted',accepted),('rejected',rejected),('unknown',unknown)]:
  if end[field]!=len(values):raise ValueError('USB log counters mismatch')
 if end['slots']!=end['offered']+end['skipped']+end['unreached']:raise ValueError('Slot accounting mismatch')
 if any(x.get('log_drops',0)>0 for x in sender):raise ValueError('USB log overflow')
 rx=[x for x in receiver if x.get('event')=='received'and x.get('run')==run and x.get('boot')==boot and x.get('bytes')==size]
 seen={};duplicates=0
 for x in rx:
  if x['seq']in seen:duplicates+=1
  else:seen[x['seq']]=x['monotonic_ns']
 if set(seen)-attempted:raise ValueError('Unexpected receiver sequences')
 first=min(seen.values())if seen else None
 in_window={seq for seq,t in seen.items()if t<first+duration*10**9}if first is not None else set()
 tails=[x for x in receiver if x.get('event')=='receiver_done'and x.get('run')==run]
 if len(tails)!=1:raise ValueError('Receiver capture incomplete')
 covered=first is not None and tails[0]['ended_monotonic_ns']>=first+duration*10**9
 complete=end['reason']=='duration'and end['unreached']==0 and not unknown and covered
 return dict(run=run,packet_bytes=size,measurement_seconds=duration,planned_slots=end['slots'],attempted=len(attempted),skipped=end['skipped'],unreached=end['unreached'],modem_accepted=len(accepted),modem_rejected=len(rejected),unknown=len(unknown),unique_received=len(seen),duplicates=duplicates,accepted_missing=sorted(accepted-set(seen)),unknown_received=sorted(unknown&set(seen)),received_in_window=len(in_window),late_received=len(seen)-len(in_window),measurement_complete=complete,received_kbps=len(in_window)*size*8/duration/1000 if complete else None,window='Fixed sender-requested duration beginning at first valid receiver arrival',limits='Direct ESP32/modem UART/AT goodput, not maximum LTE-M PHY rate. UART115200 8N1, one transaction in flight. Skipped slots were not attempted. Arrival clocks do not establish one-way latency.')

def main():
 p=argparse.ArgumentParser();p.add_argument('sender',type=Path);p.add_argument('receiver',type=Path);p.add_argument('--run',type=int,required=True);a=p.parse_args()
 read=lambda path:[json.loads(x)for x in path.read_text().splitlines()if x.strip()]
 print(json.dumps(summarize(read(a.sender),read(a.receiver),a.run),indent=2))
if __name__=='__main__':main()
