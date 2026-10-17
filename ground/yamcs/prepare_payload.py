"""Add isolated payload MDB/classes/instance to an existing Yamcs runtime.

Does not run legacy prepare.py or rewrite the existing instances/MDBs.
Back up the runtime before applying on a deployed station.
"""
import argparse
from pathlib import Path
import shutil
import tempfile
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'ember'))
from generate_mdb import generate

ROOT=Path(__file__).resolve().parent


def prepare(runtime):
    config=runtime/'src/main/yamcs/etc'
    template=config/'yamcs.ember-uhf.yaml'
    if not template.exists():template=config/'yamcs.ember.yaml'
    text=template.read_text()
    start,end=text.index('\ndataLinks:'),text.index('\nmdb:')
    links='''
dataLinks:
  - name: payload-ihu-bench-in
    class: org.yamcs.tctm.UdpTmDataLink
    stream: tm_realtime
    port: 10020
    packetPreprocessorClassName: com.example.emberpayload.EmberPacketPreprocessor
  - name: payload-ihu-bench-out
    class: org.yamcs.tctm.UdpTcDataLink
    stream: tc_realtime
    host: 192.168.1.252
    port: 10028
    commandPostprocessorClassName: com.example.emberpayload.EmberCommandPostprocessor
'''
    text=text[:start]+links+text[end:]
    import re
    text=re.sub(r'file: mdb/[^\n]+','file: mdb/ember-payload.xml',text)
    (config/'yamcs.ember-payload.yaml').write_text(text)
    main=config/'yamcs.yaml';body=main.read_text()
    if '  - ember-payload\n' not in body:
        if '  - ember-uhf\n' in body:body=body.replace('  - ember-uhf\n','  - ember-uhf\n  - ember-payload\n')
        elif '  - ember\n' in body:body=body.replace('  - ember\n','  - ember\n  - ember-payload\n')
        else:raise ValueError('Expected existing ember Yamcs instance')
    main.write_text(body)
    java=runtime/'src/main/java/com/example/emberpayload';java.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory() as temp:
        generate(temp,command_filter={'PAYLOAD_PING','PAYLOAD_IDENT','PAYLOAD_STATUS_QUERY','PAYLOAD_HEARTBEAT_QUERY'})
        shutil.copy2(Path(temp)/'ember.xml',runtime/'src/main/yamcs/mdb/ember-payload.xml')
        sources=list((ROOT/'ember-java').glob('*.java'))+[Path(temp)/'WireProfile.java']
        for source in sources:
            (java/source.name).write_text(source.read_text().replace('package com.example.ember;',
                                                                   'package com.example.emberpayload;'))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime',required=True,type=Path)
    prepare(parser.parse_args().runtime)
