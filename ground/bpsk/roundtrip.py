"""One explicitly triggered OTA PING and finite receive window; no retries/forwarding."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import select
import sys
import time
import numpy as np
from uplink_probe import waveform, RATE, DIGITAL_OFFSET, FPGA_SHA
from modem import decode
from codec import decode as native_decode


def matches_response(packet,command,ihu_boot):
    try:
        r=native_decode(bytes.fromhex(packet['hex']));c=native_decode(command)
        h=r['header'];p=r['payload']
        return (r['name']=='COMMAND_RESPONSE' and h['source']==2 and h['target']==1
                and h['source_boot_id']==ihu_boot
                and all(h[k]==c['header'][k] for k in ('transaction_epoch','transaction_id'))
                and p==dict(command_id=1,stage=2,reason=0,parameter_id=0,value=0))
    except (ValueError,KeyError,TypeError):return False


def run(a):
    if not 0<=a.gain<=70 or not 434e6<=a.frequency<=436e6 or not 1<=a.ihu_boot<=0xffffffff:
        raise ValueError('bench settings outside bounds')
    iq,packet=waveform('ping',.05,a.sequence,a.transaction)
    a.output.mkdir(parents=True,exist_ok=False)
    report=dict(packet_hex=packet.hex(),sequence=a.sequence,transaction=a.transaction,
                expected_ihu_boot=a.ihu_boot,tx_gain=a.gain,amplitude=.05,
                uplink_hz=a.frequency,downlink_hz=437000000,tx_port='TX/RX',rx_port='RX2',
                transmitted=False,errors=[],packets=[],matching_responses=[])
    path=a.output/'result.json';path.write_text(json.dumps(report,indent=2)+'\n')
    fpga=a.images/'usrp_b210_fpga.bin'
    if hashlib.sha256(fpga.read_bytes()).hexdigest()!=FPGA_SHA:raise ValueError('FPGA mismatch')
    os.environ['UHD_IMAGES_DIR']=str(a.images)
    import uhd
    radio=uhd.usrp.MultiUSRP('type=b200,fpga='+str(fpga))
    radio.set_master_clock_rate(49152000)
    radio.set_tx_rate(RATE,0);radio.set_rx_rate(RATE,0)
    radio.set_tx_antenna('TX/RX',0);radio.set_rx_antenna('RX2',0)
    radio.set_tx_gain(a.gain,0);radio.set_rx_gain(0,0)
    radio.set_tx_freq(uhd.types.TuneRequest(a.frequency-DIGITAL_OFFSET),0)
    radio.set_rx_freq(uhd.types.TuneRequest(437000000),0)
    if abs(radio.get_tx_rate(0)-RATE)>1 or abs(radio.get_rx_rate(0)-RATE)>1:raise ValueError('unexpected rate')
    sa=uhd.usrp.StreamArgs('fc32','sc16');sa.channels=[0]
    tx=radio.get_tx_stream(sa);rx=radio.get_rx_stream(sa)
    blocks=[];started=False
    print('ROUNDTRIP_READY '+json.dumps(report),flush=True)
    try:
        if not select.select([sys.stdin],[],[],30)[0] or sys.stdin.readline().strip()!='GO':
            raise RuntimeError('GO timeout; no transmission')
        md=uhd.types.TXMetadata();md.start_of_burst=True;md.end_of_burst=True
        md.has_time_spec=True;md.time_spec=uhd.types.TimeSpec(radio.get_time_now().get_real_secs()+.25)
        sent=tx.send(iq.reshape(1,-1),md,3)
        if sent!=len(iq):raise RuntimeError('short transmit; no retry')
        am=uhd.types.TXAsyncMetadata();end=time.monotonic()+3;ack=False
        while time.monotonic()<end:
            if tx.recv_async_msg(am,.1):
                if am.event_code!=uhd.types.TXMetadataEventCode.burst_ack:raise RuntimeError(str(am.event_code))
                ack=True;break
        if not ack:raise RuntimeError('missing burst acknowledgment')
        report['transmitted']=True;radio.set_tx_gain(0,0)
        command=uhd.types.StreamCMD(uhd.types.StreamMode.start_cont);command.stream_now=True
        rx.issue_stream_cmd(command);started=True
        print('ROUNDTRIP_LISTEN',flush=True)
        buf=np.empty((1,8192),np.complex64);metadata=uhd.types.RXMetadata();end=time.monotonic()+16
        while time.monotonic()<end:
            n=rx.recv(buf,metadata,.5)
            if metadata.error_code!=uhd.types.RXMetadataErrorCode.none:raise RuntimeError(metadata.strerror())
            if n:blocks.append(buf[0,:n].copy())
    except BaseException as exc:
        report['errors'].append(str(exc));raise
    finally:
        if started:rx.issue_stream_cmd(uhd.types.StreamCMD(uhd.types.StreamMode.stop_cont))
        stop=uhd.types.TXMetadata();stop.end_of_burst=True
        tx.send(np.zeros((1,0),np.complex64),stop,.5);radio.set_tx_gain(0,0)
        path.write_text(json.dumps(report,indent=2)+'\n')
    raw=np.concatenate(blocks) if blocks else np.empty(0,np.complex64)
    np.save(a.output/'raw-192k.npy',raw)
    n=np.arange(129)-64;taps=2*(18000/RATE)*np.sinc(2*(18000/RATE)*n)*np.hamming(129);taps/=taps.sum()
    base=np.convolve(raw,taps,mode='same')[::4].astype(np.complex64) if len(raw)>=129 else np.empty(0,np.complex64)
    report['packets']=decode(base)
    report['matching_responses']=[p for p in report['packets'] if matches_response(p,packet,a.ihu_boot)]
    report['samples']=len(raw)
    path.write_text(json.dumps(report,indent=2)+'\n');print('ROUNDTRIP_RESULT '+json.dumps(report),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--sequence',type=int,required=True);p.add_argument('--transaction',type=int,required=True)
    p.add_argument('--ihu-boot',type=int,required=True);p.add_argument('--gain',type=float,default=55)
    p.add_argument('--frequency',type=float,default=434994550)
    p.add_argument('--images',type=Path,default=Path.home()/'work/ember-lte/images')
    p.add_argument('--output',type=Path,required=True)
    run(p.parse_args())
