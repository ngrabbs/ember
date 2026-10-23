"""Charger sizing sensitivities; not a switching or fault simulation."""
import cmath
import json
import math
from pathlib import Path

shunt = 0.033
delta_t = 65
r_min = shunt * (1 - .01) * (1 - 50e-6 * delta_t)
r_max = shunt * (1 + .01) * (1 + 50e-6 * delta_t)
i_min = (0.032 - 0.00075) / r_max
i_max = (0.032 + 0.00075) / r_min
rt_relative_max = (1 + .001) * (1 + 25e-6 * delta_t)
rt_relative_min = (1 - .001) * (1 - 25e-6 * delta_t)
f_min = 1.4 / rt_relative_max
f_max = 1.6 / rt_relative_min
l_rule = .3 * 35 / f_min
cases = []
for nominal in (4.7, 6.8, 10, 15):
    for bias_drop in (0, .1, .3):
        effective = nominal * .8 * (1 - bias_drop)
        ripple = 8.4 * (1 - 8.4 / 35) / (effective * f_min)
        cases.append(dict(nominal_uH=nominal, additional_drop=bias_drop,
                          effective_uH=effective, meets_rule=effective >= l_rule,
                          ideal_ripple_pp_A=ripple, estimated_peak_A=i_max+ripple/2))
damper = []
for freq in (1000, 3000, 10000):
    z = 2.5 + 1 / (2j * math.pi * freq * 150e-6)
    damper.append(dict(frequency_Hz=freq, branch_magnitude_ohm=abs(z),
                       branch_phase_deg=math.degrees(cmath.phase(z))))
out = dict(
    caveat='Analytical sensitivities only; component temperature/bias and source/load acceptance open',
    shunt=dict(MPN='CRF1206-FZ-R033ELF', nominal_ohm=shunt,
               assumed_min_ohm=r_min, assumed_max_ohm=r_max,
               nominal_fullscale_A=.032/shunt,
               charge_min_A=i_min, charge_max_A=i_max,
               peak_limit_typical_A=.045/shunt,
               cold_TCR_guarantee=False,
               servo_full_voltage_range_guarantee=False,
               input_servo_full_temperature_guarantee=False),
    frequency_with_RT_variation_sensitivity_MHz=[f_min, f_max],
    inductor_rule_at_nominal_RT_min_uH=.3*35/1.4,
    inductor_rule_with_RT_variation_sensitivity_uH=l_rule, inductor_cases=cases,
    candidate_15uH_max_additional_drop_at_minus20percent=1-l_rule/(15*.8),
    mosfet_one_device=[dict(current_A=i, drop_25C_V=i*.0156,
                           power_25C_W=i*i*.0156, power_2x_hot_sensitivity_W=i*i*.0312)
                      for i in (1,2,4,6)],
    damping_branch=damper,
    ideal_150uF_damper_35V_hotplug=dict(stored_J=.5*150e-6*35**2,
                                      initial_resistor_W=35**2/2.5,
                                      RC_s=2.5*150e-6),
    SYS_nominal_capacitance_uF=dict(existing_converters=102.6,
                                   proposed_charger_VOUT=40,
                                   proposed_VOUTA=.1, total=142.7),
    charge_default_2S_4p2V_plus1p5percent_V=2*4.2*1.015,
)
Path(__file__).with_name('results.json').write_text(json.dumps(out, indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k not in ('inductor_cases','mosfet_one_device')}, indent=2))
