"""Host-driven COMMS/Walter UART bench; echo acknowledgments are not RF delivery."""
import argparse
import binascii
import json
import re
import struct
import time
from pathlib import Path

HEADER = struct.Struct('>2sBBIIIH')
MAX_PAYLOAD = 240


def cobs(raw):
    out = bytearray([0]); at = 0; code = 1
    for byte in raw:
        if byte == 0:
            out[at] = code; at = len(out); out.append(0); code = 1
        else:
            out.append(byte); code += 1
            if code == 255:
                out[at] = code; at = len(out); out.append(0); code = 1
    out[at] = code
    return bytes(out) + b'\x00'


def envelope(kind, sender, origin, request, payload=b'', version=1, corrupt=False):
    raw = HEADER.pack(b'EU', version, kind, sender, origin, request, len(payload)) + payload
    checksum = binascii.crc_hqx(raw, 0xffff) ^ int(corrupt)
    return cobs(raw + struct.pack('>H', checksum))


class Console:
    def __init__(self, port):
        import serial
        self.serial = serial.Serial(port, 115200, timeout=.02, exclusive=True)
        self.serial.dtr = True
        time.sleep(.2)
        self.serial.reset_input_buffer()
        self.transcript = []

    def command(self, text, wait=.35):
        self.serial.write(text.encode() + b'\n'); self.serial.flush()
        end = time.monotonic() + wait
        out = bytearray()
        while time.monotonic() < end:
            out.extend(self.serial.read(8192))
        result = out.decode('utf-8', 'replace')
        self.transcript.append(f'> {text}\n{result}')
        return result

    @staticmethod
    def require_match(reply, outcome):
        submitted = re.findall(r'SUBMITTED request=(\d+)', reply)
        completed = re.findall(r'RESULT request=(\d+) outcome=' + outcome + r'\b', reply)
        assert len(submitted) == 1 and completed == submitted, reply

    def hello(self):
        reply = self.command('hello')
        self.require_match(reply, 'HELLO_CONFIRMED')
        return reply

    def echo(self, payload):
        reply = self.command('packet ' + payload.hex())
        self.require_match(reply, 'BENCH_ECHO_MATCHED')
        assert f'type=113 size={len(payload)} hex={payload.hex()}' in reply, reply
        return reply


def run(port, output):
    from codec import encode, decode, DICTIONARY
    c = Console(port)
    results = {}
    try:
        first = c.command('status')
        assert 'fw=uart-framed-v1' in first and 'id=DF637882D39E4426' in first, first
        boot = int(re.search(r' boot=(\d+)', first)[1])
        initial = {name: int(value) for name, value in re.findall(r' (\w+)=(\d+)\b', first)}
        c.hello()
        for size in (1, 2, 32, 239, 240):
            for pattern in ('zeros', 'nonzero', 'ascending'):
                payload = bytes(size) if pattern == 'zeros' else bytes([0x55])*size if pattern == 'nonzero' else bytes(range(size))
                c.echo(payload)
        results['boundary_echoes'] = 15
        results['initial_status'] = first.strip()
        telemetry = encode('HEARTBEAT', sequence=7, source=DICTIONARY['endpoints']['ihu'], target=DICTIONARY['endpoints']['ground'],
                           source_boot_id=0x10203040, uptime_ms=123456,
                           payload={'mode': 3, 'configuration': 1, 'telemetry_period_ms': 1000})
        returned = c.echo(telemetry)
        returned_hex = re.search(r'type=113 size=\d+ hex=([0-9a-f]+)', returned)[1]
        results['synthetic_heartbeat'] = decode(bytes.fromhex(returned_hex))
        # Raw bench injection is separate from real pending requests.
        for request, version, kind, reason in ((900, 2, 0x70, 1), (901, 1, 0x33, 2)):
            reply = c.command('raw ' + envelope(kind, boot, boot, request, b'x', version).hex())
            assert f'request={request} type=127 size=1 hex={reason:02x}' in reply, reply
            assert 'IGNORED reason=NO_MATCHING_REQUEST' in reply, reply
        results['explicit_rejections'] = 2
        # Corrupt CRC and too-large stream are silent drops, then a valid echo must recover.
        reply = c.command('raw ' + envelope(0x70, boot, boot, 902, b'x', corrupt=True).hex())
        assert 'RAW_SENT bench_only=1' in reply and 'RX_FRAME' not in reply, reply
        c.echo(bytes(range(240)))
        reply = c.command('raw ' + (bytes([1])*263).hex())
        assert 'RAW_SENT bench_only=1' in reply and 'RX_FRAME' not in reply, reply
        c.echo(bytes(range(240)))
        # Truncated frame expires after 250 ms; discard until delimiter, then recover.
        reply = c.command('raw ' + envelope(0x70, boot, boot, 903, b'x')[:8].hex(), .4)
        assert 'RAW_SENT bench_only=1' in reply and 'RX_FRAME' not in reply, reply
        c.echo(bytes(range(240)))
        results['fault_recovery'] = ['bad_crc', 'encoded_overflow', 'truncated_gap']
        final = c.command('status')
        last = {name: int(value) for name, value in re.findall(r' (\w+)=(\d+)\b', final)}
        assert last['pending'] == 0 and last['unknown'] == initial['unknown'], final
        assert last['boot'] == initial['boot'] and last['matched'] - initial['matched'] == 20, final
        assert last['unsolicited'] - initial['unsolicited'] == 2, final
        results['matched_transactions'] = 20
        results['echoes'] = 19
        results['passed'] = True
        results['final_status'] = final.strip()
        results['scope'] = 'Bench echo only; synthetic IHU packet; no IHU forwarding or modem/RF delivery'
        print(json.dumps(results, indent=2))
    finally:
        c.serial.close()
        output.mkdir(parents=True, exist_ok=True)
        (output/'framed-bench.log').write_text(''.join(c.transcript))
        (output/'framed-bench.json').write_text(json.dumps(results, indent=2)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    run(args.port, args.output)
