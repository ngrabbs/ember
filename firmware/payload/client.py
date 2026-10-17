#!/usr/bin/env python3
"""Bench client for an already configured CAN interface; never controls RF."""
import argparse
import secrets
import socket
import struct
import time

from protocol import (Packet, Reassembler, CAN_FRAME, REQUEST_ID, REPLY_ID,
                      HELLO, HELLO_ACK, ECHO, ECHO_ACK, IDENT, IDENT_ACK,
                      STATUS, STATUS_ACK, HEARTBEAT, HEARTBEAT_ACK, ERROR, FIRE_CHECK, FIRE_RESULT, fragments)


class Client:
    def __init__(self, interface):
        self.boot = secrets.randbelow(0xffffffff) + 1
        self.request = 0
        self.peer = 0
        self.bus = socket.socket(socket.AF_CAN, socket.SOCK_RAW, socket.CAN_RAW)
        self.bus.setsockopt(socket.SOL_CAN_RAW, socket.CAN_RAW_FILTER,
                            struct.pack('=II', REPLY_ID, 0x80000000 | 0x40000000 | 0x7ff))
        self.bus.settimeout(.05)
        self.bus.bind((interface,))

    def ask(self, kind, data=b''):
        self.request += 1
        packet = Packet(kind, self.boot, self.boot, self.request, data)
        reader = Reassembler(REPLY_ID)
        for part in fragments(packet):
            self.bus.send(CAN_FRAME.pack(REQUEST_ID, len(part), part))
            time.sleep(.003)
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            try:
                raw = self.bus.recv(CAN_FRAME.size)
            except socket.timeout:
                continue
            ident, length, part = CAN_FRAME.unpack(raw)
            if length > 8:
                continue
            response = reader.feed(ident, part[:length], time.monotonic())
            if response is None or response.version != 1 or response.origin != self.boot or response.request != self.request:
                continue
            if self.peer and response.sender != self.peer:
                raise RuntimeError('Payload restarted; establish HELLO again')
            if response.kind == ERROR:
                raise RuntimeError(f'Payload rejected command: {response.payload.hex()}')
            expected = {HELLO: HELLO_ACK, ECHO: ECHO_ACK, IDENT: IDENT_ACK,
                        STATUS: STATUS_ACK, HEARTBEAT: HEARTBEAT_ACK, FIRE_CHECK: FIRE_RESULT}[kind]
            if response.kind != expected:
                continue
            if kind == HELLO:
                if response.payload:
                    raise RuntimeError('Malformed HELLO reply')
                self.peer = response.sender
            return response
        raise TimeoutError('No correlated payload reply')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--interface', default='can0')
    parser.add_argument('command', choices=['ping', 'ident', 'status', 'heartbeat', 'fire-check'])
    args = parser.parse_args()
    client = Client(args.interface)
    try:
        client.ask(HELLO)
        kind = {'ping': ECHO, 'ident': IDENT, 'status': STATUS, 'heartbeat': HEARTBEAT, 'fire-check': FIRE_CHECK}[args.command]
        response = client.ask(kind, b'EMBER' if kind == ECHO else b'')
        print(f'{args.command}: boot={response.sender} request={response.request} payload={response.payload.hex()}')
        if kind == ECHO and response.payload != b'EMBER':
            raise RuntimeError('Echo mismatch')
    finally:
        client.bus.close()


if __name__ == '__main__':
    main()
