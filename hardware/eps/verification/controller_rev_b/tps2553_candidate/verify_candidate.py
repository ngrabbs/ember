#!/usr/bin/env python3
"""Read-only proposal checks; deliberately does not authorize/native-author parts."""
import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def decoded(result):
    return json.loads(next(c['text'] for c in result['content'] if c['type'] == 'text'))


def main():
    baseline = json.loads((HERE / 'baseline.json').read_text())
    for name, digest in baseline['frozen'].items():
        assert sha((ROOT / name).read_bytes()) == digest, name
        committed = subprocess.check_output(['git', 'show', baseline['basis'] + ':' + name], cwd=ROOT)
        assert sha(committed) == digest, name
    tracked = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')
    native = lambda p: Path(p).suffix in {'.kicad_sch', '.kicad_pro', '.kicad_pcb', '.kicad_sym', '.kicad_mod'} or Path(p).name in {'sym-lib-table', 'fp-lib-table'}
    assert set(filter(native, filter(None, tracked))) == set(baseline['native_paths'])
    # Detect untracked native additions too, while excluding preexisting ignored files.
    new = subprocess.check_output(['git', 'ls-files', '--others', '--exclude-standard', '-z'], cwd=ROOT).decode().split('\0')
    assert not [p for p in new if p and native(p)]
    for name, digest in json.loads((HERE / 'source_sha256.json').read_text()).items():
        assert sha((HERE / name).read_bytes()) == digest, name
    from pypdf import PdfReader
    assert len(PdfReader(HERE / 'tps2553-1.pdf').pages) == 44
    assert sha((HERE / 'tps2553-1.pdf').read_bytes()) == '89d15eeda9575fb38ddcfc491b122e370fe76dd75a9cc49a31a1abc4110983ee'
    queries = json.loads((HERE / 'library_queries.json').read_text())
    assert decoded(queries['symbol_search'])['count'] == 0
    assert not any(x['nickname'] == 'KiCadLib' for x in decoded(queries['libraries'])['libraries'])
    stock = decoded(queries['stock'])
    assert stock['pad_count'] == len(stock['pads']) == 6
    assert Counter(p['number'] for p in stock['pads']) == Counter(map(str, range(1, 7)))
    assert all(p['width'] == 1.325 and p['height'] == 0.6 for p in stock['pads'])
    expected = json.loads((HERE / 'proposed_map.json').read_text())
    assert len(expected['leads']) == 6
    assert Counter(p['number'] for p in expected['leads']) == Counter(map(str, range(1, 7)))
    assert expected['leads'][4]['type'] == 'output'
    assert expected['raw_objects'] == 12 and expected['blank_mask_objects'] == 6
    assert abs(0.95 - 0.6 - 0.35) < 1e-12
    assert abs(0.95 - 0.7 - 0.25) < 1e-12
    result = {'status': 'READ_ONLY_PROPOSAL_NOT_APPROVED', 'basis': baseline['basis'], 'frozen_tracked_files': len(baseline['frozen']), 'protected_native_files_unchanged': len(baseline['native_paths']), 'physical_leads_proposed': 6, 'raw_objects_proposed_not_constructed': 12, 'native_acceptance': 'NOT_STARTED', 'circuit_selection': 'OPEN'}
    (HERE / 'verified.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
