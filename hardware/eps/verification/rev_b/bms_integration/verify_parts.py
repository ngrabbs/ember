#!/usr/bin/env python3
"""Read-only stock-package/disposable acceptance; no KiCad source writes."""
from pathlib import Path
from collections import Counter
import csv, hashlib, json, re
H=Path(__file__).resolve().parent
def parse(text):
    stack=[]; root=None
    for t in re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^()\s]+',text):
        if t=='(':
            n=[]
            if stack: stack[-1].append(n)
            else: root=n
            stack.append(n)
        elif t==')': stack.pop()
        else: stack[-1].append(json.loads(t) if t.startswith('"') else t)
    assert not stack
    return root
def kids(n,k): return [v for v in n if isinstance(v,list) and v and v[0]==k]
def one(n,k): return kids(n,k)[0]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
D=json.loads((H/'parts_readback.json').read_text())
expected={
 'U1':{'1':'VCC1','2':'SDA1','3':'SCL1','4':'GND1','5':'GND2','6':'SCL2','7':'SDA2','8':'VCC2'},
 'J1':{str(i):'Pin_'+str(i) for i in range(1,8)},
 'Q1':{'1':'G','2':'S','3':'D'},'D1':{'1':'K','2':'A'},'Q2':{'1':'G','2':'S','3':'D'}}
positions={'U1':(35,35),'J1':(60,35),'Q1':(35,55),'D1':(60,55),'Q2':(80,55)}
mpns={'U1':'ISO1540DR','J1':'BM07B-GHS-TBT(LF)(SN)','Q1':'BSS84-7-F','D1':'BAT46W-7-F','Q2':'DMN62D2U-7'}
sources={'U1':'TI SLLSEB6F p4 top view, CCW from upper-left pin1; p34 example land',
 'J1':'JST eGH pp2-3 mounting surface; stock normalized180deg, pin1 lower left',
 'Q1':'Diodes DS30149 Rev27 May2026 pp1/5; top view G lower-left/S lower-right/D upper; stock normalized90deg',
 'D1':'Diodes DS30044 Rev20 Nov2023 pp1/4; top-view cathode-band left maps K1',
 'Q2':'Diodes DS44892 Rev3 Mar2025 pp1/6; top view G lower-left/S lower-right/D upper; stock normalized90deg'}
board=parse((H/'parts_disposable/bms_parts_check.kicad_pcb').read_text())
fps=kids(board,'footprint');refs=[next(x[2] for x in kids(f,'property') if x[1]=='Reference') for f in fps]
assert len(refs)==len(set(refs))==5 and set(refs)==set(expected)
sch=parse((H/'parts_disposable/bms_parts_check.kicad_sch').read_text());syms=kids(sch,'symbol')
srefs=[next(p[2] for p in kids(s,'property') if p[1]=='Reference') for s in syms]
assert len(srefs)==len(set(srefs))==5 and set(srefs)==set(expected)
rows=[];total=0
for ref,funcs in expected.items():
    lib=D['footprints'][ref];live=D['after_save'][ref]
    symbol=D['symbols'][ref];assert {p['number']:p['name'] for p in symbol['pins']}==funcs
    assert len(symbol['pins'])==len(funcs)
    s=syms[srefs.index(ref)];props={p[1]:p[2] for p in kids(s,'property')}
    assert props['Value']==props['MFG P/N']==mpns[ref] and props['Footprint']
    f=fps[refs.index(ref)];pads=kids(f,'pad');n=9 if ref=='J1' else len(funcs)
    assert len(pads)==len(lib['pads'])==lib['pad_count']==len(live['pads'])==live['pad_count']==n
    expected_numbers=Counter(funcs.keys())
    if ref=='J1': expected_numbers['MP']=2
    assert Counter(p[1] for p in pads)==Counter(p['number'] for p in lib['pads'])==Counter(p['number'] for p in live['pads'])==expected_numbers
    assert live['source']=='ipc' and all(p['net']=='' for p in live['pads'])
    at=one(f,'at');assert tuple(map(float,at[1:3]))==positions[ref]
    assert float(at[3])==0 if len(at)>3 else True
    for native,lp,api in zip(pads,lib['pads'],live['pads']):
        num=native[1];assert num==lp['number']==api['number']
        xy=tuple(map(float,one(native,'at')[1:3]));size=tuple(map(float,one(native,'size')[1:3]))
        assert all(abs(a-b)<2e-6 for a,b in zip(xy,(lp['x'],lp['y']))), (ref,num,xy,lp)
        assert all(abs(a-b)<2e-6 for a,b in zip(size,(lp['width'],lp['height']))), (ref,num,size,lp)
        assert native[2:4]==[lp['type'],lp['shape']] and not kids(native,'drill') and lp['drill']==[]
        assert set(one(native,'layers')[1:])==set(lp['layers'])==set(api['layers'])=={'F.Cu','F.Mask','F.Paste'}
        assert abs(float(one(native,'roundrect_rratio')[1])-lp['roundrect_rratio'])<1e-9
        assert abs(api['x']-(positions[ref][0]+xy[0]))<2e-6 and abs(api['y']-(positions[ref][1]+xy[1]))<2e-6
        rows.append({'reference':ref,'MPN':mpns[ref],'physical_terminal':num,'function':funcs.get(num,'mechanical retention; not symbol/net'),
                     'symbol_pin':num if num!='MP' else 'absent intentionally','footprint_pad':num,'x_mm':xy[0],'y_mm':xy[1],
                     'view_and_source':sources[ref]})
    total+=n
assert total==25 and len(rows)==25
with (H/'parts_physical_map.csv').open('w') as f:
    w=csv.DictWriter(f,fieldnames=rows[0],lineterminator='\n');w.writeheader();w.writerows(rows)
result={'status':'SAVED LIBRARY / SCHEMATIC / PLACED-BOARD MAP PASS; STOCK LAND DEVIATIONS RECORDED',
 'parts':mpns,'raw_pad_objects':total,'symbol_electrical_pins':23,'mechanical_MP_objects':2,
 'nonmanufacturing_acceptance':'Development package identity only; stock lands, solder process, temperature and functional circuit qualification remain open',
 'source_sha256':{str(p.relative_to(H)):sha(p) for p in (H/'parts_disposable').iterdir() if p.suffix in {'.kicad_pro','.kicad_sch','.kicad_pcb'}},
 'Diodes_numbering_note':'Diodes figures label G/S/D physical terminal positions without printed lead numbers. Numeric stock G1/S2/D3 is checked by the corresponding terminal geometry, not by an assumed textual numeric key.',
 'render_caveat':'Numbered fab overlays cross body strokes/small labels; actual numeric pad readback is checked independently.'}
(H/'parts_verified.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
