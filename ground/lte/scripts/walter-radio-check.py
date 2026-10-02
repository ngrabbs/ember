#!/usr/bin/env python3
"""Run on M75q: bounded Walter radio test, followed by band/radio restoration."""
import argparse
import json
from datetime import datetime, timezone
import re
import time
import serial

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--enable-seconds', type=int, default=0)
parser.add_argument('--udp-count', type=int, default=0)
parser.add_argument('--run-id', default='ember-bench')
parser.add_argument('--send-retries', type=int, default=0,
                    help='Retry up to 3 completed pre-prompt operation-not-supported errors, with 2-second backoff')
parser.add_argument('--settle-seconds', type=int, default=0,
                    help='Wait 0..30 seconds after accepted sends before socket close and modem reset')
parser.add_argument('--socket-diagnostics', action='store_true',
                    help='Read socket and registration state around sends; never query after a pending command')
args = parser.parse_args()
if not 0 <= args.udp_count <= 30: parser.error('Use 0..30 UDP packets')
if not 0 <= args.send_retries <= 3: parser.error('Use 0..3 send retries')
if not 0 <= args.settle_seconds <= 30: parser.error('Use 0..30 settle seconds')
if not re.fullmatch(r'[a-zA-Z0-9_-]{1,32}', args.run_id): parser.error('Use a simple run ID')
if args.udp_count and args.enable_seconds < 30: parser.error('UDP requires at least 30 enabled seconds')
if not 0 <= args.enable_seconds <= 120: parser.error('Use 0..120 seconds')
port = '/dev/serial/by-id/usb-Espressif_USB_JTAG_serial_debug_unit_24:58:7C:6F:0C:24-if00'
s = serial.Serial(); s.port = port; s.baudrate = 115200; s.timeout = .2
s.dtr = False; s.rts = False; s.open()
class ModemRejected(RuntimeError):
    def __init__(self, cmd, response, payload_started):
        super().__init__('Modem rejected ' + cmd)
        self.response = response
        self.payload_started = payload_started

def emit(message):
    print(datetime.now(timezone.utc).isoformat(timespec='milliseconds'),
          re.sub(r'\b\d{14,22}\b', '[redacted]', message), flush=True)
def command(cmd, timeout=6, payload=None):
    emit('SEND ' + cmd); s.write((cmd + '\r\n').encode())
    output = b''; deadline = time.monotonic() + timeout
    payload_sent = payload is None
    while time.monotonic() < deadline:
        output += s.read(4096)
        if not payload_sent and b'>' in output:
            s.write(payload); s.flush(); payload_sent = True
            emit('PAYLOAD bytes=' + str(len(payload)))
        if re.search(rb'\r\n(?:OK|ERROR|\+CME ERROR[^\r]*)\r\n', output): break
    emit('RECV ' + repr(output.decode(errors='replace')))
    if not re.search(rb'\r\n(?:OK|ERROR|\+CME ERROR[^\r]*)\r\n', output):
        raise TimeoutError('No final response; do not stack further commands')
    if b'\r\nOK\r\n' not in output:
        raise ModemRejected(cmd, output, payload is not None and payload_sent)
    if not payload_sent: raise RuntimeError('No data prompt for ' + cmd)
    return output

def socket_status():
    try:
        command('AT+SQNSS?')
    except RuntimeError:
        emit('SOCKET_DIAGNOSTIC rejected; continuing after final error response')

def send_packet(packet, deadline):
    for attempt in range(args.send_retries + 1):
        if time.monotonic() >= deadline:
            raise TimeoutError('Radio-enable deadline reached during telemetry')
        try:
            return command('AT+SQNSSENDEXT=1,128,0', timeout=15, payload=packet)
        except ModemRejected as error:
            if (error.payload_started or attempt == args.send_retries or
                    b'+CME ERROR: operation not supported' not in error.response):
                raise
            emit('UDP_RETRY pre-prompt rejection; retry=' + str(attempt + 1))
            time.sleep(min(2, max(0, deadline - time.monotonic())))

time.sleep(12); s.reset_input_buffer()
try:
    command('AT'); command('AT+CMEE=2'); command('AT+CFUN=0')
    if args.enable_seconds:
        command('AT+SQNBANDSEL=0,"standard","13"')
        command('AT+CGDCONT=1,"IP","srsapn"'); command('AT+CEREG=2')
        command('AT+COPS?'); command('AT+CFUN=1')
        deadline = time.monotonic() + args.enable_seconds
        while time.monotonic() < deadline:
            time.sleep(min(5, max(0, deadline - time.monotonic())))
            registration = command('AT+CEREG?')
            if args.udp_count and re.search(rb'\+CEREG:\s*2,[15](?:,|\r)', registration):
                command('AT+CGPADDR=1'); command('AT+CGACT?'); command('AT+CSQ')
                command('AT+SQNSCFG=1,1,300,90,100,1')
                command('AT+SQNSD=1,1,51000,"172.16.0.1",0,51001,1,0,0', timeout=15)
                sent = 0
                if args.socket_diagnostics: socket_status()
                for seq in range(args.udp_count):
                    if time.monotonic() >= deadline:
                        raise TimeoutError('Radio-enable deadline reached during telemetry')
                    packet = json.dumps(dict(run=args.run_id, seq=seq,
                        sent_utc=datetime.now(timezone.utc).isoformat(timespec='milliseconds')),
                        separators=(',', ':')).encode().ljust(128, b' ')
                    if len(packet) != 128: raise ValueError('Payload exceeds 128 bytes')
                    try:
                        send_packet(packet, deadline)
                    except RuntimeError:
                        emit('UDP_SUMMARY ' + json.dumps(dict(run=args.run_id, modem_accepted=sent,
                            requested=args.udp_count, payload_bytes=128, stopped_on_rejection=True)))
                        if args.socket_diagnostics:
                            for query in ('AT+SQNSS?', 'AT+CEREG?', 'AT+CGACT?'):
                                try: command(query)
                                except RuntimeError: continue
                                except TimeoutError: break
                        raise
                    sent += 1; emit('UDP modem-accepted seq=' + str(seq))
                    if args.socket_diagnostics: socket_status()
                    if seq + 1 < args.udp_count: time.sleep(1)
                emit('UDP_SUMMARY ' + json.dumps(dict(run=args.run_id, modem_accepted=sent,
                    payload_bytes=128, requested_interval_seconds=1)))
                settle = min(args.settle_seconds, max(0, deadline - time.monotonic()))
                if settle:
                    emit('UDP_SETTLE seconds=' + str(round(settle, 3)))
                    time.sleep(settle)
                command('AT+SQNSH=1')
                break
finally:
    # Reopen to reset the existing passthrough before recovery, even after a pending command.
    s.close(); s.open(); time.sleep(12); s.reset_input_buffer()
    try:
        command('AT'); command('AT+CFUN=0')
        command('AT+SQNBANDSEL=0,"standard","1,2,3,4,5,8,12,13,17,18,19,20,25,26,28,66"')
        state = command('AT+CFUN?')
        if b'+CFUN: 0' not in state: raise RuntimeError('Radio-off state not confirmed')
        emit('RESTORED original standard bands; CFUN 0 confirmed')
    finally:
        s.close()
