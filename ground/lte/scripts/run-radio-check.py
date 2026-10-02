#!/usr/bin/env python3
"""Run on ember-ground: bounded OAI/EPC RF test with private UTC-stamped logs."""
import argparse
from datetime import datetime, timezone
import os
from pathlib import Path
import re
import subprocess
import threading

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('label')
parser.add_argument('--seconds', type=int, default=55)
parser.add_argument('--config', default='enb.band13.emtc.tx30.conf')
args = parser.parse_args()
if not re.fullmatch(r'[a-zA-Z0-9_-]+', args.label) or not 15 <= args.seconds <= 180:
    parser.error('Use a simple label and a duration between 15 and 180 seconds')
if Path(args.config).name != args.config:
    parser.error('Config must name a file in the runtime config directory')
os.umask(0o077)
base = Path.home() / 'work/ember-lte'
logs = base / 'logs'
logs.mkdir(exist_ok=True)
pattern = re.compile(r'ALL RUs ready|steady-state|Assertion|Msg4 Retransmissions|No existing UE ULSCH|Decoding UL CCCH|Generating RRCConnectionSetup|Generating RAR BR|S1 Setup Response|Scheduling BL/CE Msg4 retry|BL/CE Msg4 retries exhausted|Msg4 acknowledged|Bye')
lock = threading.Lock()
def stamp():
    return datetime.now(timezone.utc).isoformat(timespec='milliseconds')
def collect(proc, name):
    with (logs / f'{args.label}-{name}.log').open('w') as out:
        out.write(f'{stamp()} START pid={proc.pid}\n'); out.flush()
        for line in proc.stdout:
            line = re.sub(r'\x1b\[[0-9;]*m', '', line)
            entry = f'{stamp()} {line}'
            out.write(entry); out.flush()
            if pattern.search(line):
                with lock:
                    print(re.sub(r'\b\d{14,22}\b', '[redacted]', entry.rstrip())[:350], flush=True)
        code = proc.wait()
        out.write(f'{stamp()} EXIT code={code}\n')
        with lock:
            print(f'{stamp()} {name} exit={code}', flush=True)

common = ['sudo', '-n', 'env', f'UHD_IMAGES_DIR={base / "images"}',
          'stdbuf', '-oL', '-eL', 'timeout', '--signal=INT', '--kill-after=5']
epc = subprocess.Popen(common + [str(args.seconds + 5),
    str(base / 'srsRAN_4G/build-epc/srsepc/src/srsepc'), 'epc.conf'],
    cwd=base / 'configs', stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    text=True, errors='replace')
oai = subprocess.Popen(common + [str(args.seconds), './lte-softmodem', '-O',
    str(base / 'configs' / args.config), '--parallel-config', 'PARALLEL_SINGLE_THREAD',
    '--worker-config', 'WORKER_DISABLE'], cwd=base / 'openairinterface5g/build-lte',
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, errors='replace')
threads = [threading.Thread(target=collect, args=(epc, 'epc')),
           threading.Thread(target=collect, args=(oai, 'oai'))]
for thread in threads: thread.start()
for thread in threads: thread.join()
print('Timeout exit 124 is expected; assertions/other exit codes need inspection.', flush=True)
