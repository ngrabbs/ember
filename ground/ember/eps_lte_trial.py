"""Bounded hardware IHU EPS -> CAN/COMMS/Walter LTE trial; no direct AT access."""
import argparse
import json
from pathlib import Path
import re
import time
from comms_uart import Console
from codec import decode

def run(args):
    c=Console(args.port);result={'modem_accepted':[],'status':[],'scope':'Modem acceptance only; correlate ground receiver and Yamcs separately.'}
    def command(text,timeout=5):
        c.serial.write(text.encode()+b'\n');c.serial.flush();output='';end=time.monotonic()+timeout
        while time.monotonic()<end:
            output+=c.serial.read(8192).decode(errors='replace')
            lines=output.splitlines()
            if any(line.startswith('RESULT ') or line.startswith('REJECT ') for line in lines) and output.endswith('\n'):break
        c.transcript.append('> '+text+'\n'+output)
        return output
    try:
        first=c.command('status');result['initial_status']=first.strip()
        Console.require_match(command('hello'),'CAN_HELLO_CONFIRMED')
        enabled=command('lte '+str(args.seconds));Console.require_match(enabled,'RF_WINDOW_ACCEPTED')
        end=time.monotonic()+args.seconds-18
        ready=False
        while time.monotonic()<end:
            response=command('lte status')
            Console.require_match(response,'LTE_STATUS')
            result['status'].append(response.strip())
            print(response.split('RESULT ')[0].strip(),flush=True)
            match=re.search(r'LTE_STATUS state=(\d+)',response)
            if not match:break
            state=int(match[1])
            if state==6:ready=True;break
            if state==0:break
            time.sleep(2)
        result['ready']=ready
        if ready:
            for _ in range(args.count):
                if time.monotonic()>=end:break
                response=command('eps lte',22)
                if 'outcome=MODEM_ACCEPTED' not in response:
                    result['send_failure']=response.strip();print(response.strip(),flush=True);break
                Console.require_match(response,'MODEM_ACCEPTED')
                match=re.search(r'bytes=(\d+) hex=([0-9a-f]+)',response)
                packet=decode(bytes.fromhex(match[2]));assert packet['name']=='POWER_STATUS'
                result['modem_accepted'].append(dict(hex=match[2],decoded=packet))
                print('MODEM_ACCEPTED EPS sequence='+str(packet['sequence']),flush=True)
                time.sleep(1)
    finally:
        try:
            command('hello');result['stop']=command('lte 0').strip()
            result['final_modem_status']=command('lte status').strip()
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
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if not 30<=args.seconds<=120 or not 1<=args.count<=10:parser.error('seconds30..120, count1..10')
    run(args)
