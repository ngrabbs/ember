"""Input-limiter programming and headroom sensitivities, not full acceptance."""
from pathlib import Path
import itertools,json,math,xml.etree.ElementTree as E
H=Path(__file__).resolve().parent;ROOT=H.parents[4]
e=.001+25e-6*65
# Exact listed test-point current windows; resistor scaling follows programming law.
limits={}
for r,lo,hi in [(9000,1.84,2.16),(4020,4.185,4.815)]:
 limits[str(r)]={'formula_nominal_A':18000/r,'min_A_with_resistor_corner':lo/(1+e),'max_A_with_resistor_corner':hi/(1-e),'conditions':'Datasheet test-point VIN-VOUT=1V; not an initial hot-short peak bound or guarantee at arbitrary dropout.'}
def divider(top,bot,refs,leak):
 values=[v*(1+rt/rb)+i*rt for rt,rb,v,i in itertools.product([top*(1-e),top*(1+e)],[bot*(1-e),bot*(1+e)],refs,[-leak,leak])]
 return {'min_V':min(values),'max_V':max(values)}
dividers={}
for name,top,bot in [('UVLO',24900,10000),('OVP',365000,10000),('PGTH',19600,10000)]:
 dividers[name]={'top_ohm':top,'bottom_ohm':bot,'rising':divider(top,bot,[1.176,1.224],150e-9),'falling':divider(top,bot,[1.09,1.15],150e-9)}
eta_sens=[.80,.85,.90,.95];pout=2*3.324392156862745;headroom=[]
for vin,eta in itertools.product([4.5,5,8.5,35],eta_sens):
 ron=.053;i=(vin-math.sqrt(vin*vin-4*ron*pout/eta))/(2*ron);vo=vin-i*ron
 headroom.append({'vin_V':vin,'assumed_efficiency':eta,'buck_input_A':i,'buck_input_V':vo,'margin_to_buck4p3_V':vo-4.3,'efuse_R_loss_W':i*i*ron,'efuse_max_IQ_source_loss_W':vin*.0017,'current_margin_to_9k_testpoint_min_A':limits['9000']['min_A_with_resistor_corner']-i,'current_margin_to_4020_testpoint_min_A':limits['4020']['min_A_with_resistor_corner']-i})
ce=.05+30e-6*65;cd=22e-9;smin=1.775e-6*23.5/(cd*(1+ce));smax=2.225e-6*26/(cd*(1-ce))
assert dividers['UVLO']['rising']['max_V']<4.5 and dividers['OVP']['rising']['min_V']>35
pg_earliest_voltage=dividers['PGTH']['rising']['min_V']+smin*.00107
# Supply availability caps this ramp; below4.5V at limiter input is unqualified.
assert pg_earliest_voltage>4.3
R=E.parse(ROOT/'hardware/eps/verification/rev_b/swd_integration/eps_rev_b.xml').getroot();sysnet=next(n for n in R.findall('./nets/net') if n.get('name')=='SYS_PWR_PERMITTED');ends={(n.get('ref'),n.get('pin')) for n in sysnet.findall('node')}
required=[('C400','1'),('C401','1'),('C402','1'),('U400','3'),('U400','2')]
assert all(c in ends for c in required)
report={'status':'PROGRAMMING_AND_HEADROOM_FEASIBILITY;DYNAMIC_AND_NATIVE_SELECTION_OPEN','resistor_initial_and_65K_independent_error':e,'current_limit_testpoint_windows':limits,'independent_dividers':dividers,'normal_two_amp_sensitivities':headroom,'earliest_PGOOD_ramp_voltage_before_available_supply_cap_V':pg_earliest_voltage,'output_slew_V_per_s':[smin,smax],'PGOOD_pullup_ohm':100000,'PGOOD_low_with_35V_pullup_and130ohm_sink_V':35*130/(100000+130),'input_capacitor_bank':{'refs':['C400','C401','C402'],'nominal_uF':4.5,'initial_temp_high_sensitivity_uF':4.5*1.10*1.15,'energy_at35V_max_sensitivity_J':.5*4.5e-6*1.10*1.15*35**2,'not_a_combined_qualified_capacitance_bound':True},'proposed_migrations_only_not_executed':{'SYS_PWR_3V3_LIMITED':[['C400','1'],['C401','1'],['C402','1'],['U400','3']],'EPS_3V3_BUCK_EN':[['U400','2']]},'remaining_gates':['TPS2663 model is encrypted; no LTspice vendor-model execution.','Current-window test point does not bound first-short transient.','Post-limiter bank can bypass steady limit; preserve local LMR HF capacitance.','Downstream opening delay and negative limiter-output clamp need actual guaranteed paths.','Efficiency, startup/inrush, dropout, shared-source and thermal assumptions remain qualification items.','Stock PGOOD generic-output ERC type and larger stock lands are explicit review limitations.']}
(H/'static_results.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['current_limit_testpoint_windows','independent_dividers','earliest_PGOOD_ramp_voltage_before_available_supply_cap_V','output_slew_V_per_s','input_capacitor_bank']},indent=2))
