"""Ideal startup mode storage and permission; not an analogue/timing simulator."""
from itertools import product
import json
from aon_supply_budget import AON_MIN_V, AON_MAX_V
class Mode:
    def __init__(self): self.lock=False; self.bench=False; self.clock=False
    def step(self,jumper,clock=False,aon=True):
        if not aon: self.lock=False
        if not self.lock: self.bench=jumper
        if aon and clock and not self.clock: self.lock=True
        self.clock=clock
        return self.lock and self.bench and aon
sequences=0
for initial in [False,True]:
    for events in product([False,True],repeat=6):
        m=Mode(); assert not m.step(initial)
        assert m.step(initial,True)==initial
        for i,j in enumerate(events):
            m.step(j,clock=bool(i%2))
            assert m.lock and m.bench==initial
        m.step(not initial,aon=False)
        assert not m.lock
        m.step(not initial,clock=False)
        assert m.step(not initial,True)==(not initial)
        sequences+=1
count=0
for locked,aon,bench,lab_selected,lab_ok,stack_selected,stack_ok,ihu in product([False,True],repeat=8):
    # Selection inputs represent the exclusive source admission outputs.
    permit=locked and aon and ((bench and lab_selected and lab_ok) or
                              (not bench and stack_selected and stack_ok and ihu))
    if not locked or not aon: assert not permit
    if not bench and not ihu: assert not permit
    if bench and not lab_selected: assert not permit
    if not bench and not stack_selected: assert not permit
    count+=1
high=min(v*rb/(rs+rb)-5e-6*(rs*rb/(rs+rb))
         for v,rs,rb in product([AON_MIN_V,AON_MAX_V],[990,1010],[9900,10100]))
assert high>2.93
print(json.dumps({'locked_mode_sequences':sequences,'permission_combinations':count,
                  'filtered_high_min_V':round(high,6),'floating_low_max_V':.0505,
                  'result':'PASS for ideal intent and DC allocations; hardware qualification pending'},indent=2))
