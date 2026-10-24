"""Nominal independent CAN-A reset with imposed inverter logic, not a TI inverter model."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]/'protection'))
from run_protection import read_raw

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--adapted-model',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
args = parser.parse_args()
assert hashlib.sha256(args.adapted_model.read_bytes()).hexdigest() == '354d0e0c2e67a8d750fb0c1174b98e369139719d69d4d0df027b6d7ce9ef22f9'
args.output.mkdir(exist_ok=False)
result = {'status':'NOMINAL_TPS_WITH_IMPOSED_INVERTER_AND_GPIO_NOT_SYSTEM_QUALIFICATION',
          'adapted_model_sha256':hashlib.sha256(args.adapted_model.read_bytes()).hexdigest(),
          'inverter_model':'Behavioral inversion with 1V logic decision and source-.1V HIGH/.1V LOW; additional1k output resistance is a deliberate guard, not manufacturer dynamics.',
          'cases':[]}
for base in ['post_TCAN_90mA','post_TPSOUT_90mA']:
    previous = HERE.parent/'coupled_branch_screen'/(base+'.cir')
    portable = previous.read_text()
    old = 'Ven en 0 PWL(0 0 1m 0 1.001m 3.3 35m 3.3 35.001m 0 55m 0 55.001m 3.3 60m 3.3)'
    assert portable.count(old)==1
    controls = '''* Imposed GPIO/inverter behavior; actual1G14 dynamics/PVT not modeled
VstbA stbA 0 PWL(0 3.3 1m 3.3 1.001m 0 35m 0 35.001m 3.3 55m 3.3 55.001m 0 60m 0)
VstbB stbB 0 PWL(0 3.3 1m 3.3 1.001m 0 60m 0)'''
    for ch in ['A','B']:
        controls += f'''
Bdriver{ch} inv{ch} 0 V=if(V(shared)>1.65,if(V(stb{ch})<1,max(V(shared)-.1,0),.1),0)
Rdriver{ch} inv{ch} y{ch} 1k
Ren{ch} y{ch} en{ch} 1k
Rpd{ch} en{ch} 0 100k
Rbleed{ch} rail{ch} 0 10k'''
        portable = portable.replace(f'Xsw{ch} tpsin{ch} 0 en 0',f'Xsw{ch} tpsin{ch} 0 en{ch} 0')
    portable = portable.replace(old,controls).replace('V(en)','V(enA) V(enB) V(stbA) V(stbB)')
    name = base+'_independent_reset'
    (HERE/(name+'.cir')).write_text(portable)
    deck = args.output/(name+'.cir')
    deck.write_text(portable.replace('${TPS_ADAPTED_MODEL}',str(args.adapted_model.resolve())))
    try:
        proc = subprocess.run(['/Applications/LTspice.app/Contents/MacOS/LTspice','-b',str(deck)],capture_output=True,timeout=45)
        assert proc.returncode==0,proc.stderr.decode(errors='replace')
        log=deck.with_suffix('.log').read_text()
        assert 'Total elapsed time:' in log
        t,v=read_raw(deck.with_suffix('.raw'))
        assert np.isclose(t[-1],.060)
        reset=(t>=.036)&(t<=.054)
        recovery=(t>=.035)&(t<=.060)
        fault=(t>=.010)&(t<=.030)
        rec={'name':name,'status':'COMPLETED','final_time_s':float(t[-1]),
             'healthy_B_min_during_A_fault_V':float(v['v(railb)'][fault].min()),
             'healthy_B_min_during_A_reset_recovery_V':float(v['v(railb)'][recovery].min()),
             'healthy_B_EN_min_during_A_reset_recovery_V':float(v['v(enb)'][recovery].min()),
             'A_EN_max_while_reset_V':float(v['v(ena)'][reset].max()),
             'A_rail_59ms_V':float(np.interp(.059,t,v['v(raila)'])),
             'B_FAULT_min_during_A_reset_recovery_V':float(v['v(faultb)'][recovery].min()),
             'raw_sha256':hashlib.sha256(deck.with_suffix('.raw').read_bytes()).hexdigest(),
             'log_sha256':hashlib.sha256(deck.with_suffix('.log').read_bytes()).hexdigest(),
             'baseline_fixture_sha256':hashlib.sha256(previous.read_bytes()).hexdigest()}
        keys=['v(raila)','v(railb)','v(ena)','v(enb)','v(faulta)','v(faultb)']
        inds={0,len(t)-1};stride=max(1,len(t)//1000)
        for start in range(0,len(t),stride):
            end=min(start+stride,len(t))
            for key in keys:
                inds.update([start+int(np.argmin(v[key][start:end])),start+int(np.argmax(v[key][start:end]))])
        inds=sorted(inds)
        np.savetxt(HERE/(name+'.csv'),np.column_stack([t[inds]]+[v[k][inds] for k in keys]),delimiter=',',fmt='%.9g',comments='',header='time_s,A_V,B_V,A_EN_V,B_EN_V,A_fault_V,B_fault_V')
        (HERE/(name+'_log.txt')).write_text(log.replace(str(args.output),'${RUN_OUTPUT}').rstrip()+'\n')
    except subprocess.TimeoutExpired:
        rec={'name':name,'status':'TIMEOUT_TERMINATED_AFTER45s_NO_ACCEPTANCE'}
    result['cases'].append(rec)
    (HERE/'reset_results.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(rec),flush=True)
