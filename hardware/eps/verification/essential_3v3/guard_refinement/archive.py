"""Archive completed external experiments, rejecting known fixture mistakes.
Model/raw files stay external. Plotted CSVs interpolate; extrema use raw samples.
"""
from pathlib import Path
import argparse,csv,hashlib,json,re,subprocess,sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
H=Path(__file__).resolve().parent;ROOT=H.parents[4]
sys.path.insert(0,str(ROOT/'hardware/eps/verification/protection'))
from run_protection import read_raw
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
ap=argparse.ArgumentParser()
for k in ['initial','handover','unclamped','clamped','bank']:ap.add_argument('--'+k,type=Path,required=True)
a=ap.parse_args();args=vars(a);accepted={};diagnostic={};raws={}
(H/'decks').mkdir(exist_ok=True);(H/'logs').mkdir(exist_ok=True)
for group,run in args.items():
 source=json.loads((run/'results.json').read_text())
 for name,c0 in source['cases'].items():
  bad=group=='handover' or (group=='initial' and c0['parameters'].get('fault'))
  key=group+'__'+name;c=dict(c0);p=run/(name+'.portable.cir');log=run/(name+'.log');raw=run/(name+'.raw')
  assert c['status']=='completed' and c['returncode']==0
  assert sha(p)==c['portable_deck_sha256'] and sha(raw)==c['raw_sha256'] and sha(log)==c['log_sha256']
  t,v=read_raw(raw);assert np.isclose(t[-1],.4) and len(t)==c['points'];raws[key]=(t,v)
  text=p.read_text();(H/'decks'/(key+'.cir')).write_text(text)
  norm=log.read_text().replace('/private'+str(run),'${EXTERNAL_RUN}').replace(str(run),'${EXTERNAL_RUN}').replace(str(Path.home()/'Library/Application Support/LTspice/lib'),'${LTSPICE_LIBRARY}')
  (H/'logs'/(key+'.log')).write_text(norm);c['normalized_log_sha256']=sha(H/'logs'/(key+'.log'));c['model_hashes']=source['model_hashes']
  if bad:
   c['status']='SUPERSEDED_DIAGNOSTIC_NOT_SELECTION_EVIDENCE'
   c['reason']='TVS reversed (forward-biased positive rail)' if group=='initial' else 'Source-selector fixture also ramped good source to zero during disconnect; superseded by constant source selector.'
   diagnostic[key]=c;continue
  if c['parameters'].get('fault'):
   assert 'Dclamp 0 pin tv36' in text and not any('.30000001' in line for line in text.splitlines() if line.startswith('Vgood '))
   mask=t>=.3;vg=v['v(gate)']-v['v(common)']
   c.update(controller_gate_min_V=float(v['v(gate)'][mask].min()),common_source_min_V=float(v['v(common)'][mask].min()),Vgs_min_V=float(vg[mask].min()),Vgs_max_V=float(vg[mask].max()))
   if 'i(lfailed)' in v:c['failed_buck_inductor_peak_abs_A']=float(abs(v['i(lfailed)'][mask]).max())
   if 'i(dgate)' in v:c['negative_gate_clamp_peak_A']=float(v['i(dgate)'][mask].max())
  # Port power includes capacitive/storage power; positive integral is not heat/SOA proof.
  if 'i(vd1)' in v:
   powers=[(v['v(pin)']-v['v(common)'])*v['i(vd1)'],(v['v(out)']+.015*v['i(rsense)']-v['v(common)'])*(-v['i(vd2)'])]
   c['MOS_terminal_power_screen']={}
   for phase,mask in [('startup',t<.25),('fault',(t>=.3)&(t<=.301))]:
    if phase=='fault' and not c['parameters'].get('fault'):continue
    c['MOS_terminal_power_screen'][phase]=[{'peak_positive_W':float(pw[mask].max()),'positive_port_energy_J':float(np.trapezoid(np.maximum(pw[mask],0),t[mask]))} for pw in powers]
  accepted[key]=c
report={'scope':'DEVELOPMENT_FILTER_AND_GATE_CLAMP_DIRECTION;NO_SELECTED_CIRCUIT_OR_PVT/SOA_ACCEPTANCE','current_completed_experiments':len(accepted),'superseded_diagnostics':len(diagnostic),'cases':accepted,'diagnostics':diagnostic}
(H/'results.json').write_text(json.dumps(report,indent=2)+'\n')
# Independent linear sanity comparison; Rpath is fitted nominal, not guaranteed RDS.
lin=json.loads((H/'linear_results.json').read_text());mapping=['base10_192','guard4p7_192','guard2p2_192','guard4p7_384','guard2p2_384','base10_768','damped10_192']
for row,name in zip(lin['rows'],mapping):
 row['connected_min_V']=accepted['initial__'+name]['normal_step_min_V'];row['difference_V']=row['connected_min_V']-row['linear_min_V'];assert abs(row['difference_V'])<.001
