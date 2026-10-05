#!/usr/bin/env python3
"""Arm a finite native IHU telemetry observation; never send USB packet triggers."""
import argparse,hashlib,json,re,signal,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'ember'))
from ihu_cadence import check_status

def run(a):
    from comms_uart import Console
    from codec import decode,DICTIONARY
    a.output.mkdir(parents=True,exist_ok=False)
    c=Console(a.port);armed=False;error=None;records=[];initial=final=None;off=None
    passive='';started=None
    try:
        initial=check_status(c.command('status',.5))
        automatic=c.command('telem status',.3)
        if 'AUTOTELEM enabled=0' not in automatic:raise RuntimeError('Expected new timer disabled')
        hello=c.command('hello',1);c.require_match(hello,'CAN_HELLO_CONFIRMED')
        reply=c.command('telem on '+str(a.period),.3)
        if f'AUTOTELEM enabled=1 period_ms={a.period*1000}' not in reply:
            raise RuntimeError('Native timer did not arm')
        armed=True;started=time.monotonic();chunks=[]
        print('IHU_AUTOTELEM_ARMED '+json.dumps(dict(period_seconds=a.period,observe_seconds=a.seconds,
            host_telemetry_triggers=0,initial_boot=initial['boot'])),flush=True)
        # The host only reads USB during this interval. Scheduling and EPS reads
        # run in the IHU even when no USB reader is present.
        while time.monotonic()-started<a.seconds:
            chunks.append(c.serial.read(8192))
        passive=b''.join(chunks).decode('utf-8','replace')
        c.transcript.append('> PASSIVE_USB_OBSERVATION_NO_COMMANDS\n'+passive)
    except BaseException as exc:
        error=str(exc) or type(exc).__name__;raise
    finally:
        try:
            if armed:
                off=c.command('telem off',.5)
                if 'AUTOTELEM enabled=0' not in off:raise RuntimeError('Native timer did not stop')
                final=check_status(c.command('status',.5),initial)
                automatic={int(r):int(s) for r,s in re.findall(r'AUTOTELEM_SUBMITTED request=(\d+) sequence=(\d+)',passive)}
                for request,hexdata in re.findall(r'RESULT request=(\d+) outcome=WALTER_BENCH_RETURN peer=\d+ bytes=128 hex=([0-9a-f]+)',passive):
                    request=int(request);raw=bytes.fromhex(hexdata);packet=decode(raw)
                    if request not in automatic or packet['sequence']!=automatic[request]:
                        raise RuntimeError('Packet lacks native timer submission evidence')
                    if packet['name']!='POWER_STATUS' or packet['header']['source']!=DICTIONARY['endpoints']['ihu'] or packet['header']['source_boot_id']!=initial['boot']:
                        raise RuntimeError('Unexpected telemetry producer')
                    records.append(dict(request=request,hex=hexdata,sha256=hashlib.sha256(raw).hexdigest(),
                        inner_sequence=packet['sequence'],ihu_uptime_ms=packet['header']['uptime_ms']))
                if len(records)!=a.seconds//a.period:raise RuntimeError('Unexpected automatic packet count')
        except BaseException as exc:
            error=str(exc) or type(exc).__name__;raise
        finally:
            c.serial.close()
            (a.output/'ihu.txt').write_text(''.join(c.transcript))
            (a.output/'packets.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in records))
            result=dict(count=len(records),period_seconds=a.period,observe_seconds=a.seconds,error=error,
                initial_status=initial,final_status=final,timer_off_reply=off,host_telemetry_triggers=0,
                scope='One USB enable/disable; native IHU timer generated fresh EPS/CAN packets during passive observation. RF delivery is separate.')
            (a.output/'result.json').write_text(json.dumps(result,indent=2)+'\n')
            print('IHU_AUTOTELEM_STOPPED '+json.dumps(result),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--port',required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--period',type=int,default=20,choices=range(5,3601))
    p.add_argument('--seconds',type=int,default=65,choices=range(1,601))
    p.add_argument('--arm',action='store_true');a=p.parse_args()
    if not a.arm or a.seconds<a.period or a.seconds%a.period<2:
        p.error('Explicit --arm and at least2s after a full period required')
    signal.signal(signal.SIGTERM,lambda *_:(_ for _ in ()).throw(KeyboardInterrupt('Termination requested')))
    run(a)
