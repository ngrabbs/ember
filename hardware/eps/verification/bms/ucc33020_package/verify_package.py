#!/usr/bin/env python3
"""Approved UCC33020 package gate; no native writes or circuit qualification."""
from pathlib import Path
from collections import Counter
import json,re,hashlib,subprocess,xml.etree.ElementTree as E,csv
H=Path(__file__).resolve().parent;ROOT=H.parents[4]
LIB=ROOT/'hardware/eps/rev_b/libraries/Ember_Charger_BMS_Review.kicad_sym'
FP=ROOT/'hardware/eps/rev_b/libraries/Ember_Charger_BMS_Review.pretty/TI_RAQ0012C_VSON12_5x4mm_CombLand_REVIEW.kicad_mod'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def parse(s):
 stack=[];root=None
 for t in re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^()\s]+',s):
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
def props(n):return {x[1]:x[2] for x in kids(n,'property')}
def j(n):return json.loads((H/n).read_text())
def close(a,b):assert abs(a-b)<2e-6,(a,b)
base=j('baseline.json')
for p,h in base['files'].items():assert sha(ROOT/p)==h,p
before=(H/'library_before.txt').read_text();after=LIB.read_text();assert after.startswith(before.rstrip()[:-1]),'existing library bytes changed'
old=parse(before);new=parse(after);assert len(kids(new,'symbol'))==len(kids(old,'symbol'))+1
for s in kids(old,'symbol'):assert s==next(x for x in kids(new,'symbol') if x[1]==s[1])
ns=[x for x in kids(new,'symbol') if x[1]=='UCC33020RAQR_REVIEW'];assert len(ns)==1
protected=lambda p:p.endswith(('.kicad_sch','.kicad_pro','.kicad_pcb','.kicad_sym','.kicad_mod')) or Path(p).name in {'sym-lib-table','fp-lib-table'}
changed=set()
for args in [['diff','--name-only',base['commit'],'--'],['ls-files','--others','--exclude-standard']]:changed.update(p for p in subprocess.check_output(['git',*args],cwd=ROOT,text=True).splitlines() if protected(p))
allowed={str(x.relative_to(ROOT)) for x in [LIB,FP,H/'fixture/ucc33020_check.kicad_sch',H/'fixture/ucc33020_check.kicad_pro',H/'fixture/ucc33020_check.kicad_pcb',H/'fixture/sym-lib-table',H/'fixture/fp-lib-table']};assert changed==allowed,(changed,allowed)
for name in ['sym-lib-table','fp-lib-table']:
 t=parse((H/'fixture'/name).read_text());ls=kids(t,'lib');assert len(ls)==1
 assert one(ls[0],'name')[1]=='Ember_Charger_BMS_Review';assert one(ls[0],'uri')[1].startswith('${KIPRJMOD}/')
 assert (H/'fixture'/one(ls[0],'uri')[1].replace('${KIPRJMOD}/','')).resolve().exists()
