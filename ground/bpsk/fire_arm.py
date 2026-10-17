"""COMMS one-window arming service. A valid fire-check datagram permits one A window."""
import argparse
import os
import socket
import time
import serial
from codec import decode


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--device',required=True)
    a=p.parse_args()
    with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as sock:
        sock.bind(('192.168.1.252',10030))
        notify=os.environ.get('NOTIFY_SOCKET')
        if notify:
            with socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM) as ready:
                ready.connect(('\0'+notify[1:]) if notify.startswith('@') else notify)
                ready.sendall(b'READY=1')
        print('READY listening',flush=True)
        while True:
            wire,address=sock.recvfrom(241)
            if address[0]!='192.168.1.251':continue
            try:
                packet=decode(wire)
                if packet['name']!='PAYLOAD_FIRE_CHECK' or packet['header']['source']!=1 or packet['header']['target']!=2:continue
                with serial.Serial(a.device,115200,timeout=.1,write_timeout=.5,exclusive=True) as console:
                    console.reset_input_buffer();console.write(b'A');console.flush()
                    armed=False;end=time.monotonic()+24
                    while time.monotonic()<end:
                        line=console.readline().decode('utf-8','replace').strip()
                        if line:print(line,flush=True)
                        if '[auto_reply] BEGIN' in line:
                            armed=True;sock.sendto(b'ARMED'+wire,address)
                        if '[auto_reply] END' in line:break
                    else:console.write(b'x');console.flush()
                    if not armed:sock.sendto(b'FAILED'+wire,address)
            except (ValueError,OSError) as error:print('ARM_FAILED '+str(error),flush=True)

if __name__=='__main__':main()
