#!/usr/bin/env python3
"""Read-only saved-state readiness boundary check."""
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as E

H = Path(__file__).resolve().parent
ROOT = H.parents[4]
frozen = json.loads((H/'native_before.json').read_text())
for path, digest in frozen.items():
    assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest() == digest, path
x = E.parse(H/'before.xml').getroot()
assert len(x.findall('components/comp')) == 243
assert len(x.findall('nets/net')) == 137
g = {n.get('name'):{(p.get('ref'),p.get('pin')) for p in n.findall('node')} for n in x.findall('nets/net')}
assert g['unconnected-(U100-PD0-Pad26)'] == {('U100','26')}
assert g['unconnected-(U100-PD3-Pad29)'] == {('U100','29')}
assert g['/2S pack protection/BMS_SMBC'] == {('R218','2'),('U201','6'),('U200','19')}
assert g['/2S pack protection/BMS_SMBD'] == {('R219','2'),('U201','7'),('U200','18')}
assert {('U201','8'),('R218','1'),('R219','1'),('C210','1')} <= g['+3V3']
assert {('U201','5'),('C210','2')} <= g['GND_BMS_RAW']
print(f'PASS: {len(frozen)} protected native files unchanged;243 parts/137 nets;exact four-terminal proposal, no execution')
