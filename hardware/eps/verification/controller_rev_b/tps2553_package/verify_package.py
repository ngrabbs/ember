#!/usr/bin/env python3
"""TPS package readback gate. Reads native sources only for unsupported API detail."""
from collections import Counter
from pathlib import Path
import csv
import hashlib
import json
import re
import subprocess
import xml.etree.ElementTree as ET

H = Path(__file__).resolve().parent
ROOT = H.parents[4]
LIB = ROOT/'hardware/eps/rev_b/libraries/Ember_Charger_BMS_Review.kicad_sym'
FP = ROOT/'hardware/eps/rev_b/libraries/Ember_Charger_BMS_Review.pretty/TI_DBV0006A_SOT23_6_TI_Land_REVIEW.kicad_mod'
STEM = 'tps2553_check'
ID = 'Ember_Charger_BMS_Review:TI_DBV0006A_SOT23_6_TI_Land_REVIEW'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def parse(text):
    stack = []
    root = None
    for token in re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^()\s]+', text):
        if token == '(':
            node = []
            if stack:
                stack[-1].append(node)
            else:
                root = node
            stack.append(node)
        elif token == ')':
            stack.pop()
        else:
            stack[-1].append(json.loads(token) if token.startswith('"') else token)
    assert not stack
    return root


def kids(node, key):
    return [x for x in node if isinstance(x, list) and x and x[0] == key]


def one(node, key):
    return kids(node, key)[0]


def props(node):
    return {x[1]: x[2] for x in kids(node, 'property')}


def read(name):
    return json.loads((H/name).read_text())


def close(a, b):
    assert abs(float(a)-float(b)) < 2e-6, (a, b)


base = read('baseline.json')
for name, digest in read('evidence_sha256.json').items():
    assert sha(H/name) == digest, 'evidence changed: ' + name
for path, digest in base['files'].items():
    assert sha(ROOT/path) == digest, path
before = (H/'library_before.txt').read_text()
after = LIB.read_text()
assert hashlib.sha256(before.encode()).hexdigest() == base['library_before_sha256']
assert after.startswith(before.rstrip()[:-1]), 'old library byte prefix changed'
old = parse(before)
new = parse(after)
assert len(kids(new, 'symbol')) == len(kids(old, 'symbol')) + 1
for symbol in kids(old, 'symbol'):
    assert symbol == next(s for s in kids(new, 'symbol') if s[1] == symbol[1])
ns = [s for s in kids(new, 'symbol') if s[1] == 'TPS2553DBVR_1_REVIEW']
assert len(ns) == 1
protected = lambda p: p.endswith(('.kicad_sch','.kicad_pro','.kicad_pcb','.kicad_sym','.kicad_mod')) or Path(p).name in {'sym-lib-table','fp-lib-table'}
changed = set()
for args in [['diff','--name-only',base['commit'],'--'], ['ls-files','--others','--exclude-standard']]:
    changed.update(p for p in subprocess.check_output(['git', *args], cwd=ROOT, text=True).splitlines() if protected(p))
sources = [LIB, FP] + [H/'fixture'/n for n in [STEM+'.kicad_pro', STEM+'.kicad_sch', STEM+'.kicad_pcb', 'sym-lib-table', 'fp-lib-table']]
allowed = {str(p.relative_to(ROOT)) for p in sources}
assert changed == allowed, (changed, allowed)
assert {str(p.relative_to(ROOT)):sha(p) for p in sources} == read('native_source_sha256.json')
for table in ['sym-lib-table','fp-lib-table']:
    entries = kids(parse((H/'fixture'/table).read_text()), 'lib')
    assert len(entries) == 1
    assert one(entries[0], 'name')[1] == 'Ember_Charger_BMS_Review'
    uri = one(entries[0], 'uri')[1]
    assert uri.startswith('${KIPRJMOD}/')
    assert (H/'fixture'/uri.removeprefix('${KIPRJMOD}/')).resolve().exists()

names = ['IN','GND','EN','~{FAULT}','ILIM','OUT']
types = ['power_in','power_in','input','open_collector','output','power_out']
expect_pins = {str(i+1):(name,typ) for i,(name,typ) in enumerate(zip(names,types))}
symbol = read('symbol_query.json')
pins = [p for unit in kids(ns[0], 'symbol') for p in kids(unit, 'pin')]
assert len(pins) == len(symbol['pins']) == symbol['pin_count'] == 6
assert Counter(one(p,'number')[1] for p in pins) == Counter(map(str,range(1,7)))
assert {one(p,'number')[1]:(one(p,'name')[1],p[1]) for p in pins} == expect_pins
assert {p['number']:(p['name'],p['type']) for p in symbol['pins']} == expect_pins
expected_symbol_xy = {'1':(-17.78,5.08),'2':(-10.16,-12.7),'3':(-17.78,0),'4':(17.78,0),'5':(10.16,-12.7),'6':(17.78,5.08)}
for p in symbol['pins']:
    close(p['x'],expected_symbol_xy[p['number']][0])
    close(p['y'],expected_symbol_xy[p['number']][1])
