"""Conditional static ISO1540 bus screen; no transient or power-off qualification."""
import json
from pathlib import Path
vmin, vmax = 3.23280, 3.32439
rmin = 3900 * (1 - .001 - 25e-6 * 65)
rmax = 3900 * (1 + .001 + 25e-6 * 65)
shunt_max = .002 * (1 + .01 + 50e-6 * 65)
offset = 6 * shunt_max
v2min, v2max = vmin-offset, vmax+offset
# Leakage totals include endpoint input bounds; BMS internal pulldown is separate.
# MCU 1 uA is an explicit provisional input budget, not an all-mode guarantee.
leak1, leak2 = 11e-6, 11e-6
high1 = vmin-rmax*leak1
# BMS RPD is at least 0.7 Mohm; solve static divider including leakage.
high2 = (v2min-rmax*leak2)/(1+rmax/700000)
result = {
 'assumptions': {'temperature_excursion_K':65,'sensitivity_current_A':6,
   'side1_capacitance_budget_pF':40,'side2_capacitance_budget_pF':200,
   'MCU_input_leakage_budget_uA_provisional':1},
 'pullup_ohm':[rmin,rmax], 'shunt_max_ohm':shunt_max,
 'reference_offset_V':offset,'side2_supply_V':[v2min,v2max],
 'low_margin_V': {'MCU_to_ISO1':.480-.4,'ISO1_to_MCU':.3*vmin-.8,
   'BMS_to_ISO2':.3*v2min-.4,'ISO2_to_BMS':.8-.4},
 'pullup_sink_A': {'ISO1_min_at_0p8V':(vmin-.8)/rmax,
   'ISO2_min_at_0p4V':(v2min-.4)/rmax,
   'BMS_max_at_0p4V':(v2max-.4)/rmin,
   'maximum_zero_volt_sink_per_line':v2max/rmin},
 'high_screen_V': {'side1':high1,'side2':high2,
   'MCU_margin_conservative_independent_corners':high1-.7*vmax,
   'ISO1_margin':high1-.7,'BMS_margin':high2-1.3,
   'ISO2_margin_conservative_independent_corners':high2-.5*v2max},
 'rise_30_to_70_ns': {str(c):.8473*rmax*c*1e-3 for c in [40,200]},
 'static_current_budget_A': {'all_lines_low_ICs':.0071+.0067,
   'all_lines_high_ICs':.004+.0035,
   'four_zero_volt_pullups_upper_bound':4*v2max/rmin},
 'raw_bus_unmeasured_current_upper_A':.0067+2*v2max/rmin,
 'measurement_gate':'Shared positive supply causes state-dependent shunt error; isolated power unresolved',
 'qualification':'CONDITIONAL_STATIC_SCREEN_ONLY'
}
assert all(x>0 for x in result['low_margin_V'].values())
assert result['pullup_sink_A']['ISO1_min_at_0p8V']>.0005
assert result['pullup_sink_A']['ISO2_min_at_0p4V']>.0005
assert result['pullup_sink_A']['BMS_max_at_0p4V']<.0015
assert all(x<1000 for x in result['rise_30_to_70_ns'].values())
Path(__file__).with_name('calculated.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
