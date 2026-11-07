"""Managed VBAT feasibility and ideal-state checks, not device simulation.

Explicit conditions remain in results.json. No KiCad sources are changed.
"""
from itertools import product
from pathlib import Path
import json
import math

HERE = Path(__file__).resolve().parent
E = .001 + 25e-6 * 65  # independent initial/TCR bounds, -40..+85 from 25C


def divider(top, bottom, thresholds, leakage):
    values = [v * (1 + rt / rb) + i * rt
              for rt, rb, v, i in product(
                  [top * (1-E), top * (1+E)],
                  [bottom * (1-E), bottom * (1+E)], thresholds,
                  [-leakage, leakage])]
    return {'min_V': min(values), 'max_V': max(values)}


thresholds = {}
for name, top, bot, rise, fall, leak in [
        ('source_UV', 169000, 10000, [.396, .404], [.387, .400], 25e-9),
        ('source_OV', 226000, 10000, [.396, .404], [.387, .400], 15e-9),
        ('efuse_UV', 41200, 10000, [1.176, 1.224], [1.09, 1.15], 150e-9),
        ('efuse_OV_unclamped', 68100, 10000, [1.176, 1.224], [1.09, 1.15], 150e-9),
        ('efuse_PG', 36500, 10000, [1.176, 1.224], [1.09, 1.15], 150e-9)]:
    thresholds[name] = {'top_ohm': top, 'bottom_ohm': bot,
                        'rising': divider(top, bot, rise, leak),
                        'falling': divider(top, bot, fall, leak)}
thresholds['efuse_OV_with_imposed80nA_diode_leak'] = {
    'rising': divider(68100,10000,[1.176,1.224],230e-9),
    'falling': divider(68100,10000,[1.09,1.15],230e-9)}

# Exactly listed 4.02k test-point window scaled only by programming-resistor
# error. This is a programming sensitivity, not a guaranteed arbitrary-dropout
# current limit or a first-short peak bound.
imin, imax = 4.185/(1+E), 4.815/(1-E)
normal = []
vin_floor = thresholds['source_UV']['falling']['min_V']
for eta, margin, rtotal in product([.85, .90], [1, 1.2], [.08108, .13, .20]):
    pout = 18.075 * margin
    pin = pout/eta
    vo = (vin_floor + math.sqrt(vin_floor**2 - 4*rtotal*pin))/2
    current = pin/vo
    normal.append({'efficiency_assumed': eta, 'load_margin': margin,
                   'total_feed_resistance_ohm': rtotal,
                   'source_floor_V': vin_floor, 'carrier_input_V': vo,
                   'carrier_input_A': current,
                   'margin_to_6V_carrier_floor_V': vo-6,
                   'margin_to_programming_min_A': imin-current,
                   'efuse_R_loss_W': current**2*.053,
                   'external_FET_loss_W_hot_sensitivity': current**2*.0156*1.8,
                   'efuse_JEDEC_temperature_rise_K':
                   (current**2*.053+8.4*.0017)*31.4})

ce = .05 + 30e-6*65
smin = 1.775e-6*23.5/(100e-9*(1+ce))
smax = 2.225e-6*26/(100e-9*(1-ce))
inrush = []
for load_c in [1e-3, 5e-3]:
    # Include selected nominal local output bypass separately. Effective values
    # and actual carrier capacitance remain open; this is an imposed case.
    total_c = load_c + 2.3e-6*1.10*1.15
    cap_i = total_c*smax
    inrush.append({'imposed_carrier_capacitance_F': load_c,
                   'total_screened_capacitance_F': total_c,
                   'capacitive_current_max_sensitivity_A': cap_i,
                   'imposed_AON_startup_current_A': .2,
                   'margin_to_programming_min_A': imin-cap_i-.2,
                   'ramp_to8p4V_fast_s': 8.4/smax,
                   'ramp_to8p4V_slow_s': 8.4/smin,
                   'ideal_linear_charge_energy_J': .5*total_c*8.4**2,
                   'ideal_initial_pass_power_W': 8.4*(cap_i+.2)})

# OVP programming exposes an important pin-rating problem at a 35V imposed
# source event; even a 60V-rated eFuse does not give every sense pin a 60V rating.
ov_top_min = 68100*(1-E)
ov_bottom_max = 10000*(1+E)
ov_worst_at35 = 35*ov_bottom_max/(ov_top_min+ov_bottom_max)
ov_source_limit = 4*(1+ov_top_min/ov_bottom_max)

