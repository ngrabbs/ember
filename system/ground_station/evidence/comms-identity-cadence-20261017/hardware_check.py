import serial,time,pathlib,re,json
base=pathlib.Path('/home/ngrabbs/work/ember-identity-cadence-20261017/deployment')
ports={role:serial.Serial('/dev/serial/by-id/usb-Raspberry_Pi_Pico_'+identity+'-if00',115200,timeout=0,exclusive=True) for role,identity in [('IHU','DF641455DB822427'),('COMMS','E663682593639D39')]}
buffers={role:b'' for role in ports};events=[];checks=[]
def pump(seconds):
 end=time.monotonic()+seconds
 while time.monotonic()<end:
  for role,p in ports.items():
   buffers[role]+=p.read(p.in_waiting or 1)
   while b'\n' in buffers[role]:
    raw,buffers[role]=buffers[role].split(b'\n',1);line=raw.decode(errors='replace').strip()
    if line:events.append((role,line))
  time.sleep(.005)
def command(text,needle,timeout=8):
 start=len(events);ports['IHU'].write((text+'\n').encode());ports['IHU'].flush()
 events.append(('COMMAND',text));end=time.monotonic()+timeout
 while time.monotonic()<end:
  pump(.03)
  lines=[line for role,line in events[start:] if role=='IHU']
  if any(needle in line for line in lines):return '\n'.join(lines)
  if any(line.startswith(('REJECT ','ERROR ')) for line in lines):raise AssertionError((text,lines))
 raise AssertionError(('timeout',text,lines))
def message_ids(start):
 result=[]
 for role,line in events[start:]:
  if role!='COMMS':continue
  if line.startswith('[firmware_rf] packet_hex='):result.append(50)
  elif line.startswith('[uhf] packet request='):
   raw=bytes.fromhex(line.split('packet_hex=')[1]);result.append(int.from_bytes(raw[8:10],'big'))
 return result
def transmission(text,expected):
 start=len(events);result=command(text,'outcome=RF_TX_COMPLETE status=0');pump(.15)
 actual=message_ids(start);assert actual==expected,(text,actual,expected)
 checks.append({'command':text,'packet_ids':actual,'result':result})
 print('PASS',text,'packet_ids='+str(actual),flush=True)
okay=False
try:
 ports['COMMS'].write(b'v');ports['COMMS'].flush();pump(.3)
 version=command('version','FIRMWARE role=IHU_MCU');assert 'version=0.14.0' in version
 mode=command('mode','MODE ');assert 'configuration=GROUND_TEST mode=SAFE' in mode
 zero='OUTPUTS cli_debug=0 cli_telem=0 umb_debug=0 umb_telem=0 uhf_telem=0 lte_telem=0'
 assert zero in command('outputs','OUTPUTS ')
 assert any(role=='COMMS' and 'version=0.33.0' in line for role,line in events)
 assert not message_ids(0),'RF before an explicit request'
 command('output uhf_telem on','OUTPUTS ')
 command('hello comms','outcome=CAN_HELLO_CONFIRMED')
 transmission('uhf heartbeat',[50,5])
 transmission('uhf system',[1])
 transmission('uhf comms firmware',[50])
 transmission('uhf comms firmware',[50])
 start=len(events);command('output uhf_telem off','OUTPUTS ')
 result=command('uhf comms firmware','REJECT reason=OUTPUT_DISABLED');assert not message_ids(start)
 command('output uhf_telem on','OUTPUTS ')
 transmission('uhf heartbeat',[5])
 start=len(events);command('uhf run 60 10','UHF_RUN START');began=time.monotonic()
 for milestone in (20,40,61):
  while time.monotonic()-began<milestone:pump(.1)
  print('RUN elapsed='+str(milestone)+' packets='+str(len(message_ids(start))),flush=True)
 ids=message_ids(start);assert ids==[5,1,16,53]*6,ids
 status=command('status','STATUS role=IHU_MCU')
 assert 'cycles=6 submitted=24' in status and 'uhf_mode=2' in status,status
 checks.append({'command':'uhf run 60 10','packet_ids':ids,'status':status})
 command('faults','FAULTS total=');okay=True
 print('PASS full run: 24 IHU packets, zero repeated COMMS identity packets',flush=True)
finally:
 if not okay:
  try:ports['IHU'].write(b'uhf stop\noutput uhf_telem off\n');pump(.3)
  except Exception:pass
 for p in ports.values():p.close()
 for role in ['IHU','COMMS']:
  (base/('after-'+role.lower()+'.log')).write_text('\n'.join(line for kind,line in events if kind in [role,'COMMAND'])+'\n')
 (base/'hardware-check.json').write_text(json.dumps({'passed':okay,'checks':checks,'total_native_packet_ids':message_ids(0),'independent_ground_reception_checked':False},indent=2)+'\n')
