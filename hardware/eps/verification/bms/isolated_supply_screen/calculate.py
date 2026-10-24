#!/usr/bin/env python3
"""Conditional static BMS supply screen; no transient or qualification model."""
import json
from pathlib import Path
r_excursion = .001 + 25e-6 * 65
rpu_min, rpu_max = 3900*(1-r_excursion), 3900*(1+r_excursion)
rbleed_min, rbleed_max = 3000*(1-r_excursion), 3000*(1+r_excursion)
vout_min, vout_max = 3.3*.99, 3.3*1.01
pre_min, pre_max = 5.5*.96, 5.5*1.04
bleed_min, bleed_max = vout_min/rbleed_max, vout_max/rbleed_min
pullups_max = 2*vout_max/rpu_min
static_max = .0067 + pullups_max + bleed_max
allocation = .012
result = {
    'status': 'conditional DC screening only; NOT integration acceptance',
    'proposed_UCC_setting_V': 5.5,
    'UCC_SEL_binding': 'secondary GNDS; not VCC',
    'UCC_full_range_accuracy_envelope_V': [pre_min,pre_max],
    'TLV_nominal_plus_1p5_input_test_condition_V': 4.8,
    'input_margin_to_that_condition_V': pre_min-4.8,
    'LDO_output_accuracy_envelope_V': [vout_min,vout_max],
    'ISO1540_operating_min_margin_V': vout_min-3.0,
    'bleeder_ohm_range': [rbleed_min,rbleed_max],
    'bleeder_current_A': [bleed_min,bleed_max],
    'bleeder_minimum_excess_over_1mA_A': bleed_min-.001,
    'bleeder_max_power_W': vout_max**2/rbleed_min,
    'side2_two_pullups_zero_volt_sink_max_A': pullups_max,
    'ISO_side2_all_low_IC_max_A': .0067,
    'static_output_load_screen_A': static_max,
    'provisional_output_allocation_A': allocation,
    'allocation_reserve_over_static_A': allocation-static_max,
    'isolated_stage_power_at_allocation_W': pre_max*allocation,
    'LDO_pass_element_loss_at_allocation_W': (pre_max-vout_min)*allocation,
    'BMS_to_ISO2_input_low_margin_V': .3*vout_min-.4,
    'ISO2_to_BMS_input_low_margin_V': .8-.4,
    'secondary_rise_30_to_70_s_at_200pF': .8473*rpu_max*200e-12,
    'unqualified': [
        'UCC 5.5V cold/hot load rating; 0.5W table specifies 5.0V only',
        '5.5V ripple over load and temperature; 75mVpp row specifies 5.0V at 25C',
        'TLV line/load conditions and complete dynamic output envelope',
        'loaded LDO ground current; 95uA is no-load only',
        '12mA allocation includes provisional dynamic/ground reserve, not a guaranteed maximum',
        'primary loaded current/inrush and essential-rail interaction',
        'effective capacitor values, ESR, startup, prebias and restart',
        'external reverse-current protection and short-circuit discharge',
        'fault propagation, RBF leakage, EMC and vacuum thermal behavior',
    ],
}
assert bleed_min > .001
assert static_max < allocation
Path(__file__).with_name('calculated.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
