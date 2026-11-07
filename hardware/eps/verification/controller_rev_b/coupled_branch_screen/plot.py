"""Plot complete hash-checked external raw waveforms; requires matplotlib/numpy."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]/'protection'))
from run_protection import read_raw

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--raw-dir',type=Path,required=True)
args = parser.parse_args()
result = json.loads((HERE/'results.json').read_text())
fig, axes = plt.subplots(4,1,figsize=(11,12),layout='constrained')
for case in result['cases']:
    assert case['status'] == 'COMPLETED'
    raw = args.raw_dir/(case['name']+'.raw')
    assert hashlib.sha256(raw.read_bytes()).hexdigest() == case['raw_sha256']
    t, values = read_raw(raw)
    window = (t>=.010)&(t<=.030)
    # These readbacks also allow the earlier run to gain the same fields without rerunning SPICE.
    case['source_resistor_current_peak_during_fault_A'] = float(values['i(rsource)'][window].max())
    case['fault_input_cap_min_during_fault_V'] = float(values['v(ina)'][window].min())
    if case['name'].endswith('90mA'):
        label = case['name'].replace('_90mA','')
        for axis,key in zip(axes,['v(shared)','v(railb)','v(ina)','i(vmona)']):
            axis.plot((t-.010)*1e6,values[key],label=label)
for axis,ylabel in zip(axes,['Shared supply (V)','Healthy B supply (V)',
                            'Faulted TPS input (V)','Faulted TPS input current (A)']):
    axis.set_xlim(-1,15)
    axis.set_xlabel('Time after A short (us)')
    axis.set_ylabel(ylabel)
    axis.grid(alpha=.25)
    axis.legend()
for axis in axes[:2]:
    axis.axhline(3,ls=':',c='gray')
axes[0].set_ylim(2.85,3.25)
axes[1].set_ylim(3,3.2)
axes[2].axhline(2.5,ls=':',c='gray')
fig.suptitle('CAN A short with B loaded at 90 mA: nominal external TPS model\n'
             'Synthetic 3.232799 V / 50 mOhm source, 96 uF shared; 25 C; qualification open')
fig.savefig(HERE/'fault_comparison_90mA.png',dpi=150)
plt.close(fig)
(HERE/'results.json').write_text(json.dumps(result,indent=2)+'\n')
