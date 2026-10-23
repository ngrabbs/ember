#!/usr/bin/env python3
"""Read-only acceptance checks; emits tables/results, never writes KiCad sources."""
import csv
import hashlib
import json
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET
from collections import Counter

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
DATA = json.loads((HERE / 'library_readback.json').read_text())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
near = lambda a, b: abs(float(a) - float(b)) < 1e-7

L_NAMES = 'BOOST INTVCC VOUTA CLN CLP INFET VIN VCC2P5 NTCBIAS NTC RT SMBALERT SCL SDA DVCC SYNC CELLS0 CELLS1 BATSENS+ CSN CSP BATFET PGND PGND SW SW VOUT VOUT AGND'.split()
B_NAMES = 'PBI VC4 VC3 VC2 VC1 SRN NC SRP VSS TS1 TS2 TS3 TS4 NC BTP_INT PRES/SHUTDN DISP SMBD SMBC LEDCNTLA LEDCNTLB LEDCNTLC PTC PTCEN FUSE VCC PACK DSG NC PCHG CHG BAT VSS_EP'.split()
L_TYPES = 'power_in power_out power_in input input output power_in power_out output input input open_collector input bidirectional power_in input input input input input input output power_in power_in power_out power_out power_in power_in power_in'.split()
B_TYPES = 'power_in input input input input input passive input power_in input input input input passive output input input bidirectional bidirectional bidirectional bidirectional bidirectional input input output power_in input output passive output output power_in power_in'.split()

def rationale(k, n):
    if k == 'L':
        if n in (1, 3, 7, 15, 27, 28): return 'Supply/bias consumer; BOOST is floating high-side bias, VOUT is switching-regulator INPUT despite its name.'
        if n in (2, 8): return 'Internal regulator bypass output, not an externally driven supply.'
        if n in (23, 24, 29): return 'Distinct physical ground connection; EP29 is AGND; common with PGND per ADI.'
        if n in (25, 26): return 'Distinct physical switching power-transmission output; do not merge pins.'
        if n in (6, 22): return 'External MOSFET gate-control output.'
        if n == 9: return 'Pulsed 1.2 V thermistor excitation output.'
        if n == 12: return 'Explicit open-drain alert output; KiCad open_collector represents open drain.'
        if n == 13: return 'ADI describes clock input; open-drain bus does not make this pin an output.'
        if n == 14: return 'Open-drain bidirectional I2C data; bidirectional preserves input/output role.'
        if n == 11: return 'Frequency-control analog interface set by resistor to ground; modeled input, not power output.'
        return 'Analog sense/control or digital selection/clock input per ADI pin-function description.'
    if n in (7, 14, 29): return 'Not internally connected; TI explicitly permits floating OR VSS tie; passive rather than must-not-connect no_connect.'
    if n in (1, 26, 32): return 'TI P supply connection; PBI retains documented backup-input role.'
    if n in (9, 33): return 'VSS ground connection. EP33 electrical VSS allocation is required by approved construction rules; TI package identifies thermal pad33.'
    if n in (18, 19): return 'TI I/OD and equivalent diagram support input/open-drain output; KiCad bidirectional has no separate bidirectional-open-drain type.'
    if n in (20, 21, 22): return 'TI table has dash, but Fig6-2 and section7.13 specify input AND high/low output behavior; bidirectional, not open collector.'
    if n == 17: return 'Display control input function; TI table type dash reconciled with section7.12 input thresholds/application control.'
    if n in (15, 25): return 'TI O output retained. Manufacturer unused-to-VSS instruction requires explicit future ERC disposition; type is not weakened.'
    if n in (28, 30, 31): return 'TI O gate-drive output retained; unused floating/20k-to-VSS instructions are application choices.'
    if n in (2, 3, 4, 5): return 'TI IA cell-sense/balancing connection retained as analog input; internal balancing currents are application constraints.'
    if n in (23, 24): return 'TI IA PTC/PTCEN analog input classification retained, including BAT/VSS strap instructions.'
    return 'TI I/IA input classification retained; required unused ties/configuration remain circuit requirements.'