# LM4040CEM3-2.5/NOPB: full-temperature tolerance at100uA +/-38mV,
# conservative additional operating-current change1mV +8mV. Bias resistor
# connects BATT_PERMITTED directly to its cathode; no essential-rail backfeed.
# BAS116H diode A=OVP, K=reference. Its VF maximum is only specified at25C;
# cold1.2V is explicitly an imposed envelope, NOT a guaranteed cold rating.
ref_lo, ref_hi = 2.5-.038-.009, 2.5+.038+.009
clamp = {
    'reference_MPN': 'LM4040CEM3-2.5/NOPB',
    'diode_MPN': 'BAS116H,115', 'bias_resistor_ohm': 10000,
    'reference_conservative_window_V': [ref_lo,ref_hi],
    'reference_min_current_at5V_A': (5-ref_hi)/(10000*(1+E)),
    'reference_min_operating_current_A': 68e-6,
    'reference_max_current_at35V_including_full_OVP_top_current_A':
    (35-ref_lo)/(10000*(1-E))+35/(68100*(1-E)),
    'reference_max_operating_current_A': .015,
    'bias_resistor_max_power_at35V_W': (35-ref_lo)**2/(10000*(1-E)),
    'bias_resistor_min_rating_W': .25,
    'bias_resistor_selected_MPN': 'TNPW121010K0BEEA',
    'bias_resistor_selected_General_P70_W': .330,
    'bias_resistor_85C_derating_assumption': (125-85)/(125-70),
    'bias_resistor_derated60percent_limit_W': .330*(125-85)/(125-70)*.6,
    'reference_bias_source_power_at8p4V_nominal_W': 8.4*(8.4-2.5)/10000,
    'clamp_voltage_25C_1mA_VF_max_plus_full_ref_window_V': ref_hi+.9,
    'clamp_voltage_imposed_cold1p2V_VF_envelope_V': ref_hi+1.2,
    'cold_VF_guarantee_and_dynamic_acceptance': False,
}
assert clamp['reference_min_current_at5V_A'] > 68e-6
assert clamp['reference_max_current_at35V_including_full_OVP_top_current_A'] < .015
assert clamp['bias_resistor_max_power_at35V_W'] < clamp['bias_resistor_derated60percent_limit_W']
assert clamp['clamp_voltage_imposed_cold1p2V_VF_envelope_V'] < 4

# Ideal asynchronous level-memory model. PRE/CLR propagation, minimum pulse
# widths, recovery/removal, monitor/supervisor delay and analog brownout are
# deliberately not represented. Reset priority is an EN-masked abstraction,
# not a claim that both-low HC74 PRE/CLR is a valid stored state.
def step(state, req_pin, supply_ok, raw_ok, flt_n, pg):
    arm, fault = state
    req = bool(req_pin and supply_ok)
    healthy = bool(raw_ok and flt_n and pg)
    if not req:
        arm, fault = False, False
    else:
        # ARM is asynchronously set by inverted HEALTHY, not by a PGOOD edge.
        # A PGOOD that is already high at request admission cannot miss arming.
        if healthy:
            arm = True
        if arm and not healthy:
            fault = True
    en = bool(req and raw_ok and not fault)
    ready = bool(en and healthy)
    return (arm, fault), en, ready


traces = {}
scenarios = {
    'normal_start_stop': [(0,1,1,1,0),(1,1,1,1,0),(1,1,1,1,1),(0,1,1,1,1)],
    'raw_source_cycle_held_request': [(1,1,1,1,0),(1,1,1,1,1),(1,1,0,1,1),(1,1,1,1,1)],
    'efuse_fault_clears_without_request_release': [(1,1,1,1,0),(1,1,1,1,1),(1,1,1,0,1),(1,1,1,1,1)],
    'output_power_good_lost': [(1,1,1,1,0),(1,1,1,1,1),(1,1,1,1,0),(1,1,1,1,1)],
    'fresh_request_after_fault': [(1,1,1,1,0),(1,1,1,1,1),(1,1,0,1,0),(0,1,1,1,0),(1,1,1,1,0),(1,1,1,1,1)],
    'supply_reset': [(1,1,1,1,0),(1,1,1,1,1),(1,0,1,1,1),(0,1,1,1,0)],
    'startup_fault_never_healthy_is_unarmed': [(1,1,1,0,0),(1,1,1,0,1)],
    'pre_pg_source_cycle_not_latched': [(1,1,1,1,0),(1,1,0,1,0),(1,1,1,1,0)],
    'fresh_request_with_pg_already_high_arms': [(0,1,1,1,1),(1,1,1,1,1),(1,1,0,1,1)],
}
for name, sequence in scenarios.items():
    state = (False, False)
    trace = []
    for inputs in sequence:
        state, en, ready = step(state, *inputs)
        trace.append({'inputs_req_supply_raw_flt_pg': inputs,
                      'state_arm_fault': state,
                      'EN': en, 'READY': ready})
        assert not ready or (en and all(inputs))
        assert not en or (inputs[0] and inputs[1] and inputs[2] and not state[1])
    traces[name] = trace
