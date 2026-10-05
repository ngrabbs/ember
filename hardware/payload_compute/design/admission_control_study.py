"""Conditional DC screen only: MOSFET hot/cold and ramp behavior unqualified."""
from itertools import product
import json

def thresholds(top,bottom,lo,hi,leak):
    v=[x*(1+t/b)+i*t for t,b,x,i in product(
        [top*.999,top*1.001],[bottom*.999,bottom*1.001],
        [lo,hi],[-leak,leak])]
    return [min(v),max(v)]
uv_up=thresholds(374e3,37.4e3,1.183,1.223,1.1e-6)
uv_down=thresholds(374e3,37.4e3,1.076,1.116,1.1e-6)
ov_up=thresholds(365e3,29.4e3,1.183,1.223,.1e-6)
ov_down=thresholds(365e3,29.4e3,1.076,1.116,.1e-6)
assert uv_up[1]<14.25 and ov_up[0]>15.75
# Conditional 25 C allocations; IDSS at zero VGS does not bound a nonzero gate.
gates=[(raw/t-leak)/(1/t+1/b) for raw,t,b,leak in product(
    [6,23],[20e3*.99,20e3*1.01],[10e3*.99,10e3*1.01],[-1.1e-6,1.1e-6])]
assert min(gates)>1.8 and max(gates)<12
clamp_current=23/(374e3*.999)
clamped_en=clamp_current*.033
assert clamped_en<.45
# Q2 on, using 25 C RDS(on) at >=1.8 V. No temperature guarantee.
q1_gate_on=(23/(20e3*.99))*.033
assert q1_gate_on<.4
q2_high=(2.4/(100*1.01+1000*.99)-.1e-6)*1000*.99
assert q2_high>1.8
# Logic-low VOL=0.4 is not a leakage specification for this MOSFET.
q2_gate_low=.4*1010/(99+1010)
power_off_gate=(10e-6+.1e-6)*1010
# TPS25947 table current-limit point 1.65k: 1.8..2.2 A, resistor scaling.
limit=[1.8/1.001,2.2/.999]
# Equation 4 is nominal, not a timing bound. Cap tolerance/voltage derating unknown.
nominal_slew_V_ms=2000/10000
nominal_charge_A=100e-6*nominal_slew_V_ms*1000
nominal_ramp_ms=15/nominal_slew_V_ms
results={'qualification':'CONDITIONAL DC SCREEN; not a default-off guarantee',
 'usb_uv_rising_V':uv_up,'usb_uv_falling_V':uv_down,
 'usb_ov_rising_V':ov_up,'usb_ov_falling_V':ov_down,
 'uv_combined_leakage_allocation_A':1.1e-6,
 'raw_bias_gate_6_to_23V_V': [min(gates),max(gates)],
 'conditional_EN_clamped_V':clamped_en,
 'conditional_Q1_gate_with_grant_V':q1_gate_on,
 'Q2_gate_high_min_V':q2_high,'Q2_gate_low_VOL_0p4V_screen_V':q2_gate_low,
 'Q2_power_off_gate_10uA_screen_V':power_off_gate,
 'usb_current_limit_A_screen':limit,
 'nominal_output_slew_V_ms':nominal_slew_V_ms,
 'nominal_100uF_charge_A':nominal_charge_A,'nominal_15V_ramp_ms':nominal_ramp_ms,
 'open_items':['Q2 leakage at nonzero VGS and hot/cold','grant low and partial-power behavior',
 'raw fast/slow ramps and Cgd injection','negative input and entry protection',
 'capacitor tolerances, load inrush and measured reset latency']}
print(json.dumps(results,indent=2))
