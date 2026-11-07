#!/usr/bin/env python3
"""Latch correction sensitivities; no KiCad or vendor model writes."""
import argparse,hashlib,json,subprocess,sys
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'bank'))
from run_bank_checks import bank_deck,collect,read_raw,LIBRARY,EXECUTABLE

def latch_deck(c):
 s=bank_deck(c)
 if c.get('rail_fb_top'):
  old=3200*(1+c.get('threshold',0)*.002625);new=c['rail_fb_top']*(1+c.get('threshold',0)*.002625)
  assert f'Rfb output div {old}' in s
  s=s.replace(f'Rfb output div {old}',f'Rfb output div {new}')
 if c.get('rail_fb_bottom'):
  old=1000*(1-c.get('threshold',0)*.002625);new=c['rail_fb_bottom']*(1-c.get('threshold',0)*.002625)
  assert f'Rb div 0 {old}' in s
  s=s.replace(f'Rb div 0 {old}',f'Rb div 0 {new}')
 # Equivalent timer-cap scaling injects current-rate uncertainty; it is NOT
 # another hardware capacitance. Threshold and discharge variations still need
 # real-controller measurements; the 12 V timer table does not qualify 5 V.
 if 'gate_nF' in c:
  s=s.replace('Cgate gh cg 6.8e-08',f'Cgate gh cg {c["gate_nF"]*1e-9*(1.05 if c.get("slow_gate_corner") else 1)}')
 if c.get('regulator_bandwidth_Hz'):
  # Fixture-only finite bandwidth in the R4 drop correction. The prior ideal
  # instantaneous correction can introduce nonphysical negative damping.
  omega=2*np.pi*c['regulator_bandwidth_Hz']
  if 'Bregulated drive' in s:
   s=s.replace('I(Rconv)*.020','V(reg_correction)')
   s=s.replace('Bregulated drive',f'Bdrop reg_drop 0 V=I(Rconv)*.020\nRdrop reg_drop reg_correction 1000\nCdrop reg_correction 0 {1/(1000*omega)}\nBregulated drive')
 if 'pin_cap_esr' in c:s=s.replace('Cpin pin 0 2u Rser=2m Lser=1n',f'Cpin pin 0 2u Rser={c["pin_cap_esr"]} Lser=1n')
 if c.get('repeat_release'):
  s=s.replace('if(time<0.06,.5,if(time<0.08,2,0))','if(time<0.06,.5,if(time<0.08,2,if(mod(time-.08,.01)<.005,0,2)))')
 if c.get('ramped_release'):
  old=next(x for x in s.splitlines() if x.startswith('Bload output '))
  s=s.replace(old,'Bload output 0 I=min(max(V(output),0)/.1,if(time<.06,.5,if(time<.08,2,table(mod(time-.08,.05),0,0,.02,0,.025,2,.045,2,.05,0))))')
 if 'post_bulk_esr' in c:
  s=s.replace(f'Cbulk output 0 {c.get("bulk",112e-6)} Rser=0.4',f'Cbulk output 0 {c.get("bulk",112e-6)} Rser={c["post_bulk_esr"]}')
 if 'shunt_ohm' in c:s=s.replace('Rs sense output 20m',f'Rs sense output {c["shunt_ohm"]}')
 if c.get('mode')=='reset':
  s=s.replace('.tran 0 0.16 0 5e-07','.tran 0 12 0 1e-05').replace('if(time<140m,.5,2)','if(time<11900m,.5,2)').replace('if(time<81m,2,','if(time<251m,2,')
  s=s.replace('0.095 ','.25 ').replace('0.095001 ','.250001 ').replace('.095001,','.250001,').replace('time<.095001,','time<.250001,')
  s=s.replace('.105 0 .105001 3.3 .107 3.3 .107001 0','.30 0 .300001 3.3 .302 3.3 .302001 0')
 if c.get('all_current_one_fet'):
  # Sharing sensitivity: only one physical device fitted per function.
  # This changes total gate capacitance too; not a guaranteed mismatch model.
  s='\n'.join(l for l in s.split('\n') if not l.startswith(('Mpass2 ','Mpass3 ','Mdiode2 ','Mdiode3 ')))
  s=s.replace('Id(Mpass2) Id(Mdiode2) Id(Mpass3) Id(Mdiode3)','')
 return s