sch = parse((H/'fixture'/f'{STEM}.kicad_sch').read_text())
instances = kids(sch, 'symbol')
assert len(instances) == 1 and props(instances[0])['Reference'] == 'U1'
fields = props(instances[0])
assert fields['Value'] == fields['MFG P/N'] == 'TPS2553DBVR-1'
assert fields['Footprint'] == ID and fields['PackageSize'] == 'DBV0006A / SOT-23-6'
assert fields['Manufacturer'] == 'Texas Instruments' and 'CUSTOM' in fields['Review']
embedded = one(one(sch,'lib_symbols'),'symbol')
assert embedded[2:] == ns[0][2:]
assert one(sch,'paper')[1] == 'B' and not kids(sch,'no_connect') and not kids(sch,'wire')
green = next(t for t in kids(sch,'text') if t[1].startswith('CUSTOM'))
assert 'Construction authorized:' in green[1]
assert list(map(float,one(one(one(green,'effects'),'font'),'color')[1:])) == [0,255,0,1]
ip = read('instance_pins.json')['pins']
assert len(ip) == 6 and Counter(p['number'] for p in ip) == Counter(map(str,range(1,7)))
for p in ip:
    assert p['name'] == names[int(p['number'])-1]
    close(p['x'],160.02+expected_symbol_xy[p['number']][0])
    close(p['y'],99.06-expected_symbol_xy[p['number']][1])
    for axis in ['x','y']:
        close(p[axis]/1.27, round(p[axis]/1.27))
value_text = [t for t in ET.parse(H/'tps2553_check.svg').getroot().iter('{http://www.w3.org/2000/svg}text') if ''.join(t.itertext()) == 'TPS2553DBVR-1']
assert len(value_text) == 1
# Value half-width plus one grid interval clears the two bottom pin strokes.
assert float(value_text[0].get('textLength'))/2 + 1.27 < 10.16

xy = [(-1.3,-.95),(-1.3,0),(-1.3,.95),(1.3,.95),(1.3,0),(1.3,-.95)]
expected = [(str(i+1),x,y,1.1,.6,.05,('F.Cu','F.Paste','F.Mask')) for i,(x,y) in enumerate(xy)]
expected += [('',x,y,1.2,.7,.1,('F.Mask',)) for x,y in xy]
key = lambda n,x,y,w,h,r,l: (n,round(float(x),6),round(float(y),6),round(float(w),6),round(float(h),6),round(float(r),6),tuple(sorted(l)))
want = Counter(key(*p) for p in expected)
library = read('footprint_query.json')
footprint_native = parse(FP.read_text())
board = parse((H/'fixture'/f'{STEM}.kicad_pcb').read_text())
fps = kids(board,'footprint')
assert len(fps) == 1
fp = fps[0]
assert fp[1] == ID and props(fp)['Reference'] == 'U1' and props(fp)['Value'] == 'TPS2553DBVR-1'
saved_pads = kids(fp,'pad')
lib_pads = kids(footprint_native,'pad')
live = read('live_after_save.json')
assert len(saved_pads) == len(lib_pads) == len(library['pads']) == library['pad_count'] == len(live['pads']) == live['pad_count'] == 12
assert live['source'] == 'ipc'
counter = Counter(map(str,range(1,7))) + Counter({'':6})
assert Counter(p[1] for p in saved_pads) == Counter(p['number'] for p in library['pads']) == Counter(p['number'] for p in live['pads']) == counter
close(one(fp,'at')[1],50)
close(one(fp,'at')[2],50)
assert len(one(fp,'at')) == 3 or float(one(fp,'at')[3]) == 0
for collection in [saved_pads,lib_pads]:
    rows = []
    for p in collection:
        assert p[2:4] == ['smd','roundrect'] and not kids(p,'drill')
        at = list(map(float,one(p,'at')[1:3]))
        size = list(map(float,one(p,'size')[1:3]))
        radius = min(size)*float(one(p,'roundrect_rratio')[1])
        assert len(one(p,'at')) == 3 or float(one(p,'at')[3]) == 0
        rows.append(key(p[1],*at,*size,radius,one(p,'layers')[1:]))
    assert Counter(rows) == want
assert Counter(key(p['number'],p['x'],p['y'],p['width'],p['height'],min(p['width'],p['height'])*p['roundrect_rratio'],p['layers']) for p in library['pads']) == want
for p in library['pads']:
    assert p['type'] == 'smd' and p['shape'] == 'roundrect' and not p['drill'] and p['rotation'] == 0
