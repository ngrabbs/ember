"""Two finite supervised RF sessions: manual restart and owned forwarder fault."""
import subprocess,shlex,time,json
from pathlib import Path
out=Path('/tmp/ember-uhf-tools/supervision-proof-01');out.mkdir(exist_ok=False)

def console(command,sudo=False,wait=2):
    remote='python3 /tmp/console.py '+('--sudo ' if sudo else '')+'--command '+shlex.quote(command)+' --wait '+str(wait)
    r=subprocess.run(['ssh','ngrabbs@192.168.1.252',remote],capture_output=True,text=True,check=True,timeout=40)
    with (out/'console.txt').open('a') as f:f.write(r.stdout)
    return r.stdout

def pi(command):
    r=subprocess.run(['ssh','ngrabbs@192.168.1.251',command],capture_output=True,text=True,check=True,timeout=20)
    with (out/'ground-console.txt').open('a') as f:f.write(r.stdout+r.stderr)
    return r.stdout

def snapshot(role):
    root='ember-uhf-sdrb' if role=='sdrb' else 'ember-uhf-ground'
    code='import pathlib,json; p=pathlib.Path.home()/".cache/'+root+'/status.json"; print("SUPERVISOR:"+json.dumps(json.loads(p.read_text()) if p.exists() else None))'
    cmd='python3 -c '+shlex.quote(code)
    text=console(cmd) if role=='sdrb' else pi(cmd)
    for line in text.splitlines():
        if line.startswith('SUPERVISOR:'):return json.loads(line[11:])
    raise RuntimeError('Supervisor snapshot missing')

def wait(role,state):
    end=time.monotonic()+40
    while time.monotonic()<end:
        s=snapshot(role)
        if s and s['state']==state:return s
        if s and s['state']=='FAILED' and state!='FAILED':raise RuntimeError(s)
        time.sleep(.3)
    raise RuntimeError(role+' did not reach '+state)

runs=[];error=None
try:
    console('sudo -n ip link set can1 up; systemctl --user set-property --runtime ember-uhf-sdrb.service RuntimeMaxSec=120s; systemctl --user show ember-uhf-sdrb.service -p RuntimeMaxUSec',sudo=True)
    pi('systemctl --user set-property --runtime ember-uhf-ground.service RuntimeMaxSec=120s; systemctl --user show ember-uhf-ground.service -p RuntimeMaxUSec')
    for index in (1,2):
        pi('systemctl --user --no-block start ember-uhf-ground.service')
        g=wait('ground','RUNNING')
        console('systemctl --user --no-block start ember-uhf-sdrb.service')
        s=wait('sdrb','RUNNING')
        (out/f'start-{index}.json').write_text(json.dumps(dict(sdrb=s,ground=g),indent=2)+'\n')
        print('SUPERVISED_NATIVE_RF_READY '+str(index),flush=True)
        remote='cd ~/work/ember-sdrb-adapter-20261003; python3 -u ground/uhf/ihu_autotelem.py --port /dev/serial/by-id/usb-Raspberry_Pi_Pico_DF641455DB822427-if00 --period 20 --seconds 45 --arm --output system/sdrb/evidence/supervision-native-'+str(index)
        with (out/f'ihu-{index}.txt').open('w') as f:r=subprocess.run(['ssh','ngrabbs@192.168.1.252',remote],stdout=f,stderr=subprocess.STDOUT,text=True,timeout=65)
        if r.returncode:raise RuntimeError('Native IHU observation failed')
        console('python3 ~/ember-uhf-20261003/add_packet.py --status')
        if index==1:
            console('systemctl --user --no-block stop ember-uhf-sdrb.service')
            stopped=wait('sdrb','STOPPED')
        else:
            current=snapshot('sdrb');pid=current['children']['forward']['pid']
            if current['run_id']!=s['run_id'] or current['state']!='RUNNING':raise RuntimeError('Wrong supervisor owner')
            console('kill -TERM '+str(pid))
            stopped=wait('sdrb','FAILED')
            if 'forward exited unexpectedly' not in stopped['error']:raise RuntimeError('Wrong fault outcome')
        pi('systemctl --user --no-block stop ember-uhf-ground.service')
        gstopped=wait('ground','STOPPED')
        record=dict(index=index,sdrb=stopped,ground=gstopped)
        runs.append(record);(out/f'result-{index}.json').write_text(json.dumps(record,indent=2)+'\n')
        print('SUPERVISED_RUN_STOPPED '+json.dumps(dict(index=index,sdrb_state=stopped['state'],ground_state=gstopped['state'])),flush=True)
    if runs[0]['sdrb']['run_id']==runs[1]['sdrb']['run_id']:raise RuntimeError('No new restart identity')
except BaseException as exc:error=str(exc);print('SUPERVISION_ERROR '+error,flush=True);raise
finally:
    console('systemctl --user --no-block stop ember-uhf-sdrb.service')
    pi('systemctl --user --no-block stop ember-uhf-ground.service')
    # Wait for owned CAN readers to close before restoring the bench interface.
    console('while ps w | grep "[s]drb_can.py.*ember-uhf-supervised" >/dev/null; do sleep 1; done; sudo -n ip link set can1 down; systemctl --user set-property --runtime ember-uhf-sdrb.service RuntimeMaxSec=0; systemctl --user reset-failed ember-uhf-sdrb.service; systemctl --user show ember-uhf-sdrb.service -p ActiveState -p UnitFileState -p RuntimeMaxUSec',sudo=True,wait=5)
    pi('systemctl --user set-property --runtime ember-uhf-ground.service RuntimeMaxSec=0; systemctl --user reset-failed ember-uhf-ground.service; systemctl --user show ember-uhf-ground.service -p ActiveState -p UnitFileState -p RuntimeMaxUSec')
    (out/'session.json').write_text(json.dumps(dict(error=error,runs=runs),indent=2)+'\n')
    print('SUPERVISION_CLEANUP_DONE',flush=True)
