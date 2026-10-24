#!/usr/bin/env python3
"""50 V bank sensitivities. Imports the recorded barrier without changing it.
Fixtures use individual capacitor branches and the actual upstream R4 shunt.
No native KiCad or vendor-model files are written.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from run_protection import deck, read_raw, summarize, LIBRARY, EXECUTABLE

HERE=Path(__file__).resolve().parent

def bank_deck(c):
    s=deck(c)
    old='Cprebulk input 0 160u Rser=267m Lser=5n\nCprecer input 0 24u Rser=2m Lser=1n'
    assert s.count(old)==1
    capnet=[]
    for kind,count,cap,esr,esl in [
        ('b',5,c['pre_bulk'],c['pre_bulk_esr'],c.get('pre_bulk_esl',1e-9)),
        ('c',8,c['pre_ceramic'],c.get('pre_ceramic_esr',.00025),c.get('pre_ceramic_esl',.125e-9))]:
        for i in range(count):
            capnet.append(f'Cnew{kind}{i} bank 0 {cap/count} Rser={esr*count} Lser={esl*count}')
    s=s.replace(old,'\n'.join(capnet)+'\nRconv bank input .020')
    if not c.get('bypass_shunt'):
        s=s.replace('Lfeed wire input ','Lfeed wire bank ')
        # Healthy fixture regulates after R4. During a power-switch short,
        # its feedback/command source is no longer allowed to regulate.
        if c.get('finite_energy'):
            s=s.replace('Bgood 0 input I=', 'Bgood 0 bank I=')
        else:
            s=s.replace('Vrail drive 0 PWL','Vrail command 0 PWL')
            healthy='1' if c.get('mode') in ['startup','load_release','short','input_short'] else 'if(time<.08,1,0)'
            if c.get('mode')=='reset':healthy='if(time<.08,1,if(time>.095001,1,0))'
            s=s.replace('\nRfeed drive wire ',f'\nBregulated drive 0 V=V(command)+({healthy})*I(Rconv)*.020\nRfeed drive wire ')
    timer=c.get('timer_pF',220)*1e-12*(1.05 if c.get('slow_gate_corner') else 1)
    s=s.replace('Ct tmr 0 2.2e-10',f'Ct tmr 0 {timer}')
    if c.get('bleeder_ohm'):
        s=s.replace('Cbulk output',f'Rbleed output 0 {c["bleeder_ohm"]}\nCbulk output')
    if c.get('slow_gate_corner'):
        s=s.replace('Cgate gh cg 6.8e-08','Cgate gh cg 7.14e-08')
        s=s.replace('Bf=60 Vaf=20','Bf=30 Vaf=20')
        s=s.replace('Rcg cg 0 2.2k','Cgate_extra gh common 10n\nRcg cg 0 2.2k')
    if c.get('finite_energy') and c.get('mode')=='startup':
        # Finite-current emulator, NOT a TPS552872 switching/startup model.
        # No bridge closes in a startup-only case. 2.5ms commanded ramp;
        # total source current limited to the prior slow-limit sensitivity.
        s=s.replace('1m 4.919254','2.5m 4.919254').replace('1m 5.074753','2.5m 5.074753')
        s=s.replace('limit((V(command)-V(input))/.001,-10,10)',
                    'limit((V(command)-V(input))/.001,0,2.369)')
        s=s.replace('I=if(time<0.08,limit','I=if(time<1,limit')
        s=s.replace('Sbridge high wire bridge 0 swbridge','Sbridge high wire 0 0 swbridge')
    currents=' '.join(f'I(Cnew{k}{i})' for k,n in [('b',5),('c',8)] for i in range(n))
    return s.replace('.save V(pin)',f'.save V(bank) I(Rconv) {currents} V(pin)')

def collect(c,path):
    t,v=read_raw(path.with_suffix('.raw'));r=summarize(c,t,v)
    m=t>=.08;dt=np.diff(t)
    r.update(bank_peak_V=float(v['v(bank)'].max()),
             converter_shunt_abs_peak_A=float(np.max(abs(v['i(rconv)']))),
             converter_shunt_fault_energy_J=float(np.sum((v['i(rconv)'][1:]**2+v['i(rconv)'][:-1]**2)/2*dt*m[1:]*m[:-1]*.020)),
             largest_bulk_branch_abs_peak_A=max(float(np.max(abs(v[f'i(cnewb{i})']))) for i in range(5)),
             largest_ceramic_branch_abs_peak_A=max(float(np.max(abs(v[f'i(cnewc{i})']))) for i in range(8)),
             deck_SHA256=hashlib.sha256(path.read_bytes()).hexdigest(),
             raw_SHA256=hashlib.sha256(path.with_suffix('.raw').read_bytes()).hexdigest())
    r['checks']={'bank_below_50V':r['bank_peak_V']<50,
                 'protected_below_provisional_5p5V':r['fault_output_peak_V']<5.5,
                 'pass_below_80V':r['pass_FET_abs_VDS_V']<80,
                 'gate_within_16V':max(r['max_pass_VGS_V'],r['max_diode_VGS_V'],-r['pass_min_VGS_V'],-r['reverse_min_VGS_V'])<16}
    if c.get('mode') in ['startup','reset']:r['checks']['final_above_4p75V']=r['final_output_V']>4.75
    if c.get('mode')=='load_release':r['checks']['no_load_release_latch']=r['final_output_V']>4.9 and r['max_timer_V']<1.25
    return r

def main():
    p=argparse.ArgumentParser();p.add_argument('--work',type=Path,required=True)
    p.add_argument('--output',type=Path,default=HERE/'evidence');a=p.parse_args()
    a.work.mkdir(parents=True,exist_ok=True);a.output.mkdir(parents=True,exist_ok=True)
    cases=json.loads((HERE/'cases.json').read_text());results=[]
    for c in cases:
        path=a.work/(c['name']+'.cir');content=bank_deck(c)
        reusable=path.exists() and path.read_text()==content and path.with_suffix('.log').exists() and path.with_suffix('.raw').exists()
        if not reusable:
            path.write_text(content)
            for ext in ['.raw','.log']:path.with_suffix(ext).unlink(missing_ok=True)
            subprocess.run([EXECUTABLE,'-b',str(path)],check=True,timeout=120,capture_output=True)
        log=path.with_suffix('.log').read_text(errors='replace')
        assert 'Total elapsed time:' in log and 'Fatal Error' not in log,c['name']
        r=collect(c,path);results.append(r)
        print(c['name'],'bank',round(r['bank_peak_V'],4),'protected',round(r['fault_output_peak_V'],4),
              'final',round(r['final_output_V'],4),'checks',all(r['checks'].values()),flush=True)
    models={str(f.relative_to(LIBRARY)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [LIBRARY/'sub/LTC4364-1.sub',LIBRARY/'cmp/standard.mos']}
    out={'scope':'Typical-model development screening; source emulator is not TPS552872 startup qualification',
         'models_SHA256':models,'generator_SHA256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'results':results}
    (a.output/'results.json').write_text(json.dumps(out,indent=2)+'\n')
    for r in results:
        failed=[k for k,v in r['checks'].items() if not v]
        assert failed==r['conditions'].get('expected_failed_checks',[]),(r['name'],failed)

if __name__=='__main__':main()
