"""Consolidate operational links into ember; leave legacy archives on disk.

Run against an existing prepared runtime. Never calls legacy prepare.py.
Back up the running data volume while Yamcs is stopped before deploying.
"""
import argparse
from datetime import datetime, timezone
from pathlib import Path
import re
import shutil
import sys
import tempfile
import xml.etree.ElementTree as ET
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'ember'))
from generate_mdb import generate, NS

ROOT = Path(__file__).resolve().parent
LEGACY = ('ember-lte', 'ember-uhf', 'ember-payload', 'myproject')


def prepare(runtime, legacy_history=()):
    config = runtime / 'src/main/yamcs/etc'
    main = config / 'yamcs.yaml'
    instance = config / 'yamcs.ember.yaml'
    text = instance.read_text()
    services = text[:text.index('\ndataLinks:')]
    tail = text[text.index('\nstreamConfig:'):]
    tail = re.sub(r'\n  tc:.*?(?=\n\S|\Z)', '''
  tc:
    - name: tc_payload
      processor: realtime
      tcPatterns: ["/ember/PAYLOAD_(PING|IDENT|STATUS_QUERY|HEARTBEAT_QUERY)"]
    - name: tc_usb
      processor: realtime
      tcPatterns: ["/ember/(PING|REQUEST_STATUS|REQUEST_TELEMETRY|SET_PARAMETER)"]

''', tail, flags=re.S)
    links = '\ndataLinks:\n'
    for name, port in [('usb-in',10016),('eps-uart-in',10017),('eps-lte-in',10018),
                       ('eps-uhf-in',10019),('payload-ihu-bench-in',10020)]:
        links += f'''  - name: {name}
    class: org.yamcs.tctm.UdpTmDataLink
    stream: tm_realtime
    port: {port}
    packetPreprocessorClassName: com.example.ember.EmberPacketPreprocessor
    packetPreprocessorArgs:
      deduplicate: true
      resultDomain: {"usb" if port==10016 else "spacecraft"}
'''
    for name, stream, host, port in [('usb-out','tc_usb','host.docker.internal',10026),
                                     ('payload-ihu-bench-out','tc_payload','192.168.1.252',10028)]:
        links += f'''  - name: {name}
    class: org.yamcs.tctm.UdpTcDataLink
    stream: {stream}
    host: {host}
    port: {port}
    commandPostprocessorClassName: com.example.ember.EmberCommandPostprocessor
    commandPostprocessorArgs:
      resultDomain: {"usb" if port==10026 else "spacecraft"}
'''
    body = services + links + '\nmdb:\n  - type: xtce\n    args:\n      file: mdb/ember.xml\n' + tail
    current = main.read_text()
    # Remove live transport instances and upstream demo from the default server.
    # Their instance definitions and persistent databases are retained untouched.
    for name in LEGACY:
        current = re.sub(r'^  - '+re.escape(name)+r'\s*\n', '', current, flags=re.M)
    if '  - ember\n' not in current: raise ValueError('Missing ember instance')
    backup = runtime / '.unified-backups' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    backup.mkdir(parents=True, mode=0o700)
    for file in (main, instance, *(config/('yamcs.'+name+'.yaml') for name in LEGACY)):
        if file.exists():shutil.copy2(file, backup/file.name)
    mdb = runtime / 'src/main/yamcs/mdb/ember.xml'
    if mdb.exists():shutil.copy2(mdb, backup/'ember.xml')
    java = runtime / 'src/main/java/com/example/ember'
    if java.exists():shutil.copytree(java, backup/'java')
    java.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory() as temp:
        generate(temp)
        tree=ET.parse(Path(temp)/'ember.xml')
        # Shared sparse-radio freshness policy; sample timestamps stay visible.
        rates=tree.findall('.//{'+NS+'}SequenceContainer[@name="POWER_STATUS"]/{'+NS+'}DefaultRateInStream')
        if len(rates)!=1:raise ValueError('Missing POWER_STATUS rate')
        rates[0].set('minimumValue',str(1/30))
        tree.write(mdb,encoding='utf-8',xml_declaration=True)
        shutil.copy2(Path(temp)/'WireProfile.java',java/'WireProfile.java')
        for source in (ROOT/'ember-java').glob('*.java'):shutil.copy2(source,java/source.name)
    instance.write_text(body)
    for name in legacy_history:
        old = config / ('yamcs.'+name+'.yaml')
        history = old.read_text()
        begin,end = history.index('\ndataLinks:'),history.index('\nmdb:')
        history = history[:begin]+'\ndataLinks: []\n'+history[end:]
        history = re.sub(r'\n  tc:.*?(?=\n\S|\Z)', '\n  tc:\n    - name: tc_history_unrouted\n      processor: realtime\n      tcPatterns: ["(?!)"]\n', history, flags=re.S)
        old.write_text(history)
        current = current.replace('  - ember\n','  - ember\n  - '+name+'\n',1)
    main.write_text(current)
    (runtime/'.operational-consolidated').write_text('ember\n')
    print('Prepared ember: USB/EPS/LTE/UHF/payload TM and explicit USB/payload TC routes.')
    print('Previous configuration/source saved privately under '+str(backup))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime',required=True,type=Path)
    parser.add_argument('--legacy-history',action='append',choices=LEGACY,default=[],
                        help='Optional historical instance with no telemetry inputs or command links')
    args=parser.parse_args()
    prepare(args.runtime,args.legacy_history)
