#!/usr/bin/env python3
"""Verify full EPS graph union, preserved parts, package maps and scoped globals."""
from pathlib import Path
import collections,csv,fnmatch,hashlib,json,re,xml.etree.ElementTree as E
H=Path(__file__).resolve().parent;REPO=H.parents[4];P=REPO/'hardware/eps/rev_b';PREV=H.parent/'recovery_integration';AUTH=REPO/'hardware/eps/verification/protection/latch/native'
d=json.loads((H/'rebuild_readback.json').read_text());m=d['refmap'];signals={'SRC_FAULT','REC5_FAULT','REC5_RESET'}
def parse(p):
 r=E.parse(p).getroot();return r,{n.get('name'):set((x.get('ref'),x.get('pin')) for x in n.findall('node')) for n in r.findall('./nets/net')}
old,on=parse(PREV/'eps_rev_b.xml');src,sn=parse(H/'source_current.xml');authority,an=parse(AUTH/'protection.xml');new,nn=parse(H/'eps_rev_b.xml')
assert sn==an and len(sn)==41 and len([n for n in sn if not n.startswith('unconnected-')])==37
sc={c.get('ref'):c for c in src.findall('./components/comp')};ac={c.get('ref'):c for c in authority.findall('./components/comp')};assert len(sc)==83
for r,c in sc.items():assert E.tostring(c)==E.tostring(ac[r]),r

def priorname(n):return n.split('/')[-1] if n.startswith('/Controller/') and n.split('/')[-1] in signals else n
def source_name(n):
 if n.split('/')[-1] in signals:return n.split('/')[-1]
 if n.startswith('/Recovery rail fault containment/'):return n.replace('/Recovery rail fault containment/','/Recovery rail protection/',1)
 if n.startswith('/'):return '/Solar source protection'+n
 if n.startswith('Net-('):return re.sub(r'^Net-\(([^-]+)-',lambda x:'Net-('+m[x[1]]+'-',n)
 if n.startswith('unconnected-('):return re.sub(r'^unconnected-\(([^-]+)-',lambda x:'unconnected-('+m[x[1]]+'-',n)
 return n
mapped={source_name(n):{(m[r],p) for r,p in ep} for n,ep in sn.items()}
expected={priorname(n):set(ep) for n,ep in on.items()}
for n,ep in mapped.items():expected.setdefault(n,set()).update(ep)
assert nn==expected,[(n,sorted(ep),sorted(nn.get(n,set()))) for n,ep in expected.items() if nn.get(n)!=ep]
assert len(nn)==91 and len([n for n in nn if not n.startswith('unconnected-')])==68
for n,ep in on.items():assert ep<=nn[priorname(n)] and (n in ['+3V3','GND','5V0_RECOVERY_REG'] or priorname(n) in signals or ep==nn[priorname(n)]),n
assert nn['SYS_PWR_PERMITTED']==on['SYS_PWR_PERMITTED'] and nn['VIN_CHG']!=nn['SYS_PWR_PERMITTED']
assert nn['SOLAR_PERMITTED']=={('L600','1')}
assert nn['+5V']==mapped['+5V'] and ('L601','1') in nn['5V0_RECOVERY_REG']
assert nn['5V0_RECOVERY_RAW']==on['5V0_RECOVERY_RAW']
assert nn['SRC_FAULT']=={('U100','3'),('U600','11'),('R608','2')}
assert nn['REC5_FAULT']=={('U100','14'),('U601','11'),('R619','2')}
assert nn['REC5_RESET']=={('U100','13'),('R623','1')}
assert nn['+3V3']-on['+3V3']=={('R608','1'),('R619','1')}
assert all((r,'2') in nn['REC5_PIN'] for r in ['Q603','Q604','Q605'])
assert all((r,'2') in nn['/Recovery rail protection/REC5_SENSE'] for r in ['Q606','Q607','Q608'])
assert all((r,'3') in nn['/Recovery rail protection/REC5_COMMON'] for r in ['Q603','Q604','Q605','Q606','Q607','Q608'])
for u in ['U600','U601']:assert {(u,'10'),(u,'15')}<=nn['GND']
comps={c.get('ref'):c for c in new.findall('./components/comp')};assert len(comps)==160
for c in old.findall('./components/comp'):assert c.findtext('tstamps')==comps[c.get('ref')].findtext('tstamps'),c.get('ref')
fields={}
for root,remap in [(old,lambda r:r),(src,lambda r:m[r])]:
 for c in root.findall('./components/comp'):
  r=remap(c.get('ref'));z=comps[r]
  for k in ['value','footprint','datasheet']:assert (c.findtext(k) or '')==(z.findtext(k) or ''),(r,k)
  assert c.find('libsource').attrib==z.find('libsource').attrib,r
  cf={x.get('name'):x.text or '' for x in c.findall('./fields/field')};nf={x.get('name'):x.text or '' for x in z.findall('./fields/field')};assert cf==nf,r;fields[r]=nf
