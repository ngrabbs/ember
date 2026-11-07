from common import *
import hashlib,sys
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
files=[p for p in H.rglob('*') if p.is_file() and portable(p) and p.name!='evidence_sha256.json']
files += [ROOT/p for p in json.loads((H/'native_source_sha256.json').read_text())]
x={str(p.relative_to(ROOT)):sha(p) for p in sorted(set(files))};p=H/'evidence_sha256.json'
if '--check' in sys.argv:assert json.loads(p.read_text())==x;print('Portable evidence hash check PASS',len(x))
else:p.write_text(json.dumps(x,indent=2)+'\n');print('Recorded',len(x),'portable paths')
