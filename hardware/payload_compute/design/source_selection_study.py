"""Source-selection intent and power screens; no physical circuit acceptance."""
from itertools import product
import json

def admission(aon,mode_locked,source_locked,bench,alive,request,present,
              voltage_ok,pd_full):
    # Requests are independently latched one-hot bits. Reject illegal encoding
    # globally, rather than granting whichever branch happens to be healthy.
    shared=aon and mode_locked and source_locked and alive and sum(request)==1
    # Bench uses one cable/source at a time. Stack presence is irrelevant here.
    one_lab_present=present[0]!=present[1]
    return (
        bool(shared and bench and one_lab_present and request[0] and present[0]
             and voltage_ok[0] and pd_full),
        bool(shared and bench and one_lab_present and request[1] and present[1]
             and voltage_ok[1]),
        bool(shared and not bench and request[2] and present[2] and voltage_ok[2]),
    )

count=0
for bits in product([False,True],repeat=15):
    aon,ml,sl,bench,alive,pd=bits[:6]
    req,pres,valid=bits[6:9],bits[9:12],bits[12:15]
    result=admission(aon,ml,sl,bench,alive,req,pres,valid,pd)
    allowed=[False]*3
    if all([aon,ml,sl,alive]) and list(req).count(True)==1:
        target=list(req).index(True)
        if bench and target in [0,1] and list(pres[:2]).count(True)==1:
            allowed[target]=bool(pres[target] and valid[target] and (pd if target==0 else True))
        elif not bench and target==2:
            allowed[2]=bool(pres[2] and valid[2])
    assert result==tuple(allowed)
    assert sum(result)<=1
    assert not any(result[:2]) if not bench else not result[2]
    count+=1

# Separate AON bootstrap is necessary: main paths all off before mode lock.
assert admission(True,False,False,True,False,(True,False,False),
                 (True,False,False),(True,False,False),True)==(False,False,False)

# Source latch intent: ordinary MCU reset and source detach do not retarget it.
# Resetting the AON domain is the only defined unlock; no seamless transfer.
class SourceLock:
    def __init__(self):
        self.bits=(False,False,False)
        self.locked=False
    def sample(self,request,lock=False,aon_reset=False):
        if aon_reset:
            self.bits=(False,False,False);self.locked=False
        elif not self.locked:
            self.bits=tuple(request)
            if lock:
                assert sum(self.bits)==1
                self.locked=True
        return self.bits

sequences=0
for initial in [(True,False,False),(False,True,False),(False,False,True)]:
    latch=SourceLock();assert latch.sample(initial,lock=True)==initial
    for changed in product([False,True],repeat=3):
        assert latch.sample(changed)==initial
        sequences+=1
    latch.sample((False,False,False),aon_reset=True)
    assert not latch.locked and not any(latch.bits)

# Source health: AUXOFF can remain high during faults; FLT can remain released
# during UV/OV. Neither is accepted alone.
def health(enabled,raw_ok,bus_ok,inrush,no_fault,profile_ok):
    return all([enabled,raw_ok,bus_ok,inrush,no_fault,profile_ok])
health_cases=0
for flags in product([False,True],repeat=6):
    assert health(*flags)==(sum(flags)==6)
    health_cases+=1
assert not health(True,True,False,True,False,True)  # AUXOFF high, thermal fault.
assert not health(True,False,False,False,True,True)  # FLT released during UV.
assert not health(True,True,True,True,True,False)  # Lost USB contract.

def divider(top,bottom,lo,hi,leak=.1e-6):
    vals=[v*(1+t/b)+i*t for t,b,v,i in product(
        [top*.999,top*1.001],[bottom*.999,bottom*1.001],
        [lo,hi],[-leak,leak])]
    return [min(vals),max(vals)]
uv=divider(374e3,37.4e3,1.183,1.223,1.1e-6)  # Conditional combined clamp leakage.
ov=divider(365e3,29.4e3,1.183,1.223)
assert uv[1]<14.25 and ov[0]>15.75
old_usb_top=56.2e3
assert old_usb_top<350e3  # Violates TI's recommendation for >5 V/reverse exposure.
assert min(1e6,365e3,374e3,665e3)>=350e3

limit_min=3.960/1.001
limit_max=4.840/.999
flight=(18.075*1.2)/(.85*6)
lab=(22.075*1.2)/(.85*6)
assert flight>limit_min and lab>limit_max
bootstrap_active_A=.350/(.8*(4.75-.4))
bootstrap_target_A=.250/(.8*(4.75-.4))
assert bootstrap_active_A>.100 and bootstrap_target_A<.100
print(json.dumps({
    'source_admission_combinations':count,
    'locked_source_sequences':sequences,'source_health_combinations':health_cases,
    'usb_main_uv_rising_V':uv,'usb_main_ov_rising_V':ov,
    'battery_limit_min_A_screen':limit_min,'battery_limit_max_A_screen':limit_max,
    'flight_15W_20percent_allowance_6V_A':flight,
    'lab_15W_20percent_allowance_6V_A':lab,
    'active_AON_USB_bootstrap_A_screen':bootstrap_active_A,
    'reduced_AON_USB_bootstrap_A_screen':bootstrap_target_A,
    'status':'PASS for intent/screens; USB clamp unqualified; full bootstrap/source-lock/health hardware unimplemented'
},indent=2))
