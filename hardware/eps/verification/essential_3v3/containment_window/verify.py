"""Independent matrix-exponential check of the staged RK4 fault fixtures."""
from pathlib import Path
import hashlib,json,subprocess
import numpy as np
H=Path(__file__).resolve().parent;ROOT=H.parents[4]
s=json.loads((H/'results.json').read_text());r=json.loads((H/'staged_results.json').read_text())
repeat=json.loads((H/'staged_repeat.json').read_text())
assert len(s['rows'])==504 and r['case_count']==len(r['rows'])==240
assert all(a['below_3p6_at_open_in_ideal_model']==b['below_3p6_at_open_in_ideal_model'] for a,b in zip(r['rows'],repeat['rows']))
maxrepeat=max(abs(a['protected_output_at_open_V']-b['protected_output_at_open_V']) for a,b in zip(r['rows'],repeat['rows']))
assert maxrepeat<2e-6,maxrepeat
errors=[];terr=[]
for x in r['rows']:
 L1=x['buck_effective_L_uH']*1e-6;L2=x['guard_effective_L_uH']*1e-6;C1=96e-6;C2=x['post_effective_C_uF']*1e-6;R1=.0659;R2=.03;ld=x['constant_load_A']
 A=np.array([[-R1/L1,-1/L1,0,0],[1/C1,0,-1/C1,0],[0,1/L2,-R2/L2,-1/L2],[0,0,1/C2,0]],dtype=float)
 lam,P=np.linalg.eig(A);Pinv=np.linalg.inv(P)
 eq=np.array([ld,35-ld*R1,ld,35-ld*(R1+R2)])
 y0=np.array([ld,r['initial_normal_V'],ld,r['initial_normal_V']-ld*R2])
 z=Pinv@(y0-eq)
 def exact(t):
  y=eq+P@(np.exp(lam*t)*z);assert np.max(abs(y.imag))<1e-8
  return y.real
 lo=0.;hi=5e-6
 assert exact(hi)[1]>r['raw_trip_V']
 for _ in range(65):
  m=(lo+hi)/2
  if exact(m)[1]<r['raw_trip_V']:lo=m
  else:hi=m
 t=(lo+hi)/2;end=t+x['imposed_total_opening_delay_us']*1e-6
 y=exact(end);errors.append(float(np.max(abs(y-np.array([x['buck_current_at_open_A'],x['raw_output_at_open_V'],x['guard_current_at_open_A'],x['protected_output_at_open_V']])))))
 terr.append(abs(t-x['trip_s']))
assert max(errors)<5e-5,max(errors)
assert max(terr)<1e-11,max(terr)
# Explicit source-rating and static divider failure remain visible.
assert not s['LTC4365_divider_screen'][0]['OV_pin_within_5V_absolute_limit']
assert s['LTC4365_divider_screen'][1]['remaining_static_margin_to_3p6_V']<.011
# Snapshot current tracked native source bytes, not every file in a cache/history.
files=subprocess.check_output(['git','ls-files'],cwd=ROOT,text=True).splitlines()
native={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files if p.endswith(('.kicad_sch','.kicad_pcb','.kicad_pro','.kicad_sym','.kicad_mod')) or Path(p).name in ('sym-lib-table','fp-lib-table')}
for p,h in native.items():assert hashlib.sha256(subprocess.check_output(['git','show','HEAD:'+p],cwd=ROOT)).hexdigest()==h,p
out={'status':'INDEPENDENT_NUMERICAL_SCREEN_PASS_NOT_HARDWARE_ACCEPTANCE','closed_form_cases':504,'two_filter_cases':240,'matrix_exponential_cases':240,'RK4_half_step_max_protected_voltage_delta_V':maxrepeat,'matrix_vs_RK4_max_mixed_state_delta':max(errors),'matrix_vs_RK4_max_trip_time_delta_s':max(terr),'native_files_unchanged':len(native),'native_source_sha256':native,'ceilings_passed_in_imposed_two_filter_cases':sum(x['below_3p6_at_open_in_ideal_model'] for x in r['rows']),'limits':'An ideal model passing cannot qualify delay, gate drive, saturation, turn-off clamp or SOA. An imposed stiff-source failure is a counterexample for that imposed boundary, not every possible real converter fault.'}
(H/'verified.json').write_text(json.dumps(out,indent=2)+'\n')
print({k:v for k,v in out.items() if k!='native_source_sha256'})