expected_live = Counter((n,round(50+x,6),round(50+y,6),tuple(sorted(l))) for n,x,y,w,h,r,l in expected)
assert Counter((p['number'],round(p['x'],6),round(p['y'],6),tuple(sorted(p['layers']))) for p in live['pads']) == expected_live
assert all(p['net'] == '' for p in live['pads'] if p['number'] == '')
assert all(p['net'] for p in live['pads'] if p['number'])
assert not kids(fp,'model') and not kids(footprint_native,'model')
close(one(one(board,'setup'),'pad_to_mask_clearance')[1],.05)
assert not kids(fp,'solder_mask_margin')
assert not any(kids(p,'solder_mask_margin') for p in saved_pads)

# Check actual plotted mask contours: 12 objects, paired coincident openings,
# six distinct extents, each 1.20x0.70 mm = copper +0.05 on every side.
svg = ET.parse(H/'board_mask.svg').getroot()
mask_boxes = []
for path in svg.iter('{http://www.w3.org/2000/svg}path'):
    if 'fill:#D864FF' in path.get('style',''):
        pts = [(float(x),float(y)) for x,y in re.findall(r'(-?\d+\.\d+),(-?\d+\.\d+)',path.get('d',''))]
        assert pts
        xs,ys = zip(*pts)
        mask_boxes.append(tuple(round(a,5) for a in [min(xs),min(ys),max(xs),max(ys)]))
assert len(mask_boxes) == 12
assert Counter(mask_boxes) == Counter({(round(50+x-.6,5),round(50+y-.35,5),round(50+x+.6,5),round(50+y+.35,5)):2 for x,y in xy})
court = [g for g in library['graphics'] if g['layer']=='F.CrtYd']
assert len(court) == 1 and court[0]['start'] == {'x':-2.2,'y':-2.1} and court[0]['end'] == {'x':2.2,'y':2.1}
assert court[0]['fill'] == 'none' and court[0]['stroke_width_mm'] == .05
assert Counter(g['layer'] for g in library['graphics']) == {'F.CrtYd':1,'F.Fab':1,'F.SilkS':3}

xml = ET.parse(H/'fixture.xml').getroot()
components = xml.findall('components/comp')
assert len(components) == 1 and components[0].get('ref') == 'U1'
nets = xml.findall('nets/net')
assert len(nets) == 6 and all(len(n.findall('node')) == 1 for n in nets)
nodes = [p for n in nets for p in n.findall('node')]
assert Counter((p.get('ref'),p.get('pin')) for p in nodes) == Counter(('U1',str(i)) for i in range(1,7))
annotation_before = read('annotation_before.json')
assert ET.tostring(xml.find('components'),encoding='unicode') == annotation_before['component_block']
assert ET.tostring(xml.find('nets'),encoding='unicode') == annotation_before['net_block']
assert not any(t[1].startswith('MFG P/N:') for t in kids(sch,'text'))
assert any(t[1] == 'Texas Instruments | DBV0006A\nActive-high / latch-off\nILIM is programming-current output' for t in kids(sch,'text'))
violations = [v for sheet in read('erc.json')['sheets'] for v in sheet['violations']]
assert Counter((v['severity'],v['type']) for v in violations) == {('error','pin_not_connected'):6,('error','power_pin_not_driven'):2,('error','pin_not_driven'):1}
closed = read('closed_editor.json')
assert closed['requested_open'] is False and closed['open_board_count'] == 0
with (H/'physical_map.csv').open('w') as f:
    rows = [{'lead':i+1,'function':names[i],'symbol_type':types[i],'footprint_pad':i+1,'x_mm':x,'y_mm':y,'view':'TI p5 top/front; pin1 upperleft, CCW','source':'TI SLVS841F p5; DBV4214840/G pp34-36'} for i,(x,y) in enumerate(xy)]
    w = csv.DictWriter(f,fieldnames=rows[0],lineterminator='\n')
    w.writeheader()
    w.writerows(rows)
(H/'instance_fields.json').write_text(json.dumps(fields,indent=2)+'\n')
main_xml = ET.parse(ROOT/'hardware/eps/verification/rev_b/uart_integration/eps_rev_b.xml').getroot()
main_parts = main_xml.findall('components/comp')
assert len(main_parts) == len({c.get('ref') for c in main_parts}) == 243
assert len(main_xml.findall('nets/net')) == 137
assert not any('TPS2553' in c.findtext('value','') for c in main_parts)
result = {'status':'DEVELOPMENT PHYSICAL MAP PASS; CUSTOM REVIEW REQUIRED; S11 LIBRARY DEFAULTS OPEN; CIRCUIT SELECTION OPEN','basis':base['commit'],'physical_pins':6,'raw_library_pads':12,'raw_saved_pads':12,'raw_live_pads':12,'copper_and_paste_pads':6,'blank_mask_pads':6,'mask_expansion_each_side_mm':.05,'ti_nsmd_max_mm':.07,'frozen_byte_files':len(base['files']),'library_prior_prefix_and_symbols_exact':True,'value_pin_collision_repaired':True,'fixture_erc_errors':9,'fixture_erc_warnings':0,'wire_fourways':0,'changed_protected_paths':sorted(changed),'main_design':'243 parts /137 nets; native files unchanged; no TPS placement'}
(H/'verified.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
