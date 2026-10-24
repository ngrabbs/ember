"""Exact linear RLC necessary-condition screen; no controller or hardware proof."""
from pathlib import Path
import csv,hashlib,itertools,json,math,xml.etree.ElementTree as E
H=Path(__file__).resolve().parent;ROOT=H.parents[4]
P=ROOT/'hardware/eps/verification/controller_rev_b/swd_root_review/root.xml'
r=E.parse(P).getroot();cs={c.get('ref'):c for c in r.findall('./components/comp')}
caprefs=[f'C{i}' for i in range(404,412)]
for ref in caprefs:
 f={x.get('name'):x.text for x in cs[ref].findall('fields/field')}
 assert f['MFG P/N']=='GRM32ER71E226KE15L'
 assert '25' in f['Voltage']
static=json.loads((ROOT/'hardware/eps/verification/essential_3v3/analysis/screening.json').read_text())
# Existing screen varies its JSON keys; use the raw corner list, never an invented bound.
def collect(x):
 if isinstance(x,dict):
  for k,v in x.items():
   if k=='vout_V':yield float(v)
   else:yield from collect(v)
 elif isinstance(x,list):
  for v in x:yield from collect(v)
vals=list(collect(static))
assert vals, "Missing authoritative vout_V corners"
V0=max(vals)
# Explicit source bound in the current design; instantaneous stiff step is an imposed test.
VF=35.0;CEILING=3.6

def voltage(t,L,C,R,load=0):
 a=R/(2*L);w2=1/(L*C)-a*a;assert w2>0
 w=math.sqrt(w2);vf=VF-load*R;A=V0-vf
 return vf+math.exp(-a*t)*(A*math.cos(w*t)+(a*A/w)*math.sin(w*t))

def critical_delay(L,C,R):
 w=math.sqrt(1/(L*C)-(R/(2*L))**2);lo=0.;hi=math.pi/w
 assert voltage(hi,L,C,R)>CEILING
 for _ in range(80):
  mid=(lo+hi)/2
  if voltage(mid,L,C,R)<CEILING:lo=mid
  else:hi=mid
 return (lo+hi)/2
rows=[]
for Lu,Cu,R in itertools.product([3.136,5,10,22,47,100],[48,96,192,480],[0,.05,.15]):
 L=Lu*1e-6;C=Cu*1e-6;crit=critical_delay(L,C,R)
 for us in [.5,1,2,4,6,10,20]:
  t=us*1e-6;v=voltage(t,L,C,R)
  # Independent undamped closed form, and nonnegative fault current before first peak.
  if R==0:assert abs(v-(V0+(VF-V0)*(1-math.cos(t/math.sqrt(L*C)))))<1e-12
  rows.append({'L_effective_uH':Lu,'C_effective_uF':Cu,'series_R_ohm':R,'imposed_total_delay_us':us,'output_at_open_V':v,'below_3p6_in_ideal_screen':v<=CEILING,'time_to_3p6_us':crit*1e6})
# Fundamental charge budget, independent of a controller model.
q={str(Cu):Cu*1e-6*(CEILING-V0) for Cu in [48,96,192,480]}
# LTC4365 .5V +/-1.5%; TNPW independent .1% +25ppm/K*65K.
e=.001+25e-6*65
thresholds=[]
for top in [58.8e3,60.4e3]:
 trip=[vr*(1+rt/rb)+ileak*rt for vr,rt,rb,ileak in itertools.product([.4925,.5075],[top*(1-e),top*(1+e)],[1e4*(1-e),1e4*(1+e)],[-1e-8,1e-8])]
 ovpin=VF/(1+top*(1-e)/(1e4*(1+e)))
 thresholds.append({'top_ohm':top,'bottom_ohm':10000,'trip_min_V':min(trip),'trip_max_V':max(trip),'OV_pin_at_35V_ratio_corner_V':ovpin,'OV_pin_within_5V_absolute_limit':ovpin<=5,'static_margin_above_normal_max_V':min(trip)-V0,'remaining_static_margin_to_3p6_V':CEILING-max(trip)})
# Ideal low-loss bound; use gate-drive-qualified Rds only in a selected circuit.
loss=[]
for pairR in [.0182,.054,.108]:
 total=pairR+.02+.01
 loss.append({'assumed_pair_R_ohm':pairR,'other_series_R_ohm':.03,'at_2A_drop_V':2*total,'protected_static_low_V':3.2328-2*total})
result={'status':'NECESSARY_CONDITION_SCREEN_NOT_CIRCUIT_ACCEPTANCE','source_netlist_sha256':hashlib.sha256(P.read_bytes()).hexdigest(),'normal_upper_V':V0,'imposed_fault_V':VF,'design_ceiling_V':CEILING,'native_25V_capacitors_exposed_without_barrier_bank_revision':caprefs,'native_output_bank_nominal_uF':176,'inductor_references_are_effective_requirements_not_selected_parts':True,'rows':rows,'available_charge_C':q,'LTC4365_divider_screen':thresholds,'conditional_2A_drop_screen':loss,'limits':['Instantaneous stiff fault source is an imposed sensitivity, not a full LMR51635 failure model.','Zero-ESR lumped output capacitance, fixed effective inductance, ideal switch opens instantaneously at total imposed delay.','No stray feedthrough, clamp, gate dynamics, saturation, startup, SOA, control-loop stability or actual consumer acceptance.','3.6V is a working normal-operation ceiling, not an assertion of a common absolute maximum.','L before the disconnect requires a separate upstream energy/clamp path; its energy is not silently transferred to the protected output.','Capacitance values are imposed effective values, not a qualified new capacitor bank.']}
(H/'results.json').write_text(json.dumps(result,indent=2)+'\n')
with (H/'delay_sweep.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
print(json.dumps({k:v for k,v in result.items() if k not in ['rows','limits']},indent=2))
