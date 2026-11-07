#!/usr/bin/env python3
from common import *
from collections import Counter
import copy,csv,fnmatch,hashlib,subprocess,xml.etree.ElementTree as E
from pypdf import PdfReader
P=ROOT/'hardware/eps/rev_b'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,v):(H/n).write_text(json.dumps(v,indent=2)+'\n')
def graph(p):
 d=E.parse(p).getroot();cs=d.findall('components/comp');ns=d.findall('nets/net')
 assert len(cs)==len({c.get('ref') for c in cs});assert len(ns)==len({n.get('name') for n in ns})
 pins=[(p.get('ref'),p.get('pin')) for n in ns for p in n.findall('node')];assert len(pins)==len(set(pins))
 return {c.get('ref'):c for c in cs},{n.get('name'):{(p.get('ref'),p.get('pin')) for p in n.findall('node')} for n in ns}
def meta(c):return {k:c.findtext(k) or '' for k in ['value','footprint','datasheet','tstamps']}|{'libsource':c.find('libsource').attrib,'fields':{f.get('name'):f.text or '' for f in c.findall('fields/field')}}
def descend(n,k):
 out=[]
 for x in n:
  if isinstance(x,list):
   if x and x[0]==k:out.append(x)
   out+=descend(x,k)
 return out
old,on=graph(H/'before.xml');new,nn=graph(H/'eps_rev_b.xml')
assert (len(old),len(on),len(new),len(nn))==(318,175,345,186)
for r,c in old.items():assert meta(c)==meta(new[r]),r
added={*[f'R{i}' for i in range(1300,1319)],*[f'C{i}' for i in range(1300,1306)],'U1300','U1301'};assert set(new)-set(old)==added
expected={n:set(v) for n,v in on.items()}
def plus(n,v):expected.setdefault(n,set()).update(v)
channels=[('SYS','SYS_PWR_PERMITTED','7','ANA_EPS_SYS',[1300,1301],1302,1303,1304,1300,'2','3'),('5V0','+5V','8','ANA_EPS_5V0',[1305],1306,1307,1308,1301,'5','6'),('3V3','+3V3','11','ANA_EPS_3V3',[1309],1310,1311,1312,1302,'9','8'),('BATT','BATT_PERMITTED','12','ANA_EPS_BATT',[1313,1314],1315,1316,1317,1303,'12','11')]
for tail,rail,mcupin,glob,top,bottom,series,bleed,cap,sp,dp in channels:
 singleton=next(n for n,v in expected.items() if v=={('U100',mcupin)});assert singleton.startswith('unconnected-');expected.pop(singleton)
 plus(rail,{('R'+str(top[0]),'1')})
 if len(top)==2:plus('Net-(R'+str(top[0])+'-Pad2)',{('R'+str(top[0]),'2'),('R'+str(top[1]),'1')})
 plus('/Rail Telemetry/'+tail+'_DIV',{('R'+str(top[-1]),'2'),('R'+str(bottom),'1'),('C'+str(cap),'1'),('U1300',sp)})
 plus('/Rail Telemetry/'+tail+'_SW',{('U1300',dp),('R'+str(series),'1')})
 plus(glob,{('U100',mcupin),('R'+str(series),'2'),('R'+str(bleed),'1')})
 plus('GND',{('R'+str(bottom),'2'),('R'+str(bleed),'2'),('C'+str(cap),'2')})
