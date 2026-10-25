#!/usr/bin/env python3
"""Source timer survival sensitivities. No CAD writes."""
import argparse,hashlib,json,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from run_protection import deck,read_raw,summarize,LIBRARY,EXECUTABLE

def source_deck(c):
 s=deck(c).replace('Ct tmr 0 1e-07',f'Ct tmr 0 {c["timer_nF"]*1e-9}')
 # Gate-charge sensitivity external to the installed typical device model.
 if c.get('source_guard_L'):
  s=s.replace('Lfeed raw input 1u','Lfeed raw upstream 1u\nLsource upstream input '+str(c['source_guard_L'])+' Rser=10m')
 if c.get('hard_input_short'):
  s=s.replace('Vlogic logic 0 3.3','Vhard hard 0 PWL(0 0 .12 0 .12000001 5)\nShard input hard_short hard 0 sw_hard\nRhard hard_short 0 10m\n.model sw_hard SW(Ron=1m Roff=1e12 Vt=2)\nVlogic logic 0 3.3')
 if c.get('extra_gate_charge'):s=s.replace('Rcg cg 0 2.2k','Cextra gh common 10n\nRcg cg 0 2.2k')
 if c.get('source_guard_L'):
  s=s.replace('Shard input hard_short','Shard upstream hard_short').replace('.save V(pin)', '.save I(Lsource) V(upstream) V(pin)')
 return s

def main():
 p=argparse.ArgumentParser();p.add_argument('--work',type=Path,required=True);a=p.parse_args();a.work.mkdir(parents=True,exist_ok=True);rs=[]
 for c in json.loads((HERE/'source_cases.json').read_text()):
  f=a.work/(c['name']+'.cir');s=source_deck(c)
  if not(f.exists() and f.read_text()==s and f.with_suffix('.raw').exists() and f.with_suffix('.log').exists()):
   f.write_text(s)
   for e in ['.raw','.log']:f.with_suffix(e).unlink(missing_ok=True)
   subprocess.run([EXECUTABLE,'-b',str(f)],check=True,capture_output=True,timeout=180)
  assert 'Total elapsed time:' in f.with_suffix('.log').read_text(errors='replace')
  t,v=read_raw(f.with_suffix('.raw'));r=summarize(c,t,v)
  r['deck_SHA256']=hashlib.sha256(f.read_bytes()).hexdigest();r['raw_SHA256']=hashlib.sha256(f.with_suffix('.raw').read_bytes()).hexdigest()
  r['checks']={'output_below_35V':r['fault_output_peak_V']<35,'VDS_below_80V':max(r['pass_FET_abs_VDS_V'],r['reverse_FET_abs_VDS_V'])<80,'VGS_within_16V':max(r['max_pass_VGS_V'],r['max_diode_VGS_V'],-r['pass_min_VGS_V'],-r['reverse_min_VGS_V'])<16}
  if c.get('package_parasitics'):
   r['checks']['VGS_within_16V'] &= max(r['internal_pass_abs_VGS_V'],r['internal_reverse_abs_VGS_V'])<16
   r['checks']['VDS_below_80V'] &= max(r['internal_pass_abs_VDS_V'],r['internal_reverse_abs_VDS_V'])<80
   r['checks']['reverse_pulse_below_150A']=r['reverse_channel_abs_current_A']<150
  if c.get('source_guard_L'):
   r['source_guard_peak_A']=float(abs(v['i(lsource)']).max())
   r['upstream_peak_V']=float(v['v(upstream)'].max())
   r['source_guard_abs_terminal_voltage_V']=float(abs(v['v(upstream)']-v['v(input)']).max())
  if c.get('mode')=='startup':r['checks']['source_started']=r['final_output_V']>31 and r['max_timer_V']<1.22
  rs.append(r);print(c['name'],'V',round(r['fault_output_peak_V'],3),'E mJ',round(r['fault_total_pass_energy_J']*1000,3),'TMR',round(r['max_timer_V'],3),flush=True)
 (HERE/'evidence/source_results.json').write_text(json.dumps({'scope':'Typical models with equivalent timer-rate and gate-charge sensitivities; not physical hot-SOA qualification','generator_SHA256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'base_generator_SHA256':hashlib.sha256((HERE.parent/'run_protection.py').read_bytes()).hexdigest(),'models_SHA256':{str(f.relative_to(LIBRARY)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [LIBRARY/'sub/LTC4364-2.sub',LIBRARY/'cmp/standard.mos']},'results':rs},indent=2)+'\n')
 for r in rs:assert [k for k,v in r['checks'].items() if not v]==r['conditions'].get('expected_failed_checks',[]),(r['name'],r['checks'])
if __name__=='__main__':main()
