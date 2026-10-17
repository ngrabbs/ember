#!/usr/bin/env python3
"""Run or evaluate a replaceable detector on stored fixtures. Never transmits CAN/RF."""
import argparse
from collections import Counter
import json
import re
from pathlib import Path
import cv2
import numpy as np
from ember_detector.pipeline import load_config,run


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',required=True,type=Path)
    parser.add_argument('--config',required=True,type=Path)
    parser.add_argument('--calibration',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path,help='New output directory')
    parser.add_argument('--fixture',help='One fixture ID; omit to evaluate all')
    parser.add_argument('--maps',action='store_true',help='Save numerical maps and candidate mask')
    args=parser.parse_args();config=load_config(args.config)
    manifest=json.loads(args.manifest.read_text())
    ids=[args.fixture] if args.fixture else [f['fixture_id'] for f in manifest['fixtures']]
    if not ids or len(set(ids))!=len(ids) or any(not isinstance(name,str) or not re.fullmatch(r'[A-Za-z0-9_-]+',name) for name in ids):
        parser.error('Fixture IDs must be unique nonempty names without paths')
    args.output.mkdir(parents=True,exist_ok=False)
    labels={f['fixture_id']:f.get('label','UNKNOWN') for f in manifest['fixtures']}
    results=[]
    for fixture in ids:
        result,maps=run(args.manifest,fixture,config,args.calibration)
        case=args.output/fixture;case.mkdir()
        (case/'result.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
        if args.maps and maps:
            np.savez_compressed(case/'maps.npz',**maps)
            if 'candidates' in maps:cv2.imwrite(str(case/'candidates.png'),maps['candidates'].astype('uint8')*255)
        results.append(dict(fixture_id=fixture,label=labels.get(fixture,'UNKNOWN'),result=result['result'],reason=result['reason'],elapsed_ms=result['elapsed_ms']))
        print(json.dumps(results[-1]),flush=True)
    summary=dict(input_source='STORED_FIXTURE',algorithm=config['algorithm'],development_only=True,
                 results=results,counts=dict(Counter(r['result'] for r in results)),
                 confusion=dict(Counter(r['label']+'->'+r['result'] for r in results)),
                 config_sha256=result['config_sha256'],manifest_sha256=result.get('manifest_sha256'),
                 code_sha256=result['code_sha256'],dependencies=result['dependencies'],
                 calibration_sha256=result['calibration_sha256'],pipeline_version=result['pipeline_version'])
    (args.output/'evaluation.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k!='results'}))


if __name__=='__main__':main()
