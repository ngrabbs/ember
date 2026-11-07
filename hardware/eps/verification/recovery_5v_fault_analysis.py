#!/usr/bin/env python3
"""Reproducible protection feasibility arithmetic; not a circuit simulation or qualification."""
import itertools
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ERROR = .001 + 25e-6 * 65  # Independent initial error and TCR; screening only.


def divider_interval(top, bottom, references, leakage, hysteresis=None):
    values = []
    for ref, et, eb, current in itertools.product(references, [-ERROR, ERROR],
                                                  [-ERROR, ERROR], [-leakage, leakage]):
        rt, rb = top * (1 + et), bottom * (1 + eb)
        for h in (hysteresis if hysteresis else [0]):
            values.append(ref * (1 - h) * (1 + rt / rb) + current * rt)
    return [min(values), max(values)]


def analyze():
    # TPS3760-Q1 Rev B, tables 4-1, 6.5, 6.6. E012 is OV, OD low, NO LATCH.
    trip = divider_interval(412000, 10000, [.792, .808], 100e-9)
    reset = divider_interval(412000, 10000, [.792, .808], 100e-9,
                             [.02 * (1 - .015), .02 * (1 + .015)])
    # LT4363 Rev C, pp. 3-4. VFB table is at VCC=12 V, not a demonstrated
    # application-wide bound. These intervals must not be labelled guaranteed.
    source_clamp = divider_interval(25300, 1000, [1.25, 1.30], 1e-6)
    rail_clamp = divider_interval(3120, 1000, [1.25, 1.30], 1e-6)
    regulator_max = 5.074753
    # Ideal undamped LC sensitivity for converter switch pass-through. All C is
    # assumed connected while the barrier is on. No claim about a real waveform.
    vin, initial, inductance, capacitance = 35, regulator_max, 3.808e-6, 160e-6
    threshold = rail_clamp[1]
    omega = 1 / math.sqrt(inductance * capacitance)
    crossing = math.acos((vin - threshold) / (vin - initial)) / omega
    sensitivities = []
    for delay in [1e-6, 5e-6, 17e-6]:
        t = crossing + delay
        sensitivities.append({'delay_after_crossing_s': delay,
                              'ideal_uninterrupted_voltage_V': vin - (vin-initial)*math.cos(omega*t),
                              'ideal_uninterrupted_inductor_current_A':
                              (vin-initial)*math.sqrt(capacitance/inductance)*math.sin(omega*t)})
    data = {
        'date': '2026-10-23',
        'status': 'FEASIBILITY ONLY; no accepted source/fault envelope, native protection circuit or bench result',
        'resistor_initial_plus_screening_TCR_fraction': ERROR,
        'source_monitor': {'part': 'TPS3760E012DYYRQ1', 'divider_ohm': [412000, 10000],
                           'trip_interval_V': trip, 'reconnect_interval_V': reset,
                           'reconnect_margin_above_typical_cold_Voc_V': reset[0] - 32.164,
                           'remaining_static_margin_to_35V_V': 35-trip[1],
                           'sense_delay_max_at_20_percent_overdrive_s': 17e-6,
                           'delay_is_NOT_a_bound_at_small_overdrive': True,
                           'not_latching_variant': True},
        'lt4363_table_condition_sensitivities': {
            'not_guaranteed_over_application_supply_range': True,
            'source_divider_ohm': [25300, 1000], 'source_clamp_interval_V': source_clamp,
            'source_nominal_clamp_V': 1.275*(1+25300/1000),
            'rail_divider_ohm': [3120, 1000], 'rail_clamp_interval_V': rail_clamp,
            'rail_nominal_clamp_V': 1.275*(1+3120/1000),
            'rail_nuisance_clamp_margin_V': rail_clamp[0]-regulator_max,
            'rail_transient_margin_to_provisional_5p5V_V': 5.5-rail_clamp[1]},
        'ideal_pass_through_sensitivity': {'VIN_V': vin, 'initial_V': initial,
            'L_H': inductance, 'C_F': capacitance, 'threshold_V': threshold,
            'threshold_crossing_s': crossing, 'cases': sensitivities,
            'warning': 'Ideal lossless LC; no protection response, resistance, saturation or parasitics. Not a fault bound.'},
        'stored_energy_J': {'converter_input_68u_at_35V': .5*68e-6*35**2,
                            'converter_input_30u_nominal_ceramic_at_35V': .5*30e-6*35**2,
                            'output_500u_at_35V_if_uncontained': .5*500e-6*35**2},
        'linear_pass_FET_stress_allocations_NOT_ratings': [
            {'source_V': 35, 'clamp_V': 5.25, 'current_A': current, 'duration_s': duration,
             'power_W': (35-5.25)*current, 'energy_J': (35-5.25)*current*duration}
            for current, duration in itertools.product([2, 3], [.001, .005])],
        'exit_checks': {'static_source_window_above_typical_only': reset[0] > 32.164 and trip[1] < 35,
                        'rail_table_sensitivity_separates_regulator_and_5p5V':
                        regulator_max < rail_clamp[0] < rail_clamp[1] < 5.5,
                        'fault_containment_qualified': False}}
    assert data['exit_checks']['static_source_window_above_typical_only']
    assert data['exit_checks']['rail_table_sensitivity_separates_regulator_and_5p5V']
    return data


if __name__ == '__main__':
    result = analyze()
    output = ROOT/'evidence'/'2026-10-23_recovery_5v_fault_analysis.json'
    output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))
