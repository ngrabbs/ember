"""Four-channel rail measurement development arithmetic; no brownout proof."""
from pathlib import Path
from itertools import product
import json,math
H=Path(__file__).resolve().parent
rows=[]
e=.001+25e-6*65
for name,pin,top,bottom,ceiling,normal in [
 ('SYS_PWR_PERMITTED',7,[100000,100000],10000,60,35),
 ('+5V',8,[20000],10000,6,5),
 ('+3V3',11,[10000],10000,3.6,3.3),
 ('BATT_PERMITTED',12,[100000,100000],10000,60,8.5)]:
 def evaluate(values,ron):
  rt=sum(values[:-3]);rb,rs,rl=values[-3:];rs+=ron
  parallel=rb*(rs+rl)/(rb+rs+rl)
  g=parallel/(rt+parallel)*rl/(rs+rl)
  rth=(rt*rb/(rt+rb)+rs)*rl/(rt*rb/(rt+rb)+rs+rl)
  return g,rth
 parts=top+[bottom,1000,47000]
 nominal=evaluate(parts,2)
 corner=[evaluate([r*(1+s*e) for r,s in zip(parts,signs)],ron) for signs in product([-1,1],repeat=len(parts)) for ron in [0,4.5]]
 gains=[x[0] for x in corner];rmax=max(x[1] for x in corner)
 open_div_max=ceiling*bottom*(1+e)/(sum(top)*(1-e)+bottom*(1+e))
 enable_instant_max=open_div_max*(47000*(1+e))/(47000*(1+e)+1000*(1-e))
 assert open_div_max<3.6 and enable_instant_max<2.857
 filter_r=sum(top)*bottom/(sum(top)+bottom)
 # Filter is BEFORE the switch. No deliberate capacitor at the MCU pin.
 settle=math.log(8192)*filter_r*(10e-9*1.05*(1+30e-6*65))
 rows.append({'rail':name,'MCU_pin':pin,'top_resistors_ohm':top,'bottom_ohm':bottom,'series_after_switch_ohm':1000,'ADC_bleed_ohm':47000,'normal_V':normal,'design_input_ceiling_V':ceiling,'gain_nominal':nominal[0],'gain_min':min(gains),'gain_max':max(gains),'ADC_V_at_input_ceiling_max':ceiling*max(gains),'open_switch_divider_ceiling_V':open_div_max,'ideal_switch_enable_charged_filter_ADC_max_V':enable_instant_max,'source_impedance_max_ohm':rmax,'filter_half_LSB_full_step_settling_s_sensitivity':settle,'rail_V_per_LSB_at3p6V_ref':3.6/4096/nominal[0],'rail_error_from6p5LSB_at3p6V_ref_V':6.5*3.6/4096/nominal[0],'rail_error_from_0p2uA_total_on_leakage_V_sensitivity':.2e-6*rmax/nominal[0],'ratio_relative_error_max':max(abs(g/nominal[0]-1) for g in gains),'individual_series_top_resistor_voltage_conservative_bound_V':ceiling*(1+e)/(2*(1-e)) if len(top)>1 else ceiling})
assert max(r['source_impedance_max_ohm'] for r in rows)<15000
assert max(r['ADC_V_at_input_ceiling_max'] for r in rows)<2.857
assert max(r['filter_half_LSB_full_step_settling_s_sensitivity'] for r in rows)<.002
r={'scope':'CONDITIONAL_ADC_DEVELOPMENT_SCREEN;NO_NATIVE_OR_BROWNOUT_ACCEPTANCE','independent_resistor_error':e,'TMUX_Ron_sweep_ohm':[0,4.5],'switch_power_off_leakage_2uA_into47k_V':2e-6*47000*(1+e),'ADC_source_limit_ohm_at39p5_cycles35MHz':15000,'selected_sampling_cycles':160.5,'selected_ADC_clock_max_MHz':35,'enable_settling_wait_s':.002,'channels':rows,'not_included':['Reference/VREFINT/calibration error','Full dynamic ADC/switch model','Leakage outside manufacturer test conditions','Rapid or slow rail collapse and all-path injection','Unbounded input fault or divider resistor failure']}
(H/'results.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
