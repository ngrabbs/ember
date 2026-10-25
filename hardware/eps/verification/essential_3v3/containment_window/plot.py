from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
H=Path(__file__).resolve().parent
s=json.loads((H/'results.json').read_text());r=json.loads((H/'staged_results.json').read_text())
fig,ax=plt.subplots(2,2,figsize=(12,8),constrained_layout=True)
for L in [3.136,5,10,22,47,100]:
 q=[x for x in s['rows'] if x['L_effective_uH']==L and x['C_effective_uF']==96 and x['series_R_ohm']==0]
 ax[0,0].plot([x['imposed_total_delay_us'] for x in q],[x['output_at_open_V'] for x in q],marker='.',label=f'{L:g} µH')
ax[0,0].set(xlim=(0,10),ylim=(3.25,5.3),xlabel='Total delay from stiff source step (µs)',ylabel='Protected output at opening (V)',title='A. Direct 35 V step; ideal 96 µF bank')
ax[0,0].axhline(3.6,color='firebrick',linestyle='--');ax[0,0].legend(ncol=2,fontsize=8)
for L in [1,5,10,22]:
 q=[x for x in r['rows'] if x['buck_effective_L_uH']==.5 and x['guard_effective_L_uH']==L and x['post_effective_C_uF']==96 and x['constant_load_A']==0]
 ax[0,1].plot([x['imposed_total_opening_delay_us'] for x in q],[x['protected_output_at_open_V'] for x in q],marker='.',label=f'{L:g} µH guard')
ax[0,1].set(xlabel='Delay after raw-rail threshold (µs)',ylabel='Protected output at opening (V)',title='B. Two filters; 0.5 µH buck sensitivity')
ax[0,1].axhline(3.6,color='firebrick',linestyle='--');ax[0,1].legend(fontsize=8)
for Lb in [.5,3.136]:
 q=[x for x in r['rows'] if x['buck_effective_L_uH']==Lb and x['guard_effective_L_uH']==10 and x['post_effective_C_uF']==96 and x['constant_load_A']==0]
 ax[1,0].plot([x['imposed_total_opening_delay_us'] for x in q],[x['buck_current_at_open_A'] for x in q],marker='.',label=f'{Lb:g} µH buck')
ax[1,0].set(xlabel='Delay after threshold (µs)',ylabel='Buck inductor current at opening (A)',title='C. Stiff-source current exposes magnetic gap')
ax[1,0].axhline(9.9,color='firebrick',linestyle='--',label='9.9 A typical 30% L-drop reference');ax[1,0].legend(fontsize=8)
for L in [1,5,10,22]:
 q=[x for x in r['rows'] if x['buck_effective_L_uH']==.5 and x['guard_effective_L_uH']==L and x['post_effective_C_uF']==96 and x['constant_load_A']==0]
 ax[1,1].plot([x['imposed_total_opening_delay_us'] for x in q],[x['guard_stored_energy_at_open_J']*1e3 for x in q],marker='.',label=f'{L:g} µH guard')
ax[1,1].set(xlabel='Delay after threshold (µs)',ylabel='Guard stored energy at opening (mJ)',title='D. Turn-off energy still needs a real clamp');ax[1,1].legend(fontsize=8)
for a in ax.flat:a.grid(alpha=.25)
fig.suptitle('Essential 3.3 V containment — imposed linear-model sensitivities\nNo controller, saturation, clamp, SOA or hardware qualification',fontsize=13)
fig.savefig(H/'containment_window.png',dpi=170);fig.savefig(H/'containment_window.pdf')
