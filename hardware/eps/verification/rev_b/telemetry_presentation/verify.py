"""Verify bounded telemetry presentation edits, with no native writes."""
from pathlib import Path
import collections
import copy
import hashlib
import json
import re
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
TARGET = 'hardware/eps/rev_b/rail_telemetry.kicad_sch'
read = lambda name: json.loads((HERE / name).read_text())
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
base = read('baseline.json')
changed = [p for p, h in base['native_sha256'].items() if sha(ROOT / p) != h]
assert changed == [TARGET], changed
edits = read('edits.json')
allowed = collections.defaultdict(set)
for e in edits:
    allowed[e['uuid']].add(e['field'])
assert len(edits) == 93 and len(allowed) == 25
removed = {i['uuid']: i for i in read('removed_annotations.json')}
assert len(removed) == 26 and all(i['kind'] == 'text' for i in removed.values())
key = lambda n: n.get('list', [{}])[0].get('atom')

def normalized(name):
    result = {}
    for item in copy.deepcopy(read(name)['items']):
        uid = item['uuid']
        if uid in removed:
            assert item == removed[uid]
            continue
        if item['kind'] == 'text' and item['node']['list'][1].get('string', '').startswith('DEVELOPMENT: SYS/BATT'):
            expected = read('apply.json')[2]['args']['text']
            assert item['node']['list'][1]['string'] == expected
            continue
        if uid in allowed:
            assert item['kind'] == 'symbol'
            nodes = item['node']['list']
            for n in nodes:
                if key(n) == 'property' and n['list'][1].get('string') in allowed[uid]:
                    n['list'] = n['list'][:3]
            item['node']['list'] = [n for n in nodes if key(n) != 'fields_autoplaced']
        result[uid] = item
    return result

assert normalized('items_before.json') == normalized('items_after.json')
after_items = {i['uuid']: i for i in read('items_after.json')['items']}
assert not (set(removed) & set(after_items))
assert sum(i['kind'] == 'text' and i['node']['list'][1].get('string', '').startswith('DEVELOPMENT: SYS/BATT') for i in after_items.values()) == 1
fields = {s['uuid']: s for s in read('fields_after.json')['symbols']}
for e in edits:
    symbol = fields[e['uuid']]
    assert not symbol['fields_autoplaced']
    f = next(f for f in symbol['fields'] if f['name'] == e['field'])
    nodes = {key(n): n['list'] for n in f['nodes']}
    assert 'hide' not in nodes
    assert [float(n['atom']) for n in nodes['at'][1:]] == [e['x'], e['y'], e['rotation']]
    effects = {key(n): n['list'] for n in nodes['effects'][1:]}
    assert 'hide' not in effects and 'show_name' not in effects
    font = {key(n): n['list'] for n in effects['font'][1:]}
    assert [float(n['atom']) for n in font['size'][1:]] == [e['size']] * 2
    if 'font' in e:
        assert font['face'][1]['string'] == 'Arial'
    actual_justify = [n['atom'] for n in effects.get('justify', [])[1:]]
    assert actual_justify == e['justify']

def xml(name):
    root = ET.parse(HERE / name).getroot()
    root.find('design').remove(root.find('design/date'))
    for stamps in root.findall('components/comp/tstamps'):
        stamps.text = ' '.join(sorted(stamps.text.split()))
    return ET.tostring(root)

assert xml('before.xml') == xml('after.xml')
net = ET.parse(HERE / 'after.xml').getroot()
assert len(net.findall('components/comp')) == 345
assert len(net.findall('nets/net')) == 186
assert len(net.findall('nets/net/node')) == 933
assert len(net.findall('design/sheet')) == 14
erc = read('erc.json')
previous_erc = json.loads((HERE.parent / 'root_presentation/erc.json').read_text())
for d in [erc, previous_erc]:
    d.pop('date')
    for sheet in d['sheets']:
        for violation in sheet['violations']:
            for item in violation['items']:
                item.pop('uuid', None)  # CLI creates transient pin-item IDs on each load.
assert erc == previous_erc

def svg(path):
    result, count = re.subn(r'(<title>SVG Image created as [^<]* date )[^<]*(</title>)', r'\1EXPORT_TIME\2', path.read_text())
    assert count == 1
    return result

previous = HERE.parent / 'root_presentation/after_svg'
unchanged = [p for p in previous.glob('*.svg') if p.name != 'eps_rev_b-Rail Telemetry.svg']
assert len(unchanged) == 13
assert all(svg(p) == svg(HERE / 'svg' / p.name) for p in unchanged)
result = {'status': 'TELEMETRY_NATIVE_FIELD_PRESENTATION_VERIFIED',
          'baseline_commit': base['commit'], 'preserved_native_files': len(base['native_sha256']) - 1,
          'only_native_change': TARGET, 'edited_field_presentations': 93,
          'resistors': 19, 'capacitors': 6, 'Arial_0p5mm_parameter_fields': 81,
          'whole_root_XML_except_date_and_multiunit_tstamp_order_preserved': True,
          'unchanged_other_SVGs_except_title_export_time': 13,
          'ERC_errors': 6, 'ERC_warnings': 2, 'physical_parts': 345,
          'ERC_diagnostics_settings_positions_descriptions_preserved': True,
          'nets': 186, 'endpoints': 933, 'sheets': 14,
          'native_sha256': sha(ROOT / TARGET), 'design_complete': False}
(HERE / 'verified.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
