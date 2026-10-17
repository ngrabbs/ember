"""Prepare separate flight and serial-bench instances; retain all archives.

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
    def tc_tail(pattern):
        return re.sub(r'\n  tc:.*?(?=\n\S|\Z)', '\n  tc:\n    - name: tc_realtime\n      processor: realtime\n      tcPatterns: ["'+pattern+'"]\n\n', tail, flags=re.S)

    def tm(name,port):
        return f'''  - name: {name}
    class: org.yamcs.tctm.UdpTmDataLink
    stream: tm_realtime
    port: {port}
    packetPreprocessorClassName: com.example.ember.EmberPacketPreprocessor
    packetPreprocessorArgs:
      deduplicate: true
      resultDomain: spacecraft
'''
    flight = services+'\ndataLinks:\n'+tm('lte-tm-in',10018)+tm('uhf-tm-in',10019)
    flight += """  - name: uhf-command-out
    class: org.yamcs.tctm.UdpTcDataLink
    stream: tc_realtime
    host: 192.168.1.251
    port: 10029
    commandPostprocessorClassName: com.example.ember.EmberCommandPostprocessor
    commandPostprocessorArgs:
      resultDomain: spacecraft
"""
    flight += '\nmdb:\n  - type: xtce\n    args:\n      file: mdb/ember.xml\n'+tc_tail('/ember/PAYLOAD_FIRE_CHECK')
    bench = services+'\ndataLinks:\n'+tm('ihu-serial-in',10020)+'''  - name: ihu-serial-out
    class: org.yamcs.tctm.UdpTcDataLink
    stream: tc_realtime
    host: 192.168.1.252
    port: 10028
    commandPostprocessorClassName: com.example.ember.EmberCommandPostprocessor
    commandPostprocessorArgs:
      resultDomain: spacecraft
'''
    bench += '\nmdb:\n  - type: xtce\n    args:\n      file: mdb/ember-bench.xml\n'+tc_tail('/ember/PAYLOAD_(PING|IDENT|STATUS_QUERY|HEARTBEAT_QUERY|FIRE_CHECK)')
    bench=bench.replace('displayBucket: ember_displays','displayBucket: ember_bench_displays')
    current = main.read_text()
    # Remove live transport instances and upstream demo from the default server.
    # Their instance definitions and persistent databases are retained untouched.
    for name in (*LEGACY,'ember-bench'):
        current = re.sub(r'^  - '+re.escape(name)+r'\s*\n', '', current, flags=re.M)
    if '  - ember\n' not in current: raise ValueError('Missing ember instance')
    current=current.replace('  - ember\n','  - ember\n  - ember-bench\n',1)
    backup = runtime / '.unified-backups' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    backup.mkdir(parents=True, mode=0o700)
    for file in (main, instance, *(config/('yamcs.'+name+'.yaml') for name in (*LEGACY,'ember-bench'))):
        if file.exists():shutil.copy2(file, backup/file.name)
    mdb = runtime / 'src/main/yamcs/mdb/ember.xml'
    if mdb.exists():shutil.copy2(mdb, backup/'ember.xml')
    bench_mdb=mdb.with_name('ember-bench.xml')
    if bench_mdb.exists():shutil.copy2(bench_mdb, backup/'ember-bench.xml')
    java = runtime / 'src/main/java/com/example/ember'
    if java.exists():shutil.copytree(java, backup/'java')
    java.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory() as temp:
        generate(temp, command_filter={'PAYLOAD_FIRE_CHECK'})
        tree=ET.parse(Path(temp)/'ember.xml')
        # Shared sparse-radio freshness policy; sample timestamps stay visible.
        rates=tree.findall('.//{'+NS+'}SequenceContainer[@name="POWER_STATUS"]/{'+NS+'}DefaultRateInStream')
        if len(rates)!=1:raise ValueError('Missing POWER_STATUS rate')
        rates[0].set('minimumValue',str(1/30))
        tree.write(mdb,encoding='utf-8',xml_declaration=True)
        shutil.copy2(Path(temp)/'WireProfile.java',java/'WireProfile.java')
        for source in (ROOT/'ember-java').glob('*.java'):shutil.copy2(source,java/source.name)
    with tempfile.TemporaryDirectory() as temp:
        generate(temp, command_filter={'PAYLOAD_PING','PAYLOAD_IDENT','PAYLOAD_STATUS_QUERY','PAYLOAD_HEARTBEAT_QUERY','PAYLOAD_FIRE_CHECK'})
        tree=ET.parse(Path(temp)/'ember.xml')
        rate=tree.find('.//{'+NS+'}SequenceContainer[@name="POWER_STATUS"]/{'+NS+'}DefaultRateInStream')
        rate.set('minimumValue',str(1/5))
        tree.write(mdb.parent/'ember-bench.xml',encoding='utf-8',xml_declaration=True)
    instance.write_text(flight)
    (config/'yamcs.ember-bench.yaml').write_text(bench)
    for name in legacy_history:
        old = config / ('yamcs.'+name+'.yaml')
        history = old.read_text()
        begin,end = history.index('\ndataLinks:'),history.index('\nmdb:')
        history = history[:begin]+'\ndataLinks: []\n'+history[end:]
        history = re.sub(r'\n  tc:.*?(?=\n\S|\Z)', '\n  tc:\n    - name: tc_history_unrouted\n      processor: realtime\n      tcPatterns: ["(?!)"]\n', history, flags=re.S)
        old.write_text(history)
        current = current.replace('  - ember\n','  - ember\n  - '+name+'\n',1)
    main.write_text(current)
    (runtime/'.operational-consolidated').write_text('ember\nember-bench\n')
    print('Prepared ember radio reception and ember-bench serial telemetry/commands.')
    print('Previous configuration/source saved privately under '+str(backup))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime',required=True,type=Path)
    parser.add_argument('--legacy-history',action='append',choices=LEGACY,default=[],
                        help='Optional historical instance with no telemetry inputs or command links')
    args=parser.parse_args()
    prepare(args.runtime,args.legacy_history)
