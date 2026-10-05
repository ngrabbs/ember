"""Exercise the compiled GNU Radio block without a UHD device."""
import json
import numpy as np
from gnuradio import gr,blocks
from headroom_mix import headroom_mix

n=8192
phase=np.exp(2j*np.pi*np.arange(n)/n).astype(np.complex64)
f=np.concatenate((.025*phase,4*phase,np.array([complex(float('inf'),0)],np.complex64)))
t=np.concatenate((.12*phase,.3*phase,np.array([.12],np.complex64)))
tb=gr.top_block();m=headroom_mix(.25,.15);sink=blocks.vector_sink_c()
tb.connect(blocks.vector_source_c(f.tolist()),(m,0))
tb.connect(blocks.vector_source_c(t.tolist()),(m,1));tb.connect(m,sink);tb.run()
y=np.asarray(sink.data(),np.complex64);s=m.snapshot()
assert len(y)==len(f)
assert np.max(abs(y[:n]-.145*phase))<1e-7
assert np.max(abs(y[n:2*n]-.4*phase))<1e-7
assert abs(y[-1]-.12)<1e-7
assert s['samples']==len(f) and s['invalid']==1
assert s['forwarded_clipped']==s['telemetry_clipped']==n
assert s['forward_peak_after']<=.250001 and s['output_peak']<=.400001
for limits in ((0,.15),(.26,.15),(.25,.16),(float('nan'),.15)):
    try:headroom_mix(*limits)
    except ValueError:pass
    else:raise AssertionError(('accepted invalid limits',limits))
print(json.dumps(dict(status='PASS_GNU_RADIO_NATIVE_HEADROOM',measurements=s)))
