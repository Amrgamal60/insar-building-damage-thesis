"""Anonymous evidence downloader; raw responses stay in the private tree.

Run with the project Python -I. HEAD probes never fetch roll bodies.
Each response receives a fresh source directory; manifest has no record values.
"""
import argparse
import datetime as dt
import hashlib
import json
import pathlib
import urllib.error
import urllib.parse
import urllib.request
import uuid
import concurrent.futures
import subprocess
import fcntl

p = argparse.ArgumentParser()
p.add_argument('--private', type=pathlib.Path, required=True)
p.add_argument('--manifest', type=pathlib.Path, required=True)
p.add_argument('--head', action='store_true')
p.add_argument('--name')
p.add_argument('--timeout',type=int,default=180)
p.add_argument('--workers',type=int,default=4)
p.add_argument('--quiet',action='store_true')
p.add_argument('--url-list',type=pathlib.Path)
p.add_argument('urls', nargs='*')
a = p.parse_args()
if a.url_list:
    a.urls.extend(json.loads(a.url_list.read_text()))
entries = json.loads(a.manifest.read_text()) if a.manifest.exists() else []
def fetch(url):
    entry = {'url': url, 'access_date_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
             'method': 'HEAD' if a.head else 'GET'}
    folder = a.private / 'raw' / (urllib.parse.urlparse(url).netloc.replace(':','_') + '_' + uuid.uuid4().hex[:12])
    folder.mkdir(parents=True, exist_ok=False)
    name = a.name or pathlib.Path(urllib.parse.unquote(urllib.parse.urlparse(url).path)).name or 'index.html'
    dest = folder / name
    try:
        command=['curl','-q','--silent','--show-error','--location','--connect-timeout','20',
                 '--max-time',str(a.timeout),'--max-filesize','19000000000',
                 '--user-agent','Austin-research-data-availability/1.0',
                 '--output',str(dest),'--write-out','%{json}',url]
        if a.head:
            command.insert(2,'--head')
        result=subprocess.run(command,capture_output=True,text=True)
        meta=json.loads(result.stdout)
        entry.update(http_status=meta['response_code'],final_url=meta['url_effective'],
                     content_type=meta['content_type'],content_length=meta.get('size_download'))
        final=urllib.parse.urlsplit(entry['final_url'])
        params=urllib.parse.parse_qsl(final.query,keep_blank_values=True)
        signing=[k for k,v in params if k.lower().startswith('x-amz-')]
        if signing:
            entry['final_url']=urllib.parse.urlunsplit(final._replace(query=urllib.parse.urlencode([(k,v) for k,v in params if k not in signing])))
            entry['redacted_redirect_parameters']=signing
        if result.returncode:
            entry['error']='curl '+str(result.returncode)+': '+result.stderr.strip()
        if a.head:
            import re
            headers=dest.read_bytes() if dest.exists() else b''
            lengths=re.findall(rb'(?im)^content-length:\s*(\d+)',headers)
            entry.update(remote_size_bytes=int(lengths[-1]) if lengths else None,
                         size_bytes=len(headers),sha256=hashlib.sha256(headers).hexdigest() if headers else None,
                         local_path=str(dest) if headers else None)
        else:
            size = dest.stat().st_size if dest.exists() else 0
            digest = hashlib.sha256()
            if dest.exists():
                with dest.open('rb') as source:
                    while chunk := source.read(1024 * 1024):
                        digest.update(chunk)
            entry.update(size_bytes=size,sha256=digest.hexdigest() if dest.exists() else None,local_path=str(dest) if dest.exists() else None)
    except Exception as error:
        entry['error'] = type(error).__name__ + ': ' + str(error)
    (folder/'evidence.json').write_text(json.dumps(entry,indent=2)+'\n')
    return entry

with concurrent.futures.ThreadPoolExecutor(max_workers=a.workers) as pool:
    for entry in pool.map(fetch,a.urls):
        with a.manifest.open('r+') as manifest:
            fcntl.flock(manifest,fcntl.LOCK_EX)
            manifest.seek(0)
            entries=json.load(manifest)
            entries.append(entry)
            manifest.seek(0)
            json.dump(entries,manifest,indent=2)
            manifest.write('\n')
            manifest.truncate()
            fcntl.flock(manifest,fcntl.LOCK_UN)
        if not a.quiet:
            print(json.dumps(entry),flush=True)
        elif entry.get('error') or entry.get('http_status')!=200:
            print(json.dumps({'url':entry['url'],'http_status':entry.get('http_status'),'error':entry.get('error')}),flush=True)
if a.quiet:
    print(json.dumps({'requests':len(a.urls),'manifest':str(a.manifest)}),flush=True)
