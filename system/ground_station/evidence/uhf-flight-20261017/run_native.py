import serial,time,select,subprocess,json,re
from pathlib import Path
out=Path('/home/ngrabbs/work/uhf-flight-validation-20261017');out.mkdir(exist_ok=True)
logs={'ihu':[],'comms':[]};ports={}
def collect(seconds):
 end=time.monotonic()+seconds
 while time.monotonic()<end:
  for name,p in ports.items():
   line=p.readline().decode(errors='replace').strip()
   if line:
    logs[name].append(line);print(name.upper()+' '+line,flush=True)
def ihu(text,needle,seconds=3):
 logs['ihu'].append('> '+text);ports['ihu'].write((text+'\n').encode());ports['ihu'].flush()
 start=len(logs['ihu']);end=time.monotonic()+seconds
 while time.monotonic()<end:
  collect(.1)
  if any(needle in x for x in logs['ihu'][start:]):return
 raise RuntimeError('Missing '+needle+' for '+text)
subprocess.run(['sudo','systemctl','stop','ember-bench-bridge'],check=True)
error=None
try:
 for name,uid in [('ihu','DF641455DB822427'),('comms','E663682593639D39')]:
  ports[name]=serial.Serial('/dev/serial/by-id/usb-Raspberry_Pi_Pico_'+uid+'-if00',115200,timeout=.01,write_timeout=.5,exclusive=True);ports[name].dtr=True
 collect(.5)
 ihu('status','STATUS role=IHU_MCU')
 ihu('telem status','AUTOTELEM enabled=0')
 ihu('lte queue status','LTE_QUEUE enabled=0')
 ihu('hello comms','outcome=CAN_HELLO_CONFIRMED')
 ports['comms'].write(b'a');ports['comms'].flush();collect(.8)
 if not any('[uhf] LISTEN' in x for x in logs['comms']):raise RuntimeError('COMMS UHF service did not enter LISTEN')
 ihu('uhf run 30 10','UHF_RUN START')
 collect(33)
 if not any('UHF_RUN EXPIRED' in x for x in logs['ihu']):raise RuntimeError('IHU run did not expire cleanly')
finally:
 try:
  if 'ihu' in ports:ihu('uhf stop','UHF_RUN STOPPED')
  if 'comms' in ports:
   ports['comms'].write(b'x');ports['comms'].flush();collect(2)
   ports['comms'].write(b'v');ports['comms'].flush();collect(1)
  if 'ihu' in ports:ihu('hello comms','outcome=CAN_HELLO_CONFIRMED')
 finally:
  for p in ports.values():p.close()
  for name,lines in logs.items():(out/(name+'.txt')).write_text('\n'.join(lines)+'\n')
  subprocess.run(['sudo','systemctl','start','ember-bench-bridge'],check=True)
