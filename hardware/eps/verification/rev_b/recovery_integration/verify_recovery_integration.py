#!/usr/bin/env python3
"""Verify converter integration against current bank and previous combined graph."""
from pathlib import Path
import json,xml.etree.ElementTree as ET,hashlib,csv,collections
H=Path(__file__).resolve().parent;REPO=H.parents[4];P=REPO/'hardware/eps/rev_b';PREV=H.parent/'buck_integration';FIRST=H.parent/'integration';BANK=REPO/'hardware/eps/verification/protection/bank/native'
d=json.loads((H/'rebuild_readback.json').read_text());m=d['refmap']
def parse(p):
 r=ET.parse(p).getroot();return r,{n.get('name'):set((x.get('ref'),x.get('pin')) for x in n.findall('node')) for n in r.findall('./nets/net')}
old,on=parse(PREV/'eps_rev_b.xml');source,sn=parse(H/'source_current.xml');authority,an=parse(BANK/'after.xml');new,nn=parse(H/'eps_rev_b.xml')
assert sn==an and len(sn)==19 and len([n for n in sn if not n.startswith('unconnected-')])==16
# Fresh source physical records match the current 34-part bank authority, not older study exports.
sc={c.get('ref'):c for c in source.findall('./components/comp')};ac={c.get('ref'):c for c in authority.findall('./components/comp')}
assert len(sc)==34 and set(sc)==set(ac)
for r,c in sc.items():assert ET.tostring(c)==ET.tostring(ac[r]),r
def name(n):
 if n=='+5V':return '5V0_RECOVERY_REG'
 if n.startswith('/'):return '/Recovery 5V converter'+n
 if n.startswith('unconnected-'):return n.replace('U1-','U500-',1)
 return n
mapped={name(n):{(m[r],p) for r,p in ep} for n,ep in sn.items()}
expected={n:set(ep) for n,ep in on.items()}
for n,ep in mapped.items():expected.setdefault(n,set()).update(ep)
assert nn==expected,[(n,sorted(ep),sorted(nn.get(n,set()))) for n,ep in expected.items() if nn.get(n)!=ep]
assert len(nn)==56 and len([n for n in nn if not n.startswith('unconnected-')])==37
assert '+5V' not in nn
assert nn['5V0_RECOVERY_REG']=={('R503','2'),('R504','1'),('U500','13')}
assert len(nn['5V0_RECOVERY_RAW'])==17
for n,ep in on.items():assert ep<=nn[n] and (n in ['+3V3','GND','SYS_PWR_PERMITTED'] or ep==nn[n]),n
assert {n for n in on if on[n]!=nn[n]}=={'+3V3','GND','SYS_PWR_PERMITTED'}
comps={c.get('ref'):c for c in new.findall('./components/comp')};assert len(comps)==77
fields={};priorrefs=[]
for r,c in {c.get('ref'):c for c in old.findall('./components/comp')}.items():
 now=comps[r];assert c.findtext('tstamps')==now.findtext('tstamps'),r;priorrefs.append(r)
for root,remap in [(old,lambda r:r),(source,lambda r:m[r])]:
 for c in root.findall('./components/comp'):
  r=remap(c.get('ref'));now=comps[r]
  for k in ['value','footprint','datasheet']:assert (c.findtext(k) or '')==(now.findtext(k) or ''),(r,k)
  assert c.find('libsource').attrib==now.find('libsource').attrib,r
  cf={x.get('name'):x.text or '' for x in c.findall('./fields/field')};nf={x.get('name'):x.text or '' for x in now.findall('./fields/field')};assert cf==nf,r;fields[r]=nf
assert len(priorrefs)==43
assert {n:ep for n,ep in mapped.items() if n.startswith('unconnected-')}=={'unconnected-(U500-CC-Pad4)':{('U500','4')},'unconnected-(U500-CDC-Pad16)':{('U500','16')},'unconnected-(U500-EXTVCC-Pad21)':{('U500','21')}}
bank_old=[f'C{i}' for i in [9,10,11,12,13,14,15,19,20,21,22,23,24]]
for r in bank_old:
 n=m[r];assert fields[n]['Voltage']=='50 V' and (n,'1') in nn['5V0_RECOVERY_RAW'] and (n,'2') in nn['GND']
