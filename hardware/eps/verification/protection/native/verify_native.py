"""Verify the isolated protection study against explicit native hardware endpoints.
Read exported KiCad XML; never writes KiCad source.
"""
import json, hashlib, xml.etree.ElementTree as ET
from pathlib import Path
HERE=Path(__file__).resolve().parent
root=ET.parse(HERE/'protection.xml').getroot()
actual={n.attrib['name']:sorted(x.attrib['ref']+'.'+x.attrib['pin'] for x in n.findall('node')) for n in root.findall('./nets/net')}
P='/Recovery rail fault containment/'
expected={}
def net(name, endpoints): expected[name]=sorted(endpoints.split())
net('+3V3','R9.1 R109.1')
net('+5V','C101.1 C102.1 C103.1 C104.1 C105.1 C106.1 C107.1 C108.1 C109.1 C110.1 R101.2 R107.1 U2.1')
net('/SRC_COMMON','D3.2 D4.2 Q1.3 Q2.3 R11.2 U1.4')
net('/SRC_DG','D4.1 Q2.1 U1.3')
net('/SRC_FAULT','R9.2 U1.11')
net('/SRC_FB','R7.2 R8.1 U1.14')
net('/SRC_GH','C12.1 D2.1 D3.1 Q1.1 Q3.2 R10.2')
net('/SRC_HGATE','D2.2 Q3.1 R10.1 U1.5')
net('/SRC_OV','C11.1 R5.2 R6.1 U1.9')
net('/SRC_SENSE','Q2.2 R1.1 U1.2')
net('/SRC_UV','C10.1 R3.2 R4.1 U1.8')
net(P+'REC5_COMMON','D103.2 D104.2 Q101.3 Q102.3 Q103.3 Q104.3 Q105.3 Q106.3 R111.2 U2.4')
net(P+'REC5_DG','D104.1 Q104.1 Q105.1 Q106.1 U2.3')
net(P+'REC5_FAULT','R109.2 U2.11')
net(P+'REC5_FB','R107.2 R108.1 U2.14')
net(P+'REC5_GH','C112.1 D102.1 D103.1 Q101.1 Q102.1 Q103.1 Q108.2 R110.2')
net(P+'REC5_HGATE','D102.2 Q108.1 R110.1 U2.5')
net(P+'REC5_RESET','R113.1')
net(P+'REC5_SENSE','Q104.2 Q105.2 Q106.2 R101.1 U2.2')
net(P+'REC5_UV','Q107.3 R103.2 R104.1 U2.8')
net('5V0_RECOVERY_REG','L1.1')
net('REC5_BIAS','C117.1 R102.2 R103.1 U2.6')
net('REC5_PIN','C113.1 C114.1 C115.1 C116.1 D105.1 L1.2 Q101.2 Q102.2 Q103.2 R102.1')
net('SOLAR_PERMITTED','D5.1 Q1.2 R2.1 R5.1 R13.1')
net('/SRC_SNUB','C13.1 C14.1 C15.1 C16.1 R13.2')
net('SRC_BIAS','C5.1 C6.1 C7.1 C8.1 D1.1 R3.1 U1.6')
net('VIN_CHG','C1.1 C2.1 C3.1 C4.1 R1.2 R7.1 U1.1')
net('GND','C1.2 C10.2 C101.2 C102.2 C103.2 C104.2 C105.2 C106.2 C107.2 C108.2 C109.2 C11.2 C110.2 C113.2 C114.2 C115.2 C116.2 C117.2 C119.2 C13.2 C14.2 C15.2 C16.2 C2.2 C3.2 C4.2 C5.2 C6.2 C7.2 C8.2 C9.2 D105.2 D5.2 Q107.2 R104.2 R108.2 R112.2 R114.2 R12.2 R4.2 R6.2 R8.2 U1.10 U1.15 U2.10 U2.15 U2.9')
for n,e in {
'Net-(C12-Pad2)':'C12.2 R12.1',
'Net-(C112-Pad2)':'C112.2 R112.1',
'Net-(D1-A)':'D1.2 R2.2',
'Net-(Q3-C)':'Q3.3 R11.1',
'Net-(Q107-B)':'Q107.1 R113.2 R114.1',
'Net-(Q108-C)':'Q108.3 R111.1',
'Net-(U1-TMR)':'C9.1 U1.13',
'Net-(U2-TMR)':'C119.1 U2.13',
'unconnected-(U1-ENOUT-Pad12)':'U1.12',
'unconnected-(U1-~{SHDN}-Pad7)':'U1.7',
'unconnected-(U2-ENOUT-Pad12)':'U2.12',
'unconnected-(U2-~{SHDN}-Pad7)':'U2.7'}.items():net(n,e)
assert actual==expected, json.dumps({k:{'expected':expected.get(k),'actual':actual.get(k)} for k in set(expected)|set(actual) if expected.get(k)!=actual.get(k)},indent=2)
cs=root.findall('./components/comp')
assert len(cs)==81 and len({c.attrib['ref'] for c in cs})==81
parts={c.attrib['ref']:c for c in cs}
for ref,c in parts.items():
 assert c.findtext('footprint'),ref+' footprint absent'
 fields={f.attrib['name']:f.text for f in c.findall('./fields/field')}
 assert fields.get('MFG P/N'),ref+' MFG P/N absent'
 if ref.startswith('C'):
  assert all(fields.get(k) for k in ['Tolerance','Voltage','Dielectric','PackageSize']),ref
 if ref.startswith('R'):
  assert all(fields.get(k) for k in ['Tolerance','Power','PackageSize']),ref
assert [parts[r].findtext('value') for r in ['C9','C12','C119','C112']]==['100n','1n','220p','68n']
for ref in ['D3','D4','D103','D104']:assert parts[ref].findtext('value')=='SMBJ8.5A'
assert parts['D5'].findtext('value')=='SMBJ60A'
assert parts['D105'].findtext('value')=='SMBJ36A'
assert parts['R13'].findtext('value')=='1.0'
nc=json.loads((HERE/'netclasses.json').read_text())
patterns={p:n['name'] for n in nc['netclasses'] for p in n['patterns']}
assert set(patterns)=={n for n in actual if not n.startswith('unconnected-')}
evidence={'status':'PASS','physical_components':len(cs),'endpoint_sets':actual,'exact_endpoint_sets_checked':len(actual),'connected_nets':len(patterns),'intentional_NC':4,'netlist_sha256':hashlib.sha256((HERE/'protection.xml').read_bytes()).hexdigest(),'metadata':'Required values persisted; Exact manufacturer ordering codes persisted with procurement confirmation open; inductor catalog current fields retain qualification limits; S11 visual presentation not accepted','netclass_assignments':patterns}
(HERE/'verified.json').write_text(json.dumps(evidence,indent=2)+'\n')
print(json.dumps({k:v for k,v in evidence.items() if k not in ['endpoint_sets','netclass_assignments']},indent=2))
