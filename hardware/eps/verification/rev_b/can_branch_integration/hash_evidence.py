#!/usr/bin/env python3
"""Hash final native sources and this bounded evidence directory."""
from common import *
import hashlib
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
excluded={'evidence_sha256.json'}
files={str(p.relative_to(ROOT)):sha(p) for p in sorted(H.rglob('*')) if p.is_file() and p.name not in excluded and portable(p)}
native=json.loads((H/'native_source_sha256.json').read_text())
assert all(sha(ROOT/p)==h for p,h in native.items())
(H/'evidence_sha256.json').write_text(json.dumps({'native_sources':native,'evidence':files},indent=2)+'\n')
print(f'{len(native)} native paths; {len(files)} evidence files hashed.')
