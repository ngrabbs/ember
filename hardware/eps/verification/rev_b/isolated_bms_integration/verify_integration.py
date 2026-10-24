#!/usr/bin/env python3
"""Reproducible exact graph union and bounded native/preservation checks."""
from common import *
from collections import Counter
import csv,copy,fnmatch,hashlib,subprocess,xml.etree.ElementTree as E
from pypdf import PdfReader
BASE='f11ee84a0b302c72e44ec62f3172903e350f7f2a'
P=ROOT/'hardware/eps/rev_b'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,v):(H/n).write_text(json.dumps(v,indent=2)+'\n')
def graph(path):
 d=E.parse(path).getroot();cs=d.findall('components/comp')
 refs=[c.get('ref') for c in cs];assert len(refs)==len(set(refs))
 ns=d.findall('nets/net');names=[n.get('name') for n in ns];assert len(names)==len(set(names))
 endpoints=[(p.get('ref'),p.get('pin')) for n in ns for p in n.findall('node')]
 assert len(endpoints)==len(set(endpoints))
 return {c.get('ref'):c for c in cs},{n.get('name'):{(p.get('ref'),p.get('pin')) for p in n.findall('node')} for n in ns}
def meta(c):
 return {k:c.findtext(k) or '' for k in ['value','footprint','datasheet','tstamps']}|{'libsource':c.find('libsource').attrib,'fields':{x.get('name'):x.text or '' for x in c.findall('fields/field')}}
def descend(n,k):
 out=[]
 for x in n:
  if isinstance(x,list):
   if x and x[0]==k:out.append(x)
   out.extend(descend(x,k))
 return out
old,on=graph(H/'before.xml');new,nn=graph(H/'eps_rev_b.xml')
assert (len(old),len(on),len(new),len(nn))==(243,137,275,146)
for r,c in old.items():assert meta(c)==meta(new[r]),r
newrefs={'U900','U901','U902',*[f'R{i}' for i in range(900,912)],*[f'C{i}' for i in range(900,917)]}
assert set(new)-set(old)==newrefs
expected={k:set(v) for k,v in on.items()}
migrated={('U201','8'),('R218','1'),('R219','1'),('C210','1')}
assert migrated<=expected['+3V3'];expected['+3V3']-=migrated
consumed={('U100','26'),('U100','29')}
removed={k for k,v in expected.items() if v and v<=consumed}
assert len(removed)==2 and all(k.startswith('unconnected-') for k in removed)
for k in removed:del expected[k]
add={
 '+3V3':{('U900','1'),('C900','1'),('C916','1'),('R902','1'),('R907','1')},
 'GND':{*(('C'+str(i),'2') for i in [*range(900,910),916]),('R900','2'),('R910','2'),('U900','2'),*(('U901',str(i)) for i in range(3,7))},
 'GND_BMS_RAW':{*(('C'+str(i),'2') for i in range(910,916)),('R906','2'),('R909','2'),('R911','2'),('U902','2'),*(('U901',str(i)) for i in range(9,13))},
 'EPS_BMS_PRI_EN':{('U100','29'),('R903','1')},
 'EPS_BMS_PRI_FAULT_N':{('U100','26'),('R908','2')},
 '3V3_BMS_PRI_SW':{('U900','6'),('R901','1')},
 '3V3_BMS_PRI':{('R901','2'),('R904','1'),('R910','1'),('U901','2'),*(('C'+str(i),'1') for i in range(901,910))},
 '5V0_BMS_ISO':{('U901','7'),('U901','8'),('R909','1'),('U902','1'),('U902','3'),*(('C'+str(i),'1') for i in range(910,915))},
 '3V3_BMS_ISO':migrated|{('U902','5'),('R905','1'),('R911','1'),('C915','1')},
 '/Isolated BMS supply/BMS_PRI_EN':{('U900','3'),('R902','2'),('R903','2')},
 '/Isolated BMS supply/BMS_PRI_FAULT_N':{('U900','4'),('R907','2'),('R908','1')},
 '/Isolated BMS supply/BMS_PRI_ILIM':{('U900','5'),('R900','1')},
 '/Isolated BMS supply/BMS_MODULE_EN_FLT':{('U901','1'),('R904','2')},
 '/Isolated BMS supply/BMS_ISO_ADJ':{('U902','4'),('R905','2'),('R906','1')},
}
for k,v in add.items():expected.setdefault(k,set()).update(v)
assert nn==expected,{k:[sorted(expected.get(k,set())),sorted(nn.get(k,set()))] for k in set(expected)|set(nn) if expected.get(k)!=nn.get(k)}
assert sum(map(len,nn.values()))==754
assert len([n for n in nn if not n.startswith('unconnected-')])==132
assert len([p for v in nn.values() for p in v if p[0] in newrefs])==81
fields=json.loads((H/'expected_component_fields.json').read_text());assert len(fields)==32
api=json.loads((H/'metadata_api_readback.json').read_text())
assert len(api)==len({c['reference'] for c in api})==32
api={c['reference']:c for c in api}
for e in fields:
 m=meta(new[e['reference']]);assert m['value']==e['value'] and m['footprint']==e['footprint']
 assert api[e['reference']]['uuid']==m['tstamps']
 for k,v in e['fields'].items():
  assert m['fields'][k]==v,(e['reference'],k)
  assert api[e['reference']]['fields'][k]==v,(e['reference'],k,'API')
