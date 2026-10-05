"""Record Yamcs EMBER telemetry; replay locally without transmitting packets."""
import argparse
import base64
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
from urllib.parse import urlencode
from urllib.request import urlopen

from codec import decode, DICTIONARY

FORMAT = 'ember-telemetry-session-v1'
NAMES = ('HEARTBEAT', 'POWER_STATUS')
DICTIONARY_HASH = hashlib.sha256(Path(__file__).with_name('dictionary.json').read_bytes()).hexdigest()


def timestamp(value):
    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if dt.tzinfo is None:
        raise ValueError('timestamp must include timezone')
    return dt


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec='milliseconds')


def api(url):
    with urlopen(url, timeout=10) as response:
        return json.load(response)


def fetch_packets(url, start, stop, *, page_size=100, request=api):
    """Follow per-name continuation tokens with the original bounded query."""
    records = []
    for name in NAMES:
        query = dict(name='/ember/' + name, start=start, stop=stop, order='asc', limit=page_size)
        seen_tokens = set()
        for _ in range(1000):
            page = request(url.rstrip('/') + '/api/archive/ember/packets?' + urlencode(query))
            records.extend(page.get('packets', []))
            token = page.get('continuationToken')
            if not token:
                break
            if token in seen_tokens:
                raise ValueError('repeated archive continuation token')
            seen_tokens.add(token)
            query['next'] = token
        else:
            raise ValueError('archive page bound exceeded; use a shorter window')
    return sorted(records, key=lambda r: (timestamp(r['receptionTime']), r['id']['name'], r['sequenceNumber']))


def validate(session):
    if session['format'] != FORMAT or session['dictionary_sha256'] != DICTIONARY_HASH:
        raise ValueError('unsupported session format or dictionary revision')
    start, stop = timestamp(session['start']), timestamp(session['stop'])
    if stop <= start:
        raise ValueError('invalid session window')
    decoded = []
    previous = None
    for record in session['packets']:
        raw = base64.b64decode(record['packet'], validate=True)
        packet = decode(raw)  # Verifies wire size, CRC, schema and identity.
        if packet['name'] not in NAMES or packet['header']['kind'] != DICTIONARY['kinds']['telemetry']:
            raise ValueError('session must contain only selected housekeeping telemetry')
        if record['id']['name'] != '/ember/' + packet['name'] or record['size'] != len(raw):
            raise ValueError('archive metadata does not match wire packet')
        if not start <= timestamp(record['generationTime']) < stop:
            raise ValueError('packet outside selected archive window')
        received = timestamp(record['receptionTime'])
        if previous is not None and received < previous:
            raise ValueError('session reception times are not ordered')
        previous = received
        decoded.append((record, packet))
    return decoded


def summary(session):
    decoded = validate(session)
    groups = {}
    for record, packet in decoded:
        key = (packet['name'], record['link'], packet['header']['source_boot_id'])
        groups.setdefault(key, []).append((record, packet))
    streams = []
    for (name, link, boot), items in groups.items():
        times = [timestamp(r['receptionTime']) for r, _ in items]
        qualities = Counter()
        for _, p in items:
            if name == 'POWER_STATUS':
                qualities['current_readout' if p['payload']['readout_valid'] else 'invalid_or_stale_readout'] += 1
                qualities['conversion_valid' if p['payload']['conversion_valid'] else 'conversion_unavailable'] += 1
        streams.append(dict(name=name, link=link, source_boot_id=boot, packets=len(items),
                            first_sequence=items[0][1]['sequence'], last_sequence=items[-1][1]['sequence'],
                            receive_span_seconds=(times[-1]-times[0]).total_seconds(), quality=dict(qualities)))
    return dict(format=FORMAT, origin=session['origin'], start=session['start'], stop=session['stop'],
                packet_count=len(decoded), streams=streams,
                note='Archive receive times; no latency or radio loss measurement. Replay is local only.')


def playback(session, speed=0, *, emit=print, sleep=time.sleep, monotonic=time.monotonic):
    decoded = validate(session)  # Validate the complete file before emitting anything.
    started = monotonic()
    first = timestamp(decoded[0][0]['receptionTime']) if decoded else None
    for record, packet in decoded:
        if speed:
            due = (timestamp(record['receptionTime'])-first).total_seconds()/speed
            remaining = started + due - monotonic()
            if remaining > 0:
                sleep(remaining)
        emit(json.dumps(dict(mode='OFFLINE_REPLAY', origin=session['origin'],
                             recorded_reception_time=record['receptionTime'], link=record['link'], decoded=packet)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='operation', required=True)
    record = sub.add_parser('record', help='Observe a bounded window and export its archived packets')
    record.add_argument('output', type=Path)
    record.add_argument('--url', default='http://192.168.1.251:8090')
    record.add_argument('--seconds', type=int, default=30)
    record.add_argument('--origin', required=True, help='Operator-declared hardware/transport context')
    record.add_argument('--page-size', type=int, default=100)
    for name in ('summary', 'replay'):
        command = sub.add_parser(name)
        command.add_argument('input', type=Path)
        if name == 'replay':
            command.add_argument('--speed', type=float, default=0, help='0 = immediate, 1 = recorded timing, 10 = 10x')
    args = parser.parse_args()
    if args.operation == 'record':
        if not 1 <= args.seconds <= 300 or not 1 <= args.page_size <= 1000:
            parser.error('seconds must be 1..300 and page size 1..1000')
        if args.output.exists():
            parser.error('output already exists; choose a new session filename')
        before = api(args.url.rstrip('/') + '/api/links/ember')
        start = utc_now()
        print('Recording archive window from ' + start, flush=True)
        time.sleep(args.seconds)
        stop = utc_now()
        # Allow the archive writer to finish this bounded window before querying.
        time.sleep(2)
        after = api(args.url.rstrip('/') + '/api/links/ember')
        session = dict(format=FORMAT, dictionary_sha256=DICTIONARY_HASH, origin=args.origin,
                       url=args.url, start=start, stop=stop, links_before=before, links_after=after,
                       packets=fetch_packets(args.url, start, stop, page_size=args.page_size))
        result = summary(session)
        if not result['packet_count']:
            raise ValueError('no selected telemetry in the recording window')
        args.output.parent.mkdir(parents=True, exist_ok=True)
        # Exclusive creation preserves existing sessions; private mode for operational metadata.
        import os
        fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'w') as out:
            json.dump(session, out, indent=2)
            out.write('\n')
        print(json.dumps(result, indent=2))
    else:
        session = json.loads(args.input.read_text())
        if args.operation == 'summary':
            print(json.dumps(summary(session), indent=2))
        else:
            import math
            if not math.isfinite(args.speed) or args.speed < 0:
                parser.error('speed must be finite and nonnegative')
            playback(session, args.speed)


if __name__ == '__main__':
    main()
