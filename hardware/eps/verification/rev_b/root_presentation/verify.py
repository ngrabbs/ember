"""Verify a two-caption presentation repair; never write native KiCad files."""
from pathlib import Path
import collections
import copy
import hashlib
import json
import re
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
TARGET = 'hardware/eps/rev_b/eps_rev_b.kicad_sch'

def read(name):
    return json.loads((HERE / name).read_text())

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

baseline = read('baseline.json')
changed = [p for p, h in baseline['native_sha256'].items() if sha(ROOT / p) != h]
assert changed == [TARGET], changed
edits = read('edits.json')
targets = {e['uuid'] for e in edits}
assert len(targets) == 2

def key(node):
    return node.get('list', [{}])[0].get('atom')

def normalize_items(data):
    result = copy.deepcopy(data)
    for item in result['items']:
        if item.get('uuid') not in targets:
            continue
        assert item['kind'] == 'sheet'
        nodes = item['node']['list']
        for node in nodes:
            if key(node) == 'property' and node['list'][1].get('string') == 'Sheetfile':
                node['list'] = node['list'][:3]  # Preserve the exact name and value.
        item['node']['list'] = [n for n in nodes if key(n) != 'fields_autoplaced']
    return result

assert normalize_items(read('items_before.json')) == normalize_items(read('items_after.json'))
fields = read('fields_after.json')
assert len(fields['sheets']) == 13
for edit in edits:
    sheet = next(s for s in fields['sheets'] if s['uuid'] == edit['uuid'])
    field = next(f for f in sheet['fields'] if f['name'] == 'Sheetfile')
    at = next(n['list'] for n in field['nodes'] if key(n) == 'at')
    assert [float(n['atom']) for n in at[1:]] == [edit['x'], edit['y'], 0]
    assert not sheet['fields_autoplaced']

def xml(name):
    tree = ET.parse(HERE / name).getroot()
    tree.find('design').remove(tree.find('design/date'))
    return ET.tostring(tree)

assert xml('before.xml') == xml('after.xml'), 'Whole-root XML changed beyond export date'
netlist = ET.parse(HERE / 'after.xml').getroot()
assert len(netlist.findall('components/comp')) == 345
assert len(netlist.findall('nets/net')) == 186
assert len(netlist.findall('nets/net/node')) == 933
assert len(netlist.findall('design/sheet')) == 14
before = HERE / 'before_svg'
after = HERE / 'after_svg'
assert {p.name for p in before.glob('*.svg')} == {p.name for p in after.glob('*.svg')}
child_svgs = [p for p in before.glob('*.svg') if p.name != 'eps_rev_b.svg']
assert len(child_svgs) == 13
def svg_without_export_time(path):
    text = path.read_text()
    text, count = re.subn(r'(<title>SVG Image created as [^<]* date )[^<]*(</title>)', r'\1EXPORT_TIME\2', text)
    assert count == 1
    return text

assert all(svg_without_export_time(p) == svg_without_export_time(after / p.name) for p in child_svgs)
erc = read('erc.json')
counts = collections.Counter(v['severity'] for s in erc['sheets'] for v in s['violations'])
assert counts == {'error': 6, 'warning': 2}, counts
result = {
    'status': 'TWO_ROOT_FILENAME_CAPTIONS_REPAIRED',
    'baseline_commit': baseline['commit'],
    'preserved_native_files': len(baseline['native_sha256']) - 1,
    'only_native_change': TARGET,
    'allowed_delta': 'Two Sheetfile presentation nodes and their sheet autoplacement flags',
    'exact_nonpresentation_MCP_items_preserved': True,
    'whole_XML_except_export_date_preserved': True,
    'identical_child_SVGs_except_export_time_title': 13,
    'physical_parts': 345, 'nets': 186, 'endpoints': 933, 'sheets': 14,
    'ERC_errors': 6, 'ERC_warnings': 2,
    'current_native_sha256': sha(ROOT / TARGET),
    'design_complete': False,
}
(HERE / 'verified.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
