import json,math,time
from pathlib import Path
import numpy as np
from gnuradio import blocks,filter,gr,uhd
p=Path.home()/'ember-repeater-input-05';p.mkdir(exist_ok=False)
rate=614400;lowrate=76800;seconds=24
flow=gr.top_block('Finite receive-only input proof')
source=uhd.usrp_source('type=sdrb,mgmt_addr=127.0.0.1,recv_frame_size=8000',uhd.stream_args(cpu_format='fc32',otw_format='sc16',channels=[1],args='spp=1024'))
source.set_samp_rate(rate);source.set_center_freq(435100000,0);source.set_antenna('RX1',0);source.set_rx_agc(False,0);source.set_gain(60,0);source.set_bandwidth(rate,0)
filt=filter.fir_filter_ccc(8,filter.firdes.low_pass(1,rate,25000,10000))
head=blocks.head(gr.sizeof_gr_complex,lowrate*seconds)
sink=blocks.file_sink(gr.sizeof_gr_complex,str(p/'input.cf32'),False)
flow.connect(source,filt,head,sink)
settings=dict(rate=source.get_samp_rate(),clock=source.get_clock_rate(),frequency=source.get_center_freq(0),gain=source.get_gain(0),antenna=source.get_antenna(0),lowrate=lowrate,seconds=seconds)
print('INPUT_CAPTURE_READY '+json.dumps(settings),flush=True)
started=time.monotonic();flow.start()
try:flow.wait()
finally:flow.stop();flow.wait();sink.close()
x=np.memmap(p/'input.cf32',dtype=np.complex64,mode='r');rows=[]
n=8192;f=np.fft.fftfreq(n,1/lowrate);window=np.hanning(n);sel=(abs(f)>1500)&(abs(f)<24000)
indices=np.flatnonzero(sel)
for at in range(0,len(x)-n,lowrate//4):
    power=abs(np.fft.fft(x[at:at+n]*window))**2
    peak=indices[np.argmax(power[indices])];noise=max(float(np.median(power[sel])),1e-20)
    rows.append(dict(seconds=at/lowrate,peak_hz=float(f[peak]),power=float(power[peak]),snr_db=float(10*np.log10(max(power[peak],1e-20)/noise)),rms=float(np.sqrt(np.mean(abs(x[at:at+n])**2)))))
result=dict(settings=settings,samples=len(x),elapsed_seconds=time.monotonic()-started,measurements=rows)
(p/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('INPUT_CAPTURE_DONE '+json.dumps({k:v for k,v in result.items() if k!='measurements'}),flush=True)
