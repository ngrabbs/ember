"""Compare unmodified installed LTC4365/4368 gate macros at the actual rail.
A forced VOUT is a bias test only: no load, power switch, startup or fault proof.
"""
from pathlib import Path
import argparse,hashlib,itertools,json,subprocess,sys
import numpy as np
H=Path(__file__).resolve().parent;ROOT=H.parents[4]
sys.path.insert(0,str(ROOT/'hardware/eps/verification/protection'))
from run_protection import read_raw
ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
a.output.mkdir(exist_ok=False)
lib=Path.home()/'Library/Application Support/LTspice/lib';exe='/Applications/LTspice.app/Contents/MacOS/LTspice'
results={};models={}
for part,volts,leak in itertools.product(['LTC4365','LTC4368-1'],[3.2328,3.3244],[0,1e-6]):
 name=f'{part}_{volts:g}_{leak:g}'.replace('.','p').replace('-','_')
 model=lib/'sub'/f'{part}.sub';symbol=lib/'sym/SpecialFunctions'/f'{part}.asy'
 models[part]={'model_sha256':hashlib.sha256(model.read_bytes()).hexdigest(),'symbol_sha256':hashlib.sha256(symbol.read_bytes()).hexdigest()}
 # ASY SpiceOrder read independently from the installed symbol, not encrypted internals.
 call='0 0 uv vin gate out fault shdn' if part=='LTC4365' else 'vin uv 0 0 0 shdn fault out out gate'
 deck=f'''* GATE BIAS ONLY; FORCED VIN=VOUT; NOT A SWITCH CIRCUIT
.lib "${{LTSPICE_LIBRARY}}/sub/{part}.sub"
Vin vin 0 PWL(0 0 1m 0 2m {volts} .08 {volts})
Vout out 0 PWL(0 0 1m 0 2m {volts} .08 {volts})
Vuv uv 0 2.5
Vshdn shdn 0 2.5
Rfault vin fault 1meg
Cgate gate 0 2.2n
Igate gate out {leak}
Xcontroller {call} {part}
.options plotwinsize=0
.tran 0 .08 0 5u
.save V(vin) V(out) V(gate) I(Vin) I(Vout)
.end
'''
 (a.output/f'{name}.portable.cir').write_text(deck)
 target=a.output/f'{name}.cir';target.write_text(deck.replace('${LTSPICE_LIBRARY}',str(lib)))
 record={'status':'not_run','part':part,'forced_supply_V':volts,'gate_load_A':leak}
 try:
  p=subprocess.run([exe,'-b',str(target)],capture_output=True,timeout=40)
  log=target.with_suffix('.log');raw=target.with_suffix('.raw')
  record['returncode']=p.returncode
  if p.returncode==0 and log.exists() and raw.exists() and 'Total elapsed time:' in log.read_text(errors='replace'):
   t,v=read_raw(raw);assert np.isclose(t[-1],.08);m=t>=.075
   d=v['v(gate)']-v['v(out)']
   record.update(status='completed',points=len(t),end_s=float(t[-1]),late_gate_over_out_min_V=float(d[m].min()),late_gate_over_out_max_V=float(d[m].max()),raw_sha256=hashlib.sha256(raw.read_bytes()).hexdigest(),log_sha256=hashlib.sha256(log.read_bytes()).hexdigest())
  else:record['status']='incomplete'
 except subprocess.TimeoutExpired:record['status']='timeout_terminated'
 results[name]=record
 (a.output/'results.json').write_text(json.dumps({'scope':'FORCED_BIAS_TYPICAL_MACRO_ONLY','model_hashes':models,'cases':results},indent=2)+'\n')
 print(name,record['status'],record.get('late_gate_over_out_min_V'),flush=True)
