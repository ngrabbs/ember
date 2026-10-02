#!/usr/bin/env python3
"""Receive Walter's numbered bench UDP datagrams on the Pi; no latency inference."""
import argparse
from datetime import datetime, timezone
import json
import re
import socket
import time

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('run_id')
parser.add_argument('--count', type=int, default=10)
parser.add_argument('--seconds', type=int, default=150)
args = parser.parse_args()
if not re.fullmatch(r'[a-zA-Z0-9_-]{1,32}', args.run_id): parser.error('Use a simple run ID')
if not 1 <= args.count <= 30 or not 1 <= args.seconds <= 300: parser.error('Use bounded count/duration')
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('0.0.0.0', 51000)); sock.settimeout(1)
deadline = time.monotonic() + args.seconds
seen = set(); duplicates = 0; out_of_order = 0; highest = -1; sizes = set(); peers = set()
first_rx = None; last_rx = None
print('READY UDP port=51000 run=' + args.run_id, flush=True)
while time.monotonic() < deadline:
    try: data, peer = sock.recvfrom(4096)
    except socket.timeout: continue
    try: packet = json.loads(data)
    except (ValueError, UnicodeDecodeError): continue
    if not isinstance(packet, dict) or packet.get('run') != args.run_id: continue
    seq = packet.get('seq')
    if type(seq) is not int or not 0 <= seq < args.count: continue
    now = time.monotonic()
    first_rx = now if first_rx is None else first_rx; last_rx = now
    if seq in seen: duplicates += 1
    else:
        if seq < highest: out_of_order += 1
        seen.add(seq); highest = max(highest, seq)
    sizes.add(len(data)); peers.add(peer[0])
    print(json.dumps(dict(received_utc=datetime.now(timezone.utc).isoformat(timespec='milliseconds'),
        run=args.run_id, seq=seq, bytes=len(data), source_ip=peer[0])), flush=True)
    if len(seen) == args.count: break
sock.close()
print('SUMMARY ' + json.dumps(dict(run=args.run_id, expected=args.count, unique_received=len(seen),
    missing_sequences=sorted(set(range(args.count)) - seen), duplicates=duplicates,
    out_of_order=out_of_order, payload_sizes=sorted(sizes), source_ips=sorted(peers),
    receive_span_seconds=None if first_rx is None else round(last_rx-first_rx, 3),
    observation_ended_on_all_packets=len(seen)==args.count)), flush=True)
