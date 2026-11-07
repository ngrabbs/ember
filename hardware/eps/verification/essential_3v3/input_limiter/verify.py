"""Verify evidence fidelity and explicit rejection gates, not circuit acceptance."""
from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent;ROOT=H.parents[4]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
b=json.loads((H/'native_baseline.json').read_text())
for name,digest in b['files'].items():assert sha(ROOT/name)==digest,name
r=json.loads((H/'results.json').read_text())['groups'];assert len(r)==5
for group,g in r.items():
 assert len(g['cases'])==4
 for key,c in g['cases'].items():
  assert sha(H/c['archived_deck'])==c['archived_deck_sha256']
  assert sha(H/c['archived_log'])==c['normalized_log_sha256']
  log=(H/c['archived_log']).read_text();assert '/Users/nick/' not in log
  if c.get('status')=='completed' or group=='crosscheck':assert 'Total elapsed time:' in log and c['points']>10000
  if group=='early_diagnostic' or c.get('status')=='incomplete':assert c['acceptance_excluded_reason']
gear=r['late_gear']['cases'];assert all(c['status']=='completed' and c['end_s']==.34 and c['method']=='gear' for c in gear.values())
assert max(c['fault_out_max_V'] for c in gear.values())<3.4
assert max(c['input_current_peak_A'] for c in gear.values())>156
assert max(c['buck_current_peak_A'] for c in gear.values())>220
assert sum(c['status']=='completed' for c in r['late_trap']['cases'].values())==1
assert r['input_only']['cases']['high_short']['input_peak_A']>800
assert r['input_only']['cases']['low']['normal_gate_source_min_V']>10
env=json.loads((H/'envelope_results.json').read_text());half=json.loads((H/'envelope_half_step.json').read_text())
assert env['case_count']==half['case_count']==648
assert env['step_ns']==1 and half['step_ns']==.5
assert sum(c['below3p6_at_ideal_open'] for c in env['rows'])==498
for a,c in zip(env['rows'],half['rows']):
 assert a['id']==c['id'] and a['below3p6_at_ideal_open']==c['below3p6_at_ideal_open']
 assert abs(a['protected_peak_to_open_V']-c['protected_peak_to_open_V'])<.0001
for c in r['crosscheck']['cases'].values():
 assert abs(c['trip_time_difference_s'])<1e-12 and abs(c['protected_peak_difference_V'])<.00015
v=json.loads((H/'visual_review.json').read_text())
assert sha(H/'coupled_faults.png')==v['actually_opened_simulation_plot_sha256']
report={'status':'INPUT_LIMITER_UNSELECTED;FIRST_PULSE_AND_HOT_SOA_OPEN','imposed_envelope_cases':648,'solver_crosschecks':4,'input_only_completed':4,'late_gear_completed':4,'late_trap_completed':1,'early_attempts_excluded':4,'native_files_preserved':len(b['files']),'no_new_ERC_or_native_sheet_inspection':True}
(H/'verified.json').write_text(json.dumps(report,indent=2)+'\n')
manifest=H/'artifact_sha256.json'
if manifest.exists():
 for name,digest in json.loads(manifest.read_text())['files'].items():assert sha(ROOT/name)==digest,name
print(json.dumps(report,indent=2))
