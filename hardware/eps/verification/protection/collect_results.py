#!/usr/bin/env python3
"""Summarize saved LTspice raw outputs; no CAD/model-file mutations.
Run only after the serial sweep finishes. Raw waveform files stay outside Git.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from run_protection import HERE, LIBRARY, deck, read_raw, summarize

p=argparse.ArgumentParser()
p.add_argument('--work',type=Path,required=True)
p.add_argument('--output',type=Path,default=HERE/'evidence')
a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
cases=json.loads((HERE/'cases.json').read_text());results=[]
for c in cases:
    path=a.work/(c['name']+'.cir')
    assert path.read_text()==deck(c),c['name']+' stale circuit'
    log=path.with_suffix('.log').read_text(errors='replace')
    assert 'Total elapsed time:' in log and 'Fatal Error' not in log,c['name']
    t,v=read_raw(path.with_suffix('.raw'));r=summarize(c,t,v)
    r['deck_SHA256']=hashlib.sha256(path.read_bytes()).hexdigest()
    r['raw_SHA256']=hashlib.sha256(path.with_suffix('.raw').read_bytes()).hexdigest()
    r['checks']={}
    if 'rejection' in c['name']:
        r['checks']['intentional_rail_rejection_above_5p5V']=r['fault_output_peak_V']>5.5
    else:
        r['checks']['provisional_output_ceiling']=r['fault_output_peak_V']<(35 if c.get('stage')=='source' else 5.5)
        r['checks']['external_pass_VDS_below_80V']=r['pass_FET_abs_VDS_V']<80
        r['checks']['external_gate_VGS_within_16V']=max(r['max_pass_VGS_V'],r['max_diode_VGS_V'],-r['pass_min_VGS_V'],-r['reverse_min_VGS_V'])<16
    if c.get('mode')=='reset' or c['name']=='rail_load_min_hot':
        r['checks']['recovered_above_4p75V']=r['final_output_V']>4.75
    if c['name']=='source_ov_return':r['checks']['autonomous_source_restart']=r['final_output_V']>31
    if c['name'] in ['source_hotplug60','source_persistent60']:
        r['checks']['high_source_inhibited']=r['final_output_V']<.1
        r['checks']['no_sustained_TVS_absorption']=r['TVS_energy_J']<.001
    if c.get('package_parasitics'):
        r['checks']['internal_gate_VGS_within_16V']=max(r['internal_pass_abs_VGS_V'],r['internal_reverse_abs_VGS_V'])<16
        r['checks']['reverse_pulse_below_150A']=r['reverse_channel_abs_current_A']<150
    r['screening_checks_pass']=all(r['checks'].values())
    results.append(r)

models={str(f.relative_to(LIBRARY)):hashlib.sha256(f.read_bytes()).hexdigest()
        for f in [LIBRARY/'sub/LTC4364-1.sub',LIBRARY/'sub/LTC4364-2.sub',LIBRARY/'cmp/standard.mos']}
out={'date':'2026-10-23','simulator':'LTspice 26.0.2 macOS',
     'models_SHA256':models,
     'generator_SHA256':hashlib.sha256((HERE/'run_protection.py').read_bytes()).hexdigest(),
     'cases_SHA256':hashlib.sha256((HERE/'cases.json').read_bytes()).hexdigest(),
     'scope':'Development screening only; no hardware, hot SOA, low-VCC accuracy or flight qualification',
     'results':results}
(a.output/'results.json').write_text(json.dumps(out,indent=2)+'\n')
lines=['| Case | Pre-fault V | Peak protected V | Pass bank mJ after fault | Final V | Screening |',
       '|---|---:|---:|---:|---:|---|']
for r in results:
    lines.append(f"| {r['name']} | {r['pre_fault_output_V']:.4f} | {r['fault_output_peak_V']:.4f} | {1000*r['fault_total_pass_energy_J']:.3f} | {r['final_output_V']:.4f} | {'pass' if r['screening_checks_pass'] else 'FAIL'} |")
(a.output/'results.md').write_text('\n'.join(lines)+'\n')

for name,window in [('source_ov60',(.1195,.132)),('rail_hard_bridge_cold',(.07999,.0806)),('source_package_short',(.119999,.12002)),('rail_finite_330u',(.07999,.0806))]:
    c=next(c for c in cases if c['name']==name)
    t,v=read_raw(a.work/(name+'.raw'));m=(t>=window[0])&(t<=window[1]);tf=.12 if c.get('stage')=='source' else .08
    x=(t[m]-tf)*1e6
    d=v['v(dp)'] if c.get('package_parasitics') else v['v(pin)']
    s=v['v(sp)'] if c.get('package_parasitics') else v['v(common)']
    current=sum(v[k] for k in ['id(mpass)','id(mpass2)','id(mpass3)'] if k in v)
    fig,axes=plt.subplots(3,1,figsize=(9,8),sharex=True,layout='constrained')
    ax=axes[0];ax.plot(x,v['v(input)'][m],label='Upstream node',color='#777777')
    ax.plot(x,v['v(pin)'][m],label='Protector PIN',color='#245b95');ax.set_ylabel('Input V')
    ay=ax.twinx();ay.plot(x,v['v(output)'][m],color='#c25820',label='Protected output');ay.set_ylabel('Protected V',color='#c25820')
    ay.axhline(35 if tf==.12 else 5.5,color='#c25820',ls=':',alpha=.6)
    ax.legend(loc='upper left');ay.legend(loc='upper right')
    axes[1].plot(x,np.maximum((d-s)*current,0)[m],label='Total pass bank power');axes[1].set_ylabel('Pass W');axes[1].legend()
    axes[2].plot(x,(v['v(gh)']-s)[m],label='Pass VGS');axes[2].plot(x,(v['v(gd)']-v.get('v(sd)',v['v(common)']))[m],label='Reverse VGS')
    axes[2].set_ylabel('Gate V');axes[2].set_xlabel('Time since fault (µs)');axes[2].legend()
    for ax in axes:ax.grid(alpha=.25)
    fig.suptitle(name+' — typical model / stated fixture; not qualification')
    fig.savefig(a.output/(name+'.png'),dpi=160);plt.close(fig)

failed=[r['name'] for r in results if not r['screening_checks_pass']]
print(json.dumps({'cases':len(results),'failed_screening':failed},indent=2))
assert not failed,failed