baseline=json.loads((H/'baseline.json').read_text())
assert subprocess.check_output(['git','rev-parse',baseline['commit']],cwd=ROOT,text=True).strip()==BASE
for p,h in baseline['frozen'].items():
 assert sha(ROOT/p)==h,p
 assert hashlib.sha256(subprocess.check_output(['git','show',BASE+':'+p],cwd=ROOT)).hexdigest()==h,p
allowed=set(baseline['initial']);added={'hardware/eps/rev_b/bms_isolated_power.kicad_sch'}
assert all(sha(ROOT/p)!=h for p,h in baseline['initial'].items())
protected=lambda p:p.endswith(('.kicad_sch','.kicad_pro','.kicad_pcb','.kicad_sym','.kicad_mod','sym-lib-table','fp-lib-table'))
delta={}
for line in subprocess.check_output(['git','diff','--name-status',BASE,'--','hardware/eps'],cwd=ROOT,text=True).splitlines():
 status,p=line.split('\t')
 if protected(p):delta[p]=status
for p in subprocess.check_output(['git','ls-files','--others','--exclude-standard','hardware/eps'],cwd=ROOT,text=True).splitlines():
 if protected(p):delta[p]='A'
assert delta=={**{p:'M' for p in allowed},**{p:'A' for p in added}},delta
manifest=json.loads((H/'native_source_sha256.json').read_text());assert set(manifest)==allowed|added
for p,h in manifest.items():assert sha(ROOT/p)==h,p
cli=json.loads((H/'cli_checks.json').read_text())
for p,h in cli['hierarchy_source_sha256'].items():assert sha(ROOT/p)==h,p
oldsyms={};current={};crosswalk=[];refunits=[]
for path in sorted(P.glob('*.kicad_sch')):
 d=parse(path.read_text());assert one(d,'paper')[1]=='B'
 if path.name!='bms_isolated_power.kicad_sch':
  b=parse(subprocess.check_output(['git','show',BASE+':'+str(path.relative_to(ROOT))],cwd=ROOT,text=True))
  for s in kids(b,'symbol'):oldsyms[one(s,'uuid')[1]]=s
 for s in kids(d,'symbol'):
  u=one(s,'uuid')[1];pr=props(s);r=pr['Reference'];unit=int(one(s,'unit')[1])
  assert u not in current;current[u]=s;refunits.append((r,unit))
  refs=[x[1] for t in kids(s,'instances') for x in descend(t,'reference')]
  assert refs and all(v==r for v in refs) and '?' not in r
  crosswalk.append({'reference':r,'unit':unit,'uuid':u,'sheet':path.name,'baseline_retained':u in oldsyms})
