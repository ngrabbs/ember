#!/usr/bin/env python3
"""Stock package/identity check, not circuit or assembly qualification."""
from pathlib import Path
from collections import Counter
import json,re,csv,hashlib,subprocess,math,xml.etree.ElementTree as E
H=Path(__file__).resolve().parent;R=H.parents[4]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def unwrap(p):
 d=json.loads(p.read_text())
 if d.get('status')=='fulfilled':d=d['value']
 return json.loads(d['content'][0]['text'])
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
base=json.loads((H/'frozen_baseline.json').read_text())
for p,d in base['files'].items():assert sha(R/p)==d,p
protected=lambda s:s.endswith(('.kicad_sch','.kicad_pcb','.kicad_pro','.kicad_sym','.kicad_mod')) or Path(s).name in {'sym-lib-table','fp-lib-table'}
changed=set()
for args in [['diff','--name-only',base['commit'],'--'],['ls-files','--others','--exclude-standard']]:changed.update(p for p in subprocess.check_output(['git',*args],cwd=R,text=True).splitlines() if protected(p))
allowed={str((H/'fixture'/('control_check'+s)).relative_to(R)) for s in ['.kicad_sch','.kicad_pcb','.kicad_pro']};assert changed==allowed,(changed,allowed)
parts=json.loads((H/'parts.json').read_text());byref={p['reference']:p for p in parts}
functions={
'U1':['IN','IN','B_GATE','DRV','IN_SYS','UVLO','OVP','GND','dVdT','ILIM','MODE','SHDN_N','IMON','FLT_N','PGTH','PGOOD','OUT','OUT',*['NC']*6,'EP_GND'],
'U2':['1A','1B','1Y','2A','2B','2Y','GND','3Y','3A','3B','4Y','4A','4B','VCC'],
'U3':['1RD_N','1D','1CP','1SD_N','1Q','1Q_N','GND','2Q_N','2Q','2SD_N','2CP','2D','2RD_N','VCC'],
'U4':['1A','1B','2Y','GND','2A','2B','1Y','VCC'],
'U5':['A','B','GND','Y','VCC'],'D1':['K','A']}
expected_types={
'U1':['power_in','passive','output','output','power_in','input','input','power_in','passive','passive','input','input','output','open_collector','input','output','power_out','passive',*['no_connect']*6,'passive'],
'U2':['input','input','output','input','input','output','power_in','output','input','input','output','input','input','power_in'],
'U3':['input','input','input','input','output','output','power_in','output','output','input','input','input','input','power_in'],
'U4':['input','input','output','power_in','input','input','output','power_in'],
'U5':['input','input','power_in','output','power_in'],'D1':['passive','passive']}
syms={ref:unwrap(H/f'symbol_{i}.json') for i,ref in enumerate(['U1','U2','U3','U4','U5','D1'])}
fps={ref:unwrap(H/file) for ref,file in [('U1','efuse_no_vias.json'),('U2','footprint_1.json'),('U3','footprint_1.json'),('U4','footprint_2.json'),('U5','footprint_3.json'),('D1','footprint_4.json')]}
# Independent top-view numbering geometry; blank windows handled separately.
def geometry(ref,n):
 if ref=='U1':
  if n<=6:return [-1.9625,-1.25+.5*(n-1),.825,.25]
  if n<=12:return [-1.25+.5*(n-7),1.9625,.25,.825]
  if n<=18:return [1.9625,1.25-.5*(n-13),.825,.25]
  if n<=24:return [1.25-.5*(n-19),-1.9625,.25,.825]
  return [0,0,2.7,2.7]
 if ref in ['U2','U3']:return [-2.8625,-1.95+.65*(n-1),1.475,.4] if n<=7 else [2.8625,1.95-.65*(n-8),1.475,.4]
 if ref=='U4':return [-1.4,-.75+.5*(n-1),1.25,.35] if n<=4 else [1.4,.75-.5*(n-5),1.25,.35]
 if ref=='U5':return [-1.35,.95*(n-2),1.56,.65] if n<=3 else [1.35,.95 if n==4 else -.95,1.56,.65]
 return [-1.4 if n==1 else 1.4,0,1.1,1.1]
