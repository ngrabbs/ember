#!/usr/bin/env python3
"""Independent electrical/thermal extraction, NOT a hot-SOA guarantee.
Allocate the entire parallel-bank dissipation to one device for thermal sensitivity.
"""
import argparse,hashlib,json,sys
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from run_protection import read_raw

def thermal(t,p):
 dt=np.diff(t);pu=np.maximum(p[1:],p[:-1]) # interval endpoint maximum, not trapezoidal
 theta=np.zeros_like(pu,dtype=float)
 # Deliberately raised compared with the historical screening approximation.
 # Upper sensitivity at visually read Fig.11 anchor points, not a fitted or
 # guaranteed package model. Does not model local electrothermal hot spots.
 for resistance,tau in [(.03,1e-6),(.17,20e-6),(.45,.4e-3),(.65,4e-3)]:
  a=np.exp(-dt/tau);x=0.;z=np.empty_like(pu)
  for k,w in enumerate(pu):x=a[k]*x+resistance*(1-a[k])*float(w);z[k]=x
  theta+=z
 return float(theta.max())

def extract(c,path):
 t,v=read_raw(path.with_suffix('.raw'));pkg=c.get('package_parasitics',False)
 pd=v['v(dp)']-v['v(sp)'] if pkg else v['v(pin)']-v['v(common)']
 rd=v['v(dd)']-v['v(sd)'] if pkg else v['v(sense)']-v['v(common)']
 ps=v['v(sp)'] if pkg else v['v(common)'];rs=v['v(sd)'] if pkg else v['v(common)']
 pc=sum(v[k] for k in ['id(mpass)','id(mpass2)','id(mpass3)'] if k in v)
 rc=sum(v[k] for k in ['id(mdiode)','id(mdiode2)','id(mdiode3)'] if k in v)
 pp=np.maximum(pd*pc,0);rp=np.maximum(rd*rc,0);tf=.12 if c.get('stage')=='source' else .08;m=t>=tf;dt=np.diff(t)
 integ=lambda p:float(np.sum((p[1:]+p[:-1])*.5*dt*m[1:]*m[:-1]))
 out=dict(name=c['name'],conditions=c,pass_VDS_abs_V=float(abs(pd).max()),reverse_VDS_abs_V=float(abs(rd).max()),pass_VGS_min_V=float((v['v(gh)']-ps).min()),pass_VGS_max_V=float((v['v(gh)']-ps).max()),reverse_VGS_min_V=float((v['v(gd)']-rs).min()),reverse_VGS_max_V=float((v['v(gd)']-rs).max()),pass_bank_peak_A=float(abs(pc).max()),reverse_bank_peak_A=float(abs(rc).max()),pass_fault_energy_J=integ(pp),reverse_fault_energy_J=integ(rp),all_pass_power_one_device_temperature_rise_K=thermal(t,pp),all_reverse_power_one_device_temperature_rise_K=thermal(t,rp),raw_SHA256=hashlib.sha256(path.with_suffix('.raw').read_bytes()).hexdigest(),deck_SHA256=hashlib.sha256(path.read_bytes()).hexdigest())
 out['all_pass_power_one_device_Tj_C']={str(tc):tc+out['all_pass_power_one_device_temperature_rise_K'] for tc in [85,100,125]}
 out['all_reverse_power_one_device_Tj_C']={str(tc):tc+out['all_reverse_power_one_device_temperature_rise_K'] for tc in [85,100,125]}
 # Explicit screens, not cumulative-damage/SOA proofs. Total bank current is
 # compared with a SINGLE package limit: no equal-sharing assumption.
 out['electrical_screens']={'drains_below_80V':max(out['pass_VDS_abs_V'],out['reverse_VDS_abs_V'])<80,'gates_within_16V':max(abs(out[k]) for k in ['pass_VGS_min_V','pass_VGS_max_V','reverse_VGS_min_V','reverse_VGS_max_V'])<16,'bank_current_below_one_150A_pulse_rating':max(out['pass_bank_peak_A'],out['reverse_bank_peak_A'])<150}
 out['SOA_status']='OPEN: waveform-to-single-pulse graph comparison, hot linear-mode acceptance and local thermal instability require manufacturer/bench evidence; thermal sensitivity alone is insufficient'
 out['linear_power_exposure_s']={str(w):float(np.sum(dt*((np.maximum(pp[1:],pp[:-1])>w)&m[1:]))) for w in [24,120,600]}
 return out

def main():
 p=argparse.ArgumentParser();p.add_argument('--rail-work',type=Path,required=True);p.add_argument('--source-work',type=Path,required=True);a=p.parse_args();rows=[]
 for cases,work in [('cases.json',a.rail_work),('source_cases.json',a.source_work)]:
  for c in json.loads((HERE/cases).read_text()):
   f=work/(c['name']+'.cir')
   if f.with_suffix('.raw').exists() and f.with_suffix('.log').exists() and 'Total elapsed time:' in f.with_suffix('.log').read_text(errors='replace'):rows.append(extract(c,f))
 anchors={str(t):sum(r*(1-np.exp(-t/tau)) for r,tau in [(.03,1e-6),(.17,20e-6),(.45,.4e-3),(.65,4e-3)]) for t in [1e-6,10e-6,100e-6,1e-3,10e-3,.1,1]}
 selected=[r for r in rows if r['name'].startswith(('accepted_','guard_'))]
 screens={'selected_electrical':all(all(r['electrical_screens'].values()) for r in selected),'assumed_100C_case_below_150C_thermal_target':all(max(r['all_pass_power_one_device_Tj_C']['100'],r['all_reverse_power_one_device_Tj_C']['100'])<150 for r in selected)}
 (HERE/'evidence/survival.json').write_text(json.dumps({'scope':'Electrical extraction and elevated Foster thermal sensitivity. Neither equal sharing nor thermal qualification is assumed. No avalanche-energy credit.','generator_SHA256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'thermal_anchor_K_per_W':anchors,'selected_topology_screens':screens,'results':rows},indent=2)+'\n')
 assert all(screens.values()),screens
 for r in rows:print(r['name'],'Tj85',round(max(r['all_pass_power_one_device_Tj_C']['85'],r['all_reverse_power_one_device_Tj_C']['85']),2),'Ibank',round(max(r['pass_bank_peak_A'],r['reverse_bank_peak_A']),2),'screens',all(r['electrical_screens'].values()),flush=True)
if __name__=='__main__':main()