assert len(current)==len(refunits)==len(set(refunits))==524 and len(oldsyms)==472
exceptions={}
for u,s in oldsyms.items():
 r=props(s)['Reference'];now=current[u]
 if r in ['#PWR0223','#PWR0228','#PWR0229']:
  a=copy.deepcopy(s);p=next(p for p in kids(a,'property') if p[1]=='Value');p[2]='3V3_BMS_ISO'
  assert now==a;exceptions[r]='Value +3V3→3V3_BMS_ISO; UUID/other content preserved'
 elif r=='#PWR0103':
  a=copy.deepcopy(s);one(a,'at')[2]='82.55'
  for p in kids(a,'property'):one(p,'at')[2]=str(round(float(one(p,'at')[2])-2.54,4))
  assert now==a
  exceptions[r]='Ground symbol/stub shortened 2.54mm for FAULT glyph clearance; UUID/metadata preserved'
 else:assert now==s,r
assert {r for r,u in refunits if r.startswith('#') and r in ['#FLG0900',*[f'#PWR09{i:02d}' for i in range(19)]]}=={'#FLG0900',*[f'#PWR09{i:02d}' for i in range(19)]}
proj=json.loads((P/'eps_rev_b.kicad_pro').read_text());bp=json.loads(subprocess.check_output(['git','show',BASE+':hardware/eps/rev_b/eps_rev_b.kicad_pro'],cwd=ROOT))
assert {k:v for k,v in proj.items() if k!='net_settings'}=={k:v for k,v in bp.items() if k!='net_settings'}
assert proj['net_settings']['classes']==bp['net_settings']['classes']
patterns=proj['net_settings']['netclass_patterns'];oldpatterns=bp['net_settings']['netclass_patterns']
assert all(p in patterns for p in oldpatterns) and len(patterns)==len(oldpatterns)+11
classmap={n:('POWER' if n in ['3V3_BMS_PRI_SW','3V3_BMS_PRI','5V0_BMS_ISO','3V3_BMS_ISO'] else 'ANALOG_CONTROL' if n.endswith(('BMS_PRI_ILIM','BMS_ISO_ADJ')) else 'CONTROL') for n in add if n not in on}
assert len(classmap)==11
members={n:[p['netclass'] for p in patterns if fnmatch.fnmatchcase(n,p['pattern'])] for n in nn if not n.startswith('unconnected-')}
assert all(len(v)==1 for v in members.values())
for n,c in classmap.items():assert members[n]==[c]
orphans=[p for p in patterns if not any(fnmatch.fnmatchcase(n,p['pattern']) for n in nn)]
assert {p['pattern'] for p in orphans}=={'/Controller/REC5_RESET','/Controller/REC5_FAULT','/Controller/SRC_FAULT'}
rb=json.loads((H/'readback.json').read_text());cu=json.loads((H/'controller_updated_readback.json').read_text())
rb['pins']['controller']=cu['pins'];rb['layout']['controller']=cu['layout'];rb['components']['controller']=cu['components']
iu=json.loads((H/'isolated_updated_readback.json').read_text())
rb['pins']['bms_isolated_power']=iu['pins'];rb['layout']['bms_isolated_power']=iu['layout'];rb['components']['bms_isolated_power']=iu['components']
pinmaps={c['reference']:{p['number']:p['name'] for p in c['pins']} for c in iu['pins']['components'] if c['reference'].startswith('U')}
assert pinmaps=={
 'U900':{'1':'IN','2':'GND','3':'EN','4':'~{FAULT}','5':'ILIM','6':'OUT'},
 'U901':{'1':'EN/FLT','2':'VINP',**{str(i):'GNDP' for i in range(3,7)},'7':'SEL','8':'VCC',**{str(i):'GNDS' for i in range(9,13)}},
 'U902':{'1':'VIN','2':'GND','3':'~{SHDN}','4':'ADJ','5':'VOUT'}}
