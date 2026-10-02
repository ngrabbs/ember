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
args = parser.parse_args()
if not 0 <= args.udp_count <= 30: parser.error('Use 0..30 UDP packets')
if not re.fullmatch(r'[a-zA-Z0-9_-]{1,32}', args.run_id): parser.error('Use a simple run ID')
if args.udp_count and args.enable_seconds < 30: parser.error('UDP requires at least 30 enabled seconds')
if not 0 <= args.enable_seconds <= 120: parser.error('Use 0..120 seconds')
port = '/dev/serial/by-id/usb-Espressif_USB_JTAG_serial_debug_unit_24:58:7C:6F:0C:24-if00'
s = serial.Serial(); s.port = port; s.baudrate = 115200; s.timeout = .2
s.dtr = False; s.rts = False; s.open()
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
    if b'\r\nOK\r\n' not in output: raise RuntimeError('Modem rejected ' + cmd)
    if not payload_sent: raise RuntimeError('No data prompt for ' + cmd)
    return output

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
                for seq in range(args.udp_count):
                    if time.monotonic() >= deadline:
                        raise TimeoutError('Radio-enable deadline reached during telemetry')
                    packet = json.dumps(dict(run=args.run_id, seq=seq,
                        sent_utc=datetime.now(timezone.utc).isoformat(timespec='milliseconds')),
                        separators=(',', ':')).encode().ljust(128, b' ')
                    if len(packet) != 128: raise ValueError('Payload exceeds 128 bytes')
                    command('AT+SQNSSENDEXT=1,128,0', timeout=15, payload=packet)
                    sent += 1; emit('UDP modem-accepted seq=' + str(seq))
                    if seq + 1 < args.udp_count: time.sleep(1)
                command('AT+SQNSH=1')
                emit('UDP_SUMMARY ' + json.dumps(dict(run=args.run_id, modem_accepted=sent,
                    payload_bytes=128, requested_interval_seconds=1)))
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
