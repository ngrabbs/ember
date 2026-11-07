"""Primary BZT52C15 model diagnostics, with a syntax-only LTspice adapter.

External source remains unchanged. This is not corner or pack qualification.
"""
from pathlib import Path
import argparse, hashlib, json, re, subprocess, sys
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/'protection'))
from run_protection import read_raw

def adapt(source):
    text=source.read_text()
    assert text.count('\n-\n')==1 and text.count(').ENDS')==1
    result=text.replace('\n-\n','\n* Standalone separator commented for LTspice\n').replace(').ENDS',')\n.ENDS')
    tokens=lambda s:re.findall(r'\S+', '\n'.join(l for l in s.splitlines() if not l.lstrip().startswith('*')).replace(').ENDS',') .ENDS').replace('\n-\n','\n'))
    assert tokens(text)==tokens(result), 'Adapter changed executable model tokens'
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--model',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    a=p.parse_args();src=json.loads((HERE/'sources.json').read_text())
    assert hashlib.sha256(a.model.read_bytes()).hexdigest()==src['model_source_sha256']
    a.output.mkdir(exist_ok=False)
    model=a.output/'BZT52C15_ltspice.lib';model.write_text(adapt(a.model))
    assert hashlib.sha256(model.read_bytes()).hexdigest()==src['adapted_model_sha256']
    result={'status':'NOMINAL_MODEL_DIAGNOSTICS_ONLY','cases':{}}
    for temp in [-40,25,85]:
      name=f'dc_t{temp}'
      text=f'''* Nominal BZT52C15 static diagnostic; no guaranteed temperature envelope
.include "${{CLAMP_MODEL}}"
Vtest test 0 0
Xz 0 test DI_BZT52C15
.temp {temp}
.dc Vtest 0 20 .002
.save V(test) I(Vtest)
.end
'''
      (HERE/(name+'.cir')).write_text(text)
      f=a.output/(name+'.cir');f.write_text(text.replace('${CLAMP_MODEL}',str(model.resolve())))
      run=subprocess.run(['/Applications/LTspice.app/Contents/MacOS/LTspice','-b',str(f)],timeout=45,capture_output=True)
      assert run.returncode==0
      log=f.with_suffix('.log');assert log.exists() and 'Simulation Failed' not in log.read_text()
      voltage,v=read_raw(f.with_suffix('.raw'));assert np.isclose(voltage[-1],20)
      current=-v['i(vtest)'];assert np.all(np.diff(current)>=-1e-12)
      sample=lambda x:float(np.interp(x,voltage,current))
      atcurrent=lambda x:float(np.interp(x,current,voltage))
      r={'points':len(voltage),'leakage_at_10V5_A':sample(10.5),'leakage_at_12V_A':sample(12),
         'voltage_at_1mA_V':atcurrent(.001),'voltage_at_5mA_V':atcurrent(.005),
         'executed_deck_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),
         'raw_sha256':hashlib.sha256(f.with_suffix('.raw').read_bytes()).hexdigest()}
      result['cases'][name]=r
      (HERE/(name+'.log')).write_text(log.read_text().replace('/private'+str(a.output),'${RUN_OUTPUT}').replace(str(a.output),'${RUN_OUTPUT}').strip()+'\n')
      print(name,r,flush=True)
      (HERE/'results.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
