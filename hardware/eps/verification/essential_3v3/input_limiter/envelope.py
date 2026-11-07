"""Imposed eFuse-current envelopes and local-capacitor fault experiment.
This is NOT a TPS26630 vendor model or a guaranteed current/time bound.
Retires each circuit at ideal downstream opening; no post-opening SOA claim.
"""
from pathlib import Path
import argparse,itertools,json
import numpy as np
H=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--step-ns',type=float,default=1);ap.add_argument('--output',type=Path,default=H/'envelope_results.json');a=ap.parse_args()
cases=list(itertools.product([(640,.0225),(1280,.01125),(2304,.00875)],[2.2,5.6925],[.1,.5,3.136],[20,45,90],[1,4.5],[2,6,10],[0,2]))
n=len(cases);co=np.array([c[0][0] for c in cases])*1e-6;esr=np.array([c[0][1] for c in cases]);cin,lb,ip,tp,delay,load=np.array([c[1:] for c in cases]).T;cin*=1e-6;lb*=1e-6;tp*=1e-6;delay*=1e-6
raw0=3.324392156862745;trip=3.507897297148932;guard=1.232e-6;rpath=.03;cp=96e-6;dt=a.step_ns*1e-9
x=np.column_stack([np.full(n,35.),load,np.full(n,raw0),load,raw0-rpath*load]);tr=np.full(n,np.nan);done=np.zeros(n,bool);end=np.full((n,5),np.nan);op=np.full(n,np.nan)
peakv=raw0-rpath*load;peakb=load.copy();peakg=load.copy();mininput=np.full(n,35.)
def f(y,t):
 u,ib,raw,ig,vc=y.T;imax=np.where(t<tp,ip,4.83);feed=np.clip((35-u)/.053,0,imax);dclamp=np.maximum((-.3-u)/.01,0);vo=vc+esr*(ig-load)
 return np.column_stack([(feed+dclamp-ib)/cin,(u-raw-.01*ib)/lb,(ib-ig)/cp,(raw-vo-rpath*ig)/guard,(ig-load)/co])
for k in range(int(80e-6/dt)):
 t=k*dt;old=x.copy();k1=f(x,t);k2=f(x+k1*dt/2,t+dt/2);k3=f(x+k2*dt/2,t+dt/2);k4=f(x+k3*dt,t+dt);x+=dt*(k1+2*k2+2*k3+k4)/6
 hit=np.isnan(tr)&(x[:,2]>=trip);frac=np.clip((trip-old[:,2])/np.maximum(x[:,2]-old[:,2],1e-30),0,1);tr[hit]=t+frac[hit]*dt
 active=~done;peakv[active]=np.maximum(peakv[active],(x[:,4]+esr*(x[:,3]-load))[active]);peakb[active]=np.maximum(peakb[active],x[active,1]);peakg[active]=np.maximum(peakg[active],x[active,3]);mininput[active]=np.minimum(mininput[active],x[active,0])
 hit=active&np.isfinite(tr)&(t+dt>=tr+delay);q=np.clip((tr+delay-t)/dt,0,1);at=old+(x-old)*q[:,None];end[hit]=at[hit];op[hit]=tr[hit]+delay[hit];done[hit]=True;x[done]=old[done]
 if done.all():break
assert done.all() and np.isfinite(end).all()
rows=[]
for j,c in enumerate(cases):
 u,ib,raw,ig,vc=end[j];vopen=vc+esr[j]*(ig-load[j])
 rows.append({'id':j,'post_C_uF':c[0][0],'post_ESR_ohm':c[0][1],'local_input_C_uF':c[1],'buck_effective_L_uH':c[2],'imposed_initial_current_ceiling_A':c[3],'imposed_pulse_us':c[4],'imposed_total_opening_delay_us':c[5],'load_A':c[6],'trip_s':float(tr[j]),'opening_s':float(op[j]),'opening_state_u_ib_raw_ig_vc':list(map(float,end[j])),'protected_at_open_V':float(vopen),'protected_peak_to_open_V':float(peakv[j]),'buck_peak_to_open_A':float(peakb[j]),'guard_peak_to_open_A':float(peakg[j]),'limiter_output_min_V':float(mininput[j]),'guard_energy_at_open_J':float(.5*guard*ig*ig),'below3p6_at_ideal_open':bool(max(vopen,peakv[j])<=3.6)})
r={'scope':'IMPOSED_CURRENT_ENVELOPE_AND_LINEAR_MAGNETICS;NOT_TPS26630_TRANSIENT_ACCEPTANCE','step_ns':a.step_ns,'case_count':n,'initial_raw_V':raw0,'trip_V':trip,'imposed_steady_current_ceiling_A':4.83,'guard_effective_L_uH':1.232,'source_V':35,'source_R_ohm':.053,'input_negative_clamp_model':{'forward_V':.3,'dynamic_R_ohm':.01,'not_a_selected_or_qualified_diode':True},'rows':rows}
a.output.write_text(json.dumps(r,indent=2)+'\n');print('completed',n,'cases at',a.step_ns,'ns;',sum(c['below3p6_at_ideal_open'] for c in rows),'under3.6V to ideal opening; not a pass rate')
for coo in [640,1280,2304]:
 rs=[c for c in rows if c['post_C_uF']==coo];print(coo,'uF peak',max(c['protected_peak_to_open_V'] for c in rs),'buck current',max(c['buck_peak_to_open_A'] for c in rs),'limiter pin minimum',min(c['limiter_output_min_V'] for c in rs))
