import subprocess,shlex,time,pathlib
root=pathlib.Path(__file__).parent
cmd='python3 -u ~/work/ember-rx-uplink-20261017/ground/bpsk/uplink_probe.py --kind tone --frequency 434994550 --amplitude 0.05 --gain 70 --sequence 2102 --transmit --output ~/work/ember-rx-uplink-20261017/runs/libre-power-02'
p=subprocess.Popen(['ssh','ngrabbs@192.168.1.251',cmd],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
lines=[]
for line in p.stdout:
 lines.append(line)
 if line.startswith('UPLINK_PROBE_READY'):break
else:raise RuntimeError('No TX readiness')
code='''import serial,time
s=serial.Serial('/dev/serial/by-id/usb-tinysa.org_tinySA4_400-if00',115200,timeout=.1,exclusive=True)
s.reset_input_buffer()
for c in ['calc off','attenuate 10','rbw 10']:
 s.write((c+'\\r').encode());time.sleep(.1);s.read(10000)
print('SA_READY',flush=True)
for i in range(10):
 s.write(b'scan 434900000 435100000 100 3\\r');data=b'';end=time.monotonic()+2
 while time.monotonic()<end:
  data+=s.read(16000)
  if b'ch>' in data:break
 print('SCAN',i,data.decode(errors='replace'),flush=True)
'''
q=subprocess.Popen(['ssh','ngrabbs@192.168.1.252','~/tools/ember-lte-version-build/bin/python -u -c '+shlex.quote(code)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
first=q.stdout.readline();assert first.strip()=='SA_READY',first
p.stdin.write('GO\n');p.stdin.flush()
out,_=p.communicate(timeout=15);lines.append(out)
sa,_=q.communicate(timeout=30)
(root/'libre-power-02-tx.txt').write_text(''.join(lines));(root/'libre-power-02-scans.txt').write_text(first+sa)
print('tx exit',p.returncode,'measurement exit',q.returncode)
