#!/usr/bin/env python3
"""Hash this bounded checkpoint; exclude volatile GUI files and obsolete progress."""
from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent
excluded={'evidence_sha256.json','root_review.json','progress.xml','erc_progress.json','bms_progress.png','controller_progress.png'}
def keep(p):
    r=p.relative_to(H)
    return (p.is_file() and p.name not in excluded
            and not any(x in {'.history','__pycache__'} or x.endswith('-backups') for x in r.parts)
            and not p.name.startswith('~') and p.name not in {'.DS_Store','fp-info-cache'}
            and p.suffix not in {'.lck','.kicad_prl','.pyc'})
files={str(p.relative_to(H)):hashlib.sha256(p.read_bytes()).hexdigest()
       for p in sorted(H.rglob('*')) if keep(p)}
(H/'evidence_sha256.json').write_text(json.dumps({'scope':'BMS integration only; source manifests separately freeze native paths and prior tracked evidence','excluded_obsolete_or_external_review':sorted(excluded),'files':files},indent=2)+'\n')
print(f'Hashed {len(files)} checkpoint files.')
