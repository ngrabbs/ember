#!/usr/bin/env python3
"""Verify the declared charger topology against the full root, without CAD writes."""
from pathlib import Path
from collections import Counter
import csv, fnmatch, hashlib, json, re, subprocess, sys, xml.etree.ElementTree as E

H=Path(__file__).resolve().parent; ROOT=H.parents[4]; P=ROOT/'hardware/eps/rev_b'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def graph(path):
    r=E.parse(path).getroot(); raw=r.findall('./components/comp')
    refs=[c.get('ref') for c in raw]; assert len(refs)==len(set(refs)),Counter(refs)
    nodes=[(x.get('ref'),x.get('pin')) for n in r.findall('./nets/net') for x in n.findall('node')]
    assert len(nodes)==len(set(nodes)),[p for p,c in Counter(nodes).items() if c!=1]
    names=[n.get('name') for n in r.findall('./nets/net')];assert len(names)==len(set(names))
    return r,{c.get('ref'):c for c in raw},{n.get('name'):{(x.get('ref'),x.get('pin')) for x in n.findall('node')} for n in r.findall('./nets/net')}
old,oc,on=graph(H/'before.xml');new,nc,nn=graph(H/'eps_rev_b.xml')
assert len(oc)==160 and len(nc)==187 and len(nn)==103
def metadata(c):
    return {k:c.findtext(k) or '' for k in ['value','footprint','datasheet','tstamps']}|{'libsource':c.find('libsource').attrib,'fields':{x.get('name'):x.text or '' for x in c.findall('./fields/field')}}
for ref,c in oc.items():assert metadata(c)==metadata(nc[ref]),ref
assert len({c.findtext('tstamps') for c in nc.values()})==187
newrefs={'U300','Q300','Q301','L300','J300',*[f'R{i}' for i in range(300,304)],*[f'C{i}' for i in range(300,312)],*[f'TP{i}' for i in range(300,303)],'R108','R109','R110'}
assert set(nc)-set(oc)==newrefs and len(newrefs)==27
assert nc['R108'].findtext('tstamps')=='9f83d964-b5bb-49bc-ad4b-888beb34efff'
assert nc['R109'].findtext('tstamps')=='aa69f80c-62be-4650-bf5d-50c12616184f'
assert nc['R110'].findtext('tstamps')=='6f2c5373-433f-4800-8884-4a6cd8365854'

# This expected graph is specified from the reviewed circuit, not copied from XML.
prefix='/Charger PowerPath/'
ep=lambda *a:{tuple(x.split('.')) for x in a}
added={
    'VIN_CHG':ep('U300.7','Q300.1','Q300.2','Q300.3','C308.1'),
    'SYS_PWR_PERMITTED':ep('R300.2','Q301.5','U300.3','U300.4','U300.27','U300.28','C300.1','C301.1','C302.1','C303.1','C309.1'),
    '+3V3':ep('U300.15','C310.1','R108.1','R109.1','R110.1'),
    'GND':ep('U300.16','U300.23','U300.24','U300.29','R302.2','J300.2','TP302.1')|{(f'C{i}','2') for i in range(300,311)},
    'BATT_PERMITTED':ep('Q301.1','Q301.2','Q301.3','R301.2','U300.19','U300.20','C304.1','C305.1'),
    '5V0_CHG_INTVCC':ep('U300.2','U300.18','C306.1'),
    '2V5_CHG_LOGIC':ep('U300.8','U300.17','C307.1'),
    'EPS_CHG_SCL':ep('U100.30','U300.13','R108.2'),
    'EPS_CHG_SDA':ep('U100.31','U300.14','R109.2'),
    'EPS_CHG_ALERT_N':ep('U100.18','U300.12','R110.2'),
    prefix+'CHG_CLP':ep('Q300.5','R300.1','U300.5'),
    prefix+'CHG_CSP':ep('L300.2','R301.1','U300.21'),
    prefix+'CHG_SW':ep('U300.25','U300.26','L300.1','C311.2'),
    prefix+'CHG_BOOST':ep('U300.1','C311.1'),
    prefix+'CHG_INFET_GATE':ep('U300.6','Q300.4'),
    prefix+'CHG_BATFET_GATE':ep('U300.22','Q301.4'),
    prefix+'CHG_RT':ep('U300.11','R302.1'),
    prefix+'CHG_NTCBIAS':ep('U300.9','R303.1','TP300.1'),
    prefix+'THM_CHG_NTC':ep('U300.10','R303.2','J300.1','TP301.1'),
}
expected={n:set(v) for n,v in on.items()}
moved=ep('U100.18','U100.30','U100.31')
removed={n for n,v in on.items() if v<=moved}
assert len(removed)==3 and all(n.startswith('unconnected-') for n in removed)
for n in removed:del expected[n]
for n,v in added.items():expected.setdefault(n,set()).update(v)
assert nn==expected,[(n,sorted(v),sorted(nn.get(n,set()))) for n,v in expected.items() if nn.get(n)!=v]
assert nn[prefix+'CHG_BOOST']==ep('U300.1','C311.1')
assert nn[prefix+'CHG_BATFET_GATE']==ep('U300.22','Q301.4')
assert nn['VIN_CHG'].isdisjoint(nn['SYS_PWR_PERMITTED']) and nn['BATT_PERMITTED'].isdisjoint(nn['SYS_PWR_PERMITTED'])
assert not any('VSS' in n for n in added)
assert len({p for n,v in added.items() for p in v if p[0]=='U300'})==29
# Every new physical terminal and every migrated MCU terminal has exactly one full-net check.
physical=set().union(*added.values());actual_new={p for v in nn.values() for p in v if p[0] in newrefs}
assert actual_new=={p for p in physical if p[0] in newrefs}
for r in newrefs:
    assert {(r,p.get('num')) for p in nc[r].findall('./units/unit/pins/pin')}=={p for p in actual_new if p[0]==r},r
