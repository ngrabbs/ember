"""Analytical development checks, not a switching simulation or hardware qualification."""
import cmath
import itertools
import json
import math
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
OUT = BASE / 'verification/evidence/2026-10-23_recovery_5v_analysis.json'


def loop(f, vin, current, capacitance, esr, inductance, rc=3740, cc=75e-9, cp=300e-12):
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
    impedance = (1+s*rc*cc)/(s*(cc+cp)+s*s*rc*cc*cp)
    return plant * 190e-6 * impedance * (1.2/5) * load/total_load


def analyze():
    # Screening range agreed 2026-10-23; not a qualified spacecraft ambient.
    resistor_error = .001 + 25e-6*65  # initial tolerance + independent TCR, -40 C vs 25 C
    shunt_error = .01 + 50e-6*65
    c0g_error = .05 + 30e-6*65  # temperature term conservatively extended to cold
    corners = []
    for vin, current, cap, esr, inductance, rc, cc, cp in itertools.product(
            [4.5, 6, 8.4, 35], [.5, 2], [160e-6, 500e-6], [.002, .05, .8/3],
            [3.808e-6, 8.16e-6], [3740*(1-resistor_error), 3740*(1+resistor_error)],
            [75e-9*(1-c0g_error), 75e-9*(1+c0g_error)],
            [300e-12*(1-c0g_error), 300e-12*(1+c0g_error)]):
        previous = abs(loop(10, vin, current, cap, esr, inductance, rc, cc, cp))
        for i in range(1, 1001):
            f = 10 * (20000/10)**(i/1000)
            gain = loop(f, vin, current, cap, esr, inductance, rc, cc, cp)
            if previous >= 1 > abs(gain):
                corners.append(dict(vin_V=vin, load_A=current, C_F=cap, ESR_ohm=esr,
                                    L_H=inductance, Rc_ohm=rc, Cc_F=cc, Cp_F=cp, crossover_Hz=f,
                                    estimated_phase_margin_deg=180+math.degrees(cmath.phase(gain))))
                break
            previous = abs(gain)
        else:
            raise AssertionError('No crossover found within model range')
    ripple = []
    for vin, inductance, frequency in itertools.product([4.5, 6, 8.4, 35], [3.808e-6, 6.8e-6], [360e3, 400e3]):
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
                        'efficiency_sensitivity': [.85, .90], 'C_effective_F': [160e-6, 500e-6],
                        'ESR_sensitivity_ohm': [.002, .05, .8/3],
                        'electronics_screening_C': [-40, 85], 'qualified_operating_temperature': None,
                        'resistor_initial_plus_TCR_error': resistor_error,
                        'c0g_initial_plus_temperature_sensitivity': c0g_error,
                        'cold_ESR_is_lumped_sensitivity_not_validated_multibranch_bank': True,
                        'frequency_360k_is_sensitivity_not_guaranteed_corner': True},
        'feedback_V': {'nominal': 1.2*(1+31.6/10),
                       'minimum_including_100nA_leakage_and_TCR': 1.188*(1+31.6*(1-resistor_error)/(10*(1+resistor_error)))-.1e-6*31600*(1+resistor_error),
                       'maximum_including_100nA_leakage_300nA_CDC_and_TCR': 1.212*(1+31.6*(1+resistor_error)/(10*(1-resistor_error)))+.4e-6*31600*(1+resistor_error)},
        'uvlo': {'rising_min_V': 1.20*(1+39.2*(1-resistor_error)/(16.9*(1+resistor_error))),
                 'rising_max_V': 1.26*(1+39.2*(1+resistor_error)/(16.9*(1-resistor_error))),
                 'nominal_rising_V': 1.23*(1+39.2/16.9),
                 'current_hysteresis_component_V': [4.4e-6*39200*(1-resistor_error), 5.6e-6*39200*(1+resistor_error)],
                 'falling_threshold_not_guaranteed': 'Internal hysteresis voltage has only a typical value; characterize brownout/restart.'},
        'output_current_limit_A': [.048/(.020*(1+shunt_error)), .052/(.020*(1-shunt_error))],
        'shunt_loss_W_at_2A': 2**2*.02,
        'switching_frequency_Hz_nominal': 1000/(.05*49300+35)*1e6,
        'inductance': {'inner_loop_minimum_H_at_360k': 1.2/360e3,
                       'selected_nominal_H': 6.8e-6, 'effective_sensitivity_min_H': 3.808e-6,
                       'initial_tolerance_max_H': 8.16e-6,
                       'note': '30% magnetic roll-off is a sensitivity, not a guaranteed hot curve.'},
        'estimated_input_A_at_4p5V': {str(eta): 5.04*2/(4.5*eta) for eta in [.85,.90]},
        'upper_feedback_corner_input_A_at_4p5V_85pct':
            (1.212*(1+31.6*(1+resistor_error)/(10*(1-resistor_error)))+
             .4e-6*31600*(1+resistor_error)+2*.020*(1+shunt_error))*2/(4.5*.85),
        'total_loss_W_scenarios': {str(eta): 5.04*2*(1/eta-1)+.08 for eta in [.85,.90]},
        'source_OV_comparison': {
            'cold_Voc_typical_V': 32.164, 'protected_operating_ceiling_V': 35,
            'TPS26630_adjustable': {
                'minimum_ratio_for_worst_case_cold_reconnect': 32.164/1.09,
                'maximum_ratio_for_worst_case_trip_below_35V': 35/1.224,
                'result': 'No feasible divider even before resistor errors, leakage, or overshoot'},
            'TPS26630_fixed': {'maximum_trip_V':35.4, 'result':'Exceeds 35 V operating ceiling'},
            'note':'No source protector selected; independent thresholds or a qualified clamp require a complete circuit.'},
        'thermal_all_loss_at_die_sensitivity': {
            'assumed_board_reference_C':85, 'operating_junction_ceiling_C':125,
            'max_effective_thermal_resistance_K_per_W_at_85pct_eff':40/(5.04*2*(1/.85-1)+.08),
            'note':'Conservative total stage loss attributed to die; not a junction prediction or a vacuum model.'},
        'output_bank_nominal_F': 3*100e-6+4*22e-6,
        'bulk_minimum_F_from_initial_tolerance_only': 3*100e-6*.8,
        'startup_capacitor_current_A_at_min_2p5ms': 388e-6*5/.0025,
        'startup_allocation': {
            'status': 'Proposed allocation, not measured COMMS/IHU consumption or capacitance',
            'converter_bank_upper_F': 500e-6, 'external_direct_cap_upper_F': 100e-6,
            'unavoidable_startup_load_upper_A': .5, 'voltage_sensitivity_V': 5.08,
            'capacitor_current_A_at_2p5ms': 600e-6*5.08/.0025,
            'total_output_current_A_at_2p5ms': .5+600e-6*5.08/.0025,
            'max_external_cap_F_from_slow_limit_only': ((.048/(.020*(1+shunt_error)))-.5)*.0025/5.08-500e-6,
            'note': 'Slow-limit arithmetic is necessary, not a dynamic startup guarantee at 4.5 V.'},
        'resistor_power_W_at_35V': {'R1': 35**2*39200/(39200+16900)**2,
                                   'R2': 35**2*16900/(39200+16900)**2},
        'load_step_droop_V_at_220uF_25us_10mOhm': 1.9*25e-6/220e-6+1.9*.01,
        'cold_lumped_step_sensitivity_V_at_160uF_25us': 1.9*25e-6/160e-6+1.9*.8/3,
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
    assert data['inductance']['initial_tolerance_max_H'] < 10e-6
    assert data['startup_allocation']['total_output_current_A_at_2p5ms'] < data['output_current_limit_A'][0]
    return data


if __name__ == '__main__':
    result = analyze()
    OUT.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k: result[k] for k in ['feedback_V','uvlo','output_current_limit_A','estimated_input_A_at_4p5V']}))
    print('Analytical checks passed; model phase-margin minimum:', result['loop_model']['minimum_estimated_phase_margin_deg'])
