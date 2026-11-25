import zipfile, zlib, struct, subprocess, os, tempfile, sys
from concurrent.futures import ThreadPoolExecutor
src,dst=sys.argv[1:3]
z=zipfile.ZipFile(src); names=z.namelist()
def comp(n):
    raw=z.read(n)
    with tempfile.TemporaryDirectory() as d:
        p=os.path.join(d,'x'); open(p,'wb').write(raw)
        subprocess.run(['/tmp/claude-0/zopfli/zopfli','--deflate','--i15',p],check=True)
        c=open(p+'.deflate','rb').read()
    assert zlib.decompress(c,-15)==raw
    z9=zlib.compressobj(9,zlib.DEFLATED,-15); c9=z9.compress(raw)+z9.flush()
    return n,raw,(c if len(c)<len(c9) else c9)
with ThreadPoolExecutor(os.cpu_count()) as ex: res=list(ex.map(comp,names))
out=bytearray(); cd=bytearray()
for n,raw,c in res:
    nm=n.encode(); off=len(out); crc=zlib.crc32(raw)&0xffffffff
    out+=struct.pack('<IHHHHHIIIHH',0x04034b50,20,0,8,0,0x5c21,crc,len(c),len(raw),len(nm),0)+nm+c
    cd+=struct.pack('<IHHHHHHIIIHHHHHII',0x02014b50,20,20,0,8,0,0x5c21,crc,len(c),len(raw),len(nm),0,0,0,0,0,off)+nm
cdo=len(out); out+=cd+struct.pack('<IHHHHIIH',0x06054b50,0,0,len(res),len(res),len(cd),cdo,0)
open(dst,'wb').write(out)
t=zipfile.ZipFile(dst); assert t.testzip() is None
print(os.path.getsize(src),'->',len(out), sum(len(c) for _,_,c in res))
