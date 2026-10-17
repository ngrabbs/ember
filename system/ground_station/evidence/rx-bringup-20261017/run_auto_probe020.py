import subprocess,sys,time,select,shlex,pathlib,threading,queue
name=sys.argv[1];seq=int(sys.argv[2]);transaction=int(sys.argv[3]);gain=float(sys.argv[4])
root=pathlib.Path(__file__).parent
cmd=f'python3 -u ~/work/ember-rx-uplink-20261017/ground/bpsk/roundtrip_power020.py --sequence {seq} --transaction {transaction} --gain {gain} --ihu-boot 2786831095 --output ~/work/ember-rx-uplink-20261017/runs/{shlex.quote(name)}'
ground=subprocess.Popen(['ssh','ngrabbs@192.168.1.251',cmd],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1)
lines=[]
try:
 ready_lines=queue.Queue()
 def read_ready():
  while True:
   line=ground.stdout.readline()
   ready_lines.put(line)
   if not line or line.startswith('ROUNDTRIP_READY '):return
 reader=threading.Thread(target=read_ready,daemon=True);reader.start()
 end=time.monotonic()+40
 while time.monotonic()<end:
  line=ready_lines.get(timeout=max(.01,end-time.monotonic()));lines.append(line)
  if not line:raise RuntimeError('Ground ended before READY')
  if line.startswith('ROUNDTRIP_READY '):break
 else:raise RuntimeError('Ground readiness timeout')
 reader.join()
 code='''import serial,time,pathlib
with serial.Serial('/dev/serial/by-id/usb-Raspberry_Pi_Pico_E663682593639D39-if00',115200,timeout=.1,exclusive=True) as s:
 s.reset_input_buffer();s.write(b'A');end=time.monotonic()+4;data=b''
 while time.monotonic()<end and b'[rx_test] prepare lo=1' not in data:data+=s.read(4096)
 assert b'[rx_test] prepare lo=1' in data,data
 print('RX_PREPARING',flush=True);end=time.monotonic()+23
 while time.monotonic()<end:data+=s.read(131072)
 s.write(b'v');end=time.monotonic()+1
 while time.monotonic()<end:data+=s.read(16384)
 pathlib.Path.home().joinpath('work/MSU_Cubesat/rx-onboard-20261017/NAME-console.txt').write_bytes(data)
 for line in data.decode().splitlines():
  if line.startswith(('[auto_reply]','[rx_','[uplink]','[tx_tone]','[clock_status]','[firmware]','[can]')):print(line.split(' hex=')[0])
'''.replace('NAME',name)
 board=subprocess.Popen(['ssh','ngrabbs@192.168.1.252','~/tools/ember-lte-version-build/bin/python -u -c '+shlex.quote(code)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
 if not select.select([board.stdout],[],[],5)[0] or board.stdout.readline().strip()!='RX_PREPARING':raise RuntimeError('COMMS not ready')
 time.sleep(1.8);ground.stdin.write('GO\n');ground.stdin.flush()
 rest,_=ground.communicate(timeout=45);lines.append(rest)
 output,_=board.communicate(timeout=20);(root/(name+'-summary.txt')).write_text(output)
 print(output);print(''.join(lines))
 if board.returncode or ground.returncode:raise RuntimeError('probe process failed')
finally:
 (root/(name+'-ground.txt')).write_text(''.join(lines))
 if ground.poll() is None:ground.stdin.close();ground.wait(timeout=45)
