import argparse,json,time
from pathlib import Path
from gnuradio import blocks,gr,filter,uhd
p=argparse.ArgumentParser();p.add_argument('--mode',choices=['direct','filter','pipe'],required=True);p.add_argument('--rate',type=int,default=750000);p.add_argument('--start-delay',type=float,default=0);p.add_argument('--device-args',default='');p.add_argument('--rx-spp',type=int,default=0);p.add_argument('--seconds',type=int,default=10);p.add_argument('--output',required=True);a=p.parse_args()
print('IMPORTS '+json.dumps(dict(gnuradio=gr.version(),burst_to_stream=hasattr(blocks,'burst_to_stream'))),flush=True)
def udp():
 lines=Path('/proc/net/snmp').read_text().splitlines();return dict(zip(lines[-4].split()[1:],map(int,lines[-3].split()[1:])))
tb=gr.top_block();s=uhd.stream_args(cpu_format='fc32',otw_format='sc16',channels=[1],args=('spp='+str(a.rx_spp) if a.rx_spp else ''));d='type=sdrb,mgmt_addr=127.0.0.1'+(','+a.device_args if a.device_args else '');sink=uhd.usrp_sink(d,s,'');sink.set_gain(0,0);sink.set_samp_rate(a.rate);sink.set_center_freq(434200000,0);sink.set_antenna('TX1A_Direct1',0);sink.set_bandwidth(a.rate,0)
source=uhd.usrp_source(d,s);source.set_samp_rate(a.rate);source.set_center_freq(435100000,0);source.set_antenna('RX1',0);source.set_rx_agc(False,0);source.set_gain(30,0);source.set_bandwidth(a.rate,0)
actual=dict(rx_rate=source.get_samp_rate(),tx_rate=sink.get_samp_rate(),rx_clock=source.get_clock_rate(),tx_clock=sink.get_clock_rate(),rx_bw=source.get_bandwidth(0),tx_bw=sink.get_bandwidth(0),clock_source=source.get_clock_source(0));print('ACTUAL '+json.dumps(actual),flush=True)
inj=None
if a.mode=='direct':tb.connect(source,sink)
else:
 f=filter.fft_filter_ccc(1,filter.firdes.low_pass(.5,a.rate,20000,20000),1)
 if a.mode=='filter':tb.connect(source,f,sink)
 else:
  import sys;sys.path.insert(0,str(Path.home()/'ember-uhf-20261003'));from binary_injector import StreamInjector
  inj=StreamInjector();adder=blocks.add_cc();tb.connect(source,f,(adder,0));tb.connect(inj.source,(adder,1));tb.connect(adder,sink)
before=udp();
if a.start_delay:sink.set_start_time(uhd.time_spec(sink.get_time_now().get_real_secs()+a.start_delay))
tb.start();start=time.monotonic();print('PROBE_READY',flush=True);time.sleep(a.seconds)
if inj:inj.close()
tb.stop();tb.wait();after=udp();result=dict(mode=a.mode,rate=a.rate,actual=actual,elapsed=time.monotonic()-start,input=source.nitems_written(0),output=sink.nitems_read(0),udp_before=before,udp_after=after,udp_delta={k:after[k]-before[k] for k in before})
Path(a.output).write_text(json.dumps(result,indent=2));print('PROBE_RESULT '+json.dumps(result),flush=True)
