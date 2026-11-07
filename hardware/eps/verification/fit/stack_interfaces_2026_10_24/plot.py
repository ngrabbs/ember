#!/usr/bin/env python3
"""Illustrative geometry, from saved Konnect measurements and stated height assumptions."""
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
HERE=Path(__file__).resolve().parent
r=json.loads((HERE/'results.json').read_text())
fig,(a,b)=plt.subplots(1,2,figsize=(11,7),gridspec_kw={'width_ratios':[1,2]},layout='constrained')
for h in ['H1','H2']:
 rows=[p for p in r['pads'] if p['header']==h]
 a.scatter([p['eps_xy_mm'][0] for p in rows],[p['eps_xy_mm'][1] for p in rows],s=16,c='#777777')
 for n in ([1,51] if h=='H1' else [2,52]):
  p=next(p for p in rows if p['pin']==n);x,y=p['eps_xy_mm']
  a.annotate(str(n),(x,y),xytext=((5 if h=='H1' else -5),0),ha=('left' if h=='H1' else 'right'),textcoords='offset points',fontsize=8)
 center=r['centers_board_xy_mm']['eps'][h]
 a.text(center['x'],140,h,ha='center',fontsize=11)
for h,nums,color,label in [('H1',[1,2,3,4],'#d35c38','Actual COMMS CAN'),('H1',[51,52],'#19857b','Canonical CAN A'),('H2',[49,50],'#4177b9','Canonical CAN B')]:
 rows=[p for p in r['pads'] if p['header']==h and p['pin'] in nums]
 a.scatter([p['eps_xy_mm'][0] for p in rows],[p['eps_xy_mm'][1] for p in rows],s=55,c=color,label=label)
a.set(aspect='equal',xlim=(102.5,116.5),ylim=(142,68),xlabel='Saved board X (mm)',ylabel='Saved board Y (mm)',title='All 104 EPS/COMMS pads match XY\n5.08 mm between header centers')
a.legend(loc='upper center',bbox_to_anchor=(.5,-.08),fontsize=9)
# Top-mounted endpoint/stackthrough hypothesis. The upperPCB thickness is assumed.
b.add_patch(Rectangle((-2,-1.6),9,1.6,color='#bac8a7'))
b.add_patch(Rectangle((-2,16),9,1.6,color='#bac8a7'))
b.add_patch(Rectangle((0,0),4.95,11.05,fill=False,edgecolor='#444444',lw=2))
b.plot([2.475,2.475],[5.41,17.6],color='#c08d28',lw=5)
b.text(5.1,-.8,'EPS PCB',va='center');b.text(5.1,16.8,'Upper PCB, assumed 1.6 mm',va='center')
b.text(5.1,9.2,'Lower socket\n11.05 mm nominal',va='center')
b.annotate('',xy=(-1,0),xytext=(-1,16),arrowprops={'arrowstyle':'<->','lw':1.5,'color':'#31658b'})
b.text(-1.3,8,'Confirmed 16 mm clear gap',ha='right',va='center',rotation=90,color='#31658b')
b.annotate('',xy=(3.6,5.41),xytext=(3.6,11.05),arrowprops={'arrowstyle':'<->','lw':1.5,'color':'#19857b'})
b.text(3.9,5.0,'5.64 mm nominal insertion',va='top',color='#19857b')
b.text(.2,18.4,'Upper −39 tail: 12.19 mm below its seating face',fontsize=10)
b.set(xlim=(-3.5,14),ylim=(-3,20),ylabel='Height from EPS top (mm)',title='Mating-depth hypothesis, not tolerance acceptance')
b.set_xticks([]);b.grid(axis='y',alpha=.2)
b.text(-2,-2.5,'Top-side socket assumption; assembly side and exact tolerances remain open.',fontsize=9)
fig.suptitle('EMBER Rev B stack decisions: preserve existing spacing and 16 mm clear gap\nMechanical correspondence does not establish electrical CAN compatibility',fontsize=12)
fig.savefig(HERE/'stack_reconciliation.png',dpi=170)
