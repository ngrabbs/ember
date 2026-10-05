"""Check saved Konnect evidence and exported nets; never edit KiCad sources."""
from pathlib import Path
import hashlib
import json
import re

base = Path(__file__).resolve().parent
text = (base / 'stage1.net').read_text()
raw = json.loads((base / 'stage1-evidence.json').read_text())

def unwrap(value):
    assert not value.get('isError'), value
    return json.loads(value['content'][0]['text'])

nets = {}
for block in text.split('\n\t\t(net\n')[1:]:
    name = re.search(r'\(name "([^"]+)"\)', block)[1]
    if name.startswith('unconnected-'):
        key = name
    elif name == 'Net-(U1-SW)':
        key = 'AON_SW'
    else:
        key = name.rsplit('/', 1)[-1]
    assert key not in nets, ('split / duplicated domain', key)
    nets[key] = set(re.findall(r'\(node\s*\(ref "([^"]+)"\)\s*\(pin "([^"]+)"\)', block))
expected = {key: set(map(tuple, members)) for key, members in
            json.loads((base / 'stage1-expected-topology.json').read_text()).items()}
assert nets == expected, {'actual': nets, 'expected': expected}
assert len(nets) == 22
assert len(nets['+3V3_AON']) == 18
assert not {'+3V3', '+5V', 'VDC', 'SYS_RESET_N', 'MAIN_BUCK_EN', 'MCU_ALIVE'} & nets.keys()

for sheet in ['payload_compute_rev_next.kicad_sch', '03_aon_supply.kicad_sch',
              '04_reset_run_core.kicad_sch']:
    evidence = raw[sheet]
    for key, field in [('wires', 'floating_count'), ('pins', 'unconnected_count'),
                       ('shorts', 'short_count'), ('orphans', 'orphan_count'),
                       ('overlaps', 'overlap_count')]:
        assert unwrap(evidence[key])[field] == 0, (sheet, key)
    assert not unwrap(evidence['overlaps'])['bounds_unresolved']
assert unwrap(raw['sheet_pins'])['issue_count'] == 0
assert len(unwrap(raw['hierarchy'])['children']) == 2

erc = unwrap(raw['erc'])
assert erc['errors'] == 15 and erc['warnings'] == 0
ports = {'AON_BOOTSTRAP_IN', 'SOURCE_OK_AON', 'MODE_PERMISSION', 'MCU_MAIN_REQ',
         'MCU_CONTROL_READY', 'ORIN_5V_WINDOW_OK', 'SHUTDOWN_OK_AON',
         'MCU_ARM_QUAL', 'MCU_ARM_CLK', 'AON_RESET_N', 'POWER_PERMISSION',
         'MAIN_BUCK_REQUEST_OK', 'RUN_LATCH'}
port_errors = [item for item in erc['violations'] if item['rule'] == 'pin_not_connected']
assert len(port_errors) == 13
assert {re.search(r"Hierarchical Sheet Pin '([^']+)'", item['description'])[1]
        for item in port_errors} == ports
power_errors = [item for item in erc['violations'] if item['rule'] == 'power_pin_not_driven']
assert len(power_errors) == 2
assert {re.search(r'Symbol (U\d+) Pin (\d+)', item['description']).groups()
        for item in power_errors} == {('U1', '3'), ('U1', '9')}

maps = {
    'aon': {'1': ('RT', 'passive'), '2': ('PGOOD', 'open_collector'),
            '3': ('EN/UVLO', 'input'), '4': ('VIN', 'power_in'),
            '5': ('SW', 'output'), '6': ('BOOT', 'passive'),
            '7': ('VCC', 'power_out'), '8': ('VOUT/BIAS', 'input'), '9': ('GND', 'power_in')},
    'reset': {'1': ('RESET_N', 'open_collector'), '2': ('GND', 'power_in'),
              '3': ('MR_N', 'input'), '4': ('CT', 'input'),
              '5': ('SENSE', 'input'), '6': ('VDD', 'power_in')},
    'gate': {'1': ('', 'input'), '2': ('GND', 'power_in'), '3': ('', 'input'),
             '4': ('', 'output'), '5': ('VCC', 'power_in'), '6': ('', 'input')},
    'latch': {'1': ('CLK', 'input'), '2': ('D', 'input'), '3': ('Q_N', 'output'),
              '4': ('GND', 'power_in'), '5': ('Q', 'output'), '6': ('CLR_N', 'input'),
              '7': ('PRE_N', 'input'), '8': ('VCC', 'power_in')},
}
for key, mapping in maps.items():
    assert {pin['number']: (pin['name'], pin['type']) for pin in
            unwrap(raw['symbols'][key])['pins']} == mapping
instances = {'U1': ('aon', 'aon', 'LMR36506R3RPER'),
             'U101': ('reset', 'dbv', 'TPS3808G33DBVR'),
             'U102': ('gate', 'dbv', 'SN74LVC1G11DBVR'),
             'U103': ('gate', 'dbv', 'SN74LVC1G11DBVR'),
             'U104': ('gate', 'dbv', 'SN74LVC1G11DBVR'),
             'U105': ('latch', 'dcu', 'SN74LVC1G74DCUR')}
for ref, (symbol_key, footprint_key, value) in instances.items():
    instance = unwrap(raw['instances'][ref])
    footprint = unwrap(raw['footprints'][footprint_key])
    symbol = unwrap(raw['symbols'][symbol_key])
    assert instance['value'] == value and instance['lib_id'] == symbol['lib_id']
    assert instance['footprint'] == 'EMBER_Payload:' + footprint['name']
    assert not instance['mirror_x'] and not instance['mirror_y'] and instance['rotation'] == 0
    assert {pin['number']: pin['name'] for pin in unwrap(raw['pins'][ref])['pins']} == {
        num: name for num, (name, _) in maps[symbol_key].items()}
    assert {pad['number'] for pad in footprint['pads'] if 'F.Cu' in pad['layers']} == set(maps[symbol_key])
    assert re.search(r'\(ref "' + ref + r'"\)\s*\(value "([^"]+)"\)', text)[1] == value

for ref in range(101, 113):
    assert re.search(r'\(ref "R' + str(ref) + r'"\)\s*\(value "([^"]+)"\)', text)[1] == '10k'
physical_refs = re.findall(r'\(comp\s*\(ref "([^"]+)"\)', text)
assert len(physical_refs) == len(set(physical_refs)) == 30
result = {'result': 'PASS for stage 1 saved connectivity and classified boundaries',
          'physical_components': 30, 'placed_ic_pins': 41, 'exported_nets': 22,
          'aon_rail_physical_pins': 18, 'boundary_erc_errors': 15, 'erc_warnings': 0,
          'not_proven': ['protected input circuitry', 'watchdog/receivers', 'power ramps',
                         'physical regulator/module enable interfaces', 'assembly/layout/fabrication'],
          'historical_snapshot': True,
          'sha256': json.loads((base / 'stage1-check-results.json').read_text())['sha256']}
(base / 'stage1-check-results.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
