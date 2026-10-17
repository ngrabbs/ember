"""Offline analysis of the v13 ten 100-ms alternating phase holds.
Run with a capture directory containing baseband-48k.npy.
Requires a quiet first second followed by a single one-second burst.
"""
import numpy as np,json,sys
from pathlib import Path
p=Path(sys.argv[1])
x=np.load(p/'baseband-48k.npy');fs=48000
power=np.convolve(abs(x)**2,np.ones(48)/48,'same');noise=float(np.median(power[:fs]));threshold=max(noise*10,float(power.max())*.15)
indices=np.flatnonzero(power>threshold);start=indices[0]/fs
fits=[]
for k in range(10):
 a=int((start+k*.1+.02)*fs);b=int((start+k*.1+.08)*fs);y=x[a:b];t=np.arange(a,b)/fs
 coarse=np.angle(np.sum(y[1:]*y[:-1].conj()))*fs/(2*np.pi)
 phase=np.unwrap(np.angle(y*np.exp(-2j*np.pi*coarse*(t-t[0]))))
 slope,intercept=np.polyfit(t-t[0],phase,1)
 residual=phase-(slope*(t-t[0])+intercept)
 fits.append(dict(state=k%2,t0=float(t[0]),slope=float(slope+2*np.pi*coarse),intercept=float(intercept),frequency_hz=float(coarse+slope/2/np.pi),amplitude=float(np.median(abs(y))),residual_rms_deg=float(np.sqrt(np.mean(residual**2))*180/np.pi)))
transitions=[]
for k in range(1,10):
 t=start+k*.1
 def at(f):return f['intercept']+f['slope']*(t-f['t0'])
 delta=np.angle(np.exp(1j*(at(fits[k])-at(fits[k-1]))))*180/np.pi
 transitions.append(dict(to_state=k%2,phase_step_deg=float(delta)))
r=dict(burst_start_s=start,burst_end_s=indices[-1]/fs,threshold_power=threshold,noise_power=noise,method='Separate linear phase fits in central 60ms of each 100ms hold; extrapolate adjacent fits to boundary. Receiver-domain estimates, not direct XOR measurements.',fits=fits,transitions=transitions)
(p/'phase-hold-analysis.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
