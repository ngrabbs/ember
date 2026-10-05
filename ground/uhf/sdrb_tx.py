#!/usr/bin/env python3
"""Finite binary packet TX application; optional directory, no SDRB core changes."""
import argparse
import hashlib
import json
import signal
from pathlib import Path
import sys
import tempfile
import time
import numpy as np
from packet_radio import waveform, BASEBAND_OFFSET


def run(a):
    if not a.transmit and not a.prepare_only:raise ValueError('Explicit --transmit required')
    payload=a.packet.read_bytes()
    if a.prepared:
        prepared=json.loads(a.prepared.read_text())
        expected=dict(packet_sha256=hashlib.sha256(payload).hexdigest(),sequence=a.sequence,
                      count=a.count,interval_seconds=a.interval,frequency=a.frequency)
        if any(prepared.get(k)!=v for k,v in expected.items()):raise ValueError('Prepared waveform settings mismatch')
        iqpath=Path(prepared['iq_path']);sample_count=prepared['samples']
        if iqpath.stat().st_size!=sample_count*8:raise ValueError('Prepared waveform length mismatch')
        iqfile=None
    else:
        iqfile=tempfile.NamedTemporaryFile(prefix='ember-uhf-',suffix='.cf32',dir='/tmp',delete=not a.prepare_only)
        iqpath=Path(iqfile.name)
        sample_count=prepare_waveform(a,payload,iqfile)
        if a.prepare_only:
            iqfile.close()
            a.output.write_text(json.dumps(dict(iq_path=str(iqpath),samples=sample_count,
                packet_sha256=hashlib.sha256(payload).hexdigest(),sequence=a.sequence,
                count=a.count,interval_seconds=a.interval,frequency=a.frequency),indent=2)+'\n')
            print('UHF_TX_PREPARED '+str(a.output),flush=True);return
    from gnuradio import gr,blocks,uhd
    tb=gr.top_block('Optional binary packet bench TX')
    sink=uhd.usrp_sink('type=sdrb,mgmt_addr=127.0.0.1',
                        uhd.stream_args(cpu_format='fc32',otw_format='sc16',channels=[1]),'')
    sink.set_gain(0,0);sink.set_samp_rate(1500000)
    sink.set_center_freq(a.frequency,0);sink.set_antenna('TX1A_Direct1',0)
    sink.set_bandwidth(4608000,0)
    if abs(sink.get_samp_rate()-1500000)>1:raise ValueError('Unexpected SDRB sample rate')
    source=blocks.file_source(gr.sizeof_gr_complex,str(iqpath),False)
    tb.connect(source,sink)
    result=dict(packet_hex=payload.hex(),packet_sha256=hashlib.sha256(payload).hexdigest(),
                sequence=a.sequence,sequences=list(range(a.sequence,a.sequence+a.count)),
                count=a.count,interval_seconds=a.interval,
                samples=sample_count,seconds=sample_count/1500000,
                center_frequency_hz=sink.get_center_freq(0),packet_frequency_hz=a.frequency+BASEBAND_OFFSET,
                tx_channel=1,antenna='TX1A_Direct1',gain=a.gain,
                scope='Samples submitted to TX sink; RF receiver/archive proof is separate')
    try:
        sink.set_gain(a.gain,0);print('UHF_TX_READY '+json.dumps(result),flush=True)
        tb.start();time.sleep(result['seconds']+3)
    finally:
        sink.set_gain(0,0);tb.stop();tb.wait()
        if iqfile is not None:iqfile.close()
    result['source_samples_emitted']=int(source.nitems_written(0))
    a.output.write_text(json.dumps(result,indent=2)+'\n')
    print('UHF_TX_STOPPED '+json.dumps(result),flush=True)


def prepare_waveform(a,payload,iqfile):
    samples=waveform(payload,a.sequence)
    packet_seconds=len(samples)/1500000
    if a.interval < packet_seconds+2:
        raise ValueError('Interval must allow packet plus two seconds of silence')
    silence=np.zeros(1500000,np.complex64)
    silence.tofile(iqfile)
    for index in range(a.count):
        waveform(payload,a.sequence+index).tofile(iqfile)
        if index<a.count-1:
            # Sparse silence keeps series preparation independent of long zero writes.
            iqfile.seek((round(a.interval*1500000)-len(samples))*8,1)
    silence.tofile(iqfile);iqfile.flush()
    return iqfile.tell()//8


if __name__=='__main__':
    def terminate(signum, frame):raise KeyboardInterrupt('Termination requested')
    signal.signal(signal.SIGTERM,terminate)
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--packet',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--sequence',type=int,default=1)
    p.add_argument('--count',type=int,default=1,help='Finite series, at most 10 bursts')
    p.add_argument('--interval',type=float,default=8,help='Seconds between packet starts')
    p.add_argument('--frequency',type=float,default=434200000)
    p.add_argument('--gain',type=float,default=0)
    p.add_argument('--transmit',action='store_true')
    p.add_argument('--prepare-only',action='store_true',help='Build IQ before the receive window; opens no radio')
    p.add_argument('--prepared',type=Path,help='Reuse a prepared waveform manifest')
    a=p.parse_args()
    if not 0<=a.gain<=70 or not 430e6<=a.frequency<=440e6:p.error('gain/frequency outside bench range')
    if not 1<=a.count<=10 or not 0<=a.sequence<=2**32-a.count:p.error('count/sequence outside bounds')
    if not 4<=a.interval<=10:p.error('interval must be 4..10 seconds')
    if a.output.exists():p.error('Choose new evidence output')
    if a.prepare_only and (a.transmit or a.prepared):p.error('Preparation must be separate from transmission')
    run(a)
