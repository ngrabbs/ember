#!/usr/bin/env python3
"""Run isolated clamp diagnostics with the user's unmodified manufacturer model."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import numpy as np
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]/'protection'))
from run_protection import read_raw

def summarize(directory):
    results = {}
    for deck in sorted((HERE/'decks').glob('*.cir')):
        raw = directory/(deck.stem+'.raw')
        log = raw.with_suffix('.log')
        assert 'Total elapsed time:' in log.read_text(errors='replace'), log
        axis, v = read_raw(raw)
        dc = deck.stem.startswith('dc_')
        assert len(axis)>100
        assert np.isclose(axis[-1], 8.526 if dc else .005), raw
        port = v['v(port)']; gate = v['v(main_gate)']; clamp = v['v(clamp_gate)']
        mask = port<=0
        results[deck.stem] = {
            'points':len(axis),'axis_start':float(axis[0]),'axis_end':float(axis[-1]),
            'max_off_vgs_negative_port_V':float(np.max((gate-port)[mask])),
            'main_vgs_V':[float(np.min(gate-port)),float(np.max(gate-port))],
            'clamp_vgs_V':[float(np.min(clamp-port)),float(np.max(clamp-port))],
            'clamp_vds_V':[float(np.min(gate-port)),float(np.max(gate-port))],
            'max_abs_driver_current_A':float(np.max(np.abs(v['i(bdriver)']))),
            'raw_sha256':hashlib.sha256(raw.read_bytes()).hexdigest(),
            'log_sha256':hashlib.sha256(log.read_bytes()).hexdigest(),
            'portable_deck_sha256':hashlib.sha256(deck.read_bytes()).hexdigest(),
            'executed_deck_sha256':hashlib.sha256((directory/deck.name).read_bytes()).hexdigest()}
    return {'status':'ISOLATED_DIAGNOSTICS_ONLY_NOT_BMS_ACCEPTANCE','cases':results}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--model',type=Path)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--analyze-existing',action='store_true')
    p.add_argument('--gate-resistance',choices=['1k','10k'],default='1k')
    args=p.parse_args()
    if not args.analyze_existing:
        assert args.model and args.model.is_file(), 'Supply exact external DMN62D2U manufacturer model'
        sources=json.loads((HERE/'sources.json').read_text())
        expected=next(v['sha256'] for v in sources.values() if v['url'].endswith('/DMN62D2U.spice.txt'))
        assert hashlib.sha256(args.model.read_bytes()).hexdigest()==expected, 'Manufacturer model hash differs from recorded input'
        args.output.mkdir(exist_ok=False)
        for deck in sorted((HERE/'decks').glob('*.cir')):
            local=args.output/deck.name
            local.write_text(deck.read_text().replace('${DMN_MODEL}',str(args.model.resolve()))
                             .replace('Rclamp clamp_gate 0 1k',f'Rclamp clamp_gate 0 {args.gate_resistance}'))
            subprocess.run(['/Applications/LTspice.app/Contents/MacOS/LTspice','-b',str(local)],
                           check=True,timeout=45,capture_output=True)
    result=summarize(args.output)
    (args.output/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    print(f"Summarized {len(result['cases'])} isolated diagnostics; no BMS acceptance implied.")
if __name__=='__main__':main()
