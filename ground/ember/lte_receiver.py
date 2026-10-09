"""Bounded native IHU telemetry UDP receiver on the EPC SGi interface -> Yamcs LTE input.

Only accepts IHU-native POWER_STATUS, HEARTBEAT and SYSTEM_STATUS from the configured Walter IPv4/port.
Packets are forwarded byte-for-byte; no ground-generated spacecraft telemetry.
"""
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
import socket
import time

from codec import decode,validate_arguments,PacketError

def validate(packet):
    decoded=decode(packet);validate_arguments(decoded)
    h,p=decoded['header'],decoded['payload']
    if decoded['name'] not in ('POWER_STATUS','HEARTBEAT','SYSTEM_STATUS') or h['source']!=2 or h['target']!=1:
        raise PacketError('expected allowlisted IHU telemetry')
    if h['transaction_epoch'] or h['transaction_id']:
        raise PacketError('telemetry transaction must be zero')
    if decoded['name']=='POWER_STATUS' and (p['payload_version']!=1 or p['provenance']!=2 or p['bridge_session_id']):
        raise PacketError('expected native IHU observation, without a ground wrapper')
    return decoded

def run(args):
    records=[];rejected=duplicates=0;seen=set();started=time.monotonic()
    incoming=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    forward=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    try:
        incoming.bind((args.bind,51000));incoming.settimeout(.5)
        print('LISTEN UDP 51000; expected Walter '+args.peer+':51001',flush=True)
        while time.monotonic()-started<args.seconds and len(records)<args.count:
            try:packet,address=incoming.recvfrom(4096)
            except socket.timeout:continue
            if address!=(args.peer,51001):rejected+=1;continue
            try:decoded=validate(packet)
            except (PacketError,KeyError,ValueError):rejected+=1;continue
            key=(decoded['header']['source_boot_id'],decoded['sequence'])
            if key in seen:duplicates+=1;continue
            seen.add(key)
            forward.sendto(packet,('127.0.0.1',10018))
            record=dict(received_utc=datetime.now(timezone.utc).isoformat(),peer=address,
                        hex=packet.hex(),decoded=decoded)
            records.append(record)
            print(json.dumps(record,separators=(',',':')),flush=True)
    finally:
        incoming.close();forward.close()
        result=dict(scope='Native IHU telemetry UDP received over EPC SGi and forwarded unchanged to Yamcs UDP 10018; Yamcs archive verification is separate.',
                    received=len(records),requested=args.count,rejected=rejected,duplicates=duplicates,packets=records)
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(result,indent=2)+'\n')
        print('SUMMARY '+json.dumps({k:v for k,v in result.items() if k!='packets'}),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bind',default='0.0.0.0')
    parser.add_argument('--peer',default='172.16.0.2')
    parser.add_argument('--seconds',type=int,default=180)
    parser.add_argument('--count',type=int,default=10)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if not 1<=args.count<=30 or not 1<=args.seconds<=300:parser.error('Use count 1..30, seconds 1..300')
    socket.inet_aton(args.peer);run(args)
