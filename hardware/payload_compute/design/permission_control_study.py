"""Permission network intent/DC analysis; exported topology is checked separately."""
from itertools import product
import json

def gates(aon,locked,bench,lab_sel,lab_ok,stack_sel,stack_ok,ihu):
    rx=ihu
    stack_mode=not bench
    lab_deny=not (bench and lab_sel and lab_ok)
    stack_base=stack_mode and stack_sel and stack_ok
    stack_deny=not (stack_base and rx)
    branch=not (lab_deny and stack_deny)
    exclusive=not (lab_sel and stack_sel)
    ready=locked and aon and exclusive
    return branch and ready

count=0
for aon,locked,bench,ls,lo,ss,so,ihu,request in product([False,True],repeat=9):
    p=gates(aon,locked,bench,ls,lo,ss,so,ihu)
    # Independent requirement: exactly one selection, and the selected mode's
    # source must be qualified; IHU authorization applies only in stack mode.
    want=False
    if aon and locked and (ls != ss):
        want=(ls and lo) if bench else (ss and so and ihu)
    assert p==want
    assert not (p and request) if (not aon or not locked or (ls and ss)) else True
    count+=1

from run_latch_study import Latch
m=Latch()
assert m.step(permission=gates(True,True,False,False,False,True,True,True),d=True,clock=True)[1]
assert not m.step(permission=False,d=True,clock=True)[1]
assert not m.step(permission=True,d=True,clock=True)[1]
m.step(permission=True,d=True,clock=False)
assert m.step(permission=True,d=True,clock=True)[1]

corners=[]
for rs,rp,ib in product([99,101],[9900,10100],[-5e-6,5e-6]):
    equiv=rs*rp/(rs+rp)
    corners.append((3.0*rp/(rs+rp)-ib*equiv,
                    .4*rp/(rs+rp)-ib*equiv))
high=min(x[0] for x in corners);low=max(x[1] for x in corners)
assert high>2.0 and low<.8
print(json.dumps({'permission_and_request_combinations':count,
                  'receiver_corner_combinations':len(corners),
                  'received_high_min_V':round(high,6),
                  'received_low_max_V':round(low,6),
                  'missing_drive_max_V':.0505,
                  'ideal_kill_and_fresh_rearm':'PASS',
                  'physical_circuit_status':'See validation/check_permission_study.py; physical timing unqualified'},indent=2))
