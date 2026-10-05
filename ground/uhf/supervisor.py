#!/usr/bin/env python3
"""Opt-in home-directory supervision; no RF retry or automatic startup policy."""
import argparse,ctypes,fcntl,json,os,shutil,signal,socket,subprocess,sys,time,uuid
from pathlib import Path
from radio_control import request as radio_request,default_socket


def atomic(path,data):
    temporary=path.with_suffix('.tmp');temporary.write_text(json.dumps(data,indent=2)+'\n');temporary.replace(path)

def private(path):
    path.mkdir(parents=True,exist_ok=True,mode=0o700)
    st=path.lstat()
    if path.is_symlink() or st.st_uid!=os.getuid() or st.st_mode&0o077:raise ValueError('Owned mode0700 directory required: '+str(path))

def size_bytes(root):
    return sum(x.stat().st_size for x in root.rglob('*') if x.is_file() and not x.is_symlink())

def prune(root,keep):
    completed=[]
    for p in root.iterdir():
        if p.is_symlink() or not p.is_dir() or not (p/'.ember-uhf-run').is_file():continue
        try:
            status=json.loads((p/'supervisor.json').read_text())
            if status['state'] in ('STOPPED','FAILED'):completed.append(p)
        except (OSError,ValueError,KeyError):continue
    for p in sorted(completed,key=lambda p:p.name)[:-keep]:shutil.rmtree(p)

def load(path):
    c=json.loads(path.read_text())
    if c['role'] not in ('ground','sdrb'):raise ValueError('Role must be ground or sdrb')
    for key in ('state_dir','runs_dir','app_dir','ember_dir'):c[key]=str(Path(c[key]).expanduser().resolve())
    if c['role']=='sdrb':c['can_monitor']=str(Path(c['can_monitor']).expanduser().resolve())
    if not 1<=c.get('keep_runs',5)<=20 or not 16<=c.get('quota_mib',128)<=1024:raise ValueError('Invalid retention/quota')
    return c

def commands(c,run):
    app=Path(c['app_dir']);python=sys.executable
    if c['role']=='ground':
        return [('receiver',[python,'-u',str(app/'libresdr_live_rx.py'),'--seconds','0','--no-iq',
            '--retained-packets','64','--fail-on-error','--channel','0','--gain','40','--frequency','434200000',
            '--forward','--output',str(run/'receiver')],'UHF_RX_READY ')]
    interface=c.get('can_interface','can1')
    # Interface configuration belongs to the operator/AMSAT, outside this supervisor.
    flags=int((Path('/sys/class/net')/interface/'flags').read_text().strip(),16)
    if not flags&1:raise RuntimeError(interface+' is down; configure/enable CAN before starting')
    plan=[('radio',[python,'-u',str(app/'radio_service.py'),'--mode','transponder','--rate','614400',
        '--rx-frequency','435100000','--rx-gain','60','--tx-frequency','434200000','--tx-gain','70',
        '--forward-scale','16','--forward-peak','.25','--seconds','0','--output',str(run/'radio'),'--transmit'],'BINARY_RADIO_READY '),
        ('can',[python,'-u',c['can_monitor'],'--interface',interface,'--seconds','0','--output',str(run/'can')],'"ready": true'),
        ('forward',[python,'-u',str(app/'can_forward.py'),'--records',str(run/'can/packets.jsonl'),
         '--output',str(run/'forward'),'--seconds','0','--limit','0','--service-socket',str(default_socket()),'--transmit'],'CAN_RF_FORWARD_READY ')]
    # Finish Python imports and passive CAN setup before starting the timed
    # sample stream. The IHU timer is armed separately after all readiness gates.
    return sorted(plan,key=lambda child:('can','forward','radio').index(child[0]))

def tail(path):
    with path.open('rb') as f:f.seek(max(0,path.stat().st_size-16384));return f.read().decode('utf-8','replace')

def child_setup(parent):
    def setup():
        # The owner disappearing must not leave an orphan transmitter.
        if ctypes.CDLL(None,use_errno=True).prctl(1,signal.SIGTERM,0,0,0)!=0:raise OSError('PR_SET_PDEATHSIG failed')
        if os.getppid()!=parent:os.kill(os.getpid(),signal.SIGTERM)
    return setup

