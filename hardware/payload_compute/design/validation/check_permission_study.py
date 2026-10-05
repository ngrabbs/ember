"""Verify the saved permission study, physical mapping and Boolean behavior."""
from pathlib import Path
from itertools import product
import json,re
base=Path(__file__).resolve().parent/'payload_permission_acceptance'
s=base/'payload_permission_acceptance'
t=s.with_suffix('.net').read_text()
nets={}
for block in t.split('\n\t\t(net\n')[1:]:
    name=re.search(r'\(name "([^"]+)"\)',block)[1]
    nets[name]=set(re.findall(r'\(node\s*\(ref "([^"]+)"\)\s*\(pin "([^"]+)"\)',block))
assert len(nets)==20
pin_net={node:name for name,nodes in nets.items() for node in nodes}
assert len(pin_net)==sum(map(len,nets.values()))
assert nets['/IHU_PAYLOAD_EN']=={('R1','1')}
assert nets['/IHU_INPUT_PIN']=={('R1','2'),('R2','1'),('U1','1')}
assert nets['/AON_RESET_N']=={('U9','3')}  # No divider fighting supervisor pull-up.
assert not any(ref=='R9' for ref,pin in pin_net)
for i in range(1,10):
    assert pin_net[('U'+str(i),'5')]=='+3V3'
    assert pin_net[('U'+str(i),'2')]=='GND'
    assert pin_net[('C'+str(i),'1')]=='+3V3'
    assert pin_net[('C'+str(i),'2')]=='GND'
nand={2,3,5,6,8}
for i in range(1,10):
    want='SN74LVC1G10DBVR' if i in nand else 'SN74LVC1G11DBVR'
    assert re.search(r'\(ref "U'+str(i)+r'"\)\s*\(value "([^"]+)"\)',t)[1]==want
for ref,value in {'R1':'100R / 1%','R2':'10k / 1%',**{f'R{i}':'10k' for i in [3,4,5,6,7,8,10]},**{f'C{i}':'100n / 16V' for i in range(1,10)}}.items():
    assert re.search(r'\(ref "'+ref+r'"\)\s*\(value "([^"]+)"\)',t)[1]==value
# Evaluate the actual exported gate pins, rather than the intended equations.
case_count=0
for aon,locked,bench,ls,lo,ss,so,ihu,request in product([False,True],repeat=9):
    values={'+3V3':True,'GND':False,'/AON_RESET_N':aon,'/MODE_LOCKED':locked,
            '/BENCH_LATCHED':bench,'/LAB_SOURCE_SELECTED':ls,'/LAB_SOURCE_OK':lo,
            '/STACK_SOURCE_SELECTED':ss,'/STACK_SOURCE_OK':so,'/IHU_INPUT_PIN':ihu}
    remaining=set(range(1,10))
    while remaining:
        progress=False
        for i in list(remaining):
            inputs=[pin_net[('U'+str(i),p)] for p in ['1','3','6']]
            if all(n in values for n in inputs):
                out=all(values[n] for n in inputs)
                values[pin_net[('U'+str(i),'4')]]=not out if i in nand else out
                remaining.remove(i);progress=True
        assert progress, 'Unresolved gate inputs or combinational loop'
    want=False
    if aon and locked and (ls!=ss):
        want=(ls and lo) if bench else (ss and so and ihu)
    assert values['/MODE_PERMISSION']==want
    assert (values['/MODE_PERMISSION'] and request)==(want and request)
    case_count+=1
e=json.loads(Path(str(s)+'-final-evidence.json').read_text())
for k,f in [('wires','floating_count'),('pins','unconnected_count'),('shorts','short_count'),('orphans','orphan_count'),('overlaps','overlap_count')]:
    assert e[k][f]==0
assert e['erc']['errors']==1 and e['erc']['warnings']==2
assert [(v['rule'],v['severity']) for v in e['erc']['violations']]==[
    ('pin_not_driven','error'),('isolated_pin_label','warning'),('isolated_pin_label','warning')]
assert 'U9 Pin 3' in e['erc']['violations'][0]['description']
sym,fp,placed=e['symbol'],e['footprint'],e['placed']
mapping={'1':('','input'),'2':('GND','power_in'),'3':('','input'),
         '4':('','output'),'5':('VCC','power_in'),'6':('','input')}
assert {p['number']:(p['name'],p['type']) for p in sym['pins']}==mapping
assert sym['pin_count']==fp['pad_count']==placed['pad_count']==6
assert e['instance']['value']=='SN74LVC1G10DBVR'
assert e['instance']['footprint']=='EMBER_Payload:TI_DBV0006A_SOT23_6'
assert placed['source']=='file'  # KiCad closed; validated Konnect file placement.
coords={'1':(-1.3,-.95),'2':(-1.3,0),'3':(-1.3,.95),'4':(1.3,.95),'5':(1.3,0),'6':(1.3,-.95)}
assert fp['coordinate_system']=='footprint_local_mm_y_down'
for p in fp['pads']:
    x,y=coords[p['number']]
    assert abs(p['x']-x)<1e-6 and abs(p['y']-y)<1e-6
    assert p['width']==1.1 and p['height']==.6 and p['drill']==[]
    assert p['type']=='smd' and p['shape']=='roundrect' and abs(.6*p['roundrect_rratio']-.05)<1e-6
    assert set(p['layers'])=={'F.Cu','F.Mask','F.Paste'}
    q=next(q for q in placed['pads'] if q['number']==p['number'])
    assert abs(q['x']-20-x)<1e-6 and abs(q['y']-20-y)<1e-6 and q['net']==''
    assert set(q['layers'])==set(p['layers'])
print(json.dumps({'exported_nets_checked':len(nets),'exported_gate_combinations':case_count,
                  'new_physical_leads_checked':6,'boundary_erc_errors':1,'boundary_erc_warnings':2,
                  'result':'PASS for bounded schematic; physical timing and carrier integration remain open'},indent=2))
