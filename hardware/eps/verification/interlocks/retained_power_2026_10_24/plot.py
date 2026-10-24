#!/usr/bin/env python3
"""Plot archived interpolated samples; full-resolution extrema live in results.json."""
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
HERE=Path(__file__).resolve().parent
fig,ax=plt.subplots(2,2,figsize=(12,8),layout='constrained')
for suffix,color in [('baseline','#984ea3'),('bleed','#167d9a')]:
 d=np.genfromtxt(HERE/'samples'/f'staged_forward_{suffix}.csv',delimiter=',',names=True,deletechars='')
 t=d['time_s'];label='100 kΩ source + bias bleeds' if suffix=='bleed' else 'Prior fixture, no added bleeds'
 ax[0,0].plot(t*1000,d['v(sys)'],color=color,label=label)
 ax[0,1].plot(t*1000,d['v(gate)']-d['v(cs)'],color=color,label=label)
 mask=t>=.5
 ax[1,0].semilogy(t[mask]*1000,np.maximum(d['v(cs)'][mask],1e-8),color=color,label='Common source, '+suffix)
 ax[1,0].semilogy(t[mask]*1000,np.maximum(d['v(bias)'][mask],1e-8),color=color,ls='--',label='Controller bias, '+suffix)
 power=np.maximum((d['v(a)']-d['v(cs)'])*d['id(m1)'],0)
 ax[1,1].plot(t*1000,power,color=color,label=label)
for a in ax.flat:a.grid(alpha=.25);a.set_xlabel('Time (ms)')
ax[0,0].set(title='Two capacitor stages, 10 Ω system load',ylabel='System voltage (V)',xlim=(0,800))
ax[0,0].legend(fontsize=8)
ax[0,1].set(title='Actual modeled gate-to-source voltage',ylabel='VGS (V)',xlim=(0,800))
ax[1,0].set(title='Discharge after permission opens at 500.1 ms',ylabel='Residual voltage (V)',xlim=(500,800))
ax[1,0].legend(fontsize=8)
ax[1,1].set(title='M1 positive dissipation during startup',ylabel='Power (W)',xlim=(40,160))
fig.suptitle('Experimental RBF cutoff: 8.526 V, 27 °C model, 22 µF + 163.77 µF\nResistive BATFET proxy; not charger startup, leakage limits or MOSFET SOA acceptance',fontsize=12)
fig.savefig(HERE/'boundary_screen.png',dpi=160)
