"""Yamcs flight fire-check RF path. One finite burst/capture per unique command; no retry."""
import argparse
from collections import OrderedDict
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import socket
import time
import numpy as np
from codec import decode as native_decode
from modem import frame,decode
from uplink_probe import RATE,DIGITAL_OFFSET,FPGA_SHA

VERSION='0.1.0'

def valid_command(wire):
    c=native_decode(wire);h=c['header']
    return c['name']=='PAYLOAD_FIRE_CHECK' and h['source']==1 and h['target']==2 and all(h[k] for k in ('transaction_epoch','transaction_id','source_boot_id'))

def matches(wire,command):
    r=native_decode(wire);c=native_decode(command);p=r['payload'];h=r['header']
    return (r['name']=='PAYLOAD_FIRE_RESULT' and h['source']==2 and h['target']==1 and h['source_boot_id'] and
        all(h[k]==c['header'][k] for k in ('transaction_epoch','transaction_id')) and
        p['payload_version']==1 and p['transport']==2 and p['bridge_session_id']==0 and
        p['result'] in (0,1) and p['execution_mode'] in (1,2) and p['reported_boot_id'] and p['check_id'])

def execute(wire,output,images):
    if not valid_command(wire):raise ValueError('Command not admitted')
    output.mkdir(parents=True,exist_ok=False)
    report=dict(command_hex=wire.hex(),transmitted=False,packets=[],matching=[],errors=[])
    path=output/'result.json'
    fpga=images/'usrp_b210_fpga.bin'
    if hashlib.sha256(fpga.read_bytes()).hexdigest()!=FPGA_SHA:raise ValueError('FPGA mismatch')
    os.environ['UHD_IMAGES_DIR']=str(images)
    import uhd
    radio=uhd.usrp.MultiUSRP('type=b200,fpga='+str(fpga));radio.set_master_clock_rate(49152000)
    radio.set_tx_rate(RATE,0);radio.set_rx_rate(RATE,0)
    radio.set_tx_antenna('TX/RX',0);radio.set_rx_antenna('RX2',0)
    radio.set_tx_gain(55,0);radio.set_rx_gain(0,0)
    radio.set_tx_freq(uhd.types.TuneRequest(434994550-DIGITAL_OFFSET),0)
    radio.set_rx_freq(uhd.types.TuneRequest(437000000),0)
    if abs(radio.get_tx_rate(0)-RATE)>1 or abs(radio.get_rx_rate(0)-RATE)>1:raise ValueError('Unexpected rate')
    sequence=native_decode(wire)['sequence'];bits=np.unpackbits(np.frombuffer(frame(wire,sequence),np.uint8))
    amplitude=np.r_[np.zeros(RATE//20),np.repeat(1-2*(np.cumsum(bits)%2).astype(float),RATE//1200),np.zeros(RATE//20)]
    iq=(amplitude*.20*np.exp(2j*np.pi*DIGITAL_OFFSET*np.arange(len(amplitude))/RATE)).astype(np.complex64)
    if len(iq)>RATE*2 or not np.isfinite(iq).all() or np.max(np.abs(iq))>.200001:raise ValueError('Burst bound')
    sa=uhd.usrp.StreamArgs('fc32','sc16');sa.channels=[0];tx=radio.get_tx_stream(sa);rx=radio.get_rx_stream(sa)
    blocks=[];started=False
    try:
        with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as arm:
            arm.settimeout(4);arm.sendto(wire,('192.168.1.252',10030));answer,address=arm.recvfrom(512)
            if address[0]!='192.168.1.252' or answer!=b'ARMED'+wire:raise RuntimeError('COMMS not armed')
        time.sleep(.3)
        md=uhd.types.TXMetadata();md.start_of_burst=True;md.end_of_burst=True
        md.has_time_spec=True;md.time_spec=uhd.types.TimeSpec(radio.get_time_now().get_real_secs()+.25)
        if tx.send(iq.reshape(1,-1),md,3)!=len(iq):raise RuntimeError('Short transmit; no retry')
        am=uhd.types.TXAsyncMetadata();end=time.monotonic()+3;ack=False
        while time.monotonic()<end:
            if tx.recv_async_msg(am,.1):
                if am.event_code!=uhd.types.TXMetadataEventCode.burst_ack:raise RuntimeError(str(am.event_code))
                ack=True;break
        if not ack:raise RuntimeError('Missing burst acknowledgment')
        report['transmitted']=True;radio.set_tx_gain(0,0)
        stream=uhd.types.StreamCMD(uhd.types.StreamMode.start_cont);stream.stream_now=True;rx.issue_stream_cmd(stream);started=True
        buf=np.empty((1,8192),np.complex64);metadata=uhd.types.RXMetadata();end=time.monotonic()+16
        while time.monotonic()<end:
            n=rx.recv(buf,metadata,.5)
            if metadata.error_code!=uhd.types.RXMetadataErrorCode.none:raise RuntimeError(metadata.strerror())
            if n:blocks.append(buf[0,:n].copy())
    except BaseException as error:
        report['errors'].append(str(error));raise
    finally:
        if started:rx.issue_stream_cmd(uhd.types.StreamCMD(uhd.types.StreamMode.stop_cont))
        stop=uhd.types.TXMetadata();stop.end_of_burst=True
        tx.send(np.zeros((1,0),np.complex64),stop,.5);radio.set_tx_gain(0,0)
        path.write_text(json.dumps(report,indent=2)+'\n')
    raw=np.concatenate(blocks) if blocks else np.empty(0,np.complex64);np.save(output/'raw-192k.npy',raw)
    n=np.arange(129)-64;taps=2*(18000/RATE)*np.sinc(2*(18000/RATE)*n)*np.hamming(129);taps/=taps.sum()
    base=np.convolve(raw,taps,mode='same')[::4].astype(np.complex64) if len(raw)>=129 else np.empty(0,np.complex64)
    report['packets']=decode(base)
    results=[]
    for packet in report['packets']:
        result=bytes.fromhex(packet['hex'])
        if matches(result,wire) and result not in results:results.append(result)
    report['matching']=[p.hex() for p in results];path.write_text(json.dumps(report,indent=2)+'\n')
    if len(results)!=1:raise RuntimeError('No unique correlated RF result; outcome UNKNOWN')
    return results[0]

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--version',action='version',version=VERSION)
    p.add_argument('--images',type=Path,default=Path.home()/'work/ember-lte/images')
    p.add_argument('--output',type=Path,required=True);a=p.parse_args();seen=OrderedDict()
    with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as sock, socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as out:
        sock.bind(('192.168.1.251',10029))
        while True:
            wire,address=sock.recvfrom(241)
            try:
                if not valid_command(wire):continue
                c=native_decode(wire);key=tuple(c['header'][k] for k in ('transaction_epoch','transaction_id'))
                if key in seen:continue
                seen[key]=True
                if len(seen)>64:seen.popitem(last=False)
                run=a.output/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
                result=execute(wire,run,a.images)
                out.sendto(result,('127.0.0.1',10019))
                print('FIRE_RESULT '+result.hex(),flush=True)
            except Exception as error:print('UNKNOWN '+str(error),flush=True)

if __name__=='__main__':main()
