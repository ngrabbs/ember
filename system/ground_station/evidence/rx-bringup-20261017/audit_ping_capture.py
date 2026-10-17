"""Offline evidence audit only; no forwarding. Outer-frame recovery plus strict native validation.

For deliberate negative packets only, replace the modem's native validator in
this process so CRC32-valid outer payloads can be compared with transmitted
bytes even when their native CRC or destination is invalid. Record the strict
native codec result separately. This is not a production decoder configuration.
"""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path.home()/'work/ember-rx-uplink-20261017/ground/bpsk'))
import modem
from adc_capture import parse_capture,analytic_adc
from codec import decode as strict_native
modem.decode_native=lambda packet: {'header':{'kind':1},'audit_only':'native validation bypassed for outer-frame forensic recovery'}
results=[]
for filename in sys.argv[1:]:
 samples=parse_capture(Path(filename).read_text())
 packets=modem.decode(analytic_adc(samples),48000)
 for p in packets:
  try:p['strict_native']=strict_native(bytes.fromhex(p['hex']))
  except ValueError as e:p['strict_native_error']=str(e)
 results.append({'capture':Path(filename).name,'outer_crc32_packets':packets})
print(json.dumps(results,indent=2))
