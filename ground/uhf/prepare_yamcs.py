#!/usr/bin/env python3
"""Add isolated UHF reception using the already prepared EMBER MDB/adapters.

Preserves existing instance definitions, signing key and archives. No TC link.
"""
import argparse
from pathlib import Path
import xml.etree.ElementTree as ET


def prepare(root):
    config = root / '.runtime/quickstart/src/main/yamcs/etc'
    source = config / 'yamcs.ember-lte.yaml'
    text = source.read_text()
    if text.count('name: eps-lte-in') != 1 or text.count('port: 10018') != 1:
        raise ValueError('Expected the documented single-input LTE instance')
    uhf = text.replace('name: eps-lte-in', 'name: eps-uhf-in').replace('port: 10018', 'port: 10019')
    legacy_uhf = uhf
    if uhf.count('file: mdb/ember.xml') != 1:
        raise ValueError('Expected shared EMBER MDB reference')
    uhf = uhf.replace('file: mdb/ember.xml', 'file: mdb/ember-uhf.xml')
    mdb = config.parent / 'mdb'
    tree = ET.parse(mdb / 'ember.xml')
    ns = {'x': 'http://www.omg.org/spec/XTCE/20180204'}
    rates = tree.findall('.//x:SequenceContainer[@name="POWER_STATUS"]/x:DefaultRateInStream', ns)
    if len(rates) != 1:
        raise ValueError('Expected POWER_STATUS freshness rate')
    # 30 s allowance * Yamcs default expirationTolerance 1.9 = 57 s.
    # UHF display policy only; wire schema and other instances stay unchanged.
    rates[0].set('minimumValue', str(1 / 30))
    target = config / 'yamcs.ember-uhf.yaml'
    if target.exists() and target.read_text() not in (uhf, legacy_uhf):
        raise ValueError('Existing UHF config differs; preserve and review it')
    main = config / 'yamcs.yaml'
    current = main.read_text()
    if '  - ember-uhf\n' not in current:
        if '  - ember-lte\n' not in current:
            raise ValueError('Missing existing ember-lte instance entry')
        if not main.with_suffix('.yaml.before-uhf').exists():
            main.with_suffix('.yaml.before-uhf').write_text(current)
        main.write_text(current.replace('  - ember-lte\n', '  - ember-lte\n  - ember-uhf\n', 1))
    ET.register_namespace('', ns['x'])
    tree.write(mdb / 'ember-uhf.xml', encoding='utf-8', xml_declaration=True)
    target.write_text(uhf)
    print('Prepared ember-uhf / eps-uhf-in / UDP10019; restart Yamcs to load.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--yamcs-root', type=Path, default=Path(__file__).resolve().parents[1] / 'yamcs')
    prepare(parser.parse_args().yamcs_root)
