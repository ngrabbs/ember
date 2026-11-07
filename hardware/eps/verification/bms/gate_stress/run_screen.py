"""Diagnostic only: exact TI FET model, imposed gate drive, hypothetical clamp.

No BQ model, physical zener model, pack model or SOA qualification is implied.
External manufacturer model is hash checked and never modified or committed.
"""
from pathlib import Path
import argparse, hashlib, json, subprocess, sys
import numpy as np
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]/'protection'))
from run_protection import read_raw

def deck(temp, delay, clamp, profile):
    protection = '' if not clamp else '''
* Hypothetical piecewise clamp, NOT a BZT52C15 model or guaranteed bounds.
Bzc gc raw I=max((V(gc,raw)-16.38)/30,0)-max((-V(gc,raw)-0.9)/2,0)
Bzd gd port I=max((V(gd,port)-16.38)/30,0)-max((-V(gd,port)-0.9)/2,0)
Czc gc raw 100p
Czd gd port 100p
'''
    text = f'''* Coupled channel diagnostic, imposed drive; NOT pack-protection acceptance
.include "${{FET_MODEL}}"
Vcell cell 0 8.526
Rcell cell cable 80m
Lcell cable raw 1u
Vch chgcmd 0 20.526
* Held BAT reservoir / stiff charge pump is an imposed stress fixture.
Bds dsgcmd 0 V=if(time<{{1m+{delay}}},20.526,V(port)+0.4)
Rcg chgcmd gc 5.1k
Rdg dsgcmd gd 5.1k
Rgs1 gc raw 10meg
Rgs2 gd port 10meg
Xchg common gc raw csd18543q3a
Vids common dsgdrain 0
Xdsg dsgdrain gd port csd18543q3a
Rload port 0 4.263
Vfault command 0 PWL(0 0 1m 0 1.000001m 5)
Sfault port fault command 0 SHORT
Rfault fault 0 10m
.model SHORT SW(Ron=1m Roff=1e12 Vt=2.5)
* Equivalent capacitances of the two native 100 nF series pairs.
Cpair raw port 50n Rser=100m
Cport port 0 50n Rser=100m
{protection}
.temp {temp}
.options plotwinsize=0
.tran 0 3m 0 100n
.save V(raw) V(common) V(dsgdrain) V(port) V(gc) V(gd) I(Vids) I(Lcell) I(Rcg) I(Rdg)
.end
'''
    if profile == 'slewed_gear':
        delay_s={'160u':.000160,'500u':.000500}[delay]
        text=text.replace(f'Bds dsgcmd 0 V=if(time<{{1m+{delay}}},20.526,V(port)+0.4)',
            f'Voff off 0 PWL(0 1 {.001+delay_s} 1 {.001+delay_s+.000100} 0)\n'
            'Bds dsgcmd 0 V=V(port)+0.4+V(off)*(20.126-V(port))')
        text=text.replace('.options plotwinsize=0','.options plotwinsize=0 method=gear')
    return text


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--model',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--profile',choices=['abrupt','slewed_gear'],default='abrupt')
    p.add_argument('--fault-milliohm',choices=[1,10],type=int,default=10)
    p.add_argument('--only-temp',choices=[25,85],type=int)
    p.add_argument('--only-delay',choices=['160u','500u'])
    a=p.parse_args()
    digest=hashlib.sha256(a.model.read_bytes()).hexdigest()
    expected=json.loads((HERE/'sources.json').read_text())['TI_model_sha256']
    assert digest==expected, 'External manufacturer model differs'
    a.output.mkdir(exist_ok=False)
    label=a.profile if a.fault_milliohm==10 else a.profile+'_fault1m'
    target=HERE if label=='abrupt' else HERE/label
    target.mkdir(exist_ok=True)
    result={'profile':a.profile,'status':'DIAGNOSTIC_ONLY_NOT_SOA_OR_CLAMP_ACCEPTANCE','cases':{}}
    for temp in ([a.only_temp] if a.only_temp is not None else [25,85]):
      for delay in ([a.only_delay] if a.only_delay else ['160u','500u']):
       for clamp in [False,True]:
        name=f't{temp}_delay{delay}_clamp{int(clamp)}'
        portable=deck(temp,delay,clamp,a.profile).replace('Rfault fault 0 10m',f'Rfault fault 0 {a.fault_milliohm}m')
        (target/(name+'.cir')).write_text(portable)
        f=a.output/(name+'.cir')
        f.write_text(portable.replace('${FET_MODEL}',str(a.model.resolve())))
        try:
          proc=subprocess.run(['/Applications/LTspice.app/Contents/MacOS/LTspice','-b',str(f)],timeout=45,capture_output=True)
          assert proc.returncode==0, proc.stderr.decode(errors='replace')
          log=f.with_suffix('.log');assert 'Total elapsed time:' in log.read_text()
          t,v=read_raw(f.with_suffix('.raw'));assert np.isclose(t[-1],.003), f'Incomplete raw: final time {t[-1]} s'
          ids=v['i(vids)'];vds=v['v(dsgdrain)']-v['v(port)'];vgs=v['v(gd)']-v['v(port)']
          mask=t>=.001
          power=vds*ids
          rec={'status':'completed','points':len(t),'DSG_VGS_min_max_V':[float(vgs.min()),float(vgs.max())],
               'CHG_VGS_min_max_V':[float((v['v(gc)']-v['v(raw)']).min()),float((v['v(gc)']-v['v(raw)']).max())],
               'DSG_VDS_min_max_V':[float(vds.min()),float(vds.max())],
               'peak_discharge_A':float(ids.max()),'peak_DSG_power_W':float(power.max()),
               'post_fault_DSG_positive_energy_J':float(np.trapezoid(np.maximum(power[mask],0),t[mask])),
               'final_discharge_A':float(ids[-1]),
               'peak_abs_DSG_drive_A':float(np.abs(v['i(rdg)']).max()),
               'portable_deck_sha256':hashlib.sha256(portable.encode()).hexdigest(),
               'executed_deck_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),
               'raw_sha256':hashlib.sha256(f.with_suffix('.raw').read_bytes()).hexdigest()}
          (target/(name+'.log')).write_text(log.read_text().replace(str(a.model.resolve()),'${FET_MODEL}').replace(str(a.output),'${RUN_OUTPUT}').replace('/private'+str(a.output),'${RUN_OUTPUT}'))
        except (subprocess.TimeoutExpired, AssertionError, ValueError, FileNotFoundError) as e:
          rec={'status':'failed_or_timed_out','detail':str(e)}
        log=f.with_suffix('.log')
        if log.exists():
          (target/(name+'.log')).write_text(log.read_text().replace('/private'+str(a.output),'${RUN_OUTPUT}').replace(str(a.output),'${RUN_OUTPUT}').replace(str(a.model.resolve()),'${FET_MODEL}'))
        result['cases'][name]=rec
        print(name,rec['status'],flush=True)
        (target/'results.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
