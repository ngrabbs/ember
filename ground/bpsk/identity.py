"""Content identity for the receiver, including its native packet dictionary."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FILES = ('VERSION', 'identity.py', 'live.py', 'modem.py',
         '../ember/codec.py', '../ember/dictionary.json')

def identity():
    files = {p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in FILES}
    digest = hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()
    return dict(version=(ROOT/'VERSION').read_text().strip(), sha256=digest, files=files)

if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--check', type=Path)
    a=p.parse_args();current=identity()
    if a.check:
        expected=json.loads(a.check.read_text())
        if current['sha256']!=expected['sha256']:
            raise SystemExit('DRIFT: receiver files differ from approved manifest')
        print('MATCH '+current['version']+' '+current['sha256'])
    print(json.dumps(current, indent=2))
