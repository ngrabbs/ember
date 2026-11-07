#!/usr/bin/env python3
"""Render development waveforms from the recorded external scratch directory."""
import argparse,sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from run_protection import read_raw
p=argparse.ArgumentParser();p.add_argument('--rail-work',type=Path,required=True);p.add_argument('--source-work',type=Path,required=True);a=p.parse_args()
fig,axes=plt.subplots(3,1,figsize=(9,9),layout='constrained')
for name,label in [('accepted_release_min_-40','Cold, minimum protected bank'),('accepted_release_max_-40','Cold, high protected bank')]:
 t,v=read_raw(a.rail_work/(name+'.raw'));m=(t>=.0795)&(t<=.18)
 axes[0].plot((t[m]-.08)*1000,v['v(output)'][m],label=label)
 axes[1].plot((t[m]-.08)*1000,v['v(tmr)'][m],label=label)
axes[0].set(ylabel='Protected output (V)',xlabel='Time since load release (ms)',ylim=(4.7,5.55));axes[0].axhline(5.5,color='crimson',ls=':',label='Provisional peak ceiling')
axes[1].set(ylabel='Timer (V)',xlabel='Time since load release (ms)',ylim=(-.05,1.45));axes[1].axhline(1.22,color='crimson',ls=':',label='Cited minimum fault-warning threshold')
for name,label in [('src10_hard_input_short','Rejected source without L2'),('guard_src10_hard_input_short','Revised source with L2')]:
 t,v=read_raw(a.source_work/(name+'.raw'));m=(t>=.1199998)&(t<=.120005)
 axes[2].plot((t[m]-.12)*1e6,(v['v(gh)']-v['v(sp)'])[m],label=label)
axes[2].set(ylabel='Internal pass VGS (V)',xlabel='Time since hard input short (µs)',ylim=(-1,22));axes[2].axhline(16,color='crimson',ls=':',label='MOSFET absolute gate limit')
for ax in axes:ax.legend(loc='best',fontsize=8);ax.grid(alpha=.25)
fig.suptitle('Recovery corrections — stated typical-model sensitivities\nNot bench evidence or hot-SOA qualification')
fig.savefig(HERE/'evidence/waveforms.png',dpi=160)
