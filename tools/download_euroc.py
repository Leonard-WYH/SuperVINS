#!/usr/bin/env python3
"""Download only V2_01_easy.zip from a pinned HF mirror archive using HTTP ranges.
Explicit --download is required; metadata mode transfers only the ZIP directory.
"""
import argparse,io,json,pathlib,struct,time,urllib.request,zipfile,zlib,hashlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
(ROOT/'logs').mkdir(parents=True,exist_ok=True)
URL='https://huggingface.co/datasets/GlowBond/EuRoC_MAV_Dataset/resolve/29d08aeb1c8d9dc5c30497cc538d9cc61f872bb7/vicon_room2.zip'
TOTAL=6013384949
p=argparse.ArgumentParser();p.add_argument('--download',action='store_true');a=p.parse_args()
def fetch(start,end):
 for attempt in range(5):
  try:
   req=urllib.request.Request(URL+'?download=true&offset='+str(start),headers={'Range':f'bytes={start}-{end}','User-Agent':'SuperVINS-reproduction/1.0'})
   with urllib.request.urlopen(req,timeout=45) as r:
    want=f'bytes {start}-{end}/{TOTAL}'
    if r.status!=206 or r.headers.get('Content-Range')!=want:raise RuntimeError('Server did not honor range: '+str((r.status,r.headers.get('Content-Range'))))
    data=r.read(end-start+2)
    if len(data)!=end-start+1:raise RuntimeError('Incomplete range')
    return data
  except Exception:
   if attempt==4:raise
   time.sleep(2*(attempt+1))
tail=fetch(TOTAL-65536,TOTAL-1)
infos=zipfile.ZipFile(io.BytesIO(tail)).infolist()
z=next(v for v in infos if v.filename=='vicon_room2/V2_01_easy/V2_01_easy.zip')
off=z.header_offset+TOTAL-len(tail);h=fetch(off,off+29);s=struct.unpack('<4s5H3L2H',h)
if s[0]!=b'PK\x03\x04' or z.compress_type!=8:raise RuntimeError('Unsupported archive layout')
start=off+30+s[-2]+s[-1]
meta={'url':URL,'mirror_revision':'29d08aeb1c8d9dc5c30497cc538d9cc61f872bb7','entry':z.filename,'compressed_bytes':z.compress_size,'uncompressed_bytes':z.file_size,'crc32':f'{z.CRC:08x}','data_offset':start,'note':'Mirror entry CRC is validated; official ETH hash not available here.'}
(ROOT/'logs/euroc_download_metadata.json').write_text(json.dumps(meta,indent=2));print(json.dumps(meta,indent=2),flush=True)
if not a.download:raise SystemExit(0)
data_dir=ROOT/'data';data_dir.mkdir(exist_ok=True);out=data_dir/'V2_01_easy.zip'
if out.exists():
 if out.stat().st_size!=z.file_size:raise RuntimeError('Existing ZIP size differs')
 print('ZIP already exists; verifying CRC',flush=True)
else:
 packed=data_dir/'V2_01_easy.zip.deflate.part'
 received=packed.stat().st_size if packed.exists() else 0
 if received>z.compress_size:raise RuntimeError('Partial download larger than entry')
 with packed.open('ab') as f:
  while received<z.compress_size:
   count=min(16*1024*1024,z.compress_size-received);b=fetch(start+received,start+received+count-1);f.write(b);f.flush();received+=count;print(f'{received}/{z.compress_size} compressed bytes ({received/z.compress_size:.1%})',flush=True)
 dec=zlib.decompressobj(-15);tmp=data_dir/'V2_01_easy.zip.part';crc=0
 with packed.open('rb') as src,tmp.open('wb') as dest:
  while True:
   b=src.read(1024*1024)
   if not b:break
   raw=dec.decompress(b);dest.write(raw);crc=zlib.crc32(raw,crc)
  raw=dec.flush();dest.write(raw);crc=zlib.crc32(raw,crc)
 if not dec.eof or crc!=z.CRC or tmp.stat().st_size!=z.file_size:raise RuntimeError('ZIP stream/CRC/size check failed')
 tmp.rename(out);packed.unlink()
crc=0;sha=hashlib.sha256()
with out.open('rb') as f:
 for b in iter(lambda:f.read(1024*1024),b''):crc=zlib.crc32(b,crc);sha.update(b)
if crc!=z.CRC:raise RuntimeError('ZIP CRC check failed')
meta['sha256']=sha.hexdigest();(ROOT/'logs/euroc_download_metadata.json').write_text(json.dumps(meta,indent=2))
with zipfile.ZipFile(out) as archive:
 for info in archive.infolist():
  name=pathlib.PurePosixPath(info.filename)
  if name.is_absolute() or '..' in name.parts:raise RuntimeError('Unsafe archive path')
 archive.extractall(data_dir/'V2_01_easy')
print('PASS ZIP CRC and extracted',sha.hexdigest(),flush=True)
