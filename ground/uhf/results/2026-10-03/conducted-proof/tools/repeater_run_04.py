"""Prepared bounded RF proof; run only after operator confirms the TX antenna."""
import subprocess,shlex,time
from pathlib import Path
out=Path('/tmp/ember-uhf-tools/repeater-proof-04');out.mkdir(exist_ok=False)
receiver=None;service_ready=False

def console(command,sudo=False,wait=1):
    remote='python3 /tmp/console.py '+('--sudo ' if sudo else '')+'--command '+shlex.quote(command)+' --wait '+str(wait)
    r=subprocess.run(['ssh','ngrabbs@192.168.1.252',remote],capture_output=True,text=True,timeout=30,check=True)
    with (out/'console.txt').open('a') as f:f.write(r.stdout)
    return r.stdout

try:
    console('python3 ~/ember-uhf-20261003/radio_service.py --mode transponder --rate 614400 --rx-frequency 435100000 --rx-gain 60 --tx-frequency 434200000 --tx-gain 40 --seconds 120 --output ~/ember-repeater-radio-04 --transmit > ~/ember-repeater-radio-04.log 2>&1 &')
    for _ in range(15):
        text=console('tail -c 3000 ~/ember-repeater-radio-04.log')
        if 'BINARY_RADIO_READY {' in text:service_ready=True;break
        if 'Traceback' in text:raise RuntimeError(text)
        time.sleep(1)
    if not service_ready:raise RuntimeError('Radio startup failed; inspect log and owner before further action')
    remote='cd ~/work/ember-uhf-20261003; PYTHONPATH=/home/ngrabbs/work/MSU_Cubesat/ember/ground/ember python3 -u repeater_probe.py --seconds 60 --channel 0 --tx-channel 0 --gain 60 --frequency 434200000 --uplink-frequency 435100000 --uplink-gain 20 --uplink-peak .1 --forward --transmit --output /home/ngrabbs/work/ember-uhf-evidence-20261003/repeater-proof/rx-04'
    receiver=subprocess.Popen(['ssh','ngrabbs@192.168.1.251',remote],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    log=(out/'ground.txt').open('w')
    while True:
        line=receiver.stdout.readline();log.write(line);log.flush()
        if not line:raise RuntimeError('Ground RX exited during startup')
        if line.startswith('UPLINK_PROBE_READY'):break
    console('sudo -n ip link set can1 up; python3 ~/ember-can-monitor-20261003/sdrb_can.py --interface can1 --seconds 50 --output ~/ember-repeater-can-04 > ~/ember-repeater-can-04.log 2>&1 &',sudo=True)
    for _ in range(8):
        text=console('test -f ~/ember-repeater-can-04/packets.jsonl && echo CAN_RECORDS_READY')
        if any(x.strip()=='CAN_RECORDS_READY' for x in text.splitlines()):break
        time.sleep(.5)
    else:raise RuntimeError('CAN monitor not ready')
    console('PYTHONPATH=~/ember-can-monitor-20261003 python3 ~/ember-uhf-20261003/can_forward.py --records ~/ember-repeater-can-04/packets.jsonl --output ~/ember-repeater-forward-04 --seconds 60 --limit 4 --service-socket ~/.cache/ember-binary-radio/control.sock --transmit > ~/ember-repeater-forward-04.log 2>&1 &')
    for _ in range(8):
        text=console('cat ~/ember-repeater-forward-04.log')
        if 'CAN_RF_FORWARD_READY {' in text:break
        time.sleep(.5)
    else:raise RuntimeError('CAN forwarding not ready')
    remote='cd ~/work/ember-sdrb-adapter-20261003; python3 -u ground/uhf/ihu_cadence.py --port /dev/serial/by-id/usb-Raspberry_Pi_Pico_DF641455DB822427-if00 --interval 8 --count 4 --generate --output system/sdrb/evidence/repeater-proof-04'
    r=subprocess.run(['ssh','ngrabbs@192.168.1.252',remote],capture_output=True,text=True,timeout=75)
    (out/'ihu-cadence.txt').write_text(r.stdout+r.stderr)
    if r.returncode:raise RuntimeError('IHU cadence failed; see log')
    for line in receiver.stdout:log.write(line);log.flush()
    receiver.wait();log.close()
    if receiver.returncode:raise RuntimeError('Ground RX failed')
finally:
    # A failed connection still has finite radio/RX/CAN lifetimes. Do not kill
    # another console/radio owner or silently retry an uncertain transmission.
    if service_ready:
        text=console('python3 ~/ember-uhf-20261003/add_packet.py --status; python3 ~/ember-uhf-20261003/add_packet.py --stop',wait=2)
        print(text,flush=True)
    # Let this finite monitor end BEFORE taking its interface down.
    console('while ps w | grep "[s]drb_can.py.*ember-repeater-can-04" >/dev/null; do sleep 1; done; echo CAN_MONITOR_ENDED; sudo -n ip link set can1 down; ip -details -statistics link show can1',sudo=True,wait=20)
