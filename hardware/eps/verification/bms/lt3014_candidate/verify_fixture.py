#!/usr/bin/env python3
"""Bounded saved stock-map/fixture verification, not circuit qualification."""
from pathlib import Path
from collections import Counter
import json,re,hashlib,subprocess,xml.etree.ElementTree as E,csv
H=Path(__file__).resolve().parent
ROOT=H.parents[4]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def parse(text):
 stack=[];root=None
 for t in re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^()\s]+',text):
  if t=='(':
   n=[]
   if stack:stack[-1].append(n)
   else:root=n
   stack.append(n)
  elif t==')':stack.pop()
  else:stack[-1].append(json.loads(t) if t.startswith('"') else t)
 assert not stack
 return root
def kids(n,k):return [x for x in n if isinstance(x,list) and x and x[0]==k]
def one(n,k):return kids(n,k)[0]
def props(n):return {p[1]:p[2] for p in kids(n,'property')}
base=json.loads((H/'frozen_baseline.json').read_text())
for p,h in base['files'].items():assert sha(ROOT/p)==h,p
protected=lambda s:s.endswith(('.kicad_sch','.kicad_pcb','.kicad_pro','.kicad_sym','.kicad_mod')) or Path(s).name in {'sym-lib-table','fp-lib-table'}
changed=set()
for args in [['diff','--name-only',base['commit'],'--'],['ls-files','--others','--exclude-standard']]:
 changed.update(p for p in subprocess.check_output(['git',*args],cwd=ROOT,text=True).splitlines() if protected(p))
allowed={str((H/'fixture'/('lt3014_check'+x)).relative_to(ROOT)) for x in ['.kicad_sch','.kicad_pcb','.kicad_pro']}
assert changed==allowed,(changed,allowed)
lib=json.loads((H/'handsolder_footprint.json').read_text());sym=json.loads((H/'symbol.json').read_text());live=json.loads((H/'live_after_save.json').read_text());ip=json.loads((H/'instance_pins.json').read_text());fields=json.loads((H/'instance_fields.json').read_text())
expected={'1':('VIN','power_in'),'2':('GND','power_in'),'3':('~{SHDN}','input'),'4':('ADJ','input'),'5':('VOUT','power_out')}
assert len(sym['pins'])==sym['pin_count']==len(ip['pins'])==5
assert {p['number']:(p['name'],p['type']) for p in sym['pins']}==expected
assert {p['number']:p['name'] for p in ip['pins']}=={k:v[0] for k,v in expected.items()}
assert fields['fields']['MFG P/N']==fields['fields']['Value']=='LT3014IS5#TRPBF'
assert fields['fields']['PackageSize']=='S5 TSOT-23-5' and fields['footprint']=='Package_TO_SOT_SMD:TSOT-23-5_HandSoldering'
sch=parse((H/'fixture/lt3014_check.kicad_sch').read_text());ss=kids(sch,'symbol');assert len(ss)==1
assert props(ss[0])==fields['fields'];assert not kids(sch,'wire') and not kids(sch,'no_connect')
assert one(sch,'paper')[1]=='B'
board=parse((H/'fixture/lt3014_check.kicad_pcb').read_text());fps=kids(board,'footprint');assert len(fps)==1;fp=fps[0]
assert props(fp)['Reference']=='U1' and props(fp)['Value']=='LT3014IS5#TRPBF'
assert fp[1]=='Package_TO_SOT_SMD:TSOT-23-5_HandSoldering';assert list(map(float,one(fp,'at')[1:3]))==[50,50]
pads=kids(fp,'pad');assert len(pads)==len(lib['pads'])==lib['pad_count']==len(live['pads'])==live['pad_count']==5
assert Counter(p[1] for p in pads)==Counter(p['number'] for p in lib['pads'])==Counter(p['number'] for p in live['pads'])==Counter('12345')
assert live['source']=='ipc' and all(p['net']=='' for p in live['pads'])
rows=[]
for p in pads:
 n=p[1];l=next(q for q in lib['pads'] if q['number']==n);a=next(q for q in live['pads'] if q['number']==n)
 xy=list(map(float,one(p,'at')[1:3]));size=list(map(float,one(p,'size')[1:3]));assert xy==[l['x'],l['y']] and size==[l['width'],l['height']]
 assert p[2:4]==[l['type'],l['shape']]==['smd','roundrect'];assert not kids(p,'drill') and l['drill']==[]
 assert set(one(p,'layers')[1:])==set(l['layers'])==set(a['layers'])=={'F.Cu','F.Mask','F.Paste'}
 assert float(one(p,'roundrect_rratio')[1])==l['roundrect_rratio']==.25
 assert abs(a['x']-50-xy[0])<1e-6 and abs(a['y']-50-xy[1])<1e-6
 rows.append({'physical_lead':n,'function':expected[n][0],'symbol_type':expected[n][1],'pad':n,'x_mm':xy[0],'y_mm':xy[1],'width_mm':size[0],'height_mm':size[1],'view':'ADI p2 top; p14 rotated90CW; pin1 upper-left'})
with (H/'physical_map.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=rows[0],lineterminator='\n');w.writeheader();w.writerows(rows)
x=E.parse(H/'fixture.xml').getroot();cs=x.findall('components/comp');assert len(cs)==1 and cs[0].get('ref')=='U1'
nodes=[(p.get('ref'),p.get('pin')) for n in x.findall('nets/net') for p in n.findall('node')];assert len(nodes)==len(set(nodes))==5 and set(nodes)=={('U1',n) for n in '12345'}
assert len(x.findall('nets/net'))==5
v=[v for s in json.loads((H/'erc.json').read_text())['sheets'] for v in s['violations']]
assert Counter(vv['type'] for vv in v)=={'pin_not_connected':5,'power_pin_not_driven':2,'pin_not_driven':2}
assert all(vv['severity']=='error' for vv in v)
source={str(p.relative_to(H)):sha(p) for p in (H/'fixture').iterdir() if p.suffix in {'.kicad_pro','.kicad_sch','.kicad_pcb'}}
assert source==json.loads((H/'native_source_sha256.json').read_text()),'native sources changed after final export/readback'
result={'status':'STOCK PHYSICAL MAP PASS; CIRCUIT AND ASSEMBLY QUALIFICATION OPEN','raw_saved_pads':5,'raw_live_after_save_pads':5,'symbol_pins':5,'mechanical_or_EP':0,'frozen_files':len(base['files']),'fixture_erc_errors':9,'fixture_erc_warnings':0,'native_source_sha256':source,'protected_changes':sorted(changed)}
(H/'verified.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
