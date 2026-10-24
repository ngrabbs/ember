#!/usr/bin/env python3
"""Read-only native inspection for geometry/visibility unavailable in exports."""
from pathlib import Path
from collections import Counter
import json,re,hashlib,subprocess,xml.etree.ElementTree as E,csv
H=Path(__file__).resolve().parent;ROOT=H.parents[4]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
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
def kids(n,k):return [x for x in n if isinstance(x,list) and x and x[0]==k]
def one(n,k):return kids(n,k)[0]
def props(n):return {p[1]:p[2] for p in kids(n,'property')}
def unwrap(p):return json.loads(json.loads(p.read_text())['content'][0]['text'])
base=json.loads((H/'frozen_baseline.json').read_text())
for p,h in base['files'].items():assert sha(ROOT/p)==h,p
protected=lambda s:s.endswith(('.kicad_sch','.kicad_pcb','.kicad_pro','.kicad_sym','.kicad_mod')) or Path(s).name in {'sym-lib-table','fp-lib-table'}
changed=set()
for args in [['diff','--name-only',base['commit'],'--'],['ls-files','--others','--exclude-standard']]:
 changed.update(p for p in subprocess.check_output(['git',*args],cwd=ROOT,text=True).splitlines() if protected(p))
allowed={str((H/'fixture'/('payload_stock_check'+s)).relative_to(ROOT)) for s in ['.kicad_sch','.kicad_pcb','.kicad_pro']}
assert changed==allowed,(changed,allowed)
expected={'Q1':{'1':('G','input'),'2':('S','passive'),'3':('D','passive')},'U1':{'1':('K','passive'),'2':('A','passive'),'3':('NC','no_connect')}}
mpn={'Q1':'T2N7002AK,LM','U1':'LM4040CEM3-2.5/NOPB'}
lib=unwrap(H/'stock_footprint.json');assert lib['pad_count']==3
sch=parse((H/'fixture/payload_stock_check.kicad_sch').read_text());ss=kids(sch,'symbol');assert len(ss)==2
assert one(sch,'paper')[1]=='B' and not kids(sch,'wire') and not kids(sch,'no_connect')
visibility={}
for s in ss:
 p=props(s);ref=p['Reference'];assert p['Value']==p['MFG P/N']==mpn[ref]
 assert p['Footprint']=='Package_TO_SOT_SMD:SOT-23' and p['PackageSize']=={'Q1':'SOT23 / TO-236AB','U1':'DBZ / SOT-23'}[ref]
 assert p['Manufacturer']=={'Q1':'Toshiba','U1':'Texas Instruments'}[ref]
 visibility[ref]={x[1]:bool(kids(x,'hide')) or 'hide' in one(x,'effects') for x in kids(s,'property')}
 assert visibility[ref]['MFG P/N'] and not visibility[ref]['Value']
for ref,name in [('Q1','helper'),('U1','reference')]:
 sym=unwrap(H/('symbol_'+name+'.json'));assert sym['pin_count']==3
 assert {p['number']:(p['name'],p['type']) for p in sym['pins']}==expected[ref]
board=parse((H/'fixture/payload_stock_check.kicad_pcb').read_text());fps=kids(board,'footprint');assert len(fps)==2
rows=[]
for fp in fps:
 ref=props(fp)['Reference'];assert props(fp)['Value']=='SOT-23'
 assert fp[1]=='Package_TO_SOT_SMD:SOT-23'
 origin=[50,50] if ref=='Q1' else [65,50];assert list(map(float,one(fp,'at')[1:3]))==origin
 pads=kids(fp,'pad');live=unwrap(H/(ref+'_pads.json'));assert len(pads)==live['pad_count']==3
 assert Counter(p[1] for p in pads)==Counter('123')==Counter(p['number'] for p in live['pads'])
 for p in pads:
  n=p[1];l=next(q for q in lib['pads'] if q['number']==n);a=next(q for q in live['pads'] if q['number']==n)
  xy=list(map(float,one(p,'at')[1:3]));size=list(map(float,one(p,'size')[1:3]))
  assert xy==[l['x'],l['y']] and size==[l['width'],l['height']]==[1.475,.6]
  assert p[2:4]==['smd','roundrect'] and not kids(p,'drill')
  assert float(one(p,'roundrect_rratio')[1])==.25
  assert set(one(p,'layers')[1:])==set(a['layers'])=={'F.Cu','F.Paste','F.Mask'}
  assert abs(a['x']-origin[0]-xy[0])<1e-6 and abs(a['y']-origin[1]-xy[1])<1e-6 and a['net']==''
  rows.append(dict(ref=ref,physical_lead=n,function=expected[ref][n][0],symbol_type=expected[ref][n][1],pad=n,x_mm=xy[0],y_mm=xy[1],width_mm=size[0],height_mm=size[1]))
x=E.parse(H/'fixture.xml').getroot();cs=x.findall('components/comp');assert len(cs)==2
for c in cs:
 ref=c.get('ref');fields={f.get('name'):f.text for f in c.findall('fields/field')}
 assert c.findtext('value')==fields['MFG P/N']==mpn[ref]
 assert c.findtext('footprint')=='Package_TO_SOT_SMD:SOT-23'
assert sum(len(s.findall('pins/pin')) for s in x.findall('libparts/libpart'))==6
v=[v for s in json.loads((H/'erc.json').read_text())['sheets'] for v in s['violations']]
assert Counter(vv['type'] for vv in v)=={'pin_not_connected':5,'pin_not_driven':1}
assert all(vv['severity']=='error' for vv in v)
with (H/'physical_map.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=rows[0],lineterminator='\n');w.writeheader();w.writerows(rows)
source={str(p.relative_to(H)):sha(p) for p in (H/'fixture').iterdir() if p.suffix in {'.kicad_sch','.kicad_pcb','.kicad_pro'}}
(H/'native_source_sha256.json').write_text(json.dumps(source,indent=2)+'\n')
result=dict(status='STOCK_PIN_PAD_MAPPING_VERIFIED_CONDITIONAL_ASSEMBLY',preserved_native_files=len(base['files']),fixture_parts=2,physical_pads=6,erc_errors=6,erc_clean=False,field_visibility=visibility,real_EPS_mutated=False,electrical_acceptance=False,full_land_and_courtyard_acceptance=False,limitations=['Unconnected package fixture, not a circuit','U1 hidden NC3 intentionally floating','Board values generic SOT-23; not assembly exports','Q1 full 4.0x3.5 mm placement reservation required','U1 max mold-flash/courtyard and both assembly lands remain open','Generic fixture ERC defaults are retained; no circuit/ERC policy acceptance claimed'])
(H/'verified.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='field_visibility'},indent=2))
