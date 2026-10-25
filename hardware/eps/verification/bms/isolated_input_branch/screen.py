"""Analytical RC/current-limiter sensitivity, not a TPS/UCC device model."""
from pathlib import Path
import json,math
HERE=Path(__file__).resolve().parent
VS=3.232799; R=1.0+.135; ESR=.010
HIGH=.8;LOW=.015;WIDTH=8.16e-6
PERIOD=WIDTH*(HIGH-LOW)/(.050-LOW)
def advance(v,load,dt,c,limit):
 # Vpin = Vcap+ESR*(Iin-Iload); source path R. No reverse operation.
 boundary=VS+ESR*load-limit*(R+ESR)
 eq=VS-R*load;tau=c*(R+ESR)
 candidates=[v]
 if v<boundary:
  slope=(limit-load)/c
  cross=(boundary-v)/slope if slope>0 else math.inf
  first=min(dt,cross);v+=slope*first;dt-=first;candidates.append(v)
  if dt>0:v=eq+(v-eq)*math.exp(-dt/tau);candidates.append(v)
 else:
  cross=(-tau*math.log((boundary-eq)/(v-eq))) if load>limit and v>boundary else math.inf
  first=min(dt,max(cross,0));v=eq+(v-eq)*math.exp(-first/tau);dt-=first;candidates.append(v)
  if dt>0:v+=(limit-load)/c*dt;candidates.append(v)
 def pin(vc):
  i=min(limit,(VS-vc+ESR*load)/(R+ESR))
  return vc+ESR*(i-load)
 return v,min(pin(x) for x in candidates),max(pin(x) for x in candidates)
def main():
 rows=[]
 for limit in [.110,.150,.200,.300]:
  for cu in [10,22,33,47,54,68,100]:
   c=cu*1e-6;v=VS-R*LOW;mins=[];maxs=[]
   for k in range(1000):
    v,a,b=advance(v,HIGH,WIDTH,c,limit);v,a2,b2=advance(v,LOW,PERIOD-WIDTH,c,limit)
    if k>=900:mins.extend([a,a2]);maxs.extend([b,b2])
   rows.append({'limit_A':limit,'effective_C_uF':cu,'periodic_input_min_V':min(mins),'periodic_input_max_V':max(maxs),'margin_to_3V_V':min(mins)-3,'within_UCC_recommended_range_for_this_scenario':min(mins)>=3})
 startup=[]
 for nominal in [44,66,88]:
  # Nominal upper sensitivity only, not effective minimum.
  cmax=nominal*1.1*1.15
  for limit in [.110,.200]:
   startup.append({'nominal_C_uF':nominal,'C_upper_tolerance_temperature_sensitivity_uF':cmax,'minimum_limit_A':limit,'assumed_simultaneous_average_load_A':.050,'ideal_charge_time_to_3p3244V_ms':cmax*1e-6*3.3244/(limit-.05)*1000,'note':'Charge-balance sensitivity, not actual switch/UCC startup or timer reset behavior'})
 r={'status':'IMPOSED_ANALYTICAL_SENSITIVITY_NOT_DEVICE_OR_SYSTEM_ACCEPTANCE','source_V':VS,'series_path_ohm':R,'capacitor_ESR_ohm':ESR,'burst_A':HIGH,'baseline_A':LOW,'burst_width_s':WIDTH,'burst_period_s':PERIOD,'average_load_A':.05,'assumptions':['Ideal immediate current clamp; no real TPS response, latch timer, reverse comparator or soft start','Stiff essential source; source sag, shared reservoir, trace inductance and regulator loop omitted','Imposed0.8A burst is not a guaranteed UCC maximum; no self-consistent UVLO/restart model','If input falls below3V, reject the scenario; do not interpret the trace as real undervoltage operation','1ohm+135mohm series path and10mohm ESR are imposed values; not a complete PVT envelope'],'periodic_cases':rows,'startup_charge_sensitivities':startup}
 (HERE/'calculated.json').write_text(json.dumps(r,indent=2)+'\n')
 print(json.dumps({'period_us':PERIOD*1e6,'minimum_47u_cases':[x for x in rows if x['effective_C_uF']==47],'startup':startup},indent=2))

if __name__=="__main__": main()
