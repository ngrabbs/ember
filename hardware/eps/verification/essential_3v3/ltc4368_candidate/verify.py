"""Native library/pad/fixture checks; source-page visual and circuit gates separate."""
from pathlib import Path
import collections,hashlib,json,re,subprocess,sys,xml.etree.ElementTree as E
H=Path(__file__).resolve().parent;ROOT=H.parents[4]
sys.path.insert(0,str(ROOT/'hardware/eps/verification/rev_b/swd_integration'))
from common import parse,kids,one,props
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
b=json.loads((H/'baseline.json').read_text());lib='hardware/eps/rev_b/libraries/Ember_Charger_BMS_Review.kicad_sym'
allowed={lib,'hardware/eps/design/rev_b_completion.md','hardware/eps/design/rev_b_3v3_containment_candidate.md'}
for p,digest in b['files'].items():
 if p not in allowed:assert sha(ROOT/p)==digest,p
old=subprocess.check_output(['git','show',b['basis']+':'+lib],cwd=ROOT).decode();new=(ROOT/lib).read_text()
def exact_symbols(s):
 tokens=list(re.finditer(r'"(?:\\.|[^"\\])*"|[()]|[^()\s]+',s));depth=0;start=None;out={}
 for i,m in enumerate(tokens):
  if m[0]=='(':
   if depth==1 and tokens[i+1][0]=='symbol':start=m.start();name=json.loads(tokens[i+2][0]);assert name not in out,name
   depth+=1
  elif m[0]==')':
   depth-=1
   if depth==1 and start is not None:out[name]=s[start:m.end()];start=None
 return out
os,ns=exact_symbols(old),exact_symbols(new)
assert set(ns)==set(os)|{'LTC4368IMS_1_REVIEW'}
for name in os:assert ns[name]==os[name],name
mapnames={'1':'VIN','2':'UV','3':'OV','4':'RETRY','5':'GND','6':'~{SHDN}','7':'~{FAULT}','8':'VOUT','9':'SENSE','10':'GATE'}
types={'1':'power_in','2':'input','3':'input','4':'bidirectional','5':'power_in','6':'input','7':'open_collector','8':'input','9':'input','10':'output'}
sym=json.loads((H/'final_symbol_query.json').read_text());assert len(sym['pins'])==10
assert {x['number']:x['name'] for x in sym['pins']}==mapnames
assert {x['number']:x['type'] for x in sym['pins']}==types
foot=json.loads((H/'final_footprint_query.json').read_text());saved=json.loads((H/'final_saved_pads_query.json').read_text())
expected_count=collections.Counter({str(i):1 for i in range(1,11)});expected_count['']=10
assert len(foot['pads'])==len(saved['pads'])==20
assert collections.Counter(p['number'] for p in foot['pads'])==expected_count
assert collections.Counter(p['number'] for p in saved['pads'])==expected_count
for i in range(1,11):
 left=i<=5;x=-2.1055 if left else 2.1055;y=-1+(i-1)*.5 if left else 1-(i-6)*.5
 p=next(p for p in foot['pads'] if p['number']==str(i));assert abs(p['x']-x)<1e-9 and abs(p['y']-y)<1e-9
 assert p['width']==.889 and p['height']==.305 and set(p['layers'])=={'F.Cu','F.Paste'} and not p['drill']
 blanks=[q for q in foot['pads'] if q['number']=='' and abs(q['x']-x)<1e-9 and abs(q['y']-y)<1e-9]
 assert len(blanks)==1;z=blanks[0];assert z['width']==.969 and z['height']==.385 and z['layers']==['F.Mask']
 s=next(p for p in saved['pads'] if p['number']==str(i));assert abs(s['x']-(x+100))<1e-9 and abs(s['y']-(y+100))<1e-9
# Raw saved geometry is needed because get_component_pads omits dimensions and settings.
board=H/'disposable/final/ltc4368_final.kicad_pcb';ast=parse(board.read_text());bp=one(ast,'footprint');pads=kids(bp,'pad')
assert len(pads)==20 and collections.Counter(x[1] for x in pads)==expected_count
for p in pads:
 at=list(map(float,one(p,'at')[1:3]));size=list(map(float,one(p,'size')[1:3]));layers=set(one(p,'layers')[1:])
 match=[q for q in foot['pads'] if q['number']==p[1] and all(abs(a-q[k])<1e-9 for a,k in zip(at,['x','y']))];assert len(match)==1
 q=match[0];assert size==[q['width'],q['height']] and layers==set(q['layers']) and not kids(p,'drill')
