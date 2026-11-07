"""Independent nodal solution of nominal loaded dividers/source impedances.

Checks the series switch resistor and ADC bleed are included. This is not a
dynamic switch/ADC, off-state equilibrium or temperature qualification model.
"""
from pathlib import Path
import json,numpy as np
H=Path(__file__).resolve().parent;r=json.loads((H/'results.json').read_text());out=[]
for c in r['channels']:
 rt=sum(c['top_resistors_ohm']);rb=c['bottom_ohm'];rs=1002.;rl=47000.
 G=np.array([[1/rt+1/rb+1/rs,-1/rs],[-1/rs,1/rs+1/rl]])
 v=np.linalg.solve(G,[1/rt,0]);z=np.linalg.solve(G,[0,1])
 assert abs(v[1]-c['gain_nominal'])<1e-12
 assert z[1]<=c['source_impedance_max_ohm']
 # Ideal switching event with precharged external capacitor; switch charge
 # injection, finite ADC pad capacitance and clamp action are not included.
 before=c['design_input_ceiling_V']*rb/(rt+rb)
 start=before*rl/(rl+rs)
 steady=c['design_input_ceiling_V']*v[1]
 pole_R=1/(1/rt+1/rb+1/(rs+rl))
 after2ms=steady+(start-steady)*np.exp(-.002/(pole_R*10e-9))
 assert abs(after2ms-steady)<3.6/8192
 out.append({'rail':c['rail'],'nodal_gain':float(v[1]),'nominal_output_impedance_ohm':float(z[1]),'nominal_enable_step_start_V':start,'nominal_2ms_residual_ADC_V':float(after2ms-steady)})
(H/'independent_results.json').write_text(json.dumps({'scope':'NOMINAL_PASSIVE_NODAL_CHECK;NOT_SWITCH_OR_ADC_QUALIFICATION','rows':out},indent=2)+'\n')
print('Four nominal nodal/settling checks agree with loaded-divider calculations.')
