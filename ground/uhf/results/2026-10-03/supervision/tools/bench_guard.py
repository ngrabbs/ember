"""Finite fallback stop for one named bench session; no restart or PID signalling."""
import argparse,json,time
from pathlib import Path
from radio_control import request
p=argparse.ArgumentParser();p.add_argument('--state',type=Path,required=True);p.add_argument('--run-id',required=True);p.add_argument('--seconds',type=int,required=True);a=p.parse_args()
end=time.monotonic()+a.seconds
while time.monotonic()<end:
 try:r=json.loads((a.state/'status.json').read_text())
 except (OSError,ValueError):break
 if r['run_id']!=a.run_id or r['state'] not in ('RUNNING','STARTING'):break
 time.sleep(.5)
else:
 r=request(a.state/'control.sock',dict(command='status'))
 if r['run_id']==a.run_id:print(request(a.state/'control.sock',dict(command='stop')),flush=True)
