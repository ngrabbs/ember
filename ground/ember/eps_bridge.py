"""Read-only IHU UART polling -> POWER_STATUS on loopback UDP port 10017.

This is a ground-generated wrapper, not native IHU CCSDS. Never forwards TC.
Only the literal observational console command `eps json` is sent to hardware.
"""
import argparse
import json
import secrets
import socket
import time

from codec import encode
from ltc4162_decode import D, decode

UNAVAILABLE = -2147483648
NEVER = 0xffffffff
LINK = {'DISCONNECTED': 0, 'WAITING': 1, 'LIVE': 2, 'READ_TIMEOUT': 3, 'INVALID_READOUT': 4}


class Lines:
    """Bound UART noise, echoes, partial lines and malformed oversized input."""
    def __init__(self):
        self.buffer = bytearray()
        self.discard = False

    def feed(self, data):
        for byte in data:
            if byte in (10, 13):
                line = bytes(self.buffer)
                self.buffer.clear()
                if not self.discard and line:
                    yield line
                self.discard = False
            elif not self.discard:
                if len(self.buffer) >= 2048:
                    self.buffer.clear()
                    self.discard = True
                else:
                    self.buffer.append(byte)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON key')
        result[key] = value
    return result


class State:
    def __init__(self, *, cells, rsnsb, rsnsi, verified=False, session=None):
        # Validate configuration before opening UART or emitting packets.
        if type(cells) is not int or not 1 <= cells <= 8:
            raise ValueError('confirmed cell count must be 1..8')
        import math
        if not all(math.isfinite(r) and 0.00001 <= r <= 100 for r in (rsnsb, rsnsi)):
            raise ValueError('sense resistance must be finite and 0.00001..100 ohms')
        self.cells, self.rsnsb, self.rsnsi, self.verified = cells, rsnsb, rsnsi, verified
        self.session = session or secrets.randbelow(0xffffffff) + 1
        self.started = time.monotonic()
        self.sequence = self.count = 0
        self.last_at = self.sample = self.decoded = None
        self.link = 'DISCONNECTED'

    def accept(self, line, now):
        # Console prompts may precede JSON. Ignore text without an object.
        start = line.find(b'{')
        if start < 0:
            return False
        try:
            sample = json.loads(line[start:].decode('ascii'), object_pairs_hook=unique_object)
            if set(sample) != {'profile', 'uptime_ms', 'registers'}:
                raise ValueError('unexpected readout fields')
            uptime = sample['uptime_ms']
            if type(uptime) is not int or not 0 <= uptime <= 0xffffffff:
                raise ValueError('bad IHU readout uptime')
            decoded = decode(sample, cells=self.cells, rsnsb_ohms=self.rsnsb, rsnsi_ohms=self.rsnsi)
        except (ValueError, KeyError, TypeError, AttributeError, UnicodeError, RecursionError):
            self.link = 'INVALID_READOUT'
            return False
        self.sample, self.decoded, self.last_at = sample, decoded, now
        self.count = (self.count + 1) & 0xffffffff
        self.link = 'LIVE'
        return True

    def payload(self, now):
        age = NEVER if self.last_at is None else min(NEVER-1, int(max(0, now-self.last_at)*1000))
        valid = self.sample is not None and self.link == 'LIVE' and age <= 12000
        conversion = valid and self.decoded['conversion_valid']
        raw = self.sample['registers'] if self.sample else {}
        p = dict(payload_version=1, provenance=1, link=LINK[self.link],
                 readout_present=int(self.sample is not None), readout_valid=int(valid),
                 conversion_valid=int(conversion), adc_valid=int(bool(raw.get('telemetry_status', 0)&1)),
                 configured_cells=self.cells, detected_cells=raw.get('chem_cells', 0)&15,
                 sense_values_verified=int(self.verified), bridge_session_id=self.session,
                 readout_count=self.count, ihu_readout_uptime_ms=self.sample['uptime_ms'] if self.sample else NEVER,
                 readout_age_ms=age, rsnsb_microohms=round(self.rsnsb*1e6), rsnsi_microohms=round(self.rsnsi*1e6))
        for field, engineering, factor in [('battery_mv','battery_pack_v',1000),('input_mv','input_v',1000),
                                          ('output_mv','output_v',1000),('battery_ua','battery_ma',1000),
                                          ('input_ua','input_ma',1000),('die_temp_mc','die_temp_c',1000)]:
            p[field] = round(self.decoded['engineering'][engineering]*factor) if conversion else UNAVAILABLE
        p.update({'raw_'+r['name']: raw.get(r['name'], 0) for r in D['registers']})
        return p

    def packet(self, now):
        packet = encode('POWER_STATUS', sequence=self.sequence, source=2, target=1,
                        transaction_epoch=0, transaction_id=0, source_boot_id=self.session,
                        uptime_ms=int(max(0, now-self.started)*1000)&0xffffffff, payload=self.payload(now))
        self.sequence = (self.sequence+1)&0x3fff
        return packet


def run(args):
    import serial
    state = State(cells=args.cells, rsnsb=args.rsnsb_ohms, rsnsi=args.rsnsi_ohms,
                  verified=args.sense_values_verified)
    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    port = None
    lines = Lines()
    reopen = next_poll = next_emit = 0
    pending = None
    last_link = None
    try:
        while True:
            now = time.monotonic()
            if port is None and now >= reopen:
                try:
                    port = serial.Serial(args.device, 115200, timeout=.1, write_timeout=.5, exclusive=True)
                    port.reset_input_buffer()
                    lines = Lines()
                    pending = None
                    next_poll = now
                    state.link = 'WAITING'
                except (OSError, serial.SerialException):
                    reopen = now + 2
            try:
                if port:
                    if pending is None and now >= next_poll:
                        if port.write(b'eps json\r') != 9:
                            raise serial.SerialException('partial observational command write')
                        pending = now + 2
                        next_poll = now + 5
                    for line in lines.feed(port.read(4096)):
                        # Unsolicited/stale buffered JSON cannot complete a later poll.
                        if pending is not None and state.accept(line, time.monotonic()):
                            pending = None
                    if pending is not None and time.monotonic() >= pending:
                        if state.link != 'INVALID_READOUT':
                            state.link = 'READ_TIMEOUT'
                        pending = None
                        lines = Lines()
                        port.reset_input_buffer()
                else:
                    time.sleep(.1)
            except (OSError, serial.SerialException):
                if port:
                    port.close()
                port = None
                pending = None
                state.link = 'DISCONNECTED'
                reopen = now + 2
            now = time.monotonic()
            if now >= next_emit:
                udp.sendto(state.packet(now), ('127.0.0.1', 10017))
                next_emit = now + 1
            if state.link != last_link:
                print(f'EPS UART {state.link}, readouts={state.count}, session={state.session}', flush=True)
                last_link = state.link
    finally:
        if port:
            port.close()
        udp.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--device', required=True, help='Exact UART /dev/serial/by-id path; exclusive owner')
    parser.add_argument('--cells', required=True, type=int)
    parser.add_argument('--rsnsb-ohms', required=True, type=float)
    parser.add_argument('--rsnsi-ohms', required=True, type=float)
    parser.add_argument('--sense-values-verified', action='store_true', help='Only after fitted resistors are measured')
    run(parser.parse_args())
