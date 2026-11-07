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
assert (len(old),len(on),len(new),len(nn))==(305,166,318,175)
for r,c in old.items():
 if r!='J100':assert meta(c)==meta(new[r]),r
added={*[f'R{i}' for i in range(1200,1209)],'U1200','U1201','C1200','C1201'}
assert set(new)-set(old)==added
expected={n:set(v) for n,v in on.items()}
expected['+3V3'].remove(('J100','1'))
expected['+3V3']|={('U1200','14'),('U1200','12'),('U1201','3'),('C1200','1'),('C1201','1'),('R1203','1'),('R1204','1'),('R1207','1')}
expected['GND']|={('U1200','7'),('U1201','1'),('C1200','2'),('C1201','2'),('R1205','2'),('R1206','2'),('R1207','2'),('R1208','2')}
expected['GND'].remove(('J100','5'));expected['GND'].add(('J100','5'))
for name,u,r,pull,pin in [('EPS_SWDIO','24','R1200','R1203','2'),('EPS_SWCLK','25','R1201','R1205','1'),('EPS_NRST','6','R1202','R1204','2')]:
 prior=expected.pop('/Controller/'+name);assert prior=={('U100',u),('J100',{'EPS_SWDIO':'2','EPS_SWCLK':'3','EPS_NRST':'4'}[name])}|({('C112','1')} if name=='EPS_NRST' else set())
 expected[name]={('U100',u),(r,'1'),(pull,pin)}|({('C112','1')} if name=='EPS_NRST' else set())
segments={'SWDIO_SW':{('R1200','2'),('U1200','2')},'SWCLK_SW':{('R1201','2'),('U1200','5')},'NRST_SW':{('R1202','2'),('U1200','9')},'SWD_IO_CONN':{('U1200','3'),('J100','2')},'SWD_CLK_CONN':{('U1200','6'),('J100','4')},'SWD_RESET_CONN':{('U1200','8'),('J100','3')},'SWD_SUPPLY_OK':{('U1200',p) for p in ['1','4','10','13']}|{('U1201','2'),('R1206','1')}}
for n,v in segments.items():expected['/SWD Service/'+n]=v
expected['3V3_SWD_VTREF']={('U1200','11'),('J100','1'),('R1208','1')}
nc=next(n for n,v in nn.items() if v=={('J100','6')});assert nc.startswith('unconnected-');expected[nc]={('J100','6')}
assert expected==nn,{n:[sorted(expected.get(n,set())),sorted(nn.get(n,set()))] for n in set(expected)|set(nn) if expected.get(n)!=nn.get(n)}
assert sum(map(len,nn.values()))==866 and sum(not n.startswith('unconnected-') for n in nn)==158
fields=json.loads((H/'expected_component_fields.json').read_text());assert len(fields)==14
for r,fs in fields.items():
 for k,v in fs.items():assert meta(new[r])['fields'][k]==v,(r,k)
 assert new[r].findtext('footprint') and new[r].findtext('datasheet'),r
baseline=json.loads((H/'baseline.json').read_text());allowed=set(baseline['initial']);extra={'hardware/eps/rev_b/swd_service.kicad_sch'}
for p,h in baseline['frozen'].items():assert portable(p) and sha(ROOT/p)==h,p
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
# Exact preservation of every older symbol object, apart from documented J100 retirement and its two fixture ports.
oldsyms={};now={};refs=[];cross=[]
for path in sorted(P.glob('*.kicad_sch')):
 d=parse(path.read_text());assert one(d,'paper')[1]=='B'
 if path.name!='swd_service.kicad_sch':
  src=(H/(path.stem+'_before.txt')).read_text() if path.stem in ['controller','eps_rev_b'] else path.read_text()
  for s in kids(parse(src),'symbol'):oldsyms[one(s,'uuid')[1]]=s
 for s in kids(d,'symbol'):
  u=one(s,'uuid')[1];r=props(s)['Reference'];unit=int(one(s,'unit')[1]);assert u not in now;now[u]=s;refs.append((r,unit));assert '?' not in r
  ann=[a[1] for t in kids(s,'instances') for a in descend(t,'reference')];assert ann and set(ann)=={r}
  cross.append({'reference':r,'unit':unit,'UUID':u,'sheet':path.name,'old_UUID':u in oldsyms})
