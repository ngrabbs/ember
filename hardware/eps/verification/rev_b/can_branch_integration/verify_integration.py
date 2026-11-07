#!/usr/bin/env python3
"""Exact development graph delta, saved native identities, source and geometry gates."""
from common import *
from collections import Counter
import copy,csv,fnmatch,hashlib,subprocess,xml.etree.ElementTree as E
from pypdf import PdfReader
P=ROOT/'hardware/eps/rev_b'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,v):(H/n).write_text(json.dumps(v,indent=2)+'\n')
def graph(path):
 d=E.parse(path).getroot();cs=d.findall('components/comp');ns=d.findall('nets/net')
 assert len(cs)==len({c.get('ref') for c in cs})
 assert len(ns)==len({n.get('name') for n in ns})
 ep=[(p.get('ref'),p.get('pin')) for n in ns for p in n.findall('node')]
 assert len(ep)==len(set(ep))
 return {c.get('ref'):c for c in cs},{n.get('name'):{(p.get('ref'),p.get('pin')) for p in n.findall('node')} for n in ns}
def meta(c):return {k:c.findtext(k) or '' for k in ['value','footprint','datasheet','tstamps']}|{'libsource':c.find('libsource').attrib,'fields':{x.get('name'):x.text or '' for x in c.findall('fields/field')}}
def descend(n,k):
 out=[]
 for x in n:
  if isinstance(x,list):
   if x and x[0]==k:out.append(x)
   out.extend(descend(x,k))
 return out
old,on=graph(H/'before.xml');new,nn=graph(H/'eps_rev_b.xml')
prior,pn=graph(H.parent/'isolated_bms_integration/eps_rev_b.xml')
assert on==pn and {r:meta(c) for r,c in old.items()}=={r:meta(c) for r,c in prior.items()}
assert (len(old),len(on),len(new),len(nn))==(275,146,305,166)
for r,c in old.items():assert meta(c)==meta(new[r]),r
newrefs={*[f'U{i}' for i in range(1100,1104)],*[f'R{i}' for i in range(1100,1120)],*[f'C{i}' for i in range(1100,1104)],'TP1100','TP1101'}
assert set(new)-set(old)==newrefs
expected={k:set(v) for k,v in on.items()};add={}
def plus(n,p):expected.setdefault(n,set()).update(p);add.setdefault(n,set()).update(p)
for ch,u,t,r,c,tp in [('A',101,1100,1100,1100,1100),('B',102,1102,1110,1102,1101)]:
 R=lambda i:f'R{r+i}';U=f'U{t}';I=f'U{t+1}';C=lambda i:f'C{c+i}'
 migrated={(f'U{u}','3'),(f'U{u}','5'),*(('C'+str(k),'1') for k in (range(104,107) if ch=='A' else range(107,110)))}
 assert migrated<=expected['+3V3'];expected['+3V3']-=migrated
 plus('+3V3',{(U,'1'),(I,'5'),(C(0),'1'),(C(1),'1'),(R(8),'1'),(R(3),'1')})
 plus('GND',{(U,'2'),(I,'3'),(C(0),'2'),(C(1),'2'),(R(4),'2'),(R(7),'2'),(R(9),'2')})
 for suffix,pin,i in [('TX','1',0),('RX','4',1),('STB','8',2)]:
  name=f'EPS_CAN_{ch}_{suffix}';assert (f'U{u}',pin) in expected[name];expected[name].remove((f'U{u}',pin))
  p={(R(i),'1')}
  if suffix=='RX':p.add((R(3),'2'))
  if suffix=='STB':p.add((I,'2'))
  plus(name,p)
  plus(f'/CAN interfaces/CAN{ch}_{"TXD" if suffix=="TX" else "RXD" if suffix=="RX" else "STB"}',{(f'U{u}',pin),(R(i),'2')})
 plus(f'3V3_CAN{ch}',migrated|{(R(5),'2'),(R(9),'1')})
 plus(f'3V3_CAN{ch}_SW',{(U,'6'),(R(5),'1')})
 for tail,p in [('EN',{(U,'3'),(R(6),'2'),(R(7),'1')}),('EN_DRV',{(I,'4'),(R(6),'1')}),('ILIM',{(U,'5'),(R(4),'1')}),('FAULT_N',{(U,'4'),(R(8),'2'),(f'TP{tp}','1')})]:plus(f'/CAN Branch Power/CAN{ch}_{tail}',p)
 nc=next(n for n,v in nn.items() if v=={(I,'1')});assert nc.startswith('unconnected-');plus(nc,{(I,'1')})