names=['EN/FLT','VINP','GNDP','GNDP','GNDP','GNDP','SEL','VCC','GNDS','GNDS','GNDS','GNDS']
types=['bidirectional','power_in','power_in','power_in','power_in','power_in','input','power_out','power_in','power_in','power_in','power_in']
s=j('symbol_query.json');ips=j('instance_pins.json')['pins'];assert len(s['pins'])==s['pin_count']==len(ips)==12
assert Counter(p['number'] for p in s['pins'])==Counter(map(str,range(1,13)))
assert {p['number']:(p['name'],p['type']) for p in s['pins']}=={str(i+1):(n,t) for i,(n,t) in enumerate(zip(names,types))}
assert {p['number']:p['name'] for p in ips}=={str(i+1):n for i,n in enumerate(names)}
sch=parse((H/'fixture/ucc33020_check.kicad_sch').read_text());ss=kids(sch,'symbol');assert len(ss)==3 and Counter(props(x)['Reference'] for x in ss)==Counter(['U1','#PWR01','#PWR02'])
u=next(x for x in ss if props(x)['Reference']=='U1');fields=props(u);assert fields==j('instance_fields.json')['fields']
embedded=next(x for x in kids(one(sch,'lib_symbols'),'symbol') if x[1]=='Ember_Charger_BMS_Review:UCC33020RAQR_REVIEW')
assert embedded[2:]==ns[0][2:],'saved embedded symbol differs from native library definition'
nativepins=[p for unit in kids(ns[0],'symbol') for p in kids(unit,'pin')]
assert len(nativepins)==12 and {one(p,'number')[1]:(one(p,'name')[1],p[1]) for p in nativepins}=={str(i+1):(n,t) for i,(n,t) in enumerate(zip(names,types))}
assert fields['Value']==fields['MFG P/N']=='UCC33020RAQR' and fields['PackageSize']=='RAQ0012C' and fields['Manufacturer']=='Texas Instruments'
assert fields['Footprint']=='Ember_Charger_BMS_Review:'+FP.stem and 'CUSTOM' in fields['Review'];assert one(sch,'paper')[1]=='B';assert not kids(sch,'no_connect')
text=next(x for x in kids(sch,'text') if x[1].startswith('CUSTOM'));assert 'Construction authorized:' in text[1]
color=one(one(one(text,'effects'),'font'),'color');assert list(map(float,color[1:]))==[0,255,0,1]
# Explicit expected object multiplicities, independent of readback data.
xy=[(-2.4,-1.625),(-2.4,-.975),(-2.4,-.325),(-2.4,.325),(-2.4,.975),(-2.4,1.625),(2.4,1.625),(2.4,.975),(2.4,.325),(2.4,-.325),(2.4,-.975),(2.4,-1.625)]
expected=[(str(i+1),x,y,.6,.3,.05,('F.Cu','F.Mask')) for i,(x,y) in enumerate(xy)]
expected += [('3',-2.25,.325,.3,1.6,.05,('F.Cu','F.Mask')),('9',2.25,-.325,.3,1.6,.05,('F.Cu','F.Mask'))]
expected += [('',x,y,w,h,r,('F.Paste',)) for n,x,y,w,h,r,l in expected[:14]]
expected += [('',x,y,w+.14,h+.14,.12,('F.Mask',)) for n,x,y,w,h,r,l in expected[:14]]
lib=j('footprint_query.json');board=parse((H/'fixture/ucc33020_check.kicad_pcb').read_text());fps=kids(board,'footprint');assert len(fps)==1;f=fps[0];pads=kids(f,'pad');live=j('live_after_save.json');lp=live['pads']
assert len(pads)==len(lib['pads'])==lib['pad_count']==len(lp)==live['pad_count']==42
assert live['source']=='ipc';assert props(f)['Reference']=='U1' and props(f)['Value']=='UCC33020RAQR';assert f[1]=='Ember_Charger_BMS_Review:'+FP.stem
at=list(map(float,one(f,'at')[1:3]));close(at[0],50);close(at[1],50)
want=Counter([str(x) for x in range(1,13)]+['3','9']+['']*28)
assert Counter(p[1] for p in pads)==Counter(p['number'] for p in lib['pads'])==Counter(p['number'] for p in lp)==want
# Counter rows preserve the two duplicate ground spines and all 28 blanks.
def key(n,x,y,w,h,r,l):return (n,round(x,5),round(y,5),round(w,5),round(h,5),round(r,5),tuple(sorted(l)))
librows=[];saved=[]
for p in lib['pads']:
 assert p['type']=='smd' and p['shape']=='roundrect' and not p['drill']
 librows.append(key(p['number'],p['x'],p['y'],p['width'],p['height'],min(p['width'],p['height'])*p['roundrect_rratio'],p['layers']))
for p in pads:
 assert p[2:4]==['smd','roundrect'] and not kids(p,'drill')
 x,y=map(float,one(p,'at')[1:3]);w,h=map(float,one(p,'size')[1:3]);r=min(w,h)*float(one(p,'roundrect_rratio')[1]);layers=one(p,'layers')[1:]
 saved.append(key(p[1],x,y,w,h,r,layers))
assert Counter(librows)==Counter(saved)==Counter(key(*e) for e in expected)
assert Counter((p['number'],round(p['x']-at[0],5),round(p['y']-at[1],5),tuple(sorted(p['layers']))) for p in lp)==Counter((n,round(x,5),round(y,5),tuple(sorted(l))) for n,x,y,w,h,r,l in expected)
for p in lp:
 n=p['number'];assert (p['net']=='GND' if n in ['3','4','5','6'] else p['net']=='GND_BMS_RAW' if n in ['9','10','11','12'] else p['net']=='' if n=='' else p['net'].startswith('unconnected-'))