assert sum(len(c['pins']) for c in iu['pins']['components'] if c['reference'] in newrefs)==81
newdoc=parse((P/'bms_isolated_power.kicad_sch').read_text())
maps={
 'Ember_Charger_BMS_Review:TPS2553DBVR_1_REVIEW':{'1':('IN','power_in'),'2':('GND','power_in'),'3':('EN','input'),'4':('~{FAULT}','open_collector'),'5':('ILIM','output'),'6':('OUT','power_out')},
 'Ember_Charger_BMS_Review:UCC33020RAQR_REVIEW':{'1':('EN/FLT','bidirectional'),'2':('VINP','power_in'),**{str(i):('GNDP','power_in') for i in range(3,7)},'7':('SEL','input'),'8':('VCC','power_out'),**{str(i):('GNDS','power_in') for i in range(9,13)}},
 'Regulator_Linear:LT3014xS5':{'1':('VIN','power_in'),'2':('GND','power_in'),'3':('~{SHDN}','input'),'4':('ADJ','input'),'5':('VOUT','power_out')}}
rows=[]
for lib in kids(one(newdoc,'lib_symbols'),'symbol'):
 if lib[1] not in maps:continue
 ps=descend(lib,'pin');nums=[one(p,'number')[1] for p in ps]
 assert len(nums)==len(set(nums))==len(maps[lib[1]])
 assert {one(p,'number')[1]:(one(p,'name')[1],p[1]) for p in ps}==maps[lib[1]]
 ref={'Ember_Charger_BMS_Review:TPS2553DBVR_1_REVIEW':'U900','Ember_Charger_BMS_Review:UCC33020RAQR_REVIEW':'U901','Regulator_Linear:LT3014xS5':'U902'}[lib[1]]
 for p in ps:
  num=one(p,'number')[1];net=next(n for n,v in nn.items() if (ref,num) in v)
  rows.append({'reference':ref,'pin':num,'name':one(p,'name')[1],'electrical_type':p[1],'net':net,'footprint':new[ref].findtext('footprint')})
