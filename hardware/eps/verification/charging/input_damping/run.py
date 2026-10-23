#!/usr/bin/env python3
"""Study charger RC input damper with the current source protector; no CAD writes."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]/'protection/latch'))
from run_source import source_deck, read_raw, summarize, LIBRARY, EXECUTABLE

CASES = [
 dict(name='cold_start',mode='startup',temperature=-40,timer_nF=6.32,threshold=-1,bulk=106.08e-6,ceramic=37.95e-6,cap_uF=318.24,cap_esr=.1333333333),
 dict(name='hot_60V',temperature=85,timer_nF=17.5333333333,threshold=1,fault=60,cap_uF=318.24),
 dict(name='damper_short',mode='startup',temperature=85,timer_nF=17.5333333333,threshold=1,load=0,startup=0,cap_short=True,cap_uF=318.24,stop=1.2),
 dict(name='damper_short_weak',mode='startup',temperature=85,timer_nF=17.5333333333,threshold=1,load=0,startup=0,pv_current=.3,cap_short=True,cap_uF=318.24,stop=1.2),
]


def make_deck(case):
    c = dict(stage='source',extra_gate_charge=True,source_guard_L=2.5e-6,**case)
    text = source_deck(c)
    added = f'Rdamper output damper 2.7\nCdamper damper 0 {case.get("cap_uF",204)}u Rser={case.get("cap_esr",.01)} Lser=2.5n\n'
    if case.get('cap_short'):
        added += ('Vshort_cmd short_cmd 0 PWL(0 0 .12 0 .12000001 5)\n'
                  'Scap_short damper short_r short_cmd 0 cap_sw\n'
                  'Rcap_short short_r 0 10m\n.model cap_sw SW(Ron=1m Roff=1e12 Vt=2)\n')
    text = text.replace('Vlogic logic 0 3.3',added+'Vlogic logic 0 3.3')
    text = text.replace('.save ', '.save V(damper) I(Rdamper) V(vcc) V(uv) ', 1)
    return c, text


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    args.work.mkdir(parents=True,exist_ok=True)
    rows=[]
    for case in CASES:
        c,text=make_deck(case)
        path=args.work/(case['name']+'.cir')
        reuse = path.exists() and path.read_text() == text and path.with_suffix('.raw').exists() and path.with_suffix('.log').exists()
        if not reuse:
            path.write_text(text)
            for ext in ['.raw','.log']:
                path.with_suffix(ext).unlink(missing_ok=True)
            result=subprocess.run([EXECUTABLE,'-b',str(path.resolve())],cwd=args.work,timeout=45,capture_output=True)
            assert result.returncode==0, case['name']
        log=path.with_suffix('.log')
        assert 'Total elapsed time:' in log.read_text(errors='replace')
        t,v=read_raw(path.with_suffix('.raw'))
        assert np.isclose(t[-1],case.get('stop',1)), case['name']
        row=summarize(c,t,v)
        row['full_output_peak_V'] = float(v['v(output)'].max())
        row['observed_limit_checks'] = {
            'output_below_35V': row['full_output_peak_V'] < 35,
            'FET_abs_VDS_below_80V': max(row['pass_FET_abs_VDS_V'],row['reverse_FET_abs_VDS_V']) < 80,
            'FET_abs_VGS_below_16V': max(row['max_pass_VGS_V'],row['max_diode_VGS_V'],-row['pass_min_VGS_V'],-row['reverse_min_VGS_V']) < 16,
        }
        power=v['i(rdamper)']**2*2.7
        m=t>=.12
        row['damper_peak_W']=float(power.max())
        row['damper_post_event_energy_J']=float(np.sum((power[1:]+power[:-1])/2*np.diff(t)*m[1:]*m[:-1]))
        row['damper_final_W']=float(power[-1])
        row['damper_final_current_A']=float(v['i(rdamper)'][-1])
        row['damper_total_energy_J']=float(np.sum((power[1:]+power[:-1])/2*np.diff(t)))
        row['raw_sha256']=hashlib.sha256(path.with_suffix('.raw').read_bytes()).hexdigest()
        row['deck_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
        row['log_sha256']=hashlib.sha256(log.read_bytes()).hexdigest()
        rows.append(row)
        print(case['name'], 'final_output',row['final_output_V'],'Rpeak',row['damper_peak_W'],'Renergy',row['damper_post_event_energy_J'],'Rfinal',row['damper_final_W'],flush=True)
    args.output.write_text(json.dumps({'scope':'Typical-model screen; not charger loop, hot-SOA or thermal qualification','generators':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),HERE.parents[1]/'protection/latch/run_source.py',HERE.parents[1]/'protection/run_protection.py']},'models':{str(p.relative_to(LIBRARY)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [LIBRARY/'sub/LTC4364-2.sub',LIBRARY/'cmp/standard.mos']},'results':rows},indent=2)+'\n')


if __name__=='__main__': main()
