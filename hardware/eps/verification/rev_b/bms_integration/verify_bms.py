#!/usr/bin/env python3
"""Exact full-hierarchy endpoint, metadata, annotation, package and source-scope gate."""
from pathlib import Path
from collections import Counter
import copy,csv,fnmatch,hashlib,json,re,subprocess,sys,xml.etree.ElementTree as E
H=Path(__file__).resolve().parent;ROOT=H.parents[4];P=ROOT/'hardware/eps/rev_b';BASE='b9d0724'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def gitbytes(p):return subprocess.check_output(['git','show',BASE+':'+p],cwd=ROOT)
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
 assert not stack;return root
def kids(n,k):return [v for v in n if isinstance(v,list) and v and v[0]==k]
def one(n,k):return kids(n,k)[0]
def descend(n,k):
 out=[]
 for v in n:
  if isinstance(v,list):
   if v and v[0]==k:out.append(v)
   out.extend(descend(v,k))
 return out
def graph(p):
 r=E.parse(p).getroot();cs=r.findall('components/comp');refs=[c.get('ref') for c in cs]
 assert len(refs)==len(set(refs)),Counter(refs)
 nodes=[(x.get('ref'),x.get('pin')) for n in r.findall('nets/net') for x in n.findall('node')]
 assert len(nodes)==len(set(nodes)),Counter(nodes)
 names=[n.get('name') for n in r.findall('nets/net')];assert len(names)==len(set(names))
 return r,{c.get('ref'):c for c in cs},{n.get('name'):{(x.get('ref'),x.get('pin')) for x in n.findall('node')} for n in r.findall('nets/net')}
def meta(c):return {k:c.findtext(k) or '' for k in ['value','footprint','datasheet','tstamps']}|{'libsource':c.find('libsource').attrib,'fields':{x.get('name'):x.text or '' for x in c.findall('fields/field')}}
old,oc,on=graph(H/'before.xml');new,nc,nn=graph(H/'eps_rev_b.xml')
assert len(oc)==187 and len(on)==103 and len(nc)==233 and len(nn)==133
tcr={'R601','R610','R612','R614','R621'}
for ref,c in oc.items():
 expected=meta(c)
 if ref in tcr:assert expected['fields']['TCR']=='25 ppm/K';expected['fields']['TCR']='100 ppm/K'
 assert expected==meta(nc[ref]),ref
assert len({c.findtext('tstamps') for c in nc.values()})==233
added={k:set(map(tuple,v)) for k,v in json.loads((H/'expected_added_nets.json').read_text()).items()}
assert len(added)==34
expected={k:set(v) for k,v in on.items()};moved={('U100','19'),('U100','21')}
removed={k for k,v in expected.items() if v and v<=moved};assert len(removed)==2 and all(k.startswith('unconnected-') for k in removed)
for k in removed:del expected[k]
for k,v in added.items():expected.setdefault(k,set()).update(v)
assert nn==expected,{k:(sorted(v),sorted(nn.get(k,set()))) for k,v in expected.items() if v!=nn.get(k)}
newrefs={'U200','U201','D200','J200','R111','R112',*[f'Q{i}' for i in range(200,204)],*[f'R{i}' for i in range(200,220)],*[f'C{i}' for i in range(200,211)],*[f'TP{i}' for i in range(200,205)]}
assert len(newrefs)==46 and set(nc)-set(oc)==newrefs
newnodes={p for v in nn.values() for p in v if p[0] in newrefs};assert len(newnodes)==137
assert newnodes=={p for v in added.values() for p in v if p[0] in newrefs}
for ref in newrefs:
 pins=nc[ref].findall('units/unit/pins/pin');assert {(ref,p.get('num')) for p in pins}=={p for p in newnodes if p[0]==ref},ref
assert sum(map(len,nn.values()))==648
assert {p for v in added.values() for p in v if p[0]=='U200'}=={('U200',str(i)) for i in range(1,34)}
assert nn['BATT_PERMITTED']==on['BATT_PERMITTED']
assert nn['VIN_CHG']==on['VIN_CHG'] and nn['SYS_PWR_PERMITTED']==on['SYS_PWR_PERMITTED']
assert ('U100','20') in nn['+3V3'] and ('U100','29') not in set().union(*added.values())

