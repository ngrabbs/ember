"""User-requested 180-second HT transponder plus fresh IHU telemetry check."""
import subprocess,shlex,time,json
from pathlib import Path
out=Path('/tmp/ember-uhf-tools/handheld-proof-01');out.mkdir(exist_ok=False)
radio_started=False;ground=None;cadence=None;error=None

def console(command,sudo=False,wait=2):
    remote='python3 /tmp/console.py '+('--sudo ' if sudo else '')+'--command '+shlex.quote(command)+' --wait '+str(wait)
    r=subprocess.run(['ssh','ngrabbs@192.168.1.252',remote],capture_output=True,text=True,timeout=45,check=True)
    with (out/'console.txt').open('a') as f:f.write(r.stdout)
    return r.stdout

def pi(command):
    return subprocess.run(['ssh','ngrabbs@192.168.1.251',command],capture_output=True,text=True,check=True,timeout=15).stdout

def ready(command,tag,tries=10):
    for _ in range(tries):
        text=console(command)
        if tag in text:return
        if 'Traceback' in text:raise RuntimeError(text)
        time.sleep(.5)
    raise RuntimeError('Readiness gate failed: '+tag)

try:
    console('test ! -S ~/.cache/ember-binary-radio/control.sock && echo RADIO_CONTROL_CLOSED; sha256sum ~/ember-uhf-20261003/radio_service.py ~/ember-uhf-20261003/headroom_mix.so ~/ember-uhf-20261003/can_forward.py ~/ember-can-monitor-20261003/sdrb_can.py')
    console('sudo -n ip link set can1 up; python3 -u ~/ember-can-monitor-20261003/sdrb_can.py --interface can1 --seconds 220 --output ~/ember-handheld-can-01 > ~/ember-handheld-can-01.log 2>&1 &',sudo=True)
    ready('cat ~/ember-handheld-can-01.log','"ready": true')
    ground_cmd='cd ~/work/ember-uhf-20261003; PYTHONPATH=/home/ngrabbs/work/MSU_Cubesat/ember/ground/ember python3 -u libresdr_live_rx.py --seconds 210 --channel 0 --gain 40 --frequency 434200000 --forward --output /home/ngrabbs/work/ember-uhf-evidence-20261003/handheld-proof/rx-01 > /home/ngrabbs/work/ember-uhf-evidence-20261003/handheld-rx-01.log 2>&1'
    ground=subprocess.Popen(['ssh','ngrabbs@192.168.1.251',ground_cmd],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    for _ in range(20):
        text=pi('tail -c 4000 /home/ngrabbs/work/ember-uhf-evidence-20261003/handheld-rx-01.log')
        if 'UHF_RX_READY ' in text:break
        if ground.poll() is not None or 'Traceback' in text:raise RuntimeError('Ground receiver startup failed: '+text)
        time.sleep(.5)
    else:raise RuntimeError('Ground receiver not ready')
    console('python3 -u ~/ember-uhf-20261003/radio_service.py --mode transponder --rate 614400 --rx-frequency 435100000 --rx-gain 60 --tx-frequency 434200000 --tx-gain 70 --forward-scale 16 --forward-peak .25 --seconds 240 --output ~/ember-handheld-radio-01 --transmit > ~/ember-handheld-radio-01.log 2>&1 &')
    radio_started=True
    ready('tail -c 5000 ~/ember-handheld-radio-01.log','BINARY_RADIO_READY ',15)
    console('PYTHONPATH=~/ember-can-monitor-20261003 python3 -u ~/ember-uhf-20261003/can_forward.py --records ~/ember-handheld-can-01/packets.jsonl --output ~/ember-handheld-forward-01 --seconds 200 --limit 9 --service-socket ~/.cache/ember-binary-radio/control.sock --transmit > ~/ember-handheld-forward-01.log 2>&1 &')
    ready('cat ~/ember-handheld-forward-01.log','CAN_RF_FORWARD_READY ')
    (out/'ready.json').write_text(json.dumps(dict(ready_unix=time.time(),test_seconds=180,ht_tx_hz=435100000,rtl_rx_hz=434200000,telemetry_hz=434100000,telemetry_count=9,telemetry_interval=20))+'\n')
    print('HANDHELD_TEST_READY',flush=True)
    until=time.monotonic()+15
    while not (out/'go').exists():
        if time.monotonic()>until:raise RuntimeError('Window was not started within15s; stopping bounded session')
        time.sleep(.1)
    start=time.monotonic();start_unix=time.time()
    cadence_cmd='cd ~/work/ember-sdrb-adapter-20261003; python3 -u ground/uhf/ihu_cadence.py --port /dev/serial/by-id/usb-Raspberry_Pi_Pico_DF641455DB822427-if00 --interval 20 --count 9 --generate --output system/sdrb/evidence/handheld-proof-01'
    with (out/'ihu-cadence.txt').open('w') as log:
        cadence=subprocess.Popen(['ssh','ngrabbs@192.168.1.252',cadence_cmd],stdout=log,stderr=subprocess.STDOUT,text=True)
        print('HANDHELD_WINDOW_STARTED '+json.dumps(dict(unix=start_unix,seconds=180)),flush=True)
        for checkpoint in (45,90,135,180):
            while time.monotonic()-start<checkpoint:
                if cadence.poll() not in (None,0):raise RuntimeError('IHU cadence failed')
                if ground.poll() is not None:raise RuntimeError('Ground receiver ended before test window')
                time.sleep(.2)
            if checkpoint<180:
                text=console('python3 ~/ember-uhf-20261003/add_packet.py --status',wait=2)
                (out/f'status-{checkpoint}.txt').write_text(text)
                print('HANDHELD_PROGRESS '+str(checkpoint),flush=True)
        elapsed=time.monotonic()-start
        cadence.wait(timeout=10)
    (out/'window.json').write_text(json.dumps(dict(start_unix=start_unix,end_unix=time.time(),elapsed_seconds=elapsed,cadence_returncode=cadence.returncode),indent=2)+'\n')
    print('HANDHELD_WINDOW_ENDED',flush=True)
except BaseException as exc:
    error=str(exc);print('HANDHELD_ERROR '+error,flush=True);raise
finally:
    if radio_started:
        print(console('python3 ~/ember-uhf-20261003/add_packet.py --status; python3 ~/ember-uhf-20261003/add_packet.py --stop',wait=2),flush=True)
    if ground is not None:
        try:ground.wait(timeout=55)
        except subprocess.TimeoutExpired:print('GROUND_FINITE_TIMEOUT_INSPECT_OWNER',flush=True)
        (out/'ground.txt').write_text(pi('cat /home/ngrabbs/work/ember-uhf-evidence-20261003/handheld-rx-01.log'))
    console('while ps w | grep "[s]drb_can.py.*ember-handheld-can-01" >/dev/null; do sleep 1; done; echo CAN_MONITOR_ENDED; sudo -n ip link set can1 down; ip -details -statistics link show can1',sudo=True,wait=30)
    (out/'session.json').write_text(json.dumps(dict(error=error,ground_returncode=None if ground is None else ground.poll()),indent=2)+'\n')
    print('HANDHELD_CLEANUP_ENDED',flush=True)