assert len(d['crosswalk'])==165 and sum(bool(r['new_reference']) for r in d['crosswalk'])==161
assert len([r for r in d['crosswalk'] if r['physical']])==83
assert set(d['omitted'])=={'#FLG172','#FLG173','#FLG202','#PWR171'}
for row in d['crosswalk']:
 if row['new_reference']:assert row['new_uuid']!=row['old_uuid']
 else:assert row['reason'] and row['old_reference'] in d['omitted']
retained_flags=sorted(c['reference'] for v in d['readback'].values() for c in v['components'].values() if c['lib_id']=='power:PWR_FLAG')
assert retained_flags==[f'#FLG{i:04}' for i in range(600,607)]
assert sum(len(v) for v in d['omitted_wire_UUIDs'].values())==4
# Exact verified stock symbol electrical-number maps; paste-only apertures are not electrical pads.
pk=d['packages'];pinmap=lambda k:{p['number']:p['name'] for p in pk['symbols'][k]['pins']}
assert pinmap('Power_Management:LTC4364HDE')=={'1':'OUT','2':'SENSE','3':'DGATE','4':'SOURCE','5':'GATE','6':'VCC','7':'~{SHDN}','8':'UV','9':'OV','10':'GND','11':'~{FLT}','12':'ENOUT','13':'TMR','14':'FB','15':'GND'}
assert pinmap('Transistor_FET:Q_NMOS_GDS')=={'1':'G','2':'D','3':'S'}
for k in ['Transistor_BJT:MMBT3906','Transistor_BJT:MMBT3904']:assert pinmap(k)=={'1':'B','2':'E','3':'C'}
for k in ['Diode:1N4148W','Device:D_Zener']:assert pinmap(k)=={'1':'K','2':'A'}
for k,nums,apertures in [('Package_DFN_QFN:DFN-14-1EP_3x4mm_P0.5mm_EP1.7x3.3mm',set(map(str,range(1,16))),8),('Package_TO_SOT_SMD:TO-252-2',{'1','2','3'},4)]:
 pads=pk['footprints'][k]['pads'];named=[p for p in pads if p['number']];blank=[p for p in pads if not p['number']]
 assert len(named)==len(nums) and {p['number'] for p in named}==nums
 assert len(blank)==apertures and all(p['layers']==['F.Paste'] for p in blank)
 assert all(p['type']=='smd' and not p['drill'] for p in pads)
ep=[p for p in pk['footprints']['Package_DFN_QFN:DFN-14-1EP_3x4mm_P0.5mm_EP1.7x3.3mm']['pads'] if p['number']=='15'][0];assert (ep['x'],ep['y'],ep['width'],ep['height'])==(0,0,1.7,3.3)
for k in ['Ember_EPS_Recovery:Panasonic_CP_F_8x10.2mm_REVIEW','Ember_EPS_Recovery:Panasonic_CP_D8_6.3x7.7mm_REVIEW','Diode_SMD:D_SOD-123','Diode_SMD:D_SMB']:
 assert {p['number'] for p in pk['footprints'][k]['pads']}=={'1','2'}
