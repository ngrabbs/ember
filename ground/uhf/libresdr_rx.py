#!/usr/bin/env python3
"""Bounded RX-only LibreSDR capture; validated RF payload -> Yamcs UHF input."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import socket
import sys
import time
import numpy as np
from packet_radio import BASEBAND_OFFSET, decode_iq, decode_iq_coherent
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'ember'))
from lte_receiver import validate


def run(args):
    fpga=args.images/'usrp_b210_fpga.bin'
    expected='7f0e329b4724e0d919a06b9924aaa3c77305b6f25038deebd6171657ac7c8a99'
    if hashlib.sha256(fpga.read_bytes()).hexdigest()!=expected:
        raise ValueError('Custom LibreSDR FPGA hash mismatch')
    os.environ['UHD_IMAGES_DIR']=str(args.images)
    import uhd
    radio=uhd.usrp.MultiUSRP(f'type=b200,fpga={fpga}')
    rate=2000000;factor=50
    radio.set_rx_rate(rate,args.channel)
    radio.set_rx_freq(uhd.types.TuneRequest(args.frequency),args.channel)
    radio.set_rx_gain(args.gain,args.channel)
    radio.set_rx_antenna('RX2',args.channel)
    actual=radio.get_rx_rate(args.channel)
    if abs(actual-rate)>1:raise ValueError('Unexpected RX sample rate')
    master_clock=radio.get_master_clock_rate();ratio=master_clock/actual
    if not np.isclose(ratio,round(ratio)) or round(ratio)%2:
        raise ValueError('Automatic LibreSDR clock must give an even integer decimation')
    sa=uhd.usrp.StreamArgs('fc32','sc16');sa.channels=[args.channel]
    stream=radio.get_rx_stream(sa);md=uhd.types.RXMetadata()
    command=uhd.types.StreamCMD(uhd.types.StreamMode.start_cont);command.stream_now=True
    iq=np.zeros((1,50000),np.complex64);blocks=[];samples=0;errors=[];carry=np.empty(0,np.complex64)
    result=dict(scope='RF-only decode, validation and unchanged Yamcs forwarding; archive check separate',
                started_utc=datetime.now(timezone.utc).isoformat(),frequency_hz=args.frequency,
                rx_channel=args.channel,rx_antenna='RX2',rx_gain=radio.get_rx_gain(args.channel),
                rate=actual,master_clock_hz=master_clock,hardware_decimation=ratio,
                fpga_sha256=expected,packets=[],errors=errors)
    stream.issue_stream_cmd(command)
    print('UHF_RX_READY '+json.dumps({k:v for k,v in result.items() if k not in ('packets','errors')}),flush=True)
    deadline=time.monotonic()+args.seconds
    try:
        while time.monotonic()<deadline:
            n=stream.recv(iq,md,.5)
            if md.error_code!=uhd.types.RXMetadataErrorCode.none:
                errors.append(str(md.strerror()))
                if md.error_code!=uhd.types.RXMetadataErrorCode.timeout:break
                continue
            if not n:continue
            index=np.arange(samples,samples+n)
            mixed=iq[0,:n]*np.exp(-2j*np.pi*BASEBAND_OFFSET*index/rate)
            samples+=n
            merged=np.concatenate((carry,mixed));used=len(merged)//factor*factor
            blocks.append(merged[:used].reshape(-1,factor).mean(axis=1).astype(np.complex64))
            carry=merged[used:]
    finally:
        stream.issue_stream_cmd(uhd.types.StreamCMD(uhd.types.StreamMode.stop_cont))
    lowrate=np.concatenate(blocks) if blocks else np.empty(0,np.complex64)
    args.output.mkdir(parents=True,exist_ok=False)
    np.save(args.output/'baseband.npy',lowrate)
    result['samples']=samples
    seen=set()
    with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as forward:
        for item in (decode_iq(lowrate,rate/factor) or decode_iq_coherent(lowrate,rate/factor)):
            packet=item.pop('payload')
            try:decoded=validate(packet)
            except ValueError:continue
            key=(decoded['header']['source_boot_id'],decoded['sequence'])
            if key in seen:continue
            seen.add(key)
            record=dict(item,hex=packet.hex(),decoded=decoded,received_utc=datetime.now(timezone.utc).isoformat())
            # Preserve decoded RF evidence before forwarding; do not synthesize packets.
            with (args.output/'packets.jsonl').open('a') as f:
                f.write(json.dumps(record)+'\n');f.flush();os.fsync(f.fileno())
            if args.forward:forward.sendto(packet,('127.0.0.1',10019))
            result['packets'].append(record)
    result['forwarded_to_yamcs']=args.forward;result['decoded_count']=len(result['packets'])
    (args.output/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print('UHF_RX_RESULT '+json.dumps(result),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--frequency',type=float,default=434200000)
    p.add_argument('--gain',type=float,default=30)
    p.add_argument('--channel',type=int,choices=(0,1),default=0)
    p.add_argument('--seconds',type=int,default=25,choices=range(1,61))
    p.add_argument('--images',type=Path,default=Path.home()/'work/ember-lte/images')
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--forward',action='store_true')
    a=p.parse_args()
    if not 0<=a.gain<=76 or not 430e6<=a.frequency<=440e6:p.error('gain/frequency outside bench range')
    run(a)
