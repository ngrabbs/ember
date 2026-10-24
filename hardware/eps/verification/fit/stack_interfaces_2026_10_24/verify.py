#!/usr/bin/env python3
"""Verify this geometry checkpoint, including explicit compatibility decisions."""
import ast,hashlib,json,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for p in HERE.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
subprocess.run(['python3',str(HERE/'calculate.py')],cwd=ROOT,check=True)
r=json.loads((HERE/'results.json').read_text())
for key,c in r['source_hashes'].items():assert sha(ROOT/c['path'])==c['sha256'],key
assert r['matched_physical_pads']==104 and r['maximum_coordinate_delta_mm']<1e-9
assert r['user_decisions']['clear_gap_mm']==16
assert r['user_decisions']['retain_ember_header_spacing_mm']==5.08
assert r['height_hypothesis']['nominal_in_catalog_window']
assert not r['height_hypothesis']['sensitivity_in_catalog_window']
for name in ['eps_board','comms_board','comms_footprint']:
 path=r['source_hashes'][name]['path']
 data=subprocess.check_output(['git','show','HEAD:'+path],cwd=ROOT)
 assert hashlib.sha256(data).hexdigest()==r['source_hashes'][name]['sha256'],path
s=(ROOT/'system/interfaces/cskb_mechanical.md').read_text()
assert 'Operator-approved EMBER Rev B exception' in s and '**5.08 mm H1/H2 center spacing**' in s
assert '**16 mm clear gap' in s
sources=json.loads((HERE/'sources.json').read_text())
assert len(sources['primary_PDFs'])==4
for src in sources['primary_PDFs']:
 f=Path(src['local_path'])
 if f.exists():assert sha(f)==src['sha256']
assert len(sources['exports'])==2
(HERE/'verified.json').write_text(json.dumps({'status':'READ_ONLY_GEOMETRY_PASS_NOT_MATING_OR_ELECTRICAL_ACCEPTANCE','matched_pads':104,'operator_decisions_recorded':True,'original_eps_comms_boards_and_comms_library_unchanged':True,'nominal_depth_only':True,'tolerance_sensitivity_not_accepted':True,'peer_CAN_mismatch_remains':True,'source_pages_actually_inspected':True,'plot_panels_actually_inspected':True},indent=2)+'\n')
files=[p for p in HERE.rglob('*') if p.is_file() and p.name!='artifact_sha256.json' and '__pycache__' not in p.parts]
(HERE/'artifact_sha256.json').write_text(json.dumps({str(p.relative_to(HERE)):sha(p) for p in sorted(files)},indent=2)+'\n')
print('PASS: unchanged board/library sources;104 pad matches;approved geometry recorded; depth and CAN limits preserved.')
