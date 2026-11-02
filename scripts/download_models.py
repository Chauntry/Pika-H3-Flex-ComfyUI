"""Explicit, resumable model download. Default: print plan only. Python 3.11+."""
import argparse,hashlib,json,pathlib,urllib.request,os,time
p=argparse.ArgumentParser()
p.add_argument('--comfy-root',required=True,type=pathlib.Path)
p.add_argument('--groups',default='base,ref2va,rewriter,upscaler')
p.add_argument('--download',action='store_true')
a=p.parse_args()
if not (a.comfy_root/'main.py').is_file():p.error('--comfy-root must point to ComfyUI containing main.py')
items=json.loads((pathlib.Path(__file__).resolve().parents[1]/'models.json').read_text(encoding='utf-8'))
groups=set(a.groups.split(','))
unknown=groups-{e['group'] for e in items}
if unknown:p.error('Unknown groups: '+','.join(sorted(unknown)))
items=[e for e in items if e['group'] in groups]
def verified(path,entry):
 if not path.is_file() or path.stat().st_size!=entry['size']:return False
 with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()==entry['sha256']
def download(entry,target):
 part=target.with_suffix(target.suffix+'.part')
 if verified(part,entry):os.replace(part,target);return
 if part.exists() and part.stat().st_size>=entry['size']:
  raise RuntimeError('Invalid complete .part file; rename/remove this exact file and retry: '+str(part))
 for attempt in range(3):
  offset=part.stat().st_size if part.exists() else 0
  headers={'User-Agent':'H3-Workflow-Setup/1.0'}
  if offset:headers['Range']=f'bytes={offset}-'
  try:
   request=urllib.request.Request(entry['url'],headers=headers)
   with urllib.request.urlopen(request,timeout=180) as src:
    if src.status==206:
     if not src.headers.get('Content-Range','').startswith(f'bytes {offset}-'):
      raise RuntimeError('Server returned unexpected range; refusing to append')
     mode='ab' if offset else 'wb'
    elif src.status==200:offset=0;mode='wb'
    else:raise RuntimeError('Unexpected HTTP status: '+str(src.status))
    written=offset;last_report=written
    with part.open(mode) as dst:
     while block:=src.read(8*1024*1024):
      dst.write(block);written+=len(block)
      if written-last_report>=256*1024*1024:
       print(f'  {written/2**30:.2f} / {entry["size"]/2**30:.2f} GiB',flush=True);last_report=written
   break
  except (OSError,TimeoutError) as exc:
   if attempt==2:raise
   print('Network interruption, retrying from .part:',type(exc).__name__,flush=True)
   time.sleep(2)
 if not verified(part,entry):raise RuntimeError('Size or SHA256 mismatch. Rename/remove this exact .part and retry: '+str(part))
 os.replace(part,target)
for e in items:
 target=(a.comfy_root/'models'/e['path']).resolve()
 if not target.is_relative_to((a.comfy_root/'models').resolve()):raise ValueError('Unsafe path')
 print(e['group'],e['path'],round(e['size']/2**30,2),'GiB',flush=True)
 if not a.download:continue
 if verified(target,e):print('verified, skip',flush=True);continue
 target.parent.mkdir(parents=True,exist_ok=True)
 download(e,target)
print('Total:',round(sum(e['size'] for e in items)/2**30,2),'GiB; download =',a.download)
