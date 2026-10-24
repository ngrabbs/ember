#!/usr/bin/env python3
"""Saved stock/custom physical-map gate; preserves the main circuit and prior fixtures."""
from common import *
from collections import Counter
import csv,hashlib,xml.etree.ElementTree as E
F=H/'disposable/swd_parts_check'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def un(r):assert not r.get('isError');return json.loads(r['content'][0]['text'])
def descend(n,k):
 out=[]
 for x in n:
  if isinstance(x,list):
   if x and x[0]==k:out.append(x)
   out.extend(descend(x,k))
 return out
b=json.loads((H/'baseline.json').read_text());rb=json.loads((H/'readback.json').read_text())
libpath='hardware/eps/rev_b/libraries/Ember_Charger_BMS_Review.kicad_sym'
for p,h in b['frozen'].items():
 assert portable(p)
 if p!=libpath:assert sha(ROOT/p)==h,p
for p,h in b['five_progress'].items():assert sha(ROOT/p)==h,p
old=parse((H/'review_library_before.txt').read_text());now=parse((ROOT/libpath).read_text())
assert sha(H/'review_library_before.txt')==b['frozen'][libpath]
newsyms=[s for s in kids(now,'symbol') if s[1]=='TMUX1511PWR_REVIEW'];assert len(newsyms)==1
assert [s for s in now if not isinstance(s,list) or not s or s[0]!='symbol' or s[1]!='TMUX1511PWR_REVIEW']==old
maps={
 'J1':{'1':('VCC','power_in'),'2':('SWDIO','bidirectional'),'3':('~{RESET}','open_collector'),'4':('SWCLK','output'),'5':('GND','power_in'),'6':('SWO','input')},
 'U1':{'1':('SEL1','input'),'2':('S1','bidirectional'),'3':('D1','bidirectional'),'4':('SEL2','input'),'5':('S2','bidirectional'),'6':('D2','bidirectional'),'7':('GND','power_in'),'8':('D3','bidirectional'),'9':('S3','bidirectional'),'10':('SEL3','input'),'11':('D4','bidirectional'),'12':('S4','bidirectional'),'13':('SEL4','input'),'14':('VDD','power_in')},
 'U2':{'1':('GND','power_in'),'2':('~{RESET}','output'),'3':('VDD','power_in')}}
