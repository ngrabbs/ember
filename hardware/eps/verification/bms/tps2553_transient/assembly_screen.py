"""Update the existing isolated-supply static budget for selected bleeders."""
from pathlib import Path
import json

HERE = Path(__file__).resolve().parent
ldo = json.loads((HERE.parent/'lt3014_screen/calculated.json').read_text())
vmin, vmax = ldo['output_envelope_V_including_25C_bias_sensitivity']
exc = .001+25e-6*65
pull_lo,pull_hi = 3900*(1-exc),3900*(1+exc)
bleed_lo = 4700*(1-exc)
output_bleed = vmax/bleed_lo
static = ldo['output_static_current_screen_A']+output_bleed
mid_bleed = 5.2/bleed_lo
mid = .012+.001+mid_bleed
high2 = (vmin-pull_hi*11e-6)/(1+pull_hi/700000)
result = {
    'status':'CONDITIONAL_ASSEMBLY_STATIC_SCREEN; inherits LDO bias/temp and capacitor assumptions',
    'isolated_3V3_envelope_V':[vmin,vmax],
    'added_output_bleed_max_A':output_bleed,
    'output_static_with_bleed_A':static,
    'output_allocation_A':.012,
    'output_allocation_reserve_A':.012-static,
    'isolated_5V_bleed_max_A':mid_bleed,
    'intermediate_allocation_with_bleed_A':mid,
    'intermediate_max_power_W':5.2*mid,
    'primary_bleed_max_A':3.3244/pull_lo,
    'side2_pullup_min_at0p4V_A':(vmin-.4)/pull_hi,
    'BMS_max_sink_at0p4V_A':(vmax-.4)/pull_lo,
    'BMS_to_ISO2_low_margin_V':.3*vmin-.4,
    'ISO2_to_BMS_low_margin_V':.8-.4,
    'side2_high_min_with11uA_and700k_pulldown_V':high2,
    'BMS_high_margin_to1p3V_V':high2-1.3,
    'ISO2_high_margin_to0p5Vcc_independent_corners_V':high2-.5*vmax,
    'side2_200pF_30_70_rise_ns':.8473*pull_hi*200e-12*1e9,
    'scope':[
        'Same ISO1540/BQ limits as historical bus_screening/calculate.py; no new signal interface',
        'Side2 voltage now referenced to raw domain; do not reapply shared-positive shunt offset',
        'All-low IC6.7mA and LDO GND1mA allocations retain their original test-point qualifications',
        'Side1 is unchanged; dynamic loading, ramp, power-off and all-path leakage remain open',
    ],
}
assert result['output_allocation_reserve_A']>0
assert result['side2_pullup_min_at0p4V_A']>.0005
assert result['BMS_max_sink_at0p4V_A']<.0015
assert result['ISO2_high_margin_to0p5Vcc_independent_corners_V']>0
assert result['side2_200pF_30_70_rise_ns']<1000
(HERE/'assembly_screen.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
