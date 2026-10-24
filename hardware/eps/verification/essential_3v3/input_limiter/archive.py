"""Archive development experiments without redistributing vendor models/raw files.

Requires the original external run directories and NumPy/Matplotlib. Re-running
this archive does not re-run simulations or turn numerical completion into an
electrical acceptance verdict.
"""
from pathlib import Path
import hashlib,json,shutil,sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
H=Path(__file__).resolve().parent; ROOT=H.parents[4]
sys.path.insert(0,str(ROOT/'hardware/eps/verification/protection'))
from run_protection import read_raw
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
groups={
 'crosscheck':Path('/tmp/ember-input-envelope-crosscheck'),
 'input_only':Path('/tmp/ember-ltc4231-input-first'),
 'early_diagnostic':Path('/tmp/ember-input-coupled4231'),
 'late_trap':Path('/tmp/ember-input-coupled4231-late'),
 'late_gear':Path('/tmp/ember-input-coupled4231-gear'),
}
out={'scope':'DEVELOPMENT_EVIDENCE_ONLY;NO_INTEGRATION_OR_SOA_ACCEPTANCE','groups':{}}
for group,folder in groups.items():
 r=json.loads((folder/'results.json').read_text())
 rows=r['cases']; rows={str(c['id']):c for c in rows} if isinstance(rows,list) else rows
 for key,c in rows.items():
  stem='case_'+key if group=='crosscheck' else key
  p=folder/(stem+'.portable.cir'); p=p if p.exists() else folder/(stem+'.cir')
  digest=c.get('portable_deck_sha256',c.get('deck_sha256'));assert sha(p)==digest
  dest=H/'decks'/(group+'__'+key+'.cir');dest.parent.mkdir(exist_ok=True);shutil.copyfile(p,dest)
  c['archived_deck']=str(dest.relative_to(H));c['archived_deck_sha256']=sha(dest)
  log=folder/(stem+'.log')
  if log.exists():
   assert sha(log)==c['log_sha256']
   content=log.read_text(errors='replace').replace(str(folder),'${RUN_DIR}').replace(str(Path.home()/'Library/Application Support/LTspice/lib'),'${LTSPICE_LIBRARY}')
   dest=H/'logs'/(group+'__'+key+'.log');dest.parent.mkdir(exist_ok=True);dest.write_text(content)
   c['archived_log']=str(dest.relative_to(H));c['normalized_log_sha256']=sha(dest)
  if c.get('status')=='completed' or group=='crosscheck':
   raw=folder/(stem+'.raw');assert sha(raw)==c['raw_sha256']
   t,v=read_raw(raw);assert np.isclose(t[-1],c['end_s'])
  if group=='early_diagnostic':
   c['acceptance_excluded_reason']='Fault applied before output gate/startup settled; incomplete cases also excluded.'
  elif c.get('status')=='incomplete':
   c['acceptance_excluded_reason']='Simulator did not complete; partial trajectory is not accepted.'
 r['cases']=rows;out['groups'][group]=r
(H/'results.json').write_text(json.dumps(out,indent=2)+'\n')
shutil.copyfile('/tmp/ember-input-envelope-repeat.json',H/'envelope_half_step.json')
baseline=json.loads((H.parent/'guard_refinement/native_baseline.json').read_text());baseline['basis']='66bb97e; identical to previous 218-file native baseline'
for name,digest in baseline['files'].items():assert sha(ROOT/name)==digest,name
(H/'native_baseline.json').write_text(json.dumps(baseline,indent=2)+'\n')
fig,axes=plt.subplots(3,1,figsize=(9,9),sharex=True)
csvrows=[]
for key in ['L0p1_load2','L0p5_load2','L3p136_load2','L0p1_noload']:
 t,v=read_raw(groups['late_gear']/(key+'.raw'))
 mask=(t>=.299999)&(t<=.30003);x=(t[mask]-.3)*1e6
 for ax,trace in zip(axes,['v(out)','i(rinshunt)','i(lfailed)']):ax.plot(x,v[trace][mask],label=key,linewidth=1)
 grid=np.linspace(.299999,.30003,3101)
 csvrows.extend(zip([key]*len(grid),(grid-.3)*1e6,*[np.interp(grid,t,v[z]) for z in ['v(out)','i(rinshunt)','i(lfailed)']]))
axes[0].axhline(3.6,color='red',linestyle='--');axes[0].set_ylabel('Protected rail (V)')
axes[1].axhline(156,color='red',linestyle='--',label='156 A pulse rating; conditions apply');axes[1].set_ylabel('Input shunt current (A)')
axes[2].set_ylabel('Imposed buck-L current (A)');axes[2].set_xlabel('Time from fault (µs)')
for ax in axes:ax.grid(True,alpha=.25);ax.legend(fontsize=7)
fig.suptitle('Typical coupled models, Gear 0.5 µs maxstep\nBehavioral buck proxy and linear inductors; no survival acceptance')
fig.tight_layout();fig.savefig(H/'coupled_faults.png',dpi=150);plt.close(fig)
import csv
with (H/'coupled_plot.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['case','time_from_fault_us','protected_V','input_current_A','buck_current_A']);w.writerows(csvrows)
print('Archived four solver crosschecks, four input cases and twelve coupled attempts; generated one plot.')
