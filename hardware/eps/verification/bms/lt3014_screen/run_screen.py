"""Nominal external LT3014 macromodel diagnostic, imposed source and loads only."""
from pathlib import Path
import hashlib,json,subprocess,sys,argparse
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/'protection'))
from run_protection import read_raw

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--model',type=Path,required=True)
 p.add_argument('--output',type=Path,required=True)
 p.add_argument('--case',type=int,choices=[0,1,2],help='Run only this prebias mode')
 a=p.parse_args()
 expected='9757f56b9c8372a738c1e1cad8c36ac95318260c4bac1b6d3be75b045693c337'
 assert hashlib.sha256(a.model.read_bytes()).hexdigest()==expected,'Unexpected external model revision'
 a.output.mkdir(exist_ok=False)
 result={'status':'NOMINAL_MACROMODEL_DIAGNOSTIC_ONLY','model_sha256':hashlib.sha256(a.model.read_bytes()).hexdigest(),'cases':{}}
 for cap,pre in [(1,False),(4.7,False),(10,False),(10,True),(10,2)]:
  if a.case is not None and int(pre)!=a.case: continue
  name=f'cout{cap:g}u_prebias{int(pre)}'
  source='PWL(0 0 1m 4.8 60m 4.8 60.001m 0 80m 0 81m 4.8 120m 4.8)'
  if pre: source='PWL(0 0 5m 0 6m 4.8 60m 4.8 60.001m 0 80m 0 81m 4.8 120m 4.8)'
  portable=f'''* Synthetic source and load; no UCC33020 or ISO1540 model
.include "${{LDO_MODEL}}"
Vsource source 0 {source}
Vsense source inp 0
Cin inp 0 22u Rser=20m
Vldo inp ldoin 0
* Model port order OUT ADJ NC GND SHDN NC NC IN; NOT package order
Xldo out adj 0 0 ldoin 0 0 ldoin LT3014
Rt out adj 16.9k
Rb adj 0 10k
Cout out 0 {cap}u Rser=20m
Vload_cmd command 0 PWL(0 .0035 20m .0035 20.001m .0085 40m .0085 40.001m .0035 120m .0035)
* Finite-voltage synthetic sink, deliberately not an ISO1540 startup model
Bload out 0 I=V(command)*min(max(V(out),0)/3,1)
{'.ic V(out)=3.4' if pre==1 else ''}
{'''Vpre bias 0 PWL(0 0 .2m 3.4 120m 3.4)
Vpre_ctl bias_ctl 0 PWL(0 5 4.9m 5 4.901m 0 120m 0)
Spre bias out bias_ctl 0 PRE
.model PRE SW(Ron=1 Roff=1e12 Vt=2.5)''' if pre==2 else ''}
.temp 25
.options plotwinsize=0
.tran 0 120m 0 2u {'uic' if pre==1 else 'startup'}
.save V(inp) V(out) V(adj) I(Vsense) I(Vldo)
.end
'''
  (HERE/(name+'.cir')).write_text(portable)
  f=a.output/(name+'.cir');f.write_text(portable.replace('${LDO_MODEL}',str(a.model.resolve())))
  try:
   proc=subprocess.run(['/Applications/LTspice.app/Contents/MacOS/LTspice','-b',str(f)],timeout=45,capture_output=True)
   assert proc.returncode==0,proc.stderr.decode(errors='replace')
   log=f.with_suffix('.log').read_text();assert 'Total elapsed time:' in log
   t,v=read_raw(f.with_suffix('.raw'));assert np.isclose(t[-1],.120),str(t[-1])
   active=(t>=.015)&(t<=.059)
   load=(t>=.020)&(t<=.040)
   collapse=(t>=.060)&(t<=.079)
   # Source monitor includes the input capacitor's imposed-source discharge.
   # It is NOT a separate reverse-current measurement of the LDO alone.
   rec={'status':'completed','points':len(t),'final_time_s':float(t[-1]),
        'active_output_min_max_V':[float(v['v(out)'][active].min()),float(v['v(out)'][active].max())],
        'load_step_output_min_V':float(v['v(out)'][load].min()),
        'collapse_output_max_V':float(v['v(out)'][collapse].max()),
        'post_collapse_LDO_input_min_A':float(v['i(vldo)'][(t>=.06001)&(t<=.079)].min()),
        'prebias_input_min_A_first_5ms':float(v['i(vldo)'][t<.005].min()),
        'prebias_input_min_A_after_10us_before_5ms':float(v['i(vldo)'][(t>=.00001)&(t<.005)].min()),
        'prebias_window_output_max_V':float(v['v(out)'][t<.005].max()),
        'final_output_V':float(v['v(out)'][-1]),
        'raw_sha256':hashlib.sha256(f.with_suffix('.raw').read_bytes()).hexdigest()}
   (HERE/(name+'.log')).write_text(log.replace(str(a.model.resolve()),'${LDO_MODEL}').replace('/private'+str(a.output),'${RUN_OUTPUT}').replace(str(a.output),'${RUN_OUTPUT}'))
   # Portable decimated CSV for independent plot review; full raw remains runtime output.
   inds=np.unique(np.r_[np.arange(0,len(t),max(1,len(t)//12000)),len(t)-1])
   np.savetxt(HERE/(name+'.csv'),np.column_stack([t[inds],v['v(inp)'][inds],v['v(out)'][inds],v['v(adj)'][inds]]),delimiter=',',fmt='%.9g',header='time_s,input_V,output_V,adj_V',comments='')
  except (subprocess.TimeoutExpired,AssertionError,ValueError,FileNotFoundError) as e:
   rec={'status':'failed_or_timed_out','detail':str(e)}
  result['cases'][name]=rec
  (HERE/'results.json').write_text(json.dumps(result,indent=2)+'\n')
  print(name,rec,flush=True)
if __name__=='__main__':main()
