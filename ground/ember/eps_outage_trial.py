"""Hardware EPS retention during a coordinated ground-cell outage.

Ground coordinator confirms baseline UDP/archive, removes its own bounded cell,
and creates 'outage'/'restored' files in --output. RF windows remain explicit.
"""
import argparse
import json
from pathlib import Path
import re
import time
from comms_uart import Console
from codec import decode
from lte_diagnostics import decode_diagnostics
from eps_queue_trial import queue_status,accepted_packets


def run(args):
    args.output.mkdir(parents=True,exist_ok=True)
    # A stale coordinator flag must never shortcut the next physical outage.
    if any((args.output/name).exists() for name in ('outage','restored','trial.json')):
        raise ValueError('Use a fresh output directory for each outage trial')
    c=Console(args.port);r={'scope':'Deliberate cell outage, hardware EPS FIFO retention, explicit new RF window recovery; ground comparison separate.', 'queued':[], 'events':[]}
    def command(text,wait=2):return c.command(text,wait)
    def event(name,**values):
        row=dict(event=name,elapsed_s=round(time.monotonic()-started,3),**values)
        r['events'].append(row);print('EVENT '+json.dumps(row),flush=True)
    def status():
        reply=command('lte status');Console.require_match(reply,'LTE_STATUS')
        m=re.search(r'bytes=16 hex=([0-9a-f]{32})',reply);assert m,reply
        return bytes.fromhex(m[1])
    def diagnostic(stage):
        reply=command('lte diagnostics');Console.require_match(reply,'LTE_DIAG')
        m=re.search(r'bytes=96 hex=([0-9a-f]{192})',reply);assert m,reply
        value=decode_diagnostics(bytes.fromhex(m[1]));r.setdefault('diagnostics',[]).append(dict(stage=stage,decoded=value));return value
    def wait_flag(name,seconds):
        end=time.monotonic()+seconds
        while time.monotonic()<end:
            if (args.output/name).exists():return
            time.sleep(.25)
        raise TimeoutError('Coordinator did not confirm '+name)
    def enable():
        Console.require_match(command('lte 120'),'RF_WINDOW_ACCEPTED')
    def wait_ready():
        end=time.monotonic()+95
        while time.monotonic()<end:
            s=status()
            if s[0]==6 and s[3]==1:return
            if s[0]==0:break
        raise RuntimeError('Modem did not become registered/READY within bounded window')
    started=time.monotonic()
    try:
        r['initial_status']=command('status',.5)
        initial=queue_status(command('lte queue off',3));assert initial['count']==0 and initial['state']==0
        Console.require_match(command('hello'),'CAN_HELLO_CONFIRMED')
        assert status()[0]==0,'Walter must start OFF'
        assert 'outcome=VERIFIED' in command('eps adc on',1)
        enable();wait_ready()
        baseline=command('eps lte',22);Console.require_match(baseline,'MODEM_ACCEPTED')
        data=re.search(r'bytes=128 hex=([0-9a-f]{256})',baseline)[1]
        r['baseline']=dict(hex=data,decoded=decode(bytes.fromhex(data)))
        r['before_outage']=diagnostic('before_outage')
        event('baseline_accepted',hex=data)
        wait_flag('outage',60)
        event('cell_removed')
        end=time.monotonic()+45;observations=[]
        while time.monotonic()<end:
            s=status();observations.append(dict(state=s[0],registered=s[3],window_ms=int.from_bytes(s[4:8],'big')))
            if not s[3]:break
        r['outage_status']=observations;r['during_outage']=diagnostic('during_outage')
        r['registration_loss_observed']=r['during_outage']['registration_losses']>r['before_outage']['registration_losses']
        # If no loss is reported, do not send against a potentially stale cache.
        if observations[-1]['registered']:
            Console.require_match(command('lte 0'),'RF_WINDOW_ACCEPTED')
            assert status()[0]==0
            r['forced_off_for_stale_registration']=True
        for _ in range(3):
            reply=command('eps enqueue',1);m=re.search(r'EPS_QUEUED sequence=\d+ count=\d+ bytes=128 hex=([0-9a-f]{256})',reply);assert m,reply
            r['queued'].append(dict(hex=m[1],decoded=decode(bytes.fromhex(m[1]))))
        command('lte queue on',8)
        r['retained_during_outage']=queue_status(command('lte queue off',3))
        q=r['retained_during_outage'];assert q['count']==3 and q['attempts']==0 and q['hold']==0 and q['accepted']==initial['accepted']
        r['before_recovery']=diagnostic('before_recovery')
        Console.require_match(command('lte 0'),'RF_WINDOW_ACCEPTED');assert status()[0]==0
        event('retained',queue=q,registration_loss_observed=r['registration_loss_observed'])
        wait_flag('restored',45)
        event('cell_restored');enable();command('lte queue on',.5)
        end=time.monotonic()+120;r['recovery_queue_status']=[]
        while time.monotonic()<end:
            q=queue_status(command('lte queue status'));r['recovery_queue_status'].append(q)
            if q['hold'] or q['count']==0:break
        command('lte queue off',3)
        all_accepted=accepted_packets(''.join(c.transcript))
        r['recovered']=[p for p in all_accepted if p['hex']!=data]
        r['exact_fifo_recovery']=[p['hex'] for p in r['queued']]==[p['hex'] for p in r['recovered']]
        r['recovery_diagnostic']=diagnostic('after_recovery')
        event('recovered',exact_fifo_recovery=r['exact_fifo_recovery'],queue=q)
        if r['exact_fifo_recovery']:time.sleep(10)
    finally:
        try:
            command('lte queue off',.5)
            idle_end=time.monotonic()+25
            while time.monotonic()<idle_end:
                if 'pending=0 ' in command('status',.5):break
            command('hello')
            r['stop']=command('lte 0');r['final_modem_status']=command('lte status')
            r['off_confirmed']=bool(re.search(r'LTE_STATUS state=0 .*window_ms=0\b',r['final_modem_status']))
            r['final_queue']=queue_status(command('lte queue status',.5));r['final_status']=command('status',.5)
        finally:
            c.serial.close();(args.output/'trial.log').write_text(''.join(c.transcript))
            (args.output/'trial.json').write_text(json.dumps(r,indent=2)+'\n')
            print('SUMMARY '+json.dumps({k:r.get(k) for k in ('exact_fifo_recovery','registration_loss_observed','off_confirmed','final_queue')}),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--port',required=True);p.add_argument('--output',required=True,type=Path)
    run(p.parse_args())
