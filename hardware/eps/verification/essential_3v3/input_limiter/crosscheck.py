"""Independent LTspice solution of four imposed-envelope ODE cases.
No TPS26630 model is used. Circuits remain closed until the ODE opening time;
compare pre-opening states and independent threshold timing, not post-open behavior.
"""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys
import numpy as np
H=Path(__file__).resolve().parent;ROOT=H.parents[4]
sys.path.insert(0,str(ROOT/'hardware/eps/verification/protection'))
from run_protection import read_raw
ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();a.output.mkdir(exist_ok=False)
r=json.loads((H/'envelope_results.json').read_text());cs=r['rows'];selected=[max([c for c in cs if c['post_C_uF']==co],key=lambda c:c['protected_peak_to_open_V']) for co in [640,1280,2304]];selected.append(max([c for c in cs if c['post_C_uF']==640 and c['imposed_total_opening_delay_us']==2],key=lambda c:c['protected_peak_to_open_V']))
results=[];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for c in selected:
 key='case_'+str(c['id']);load=c['load_A'];vc=r['initial_raw_V']-.03*load
 deck=f'''* Independent solution of imposed envelope case {c['id']}; not a vendor model
Bfeed 0 vin I=limit((35-V(vin))/.053,0,if(time<{c['imposed_pulse_us']}u,{c['imposed_initial_current_ceiling_A']},4.83))
Bclamp 0 vin I=max((-.3-V(vin))/.01,0)
Cin vin 0 {c['local_input_C_uF']}u IC=35
Lb vin raw {c['buck_effective_L_uH']}u Rser=.01 IC={load}
Cpre raw 0 96u IC={r['initial_raw_V']}
Lguard raw out 1.232u Rser=.03 IC={load}
Rpost out capnode {c['post_ESR_ohm']}
Cpost capnode 0 {c['post_C_uF']}u IC={vc}
Iload out 0 {load}
.ic V(vin)=35 V(raw)={r['initial_raw_V']} V(out)={vc} V(capnode)={vc}
.options plotwinsize=0 reltol=1e-6 abstol=1e-10 vntol=1e-8
.tran 0 {c['opening_s']:.17g} 0 .05n uic
.save V(vin) I(Lb) V(raw) I(Lguard) V(capnode) V(out)
.end
'''
 p=a.output/(key+'.cir');p.write_text(deck);proc=subprocess.run(['/Applications/LTspice.app/Contents/MacOS/LTspice','-b',str(p)],capture_output=True,timeout=30);assert proc.returncode==0
 log=p.with_suffix('.log');raw=p.with_suffix('.raw');assert 'Total elapsed time:' in log.read_text(errors='replace')
 t,v=read_raw(raw);state=np.array([v[z][-1] for z in ['v(vin)','i(lb)','v(raw)','i(lguard)','v(capnode)']]);expected=np.array(c['opening_state_u_ib_raw_ig_vc']);delta=state-expected
 i=np.flatnonzero(v['v(raw)']>=r['trip_V'])[0];trip=t[i-1]+(r['trip_V']-v['v(raw)'][i-1])/(v['v(raw)'][i]-v['v(raw)'][i-1])*(t[i]-t[i-1]);peak=float(v['v(out)'].max())
 rec={'id':c['id'],'end_s':float(t[-1]),'expected_end_s':c['opening_s'],'spice_opening_state_u_ib_raw_ig_vc':list(map(float,state)),'state_difference':list(map(float,delta)),'trip_time_difference_s':float(trip-c['trip_s']),'protected_peak_difference_V':peak-c['protected_peak_to_open_V'],'deck_sha256':sha(p),'log_sha256':sha(log),'raw_sha256':sha(raw),'points':len(t)}
 assert abs(t[-1]-c['opening_s'])<1e-15
 assert max(abs(delta))<.003,rec
 assert abs(rec['trip_time_difference_s'])<1e-9,rec
 assert abs(rec['protected_peak_difference_V'])<.001,rec
 results.append(rec);(a.output/'results.json').write_text(json.dumps({'scope':'INDEPENDENT_SOLVER_CHECK_OF_IMPOSED_EQUATIONS;NOT_VENDOR_VALIDATION','cases':results},indent=2)+'\n');print(json.dumps(rec),flush=True)
