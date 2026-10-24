"""LM4040 nominal subcircuit + imposed diode-envelope sensitivity.

TI's explicitly unencrypted model is kept unmodified. This is not a model of
TPS2663, an exact BAS116H diode simulation, or a qualified source waveform.
"""
from pathlib import Path
import importlib.util
import json
import hashlib
import subprocess
import sys
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
spec = importlib.util.spec_from_file_location(
    'eps_raw', ROOT/'hardware/eps/verification/protection/run_protection.py')
raw_reader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(raw_reader)
LT = '/Applications/LTspice.app/Contents/MacOS/LTspice'


def deck(c):
    normal = 8.4 if c['source'] == 'warm_step' else 0
    return f'''LM4040 clamp only; nominal vendor reference, imposed diode envelope
Vraw raw 0 PWL(0 {normal} 1m {normal} 1.000001m 35 1.5m 35 1.500001m {normal} 2m {normal})
Rbias raw ref 10k
Xref ref 0 LM4040_NC2P5 TOL=0
Rtop raw ovp_in 68.1k
Cfeed raw ovp_in 0.5p
Ltop ovp_in ovp 2n Rser=1
Rbottom ovp 0 10k
Ipin ovp 0 150n
Covp ovp 0 {5e-12+c['cap_F']}
Ldiode ovp da 2n Rser=1
Bdiode da ref I=max(0,(V(da,ref)-{c['vf_V']})/1)
Cdiode da ref 2p
.include "../models/LM4040_NC2P5_TRANS.lib"
.temp {c['temperature_C']}
.options plotwinsize=0 method=gear
.tran 0 2m 0 5n
.save V(raw) V(ovp) V(ref) I(Rbias) I(Rtop) I(Bdiode) I(Cdiode)
.end
'''


def run(c):
    (HERE/'decks').mkdir(exist_ok=True)
    p = HERE/'decks'/(c['name']+'.cir')
    content = deck(c)
    if p.exists() and p.read_text() != content:
        raise RuntimeError('Preserve the prior deck; use a fresh case name: '+str(p))
    p.write_text(content)
    model_hash = hashlib.sha256((HERE/'models/LM4040_NC2P5_TRANS.lib').read_bytes()).hexdigest()
    deck_hash = hashlib.sha256(p.read_bytes()).hexdigest()
    prior = p.with_suffix('.json')
    if prior.exists():
        old = json.loads(prior.read_text())
        if old.get('model_sha256') == model_hash and old.get('deck_sha256') == deck_hash and old.get('status') == 'COMPLETED_IMPOSED_SUBCIRCUIT_CASE':
            return old
    try:
        result = subprocess.run([LT,'-b',str(p)], capture_output=True,
                                text=True, timeout=60)
    except subprocess.TimeoutExpired:
        return dict(c,status='TIMEOUT_NO_ACCEPTANCE')
    if result.returncode:
        return dict(c,status='SIMULATOR_ERROR',returncode=result.returncode,
                    stderr=result.stderr[-1000:])
    log = p.with_suffix('.log').read_text(errors='replace')
    if 'Total elapsed time:' not in log or 'Fatal Error' in log:
        return dict(c,status='INCOMPLETE_LOG_NO_ACCEPTANCE')
    t,v = raw_reader.read_raw(p.with_suffix('.raw'))
    assert abs(t[-1]-.002)<1e-12, 'Requested endpoint not reached'
    ovp,ref=v['v(ovp)'],v['v(ref)']
    voltage_at = lambda tt: float(ovp[np.argmin(abs(t-tt))])
    warnings = [line for line in log.splitlines() if 'Ignoring unknown model parameter' in line]
    result = dict(c,status='COMPLETED_IMPOSED_SUBCIRCUIT_CASE',
        deck_sha256=deck_hash,model_sha256=model_hash,
        log_sha256=hashlib.sha256(p.with_suffix('.log').read_bytes()).hexdigest(),
        raw_sha256=hashlib.sha256(p.with_suffix('.raw').read_bytes()).hexdigest(),
        endpoint_s=float(t[-1]),points=len(t),
        ovp_peak_V=float(ovp.max()),ovp_min_V=float(ovp.min()),
        ovp_before_fault_V=voltage_at(.00099),ovp_at_end_of_fault_V=voltage_at(.00149),
        reference_peak_V=float(ref.max()),reference_min_V=float(ref.min()),
        reference_bias_current_abs_peak_A=float(np.max(abs(v['i(rbias)']))),
        diode_conduction_current_peak_A=float(v['i(bdiode)'].max()),
        diode_total_current_abs_peak_A=float(np.max(abs(v['i(bdiode)']+v['i(cdiode)']))),
        OVP4V_operating_screen=bool(ovp.max()<=4 and ovp.min()>=0),
        OVP_absolute_screen=bool(ovp.max()<=5.5 and ovp.min()>=-.3),
        interpreted_model_warnings=warnings,
        physical_or_PVT_acceptance=False)
    prior.write_text(json.dumps(result,indent=2)+'\n')
    # Save all samples around fault edges and a sparse background for review.
    # Peaks above are computed from the complete adaptive trace, not this CSV.
    mask=((t>.0009999)&(t<.0010005))|((t>.0014999)&(t<.0015005))
    mask[::200]=True
    np.savetxt(p.with_suffix('.csv'),np.column_stack([t[mask],ovp[mask],ref[mask]]),
               delimiter=',',header='time_s,OVP_V,reference_V',comments='')
    return result


if __name__ == '__main__':
    if '--matrix' in sys.argv:
        cases=[]
        for source in ['warm_step','cold_start']:
            for temp in [-40,25,85]:
                for cap in [0,1e-9]:
                    for vf in [.9,1.2]:
                        cases.append(dict(name=f'cycle_{source}_t{temp}_c{int(cap*1e12)}p_vf{str(vf).replace(".","p")}',
                            source=source,temperature_C=temp,cap_F=cap,vf_V=vf))
    else:
        cases=[dict(name='cycle_cold_start_t-40_c0p_vf1p2',source='cold_start',
                    temperature_C=-40,cap_F=0,vf_V=1.2),
               dict(name='cycle_cold_start_t-40_c1000p_vf1p2',source='cold_start',
                    temperature_C=-40,cap_F=1e-9,vf_V=1.2)]
    results=[]
    for c in cases:
        r=run(c);results.append(r)
        print(json.dumps({k:r[k] for k in ['name','status','ovp_peak_V','ovp_min_V'] if k in r}),flush=True)
        (HERE/'results.json').write_text(json.dumps(results,indent=2)+'\n')
