"""Nominal vendor-model comparison with imposed eFuse timing/drive and source.

No encrypted contents are inspected or changed. No native KiCad writes.
This is not a TPS2663 model or a guaranteed reverse-interruption/SOA bound.
"""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import sys
import zipfile
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT / 'hardware/eps/verification/protection'))
from run_protection import read_raw

LIB = Path.home() / 'Library/Application Support/LTspice/lib'
TI = Path('/tmp/ember-ltc4231-input-first/CSD18543Q3A.LIB')
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert TI.read_bytes() == zipfile.ZipFile('/tmp/ember-csd18543.zip').read('CSD18543Q3A.LIB')

def deck(part, temperature, resistor, edge, maxstep):
    model = LIB / f'sub/Contrib/Toshiba/LVMOS/{part}_G0_00_enc.lib'
    return f'''* Nominal helper comparison, imposed TPS drive and reverse fault
.lib "{TI}"
.lib "{model}"
Vraw raw 0 PWL(0 8.4 10u 8.4 {10e-6+edge} 0 30u 0)
Rsource raw wire .05
Lsource wire src 100n Rser=.01
Csrc src 0 2.3u Rser=.02
Cinternal drain 0 100n Rser=.02
Rpass drain out .031
Cout out 0 1m Rser=.02
Rload out 0 1meg
Vmain drain md 0
Vmaing bg mg 0
Xmain md mg src CSD18543Q3A
Vpre pre src 14
Vinit init 0 PWL(0 1 9u 1 9.001u 0 30u 0)
Spre pre bg init 0 pre
.model pre SW(Ron=1 Roff=1e12 Vt=.5)
Ibias src bg 23u
Rbleed bg src 800k
Vcmd cmd 0 PWL(0 0 13u 0 13.01u 3 30u 3)
Bdrv drv 0 V=V(src)+V(cmd)
Rdrv drv hg 10
Croute hg src 10p
Roff bg hd {resistor}
Vhgate hg hgm 0
Xhelper hd hgm src {part}_G0_00
.temp {temperature}
.options plotwinsize=0 method=gear
.tran 0 30u 0 {maxstep}
.save V(raw) V(src) V(bg) V(hd) V(hg) V(drain) V(out) I(Roff) I(Rdrv) I(Lsource) I(Rpass) I(Vmain) I(Vmaing) I(Vhgate)
.end
'''

