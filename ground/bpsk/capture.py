"""Finite receive-only LibreSDR capture for Y24 DBPSK; no transmit configuration.

Retains IQ and CRC-valid native telemetry. --forward explicitly sends recovered
original bytes to local Yamcs ember; archive byte identity is a separate check.
"""
import argparse
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import socket
import time
import numpy as np
from modem import decode

def run(args):
    fpga=args.images/'usrp_b210_fpga.bin'
    expected='7f0e329b4724e0d919a06b9924aaa3c77305b6f25038deebd6171657ac7c8a99'
    if hashlib.sha256(fpga.read_bytes()).hexdigest()!=expected:raise ValueError('FPGA hash mismatch')
    args.output.mkdir(parents=True,exist_ok=False)
    os.environ['UHD_IMAGES_DIR']=str(args.images)
    import uhd
    radio=uhd.usrp.MultiUSRP(f'type=b200,fpga={fpga}')
    radio.set_rx_rate(192000,args.channel)
    radio.set_rx_freq(uhd.types.TuneRequest(args.frequency),args.channel)
    radio.set_rx_gain(args.gain,args.channel)
    radio.set_rx_antenna('RX2',args.channel)
    rate=radio.get_rx_rate(args.channel)
    if abs(rate-192000)>1:raise ValueError('unexpected sample rate')
    report=dict(utc=datetime.now(timezone.utc).isoformat(),frequency_hz=radio.get_rx_freq(args.channel),
                channel=args.channel,antenna=radio.get_rx_antenna(args.channel),rate=rate,
                gain=radio.get_rx_gain(args.channel),fpga_sha256=expected,errors=[],packets=[])
    sa=uhd.usrp.StreamArgs('fc32','sc16');sa.channels=[args.channel]
    stream=radio.get_rx_stream(sa);md=uhd.types.RXMetadata()
    command=uhd.types.StreamCMD(uhd.types.StreamMode.start_cont);command.stream_now=True
    buf=np.empty((1,8192),np.complex64);blocks=[]
    stream.issue_stream_cmd(command)
    print('BPSK_RX_READY '+json.dumps(report),flush=True)
    end=time.monotonic()+args.seconds
    try:
        while time.monotonic()<end:
            n=stream.recv(buf,md,.5)
            if md.error_code!=uhd.types.RXMetadataErrorCode.none:
                report['errors'].append(md.strerror());break
            if n:blocks.append(buf[0,:n].copy())
    finally:
        stream.issue_stream_cmd(uhd.types.StreamCMD(uhd.types.StreamMode.stop_cont))
    raw=np.concatenate(blocks) if blocks else np.empty(0,np.complex64)
    np.save(args.output/'raw-192k.npy',raw)
    # 129-tap lowpass before 4:1 decimation; retain full-rate evidence too.
    n=np.arange(129)-64
    taps=2*(18000/192000)*np.sinc(2*(18000/192000)*n)*np.hamming(129);taps/=taps.sum()
    iq=np.convolve(raw,taps,mode='same')[::4].astype(np.complex64) if len(raw)>=129 else np.empty(0,np.complex64)
    np.save(args.output/'baseband-48k.npy',iq)
    report['samples']=len(raw)
    report['peak_magnitude']=float(np.max(np.abs(raw))) if len(raw) else 0
    report['packets']=decode(iq) if not report['errors'] else []
    report['forwarded']=0
    # Write recovered evidence before any forwarding; never fabricate telemetry.
    (args.output/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    if args.forward:
        with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as sock:
            for packet in report['packets']:
                sock.sendto(bytes.fromhex(packet['hex']),('127.0.0.1',10019));report['forwarded']+=1
    (args.output/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    print('BPSK_RX_RESULT '+json.dumps(report),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--seconds',type=int,choices=range(1,181),default=8)
    p.add_argument('--frequency',type=float,default=437000000)
    p.add_argument('--gain',type=float,default=0)
    p.add_argument('--channel',type=int,choices=(0,1),default=0)
    p.add_argument('--images',type=Path,default=Path.home()/'work/ember-lte/images')
    p.add_argument('--output',type=Path,required=True);p.add_argument('--forward',action='store_true')
    args=p.parse_args()
    if not 430e6<=args.frequency<=440e6 or not 0<=args.gain<=40:p.error('bench range exceeded')
    run(args)
