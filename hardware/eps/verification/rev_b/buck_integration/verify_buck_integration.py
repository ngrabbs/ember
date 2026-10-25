#!/usr/bin/env python3
"""Compare complete exported integration graph against two reviewed checkpoints."""
from pathlib import Path
import json,xml.etree.ElementTree as ET,hashlib,csv,collections
H=Path(__file__).resolve().parent; REPO=H.parents[4]; P=REPO/'hardware/eps/rev_b'; B=REPO/'hardware/eps/verification/essential_3v3/native'; PREV=H.parent/'integration'
d=json.loads((H/'rebuild_readback.json').read_text());m=d['refmap']
def parse(p):
 r=ET.parse(p).getroot();return r,{n.get('name'):set((x.get('ref'),x.get('pin')) for x in n.findall('node')) for n in r.findall('./nets/net')}
pr,pn=parse(PREV/'eps_rev_b.xml');br,bn=parse(B/'essential_3v3.xml');nr,nn=parse(H/'eps_rev_b.xml')
def name(n):return '/Essential 3V3'+n if n.startswith('/') else n
expected={n:set(ep) for n,ep in pn.items()};mapped={name(n):{(m[r],p) for r,p in ep} for n,ep in bn.items()}
for n,ep in mapped.items():expected.setdefault(n,set()).update(ep)
assert expected==nn,{n:(sorted(ep),sorted(nn.get(n,set()))) for n,ep in expected.items() if ep!=nn.get(n)}
assert len(nn)==40 and len([n for n in nn if not n.startswith('unconnected-')])==24
# Every controller endpoint survives; buck only adds nodes to the common power/return.
for n,ep in pn.items():assert ep<=nn[n] and (n in ['+3V3','GND'] or ep==nn[n]),n
assert {n for n in pn if pn[n]!=nn[n]}=={'+3V3','GND'}
assert len(bn)==6
comps={c.get('ref'):c for c in nr.findall('./components/comp')};assert len(comps)==43
fields={}
for oldroot,remap in [(pr,lambda r:r),(br,lambda r:m[r])]:
 for c in oldroot.findall('./components/comp'):
  r=remap(c.get('ref'));new=comps[r]
  for k in ['value','footprint','datasheet']:assert (c.findtext(k) or '')==(new.findtext(k) or ''),(r,k)
  assert c.find('libsource').attrib==new.find('libsource').attrib,r
  cf={x.get('name'):x.text or '' for x in c.findall('./fields/field')};nf={x.get('name'):x.text or '' for x in new.findall('./fields/field')};assert cf==nf,r
  fields[r]=nf
assert len(d['crosswalk'])==24 and len({x['new_reference'] for x in d['crosswalk']})==24
assert len([x for x in d['crosswalk'] if x['physical']])==16
assert all(x['old_uuid']!=x['new_uuid'] for x in d['crosswalk'])
# Existing controller identities, geometry and pin maps are not reannotated.
prior=json.loads((PREV/'readback.json').read_text())
for v in prior['readback'].values():
 for ref,c in v['components'].items():
  uuid=c['uuid'];new=comps.get(ref)
  if new is not None:assert uuid in [x.text for x in new.findall('./tstamps')][0].split(),ref
sym,fp,lfp=d['packages'];assert {p['number']:p['name'] for p in sym['pins']}=={'1':'FB','2':'EN','3':'VIN','4':'GND','5':'SW','6':'CB'}
assert len(fp['pads'])==6
coords={'1':(-1.35,-.95),'2':(-1.35,0),'3':(-1.35,.95),'4':(1.35,.95),'5':(1.35,0),'6':(1.35,-.95)}
for p in fp['pads']:assert (p['x'],p['y'])==coords[p['number']] and p['width']==1.1 and p['height']==.6 and p['drill']==[] and p['type']=='smd'
assert [(p['number'],p['x'],p['y'],p['width'],p['height']) for p in lfp['pads']]==[('1',-2.02,0.0,1.43,5.5),('2',2.02,0.0,1.43,5.5)]
# Reuse the previous independently checked direction function for current buck geometry.
def directions(p,w):
 x,y=p;a,b,c,e=[round(w[k],4) for k in ['x1','y1','x2','y2']];o=set()
 if b==e==y and min(a,c)<=x<=max(a,c):
  if x>min(a,c):o.add('L')
  if x<max(a,c):o.add('R')
 if a==c==x and min(b,e)<=y<=max(b,e):
  if y>min(b,e):o.add('U')
  if y<max(b,e):o.add('D')
 return o