# Per-part metadata contract from selected manufacturer codes.
mpn={'U200':'BQ40Z50RSMR-R2','U201':'ISO1540DR','Q200':'CSD18543Q3A','Q201':'CSD18543Q3A','Q202':'BSS84-7-F','Q203':'DMN62D2U-7','D200':'BAT46W-7-F','J200':'BM07B-GHS-TBT(LF)(SN)','R200':'CRF1206-FZ-R002ELF','R213':'CRCW1206300RFKEAHP'}
for i in range(201,220):
 if i==213:continue
 code='100R' if i<=205 else '10K0' if i==206 else '5K10' if i in [207,208,211] else '1K00' if i==214 else '20K0' if 215<=i<=217 else '3K90' if i>=218 else None
 mpn[f'R{i}']='TNPW0603'+code+'BEEA' if code else 'CRCW060310M0JNEA'
for ref in ['R111','R112']:mpn[ref]='TNPW06033K90BEEA'
for i in range(200,211):mpn[f'C{i}']='GRM21BR71A475KE51L' if i==203 else 'GRM188R72A104KA35D'
for i in range(200,205):mpn[f'TP{i}']='PCB copper test feature; not procured'
fields={r:meta(nc[r])['fields'] for r in newrefs};assert set(mpn)==newrefs
for ref,m in mpn.items():assert fields[ref]['MFG P/N']==m and nc[ref].findtext('footprint'),ref
for ref in [r for r in newrefs if r.startswith('R')]:
 f=fields[ref];assert all(k in f for k in ['Tolerance','Power','PackageSize'])
 if f['MFG P/N'].startswith('TNPW'):assert f['Tolerance']=='0.1%' and f['Power']=='0.110 W general P70' and f['TemperatureCoefficient']=='25 ppm/K'
 if ref in ['R209','R210','R212']:assert f['Tolerance']=='5%' and f['TemperatureCoefficient']=='200 ppm/K' and f['Power']=='0.10 W standard P70'
assert fields['R200']['Power']=='1 W P70' and fields['R200']['TemperatureCoefficient']=='50 ppm/K'
assert fields['R213']['Power']=='0.75 W P70' and fields['R213']['TemperatureCoefficient']=='100 ppm/K'
assert nc['R214'].findtext('value')=='1k'
for i in range(200,211):
 f=fields[f'C{i}'];assert f['Dielectric']=='X7R' and f['Tolerance']=='10%' and f['Voltage']==('10 V' if i==203 else '100 V')
assert fields['U200']['Review']=='CUSTOM — REVIEW REQUIRED'
assert all(fields[r]['Review']=='CUSTOM FOOTPRINT — REVIEW REQUIRED' for r in ['Q200','Q201'])

rb=json.loads((H/'readback.json').read_text());lib=rb['library'];bq=lib['bq']
assert bq['pin_count']==len(bq['pins'])==33 and {p['number'] for p in bq['pins']}==set(map(str,range(1,34)))
names=['PBI','VC4','VC3','VC2','VC1','SRN','NC','SRP','VSS','TS1','TS2','TS3','TS4','NC','BTP_INT','PRES/SHUTDN','DISP','SMBD','SMBC','LEDCNTLA','LEDCNTLB','LEDCNTLC','PTC','PTCEN','FUSE','VCC','PACK','DSG','NC','PCHG','CHG','BAT','VSS_EP']
assert {p['number']:p['name'] for p in bq['pins']}=={str(i):v for i,v in enumerate(names,1)}
assert {p['number']:p['type'] for p in bq['pins'] if p['number'] in ['15','25']}=={'15':'output','25':'output'}
assert lib['bq_land']['pad_count']==len(lib['bq_land']['pads'])==33 and {p['number'] for p in lib['bq_land']['pads']}==set(map(str,range(1,34)))
assert lib['powerfet_land']['pad_count']==len(lib['powerfet_land']['pads'])==30
assert Counter(p['number'] for p in lib['powerfet_land']['pads'])=={'1':1,'2':1,'3':1,'4':1,'5':5,'':21}
assert {p['number']:p['name'] for p in lib['powerfet']['pins']}=={'1':'S','2':'S','3':'S','4':'G','5':'D'}
assert nc['U201'].findtext('datasheet')=='https://www.ti.com/lit/ds/symlink/iso1540.pdf'
subprocess.run([sys.executable,str(H/'verify_parts.py')],check=True,capture_output=True,text=True)

