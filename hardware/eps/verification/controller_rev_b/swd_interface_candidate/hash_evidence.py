#!/usr/bin/env python3
from common import *
import hashlib,sys
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
paths=[p for p in H.rglob('*') if p.is_file() and portable(p) and p.name!='evidence_sha256.json']
paths += [ROOT/'hardware/eps/design/rev_b_swd_tmux1511_library_rules.md',ROOT/'hardware/eps/rev_b/libraries/Ember_Charger_BMS_Review.kicad_sym']
x={str(p.relative_to(ROOT)):sha(p) for p in sorted(set(paths))}
p=H/'evidence_sha256.json'
if '--check' in sys.argv:assert json.loads(p.read_text())==x;print('Portable evidence hash check PASS:',len(x),'files')
else:p.write_text(json.dumps(x,indent=2)+'\n');print('Recorded',len(x),'portable files')