assert fields['C515']['Voltage']=='50 V' and comps['C515'].findtext('value')=='100n'
assert len(d['crosswalk'])==75 and len(d['components'])==71
assert set(d['omitted'])=={'#FLG01','#FLG02','#FLG04','#PWR001'}
assert [c['reference'] for c in d['components'].values() if c['lib_id']=='power:PWR_FLAG']==['#FLG0502']
for row in d['crosswalk']:
 if row['new_reference']:assert row['new_uuid']!=row['old_uuid']
 else:assert row['old_reference'] in d['omitted'] and row['reason']
assert len(d['removed_fixture_wires'])==3
# Compare the exact accepted manufacturer pin/pad map, including composite pad9.
sym=d['packages']['symbol'];fp=d['packages']['ic'];bulk=d['packages']['bulk']
functions={'1':'EN/UVLO','2':'MODE','3':'PG','4':'CC','5':'DITH/SYNC','6':'FSW','7':'VIN','8':'SW1','9':'PGND','10':'SW2','11':'VOUT','12':'ISP','13':'ISN','14':'FB','15':'COMP','16':'CDC','17':'AGND','18':'VCC','19':'BOOT2','20':'BOOT1','21':'EXTVCC'}
assert {p['number']:p['name'] for p in sym['pins']}==functions
assert len(fp['pads'])==23 and set(p['number'] for p in fp['pads'])==set(functions)
assert all(p['type']=='smd' and not p['drill'] for p in fp['pads'])
with (REPO/'hardware/eps/studies/recovery_5v/physical_pin_map.csv').open() as f:rows=list(csv.DictReader(f))
def querykey(p):return (p['number'],p['x'],p['y'],p['width'],p['height'])
assert collections.Counter(querykey(p) for p in fp['pads'])==collections.Counter((r['Physical lead / pad'],float(r['X mm']),float(r['Y mm (front view, down positive)']),float(r['Width mm']),float(r['Height mm'])) for r in rows)
assert len(bulk['pads'])==2 and {p['number'] for p in bulk['pads']}=={'1','2'}
# Geometry separates unconnected crossings from prohibited joined four-way nodes.
def directions(p,w):
 x,y=p;a,b,c,e=[round(w[k],4) for k in ['x1','y1','x2','y2']];out=set()
 if b==e==y and min(a,c)<=x<=max(a,c):
  if x>min(a,c):out.add('L')
  if x<max(a,c):out.add('R')
 if a==c==x and min(b,e)<=y<=max(b,e):
  if y>min(b,e):out.add('U')
  if y<max(b,e):out.add('D')
 return out
w=d['geometry']['wires'];points=set();endpoints=set()
for z in w:
 assert z['x1']==z['x2'] or z['y1']==z['y2']
 assert all(abs(z[k]/1.27-round(z[k]/1.27))<1e-6 for k in ['x1','y1','x2','y2'])
 endpoints|={(round(z['x1'],4),round(z['y1'],4)),(round(z['x2'],4),round(z['y2'],4))}
for a in w:
 for z in w:
  p=(round(a['x1'],4),round(z['y1'],4))
  if a['x1']==a['x2'] and z['y1']==z['y2'] and directions(p,a) and directions(p,z):points.add(p)
def deg(p):return len(set().union(*(directions(p,z) for z in w)))
annotation=json.loads((H/'annotation_geometry.json').read_text());junctions={tuple(round(v,4) for v in p) for p in annotation['junctions']};crossings={p for p in points if deg(p)==4}
assert len(w)==124 and len(crossings)==7
assert not crossings & (junctions|endpoints),crossings & (junctions|endpoints)
for c in d['pins']['components']:
 for p in c['pins']:assert deg((round(p['x'],4),round(p['y'],4)))<=1,(c['reference'],p['number'])