# Every prior symbol object, including invisible powers/instance annotations, is retained.
oldnames=['eps_rev_b','controller','can_interfaces','essential_3v3','recovery_5v','source_protection','rail_protection','charger']
oldsyms={};cursyms={};allrefs=[];allids=[];rows=[]
for name in oldnames+['bms_protection']:
 current=parse((P/(name+'.kicad_sch')).read_text());assert one(current,'paper')[1]=='B'
 if name in oldnames:
  for s in kids(parse(gitbytes('hardware/eps/rev_b/'+name+'.kicad_sch').decode()),'symbol'):oldsyms[one(s,'uuid')[1]]=(name,s)
 for s in kids(current,'symbol'):
  props={v[1]:v[2] for v in kids(s,'property')};ref=props['Reference'];u=one(s,'uuid')[1];allrefs.append(ref);allids.append(u)
  ir=[v[1] for v in descend(s,'reference')];assert ir and all(x==ref for x in ir) and '?' not in ref
  cursyms[u]=(name,s);rows.append({'sheet':name,'reference':ref,'uuid':u,'instance_refs':ir})
 assert {c['reference'] for c in rb['all_symbols'][name]['components']}=={v['reference'] for v in rows if v['sheet']==name}
assert len(allrefs)==len(set(allrefs))==len(allids)==len(set(allids))==451
norm=[(re.sub(r'\d+$','',r),int(re.search(r'\d+$',r)[0])) if re.match(r'^#(?:PWR|FLG)\d+$',r) else r for r in allrefs]
assert len(norm)==len(set(norm))
assert len(oldsyms)==359
for u,(name,s) in oldsyms.items():
 expected=copy.deepcopy(s);ref=next(v[2] for v in kids(expected,'property') if v[1]=='Reference')
 if ref in tcr:next(v for v in kids(expected,'property') if v[1]=='TCR')[2]='100 ppm/K'
 assert cursyms[u]==(name,expected),(name,ref)
(H/'annotation_verified.json').write_text(json.dumps({'old_symbols_preserved':359,'current_symbols':451,'all_reference_UUID_and_instance_records_unique':True,'symbols':rows},indent=2)+'\n')

# Project-only assignments, with exactly one class per actual functional net.
proj=json.loads((P/'eps_rev_b.kicad_pro').read_text());bp=json.loads(gitbytes('hardware/eps/rev_b/eps_rev_b.kicad_pro'))
assert {k:v for k,v in proj.items() if k!='net_settings'}=={k:v for k,v in bp.items() if k!='net_settings'}
assert proj['net_settings']['classes']==bp['net_settings']['classes']
patterns=proj['net_settings']['netclass_patterns'];assert all(p in patterns for p in bp['net_settings']['netclass_patterns'])
classes={n:[p['netclass'] for p in patterns if fnmatch.fnmatchcase(n,p['pattern'])] for n in nn if not n.startswith('unconnected-')}
assert len(classes)==115 and all(len(c)==1 for c in classes.values()),classes
for n in ['EPS_BMS_SCL','EPS_BMS_SDA','/2S pack protection/BMS_SMBC','/2S pack protection/BMS_SMBD']:assert classes[n]==['I2C']
assert classes['GND_BMS_RAW']==['POWER'] and classes['/2S pack protection/BMS_SRP']==['ANALOG']
orphan={p['pattern'] for p in patterns if not any(fnmatch.fnmatchcase(n,p['pattern']) for n in nn)}
assert orphan=={'/Controller/REC5_RESET','/Controller/REC5_FAULT','/Controller/SRC_FAULT'}
(H/'class_membership.json').write_text(json.dumps({'classes':classes,'orphan_patterns':sorted(orphan),'routing_defaults_not_physical_qualification':True},indent=2)+'\n')

def dirs(p,w):
 x,y=p;a,b,c,d=[round(w[k],4) for k in ['x1','y1','x2','y2']];o=set()
 if b==d==y and min(a,c)<=x<=max(a,c):
  if x>min(a,c):o.add('L')
  if x<max(a,c):o.add('R')
 if a==c==x and min(b,d)<=y<=max(b,d):
  if y>min(b,d):o.add('U')
  if y<max(b,d):o.add('D')
 return o