# Saved native label scopes are checked separately from the connected graph.
clabels=d['controller_labels']['labels']
for n in signals:assert len([l for l in clabels if l['net']==n and l['type']=='GlobalLabel'])==1
for k,names in [('source',['SRC_FAULT']),('rail',['REC5_FAULT','REC5_RESET'])]:
 for n in names:assert len([l for l in d['readback'][k]['labels']['labels'] if l['net']==n and l['type']=='GlobalLabel'])==1
# Geometry distinguishes unconnected crossings from forbidden joined four-way nodes.
def directions(p,w):
 x,y=p;a,b,c,e=[round(w[k],4) for k in ['x1','y1','x2','y2']];out=set()
 if b==e==y and min(a,c)<=x<=max(a,c):
  if x>min(a,c):out.add('L')
  if x<max(a,c):out.add('R')
 if a==c==x and min(b,e)<=y<=max(b,e):
  if y>min(b,e):out.add('U')
  if y<max(b,e):out.add('D')
 return out
annotation=json.loads((H/'annotation_geometry.json').read_text())['sheets'];geometry={}
for k,v in d['readback'].items():
 w=v['geometry']['wires'];points=set();ends=set();file='source_protection' if k=='source' else 'rail_protection'
 for z in w:
  assert z['x1']==z['x2'] or z['y1']==z['y2']
  assert all(abs(z[n]/1.27-round(z[n]/1.27))<1e-6 for n in ['x1','y1','x2','y2'])
  ends|={(round(z['x1'],4),round(z['y1'],4)),(round(z['x2'],4),round(z['y2'],4))}
 for a in w:
  for z in w:
   p=(round(a['x1'],4),round(z['y1'],4))
   if a['x1']==a['x2'] and z['y1']==z['y2'] and directions(p,a) and directions(p,z):points.add(p)
 def degree(p):return len(set().union(*(directions(p,z) for z in w)))
 cross={p for p in points if degree(p)==4};dots={tuple(round(x,4) for x in p) for p in annotation[file]['junctions']};assert not cross&(ends|dots)
 for c in v['pins']['components']:
  for p in c['pins']:assert degree((round(p['x'],4),round(p['y'],4)))<=1,(k,c['reference'],p['number'])
 assert len(annotation[file]['no_connects'])==2
 assert all(l['net'] not in ['GND','+3V3','+5V','SOLAR_PERMITTED','VIN_CHG','5V0_RECOVERY_REG'] for l in v['geometry']['labels'])
 geometry[k]={'orthogonal_on_grid_wires':len(w),'joined_fourway':0,'unconnected_crossings':sorted(cross),'pins_at_branches':0}
assert len(geometry['source']['unconnected_crossings'])==1 and len(geometry['rail']['unconnected_crossings'])==5
assert len(d['readback']['source']['geometry']['wires'])==107 and len(d['readback']['rail']['geometry']['wires'])==138
settings=json.loads((P/'eps_rev_b.kicad_pro').read_text())['net_settings'];patterns={x['pattern']:x['netclass'] for x in settings['netclass_patterns']};functional={n for n in nn if not n.startswith('unconnected-')}
assert len(patterns)==71
orphans={p for p in patterns if not any(fnmatch.fnmatchcase(n,p) for n in nn)};assert orphans==set(d['orphan_class_patterns'])
for n in functional:
 matches=[p for p in patterns if fnmatch.fnmatchcase(n,p)];assert matches==[n],(n,matches)
for n,cls in d['class_intent'].items():assert n in functional and patterns[n]==cls
for n in signals:assert patterns[n]=='CONTROL'
assert all(not any(fnmatch.fnmatchcase(n,p) for n in nn) for p in orphans)
for f in ['sym-lib-table','fp-lib-table']:
 s=(P/f).read_text();assert '${KIPRJMOD}/../libraries/' in s and '/Users/' not in s
