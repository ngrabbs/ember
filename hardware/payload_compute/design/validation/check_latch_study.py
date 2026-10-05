"""Read exported netlist and Konnect evidence; never modify KiCad sources."""
from pathlib import Path
import json
import re
b = Path(__file__).resolve().parent / 'payload_latch_acceptance'
s = b / 'payload_latch_acceptance'
t = s.with_suffix('.net').read_text()
nets = {}
for block in t.split('\n\t\t(net\n')[1:]:
    name = re.search(r'\(name "([^"]+)"\)', block)[1]
    nets[name] = set(re.findall(r'\(node\s*\(ref "([^"]+)"\)\s*\(pin "([^"]+)"\)', block))
expected = {k: set(map(tuple,v)) for k,v in json.loads((b/'expected-topology.json').read_text()).items()}
assert nets == expected
for ref,value in {**{'U1':'TPS3808G33DBVR','U5':'SN74LVC1G74DCUR'},
                  **{f'U{i}':'SN74LVC1G11DBVR' for i in range(2,5)},
                  **{f'R{i}':'10k' for i in range(1,9)},
                  **{f'C{i}':'100n / 16V' for i in range(1,6)}}.items():
    assert re.search(r'\(ref "'+ref+r'"\)\s*\(value "([^"]+)"\)',t)[1] == value

e=json.loads(Path(str(s)+'-accepted-library-evidence.json').read_text())
for k,f in [('wires','floating_count'),('pins','unconnected_count'),('shorts','short_count'),('orphans','orphan_count')]: assert e[k][f] == 0
assert e['erc']['errors'] == e['erc']['warnings'] == 4
assert len(e['erc']['violations']) == 8
errors=[v for v in e['erc']['violations'] if v['severity']=='error']
assert {v['rule'] for v in errors} == {'pin_not_driven'}
assert {re.search(r'Symbol (U[24]) Pin ([13])',v['description']).groups() for v in errors} == {('U2','1'),('U2','3'),('U4','1'),('U4','3')}
warnings=[v for v in e['erc']['violations'] if v['severity']=='warning']
assert {v['rule'] for v in warnings} == {'isolated_pin_label'}
assert {re.search(r"Label '([^']+)'",v['description'])[1] for v in warnings} == {'SOURCE_OK_AON','MODE_PERMISSION','5V_WINDOW_OK','SHUTDOWN_OK_AON'}
maps={
'reset':{'1':('RESET_N','open_collector'),'2':('GND','power_in'),'3':('MR_N','input'),'4':('CT','input'),'5':('SENSE','input'),'6':('VDD','power_in')},
'gate':{'1':('','input'),'2':('GND','power_in'),'3':('','input'),'4':('','output'),'5':('VCC','power_in'),'6':('','input')},
'latch':{'1':('CLK','input'),'2':('D','input'),'3':('Q_N','output'),'4':('GND','power_in'),'5':('Q','output'),'6':('CLR_N','input'),'7':('PRE_N','input'),'8':('VCC','power_in')}}
placed={c['reference']:c for c in e['pins_query']['components']}
for key,ref,cx,fk,rowx,ys,width,height in [
('reset','U1',100,'dbv',1.3,[-.95,0,.95],1.1,.6),
('gate','U2',110,'dbv',1.3,[-.95,0,.95],1.1,.6),
('latch','U5',120,'dcu',1.55,[-.75,-.25,.25,.75],.85,.3)]:
    sym=e[key+'_symbol']; fp=e[fk+'_fp']; live=e[ref+'_live']; inst=e[ref+'_instance']; mp=maps[key]
    assert sym['pin_count']==len(sym['pins'])==len(mp)
    assert {p['number']:(p['name'],p['type']) for p in sym['pins']}==mp
    assert inst['footprint']=='EMBER_Payload:'+fp['name'] and inst['lib_id']==sym['lib_id']
    assert fp['pad_count']==len(fp['pads'])==len(mp)
    assert fp['coordinate_system']=='footprint_local_mm_y_down'
    assert live['source']=='ipc' and live['pad_count']==len(live['pads'])==len(mp)
    for pad in fp['pads']:
        n=int(pad['number']); half=len(ys)
        x,y=(-rowx,ys[n-1]) if n<=half else (rowx,ys[2*half-n])
        assert abs(pad['x']-x)<1e-6 and abs(pad['y']-y)<1e-6
        assert pad['width']==width and pad['height']==height
        assert pad['drill']==[] and pad['type']=='smd' and pad['shape']=='roundrect'
        assert pad['rotation']==0 and abs(height*pad['roundrect_rratio']-.05)<1e-6
        assert set(pad['layers'])=={'F.Cu','F.Mask','F.Paste'}
        lp=next(p for p in live['pads'] if p['number']==pad['number'])
        assert abs(lp['x']-cx-x)<1e-6 and abs(lp['y']-100-y)<1e-6
        assert lp['net']=='' and set(lp['layers'])==set(pad['layers'])
    for rr in ([ref] if key!='gate' else ['U2','U3','U4']):
        assert {p['number']:p['name'] for p in placed[rr]['pins']}=={n:v[0] for n,v in mp.items()}
print(json.dumps({'exported_nets_checked':len(nets),'distinct_package_leads':20,
                  'placed_ic_pins_checked':32,'expected_boundary_erc_errors':4,
                  'expected_boundary_erc_warnings':4,'result':'PASS for declared bounded study'},indent=2))
