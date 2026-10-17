import sys,json
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path.home()/'work/ember-rx-uplink-20261017/ground/bpsk'))
import modem
from adc_capture import parse_capture,analytic_adc
from codec import decode as native_decode
# Offline forensic recovery retains outer CRC; separately validate native CRC.
modem.decode_native=lambda p:{'header':{'kind':1}}
results=[]
for file in sys.argv[1:]:
 x=parse_capture(Path(file).read_text()).astype(float);a=analytic_adc(x)
 windows=[]
 for start in range(0,len(x)-3999,2000):
  y=x[start:start+4000];y=y-y.mean();w=np.hanning(len(y));f=np.fft.rfftfreq(len(y),1/8000);power=abs(np.fft.rfft(y*w))**2
  sel=(f>=400)&(f<=2600); k=np.where(sel)[0][np.argmax(power[sel])]
  windows.append(dict(start_s=start/8000,rms_counts=float(np.std(y)),peak_hz=float(f[k]),band_power=float(power[sel].sum()*2/(len(y)*(w*w).sum()))))
 packets=modem.decode(a,48000)
 seen={p['hex'] for p in packets}
 for carrier in range(400,2601,25):
  corrected=a*np.exp(-2j*np.pi*carrier*np.arange(len(a))/48000);integ=np.r_[0,np.cumsum(corrected)]
  for phase in range(0,40,5):
   bounds=np.arange(phase,len(a)+1,40);symbols=np.diff(integ[bounds]);bits=(np.real(symbols[1:]*symbols[:-1].conj())<0).astype(np.uint8)
   for p in modem.recover_bits(bits):
    if p['hex'] not in seen: p.update(grid_carrier_hz=carrier,phase=phase);packets.append(p);seen.add(p['hex'])
 for p in packets:
  p['strict_native']=native_decode(bytes.fromhex(p['hex']))
 burst=a[int(1.1*48000):int(1.75*48000)];nfft=262144
 f=np.fft.fftfreq(nfft,1/48000)/2;spec=abs(np.fft.fft(burst*burst*np.hanning(len(burst)),nfft));sel=(f>=400)&(f<=2600);k=np.where(sel)[0][np.argmax(spec[sel])]
 results.append(dict(file=Path(file).name,windows=windows,squared_burst_candidate_hz=float(f[k]),outer_crc32_packets=packets))
print(json.dumps(results,indent=2))
