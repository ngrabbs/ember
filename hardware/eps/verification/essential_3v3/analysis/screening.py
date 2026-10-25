#!/usr/bin/env python3
"""Reproducible development screening, not an IC/loop/thermal qualification model."""
import itertools,json,math
from pathlib import Path
HERE=Path(__file__).resolve().parent
p={"vin":[4.5,5.0,7.27,12.0,24.0,35.0],"load_A":2.0,"rtop_ohm":31600.0,"rbot_ohm":10200.0,"r_initial":.001,"r_tcr_per_K":25e-6,"max_delta_K":65,"vref":[.792,.808],"l_nom_H":5.6e-6,"l_tol_min":.8,"l_bias_hot_sensitivity":.7,"f_min_Hz":360e3*.915,"f_nom_Hz":400e3,"f_max_Hz":440e3*1.085,"cout_nom_F":176e-6,"cout_required_min_F":96e-6,"cout_initial_temp_max_F":176e-6*1.1*1.15,"cout_startup_allocation_F":250e-6,"cout_bank_esr_required_ohm":.010,"cin_required_min_F":2.2e-6,"peak_limit_min_A":4.2,"peak_limit_max_A":6.0,"valley_limit_min_A":3.2,"inductor_Isat_typ_30percent_drop_A":9.9,"inductor_Irms_ref20C_A":7.5,"inductor_DCR_max25_ohm":.0159,"uvlo_rise_max_V":4.25,"uvlo_fall_typ_V":3.8,"vin_operating_min_V":4.3,"rhs_typ25_ohm":.085,"rls_typ25_ohm":.045}
rt=p["r_initial"]+p["r_tcr_per_K"]*p["max_delta_K"]
vouts=[vr*(1+p["rtop_ohm"]*(1+et*rt)/(p["rbot_ohm"]*(1+eb*rt))) for vr,et,eb in itertools.product(p["vref"],[-1,1],[-1,1])]
vmin,vmax=min(vouts),max(vouts);vnom=.8*(1+31600/10200)
lmin=p["l_nom_H"]*p["l_tol_min"]*p["l_bias_hot_sensitivity"]
rows=[]
for vin,vout,L,f in itertools.product(p["vin"],[vmin,vmax],[lmin,p["l_nom_H"]*1.2],[p["f_min_Hz"],p["f_max_Hz"]]):
 ripple=vout*(1-vout/vin)/(L*f);peak=2+ripple/2;valley=2-ripple/2
 rms=math.sqrt(4+ripple*ripple/12)
 cv=ripple/(8*f*p["cout_required_min_F"]);ev=ripple*p["cout_bank_esr_required_ohm"]
 # Doubled room-temperature typ Rds(on) is an explicit sensitivity, never a guaranteed hot maximum.
 rhs=.17;rls=.09;rdcr=.0159*(1+.00393*60)
 duty=(vout+2*(rls+rdcr))/(vin-2*(rhs-rls))
 pc=rms*rms*(duty*rhs+(1-duty)*rls)
 ps=.5*vin*2*30e-9*f
 pl=rms*rms*rdcr
 rows.append(dict(vin_V=vin,vout_V=vout,L_H=L,f_Hz=f,ripple_pp_A=ripple,peak_A=peak,valley_A=valley,rms_A=rms,capacitive_ripple_V=cv,esr_ripple_V=ev,duty_with_sensitivity_losses=duty,typ_toff_available_s=(1-duty)/f,IC_conduction_sensitivity_W=pc,IC_switching_30ns_sensitivity_W=ps,inductor_copper_sensitivity_W=pl,IC_total_partial_sensitivity_W=pc+ps))
