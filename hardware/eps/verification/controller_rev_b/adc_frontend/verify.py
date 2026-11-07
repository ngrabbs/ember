"""Check the conditional passive screen and independent solution bindings."""
from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent;ROOT=H.parents[4]
r=json.loads((H/'results.json').read_text());ind=json.loads((H/'independent_results.json').read_text())
assert len(r['channels'])==len(ind['rows'])==4
assert [c['MCU_pin'] for c in r['channels']]==[7,8,11,12]
for c,d in zip(r['channels'],ind['rows']):
 assert c['rail']==d['rail']
 assert abs(c['gain_nominal']-d['nodal_gain'])<1e-12
 assert c['source_impedance_max_ohm']<15000
 assert c['open_switch_divider_ceiling_V']<3.6
 assert c['ideal_switch_enable_charged_filter_ADC_max_V']<2.857
 assert c['filter_half_LSB_full_step_settling_s_sensitivity']<.002
 assert abs(d['nominal_2ms_residual_ADC_V'])<3.6/8192
assert r['switch_power_off_leakage_2uA_into47k_V']<.095
assert r['not_included'] and r['scope'].startswith('CONDITIONAL')
report={'status':'CONDITIONAL_PASSIVE_ADC_SCREEN_AGREES;REFERENCE_BROWNOUT_AND_HARDWARE_GATES_OPEN','channels':4,'native_integration_authority':'Separate rev_b/adc_integration packet; no native-state claim here'}
(H/'verified.json').write_text(json.dumps(report,indent=2)+'\n')
if (H/'artifact_sha256.json').exists():
 for n,d in json.loads((H/'artifact_sha256.json').read_text())['files'].items():assert hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==d,n
print(json.dumps(report,indent=2))
