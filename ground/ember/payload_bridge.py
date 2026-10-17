"""Yamcs LAN bench link -> exclusive IHU USB console -> payload over CAN A.

Native telemetry is wrapped from validated IHU application replies. This is
not an RF uplink/downlink. Never sends camera, power, UHF or LTE commands.
"""
import argparse
from collections import OrderedDict
import json
from pathlib import Path
import re
import secrets
import signal
import socket
import time

from codec import decode, encode, PacketError

VERSION = '0.2.0'
COMMANDS = {'PAYLOAD_PING', 'PAYLOAD_IDENT', 'PAYLOAD_STATUS_QUERY', 'PAYLOAD_HEARTBEAT_QUERY'}


class UnknownOutcome(RuntimeError):
    pass


class Console:
    def __init__(self, device):
        import serial
        self.port = serial.Serial(device, 115200, timeout=.02, write_timeout=.5, exclusive=True)
        self.boot = self.uptime = 0
        self.sampled = time.monotonic()

    def command(self, text, outcome=None, on_submit=lambda: None, timeout=3):
        self.port.write(text.encode() + b'\n'); self.port.flush()
        end = time.monotonic() + timeout
        lines = []; request = None
        while time.monotonic() < end:
            line = self.port.readline().decode('utf-8', 'replace').strip()
            if not line:
                continue
            lines.append(line)
            print(json.dumps({'console_command':text, 'line':line}), flush=True)
            if line.startswith('FIRMWARE role=IHU_MCU '):
                self.boot = int(re.search(r' boot=(\d+)', line)[1])
            if line.startswith('STATUS role=IHU_MCU '):
                self.uptime = int(re.search(r' uptime_ms=(\d+)', line)[1]); self.sampled=time.monotonic()
                if text == 'status':
                    if ' can_ready=1 ' not in line or ' mode=00 ' not in line:
                        raise RuntimeError('IHU CAN A not ready')
                    return '\n'.join(lines)
            if text == 'eps json' and line.startswith('{'):
                return line
            match = re.search(r'^SUBMITTED request=(\d+) ', line)
            if match:
                request = int(match[1]); on_submit()
            match = re.search(r'^RESULT request=(\d+) outcome=(\w+)', line)
            if match and request == int(match[1]):
                if match[2] != outcome:
                    if match[2].startswith('UNKNOWN'):
                        raise UnknownOutcome(line)
                    raise RuntimeError(line)
                return '\n'.join(lines)
            if line.startswith(('REJECT ', 'ERROR ')):
                raise RuntimeError(line)
        raise UnknownOutcome('IHU reply deadline; no automatic retry')

    def execute(self, name, size, on_submit):
        self.command('status')
        deadline = time.monotonic() + 3
        while True:
            try:
                self.command('hello payload', 'CAN_HELLO_CONFIRMED')
                break
            except UnknownOutcome:
                raise
            except RuntimeError as error:
                # Discovery may hold the target switch briefly. Only retry an
                # explicit pre-dispatch refusal, never an ambiguous CAN result.
                if str(error) != 'REJECT reason=BUSY_TARGET_SWITCH' or time.monotonic() >= deadline:
                    raise
                time.sleep(.1)
        text = {'PAYLOAD_PING':f'ping {size}', 'PAYLOAD_IDENT':'payload ident',
                'PAYLOAD_STATUS_QUERY':'payload status', 'PAYLOAD_HEARTBEAT_QUERY':'payload heartbeat'}[name]
        expected = {'PAYLOAD_PING':'CAN_ECHO_MATCHED', 'PAYLOAD_IDENT':'FIRMWARE_IDENTITY',
                    'PAYLOAD_STATUS_QUERY':'PAYLOAD_STATUS', 'PAYLOAD_HEARTBEAT_QUERY':'PAYLOAD_HEARTBEAT'}[name]
        started=time.monotonic()
        result=self.command(text, expected, on_submit)
        matches=re.findall(r'^RESULT request=\d+ outcome=\w+ peer=(\d+) bytes=(\d+) hex=([0-9a-f]+)$',result,re.M)
        if len(matches)!=1:
            raise UnknownOutcome('Missing unique validated payload result')
        peer,length,hexadecimal=matches[0]; raw=bytes.fromhex(hexadecimal)
        if not int(peer) or len(raw)!=int(length):
            raise UnknownOutcome('Bad result length/identity')
        return raw,int(peer),int((time.monotonic()-started)*1000)

    def close(self):
        # Restore the usual target when the bridge deliberately releases ownership.
        try:self.command('hello comms','CAN_HELLO_CONFIRMED')
        except Exception:pass
        self.port.close()


def observed(name, raw, peer, elapsed, bridge):
    common={'transport':1,'bridge_session_id':bridge,'reported_boot_id':peer}
    if name=='PAYLOAD_PING':
        if not 1<=len(raw)<=240 or raw!=bytes(range(len(raw))):
            raise UnknownOutcome('Echo bytes do not match request')
        return 'PAYLOAD_PING_RESULT',dict(common,bytes=len(raw),echo_ok=1,round_trip_ms=elapsed)
    if name=='PAYLOAD_IDENT':
        if len(raw)!=32 or raw[3]>1 or int.from_bytes(raw[24:28],'big')!=peer:
            raise UnknownOutcome('Firmware identity invalid')
        fields=dict(common,version_major=raw[0],version_minor=raw[1],version_patch=raw[2],dirty=raw[3],
                    reported_uptime_ms=int.from_bytes(raw[28:32],'big'),observation_age_ms=0)
        fields.update({'git_sha_'+str(i):int.from_bytes(raw[4+i*4:8+i*4],'big') for i in range(5)})
        return 'PAYLOAD_FIRMWARE',fields
    if len(raw)!=28 or raw[:4]!=bytes([1,4,1,0]) or int.from_bytes(raw[4:8],'big')!=peer:
        raise UnknownOutcome('Payload report invalid')
    fields=dict(common,payload_version=1,report_kind=1 if name=='PAYLOAD_STATUS_QUERY' else 2,node=4,ready=1)
    fields.update({key:int.from_bytes(raw[offset:offset+4],'big') for key,offset in
                   [('reported_uptime_ms',8),('requests',12),('replies',16),('rejected',20),('fragment_errors',24)]})
    return 'PAYLOAD_STATUS',fields


