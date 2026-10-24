#!/usr/bin/env python3
"""Verify exported graph, metadata, new reference crosswalk and untouched studies."""
from pathlib import Path
import json,xml.etree.ElementTree as ET,hashlib,csv,collections
H=Path(__file__).resolve().parent
REPO=H.parents[4]
P=REPO/'hardware/eps/rev_b'
b=json.loads((H/'rebuild_blueprint.json').read_text());saved=json.loads((H/'readback.json').read_text());mapping=b['refmap']
def parse(p):
 r=ET.parse(p).getroot()
 return r,{n.get('name'):sorted((x.get('ref'),x.get('pin')) for x in n.findall('node')) for n in r.findall('./nets/net')}
old,on=parse(REPO/'hardware/eps/verification/controller_rev_b/native/controller.xml');new,nn=parse(H/'eps_rev_b.xml')
def name(n):
 if n.startswith('/CAN A and B interfaces/'):return n.replace('/CAN A and B interfaces/','/CAN interfaces/',1)
 if n.startswith('/'):return '/Controller'+n
 if n.startswith('unconnected-'):return n.replace('U1-','U100-',1)
 return n
expected={name(n):sorted((mapping[r],p) for r,p in ep) for n,ep in on.items()}
assert expected==nn,[(n,ep,nn.get(n)) for n,ep in expected.items() if nn.get(n)!=ep]
assert len(nn)==36 and len([n for n in nn if not n.startswith('unconnected-')])==20
oc={c.get('ref'):c for c in old.findall('./components/comp')};nc={c.get('ref'):c for c in new.findall('./components/comp')}
assert len(nc)==27 and {mapping[r] for r in oc}==set(nc)
fields={}
for r,c in oc.items():
 d=nc[mapping[r]]
 for key in ['value','footprint','datasheet']:assert (c.findtext(key) or '')==(d.findtext(key) or ''),(r,key)
 assert c.find('libsource').attrib==d.find('libsource').attrib,r
 cf={x.get('name'):x.text or '' for x in c.findall('./fields/field')};df={x.get('name'):x.text or '' for x in d.findall('./fields/field')}
 assert cf==df,(r,cf,df)
 fields[mapping[r]]=df
for row in saved['crosswalk']:
 assert row['old_uuid']!=row['new_uuid'] and mapping[row['old_reference']]==row['new_reference']
assert len(saved['crosswalk'])==48 and len({x['new_reference'] for x in saved['crosswalk']})==48
hashes=json.loads((H/'historical_source_hashes.json').read_text())
for path,digest in hashes.items():assert hashlib.sha256((REPO/path).read_bytes()).hexdigest()==digest,path
classes=json.loads((P/'eps_rev_b.kicad_pro').read_text())['net_settings']
patterns={p['pattern']:p['netclass'] for p in classes['netclass_patterns']}
assert len(patterns)==20
for cls,names in saved['classes'].items():
 for n in names:assert n in nn and patterns[n]==cls,(n,cls)
for f in ['sym-lib-table','fp-lib-table']:
 s=(P/f).read_text();assert '${KIPRJMOD}/../libraries/' in s and '/Users/' not in s
geometry={}
def directions(p,w):
 x,y=p;a,b,c,d=[round(w[k],4) for k in ['x1','y1','x2','y2']];o=set()
 if b==d==y and min(a,c)<=x<=max(a,c):
  if x>min(a,c):o.add('L')
  if x<max(a,c):o.add('R')
 if a==c==x and min(b,d)<=y<=max(b,d):
  if y>min(b,d):o.add('U')
  if y<max(b,d):o.add('D')
 return o
for sheet,v in saved['readback'].items():
 g=v['layout'];w=g['wires'];points=set()
 for z in w:
  assert z['x1']==z['x2'] or z['y1']==z['y2']
  assert all(abs(z[k]/1.27-round(z[k]/1.27))<1e-6 for k in ['x1','y1','x2','y2'])
  points|={(round(z['x1'],4),round(z['y1'],4)),(round(z['x2'],4),round(z['y2'],4))}
 for a in w:
  for z in w:
   p=(round(a['x1'],4),round(z['y1'],4))
   if a['x1']==a['x2'] and z['y1']==z['y2'] and directions(p,a) and directions(p,z):points.add(p)
 def degree(p):return len(set().union(*(directions(p,z) for z in w)))
 assert not [p for p in points if degree(p)>=4],sheet
 for c in v['pins']['components']:
  for pin in c['pins']:assert degree((round(pin['x'],4),round(pin['y'],4)))<=1,(sheet,c['reference'],pin)
 assert all(l['net'] not in ['GND','+3V3'] for l in g['labels'])
 geometry[sheet]={'HV_on_grid_wire_segments':len(w),'fourway':0,'pins_at_branches':0}
erc=json.loads((H/'erc.json').read_text());vs=[v for s in erc['sheets'] for v in s['violations']]
counts=dict(collections.Counter(v['severity'] for v in vs));types=dict(collections.Counter(v['type'] for v in vs))
assert counts=={'error':18,'warning':3};assert types=={'pin_not_connected':16,'power_pin_not_driven':2,'isolated_pin_label':3}
assert 'four_way_junction' in [x['key'] for x in erc['ignored_checks']]
with (H/'reference_crosswalk.csv').open('w') as f:
 writer=csv.DictWriter(f,fieldnames=saved['crosswalk'][0].keys(),lineterminator='\n');writer.writeheader();writer.writerows(saved['crosswalk'])
with (H/'endpoint_crosswalk.csv').open('w') as f:
 writer=csv.writer(f,lineterminator='\n');writer.writerow(['OldNet','NewNet','MappedEndpoints'])
 for n,ep in on.items():writer.writerow([n,name(n),'; '.join(r+'.'+p for r,p in nn[name(n)])])
(H/'fields_readback.json').write_text(json.dumps(fields,indent=2)+'\n')
result={'status':'CONTROLLER_REBUILD_GRAPH_AND_METADATA_PASS; EPS_INCOMPLETE','physical_parts':27,'crosswalk_entries':48,'mapped_nets':36,'functional_nets':20,'unfinished_pins':16,'erc_counts':counts,'erc_types':types,'geometry':geometry,'classes':saved['classes'],'historical_files_hash_unchanged':len(hashes),'unselected_parts':['J100','J101','J102','R106','R107'],'policy_open':['S03 native severity API unavailable/default ignored','S08 reused custom-symbol review marker unresolved','S11 fields saved but required display unsupported','S04 native root pagination setter absent; root render Id3/3']}
(H/'verified.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
