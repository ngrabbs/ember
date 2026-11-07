#!/usr/bin/env python3
"""Check geometry exported by Konnect; never reads or writes KiCad source."""
from pathlib import Path
import json
HERE=Path(__file__).resolve().parent
out={}
for name,l in json.loads((HERE/'layouts.json').read_text()).items():
 wires=l['wires'];nodes={}
 for w in wires:
  x1,y1,x2,y2=[round(w[k],5) for k in ['x1','y1','x2','y2']]
  assert x1==x2 or y1==y2
  for x,y in [(x1,y1),(x2,y2)]:
   assert abs(x/1.27-round(x/1.27))<1e-5 and abs(y/1.27-round(y/1.27))<1e-5,(name,x,y)
   nodes[(x,y)]=set()
 for (x,y),dirs in nodes.items():
  for w in wires:
   x1,y1,x2,y2=[round(w[k],5) for k in ['x1','y1','x2','y2']]
   if y1==y2==y and min(x1,x2)<=x<=max(x1,x2):
    if x>min(x1,x2):dirs.add('L')
    if x<max(x1,x2):dirs.add('R')
   if x1==x2==x and min(y1,y2)<=y<=max(y1,y2):
    if y>min(y1,y2):dirs.add('U')
    if y<max(y1,y2):dirs.add('D')
  assert len(dirs)<4,(name,x,y,dirs)
 overlaps=0
 for k,a in enumerate(wires):
  for b in wires[k+1:]:
   if abs(a['y1']-a['y2'])<1e-6 and abs(b['y1']-b['y2'])<1e-6 and abs(a['y1']-b['y1'])<1e-6:
    overlaps+=min(max(a['x1'],a['x2']),max(b['x1'],b['x2']))-max(min(a['x1'],a['x2']),min(b['x1'],b['x2']))>1e-5
   if abs(a['x1']-a['x2'])<1e-6 and abs(b['x1']-b['x2'])<1e-6 and abs(a['x1']-b['x1'])<1e-6:
    overlaps+=min(max(a['y1'],a['y2']),max(b['y1'],b['y2']))-max(min(a['y1'],a['y2']),min(b['y1'],b['y2']))>1e-5
 assert overlaps==0,(name,overlaps)
 out[name]={'wire_count':len(wires),'four_direction_endpoints':0,'off_grid_endpoints':0,'collinear_overlaps':0,'unresolved_bounds':l['bounds_unresolved']}
(HERE/'geometry.json').write_text(json.dumps(out,indent=2)+'\n');print(out)
