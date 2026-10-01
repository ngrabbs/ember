"""COBS framing for packets up to 240 bytes; one trailing zero delimiter."""
MAX_PACKET = 240


def encode_frame(packet):
    if not packet or len(packet) > MAX_PACKET:
        raise ValueError("packet outside framing bound")
    out = bytearray([0])
    code_at, code = 0, 1
    for byte in packet:
        if byte == 0:
            out[code_at] = code
            code_at = len(out)
            out.append(0)
            code = 1
        else:
            out.append(byte)
            code += 1
    out[code_at] = code
    return bytes(out) + b"\x00"


def decode_frame(frame):
    if not frame or len(frame) > MAX_PACKET + 1:
        raise ValueError("frame outside bound")
    out = bytearray()
    i = 0
    while i < len(frame):
        code = frame[i]
        i += 1
        if code in (0, 255) or i + code - 1 > len(frame):
            raise ValueError("invalid COBS block")
        block = frame[i:i + code - 1]
        if 0 in block:
            raise ValueError("zero inside COBS block")
        out.extend(block)
        i += code - 1
        if i < len(frame):
            out.append(0)
    if not out or len(out) > MAX_PACKET:
        raise ValueError("decoded packet outside bound")
    return bytes(out)


class FrameReader:
    def __init__(self):
        self.buffer = bytearray()
        self.discard = False
        self.errors = 0

    def feed(self, data):
        packets = []
        for byte in data:
            if byte == 0:
                if self.buffer and not self.discard:
                    try:
                        packets.append(decode_frame(self.buffer))
                    except ValueError:
                        self.errors += 1
                self.buffer.clear()
                self.discard = False
            elif not self.discard:
                if len(self.buffer) == MAX_PACKET + 1:
                    self.errors += 1
                    self.buffer.clear()
                    self.discard = True
                else:
                    self.buffer.append(byte)
        return packets
