#!/usr/bin/env python3
"""Finite host-triggered EPS telemetry cadence for the existing IHU CAN bench.

The IHU reads and encodes real EPS data; this host only sends console triggers.
No firmware, charger configuration, spacecraft scheduler or RF owner is changed.
"""
import argparse,hashlib,json,math,re,signal,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'ember'))

ERROR_COUNTERS=('unknown','tx_fail','tx_timeout','rx_bad','rx_overflow','fragments_bad','fragments_timeout','busy_drops')

def numeric_status(text):
    return {key:int(value) for key,value in re.findall(r' (\w+)=(\d+)\b',text)}


def check_status(text,baseline=None):
    if 'role=IHU_MCU fw=can-bench-v2' not in text or 'can_ready=1' not in text:raise RuntimeError('Expected IHU CAN bench not ready')
    status=numeric_status(text)
    if not status.get('boot') or status.get('pending')!=0 or 'eflg=00' not in text or status.get('tec')!=0 or status.get('rec')!=0:
        raise RuntimeError('IHU has a pending transaction or CAN fault')
    if baseline is not None:
        if status['boot']!=baseline['boot']:raise RuntimeError('IHU rebooted during cadence')
        for key in ERROR_COUNTERS:
            if status[key]!=baseline[key]:raise RuntimeError('IHU counter increased: '+key)
    return status


def run(a):
    from comms_uart import Console
    from codec import decode,DICTIONARY
    a.output.mkdir(parents=True,exist_ok=False)
    c=Console(a.port);records=[];error=None;initial=None;final=None
    try:
        initial=check_status(c.command('status',1))
        hello=c.command('hello',1);c.require_match(hello,'CAN_HELLO_CONFIRMED')
        start=time.monotonic()
        with (a.output/'packets.jsonl').open('w') as log:
            for i in range(a.count):
                deadline=start+i*a.interval
                time.sleep(max(0,deadline-time.monotonic()))
                reply=c.command('eps telemetry',1)
                c.require_match(reply,'WALTER_BENCH_RETURN')
                matches=re.findall(r'RESULT request=(\d+) outcome=WALTER_BENCH_RETURN peer=\d+ bytes=128 hex=([0-9a-f]+)',reply)
                if len(matches)!=1:raise RuntimeError('Missing single128-byte EPS return')
                request,hexdata=matches[0];raw=bytes.fromhex(hexdata);packet=decode(raw)
                if packet['name']!='POWER_STATUS' or packet['header']['source']!=DICTIONARY['endpoints']['ihu'] or packet['header']['source_boot_id']!=initial['boot']:
                    raise RuntimeError('Unexpected EPS producer or session')
                if records and packet['sequence']==records[-1]['inner_sequence']:raise RuntimeError('Repeated IHU telemetry identity')
                record=dict(request=int(request),hex=hexdata,sha256=hashlib.sha256(raw).hexdigest(),inner_sequence=packet['sequence'],
                    generated_unix=time.time(),cadence_elapsed_seconds=time.monotonic()-start)
                records.append(record);log.write(json.dumps(record)+'\n');log.flush()
                print('IHU_CADENCE_PACKET '+json.dumps(record),flush=True)
                final=check_status(c.command('status',.5),initial)
    except BaseException as exc:error=str(exc) or type(exc).__name__;raise
    finally:
        c.serial.close()
        (a.output/'ihu.txt').write_text(''.join(c.transcript))
        result=dict(count=len(records),requested=a.count,interval_seconds=a.interval,error=error,initial_status=initial,final_status=final,
            scope='Finite host console triggers; original IHU EPS/CAN packets, no flight autonomous scheduling or RF delivery claim')
        (a.output/'result.json').write_text(json.dumps(result,indent=2)+'\n')
        print('IHU_CADENCE_STOPPED '+json.dumps(result),flush=True)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--port',required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--interval',type=float,default=8);p.add_argument('--count',type=int,default=6)
    p.add_argument('--generate',action='store_true');a=p.parse_args()
    if not a.generate:p.error('Explicit --generate required')
    if not math.isfinite(a.interval) or not 5<=a.interval<=60 or not 1<=a.count<=10 or (a.count-1)*a.interval+3>600:
        p.error('Interval5..60s, count1..10, total<=600s required')
    signal.signal(signal.SIGTERM,lambda *_:(_ for _ in ()).throw(KeyboardInterrupt('Termination requested')))
    run(a)
if __name__=='__main__':main()
