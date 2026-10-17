"""Fail closed on missing source identity when building exported Walter sources."""
Import("env")
from pathlib import Path
import os
import re
project=Path(env['PROJECT_DIR'])
revision=os.environ.get('EMBER_GIT_REVISION','')
dirty=os.environ.get('EMBER_GIT_DIRTY','')
version=(project/'VERSION').read_text().strip()
assert re.fullmatch('[0-9a-f]{40}',revision), 'Set EMBER_GIT_REVISION to full source SHA'
assert dirty in ('0','1'), 'Set EMBER_GIT_DIRTY=0 or 1'
assert re.fullmatch(r'\d+\.\d+\.\d+',version)
parts=[int(x) for x in version.split('.')];assert all(x<256 for x in parts)
out=project/'.generated/build_identity.h';out.parent.mkdir(exist_ok=True)
out.write_text('#pragma once\n'+''.join(f'#define FW_{k} {v}u\n' for k,v in zip(('MAJOR','MINOR','PATCH'),parts))+f'#define FW_DIRTY {dirty}u\n#define FW_VERSION "{version}"\n#define FW_GIT "{revision}"\n')