geometry={}
for name,data in rb['pins'].items():
 d=data['layout'];w=d['wires'];points=set();ends=set();segments=[]
 for z in w:
  assert z['x1']==z['x2'] or z['y1']==z['y2']
  assert all(abs(z[k]/1.27-round(z[k]/1.27))<1e-5 for k in ['x1','y1','x2','y2'])
  a=(round(z['x1'],4),round(z['y1'],4));b=(round(z['x2'],4),round(z['y2'],4));assert a!=b
  points.update([a,b]);ends.update([a,b]);segments.append(tuple(sorted([a,b])))
 assert len(segments)==len(set(segments)),name
 for a in w:
  for b in w:
   x,y=round(a['x1'],4),round(b['y1'],4)
   if a['x1']==a['x2'] and b['y1']==b['y2'] and min(a['y1'],a['y2'])<=y<=max(a['y1'],a['y2']) and min(b['x1'],b['x2'])<=x<=max(b['x1'],b['x2']):points.add((x,y))
 native=parse((P/(name+'.kicad_sch')).read_text());junctions={tuple(map(float,one(j,'at')[1:3])) for j in kids(native,'junction')}
 four={p for p in points if len(set().union(*(dirs(p,z) for z in w)))==4}
 assert not (four & (ends|junctions)),(name,four&(ends|junctions))
 assert not any((round(l['x'],4),round(l['y'],4)) in four for l in d['labels'])
 pins=data['pins']['components'];assert {c['reference'] for c in pins}=={c['reference'] for c in d['components']}
 for c in pins:
  for pin in c['pins']:
   p=round(pin['x'],4),round(pin['y'],4);assert all(abs(v/1.27-round(v/1.27))<1e-5 for v in p)
   assert len(set().union(*(dirs(p,z) for z in w)))<3,(name,c['reference'],pin)
 geometry[name]={'wire_segments':len(w),'joined_fourways':0,'unconnected_crossings':sorted(four),'all_queried_pin_anchors_checked':sum(len(c['pins']) for c in pins),'pin_branch_anchors':0}
(H/'geometry.json').write_text(json.dumps(geometry,indent=2)+'\n')

erc=json.loads((H/'erc.json').read_text());viol=[v for s in erc['sheets'] for v in s['violations']]
assert Counter((v['severity'],v['type']) for v in viol)=={('error','pin_not_connected'):11,('error','pin_to_pin'):3}
intentional=[]
for v in viol:
 if v['type']=='pin_to_pin':intentional.append(sorted(i['description'].split('Symbol ')[1].split(' [')[0] for i in v['items']))
assert sorted(intentional)==sorted([['U300 Pin 25','U300 Pin 26'],['U200 Pin 15','U200 Pin 25'],['#FLG0202 Pin 1','U200 Pin 25']])
cli=json.loads((H/'cli_checks.json').read_text());assert cli['netlist_sha256']==sha(H/'eps_rev_b.xml')
assert all(not v['annotation_warning'] for v in cli.values() if isinstance(v,dict) and 'annotation_warning' in v)
for p,h in cli['hierarchy_source_sha256'].items():assert sha(ROOT/p)==h,p

baseline=json.loads((H/'baseline_sha256.json').read_text());assert baseline['commit'].startswith(BASE)
allowed={'hardware/eps/rev_b/'+f for f in ['eps_rev_b.kicad_sch','eps_rev_b.kicad_pro','controller.kicad_sch','recovery_5v.kicad_sch','source_protection.kicad_sch','rail_protection.kicad_sch']}
changed={p for p,h in baseline['protected'].items() if sha(ROOT/p)!=h};assert changed==allowed,changed
for p,h in baseline['protected'].items():assert hashlib.sha256(gitbytes(p)).hexdigest()==h,p
frozen_tracked=set(subprocess.check_output(['git','ls-tree','-r','--name-only',BASE,'hardware/eps/verification/rev_b/charger_integration'],cwd=ROOT,text=True).splitlines())
assert len(frozen_tracked)==61 and frozen_tracked<=set(baseline['frozen_charger'])
for p in frozen_tracked:
 h=baseline['frozen_charger'][p];assert sha(ROOT/p)==h==hashlib.sha256(gitbytes(p)).hexdigest(),p
