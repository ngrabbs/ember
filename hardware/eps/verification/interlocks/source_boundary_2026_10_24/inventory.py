#!/usr/bin/env python3
"""Read an exported graph, not native CAD; keep switched capacitor stages separate."""
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
EPS = HERE.parents[2]
SOURCE = EPS / 'verification/rev_b/isolated_bms_integration/eps_rev_b.xml'


def main():
    root = ET.parse(SOURCE).getroot()
    components = {c.get('ref'): c for c in root.findall('./components/comp')}
    nets = {}
    for net in root.findall('./nets/net'):
        for node in net.findall('node'):
            key = (node.get('ref'), node.get('pin'))
            assert key not in nets, key
            nets[key] = net.get('name')
    expected = {
        'BATT_PERMITTED': ['C304', 'C305'],
        'SYS_PWR_PERMITTED': ['C300', 'C301', 'C302', 'C303', 'C309',
                              'C400', 'C401', 'C402', 'C503', 'C504',
                              'C505', 'C506', 'C507'],
        'VIN_CHG': ['C308', 'C600', 'C601', 'C602', 'C603'],
        'SRC_BIAS': ['C604', 'C605', 'C606', 'C607'],
        '/Solar source protection/SRC_SNUB': ['C612', 'C613', 'C614', 'C615'],
    }
    groups = {}
    for rail, refs in expected.items():
        actual = sorted(ref for ref in components if ref.startswith('C')
                        and {nets.get((ref, '1')), nets.get((ref, '2'))} == {rail, 'GND'})
        assert actual == sorted(refs), (rail, actual)
        rows = []
        for ref in refs:
            c = components[ref]
            fields = {f.get('name'): f.text for f in c.findall('./fields/field')}
            match = re.fullmatch(r'([\d.]+)([unp])F?', c.findtext('value'))
            assert match, ref
            nominal = float(match[1]) * {'u': 1, 'n': .001, 'p': .000001}[match[2]]
            tol = float(fields['Tolerance'].rstrip('%')) / 100
            rows.append({'ref': ref, 'nominal_uF': nominal, 'initial_tolerance': tol,
                         'initial_tolerance_upper_uF': nominal * (1 + tol),
                         'mpn': fields['MFG P/N'],
                         'pins': {pin: nets[(ref, pin)] for pin in ['1', '2']}})
        groups[rail] = {'parts': rows,
                        'nominal_uF': round(sum(v['nominal_uF'] for v in rows), 6),
                        'initial_tolerance_upper_uF': round(sum(v['initial_tolerance_upper_uF'] for v in rows), 6)}
    # Topological path assertions: these are separated banks, not one capacitor.
    for ref, pin, net in [('L600', '1', 'SOLAR_PERMITTED'),
                          ('L600', '2', 'SRC_FILTERED'),
                          ('R612', '1', 'SRC_FILTERED'),
                          ('R612', '2', '/Solar source protection/SRC_SNUB'),
                          ('Q301', '1', 'BATT_PERMITTED'),
                          ('Q301', '5', 'SYS_PWR_PERMITTED'),
                          ('Q300', '1', 'VIN_CHG'),
                          ('R300', '2', 'SYS_PWR_PERMITTED')]:
        assert nets[(ref, pin)] == net, (ref, pin)
    sums = {}
    for name, members, voltage in [
        ('battery_passive_capacitor_screen', ['BATT_PERMITTED', 'SYS_PWR_PERMITTED'], 8.526),
        ('solar_passive_capacitor_screen', ['SRC_BIAS', '/Solar source protection/SRC_SNUB',
                                            'VIN_CHG', 'SYS_PWR_PERMITTED'], 35.0)]:
        nom = sum(groups[m]['nominal_uF'] for m in members)
        high = sum(groups[m]['initial_tolerance_upper_uF'] for m in members)
        sums[name] = {'members': members, 'nominal_uF': round(nom, 6),
                      'initial_tolerance_upper_uF': round(high, 6),
                      'illustrative_voltage_V': voltage,
                      'nominal_stored_energy_J': .5 * nom * 1e-6 * voltage**2,
                      'initial_tolerance_upper_stored_energy_J': .5 * high * 1e-6 * voltage**2}
    result = {'status': 'TOPOLOGY_INVENTORY_NOT_INRUSH_OR_SOA_ACCEPTANCE',
              'source': str(SOURCE.relative_to(EPS)),
              'source_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
              'physical_parts': len(components), 'groups': groups, 'illustrative_sums': sums,
              'limits': ['Initial tolerance only; not a guaranteed capacitance envelope across voltage, temperature or ageing.',
                         'Do not collapse banks across the filter, resistor, active switches or charger PowerPath.',
                         'Converted output banks and active/constant-power startup loads are excluded from these passive sums.',
                         '8.526 V and 35 V are study points, not newly accepted source limits.',
                         'Stored capacitor energy is not MOSFET dissipation or an SOA proof.']}
    (HERE / 'inventory.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(sums, indent=2))


if __name__ == '__main__':
    main()