# Connected-region count from robust overlaps; all comb overlaps exceed corner radii.
def regions(items):
 groups=[]
 for _,x,y,w,h,_,_ in items:
  box=(x-w/2,y-h/2,x+w/2,y+h/2);hit=[]
  for i,g in enumerate(groups):
   if any(min(box[2],b[2])>max(box[0],b[0])+1e-6 and min(box[3],b[3])>max(box[1],b[1])+1e-6 for b in g):hit.append(i)
  g=[box]
  for i in reversed(hit):g+=groups.pop(i)
  groups.append(g)
 return len(groups)
assert regions(expected[:14])==regions(expected[14:28])==regions(expected[28:])==regions(expected[:14]+expected[28:])==8
for cu,mask in zip(expected[:14],expected[28:]):
 assert mask[0]=='' and mask[-1]==('F.Mask',);close(mask[3]-cu[3],.14);close(mask[4]-cu[4],.14);close(mask[5]-cu[5],.07)
assert not kids(f,'model') and not kids(parse(FP.read_text()),'model')
q=lib['graphics'];court=[g for g in q if g['layer']=='F.CrtYd'];assert len(court)==1 and court[0]['start']=={'x':-3.1,'y':-2.4} and court[0]['end']=={'x':3.1,'y':2.4}
assert court[0]['fill']=='none' and court[0]['stroke_width_mm']==.05
assert Counter(g['layer'] for g in q)=={'F.CrtYd':1,'F.Fab':1,'F.SilkS':3}
# CLI graph has exactly the intended two return groups plus four unwired pins.
x=E.parse(H/'fixture.xml').getroot();cs=x.findall('components/comp');assert len(cs)==1 and cs[0].get('ref')=='U1'
graph={n.get('name'):{(p.get('ref'),p.get('pin')) for p in n.findall('node')} for n in x.findall('nets/net')}
allnodes=[a for n in graph.values() for a in n];assert len(allnodes)==len(set(allnodes))==12 and len(graph)==6
assert graph['GND']=={('U1',n) for n in ['3','4','5','6']};assert graph['GND_BMS_RAW']=={('U1',n) for n in ['9','10','11','12']}
assert all(len(v)==1 for k,v in graph.items() if k not in ['GND','GND_BMS_RAW'])
v=[v for s in j('erc.json')['sheets'] for v in s['violations']];assert Counter((z['severity'],z['type']) for z in v)=={('error','pin_not_connected'):4,('error','power_pin_not_driven'):3,('error','pin_not_driven'):1}
# Physical lead table retains every repeated ground as a separate row.
rows=[{'physical_lead':i+1,'function':names[i],'symbol_type':types[i],'pad':i+1,'x_mm':x,'y_mm':y,'view':'TI p4 top; 1 upper-left; 1..6 down-left,7..12 up-right; p35 front land'} for i,(x,y) in enumerate(xy)]
with (H/'physical_map.csv').open('w') as z:
 w=csv.DictWriter(z,fieldnames=rows[0],lineterminator='\n');w.writeheader();w.writerows(rows)
source={str(p.relative_to(ROOT)):sha(p) for p in [LIB,FP,*[H/'fixture'/n for n in ['ucc33020_check.kicad_sch','ucc33020_check.kicad_pro','ucc33020_check.kicad_pcb','sym-lib-table','fp-lib-table']]]}
assert source==j('native_source_sha256.json'),'native source changed after export/readback'
result={'status':'DEVELOPMENT PHYSICAL MAP PASS; CUSTOM REVIEW MARKER RETAINED; CIRCUIT/ASSEMBLY QUALIFICATION OPEN','physical_pins':12,'raw_library_pads':42,'raw_saved_pads':42,'raw_live_after_save_pads':42,'split':{'copper':14,'paste_only':14,'mask_only':14},'continuous_regions_each':8,'frozen_files':len(base['files']),'previous_library_prefix_exact':True,'fixture_erc_errors':8,'fixture_erc_warnings':0,'protected_changes':sorted(changed),'native_source_sha256':source}
(H/'verified.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
