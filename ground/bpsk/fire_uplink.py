"""Finite direct-RF PING diagnostic; use link_gateway.py for the live Yamcs link."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import time
import threading
import numpy as np
from codec import decode as native_decode
from modem import frame,decode
from uplink_probe import RATE,DIGITAL_OFFSET,FPGA_SHA

def valid_command(wire):
    c=native_decode(wire);h=c['header']
    return c['name'] in ('PAYLOAD_FIRE_CHECK','PING','REQUEST_STATUS','REQUEST_TELEMETRY','STATUS_CAPTURE','STATUS_FETCH','IHU_REBOOT') and h['source']==1 and h['target']==2 and all(h[k] for k in ('transaction_epoch','transaction_id','source_boot_id'))

def matches(wire,command):
    r=native_decode(wire);c=native_decode(command);p=r['payload'];h=r['header']
    correlated=(h['source']==2 and h['target']==1 and h['source_boot_id'] and
        all(h[k]==c['header'][k] for k in ('transaction_epoch','transaction_id')))
    if not correlated:return False
    if c['name'] in ('REQUEST_TELEMETRY','STATUS_CAPTURE','STATUS_FETCH','IHU_REBOOT') and r['name']=='COMMAND_RESPONSE':
        if c['name']=='IHU_REBOOT' and p==dict(command_id=6,stage=2,reason=0,parameter_id=0,value=5000):return True
        return (p['command_id']==c['header']['message_id'] and p['parameter_id']==0 and p['value']==0 and
            ((p['stage']==1 and p['reason'] in (2,3,5,9)) or (p['stage']==3 and p['reason'] in (7,8))))
    if c['name'] in ('STATUS_CAPTURE','STATUS_FETCH','IHU_REBOOT'):
        if not (r['name']=='STATUS_RECORDS' and p['payload_version']==1 and p['count']==5 and
                p['record_size']==16 and p['volatile']==1 and p['capture_id'] and
                (c['name']!='STATUS_FETCH' or p['capture_id']==c['payload']['capture_id'])):return False
        for i in range(1,6):
            if not (p[f'record{i}_sequence']==i and p[f'record{i}_mode'] in range(5) and
                    p[f'record{i}_configuration'] in (1,2) and p[f'record{i}_can_ready'] in (0,1) and
                    p[f'record{i}_eps_valid'] in (0,1)):return False
            if i>1 and not 900<=(p[f'record{i}_uptime_ms']-p[f'record{i-1}_uptime_ms'])%2**32<=1100:return False
        return True
    if c['name']=='REQUEST_STATUS' or (c['name']=='REQUEST_TELEMETRY' and c['payload']['data_group']==1):
        return (r['name']=='IHU_STATUS' and p['payload_version']==1 and
            p['mode'] in range(5) and p['configuration'] in (1,2) and
            p['can_ready'] in (0,1) and p['eps_attempted'] in (0,1) and p['eps_valid'] in (0,1) and
            all(p[k] in range(4) for k in ('comms_state','payload_state','lte_state')) and
            p['health_gate_implemented']==0)
    if r['name']=='COMMAND_RESPONSE':
        if c['name']=='PING':
            return (p['command_id']==1 and p['stage']==2 and p['reason']==0 and p['parameter_id']==0 and p['value']==0)
        return (p['command_id']==1028 and p['stage']==3 and p['reason']==7 and p['parameter_id']==0)
    if c['name']!='PAYLOAD_FIRE_CHECK':return False
    return (r['name']=='PAYLOAD_FIRE_RESULT' and
        p['payload_version'] in (1,2) and p['transport']==2 and p['bridge_session_id']==0 and
        p['result'] in ((0,1) if p['payload_version']==1 else (0,1,2)) and
        p['execution_mode'] in (1,2) and (p['result']!=2 or p['execution_mode']==2) and
        p['reported_boot_id'] and p['check_id'])

def execute(wire,output,images):
    if not valid_command(wire) or native_decode(wire)['name']!='PING':
        raise ValueError('Command not admitted in selected profile')
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
    radio.set_tx_gain(70,0);radio.set_rx_gain(0,0)
    radio.set_tx_freq(uhd.types.TuneRequest(434994550-DIGITAL_OFFSET),0)
    radio.set_rx_freq(uhd.types.TuneRequest(437000000),0)
    if abs(radio.get_tx_rate(0)-RATE)>1 or abs(radio.get_rx_rate(0)-RATE)>1:raise ValueError('Unexpected rate')
    sequence=native_decode(wire)['sequence'];bits=np.unpackbits(np.frombuffer(frame(wire,sequence),np.uint8))
    amplitude=np.r_[np.zeros(RATE//20),np.repeat(1-2*(np.cumsum(bits)%2).astype(float),RATE//1200),np.zeros(RATE//20)]
    iq=(amplitude*.20*np.exp(2j*np.pi*DIGITAL_OFFSET*np.arange(len(amplitude))/RATE)).astype(np.complex64)
    if len(iq)>RATE*2 or not np.isfinite(iq).all() or np.max(np.abs(iq))>.200001:raise ValueError('Burst bound')
    sa=uhd.usrp.StreamArgs('fc32','sc16');sa.channels=[0];tx=radio.get_tx_stream(sa);rx=radio.get_rx_stream(sa)
    blocks=[];started=False
    stop_capture=threading.Event()
    worker=None
    def start_rx():
        stream=uhd.types.StreamCMD(uhd.types.StreamMode.start_cont)
        stream.stream_now=True;rx.issue_stream_cmd(stream)
    def capture():
        buf=np.empty((1,8192),np.complex64);metadata=uhd.types.RXMetadata();end=time.monotonic()+20
        try:
            while time.monotonic()<end and not stop_capture.is_set():
                n=rx.recv(buf,metadata,.5)
                if metadata.error_code!=uhd.types.RXMetadataErrorCode.none:raise RuntimeError(metadata.strerror())
                if n:blocks.append(buf[0,:n].copy())
        except Exception as error:
            report['errors'].append(str(error))
    try:
        start_rx();started=True
        worker=threading.Thread(target=capture);worker.start()
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
        worker.join()
        if report['errors']:raise RuntimeError('Receive capture failed')
    except BaseException as error:
        report['errors'].append(str(error));raise
    finally:
        stop_capture.set()
        if worker is not None:worker.join()
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
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--images',type=Path,default=Path.home()/'work/ember-lte/images')
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--ping-hex',required=True,help='One native PING to transmit over a conducted link')
    args=p.parse_args()
    print(execute(bytes.fromhex(args.ping_hex),args.output,args.images).hex())

if __name__=='__main__':main()
