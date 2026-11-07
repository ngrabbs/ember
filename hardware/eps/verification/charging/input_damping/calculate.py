#!/usr/bin/env python3
"""Passive damping bounds and small-signal network sensitivity; not loop stability."""
import cmath
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
R=2.7
CAP=204e-6
# ±5% initial resistance; a symmetric ±80 ppm/K over 65 K is a conservative
# sensitivity for the documented negative-TCR wire, not a new coefficient claim.
rlo=R*.95*(1-80e-6*65)
rhi=R*1.05*(1+80e-6*65)
cmin=CAP*.8
cmax=CAP*1.2
cend_high=cmax*1.3
V=35
result={
 'scope':'Development component allocation; hot pulse, actual effective capacitance and coupled loop qualification open',
 'resistor_candidate':'AC05000002708JAC00',
 'capacitor_candidate':{'part':'EEHZA1H680P','quantity':3},
 'resistance_sensitivity_ohm':[rlo,rhi],
 'capacitance_initial_F':[cmin,cmax],
 'capacitance_endurance_high_sensitivity_F':cend_high,
 'capacitance_endurance_low_sensitivity_F':cmin*.7,
 'nominal_time_constant_s':R*CAP,
 'ideal_35V_step_peak_W':V**2/rlo,
 'ideal_35V_step_energy_J':.5*cend_high*V**2,
 'constant_1A_short_resistor_W':rhi,
 'rejected_two_5p1ohm_1W_parallel_nominal_short_per_resistor_W':5.1/4,
 'source_capacitance_nominal_F':98e-6,
 'system_input_capacitance_proposed_nominal_F':142.7e-6,
 'source_plus_system_plus_new_damper_nominal_F':98e-6+142.7e-6+CAP,
 'impedance_sensitivity':[]
}
for freq in [1000,3000,10000]:
 w=2*cmath.pi*freq
 zd=R+1/(1j*w*CAP)
 # Lumped bank sensitivity, not capacitor frequency specifications. No input
 # control, INFET dynamics, harness, source protector or converter switching.
 zcer=1/(1j*w*30e-6)+.002
 zbulk=1/(1j*w*68e-6)+.030
 zbank=1/(1/zcer+1/zbulk)
 zcombined=1/(1/zbank+1/zd)
 zsys=1/(1j*w*142.7e-6)+.002
 zall=1/(1/zcombined+1/zsys)
 result['impedance_sensitivity'].append({'frequency_Hz':freq,'damper_alone_abs_ohm':abs(zd),'source_bank_plus_damper_abs_ohm':abs(zcombined),'source_bank_plus_damper_real_ohm':zcombined.real,'source_bank_plus_damper_phase_deg':cmath.phase(zcombined)*180/cmath.pi,'including_conducting_PowerPath_system_bank_abs_ohm':abs(zall),'including_conducting_PowerPath_system_bank_real_ohm':zall.real})
(HERE/'calculations.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
