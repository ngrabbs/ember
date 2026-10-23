#!/usr/bin/env python3
"""Summarize completed screening raws; no qualified design acceptance implied."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / 'protection'))
from run_protection import read_raw


def summarize(path, name):
    t, v = read_raw(path)
    expected_end = (-8.4 if name.endswith('_dc') else .009) if name.startswith('pmos_') else .8
    assert np.isclose(t[-1], expected_end), f'Incomplete analysis axis: {name}'
    result = {'points': len(t), 'axis_start': float(t[0]), 'axis_end': float(t[-1]),
              'raw_sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
    bounds = lambda a: {'min': float(np.min(a)), 'max': float(np.max(a))}
    if name.startswith('pmos_'):
        output = v['v(out)'] if 'v(out)' in v else v['v(drain)']
        result['output_V'] = bounds(output)
        result['supply_current_A'] = bounds(-v['i(vsource)'])
        result['final_output_V'] = float(output[-1])
        if 'transient' in name:
            result['output_4ms_V'] = float(np.interp(.004, t, output))
        return result
    sense = v.get('v(sense)', v['v(cs)'])
    result['sense_V'] = bounds(sense)
    result['vgs_V'] = bounds(v['v(gate)'] - v['v(cs)'])
    for node in ['a', 'b', 'cs', 'gate', 'bias', 'permission', 'uv']:
        result[node + '_V'] = bounds(v[f'v({node})'])
    result['vds1_V'] = bounds(v['v(a)'] - v['v(cs)'])
    result['vds2_V'] = bounds(v['v(b)'] - v['v(cs)'])
    result['sense_below_minus_0p3V'] = bool(np.min(sense) < -.3)
    result['fet_above_80V_abs_vds'] = bool(max(np.max(np.abs(v['v(a)']-v['v(cs)'])), np.max(np.abs(v['v(b)']-v['v(cs)']))) > 80)
    result['fet_above_16V_abs_vgs'] = bool(np.max(np.abs(v['v(gate)']-v['v(cs)'])) > 16)
    output = v['v(a)'] if name.startswith('controller_reverse') else v['v(b)']
    result['output_before_49ms_V'] = bounds(output[t <= .049])
    result['output_450ms_V'] = float(np.interp(.45, t, output))
    result['output_700ms_V'] = float(np.interp(.7, t, output))
    active = (t >= .049) & (t <= .501)
    for index, node in [(1, 'a'), (2, 'b')]:
        current = v[f'id(m{index})']
        power = np.maximum((v[f'v({node})']-v['v(cs)'])*current, 0)
        result[f'fet{index}_on_interval_current_A'] = bounds(current[active])
        result[f'fet{index}_positive_energy_J'] = float(np.sum((power[1:]+power[:-1])/2*np.diff(t)))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--controller-raw', type=Path, required=True)
    parser.add_argument('--pmos-raw', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--case', action='append', help='Exact portable deck stem; repeat for a subset.')
    args = parser.parse_args()
    results = {}
    for deck in sorted((HERE/'decks').glob('*.cir')):
        if args.case and deck.stem not in args.case:
            continue
        group, original = deck.stem.split('_', 1)
        raw = (args.controller_raw if group == 'controller' else args.pmos_raw)/(original+'.raw')
        if not raw.exists():
            raw = raw.with_name(deck.stem+'.raw')
        results[deck.stem] = summarize(raw, deck.stem)
        log = raw.with_suffix('.log')
        log_text = log.read_text(errors='replace')
        assert 'Total elapsed time:' in log_text, f'Incomplete log: {log}'
        results[deck.stem]['log_sha256_original'] = hashlib.sha256(log.read_bytes()).hexdigest()
        results[deck.stem]['portable_deck_sha256'] = hashlib.sha256(deck.read_bytes()).hexdigest()
    assert results, 'No matching cases'
    if args.case:
        assert set(args.case) == set(results), 'Unknown requested case'
    args.output.write_text(json.dumps({'status': 'EXPERIMENTAL_NOT_ACCEPTED', 'cases': results}, indent=2)+'\n')
    print(f'Summarized {len(results)} completed cases; no circuit acceptance implied.')


if __name__ == '__main__':
    main()