assert len(annotation['no_connects'])==3
assert all(l['net'] not in ['GND','+3V3','+5V','5V0_RECOVERY_RAW','5V0_RECOVERY_REG','SYS_PWR_PERMITTED'] for l in d['geometry']['labels'])
classes=json.loads((P/'eps_rev_b.kicad_pro').read_text())['net_settings'];patterns={x['pattern']:x['netclass'] for x in classes['netclass_patterns']}
assert len(patterns)==37
priorclasses=json.loads((FIRST/'readback.json').read_text())['classes']
buckclasses=json.loads((PREV/'rebuild_readback.json').read_text())['newclasses']
for group in [priorclasses,buckclasses,d['classes']]:
 for cls,names in group.items():
  for n in names:assert n in nn and patterns[n]==cls,(n,cls)
assert set(patterns)=={n for n in nn if not n.startswith('unconnected-')}
for f in ['sym-lib-table','fp-lib-table']:
 s=(P/f).read_text();assert '${KIPRJMOD}/../libraries/Ember_EPS_Recovery' in s and '/Users/' not in s
hashes=json.loads((H/'historical_source_hashes.json').read_text())
for f,digest in hashes.items():assert hashlib.sha256((REPO/f).read_bytes()).hexdigest()==digest,f
old_evidence=0
for folder in [FIRST,PREV]:
 for f,digest in json.loads((folder/'evidence_sha256.json').read_text()).items():assert hashlib.sha256((folder/f).read_bytes()).hexdigest()==digest,(folder,f);old_evidence+=1
erc=json.loads((H/'erc.json').read_text());vs=[v for s in erc['sheets'] for v in s['violations']];counts=dict(collections.Counter(v['severity'] for v in vs));types=dict(collections.Counter(v['type'] for v in vs));assert counts=={'error':16,'warning':3};assert types=={'pin_not_connected':16,'isolated_pin_label':3}
assert 'four_way_junction' in [x['key'] for x in erc['ignored_checks']]
with (PREV/'reference_crosswalk.csv').open() as f:previous=list(csv.DictReader(f))
allrows=[dict(x,disposition='earlier checkpoint',reason='') for x in previous]+d['crosswalk']
with (H/'reference_crosswalk.csv').open('w') as f:
 writer=csv.DictWriter(f,fieldnames=list(d['crosswalk'][0]),lineterminator='\n');writer.writeheader();writer.writerows(allrows)
with (H/'converter_endpoint_crosswalk.csv').open('w') as f:
 writer=csv.writer(f,lineterminator='\n');writer.writerow(['SourceNet','IntegratedNet','MappedConverterEndpoints','FullRootEndpoints'])
 for n,ep in sn.items():writer.writerow([n,name(n),'; '.join(r+'.'+p for r,p in sorted(mapped[name(n)])),'; '.join(r+'.'+p for r,p in sorted(nn[name(n)]))])
(H/'fields_readback.json').write_text(json.dumps(fields,indent=2)+'\n')
result={'status':'COMBINED_GRAPH_METADATA_PASS; POWER_PROTECTION_AND_QUALIFICATION_OPEN','commit_basis':'96702c3','source_authority':'protection/bank/native/after.xml, fresh current study matches','physical_parts':77,'new_converter_parts':34,'converter_functional_sets':16,'converter_intentional_NC_sets':3,'root_nets':56,'functional_nets':37,'previous_43_UUIDs_preserved':True,'previous_endpoint_sets_preserved':40,'shared_nets_only_add_expected_converter_nodes':['+3V3','GND','SYS_PWR_PERMITTED'],'postshunt_translation':'+5V ->5V0_RECOVERY_REG at R503.2/R504.1/U500.13','shared_+5V_bypass_present':False,'crosswalk_rows':len(allrows),'retained_unique_native_instances':143,'omitted_redundant_fixtures':d['omitted'],'erc_counts':counts,'erc_types':types,'converter_geometry':{'orthogonal_on_grid_wires':124,'connected_fourway':0,'unconnected_crossings':sorted(crossings),'pins_at_branches':0},'netclass_members':37,'historical_files_unchanged':len(hashes),'previous_evidence_files_unchanged':old_evidence,'shared_input_nominal_uF':102.6,'converter_output_bank_nominal_uF_plus_bypass':420.1,'converter_output_high_endurance_tolerance_uF_excluding_bypass':618.4,'C515_bypass_nominal_uF':0.1,'output_development_allocation_uF':650,'qualified_combined_startup':False}
(H/'verified.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
