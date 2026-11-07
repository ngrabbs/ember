"""Helper-only discharge benchmark with imposed 2/4nF main-gate loads.

These capacitors are sensitivity loads, not a nonlinear CSD18543 model or
guaranteed Qg bounds. The unmodified encrypted Toshiba models run in LTspice.
"""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT / 'hardware/eps/verification/protection'))
from run_protection import read_raw
LIB = Path.home() / 'Library/Application Support/LTspice/lib'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()

def run(part, temperature, resistor, cap, maxstep=2e-9, suffix=''):
    model = LIB / f'sub/Contrib/Toshiba/LVMOS/{part}_G0_00_enc.lib'
    name = f'{part}_T{temperature}_R{resistor:g}_C{cap*1e9:g}n{suffix}'
    path = HERE / 'gate_decks' / (name + '.cir')
    path.parent.mkdir(exist_ok=True)
    deck = f'''* Helper-only charge-discharge benchmark; no full eFuse or EPS model
.lib "{model}"
Vpre pre 0 14
Vinit init 0 PWL(0 1 9u 1 9.001u 0 30u 0)
Spre pre bg init 0 pre
.model pre SW(Ron=1 Roff=1e12 Vt=.5)
Ibias 0 bg 23u
Rbleed bg 0 800k
Cmain bg 0 {cap}
Vcmd drv 0 PWL(0 0 13u 0 13.01u 3 30u 3)
Rdrv drv hg 10
Croute hg 0 10p
Roff bg hd {resistor}
Xhelper hd hg 0 {part}_G0_00
.temp {temperature}
.options plotwinsize=0 method=gear
.tran 0 30u 0 {maxstep}
.save V(bg) V(hg) V(hd) I(Roff) I(Rdrv)
.end
'''
    if path.exists():
        assert path.read_text() == deck
    else:
        path.write_text(deck)
    saved = path.with_suffix('.json')
    if saved.exists():
        old = json.loads(saved.read_text())
        assert old['deck_sha256'] == sha(path) and old['model_sha256'] == sha(model)
        return old
    process = subprocess.run(['/Applications/LTspice.app/Contents/MacOS/LTspice','-b',str(path)],
                             capture_output=True,text=True,timeout=30)
    log = path.with_suffix('.log').read_text(errors='replace')
    assert process.returncode == 0 and 'Total elapsed time:' in log and 'Simulation Failed:' not in log
    warnings = [l for l in log.splitlines() if any(k in l.lower() for k in ['warning','error','ignoring'])]
    assert not warnings, warnings
    t, v = read_raw(path.with_suffix('.raw'))
    assert abs(t[-1] - 30e-6) < 1e-15
    assert all(np.isfinite(a).all() for a in v.values())
    w = t >= 9e-6
    drive = t >= 13e-6
    below = np.flatnonzero(drive & (v['v(bg)'] < 1))
    charge = float(np.trapezoid(np.maximum(v['i(rdrv)'][drive],0),t[drive]))
    result = {'case':name,'part':part,'temperature_C':temperature,'drain_R_ohm':resistor,
        'imposed_gate_cap_F':cap,'status':'COMPLETED_NOMINAL_HELPER_ONLY_BENCH',
        'endpoint_s':float(t[-1]),'points':len(t),'maxstep_s':maxstep,
        'helper_Id_peak_A':float(np.max(np.abs(v['i(roff)'][w]))),
        'helper_Vds_max_V':float(v['v(hd)'][w].max()),
        'helper_Vgs_min_V':float(v['v(hg)'][w].min()),'helper_Vgs_max_V':float(v['v(hg)'][w].max()),
        'main_gate_first_below_1V_after_DRV_s':float(t[below[0]] - 13e-6),
        'helper_positive_drain_energy_J':float(np.trapezoid(np.maximum(v['v(hd)'][w]*v['i(roff)'][w],0),t[w])),
        'drain_resistor_energy_J':float(np.trapezoid(v['i(roff)'][w]**2*resistor,t[w])),
        'driver_positive_charge_C':charge,'diagnostic_charge_over_3V_pF':charge/3*1e12,
        'warning_count':0,'deck_sha256':sha(path),'model_sha256':sha(model),
        'log_sha256':sha(path.with_suffix('.log')),'raw_sha256':sha(path.with_suffix('.raw')),
        'guaranteed_DRV_or_main_FET_SOA_acceptance':False}
    saved.write_text(json.dumps(result,indent=2)+'\n')
    window = (t >= 12.9e-6) & (t <= 18e-6)
    np.savetxt(path.with_suffix('.csv'),np.column_stack([t[window],v['v(bg)'][window],v['v(hg)'][window],v['i(roff)'][window],v['i(rdrv)'][window]]),
               delimiter=',',header='time_s,main_gate_proxy_V,helper_gate_V,helper_Id_A,driver_current_A',comments='')
    print(json.dumps({k:result[k] for k in ['case','helper_Id_peak_A','diagnostic_charge_over_3V_pF']}),flush=True)
    return result

if __name__ == '__main__':
    results=[]
    for part in ['T2N7002AK','SSM3K15AMFV']:
        for temperature in [-40,25,85]:
            for resistor in [.001,180]:
                for cap in [2e-9,4e-9]:
                    results.append(run(part,temperature,resistor,cap))
    results.append(run('T2N7002AK',25,.001,4e-9,1e-9,'_finer'))
    results.append(run('SSM3K15AMFV',25,.001,4e-9,1e-9,'_finer'))
    (HERE/'gate_results.json').write_text(json.dumps(results,indent=2)+'\n')
