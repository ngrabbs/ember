"""Check final exported circuit and physical mapping evidence."""
from pathlib import Path
import re,json
b=Path(__file__).resolve().parent/'payload_mode_acceptance';s=b/'payload_mode_acceptance'
expected={
'+3V3':{('C2','1'),('C3','1'),('C4','1'),('C5','1'),('J1','1'),('U1','2'),('U1','7'),('U1','8'),('U2','5'),('U3','5'),('U4','5')},
'GND':{('C1','2'),('C2','2'),('C3','2'),('C4','2'),('C5','2'),('R2','2'),('R3','2'),('R4','2'),('R5','2'),('U1','4'),('U2','2'),('U2','6'),('U3','2'),('U4','3')},
'/AON_RESET_N':{('U1','6'),('U3','3')},
'/BENCH_AUTH':{('R5','1'),('U3','4')},
'/BENCH_JUMPER_RAW':{('J1','2'),('R1','1')},
'/BENCH_FILTERED':{('R1','2'),('R2','1'),('C1','1'),('U4','2')},
'/BENCH_SENSE':{('U4','4'),('U2','3')},
'/BENCH_LATCHED':{('U2','4'),('U3','6')},
'/MCU_MODE_LOCK_CLK':{('R3','1'),('U1','1')},
'/MODE_LOCKED':{('R4','1'),('U1','5'),('U3','1')},
'/MODE_SAMPLE_OPEN':{('U1','3'),('U2','1')},
'unconnected-(U4-NC-Pad1)':{('U4','1')}}
t=s.with_suffix('.net').read_text();nets={}
for block in t.split('\n\t\t(net\n')[1:]:
 name=re.search(r'\(name "([^"]+)"\)',block)[1]
 nets[name]=set(re.findall(r'\(node\s*\(ref "([^"]+)"\)\s*\(pin "([^"]+)"\)',block))
assert nets==expected, nets
for ref,value in {'U1':'SN74LVC1G74DCUR','U2':'SN74LVC1G373DBVR','U3':'SN74LVC1G11DBVR','U4':'SN74LVC1G17DBVR','R1':'1k',**{f'R{i}':'10k' for i in range(2,6)},**{f'C{i}':'100n / 16V' for i in range(1,6)}}.items():
 assert re.search(r'\(ref "'+ref+r'"\)\s*\(value "([^"]+)"\)',t)[1]==value
e=json.loads(Path(str(s)+'-final-evidence.json').read_text())
for k,f in [('wires','floating_count'),('pins','unconnected_count'),('shorts','short_count'),('orphans','orphan_count')]: assert e[k][f]==0
assert e['erc']['total']==e['erc']['errors']==1 and e['erc']['warnings']==0
v=e['erc']['violations'][0]
assert v['rule']=='pin_not_driven' and 'Symbol U1 Pin 6 ' in v['description']
placed={c['reference']:c for c in e['pins_query']['components']}
for sk,fk,lk,ik,ref,cx,mp in [
('symbol','footprint','live','instance','U2',100,{'1':('LE','input'),'2':('GND','power_in'),'3':('D','input'),'4':('Q','tri_state'),'5':('VCC','power_in'),'6':('~{OE}','input')}),
('schmitt_symbol','schmitt_fp','schmitt_live','schmitt_instance','U4',110,{'1':('NC','no_connect'),'2':('','input'),'3':('GND','power_in'),'4':('','output'),'5':('VCC','power_in')})]:
 sym,fp,live,inst=[e[k] for k in [sk,fk,lk,ik]]
 assert sym['pin_count']==len(sym['pins'])==len(mp)
 assert {p['number']:(p['name'],p['type']) for p in sym['pins']}==mp
 assert {p['number']:p['name'] for p in placed[ref]['pins']}=={n:v[0] for n,v in mp.items()}
 assert fp['pad_count']==len(fp['pads'])==len(mp)
 assert fp['coordinate_system']=='footprint_local_mm_y_down'
 assert inst['footprint']=='EMBER_Payload:'+fp['name']
 assert inst['value']==('SN74LVC1G373DBVR' if ref=='U2' else 'SN74LVC1G17DBVR')
 assert live['source']=='ipc' and live['pad_count']==len(live['pads'])==len(mp)
 coords={'1':(-1.3,-.95),'2':(-1.3,0),'3':(-1.3,.95),'4':(1.3,.95)}
 coords.update({'5':(1.3,0),'6':(1.3,-.95)} if ref=='U2' else {'5':(1.3,-.95)})
 for p in fp['pads']:
  x,y=coords[p['number']]
  assert abs(p['x']-x)<1e-6 and abs(p['y']-y)<1e-6
  assert p['width']==1.1 and p['height']==.6 and p['drill']==[] and p['rotation']==0
  assert p['type']=='smd' and p['shape']=='roundrect' and abs(.6*p['roundrect_rratio']-.05)<1e-6
  assert set(p['layers'])=={'F.Cu','F.Mask','F.Paste'}
  lp=next(q for q in live['pads'] if q['number']==p['number'])
  assert abs(lp['x']-cx-x)<1e-6 and abs(lp['y']-100-y)<1e-6 and lp['net']==''
  assert set(lp['layers'])==set(p['layers'])
print(json.dumps({'exported_nets_checked':len(nets),'new_physical_leads_checked':11,
                  'boundary_erc_errors':1,'erc_warnings':0,'result':'PASS for bounded sampler'},indent=2))
