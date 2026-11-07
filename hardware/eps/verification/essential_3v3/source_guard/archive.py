"""Archive the two source-guard sensitivity cases; not a part selection."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
H=Path(__file__).resolve().parent;ROOT=H.parents[4]
sys.path.insert(0,str(ROOT/'hardware/eps/verification/protection'))
from run_protection import read_raw
F=Path('/tmp/ember-sourceguard-1p232');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((F/'results.json').read_text());fig,ax=plt.subplots(3,1,figsize=(9,8),sharex=True)
for name,c in r['cases'].items():
 assert c['status']=='completed' and c['returncode']==0 and c['end_s']==.34
 for ext in ['raw','log']:assert sha(F/(name+'.'+ext))==c[ext+'_sha256']
 d=F/(name+'.portable.cir');assert sha(d)==c['portable_deck_sha256']
 (H/'decks').mkdir(exist_ok=True);(H/'logs').mkdir(exist_ok=True)
 (H/'decks'/(name+'.cir')).write_bytes(d.read_bytes())
 log=(F/(name+'.log')).read_text().replace(str(F),'${RUN_DIR}').replace(str(Path.home()/'Library/Application Support/LTspice/lib'),'${LTSPICE_LIBRARY}')
 target=H/'logs'/(name+'.log');target.write_text(log);c['normalized_log_sha256']=sha(target)
 t,v=read_raw(F/(name+'.raw'));assert t[-1]==.34
 fault=t>=.3;first_ms=fault&(t<=.301)
 p=(v['v(insense)']-v['v(ips)'])*v['i(vinmos)']
 c['input_FET_abs_Vgs_max_V']=float(abs(v['v(ingate)']-v['v(ips)'])[fault].max())
 c['output_FET_abs_Vgs_max_V']=float(abs(v['v(gate)']-v['v(common)'])[fault].max())
 c['input_FET_positive_port_energy_first_ms_J']=float(np.trapezoid(np.maximum(p[first_ms],0),t[first_ms]))
 c['input_FET_port_power_peak_W']=float(p[fault].max())
 m=(t>=.299999)&(t<=.30004);x=(t[m]-.3)*1e6
 for a,trace in zip(ax,['v(out)','i(rinshunt)','i(linput)']):a.plot(x,v[trace][m],label=name,linewidth=1)
ax[0].axhline(3.6,color='r',linestyle='--');ax[0].set_ylabel('Protected voltage (V)')
ax[1].set_ylabel('Input FET current (A)');ax[2].set_ylabel('Added inductor current (A)');ax[2].set_xlabel('Time from fault (µs)')
for a in ax:a.grid(True,alpha=.3);a.legend(fontsize=8)
fig.suptitle('Imposed 1.232 µH input guard and generic return diode\nTypical models / linear inductors; no selected magnetic or survival pass')
fig.tight_layout();fig.savefig(H/'source_guard.png',dpi=150);plt.close(fig)
(H/'results.json').write_text(json.dumps(r,indent=2)+'\n')
print('Two completed sensitivity cases archived; plot generated.')
