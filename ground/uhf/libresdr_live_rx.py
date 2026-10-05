#!/usr/bin/env python3
"""Bounded continuous RF capture with concurrent incremental decode and forwarding."""
import argparse
from datetime import datetime,timezone
from collections import deque
from contextlib import nullcontext
import hashlib,json,multiprocessing as mp,os,queue,signal,socket,sys,threading,time
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'ember'))
from lte_receiver import validate
from stream_decoder import WindowBuffer,Decoder
from packet_radio import BASEBAND_OFFSET


def decode_worker(jobs, output, forward_enabled, retained_packets=None):
    # Ctrl-C stops capture first; the worker drains recorded windows normally.
    signal.signal(signal.SIGINT,signal.SIG_IGN)
    decoder=Decoder(validate);records=deque(maxlen=retained_packets);decoded_count=0
    with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as sock, (output/'packets.jsonl').open('w') as log:
        while True:
            job=jobs.get()
            if job is None:break
            offset,samples,captured_at=job
            for row in decoder.decode(offset,samples):
                row.update(received_utc=datetime.now(timezone.utc).isoformat(),window_captured_unix=captured_at)
                log.write(json.dumps(row)+'\n');log.flush();os.fsync(log.fileno())
                if forward_enabled:sock.sendto(bytes.fromhex(row['hex']),('127.0.0.1',10019))
                records.append(row);decoded_count+=1
                print('UHF_RX_PACKET '+json.dumps(row),flush=True)
    (output/'decoder.json').write_text(json.dumps(dict(decoded_count=decoded_count,
        overlap_duplicates=decoder.overlap_duplicates,rejected=decoder.rejected,
        forwarded_to_yamcs=forward_enabled,packets=list(records)),indent=2)+'\n')


