"""Check exported monitor topology and saved Konnect package evidence.

This checks design intent and exact package mapping, not physical operation.
Re-export and refresh evidence after any KiCad source change.
"""
import json
from pathlib import Path
import re

base = Path(__file__).resolve().parent / 'payload_monitor_acceptance'
stem = base / 'payload_monitor_acceptance'
text = stem.with_suffix('.net').read_text()
expected = {
    '+3V3': {('U1', '3'), ('U1', '4'), ('C1', '1'), ('R5', '1')},
    '+5V': {('R1', '1'), ('R3', '1')},
    'GND': {('U1', '1'), ('U1', '2'), ('U2', '4'), ('R2', '2'),
            ('R4', '2'), ('C1', '2'), ('C2', '2'), ('C3', '2')},
    '/VIN_SELECTED': {('U2', '8'), ('C3', '1')},
    '/REF_2V5': {('U1', '5'), ('U1', '6'), ('C2', '1'), ('U2', '2'), ('U2', '5')},
    '/SENSE_UV': {('R1', '2'), ('R2', '1'), ('U2', '3')},
    '/SENSE_OV': {('R3', '2'), ('R4', '1'), ('U2', '6')},
    '/5V_WINDOW_OK': {('U2', '1'), ('U2', '7'), ('R5', '2')},
}
nets = {}
for block in text.split('\n\t\t(net\n')[1:]:
    name = re.search(r'\(name "([^"]+)"\)', block)[1]
    nets[name] = set(re.findall(r'\(node\s*\(ref "([^"]+)"\)\s*\(pin "([^"]+)"\)', block))
assert nets == expected, f'Exported monitor topology differs: {nets}'
for ref, value in {'U1': 'REF3425IDBVR', 'U2': 'LM2903BIDR', 'R1': '9.31k',
                   'R2': '10k', 'R3': '10.7k', 'R4': '10k', 'R5': '10k',
                   'C1': '100n / 16V', 'C2': '1u / 10V', 'C3': '100n / 50V'}.items():
    match = re.search(r'\(ref "' + ref + r'"\)\s*\(value "([^"]+)"\)', text)
    assert match and match[1] == value, f'Wrong exported value: {ref}'
ev = json.loads(Path(str(stem) + '-accepted-library-evidence.json').read_text())
for key, field in [('wires', 'floating_count'), ('pins', 'unconnected_count'),
                   ('shorts', 'short_count'), ('orphans', 'orphan_count'), ('erc', 'total')]:
    assert ev[key][field] == 0, f'Unresolved {key} check'

maps = {
    'ref': {'1': ('GND_F', 'power_in'), '2': ('GND_S', 'power_in'),
            '3': ('EN', 'input'), '4': ('IN', 'power_in'),
            '5': ('OUT_S', 'input'), '6': ('OUT_F', 'power_out')},
    'comp': {'1': ('', 'open_collector'), '2': ('-', 'input'), '3': ('+', 'input'),
             '4': ('V-', 'power_in'), '5': ('+', 'input'), '6': ('-', 'input'),
             '7': ('', 'open_collector'), '8': ('V+', 'power_in')},
}
placed = {c['reference']: c for c in ev['pins_query']['components']}
for key, ref, cx, width, rowx, ys, court in [
    ('ref', 'U1', 100, 1.10, 1.30, [-.95, 0, .95], (2.10, 1.70)),
    ('comp', 'U2', 112, 1.55, 2.70, [-1.905, -.635, .635, 1.905], (3.725, 2.70)),
]:
    symbol, fp, live, instance = [ev[key + suffix] for suffix in
                                  ['_symbol', '_fp', '_live', '_instance']]
    pinmap = maps[key]
    assert symbol['pin_count'] == len(symbol['pins']) == len(pinmap)
    assert {p['number']: (p['name'], p['type']) for p in symbol['pins']} == pinmap
    assert fp['pad_count'] == len(fp['pads']) == len(pinmap)
    assert fp['coordinate_system'] == 'footprint_local_mm_y_down'
    assert instance['footprint'] == 'EMBER_Payload:' + fp['name']
    assert instance['lib_id'] == symbol['lib_id']
    assert instance['unit_count'] == (1 if key == 'ref' else 3)
    assert {p['number']: p['name'] for p in placed[ref]['pins']} == {
        n: data[0] for n, data in pinmap.items()}
    assert len(placed[ref]['pins']) == len(pinmap)
    if key == 'ref':
        assert symbol['properties']['Footprint'] == instance['footprint']
        for p in placed[ref]['pins']:
            q = next(q for q in symbol['pins'] if q['number'] == p['number'])
            assert abs(p['x'] - instance['x'] - q['x']) < 1e-6
            assert abs(p['y'] - instance['y'] + q['y']) < 1e-6
    assert {p['number'] for p in fp['pads']} == set(pinmap)
    for pad in fp['pads']:
        n = int(pad['number']); half = len(ys)
        x, y = (-rowx, ys[n - 1]) if n <= half else (rowx, ys[2 * half - n])
        assert abs(pad['x'] - x) < 1e-6 and abs(pad['y'] - y) < 1e-6
        assert pad['width'] == width and pad['height'] == .6
        assert pad['drill'] == [] and pad['type'] == 'smd'
        assert pad['shape'] == 'roundrect' and pad['rotation'] == 0
        assert abs(.6 * pad['roundrect_rratio'] - .05) < 1e-6
        assert set(pad['layers']) == {'F.Cu', 'F.Mask', 'F.Paste'}
    assert live['source'] == 'ipc' and live['reference'] == ref
    assert live['pad_count'] == len(live['pads']) == len(pinmap)
    for pad in live['pads']:
        match = [q for q in fp['pads'] if q['number'] == pad['number'] and
                 abs(pad['x'] - cx - q['x']) < 1e-6 and
                 abs(pad['y'] - 100 - q['y']) < 1e-6 and
                 set(pad['layers']) == set(q['layers'])]
        assert len(match) == 1 and pad['net'] == '', f'Live package pad mismatch: {pad}'
    courts = [g for g in fp['graphics'] if g['layer'] == 'F.CrtYd']
    assert len(courts) == 1 and courts[0]['type'] == 'rect'
    assert courts[0]['start'] == {'x': -court[0], 'y': -court[1]}
    assert courts[0]['end'] == {'x': court[0], 'y': court[1]}
    assert courts[0]['stroke_width_mm'] == .05
    assert len([g for g in fp['graphics'] if g['layer'] == 'F.Fab']) == 1
    assert len([g for g in fp['graphics'] if g['layer'] == 'F.SilkS' and
                g['type'] == 'circle' and g['center']['x'] < 0 and
                g['center']['y'] < 0]) == 1
print(json.dumps({'exported_nets_checked': len(nets), 'physical_leads_checked': 14,
                  'erc_errors': 0, 'erc_warnings': 0,
                  'result': 'PASS for bounded monitor study; hardware qualification pending'}, indent=2))
