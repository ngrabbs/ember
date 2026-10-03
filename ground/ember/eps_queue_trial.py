"""Opt-in hardware EPS FIFO trial; correlate UDP/Yamcs independently.

Requires queue-capable IHU and registration-admission-capable Walter images.
Does not synthesize telemetry, extend RF deadlines, or retry ambiguous sends.
"""
import argparse
import json
from pathlib import Path
import re
import time
from comms_uart import Console
from codec import decode


def queue_status(text):
    rows=re.findall(r'^LTE_QUEUE (.*)$', text, re.M)
    if not rows:raise ValueError('No queue status returned')
    return {k:int(v) for k,v in re.findall(r'(\w+)=(\d+)',rows[-1])}


def accepted_packets(transcript):
    return [dict(request=int(request),hex=data,decoded=decode(bytes.fromhex(data)))
            for request,data in re.findall(
                r'RESULT request=(\d+) outcome=MODEM_ACCEPTED peer=\d+ bytes=128 hex=([0-9a-f]{256})',
                transcript)]


def run(args):
    c=Console(args.port)
    result={'scope':'Volatile IHU bench FIFO, explicit RF window, modem acceptance only; verify ground and archive separately.',
            'queued':[], 'queue_status':[]}
    try:
        result['initial_status']=c.command('status')
        assert 'role=IHU_MCU' in result['initial_status']
        initial=queue_status(c.command('lte queue off',3))
        assert initial['count']==0 and initial['state']==0, 'Existing packets require inspection; trial will not discard them'
        Console.require_match(c.command('hello',2),'CAN_HELLO_CONFIRMED')
        off=c.command('lte status',2);Console.require_match(off,'LTE_STATUS')
        assert 'state=0 ' in off and 'window_ms=0 ' in off, 'Start with Walter OFF'
        adc=c.command('eps adc on',1);assert 'outcome=VERIFIED' in adc
        for _ in range(args.count):
            response=c.command('eps enqueue',1)
            match=re.search(r'EPS_QUEUED sequence=(\d+) count=\d+ bytes=128 hex=([0-9a-f]{256})',response)
            assert match,response
            packet=decode(bytes.fromhex(match[2]))
            assert packet['name']=='POWER_STATUS' and packet['payload']['provenance']==2
            result['queued'].append(dict(hex=match[2],decoded=packet))
        # Exercise retention with actual queue service active, but RF held OFF.
        c.command('lte queue on',8)
        retained=queue_status(c.command('lte queue off',3))
        assert retained['count']==args.count and retained['accepted']==initial['accepted'] and retained['hold']==0
        assert retained['attempts']==0
        result['retained_while_off']=retained
        enabled=c.command('lte '+str(args.seconds),2)
        Console.require_match(enabled,'RF_WINDOW_ACCEPTED')
        end=time.monotonic()+args.seconds
        c.command('lte queue on',.5)
        while time.monotonic()<end:
            response=c.command('lte queue status',2)
            snapshot=queue_status(response);result['queue_status'].append(snapshot)
            print('QUEUE '+json.dumps(snapshot),flush=True)
            if snapshot['hold'] or snapshot['count']==0:break
        result['modem_accepted']=accepted_packets(''.join(c.transcript))
        result['exact_fifo_acceptance']=([p['hex'] for p in result['queued']]==
                                        [p['hex'] for p in result['modem_accepted']])
        if result['exact_fifo_acceptance']:time.sleep(min(15,max(0,end-time.monotonic())))
    finally:
        try:
            c.command('lte queue off',.5)
            # Disabling never cancels an in-flight send; allow its bounded
            # outcome to finish before the explicit RF stop request.
            idle_end=time.monotonic()+25
            idle=False
            while time.monotonic()<idle_end:
                status=c.command('status',.5)
                if 'pending=0 ' in status:
                    idle=True;break
            result['idle_before_stop']=idle
            result['cleanup_hello']=c.command('hello',2)
            result['stop']=c.command('lte 0',2)
            result['final_modem_status']=c.command('lte status',2)
            result['off_confirmed']=bool(re.search(r'LTE_STATUS state=0 .*window_ms=0\b',result['final_modem_status']))
            result['final_queue']=queue_status(c.command('lte queue status',.5))
            result['final_status']=c.command('status',.5)
        finally:
            result['modem_accepted']=accepted_packets(''.join(c.transcript))
            c.serial.close();args.output.mkdir(parents=True,exist_ok=True)
            (args.output/'trial.log').write_text(''.join(c.transcript))
            (args.output/'trial.json').write_text(json.dumps(result,indent=2)+'\n')
            print('SUMMARY '+json.dumps({k:result.get(k) for k in ('exact_fifo_acceptance','off_confirmed','final_queue')}),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port',required=True)
    parser.add_argument('--seconds',type=int,default=120)
    parser.add_argument('--count',type=int,default=3)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    if not 30<=args.seconds<=120 or not 1<=args.count<=4:parser.error('seconds30..120, count1..4')
    run(args)
