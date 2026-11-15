"""Software GNU Radio forwarding/filter/injection proof; opens no UHD device."""
import argparse,json,tempfile,time
from pathlib import Path
import numpy as np
from gnuradio import gr,blocks,filter
from binary_injector import StreamInjector
from packet_radio import waveform,BASEBAND_OFFSET,decode_iq,decode_iq_coherent

parser=argparse.ArgumentParser();parser.add_argument('--headroom',action='store_true');args=parser.parse_args()
rate=40000;payload=bytes(range(128));offset=8000

def prepare(payload,sequence):
    iq=waveform(payload,sequence,rate);n=np.arange(len(iq))
    return (iq*np.exp(2j*np.pi*(offset-BASEBAND_OFFSET)*n/rate)).astype(np.complex64).tobytes()

injector=StreamInjector(prepare=prepare);tb=gr.top_block()
n=np.arange(400)
source=blocks.vector_source_c((.25*np.exp(2j*np.pi*1000*n/rate)+.25*np.exp(2j*np.pi*10000*n/rate)).tolist(),True)
forward=filter.fft_filter_ccc(1,filter.firdes.low_pass(.5,rate,2000,2000),1)
if args.headroom:
    from headroom_mix import headroom_mix
    adder=headroom_mix(.25,.15)
else:adder=blocks.add_cc()
throttle=blocks.throttle(gr.sizeof_gr_complex,rate,True)
sink=blocks.vector_sink_c()
tb.connect(source,forward,(adder,0));tb.connect(injector.source,(adder,1));tb.connect(adder,throttle,sink)
try:
    tb.start();time.sleep(1.5);meta=injector.queue.enqueue(payload.hex(),'native-test')
    time.sleep(5)
finally:
    injector.close();tb.stop();tb.wait()
iq=np.asarray(sink.data(),np.complex64);n=np.arange(len(iq));probe=slice(8000,30000)
h=np.mean(iq[probe]*np.exp(-2j*np.pi*1000*n[probe]/rate))
stop=np.mean(iq[probe]*np.exp(-2j*np.pi*10000*n[probe]/rate))
assert .115<abs(h)<.13,abs(h)  # Finite FIR has transition-band droop at this test tone.
assert abs(stop)<.002,abs(stop)
residual=iq-h*np.exp(2j*np.pi*1000*n/rate)
baseband=residual*np.exp(-2j*np.pi*offset*n/rate)
rows=decode_iq(baseband) or decode_iq_coherent(baseband)
assert [(r['sequence'],r['payload']) for r in rows]==[(1,payload)]
headroom=adder.snapshot() if args.headroom else None
if headroom:
    assert headroom['invalid']==headroom['telemetry_clipped']==headroom['forwarded_clipped']==0,headroom
    assert headroom['output_peak']<.4,headroom
status=injector.status(adder.nitems_written(0));assert status['emitted']==1,status
print(json.dumps(dict(status='PASS_NATIVE_FILTERED_FORWARDING_PLUS_BINARY_INJECTION',
    forwarded_tone_amplitude=float(abs(h)),rejected_tone_amplitude=float(abs(stop)),
    recovered_payload_bytes=len(payload),injector=status,headroom=headroom)))
