"""Analytical development checks, not a switching simulation or hardware qualification."""
import cmath
import itertools
import json
import math
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
OUT = BASE / 'verification/evidence/2026-10-23_recovery_5v_analysis.json'


def loop(f, vin, current, capacitance, esr, inductance):
    # TI SLVSHG1 equations 19-26. Infinite error-amplifier output resistance
    # approximation. Excludes sampled-data, transition, PFM and current-limit loops.
    load = 5 / current
    total_load = load + .02
    raw = 5 + current * .02
    duty = max(0, 1 - vin / raw)
    pole = 2 / (2 * math.pi * total_load * capacitance)
    rhpz = total_load * (1-duty)**2 / (2*math.pi*inductance)
    s = 2j * math.pi * f
    plant = total_load * (1-duty) / (.055*2)
    plant *= (1+s*esr*capacitance)/(1+s/(2*math.pi*pole))
    if vin < raw:
        plant *= 1-s/(2*math.pi*rhpz)
    impedance = (1+s*3740*75e-9)/(s*(75e-9+300e-12)+s*s*3740*75e-9*300e-12)
    return plant * 190e-6 * impedance * (1.2/5) * load/total_load


def analyze():
    corners = []
    for vin, current, cap, esr, inductance in itertools.product(
            [4.5, 6, 8.4, 35], [.5, 2], [220e-6, 450e-6], [.002, .05], [5.6e-6, 12e-6]):
        previous = abs(loop(10, vin, current, cap, esr, inductance))
        for i in range(1, 1001):
            f = 10 * (20000/10)**(i/1000)
            gain = loop(f, vin, current, cap, esr, inductance)
            if previous >= 1 > abs(gain):
                corners.append(dict(vin_V=vin, load_A=current, C_F=cap, ESR_ohm=esr,
                                    L_H=inductance, crossover_Hz=f,
                                    estimated_phase_margin_deg=180+math.degrees(cmath.phase(gain))))
                break
            previous = abs(gain)
        else:
            raise AssertionError('No crossover found within model range')
    ripple = []
    for vin, inductance, frequency in itertools.product([4.5, 6, 8.4, 35], [5.6e-6, 10e-6], [360e3, 400e3]):
        raw = 5.04
        if vin < raw:
            pp = vin*(1-vin/raw)/(inductance*frequency)
            average = raw*2/(vin*.85)
        else:
            pp = raw*(vin-raw)/(vin*inductance*frequency)
            average = 2
        ripple.append(dict(vin_V=vin, L_H=inductance, f_Hz=frequency,
                           ripple_A_pp=pp, average_A=average, peak_A=average+pp/2))
    data = {
        'date': '2026-10-23',
        'status': 'DEVELOPMENT: no bench/switching-model/thermal qualification',
        'assumptions': {'load_A': 2, 'low_converter_input_V': 4.5, 'protected_input_ceiling_V': 35,
                        'efficiency_sensitivity': [.85, .90], 'C_effective_F': [220e-6, 450e-6],
                        'ESR_sensitivity_ohm': [.002, .05], 'frequency_360k_is_sensitivity_not_guaranteed_corner': True},
        'feedback_V': {'nominal': 1.2*(1+31.6/10),
                       'minimum_including_100nA_leakage': 1.188*(1+31.6*.999/(10*1.001))-.0000001*31600*1.001,
                       'maximum_including_100nA_leakage': 1.212*(1+31.6*1.001/(10*.999))+.0000001*31600*1.001},
        'uvlo': {'rising_min_V': 1.20*(1+39.2*.999/(16.9*1.001)),
                 'rising_max_V': 1.26*(1+39.2*1.001/(16.9*.999)),
                 'nominal_rising_V': 1.23*(1+39.2/16.9),
                 'current_hysteresis_component_V': [4.4e-6*39200*.999, 5.6e-6*39200*1.001],
                 'falling_threshold_not_guaranteed': 'Internal hysteresis voltage has only a typical value; characterize brownout/restart.'},
        'output_current_limit_A': [.048/(.020*1.01), .052/(.020*.99)],
        'shunt_loss_W_at_2A': 2**2*.02,
        'switching_frequency_Hz_nominal': 1000/(.05*49300+35)*1e6,
        'inductance': {'inner_loop_minimum_H_at_360k': 1.2/360e3,
                       'selected_nominal_H': 10e-6, 'effective_sensitivity_min_H': 5.6e-6},
        'estimated_input_A_at_4p5V': {str(eta): 5.04*2/(4.5*eta) for eta in [.85,.90]},
        'total_loss_W_scenarios': {str(eta): 5.04*2*(1/eta-1)+.08 for eta in [.85,.90]},
        'output_bank_nominal_F': 3*100e-6+4*22e-6,
        'bulk_minimum_F_from_initial_tolerance_only': 3*100e-6*.8,
        'startup_capacitor_current_A_at_min_2p5ms': 388e-6*5/.0025,
        'load_step_droop_V_at_220uF_25us_10mOhm': 1.9*25e-6/220e-6+1.9*.01,
        'ripple_cases': ripple,
        'loop_model': {'scope': 'TI averaged buck/boost approximation; no valid transition/PFM prediction',
                       'Rc_ohm':3740, 'Cc_F':75e-9, 'Cp_F':300e-12,
                       'corners':corners,
                       'minimum_estimated_phase_margin_deg':min(x['estimated_phase_margin_deg'] for x in corners),
                       'crossover_range_Hz':[min(x['crossover_Hz'] for x in corners),max(x['crossover_Hz'] for x in corners)]},
    }
    assert data['uvlo']['rising_max_V'] < 4.5
    assert data['output_current_limit_A'][0] > 2
    assert data['inductance']['effective_sensitivity_min_H'] > data['inductance']['inner_loop_minimum_H_at_360k']
    return data


if __name__ == '__main__':
    result = analyze()
    OUT.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k: result[k] for k in ['feedback_V','uvlo','output_current_limit_A','estimated_input_A_at_4p5V']}))
    print('Analytical checks passed; model phase-margin minimum:', result['loop_model']['minimum_estimated_phase_margin_deg'])
