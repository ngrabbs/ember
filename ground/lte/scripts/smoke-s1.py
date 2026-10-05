#!/usr/bin/env python3
"""Bounded OAI/EPC startup check on ember-ground using a simulated radio only."""
import os
from pathlib import Path
import re
import subprocess
import time

os.umask(0o077)
base = Path.home() / 'work/ember-lte'
logs = base / 'logs'
logs.mkdir(exist_ok=True)
with (logs / 'epc-smoke.log').open('w') as epc_out:
    epc = subprocess.Popen([
        'sudo', '-n', 'timeout', '--signal=INT', '--kill-after=5', '25',
        str(base / 'srsRAN_4G/build-epc/srsepc/src/srsepc'), 'epc.conf',
    ], cwd=base / 'configs', stdout=epc_out, stderr=subprocess.STDOUT)
    time.sleep(2)
    with (logs / 'oai-s1-smoke.log').open('w') as oai_out:
        oai = subprocess.run([
            'sudo', '-n', 'timeout', '--signal=INT', '--kill-after=5', '15',
            './lte-softmodem', '-O', str(base / 'configs/enb.band13.emtc.conf'),
            '--rfsim', '--rfsimulator.serveraddr', 'server',
        ], cwd=base / 'openairinterface5g/build-lte', stdout=oai_out,
            stderr=subprocess.STDOUT)
    epc.wait(timeout=35)
print(f'Bounded run exit codes: OAI={oai.returncode}, EPC={epc.returncode}')
print('Exit 124 is expected when stopped by the timeout.')
for name in ['epc-smoke.log', 'oai-s1-smoke.log']:
    print(name)
    for line in (logs / name).read_text(errors='replace').splitlines():
        if re.search(r'S1 Setup|S1_SETUP|S1AP|ready|Assertion|failed|Error|error|Bye|SIB2/3 Encoding', line):
            line = re.sub(r'\x1b\[[0-9;]*m', '', line)
            print(re.sub(r'\b\d{14,22}\b', '[redacted]', line)[:300])
