"""Snapshot and compare the running Yamcs MDB and shared display bucket.

Read-only by default. --publish installs only Ground-Build.opi and its manifest.
The page is a dated audit, not a continuously polled health indicator.
"""
import argparse
import copy
import contextlib
import io
import tempfile
from generate_displays import generate
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

EXCLUDED = {'Ground-Build.opi', 'ground-build.json'}

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

def snapshot(url, instance):
    def get(path):
        with urlopen(url.rstrip('/')+path, timeout=20) as r:
            return r.read()
    server = json.loads(get('/api'))
    bucket = '/api/storage/buckets/ember_displays/objects'
    listing = json.loads(get(bucket))
    assert not listing.get('continuationToken'), 'Display list truncated'
    displays = {o['name']: hashlib.sha256(get(bucket+'/'+quote(o['name'], safe='/'))).hexdigest()
                for o in listing.get('objects', []) if o['name'] not in EXCLUDED}
    assert displays, 'Empty display bucket'
    mdb = {}
    for kind in ('parameters', 'containers', 'commands', 'algorithms'):
        data = json.loads(get('/api/mdb/'+quote(instance, safe='')+'/'+kind+
                              '?system=/ember&details=true&limit=1000'))
        assert not data.get('continuationToken'), 'MDB list truncated: '+kind
        mdb[kind] = data
    assert mdb['parameters'].get('parameters'), 'Empty EMBER MDB'
    components = dict(yamcs_version=server['yamcsVersion'], yamcs_revision=server.get('revision'),
                      instance=instance, displays=displays, loaded_mdb_sha256=digest(mdb))
    return dict(schema_version=1, audited_utc=datetime.now(timezone.utc).isoformat(),
                fingerprint=digest(components), components=components)

def page(manifest):
    with tempfile.TemporaryDirectory() as directory:
        with contextlib.redirect_stdout(io.StringIO()):generate(directory)
        d=ET.parse(Path(directory)/'Comms-Firmware.opi').getroot()
    template=copy.deepcopy(d.find('widget'))
    for w in list(d.findall('widget')):d.remove(w)
    d.find('name').text='EMBER ground build'
    c=manifest['components']
    lines=['EMBER UHF ground build '+manifest['release'],
           'Yamcs server '+c['yamcs_version']+' | Instance: '+c['instance'],
           'Audited UTC: '+manifest['audited_utc'],
           'Deployment fingerprint (compare this across team installations):',manifest['fingerprint'],
           'Loaded EMBER definitions SHA-256:',c['loaded_mdb_sha256'],
           'Shared dashboard/script files audited: '+str(len(c['displays'])),
           'Dated snapshot; rerun build_identity.py --check to detect later drift.',
           'Manifest: ember_displays / ground-build.json',
           'Receiver is separately identified by live.py --version and capture session.json.']
    for i,line in enumerate(lines):
        w=copy.deepcopy(template)
        for k,v in dict(name='line'+str(i),text=line,x=20,y=20+i*55,
                        width=1060,height=45,wrap_words='true').items():
            child=w.find(k)
            if child is None:child=ET.SubElement(w,k)
            child.text=str(v)
        w.find('font/opifont.name').set('height','16')
        w.find('font/opifont.name').set('style','0')
        d.append(w)
    return ET.tostring(d,encoding='utf-8',xml_declaration=True)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--url',default='http://127.0.0.1:8090')
    p.add_argument('--instance',default='ember-uhf')
    p.add_argument('--release',help='Explicit version for a new approved baseline')
    p.add_argument('--output',type=Path)
    p.add_argument('--check',type=Path,help='Compare with a previously approved manifest')
    p.add_argument('--publish',action='store_true')
    a=p.parse_args()
    if not a.check and not a.release:p.error('Use --check or an explicit --release for a new baseline')
    m=snapshot(a.url,a.instance);m['release']=a.release
    if a.check:
        expected=json.loads(a.check.read_text())
        m['release']=a.release or expected['release']
        if m['fingerprint']!=expected['fingerprint']:
            raise SystemExit('DRIFT: running Yamcs assets differ from '+str(a.check))
        print('MATCH '+expected['release']+' '+m['fingerprint'])
    data=(json.dumps(m,indent=2)+'\n').encode()
    if a.output:a.output.write_bytes(data)
    if a.publish:
        for name,body,mime in [('ground-build.json',data,'application/json'),
                                ('Ground-Build.opi',page(m),'application/xml')]:
            url=a.url.rstrip('/')+'/api/storage/buckets/ember_displays/objects/'+name
            with urlopen(Request(url,data=body,headers={'Content-Type':mime}),timeout=20) as r:r.read()
            with urlopen(url,timeout=20) as r:assert r.read()==body
        assert snapshot(a.url,a.instance)['fingerprint']==m['fingerprint'], 'Assets changed during audit'
    print(json.dumps(m,indent=2))

if __name__=='__main__':main()