assert nn==expected,{n:[sorted(expected.get(n,set())),sorted(nn.get(n,set()))] for n in set(nn)|set(expected) if expected.get(n)!=nn.get(n)}
assert sum(map(len,nn.values()))==826
assert sum(not n.startswith('unconnected-') for n in nn)==150
assert sum(r in newrefs for v in nn.values() for r,p in v)==72
fields=json.loads((H/'expected_component_fields.json').read_text());assert len(fields)==30
for e in fields:
 m=meta(new[e['reference']]);assert m['value']==e['value'] and m['footprint']==e['footprint'] and m['datasheet']==e['datasheet']
 for k,v in e['fields'].items():assert m['fields'][k]==v,(e['reference'],k)
b=json.loads((H/'baseline.json').read_text());BASE=b['basis'];allowed=set(b['initial']);added={'hardware/eps/rev_b/can_branch_power.kicad_sch'}
frozen={}
for category in ['frozen_protected','frozen_history','progress','frozen_package','frozen_checkpoint']:
 for p,h in b[category].items():
  assert portable(p),(category,p)
  assert sha(ROOT/p)==h,(category,p);frozen[p]=h
protected=lambda p:p.endswith(('.kicad_sch','.kicad_pro','.kicad_pcb','.kicad_sym','.kicad_mod','sym-lib-table','fp-lib-table'))
delta={}
for line in subprocess.check_output(['git','diff','--name-status',BASE,'--','hardware'],cwd=ROOT,text=True).splitlines():
 st,p=line.split('\t')
 if protected(p):delta[p]=st
for p in subprocess.check_output(['git','ls-files','--others','--exclude-standard','hardware'],cwd=ROOT,text=True).splitlines():
 if protected(p) and p not in b['frozen_package']:delta[p]='A'
fixture={'hardware/eps/verification/controller_rev_b/can_branch_parts/disposable/can_branch_parts_check'+x for x in ['.kicad_pro','.kicad_sch','.kicad_pcb']}
delta={p:s for p,s in delta.items() if p not in fixture}
assert delta=={**{p:'M' for p in allowed},**{p:'A' for p in added}},delta
manifest=json.loads((H/'native_source_sha256.json').read_text());assert set(manifest)==allowed|added
cli=json.loads((H/'cli_checks.json').read_text())
for p,h in (manifest|cli['hierarchy_source_sha256']).items():assert sha(ROOT/p)==h,p
oldsyms={};current={};cross=[];refunits=[]
for path in sorted(P.glob('*.kicad_sch')):
 d=parse(path.read_text());assert one(d,'paper')[1]=='B'
 if path.name!='can_branch_power.kicad_sch':
  before=parse(subprocess.check_output(['git','show',BASE+':'+str(path.relative_to(ROOT))],cwd=ROOT,text=True))
  for s in kids(before,'symbol'):oldsyms[one(s,'uuid')[1]]=s
 for s in kids(d,'symbol'):
  u=one(s,'uuid')[1];r=props(s)['Reference'];unit=int(one(s,'unit')[1]);assert u not in current
  current[u]=s;refunits.append((r,unit));assert '?' not in r
  refs=[x[1] for t in kids(s,'instances') for x in descend(t,'reference')];assert refs and set(refs)=={r}
  cross.append({'reference':r,'unit':unit,'uuid':u,'sheet':path.name,'baseline_retained':u in oldsyms})
assert len(current)==len(refunits)==len(set(refunits))==582 and len(oldsyms)==524
root_before=parse(subprocess.check_output(['git','show',BASE+':hardware/eps/rev_b/eps_rev_b.kicad_sch'],cwd=ROOT,text=True))
root_now=parse((P/'eps_rev_b.kicad_sch').read_text())
for sheet in kids(root_before,'sheet'):assert sheet in kids(root_now,'sheet')
exceptions={'#PWR0112':'3V3_CANA','#PWR0117':'3V3_CANB'}
for u,s in oldsyms.items():
 a=copy.deepcopy(s);r=props(s)['Reference']
 if r in exceptions:next(p for p in kids(a,'property') if p[1]=='Value')[2]=exceptions[r]
 assert current[u]==a,r
proj=json.loads((P/'eps_rev_b.kicad_pro').read_text());bp=json.loads(subprocess.check_output(['git','show',BASE+':hardware/eps/rev_b/eps_rev_b.kicad_pro'],cwd=ROOT))
assert {k:v for k,v in proj.items() if k!='net_settings'}=={k:v for k,v in bp.items() if k!='net_settings'}
assert proj['net_settings']['classes']==bp['net_settings']['classes']
patterns=proj['net_settings']['netclass_patterns'];op=bp['net_settings']['netclass_patterns'];assert all(p in patterns for p in op) and len(patterns)==len(op)+18
members={n:[p['netclass'] for p in patterns if fnmatch.fnmatchcase(n,p['pattern'])] for n in nn if not n.startswith('unconnected-')}
assert all(len(v)==1 for v in members.values())
for n in set(nn)-set(on):
 if n.startswith('unconnected-'):continue
 cls='POWER' if n.startswith('3V3_CAN') else 'CAN_LOGIC' if n.startswith('/CAN interfaces/') else 'ANALOG_CONTROL' if n.endswith('_ILIM') else 'CONTROL'
 assert members[n]==[cls],(n,members[n])
