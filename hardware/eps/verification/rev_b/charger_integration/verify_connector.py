#!/usr/bin/env python3
"""Read-only accepted stock JST GH fixture map, preserving both MP objects."""
from pathlib import Path
from collections import Counter
import csv,hashlib,json,re,xml.etree.ElementTree as E
H=Path(__file__).resolve().parent;d=json.loads((H/'connector_readback.json').read_text())
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
def children(n,k):return [v for v in n if isinstance(v,list) and v and v[0]==k]
def child(n,k):
    a=children(n,k);assert len(a)==1,(k,len(a));return a[0]
native=parse((H/'parts_disposable/charger_parts_check.kicad_pcb').read_text())
fps=children(native,'footprint');assert len(fps)==1
fp=fps[0];assert fp[1]=='Connector_JST:JST_GH_BM02B-GHS-TBT_1x02-1MP_P1.25mm_Vertical'
assert child(fp,'at')[1:]==['25','25'] and child(fp,'layer')[1]=='F.Cu'
raw=children(fp,'pad');assert len(raw)==4
expected=[('1',-.625,1.95,.6,1.7),('2',.625,1.95,.6,1.7),('MP',-2.475,-1.4,1,2.8),('MP',2.475,-1.4,1,2.8)]
saved=[]
for p in raw:
    at=child(p,'at');size=child(p,'size');rr=child(p,'roundrect_rratio')
    assert p[2:4]==['smd','roundrect'] and not children(p,'drill')
    assert set(child(p,'layers')[1:])=={'F.Cu','F.Mask','F.Paste'} and float(rr[1])==.25
    assert len(at)==3 or float(at[3])==0
    saved.append((p[1],float(at[1]),float(at[2]),float(size[1]),float(size[2])))
assert Counter(saved)==Counter(expected)
library=d['library']['pads'];assert len(library)==d['library']['pad_count']==4
assert Counter(p['number'] for p in library)=={'1':1,'2':1,'MP':2}
for z,e in zip(library,expected):
    assert z['number']==e[0] and all(abs(z[k]-v)<1e-7 for k,v in zip(['x','y','width','height'],e[1:]))
    assert not z['drill'] and z['type']=='smd' and set(z['layers'])=={'F.Cu','F.Mask','F.Paste'}
for k in ['pads','after_save']:
    assert len(d[k]['pads'])==d[k]['pad_count']==4 and d[k]['source']=='ipc'
    sig=Counter((z['number'],round(z['x']-25,5),round(z['y']-25,5)) for z in d[k]['pads'])
    assert sig==Counter((n,x,y) for n,x,y,w,h in expected)
    assert all(z['net']=='' for z in d[k]['pads'])
assert d['symbol']['pin_count']==2 and {p['number'] for p in d['symbol']['pins']}=={'1','2'}
assert len(d['instance_pins']['pins'])==2 and d['instance']['value']=='BM02B-GHS-TBT(LF)(SN)'
props={p[1]:p[2] for p in children(fp,'property')};assert props['Reference']=='J1' and props['Value']=='BM02B-GHS-TBT(LF)(SN)'
x=E.parse(H/'connector_fixture.xml').getroot();assert len(x.findall('./components/comp'))==1
sets=[{(p.get('ref'),p.get('pin')) for p in n.findall('node')} for n in x.findall('./nets/net')]
assert len(sets)==2 and {frozenset(s) for s in sets}=={frozenset({('J1','1')}),frozenset({('J1','2')})}
erc=json.loads((H/'connector_fixture_erc.json').read_text());v=[v for s in erc['sheets'] for v in s['violations']]
assert Counter((z['severity'],z['type']) for z in v)=={('error','pin_not_connected'):2}
with (H/'connector_physical_map.csv').open('w') as f:
    w=csv.writer(f,lineterminator='\n');w.writerow(['physical_lead','function','symbol_pin','footprint_pad','x_mm','y_mm','width_mm','height_mm','view','disposition'])
    for n,x,y,a,b in expected:w.writerow([n,{'1':'CHG NTC','2':'Quiet system GND','MP':'Mechanical retention'}[n],n if n!='MP' else 'none',n,x,y,a,b,'JST mounting front view rotated180deg; pin1 left/bottom','stock longer signal toe; temperature/assembly open' if n!='MP' else 'floating mechanical; duplicate MP intentional'])
result={'status':'DEVELOPMENT STOCK CONNECTOR MAP PASS; ASSEMBLY/TEMPERATURE OPEN','exact_MPN':'BM02B-GHS-TBT(LF)(SN)','physical_contacts':2,'symbol_pins':2,'raw_pads':4,'MP_mechanical_objects':2,'unique_electrical_numbers':['1','2'],'stock_signal_land_mm':[.6,1.7],'JST_reference_signal_land_mm':[.6,1.35],'reference_height_tolerance_mm':.1,'stock_toe_deviation_mm':.35,'normalization':'front mounting view rotated180deg; no pin-number swap','temperature':'US -25..85C and current JP -40..105C discrepancy; -40 screening not accepted','saved_board_sha256':hashlib.sha256((H/'parts_disposable/charger_parts_check.kicad_pcb').read_bytes()).hexdigest(),'actual_images_inspected':['connector_symbol.png','connector_symbol_detail.png','connector_render/copper.png','connector_render/fab.png'],'fab_label_limit':'Tiny pad1/2 and MP strokes overlap fab/body outlines; numeric readback corroborates'}
(H/'connector_verified.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
