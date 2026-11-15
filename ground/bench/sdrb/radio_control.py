"""Private local control client; no GNU Radio or spacecraft dictionary imports."""
import json,socket
from pathlib import Path

def default_socket():return Path.home()/'.cache/ember-binary-radio/control.sock'
def request(path, message, timeout=15):
    data=(json.dumps(message)+'\n').encode()
    if len(data)>2048:raise ValueError('Control request exceeds bound')
    with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as conn:
        conn.settimeout(timeout);conn.connect(str(path));conn.sendall(data)
        data=b''
        while b'\n' not in data:
            chunk=conn.recv(8192-len(data))
            if not chunk:raise RuntimeError('Control closed without a response; submission outcome unknown')
            data+=chunk
            if len(data)>=8192:raise ValueError('Control response exceeds bound')
    result=json.loads(data.split(b'\n',1)[0])
    if not result['ok']:raise RuntimeError(result['error'])
    return result['result']
