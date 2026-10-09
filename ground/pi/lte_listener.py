#!/usr/bin/env python3
"""Persistent, validated native EPS UDP -> Yamcs; this never starts a radio."""
import argparse
from collections import OrderedDict
from datetime import datetime, timezone
import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import signal
import socket
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent / 'ember'))
from codec import PacketError
from lte_receiver import validate


def run(args):
    running = True
    def stop(signum, frame):
        nonlocal running
        running = False
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    args.log.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger('packets')
    logger.setLevel(logging.INFO)
    handler = RotatingFileHandler(args.log, maxBytes=10_000_000, backupCount=3)
    logger.addHandler(handler)
    seen = OrderedDict()
    received = rejected = duplicates = 0
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as incoming, \
            socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as forward:
        incoming.bind(('0.0.0.0', 51000))
        incoming.settimeout(1)
        print('Listening UDP 51000 -> Yamcs 127.0.0.1:10018; no RF transmit', flush=True)
        while running:
            try:
                packet, peer = incoming.recvfrom(4096)
            except socket.timeout:
                continue
            if peer != (args.peer, 51001):
                rejected += 1
                continue
            try:
                decoded = validate(packet)
            except (PacketError, KeyError, ValueError):
                rejected += 1
                continue
            now = time.monotonic()
            while seen and (next(iter(seen.values())) < now - 120 or len(seen) >= 4096):
                seen.popitem(last=False)
            key = (decoded['header']['source_boot_id'], decoded['sequence'],
                   decoded['header']['uptime_ms'])
            if key in seen:
                duplicates += 1
                continue
            forward.sendto(packet, ('127.0.0.1', 10018))
            seen[key] = now
            received += 1
            logger.info(json.dumps(dict(received_utc=datetime.now(timezone.utc).isoformat(),
                                       peer=peer, hex=packet.hex(), decoded=decoded)))
            print(f'Forwarded POWER_STATUS sequence={decoded["sequence"]} '
                  f'received={received} rejected={rejected} duplicates={duplicates}', flush=True)
    handler.close()
    print(f'Stopped received={received} rejected={rejected} duplicates={duplicates}', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--peer', default='172.16.0.2')
    parser.add_argument('--log', type=Path, default=Path('/var/lib/ember-lte-listener/packets.jsonl'))
    args = parser.parse_args()
    socket.inet_aton(args.peer)
    run(args)
