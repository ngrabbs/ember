#!/usr/bin/env python3
"""Bounded package verification; read-only fallback for omitted native geometry."""
from pathlib import Path
from collections import Counter
import json,re,hashlib,subprocess,xml.etree.ElementTree as E
H=Path(__file__).resolve().parent;R=H.parents[4]
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
def unwrap(p):return json.loads(json.loads(p.read_text())['content'][0]['text'])
name='C_0603_TDK_CGA3_PA0.70_PB0.70_PC0.70_REVIEW';library=R/'hardware/eps/rev_b/libraries/Ember_Charger_BMS_Review.pretty'/(name+'.kicad_mod')
base=json.loads((H/'frozen_baseline.json').read_text())
for p,h in base['files'].items():assert sha(R/p)==h,p
allowed={str(library.relative_to(R)),*[str((H/'fixture'/('tdk_filter_check'+s)).relative_to(R)) for s in ['.kicad_sch','.kicad_pcb','.kicad_pro']],str((H/'fixture/fp-lib-table').relative_to(R))}
protected=lambda s:s.endswith(('.kicad_sch','.kicad_pcb','.kicad_pro','.kicad_sym','.kicad_mod')) or Path(s).name in {'sym-lib-table','fp-lib-table'}
changed=set()
for args in [['diff','--name-only',base['commit'],'--'],['ls-files','--others','--exclude-standard']]:
 changed.update(p for p in subprocess.check_output(['git',*args],cwd=R,text=True).splitlines() if protected(p))
assert changed==allowed,(changed,allowed)
lib=unwrap(H/'footprint.json');live=unwrap(H/'pads.json');sym=unwrap(H/'symbol.json')
assert lib['pad_count']==live['pad_count']==4
assert Counter(p['number'] for p in lib['pads'])==Counter(p['number'] for p in live['pads'])=={'1':1,'2':1,'':2}
assert sym['pin_count']==2 and {(p['number'],p['type']) for p in sym['pins']}=={('1','passive'),('2','passive')}
board=parse((H/'fixture/tdk_filter_check.kicad_pcb').read_text());fps=kids(board,'footprint');assert len(fps)==1;fp=fps[0]
assert list(map(float,one(fp,'at')[1:3]))==[50,50] and fp[1]=='Ember_Charger_BMS_Review:'+name
assert float(one(one(board,'setup'),'pad_to_mask_clearance')[1])==.05
pads=kids(fp,'pad');assert len(pads)==4 and Counter(p[1] for p in pads)=={'1':1,'2':1,'':2}
for p in pads:
 n=p[1];xy=list(map(float,one(p,'at')[1:3]));size=list(map(float,one(p,'size')[1:3]));layers=one(p,'layers')[1:]
 assert xy in [[-.7,0],[.7,0]] and p[2:4]==['smd','roundrect'] and not kids(p,'drill')
 if n:
  assert xy==([-.7,0] if n=='1' else [.7,0]) and size==[.7,.7] and set(layers)=={'F.Cu','F.Paste','F.Mask'}
  assert abs(float(one(p,'roundrect_rratio')[1])-1/14)<1e-5
 else:
  assert size==[.8,.8] and layers==['F.Mask'] and float(one(p,'roundrect_rratio')[1])==.125
 l=[a for a in lib['pads'] if a['number']==n and a['x']==xy[0]];assert len(l)==1
 assert [l[0]['width'],l[0]['height']]==size and set(l[0]['layers'])==set(layers)
 assert l[0]['type']=='smd' and l[0]['shape']=='roundrect' and l[0]['rotation']==0 and l[0]['drill']==[]
 assert abs(l[0]['roundrect_rratio']-float(one(p,'roundrect_rratio')[1]))<1e-6
 a=[a for a in live['pads'] if a['number']==n and abs(a['x']-50-xy[0])<1e-6];assert len(a)==1 and a[0]['y']==50 and a[0]['net']==''
 assert not kids(p,'solder_mask_margin') and not kids(p,'solder_paste_margin')
