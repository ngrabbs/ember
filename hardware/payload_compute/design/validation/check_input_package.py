"""Compare MCP readback/instances with the TI RPW0010A physical map.

Read exported evidence only; never parse or mutate protected KiCad sources.
"""
from pathlib import Path
from itertools import combinations
import json
import math

base = Path(__file__).resolve().parent / 'payload_input_acceptance'
raw = json.loads((base/'payload_input_acceptance-package-evidence.json').read_text())
e = {k: json.loads(v['content'][0]['text']) for k,v in raw.items()}
mapping = {
    '1': ('EN/UVLO','input'), '2': ('OVLO','input'),
    '3': ('AUXOFF','open_collector'), '4': ('~{FLT}','open_collector'),
    '5': ('IN','power_in'), '6': ('OUT','power_out'),
    '7': ('DVDT','passive'), '8': ('GND','power_in'),
    '9': ('ILM','passive'), '10': ('ITIMER','passive'),
}
s,f,inst,p = (e[k] for k in ['symbol','footprint','instance','placed_pads'])
assert s['pin_count'] == 10
assert {q['number']:(q['name'],q['type']) for q in s['pins']} == mapping
assert {q['number']:q['name'] for q in e['placed_pins']['pins']} == {k:v[0] for k,v in mapping.items()}
assert inst['lib_id'] == 'EMBER_Payload:TPS259470LRPWR'
assert inst['footprint'] == 'EMBER_Payload:TI_RPW0010A_VQFN-HR-10_2x2mm'
assert not inst['mirror_x'] and not inst['mirror_y'] and inst['rotation']==0
assert len(f['pads']) == p['pad_count'] == 26 and p['source']=='file'
cu = [q for q in f['pads'] if 'F.Cu' in q['layers']]
assert len(cu)==14 and {q['number'] for q in cu}==set(mapping)
assert sum(q['number']=='' for q in f['pads'])==12

# Drawing 4225183/A: top view, 1 upper-left, 5/6 internal power bars.
expected = {
 '1':[(-.9,-.7,.6,.3),(-.725,-.875,.25,.65)],
 '2':[(-.9,-.225,.6,.25)], '3':[(-.9,.225,.6,.25)],
 '4':[(-.9,.7,.6,.3),(-.725,.875,.25,.65)],
 '5':[(-.25,0,.3,2.4)], '6':[(.25,0,.3,2.4)],
 '7':[(.9,.7,.6,.3),(.725,.875,.25,.65)],
 '8':[(.9,.225,.6,.25)], '9':[(.9,-.225,.6,.25)],
 '10':[(.9,-.7,.6,.3),(.725,-.875,.25,.65)],
}
for n,want in expected.items():
    got=[q for q in cu if q['number']==n]
    assert len(got)==len(want)
    for q,(x,y,w,h) in zip(got,want):
        assert all(math.isclose(q[k],v,abs_tol=1e-9) for k,v in zip(['x','y','width','height'],[x,y,w,h]))
for q,placed in zip(f['pads'],p['pads']):
    assert q['type']=='smd' and q['shape']=='roundrect' and q['drill']==[]
    assert math.isclose(min(q['width'],q['height'])*q['roundrect_rratio'],.05)
    assert q['rotation']==0
    assert placed['number']==q['number'] and placed['net']==''
    assert set(placed['layers'])==set(q['layers'])
    assert math.isclose(placed['x'],20+q['x']) and math.isclose(placed['y'],20+q['y'])
    assert set(q['layers']) in ({'F.Cu','F.Mask'}, {'F.Cu','F.Mask','F.Paste'}, {'F.Paste'})

def gap(a,b):
    dx=max(0,abs(a['x']-b['x'])-(a['width']+b['width'])/2)
    dy=max(0,abs(a['y']-b['y'])-(a['height']+b['height'])/2)
    return math.hypot(dx,dy)
min_gap=min(gap(a,b) for a,b in combinations(cu,2) if a['number']!=b['number'])
assert min_gap>=.2-1e-9  # conservative rectangle envelope, excluding deliberate same-lead overlap
paste=[q for q in f['pads'] if 'F.Paste' in q['layers']]
assert len(paste)==16
bars=[q for q in paste if math.isclose(q['width'],.28)]
assert len(bars)==4
assert {(q['x'],q['y'],q['height']) for q in bars}=={(x,y,1.06) for x in [-.25,.25] for y in [-.63,.63]}
assert sum(math.isclose(q['width'],.225) for q in paste)==4
assert sum(math.isclose(q['height'],.275) for q in paste)==4
court=next(g for g in f['graphics'] if g['layer']=='F.CrtYd')
assert court['start']=={'x':-1.65,'y':-1.65} and court['end']=={'x':1.65,'y':1.65}
dot=next(g for g in f['graphics'] if g['type']=='circle' and g['layer']=='F.SilkS')
assert dot['center']=={'x':-1.35,'y':-1.35}
for name in ['payload_input_acceptance-detail.png','payload_input_acceptance-package-detail.png','payload_input_acceptance-paste-detail.png']:
    assert (base/name).stat().st_size>1000
print(json.dumps({'physical_leads_checked':10,'numbered_copper_primitives':14,
                  'intentional_duplicate_copper_primitives':4,'paste_only_primitives':12,
                  'minimum_different_lead_envelope_gap_mm':round(min_gap,6),
                  'result':'PASS for documented package map; unwired fixture'},indent=2))
