"""Finite native IHU timer -> unchanged SDRB transponder -> Yamcs proof."""
import subprocess,shlex,time,json
from pathlib import Path
out=Path('/tmp/ember-uhf-tools/autotelem-proof-01');out.mkdir(exist_ok=False)
service_ready=False;receiver=None;error=None

def console(command,sudo=False,wait=2):
    remote='python3 /tmp/console.py '+('--sudo ' if sudo else '')+'--command '+shlex.quote(command)+' --wait '+str(wait)
    r=subprocess.run(['ssh','ngrabbs@192.168.1.252',remote],capture_output=True,text=True,timeout=45,check=True)
    with (out/'console.txt').open('a') as f:f.write(r.stdout)
    return r.stdout

try:
    console('python3 -u ~/ember-uhf-20261003/radio_service.py --mode transponder --rate 614400 --rx-frequency 435100000 --rx-gain 60 --tx-frequency 434200000 --tx-gain 70 --forward-scale 16 --forward-peak .25 --seconds 170 --output ~/ember-autotelem-radio-01 --transmit > ~/ember-autotelem-radio-01.log 2>&1 &')
    for _ in range(15):
        text=console('tail -c 5000 ~/ember-autotelem-radio-01.log')
        if 'BINARY_RADIO_READY ' in text:service_ready=True;break
        if 'Traceback' in text:raise RuntimeError('Radio startup failed')
        time.sleep(.5)
    if not service_ready:raise RuntimeError('Radio readiness gate failed')
    remote='cd ~/work/ember-uhf-20261003; PYTHONPATH=/home/ngrabbs/work/MSU_Cubesat/ember/ground/ember python3 -u libresdr_live_rx.py --seconds 140 --channel 0 --gain 40 --frequency 434200000 --forward --output /home/ngrabbs/work/ember-uhf-evidence-20261003/native-autotelem/rx-01'
    receiver=subprocess.Popen(['ssh','ngrabbs@192.168.1.251',remote],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    groundlog=(out/'ground.txt').open('w')
    while True:
        line=receiver.stdout.readline();groundlog.write(line);groundlog.flush()
        if not line:raise RuntimeError('Ground receiver exited during startup')
        if line.startswith('UHF_RX_READY '):break
    console('sudo -n ip link set can1 up; python3 -u ~/ember-can-monitor-20261003/sdrb_can.py --interface can1 --seconds 140 --output ~/ember-autotelem-can-01 > ~/ember-autotelem-can-01.log 2>&1 &',sudo=True)
    for _ in range(8):
        text=console('cat ~/ember-autotelem-can-01.log')
        if '"ready": true' in text:break
        time.sleep(.5)
    else:raise RuntimeError('CAN monitor not ready')
    console('PYTHONPATH=~/ember-can-monitor-20261003 python3 -u ~/ember-uhf-20261003/can_forward.py --records ~/ember-autotelem-can-01/packets.jsonl --output ~/ember-autotelem-forward-01 --seconds 130 --limit 4 --service-socket ~/.cache/ember-binary-radio/control.sock --transmit > ~/ember-autotelem-forward-01.log 2>&1 &')
    for _ in range(8):
        text=console('cat ~/ember-autotelem-forward-01.log')
        if 'CAN_RF_FORWARD_READY ' in text:break
        time.sleep(.5)
    else:raise RuntimeError('CAN forwarding not ready')
    print('NATIVE_AUTOTELEM_RF_PATH_READY',flush=True)
    remote='cd ~/work/ember-sdrb-adapter-20261003; python3 -u ground/uhf/ihu_autotelem.py --port /dev/serial/by-id/usb-Raspberry_Pi_Pico_DF641455DB822427-if00 --period 20 --seconds 65 --arm --output system/sdrb/evidence/native-autotelem-01'
    with (out/'ihu-native.txt').open('w') as log:
        r=subprocess.run(['ssh','ngrabbs@192.168.1.252',remote],stdout=log,stderr=subprocess.STDOUT,text=True,timeout=85)
    if r.returncode:raise RuntimeError('Native IHU timer observation failed')
    print('NATIVE_THREE_PACKETS_DONE_TIMER_OFF',flush=True)
    with (out/'ihu-closed-usb.txt').open('w') as log:
        r=subprocess.run(['ssh','ngrabbs@192.168.1.252','python3 -u /tmp/autotelem_closed_usb.py'],stdout=log,stderr=subprocess.STDOUT,text=True,timeout=40)
    if r.returncode:raise RuntimeError('Closed USB check failed')
    print('CLOSED_USB_PERIOD_DONE_TIMER_OFF',flush=True)
except BaseException as exc:error=str(exc);print('NATIVE_AUTOTELEM_ERROR '+error,flush=True);raise
finally:
    if service_ready:
        text=console('python3 ~/ember-uhf-20261003/add_packet.py --status; python3 ~/ember-uhf-20261003/add_packet.py --stop',wait=2)
        print(text,flush=True)
    if receiver is not None:
        for line in receiver.stdout:groundlog.write(line);groundlog.flush()
        receiver.wait();groundlog.close()
    console('while ps w | grep "[s]drb_can.py.*ember-autotelem-can-01" >/dev/null; do sleep 1; done; echo CAN_MONITOR_ENDED; sudo -n ip link set can1 down; ip -details -statistics link show can1',sudo=True,wait=15)
    (out/'session.json').write_text(json.dumps(dict(error=error,ground_returncode=None if receiver is None else receiver.returncode),indent=2)+'\n')
    print('NATIVE_AUTOTELEM_CLEANUP_ENDED',flush=True)
