"""Independent whole-root endpoint/class/metadata review of ADC integration.

Inputs are fresh CLI exports and Konnect class readback, never native-source
text parsing. Source hashes detect any subsequent authorized design change.
"""
from pathlib import Path
import fnmatch,hashlib,json,subprocess,xml.etree.ElementTree as E
H=Path(__file__).resolve().parent;ROOT=H.parents[4]
old=E.parse(ROOT/'hardware/eps/verification/rev_b/adc_integration/before.xml').getroot()
new=E.parse(H/'eps_rev_b.xml').getroot()
comps=lambda r:{c.get('ref'):c for c in r.findall('./components/comp')}
nets=lambda r:{n.get('name'):{(a.get('ref'),a.get('pin')) for a in n.findall('node')} for n in r.findall('./nets/net')}
bc,ac=comps(old),comps(new);bn,an=nets(old),nets(new)
refs={f'R{i}' for i in range(1300,1319)}|{f'C{i}' for i in range(1300,1306)}|{'U1300','U1301'}
assert len(bc)==318 and len(ac)==345 and set(ac)-set(bc)==refs
def normalized(c):
 c=E.fromstring(E.tostring(c))
 for x in c.iter():x.tail=None;x.text=x.text.strip() if x.text else None
 return E.tostring(c)
for ref,c in bc.items():assert normalized(c)==normalized(ac[ref]),ref
moved={('U100',str(p)) for p in [7,8,11,12]}
for name,ends in bn.items():
 if ends<=moved:assert name not in an;continue
 assert name in an and {(r,p) for r,p in an[name] if r not in refs}==ends,name
expected={
 'ANA_EPS_SYS':{('U100','7'),('R1303','2'),('R1304','1')},
 'ANA_EPS_5V0':{('U100','8'),('R1307','2'),('R1308','1')},
 'ANA_EPS_3V3':{('U100','11'),('R1311','2'),('R1312','1')},
 'ANA_EPS_BATT':{('U100','12'),('R1316','2'),('R1317','1')},
 '/Rail Telemetry/ADC_SUPPLY_OK':{('U1300',p) for p in ['1','4','10','13']}|{('U1301','2'),('R1318','1')},
 'Net-(R1300-Pad2)':{('R1300','2'),('R1301','1')},
 'Net-(R1313-Pad2)':{('R1313','2'),('R1314','1')},
}
for tag,top,bottom,cap,s,d,series in [('SYS','R1301','R1302','C1300','2','3','R1303'),('5V0','R1305','R1306','C1301','5','6','R1307'),('3V3','R1309','R1310','C1302','9','8','R1311'),('BATT','R1314','R1315','C1303','12','11','R1316')]:
 expected['/Rail Telemetry/'+tag+'_DIV']={(top,'2'),(bottom,'1'),(cap,'1'),('U1300',s)}
 expected['/Rail Telemetry/'+tag+'_SW']={(series,'1'),('U1300',d)}
assert set(an)-set(bn)==set(expected)
for name,ends in expected.items():assert an[name]==ends,name
rails={'+3V3':{('U1300','14'),('U1301','3'),('C1304','1'),('C1305','1'),('R1309','1')},'+5V':{('R1305','1')},'SYS_PWR_PERMITTED':{('R1300','1')},'BATT_PERMITTED':{('R1313','1')}}
gnd={(r,'2') for r in ['R1302','R1304','R1306','R1308','R1310','R1312','R1315','R1317','R1318']}|{(f'C{i}','2') for i in range(1300,1306)}|{('U1300','7'),('U1301','1')}
rails['GND']=gnd
for name,ends in rails.items():assert an[name]-bn[name]==ends,name
endpoints=[x for v in an.values() for x in v];assert len(endpoints)==len(set(endpoints))==933
assert len(an)==186
functional={n for n in an if not n.startswith('unconnected-')};assert len(functional)==173
classes=json.loads((H/'netclasses.json').read_text())['netclasses']
membership={n:[c['name'] for c in classes if any(fnmatch.fnmatchcase(n,p) for p in c['patterns'])] for n in sorted(functional)}
assert all(len(v)==1 for v in membership.values()),{n:v for n,v in membership.items() if len(v)!=1}
for name in expected:assert membership[name]==(['CONTROL'] if name.endswith('ADC_SUPPLY_OK') else ['ANALOG']),name
erc=json.loads((H/'erc.json').read_text());violations=[v for sheet in erc['sheets'] for v in sheet['violations']]
errors=[v for v in violations if v['severity']=='error'];warnings=[v for v in violations if v['severity']=='warning']
assert len(errors)==6 and len(warnings)==2
unfinished=[v for v in errors if v['type']=='pin_not_connected'];assert len(unfinished)==3
pins={i['description'].split('Pin ')[1].split()[0] for v in unfinished for i in v['items']}
assert pins=={'17','28','32'}
previous=json.loads((ROOT/'hardware/eps/verification/rev_b/swd_integration/erc.json').read_text())
oldv=[v for s in previous['sheets'] for v in s['violations']]
def signature(v):
 # KiCad regenerates ERC pin-item IDs even between exports of unchanged
 # source. Compare exact logical diagnostics and locations; persistent
 # physical component IDs/metadata are checked independently above.
 return (v['severity'],v['type'],v['description'],tuple(sorted((i['description'],i['pos']['x'],i['pos']['y']) for i in v['items'])))
def retired(v):
 return v['type']=='pin_not_connected' and any(any(('Symbol U100 Pin '+p+' [') in i['description'] for p in ['7','8','11','12']) for i in v['items'])
assert sum(retired(v) for v in oldv)==4
assert sorted(signature(v) for v in oldv if not retired(v))==sorted(signature(v) for v in violations)
from pypdf import PdfReader
pdf=PdfReader(ROOT/'hardware/eps/verification/rev_b/adc_integration/eps_rev_b.pdf')
assert len(pdf.pages)==14
assert all(abs(float(p.mediabox.width)-1224)<.1 and abs(float(p.mediabox.height)-792)<.1 for p in pdf.pages)
for name,digest in json.loads((H/'native_source_sha256.json').read_text()).items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
docs=json.loads((H/'documentation_changes.json').read_text());assert set(docs['files'])=={'hardware/eps/design/rev_b_completion.md','hardware/eps/design/rev_b_pin_and_fit_study.md','hardware/eps/design/rev_b_3v3_containment_candidate.md'}
for n,d in docs['files'].items():
 assert hashlib.sha256(subprocess.check_output(['git','show',docs['basis']+':'+n],cwd=ROOT)).hexdigest()==d['before_sha256']
 assert hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==d['after_sha256']
out={'status':'DEVELOPMENT_GRAPH_CLASS_METADATA_CHECKS_PASS;HARDWARE_AND_PRESENTATION_GATES_SEPARATE','physical_parts':345,'nets':186,'functional_nets':173,'endpoints':933,'previous_physical_components_preserved':318,'new_nets_checked':15,'ERC_errors':6,'ERC_warnings':2,'unfinished_MCU_pins':sorted(pins),'class_membership':membership}
(H/'verified.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='class_membership'},indent=2))
if (H/'artifact_sha256.json').exists():
 for n,d in json.loads((H/'artifact_sha256.json').read_text())['files'].items():assert hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==d,n
