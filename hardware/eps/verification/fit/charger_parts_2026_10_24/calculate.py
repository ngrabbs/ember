"""Read-only footprint courtyard budget; no CAD mutation or fit claim."""
from pathlib import Path
from collections import Counter
import csv, hashlib, json, xml.etree.ElementTree as ET
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
SOURCE=HERE/'eps_rev_b_at_charger.xml'
xml=SOURCE.read_bytes()
r=ET.fromstring(xml)
comps=r.findall('./components/comp')
refs=[c.attrib['ref'] for c in comps]
assert len(refs)==len(set(refs))==187
counts=Counter(c.findtext('footprint','') for c in comps)
missing=[c.attrib['ref'] for c in comps if not c.findtext('footprint','')]
readbacks=json.loads((HERE/'footprint_readback.json').read_text())['readbacks']
assert len({x['id'] for x in readbacks})==len(readbacks)
info={x['id']:x['info'] for x in readbacks}
assert set(counts)-{''}==set(info)
rows=[]
for ident,num in counts.items():
    if not ident:continue
    points=[]
    for g in info[ident]['graphics']:
        if g['layer']!='F.CrtYd':continue
        if g['type'] in ('rect','line'):
            points.extend((g['start'],g['end']))
        elif g['type']=='circle':
            c=g['center'];radius=g['radius_mm']
            points.extend([{'x':c['x']-radius,'y':c['y']-radius},
                           {'x':c['x']+radius,'y':c['y']+radius}])
        elif g['type']=='poly':points.extend(g['points'])
        else:raise AssertionError((ident,g['type']))
    assert points,ident
    w=max(q['x'] for q in points)-min(q['x'] for q in points)
    h=max(q['y'] for q in points)-min(q['y'] for q in points)
    rows.append(dict(footprint=ident,count=num,width_mm=w,height_mm=h,
                     rectangle_mm2=w*h,extended_mm2=num*w*h))
rows.sort(key=lambda x:-x['extended_mm2'])
area=sum(x['extended_mm2'] for x in rows)
assert sum(x['count'] for x in rows)==182 and len(missing)==5
source_hashes={ident:hashlib.sha256(Path(x['path']).read_bytes()).hexdigest() for ident,x in info.items()}
result=dict(physical_parts=len(comps),unique_references=len(set(refs)),
 assigned_footprints=182,missing_footprints=missing,assigned_types=len(info),
 courtyard_centerline_rectangle_sum_mm2=area,illustrative_board_rectangle_mm2=96*90,
 illustrative_fraction=area/(96*90),input_netlist_sha256=hashlib.sha256(xml).hexdigest(),
 footprint_source_sha256=source_hashes,
 scope='Current 187 parts only; no placement/routing/thermal/mechanical/full-EPS fit acceptance',rows=rows)
(HERE/'results.json').write_text(json.dumps(result,indent=2)+'\n')
with (HERE/'courtyards.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
print(json.dumps({k:v for k,v in result.items() if k not in ('rows','footprint_source_sha256')},indent=2))