class Bridge:
    def __init__(self, console, emit):
        self.console,self.emit=console,emit
        self.session=secrets.randbelow(0xffffffff)+1
        self.sequence=0; self.cache=OrderedDict()

    def packet(self,name,payload,command):
        header=command['header']
        self.sequence=(self.sequence+1)&0x3fff
        return encode(name,sequence=self.sequence,source=2,target=1,
                      transaction_epoch=header['transaction_epoch'],transaction_id=header['transaction_id'],
                      source_boot_id=self.console.boot,
                      uptime_ms=(self.console.uptime+int((time.monotonic()-self.console.sampled)*1000))&0xffffffff,
                      payload=payload)

    def handle(self,wire):
        command=decode(wire)
        if command['name'] not in COMMANDS:
            return  # The serial bench accepts only this explicit command set.
        key=(command['header']['transaction_epoch'],command['header']['transaction_id'])
        if key in self.cache:
            previous,packets=self.cache[key]
            if previous==wire:
                for packet in packets:self.emit(packet)
            return  # Conflicting duplicates never execute a second operation.
        packets=[]; self.cache[key]=(wire,packets)
        if len(self.cache)>64:self.cache.popitem(last=False)
        def send(name,data):
            packet=self.packet(name,data,command);packets.append(packet);self.emit(packet)
        def stage(value,reason=0):
            send('COMMAND_RESPONSE',dict(command_id=command['header']['message_id'],stage=value,
                 reason=reason,parameter_id=0,value=0))
        size=command['payload'].get('bytes',32)
        accepted=False
        def submitted():
            nonlocal accepted
            accepted=True;stage(0)
        try:
            if not 1<=size<=240:
                self.console.command('status');stage(1,2);return
            raw,peer,elapsed=self.console.execute(command['name'],size,submitted)
            if command['name']=='PAYLOAD_PING' and len(raw)!=size:
                raise UnknownOutcome('Wrong echo size')
            name,data=observed(command['name'],raw,peer,elapsed,self.session)
            send(name,data);stage(2)
        except UnknownOutcome as error:
            print(json.dumps({'outcome':'UNKNOWN','reason':str(error)}),flush=True)
            # Yamcs times out; retain cache entry so duplicates do not execute again.
        except (RuntimeError,OSError) as error:
            print(json.dumps({'outcome':'FAILED','reason':str(error)}),flush=True)
            if not accepted and self.console.boot:stage(1,5)
            # After dispatch, a transport failure remains UNKNOWN.


class EpsMonitor:
    """Observational polling between commands, using the same serial owner."""
    def __init__(self,console,emit,*,cells,rsnsb,rsnsi):
        from eps_bridge import State
        self.console,self.emit=console,emit
        self.state=State(cells=cells,rsnsb=rsnsb,rsnsi=rsnsi)

    def poll(self):
        try:
            line=self.console.command('eps json',timeout=2)
            self.state.accept(line.encode(),time.monotonic())
        except RuntimeError as error:
            self.state.link='READ_TIMEOUT'
            print(json.dumps({'eps_poll':'failed','reason':str(error)}),flush=True)
        self.emit(self.state.packet(time.monotonic()))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version',action='version',version=VERSION)
    parser.add_argument('--device',required=True)
    parser.add_argument('--bind',default='192.168.1.252')
    parser.add_argument('--ground',default='192.168.1.251')
    parser.add_argument('--poll-eps',action='store_true',help='Read eps json every five seconds between commands')
    parser.add_argument('--cells',type=int,default=2)
    parser.add_argument('--rsnsb-ohms',type=float,default=.01)
    parser.add_argument('--rsnsi-ohms',type=float,default=.01)
    args=parser.parse_args()
    incoming=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);incoming.bind((args.bind,10028))
    outgoing=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    console=Console(args.device)
    console.command('status')
    bridge=Bridge(console,lambda packet:outgoing.sendto(packet,(args.ground,10020)))
    monitor=EpsMonitor(console,bridge.emit,cells=args.cells,rsnsb=args.rsnsb_ohms,rsnsi=args.rsnsi_ohms) if args.poll_eps else None
    incoming.settimeout(.2)
    next_poll=0
    def stop(signum,frame):raise KeyboardInterrupt
    signal.signal(signal.SIGTERM,stop)
    try:
        while True:
            if monitor and time.monotonic()>=next_poll:
                monitor.poll()
                next_poll=time.monotonic()+5
            try:wire,address=incoming.recvfrom(241)
            except socket.timeout:continue
            if address[0]!=args.ground:continue
            try:bridge.handle(wire)
            except (PacketError,ValueError) as error:print('INVALID '+str(error),flush=True)
    finally:
        console.close()


if __name__=='__main__':main()
