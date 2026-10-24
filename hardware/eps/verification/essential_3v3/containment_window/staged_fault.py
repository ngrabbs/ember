"""Two-filter fault model with explicit voltage-trip and total opening delay.
No encrypted models, source rewriting, selected new hardware or native edits.
"""
from pathlib import Path
import json,csv,itertools,argparse,hashlib
import numpy as np
H=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--step-ns',type=float,default=2);ap.add_argument('--output',type=Path,default=H/'staged_results.json');a=ap.parse_args()
static=json.loads((H/'results.json').read_text());V0=static['normal_upper_V']
cases=list(itertools.product([.5,3.136],[1,5,10,22],[48,96,192],[.5,2,4,6,10],[0,2]))
n=len(cases);Lb,Lg,Co,delay,load=np.array(cases).T;Lb*=1e-6;Lg*=1e-6;Co*=1e-6;delay*=1e-6
Cp=96e-6;R1=.05+.0159;R2=.03;VF=35.;trip=static['LTC4365_divider_screen'][0]['trip_max_V']
dt=a.step_ns*1e-9
x=np.column_stack([load,np.full(n,V0),load,V0-load*R2])
trip_t=np.full(n,np.nan);opened=np.zeros(n,dtype=bool);opening=np.full((n,6),np.nan)
peak_i1=load.copy();peak_i2=load.copy();peak_v1=np.full(n,V0)
def f(y):
 i1,v1,i2,v2=y.T
 return np.column_stack([(VF-v1-R1*i1)/Lb,(i1-i2)/Cp,(v1-v2-R2*i2)/Lg,(i2-load)/Co])
for step in range(int(np.ceil(60e-6/dt))):
 t=step*dt;old=x.copy()
 k1=f(x);k2=f(x+k1*dt/2);k3=f(x+k2*dt/2);k4=f(x+k3*dt)
 x=x+dt*(k1+2*k2+2*k3+k4)/6
 newly=np.isnan(trip_t)&(x[:,1]>=trip)
 frac=np.clip((trip-old[:,1])/np.maximum(x[:,1]-old[:,1],1e-30),0,1)
 trip_t[newly]=t+frac[newly]*dt
 active=~opened
 peak_i1[active]=np.maximum(peak_i1[active],x[active,0]);peak_i2[active]=np.maximum(peak_i2[active],x[active,2]);peak_v1[active]=np.maximum(peak_v1[active],x[active,1])
 now=active&np.isfinite(trip_t)&(t+dt>=trip_t+delay)
 frac2=np.clip((trip_t+delay-t)/dt,0,1)
 yopen=old+(x-old)*frac2[:,None]
 opening[now,:4]=yopen[now];opening[now,4]=trip_t[now];opening[now,5]=trip_t[now]+delay[now]
 opened[now]=True
 # Opened fixtures are retired, avoiding any claim about post-opening clamp energy.
 x[opened]=old[opened]
 if opened.all():break
assert opened.all()
rows=[]
for j,(lb,lg,co,de,ld) in enumerate(cases):
 i1,v1,i2,v2,tr,op=opening[j]
 rows.append({'buck_effective_L_uH':lb,'guard_effective_L_uH':lg,'post_effective_C_uF':co,'imposed_total_opening_delay_us':de,'constant_load_A':ld,'trip_s':float(tr),'opening_s':float(op),'protected_output_at_open_V':float(v2),'raw_output_at_open_V':float(v1),'buck_current_at_open_A':float(i1),'guard_current_at_open_A':float(i2),'guard_stored_energy_at_open_J':float(.5*lg*1e-6*i2*i2),'buck_peak_to_open_A':float(peak_i1[j]),'below_3p6_at_open_in_ideal_model':bool(v2<=3.6)})
report={'status':'IMPOSED_LINEAR_TWO_FILTER_MODEL_NOT_CIRCUIT_ACCEPTANCE','case_count':n,'step_ns':a.step_ns,'raw_trip_V':trip,'initial_normal_V':V0,'fault_source_V':VF,'pre_effective_C_uF':96,'rows':rows,'limits':['Buck high-side permanently shorted to an imposed stiff35V source; no source/PowerPath recovery or finite input reservoir model.','Buck effective L .5/3.136uH are sensitivities; neither is a guaranteed high-current saturation floor.','Current can greatly exceed normal device ratings; measured magnetic collapse and source limits are mandatory.','Post-bank is a proposed isolated effective bank; actual present bank is entirely upstream and25V-rated.','Comparator uses exact imposed raw threshold and total delay; no controller/gate model or PVT guarantee.','Ideal instantaneous switch opens after guard inductor; its turn-off clamp, parasitic feedthrough and SOA are excluded.','No acceptance of full startup/load/transient/thermal or flight behavior.']}
a.output.write_text(json.dumps(report,indent=2)+'\n')
if a.output==H/'staged_results.json':
 with (H/'staged_sweep.csv').open('w',newline='') as fp:
  w=csv.DictWriter(fp,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
print('Completed',n,'two-filter fixtures;',sum(r['below_3p6_at_open_in_ideal_model'] for r in rows),'below working ceiling at opening; step',a.step_ns,'ns')