assert not kids(fp,'solder_mask_margin') and not kids(fp,'solder_paste_margin')
source=parse(library.read_text());assert not kids(source,'model')
cr=[a for a in kids(source,'fp_rect') if one(a,'layer')[1]=='F.CrtYd'];assert len(cr)==1
assert list(map(float,one(cr[0],'start')[1:]))==[-1.35,-.7] and list(map(float,one(cr[0],'end')[1:]))==[1.35,.7]
# CLI layer exports prove effective openings, including the board's inherited margin.
layer_bounds={}
for layer in ['F_Cu','F_Paste','F_Mask']:
 bounds=[]
 for p in E.parse(H/f'board_{layer}.svg').getroot().iter():
  if p.tag.endswith('path') and 'fill-opacity:' in p.get('style',''):
   ns=list(map(float,re.findall(r'-?\d+(?:\.\d+)?',p.get('d',''))));assert len(ns)%2==0
   bounds.append((min(ns[::2]),min(ns[1::2]),max(ns[::2]),max(ns[1::2])))
 expected=[(48.9,49.6,49.7,50.4),(50.3,49.6,51.1,50.4)] if layer=='F_Mask' else [(48.95,49.65,49.65,50.35),(50.35,49.65,51.05,50.35)]
 assert Counter(bounds)==Counter({x:(2 if layer=='F_Mask' else 1) for x in expected})
 layer_bounds[layer]=[dict(bounds_mm=list(b),multiplicity=Counter(bounds)[b]) for b in sorted(set(bounds))]
x=E.parse(H/'fixture.xml').getroot();cs=x.findall('components/comp');assert len(cs)==1 and cs[0].get('ref')=='C1'
fields={f.get('name'):f.text for f in cs[0].findall('fields/field')}
for k,v in {'MFG P/N':'CGA3E2C0G1H102J080AA','Manufacturer':'TDK','PackageSize':'0603','Tolerance':'5%','Voltage':'50 V','Dielectric':'C0G'}.items():assert fields[k]==v
assert cs[0].findtext('footprint')=='Ember_Charger_BMS_Review:'+name
nodes=[(n.get('ref'),n.get('pin')) for net in x.findall('nets/net') for n in net.findall('node')];assert Counter(nodes)=={('C1','1'):1,('C1','2'):1}
v=[v for s in json.loads((H/'erc.json').read_text())['sheets'] for v in s['violations']];assert Counter(a['type'] for a in v)=={'pin_not_connected':2}
sch=parse((H/'fixture/tdk_filter_check.kicad_sch').read_text());assert one(sch,'paper')[1]=='B' and len(kids(sch,'symbol'))==1 and not kids(sch,'wire') and not kids(sch,'no_connect')
instance=kids(sch,'symbol')[0];hidden=[p[1] for p in kids(instance,'property') if kids(p,'hide')]
assert all(p in hidden for p in ['Tolerance','Voltage','PackageSize','Dielectric'])
texts=kids(sch,'text');review=[t for t in texts if t[1]=='CUSTOM FOOTPRINT — REVIEW REQUIRED'];assert len(review)==1
assert one(one(one(review[0],'effects'),'font'),'color')[1:]==['0','255','0','1']
source_hash={str(library.relative_to(R)):sha(library),**{str(p.relative_to(R)):sha(p) for p in (H/'fixture').iterdir() if protected(p.name)}}
(H/'native_source_sha256.json').write_text(json.dumps(source_hash,indent=2)+'\n')
result=dict(status='PAD_MAP_AND_DISPOSABLE_MASK_GEOMETRY_VERIFIED_REVIEW_REQUIRED',baseline_native_files_preserved=len(base['files']),new_native_paths=len(allowed),raw_pads=4,numbered_electrical_pads=2,blank_mask_only_pads=2,live_query_source=live['source'],effective_mask_opening_mm=.8,mask_margin_from_copper_mm=.05,mask_web_mm=.6,layer_bounds=layer_bounds,erc_errors=2,erc_clean=False,full_S11_presentation=False,hidden_auxiliary_fields=hidden,real_EPS_circuit_or_PCB_mutated=False,qualification=False,limits=['Ratings are visible as annotations; installed tool cannot position/show native auxiliary fields','Unwired fixture; two genuine unconnected-pin ERC errors; generic fixture defaults retained','Board Value is long package identifier, not an assembly MPN','Recheck effective mask in real PCB settings before placement','No assembly-process, coupled-filter response or hardware/flight qualification'])
(H/'verified.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='layer_bounds'},indent=2))
