import sys,json,time,re
from pathlib import Path
sys.path.insert(0,'/home/ngrabbs/work/ember-sdrb-adapter-20261003/ground/ember')
from comms_uart import Console
p=Path('/home/ngrabbs/work/ember-sdrb-adapter-20261003/system/sdrb/evidence/native-autotelem-closed-usb-01');p.mkdir(exist_ok=False)
port='/dev/serial/by-id/usb-Raspberry_Pi_Pico_DF641455DB822427-if00'
c=Console(port);transcript=[];armed=False;result={}
def numbers(s):return {k:int(v) for k,v in re.findall(r' (\w+)=(\d+)',s)}
try:
 before=c.command('telem status',.3);assert 'AUTOTELEM enabled=0' in before
 before=numbers(before);status=c.command('status',.3);boot=numbers(status)['boot']
 reply=c.command('telem on 20',.3);assert 'AUTOTELEM enabled=1 period_ms=20000' in reply
 armed=True;transcript.extend(c.transcript);c.serial.close();c=None
 start=time.monotonic();print('IHU_USB_CONSOLE_CLOSED_NO_COMMANDS',flush=True)
 time.sleep(25);elapsed=time.monotonic()-start
 c=Console(port);off=c.command('telem off',.3);assert 'AUTOTELEM enabled=0' in off
 armed=False;after=numbers(off);status=c.command('status',.3)
 assert numbers(status)['boot']==boot and numbers(status)['pending']==0
 assert after['submitted']-before['submitted']==1 and after['failed']==before['failed'] and after['skipped']==before['skipped']
 result=dict(passed=True,boot=boot,usb_console_closed_seconds=elapsed,before=before,after=after,host_telemetry_triggers=0,
  scope='USB serial endpoint closed/DTR released for25s after one enable command; native submitted counter advanced once. CAN/RF/archive packet verification is separate. Cable stayed attached.')
finally:
 if c is None:c=Console(port)
 if armed:c.command('telem off',.5)
 transcript.extend(c.transcript);c.serial.close();(p/'ihu.txt').write_text(''.join(transcript));(p/'result.json').write_text(json.dumps(result,indent=2)+'\n')
print('IHU_CLOSED_USB_RESULT '+json.dumps(result),flush=True)