board=parse((H/'fixture/control_check.kicad_pcb').read_text());nativefps=kids(board,'footprint');assert len(nativefps)==6
assert float(one(one(board,'setup'),'pad_to_mask_clearance')[1])==.05
rows=[];pad_total=0
for i,ref in enumerate(['U1','U2','U3','U4','U5','D1']):
 sym=syms[ref];count=len(functions[ref]);assert sym['pin_count']==len(sym['pins'])==count
 assert Counter(p['number'] for p in sym['pins'])==Counter(str(n) for n in range(1,count+1))
 assert {p['number']:p['type'] for p in sym['pins']}=={str(n):t for n,t in enumerate(expected_types[ref],1)}
 fp=next(p for p in nativefps if props(p)['Reference']==ref);ps=kids(fp,'pad');lib=fps[ref]
 q=json.loads((H/f'readback_{ref}.json').read_text());live=json.loads(q['pads']['content'][0]['text']);origin=[50+i*15,50]
 assert list(map(float,one(fp,'at')[1:3]))==origin and fp[1]==byref[ref]['footprint']
 assert not kids(fp,'solder_mask_margin')
 assert len(ps)==lib['pad_count']==live['pad_count']==count+(4 if ref=='U1' else 0)
 assert Counter(p[1] for p in ps)==Counter(p['number'] for p in lib['pads'])==Counter(p['number'] for p in live['pads'])
 assert all(not kids(p,'drill') and not kids(p,'solder_mask_margin') for p in ps);pad_total+=len(ps)
 for p in ps:
  n=p[1];xy=list(map(float,one(p,'at')[1:3]));wh=list(map(float,one(p,'size')[1:3]));layers=one(p,'layers')[1:]
  l=[a for a in lib['pads'] if a['number']==n and abs(a['x']-xy[0])<1e-6 and abs(a['y']-xy[1])<1e-6];assert len(l)==1;l=l[0]
  assert all(abs(a-b)<1e-6 for a,b in zip(wh,[l['width'],l['height']])) and set(layers)==set(l['layers'])
  assert p[2:4]==[l['type'],l['shape']] and l['rotation']==0 and l['drill']==[]
  if l['roundrect_rratio'] is not None:assert abs(float(one(p,'roundrect_rratio')[1])-l['roundrect_rratio'])<1e-7
  a=[a for a in live['pads'] if a['number']==n and abs(a['x']-origin[0]-xy[0])<1e-6 and abs(a['y']-origin[1]-xy[1])<1e-6];assert len(a)==1 and a[0]['net']=='' and set(a[0]['layers'])==set(layers)
  if n:
   assert all(abs(a-b)<1e-6 for a,b in zip(xy+wh,geometry(ref,int(n))))
   pin=next(a for a in sym['pins'] if a['number']==n)
   rows.append(dict(reference=ref,MPN=byref[ref]['mpn'],physical_lead=n,function=functions[ref][int(n)-1],symbol_pin=n,symbol_name=pin['name'],symbol_type=pin['type'],pad=n,x_mm=xy[0],y_mm=xy[1],width_mm=wh[0],height_mm=wh[1],view='Component front/top, Xright/Ydown; reconcile manufacturer views per contract'))
  else:assert ref=='U1' and xy in [[-.675,-.675],[-.675,.675],[.675,-.675],[.675,.675]] and wh==[1.09,1.09] and layers==['F.Paste']