def serve(a):
    c=load(a.config)
    if c['role']=='sdrb' and not a.transmit:raise ValueError('SDRB requires explicit --transmit')
    state=Path(c['state_dir']);root=Path(c['runs_dir']);private(state);private(root)
    lock=(state/'owner.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    prune(root,c.get('keep_runs',5))
    run=root/(time.strftime('%Y%m%dT%H%M%SZ',time.gmtime())+'-'+uuid.uuid4().hex[:12]);private(run)
    (run/'.ember-uhf-run').write_text('Owned EMBER supervisor evidence\n');atomic(run/'config.json',c)
    children={};logs={};stopping=False;reason=None;failure=None;sock=None;bound=False
    record=dict(state='STARTING',role=c['role'],pid=os.getpid(),run=str(run),run_id=run.name,
        config=str(a.config.resolve()),lease_seconds=a.seconds,children={},reason=None,error=None)
    def publish():
        record['children']={name:dict(pid=p.pid,returncode=p.poll()) for name,p in children.items()}
        record['updated_unix']=time.time();atomic(run/'supervisor.json',record);atomic(state/'status.json',record)
    def stop_signal(*_):
        nonlocal stopping,reason
        stopping=True;reason='signal'
    for sig in (signal.SIGINT,signal.SIGTERM):signal.signal(sig,stop_signal)
    try:
        publish();sock=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);path=state/'control.sock'
        if path.exists():
            if not path.is_socket():raise ValueError('Refusing non-socket control path')
            path.unlink()
        sock.bind(str(path));bound=True;os.chmod(path,0o600);sock.listen(2);sock.settimeout(.2)
        env=os.environ.copy();env['PYTHONPATH']=c['ember_dir']+os.pathsep+c['app_dir']
        for name,argv,ready in commands(c,run):
            if stopping:break
            log=run/(name+'.log');logs[name]=log.open('wb')
            children[name]=subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=logs[name],stderr=subprocess.STDOUT,
                env=env,start_new_session=True,preexec_fn=child_setup(os.getpid()))
            publish();deadline=time.monotonic()+35
            while ready not in tail(log):
                if stopping:break
                if children[name].poll() is not None:raise RuntimeError(name+' exited during startup')
                if time.monotonic()>deadline:raise RuntimeError(name+' readiness timeout')
                if any(p.poll() is not None for p in children.values()):raise RuntimeError('A component exited during startup')
                time.sleep(.1)
        if not stopping:
            record['state']='RUNNING';publish();print('EMBER_UHF_SUPERVISOR_READY '+json.dumps(record),flush=True)
        started=time.monotonic();next_check=0
        while not stopping:
            for name,p in children.items():
                if p.poll() is not None:raise RuntimeError(name+' exited unexpectedly: '+str(p.returncode))
            if a.seconds and time.monotonic()-started>=a.seconds:stopping=True;reason='lease_expired';break
            if time.monotonic()>=next_check:
                if size_bytes(run)>c.get('quota_mib',128)*1024**2:raise RuntimeError('Evidence quota exceeded')
                publish();next_check=time.monotonic()+1
            try:conn,_=sock.accept()
            except socket.timeout:continue
            with conn:
                conn.settimeout(2)
                try:
                    data=b''
                    while b'\n' not in data:
                        part=conn.recv(1025-len(data))
                        if not part or len(data)+len(part)>1024:raise ValueError('One short JSON command required')
                        data+=part
                    message=json.loads(data.split(b'\n',1)[0]);command=message.get('command')
                    if command=='stop':stopping=True;reason='control_stop';result=dict(state='STOPPING')
                    elif command=='status':
                        result=dict(record)
                        if c['role']=='sdrb':result['radio']=radio_request(default_socket(),dict(command='status'),timeout=2)
                    else:raise ValueError('Unknown control command')
                    reply=dict(ok=True,result=result)
                except Exception as exc:reply=dict(ok=False,error=str(exc))
                conn.sendall((json.dumps(reply)+'\n').encode())
    except BaseException as exc:failure=str(exc) or type(exc).__name__;reason='component_failure'
    finally:
        record.update(state='STOPPING',reason=reason,error=failure);publish()
        if sock is not None:sock.close()
        # RF goes quiet first. Forwarder stops before CAN reader. No CAN link
        # mutation is performed: another AMSAT application may share the bus.
        order=('radio','forward','can','receiver')
        for name in order:
            if name not in children:continue
            p=children[name]
            if p.poll() is None:
                p.terminate()
                try:p.wait(timeout=90 if name=='receiver' else 25)
                except subprocess.TimeoutExpired:
                    os.killpg(p.pid,signal.SIGKILL);p.wait();failure=(failure or '')+' '+name+' forced shutdown'
            # Remove descendants left by a component that crashed before cleanup.
            try:os.killpg(p.pid,signal.SIGKILL)
            except ProcessLookupError:pass
            logs[name].close()
        record.update(state='FAILED' if failure else 'STOPPED',error=failure);publish()
        if bound:(state/'control.sock').unlink(missing_ok=True)
        lock.close()
        print('EMBER_UHF_SUPERVISOR_STOPPED '+json.dumps(record),flush=True)
    return 1 if failure else 0