rows=[]
for n,v in added.items():
    for r,p in sorted(v):rows.append({'reference':r,'pin':p,'net':n,'complete_endpoint_set':';'.join(a+'.'+b for a,b in sorted(nn[n]))})
with (H/'endpoint_contract.csv').open('w') as f:
    w=csv.DictWriter(f,fieldnames=rows[0],lineterminator='\n');w.writeheader();w.writerows(rows)

fields={r:metadata(c)['fields'] for r,c in nc.items()}
mpns={'U300':'LTC4162IUFD-LADM#TRPBF','Q300':'CSD18543Q3A','Q301':'CSD18543Q3A','L300':'XAL6060-153MEC','R300':'CRF1206-FZ-R033ELF','R301':'CRF1206-FZ-R033ELF','R302':'TNPW060363K4BEEA','R303':'TNPW060310K0BEEA','J300':'BM02B-GHS-TBT(LF)(SN)'}
for r in ['R108','R109','R110']:mpns[r]='TNPW06034K70BEEA'
for i in range(300,307):mpns[f'C{i}']='CGA5L1X7R1H106K160AC'
mpns.update({'C307':'GRM21BR71A475KE51L','C308':'GRM188R72A104KA35D','C309':'GRM188R72A104KA35D','C310':'GRM188R72A104KA35D','C311':'GRM188R72A223KAC4D'})
for r in ['TP300','TP301','TP302']:mpns[r]='PCB copper test feature; not procured'
for r,m in mpns.items():assert fields[r]['MFG P/N']==m and nc[r].findtext('footprint'),r
for r in ['R300','R301']:assert fields[r]['Power']=='1 W P70' and fields[r]['Tolerance']=='1%'
for r in ['R302','R303']:assert fields[r]['Power']=='0.11 W general P70' and fields[r]['Tolerance']=='0.1%'
for r in ['R108','R109','R110']:assert fields[r]['Power']=='0.110 W general P70' and nc[r].findtext('value')=='4.7k'
for i in range(300,312):
    f=fields[f'C{i}'];assert f['Dielectric']=='X7R' and f['Tolerance']=='10%'
    assert f['Voltage']==('50 V' if i<=306 else '10 V' if i==307 else '100 V')
assert fields['U300']['Review']=='CUSTOM — REVIEW REQUIRED'
for r in ['Q300','Q301']:assert fields[r]['Review']=='CUSTOM FOOTPRINT — REVIEW REQUIRED'
native_charger=(P/'charger.kicad_sch').read_text()
assert 'External BATT_PERMITTED development fixture only; future BMS+RBF absent' in native_charger
assert 'Real internal INTVCC diode / SW bootstrap energy; not independent supply' in native_charger
assert 'Actual passive charger PowerPath output; supersedes earlier external SYS fixture' in (P/'essential_3v3.kicad_sch').read_text()
(H/'fields_readback.json').write_text(json.dumps({r:metadata(nc[r]) for r in sorted(newrefs)},indent=2)+'\n')

