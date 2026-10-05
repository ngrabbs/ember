"""Opt-in EMBER CAN bench responder for SDRB Linux. Never opens a radio.

Uses the existing Feather debug transport, not AMSAT flight CAN identifiers.
CHAIN_ACK means validated and recorded locally; it does not mean RF delivery.
"""
import argparse
from collections import OrderedDict
from dataclasses import dataclass
import fcntl
import json
import os
from pathlib import Path
import secrets
import socket
import struct
import time

from codec import decode, DICTIONARY, crc16
from comms_uart import HEADER, envelope

IHU_ID, COMMS_ID = 0x710, 0x711
# Match standard data frames. CAN_ERR_FLAG in a filter mask selects the
# kernel's error-frame subscription instead of ordinary CAN traffic.
IHU_FILTER_MASK = 0x80000000 | 0x40000000 | 0x7ff
WIRE_MAX = 263
CAN_FRAME = struct.Struct('=IB3x8s')


@dataclass(frozen=True)
class Envelope:
    version: int
    kind: int
    sender: int
    origin: int
    request: int
    payload: bytes

    def wire(self):
        return envelope(self.kind, self.sender, self.origin, self.request,
                        self.payload, self.version)


def parse_envelope(wire):
    if not 2 <= len(wire) <= WIRE_MAX or wire[-1] != 0:
        raise ValueError('envelope bound/delimiter')
    encoded = wire[:-1]
    raw = bytearray()
    i = 0
    while i < len(encoded):
        code = encoded[i]
        i += 1
        if not code or i + code - 1 > len(encoded):
            raise ValueError('COBS block')
        block = encoded[i:i + code - 1]
        if 0 in block:
            raise ValueError('COBS zero')
        raw.extend(block)
        i += code - 1
        if code != 255 and i < len(encoded):
            raw.append(0)
    if len(raw) < HEADER.size + 2:
        raise ValueError('short envelope')
    magic, version, kind, sender, origin, request, size = HEADER.unpack_from(raw)
    if (magic != b'EU' or size > 240 or len(raw) != HEADER.size + size + 2
            or not sender or not origin or not request):
        raise ValueError('envelope identity/length')
    if crc16(raw[:-2]) != int.from_bytes(raw[-2:], 'big'):
        raise ValueError('envelope CRC')
    return Envelope(version, kind, sender, origin, request,
                    bytes(raw[HEADER.size:-2]))


def fragments(wire, token):
    if not 1 <= len(wire) <= WIRE_MAX:
        raise ValueError('fragment bound')
    for index, offset in enumerate(range(0, len(wire), 4)):
        chunk = wire[offset:offset + 4]
        flags = 0x10 | (offset == 0) | (2 if offset + len(chunk) == len(wire) else 0)
        yield bytes([flags]) + struct.pack('>HB', token, index) + chunk


class Reassembler:
    def __init__(self):
        self.active = False
        self.last = 0
        self.errors = self.timeouts = 0
        self.used = bytearray()

    def expire(self, now):
        if self.active and now - self.last >= .5:
            self.active = False
            self.used.clear()
            self.timeouts += 1

    def feed(self, can_id, data, now):
        self.expire(now)
        if can_id != IHU_ID:  # includes SocketCAN EFF/RTR/error flags
            return None
        try:
            if not 5 <= len(data) <= 8 or data[0] & 0xfc != 0x10:
                raise ValueError('fragment format')
            start, end = data[0] & 1, data[0] & 2
            token, index = struct.unpack('>HB', data[1:4])
            if start:
                if index or self.active:
                    raise ValueError('duplicate/invalid start')
                self.active = True
                self.token, self.next = token, 0
                self.used.clear()
            if (not self.active or token != self.token or index != self.next
                    or len(self.used) + len(data) - 4 > WIRE_MAX
                    or (not end and len(data) != 8)):
                raise ValueError('fragment sequence/bound')
            self.used.extend(data[4:])
            self.next += 1
            self.last = now
            if end:
                self.active = False
                packet = parse_envelope(bytes(self.used))
                if packet.request & 0xffff != token:
                    raise ValueError('transfer token/request mismatch')
                return packet
        except ValueError:
            self.active = False
            self.used.clear()
            self.errors += 1
        return None


