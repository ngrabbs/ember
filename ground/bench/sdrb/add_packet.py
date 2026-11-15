#!/usr/bin/env python3
"""Submit one opaque binary packet to an already-running GNU Radio application."""
import argparse,json,sys,uuid
from pathlib import Path
from radio_control import default_socket,request

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--socket',type=Path,default=default_socket())
    group=p.add_mutually_exclusive_group(required=True)
    group.add_argument('--packet',type=Path);group.add_argument('--status',action='store_true');group.add_argument('--stop',action='store_true')
    p.add_argument('--request-id',default=None,help='Reuse this ID only for the same packet if querying an uncertain submission')
    a=p.parse_args()
    message=dict(command='status' if a.status else 'stop' if a.stop else 'enqueue')
    if a.packet:
        payload=a.packet.read_bytes()
        if not 1<=len(payload)<=240:p.error('Packet must contain 1..240 bytes')
        message.update(hex=payload.hex(),request_id=a.request_id or uuid.uuid4().hex)
    # Print identity before IPC so an uncertain timeout can be correlated.
    print(json.dumps(dict(request=message)),flush=True)
    try:result=request(a.socket,message)
    except (OSError,RuntimeError,ValueError) as exc:
        print(json.dumps(dict(ok=False,error=str(exc),request_id=message.get('request_id'),
              note='Check radio status/events before retrying an uncertain submission')),file=sys.stderr)
        return 1
    print(json.dumps(result,indent=2),flush=True)
    return 0
if __name__=='__main__':sys.exit(main())