plus('+3V3',{('U1300','14'),('U1301','3'),('C1304','1'),('C1305','1')})
plus('GND',{('U1300','7'),('U1301','1'),('R1318','2'),('C1304','2'),('C1305','2')})
plus('/Rail Telemetry/ADC_SUPPLY_OK',{('U1300',p) for p in ['1','4','10','13']}|{('U1301','2'),('R1318','1')})
assert nn==expected,{n:[sorted(expected.get(n,set())),sorted(nn.get(n,set()))] for n in set(expected)|set(nn) if expected.get(n)!=nn.get(n)}
assert sum(map(len,nn.values()))==933 and sum(not n.startswith('unconnected-') for n in nn)==173
fields=json.loads((H/'expected_component_fields.json').read_text());assert set(fields)==added
for r,fs in fields.items():
 m=meta(new[r])
 for k,v in fs.items():assert m['fields'][k]==v,(r,k)
 fp='Resistor_SMD:R_0603_1608Metric' if r.startswith('R') else 'Capacitor_SMD:C_0603_1608Metric' if r.startswith('C') else 'Package_SO:TSSOP-14_4.4x5mm_P0.65mm' if r=='U1300' else 'Package_TO_SOT_SMD:SOT-23'
 assert m['footprint']==fp and m['datasheet']
 if r.startswith('R'):
  pn={'100k':'TNPW0603100KBEEA','20k':'TNPW060320K0BEEA','10k':'TNPW060310K0BEEA','1k':'TNPW06031K00BEEA','47k':'TNPW060347K0BEEA'}[m['value']];assert m['fields']['MFG P/N']==pn
 if r.startswith('C'):assert m['value']==('10nF' if int(r[1:])<1304 else '100nF')
 if r.startswith('U'):assert m['value']==m['fields']['MFG P/N']
baseline=json.loads((H/'baseline.json').read_text());allowed=set(baseline['initial']);extra={'hardware/eps/rev_b/rail_telemetry.kicad_sch'}
for p,h in baseline['frozen'].items():assert portable(p) and sha(ROOT/p)==h,p
progress=['hardware/eps/verification/rev_b/bms_integration/'+x for x in ['bms_progress.png','controller_progress.png','erc_progress.json','progress.xml']]+['hardware/eps/verification/rev_b/uart_integration/progress_cli.json'];assert set(progress)<=set(baseline['frozen'])
protected=lambda p:p.endswith(('.kicad_sch','.kicad_pro','.kicad_pcb','.kicad_sym','.kicad_mod')) or Path(p).name in {'sym-lib-table','fp-lib-table'}
delta={}
for line in subprocess.check_output(['git','diff','--name-status',baseline['basis'],'--','hardware'],cwd=ROOT,text=True).splitlines():
 st,p=line.split('\t')
 if protected(p) and p not in baseline['frozen']:delta[p]=st
for p in subprocess.check_output(['git','ls-files','--others','--exclude-standard','hardware'],cwd=ROOT,text=True).splitlines():
 if protected(p) and p not in baseline['frozen']:delta[p]='A'
assert delta=={**{p:'M' for p in allowed},**{p:'A' for p in extra}},delta
manifest=json.loads((H/'native_source_sha256.json').read_text());assert set(manifest)==allowed|extra
cli=json.loads((H/'cli_checks.json').read_text())
for p,h in (manifest|cli['hierarchy_source_sha256']).items():assert sha(ROOT/p)==h,p
oldsyms={};now={};refs=[];cross=[];oldnotes={};newnotes={}
for path in sorted(P.glob('*.kicad_sch')):
 d=parse(path.read_text());assert one(d,'paper')[1]=='B'
 if path.name!='rail_telemetry.kicad_sch':
  src=(H/(path.stem+'_before.txt')).read_text() if path.stem in ['controller','eps_rev_b'] else path.read_text()
  prior=parse(src)
  for s in kids(prior,'symbol'):
   u=one(s,'uuid')[1];assert u not in oldsyms;oldsyms[u]=s
  if path.stem=='controller':oldnotes={one(t,'uuid')[1]:t for t in kids(prior,'text')}
 for s in kids(d,'symbol'):
  u=one(s,'uuid')[1];r=props(s)['Reference'];unit=int(one(s,'unit')[1]);assert u not in now;now[u]=s;refs.append((r,unit));assert '?' not in r
  ann=[a[1] for t in kids(s,'instances') for a in descend(t,'reference')];assert ann and set(ann)=={r}
  cross.append({'reference':r,'unit':unit,'UUID':u,'sheet':path.name,'old_UUID':u in oldsyms})
 if path.stem=='controller':newnotes={one(t,'uuid')[1]:t for t in kids(d,'text')}
