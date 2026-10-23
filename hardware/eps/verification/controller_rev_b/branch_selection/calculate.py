#!/usr/bin/env python3
"""CAN branch design calculations. No hardware/dynamic survival qualification."""
from pathlib import Path
import json
H=Path(__file__).resolve().parent
vmin=3.232799137558028;vmax=3.324392156862745
rtol=.001+25e-6*65
rmin=210*(1-rtol);rmax=210*(1+rtol)
imin=25230/rmax**1.016/1000;imax=22980/rmin**.94/1000
current=.060+.000300+2*vmax/10000
rseries_max=1*(1+.01+100e-6*65);rseries_min=1*(1-.01-100e-6*65)
ronmax=.135
shortpeak=vmax/rseries_min # conservative no specified minimum switch resistance
rows=[]
for valid in [current,.080,.090]:
 low=vmin-valid*(rseries_max+ronmax)
 deficit=shortpeak-valid
 for response in [2e-6,3e-6,5e-6,10e-6]:
  droop=deficit*(response/96e-6+.010)
  rows.append(dict(valid_branch_A=valid,short_response_s=response,short_current_upper_sensitivity_A=shortpeak,shared_cap_F=96e-6,shared_ESR_ohm=.010,branch_static_low_V=low,estimated_shared_droop_V=droop,B_branch_after_sensitivity_V=low-droop,meaning="no regulator help, no wiring L, switched short R>=0.9835ohm; response at3.3V is unguaranteed"))
assumptions={"TCAN_CCanormal_max_A":.060,"TCAN_VIOnormal_RXfloating_max_A":.0003,"TCAN_fault_CCAN_at_both_bus_25V_max_A":.130,"TXD_STB_pullup_each_ohm":10000,"added_dynamic_current_allocation_A":.020,"normal_RDS_on_hot_max_ohm":.135,"branch_series_ohm":1.0,"series_tolerance":.01,"series_TCR_per_K":100e-6,"RILIM_nom_kohm":210,"RILIM_initial_tol":.001,"RILIM_TCR_per_K":25e-6,"temperature_span_from25_K":65,"branch_C_nom_F":1.2e-6,"short_response_2us_is_typ_at5V_not_guaranteed_at3V3":True,"limit_latch_delay_s":[.005,.010]}
logic={"series_TXD_STB_RXD_ohm":1000,"ground_short_each_GPIO_current_max_A":vmax/1000,"resistor_ground_short_power_max_W":vmax*vmax/1000,"TCAN_TXD_internal_low_current_bound_A":.0002,"TXD_low_with_MCU_Vol0p4_V":(.4+1000*(vmax/10000+.0002))/(1+1000/10000),"TCAN_TXD_VIL_at_branch3V0_V":.3*3.0,"RXD_VOH_at_branch3V0_V":.8*3.0,"MCU_VIH_sensitivity_V":.7*vmax,"MCU_low_voltage_0p4_is_an_allocation_to_confirm":True,"TXD_STB_RXD_Ioff_abs_A":1e-6,"Ioff_conditions":"VCC=VIO=0, pin3.6V; TCAN supplyoff leakage does not establish arbitrary breakdown isolation","input_cap_allocation_F":50e-12,"1k_50pF_70percent_delay_s":-1000*50e-12*__import__("math").log(.3)}
result={"status":"TPS2553DBVR-1_DEVELOPMENT_CANDIDATE; NO_NATIVE_BRANCH_BUILD; QUALIFICATION_OPEN","exact_MPN":"TPS2553DBVR-1","assumptions":assumptions,"RILIM_equation_bounds_A":[imin,imax],"published210k_table_A":[.110,.150],"normal_steady_current_A":current,"normal_drop_max_V":current*(ronmax+rseries_max),"branch_static_normal_min_V":vmin-current*(ronmax+rseries_max),"current_limited_latch_portion_energy_J":vmax*imax*.010,"limit_headroom_for80mA_valid_A":imin-.080,"charge_1p2u_at110mA_minus61mA_s":1.2e-6*vmax/(imin-current),"fault_transient_sensitivities":rows,"logic_sensitivities":logic,"required_closures":["3.3V maximum short response and peak/inrush pulse (2us only typical at5V)","actual MCU/IHU/CAN load and controller/regulator response with96u qualified floor","dynamic normal traffic capacitive current and VCC minimum","series resistor pulse qualification/temperature","poweroff injection and arbitrary failed bus-to-logic paths","per-channel latch-reset GPIO/interface ownership and recovery timing","exact custom symbol construction approval,physical pin/pad review"]}
(H/"calculations.json").write_text(json.dumps(result,indent=2)+"\n")
print(json.dumps({k:result[k] for k in ["status","RILIM_equation_bounds_A","normal_steady_current_A","normal_drop_max_V","branch_static_normal_min_V","current_limited_latch_portion_energy_J"]},indent=2))
