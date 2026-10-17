"""Install only payload assets, preserving existing ground displays and scripts."""
import argparse
from pathlib import Path
import tempfile
from urllib.request import Request, urlopen
from generate_displays import generate


def install(url):
    with tempfile.TemporaryDirectory() as temp:
        root=Path(temp);generate(root,instance="ember-bench")
        display=(root/'Payload.opi').read_text()
        files={'Payload.par':(root/'Payload.par').read_bytes()}
        for name in ('comms-version','comms-git','sample-time'):
            display=display.replace('scripts/'+name+'.js','scripts/payload-'+name+'.js')
            files['scripts/payload-'+name+'.js']=(root/'scripts'/(name+'.js')).read_bytes()
        files['Payload.opi']=display.encode()
        for name,body in files.items():
            destination=url.rstrip('/')+'/api/storage/buckets/ember_bench_displays/objects/'+name
            with urlopen(Request(destination,data=body,headers={'Content-Type':'application/octet-stream'}),timeout=20) as response:response.read()
            with urlopen(destination,timeout=20) as response:assert response.read()==body
        print('Installed and verified: '+', '.join(files))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url',default='http://127.0.0.1:8090')
    install(parser.parse_args().url)
