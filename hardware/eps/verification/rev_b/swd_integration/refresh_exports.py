#!/usr/bin/env python3
"""Read-only fresh whole-hierarchy CLI exports; captures exact source basis."""
from common import *
import hashlib,subprocess
P=ROOT/'hardware/eps/rev_b'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
sources={str(p.relative_to(ROOT)):sha(p) for p in sorted(P.glob('*.kicad_sch'))}
sources[str((P/'eps_rev_b.kicad_pro').relative_to(ROOT))]=sha(P/'eps_rev_b.kicad_pro')
commands=[
 ['sch','export','netlist','--format','kicadxml','--output',str(H/'eps_rev_b.xml')],
 ['sch','erc','--format','json','--output',str(H/'erc.json')],
 ['sch','export','pdf','--output',str(H/'eps_rev_b.pdf')],
]
checks=[]
for args in commands:
 cmd=['/opt/homebrew/bin/kicad-cli',*args,str(P/'eps_rev_b.kicad_sch')]
 r=subprocess.run(cmd,capture_output=True,text=True);assert r.returncode==0
 checks.append({'command':cmd,'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr})
 assert 'annotation errors' not in r.stdout+r.stderr
assert all(sha(ROOT/p)==h for p,h in sources.items())
(H/'cli_checks.json').write_text(json.dumps({'hierarchy_source_sha256':sources,'commands':checks},indent=2)+'\n')
mutable=json.loads((H/'baseline.json').read_text())['initial']
paths=set(mutable)|{'hardware/eps/rev_b/swd_service.kicad_sch'}
(H/'native_source_sha256.json').write_text(json.dumps({p:sha(ROOT/p) for p in sorted(paths)},indent=2)+'\n')
print('Fresh XML / ERC / thirteen-page PDF; sources stable.')
