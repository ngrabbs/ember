"""Ten isolated, bounded native EPS LTE trials using existing bench images.

Run on the operator computer with SSH access to both hosts. Full radio logs and
pcaps stay private on the ground host; evidence contains only packet/status data.
"""
import argparse
import base64
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import shlex
import subprocess
import time
from urllib.request import urlopen

GROUND = 'ngrabbs@ember-ground.local'
IHU_HOST = 'ngrabbs@192.168.1.252'
PORT = '/dev/serial/by-id/usb-Raspberry_Pi_Pico_DF641455DB822427-if00'
REMOTE = '/media/ngrabbs/BACKUP-A/ember-walter-bridge'
API = 'http://192.168.1.251:8090/api/'
PROFILE = 'enb.band13.emtc.ce300tx20diag.conf'


def utc():
    return datetime.now(timezone.utc).isoformat()


def ssh(host, command):
    return ['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=5', host, command]


def remote_json(host, path):
    value = subprocess.check_output(ssh(host, 'cat '+shlex.quote(path)), timeout=15)
    return json.loads(value)


def compare(host, received, archive):
    submitted = [p['hex'] for p in host.get('modem_accepted', [])]
    radio = [p['hex'] for p in received.get('packets', [])]
    stored = {base64.b64decode(p['packet']).hex()
              for p in archive.get('packets') or archive.get('packet', [])}
    # A successful run needs its own submitted packet in both independent sinks.
    exact = len(submitted) == len(radio) == 1 and submitted[0] == radio[0]
    archived = exact and radio[0] in stored
    off = bool(re.search(r'LTE_STATUS state=0 .*window_ms=0\b',
                         host.get('final_modem_status', '')))
    return dict(modem_accepted=len(submitted), radio_received=len(radio),
                receiver_rejected=received.get('rejected', 0),
                bytes_match=exact, archive_match=archived, off_confirmed=off,
                success=bool(archived and off), ready_elapsed_s=host.get('ready_elapsed_s'))


def radio_exit_status(log):
    """The wrapper can exit zero even when its eNodeB child aborts."""
    return {name: int(matches[-1]) if matches else None
            for name in ('oai', 'epc')
            for matches in [re.findall(r'\b'+name+r' exit=(-?\d+)\b', log)]}


def run(args):
    args.output.mkdir(parents=True, exist_ok=True)
    report = dict(started_utc=utc(), profile=PROFILE, requested=10, trials=[],
                  diagnostics=args.diagnostics,
                  method='One fresh EPS packet per separate cell/modem window; '
                  '120-second modem window, 15-second settle, no send retries.')
    previous=args.output/'report.json'
    if previous.exists():
        report=json.loads(previous.read_text())
        if report.get('diagnostics', False) != args.diagnostics:
            raise ValueError('Resume must preserve the diagnostic setting')
    for number in range(len(report['trials'])+1, 11):
        label = f'{args.label}-{number:02d}'
        print(f'BEGIN {number}/10 {label}', flush=True)
        directory = args.output/label
        directory.mkdir(exist_ok=True)
        started = time.monotonic()
        record = dict(number=number, label=label, started_utc=utc())
        procs = []
        files = []
        def launch(host, cmd, name):
            out = (directory/(name+'.log')).open('w')
            files.append(out)
            proc = subprocess.Popen(ssh(host, cmd), stdout=out, stderr=subprocess.STDOUT)
            procs.append(proc)
            return proc
        try:
            receiver = launch(GROUND,
                'cd ~/work/MSU_Cubesat/ember/ground/ember && python3 -u lte_receiver.py '
                f'--count 1 --seconds 165 --output ~/work/ember-lte/logs/{label}-received.json',
                'receiver')
            radio = launch(GROUND,
                f'python3 ~/work/ember-lte/run-radio-check.py {label} --seconds 150 --config {PROFILE}',
                'radio')
            capture = launch(GROUND,
                'sudo -n timeout --signal=INT 155 tcpdump -i any -s0 -U '
                f'-w ~/work/ember-lte/logs/{label}-udp.pcap "udp port 2152 or udp port 51000"',
                'capture')
            ready = False
            for _ in range(40):
                if 'Starting steady-state operation' in (directory/'radio.log').read_text():
                    ready = True
                    break
                if radio.poll() is not None:
                    break
                time.sleep(1)
            if not ready:
                raise RuntimeError('Ground cell did not reach steady state; no modem window started')
            host_proc = launch(IHU_HOST,
                f'cd {REMOTE}/host-tests && python3 -u eps_lte_trial.py '
                f'--seconds 120 --count 1 --settle 15 --port {PORT} '
                + ('--diagnostics ' if args.diagnostics else '') +
                f'--output {REMOTE}/{label}', 'host')
            record['host_exit'] = host_proc.wait(timeout=145)
            host = remote_json(IHU_HOST, f'{REMOTE}/{label}/trial.json')
            record['host'] = host
            record['off_confirmed'] = compare(host,{}, {})['off_confirmed']
            # Finish all bounded network processes before the next independent cell.
            record['receiver_exit'] = receiver.wait(timeout=180)
            record['radio_exit'] = radio.wait(timeout=180)
            record['capture_exit'] = capture.wait(timeout=180)
            received = remote_json(GROUND, f'/home/ngrabbs/work/ember-lte/logs/{label}-received.json')
            archive = json.load(urlopen(API+'archive/ember-lte/packets?name=/ember/POWER_STATUS&limit=100', timeout=10))
            record.update(compare(host, received, archive))
            record['radio_children'] = radio_exit_status((directory/'radio.log').read_text())
            record['delivery_success'] = record['success']
            record['normal_process_exits'] = (record['host_exit']==0 and record['receiver_exit']==0 and record['radio_exit']==0 and record['capture_exit']==124 and record['radio_children']=={'oai':124,'epc':124})
            record['success'] = record['success'] and record['normal_process_exits']
            record['ground_receiver'] = received
            record['matching_archive'] = [p for p in archive.get('packets') or archive.get('packet', [])
                if base64.b64decode(p['packet']).hex() in [x['hex'] for x in received.get('packets', [])]]
        except Exception as error:
            record['error'] = str(error)
            record['success'] = False
        finally:
            # Every remote RF command has its own timeout, independent of SSH.
            for proc in procs:
                if proc.poll() is None:
                    try:
                        proc.wait(timeout=180)
                    except subprocess.TimeoutExpired:
                        proc.terminate()
                        proc.wait(timeout=10)
            for out in files:
                out.close()
            record['duration_s'] = round(time.monotonic()-started, 3)
            record['finished_utc'] = utc()
            report['trials'].append(record)
            report['successful'] = sum(t.get('success', False) for t in report['trials'])
            report['completed'] = len(report['trials'])
            (args.output/'report.json').write_text(json.dumps(report, indent=2)+'\n')
            print('RESULT '+json.dumps({k:v for k,v in record.items()
                  if k not in ('host','ground_receiver','matching_archive')}), flush=True)
        if not record.get('off_confirmed'):
            print('STOP: modem OFF could not be verified; remaining runs not started.', flush=True)
            break
    report['finished_utc'] = utc()
    (args.output/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    print(f"SUMMARY {report['successful']}/{report['completed']} full-chain successes", flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--label', required=True)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--diagnostics', action='store_true', help='Capture cached modem diagnostics consistently in every run.')
    args = parser.parse_args()
    if not re.fullmatch(r'[a-zA-Z0-9_-]+', args.label):
        parser.error('Label must contain only letters, digits, underscores and hyphens')
    run(args)