pcb=parse(F.with_suffix('.kicad_pcb').read_text());fps=kids(pcb,'footprint');assert len(fps)==3
assert len({props(f)['Reference'] for f in fps})==3
sch=parse(F.with_suffix('.kicad_sch').read_text());ss=kids(sch,'symbol');assert len(ss)==7 and len({(props(s)['Reference'],one(s,'unit')[1]) for s in ss})==7
assert one(sch,'paper')[1]=='B' and not kids(sch,'wire') and not kids(sch,'no_connect')
rows=[];total=0
for ref,mpn,xy in [('J1','TC2030-CTX-NL',(100,100)),('U1','TMUX1511PWR',(140,100)),('U2','TPS3839K33DBZR',(175,100))]:
 sym=un(rb['symbols'][ref]);fp=un(rb['footprints'][ref]);query=un(rb['pads'][ref]);pins=sym['pins']
 assert len(pins)==sym['pin_count']==len(maps[ref]) and len({p['number'] for p in pins})==len(pins)
 assert {p['number']:(p['name'],p['type']) for p in pins}==maps[ref]
 placed=next(f for f in fps if props(f)['Reference']==ref);pads=kids(placed,'pad')
 assert list(map(float,one(placed,'at')[1:3]))==list(xy)
 count=9 if ref=='J1' else len(pins)
 assert len(pads)==len(fp['pads'])==fp['pad_count']==len(query['pads'])==query['pad_count']==count
 assert query['source']=='file' and all(p['net']=='' for p in query['pads'])
 assert Counter(p[1] for p in pads)==Counter(p['number'] for p in fp['pads'])==Counter(p['number'] for p in query['pads'])==Counter({**{n:1 for n in maps[ref]},**({'':3} if ref=='J1' else {})})
 for p in pads:
  n=p[1];pos=tuple(map(float,one(p,'at')[1:3]));size=list(map(float,one(p,'size')[1:]));layers=set(one(p,'layers')[1:])
  q=next(q for q in fp['pads'] if q['number']==n and abs(q['x']-pos[0])<1e-6 and abs(q['y']-pos[1])<1e-6)
  a=next(a for a in query['pads'] if a['number']==n and abs(a['x']-xy[0]-pos[0])<1e-6 and abs(a['y']-xy[1]-pos[1])<1e-6)
  assert size==[q['width'],q['height']] and layers==set(q['layers'])==set(a['layers'])
  assert p[2]==q['type'] and p[3]==q['shape']
  drill=kids(p,'drill')
  if ref=='J1':
   if n:
    assert p[2:4]==['connect','circle'] and size==[.7874,.7874] and not drill and layers=={'F.Cu','F.Mask'}
    expected={str(i):(x,y) for i,x,y in [(1,-1.27,.635),(2,-1.27,-.635),(3,0,.635),(4,0,-.635),(5,1.27,.635),(6,1.27,-.635)]};assert pos==expected[n]
   else:
    assert p[2:4]==['np_thru_hole','circle'] and size==[.9906,.9906] and float(drill[0][1])==.9906
    assert pos in {(-2.54,0),(2.54,-1.016),(2.54,1.016)}
  else:
   assert p[2:4]==['smd','roundrect'] and not drill and layers=={'F.Cu','F.Mask','F.Paste'} and float(one(p,'roundrect_rratio')[1])==.25
   if ref=='U1':
    assert size==[1.475,.4];i=int(n);expected=(-2.8625,-1.95+(i-1)*.65) if i<=7 else (2.8625,1.95-(i-8)*.65)
   else:assert size==[1.475,.6];expected={'1':(-.9375,-.95),'2':(-.9375,.95),'3':(.9375,0)}[n]
   assert all(abs(a-z)<1e-6 for a,z in zip(pos,expected))
  rows.append({'reference':ref,'MPN':mpn,'physical_lead':n or 'mechanical alignment hole','function':maps[ref][n][0] if n else 'NPTH alignment','symbol_type':maps[ref][n][1] if n else 'not electrical','x_mm':pos[0],'y_mm':pos[1],'width_mm':size[0],'height_mm':size[1],'layers':','.join(sorted(layers)),'view':'PCB/component top, Xright/Ydown; TI ICs CCW from upper-left; Tag odd bottom/even top'})
 for s in [s for s in ss if props(s)['Reference']==ref]:assert props(s)['MFG P/N']==mpn and props(s)['Footprint']==placed[1]
 pc=next(c for c in un(rb['component_pins'])['components'] if c['reference']==ref)
 assert len(pc['pins'])==len(pins) and {p['number']:p['name'] for p in pc['pins']}=={n:v[0] for n,v in maps[ref].items()}
 total+=len(pads)
assert total==26 and len(rows)==26
xml=E.parse(H/'fixture.xml').getroot();cs=xml.findall('components/comp');assert len(cs)==len({c.get('ref') for c in cs})==3
endpoints=[(p.get('ref'),p.get('pin')) for n in xml.findall('nets/net') for p in n.findall('node')];assert len(endpoints)==len(set(endpoints))==23
vs=[v for s in json.loads((H/'erc.json').read_text())['sheets'] for v in s['violations']]
assert Counter((v['severity'],v['type']) for v in vs)=={('error','pin_not_connected'):23,('error','power_pin_not_driven'):6,('error','pin_not_driven'):5}
with (H/'physical_map.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=rows[0],lineterminator='\n');w.writeheader();w.writerows(rows)
sources={str(p.relative_to(ROOT)):sha(p) for p in H.rglob('*') if p.is_file() and portable(p) and (p.suffix in {'.kicad_sch','.kicad_pcb','.kicad_pro'} or p.name=='sym-lib-table')}
sources[libpath]=sha(ROOT/libpath)
result={'status':'DEVELOPMENT CONTACT/PIN MAP PASS; CIRCUIT/PVT/MECHANICAL QUALIFICATION OPEN','basis':'0660ad3','parts':3,'physical_electrical_pins':23,'raw_saved_pad_objects':26,'alignment_NPTH':3,'saved_query_source':'supported Konnect closed-board file readback; no live-after-save claim','frozen_byte_files':len(b['frozen'])-1,'prior_library_symbols_preserved':len(kids(old,'symbol')),'library_append_only':'TMUX1511PWR_REVIEW','five_progress_preserved':5,'ERC_errors':34,'ERC_warnings':0,'native_source_sha256':sources}
(H/'verified.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
