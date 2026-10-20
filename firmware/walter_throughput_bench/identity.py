"""Temporary image identity: source SHA plus exact project-source digest."""
Import('env')
from pathlib import Path
import hashlib,os,re
p=Path(env['PROJECT_DIR']);revision=os.environ.get('EMBER_GIT_REVISION','');assert re.fullmatch('[0-9a-f]{40}',revision)
h=hashlib.sha256()
for f in sorted([p/'platformio.ini',p/'identity.py',*[f for f in p.glob('src/*')if not f.name.startswith('.')and f.suffix in ('.cpp','.h','.c')],p/'../walter/src/cereg.h']):
 h.update(os.path.relpath(f,p).encode()+b'\0'+f.read_bytes()+b'\0')
out=p/'.generated/bench_identity.h';out.parent.mkdir(exist_ok=True)
out.write_text('#pragma once\n#define BENCH_GIT "'+revision+'"\n#define BENCH_SOURCE_SHA256 "'+h.hexdigest()+'"\n')
