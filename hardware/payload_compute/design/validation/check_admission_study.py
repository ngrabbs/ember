"""Check USB clamp exported topology and accepted MOSFET readback."""
NAME='payload_admission_acceptance'
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

assert len(nets)==13
net('/EFUSE_EN',[('U1','1'),('R1','2'),('R2','1'),('Q1','3'),('C1','1')])
net('/CLAMP_G',[('Q1','1'),('Q2','3'),('R3','2'),('R4','1')])
net('/GRANT_RX',[('R5','2'),('R6','1'),('Q2','1')])
net('/ADMISSION_GRANT',[('R5','1')])
net('/OV_SENSE',[('U1','2'),('R7','2'),('R8','1')])
net('/DVDT',[('U1','7'),('C2','1')])
net('/ILM',[('U1','9'),('R9','1')])
net('+15V',[('U1','6'),('C3','1')])
net('VDC',[('U1','5'),('R1','1'),('R3','1'),('R7','1'),('C4','1')])
net('GND',[('U1','8'),('Q1','2'),('Q2','2')]+[(f'R{i}','2') for i in [2,4,6,8,9]]+[(f'C{i}','2') for i in [1,2,3,4]])
for n,pin in [('AUXOFF','3'),('ITIMER','10'),('~{FLT}','4')]: net('unconnected-(U1-'+n+'-Pad'+pin+')',[('U1',pin)])
for ref,want in {'U1':'TPS259470LRPWR','Q1':'PMV16XNR','Q2':'PMV16XNR','R1':'374k / 0.1%','R2':'37.4k / 0.1%','R3':'20k / 1%','R4':'10k / 1%','R5':'100R / 1%','R6':'1k / 1%','R7':'365k / 0.1%','R8':'29.4k / 0.1%','R9':'1.65k / 0.1%','C1':'4.7n / 16V','C2':'10n / 50V','C3':'100u / 35V','C4':'10u / 50V'}.items(): value(ref,want)
assert checks['erc']['errors']==0 and checks['erc']['warnings']==1
assert checks['erc']['violations'][0]['rule']=='isolated_pin_label'
assert 'ADMISSION_GRANT' in checks['erc']['violations'][0]['description']
assert {q['number']:q['name'] for q in e['symbol']['pins']}=={'1':'G','2':'S','3':'D'}
f=e['footprint']; pads=e['placed_pads']
assert f['pad_count']==pads['pad_count']==3 and pads['source']=='file'
coords={'1':(-.9375,-.95),'2':(-.9375,.95),'3':(.9375,0)}
for q,a in zip(f['pads'],pads['pads']):
    x,y=coords[q['number']]
    assert math.isclose(q['x'],x) and math.isclose(q['y'],y)
    assert q['width']==1.475 and q['height']==.6 and q['drill']==[]
    assert set(q['layers'])=={'F.Cu','F.Mask','F.Paste'}
    assert a['number']==q['number'] and a['net']==''
    assert math.isclose(a['x'],20+x) and math.isclose(a['y'],20+y)
assert e['instance']['lib_id']=='Transistor_FET:Q_NMOS_GSD'
print(json.dumps({'physical_leads':3,'exported_nets':13,'erc_errors':0,'external_boundary_warnings':1,'result':'PASS for exported topology; electrical default-off qualification remains open'},indent=2))
