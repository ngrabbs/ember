#!/usr/bin/env python3
"""Verify archived experiment integrity and unchanged capacitor stages in current graph."""
import hashlib,json,re,subprocess,xml.etree.ElementTree as ET
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
EPS=ROOT/'hardware/eps'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source=EPS/'verification/rev_b/can_branch_integration/eps_rev_b.xml'
root=ET.parse(source).getroot()
components={c.get('ref'):c for c in root.findall('./components/comp')}
assert len(components)==305
nets={}
for net in root.findall('./nets/net'):
 for n in net.findall('node'):nets[(n.get('ref'),n.get('pin'))]=net.get('name')
inventory=json.loads((HERE.parent/'source_boundary_2026_10_24/inventory.json').read_text())
for rail,g in inventory['groups'].items():
 actual=sorted(ref for ref in components if ref.startswith('C') and {nets.get((ref,'1')),nets.get((ref,'2'))}=={rail,'GND'})
 assert actual==sorted(p['ref'] for p in g['parts']),(rail,actual)
 for p in g['parts']:
  c=components[p['ref']];f={x.get('name'):x.text for x in c.findall('./fields/field')}
  assert f['MFG P/N']==p['mpn']
  assert float(f['Tolerance'].rstrip('%'))/100==p['initial_tolerance']
  m=re.fullmatch(r'([\d.]+)([unp])F?',c.findtext('value'));assert m
  assert float(m[1])*{'u':1,'n':.001,'p':.000001}[m[2]]==p['nominal_uF']
  assert {pin:nets[(p['ref'],pin)] for pin in ['1','2']}==p['pins']
assert nets[('Q301','1')]=='BATT_PERMITTED' and nets[('Q301','5')]=='SYS_PWR_PERMITTED'
r=json.loads((HERE/'results.json').read_text());assert len(r['cases'])==8
for name,c in r['cases'].items():
 assert c['status']=='completed' and c['end_s']==.8
 deck=HERE/'decks'/(name+'.cir')
 assert sha(deck)==c['portable_deck_sha256']
 for m in [1,2]:assert re.search(rf'^M{m} (\w+) gate cs cs IRLR2908$',deck.read_text(),re.M)[1]==c[f'm{m}_drain_node']
 assert 'Total elapsed time:' in (HERE/'logs'/(name+'.log')).read_text()
 assert 'temp = 27' in (HERE/'logs'/(name+'.log')).read_text()
 assert c['cs_V']['min']>=-.3
 assert max(abs(x) for x in c['vgs_V'].values())<16
 for m in [1,2]:assert max(abs(x) for x in c[f'm{m}_vds_V'].values())<80
repeat=json.loads((HERE/'repeat_verified.json').read_text());assert repeat['identical_observations']
# Preserve all tracked native CAD/library files, excluding untracked user artifacts.
paths=subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0')
native=[p for p in paths if p and (Path(p).suffix in ['.kicad_sch','.kicad_pcb','.kicad_pro','.kicad_sym','.kicad_mod'] or Path(p).name in ['sym-lib-table','fp-lib-table'])]
changed=subprocess.check_output(['git','diff','HEAD','--name-only'],cwd=ROOT).decode().splitlines()
assert not set(native)&set(changed),'Unexpected native design change'
report={'status':'EXPERIMENTAL_INTEGRITY_PASS_NOT_ELECTRICAL_ACCEPTANCE','current_graph_parts':305,'graph_source':str(source.relative_to(ROOT)),'graph_sha256':sha(source),'unchanged_capacitor_groups':list(inventory['groups']),'completed_cases':8,'repeat_matches':True,'native_files':{p:sha(ROOT/p) for p in sorted(native)},'visual_review':'Root opened boundary_screen.png; all four panels readable. No new native schematic pages exist. ADI datasheet text reviewed; fresh source PDF download failed, so no new rendered-datasheet inspection claimed.'}
(HERE/'verified.json').write_text(json.dumps(report,indent=2)+'\n')
files=[p for p in HERE.rglob('*') if p.is_file() and p.name!='artifact_sha256.json' and '__pycache__' not in p.parts]
(HERE/'artifact_sha256.json').write_text(json.dumps({str(p.relative_to(HERE)):sha(p) for p in sorted(files)},indent=2)+'\n')
print(f'PASS: 8 complete runs, repeat, 305-part capacitor graph; {len(native)} tracked native files unchanged.')
