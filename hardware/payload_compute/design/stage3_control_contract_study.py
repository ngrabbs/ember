"""Ideal control-contract invariants; no KiCad mutation or electrical proof."""
from itertools import product
from pathlib import Path
import json


def choices(reset, mode_locked, source_locked, bench, q):
    onehot = sum(q) == 1
    committed = reset and mode_locked and source_locked and onehot
    return tuple(bool(committed and bit and (bench if i < 2 else not bench))
                 for i, bit in enumerate(q))


def mode_permission(reset, mode_locked, source_locked, bench, ihu, q):
    usb, lab, stack = choices(reset, mode_locked, source_locked, bench, q)
    return bool(reset and mode_locked and (usb or lab or (stack and ihu)))


cases = 0
for reset, ml, sl, bench, ihu, *q in product([False, True], repeat=8):
    selected = choices(reset, ml, sl, bench, q)
    permit = mode_permission(reset, ml, sl, bench, ihu, q)
    assert sum(selected) <= 1
    assert not permit or (reset and ml and sl and sum(q) == 1)
    assert not permit or ((bench and (q[0] or q[1])) or
                          (not bench and q[2] and ihu))
    if not bench and not ihu:
        assert not permit
    if bench:
        assert permit == mode_permission(reset, ml, sl, bench, not ihu, q)
    if sum(q) != 1 or not reset or not ml or not sl:
        assert not any(selected) and not permit
    cases += 1

# These are requirement models, not simulations of actual asynchronous gates.
result = {
    'result': 'PASS for ideal stage3 control contract only',
    'mode_source_cases': cases,
    'invariants': [
        '000/multihot and uncommitted mode/source deny permission',
        'bench permits USB/bench only; flight permits stack only with IHU high',
        'source choice does not establish raw/PD/bus/inrush qualification'
    ],
    'limits': [
        'Actual exported gate topology must independently implement these rules',
        'Stored-choice retention and watchdog/reset qualification need actual topology and state checks',
        'No metastability, propagation-race, brownout or partial-power proof',
        'MCU_READY must come from healthy supervisor state; WDI must come from its live loop',
        'Full AON loss requires persistent unclean-session recovery policy',
        'No direct buck/Jetson enable or flight inhibit acceptance'
    ]
}
p = Path(__file__).with_name('stage3_control_contract_results.json')
p.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
