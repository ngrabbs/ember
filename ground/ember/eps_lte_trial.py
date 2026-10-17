"""Bounded hardware IHU telemetry -> CAN/COMMS/Walter LTE trial; no direct AT access."""
import argparse
import json
from pathlib import Path
import re
import time
from comms_uart import Console
from codec import decode
from lte_diagnostics import decode_diagnostics

def run(args):
    c=Console(args.port);result={'modem_accepted':[],'status':[],'status_timing':[],'scope':'Modem acceptance only; correlate ground receiver and Yamcs separately.'}
    def command(text,timeout=5):
        c.serial.write(text.encode()+b'\n');c.serial.flush();output='';end=time.monotonic()+timeout
        while time.monotonic()<end:
            output+=c.serial.read(8192).decode(errors='replace')
            lines=output.splitlines()
            if any(line.startswith('RESULT ') or line.startswith('REJECT ') for line in lines) and output.endswith('\n'):break
        c.transcript.append('> '+text+'\n'+output)
        return output
    def diagnostics(stage):
        if not args.diagnostics:return
        response=command('lte diagnostics')
        Console.require_match(response,'LTE_DIAG')
        match=re.search(r'bytes=96 hex=([0-9a-f]+)',response)
        parsed=decode_diagnostics(bytes.fromhex(match[1]))
        result.setdefault('diagnostics',[]).append({'stage':stage,'decoded':parsed})
        print('DIAGNOSTICS '+json.dumps(parsed),flush=True)
    try:
        c.command('')  # Finish a partial line left by an earlier console session.
        first=c.command('status');result['initial_status']=first.strip()
        Console.require_match(command('hello'),'CAN_HELLO_CONFIRMED')
        enabled=command('lte '+str(args.seconds));Console.require_match(enabled,'RF_WINDOW_ACCEPTED')
        admitted=time.monotonic()
        end=admitted+args.seconds-18
        ready=False
        while time.monotonic()<end:
            response=command('lte status')
            Console.require_match(response,'LTE_STATUS')
            result['status'].append(response.strip())
            result['status_timing'].append({'elapsed_s':round(time.monotonic()-admitted,3),'response':response.strip()})
            print(response.split('RESULT ')[0].strip(),flush=True)
            match=re.search(r'LTE_STATUS state=(\d+).*registered=(\d+)',response)
            if not match:break
            state=int(match[1])
            if state==6 and int(match[2])==1:
                ready=True;result['ready_elapsed_s']=round(time.monotonic()-admitted,3);break
            if state==0:break
            time.sleep(2)
        result['ready']=ready
        if ready:
            for kind in args.telemetry*args.count:
                if time.monotonic()>=end:break
                diagnostics('before_send')
                response=command({'eps':'eps lte','heartbeat':'heartbeat lte','system':'system lte'}[kind],22)
                if 'outcome=MODEM_ACCEPTED' not in response:
                    result['send_failure']=response.strip();print(response.strip(),flush=True);break
                Console.require_match(response,'MODEM_ACCEPTED')
                match=re.search(r'bytes=(\d+) hex=([0-9a-f]+)',response)
                packet=decode(bytes.fromhex(match[2]));assert packet['name']=={'eps':'POWER_STATUS','heartbeat':'HEARTBEAT','system':'SYSTEM_STATUS'}[kind]
                result['modem_accepted'].append(dict(hex=match[2],decoded=packet,elapsed_s=round(time.monotonic()-admitted,3)))
                print('MODEM_ACCEPTED '+packet['name']+' sequence='+str(packet['sequence']),flush=True)
                diagnostics('after_send')
                time.sleep(1)
            if result['modem_accepted'] and 'send_failure' not in result:
                time.sleep(min(args.settle,max(0,end-time.monotonic())))
    finally:
        try:
            command('hello')
            try:
                diagnostics('before_stop')
            except Exception as exc:
                result['before_stop_diagnostic_error']=str(exc)
            finally:
                result['stop']=command('lte 0').strip()
            result['final_modem_status']=command('lte status').strip()
            diagnostics('after_stop')
            result['final_status']=c.command('status').strip()
        finally:
            c.serial.close();args.output.mkdir(parents=True,exist_ok=True)
            (args.output/'trial.log').write_text(''.join(c.transcript))
            (args.output/'trial.json').write_text(json.dumps(result,indent=2)+'\n')
            print('SUMMARY '+json.dumps({'ready':result.get('ready',False),'modem_accepted':len(result['modem_accepted']),'final_modem_status':result.get('final_modem_status'),'evidence':str(args.output)}),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port',required=True)
    parser.add_argument('--seconds',type=int,default=90)
    parser.add_argument('--count',type=int,default=10)
    parser.add_argument('--telemetry',nargs='+',choices=('eps','heartbeat','system'),default=['eps'],help='Packet types per round; default preserves the EPS trial.')
    parser.add_argument('--diagnostics',action='store_true',help='Requires diagnostic-capable firmware on all three boards.')
    parser.add_argument('--settle',type=int,default=10,help='Wait after final modem acceptance before stopping RF (seconds).')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if not 30<=args.seconds<=120 or not 1<=args.count<=10 or not 0<=args.settle<=15:parser.error('seconds30..120, count1..10')
    run(args)
