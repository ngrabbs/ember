"""Stage2 saved-netlist and evidence checks. Protected KiCad sources are read only for hashes."""
from pathlib import Path
import re, json, hashlib, itertools
base=Path(__file__).resolve().parent
raw=json.loads((base/'stage2-evidence.json').read_text())
def unwrap(v):
    assert not v.get('isError'),v
    return json.loads(v['content'][0]['text'])
def parse(path):
    nets={}
    for block in path.read_text().split('\n\t\t(net\n')[1:]:
        name=re.search(r'\(name "([^"]+)"\)',block)[1]
        key='AON_SW' if name=='Net-(U1-SW)' else name.rsplit('/',1)[-1]
        assert key not in nets,('duplicate domain',key)
        nets[key]=set(re.findall(r'\(node\s*\(ref "([^"]+)"\)\s*\(pin "([^"]+)"\)',block))
    return nets
expected={k:set(map(tuple,v)) for k,v in json.loads((base/'stage1-expected-topology.json').read_text()).items()}
for prefix,n in [('USB',201),('BENCH',211),('STACK',221)]:
    u,r0,r1,r2,c0,c1=f'U{n}',f'R{n}',f'R{n+1}',f'R{n+2}',f'C{n}',f'C{n+1}'
    expected['AON_BOOTSTRAP_IN']|={(u,'15'),(u,'16')}
    expected['GND']|={(u,'9'),(c0,'2')}
    expected[prefix+'_ENTRY_POS']={(u,'1'),(u,'2'),(u,'3'),(c0,'1'),(r0,'1')}
    expected[prefix+'_BOOT_RTN']={(u,'6'),(u,'8'),(u,'17'),(r1,'2'),(r2,'2'),(c1,'2')}
    expected[f'Net-({u}-OVP)']={(u,'5'),(r0,'2'),(r1,'1')}
    expected[f'Net-({u}-ILIM)']={(u,'11'),(r2,'1')}
    expected[f'Net-({u}-dVdT)']={(u,'12'),(c1,'1')}
    for pin,name in [('4','NC'),('13','NC'),('7','~{SHDN}'),('10','IMON'),('14','~{FLT}')]:
        expected[f'unconnected-({u}-{name}-Pad{pin})']={(u,pin)}
nets=parse(base/'stage2.net')
assert nets==expected,{'actual':nets,'expected':expected}
assert len(nets)==52
assert len(nets['+3V3_AON'])==18
assert len(nets['AON_BOOTSTRAP_IN'])==10
assert not {'+3V3','+5V','MAIN_BUCK_EN','MCU_ALIVE'}&nets.keys()
text=(base/'stage2.net').read_text()
refs=re.findall(r'\(comp\s*\(ref "([^"]+)"\)',text)
assert len(refs)==len(set(refs))==48
for sheet in ['payload_compute_rev_next.kicad_sch','02_bootstrap_inputs.kicad_sch','03_aon_supply.kicad_sch','04_reset_run_core.kicad_sch']:
    for key,field in [('wires','floating_count'),('pins','unconnected_count'),('shorts','short_count'),('orphans','orphan_count'),('overlaps','overlap_count')]:
        assert unwrap(raw[sheet][key])[field]==0,(sheet,key)
    assert not unwrap(raw[sheet]['overlaps'])['bounds_unresolved']
assert unwrap(raw['sheet_pins'])['issue_count']==0
assert len(unwrap(raw['hierarchy'])['children'])==3
mapping={'1':('IN','power_in'),'2':('IN','passive'),'3':('UVLO','input'),'4':('NC','no_connect'),'5':('OVP','input'),'6':('MODE','input'),'7':('~{SHDN}','input'),'8':('RTN','passive'),'9':('GND','power_in'),'10':('IMON','output'),'11':('ILIM','passive'),'12':('dVdT','passive'),'13':('NC','no_connect'),'14':('~{FLT}','open_collector'),'15':('OUT','power_out'),'16':('OUT','passive'),'17':('RTN','passive')}
assert {p['number']:(p['name'],p['type']) for p in unwrap(raw['bootstrap_symbol'])['pins']}==mapping
fp=unwrap(raw['bootstrap_footprint'])
assert len(fp['pads'])==22
copper=[p for p in fp['pads'] if 'F.Cu' in p['layers']]
assert len(copper)==17 and {p['number'] for p in copper}==set(mapping)
for p in copper:
    n=int(p['number'])
    x=-2.9 if n<=8 else 2.9 if n<=16 else 0
    y=-2.275+(n-1)*.65 if n<=8 else 2.275-(n-9)*.65 if n<=16 else 0
    assert abs(p['x']-x)<1e-9 and abs(p['y']-y)<1e-9
    assert not p['drill'] and p['type']=='smd'
    assert p['width']==(3.4 if n==17 else 1.5)
    assert p['height']==(5 if n==17 else .45)
