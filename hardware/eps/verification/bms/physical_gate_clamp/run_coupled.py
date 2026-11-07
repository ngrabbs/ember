"""Two nominal 25 C imposed-drive diagnostics, with physical model clamps.

Includes Q203 and the 2 mOhm shunt; not a BQ/pack model or SOA acceptance.
"""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys
import numpy as np
from run_clamp import adapt
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/'protection'))
from run_protection import read_raw

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['clamp','fet','reverse']:p.add_argument('--'+name+'-model',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path);a=p.parse_args()
    src=json.loads((HERE/'sources.json').read_text())
    assert sha(a.clamp_model)==src['model_source_sha256']
    assert sha(a.fet_model)==src['TI_FET_sha256']
    assert sha(a.reverse_model)==src['reverse_model_sha256']
    a.output.mkdir(exist_ok=False)
    clamp=a.output/'BZT52C15_ltspice.lib';clamp.write_text(adapt(a.clamp_model))
    assert sha(clamp)==src['adapted_model_sha256']
    result={'status':'NOMINAL_25C_IMPOSED_DRIVE_DIAGNOSTIC_ONLY','cases':{}}
    for enabled in [0,1]:
      name=f'coupled25_clamp{enabled}';f=a.output/(name+'.cir')
      s=(HERE/(name+'.cir')).read_text()
      for token,path in [('FET_MODEL',a.fet_model),('CLAMP_MODEL',clamp),('REVERSE_MODEL',a.reverse_model)]:
        s=s.replace('${'+token+'}',str(path.resolve()))
      f.write_text(s)
      run=subprocess.run(['/Applications/LTspice.app/Contents/MacOS/LTspice','-b',str(f)],timeout=45,capture_output=True)
      assert run.returncode==0
      log=f.with_suffix('.log');assert log.exists() and 'Simulation Failed' not in log.read_text()
      t,v=read_raw(f.with_suffix('.raw'));assert np.isclose(t[-1],.003)
      vg=v['v(gd)']-v['v(port)'];vc=v['v(gc)']-v['v(raw)'];ids=v['i(vids)']
      power=(v['v(dsgdrain)']-v['v(port)'])*ids;mask=t>=.001
      r={'points':len(t),'DSG_VGS_min_max_V':[float(vg.min()),float(vg.max())],
         'CHG_VGS_min_max_V':[float(vc.min()),float(vc.max())],
         'peak_discharge_A':float(ids.max()),'peak_DSG_power_W':float(power.max()),
         'DSG_post_fault_positive_energy_J':float(np.trapezoid(np.maximum(power[mask],0),t[mask])),
         'final_discharge_A':float(ids[-1]),'max_system_return_V':float(v['v(sys)'].max()),
         'peak_abs_DSG_drive_A':float(np.abs(v['i(rdg)']).max()),'raw_sha256':sha(f.with_suffix('.raw')),
         'executed_deck_sha256':sha(f)}
      if enabled:
        for n,gs in [('c',vc),('d',vg)]:
          i=v['i(vz'+n+')']
          r['clamp_'+n]={'peak_positive_A':float(i.max()),'peak_negative_A':float(i.min()),
             'pre_fault_mean_A':float(np.mean(i[(t>.0005)&(t<.0009)])),
             'positive_energy_J':float(np.trapezoid(np.maximum(gs*i,0),t))}
      (HERE/(name+'.log')).write_text('\n'.join(l.rstrip() for l in log.read_text().replace('/private'+str(a.output),'${RUN_OUTPUT}').replace(str(a.output),'${RUN_OUTPUT}').replace(str(a.fet_model.resolve()),'${FET_MODEL}').replace(str(a.reverse_model.resolve()),'${REVERSE_MODEL}').splitlines()).rstrip()+'\n')
      result['cases'][name]=r
      (HERE/'coupled_results.json').write_text(json.dumps(result,indent=2)+'\n')
      print(name,json.dumps(r),flush=True)
if __name__=='__main__':main()