assert len(refs)==len(set(refs))
retired={u:s for u,s in oldsyms.items() if props(s)['Reference'] in {'J100','#PWR0109','#PWR0110'}};assert len(retired)==3
for u,s in oldsyms.items():
 if u in retired:assert u not in now
 else:assert now[u]==s,props(s)['Reference']
assert len(kids(parse((P/'eps_rev_b.kicad_sch').read_text()),'sheet'))==12
for s in kids(parse((H/'eps_rev_b_before.txt').read_text()),'sheet'):assert s in kids(parse((P/'eps_rev_b.kicad_sch').read_text()),'sheet')
proj=json.loads((P/'eps_rev_b.kicad_pro').read_text())
bp=json.loads((H/'project_before.json').read_text())
assert {k:v for k,v in proj.items() if k!='net_settings'}=={k:v for k,v in bp.items() if k!='net_settings'}
assert proj['net_settings']['classes']==bp['net_settings']['classes']
patterns=proj['net_settings']['netclass_patterns'];op=bp['net_settings']['netclass_patterns'];assert all(p in patterns for p in op) and len(patterns)==len(op)+11
members={n:[p['netclass'] for p in patterns if fnmatch.fnmatchcase(n,p['pattern'])] for n in nn if not n.startswith('unconnected-')};assert all(len(v)==1 for v in members.values())
for n in ['EPS_SWDIO','EPS_SWCLK','EPS_NRST',*['/SWD Service/'+n for n in segments if n!='SWD_SUPPLY_OK']]:assert members[n]==['DEBUG']
assert members['3V3_SWD_VTREF']==['POWER'] and members['/SWD Service/SWD_SUPPLY_OK']==['CONTROL']
orphans=[p for p in patterns if not any(fnmatch.fnmatchcase(n,p['pattern']) for n in nn)]
assert {p['pattern'] for p in orphans}=={'/Controller/'+n for n in ['REC5_RESET','REC5_FAULT','SRC_FAULT','EPS_SWDIO','EPS_SWCLK','EPS_NRST']}
for r in added|{'J100'}:
 m=meta(new[r]);wantfp='Resistor_SMD:R_0603_1608Metric' if r.startswith('R') else 'Capacitor_SMD:C_0603_1608Metric' if r.startswith('C') else {'J100':'Connector:Tag-Connect_TC2030-IDC-NL_2x03_P1.27mm_Vertical','U1200':'Package_SO:TSSOP-14_4.4x5mm_P0.65mm','U1201':'Package_TO_SOT_SMD:SOT-23'}[r]
 assert m['footprint']==wantfp,r
 wantval='330' if r in {'R1200','R1201','R1202'} else '47k' if r=='R1205' else '10k' if r.startswith('R') else '100nF' if r.startswith('C') else {'J100':'SWD','U1200':'TMUX1511PWR','U1201':'TPS3839K33DBZR'}[r]
 assert m['value']==wantval,r
rb=json.loads((H/'readback.json').read_text());exec((H/'geometry_check.py').read_text())
# All new physical pins are queried; names/types inherited from the accepted exact map.
fixture=parse((ROOT/'hardware/eps/verification/controller_rev_b/swd_interface_candidate/disposable/swd_parts_check.kicad_sch').read_text());d=parse((P/'swd_service.kicad_sch').read_text());rows=[]
for libid,ref in [('Ember_Charger_BMS_Review:TMUX1511PWR_REVIEW','U1200'),('Power_Supervisor:TPS3839DBZ','U1201'),('Connector:Conn_ARM_SWD_TagConnect_TC2030-NL','J100')]:
 src=next(s for s in kids(one(fixture,'lib_symbols'),'symbol') if s[1]==libid);dest=next(s for s in kids(one(d,'lib_symbols'),'symbol') if s[1]==libid);assert src==dest
 pins=descend(src,'pin');nums=[one(p,'number')[1] for p in pins];assert len(nums)==len(set(nums))
 query=next(c for c in rb['pins']['swd_service']['components'] if c['reference']==ref);assert len(query['pins'])==len(pins)
 assert {p['number']:p['name'] for p in query['pins']}=={one(p,'number')[1]:one(p,'name')[1] for p in pins}
 for p in pins:
  num=one(p,'number')[1];net=next(n for n,v in nn.items() if (ref,num) in v);rows.append({'reference':ref,'pin':num,'name':one(p,'name')[1],'electrical_type':p[1],'net':net,'footprint':new[ref].findtext('footprint')})