rows = []
for key, names, types, count in [('L', L_NAMES, L_TYPES, 29), ('B', B_NAMES, B_TYPES, 33)]:
    p = DATA['parts'][key]
    sym, fp = p['symbol'], p['footprint']
    assert sym['pin_count'] == fp['pad_count'] == count
    pins = {x['number']: x for x in sym['pins']}
    pads = {x['number']: x for x in fp['pads']}
    assert len(pins) == len(pads) == count
    assert set(pins) == set(pads) == {str(i) for i in range(1, count + 1)}
    actual_instance = {x['number']: x for x in p['pins']['pins']}
    assert len(actual_instance) == count
    assert p['instance']['rotation'] == 0
    assert not p['instance']['mirror_x'] and not p['instance']['mirror_y']
    assert p['instance']['footprint'] == sym['properties']['Footprint']
    assert p['instance']['value'] == sym['properties']['Value']
    for n, name, typ in zip(range(1, count + 1), names, types):
        pin, pad = pins[str(n)], pads[str(n)]
        assert (pin['name'], pin['type']) == (name, typ), (key, n, pin)
        if n == count:
            x = y = 0
            w, h = ((2.65, 3.65) if key == 'L' else (1.4, 1.4))
        else:
            if key == 'L':
                if n <= 8: x, y, w, h = -1.9, -1.75 + .5*(n-1), .7, .25
                elif n <= 14: x, y, w, h = -1.25 + .5*(n-9), 2.4, .25, .7
                elif n <= 22: x, y, w, h = 1.9, 1.75 - .5*(n-15), .7, .25
                else: x, y, w, h = 1.25 - .5*(n-23), -2.4, .25, .7
            else:
                if n <= 8: x, y, w, h = -1.9, -1.4 + .4*(n-1), .6, .2
                elif n <= 16: x, y, w, h = -1.4 + .4*(n-9), 1.9, .2, .6
                elif n <= 24: x, y, w, h = 1.9, 1.4 - .4*(n-17), .6, .2
                else: x, y, w, h = 1.4 - .4*(n-25), -1.9, .2, .6
        for field, expected in [('x', x), ('y', y), ('width', w), ('height', h)]: assert near(pad[field], expected), (key,n,field)
        assert pad['type'] == 'smd' and pad['drill'] == [] and pad['rotation'] == 0
        assert set(pad['layers']) == {'F.Cu', 'F.Paste', 'F.Mask'}
        assert pad['shape'] == ('roundrect' if key == 'B' and n < count else 'rect')
        if key == 'B' and n < count: assert near(pad['roundrect_rratio'] * min(w, h), .05)
        ip = actual_instance[str(n)]
        assert ip['name'] == name
        assert near(ip['x'], p['instance']['x'] + pin['x'])
        assert near(ip['y'], p['instance']['y'] - pin['y'])
        assert near(ip['length_mm'], 5.08)
        for xy in (pin['x'],pin['y'],ip['x'],ip['y']): assert near(xy/1.27, round(xy/1.27))
        rows.append([sym['properties']['Value'], 'UFD' if key=='L' else 'RSM', n, name, str(n)+'/'+name+'/'+typ, n,
                     f'{x:.3f}', f'{y:.3f}', f'{w:.3f}', f'{h:.3f}', pad['shape'], 'F.Cu/F.Paste/F.Mask; SMD; no drill',
                     'front/component view; pin1 upper-left; CCW; X right/Y down',
                     'ADI LTC4162-L RevA pp3-4,10-11,50; UFD05-08-1712 RevC; mechanical BOTTOM view mirrored/rotated' if key=='L' else 'TI SLUSCS4C pp3-7,11-12; RSM0032A4219107/A pp52-54; front land/pin views',rationale(key,n)])
    courtyard = next(g for g in fp['graphics'] if g['layer']=='F.CrtYd')
    for pad in pads.values():
        assert pad['x'] - pad['width']/2 - courtyard['start']['x'] >= .25-1e-7
        assert courtyard['end']['x'] - pad['x'] - pad['width']/2 >= .25-1e-7
        assert pad['y'] - pad['height']/2 - courtyard['start']['y'] >= .25-1e-7
        assert courtyard['end']['y'] - pad['y'] - pad['height']/2 >= .25-1e-7
    fab = next(g for g in fp['graphics'] if g['layer']=='F.Fab')
    assert near(max(t['x'] for t in fab['points'])-min(t['x'] for t in fab['points']),4.1)
    assert near(max(t['y'] for t in fab['points'])-min(t['y'] for t in fab['points']),5.1 if key=='L' else 4.1)
    assert any(g['layer']=='F.SilkS' and g['type']=='circle' and g['center']['x']<0 and g['center']['y']<0 for g in fp['graphics'])

with (HERE/'physical_map.csv').open('w',newline='') as f:
    w=csv.writer(f,lineterminator='\n')
    w.writerow(['MPN','package','datasheet_lead','function','symbol_pin/name/type','footprint_pad','X_mm','Y_mm','width_mm','height_mm','shape','layers/drill','view/direction','source','electrical_type_reconciliation'])
    w.writerows(rows)

before=json.loads((HERE/'integrated_before.json').read_text())
unchanged=[]
for file, digest in before.items():
    if Path(file).name in ('sym-lib-table','fp-lib-table'): continue
    assert sha(ROOT/file)==digest,file
    unchanged.append(file)
def graph(path):
    doc=ET.parse(path).getroot()
    cs={c.attrib['ref']:ET.tostring(c,encoding='unicode') for c in doc.findall('./components/comp')}
    ns={n.attrib['name']:sorted((a.attrib['ref'],a.attrib['pin']) for a in n.findall('node')) for n in doc.findall('./nets/net')}
    return cs,ns