def run(part, temperature, resistor, edge, maxstep=2e-9, suffix='_op'):
    name = f'{part}_T{temperature}_R{resistor:g}_edge{edge*1e9:g}ns{suffix}'
    path = HERE / 'decks' / (name + '.cir')
    path.parent.mkdir(exist_ok=True)
    content = deck(part, temperature, resistor, edge, maxstep)
    if path.exists():
        assert path.read_text() == content, 'Preserve previous case; use a new suffix'
    else:
        path.write_text(content)
    result = {'case': name, 'part': part, 'temperature_C': temperature,
              'helper_drain_resistor_ohm': resistor, 'source_fall_s': edge,
              'maxstep_s': maxstep, 'deck_sha256': sha(path)}
    saved = path.with_suffix('.json')
    if saved.exists():
        old = json.loads(saved.read_text())
        if old.get('status') in ['COMPLETED_NOMINAL_IMPOSED_DRIVER_CASE', 'SIMULATOR_FAILURE_NO_ACCEPTANCE'] and old['deck_sha256'] == result['deck_sha256']:
            return old
    if path.with_suffix('.log').exists() and 'Simulation Failed:' in path.with_suffix('.log').read_text(errors='replace'):
        result.update(status='SIMULATOR_FAILURE_NO_ACCEPTANCE',
                      log_sha256=sha(path.with_suffix('.log')), raw_sha256=sha(path.with_suffix('.raw')),
                      reason='Preserved terminal failed log; no restart')
        saved.write_text(json.dumps(result, indent=2) + '\n')
        return result
    try:
        process = subprocess.run(['/Applications/LTspice.app/Contents/MacOS/LTspice', '-b', str(path)],
                                 capture_output=True, text=True, timeout=60)
    except subprocess.TimeoutExpired:
        result.update(status='TIMEOUT_NO_ACCEPTANCE', timeout_s=60)
        saved.write_text(json.dumps(result, indent=2) + '\n')
        return result
    log = path.with_suffix('.log').read_text(errors='replace')
    if process.returncode != 0 or 'Total elapsed time:' not in log or 'Fatal Error' in log or 'Simulation Failed:' in log:
        result.update(status='SIMULATOR_FAILURE_NO_ACCEPTANCE', returncode=process.returncode,
                      log_sha256=sha(path.with_suffix('.log')), raw_sha256=sha(path.with_suffix('.raw')),
                      reason='Terminal simulator failure; no result accepted')
        saved.write_text(json.dumps(result, indent=2) + '\n')
        return result
    t, v = read_raw(path.with_suffix('.raw'))
    assert abs(t[-1] - 30e-6) < 1e-15
    window = t >= 9e-6
    drive = t >= 13e-6
    helper_vds, helper_vgs = v['v(hd)'] - v['v(src)'], v['v(hg)'] - v['v(src)']
    main_vds, main_vgs = v['v(drain)'] - v['v(src)'], v['v(bg)'] - v['v(src)']
    hp = helper_vds * v['i(roff)'] + helper_vgs * v['i(vhgate)']
    mp = main_vds * v['i(vmain)'] + main_vgs * v['i(vmaing)']
    post = np.flatnonzero(drive & (main_vgs <= 1))
    integral = lambda x: float(np.trapezoid(np.maximum(x[window], 0), t[window]))
    result.update(status='COMPLETED_NOMINAL_IMPOSED_DRIVER_CASE', endpoint_s=float(t[-1]), points=len(t),
        helper_Id_abs_peak_A=float(np.max(np.abs(v['i(roff)'][window]))),
        helper_Vgs_min_V=float(helper_vgs[window].min()), helper_Vgs_max_V=float(helper_vgs[window].max()),
        helper_Vds_min_V=float(helper_vds[window].min()), helper_Vds_max_V=float(helper_vds[window].max()),
        main_Vgs_min_V=float(main_vgs[window].min()), main_Vgs_max_V=float(main_vgs[window].max()),
        main_Vds_abs_peak_V=float(np.max(np.abs(main_vds[window]))),
        main_Id_abs_peak_A=float(np.max(np.abs(v['i(vmain)'][window]))),
        source_current_abs_peak_A=float(np.max(np.abs(v['i(lsource)'][window]))),
        helper_positive_port_energy_J=integral(hp), main_positive_port_energy_J=integral(mp),
        helper_port_power_peak_W=float(hp[window].max()),
        helper_time_above_400mA_s=float(np.trapezoid((np.abs(v['i(roff)'][window]) > .4).astype(float),t[window])),
        main_gate_first_below_1V_after_imposed_DRV_s=None if not len(post) else float(t[post[0]] - 13e-6),
        diagnostic_gate_threshold_not_turnoff_guarantee=True,
        driver_positive_charge_C=float(np.trapezoid(np.maximum(v['i(rdrv)'][drive],0),t[drive])),
        log_sha256=sha(path.with_suffix('.log')), raw_sha256=sha(path.with_suffix('.raw')),
        warnings=[line for line in log.splitlines() if any(word in line.lower() for word in ('warning', 'ignoring', 'error'))],
        SOA_or_PVT_acceptance=False)
    saved.write_text(json.dumps(result, indent=2) + '\n')
    mask = (t >= 9.8e-6) & (t <= 16e-6)
    np.savetxt(path.with_suffix('.csv'), np.column_stack([t[mask], main_vgs[mask], helper_vgs[mask],
        helper_vds[mask], v['i(roff)'][mask], v['i(vmain)'][mask], v['v(src)'][mask], v['v(out)'][mask]]),
        delimiter=',', header='time_s,main_Vgs_V,helper_Vgs_V,helper_Vds_V,helper_Id_A,main_Id_A,source_V,out_V', comments='')
    return result

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--repeat', action='store_true')
    parser.add_argument('--execute', action='store_true', help='Explicitly run the exploratory coupled matrix; default only reports saved cases')
    args = parser.parse_args()
    if not args.execute:
        for path in sorted((HERE / 'decks').glob('*.json')):
            result = json.loads(path.read_text())
            print(result['case'], result['status'])
        sys.exit(0)
    models = {part: {'path': str(LIB / f'sub/Contrib/Toshiba/LVMOS/{part}_G0_00_enc.lib'),
                     'sha256': sha(LIB / f'sub/Contrib/Toshiba/LVMOS/{part}_G0_00_enc.lib')}
              for part in ['T2N7002AK', 'SSM3K15AMFV']}
    models['CSD18543Q3A'] = {'path': str(TI), 'sha256': sha(TI), 'original_TI_archive_matches': True}
    (HERE / 'models.json').write_text(json.dumps(models, indent=2) + '\n')
    cases = []
    for part in ['T2N7002AK', 'SSM3K15AMFV']:
        for temperature in [-40, 25, 85]:
            for resistor in [.001, 180]:
                for edge in [10e-9, 1e-6]:
                    result = run(part, temperature, resistor, edge)
                    cases.append(result)
                    print(json.dumps({k: result.get(k) for k in ['case','status','helper_Id_abs_peak_A','main_Vgs_max_V']}), flush=True)
    if args.repeat:
        cases.append(run('SSM3K15AMFV',25,180,1e-6,1e-9,'_finer'))
    (HERE / 'results.json').write_text(json.dumps(cases, indent=2) + '\n')