assert len(rows)==68 and pad_total==72
with (H/'physical_map.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=rows[0],lineterminator='\n');w.writeheader();w.writerows(rows)
sch=parse((H/'fixture/control_check.kicad_sch').read_text());units=kids(sch,'symbol');assert len(units)==14 and one(sch,'paper')[1]=='B' and not kids(sch,'wire') and not kids(sch,'no_connect')
assert Counter(props(s)['Reference'] for s in units)=={'U1':1,'U2':5,'U3':3,'U4':3,'U5':1,'D1':1}
for s in units:
 p=props(s);ref=p['Reference'];assert p['Value']==p['MFG P/N']==byref[ref]['mpn'] and p['Footprint']==byref[ref]['footprint']
 assert p['Manufacturer']==byref[ref]['mfr'] and p['PackageSize']==byref[ref]['pkg']
x=E.parse(H/'fixture.xml').getroot();cs=x.findall('components/comp');assert len(cs)==6
for c in cs:
 ref=c.get('ref');fields={f.get('name'):f.text for f in c.findall('fields/field')}
 assert c.findtext('value')==fields['MFG P/N']==byref[ref]['mpn'] and c.findtext('footprint')==byref[ref]['footprint']
nets=[tuple(sorted((n.get('ref'),n.get('pin')) for n in net.findall('node'))) for net in x.findall('nets/net')]
assert len(nets)==65 and sum(map(len,nets))==68 and len({a for net in nets for a in net})==68
assert {a for net in nets for a in net}=={(ref,str(n)) for ref,fs in functions.items() for n in range(1,len(fs)+1)}
assert set(n for n in nets if len(n)>1)=={(('U1','1'),('U1','2')),(('U1','17'),('U1','18')),(('U1','25'),('U1','8'))}
assert sum(len(a.findall('pins/pin')) for a in x.findall('libparts/libpart'))==68
v=[a for s in json.loads((H/'erc.json').read_text())['sheets'] for a in s['violations']]
assert Counter((a['severity'],a['type']) for a in v)=={('error','pin_not_connected'):59,('error','pin_not_driven'):27,('error','power_pin_not_driven'):11}
# Verify the new MCP presentation operation preserved everything except field presentation.
def flatten(n):
 if 'atom' in n:return n['atom']
 if 'string' in n:return n['string']
 return [flatten(v) for v in n['list']]
def strip(n):
 if not isinstance(n,list):return n
 if n and n[0]=='property':return n[:3]
 return [strip(a) for a in n if not (isinstance(a,list) and a and a[0]=='fields_autoplaced')]
before=json.loads((H/'items_before.json').read_text())['items'];after=json.loads((H/'items_after.json').read_text())['items'];assert len(before)==len(after)
for a,b in zip(before,after):assert a['kind']==b['kind'] and strip(flatten(a['node']))==strip(flatten(b['node']))
y=E.parse(H/'before_presentation.xml').getroot()
def graph(root):return (sorted((c.get('ref'),c.findtext('value'),c.findtext('footprint'),sorted((f.get('name'),f.text) for f in c.findall('fields/field'))) for c in root.findall('components/comp')),sorted(tuple(sorted((n.get('ref'),n.get('pin')) for n in net.findall('node'))) for net in root.findall('nets/net')))
assert graph(x)==graph(y)
field_state=json.loads((H/'field_presentation_after.json').read_text())
for s in field_state['symbols']:
 fs={f['name']:f for f in s['fields']}
 visible=lambda f:not any(flatten(n)==['hide','yes'] for n in f['nodes'])
 assert visible(fs['Reference']) and visible(fs['Value'])==(s['unit']==1) and not visible(fs['MFG P/N'])
 assert not s['fields_autoplaced']
# Raw paste area counts rounded corners; TI example78% is not the stock pattern.
ep_paste_area=4*(1.09**2-(4-math.pi)*(.229358*1.09)**2)
result=dict(status='68_LEAD_STOCK_CONTACT_MAPPING_VERIFIED_ASSEMBLY_AND_CIRCUIT_OPEN',preserved_native_files=len(base['files']),fixture_physical_parts=6,placed_symbol_units=14,physical_leads=68,CLI_unique_endpoints=68,CLI_nets=65,raw_board_pads=72,blank_paste_only=4,drills=0,ERC_errors=len(v),ERC_warnings=0,presentation_only_identity_and_netlist_preserved=True,efuse_EP_stock_paste_fraction=ep_paste_area/2.7**2,TI_EP_paste_example_fraction=.78,efuse_embedded_0p20_drill_variant_rejected=True,real_EPS_circuit_mutated=False,qualification=False,limits=['Unwired package fixture, no complete ERC/policy/circuit acceptance','Generic copper/paste differ from manufacturer example lands','Full layout rectangles must supplement stock notched courtyards','Generic board package Values overlap; board is not an assembly drawing/export','Thermal-via layout, stencil/voiding and board thermal behavior remain open','PGOOD stock output type retained despite actual open-drain behavior','Timing/brownout/cutoff/SOA and hardware/flight qualification remain open'])
(H/'verified.json').write_text(json.dumps(result,indent=2)+'\n')
(H/'native_source_sha256.json').write_text(json.dumps({str(p.relative_to(R)):sha(p) for p in (H/'fixture').iterdir() if protected(p.name)},indent=2)+'\n')
print(json.dumps(result,indent=2))
