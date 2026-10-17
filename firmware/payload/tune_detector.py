#!/usr/bin/env python3
"""Development-only spectral threshold sweep. Prepare each scene once; no CAN/RF."""
import argparse
from collections import Counter
import itertools
import json
from pathlib import Path
import cv2
from ember_detector.pipeline import load_config,prepare,canonical,digest
from ember_detector.registry import create


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('manifest','config','calibration','output'):p.add_argument('--'+name,required=True,type=Path)
    p.add_argument('--k',nargs='+',type=float,default=[.5,1,2])
    p.add_argument('--excess',nargs='+',type=float,default=[5,10,20])
    p.add_argument('--area',nargs='+',type=int,default=[8,32])
    a=p.parse_args();config=load_config(a.config)
    if config['algorithm'] not in ('spectral_excess_v1','spectral_guarded_v1'):p.error('This sweep targets spectral plugin settings')
    detector=create(config['algorithm']);trials=[]
    for k,excess,area in itertools.product(a.k,a.excess,a.area):
        settings=dict(config['detector'],k_threshold=k,excess_min=excess,min_area_px=area);detector.validate(settings)
        trials.append(dict(settings=settings,counts=Counter(),confusion=Counter()))
    manifest=json.loads(a.manifest.read_text());failures=[]
    for fixture in manifest['fixtures']:
        try:scene,_=prepare(fixture,a.manifest.parent,config,a.calibration)
        except (ValueError,KeyError,OSError,cv2.error) as error:
            failures.append(dict(fixture_id=fixture['fixture_id'],reason=str(error)));scene=None
        for trial in trials:
            decision=detector.detect(scene,trial['settings']).decision.name if scene else 'UNKNOWN'
            trial['counts'][decision]+=1;trial['confusion'][fixture['label']+'->'+decision]+=1
    report=dict(development_only=True,independent_holdout=False,config_sha256=digest(canonical(config)),
                manifest_sha256=digest(a.manifest.read_bytes()),preparation_failures=failures,trials=trials)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open('x') as f:json.dump(report,f,indent=2);f.write('\n')
    for trial in trials:print(json.dumps(trial))


if __name__=='__main__':main()