assert len(rows)==23
with (H/'package_pin_map.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=rows[0],lineterminator='\n');w.writeheader();w.writerows(rows)
def dirs(p,w):
 x,y=p;a,b,c,d=[round(w[k],4) for k in ['x1','y1','x2','y2']];out=set()
 if b==d==y and min(a,c)<=x<=max(a,c):
  if x>min(a,c):out.add('L')
  if x<max(a,c):out.add('R')
 if a==c==x and min(b,d)<=y<=max(b,d):
  if y>min(b,d):out.add('U')
  if y<max(b,d):out.add('D')
 return out
geometry={}
for name,d in rb['layout'].items():
 wires=d['wires'];ends=set();points=set();segs=[]
 for w in wires:
  assert w['x1']==w['x2'] or w['y1']==w['y2']
  assert all(abs(w[k]/1.27-round(w[k]/1.27))<1e-5 for k in ['x1','y1','x2','y2'])
  a=round(w['x1'],4),round(w['y1'],4);b=round(w['x2'],4),round(w['y2'],4);assert a!=b
  ends.update([a,b]);points.update([a,b]);segs.append(tuple(sorted([a,b])))
 assert len(segs)==len(set(segs))
 for a in wires:
  for b in wires:
   p=round(a['x1'],4),round(b['y1'],4)
   if a['x1']==a['x2'] and b['y1']==b['y2'] and min(a['y1'],a['y2'])<=p[1]<=max(a['y1'],a['y2']) and min(b['x1'],b['x2'])<=p[0]<=max(b['x1'],b['x2']):points.add(p)
 doc=parse((P/(name+'.kicad_sch')).read_text())
 placed={(props(s)['Reference'],int(one(s,'unit')[1])):one(s,'at') for s in kids(doc,'symbol')}
 queried=set()
 for c in rb['pins'][name]['components']:
  for unit in c['units']:
   key=(c['reference'],unit['unit']);queried.add(key)
   at=placed[key]
   assert abs(float(at[1])-unit['x'])<1e-5 and abs(float(at[2])-unit['y'])<1e-5
   assert abs(float(at[3])-unit['rotation'])<1e-5
 assert queried==set(placed),name
 native_segments=[tuple(sorted([tuple(map(float,p[1][1:])),tuple(map(float,p[2][1:]))])) for w in kids(doc,'wire') for p in [one(w,'pts')]]
 assert Counter(native_segments)==Counter(segs),name
 native_labels={(l[1],float(one(l,'at')[1]),float(one(l,'at')[2])) for typ in ['label','global_label','hierarchical_label'] for l in kids(doc,typ)}
 assert native_labels=={(l['net'],l['x'],l['y']) for l in d['labels']},name
 junctions={tuple(map(float,one(j,'at')[1:3])) for j in kids(doc,'junction')}
 four={p for p in points if len(set().union(*(dirs(p,w) for w in wires)))==4}
 assert not four&(ends|junctions),(name,four&(ends|junctions))
 assert not any((round(l['x'],4),round(l['y'],4)) in four for l in d['labels'])
 count=0
 for c in rb['pins'][name]['components']:
  for pin in c['pins']:
   p=round(pin['x'],4),round(pin['y'],4)
   assert all(abs(v/1.27-round(v/1.27))<1e-5 for v in p)
   assert len(set().union(*(dirs(p,w) for w in wires)))<3,(name,c['reference'],pin)
   count+=1
 geometry[name]={'segments':len(wires),'connected_fourways':0,'unconnected_crossings':sorted(four),'queried_pin_anchors_including_power_flags':count,'pin_branch_anchors':0}
erc=json.loads((H/'erc.json').read_text());viol=[{'sheet':s['path'],**v} for s in erc['sheets'] for v in s['violations']]
assert Counter((v['severity'],v['type']) for v in viol)=={('error','pin_not_connected'):7,('error','pin_to_pin'):3}
nc={v['items'][0]['description'].split(' Pin ')[1].split(' ')[0] for v in viol if v['type']=='pin_not_connected'}
assert nc=={'7','8','11','12','17','28','32'}
assert len(PdfReader(H/'eps_rev_b.pdf').pages)==11
visual=json.loads((H/'visual_review.json').read_text())
assert len(visual['full_pages'])==11 and len(visual['details'])==6
assert visual['hierarchy_source_sha256']==cli['hierarchy_source_sha256']
for n,h in visual['full_pages'].items()|visual['details'].items():assert sha(H/n)==h,n
assert len(rb['tree']['children'])==10 and [c['page'] for c in rb['tree']['children']]==[str(i) for i in range(2,12)]
for n in rb['layout']:assert (H/(n+'.png')).exists()
save('reference_UUID_crosswalk.json',crosswalk);save('symbol_exceptions.json',exceptions)
save('fields_readback.json',{r:meta(new[r]) for r in sorted(newrefs)})
save('class_membership.json',{'actual':members,'orphan_patterns':orphans})
save('geometry.json',geometry);save('erc_classified.json',viol)
with (H/'endpoint_contract.csv').open('w') as f:
 rows=[{'reference':r,'pin':p,'net':n,'whole_net_endpoints':';'.join(a+'.'+b for a,b in sorted(nn[n]))} for n in add for r,p in sorted(add[n]) if r in newrefs or (r,p) in migrated|consumed]
 w=csv.DictWriter(f,fieldnames=rows[0],lineterminator='\n');w.writeheader();w.writerows(rows)
result={'basis':BASE,'status':'DEVELOPMENT CONNECTIVITY / PRESERVATION PASS; ELECTRICAL/PVT/PCB QUALIFICATION OPEN','parts':275,'nets':146,'functional_nets':132,'physical_pin_endpoints':754,'old_physical_parts_preserved':243,'old_symbol_objects_retained':472,'current_symbol_objects':524,'added_parts':32,'frozen_tracked_files':len(baseline['frozen']),'ERC_errors':10,'ERC_warnings':0,'protected_delta':dict(sorted(delta.items())),'symbol_exceptions':exceptions,'geometry':geometry}
save('verified.json',result);print(json.dumps(result,indent=2))
