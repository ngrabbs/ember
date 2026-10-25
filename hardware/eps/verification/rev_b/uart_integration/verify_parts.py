#!/usr/bin/env python3
"""Saved library/schematic/live-and-saved disposable pad acceptance."""
from check_common import *
from collections import Counter
import csv
D=json.loads((H/'parts_readback.json').read_text())
expected={'U1':{'1':'1A','2':'GND','3':'2A','4':'2Y','5':'VCC','6':'1Y'},'J1':{'1':'GND','2':'EPS_TX','3':'EPS_RX'}}
positions={'U1':(35,35),'J1':(55,35)}
mpns={'U1':'74LVC2G34GW,125','J1':'BM03B-GHS-TBT(LF)(SN)'}
board=parse((H/'parts_disposable/uart_parts_check.kicad_pcb').read_text());fps=kids(board,'footprint')
refs=[props(f)['Reference'] for f in fps];assert len(refs)==len(set(refs))==2 and set(refs)==set(expected)
sch=parse((H/'parts_disposable/uart_parts_check.kicad_sch').read_text());syms=kids(sch,'symbol')
assert Counter(props(s)['Reference'] for s in syms)=={'U1':3,'J1':1}
assert {int(one(s,'unit')[1]) for s in syms if props(s)['Reference']=='U1'}=={1,2,3}
assert Counter(p['number'] for c in D['schematic_pins']['components'] for p in c['pins'])==Counter({'1':2,'2':2,'3':2,'4':1,'5':1,'6':1})
rows=[]
for ref,funcs in expected.items():
    lib=D['footprints'][ref];api=D['after_save'][ref];sp=D['symbols'][ref]['pins']
    assert len(sp)==len(funcs) and {p['number'] for p in sp}==set(funcs)
    if ref=='U1':assert {p['number']:p['type'] for p in sp}=={'1':'input','2':'power_in','3':'input','4':'output','5':'power_in','6':'output'}
    for s in syms:
        if props(s)['Reference']==ref:assert props(s)['Value']==props(s)['MFG P/N']==mpns[ref] and props(s)['Footprint']
    f=fps[refs.index(ref)];pads=kids(f,'pad');n=6 if ref=='U1' else 5
    assert len(pads)==len(lib['pads'])==lib['pad_count']==len(api['pads'])==api['pad_count']==n
    counter=Counter(funcs.keys())
    if ref=='J1':counter['MP']=2
    assert Counter(p[1] for p in pads)==Counter(p['number'] for p in lib['pads'])==Counter(p['number'] for p in api['pads'])==counter
    assert api['source']=='ipc' and all(p['net']=='' for p in api['pads'])
    assert tuple(map(float,one(f,'at')[1:3]))==positions[ref]
    for p,l,a in zip(pads,lib['pads'],api['pads']):
        assert p[1]==l['number']==a['number'];xy=tuple(map(float,one(p,'at')[1:3]));size=tuple(map(float,one(p,'size')[1:3]))
        assert all(abs(x-y)<2e-6 for x,y in zip(xy,(l['x'],l['y'])))
        assert all(abs(x-y)<2e-6 for x,y in zip(size,(l['width'],l['height'])))
        assert p[2:4]==[l['type'],l['shape']] and not kids(p,'drill') and l['drill']==[]
        assert set(one(p,'layers')[1:])==set(l['layers'])==set(a['layers'])=={'F.Cu','F.Mask','F.Paste'}
        assert abs(float(one(p,'roundrect_rratio')[1])-l['roundrect_rratio'])<1e-9
        assert abs(a['x']-positions[ref][0]-xy[0])<2e-6 and abs(a['y']-positions[ref][1]-xy[1])<2e-6
        rows.append({'reference':ref,'MPN':mpns[ref],'physical_lead':p[1],'function':funcs.get(p[1],'mechanical retention only; no symbol/net'),'symbol_pin':p[1] if p[1]!='MP' else 'intentionally absent','footprint_pad':p[1],'x_mm':xy[0],'y_mm':xy[1],'view':('Nexperia Rev13 p3 top view; p8 outline normalized90deg clockwise; pin1 upper-left' if ref=='U1' else 'JST eGH pp2-3 mounting surface; normalized180deg; pin1 lower-left; housing mating identity retained')})
assert len(rows)==11
with (H/'parts_physical_map.csv').open('w') as f:
    w=csv.DictWriter(f,fieldnames=rows[0],lineterminator='\n');w.writeheader();w.writerows(rows)
result={'status':'DEVELOPMENT PHYSICAL MAP PASS; STOCK LANDS AND ASSEMBLY QUALIFICATION OPEN','parts':mpns,'raw_pad_objects':11,'electrical_pins':9,'mechanical_MP_objects':2,'source_sha256':{str(p.relative_to(H)):sha(p) for p in (H/'parts_disposable').iterdir() if p.suffix in {'.kicad_sch','.kicad_pcb','.kicad_pro'}},'render_limits':['stock power-unit Reference/Value crosses pin strokes; supported field reset is no-op','numbered fab text overlaps body strokes; numeric pad map checked independently']}
(H/'parts_verified.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
