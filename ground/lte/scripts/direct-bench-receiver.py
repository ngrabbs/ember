#!/usr/bin/env python3
"""Temporary Walter throughput endpoint; separate from native telemetry/Yamcs."""
import argparse,json,socket,struct,time,zlib
from datetime import datetime,timezone

def decode(data):
 if len(data)not in (128,512,1024)or data[:4]!=b'ELTB':raise ValueError('shape')
 version,flags,header=struct.unpack_from('!BBH',data,4)
 run,seq,sender_ms=struct.unpack_from('!III',data,8);size,reserved=struct.unpack_from('!HH',data,20)
 checksum,boot=struct.unpack_from('!II',data,24)
 if (version,flags,header,reserved)!=(1,0,32,0)or size!=len(data)or not run or not boot:raise ValueError('header')
 canonical=data[:24]+b'\0'*4+data[28:]
 if zlib.crc32(canonical)!=checksum:raise ValueError('crc')
 if data[32:]!=bytes((run+seq+i)&255 for i in range(32,size)):raise ValueError('pattern')
 return dict(run=run,seq=seq,sender_ms=sender_ms,bytes=size,boot=boot,crc32=checksum)

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=int,required=True);p.add_argument('--port',type=int,default=51002);p.add_argument('--seconds',type=int,default=180);a=p.parse_args()
 if not 0<a.run<2**32 or not 1024<=a.port<=65535 or not 1<=a.seconds<=300:p.error('bounded run/port/duration required')
 sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);sock.bind(('0.0.0.0',a.port));sock.settimeout(.25)
 end=time.monotonic()+a.seconds;seen=set();duplicates=bad=other=out_of_order=0;highest=-1;first=None;last=None
 print(json.dumps(dict(event='receiver_ready',run=a.run,port=a.port,seconds=a.seconds,started_monotonic_ns=time.monotonic_ns())),flush=True)
 try:
  while time.monotonic()<end:
   try:data,peer=sock.recvfrom(2048)
   except socket.timeout:continue
   try:row=decode(data)
   except ValueError:bad+=1;continue
   if row['run']!=a.run:other+=1;continue
   now=time.monotonic_ns();identity=(row['boot'],row['seq']);duplicate=identity in seen
   if duplicate:duplicates+=1
   else:
    if row['seq']<highest:out_of_order+=1
    highest=max(highest,row['seq']);seen.add(identity);first=now if first is None else first;last=now
   print(json.dumps(dict(event='received',received_utc=datetime.now(timezone.utc).isoformat(),monotonic_ns=now,duplicate=duplicate,source_port=peer[1],**row)),flush=True)
 except KeyboardInterrupt:pass
 finally:
  sock.close();print(json.dumps(dict(event='receiver_done',run=a.run,unique=len(seen),duplicates=duplicates,out_of_order=out_of_order,bad=bad,other_runs=other,first_monotonic_ns=first,last_monotonic_ns=last,ended_monotonic_ns=time.monotonic_ns())),flush=True)
if __name__=='__main__':main()
