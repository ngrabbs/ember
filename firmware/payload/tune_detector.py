#!/usr/bin/env python3
"""Development-only spectral threshold sweep. Prepare each scene once; no CAN/RF."""
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


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('manifest','config','calibration','output'):p.add_argument('--'+name,required=True,type=Path)
    p.add_argument('--k',nargs='+',type=float,default=[.5,1,2])
    p.add_argument('--excess',nargs='+',type=float,default=[5,10,20])
    p.add_argument('--area',nargs='+',type=int,default=[8,32])
    p.add_argument('--guard',nargs='+',type=int,help='Guarded detector only: reference-neighborhood radius in pixels')
    a=p.parse_args();config=load_config(a.config)
    if config['algorithm'] not in ('spectral_excess_v1','spectral_guarded_v1'):p.error('This sweep targets spectral plugin settings')
    if a.guard is not None and config['algorithm']!='spectral_guarded_v1':p.error('--guard requires spectral_guarded_v1')
    detector=create(config['algorithm']);trials=[]
    guards=a.guard if a.guard is not None else [config['detector'].get('alignment_guard_px')]
    for k,excess,area,guard in itertools.product(a.k,a.excess,a.area,guards):
        settings=dict(config['detector'],k_threshold=k,excess_min=excess,min_area_px=area)
        if guard is not None:settings['alignment_guard_px']=guard
        detector.validate(settings)
        trials.append(dict(settings=settings,counts=Counter(),confusion=Counter()))
    manifest=json.loads(a.manifest.read_text());failures=[]
    for index,fixture in enumerate(manifest['fixtures'],1):
        try:scene,_=prepare(fixture,a.manifest.parent,config,a.calibration)
        except (ValueError,KeyError,OSError,cv2.error) as error:
            failures.append(dict(fixture_id=fixture['fixture_id'],reason=str(error)));scene=None
        for trial in trials:
            decision=detector.detect(scene,trial['settings']).decision.name if scene else 'UNKNOWN'
            trial['counts'][decision]+=1;trial['confusion'][fixture['label']+'->'+decision]+=1
        print(f"Prepared/evaluated {index}/{len(manifest['fixtures'])}: {fixture['fixture_id']}",file=sys.stderr,flush=True)
    report=dict(development_only=True,independent_holdout=False,config_sha256=digest(canonical(config)),
                base_config=config,manifest_sha256=digest(a.manifest.read_bytes()),
                code_sha256=digest(b''.join(f.name.encode()+f.read_bytes() for f in sorted((Path(__file__).parent/'ember_detector').glob('*.py')) if not f.name.startswith('.'))),
                tuner_sha256=digest(Path(__file__).read_bytes()),
                dependencies={'numpy':np.__version__,'opencv':cv2.__version__,'python':platform.python_version(),'machine':platform.machine()},
                preparation_failures=failures,trials=trials)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open('x') as f:json.dump(report,f,indent=2);f.write('\n')
    for trial in trials:print(json.dumps(trial))


if __name__=='__main__':main()