old=HERE.parent/'protection_integration'/'eps_rev_b.xml'
assert graph(old)==graph(HERE/'integrated.xml')
assert len(graph(old)[0])==160 and len(graph(old)[1])==91
dis=ET.parse(HERE/'disposable.xml').getroot()
assert len(dis.findall('./components/comp'))==2
isolated=dis.findall('./nets/net')
assert len(isolated)==62 and all(len(n.findall('node'))==1 for n in isolated)
assert {(n.find('node').attrib['ref'],n.find('node').attrib['pin']) for n in isolated} == {(p['reference'],v['number']) for p in DATA['parts'].values() for v in p['symbol']['pins']}
for c in dis.findall('./components/comp'):
    p=DATA['parts']['L' if c.attrib['ref']=='U1' else 'B']
    fields={v.attrib['name']:v.text for v in c.findall('./fields/field')}
    assert fields['MFG P/N']==p['symbol']['properties']['Value']
    assert fields['Review']=='CUSTOM — REVIEW REQUIRED'
    lp=dis.find("./libparts/libpart[@part='"+p['name']+"']")
    assert lp is not None
    actual={i.attrib['num']:(i.attrib['name'],i.attrib['type']) for i in lp.findall('./pins/pin')}
    expected={i['number']:(i['name'],i['type']) for i in p['symbol']['pins']}
    assert actual==expected
for name in ('sym-lib-table','fp-lib-table'):
    rel='hardware/eps/rev_b/'+name
    old_text=subprocess.check_output(['git','show','6be2bc7:'+rel],cwd=ROOT,text=True)
    current=(ROOT/rel).read_text()
    entries=lambda text: {m.group(1):m.group(2) for m in re.finditer(r'\(lib\s+\(name\s+"?([^"\s)]+)"?\).*?\(uri\s+"([^"]+)"\)',text,re.S)}
    a,b=entries(old_text),entries(current)
    assert a and all(b[n]==v for n,v in a.items())
    assert len(b)==len(a)+1
    assert b['Ember_Charger_BMS_Review'].startswith('${KIPRJMOD}/libraries/')
protected=lambda p: Path(p).suffix in ('.kicad_sch','.kicad_pcb','.kicad_pro','.kicad_sym','.kicad_mod') or Path(p).name in ('sym-lib-table','fp-lib-table')
# Include the approved additions once staged/committed. The old name-only
# assertion saw only the two modified tables while the new files were untracked,
# then incorrectly rejected the same library checkpoint after it was committed.
# Keep exact path/status coverage and source hashes; do not allow arbitrary new
# protected files or changes to the existing integrated design.
sources=json.loads((HERE/'candidate_source_sha256.json').read_text())
existing_tables={'hardware/eps/rev_b/fp-lib-table','hardware/eps/rev_b/sym-lib-table'}
assert len(sources)==10 and existing_tables <= sources.keys()
assert all(protected(file) for file in sources)
expected_changes={file: 'M' if file in existing_tables else 'A' for file in sources}
status_lines=subprocess.check_output(['git','diff','--no-renames','--name-status','6be2bc7','--','hardware/eps'],cwd=ROOT,text=True).splitlines()
native_changes={file: status for status,file in (line.split('\t') for line in status_lines) if protected(file)}
assert native_changes==expected_changes, (native_changes,expected_changes)
for file,digest in sources.items(): assert sha(ROOT/file)==digest,file
erc=json.loads((HERE/'integrated_erc.json').read_text())
assert len(erc)==16 and all(e['rule']=='pin_not_connected' and e['severity']=='error' for e in erc)
dc=json.loads((HERE/'disposable_erc.json').read_text())
assert len(dc)==94
assert Counter(e['rule'] for e in dc)=={'pin_not_connected':58,'pin_not_driven':23,'power_pin_not_driven':13}
result={'status':'PARTIAL — LIBRARY AND SCHEMATIC INSTANCE PASS; BOARD INSTANCE ACCEPTANCE BLOCKED',
        'basis':'6be2bc7','physical_rows':len(rows),'LTC_counts':{'perimeter':28,'EP':1,'symbol':29,'electrical_pads':29,'duplicates':0,'mechanical_only':0},
        'BQ_counts':{'perimeter':32,'EP':1,'symbol':33,'electrical_pads':33,'duplicates':0,'mechanical_only':0,'internally_NC':[7,14,29]},
        'integrated_native_source_files_unchanged':unchanged,'integrated_parts':160,'integrated_nets':91,'integrated_ERC_errors':16,'integrated_ERC_warnings':0,
        'approved_native_file_changes':dict(sorted(native_changes.items())),
        'disposable_ERC':dict(Counter(e['rule'] for e in dc)),
        'library_copper_fab_renders_inspected':True,'disposable_symbols_full_and_details_inspected':True,
        'disposable_board_instances_created':False,'disposable_board_render_inspected':False,
        'open':['Board instance placement/queryback/render blocked by fixed live IPC transport; no bypass attempted',
                'CUSTOM review markers retained; no real circuit placement authorized by this checkpoint',
                'Nominal copper only: stencil segmentation/thermal vias/assembly tolerances/3D/application qualification open',
                'S11 library custom field/default instance copying/display limitations require explicit placement field readback/callouts']}
(HERE/'verified.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