def main():
 p=argparse.ArgumentParser();p.add_argument('--work',type=Path,required=True);p.add_argument('--filter',default='');a=p.parse_args();a.work.mkdir(parents=True,exist_ok=True)
 results=[]
 for c in json.loads((HERE/'cases.json').read_text()):
  if a.filter and a.filter not in c['name']:continue
  path=a.work/(c['name']+'.cir');s=latch_deck(c)
  reuse=path.exists() and path.read_text()==s and path.with_suffix('.raw').exists() and path.with_suffix('.log').exists()
  if not reuse:
   path.write_text(s)
   for ext in ['.raw','.log']:path.with_suffix(ext).unlink(missing_ok=True)
   subprocess.run([EXECUTABLE,'-b',str(path)],check=True,timeout=180,capture_output=True)
  log=path.with_suffix('.log').read_text(errors='replace');assert 'Total elapsed time:' in log and 'Fatal Error' not in log
  r=collect(c,path);t,v=read_raw(path.with_suffix('.raw'))
  r['minimum_after_event_V']=float(v['v(output)'][t>=.08].min())
  r['final_timer_V']=float(v['v(tmr)'][-1])
  if c.get('repeat_release'):
   mask=t>=.08 if c.get('ramped_release') else t>.09;r['checks']['no_load_release_latch']=r['max_timer_V']<1.22 and r['final_output_V']>4.9
   r['checks']['repeated_abrupt_load_stays_above_4p75V']=float(v['v(output)'][mask].min())>4.75
  elif c.get('mode')=='load_release':
   r['checks']['no_load_release_latch']=r['final_output_V']>4.9 and r['max_timer_V']<1.22
   r['checks']['timer_cleared_after_release']=float(v['v(tmr)'][-1])<.1
  if c.get('mode')=='reset':
   r['checks']['fault_really_latched']=float(v['v(output)'][np.argmin(abs(t-.28))])<.1
   r['checks']['cooldown_respected']=float(v['v(output)'][np.argmin(abs(t-.31))])<.1
  if c.get('mode')=='short':r['checks']['short_disconnected']=r['final_output_V']<.1 and float(abs(v['id(mpass)'][-1]))<.01
  if c.get('mode')=='input_short':r['checks']['reverse_blocked']=float(abs(v['id(mdiode)'][-1]))<.01
  if c.get('mode')=='startup':r['checks']['startup_timer_below_warning']=r['max_timer_V']<1.22
  r['external_GH_minus_COMMON_peak_V']=float((v['v(gh)']-v['v(common)']).max()) # external GH, not controller pin
  r['bleeder_W_at_max_reg']=5.074753**2/c['bleeder_ohm']
  r['checks']['reverse_below_80V']=r['reverse_FET_abs_VDS_V']<80
  results.append(r)
  (a.work/(c['name']+'.json')).write_text(json.dumps(r,indent=2)+'\n')
  print(c['name'], 'peak',round(r['fault_output_peak_V'],4),'TMR',round(r['max_timer_V'],4),'mJ',round(r['fault_total_pass_energy_J']*1000,3),'failed',[k for k,x in r['checks'].items() if not x],flush=True)
 (HERE/'evidence/results.json').write_text(json.dumps({'scope':'Explicit typical-model sensitivities, not guaranteed hot SOA or low-VCC controller accuracy','generator_SHA256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'base_generator_SHA256':hashlib.sha256((HERE.parent/'run_protection.py').read_bytes()).hexdigest(),'bank_generator_SHA256':hashlib.sha256((HERE.parent/'bank/run_bank_checks.py').read_bytes()).hexdigest(),'models_SHA256':{str(f.relative_to(LIBRARY)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [LIBRARY/'sub/LTC4364-1.sub',LIBRARY/'cmp/standard.mos']},'results':results},indent=2)+'\n')
 (HERE/'evidence/release_minima.json').write_text(json.dumps([{k:r[k] for k in ['name','minimum_after_event_V','final_timer_V','raw_SHA256']} for r in results if r['conditions'].get('mode')=='load_release'],indent=2)+'\n')
 for r in results:assert [k for k,x in r['checks'].items() if not x]==r['conditions'].get('expected_failed_checks',[]),(r['name'],r['checks'])
if __name__=='__main__':main()