assert len(refs)==len(set(refs));assert len(oldsyms)==616
for u,s in oldsyms.items():assert now[u]==s,props(s)['Reference']
removednotes=set(oldnotes)-set(newnotes);assert removednotes=={'4aa06701-614f-462e-8ddc-d3a240e8fe64','42ebef24-6b60-41a7-b637-ea041fdf8255'}
for u,n in oldnotes.items():
 if u not in removednotes:assert newnotes[u]==n
assert len(set(newnotes)-set(oldnotes))==2
root=parse((P/'eps_rev_b.kicad_sch').read_text());priorroot=parse((H/'eps_rev_b_before.txt').read_text());assert len(kids(root,'sheet'))==13
for s in kids(priorroot,'sheet'):assert s in kids(root,'sheet')
for typ in ['text','wire','label','global_label','junction','no_connect']:assert kids(priorroot,typ)==kids(root,typ)
proj=json.loads((P/'eps_rev_b.kicad_pro').read_text());bp=json.loads((H/'project_before.json').read_text())
assert {k:v for k,v in proj.items() if k!='net_settings'}=={k:v for k,v in bp.items() if k!='net_settings'}
assert proj['net_settings']['classes']==bp['net_settings']['classes']
patterns=proj['net_settings']['netclass_patterns'];op=bp['net_settings']['netclass_patterns'];assert all(p in patterns for p in op) and len(patterns)==len(op)+15
members={n:[p['netclass'] for p in patterns if fnmatch.fnmatchcase(n,p['pattern'])] for n in nn if not n.startswith('unconnected-')};assert all(len(v)==1 for v in members.values())
for n in set(nn)-set(on):assert members[n]==(['CONTROL'] if n=='/Rail Telemetry/ADC_SUPPLY_OK' else ['ANALOG']),(n,members[n])
orphans=[p for p in patterns if not any(fnmatch.fnmatchcase(n,p['pattern']) for n in nn)]
assert {p['pattern'] for p in orphans}=={'/Controller/'+n for n in ['REC5_RESET','REC5_FAULT','SRC_FAULT','EPS_SWDIO','EPS_SWCLK','EPS_NRST']}
rb=json.loads((H/'readback.json').read_text());exec((H/'geometry_check.py').read_text());doc=parse((P/'rail_telemetry.kicad_sch').read_text());rows=[]
fixture=parse((ROOT/'hardware/eps/verification/controller_rev_b/swd_interface_candidate/disposable/swd_parts_check.kicad_sch').read_text())
for libid,ref in [('Ember_Charger_BMS_Review:TMUX1511PWR_REVIEW','U1300'),('Power_Supervisor:TPS3839DBZ','U1301')]:
 src=next(s for s in kids(one(fixture,'lib_symbols'),'symbol') if s[1]==libid);dest=next(s for s in kids(one(doc,'lib_symbols'),'symbol') if s[1]==libid);assert src==dest
 pins=descend(src,'pin');nums=[one(p,'number')[1] for p in pins];assert len(nums)==len(set(nums))
 query=next(c for c in rb['pins']['rail_telemetry']['components'] if c['reference']==ref);assert len(query['pins'])==len(pins)
 assert {p['number']:p['name'] for p in query['pins']}=={one(p,'number')[1]:one(p,'name')[1] for p in pins}
 for p in pins:
  num=one(p,'number')[1];net=next(n for n,v in nn.items() if (ref,num) in v);rows.append({'reference':ref,'pin':num,'name':one(p,'name')[1],'electrical_type':p[1],'net':net,'footprint':new[ref].findtext('footprint')})
assert len(rows)==17
assert sum(len(c['pins']) for c in rb['pins']['rail_telemetry']['components'] if c['reference'] in added)==67
for r,fs in fields.items():
 for unit in [s for s in kids(doc,'symbol') if props(s)['Reference']==r]:
  for k,v in fs.items():assert props(unit)[k]==v