class Service:
    def __init__(self, boot, record):
        if not 0 < boot <= 0xffffffff:
            raise ValueError('nonzero uint32 boot required')
        self.boot, self.record = boot, record
        self.peer = 0
        self.cache = OrderedDict()
        self.accepted = self.rejected = self.duplicates = 0

    def handle(self, p):
        def reply(kind, payload=b''):
            return Envelope(1, kind, self.boot, p.origin, p.request, payload)

        def reject(reason):
            self.rejected += 1
            return reply(0x7f, bytes([reason]))

        if p.version != 1:
            return reject(1)
        if p.origin != p.sender:
            return reject(3)
        if p.kind == 1:
            if p.payload:
                return reject(4)
            if self.peer != p.sender:
                self.cache.clear()
            self.peer = p.sender
            return reply(2)
        if p.sender != self.peer:
            return reject(3)
        if p.kind == 0x70:  # opaque diagnostic echo, no radio or packet admission
            return reply(0x71, p.payload) if p.payload else reject(4)
        if p.kind != 0x72:
            return reject(2)  # LTE/RF-control types deliberately unsupported
        if p.request in self.cache:
            original, response = self.cache[p.request]
            if original != p:
                return reject(3)
            self.duplicates += 1
            return response
        try:
            decoded = decode(p.payload)
            h = decoded['header']
            if (decoded['name'] not in ('HEARTBEAT', 'POWER_STATUS')
                    or h['kind'] != DICTIONARY['kinds']['telemetry']
                    or h['source'] != DICTIONARY['endpoints']['ihu']
                    or h['target'] != DICTIONARY['endpoints']['ground']
                    or h['source_boot_id'] != p.sender):
                raise ValueError('packet route/producer')
        except ValueError:
            return reject(7)
        # Record before acknowledging. Storage failure must not produce success.
        try:
            self.record({'outcome': 'VALIDATED_AND_RECORDED', 'rf_started': False,
                         'sender_boot': p.sender, 'responder_boot': self.boot,
                         'request': p.request, 'hex': p.payload.hex(),
                         'decoded': decoded})
        except OSError:
            return reject(6)  # unknown local record outcome; no automatic retry
        response = reply(0x73, p.payload)
        self.cache[p.request] = (p, response)
        if len(self.cache) > 32:
            self.cache.popitem(last=False)
        self.accepted += 1
        return response


def serve(interface, seconds, output, respond=False):
    if not interface or len(interface) > 15 or not interface.replace('_', '').isalnum():
        raise ValueError('invalid interface name')
    output.mkdir(parents=True, exist_ok=False)
    with (output / 'packets.jsonl').open('x') as log:
        def record(item):
            item['application_replies_enabled'] = respond
            item['host_unix_ns'] = time.time_ns()
            log.write(json.dumps(item) + '\n')
            log.flush()
            os.fsync(log.fileno())

        service = Service(secrets.randbelow(0xffffffff) + 1, record)
        reader = Reassembler()
        # Advisory ownership within this adapter; cannot exclude other programs.
        lock_path = Path('/tmp') / f'ember-sdrb-{os.getuid()}-{interface}.lock'
        with lock_path.open('a') as lock, socket.socket(socket.PF_CAN, socket.SOCK_RAW, socket.CAN_RAW) as bus:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            bus.setsockopt(socket.SOL_CAN_RAW, socket.CAN_RAW_FILTER,
                           struct.pack('=II', IHU_ID, IHU_FILTER_MASK))
            bus.settimeout(.1)
            bus.bind((interface,))
            deadline = time.monotonic() + seconds
            print(json.dumps({'ready': True, 'interface': interface,
                              'boot': service.boot, 'radio': 'disabled',
                              'application_replies_enabled': respond}), flush=True)
            try:
                while time.monotonic() < deadline:
                    try:
                        frame = bus.recv(CAN_FRAME.size)
                    except socket.timeout:
                        reader.expire(time.monotonic())
                        continue
                    if len(frame) != CAN_FRAME.size:
                        continue
                    can_id, dlc, data = CAN_FRAME.unpack(frame)
                    if dlc > 8:
                        continue
                    incoming = reader.feed(can_id, data[:dlc], time.monotonic())
                    if incoming is None:
                        continue
                    response = service.handle(incoming)
                    if not respond:
                        continue
                    for fragment in fragments(response.wire(), response.request & 0xffff):
                        bus.send(CAN_FRAME.pack(COMMS_ID, len(fragment), fragment.ljust(8, b'\0')))
                        time.sleep(.002)
            finally:
                (output / 'status.json').write_text(json.dumps({
                    'boot': service.boot, 'accepted': service.accepted,
                    'rejected': service.rejected, 'duplicates': service.duplicates,
                    'fragment_errors': reader.errors, 'fragment_timeouts': reader.timeouts,
                    'rf_started': False, 'application_replies_enabled': respond}, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--interface', required=True, help='Already configured SocketCAN interface')
    parser.add_argument('--seconds', type=int, default=60, choices=range(1, 601), metavar='1..600')
    parser.add_argument('--output', type=Path, required=True, help='New evidence directory')
    parser.add_argument('--respond', action='store_true',
                        help='Enable application replies ONLY when the existing COMMS responder is absent')
    args = parser.parse_args()
    serve(args.interface, args.seconds, args.output, args.respond)