rb=json.loads((H/'readback.json').read_text());pins=rb['symbols']['pins']
assert len(pins)==29 and {p['number'] for p in pins}==set(map(str,range(1,30)))
assert [p['type'] for p in pins if p['number'] in ['25','26']]==['power_out','power_out']
assert {p['number']:p['name'] for p in rb['fet_symbol']['pins']}=={'1':'S','2':'S','3':'S','4':'G','5':'D'}
for ref in ['Q300','Q301']:
    z=next(c for c in rb['charger_pins']['components'] if c['reference']==ref)
    assert len(z['pins'])==5 and len({(p['x'],p['y']) for p in z['pins'] if p['number'] in ['1','2','3']})==1
for k,v in rb['packages'].items():
    assert v['pad_count']==len(v['pads'])
    if 'CSD18543' in k:assert Counter(p['number'] for p in v['pads'])=={'1':1,'2':1,'3':1,'4':1,'5':5,'':21}
    elif 'UFD' in k:assert {p['number'] for p in v['pads']}==set(map(str,range(1,30)))

erc=json.loads((H/'erc.json').read_text());viol=[v for s in erc['sheets'] for v in s['violations']]
assert Counter((v['severity'],v['type']) for v in viol)=={('error','pin_not_connected'):13,('error','pin_to_pin'):1}
pair=next(v for v in viol if v['type']=='pin_to_pin');assert {i['description'].split(' Pin ')[1].split(' ')[0] for i in pair['items']}=={'25','26'}
assert all('U300' in i['description'] for i in pair['items'])

# Native project settings are read only; match saved patterns to the CLI root graph.
proj=json.loads((P/'eps_rev_b.kicad_pro').read_text())
baseproj=json.loads(subprocess.check_output(['git','show','8d03a76:hardware/eps/rev_b/eps_rev_b.kicad_pro'],cwd=ROOT,text=True))
assert {k:v for k,v in proj.items() if k!='net_settings'}=={k:v for k,v in baseproj.items() if k!='net_settings'}
patterns=proj['net_settings']['netclass_patterns'];bp=baseproj['net_settings']['netclass_patterns']
assert all(p in patterns for p in bp)
assert all(c in proj['net_settings']['classes'] for c in baseproj['net_settings']['classes'])
classes={n:[p['netclass'] for p in patterns if fnmatch.fnmatchcase(n,p['pattern'])] for n in nn if not n.startswith('unconnected-')}
assert all(len(c)==1 for c in classes.values()),classes
for n in ['EPS_CHG_SCL','EPS_CHG_SDA']:assert classes[n]==['I2C']
assert classes['EPS_CHG_ALERT_N']==['CONTROL']
for n in ['BATT_PERMITTED','5V0_CHG_INTVCC','2V5_CHG_LOGIC',prefix+'CHG_CLP',prefix+'CHG_CSP']:assert classes[n]==['POWER']
for n in [prefix+'CHG_BOOST',prefix+'CHG_SW']:assert classes[n]==['SWITCHING']
orphan=[p['pattern'] for p in patterns if not any(fnmatch.fnmatchcase(n,p['pattern']) for n in nn)]
assert set(orphan)=={'/Controller/REC5_RESET','/Controller/REC5_FAULT','/Controller/SRC_FAULT'}
(H/'class_membership.json').write_text(json.dumps({'classes':classes,'orphan_patterns':orphan,'note':'Widths are inherited routing defaults; physical stackup/current/timing qualification open'},indent=2)+'\n')

baseline=json.loads((H/'baseline.json').read_text());assert baseline['basis'].startswith('8d03a76')
allowed={'hardware/eps/rev_b/'+f for f in ['eps_rev_b.kicad_sch','eps_rev_b.kicad_pro','controller.kicad_sch','essential_3v3.kicad_sch','recovery_5v.kicad_sch','source_protection.kicad_sch']}
changed={f for f,h in baseline['files'].items() if sha(ROOT/f)!=h}
assert changed==allowed,changed
newpaths={'hardware/eps/rev_b/charger.kicad_sch'}|{'hardware/eps/verification/rev_b/charger_integration/parts_disposable/charger_parts_check'+s for s in ['.kicad_sch','.kicad_pro','.kicad_pcb']}
protected=lambda f:f.endswith(('.kicad_sch','.kicad_pro','.kicad_pcb','.kicad_sym','.kicad_mod','sym-lib-table','fp-lib-table'))
delta={}
for line in subprocess.check_output(['git','diff','--name-status','8d03a76','--','hardware/eps'],cwd=ROOT,text=True).splitlines():
    status,path=line.split('\t');
    if protected(path):delta[path]=status
for path in subprocess.check_output(['git','ls-files','--others','--exclude-standard','hardware/eps'],cwd=ROOT,text=True).splitlines():
    if protected(path):delta[path]='A'
