"""Check the portable helper packet without LTspice, models or raw files."""
from pathlib import Path
import csv
import gzip
import hashlib
import json
import math

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
read = lambda name: json.loads((HERE / name).read_text())
sha = lambda data: hashlib.sha256(data).hexdigest()
manifest = read('evidence_sha256.json')
for name, digest in manifest.items():
    assert sha((HERE / name).read_bytes()) == digest, name
native = read('native_preservation.json')
assert native['baseline'] == 'ac4a4b9' and native['preserved_native_files'] == 230
for name, digest in native['sha256'].items():
    assert sha((ROOT / name).read_bytes()) == digest, name
for name, hashes in read('log_archive.json').items():
    data = (HERE / name).read_bytes()
    assert sha(data) == hashes['compressed_sha256']
    assert sha(gzip.decompress(data)) == hashes['original_sha256']

results = read('gate_results.json')
assert len(results) == 26
for result in results:
    stem = HERE / 'gate_decks' / result['case']
    assert result['status'] == 'COMPLETED_NOMINAL_HELPER_ONLY_BENCH'
    assert result['warning_count'] == 0 and abs(result['endpoint_s'] - 30e-6) < 1e-15
    assert sha(Path(str(stem) + '.cir').read_bytes()) == result['deck_sha256']
    with Path(str(stem) + '.csv').open() as f:
        samples = [{k: float(v) for k, v in row.items()} for row in csv.DictReader(f)]
    peak = max(abs(row['helper_Id_A']) for row in samples)
    assert math.isclose(peak, result['helper_Id_peak_A'], rel_tol=1e-12)
    crossing = next(row['time_s'] - 13e-6 for row in samples if row['time_s'] >= 13e-6 and row['main_gate_proxy_V'] < 1)
    assert math.isclose(crossing, result['main_gate_first_below_1V_after_DRV_s'], rel_tol=1e-12)
    assert not result['guaranteed_DRV_or_main_FET_SOA_acceptance']
assert len(read('coupled_attempts.json')) == 9
assert read('summary.json')['scope'] == 'NOMINAL_HELPER_ONLY_BENCH; NO_TPS_DRIVER_OR_MAIN_FET_SURVIVAL_ACCEPTANCE'
print('26 completed helper traces, 9 separate coupled attempts, all evidence hashes and 230 native files verified; no survival/qualification acceptance.')
