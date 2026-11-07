#!/usr/bin/env python3
"""Compare CAN branch fault locations; imposed source/load, not CAN redundancy proof."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
VERIFICATION = HERE.parents[1]
sys.path.insert(0, str(VERIFICATION / 'protection'))
from run_protection import read_raw


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists(), 'Use a fresh external directory; never overwrite raw evidence.'
    args.output.mkdir()
    source = args.model.read_bytes()
    expected = '2c4436b54cf8efc9dd522e110708fcb942e741a9620d6f442c577f787f451622'
    assert hashlib.sha256(source).hexdigest() == expected
    spec = importlib.util.spec_from_file_location('bms_switch_adapter', VERIFICATION/'bms/tps2553_transient/run_screen.py')
    adapter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(adapter)
    model = args.output / 'tps2553_ltspice.lib'
    model.write_text(adapter.adapt(source.decode()))
    assert hashlib.sha256(model.read_bytes()).hexdigest() == '354d0e0c2e67a8d750fb0c1174b98e369139719d69d4d0df027b6d7ce9ef22f9'
    # The adapter has an existing separate four-case truth-table verification.
    cases = [('post_TCAN_61mA', 'post', 'railA', .060965),
             ('post_TPSOUT_61mA', 'post', 'swA', .060965),
             ('pre_TPSOUT_61mA', 'pre', 'swA', .060965),
             ('post_TCAN_90mA', 'post', 'railA', .090),
             ('post_TPSOUT_90mA', 'post', 'swA', .090),
             ('pre_TPSOUT_90mA', 'pre', 'swA', .090)]
    result = {'status': 'NOMINAL_SYNTHETIC_SOURCE_AND_LOAD_NOT_SYSTEM_ACCEPTANCE',
              'model_sha256': expected,
              'adapted_sha256': hashlib.sha256(model.read_bytes()).hexdigest(),
              'adapter': 'Existing independently truth-checked PSpice XNOR syntax correction only',
              'current_probe': 'I(VmonA/B) enters TPS IN, after each external input bypass; it is not a direct OUT/FET-drain probe.',
              'temperature_C': 25, 'cases': []}
    for name, position, fault_node, load in cases:
        branches = []
        for channel in ['A', 'B']:
            pre = f'Rlimit{channel} shared in{channel} 1' if position == 'pre' else f'Rfeed{channel} shared in{channel} 1m'
            post = f'Rout{channel} sw{channel} rail{channel} 1' if position == 'post' else f'Rout{channel} sw{channel} rail{channel} 1m'
            branches.append(f'''{pre}
Cin{channel} in{channel} 0 100n Rser=.05
Vmon{channel} in{channel} tpsin{channel} 0
Xsw{channel} tpsin{channel} 0 en 0 fault{channel} ilim{channel} sw{channel} TPS2553-1_TRANS
Rilim{channel} ilim{channel} 0 210k
Rfault{channel} shared fault{channel} 10k
{post}
Cload{channel} rail{channel} 0 1.2u Rser=.02
Bload{channel} rail{channel} 0 I={load}*min(max(V(rail{channel}),0)/2.7,1)''')
        portable = f'''* CAN branch resistor-position / fault-location comparison, development only
.include "${{TPS_ADAPTED_MODEL}}"
Vsrc source 0 PWL(0 0 100u 3.232799 60m 3.232799)
Rsource source shared .05
Cshared shared 0 96u Rser=10m
* 100mA imposed other essential load; no LMR51635 control-loop model
Bother shared 0 I=.1*min(max(V(shared),0)/2.7,1)
Ven en 0 PWL(0 0 1m 0 1.001m 3.3 35m 3.3 35.001m 0 55m 0 55.001m 3.3 60m 3.3)
{chr(10).join(branches)}
Vfault command 0 PWL(0 0 10m 0 10.0001m 1 30m 1 30.0001m 0 60m 0)
Sfault {fault_node} 0 command 0 SHORT
.model SHORT SW(Ron=.01 Roff=1e12 Vt=.5)
.temp 25
.options plotwinsize=0
.tran 0 60m 0 250n startup
.save V(shared) V(inA) V(inB) V(railA) V(railB) V(faultA) V(faultB) V(en) I(VmonA) I(VmonB) I(Rsource)
.end
'''
        (HERE/(name+'.cir')).write_text(portable)
        deck = args.output/(name+'.cir')
        deck.write_text(portable.replace('${TPS_ADAPTED_MODEL}', str(model.resolve())))
        try:
            proc = subprocess.run(['/Applications/LTspice.app/Contents/MacOS/LTspice', '-b', str(deck)],
                                  capture_output=True, timeout=45)
            assert proc.returncode == 0, proc.stderr.decode(errors='replace')
            log = deck.with_suffix('.log').read_text()
            assert 'Total elapsed time:' in log
            t, v = read_raw(deck.with_suffix('.raw'))
            assert np.isclose(t[-1], .060)
            window = (t >= .010) & (t <= .030)
            latched = (t >= .023) & (t <= .029)
            healthy = v['v(railb)']
            fault_assert = (t >= .010) & (v['v(faulta)'] < .8)
            rec = {'name': name, 'status': 'COMPLETED', 'resistor_position': position,
                   'fault_node': fault_node, 'imposed_each_normal_load_A': load,
                   'final_time_s': float(t[-1]), 'points': len(t),
                   'healthy_rail_min_during_fault_V': float(healthy[window].min()),
                   'shared_min_during_fault_V': float(v['v(shared)'][window].min()),
                   'faulted_switch_peak_A': float(v['i(vmona)'][window].max()),
                   'source_resistor_current_peak_during_fault_A': float(v['i(rsource)'][window].max()),
                   'fault_input_cap_min_during_fault_V': float(v['v(ina)'][window].min()),
                   'healthy_fault_min_during_fault_V': float(v['v(faultb)'][window].min()),
                   'fault_assert_after_short_s': float(t[fault_assert][0]-.010) if np.any(fault_assert) else None,
                   'latched_A_current_max_A': float(v['i(vmona)'][latched].max()),
                   'healthy_rail_59ms_V': float(np.interp(.059,t,healthy)),
                   'reset_A_rail_59ms_V': float(np.interp(.059,t,v['v(raila)'])),
                   'raw_sha256': hashlib.sha256(deck.with_suffix('.raw').read_bytes()).hexdigest(),
                   'log_sha256': hashlib.sha256(deck.with_suffix('.log').read_bytes()).hexdigest()}
            # Preserve local extrema in every channel, including short transients.
            keys = ['v(shared)','v(raila)','v(railb)','v(faulta)','v(faultb)','i(vmona)','i(vmonb)']
            indices = {0, len(t)-1}
            stride = max(1, len(t)//1200)
            for start in range(0,len(t),stride):
                end = min(start+stride,len(t))
                for key in keys:
                    indices.update([start+int(np.argmin(v[key][start:end])),start+int(np.argmax(v[key][start:end]))])
            indices = sorted(indices)
            np.savetxt(HERE/(name+'.csv'), np.column_stack([t[indices]]+[v[k][indices] for k in keys]),
                       delimiter=',',fmt='%.9g',header='time_s,shared_V,A_V,B_V,A_fault_V,B_fault_V,A_current_A,B_current_A',comments='')
        except subprocess.TimeoutExpired:
            rec = {'name':name,'status':'TIMEOUT_TERMINATED_AFTER45s_NO_ACCEPTANCE'}
        result['cases'].append(rec)
        (HERE/'results.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps(rec),flush=True)


if __name__ == '__main__':
    main()