def status(c):
    path=Path(c['state_dir'])/'control.sock'
    if path.exists():
        try:return radio_request(path,dict(command='status'),timeout=3)
        except (OSError,RuntimeError):pass
    saved=Path(c['state_dir'])/'status.json'
    result=json.loads(saved.read_text()) if saved.exists() else dict(state='NOT_STARTED',role=c['role'])
    if result['state'] in ('STARTING','RUNNING','STOPPING'):
        with (Path(c['state_dir'])/'owner.lock').open('a') as lock:
            try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);result=dict(result,state='OWNER_LOST')
            except BlockingIOError:pass
    return result

def remove_stale(c):
    state=Path(c['state_dir']);path=state/'control.sock'
    with (state/'owner.lock').open('a') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise RuntimeError('Supervisor already owns this role; use status/stop')
        saved=state/'status.json'
        if saved.exists():
            old=json.loads(saved.read_text())
            if old['state'] in ('STARTING','RUNNING','STOPPING'):
                old.update(state='FAILED',reason='owner_lost',error='Owner disappeared; children received parent-death signal')
                run=Path(old['run'])
                if run.parent==Path(c['runs_dir']) and not run.is_symlink() and (run/'.ember-uhf-run').is_file():atomic(run/'supervisor.json',old)
                atomic(saved,old)
        if path.exists():
            if not path.is_socket():raise RuntimeError('Refusing non-socket control path')
            path.unlink()

def client(a):
    c=load(a.config);state=Path(c['state_dir'])
    if a.command=='status':print(json.dumps(status(c),indent=2));return 0
    if a.command=='stop':
        if status(c)['state']=='OWNER_LOST':remove_stale(c);print(json.dumps(status(c),indent=2));return 0
        if not (state/'control.sock').exists():print(json.dumps(status(c),indent=2));return 0
        radio_request(state/'control.sock',dict(command='stop'),timeout=3)
        deadline=time.monotonic()+110
        while (state/'control.sock').exists():
            if time.monotonic()>deadline:raise RuntimeError('Stop timed out; inspect owned process state')
            time.sleep(.2)
        print(json.dumps(status(c),indent=2));return 0
    if c['role']=='sdrb' and not a.transmit:raise ValueError('SDRB start requires --transmit')
    private(state)
    remove_stale(c)
    argv=[sys.executable,str(Path(__file__).resolve()),'serve','--config',str(a.config.resolve()),'--seconds',str(a.seconds)]
    if a.transmit:argv.append('--transmit')
    with (state/'start.log').open('wb') as log:
        p=subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    deadline=time.monotonic()+110
    while True:
        saved=state/'status.json'
        if saved.exists():
            r=json.loads(saved.read_text())
            if r['pid']==p.pid and r['state']=='RUNNING':print(json.dumps(r,indent=2));return 0
            if r['pid']==p.pid and r['state']=='FAILED':raise RuntimeError(r['error'])
        if p.poll() is not None:raise RuntimeError('Supervisor exited; inspect '+str(state/'start.log'))
        if time.monotonic()>deadline:raise RuntimeError('Startup timeout; inspect status, do not silently retry')
        time.sleep(.2)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=('start','serve','status','stop'))
    p.add_argument('--config',type=Path,required=True);p.add_argument('--seconds',type=int,default=0,choices=range(0,601),help='0: until stop/fault; nonzero is a finite post-readiness lease')
    p.add_argument('--transmit',action='store_true');a=p.parse_args()
    try:sys.exit(serve(a) if a.command=='serve' else client(a))
    except Exception as exc:print(str(exc),file=sys.stderr);sys.exit(1)