for name in ['raw_source_cycle_held_request',
             'efuse_fault_clears_without_request_release',
             'output_power_good_lost',
             'fresh_request_with_pg_already_high_arms']:
    assert traces[name][-1]['state_arm_fault'][1]
    assert not traces[name][-1]['EN']
assert traces['fresh_request_after_fault'][-1]['READY']
assert traces['pre_pg_source_cycle_not_latched'][-1]['EN']  # explicit limitation
assert not traces['startup_fault_never_healthy_is_unarmed'][-1]['state_arm_fault'][0]
for arm, fault, req_pin, supply_ok, raw, flt, pg in product([0,1],repeat=7):
    state, en, ready = step((arm,fault),req_pin,supply_ok,raw,flt,pg)
    assert not ready or (en and raw and flt and pg)
    assert not en or (req_pin and supply_ok and raw and not state[1])
    if req_pin and supply_ok and fault:
        assert state[1] and not en

results = {
    'status': 'CONDITIONAL_DEVELOPMENT_CANDIDATE_NOT_INTEGRATED',
    'screening_temperature_C': [-40,85], 'resistor_fractional_error': E,
    'thresholds': thresholds,
    'current_limit_4020ohm_programming_sensitivity_A': [imin, imax],
    'normal_constant_power_sensitivities': normal,
    'slew_V_per_s': [smin,smax], 'startup_sensitivities': inrush,
    'SHDN_DC_off_V_20kohm_internal10uA_plus_imposed10uA_driver_leak': .4,
    'OVP_sense_at35V_worst_divider_V': ov_worst_at35,
    'unclamped_source_max_for_OVP4V_recommended_V': ov_source_limit,
    'OVP_35V_rating_pass': ov_worst_at35 <= 4,
    'proposed_sense_clamp': clamp,
    'helper_DRV_capacitance_screen': {
        'selected_MPN': 'T2N7002AK,LM',
        'Ciss_test_point_max_pF': 17, 'imposed_routing_pF': 10,
        'test_point_plus_routing_pF': 17+10,
        'imposed_2x_Ciss_plus_routing_pF': 2*17+10,
        'TPS_DRV_listed_load_pF': 50,
        'full_trajectory_and_temperature_acceptance': False},
    'proposed_OVP_filter_F': 1e-9,
    'clamp_transient_evidence': 'clamp_transient/analysis.json; nominal subcircuit only',
    'total_R_limit_from_current_at_worst_allocated_power_ohm':
    (vin_floor-(18.075*1.2/.85)/imin)/imin,
    'ideal_state_traces': traces, 'ideal_state_transition_rows': 128,
    'remaining_gates': [
        'Clamp now has 24 nominal subcircuit cases plus static arithmetic; cold diode/reference/PVT and coupled cutoff/survival remain open.',
        'T2N7002AK helper full-temperature drive/loading and assembly lands remain conditional.',
        'TPS3700 construction approval and exact package acceptance remain pending.',
        '100n C0G cold capacitance bound is open; 30ppm/65K is a sensitivity, not a manufacturer combined guarantee.',
        'The .13ohm feed budget and 1.8x hot external-FET resistance are imposed sensitivities, not verified harness/hot bounds.',
        'AON .2A startup bound and downstream capacitance require exact carrier evidence/measurement.',
        'No encrypted TPS2663 model was executed; slew/energy arithmetic is not thermal/SOA acceptance.',
        'Initial short current, source inductance, reverse interruption, pin clamps and healthy essential-rail survival remain open.',
        'Ideal state verification excludes timing races, invalid PRE/CLR overlap, minimum fault pulses and supply collapse.',
        'A startup that never becomes fully HEALTHY remains unarmed; require a firmware startup deadline and native eFuse latch behavior.',
        'No quick-discharge path is selected; RBF residual-energy and carrier/alternate-source decay require system closure.',
        'No hardware permission-expiry timer is implemented; firmware lease plus independent IWDG remains a separate requirement.',
        'All-source payload inhibition requires USB/bench path treatment; IHU retains PAYLOAD_EN ownership.',
    ]}
(HERE/'results.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps({k:results[k] for k in ['thresholds',
      'current_limit_4020ohm_programming_sensitivity_A','slew_V_per_s',
      'startup_sensitivities','OVP_sense_at35V_worst_divider_V',
      'unclamped_source_max_for_OVP4V_recommended_V','OVP_35V_rating_pass']},indent=2))
