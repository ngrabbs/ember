#!/usr/bin/env python3
"""Export runtime files and the source checkout identity, without SSH secrets."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    source = Path(__file__).resolve().parent
    root = source.parents[1]
    git = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip()
    dirty = bool(subprocess.check_output(['git', '-C', str(root), 'status', '--porcelain'], text=True))
    if args.destination.exists():
        raise SystemExit('Export destination already exists')
    args.destination.mkdir(parents=True)
    for filename in ('protocol.py', 'payload.py', 'can_setup.py', 'install.sh', 'client.py', 'VERSION'):
        shutil.copy2(source / filename, args.destination / filename)
    shutil.copytree(source / 'systemd', args.destination / 'systemd')
    (args.destination / 'build_identity.json').write_text(json.dumps({
        'git': git, 'dirty': int(dirty), 'version': (source / 'VERSION').read_text().strip()
    }, indent=2) + '\n')


if __name__ == '__main__':
    main()
