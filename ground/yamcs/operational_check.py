"""Integration check ONLY for the isolated validation server on loopback:8091.

Requires its five TM ports remapped to 11016..11020 and TC mock sinks to
11026/11028. Synthetic packets and commands never go to operational ports.
"""
import base64
import json
from pathlib import Path
import select
import socket
import sys
import time
from urllib.parse import quote
from urllib.request import Request, urlopen
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'ember'))
from codec import encode,decode,DICTIONARY
BASE='http://127.0.0.1:8091'

def api(path,body=None):
    req=Request(BASE+'/api'+path,data=None if body is None else json.dumps(body).encode(),headers={'Content-Type':'application/json'})
    with urlopen(req,timeout=10) as r:return json.load(r)

def check():
    assert [x['name'] for x in api('/instances')['instances']]==['ember']
    wire={};sender=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    def send(name,port,boot=22,seq=0,**payload):
        b=encode(name,sequence=seq,source=2,target=1,source_boot_id=boot,uptime_ms=seq+100, payload=payload)
        sender.sendto(b,('127.0.0.1',port));return b
    for n,port in enumerate(range(11016,11021)):
        b=send('HEARTBEAT',port,boot=11 if port==11016 else 22,seq=n,mode=3,configuration=1,telemetry_period_ms=1000)
        wire[b.hex()]=port;time.sleep(.1)
    duplicate=encode('HEARTBEAT',sequence=10,source=2,target=1,source_boot_id=22,uptime_ms=10000,payload={'mode':3,'configuration':1,'telemetry_period_ms':1000})
    for port in range(11016,11021):sender.sendto(duplicate,('127.0.0.1',port));time.sleep(.05)
    bad=bytearray(duplicate);bad[-1]^=1;sender.sendto(bad,('127.0.0.1',11018))
    time.sleep(.5)
    rows=api('/archive/ember/packets?limit=100')['packets']
    for b in wire:assert any(base64.b64decode(x['packet']).hex()==b for x in rows)
    assert sum(base64.b64decode(x['packet'])==duplicate for x in rows)==1
    assert len(rows)==6
    usb=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);usb.bind(('127.0.0.1',11026))
    payload=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);payload.bind(('127.0.0.1',11028))
    report={'tm_ports_verified':list(range(11016,11021)),'duplicate_arrivals':5,'duplicate_archived':1,'bad_crc_archived':False,'commands':[]}
    # Restore distinct stable bench identities before registering commands.
    send('HEARTBEAT',11016,boot=11,seq=11,mode=3,configuration=1,telemetry_period_ms=1000)
    send('HEARTBEAT',11020,boot=22,seq=12,mode=3,configuration=1,telemetry_period_ms=1000)
    time.sleep(.2)
    for name,sink,port,boot in [('PING',usb,11016,11),('PAYLOAD_STATUS_QUERY',payload,11020,22)]:
        ticket=api('/processors/ember/realtime/commands/ember/'+name,{'origin':'isolated-unification-check','sequenceNumber':int(time.time()),'args':{}})
        readable,_,_=select.select([usb,payload],[],[],2)
        assert readable==[sink],(name,'wrong command route')
        cmd=decode(sink.recv(4096));assert cmd['name']==name
        assert not select.select([usb,payload],[],[],.15)[0],'command sent twice'
        if name.startswith('PAYLOAD'):
            # Neither a ground EPS wrapper nor spare USB boot is an IHU reset.
            fields=next(m['fields'] for m in DICTIONARY['messages'] if m['name']=='POWER_STATUS')
            p={x['name']:0 for x in fields};p.update(payload_version=1,provenance=1,bridge_session_id=999)
            send('POWER_STATUS',11017,boot=999,seq=13,**p)
            send('HEARTBEAT',11016,boot=11,seq=14,mode=3,configuration=1,telemetry_period_ms=1000)
        for stage in (0,2):
            result=encode('COMMAND_RESPONSE',sequence=20+stage+(10 if boot==22 else 0),source=2,target=1,
                          source_boot_id=boot,uptime_ms=200+stage,
                          transaction_epoch=cmd['header']['transaction_epoch'],transaction_id=cmd['header']['transaction_id'],
                          payload={'command_id':cmd['header']['message_id'],'stage':stage,'reason':0,'parameter_id':0,'value':0})
            sender.sendto(result,('127.0.0.1',port));time.sleep(.1)
        history=api('/archive/ember/commands/'+quote(ticket['id'],safe=''))
        attrs={x['name']:x['value'] for x in history['attr']}
        assert attrs['ember-outcome']['stringValue']=='COMPLETED',attrs
        report['commands'].append({'name':name,'udp_port':11026 if boot==11 else 11028,'completed':True,'cross_route_delivery':False})
    api('/links/ember/payload-ihu-bench-out:disable',{})
    ticket=api('/processors/ember/realtime/commands/ember/PAYLOAD_IDENT',{'origin':'isolated-unification-check','sequenceNumber':int(time.time())+1,'args':{}})
    assert not select.select([usb,payload],[],[],.3)[0],'disabled payload route fell back to USB'
    report['disabled_payload_route_does_not_fall_back']=True
    report['history']=ticket['id'];print(json.dumps(report,indent=2))
    sender.close();usb.close();payload.close()
    return report

if __name__=='__main__':check()
