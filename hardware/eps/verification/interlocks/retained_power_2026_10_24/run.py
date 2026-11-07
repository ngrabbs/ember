#!/usr/bin/env python3
"""Run eight controller/common-source boundary fixtures, never native KiCad edits."""
from pathlib import Path
import argparse, subprocess, json, hashlib, sys
import numpy as np
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
parser=argparse.ArgumentParser(description='Experimental RBF retained-power screen; no circuit acceptance.')
parser.add_argument('--output',type=Path,required=True,help='New external directory; models/raw outputs stay outside Git.')
parser.add_argument('--case',action='append',help='Exact case name; repeat to select a subset.')
args=parser.parse_args()
OUT=args.output.resolve()
OUT.mkdir(exist_ok=False)
sys.path.insert(0,str(ROOT/'hardware/eps/verification/protection'))
from run_protection import read_raw
LIB=Path.home()/'Library/Application Support/LTspice/lib'
base=(ROOT/'hardware/eps/verification/interlocks/controller_screening/decks/controller_battery_c1u.cir').read_text()
base=base.replace('Xcontroller 0 0 uv bias gate cs fault permission LTC4367','Vmonbias bias vin 0\nVmonsense cs sense 0\nXcontroller 0 0 uv vin gate sense fault permission LTC4367')
base=base.replace('.save V(a) V(b) V(cs) V(gate) V(bias) V(permission) V(uv) I(Vsource) Id(M1) Id(M2)', '.save V(a) V(b) V(cs) V(gate) V(bias) V(permission) V(uv) V(sys) I(Vsource) I(Vother) I(Vmonbias) I(Vmonsense) Id(M1) Id(M2)')
base=base[:base.index('.meas')]+'.end\n'
results={}
cases=[]
for direction in ['forward','reverse']:
 for bleed in [False,True]:
  name=f'staged_{direction}_'+('bleed' if bleed else 'baseline')
  deck=base.replace('8.4','8.526').replace('Cload b 0 142.7u Rser=.02\nRload b 0 10','Cdirect b 0 22u Rser=.02\nRbatfet_proxy b sys .025\nCsys sys 0 163.77u Rser=.02\nRload sys 0 10')
  deck=deck.replace('Cinput a 0 1u Rser=.05','Cinput a 0 1u Rser=.05\nVother unused 0 0\nRunused unused 0 1meg')
  if direction=='reverse':
   # Rename only port nodes, leaving the common-source and two MOSFETs structurally symmetric.
   import re
   deck=re.sub(r'\ba\b','PORT_A_TEMP',deck)
   deck=re.sub(r'\bb\b','a',deck).replace('PORT_A_TEMP','b')
  if bleed:deck=deck.replace('Rgs gate cs 1meg','Rgs gate cs 1meg\nRcsbleed cs 0 100k\nRbiasbleed bias 0 100k')
  cases.append((name,deck))
for a,b in [(8.526,0),(0,8.526),(8.526,8.526),(35,0)]:
 name=f'inhibited_a{a:g}_b{b:g}'.replace('.','p')
 deck=base.replace('Vsource drive 0 PWL(0 0 1m 0 1.001m 8.4 .8 8.4)',f'Vsource drive 0 PWL(0 0 1m 0 1.001m {a} .8 {a})')
 deck=deck.replace('Cload b 0 142.7u Rser=.02\nRload b 0 10',f'Vother other 0 PWL(0 0 1m 0 1.001m {b} .8 {b})\nRother other b .05\nRsys b sys .025\nCload sys 0 163.77u Rser=.02')
 deck=deck.replace('Vcommand command 0 PWL(0 0 50m 0 50.1m 1 500m 1 500.1m 0)','Vcommand command 0 0')
 deck=deck.replace('Rgs gate cs 1meg','Rgs gate cs 1meg\nRcsbleed cs 0 100k\nRbiasbleed bias 0 100k')
 cases.append((name,deck))
known={name for name,_ in cases}
assert not args.case or set(args.case)<=known, 'Unknown case'
model_hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [LIB/'sub/LTC4367.sub',LIB/'cmp/standard.mos']}
for name,deck in cases:
 if args.case and name not in args.case:continue
 portable=OUT/(name+'.portable.cir');portable.write_text(deck)
 target=OUT/(name+'.cir');target.write_text(deck.replace('${LTSPICE_LIBRARY}',str(LIB)))
 r={'status':'not_run'}
 try:
  proc=subprocess.run(['/Applications/LTspice.app/Contents/MacOS/LTspice','-b',str(target)],timeout=45,capture_output=True)
  log=target.with_suffix('.log');raw=target.with_suffix('.raw')
  r={'returncode':proc.returncode,'status':'incomplete'}
  if proc.returncode==0 and log.exists() and raw.exists() and 'Total elapsed time:' in log.read_text(errors='replace'):
   t,v=read_raw(raw);assert np.isclose(t[-1],.8)
   r.update(status='completed',end_s=float(t[-1]),points=len(t))
   bounds=lambda x:{'min':float(np.min(x)),'max':float(np.max(x))}
   late=t>=.75
   def mean_late(x):
    tt=np.r_[.75,t[t>.75]];xx=np.r_[np.interp(.75,t,x),x[t>.75]]
    return float(np.sum((xx[1:]+xx[:-1])/2*np.diff(tt))/(tt[-1]-tt[0]))
   for n in ['a','b','cs','gate','bias','permission','uv','sys']:
    r[n+'_V']=bounds(v['v('+n+')']);r[n+'_late_V']=bounds(v['v('+n+')'][late])
   r['vgs_V']=bounds(v['v(gate)']-v['v(cs)'])
   r['vgs_late_V']=bounds((v['v(gate)']-v['v(cs)'])[late])
   for n in ['i(vsource)','i(vother)','i(vmonbias)','i(vmonsense)','id(m1)','id(m2)']:
    r[n]=bounds(v[n]);r[n+'_late']=bounds(v[n][late]);r[n+'_late_mean']=mean_late(v[n])
   for m,node in ([(1,'b'),(2,'a')] if name.startswith('staged_reverse') else [(1,'a'),(2,'b')]):
    vd=v['v('+node+')']-v['v(cs)'];p=np.maximum(vd*v[f'id(m{m})'],0)
    r[f'm{m}_vds_V']=bounds(vd);r[f'm{m}_positive_energy_J']=float(np.sum((p[1:]+p[:-1])/2*np.diff(t)))
   r['raw_sha256']=hashlib.sha256(raw.read_bytes()).hexdigest()
  if log.exists():r['log_sha256']=hashlib.sha256(log.read_bytes()).hexdigest()
 except subprocess.TimeoutExpired:r={'status':'timeout_terminated'}
 r['portable_deck_sha256']=hashlib.sha256(portable.read_bytes()).hexdigest();results[name]=r
 (OUT/'results.json').write_text(json.dumps({'status':'EXPERIMENTAL_NOT_ACCEPTED','models':model_hashes,'cases':results},indent=2)+'\n')
 print(name,r['status'],{k:r[k] for k in ['cs_late_V','bias_late_V','vgs_V','i(vmonsense)_late'] if k in r},flush=True)
