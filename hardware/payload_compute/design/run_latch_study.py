"""Ideal event model; no analogue ramps or asynchronous timing simulation."""
from itertools import product
import json
from aon_supply_budget import AON_MIN_V, SUPERVISOR_RELEASE_MAX_V

class Latch:
    def __init__(self):
        self.q = False
        self.clock = False
    def step(self, *, aon=True, source=True, permission=True, request=True,
             alive=True, window=True, shutdown_ok=True, d=False, clock=False):
        buck = aon and source and permission and request and alive
        clear_n = buck and window and shutdown_ok
        if not clear_n:
            self.q = False
        elif clock and not self.clock:
            self.q = d
        self.clock = clock
        return buck, self.q

# Exhaust every prior state, prior clock, seven clear inputs, D and clock.
checked = 0
for bits in product([False, True], repeat=11):
    q, old_clock, aon, source, permission, request, alive, window, ok, d, clk = bits
    m = Latch(); m.q = q; m.clock = old_clock
    buck, out = m.step(aon=aon, source=source, permission=permission,
                      request=request, alive=alive, window=window,
                      shutdown_ok=ok, d=d, clock=clk)
    assert buck == all([aon, source, permission, request, alive])
    if not all([aon, source, permission, request, alive, window, ok]):
        assert not out
    elif clk and not old_clock:
        assert out == d
    else:
        assert out == q
    checked += 1

faults = ['aon', 'source', 'permission', 'request', 'alive', 'window', 'shutdown_ok']
for fault in faults:
    m = Latch()
    assert not m.step(window=False)[1]  # converter may start before main rail
    assert not m.step(d=True)[1]  # D alone cannot arm
    assert m.step(d=True, clock=True)[1]
    assert not m.step(d=True, clock=True, **{fault: False})[1]
    assert not m.step(d=True, clock=True)[1]  # recovery while clock stale high
    assert not m.step(d=False, clock=True)[1]  # data change is not an edge
    assert not m.step(d=False, clock=False)[1]
    assert not m.step(d=False, clock=True)[1]  # unqualified rising edge ignored
    assert not m.step(d=True, clock=True)[1]  # qualification cannot create edge
    m.step(d=True, clock=False)
    assert m.step(d=True, clock=True)[1]  # deliberate fresh edge required

# Policy qualification: elapsed stability alone does not replace discharge proof.
class Qualification:
    def __init__(self): self.since = None
    def ready(self, ms, healthy, discharged):
        if not healthy:
            self.since = None
            return False
        if self.since is None: self.since = ms
        return discharged and ms - self.since >= 100
q = Qualification()
assert not q.ready(0, True, True)
assert not q.ready(99, True, True)
assert not q.ready(100, True, False)
assert q.ready(100, True, True)
assert not q.ready(101, False, True)
assert not q.ready(200, True, True)
assert not q.ready(299, True, True)
assert q.ready(300, True, True)
release_margin = AON_MIN_V - SUPERVISOR_RELEASE_MAX_V
assert release_margin > 0
print(json.dumps({'ideal_state_transitions': checked, 'fault_recovery_sequences': 7,
                  'qualification_checks': 8, 'aon_release_margin_mV': round(1000*release_margin, 3),
                  'result': 'PASS; physical timing and ramps unqualified'}, indent=2))
