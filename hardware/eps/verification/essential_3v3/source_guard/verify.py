"""Check archived sensitivity fidelity; no native or hardware release claim."""
from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent;ROOT=H.parents[4]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((H/'results.json').read_text());assert len(r['cases'])==2
assert r['hashes']=={'LTC4231-2':'d8bfe32153eda3edb581a11ef1df10614bb681e6a738b458fe79b9069d6ac470','LTC4368-1':'d02c1dc157882e68619668ee8b843971984874514a0bb07bf5e0f9f4ebe3410f','TI_CSD18543':'fa4ef72177bc7691b956ef047985e6fc0a490ae1e12d41295c787e6e51dba170'}
for name,c in r['cases'].items():
 assert c['status']=='completed' and c['returncode']==0 and c['end_s']==.34
 assert c['points']>700000
 assert sha(H/'decks'/(name+'.cir'))==c['portable_deck_sha256']
 assert sha(H/'logs'/(name+'.log'))==c['normalized_log_sha256']
 d=(H/'decks'/(name+'.cir')).read_text();log=(H/'logs'/(name+'.log')).read_text()
 assert 'Linput bulk in 1.232u Rser=.01' in d and 'Dreturn in bulk input_return' in d
 assert 'Ccontroller in 0 100n' in d and 'Cin ips 0 5.6925u' in d
 assert 'Total elapsed time:' in log and '/Users/nick/' not in log
 assert c['fault_out_max_V']<3.4 and c['input_current_peak_A']<60
 assert c['source_inductor_peak_A']>60 and c['input_pin_max_V']>36
 assert c['input_FET_positive_port_energy_first_ms_J']>.02
v=json.loads((H/'visual_review.json').read_text());assert sha(H/'source_guard.png')==v['actually_opened_plot_sha256']
report={'status':'SOURCE_GUARD_UNSELECTED;MAGNETIC_CURRENT_CONTROLLER_RANGE_AND_HOT_SOA_OPEN','completed_sensitivity_cases':2,'no_claim_of_native_design_freeze':True,'source_inductor_peak_A':max(c['source_inductor_peak_A'] for c in r['cases'].values())}
(H/'verified.json').write_text(json.dumps(report,indent=2)+'\n')
if (H/'artifact_sha256.json').exists():
 for n,d in json.loads((H/'artifact_sha256.json').read_text())['files'].items():assert sha(ROOT/n)==d,n
print(json.dumps(report,indent=2))
