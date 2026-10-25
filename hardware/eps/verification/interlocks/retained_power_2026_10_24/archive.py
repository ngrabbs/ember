#!/usr/bin/env python3
"""Archive completed raw evidence and correct per-device drain mapping from each deck."""
import argparse, hashlib, json, re, sys
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
sys.path.insert(0,str(ROOT/'hardware/eps/verification/protection'))
from run_protection import read_raw
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--raw-dir',type=Path,required=True)
args=parser.parse_args()
rawdir=args.raw_dir.resolve()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
bounds=lambda x:{'min':float(np.min(x)),'max':float(np.max(x))}
results={}
for portable in sorted(rawdir.glob('*.portable.cir')):
 name=portable.name.removesuffix('.portable.cir')
 raw=rawdir/(name+'.raw'); log=rawdir/(name+'.log');deck=portable.read_text()
 assert 'Total elapsed time:' in log.read_text(errors='replace'),name
 t,v=read_raw(raw);assert np.isclose(t[-1],.8),name
 late=t>=.75
 def mean_late(x):
  tt=np.r_[.75,t[t>.75]];xx=np.r_[np.interp(.75,t,x),x[t>.75]]
  return float(np.sum((xx[1:]+xx[:-1])/2*np.diff(tt))/(tt[-1]-tt[0]))
 r={'status':'completed','points':len(t),'end_s':float(t[-1]),'raw_sha256':sha(raw),'original_log_sha256':sha(log),'portable_deck_sha256':sha(portable)}
 for n in ['a','b','cs','gate','bias','permission','uv','sys']:
  x=v[f'v({n})'];r[n+'_V']=bounds(x);r[n+'_late_V']=bounds(x[late])
 r['vgs_V']=bounds(v['v(gate)']-v['v(cs)']);r['vgs_late_V']=bounds((v['v(gate)']-v['v(cs)'])[late])
 for n in ['i(vsource)','i(vother)','i(vmonbias)','i(vmonsense)','id(m1)','id(m2)']:
  x=v[n];r[n]=bounds(x);r[n+'_late']=bounds(x[late]);r[n+'_late_mean']=mean_late(x)
 for m in [1,2]:
  drain=re.search(rf'^M{m} (\w+) gate cs cs IRLR2908$',deck,re.M)[1]
  vd=v[f'v({drain})']-v['v(cs)'];p=np.maximum(vd*v[f'id(m{m})'],0)
  r[f'm{m}_drain_node']=drain;r[f'm{m}_vds_V']=bounds(vd)
  r[f'm{m}_positive_energy_J']=float(np.sum((p[1:]+p[:-1])/2*np.diff(t)))
 r['sample_450ms_V']={n:float(np.interp(.45,t,v[f'v({n})'])) for n in ['sys','bias','cs','gate']}
 cols=['v(a)','v(b)','v(sys)','v(cs)','v(bias)','v(gate)','v(permission)','id(m1)','id(m2)','i(vmonbias)','i(vmonsense)']
 grid=np.unique(np.r_[np.linspace(0,.8,3201),.049,.050,.0501,.500,.5001,.501,.75])
 csv=HERE/'samples'/(name+'.csv');csv.parent.mkdir(exist_ok=True)
 np.savetxt(csv,np.column_stack([grid]+[np.interp(grid,t,v[c]) for c in cols]),delimiter=',',header=','.join(['time_s']+cols),comments='',fmt='%.9g')
 for folder in ['decks','logs']:(HERE/folder).mkdir(exist_ok=True)
 (HERE/'decks'/(name+'.cir')).write_text(deck)
 normalized=log.read_text(errors='replace').replace(str(rawdir),'${RAW_DIR}').replace(str(Path.home()/'Library/Application Support/LTspice/lib'),'${LTSPICE_LIBRARY}')
 (HERE/'logs'/(name+'.log')).write_text(normalized.rstrip()+'\n')
 results[name]=r
assert len(results)==8,len(results)
models={str(p):sha(p) for p in [Path.home()/'Library/Application Support/LTspice/lib/sub/LTC4367.sub',Path.home()/'Library/Application Support/LTspice/lib/cmp/standard.mos']}
(HERE/'results.json').write_text(json.dumps({'status':'EXPERIMENTAL_NOT_ACCEPTED','raw_directory':str(rawdir),'models':models,'cases':results},indent=2)+'\n')
# Make diagnostic process provenance explicit: the initial scratch analyzer assumed
# M1 drain=a even in reversed fixtures. Authoritative metrics above parse each deck.
initial=rawdir/'results.json'
(HERE/'analysis_provenance.json').write_text(json.dumps({'initial_scratch_summary_sha256':sha(initial),'supersedes':'Initial reversed-device VDS/energy used fixed a/b indexing; results.json here parses M1/M2 drain nodes from each deck. No native design used the scratch metrics.','source_runner_sha256':sha(Path('/tmp/ember-rbf-boundary-study.py')) if Path('/tmp/ember-rbf-boundary-study.py').exists() else None},indent=2)+'\n')
print('Archived 8 completed cases; reverse-device drain mapping independently resolved from decks.')