# Preserve the original broad capture, but do not call OS/GUI caches committed evidence.
ignored_status={p:{'before':h,'after':sha(ROOT/p) if (ROOT/p).exists() else None} for p,h in baseline['frozen_charger'].items() if p not in frozen_tracked}
ignored_changed={p:v for p,v in ignored_status.items() if v['before']!=v['after']}
assert all(Path(p).name=='.DS_Store' or p.endswith('.lck') for p in ignored_changed),ignored_changed
(H/'ignored_prior_gui_files.json').write_text(json.dumps({'captured_untracked_ignored_files':34,'scope':'Not committed checkpoint artifacts; no native source changes allowed','changed_GUI_cache_or_removed_lock':ignored_changed},indent=2)+'\n')
newpaths={'hardware/eps/rev_b/bms_protection.kicad_sch'}|{'hardware/eps/verification/rev_b/bms_integration/parts_disposable/bms_parts_check'+s for s in ['.kicad_sch','.kicad_pro','.kicad_pcb']}
protected=lambda p:p.endswith(('.kicad_sch','.kicad_pro','.kicad_pcb','.kicad_sym','.kicad_mod','sym-lib-table','fp-lib-table'))
delta={}
for line in subprocess.check_output(['git','diff','--name-status',BASE,'--','hardware/eps'],cwd=ROOT,text=True).splitlines():
 status,path=line.split('\t')
 if protected(path):delta[path]=status
for path in subprocess.check_output(['git','ls-files','--others','--exclude-standard','hardware/eps'],cwd=ROOT,text=True).splitlines():
 if protected(path):delta[path]='A'
assert delta==({p:'M' for p in allowed}|{p:'A' for p in newpaths}),delta
manifest=json.loads((H/'native_source_sha256.json').read_text());assert set(manifest)==allowed|newpaths
for p,h in manifest.items():assert sha(ROOT/p)==h,p
assert len(rb['hierarchy']['children'])==8 and rb['hierarchy']['children'][-1]['file']=='bms_protection.kicad_sch'

with (H/'endpoint_contract.csv').open('w') as f:
 rows=[{'reference':r,'pin':pin,'net':n,'whole_net_endpoints':';'.join(a+'.'+b for a,b in sorted(nn[n]))} for n,v in added.items() for r,pin in sorted(v)]
 w=csv.DictWriter(f,fieldnames=rows[0],lineterminator='\n');w.writeheader();w.writerows(rows)
with (H/'bom.csv').open('w') as f:
 cols=['Reference','Value','MFG P/N','Footprint','Tolerance','Power','PackageSize','Voltage','Dielectric','Qualification']
 w=csv.DictWriter(f,fieldnames=cols,lineterminator='\n');w.writeheader()
 for r in sorted(newrefs):w.writerow({'Reference':r,'Value':nc[r].findtext('value'),'Footprint':nc[r].findtext('footprint')}|{k:fields[r].get(k,'') for k in cols[2:] if k!='Footprint'})
(H/'fields_readback.json').write_text(json.dumps({r:meta(nc[r]) for r in sorted(newrefs)},indent=2)+'\n')
result={'status':'DEVELOPMENT ENDPOINT/METADATA/PACKAGE MAP PASS; PACK PROTECTION/GAUGING QUALIFICATION OPEN','basis':baseline['commit'],'physical_parts':233,'nets':133,'functional_nets':115,'unique_physical_ref_pin_endpoints':648,'new_physical_parts':46,'prior_physical_UUIDs_retained':187,'prior_symbol_objects_retained':359,'approved_metadata_exceptions':sorted(tcr),'BQ_physical_pins_checked':33,'added_or_expanded_whole_net_sets':34,'all_symbol_instances':451,'ERC_errors':14,'ERC_warnings':0,'intentional_ERC_pairs':intentional,'frozen_committed_charger_files':len(frozen_tracked),'geometry':geometry,'orphan_patterns':sorted(orphan),'PCB_scope':'Only independent five-part disposable; real integrated board unchanged','open_gates':['DSG short gate-source overvoltage / coupled cutoff SOA','shared-positive ISO bus current-measurement error / isolated power','physical RBF and charger-to-pack35V fault containment','commissioning/configuration/thresholds/NTC/harness/thermal/pack acceptance','S03 native severity / S11 visible-field API limits']}
(H/'verified.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