for n in [201,211,221]:
    u=f'U{n}'
    instance=unwrap(raw['new_ic_instances'][u])
    assert instance['value']=='TPS26600PWPR'
    assert instance['lib_id']=='Power_Management:TPS26600PWP'
    assert instance['footprint']=='EMBER_Payload:'+fp['name']
    assert instance['rotation']==0 and not instance.get('mirror_x',False) and not instance.get('mirror_y',False)
    assert {p['number']:p['name'] for p in unwrap(raw['new_ic_pins'][u])['pins']}=={n:v[0] for n,v in mapping.items()}
    for ref,value in [(f'R{n}',('130k' if n==201 else '66.5k')+' / 1%'),(f'R{n+1}','10k / 1%'),(f'R{n+2}','118k / 1%'),(f'C{n}','100n / 50V'),(f'C{n+1}','220n / 16V')]:
        assert re.search(r'\(ref "'+ref+r'"\)\s*\(value "([^"]+)"\)',text)[1]==value
erc=unwrap(raw['erc'])
assert erc['errors']==21 and erc['warnings']==0
ports={'USB_ENTRY_POS','BENCH_ENTRY_POS','STACK_ENTRY_POS','SOURCE_OK_AON','MODE_PERMISSION','MCU_MAIN_REQ','MCU_CONTROL_READY','ORIN_5V_WINDOW_OK','SHUTDOWN_OK_AON','MCU_ARM_QUAL','MCU_ARM_CLK','AON_RESET_N','POWER_PERMISSION','MAIN_BUCK_REQUEST_OK','RUN_LATCH'}
p=[v for v in erc['violations'] if v['rule']=='pin_not_connected']
assert len(p)==15 and {re.search(r"Hierarchical Sheet Pin '([^']+)'",v['description'])[1] for v in p}==ports
p=[v for v in erc['violations'] if v['rule']=='power_pin_not_driven']
assert len(p)==4 and {re.search(r'Symbol (U\d+) Pin (\d+)',v['description']).groups() for v in p}=={('U1','9'),('U201','1'),('U211','1'),('U221','1')}
p=[v for v in erc['violations'] if v['rule']=='pin_to_pin']
assert len(p)==2
pairs={tuple(sorted(re.search(r'Symbol (U\d+) Pin (\d+)',item['description']).groups() for item in v['items'])) for v in p}
assert pairs=={(('U201','15'),('U211','15')),(('U211','15'),('U221','15'))}
assert all(v['rule'] in {'pin_not_connected','power_pin_not_driven','pin_to_pin'} for v in erc['violations'])
# Historical stage2 hashes retain the accepted capture; current sources continue in stage3.
hashes=json.loads((base/'stage2-source-hashes.json').read_text())
for path,digest in json.loads((base/'stage2-package-hashes.json').read_text()).items():
    assert hashlib.sha256((base/path).read_bytes()).hexdigest()==digest,('changed package',path)
# Conservative OV divider corners, assuming +/-1% total resistance allocation.
def ov(top,bottom=10000):
    vals=[]
    for t,b,threshold,leak in itertools.product([top*.99,top*1.01],[bottom*.99,bottom*1.01],[1.17,1.225],[-100e-9,100e-9]):
        vals.append(threshold*(1+t/b)+leak*t)
    return [min(vals),max(vals)]
uv_usb=ov(130000);uv_bat=ov(66500)
max_ov_usb=24*10100/(128700+10100)
max_ov_bat=24*10100/(65835+10100)
assert max_ov_usb<4 and max_ov_bat<4
rmin,rmax=118000*.99,118000*1.01
assert rmax<=120000
overload=[.085*120000/rmax,.115*120000/rmin]
short=[.080*120000/rmax,.120*120000/rmin]
slew=[4e-6*23.75/(220e-9*1.2),5.5e-6*25.5/(220e-9*.8)]
cap_max=10.1e-6*1.2
inrush=cap_max*slew[1]
# CONDITIONAL: allocate>=4.35V at buck after cable/switch; not a low-load RON guarantee.
power=[]
for p in [.200,.250,.350]:
    input_current=p/(.8*4.35)
    own=3*.000390+4.75/(128700+9900)+.000000100
    allocated_pd=.004 # provisional reserve, final PD sheet not captured
    power.append({'regulated_W':p,'load_input_A':input_current,'steady_A_with_own_and_PD_reserve':input_current+own+allocated_pd,'ramp_end_A_with_cap_charge':input_current+own+allocated_pd+inrush})
result={'result':'PASS for stage2 saved topology, accepted lead mapping and classified ERC; startup/fabrication not qualified','physical_components':48,'exported_nets':52,'aon_rail_pins':18,'bootstrap_bus_pins':10,'new_efuse_pins':51,'erc_errors':21,'erc_warnings':0,'erc_classification':{'missing_future_ports':15,'missing_external_power_or_return_drivers':4,'documented_native_OR_power_output_conflicts':2},'corners':{'OV_usb_V':uv_usb,'OV_bench_stack_V':uv_bat,'max_OV_sense_at_24V':[max_ov_usb,max_ov_bat],'inferred_overload_A':overload,'inferred_short_A':short,'slew_V_per_s':slew,'max_switched_input_cap_F':cap_max,'ramp_end_cap_current_A':inrush,'conditional_boot_budget':power},'sha256':hashes,'not_proven':['fuse/TVS/harness fault envelope','USB inlet/PD and whole-port input capacitance','low-voltage buck cold ramp/output-cap charging','low-load switch drop, reverse leakage/dynamicOR','persistent unclean-session firmware','thermal/stencil/physical flight inhibit','main admissions/source selection/MCU/cameras/PCB']}
(base/'stage2-check-results.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
