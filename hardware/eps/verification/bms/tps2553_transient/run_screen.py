"""External TI switch model plus imposed converter loads; not UCC qualification."""
from pathlib import Path
import argparse, hashlib, json, re, subprocess, sys
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / 'protection'))
from run_protection import read_raw
EXPECTED = '2c4436b54cf8efc9dd522e110708fcb942e741a9620d6f442c577f787f451622'

def adapt(source):
    # LTspice interprets the PSpice XOR caret as exponentiation. Replace only
    # the XNOR truth expression, with the same four-input truth table.
    pattern = r'(\.SUBCKT XNOR2_BASIC_GEN[^\n]*\n)E_ABMGATE.*?\nRINT'
    changed, n = re.subn(pattern, r'\1E_ABMGATE YINT 0 VALUE={IF((V(A)>VTHRESH)!=(V(B)>VTHRESH),VSS,VDD)}\nRINT', source, flags=re.S|re.I)
    assert n == 1
    return changed

def export_csv(path, name):
    t, v = read_raw(path)
    cols = ['v(inp)','v(reservoir)','v(fault)','i(vmon)','v(xsw:u1_7_5ms)']
    # Preserve every selected channel's min/max in each decimation bucket.
    # This retains short pulses that uniform thinning could miss.
    stride = max(1,len(t)//1000)
    inds = {0,len(t)-1}
    for start in range(0,len(t),stride):
        end = min(start+stride,len(t))
        for key in cols:
            inds.add(start+int(np.argmin(v[key][start:end])))
            inds.add(start+int(np.argmax(v[key][start:end])))
    if name == 'short_latch_reset_3v3':
        inds.update(int(i) for i in np.flatnonzero((t>=.00999)&(t<=.01006)))
    inds = sorted(inds)
    np.savetxt(HERE/(name+'.csv'),np.column_stack([t[inds]]+[v[k][inds] for k in cols]),delimiter=',',fmt='%.9g',comments='',header='time_s,shared_input_V,reservoir_V,fault_V,source_A,timer_V')

def verify_xnor(model, output):
    path = output/'xnor_truth.cir'
    path.write_text(f'''* Four DC truth-table cases for the syntax-only adapter
.include "{model.resolve()}"
Vlo lo 0 0
Vhi hi 0 1
X00 lo lo y00 XNOR2_BASIC_GEN
X01 lo hi y01 XNOR2_BASIC_GEN
X10 hi lo y10 XNOR2_BASIC_GEN
X11 hi hi y11 XNOR2_BASIC_GEN
.tran 0 5u 0 10n
.save V(y00) V(y01) V(y10) V(y11)
.end
''')
    proc = subprocess.run(['/Applications/LTspice.app/Contents/MacOS/LTspice','-b',str(path)],timeout=45,capture_output=True)
    assert proc.returncode == 0
    assert 'Total elapsed time:' in path.with_suffix('.log').read_text()
    t, v = read_raw(path.with_suffix('.raw'))
    assert np.isclose(t[-1],5e-6)
    found = {k:float(v[k][-1]) for k in ['v(y00)','v(y01)','v(y10)','v(y11)']}
    assert all(abs(found[k]-expected)<1e-6 for k,expected in zip(found,[1,0,0,1]))
    (HERE/'xnor_verified.json').write_text(json.dumps({'four_truth_cases':found,'passed':True},indent=2)+'\n')

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--model', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    a = ap.parse_args()
    assert hashlib.sha256(a.model.read_bytes()).hexdigest() == EXPECTED
    a.output.mkdir(exist_ok=False)
    adapted = a.output / 'tps2553_ltspice.lib'
    adapted.write_text(adapt(a.model.read_text()))
    verify_xnor(adapted, a.output)
    rows = []
    cases = [
        ('startup_3v3_115k_upperC', 3.232799, 102.65, 115, 'dc', .050),
        ('startup_3v3_210k_upperC', 3.232799, 102.65, 210, 'dc', .050),
        ('startup_3v3_115k_100mA', 3.232799, 102.65, 115, 'dc', .100),
        ('startup_5v_115k_smallC', 4.8, 12.96, 115, 'dc', .050),
        ('bursts_3v3_115k_lowC', 3.232799, 54.38, 115, 'burst', .050),
        ('bursts_5v_115k_smallC', 4.8, 6.79, 115, 'burst', .050),
        ('short_latch_reset_3v3', 3.232799, 54.38, 115, 'fault', .050),
    ]
    result = {'status':'NOMINAL_TPS_MODEL_DIAGNOSTIC; IMPOSED_UCC_LOAD; NO_SYSTEM_QUALIFICATION',
              'model_url':'https://www.ti.com/lit/zip/SLVM426',
              'model_sha256':EXPECTED,
              'adapted_model_sha256':hashlib.sha256(adapted.read_bytes()).hexdigest(),
              'adaptation':'Only PSpice XNOR caret changed to explicit Boolean inequality; external source otherwise unchanged',
              'cases':rows}
    for name, vin, cu, rk, mode, load in cases:
        stop = .060 if mode == 'fault' else .020
        en = f'PWL(0 0 1m 0 1.001m 3.3 {stop} 3.3)'
        if mode == 'fault':
            en = 'PWL(0 0 1m 0 1.001m 3.3 35m 3.3 35.001m 0 55m 0 55.001m 3.3 60m 3.3)'
        pulse = ''
        load_expr = f'{load}*min(max(V(reservoir),0)/2.7,1)'
        if mode == 'burst':
            # Deliberately imposed pulse pattern, not extracted UCC behavior.
            pulse = 'Vburst command 0 PULSE(0 .785 8m 100n 100n 8.06u 183.017u)'
            load_expr = '(.015+V(command))*min(max(V(reservoir),0)/2.7,1)'
        fault = ''
        if mode == 'fault':
            fault = '''Vfault fault_command 0 PWL(0 0 10m 0 10.0001m 1 30m 1 30.0001m 0 60m 0)
Sfault reservoir 0 fault_command 0 SHORT
.model SHORT SW(Ron=.01 Roff=1e12 Vt=.5)'''
        portable = f'''* External TI TPS2553-1 model; synthetic source and UCC load
.include "${{TPS_ADAPTED_MODEL}}"
Vsrc source 0 PWL(0 0 100u {vin} {stop} {vin})
Rsource source inp .05
Cshared inp 0 96u Rser=10m
Vmon inp tpsin 0
Ven en 0 {en}
* MODEL ports IN GND EN PWPD FAULT_B ILIM OUT; not DBV physical order
Xsw tpsin 0 en 0 fault ilim switched TPS2553-1_TRANS
Rilim ilim 0 {rk}k
Rfault inp fault 10k
Rseries switched reservoir 1
Cbulk reservoir 0 {cu}u Rser=10m
Rbleed reservoir 0 3.9k
Bload reservoir 0 I={load_expr}
{pulse}
{fault}
.temp 25
.tran 0 {stop} 0 250n startup
.options plotwinsize=0
.save V(inp) V(switched) V(reservoir) V(fault) V(en) I(Vmon) V(xsw:u1_7_5ms)
.end
'''
        (HERE/(name+'.cir')).write_text(portable)
        path = a.output/(name+'.cir')
        path.write_text(portable.replace('${TPS_ADAPTED_MODEL}',str(adapted.resolve())))
        proc = subprocess.run(['/Applications/LTspice.app/Contents/MacOS/LTspice','-b',str(path)],timeout=45,capture_output=True)
        assert proc.returncode == 0, proc.stderr.decode(errors='replace')
        log = path.with_suffix('.log').read_text()
        assert 'Total elapsed time:' in log
        assert 'caret character' not in log
        t, v = read_raw(path.with_suffix('.raw'))
        assert np.isclose(t[-1],stop)
        settled = (t>=.008)&(t<=.0099) if mode=='fault' else t>=.012
        rec = {'name':name,'source_V':vin,'reservoir_uF':cu,'RILIM_kohm':rk,
               'load_mode':mode,'planning_average_load_A':load,'final_time_s':float(t[-1]),'points':len(t),
               'final_input_V':float(v['v(reservoir)'][-1]),
               'settled_input_min_max_V':[float(v['v(reservoir)'][settled].min()),float(v['v(reservoir)'][settled].max())],
               'source_current_peak_A':float(v['i(vmon)'].max()),
               'timer_max_V':float(v['v(xsw:u1_7_5ms)'].max()),
               'settled_fault_min_V':float(v['v(fault)'][settled].min()),
               'raw_sha256':hashlib.sha256(path.with_suffix('.raw').read_bytes()).hexdigest()}
        if mode == 'fault':
            latch = (t>=.023)&(t<=.029)
            rec.update(latched_fault_max_V=float(v['v(fault)'][latch].max()),
                       latched_current_max_A=float(v['i(vmon)'][latch].max()),
                       shared_input_min_during_initial_short_V=float(v['v(inp)'][(t>=.010)&(t<=.011)].min()))
        rows.append(rec)
        normalized = log.replace(str(a.output),'${RUN_OUTPUT}').replace('/private${RUN_OUTPUT}','${RUN_OUTPUT}')
        (HERE/(name+'.log')).write_text(normalized)
        export_csv(path.with_suffix('.raw'),name)
        (HERE/'results.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps(rec),flush=True)

if __name__ == '__main__':
    main()