(H/'linear_comparison.json').write_text(json.dumps(lin,indent=2)+'\n')
# Actual trace plots; no manufacturer schematic/source-page inspection claim.
fig,axes=plt.subplots(2,1,figsize=(10,7),sharex=True);plotrows=[]
for key,label in [('initial__base10_192','10 µH / 192 µF'),('initial__guard2p2_384','2.2 µH / 384 µF'),('clamped__bulk2p2_640','2.2 µH / 640 µF / 9 mΩ guard'),('bank__bulk640_esr_hot','2.64 µH / 640 µF / 85 °C sensitivity')]:
 t,v=raws[key];x=(t-.25)*1000;axes[0].plot(x,v['v(out)'],label=label);axes[1].plot(x,v['i(rsense)'])
 for tm in np.linspace(.2499,.251,1501):plotrows.append([key,f'{tm:.9g}',f'{np.interp(tm,t,v["v(out)"]):.9g}',f'{np.interp(tm,t,v["i(rsense)"]):.9g}'])
axes[0].axhline(3,color='red',linestyle='--');axes[0].set_ylabel('Protected output (V)');axes[0].set_ylim(2.65,3.35);axes[0].legend(fontsize=9)
axes[1].set_ylabel('Shunt current (A)');axes[1].set_xlabel('Time relative to 0.2 → 2 A step (ms)');axes[1].set_xlim(-.1,1)
for ax in axes:ax.grid(alpha=.25)
fig.suptitle('Guard / protected-bank refinement\nUnmodified typical semiconductor models; imposed passive/source values');fig.tight_layout();fig.savefig(H/'load_comparison.png',dpi=150)
with (H/'load_plot.csv').open('w',newline='') as f:w=csv.writer(f,lineterminator='\n');w.writerow(['case','time_s','output_V','shunt_A']);w.writerows(plotrows)
fig,axes=plt.subplots(3,1,figsize=(10,9),sharex=True);plotrows=[]
for key,label in [('unclamped__fault_guard4p7_384','No negative-gate clamp'),('clamped__fault_guard4p7_384_clamped','Imposed negative-gate diode clamp')]:
 t,v=raws[key];x=(t-.3)*1e6;ys=[v['v(gate)'],v['v(pin)']-v['v(common)'],v['v(out)']]
 for ax,y in zip(axes,ys):ax.plot(x,y,label=label)
 for tm in np.linspace(.299999,.30002,2501):plotrows.append([key,f'{tm:.10g}',*[f'{np.interp(tm,t,y):.9g}' for y in ys]])
axes[0].axhline(-40,color='red',linestyle='--');axes[0].set_ylabel('Controller GATE (V)');axes[0].legend(fontsize=9)
axes[1].axhline(60,color='red',linestyle='--');axes[1].set_ylabel('Q1 drain − source (V)')
axes[2].set_ylabel('Protected output (V)');axes[2].set_xlabel('Time relative to imposed fault (µs)');axes[2].set_xlim(-1,20)
for ax in axes:ax.grid(alpha=.25)
fig.suptitle('Same 4.7 µH / 384 µF fault fixture: gate-clamp sensitivity\nFinite 650 µF / 35 V reservoir; synthetic TVS; not component qualification');fig.tight_layout();fig.savefig(H/'gate_clamp_comparison.png',dpi=150)
with (H/'fault_plot.csv').open('w',newline='') as f:w=csv.writer(f,lineterminator='\n');w.writerow(['case','time_s','gate_V','Q1_Vds_V','output_V']);w.writerows(plotrows)
# Every previously tracked native source/table is checked against this turn's Git basis.
paths=subprocess.check_output(['git','ls-files'],cwd=ROOT,text=True).splitlines();native=[p for p in paths if Path(p).suffix in {'.kicad_sch','.kicad_pcb','.kicad_pro','.kicad_sym','.kicad_mod'} or Path(p).name in ['sym-lib-table','fp-lib-table']]
base={}
for p in native:
 old=subprocess.check_output(['git','show','490721c:'+p],cwd=ROOT);assert old==(ROOT/p).read_bytes(),p;base[p]=hashlib.sha256(old).hexdigest()
(H/'native_baseline.json').write_text(json.dumps({'basis':'490721c','files':base},indent=2)+'\n')
print('Archived',len(accepted),'current experiments and',len(diagnostic),'superseded diagnostics;',len(base),'native files unchanged')
for key in ['clamped__fault_bulk2p2_640_clamped','bank__fault_bulk640_repeat']:print(key,json.dumps(accepted[key]))