assert max(r["peak_A"] for r in rows)<p["peak_limit_min_A"]
assert max(r["valley_A"] for r in rows)<p["valley_limit_min_A"]
assert max(r["rms_A"] for r in rows)<p["inductor_Irms_ref20C_A"]
transients=[]
for step,c in itertools.product([.15,.5,1.,1.8,2.],[96e-6,176e-6,p["cout_initial_temp_max_F"]]):
 capdroop=4*step/(p["f_min_Hz"]*c)
 droop=capdroop+step*p["cout_bank_esr_required_ohm"]
 transients.append(dict(step_A=step,cout_F=c,TI_eight_cycle_triangle_V=capdroop,plus_ESR_V=droop,static_low_minus_estimate_V=vmin-droop,static_high_plus_estimate_V=vmax+droop,meaning="rule-of-thumb estimate; not a guaranteed response or closed-loop model"))
sources=[]
for voc in [4.5,5.,6.,8.,12.,35.]:
 pin=vnom*2/.9
 sources.append(dict(Voc_V=voc,assumed_efficiency=.9,Pin_W=pin,Iin_at_Voc_A=pin/voc,Rsource_max_for_Vin4p3_ohm=max(0,(voc-4.3)*4.3/pin),constant_power_loadline_Rcritical_ohm=voc*voc/(4*pin),meaning="static power balance; no source/PV dynamics or startup guarantee"))
startup=[]
for ss in [.002,.004,.005]:
 ic=p["cout_startup_allocation_F"]*vmax/ss
 startup.append(dict(ramp_s=ss,allocation_F=p["cout_startup_allocation_F"],extra_capacitor_current_A=ic,load_plus_cap_current_A=2+ic,peak_plus_cap_sensitivity_A=max(r["peak_A"] for r in rows)+ic))
result={"status":"CONDITIONAL_STEADY_STATE_SCREENING_PASSES; DYNAMIC/PHYSICAL_QUALIFICATION_OPEN","inputs":p,"static":{"nominal_V":vnom,"initial_tolerance_only_low_V":.792*(1+31600*.999/(10200*1.001)),"initial_tolerance_only_high_V":.808*(1+31600*1.001/(10200*.999)),"temperature_inclusive_low_V":vmin,"temperature_inclusive_high_V":vmax},"sweep_corners":len(rows),"extrema":{"max_ripple_pp_A":max(r["ripple_pp_A"] for r in rows),"max_peak_A":max(r["peak_A"] for r in rows),"min_valley_A":min(r["valley_A"] for r in rows),"max_rms_A":max(r["rms_A"] for r in rows),"min_peak_limit_margin_A":4.2-max(r["peak_A"] for r in rows),"max_cap_plus_esr_ripple_estimate_V":max(r["capacitive_ripple_V"]+r["esr_ripple_V"] for r in rows),"min_offtime_available_s":min(r["typ_toff_available_s"] for r in rows),"max_partial_IC_loss_sensitivity_W":max(r["IC_total_partial_sensitivity_W"] for r in rows)},"steady_state_corners":rows,"transient_estimates":transients,"source_loadline":sources,"startup_allocation_sensitivity":startup,"qualification_conditions":["Each output capacitor must demonstrate>=12uF through3.6V,-40..85C and aging;8x22nominal does not prove96uF minimum","Input ceramics must demonstrate>=2.2uF aggregate through35V and ripple heating; no bulk added","Lmin3.136uH is a sensitivity from20%tol and30%drop, not guaranteed hot inductance","9.9A saturation reference is typical25C, not a hot fault rating","Full internal-compensated LC loop/PFM load response needs vendor model or bench; TI table does not authorize arbitrary Cout max","Rds(on)*2,switching30ns,90%efficiency and250uF startup allocation are assumptions","No full-temperature min/max soft-start,UVLO falling/hysteresis or thermal performance guarantee derived","No autonomous3V3 output-fault isolation: failed high-side can apply35V to25V bank and3V3 consumers","Downstream load/capacitance and source protection interactions not integrated"]}
(HERE/"screening.json").write_text(json.dumps(result,indent=2)+"\n")
print(json.dumps({k:result[k] for k in ["status","static","sweep_corners","extrema"]},indent=2))
