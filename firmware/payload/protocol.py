"""Classic CAN payload v1: compatible with comms_transport's C wire codec."""
from dataclasses import dataclass
import binascii
import struct

QUERY_ID, NODE, DISCOVERY_ID = 0x700, 4, 0x704
REQUEST_ID, REPLY_ID = 0x740, 0x741
HELLO, HELLO_ACK, ECHO, ECHO_ACK = 1, 2, 0x70, 0x71
IDENT, IDENT_ACK, ERROR = 0x18, 0x19, 0x7F
STATUS, STATUS_ACK, HEARTBEAT, HEARTBEAT_ACK = 0x94, 0x95, 0x96, 0x97
FIRE_CHECK, FIRE_RESULT = 0x98, 0x99
FIRE_REPORT = struct.Struct('>BBBBIII')
HEADER = struct.Struct('>2sBBIIIH')
REPORT = struct.Struct('>BBBB6I')
CAN_FRAME = struct.Struct('=IB3x8s')
WIRE_MAX = 263


@dataclass(frozen=True)
class Packet:
    kind: int
    sender: int
    origin: int
    request: int
    payload: bytes = b''
    version: int = 1

    def encode(self):
        if len(self.payload) > 240 or not all(0 < x <= 0xffffffff for x in
                                              (self.sender, self.origin, self.request)):
            raise ValueError('packet bound/identity')
        raw = HEADER.pack(b'EU', self.version, self.kind, self.sender,
                          self.origin, self.request, len(self.payload)) + self.payload
        raw += struct.pack('>H', binascii.crc_hqx(raw, 0xffff))
        out = bytearray([0]); at = 0; code = 1
        for value in raw:
            if value == 0:
                out[at] = code; at = len(out); out.append(0); code = 1
            else:
                out.append(value); code += 1
                if code == 255:
                    out[at] = code; at = len(out); out.append(0); code = 1
        out[at] = code
        return bytes(out) + b'\0'

    @classmethod
    def decode(cls, wire):
        if not 2 <= len(wire) <= WIRE_MAX or wire[-1] != 0:
            raise ValueError('wire length/delimiter')
        raw = bytearray(); at = 0; encoded = wire[:-1]
        while at < len(encoded):
            code = encoded[at]; at += 1
            if not code or at + code - 1 > len(encoded):
                raise ValueError('COBS block')
            block = encoded[at:at + code - 1]
            if 0 in block:
                raise ValueError('COBS embedded delimiter')
            raw.extend(block); at += code - 1
            if code != 255 and at < len(encoded):
                raw.append(0)
        if len(raw) < HEADER.size + 2:
            raise ValueError('short envelope')
        magic, version, kind, sender, origin, request, length = HEADER.unpack_from(raw)
        if (magic != b'EU' or length > 240 or len(raw) != HEADER.size + length + 2
                or not sender or not origin or not request):
            raise ValueError('envelope length/identity')
        if binascii.crc_hqx(raw[:-2], 0xffff) != int.from_bytes(raw[-2:], 'big'):
            raise ValueError('CRC')
        return cls(kind, sender, origin, request, bytes(raw[HEADER.size:-2]), version)


def fragments(packet):
    wire = packet.encode()
    for index, offset in enumerate(range(0, len(wire), 4)):
        chunk = wire[offset:offset + 4]
        flags = 0x10 | int(offset == 0) | (2 if offset + len(chunk) == len(wire) else 0)
        yield struct.pack('>BHB', flags, packet.request & 0xffff, index) + chunk


class Reassembler:
    def __init__(self, can_id=REQUEST_ID):
        self.can_id = can_id
        self.active = False
        self.last = 0.0
        self.errors = self.timeouts = 0
        self.used = bytearray()

    def expire(self, now):
        if self.active and now - self.last >= .5:
            self.active = False; self.used.clear(); self.timeouts += 1

    def feed(self, can_id, data, now):
        self.expire(now)
        if can_id != self.can_id:  # Also rejects EFF, RTR and error flags.
            return None
        try:
            if not 5 <= len(data) <= 8 or data[0] & 0xfc != 0x10:
                raise ValueError('fragment shape')
            token, index = struct.unpack('>HB', data[1:4])
            start, end = data[0] & 1, data[0] & 2
            if start:
                if self.active or index:
                    raise ValueError('duplicate start')
                self.active = True; self.token = token; self.next = 0; self.used.clear()
            if (not self.active or token != self.token or index != self.next or
                    len(self.used) + len(data) - 4 > WIRE_MAX or (not end and len(data) != 8)):
                raise ValueError('fragment sequence/bound')
            self.used.extend(data[4:]); self.next += 1; self.last = now
            if end:
                self.active = False
                packet = Packet.decode(bytes(self.used))
                if packet.request & 0xffff != token:
                    raise ValueError('token mismatch')
                return packet
        except ValueError:
            self.active = False; self.used.clear(); self.errors += 1
        return None


def discovery(data, boot):
    if len(data) != 8:
        return None
    version, node, nonce, sender = struct.unpack('>BBHI', data)
    if version == 1 and node == NODE and nonce and sender:
        return struct.pack('>BBHI', 1, NODE, nonce, boot)
    return None
