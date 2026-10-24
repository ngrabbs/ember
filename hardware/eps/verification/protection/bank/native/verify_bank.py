"""Verify the converter 50V bank correction using fresh exported KiCad XML."""
from pathlib import Path
import json,xml.etree.ElementTree as E,hashlib,csv
P=Path(__file__).resolve().parent
before=E.parse(P/'before.xml').getroot();after=E.parse(P/'after.xml').getroot()
def nets(r):return {n.attrib['name']:set(x.attrib['ref']+'.'+x.attrib['pin'] for x in n.findall('node')) for n in r.findall('./nets/net')}
bn,an=nets(before),nets(after);expected={k:set(v) for k,v in bn.items()}
for i in range(19,25):
 expected['5V0_RECOVERY_RAW'].add(f'C{i}.1');expected['GND'].add(f'C{i}.2')
assert an==expected,{n:{'expected':sorted(expected.get(n,set())),'actual':sorted(an.get(n,set()))} for n in set(an)|set(expected) if an.get(n)!=expected.get(n)}
assert len(an)==19 and len([n for n in an if not n.startswith('unconnected-')])==16
bc={c.attrib['ref']:c for c in before.findall('./components/comp')};ac={c.attrib['ref']:c for c in after.findall('./components/comp')}
assert len(bc)==28 and len(ac)==34
assert set(ac)-set(bc)=={f'C{i}' for i in range(19,25)}
def fields(c):return {f.attrib['name']:f.text for f in c.findall('./fields/field')}
bank={f'C{i}' for i in [9,10,11,12,13,14,15,19,20,21,22,23,24]}
for r,c in bc.items():
 assert c.findtext('tstamps')==ac[r].findtext('tstamps'),r+' UUID changed'
 if r not in bank:
  assert E.tostring(c)==E.tostring(ac[r]),r+' unrelated component changed'
for r in bank:
 f=fields(ac[r]);assert f['Voltage']=='50 V'
 assert r+'.1' in an['5V0_RECOVERY_RAW'] and r+'.2' in an['GND']
 if r in {f'C{i}' for i in [9,10,11,12,19,20,21,22]}:
  assert ac[r].findtext('value')=='10u' and f['MFG P/N']=='CGA5L1X7R1H106K160AC'
  assert f['Tolerance']=='10%' and f['PackageSize']=='1206' and f['Dielectric']=='X7R'
  assert ac[r].findtext('footprint')=='Capacitor_SMD:C_1206_3216Metric'
 else:
  assert ac[r].findtext('value')=='68u' and f['MFG P/N']=='EEHZA1H680P'
  assert f['Tolerance']=='20%' and f['Dielectric']=='Hybrid aluminum'
  assert ac[r].findtext('footprint')=='Ember_EPS_Recovery:Panasonic_CP_F_8x10.2mm_REVIEW'
assert ac['C16'].findtext('value')=='100n' and fields(ac['C16'])['Voltage']=='50 V'
nc=json.loads((P/'netclasses.json').read_text());patterns={p for c in nc['netclasses'] for p in c['patterns']}
assert patterns=={n for n in an if not n.startswith('unconnected-')}
result={'status':'PASS','physical_components_before':28,'physical_components_after':34,'functional_endpoint_sets':16,'intentional_NC_endpoint_sets':3,'endpoint_sets':{k:sorted(v) for k,v in an.items()},'unrelated_components_preserved':21,'original_component_UUIDs_preserved':28,'bank_voltage':'50 V','unchanged_bypass':'C16','bank_nominal_uF':420.0,'bank_high_tolerance_uF':496.0,'bank_high_endurance_tolerance_uF':618.4,'additional_C16_nominal_uF':0.1,'development_total_bank_allocation_uF':650,'integration_status':'Converter/protection coupling not accepted; no integration performed','after_xml_sha256':hashlib.sha256((P/'after.xml').read_bytes()).hexdigest()}
(P/'verified.json').write_text(json.dumps(result,indent=2)+'\n')
rows=[]
for r,c in ac.items():
 f=fields(c);rows.append({'Reference':r,'Value':c.findtext('value'),'MFG P/N':f.get('MFG P/N',''),'Footprint':c.findtext('footprint'),'Tolerance':f.get('Tolerance',''),'Power':f.get('Power',''),'Voltage':f.get('Voltage',''),'Dielectric':f.get('Dielectric',''),'PackageSize':f.get('PackageSize',''),'Review status':f.get('Review status','')})
with (P/'development_bom.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
print(json.dumps({k:v for k,v in result.items() if k!='endpoint_sets'},indent=2))
