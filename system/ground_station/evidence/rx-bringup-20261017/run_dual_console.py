import subprocess,shlex,pathlib,sys
root=pathlib.Path(__file__).parent
name='auto-ota-030-07'
code='''import serial,time
with serial.Serial('/dev/serial/by-id/usb-Raspberry_Pi_Pico_DF641455DB822427-if00',115200,timeout=.1,exclusive=True) as s:
 s.write(b'version\\nstatus\\n');data=b'';end=time.monotonic()+2
 while time.monotonic()<end:data+=s.read(16000)
 assert b'boot=2786831095' in data and b'uhf_mode=0' in data,data
 print('IHU_READY',flush=True);print(data.decode(),flush=True)
 end=time.monotonic()+40
 while time.monotonic()<end:
  d=s.read(16000)
  if d:print(d.decode(),end='',flush=True)
 s.write(b'status\\n');end=time.monotonic()+1
 while time.monotonic()<end:
  d=s.read(16000)
  if d:print(d.decode(),end='',flush=True)
'''
p=subprocess.Popen(['ssh','ngrabbs@192.168.1.252','~/tools/ember-lte-version-build/bin/python -u -c '+shlex.quote(code)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
line=p.stdout.readline();assert line.strip()=='IHU_READY',line
with (root/(name+'-run.txt')).open('w') as f:r=subprocess.run([sys.executable,str(root/'run_auto_probe020.py'),name,'2007','25','70'],stdout=f,stderr=subprocess.STDOUT,timeout=65)
out,_=p.communicate(timeout=45);(root/(name+'-ihu.txt')).write_text(line+out)
print('trial',r.returncode,'IHU capture',p.returncode)