setup=one(ast,'setup');margin=float(one(setup,'pad_to_mask_clearance')[1]);assert margin==.05
# Assert actually exported final mask polygons, including the inherited-margin test.
def maskrects(name):
 out=[]
 for p in E.parse(H/name).getroot().iter():
  if p.tag.endswith('path') and 'fill:#D864FF' in p.get('style',''):
   xy=re.findall(r'([-+]?\d+(?:\.\d+)?),([-+]?\d+(?:\.\d+)?)',p.get('d',''))
   if xy:
    xs=[float(x) for x,y in xy];ys=[float(y) for x,y in xy]
    if 94<min(xs)<106 and 94<min(ys)<106:out.append((max(xs)-min(xs),max(ys)-min(ys)))
 return out
mr=maskrects('final_mask.svg');assert len(mr)==10
assert all(abs(w-.969)<1e-7 and abs(h-.385)<1e-7 for w,h in mr),mr
oldmask=maskrects('mask.svg');assert len(oldmask)==20 # overlapping auto and explicit openings in diagnostic fixture
assert any(abs(w-.989)<1e-7 and abs(h-.405)<1e-7 for w,h in oldmask)
xml=E.parse(H/'final_fixture.xml').getroot();cs=xml.findall('./components/comp');assert len(cs)==1 and cs[0].get('ref')=='U1'
assert cs[0].findtext('footprint')=='Ember_Charger_BMS_Review:ADI_MS10_05_08_1661_REVIEW'
fields={p.get('name'):p.text for p in cs[0].findall('fields/field')};assert fields['MFG P/N']=='LTC4368IMS-1#TRPBF'
ends=[(x.get('ref'),x.get('pin')) for x in xml.findall('./nets/net/node')];assert len(ends)==10 and set(ends)=={('U1',str(i)) for i in range(1,11)}
erc=json.loads((H/'final_erc.json').read_text());vs=[v for s in erc['sheets'] for v in s['violations']]
assert collections.Counter((v['severity'],v['type']) for v in vs)=={('error','pin_not_connected'):10,('error','pin_not_driven'):5,('error','power_pin_not_driven'):2}
for table in ['sym-lib-table','fp-lib-table']:assert '${KIPRJMOD}/../../../../../rev_b/libraries/' in (H/'disposable/final'/table).read_text()
# Bind the actual inspected current native sources/images and archived run artifacts.
vr=json.loads((H/'visual_review.json').read_text())
for category in ['actually_opened_and_inspected','bound_native_sources']:
 for name,digest in vr[category].items(): assert sha(ROOT/name)==digest,name
assert vr['manufacturer_source_pixels_inspected'] is False
for group in ['gate','connected']:
 results=json.loads((H/f'{group}_results.json').read_text())
 assert len(results['cases'])==(8 if group=='gate' else 3)
 for name,c in results['cases'].items():
  assert c['status']=='completed' and c['returncode']==0
  assert sha(H/f'{group}_decks'/f'{name}.cir')==c['portable_deck_sha256']
  assert sha(H/f'{group}_logs'/f'{name}.log')==c['normalized_log_sha256']
  assert 'Total elapsed time:' in (H/f'{group}_logs'/f'{name}.log').read_text()
  if group=='connected':
   assert c['observed_below3V_after_step'] and c['load_step_window_out_min_V']<3
   assert c['out_min_time_s']>=c['load_step_window_s'][0]
report={'status':'CONSTRUCTION_GEOMETRY_CHECK_PASS_SOURCE_VISUAL_AND_CIRCUIT_ACCEPTANCE_OPEN','exact_old_symbol_subtrees_preserved':len(os),'frozen_prior_files_checked':len(b['files'])-len([p for p in allowed if p in b['files']]),'electrical_pins':10,'raw_final_saved_and_library_pad_objects_each':20,'final_effective_mask_expansion_mm':.04,'final_mask_web_mm':.115,'diagnostic_inherited_mask_expansion_mm':.05,'ERC_errors':17,'ERC_warnings':0,'no_main_circuit_or_PCB_mutation':True,'limits':['Manufacturer drawing pixels not yet accessible; web text/source map reviewed.','Footprint Fab Value field overflow remains tool-limited; numbered lands readable.','Library custom sourcing defaults not exposed; fixture instance metadata set/read back.','Circuit supply/gate/PVT/fault and hardware qualification remain open.']}
(H/'verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

manifest=H/'artifact_sha256.json'
if manifest.exists():
 for name,digest in json.loads(manifest.read_text())['files'].items():assert sha(ROOT/name)==digest,name
 print('Portable artifact manifest: PASS')
