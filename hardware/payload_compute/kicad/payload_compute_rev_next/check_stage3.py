"""Read-only stage3 saved topology, physical-pin truth table and evidence checker."""
from pathlib import Path
import json,re,itertools,hashlib
base=Path(__file__).resolve().parent
raw=json.loads((base/'stage3-evidence.json').read_text())
def unwrap(v):
 assert not v.get('isError'),v
 return json.loads(v['content'][0]['text'])
def parse(path):
 nets={}
 for block in path.read_text().split('\n\t\t(net\n')[1:]:
  name=re.search(r'\(name "([^"]+)"\)',block)[1]
  key='AON_SW' if name=='Net-(U1-SW)' else name.rsplit('/',1)[-1]
  assert key not in nets,key
  nets[key]=set(re.findall(r'\(node\s*\(ref "([^"]+)"\)\s*\(pin "([^"]+)"\)',block))
 return nets
expected=parse(base/'stage2.net')
expected['AON_RESET_RAW_N']={('R101','2'),('U101','1')}
expected['AON_RESET_N']-=expected['AON_RESET_RAW_N']
intent=json.loads((base/'stage3-new-expected-pins.json').read_text())
for group in intent.values():
 for sheet,components in group.items():
  for ref,pins in components.items():
   for pin,net in pins.items(): expected.setdefault(net,set()).add((ref,pin))
for ref in ['U302','U303','U304','U305','U311','U309','U407','U408','U409']:
 expected[f'unconnected-({ref}-NC-Pad1)']={(ref,'1')}
expected['unconnected-(U310-CWD-Pad2)']={('U310','2')}
nets=parse(base/'payload_compute_rev_next.net')
assert nets==expected,{'missing':{k:sorted(v-nets.get(k,set())) for k,v in expected.items() if v!=nets.get(k)},'extra':{k:sorted(v-expected.get(k,set())) for k,v in nets.items() if v!=expected.get(k)}}
assert len(nets)==105
text=(base/'payload_compute_rev_next.net').read_text()
refs=re.findall(r'\(comp\s*\(ref "([^"]+)"\)',text)
assert len(refs)==len(set(refs))==132
assert not {'+3V3','MAIN_BUCK_EN','MCU_ALIVE'}&nets.keys()
pin_net={node:net for net,nodes in nets.items() for node in nodes}
assert len(pin_net)==sum(map(len,nets.values()))
sheets=[k for k in raw if k.endswith('.kicad_sch')]
assert len(sheets)==6
for sheet in sheets:
 for key,field in [('wires','floating_count'),('pins','unconnected_count'),('shorts','short_count'),('orphans','orphan_count'),('overlaps','overlap_count')]: assert unwrap(raw[sheet][key])[field]==0,(sheet,key)
 assert not unwrap(raw[sheet]['overlaps'])['bounds_unresolved']
assert unwrap(raw['sheet_pins'])['issue_count']==0
assert len(unwrap(raw['hierarchy'])['children'])==5
assert len(raw['new_ic_instances'])==31
for ref,item in raw['new_ic_instances'].items():
 d=unwrap(item)
 assert d['rotation']==0 and not d['mirror_x'] and not d['mirror_y']
 assert re.search(r'\(ref "'+ref+r'"\)\s*\(value "([^"]+)"\)',text)[1]==d['value']
 assert d['footprint'].startswith('EMBER_Payload:')
 queried={p['number'] for p in unwrap(raw['new_ic_pins'][ref])['pins']}
 assert queried=={p for r,p in pin_net if r==ref},(ref,queried)
# Disposable manufacturer-map acceptance; copper tails retain one physical EP number.
maps={'U1':{'1':'OUTA','2':'GND','3':'INA+','4':'INB-','5':'VDD','6':'OUTB'},'U2':{'1':'VDD','2':'CWD','3':'EN','4':'GND','5':'SET1','6':'WDI','7':'WDO_N','8':'ENOUT','9':'EP_GND'},'U3':{'1':'NC','2':'','3':'GND','4':'','5':'VCC'},'U4':{'1':'','2':'','3':'GND','4':'','5':'VCC'}}
for ref,want in maps.items():
 a=raw['package_acceptance'][ref]
 assert {p['number']:p['name'] for p in unwrap(a['symbol'])['pins']}==want
 assert {p['number']:p['name'] for p in unwrap(a['pins'])['pins']}==want
 pads=unwrap(a['pads'])['pads']
 copper=[p for p in pads if 'F.Cu' in p['layers']]
 assert {p['number'] for p in copper}==set(want)
 assert len(copper)==(13 if ref=='U2' else len(want))
 if ref=='U2': assert sum(p['number']=='9' for p in copper)==5
# Combinatorial proof resolves every gate input/output from exported physical pins.
instances={r:unwrap(v)['value'] for r,v in raw['new_ic_instances'].items()}
gates=['U402','U403','U407','U408','U409','U410','U411','U412','U413','U414','U415','U308','U309','U313','U314','U315','U316']
def evaluate(values,which):
 pending=list(which)
 while pending:
  progress=False
  for ref in pending[:]:
   kind=instances[ref]
   pins=['1','3','6'] if '1G11' in kind else ['1','2'] if '1G32' in kind else ['2']
   inputs=[pin_net[ref,p] for p in pins]
   if all(p in values for p in inputs):
    a=[values[p] for p in inputs]
    values[pin_net[ref,'4']]=(all(a) if '1G11' in kind else any(a) if '1G32' in kind else not a[0])
    pending.remove(ref);progress=True
  assert progress,('unresolved gate',pending,values)
 return values