w=d['geometry']['wires'];points=set()
for z in w:
 assert z['x1']==z['x2'] or z['y1']==z['y2']
 assert all(abs(z[k]/1.27-round(z[k]/1.27))<1e-6 for k in ['x1','y1','x2','y2'])
 points|={(round(z['x1'],4),round(z['y1'],4)),(round(z['x2'],4),round(z['y2'],4))}
for a in w:
 for z in w:
  p=(round(a['x1'],4),round(z['y1'],4))
  if a['x1']==a['x2'] and z['y1']==z['y2'] and directions(p,a) and directions(p,z):points.add(p)
def deg(p):return len(set().union(*(directions(p,z) for z in w)))
assert len(w)==51 and all(deg(p)<4 for p in points)
for c in d['pins']['components']:
 for p in c['pins']:assert deg((round(p['x'],4),round(p['y'],4)))<=1,(c['reference'],p['number'])
assert not [l for l in d['geometry']['labels'] if l['net'] in ['SYS_PWR_PERMITTED','GND','+3V3']]
classes=json.loads((P/'eps_rev_b.kicad_pro').read_text())['net_settings'];patterns={x['pattern']:x['netclass'] for x in classes['netclass_patterns']}
intent={k:list(v) for k,v in prior['classes'].items()}
for k,v in d['newclasses'].items():intent.setdefault(k,[]).extend(v)
assert len(patterns)==24
for cls,names in intent.items():
 for n in names:assert n in nn and patterns[n]==cls,(n,cls)
for f in ['sym-lib-table','fp-lib-table']:
 s=(P/f).read_text();assert '${KIPRJMOD}/../libraries/Ember_EPS_Power' in s and '/Users/' not in s
hashes=json.loads((H/'historical_source_hashes.json').read_text())
for f,v in hashes.items():assert hashlib.sha256((REPO/f).read_bytes()).hexdigest()==v,f
# Previous 27-part evidence remains immutable.
oldhash=json.loads((PREV/'evidence_sha256.json').read_text())
for f,v in oldhash.items():assert hashlib.sha256((PREV/f).read_bytes()).hexdigest()==v,f
erc=json.loads((H/'erc.json').read_text());vs=[v for s in erc['sheets'] for v in s['violations']];counts=dict(collections.Counter(v['severity'] for v in vs));types=dict(collections.Counter(v['type'] for v in vs));assert counts=={'error':16,'warning':3};assert types=={'pin_not_connected':16,'isolated_pin_label':3}
assert 'four_way_junction' in [x['key'] for x in erc['ignored_checks']]
combined=prior['crosswalk']+d['crosswalk']
with (H/'reference_crosswalk.csv').open('w') as f:
 writer=csv.DictWriter(f,fieldnames=combined[0].keys(),lineterminator='\n');writer.writeheader();writer.writerows(combined)
with (H/'buck_endpoint_crosswalk.csv').open('w') as f:
 writer=csv.writer(f,lineterminator='\n');writer.writerow(['OldBuckNet','NewRootNet','MappedBuckEndpoints','CompleteRootEndpoints'])
 for n,ep in bn.items():writer.writerow([n,name(n),'; '.join(r+'.'+p for r,p in sorted(mapped[name(n)])),'; '.join(r+'.'+p for r,p in sorted(nn[name(n)]))])
(H/'fields_readback.json').write_text(json.dumps(fields,indent=2)+'\n')
result={'status':'COMBINED_GRAPH_METADATA_PASS; ESSENTIAL_POWER_ACCEPTANCE_OPEN','commit_basis':'d8d5580','physical_parts':43,'new_buck_parts':16,'mapped_buck_nets':6,'complete_root_nets':40,'functional_nets':24,'old_controller_endpoint_sets_preserved':36,'changed_controller_nets_only_added_buck_nodes':['+3V3','GND'],'crosswalk_entries':len(combined),'new_buck_crosswalk_entries':24,'erc_counts':counts,'erc_types':types,'buck_geometry':{'HV_on_grid_wires':51,'fourway':0,'pins_at_branches':0},'historical_files_unchanged':len(hashes),'previous_evidence_files_unchanged':len(oldhash),'netclass_members':24,'source_fixture_flags':['#FLG0400 external SYS_PWR_PERMITTED','#FLG0401 external GND'],'actual_buck_output_flag':'#FLG0402 after L400','open':['external source/interlock/charger/BMS not drawn','weak-source UVLO/chatter','autonomous3V3outputOVcontainment absent','actual MCU/IHU/CAN dynamic load/thermal/effective-C/loop qualification','S03severityAPI/S08existingcustomreview/S11display/S04pagination']}
(H/'verified.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