orphans=[p for p in patterns if not any(fnmatch.fnmatchcase(n,p['pattern']) for n in nn)]
assert {p['pattern'] for p in orphans}=={'/Controller/REC5_RESET','/Controller/REC5_FAULT','/Controller/SRC_FAULT'}
rb=json.loads((H/'readback.json').read_text())
doc=parse((P/'can_branch_power.kicad_sch').read_text())
maps={
 'Ember_Charger_BMS_Review:TPS2553DBVR_1_REVIEW':{'1':('IN','power_in'),'2':('GND','power_in'),'3':('EN','input'),'4':('~{FAULT}','open_collector'),'5':('ILIM','output'),'6':('OUT','power_out')},
 '74xGxx:SN74LVC1G14DBV':{'1':('NC','no_connect'),'2':('','input'),'3':('GND','power_in'),'4':('','output'),'5':('VCC','power_in')}}
rows=[]
for lib in kids(one(doc,'lib_symbols'),'symbol'):
 if lib[1] not in maps:continue
 pins=descend(lib,'pin');nums=[one(p,'number')[1] for p in pins]
 assert len(nums)==len(set(nums))==len(maps[lib[1]])
 got={one(p,'number')[1]:(one(p,'name')[1],p[1]) for p in pins};assert got==maps[lib[1]],got
 refs=['U1100','U1102'] if 'TPS2553' in lib[1] else ['U1101','U1103']
 for ref in refs:
  query=next(c for c in rb['pins']['can_branch_power']['components'] if c['reference']==ref)
  assert len(query['pins'])==len(set(p['number'] for p in query['pins']))==len(pins)
  assert {p['number']:p['name'] for p in query['pins']}=={n:v[0] for n,v in maps[lib[1]].items()}
  for pin in pins:
   num=one(pin,'number')[1];net=next(n for n,v in nn.items() if (ref,num) in v)
   rows.append({'reference':ref,'pin':num,'name':one(pin,'name')[1],'electrical_type':pin[1],'net':net,'footprint':new[ref].findtext('footprint')})
assert len(rows)==22
assert sum(len(c['pins']) for name in ['can_interfaces','can_branch_power'] for c in rb['pins'][name]['components'] if c['reference'] in newrefs)==72
with (H/'package_pin_map.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=rows[0],lineterminator='\n');w.writeheader();w.writerows(rows)
exec((H/'geometry_check.py').read_text())
erc=json.loads((H/'erc.json').read_text());viol=[{'sheet':s['path'],**v} for s in erc['sheets'] for v in s['violations']]
assert Counter((v['severity'],v['type']) for v in viol)=={('error','pin_not_connected'):7,('error','pin_to_pin'):3}
def erc_signature(d):
 return sorted((s['path'],v['severity'],v['type'],v['description'],tuple(sorted(i['description'] for i in v['items']))) for s in d['sheets'] for v in s['violations'])
assert erc_signature(erc)==erc_signature(json.loads((H.parent/'isolated_bms_integration/erc.json').read_text()))
assert len(PdfReader(H/'eps_rev_b.pdf').pages)==12
assert len(rb['tree']['children'])==11 and [c['page'] for c in rb['tree']['children']]==[str(i) for i in range(2,13)]
visual=json.loads((H/'visual_review.json').read_text())
assert visual['hierarchy_source_sha256']==cli['hierarchy_source_sha256']
assert len(visual['full_pages'])==12 and len(visual['details'])==14
for n,h in (visual['full_pages']|visual['details']).items():assert sha(H/n)==h,n
save('geometry.json',geometry);save('reference_UUID_crosswalk.json',cross);save('class_membership.json',{'actual':members,'orphans':orphans});save('fields_readback.json',{r:meta(new[r]) for r in sorted(newrefs)});save('erc_classified.json',viol)
with (H/'endpoint_contract.csv').open('w') as f:
 rows=[{'reference':r,'pin':p,'net':n,'whole_net_endpoints':';'.join(a+'.'+z for a,z in sorted(nn[n]))} for n in add for r,p in sorted(nn[n])]
 w=csv.DictWriter(f,fieldnames=rows[0],lineterminator='\n');w.writeheader();w.writerows(rows)
result={'basis':BASE,'status':'DEVELOPMENT GRAPH / PRESERVATION PASS; ELECTRICAL/PVT/PCB QUALIFICATION OPEN','parts':305,'nets':166,'functional_nets':150,'physical_endpoints':826,'added_parts':30,'old_physical_parts_preserved':275,'old_symbol_objects_retained':524,'current_symbol_objects':582,'frozen_unique_files':len(frozen),'ERC_errors':10,'ERC_warnings':0,'protected_delta':dict(sorted(delta.items())),'symbol_value_exceptions':exceptions,'geometry':geometry}
save('verified.json',result);print(json.dumps(result,indent=2))
