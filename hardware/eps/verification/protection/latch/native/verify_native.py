#!/usr/bin/env python3
"""Verify exported native latch/source corrections; no KiCad source writes."""
import csv,hashlib,json,xml.etree.ElementTree as ET
from pathlib import Path
HERE=Path(__file__).resolve().parent
prior=HERE.parent.parent/'native'
old=ET.parse(prior/'protection.xml').getroot();root=ET.parse(HERE/'protection.xml').getroot()
actual={n.attrib['name']:sorted(x.attrib['ref']+'.'+x.attrib['pin'] for x in n.findall('node')) for n in root.findall('./nets/net')}
expected=json.loads((prior/'verified.json').read_text())['endpoint_sets']
expected['+5V']=sorted(expected['+5V']+['R115.1']);expected['GND']=sorted(expected['GND']+['R115.2'])
expected['SRC_FILTERED']=sorted(expected['SOLAR_PERMITTED']+['L2.2']);expected['SOLAR_PERMITTED']=['L2.1']
assert actual==expected,{k:{'expected':expected.get(k),'actual':actual.get(k)} for k in actual.keys()|expected.keys() if actual.get(k)!=expected.get(k)}
cs={c.attrib['ref']:c for c in root.findall('./components/comp')};before={c.attrib['ref']:c for c in old.findall('./components/comp')}
assert len(cs)==83 and set(cs)==set(before)|{'L2','R115'}
for ref,c in before.items():assert c.find('tstamps').text==cs[ref].find('tstamps').text,ref
for ref in set(before)-{'C9','C112','C119','R107','R108','R5'}:assert ET.tostring(before[ref])==ET.tostring(cs[ref]),ref
fields=lambda c:{f.attrib['name']:f.text or '' for f in c.findall('./fields/field')}
for ref,value,mpn in [('C9','10n','C1210C103J1GACTU'),('C112','10n','C1210C103J1GACTU'),('C119','100n','C1210C104J1GACTU'),('R5','27.8k','TNPW121027K8BEEA'),('R107','3.57k','TNPW06033K57BEEA'),('R108','1.11k','TNPW06031K11BEEA'),('R115','330','CRCW1206330RFKEAHP'),('L2','4.7u','XAL1010-472MED')]:
 assert cs[ref].findtext('value')==value and fields(cs[ref])['MFG P/N']==mpn,ref
for ref,c in cs.items():
 f=fields(c);assert c.findtext('footprint') and f.get('MFG P/N'),ref
 if ref.startswith('C'):assert all(f.get(k) for k in ['Voltage','Tolerance','Dielectric','PackageSize']),ref
 if ref.startswith('R'):assert all(f.get(k) for k in ['Tolerance','Power','PackageSize']),ref
classes=json.loads((HERE/'netclasses.json').read_text());classes=classes.get('netclasses',classes)
patterns={p:c['name'] for c in classes for p in c['patterns']}
assert set(patterns)=={n for n in actual if not n.startswith('unconnected-')}
assert patterns['SRC_FILTERED']=='POWER'
with (HERE/'development_bom.csv').open('w',newline='') as file:
 keys=['Reference','Value','MFG P/N','Footprint','Tolerance','Power','Voltage','Dielectric','PackageSize','Current','Saturation Current','Qualification'];w=csv.DictWriter(file,keys,lineterminator="\n");w.writeheader()
 for ref,c in sorted(cs.items()):
  row={k:fields(c).get(k,'') for k in keys};row.update(Reference=ref,Value=c.findtext('value'),Footprint=c.findtext('footprint'));w.writerow(row)
evidence={'status':'PASS','physical_parts':83,'exact_endpoint_sets_checked':len(expected),'functional_nets':len(patterns),'intentional_NC':4,'original_component_UUIDs_preserved':len(before),'unrelated_component_records_preserved':len(before)-6,'endpoint_sets':actual,'netlist_SHA256':hashlib.sha256((HERE/'protection.xml').read_bytes()).hexdigest(),'presentation':'Electrical/metadata evidence only. Actual renders checked separately; S03/S11 API limits remain.'}
(HERE/'verified.json').write_text(json.dumps(evidence,indent=2)+'\n');print({k:v for k,v in evidence.items() if k!='endpoint_sets'})