assert delta==({p:'M' for p in allowed}|{p:'A' for p in newpaths}),delta
# Prior library fixtures AND evidence are compared to the immutable commit, not refreshed current bytes.
frozen={}
for folder in ['hardware/eps/verification/rev_b/charger_bms_library','hardware/eps/verification/charging/powerpath_package']:
    for f in subprocess.check_output(['git','ls-tree','-r','--name-only','8d03a76',folder],cwd=ROOT,text=True).splitlines():
        h=hashlib.sha256(subprocess.check_output(['git','show','8d03a76:'+f],cwd=ROOT)).hexdigest();assert sha(ROOT/f)==h,f;frozen[f]=h
(H/'frozen_prior_evidence.json').write_text(json.dumps(frozen,indent=2)+'\n')
assert len(rb['hierarchy']['children'])==7 and rb['hierarchy']['children'][-1]['file']=='charger.kicad_sch'

# Geometry including junctions is absent from the layout API, so inspect it read-only.
layout=json.loads((H/'layout_readback.json').read_text());geometry={}
def dirs(p,w):
    x,y=p;a,b,c,d=[round(w[k],4) for k in ['x1','y1','x2','y2']];out=set()
    if b==d==y and min(a,c)<=x<=max(a,c):
        if x>min(a,c):out.add('L')
        if x<max(a,c):out.add('R')
    if a==c==x and min(b,d)<=y<=max(b,d):
        if y>min(b,d):out.add('U')
        if y<max(b,d):out.add('D')
    return out
for name in ['charger','controller']:
    data=layout[name];w=data['wires'];points=set();ends=set()
    for z in w:
        assert z['x1']==z['x2'] or z['y1']==z['y2']
        assert all(abs(z[k]/1.27-round(z[k]/1.27))<1e-5 for k in ['x1','y1','x2','y2']),(name,z)
        for p in [(z['x1'],z['y1']),(z['x2'],z['y2'])]:points.add(tuple(round(v,4) for v in p));ends.add(tuple(round(v,4) for v in p))
    for a in w:
        for b in w:
            x,y=round(a['x1'],4),round(b['y1'],4)
            if a['x1']==a['x2'] and b['y1']==b['y2'] and min(a['y1'],a['y2'])<=y<=max(a['y1'],a['y2']) and min(b['x1'],b['x2'])<=x<=max(b['x1'],b['x2']):points.add((x,y))
    native=(P/(name+'.kicad_sch')).read_text();junctions={tuple(map(float,v.split())) for v in re.findall(r'\(junction\s+\(at ([^)]*)\)',native)}
    four={p for p in points if len(set().union(*(dirs(p,z) for z in w)))==4}
    assert not (four & (junctions|ends)),(name,four & (junctions|ends))
    assert not any((round(l['x'],4),round(l['y'],4)) in four for l in data['labels'])
    queried=rb['charger_pins' if name=='charger' else 'controller_pins']['components']
    assert {c['reference'] for c in queried}=={c['reference'] for c in data['components']}
    for c in queried:
        for pin in c['pins']:
            p=(round(pin['x'],4),round(pin['y'],4));assert len(set().union(*(dirs(p,z) for z in w)))<3,(name,c['reference'],pin)
    geometry[name]={'wires':len(w),'joined_fourways':0,'unconnected_crossings':[list(p) for p in sorted(four)],'pin_branch_anchors':0}
(H/'geometry.json').write_text(json.dumps(geometry,indent=2)+'\n')
manifest=json.loads((H/'native_source_sha256.json').read_text());assert set(manifest)==allowed|newpaths
for f,h in manifest.items():assert sha(ROOT/f)==h,f
subprocess.run([sys.executable,str(H/'verify_annotations.py')],check=True,capture_output=True,text=True)
result={'status':'DEVELOPMENT TOPOLOGY/METADATA PASS; FULL EPS ACCEPTANCE OPEN','basis':baseline['basis'],'parts':len(nc),'new_parts':len(newrefs),'prior_physical_UUIDs_metadata_preserved':len(oc),'nets':len(nn),'functional_nets':len(classes),'each_ref_pin_occurs_once':sum(map(len,nn.values())),'charger_physical_pins_checked':29,'complete_added_or_expanded_sets':len(added),'ERC_errors':14,'ERC_warnings':0,'intentional_ERC_pair':['U300.25','U300.26'],'frozen_prior_evidence_files':len(frozen),'existing_native_changed':sorted(changed),'orphan_patterns':orphan,'geometry':geometry,'scope':'No real PCB, raw BMS or historical fixture changes; external BATT/SOLAR fixtures and incomplete protections remain explicit'}
(H/'verified.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
