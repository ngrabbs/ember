"""Install generated EMBER displays; back up modified objects before replacing."""
import argparse
import datetime
import json
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen
from generate_displays import generate

ROOT = Path(__file__).resolve().parent
BUCKET = 'ember_displays'


def install_instance(url, instance):
    url=url.rstrip('/')
    bucket='ember_bench_displays' if instance=='ember-bench' else BUCKET
    output=ROOT/'.runtime/ember-displays'/instance
    generate(output,instance=instance)

    def request(path, data=None, content_type=None):
        headers={'Content-Type':content_type} if content_type else {}
        with urlopen(Request(url+path, data=data, headers=headers),timeout=15) as response:
            return response.read()

    try:
        request('/api/storage/buckets/'+bucket)
    except HTTPError as error:
        if error.code != 404:
            raise
        request('/api/storage/buckets',json.dumps({'name':bucket}).encode(),'application/json')
    backup=ROOT/'.runtime/display-backups'/datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    for source in sorted(output.rglob('*')):
        if not source.is_file():
            continue
        name=source.relative_to(output).as_posix()
        path='/api/storage/buckets/'+bucket+'/objects/'+quote(name,safe='/')
        data=source.read_bytes()
        try:
            previous=request(path)
        except HTTPError as error:
            if error.code != 404:
                raise
            previous=None
        if previous == data:
            print('Unchanged:',name)
            continue
        if previous is not None:
            saved=backup/instance/name; saved.parent.mkdir(parents=True,exist_ok=True); saved.write_bytes(previous)
            print('Previous object saved:',saved)
        mime='application/json' if source.suffix=='.par' else 'application/xml' if source.suffix=='.opi' else 'text/javascript'
        request(path,data,mime)
        assert request(path)==data, 'Uploaded display differs: '+name
        print('Installed:',name)
    print(url+'/telemetry/displays/files/Overview.opi?c='+instance+'__realtime')


def install(url):
    for instance in ('ember','ember-bench'):install_instance(url,instance)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url',default='http://127.0.0.1:8090')
    install(parser.parse_args().url)
