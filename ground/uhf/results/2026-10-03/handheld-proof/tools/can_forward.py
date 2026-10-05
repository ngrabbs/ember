#!/usr/bin/env python3
"""Optional bounded CAN-record -> binary TX adapter. No CAN replies/core edits."""
import argparse
from collections import OrderedDict
from datetime import datetime,timezone
import json,os,queue,subprocess,sys,threading,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'ember'))
from lte_receiver import validate
from radio_control import request as radio_request

class Admission:
    def __init__(self, pending):
        self.pending=pending;self.seen=OrderedDict();self.accepted=self.duplicates=self.dropped=self.rejected=0
    def admit(self, record):
        try:
            if record['outcome']!='VALIDATED_AND_RECORDED' or record['application_replies_enabled']:
                raise ValueError('Expected passive CAN record')
            raw=bytes.fromhex(record['hex']);decoded=validate(raw)
            if decoded['header']['source_boot_id']!=record['sender_boot']:raise ValueError('Producer mismatch')
        except (KeyError,ValueError):self.rejected+=1;return 'REJECTED'
        key=(decoded['header']['source_boot_id'],decoded['sequence'])
        if key in self.seen:self.duplicates+=1;return 'DUPLICATE'
        # Remember even queue-full observations; do not silently retry old telemetry.
        self.seen[key]=None
        if len(self.seen)>256:self.seen.popitem(last=False)
        try:self.pending.put_nowait((raw,record))
        except queue.Full:self.dropped+=1;return 'QUEUE_FULL'
        self.accepted+=1;return 'QUEUED'


def run(a):
    if not a.transmit:raise ValueError('Explicit --transmit required')
    a.output.mkdir(parents=True,exist_ok=False)
    pending=queue.Queue(maxsize=2);admission=Admission(pending);stop=threading.Event();lock=threading.Lock()
    deadline=time.monotonic()+a.seconds;submitted=failed=expired=service_admitted=0
    events=(a.output/'events.jsonl').open('w')
    def event(kind,**values):
        with lock:
            events.write(json.dumps(dict(event=kind,utc=datetime.now(timezone.utc).isoformat(),**values))+'\n')
            events.flush();os.fsync(events.fileno())
    def sender():
        nonlocal submitted,failed,expired,service_admitted
        next_start=0;index=0
        while not stop.is_set():
            try:raw,record=pending.get(timeout=.1)
            except queue.Empty:continue
            if stop.wait(max(0,next_start-time.monotonic())):expired+=1;break
            if time.monotonic()>=deadline:expired+=1;break
            index+=1;sequence=a.sequence+index-1
            packet=a.output/f'packet-{index:03}.bin';packet.write_bytes(raw)
            tx=a.output/f'tx-{index:03}.json';log=a.output/f'tx-{index:03}.log'
            if a.service_socket:
                decoded=validate(raw)
                request_id=f"can-{record['sender_boot']}-{decoded['sequence']}"
                event('SERVICE_SUBMIT',request_id=request_id,can_request=record['request'],hex=raw.hex())
                next_start=time.monotonic()+8
                try:
                    result=radio_request(a.service_socket,dict(command='enqueue',hex=raw.hex(),request_id=request_id))
                    tx.write_text(json.dumps(result,indent=2)+'\n');service_admitted+=1
                    event('SERVICE_ADMITTED',request_id=request_id,sequence=result['sequence'],meaning='queued; RF delivery unconfirmed')
                except Exception as exc:
                    failed+=1;event('SERVICE_SUBMISSION_ERROR',request_id=request_id,error=str(exc),meaning='inspect service status; no automatic retry')
                pending.task_done();continue
            event('TX_START',sequence=sequence,can_request=record['request'],hex=raw.hex())
            next_start=time.monotonic()+8
            with log.open('w') as out:
                child=subprocess.Popen([sys.executable,str(a.sender),'--packet',str(packet),'--output',str(tx),
                    '--sequence',str(sequence),'--frequency',str(a.frequency),'--gain',str(a.gain),'--transmit'],stdout=out,stderr=subprocess.STDOUT)
                try:code=child.wait(timeout=30)
                except subprocess.TimeoutExpired:
                    child.terminate()
                    try:child.wait(timeout=8)
                    except subprocess.TimeoutExpired:child.kill();child.wait()
                    code=-1
            if code==0:submitted+=1
            else:failed+=1
            event('TX_STOP',sequence=sequence,returncode=code,meaning='local TX completion; RF delivery unconfirmed')
            pending.task_done()
    worker=threading.Thread(target=sender);worker.start()
    print('CAN_RF_FORWARD_READY '+json.dumps(dict(input=str(a.records),queue_capacity=2,limit=a.limit,
        seconds=a.seconds,application_replies=False)),flush=True)
    try:
        with a.records.open() as incoming:
            # Ignore older records; this session admits only newly appended observations.
            incoming.seek(0,2);partial=''
            while time.monotonic()<deadline and admission.accepted<a.limit:
                chunk=incoming.read(4096)
                if not chunk:time.sleep(.05);continue
                partial+=chunk
                if len(partial)>16384:raise ValueError('CAN record exceeds bound')
                while '\n' in partial and admission.accepted<a.limit:
                    line,partial=partial.split('\n',1)
                    try:record=json.loads(line)
                    except ValueError:admission.rejected+=1;event('REJECTED_JSON');continue
                    outcome=admission.admit(record);event(outcome,can_request=record.get('request'))
            # Let already admitted work finish while still inside the finite session.
            while time.monotonic()<deadline and worker.is_alive() and pending.unfinished_tasks:
                time.sleep(.1)
    finally:
        stop.set();worker.join(timeout=40)
        result=dict(accepted=admission.accepted,duplicates=admission.duplicates,queue_full=admission.dropped,
            rejected=admission.rejected,local_tx_completed=submitted,local_tx_failed=failed,
            service_admitted=service_admitted,
            untransmitted=pending.qsize()+expired,worker_stopped=not worker.is_alive(),
            scope='CAN admission and local TX only; independent RF/Yamcs verification required')
        (a.output/'status.json').write_text(json.dumps(result,indent=2)+'\n');event('STOP',**result);events.close()
        print(json.dumps(result),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--records',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--sender',type=Path,default=Path(__file__).with_name('sdrb_tx.py'))
    p.add_argument('--seconds',type=int,default=60,choices=range(1,601));p.add_argument('--limit',type=int,default=3,choices=range(1,11))
    p.add_argument('--sequence',type=int,default=1000);p.add_argument('--frequency',type=float,default=434200000)
    p.add_argument('--service-socket',type=Path,help='Submit to a running persistent radio; it owns RF settings and outer sequence')
    p.add_argument('--gain',type=float,default=0);p.add_argument('--transmit',action='store_true');a=p.parse_args()
    if not 0<=a.gain<=70 or not 430e6<=a.frequency<=440e6:p.error('gain/frequency outside bench range')
    if not 0<=a.sequence<=2**32-a.limit:p.error('sequence out of range')
    run(a)
