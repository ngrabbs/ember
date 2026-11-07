#!/usr/bin/env python3
"""Scoped read-only native/package checks; writes only ordinary evidence."""
from pathlib import Path
from collections import Counter
import csv, hashlib, json, re, subprocess, xml.etree.ElementTree as ET

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
RB=json.loads((HERE/'readback.json').read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
near=lambda a,b:abs(float(a)-float(b))<1e-6

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
    assert not stack
    return root
def children(n,k):return [v for v in n if isinstance(v,list) and v and v[0]==k]
def child(n,k):
    a=children(n,k);assert len(a)==1,(k,len(a));return a[0]

native=parse((HERE/'disposable/powerpath_check.kicad_pcb').read_text())
fps=children(native,'footprint');assert len(fps)==1
fp=fps[0];props={v[1]:v[2] for v in children(fp,'property')}
assert props['Reference']=='Q1' and props['Value']=='CSD18543Q3A'
assert fp[1]=='Ember_Charger_BMS_Review:TI_CSD18543Q3A_Q3A_Manufacturer'
assert child(fp,'layer')[1]=='F.Cu' and child(fp,'at')[1:]==['25','25']
saved=[]
for p in children(fp,'pad'):
    at=child(p,'at');size=child(p,'size');rr=child(p,'roundrect_rratio')
    saved.append({'number':p[1],'type':p[2],'shape':p[3],'x':float(at[1]),'y':float(at[2]),'rotation':float(at[3]) if len(at)>3 else 0,'width':float(size[1]),'height':float(size[2]),'layers':child(p,'layers')[1:],'drill':children(p,'drill'),'roundrect_rratio':float(rr[1])})
assert all(not children(native,k) for k in ('segment','via','zone','gr_line','gr_rect','gr_poly','gr_arc','gr_text'))

# Expected objects are derived from the approved TI physical table, preserving
# raw multiplicity. Never use a number→pad dictionary for these aliases/windows.
copper=[(str(i+1),-1.55,-.975+.65*i,.6,.3) for i in range(4)]
copper += [('5',1.4825,.975-.65*i,.735,.3) for i in range(4)]
copper += [('5',.3275,0,1.775,2.45)]
expected=[]
for num,x,y,w,h in copper:expected.append((num,('F.Cu','F.Mask'),x,y,w,h,.05))
for x in (-1.55,1.55):
    for y in (-.975,-.325,.325,.975):expected.append(('',('F.Paste',),x,y,.6,.3,.05))
for x in (-.2075,.6975):
    for y in (-.6625,.6625):expected.append(('',('F.Paste',),x,y,.705,1.125,.05))
for num,x,y,w,h in copper:expected.append(('',('F.Mask',),x,y,w+.1,h+.1,.1))
def sign(p):
    assert p['type']=='smd' and p['shape']=='roundrect' and not p['drill'] and p['rotation']==0
    return (p['number'],tuple(sorted(p['layers'])),*[round(float(p[k]),6) for k in ('x','y','width','height')],round(p['roundrect_rratio']*min(p['width'],p['height']),6))
ex=Counter((n,tuple(sorted(l)),*[round(v,6) for v in (x,y,w,h,r)]) for n,l,x,y,w,h,r in expected)
library=RB['library']['pads']
assert RB['library']['pad_count']==len(library)==len(saved)==len(expected)==30
assert Counter(map(sign,library))==Counter(map(sign,saved))==ex
cu=[p for p in saved if 'F.Cu' in p['layers']]
paste=[p for p in saved if p['layers']==['F.Paste']]
mask=[p for p in saved if p['layers']==['F.Mask']]
assert len(cu)==9 and len(paste)==12 and len(mask)==9
assert Counter(p['number'] for p in cu)=={'1':1,'2':1,'3':1,'4':1,'5':5}
assert all(p['number']=='' for p in paste+mask)
live=RB['live'];assert live['source']=='ipc' and live['pad_count']==len(live['pads'])==30
live_sig=lambda p:(p['number'],tuple(sorted(p['layers'])),round(p['x']-25,6),round(p['y']-25,6))
assert Counter(map(live_sig,live['pads']))==Counter((n,tuple(sorted(l)),round(x,6),round(y,6)) for n,l,x,y,w,h,r in expected)
assert all(p['net']=='' for p in live['pads'])
assert RB['open']['requested_open'] is True and RB['open']['open_boards']==[RB['board']]
assert RB['component']['x']==RB['component']['y']==25 and RB['component']['rotation']==0

# Nonempty full-height overlap proves each rounded finger connects to the
# central drain. Internal concave fillets intentionally remain a deviation.
central=copper[-1];right=central[1]+central[3]/2
overlap=[]
for num,x,y,w,h in copper[4:8]:
    nominal=right-(x-w/2);full_height=right-(x-w/2+.05)
    assert near(nominal,.1) and full_height>=.05-1e-7
    assert near(x+w/2,1.85) and near(x+w/2-right,.635)
    overlap.append({'nominal_overlap_mm':nominal,'full_height_overlap_mm':full_height})

# Explicit mask-only roundrects are +0.05 mm Minkowski expansions of every
# actual copper object, independent of an unavailable local mask-margin setter.
for c in cu:
    m=next(m for m in mask if near(m['x'],c['x']) and near(m['y'],c['y']))
    assert near((m['width']-c['width'])/2,.05) and near((m['height']-c['height'])/2,.05)
    assert near(m['roundrect_rratio']*min(m['width'],m['height']),.1)
mask_setting=float(child(child(native,'setup'),'pad_to_mask_clearance')[1])
assert near(mask_setting,.05)
graphics=RB['library']['graphics'];cy=next(g for g in graphics if g['layer']=='F.CrtYd')
assert cy['start']=={'x':-2.25,'y':-2.0} and cy['end']=={'x':2.25,'y':2.0}
for p in cu+mask:
    assert p['x']-p['width']/2-cy['start']['x']>=.25-1e-7
    assert cy['end']['x']-p['x']-p['width']/2>=.25-1e-7
    assert p['y']-p['height']/2-cy['start']['y']>=.25-1e-7
    assert cy['end']['y']-p['y']-p['height']/2>=.25-1e-7
fab=next(g for g in graphics if g['layer']=='F.Fab')
assert near(max(q['x'] for q in fab['points'])-min(q['x'] for q in fab['points']),3.1)
assert near(max(q['y'] for q in fab['points'])-min(q['y'] for q in fab['points']),3.25)

pins=RB['symbol']['pins'];assert len(pins)==RB['symbol']['pin_count']==5
assert [(p['number'],p['name'],p['type']) for p in pins]==[('1','S','passive'),('2','S','passive'),('3','S','passive'),('4','G','input'),('5','D','passive')]
assert len({(p['x'],p['y']) for p in pins[:3]})==1
ip=RB['instance_pins']['pins'];assert len(ip)==5
assert len({(p['x'],p['y']) for p in ip[:3]})==1
assert RB['instance']['lib_id']=='Transistor_FET:CSD18543Q3A'
doc=ET.parse(HERE/'disposable.xml').getroot();comps=doc.findall('./components/comp');assert len(comps)==1
fields={f.attrib['name']:f.text for f in comps[0].findall('./fields/field')}
assert fields['MFG P/N']=='CSD18543Q3A' and fields['Review']=='CUSTOM FOOTPRINT — REVIEW REQUIRED'
assert comps[0].findtext('footprint')==fp[1]
assert {frozenset(p.attrib['pin'] for p in n.findall('node')) for n in doc.findall('./nets/net')}=={frozenset(('1','2','3')),frozenset(('4',)),frozenset(('5',))}
assert [(p.attrib['num'],p.attrib['name'],p.attrib['type']) for p in doc.findall('./libparts/libpart/pins/pin')]==[(p['number'],p['name'],p['type']) for p in pins]
erc=json.loads((HERE/'erc.json').read_text());assert len(erc)==4 and all(e['severity']=='error' for e in erc)

frozen=json.loads((HERE/'frozen_baseline.json').read_text());assert frozen['basis']=='2450670'
for f,h in frozen['files'].items():assert sha(ROOT/f)==h,f
manifest=json.loads((HERE/'native_source_sha256.json').read_text())
expected_paths={'hardware/eps/rev_b/libraries/Ember_Charger_BMS_Review.pretty/TI_CSD18543Q3A_Q3A_Manufacturer.kicad_mod'}
expected_paths.update('hardware/eps/verification/charging/powerpath_package/disposable/'+f for f in ('powerpath_check.kicad_pro','powerpath_check.kicad_pcb','powerpath_check.kicad_sch','fp-lib-table'))
assert set(manifest)==expected_paths
for f,h in manifest.items():assert sha(ROOT/f)==h,f
protected=lambda f:Path(f).suffix in ('.kicad_pro','.kicad_pcb','.kicad_sch','.kicad_sym','.kicad_mod') or Path(f).name in ('fp-lib-table','sym-lib-table')
changes={f:s for s,f in (x.split('\t') for x in subprocess.check_output(['git','diff','--no-renames','--name-status','2450670','--','hardware/eps'],cwd=ROOT,text=True).splitlines()) if protected(f)}
for f in subprocess.check_output(['git','ls-files','--others','--exclude-standard','--','hardware/eps'],cwd=ROOT,text=True).splitlines():
    if protected(f):assert f not in changes;changes[f]='A'
assert changes=={f:'A' for f in manifest},changes
with (HERE/'physical_map.csv').open('w',newline='') as f:
    w=csv.writer(f,lineterminator='\n');w.writerow(['physical_terminal','function','symbol_pin/name/type','copper_number','localX_mm','localY_mm','width_mm','height_mm','boardX_mm','boardY_mm','view/source'])
    for i,(n,x,y,ww,hh) in enumerate(copper,1):w.writerow([i,'S' if i<4 else ('G' if i==4 else 'D'),n+'/'+('S/passive' if i<4 else ('G/input' if i==4 else 'D/passive')),n,x,y,ww,hh,x+25,y+25,'front/component; pin1 upper-left; CCW; TI SLPS633 pp1/8/9; bottom mechanical mirrored'])
with (HERE/'all_objects.csv').open('w',newline='') as f:
    w=csv.writer(f,lineterminator='\n');w.writerow(['object','number','layers','x','y','width','height','radius_mm','type','drill'])
    for i,p in enumerate(saved,1):w.writerow([i,p['number'],'/'.join(p['layers']),p['x'],p['y'],p['width'],p['height'],p['roundrect_rratio']*min(p['width'],p['height']),p['type'],'none'])
(HERE/'saved_geometry.json').write_text(json.dumps({'board_sha256':sha(HERE/'disposable/powerpath_check.kicad_pcb'),'pads':saved,'pad_to_mask_clearance_mm':mask_setting,'drain_overlap':overlap,'note':'read-only native geometry supplements API omission of sizes/types/radii/drills'},indent=2)+'\n')
result={'status':'DEVELOPMENT PHYSICAL MAP PASS UNDER APPROVED DECOMPOSITION; MANUFACTURING QUALIFICATION OPEN','basis':'2450670','raw_objects':30,'copper_objects':9,'unique_electrical_numbers':5,'drain_number5_objects':5,'intentional_number_repetitions':4,'blank_paste_objects':12,'blank_mask_objects':9,'drills':0,'physical_rows':9,'stock_symbol_pins':5,'source_pins_stacked':[1,2,3],'drain_union_continuous':True,'concave_corner_deviation_extent_mm':.05,'mask_expansion_minimum_mm':.05,'frozen_files_unchanged':len(frozen['files']),'exact_new_native_paths':sorted(manifest),'CLI_ERC':dict(Counter(e['rule'] for e in erc)),'actual_images_inspected':['symbol.png','symbol_detail.png','board_copper.png','board_silk.png','board_paste.png','board_mask.png','board_mask_copper.png','board_fab.png'],'open':['CUSTOM FOOTPRINT review marker retained','Internal concave R0.05 arcs not reproduced by approved overlapping rounded rectangles','Placed default Reference crosses drain/mask; outline/dot clear, production reference placement remains open','Fab strokes obscure parts of tiny numbers; raw numeric map corroborates','Stencil/thermal-via/assembly/application/fit/flight qualification open; no real integrated circuit placement']}
(HERE/'verified.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
