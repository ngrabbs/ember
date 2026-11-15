#!/usr/bin/env python3
"""Development-only detector parameter sweep. Prepare each scene once; no CAN/RF."""
import argparse
from collections import Counter
import itertools
import json
import platform
import sys
from pathlib import Path
import cv2
import numpy as np
from ember_detector.pipeline import load_config,prepare,canonical,digest
from ember_detector.registry import create
from ember_detector.profiles import add_profile_arguments, profile_name


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('manifest', 'calibration', 'output'):
        p.add_argument('--' + name, required=True, type=Path)
    add_profile_arguments(p)
    p.add_argument('--k', nargs='+', type=float)
    p.add_argument('--excess', nargs='+', type=float)
    p.add_argument('--area', nargs='+', type=int)
    p.add_argument('--guard', nargs='+', type=int)
    p.add_argument('--coverage', nargs='+', type=float, help='Minimum valid fraction, e.g. 0.0043')
    p.add_argument('--sweep', action='append', default=[], metavar='KEY=JSON_ARRAY',
                   help='Sweep any detector parameter, e.g. cutoff_dn=[8,16,32]')
    a = p.parse_args()
    config = load_config(a.config, profile=a.profile)
    base = config['detector']
    axes = {key: values for key, values in (
        ('k_threshold', a.k), ('excess_min', a.excess), ('min_area_px', a.area),
        ('alignment_guard_px', a.guard), ('min_valid_fraction', a.coverage)) if values is not None}
    for spec in a.sweep:
        key, sep, encoded = spec.partition('=')
        try:
            values = json.loads(encoded)
        except ValueError:
            p.error('Expected KEY=JSON_ARRAY')
        if not sep or key in axes or not isinstance(values, list) or not values:
            p.error(f'Invalid or duplicate sweep axis: {key}')
        axes[key] = values
    if not axes and 'k_threshold' in base:
        axes = dict(k_threshold=[.5, 1, 2], excess_min=[5, 10, 20], min_area_px=[8, 32])
    if axes.keys() - base.keys():
        p.error(f'Unknown detector parameters: {sorted(axes.keys() - base.keys())}')
    detector = create(config['algorithm'])
    trials = []
    for values in itertools.product(*axes.values()):
        settings = dict(base, **dict(zip(axes, values)))
        try:
            detector.validate(settings)
        except ValueError as error:
            p.error(str(error))
        trials.append(dict(settings=settings, counts=Counter(), confusion=Counter(), results=[]))
    manifest=json.loads(a.manifest.read_text());failures=[]
    for index,fixture in enumerate(manifest['fixtures'],1):
        try:scene,_=prepare(fixture,a.manifest.parent,config,a.calibration)
        except (ValueError,KeyError,OSError,cv2.error) as error:
            failures.append(dict(fixture_id=fixture['fixture_id'],reason=str(error)));scene=None
        for trial in trials:
            result = detector.detect(scene, trial['settings']) if scene else None
            decision = result.decision.name if result else 'UNKNOWN'
            label = fixture.get('label')
            trial['counts'][decision] += 1
            if label in ('FIRE', 'NO_FIRE'):
                trial['confusion'][label + '->' + decision] += 1
            trial['results'].append(dict(fixture_id=fixture['fixture_id'], label=label, decision=decision,
                                         score=result.metrics.get('score') if result else None,
                                         reason=result.reason if result else failures[-1]['reason']))
        print(f"Prepared/evaluated {index}/{len(manifest['fixtures'])}: {fixture['fixture_id']}",file=sys.stderr,flush=True)
    report=dict(profile=profile_name(config),input_format=config.get("input_format","jpeg"),development_only=True,independent_holdout=False,config_sha256=digest(canonical(config)),
                base_config=config,manifest_sha256=digest(a.manifest.read_bytes()),
                code_sha256=digest(b''.join(f.name.encode()+f.read_bytes() for f in sorted((Path(__file__).parent/'ember_detector').glob('*.py')) if not f.name.startswith('.'))),
                tuner_sha256=digest(Path(__file__).read_bytes()),
                dependencies={'numpy':np.__version__,'opencv':cv2.__version__,'python':platform.python_version(),'machine':platform.machine()},
                preparation_failures=failures,trials=trials)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open('x') as f:json.dump(report,f,indent=2);f.write('\n')
    for trial in trials:print(json.dumps({k:v for k,v in trial.items() if k != "results"}))


if __name__=='__main__':main()
