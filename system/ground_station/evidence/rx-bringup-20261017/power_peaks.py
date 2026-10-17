from pathlib import Path
import re,json,sys
root=Path(__file__).parent
for name in sys.argv[1:]:
 s=(root/(name+'-scans.txt')).read_text();rows=[]
 for t in s.split('SCAN ')[1:]:
  d=[(int(a),float(b)) for a,b in re.findall(r'^(\d{9}) (-?\d+\.\d+e[+-]\d+)',t,re.M)]
  if d:
   a,b=max(d,key=lambda x:x[1]);rows.append(dict(scan=int(t.split()[0]),frequency_hz=a,input_dbm=b,pad_corrected_dbm=b+30))
 tx=(root/(name+'-tx.txt')).read_text();report=json.loads(next(x.split(' ',1)[1] for x in tx.splitlines() if x.startswith('UPLINK_PROBE_RESULT ')))
 result=dict(transmit=report,peaks=rows,external_attenuation_db=30,notes='Nominal pad correction only, internal attenuation already accounted by tinySA; noise-only scans are not source power.')
 (root/(name+'-result.json')).write_text(json.dumps(result,indent=2)+'\n')
 print(name,'TX',report['transmitted'],'errors',report['errors'],'peak',max(rows,key=lambda r:r['input_dbm']))
