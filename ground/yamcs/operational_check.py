"""Isolated loopback:8091 check; TM11018/11019/TC11029 flight, TM11020/TC11028 bench.

Never sends synthetic packets to operational ports or commands to hardware.
"""
import base64
import json
from pathlib import Path
import select
import socket
import sys
import time
from urllib.parse import quote
from urllib.request import Request,urlopen
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'ember'))
from codec import encode,decode
BASE='http://127.0.0.1:8091'
def api(path,body=None):
    req=Request(BASE+'/api'+path,data=None if body is None else json.dumps(body).encode(),headers={'Content-Type':'application/json'})
    with urlopen(req,timeout=10) as r:return json.load(r)
def check():
    disabled = [link['name'] for link in api('/links/ember-bench')['links'] if link['disabled']]
    try:
        for name in disabled:
            api('/links/ember-bench/'+name+':enable', {})
        return check_links()
    finally:
        for name in reversed(disabled):
            api('/links/ember-bench/'+name+':disable', {})

def check_links():
    assert {x['name'] for x in api('/instances')['instances']}=={'ember','ember-bench'}
    expected={'ember':{'lte-tm-in','uhf-tm-in','uhf-command-out'},'ember-bench':{'ihu-serial-in','ihu-serial-out'}}
    for instance,names in expected.items():assert {x['name'] for x in api('/links/'+instance)['links']}==names
    sender=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    sink=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);sink.bind(('127.0.0.1',11028))
    packet=encode('HEARTBEAT',sequence=1,source=2,target=1,source_boot_id=22,uptime_ms=100,payload={'mode':3,'configuration':1,'telemetry_period_ms':1000})
    for port in (11018,11019,11020):sender.sendto(packet,('127.0.0.1',port));time.sleep(.1)
    bad=bytearray(packet);bad[-1]^=1;sender.sendto(bad,('127.0.0.1',11018));time.sleep(.3)
    for instance in expected:
        rows=api('/archive/'+instance+'/packets?limit=100')['packets']
        assert len(rows)==1 and base64.b64decode(rows[0]['packet'])==packet
    with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as uhf_sink:
        uhf_sink.bind(('127.0.0.1',11029))
        flight_ticket=api('/processors/ember/realtime/commands/ember/PAYLOAD_STATUS_QUERY',
                          {'origin':'isolated-environment-check','sequenceNumber':1,'args':{}})
        assert select.select([uhf_sink],[],[],2)[0]
        flight_cmd=decode(uhf_sink.recv(4096))
        assert flight_cmd['name']=='PAYLOAD_STATUS_QUERY'
        assert not select.select([sink],[],[],.2)[0]
        result=encode('PAYLOAD_STATUS',sequence=9,source=2,target=1,source_boot_id=22,uptime_ms=199,
                      transaction_epoch=flight_cmd['header']['transaction_epoch'],
                      transaction_id=flight_cmd['header']['transaction_id'],
                      payload=dict(payload_version=1,transport=2,report_kind=1,node=4,ready=1,
                                   bridge_session_id=0,reported_boot_id=42,reported_uptime_ms=800,
                                   requests=2,replies=1,rejected=0,fragment_errors=0))
        sender.sendto(result,('127.0.0.1',11019));time.sleep(.2)
        flight_history=api('/archive/ember/commands/'+quote(flight_ticket['id'],safe=''))['attr']
        assert any(a['name']=='ember-outcome' and a['value']['stringValue']=='COMPLETED' for a in flight_history)
    ticket=api('/processors/ember-bench/realtime/commands/ember/PAYLOAD_STATUS_QUERY',{'origin':'isolated-environment-check','sequenceNumber':1,'args':{}})
    assert select.select([sink],[],[],2)[0]
    cmd=decode(sink.recv(4096));assert cmd['name']=='PAYLOAD_STATUS_QUERY'
    responses=[]
    for stage in (0,2):
        responses.append(encode('COMMAND_RESPONSE',sequence=10+stage,source=2,target=1,source_boot_id=22,uptime_ms=200+stage,
            transaction_epoch=cmd['header']['transaction_epoch'],transaction_id=cmd['header']['transaction_id'],
            payload={'command_id':cmd['header']['message_id'],'stage':stage,'reason':0,'parameter_id':0,'value':0}))
    for response in responses:sender.sendto(response,('127.0.0.1',11018))
    time.sleep(.2)
    def history():return {x['name']:x['value'] for x in api('/archive/ember-bench/commands/'+quote(ticket['id'],safe=''))['attr']}
    assert 'ember-outcome' not in history(),'Flight packets completed a bench command'
    for response in responses:sender.sendto(response,('127.0.0.1',11020));time.sleep(.1)
    assert history()['ember-outcome']['stringValue']=='COMPLETED'
    assert not select.select([sink],[],[],.2)[0],'duplicate send'
    report={'instances':list(expected),'link_sets':{k:sorted(v) for k,v in expected.items()},'radio_duplicate_copies_archived':1,'same_bytes_in_bench_archive':True,'bad_crc_rejected':True,'flight_payload_status_completed':True,'flight_reply_cannot_complete_bench_command':True,'bench_mock_command_completed':True}
    print(json.dumps(report,indent=2));sender.close();sink.close();return report
if __name__=='__main__':check()
