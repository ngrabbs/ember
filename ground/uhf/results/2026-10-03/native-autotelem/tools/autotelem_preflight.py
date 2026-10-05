import sys,re,json
from pathlib import Path
sys.path.insert(0,'/home/ngrabbs/work/ember-sdrb-adapter-20261003/ground/ember')
from comms_uart import Console
from codec import decode
p=Path('/home/ngrabbs/work/MSU_Cubesat/ember-autotelem-20261003')
c=Console('/dev/serial/by-id/usb-Raspberry_Pi_Pico_DF641455DB822427-if00')
result={}
try:
 s=c.command('status',.5);assert 'id=DF641455DB822427' in s and 'pending=0' in s
 result['boot']=int(re.search(r' boot=(\d+)',s)[1]);result['initial_status']=s
 a=c.command('telem status',.3);assert 'AUTOTELEM enabled=0' in a and 'submitted=0' in a
 result['boot_disabled']=True
 rejected=[]
 for command in ('telem on 4','telem on 3601','telem on -1','telem on 20x','telem on '):
  text=c.command(command,.2);assert 'TELEM_PERIOD_RANGE' in text,rejected
  rejected.append(command)
 result['rejected_period_commands']=rejected
 text=c.command('telem on',.2);assert 'NORMAL_CAN_HELLO_AND_LTE_QUEUE_OFF_REQUIRED' in text
 result['pre_handshake_enable_rejected']=True
 text=c.command('normal',.3);assert 'CAN_NORMAL ready=1' in text
 text=c.command('hello',1);c.require_match(text,'CAN_HELLO_CONFIRMED')
 text=c.command('eps telemetry',1);c.require_match(text,'WALTER_BENCH_RETURN')
 h=re.search(r'bytes=128 hex=([0-9a-f]+)',text)[1];packet=decode(bytes.fromhex(h))
 assert packet['name']=='POWER_STATUS' and packet['header']['source_boot_id']==result['boot']
 result['manual_packet_hex']=h;result['manual_packet_sequence']=packet['sequence']
 a=c.command('telem status',.2);assert 'AUTOTELEM enabled=0' in a and 'due=0' in a
 result['manual_still_works_with_timer_disabled']=True
 result['passed']=True
finally:
 c.serial.close();(p/'postflash-preflight.txt').write_text(''.join(c.transcript));(p/'postflash-preflight.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