def run(a, probe=None, stop=None):
    stop=stop or threading.Event()
    fpga=a.images/'usrp_b210_fpga.bin'
    expected='7f0e329b4724e0d919a06b9924aaa3c77305b6f25038deebd6171657ac7c8a99'
    if hashlib.sha256(fpga.read_bytes()).hexdigest()!=expected:raise ValueError('Custom FPGA hash mismatch')
    a.output.mkdir(parents=True,exist_ok=False)
    os.environ['UHD_IMAGES_DIR']=str(a.images)
    import uhd
    radio=uhd.usrp.MultiUSRP(f'type=b200,fpga={fpga}')
    rate=2000000;factor=50
    radio.set_rx_rate(rate,a.channel);radio.set_rx_freq(uhd.types.TuneRequest(a.frequency),a.channel)
    radio.set_rx_gain(a.gain,a.channel);radio.set_rx_antenna('RX2',a.channel)
    if probe is not None:probe.configure(radio,rate)
    if abs(radio.get_rx_rate(a.channel)-rate)>1:raise ValueError('Unexpected RX rate')
    master_clock=radio.get_master_clock_rate()
    ratio=master_clock/radio.get_rx_rate(a.channel)
    if not np.isclose(ratio,round(ratio)) or round(ratio)%2:
        raise ValueError('Automatic LibreSDR clock must give an even integer decimation')
    sa=uhd.usrp.StreamArgs('fc32','sc16');sa.channels=[a.channel]
    stream=radio.get_rx_stream(sa);md=uhd.types.RXMetadata()
    ctx=mp.get_context('spawn');jobs=ctx.Queue(maxsize=3)
    worker=ctx.Process(target=decode_worker,args=(jobs,a.output,a.forward,getattr(a,'retained_packets',None)));worker.start()
    windows=WindowBuffer();samples=0;carry=np.empty(0,np.complex64)
    iq=np.zeros((1,50000),np.complex64);errors=[];dropped=0;started=time.monotonic()
    command=uhd.types.StreamCMD(uhd.types.StreamMode.start_cont);command.stream_now=True
    stream.issue_stream_cmd(command)
    print('UHF_RX_READY '+json.dumps(dict(mode='incremental',seconds=a.seconds,frequency=a.frequency,
          channel=a.channel,antenna='RX2',gain=a.gain,window_seconds=8,stride_seconds=4,
          master_clock_hz=master_clock,hardware_decimation=ratio)),flush=True)
    def submit(job):
        nonlocal dropped
        try:jobs.put_nowait((*job,time.time()))
        except queue.Full:
            dropped+=1
            if getattr(a,'fail_on_error',False):raise RuntimeError('Decode window queue full')
    try:
        if probe is not None:probe.start()
        with (nullcontext(None) if getattr(a,'no_iq',False) else (a.output/'baseband.cf32').open('wb')) as raw:
            while not stop.is_set() and (not a.seconds or time.monotonic()-started<a.seconds):
                if not worker.is_alive():raise RuntimeError('Decoder worker stopped')
                n=stream.recv(iq,md,.5)
                if md.error_code!=uhd.types.RXMetadataErrorCode.none:
                    errors.append(str(md.strerror()))
                    if getattr(a,'fail_on_error',False):raise RuntimeError('RX stream error: '+str(md.strerror()))
                    # Do not join IQ across missing samples into a candidate frame.
                    windows=WindowBuffer();carry=np.empty(0,np.complex64)
                    if md.error_code!=uhd.types.RXMetadataErrorCode.timeout:break
                    continue
                if not n:continue
                if probe is not None:probe.observe(iq[0,:n],md.time_spec.get_real_secs())
                index=np.arange(samples,samples+n)
                mixed=iq[0,:n]*np.exp(-2j*np.pi*BASEBAND_OFFSET*index/rate);samples+=n
                merged=np.concatenate((carry,mixed));used=len(merged)//factor*factor
                low=merged[:used].reshape(-1,factor).mean(axis=1).astype(np.complex64);carry=merged[used:]
                if raw is not None:low.tofile(raw)
                for job in windows.push(low):submit(job)
    finally:
        capture_elapsed=time.monotonic()-started
        stream.issue_stream_cmd(uhd.types.StreamCMD(uhd.types.StreamMode.stop_cont))
        if probe is not None:
            try:probe.close()
            except Exception as exc:errors.append('Probe cleanup: '+str(exc))
        if worker.is_alive():
            # Drain queued windows before bounded shutdown, including the last partial window.
            try:
                jobs.put((*windows.tail(),time.time()),timeout=20);jobs.put(None,timeout=20)
            except queue.Full:
                errors.append('Decoder shutdown queue timeout')
            worker.join(timeout=45)
        if worker.is_alive():worker.terminate();worker.join();errors.append('Decoder shutdown timeout')
        result=dict(samples=samples,errors=errors,dropped_decode_windows=dropped,
            decoder_exitcode=worker.exitcode,fpga_sha256=expected,frequency_hz=a.frequency,
            rx_channel=a.channel,rx_gain=a.gain,seconds=a.seconds,lowrate_hz=40000,
            master_clock_hz=master_clock,hardware_decimation=ratio,iq_saved=not getattr(a,'no_iq',False),
            capture_elapsed_seconds=capture_elapsed, sample_seconds=samples/rate)
        (a.output/'capture.json').write_text(json.dumps(result,indent=2)+'\n')
        print('UHF_RX_STOPPED '+json.dumps(result),flush=True)
        jobs.close()

if __name__=='__main__':
    stop=threading.Event()
    for sig in (signal.SIGINT,signal.SIGTERM):signal.signal(sig,lambda *_:stop.set())
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--frequency',type=float,default=434200000);p.add_argument('--gain',type=float,default=40)
    p.add_argument('--channel',type=int,choices=(0,1),default=0)
    p.add_argument('--seconds',type=int,default=60,choices=range(0,601),help='0: until stopped')
    p.add_argument('--no-iq',action='store_true',help='Decode live without saving raw IQ')
    p.add_argument('--retained-packets',type=int,choices=range(1,4097),help='Keep this many packet details in decoder.json; JSONL records remain complete')
    p.add_argument('--fail-on-error',action='store_true',help='Exit on RX or decode queue faults for supervision')
    p.add_argument('--images',type=Path,default=Path.home()/'work/ember-lte/images')
    p.add_argument('--output',type=Path,required=True);p.add_argument('--forward',action='store_true')
    a=p.parse_args()
    if not 0<=a.gain<=76 or not 430e6<=a.frequency<=440e6:p.error('gain/frequency outside bench range')
    if not a.seconds and (not a.no_iq or not a.retained_packets):p.error('Persistent RX requires --no-iq and --retained-packets')
    try:run(a,stop=stop)
    except KeyboardInterrupt:
        print('UHF_RX_INTERRUPTED',flush=True);sys.exit(130)
