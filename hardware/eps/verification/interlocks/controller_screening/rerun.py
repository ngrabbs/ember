#!/usr/bin/env python3
"""Run portable screening decks serially; keep models and raw outputs outside git."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--pmos-model', type=Path, required=True)
parser.add_argument('--library', type=Path, default=Path.home()/'Library/Application Support/LTspice/lib')
parser.add_argument('--executable', default='/Applications/LTspice.app/Contents/MacOS/LTspice')
parser.add_argument('--case', action='append', help='Exact portable deck stem; repeat to select several.')
args = parser.parse_args()
args.output.mkdir(parents=True, exist_ok=False)
records = []
for source in sorted((HERE/'decks').glob('*.cir')):
    if args.case and source.stem not in args.case:
        continue
    text = source.read_text().replace('${LTSPICE_LIBRARY}', str(args.library.resolve())).replace('${PMOS_MODEL}', str(args.pmos_model.resolve()))
    target = args.output/source.name
    target.write_text(text)
    record = {'case': source.stem}
    try:
        result = subprocess.run([args.executable, '-b', str(target.resolve())], cwd=args.output, timeout=45, capture_output=True)
        record['returncode'] = result.returncode
        record['status'] = 'completed' if result.returncode == 0 and target.with_suffix('.raw').exists() and 'Total elapsed time:' in target.with_suffix('.log').read_text(errors='replace') else 'incomplete'
    except subprocess.TimeoutExpired:
        record['status'] = 'timeout_terminated'
    records.append(record)
    print(record, flush=True)
manifest = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in [args.pmos_model,args.library/'sub/LTC4367.sub',args.library/'cmp/standard.mos']}
(args.output/'runs.json').write_text(json.dumps({'runs': records, 'models': manifest}, indent=2)+'\n')
