import json,time
from pathlib import Path
import numpy as np
from gnuradio import blocks,filter,gr,uhd
p=Path.home()/'ember-duplex-iq-02';p.mkdir(exist_ok=False)
rate=614400;lowrate=76800;seconds=32
flow=gr.top_block('Finite duplex IQ proof')
d='type=sdrb,mgmt_addr=127.0.0.1,recv_frame_size=8000,send_frame_size=8000'
a=uhd.stream_args(cpu_format='fc32',otw_format='sc16',channels=[1],args='spp=1024')
sink=uhd.usrp_sink(d,a,'');sink.set_gain(0,0);sink.set_samp_rate(rate);sink.set_center_freq(434200000,0);sink.set_antenna('TX1A_Direct1',0);sink.set_bandwidth(rate,0)
source=uhd.usrp_source(d,a);source.set_samp_rate(rate);source.set_center_freq(435100000,0);source.set_antenna('RX1',0);source.set_rx_agc(False,0);source.set_gain(60,0);source.set_bandwidth(rate,0)
filt=filter.fft_filter_ccc(1,filter.firdes.low_pass(.5,rate,20000,20000),1)
flow.connect(source,filt,sink)
files=[]
for block,name in ((source,'input'),(filt,'output')):
 dec=filter.fir_filter_ccc(8,filter.firdes.low_pass(1,rate,25000,10000));file=blocks.file_sink(gr.sizeof_gr_complex,str(p/(name+'.cf32')),False)
 flow.connect(block,dec,file);files.append(file)
settings=dict(rx_rate=source.get_samp_rate(),tx_rate=sink.get_samp_rate(),rx_frequency=source.get_center_freq(0),tx_frequency=sink.get_center_freq(0),rx_gain=source.get_gain(0),tx_gain=70,antenna=source.get_antenna(0),lowrate=lowrate,seconds=seconds)
sink.set_gain(70,0);sink.set_start_time(uhd.time_spec(sink.get_time_now().get_real_secs()+1.0))
started=time.monotonic();flow.start();print('DUPLEX_IQ_READY '+json.dumps(settings),flush=True)
try:time.sleep(seconds)
finally:sink.set_gain(0,0);flow.stop();flow.wait()
for file in files:file.close()
result=dict(settings=settings,elapsed_seconds=time.monotonic()-started,measurements={})
n=8192;f=np.fft.fftfreq(n,1/lowrate);window=np.hanning(n);sel=(abs(f)>1500)&(abs(f)<24000);indices=np.flatnonzero(sel)
for name in ('input','output'):
 x=np.memmap(p/(name+'.cf32'),dtype=np.complex64,mode='r');rows=[]
 for at in range(0,len(x)-n,lowrate//4):
  power=abs(np.fft.fft(x[at:at+n]*window))**2;peak=indices[np.argmax(power[indices])];noise=max(float(np.median(power[sel])),1e-20)
  rows.append(dict(seconds=at/lowrate,peak_hz=float(f[peak]),power=float(power[peak]),snr_db=float(10*np.log10(max(power[peak],1e-20)/noise)),rms=float(np.sqrt(np.mean(abs(x[at:at+n])**2)))))
 result['measurements'][name]=rows
(p/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('DUPLEX_IQ_DONE',flush=True)
