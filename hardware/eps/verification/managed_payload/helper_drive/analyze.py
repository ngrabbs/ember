"""Archive and inspect the bounded helper study; no native-file writes."""
from pathlib import Path
import csv
import gzip
import hashlib
import json
import re
import subprocess
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
data = json.loads((HERE / 'gate_results.json').read_text())
base = [d for d in data if not d['case'].endswith('_finer')]
assert len(base) == 24 and len(data) == 26
assert {(d['part'], d['temperature_C'], d['drain_R_ohm'], d['imposed_gate_cap_F']) for d in base} == {
    (p, t, r, c) for p in ['T2N7002AK', 'SSM3K15AMFV'] for t in [-40,25,85]
    for r in [.001,180] for c in [2e-9,4e-9]}
for d in data:
    path = HERE / 'gate_decks' / (d['case'] + '.cir')
    assert d['status'] == 'COMPLETED_NOMINAL_HELPER_ONLY_BENCH' and d['warning_count'] == 0
    assert abs(d['endpoint_s'] - 30e-6) < 1e-15
    assert d['deck_sha256'] == sha(path) and d['log_sha256'] == sha(path.with_suffix('.log'))
    assert d['raw_sha256'] == sha(path.with_suffix('.raw'))
    assert d['model_sha256'] == sha(Path.home() / f"Library/Application Support/LTspice/lib/sub/Contrib/Toshiba/LVMOS/{d['part']}_G0_00_enc.lib")

summary = {'scope':'NOMINAL_HELPER_ONLY_BENCH; NO_TPS_DRIVER_OR_MAIN_FET_SURVIVAL_ACCEPTANCE',
           'completed_no_warning_cases':26, 'initial_charge_V':14, 'imposed_DRV_V':3,
           'imposed_DRV_R_ohm':10, 'imposed_routing_cap_pF':10, 'rows':[], 'finer_step_comparison':[]}
for part in ['T2N7002AK','SSM3K15AMFV']:
    for resistor in [.001,180]:
        rows = [d for d in base if d['part'] == part and d['drain_R_ohm'] == resistor]
        summary['rows'].append({'part':part,'drain_R_ohm':resistor,
            **{key:[min(d[key] for d in rows),max(d[key] for d in rows)] for key in [
                'helper_Id_peak_A','main_gate_first_below_1V_after_DRV_s','diagnostic_charge_over_3V_pF',
                'helper_positive_drain_energy_J','drain_resistor_energy_J']}})
    original = next(d for d in base if d['part'] == part and d['temperature_C'] == 25 and d['drain_R_ohm'] == .001 and d['imposed_gate_cap_F'] == 4e-9)
    finer = next(d for d in data if d['part'] == part and d['case'].endswith('_finer'))
    summary['finer_step_comparison'].append({'part':part,
        **{k:abs(finer[k]-original[k])/abs(original[k]) for k in ['helper_Id_peak_A','driver_positive_charge_C','main_gate_first_below_1V_after_DRV_s']}})

coupled=[]
for path in sorted(list((HERE/'decks').glob('*.cir'))+[HERE/'pilot.cir']):
    log=path.with_suffix('.log').read_text(errors='replace')
    if 'Simulation Failed:' in log:status='FAILED_NO_ACCEPTANCE'
    elif 'Total elapsed time:' not in log:status='TERMINAL_TIMEOUT_NO_ACCEPTANCE'
    elif 'Warning:' in log:status='COMPLETED_WITH_RELAXATION_WARNINGS_NO_SELECTION'
    else:status='COMPLETED_PILOT_ONLY_NO_SELECTION'
    coupled.append({'case':path.stem,'status':status,'warning_count':log.count('Warning:'),
                    'deck_sha256':sha(path),'log_sha256':sha(path.with_suffix('.log')),
                    'raw_sha256':sha(path.with_suffix('.raw'))})
summary['coupled_probe_counts']={s:sum(d['status']==s for d in coupled) for s in sorted({d['status'] for d in coupled})}
(HERE/'coupled_attempts.json').write_text(json.dumps(coupled,indent=2)+'\n')
(HERE/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
with (HERE/'gate_summary.csv').open('w') as f:
    writer=csv.DictWriter(f,fieldnames=list(data[0]),lineterminator='\n');writer.writeheader();writer.writerows(data)

log_archive={}
for path in sorted(HERE.rglob('*.log')):
    zipped=path.with_suffix('.log.gz');zipped.write_bytes(gzip.compress(path.read_bytes(),mtime=0))
    assert gzip.decompress(zipped.read_bytes()) == path.read_bytes()
    log_archive[str(zipped.relative_to(HERE))]={'original_sha256':sha(path),'compressed_sha256':sha(zipped)}
(HERE/'log_archive.json').write_text(json.dumps(log_archive,indent=2)+'\n')

fig,axes=plt.subplots(3,1,figsize=(10,9),sharex=True)
for part,color in [('T2N7002AK','#0072b2'),('SSM3K15AMFV','#d55e00')]:
    for resistor,style in [(.001,'-'),(180,'--')]:
        row=next(d for d in base if d['part']==part and d['temperature_C']==25 and d['drain_R_ohm']==resistor and d['imposed_gate_cap_F']==4e-9)
        wave=np.genfromtxt(HERE/'gate_decks'/(row['case']+'.csv'),delimiter=',',names=True)
        x=(wave['time_s']-13e-6)*1e6;label=f'{part}, '+('direct' if resistor<1 else '180 ohm sensitivity')
        for ax,key,scale in [(axes[0],'main_gate_proxy_V',1),(axes[1],'helper_Id_A',1e3),(axes[2],'driver_current_A',1e3)]:
            ax.plot(x,wave[key]*scale,style,color=color,label=label,linewidth=1.5)
axes[0].set_ylabel('4 nF proxy gate (V)');axes[1].set_ylabel('Helper drain (mA)');axes[2].set_ylabel('Imposed driver (mA)')
axes[0].legend(fontsize=8);axes[2].set_xlabel('Time after imposed DRV command (us)')
for ax in axes:ax.grid(alpha=.25);ax.set_xlim(-.05,2.5)
fig.suptitle('Nominal helper-only comparison at 25 C\n3 V / 10 ohm imposed drive; not full eFuse or MOSFET survival proof')
fig.tight_layout();fig.savefig(HERE/'helper_comparison.png',dpi=160);fig.savefig(HERE/'helper_comparison.svg');plt.close(fig)

files=subprocess.check_output(['git','ls-files'],cwd=ROOT,text=True).splitlines()
native=[p for p in files if p.endswith(('.kicad_sch','.kicad_pcb','.kicad_pro','.kicad_sym','.kicad_mod')) or Path(p).name in ['sym-lib-table','fp-lib-table']]
preserved={}
for path in native:
    prior=subprocess.check_output(['git','show','ac4a4b9:'+path],cwd=ROOT)
    assert prior == (ROOT/path).read_bytes(),path
    preserved[path]=sha(ROOT/path)
(HERE/'native_preservation.json').write_text(json.dumps({'baseline':'ac4a4b9','preserved_native_files':len(native),'sha256':preserved},indent=2)+'\n')
print(json.dumps(summary,indent=2))