for R,M,S,B,I,U,V,T in itertools.product([False,True],repeat=8):
 values=evaluate({'+3V3_AON':True,'GND':False,'AON_RESET_N':R,'MODE_LOCKED':M,'SOURCE_LOCKED':S,'SOURCE_UNLOCKED':not S,'MODE_UNLOCKED':not M,'BENCH_LATCHED':B,'IHU_EN_VALID':I,'USB_REQ_LATCHED':U,'BENCH_REQ_LATCHED':V,'STACK_REQ_LATCHED':T},gates)
 valid=R and M and S and sum([U,V,T])==1
 choice=[valid and U and B,valid and V and B,valid and T and not B]
 assert [values[n] for n in ['USB_CHOICE_ONLY','BENCH_CHOICE_ONLY','STACK_CHOICE_ONLY']]==choice
 assert values['MODE_PERMISSION']==(choice[0] or choice[1] or (choice[2] and I))
 assert values['SOURCE_REQ_LE']==(R and not S)
 assert values['MODE_LE']==(R and not M)
for R,Q,W in itertools.product([False,True],repeat=3):
 v=evaluate({'AON_RESET_N':R,'MCU_READY':Q,'WD_RESET_VALID':W},['U312'])
 assert v['MCU_CONTROL_READY']==(R and Q and W)
assert pin_net['U401','6']==pin_net['U307','6']=='AON_RESET_N'
assert pin_net['U310','3']=='WDT_ENABLE' and pin_net['U310','7']==pin_net['U310','8']=='MCU_NRST_N'
assert nets['AON_RESET_RAW_N']=={('U101','1'),('R101','2'),('U303','2'),('U304','2')}
erc=unwrap(raw['erc']);assert (erc['errors'],erc['warnings'])==(31,3)
ports=set('USB_ENTRY_POS BENCH_ENTRY_POS STACK_ENTRY_POS SOURCE_OK_AON MCU_MAIN_REQ ORIN_5V_WINDOW_OK SHUTDOWN_OK_AON MCU_ARM_QUAL MCU_ARM_CLK POWER_PERMISSION MAIN_BUCK_REQUEST_OK RUN_LATCH IHU_PAYLOAD_EN BENCH_JUMPER_N MODE_LOCK_CLK MCU_WDI MCU_READY MCU_NRST_N USB_REQ BENCH_REQ STACK_REQ SOURCE_LOCK_CLK SOURCE_LOCKED WD_RESET_VALID IHU_EN_VALID'.split())
viol=erc['violations']
p=[v for v in viol if v['rule']=='pin_not_connected']
assert len(p)==25 and {re.search(r"Hierarchical Sheet Pin '([^']+)'",v['description'])[1] for v in p}==ports
p=[v for v in viol if v['rule']=='power_pin_not_driven'];assert len(p)==4
assert {re.search(r'Symbol (U\d+) Pin (\d+)',v['description']).groups() for v in p}=={('U1','9'),('U201','1'),('U211','1'),('U221','1')}
p=[v for v in viol if v['rule']=='pin_to_pin'];assert len(p)==2
pairs={tuple(sorted(re.search(r'Symbol (U\d+) Pin (\d+)',i['description']).groups() for i in v['items'])) for v in p}
assert pairs=={(('U201','15'),('U211','15')),(('U211','15'),('U221','15'))}
p=[v for v in viol if v['rule']=='isolated_pin_label'];assert len(p)==3 and all("'IHU_PAYLOAD_EN'" in v['description'] for v in p)
assert len(viol)==34
for f,h in json.loads((base/'stage3-source-hashes.json').read_text()).items(): assert hashlib.sha256((base/f).read_bytes()).hexdigest()==h,f
for f,h in json.loads((base/'stage3-package-hashes.json').read_text()).items(): assert hashlib.sha256((base.parent/f).read_bytes()).hexdigest()==h,f
Vmax=3.3*1.025
sink=Vmax/9900
reset_load=Vmax/99000+8*5e-6
wd_en_load=Vmax/99000+.7e-6
assert reset_load<100e-6 and wd_en_load<100e-6
sense=lambda v,t,b,leak:v*b/(t+b)+leak*t*b/(t+b)
hi=min(sense(3.,t,b,l) for t,b,l in itertools.product([9900,10100],[5049,5151],[-25e-9,25e-9]))
lo=max(sense(.4,t,b,l) for t,b,l in itertools.product([9900,10100],[5049,5151],[-25e-9,25e-9]))
assert hi>.404 and lo<.387
new=.000322+14*sink+4*Vmax/99000+.001
old=12*sink+.000060
standing=(new+old)*Vmax
assert standing<.036
result={'result':'PASS bounded stage3 capture; prototype qualifications remain open','physical_components':132,'exported_nets':105,'new_ICs':31,'truth_cases':{'mode_source':256,'qualified_readiness':8},'checks':'all six sheets wires/pins/shorts/orphans/overlaps zero; hierarchy zero issues','ERC':{'errors':31,'warnings':3,'open_ports':sorted(ports),'missing_external_power_drivers':4,'documented_native_OR_conflicts':2,'isolated_IHU_boundary_labels':3},'conditional_corners':{'sink_A_per_10k':sink,'clean_reset_buffer_load_A':reset_load,'watchdog_enable_buffer_load_A':wd_en_load,'IHU_high_min_V':hi,'IHU_low_max_V':lo,'captured_AON_W_with_1mA_reserve':standing,'rounded_allocation_W':.036,'remaining_of_200mW_W':.164},'not_proven':['receiver threshold/ramp envelope','early mode lock firmware prevention','AON/eFuse/buck cold startup and capacitor charging','watchdog partial-power/startup/level waveform','physical MCU/PD/raw windows/source qualification/main admissions','entry fuse/TVS/connector/harness qualification','EP/stencil/assembly/layout/fabrication/flight']}
(base/'stage3-check-results.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
