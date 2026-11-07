#!/usr/bin/env python3
"""Hash bounded UART checkpoint, excluding GUI caches and external review outputs."""
from check_common import *
excluded={'evidence_sha256.json','root_review.json','progress_cli.json'}
def keep(p):
    r=p.relative_to(H)
    return (p.is_file() and p.name not in excluded
            and not any(s in {'.history','__pycache__'} or s.endswith('-backups') for s in r.parts)
            and not p.name.startswith('~') and p.name not in {'.DS_Store','fp-info-cache'}
            and p.suffix not in {'.pyc','.lck','.kicad_prl'})
files={str(p.relative_to(H)):sha(p) for p in sorted(H.rglob('*')) if keep(p)}
(H/'evidence_sha256.json').write_text(json.dumps({'scope':'UART checkpoint only; historical/source boundaries separately verified','excluded':sorted(excluded),'files':files},indent=2)+'\n')
print(f'Hashed {len(files)} UART checkpoint artifacts.')
