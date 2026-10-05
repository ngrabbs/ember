"""Candidate steady-state allocation, not a measured regulator guarantee.

TI LMR36506 SNVSBB6C fixed 3.3 V auto-mode system accuracy table:
minus 1.5%, plus 2.5% under its stated operating conditions.
Separate ripple, routing drops, ramps, dropout and transient allowances remain open.
"""
from itertools import product
import json

AON_MIN_V = 3.3 * 0.985
AON_MAX_V = 3.3 * 1.025
SUPERVISOR_RELEASE_MAX_V = 3.07 * (1.015 + 0.025)

def results():
    bench_high = min(v*rb/(rs+rb)-5e-6*rs*rb/(rs+rb)
                     for v, rs, rb in product([AON_MIN_V, AON_MAX_V],
                                               [990, 1010], [9900, 10100]))
    assert 3.0 <= AON_MIN_V < AON_MAX_V <= 3.6
    assert AON_MIN_V > SUPERVISOR_RELEASE_MAX_V
    return {
        'candidate': 'LMR36506R3RPER; fixed 3.3 V, PFM/auto mode',
        'steady_allocation_min_V': round(AON_MIN_V, 6),
        'steady_allocation_max_V': round(AON_MAX_V, 6),
        'supervisor_release_max_V': round(SUPERVISOR_RELEASE_MAX_V, 6),
        'static_release_margin_mV': round(1000*(AON_MIN_V-SUPERVISOR_RELEASE_MAX_V), 3),
        'lvc_3_to_3p6_supply_range': 'inside at these allocated DC corners',
        'bench_filtered_high_min_V': round(bench_high, 6),
        'bench_schmitt_threshold_envelope': 'UNQUALIFIED; no interpolation between test points',
        'result': 'PASS for candidate DC allocation; startup/transient/passive qualification pending; prototype package map accepted',
    }

if __name__ == '__main__':
    print(json.dumps(results(), indent=2))
