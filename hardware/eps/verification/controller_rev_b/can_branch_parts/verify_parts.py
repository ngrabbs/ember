#!/usr/bin/env python3
"""Exact stock contact-map gate at pre-integration basis2d1ff31."""
from common import *
from collections import Counter
import csv,xml.etree.ElementTree as E
F=H/'disposable/can_branch_parts_check'
b=json.loads((H/'baseline.json').read_text());rb=json.loads((H/'readback.json').read_text())
assert all(portable(p) for category in ['protected_sources','preserved_untracked_progress'] for p in b[category])
for p,h in b['protected_sources'].items():assert sha(ROOT/p)==h,p
for p,h in b['preserved_untracked_progress'].items():assert sha(ROOT/p)==h,p
sym=unwrap(rb['symbol']['value']);lib=unwrap(rb['footprint']);live=unwrap(rb['live_after_save'])
assert sym['pin_count']==len(sym['pins'])==5
assert {p['number']:(p['name'],p['type']) for p in sym['pins']}=={'1':('NC','no_connect'),'2':('','input'),'3':('GND','power_in'),'4':('','output'),'5':('VCC','power_in')}
assert lib['pad_count']==len(lib['pads'])==5
pcb=parse(F.with_suffix('.kicad_pcb').read_text());fps=kids(pcb,'footprint');assert len(fps)==1
fp=fps[0];assert fp[1]=='Package_TO_SOT_SMD:SOT-23-5_HandSoldering'
assert props(fp)['Reference']=='U1' and props(fp)['Value']=='SN74LVC1G14DBVR'
assert list(map(float,one(fp,'at')[1:]))==[100,100]
pads=kids(fp,'pad');assert len(pads)==lib['pad_count']==len(live['pads'])==live['pad_count']==5
assert Counter(p[1] for p in pads)==Counter(p['number'] for p in live['pads'])==Counter({str(i):1 for i in range(1,6)})
loc={'1':(-1.35,-.95),'2':(-1.35,0),'3':(-1.35,.95),'4':(1.35,.95),'5':(1.35,-.95)}
for p in pads:
 n=p[1];q=next(q for q in lib['pads'] if q['number']==n);a=next(q for q in live['pads'] if q['number']==n)
 assert p[2:4]==['smd','roundrect'] and not kids(p,'drill')
 assert tuple(map(float,one(p,'at')[1:3]))==loc[n]
 assert list(map(float,one(p,'size')[1:]))==[1.56,.65]
 assert float(one(p,'roundrect_rratio')[1])==.25
 assert set(one(p,'layers')[1:])==set(q['layers'])==set(a['layers'])=={'F.Cu','F.Paste','F.Mask'}
 assert abs(a['x']-100-loc[n][0])<1e-6 and abs(a['y']-100-loc[n][1])<1e-6
 assert a['net']==''
setup=one(pcb,'setup');m=kids(setup,'pad_to_mask_clearance')
mask=float(m[0][1]) if m else 0
assert not kids(fp,'solder_mask_margin') and all(not kids(p,'solder_mask_margin') for p in pads)
court=[g for g in kids(fp,'fp_line') if one(g,'layer')[1]=='F.CrtYd']
assert len(court)==4
pts=[tuple(map(float,one(g,k)[1:3])) for g in court for k in ['start','end']]
assert {abs(x) for x,y in pts}=={2.38} and {abs(y) for x,y in pts}=={1.8}
sch=parse(F.with_suffix('.kicad_sch').read_text());ss=kids(sch,'symbol');assert len(ss)==1
assert one(sch,'paper')[1]=='B'
pr=props(ss[0]);assert pr['MFG P/N']==pr['Value']=='SN74LVC1G14DBVR'
assert pr['Footprint']==fp[1] and pr['Manufacturer']=='Texas Instruments'
ncs=kids(sch,'no_connect');assert len(ncs)==1 and list(map(float,one(ncs[0],'at')[1:]))==[92.71,85.09]
pins=unwrap(rb['symbol_pins'])['components'][0]['pins'];assert len(pins)==5
xml=E.parse(H/'fixture.xml').getroot();assert len(xml.findall('components/comp'))==1
erc=json.loads((H/'erc.json').read_text());vs=[v for s in erc['sheets'] for v in s['violations']]
assert Counter((v['severity'],v['type']) for v in vs)=={('error','pin_not_connected'):4,('error','power_pin_not_driven'):2,('error','pin_not_driven'):1}
ipc=unwrap(rb['ipc_before']);assert ipc['requested_open'] and ipc['open_board_count']==1 and ipc['open_boards']==[str(F.with_suffix('.kicad_pcb'))]
rows=[]
names={'1':'NC','2':'A','3':'GND','4':'Y','5':'VCC'}
for n,xy in loc.items():
 sp=next(p for p in sym['pins'] if p['number']==n)
 rows.append({'physical_lead':n,'function':names[n],'symbol_pin':n,'symbol_name':sp['name'],'symbol_type':sp['type'],'footprint_pad':n,'x_mm':xy[0],'y_mm':xy[1],'view':'top/component; pin1 upper-left, counterclockwise; Ydown','source':'TI SCES218AA p3 Fig4-1, p4 Table4-1, p28-30 DBV0005A'})
with (H/'physical_map.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=rows[0],lineterminator='\n');w.writeheader();w.writerows(rows)
sources={str(p.relative_to(ROOT)):sha(p) for p in H.rglob('*') if p.is_file() and portable(p) and p.suffix in ['.kicad_sch','.kicad_pcb','.kicad_pro']}
result={'status':'DEVELOPMENT CONTACT/PIN MAP PASS; GENERIC LAND / FULL-FLASH / ASSEMBLY ACCEPTANCE OPEN','basis':'2d1ff31','MPN':'SN74LVC1G14DBVR','library_pins':5,'library_raw_pads':5,'saved_raw_pads':5,'live_after_save_raw_pads':5,'electrical_unique_numbers':5,'mechanical_or_EP_pads':0,'pin1':'NC; no internal connection; pad retained and soldered','source_sha256':b['source']['sha256'],'preserved_protected_sources':len(b['protected_sources']),'preserved_untracked_progress':5,'board_mask_margin_mm':mask,'stock_y_half_courtyard_mm':1.8,'maximum_flash_y_half_mm':1.775,'remaining_y_margin_mm':.025,'required_layout_y_half_mm':2.025,'required_layout_reservation_mm':[4.76,4.05],'ERC_errors':7,'ERC_warnings':0,'native_source_sha256':sources}
(H/'verified.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
