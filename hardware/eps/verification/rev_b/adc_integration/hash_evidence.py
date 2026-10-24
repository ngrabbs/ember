#!/usr/bin/env python3
from common import *
import hashlib,sys
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=H/'evidence_sha256.json'
paths=[p for p in H.rglob('*') if p.is_file() and portable(p) and p!=manifest]
paths += [ROOT/'hardware/eps/rev_b'/n for n in ['eps_rev_b.kicad_sch','eps_rev_b.kicad_pro','controller.kicad_sch','rail_telemetry.kicad_sch']]
actual={str(p.relative_to(ROOT)):sha(p) for p in sorted(set(paths))}
if '--check' in sys.argv:
 assert actual==json.loads(manifest.read_text()),'Portable artifact set/hash differs'
 print(f'PASS {len(actual)} portable evidence/native hashes')
else:
 manifest.write_text(json.dumps(actual,indent=2)+'\n');print(f'Wrote {len(actual)} portable evidence/native hashes')
