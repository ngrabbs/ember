"""Check exported AON topology and accepted physical-map readback."""
NAME='payload_aon_acceptance'
from pathlib import Path
import json,re,math
base=Path(__file__).resolve().parent / NAME
stem=base/NAME
text=stem.with_suffix('.net').read_text()
nets={}
for block in text.split('\n\t\t(net\n')[1:]:
    name=re.search(r'\(name "([^"]+)"\)',block)[1]
    nets[name]=set(re.findall(r'\(node\s*\(ref "([^"]+)"\)\s*\(pin "([^"]+)"\)',block))
def net(name, members):
    assert nets[name]==set(members), (name,nets[name],members)
def value(ref,want):
    assert re.search(r'\(ref "'+ref+r'"\)\s*\(value "([^"]+)"\)',text)[1]==want
checks=json.loads(Path(str(stem)+'-checks.json').read_text())
checks={k:json.loads(v['content'][0]['text']) for k,v in checks.items()}
for k,f in [('wires','floating_count'),('pins','unconnected_count'),('shorts','short_count'),('orphans','orphan_count'),('overlaps','overlap_count')]:
    assert checks[k][f]==0
assert not checks['overlaps']['bounds_unresolved']
e=json.loads(Path(str(stem)+'-package-evidence.json').read_text())
e={k:json.loads(v['content'][0]['text']) for k,v in e.items()}

assert len(nets)==7
net('VDC',[('C1','1'),('C2','1'),('U1','3'),('U1','4')])
net('+3V3',[('L1','2'),('C5','1'),('C6','1'),('U1','8')])
net('/AON_SW',[('U1','5'),('L1','1'),('C3','2')])
net('/AON_BOOT',[('U1','6'),('C3','1')])
net('/AON_INT_VCC',[('U1','7'),('U1','1'),('C4','1')])
net('GND',[(f'C{i}','2') for i in [1,2,4,5,6]]+[('U1','9')])
net('unconnected-(U1-PGOOD-Pad2)',[('U1','2')])
for ref,want in {'U1':'LMR36506R3RPER','L1':'15u','C1':'10u / 50V','C2':'100n / 50V','C3':'100n / 16V','C4':'1u / 16V','C5':'22u / 10V','C6':'22u / 10V'}.items(): value(ref,want)
assert checks['erc']['errors']==checks['erc']['warnings']==0
mapping={'1':('RT','passive'),'2':('PGOOD','open_collector'),'3':('EN/UVLO','input'),'4':('VIN','power_in'),'5':('SW','output'),'6':('BOOT','passive'),'7':('VCC','power_out'),'8':('VOUT/BIAS','input'),'9':('GND','power_in')}
assert {q['number']:(q['name'],q['type']) for q in e['symbol']['pins']}==mapping
f=e['footprint']; pads=e['placed_pads']
assert f['pad_count']==pads['pad_count']==23 and pads['source']=='file'
cu=[q for q in f['pads'] if 'F.Cu' in q['layers']]
assert len(cu)==13 and {q['number'] for q in cu}==set(mapping)
expected={'1':[(-.825,-.738,.75,.225),(-.65,-.9125,.4,.575)],'2':[(-.9,-.25,.6,.25)],'3':[(-.9,.25,.6,.25)],'4':[(-.85,.738,.7,.225),(-.7,.9125,.4,.575)],'5':[(.85,.738,.7,.225),(.7,.9125,.4,.575)],'6':[(.9,.25,.6,.25)],'7':[(.9,-.25,.6,.25)],'8':[(.825,-.738,.75,.225),(.65,-.9125,.4,.575)],'9':[(0,-.55,.35,1.3)]}
for n,coords in expected.items():
    got=[q for q in cu if q['number']==n]
    assert len(got)==len(coords)
    for q,coord in zip(got,coords):
        assert all(math.isclose(q[k],v,abs_tol=1e-9) for k,v in zip(['x','y','width','height'],coord))
for q,a in zip(f['pads'],pads['pads']):
    assert q['type']=='smd' and q['drill']==[] and q['rotation']==0
    assert a['number']==q['number'] and a['net']==''
    assert set(a['layers'])==set(q['layers'])
    assert math.isclose(a['x'],20+q['x']) and math.isclose(a['y'],20+q['y'])
assert sum(q['number']=='' and q['layers']==['F.Paste'] for q in f['pads'])==10
assert e['instance']['lib_id']=='EMBER_Payload:LMR36506R3RPER'
assert e['instance']['rotation']==0 and not e['instance']['mirror_x'] and not e['instance']['mirror_y']
print(json.dumps({'physical_leads':9,'numbered_copper_primitives':13,'paste_only_primitives':10,'exported_nets':7,'erc_errors':0,'erc_warnings':0,'result':'PASS for prototype package map and standalone schematic'},indent=2))
