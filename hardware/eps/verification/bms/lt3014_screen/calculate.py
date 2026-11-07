"""Conditional LT3014 + UCC33020 5V DC corner screen; no dynamic guarantee."""
from pathlib import Path
import json
HERE=Path(__file__).resolve().parent
exc=.001+25e-6*65
rt=(16900*(1-exc),16900*(1+exc)); rb=(10000*(1-exc),10000*(1+exc))
gain=(1+rt[0]/rb[1],1+rt[1]/rb[0])
# Full range VADJ includes input/load/temp; do not add line/load a second time.
# 10nA bias upper bound is specified at25C only: displayed as a sensitivity.
v=(1.18*gain[0],1.26*gain[1]+10e-9*rt[1])
rpu=3900*(1-exc)
div_min=1.18/rb[1];div_max=1.26/rb[0]+10e-9
iso=0.0067;pull=2*v[1]/rpu
out_current=iso+pull+div_max
allocated_out=.012
# Reserve the larger20mA endpoint GND maximum for a12mA allocation.
# Applying the endpoint to lower currents is a conservative engineering assumption.
gnd_test=.001000
input_allocation=allocated_out+gnd_test
res={
 'status':'conditional_DC_screen_NOT_dynamic_or_fault_acceptance',
 'UCC_setting_V':5.0,'SEL':'VCC','UCC_DC_V':[4.8,5.2],
 'selected_LDO':'LT3014IS5#TRPBF','divider_top_bottom_ohm':[16900,10000],
 'resistor_excursion_fraction':exc,'gain_range':gain,
 'output_envelope_V_including_25C_bias_sensitivity':v,
 'bias_10nA_output_effect_V':10e-9*rt[1],
 'minimum_output_margin_to_ISO1540_3V_V':v[0]-3,
 'maximum_output_margin_to_ISO1540_3p6_current_test_window_V':3.6-v[1],
 'divider_min_current_A':div_min,'divider_max_current_A':div_max,
 'minimum_load_margin_to_100uA_test_condition_A':div_min-.0001,
 'ISO2_max_all_low_IC_current_A':iso,'two_pullup_zero_volt_sink_max_A':pull,
 'output_static_current_screen_A':out_current,
 'provisional_output_current_allocation_A':allocated_out,
 'allocation_minus_static_A':allocated_out-out_current,
 'GND_max_test_point_20mA_A_used_as_budget':gnd_test,
 'provisional_isolated_input_current_A':input_allocation,
 'isolated_power_at_5p2V_W':5.2*input_allocation,
 'LDO_loss_at_screened_corners_W':(5.2-v[0])*allocated_out+5.2*gnd_test,
 'dropout20mA_fulltemperature_max_V':.570,
 'input_margin_after_output_upper_and_20mA_dropout_V':4.8-v[1]-.570,
 'BMS_to_ISO2_low_margin_V':.3*v[0]-.4,
 'unqualified':['10nA ADJ bias maximum is 25C only; full-temperature bound needed',
  '1mA GND budget uses20mA test-point maximum; lower-current monotonic envelope assumed',
  'complete UCC startup/prebias/input-current/temperature envelope',
  'nominal LDO model includes fixed27C transistor parameters; not PVT proof',
  'effective capacitors, coupling, thermal/EMC and powered/unpowered bus measurements']}
assert div_min>.0001
assert out_current<allocated_out
assert v[0]>3 and v[1]<3.6
assert res['input_margin_after_output_upper_and_20mA_dropout_V']>0
(HERE/'calculated.json').write_text(json.dumps(res,indent=2)+'\n')
print(json.dumps(res,indent=2))
