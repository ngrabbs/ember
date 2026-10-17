#!/usr/bin/env python3
"""Boot-ready Pi payload responder. No camera, power or image operations."""
import argparse
from collections import deque
import fcntl
import json
import logging
from pathlib import Path
import secrets
import signal
import socket
import struct
import time

from protocol import (Packet, Reassembler, CAN_FRAME, REPORT, QUERY_ID, DISCOVERY_ID,
                      REQUEST_ID, REPLY_ID, NODE, HELLO, HELLO_ACK, ECHO, ECHO_ACK,
                      IDENT, IDENT_ACK, STATUS, STATUS_ACK, HEARTBEAT, HEARTBEAT_ACK,
                      ERROR, discovery, fragments)


class Service:
    def __init__(self, identity, boot=None, now=time.monotonic):
        self.identity = identity
        self.boot = boot or secrets.randbelow(0xffffffff) + 1
        self.now = now; self.started = now()
        self.peer = 0
        self.requests = self.replies = self.rejected = 0

    def handle(self, packet, fragment_errors=0):
        self.requests += 1
        def reply(kind, payload=b''):
            self.replies += 1
            return Packet(kind, self.boot, packet.origin, packet.request, payload)
        def reject(reason):
            self.rejected += 1
            return reply(ERROR, bytes([reason]))
        if packet.version != 1:
            return reject(1)
        if packet.sender != packet.origin:
            return reject(3)
        if packet.kind not in (HELLO, ECHO, IDENT, STATUS, HEARTBEAT):
            return reject(2)
        if (packet.kind == ECHO and not packet.payload) or (packet.kind != ECHO and packet.payload):
            return reject(4)
        if packet.kind == HELLO:
            self.peer = packet.sender
            return reply(HELLO_ACK)
        if self.peer != packet.sender:
            return reject(3)
        if packet.kind == ECHO:
            return reply(ECHO_ACK, packet.payload)
        uptime = int((self.now() - self.started) * 1000) & 0xffffffff
        if packet.kind == IDENT:
            version = bytes(int(x) for x in self.identity['version'].split('.'))
            data = version + bytes([self.identity['dirty']]) + bytes.fromhex(self.identity['git'])
            return reply(IDENT_ACK, data + struct.pack('>II', self.boot, uptime))
        report = REPORT.pack(1, NODE, 1, 0, self.boot, uptime, self.requests & 0xffffffff,
                             self.replies & 0xffffffff, self.rejected & 0xffffffff,
                             fragment_errors & 0xffffffff)
        return reply(STATUS_ACK if packet.kind == STATUS else HEARTBEAT_ACK, report)


def open_can(interface):
    bus = socket.socket(socket.AF_CAN, socket.SOCK_RAW, socket.CAN_RAW)
    try:
        mask = 0x80000000 | 0x40000000 | 0x7ff
        bus.setsockopt(socket.SOL_CAN_RAW, socket.CAN_RAW_FILTER,
                       b''.join(struct.pack('=II', ident, mask) for ident in (QUERY_ID, REQUEST_ID)))
        bus.setsockopt(socket.SOL_CAN_RAW, socket.CAN_RAW_RECV_OWN_MSGS, 0)
        bus.settimeout(.05)
        bus.bind((interface,))
        return bus
    except BaseException:
        bus.close()
        raise


def run(interface, identity, lock_path='/run/ember-payload/owner.lock'):
    # Keep one responder/boot identity per physical payload interface.
    with open(lock_path, 'w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        service = Service(identity)
        parser = Reassembler()
        outgoing = deque()
        stopped = False
        def stop(signum, frame):
            nonlocal stopped
            stopped = True
        signal.signal(signal.SIGTERM, stop)
        signal.signal(signal.SIGINT, stop)
        with open_can(interface) as bus:
            logging.info('CAN_READY interface=%s node=4 boot=%u git=%s version=%s',
                         interface, service.boot, identity['git'], identity['version'])
            while not stopped:
                now = time.monotonic()
                parser.expire(now)
                bus.settimeout(.002 if outgoing else .05)
                if outgoing and now >= outgoing[0][0]:
                    due, ident, data = outgoing.popleft()
                    # A congested/down bus is a failed transaction, not success.
                    bus.send(CAN_FRAME.pack(ident, len(data), data))
                try:
                    raw = bus.recv(CAN_FRAME.size)
                except socket.timeout:
                    continue
                if len(raw) != CAN_FRAME.size:
                    continue
                ident, length, data = CAN_FRAME.unpack(raw)
                if length > 8:
                    continue
                data = data[:length]
                # Bound memory even if a peer floods complete command packets.
                if len(outgoing) > 128:
                    logging.warning('BUSY reply queue full')
                    continue
                if ident == QUERY_ID:
                    response = discovery(data, service.boot)
                    if response:
                        outgoing.append((now, DISCOVERY_ID, response))
                    continue
                packet = parser.feed(ident, data, now)
                if packet is None:
                    continue
                response = service.handle(packet, parser.errors + parser.timeouts)
                logging.info('REQUEST type=%02x origin=%u request=%u reply=%02x',
                             packet.kind, packet.origin, packet.request, response.kind)
                start = max(now, outgoing[-1][0] + .002 if outgoing else now)
                for index, part in enumerate(fragments(response)):
                    outgoing.append((start + index * .002, REPLY_ID, part))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--interface', default='can0')
    parser.add_argument('--identity', type=Path, default=Path(__file__).with_name('build_identity.json'))
    parser.add_argument('--lock', default='/run/ember-payload/owner.lock')
    args = parser.parse_args()
    identity = json.loads(args.identity.read_text())
    if (len(identity['git']) != 40 or len(bytes.fromhex(identity['git'])) != 20
            or identity['dirty'] not in (0, 1) or len(identity['version'].split('.')) != 3):
        raise ValueError('invalid build identity')
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    run(args.interface, identity, args.lock)


if __name__ == '__main__':
    main()