assert len(rows)==23
for r,fs in fields.items():
 q=rb['fields'][r]
 for unit in [s for s in kids(d,'symbol') if props(s)['Reference']==r]:
  for k,v in fs.items():assert props(unit)[k]==v
for fn,data in [('package_pin_map.csv',rows),('endpoint_contract.csv',[{'reference':r,'pin':p,'net':n,'whole_net_endpoints':';'.join(a+'.'+z for a,z in sorted(v))} for n,v in nn.items() for r,p in sorted(v) if r in added|{'J100'} or n in {'EPS_SWDIO','EPS_SWCLK','EPS_NRST'}])]:
 with (H/fn).open('w') as f:w=csv.DictWriter(f,fieldnames=data[0],lineterminator='\n');w.writeheader();w.writerows(data)
erc=json.loads((H/'erc.json').read_text());vs=[{'sheet':s['path'],**v} for s in erc['sheets'] for v in s['violations']]
assert Counter((v['severity'],v['type']) for v in vs)=={('error','pin_not_connected'):7,('error','pin_to_pin'):3,('warning','pin_to_pin'):2}
newjoins=[v for v in vs if v['sheet']=='/SWD Service/'];assert len(newjoins)==2
assert {frozenset(i['description'] for i in v['items']) for v in newjoins}=={frozenset(['Symbol U1200 Pin 12 [S4, Bidirectional, Line]','Symbol #FLG0402 Pin 1 [Power output, Line]']),frozenset(['Symbol U1200 Pin 11 [D4, Bidirectional, Line]','Symbol #FLG1200 Pin 1 [Power output, Line]'])}
def erc_signature(data):
 return sorted((v['sheet'],v['severity'],v['type'],v['description'],tuple(sorted(i['description'] for i in v['items']))) for v in data)
priorerc=json.loads((H.parent/'can_branch_integration/erc.json').read_text());priorvs=[{'sheet':s['path'],**v} for s in priorerc['sheets'] for v in s['violations']]
assert erc_signature([v for v in vs if v not in newjoins])==erc_signature(priorvs)
assert sum(len(c['pins']) for c in rb['pins']['swd_service']['components'] if c['reference'] in added|{'J100'})==45
assert len(PdfReader(H/'eps_rev_b.pdf').pages)==13
visual=json.loads((H/'visual_review.json').read_text());assert visual['hierarchy_source_sha256']==cli['hierarchy_source_sha256']
assert len(visual['full_pages'])==13 and len(visual['details'])==16
for name,h in (visual['full_pages']|visual['details']).items():assert sha(H/name)==h,name
save('geometry.json',geometry);save('class_membership.json',{'actual':members,'orphans':orphans});save('reference_UUID_crosswalk.json',{'current':cross,'retired':[{'reference':props(s)['Reference'],'uuid':u,'reason':'Logical J100 connector-only object replaced by physical service sheet'} for u,s in retired.items()]});save('erc_classified.json',vs);save('fields_readback.json',{r:meta(new[r]) for r in sorted(added|{'J100'})})
result={'basis':baseline['basis'],'status':'DEVELOPMENT GRAPH/PRESERVATION PASS; ELECTRICAL/PVT/PCB QUALIFICATION OPEN','parts':318,'nets':175,'functional_nets':158,'physical_endpoints':866,'new_parts':13,'old_physical_parts_preserved':304,'old_J100_UUID_retired':True,'old_symbol_objects':len(oldsyms),'old_symbol_objects_retained':len(oldsyms)-3,'current_symbol_objects':len(now),'frozen_files':len(baseline['frozen']),'ERC_errors':10,'ERC_warnings':2,'protected_delta':dict(sorted(delta.items())),'geometry':geometry}
save('verified.json',result);print(json.dumps(result,indent=2))