writes=json.loads((H/'fields_writeback.json').read_text());assert set(writes)==added
for r,q in writes.items():
 assert not q.get('isError');q=json.loads(q['content'][0]['text'])
 for k,v in fields[r].items():assert q['fields'][k]==v
for fp,q in rb['footprints'].items():
 assert not q.get('isError');q=json.loads(q['content'][0]['text']);count=14 if 'TSSOP-14' in fp else 3 if fp.endswith('SOT-23') else 2
 assert len(q['pads'])==q['pad_count']==len(set(p['number'] for p in q['pads']))==count
for fn,data in [('package_pin_map.csv',rows),('endpoint_contract.csv',[{'reference':r,'pin':p,'net':n,'whole_net_endpoints':';'.join(a+'.'+z for a,z in sorted(v))} for n,v in nn.items() for r,p in sorted(v) if r in added or (r=='U100' and p in {'7','8','11','12'})])]:
 with (H/fn).open('w') as f:w=csv.DictWriter(f,fieldnames=data[0],lineterminator='\n');w.writeheader();w.writerows(data)
erc=json.loads((H/'erc.json').read_text());vs=[{'sheet':s['path'],**v} for s in erc['sheets'] for v in s['violations']]
assert Counter((v['severity'],v['type']) for v in vs)=={('error','pin_not_connected'):3,('error','pin_to_pin'):3,('warning','pin_to_pin'):2}
def sig(data):return sorted((v['sheet'],v['severity'],v['type'],v['description'],tuple(sorted(i['description'] for i in v['items']))) for v in data)
priorerc=json.loads((H.parent/'swd_integration/erc.json').read_text());priorvs=[{'sheet':s['path'],**v} for s in priorerc['sheets'] for v in s['violations']]
removed=[]
for v in priorvs:
 if v['type']=='pin_not_connected' and any(any(('Symbol U100 Pin '+pin+' [') in i['description'] for pin in ['7','8','11','12']) for i in v['items']):removed.append(v)
assert len(removed)==4 and sig(vs)==sig([v for v in priorvs if v not in removed])
assert len(PdfReader(H/'eps_rev_b.pdf').pages)==14
visual=json.loads((H/'visual_review.json').read_text())
assert len(visual['full_pages'])==14 and len(visual['details'])==18
for group in ['full_pages','details']:
 for name,digest in visual[group].items():assert sha(H/name)==digest,name
assert visual['native_source_sha256']==json.loads((H/'native_source_sha256.json').read_text())
effects=json.loads((H/'field_effects.json').read_text())
for s in kids(doc,'symbol'):
 r=props(s)['Reference']
 if r.startswith(('R','C')):
  f=next(x for x in effects if x['reference']==r)
  assert f['properties']=={p[1]:p for p in kids(s,'property')}
  assert abs(f['rendered_reference_angle_mod180'])<1e-6,r
  if r.startswith('R'):
   assert float(one(s,'at')[3])==90
   assert one(f['properties']['Value'],'at')[1:3]==one(s,'at')[1:3]
save('geometry.json',geometry);save('class_membership.json',{'actual':members,'orphans':orphans});save('reference_UUID_crosswalk.json',cross);save('presentation_crosswalk.json',{'retired_controller_text':{u:oldnotes[u] for u in removednotes},'added_controller_text':{u:newnotes[u] for u in set(newnotes)-set(oldnotes)}});save('erc_classified.json',vs);save('fields_readback.json',{r:meta(new[r]) for r in sorted(added)})
result={'basis':baseline['basis'],'status':'DEVELOPMENT GRAPH/PRESERVATION PASS; ELECTRICAL/PVT/PCB QUALIFICATION OPEN','parts':345,'nets':186,'functional_nets':173,'physical_endpoints':933,'new_parts':27,'old_physical_parts_preserved':318,'old_symbol_objects_retained':len(oldsyms),'current_symbol_objects':len(now),'frozen_files':len(baseline['frozen']),'ERC_errors':6,'ERC_warnings':2,'protected_delta':dict(sorted(delta.items())),'geometry':geometry}
save('verified.json',result);print(json.dumps(result,indent=2))
