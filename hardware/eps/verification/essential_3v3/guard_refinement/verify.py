"""Check archived experiment fidelity; no claim of circuit acceptance."""
from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent;ROOT=H.parents[4]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
b=json.loads((H/'native_baseline.json').read_text())
for name,digest in b['files'].items():assert sha(ROOT/name)==digest,name
r=json.loads((H/'results.json').read_text());assert r['current_completed_experiments']==len(r['cases'])==22
assert r['superseded_diagnostics']==len(r['diagnostics'])==8
for key,c in (r['cases']|r['diagnostics']).items():
 assert c['returncode']==0 and c['end_s']==.4 and c['points']>200000
 assert sha(H/'decks'/(key+'.cir'))==c['portable_deck_sha256']
 assert sha(H/'logs'/(key+'.log'))==c['normalized_log_sha256']
 log=(H/'logs'/(key+'.log')).read_text();assert 'Total elapsed time:' in log and '/Users/nick/' not in log
 assert c['model_hashes']['TI_model_sha256']=='fa4ef72177bc7691b956ef047985e6fc0a490ae1e12d41295c787e6e51dba170'
 assert c['model_hashes']['controller_sha256']=='d02c1dc157882e68619668ee8b843971984874514a0bb07bf5e0f9f4ebe3410f'
for key,c in r['cases'].items():
 assert c['status']=='completed'
 d=(H/'decks'/(key+'.cir')).read_text();p=c['parameters']
 if p.get('fault'):
  assert 'Dclamp 0 pin tv36' in d
  good=[line for line in d.splitlines() if line.startswith('Vgood ')];assert len(good)==1 and '.30000001' not in good[0]
  if p.get('gate_clamp'):
   assert 'Dgate 0 gate gate_negative_clamp' in d and c['controller_gate_min_V']>-2 and c['Q1_Vds_abs_max_V']<50
  else:assert c['controller_gate_min_V']< -40 and c['Q1_Vds_abs_max_V']>60
for c in r['diagnostics'].values():assert c['status']=='SUPERSEDED_DIAGNOSTIC_NOT_SELECTION_EVIDENCE' and c['reason']
base=r['cases']['clamped__fault_bulk2p2_640_clamped'];repeat=r['cases']['bank__fault_bulk640_repeat']
assert abs(base['fault_out_max_V']-repeat['fault_out_max_V'])<1e-6
assert abs(base['Q1_Vds_abs_max_V']-repeat['Q1_Vds_abs_max_V'])<.02
assert repeat['failed_buck_inductor_peak_abs_A']>300
assert .01<repeat['negative_gate_clamp_peak_A']<.05
linear=json.loads((H/'linear_comparison.json').read_text());assert len(linear['rows'])==7
assert max(abs(c['difference_V']) for c in linear['rows'])<.001
assert max(c['rk4_matrix_exp_max_state_difference'] for c in linear['rows'])<1e-7
visual=json.loads((H/'visual_review.json').read_text())
for name,digest in visual['actually_opened_simulation_plots'].items():assert sha(H/name)==digest
report={'status':'PROMISING_FILTER_DIRECTION;UPSTREAM_CURRENT_LIMIT_AND_COMPONENT/TIMING/SOA_GATES_OPEN','current_completed_experiments':22,'superseded_diagnostics_excluded':8,'native_files_byte_preserved':len(b['files']),'nominal_low_rail_min_V':r['cases']['clamped__bulk2p2_640']['normal_step_min_V'],'85C_esr_sensitivity_min_V':r['cases']['bank__bulk640_esr_hot']['normal_step_min_V'],'failed_buck_inductor_imposed_model_peak_A':repeat['failed_buck_inductor_peak_abs_A'],'source_current_is_not_physically_qualified':True,'no_native_circuit_or_PCB_changes':True,'simulation_plot_inspection_separate_from_schematic_and_source_page_review':True}
(H/'verified.json').write_text(json.dumps(report,indent=2)+'\n')
manifest=H/'artifact_sha256.json'
if manifest.exists():
 for name,digest in json.loads(manifest.read_text())['files'].items():assert sha(ROOT/name)==digest,name
print(json.dumps(report,indent=2))