hashes=json.loads((H/'historical_source_hashes.json').read_text())
for file,digest in hashes.items():assert hashlib.sha256((REPO/file).read_bytes()).hexdigest()==digest,file
old_evidence=0
for folder in [H.parent/'integration',H.parent/'buck_integration',PREV]:
 for file,digest in json.loads((folder/'evidence_sha256.json').read_text()).items():assert hashlib.sha256((folder/file).read_bytes()).hexdigest()==digest,(folder,file);old_evidence+=1
erc=json.loads((H/'erc.json').read_text());vs=[v for s in erc['sheets'] for v in s['violations']];counts=dict(collections.Counter(v['severity'] for v in vs));types=dict(collections.Counter(v['type'] for v in vs));assert counts=={'error':16} and types=={'pin_not_connected':16}
assert 'four_way_junction' in [x['key'] for x in erc['ignored_checks']]
with (PREV/'reference_crosswalk.csv').open() as f:previous=list(csv.DictReader(f))
rows=previous+d['crosswalk']
with (H/'reference_crosswalk.csv').open('w') as f:
 writer=csv.DictWriter(f,fieldnames=list(d['crosswalk'][0]),lineterminator='\n');writer.writeheader();writer.writerows(rows)
with (H/'protection_endpoint_crosswalk.csv').open('w') as f:
 writer=csv.writer(f,lineterminator='\n');writer.writerow(['OldNet','IntegratedNet','MappedProtectionEndpoints','CompleteRootEndpoints'])
 for n in sn:writer.writerow([n,source_name(n),'; '.join(r+'.'+p for r,p in sorted(mapped[source_name(n)])),'; '.join(r+'.'+p for r,p in sorted(nn[source_name(n)]))])
with (H/'prior_endpoint_crosswalk.csv').open('w') as f:
 writer=csv.writer(f,lineterminator='\n');writer.writerow(['PreviousNet','IntegratedNet','PreviousEndpoints','CompleteRootEndpoints'])
 for n in on:writer.writerow([n,priorname(n),'; '.join(r+'.'+p for r,p in sorted(on[n])),'; '.join(r+'.'+p for r,p in sorted(nn[priorname(n)]))])
(H/'fields_readback.json').write_text(json.dumps(fields,indent=2)+'\n')
result={'status':'FULL_GRAPH_AND_METADATA_PASS; QUALIFICATION_OPEN','cad_basis':'b5b1c03','physical_parts':160,'new_protection_parts':83,'protection_sets':41,'protection_functional_sets':37,'protection_NC_sets':4,'root_nets':91,'root_functional_nets':68,'previous_part_UUIDs_preserved':77,'previous_endpoint_sets_preserved_with_approved_scope_migration':56,'fault_reset_endpoints':{n:sorted(r+'.'+p for r,p in nn[n]) for n in sorted(signals)},'VIN_CHG_joined_to_SYS_PWR_PERMITTED':False,'protected_+5V_has_only_barrier_downstream_nodes':True,'crosswalk_rows':len(rows),'retained_native_instances':304,'new_retained_protection_instances':161,'omitted_protection_instances':d['omitted'],'retained_protection_flags':retained_flags,'geometry':geometry,'netclass_actual_members':68,'netclass_patterns':71,'orphan_patterns_proven_unmatched':sorted(orphans),'erc_counts':{'error':16,'warning':0},'erc_types':types,'historical_files_unchanged':len(hashes),'previous_evidence_files_unchanged':old_evidence,'open':['physical RBF/charger PowerPath/BMS absent; SYS and SOLAR external fixtures','low-VCC FB accuracy/hot SOA/source-energy/component bounds','102.6uF nominal SYS input load and simultaneous startup unqualified','autonomous3V3OVcontainment absent','S03 severity/S11 display/S04 page metadata/S08 earlier custom review','3 orphan native class patterns cannot be deleted with exposedAPI']}
(H/'verified.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
