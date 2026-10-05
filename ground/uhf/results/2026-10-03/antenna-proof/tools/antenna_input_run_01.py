"""One finite antenna input check, SDRB receiver only; no IHU/CAN work."""
import shlex,subprocess,time
from pathlib import Path
out=Path('/tmp/ember-uhf-tools/antenna-input-01');out.mkdir(exist_ok=False)
def console(command):
    result=subprocess.run(['ssh','ngrabbs@192.168.1.252','python3 /tmp/console.py --command '+shlex.quote(command)+' --wait 1'],capture_output=True,text=True,check=True,timeout=20)
    with (out/'console.txt').open('a') as f:f.write(result.stdout)
    return result.stdout
console('python3 ~/ember-uhf-20261003/rx_antenna_probe_01.py > ~/ember-antenna-input-01.log 2>&1 &')
for _ in range(15):
    line=console('tail -c 2000 ~/ember-antenna-input-01.log')
    if 'INPUT_CAPTURE_READY {' in line:break
    if 'Traceback' in line:raise RuntimeError(line)
    time.sleep(.5)
else:raise RuntimeError('Input receiver did not become ready; no new ground transmission started')
command='cd ~/work/ember-uhf-20261003; PYTHONPATH=/home/ngrabbs/work/MSU_Cubesat/ember/ground/ember python3 -u repeater_probe.py --seconds 24 --channel 0 --tx-channel 0 --gain 40 --frequency 435100000 --uplink-frequency 435100000 --uplink-gain 20 --uplink-peak .1 --direct-check --transmit --output /home/ngrabbs/work/ember-uhf-evidence-20261003/antenna-proof/direct-01'
r=subprocess.run(['ssh','ngrabbs@192.168.1.251',command],capture_output=True,text=True,timeout=70)
(out/'ground.txt').write_text(r.stdout+r.stderr)
if r.returncode:raise RuntimeError('Ground positive-control check failed; see log')
print(console('tail -c 2000 ~/ember-antenna-input-01.log'),flush=True)
