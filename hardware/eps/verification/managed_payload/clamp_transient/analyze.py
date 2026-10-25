#!/usr/bin/env python3
"""Collect completed raw traces; no simulator launches and no native CAD writes."""
from pathlib import Path
import hashlib,json,importlib.util,zipfile
import numpy as np
H=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('clamp_run',H/'run.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rs=json.loads((H/'results.json').read_text());assert len(rs)==24
metrics=[];plotdata={}
for r in rs:
 p=H/'decks'/(r['name']+'.cir')
 assert r['status']=='COMPLETED_IMPOSED_SUBCIRCUIT_CASE'
 for ext,key in [('.cir','deck_sha256'),('.log','log_sha256'),('.raw','raw_sha256')]:assert sha(p.with_suffix(ext))==r[key]
 t,v=m.raw_reader.read_raw(p.with_suffix('.raw'));ovp=v['v(ovp)'];assert abs(t[-1]-.002)<1e-12
 crossings={}
 for threshold in [1.176,1.224]:
  ix=np.flatnonzero((t>=.001)&(ovp>=threshold));assert len(ix)
  crossings[str(threshold)]=float((t[ix[0]]-.001)*1e6)
 metrics.append(dict(name=r['name'],OVP_peak_V=float(ovp.max()),OVP_min_V=float(ovp.min()),first_threshold_crossing_after_step_us=crossings))
 if r['vf_V']==1.2 and ((r['source']=='warm_step' and r['temperature_C']==85) or (r['source']=='cold_start' and r['temperature_C']==-40)):
  plotdata[(r['source'],r['cap_F'])]=(t,ovp,v['v(ref)'])
model=H/'models/LM4040_NC2P5_TRANS.lib';lines=model.read_text().splitlines();active=[l.strip() for l in lines if l.strip() and not l.lstrip().startswith('*')]
assert not any(l.lower().startswith('m') and 'menable' in l.lower() for l in active)
summary=dict(status='COMPLETED_NOMINAL_SUBCIRCUIT_SENSITIVITY_ONLY',completed_cases=24,
 peak_without_filter_V=max(r['ovp_peak_V'] for r in rs if r['cap_F']==0),peak_with_1nF_V=max(r['ovp_peak_V'] for r in rs if r['cap_F']>0),
 global_minimum_OVP_V=min(r['ovp_min_V'] for r in rs),reference_peak_V=max(r['reference_peak_V'] for r in rs),reference_bias_abs_peak_A=max(r['reference_bias_current_abs_peak_A'] for r in rs),
 full_0_to_4V_operating_screen_passes=sum(r['OVP4V_operating_screen'] for r in rs),absolute_minus0p3_to5p5V_screen_passes=sum(r['OVP_absolute_screen'] for r in rs),
 model_sha256=sha(model),simulator='LTspice 26.0.2',model_source='https://www.ti.com/lit/zip/SNOM541',model_revision='10APR2013 Final 1.00; PSPICE16 transient; TOL=0',
 compatibility_warnings='PBSW, UCRIT, DIOMOD ignored in unused Menable declaration; no M instance uses it. Original model and warnings retained. Not vendor-certified LTspice/PVT validation.',
 diode_model='Imposed instantaneous forward envelope plus capacitance; NOT a BAS116H manufacturer model',physical_or_PVT_acceptance=False,threshold_metrics=metrics)
archive=Path('/tmp/ember-lm4040-snom541.zip')
if archive.exists():
 with zipfile.ZipFile(archive) as z:
  names=[n for n in z.namelist() if n.endswith('LM4040_NC2P5_TRANS.lib')];assert len(names)==1
  assert z.read(names[0])==model.read_bytes();summary['download_zip_sha256']=sha(archive);summary['zip_member']=names[0];summary['unmodified_zip_member_verified']=True
(H/'analysis.json').write_text(json.dumps(summary,indent=2)+'\n')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig,axs=plt.subplots(2,2,figsize=(12,7),layout='constrained')
for row,source in enumerate(['warm_step','cold_start']):
 for cap in [0,1e-9]:
  t,ovp,ref=plotdata[(source,cap)];label='no added filter' if cap==0 else '1 nF filter'
  for col,edge in enumerate([.001,.0015]):
   mask=(t>=edge-1e-7)&(t<=edge+10e-6)
   axs[row,col].plot((t[mask]-edge)*1e6,ovp[mask],label=label,linewidth=1.2)
 for col in range(2):
  ax=axs[row,col];ax.axhline(4,color='red',ls='--',lw=1,label='4 V operating upper limit');ax.set(xlabel='Time from source edge (µs)',ylabel='OVP pin (V)',title=f'{source}, {85 if row==0 else -40} °C; '+('rise to 35 V' if col==0 else 'return to initial source'))
  ax.grid(alpha=.25);ax.legend(fontsize=8)
fig.suptitle('LM4040 nominal macro + imposed diode VF = 1.2 V\nSensitivity study only; no TPS2663/MOSFET survival or full-temperature guarantee',fontsize=12)
fig.savefig(H/'clamp_edges.png',dpi=160);fig.savefig(H/'clamp_edges.pdf');plt.close(fig)
print(json.dumps({k:v for k,v in summary.items() if k!='threshold_metrics'},indent=2))
