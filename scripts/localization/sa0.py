import sys, struct, pickle, numpy as np, os
sys.path.insert(0,'/tmp/claude-0/u4'); from sf import *
from PIL import Image
d=open('/tmp/claude-0/sharedassets0.assets','rb').read(); s=SF(d); O={o['pid']:o for o in s.objs}
D=pickle.load(open('/tmp/claude-0/ru/fonts.pkl','rb'))
TEXP={'arial':26,'papyrus':27,'stencil':34,'typew':35,'cooper':37}
FNTP={'arial':42,'stencil':44,'cooper':45,'typew':46,'papyrus':50}
new={}
def enc(a, fmt):
    a=a[::-1]  # bottom-up
    if fmt==13:
        a=a.astype(np.uint16)>>4
        return ((a[...,0]<<12)|(a[...,1]<<8)|(a[...,2]<<4)|a[...,3]).astype('<u2').tobytes()
    return a.astype(np.uint8).tobytes()
def tex_replace(pid, arr):
    b=bytes(s.data(O[pid])); t=parse_tex(b); h,w=arr.shape[:2]; assert w==t['w']
    raw=enc(arr,t['fmt'])
    n,p=cstr_aligned(b,0)
    nb=bytearray(b[:t['data_off']-4]); struct.pack_into('<iii',nb,p,w,h,len(raw))
    nb+=struct.pack('<I',len(raw))+raw+b[t['data_off']+t['data_len']:]
    return bytes(nb)
for k,(arr,txt) in D.items():
    new[TEXP[k]]=tex_replace(TEXP[k],arr)
    b=bytes(s.data(O[FNTP[k]])); n,p=cstr_aligned(b,0); old,q=cstr_aligned(b,p)
    tb=txt.encode(); body=struct.pack('<I',len(tb))+tb; body+=b'\0'*((-len(body))%4)
    new[FNTP[k]]=b[:p]+body+b[q:]
# RU flag: its own 128x128 texture (pid 436) + material (pid 437); the store atlas has no unused space
ru=np.array(Image.open('/tmp/claude-0/u4/tex/StoreMaterial_ru.png').convert('RGBA'))
fl=np.zeros((128,128,4),np.uint8); fl[0:74,0:105]=ru[89:163,376:481]
Image.fromarray(fl).save('/tmp/claude-0/ru/ruflag_tex.png')
b=bytes(s.data(O[36])); t=parse_tex(b); n,p=cstr_aligned(b,0)
nm=b'RuFlag'; nmb=struct.pack('<I',len(nm))+nm; nmb+=b'\0'*((-len(nmb))%4)
raw=fl[::-1].tobytes()
hdr=bytearray(b[p:t['data_off']-4]); struct.pack_into('<iii',hdr,0,128,128,len(raw))
TEX=nmb+bytes(hdr)+struct.pack('<I',len(raw))+raw+b[t['data_off']+t['data_len']:]
mb=bytearray(s.data(O[18])); mn,mp=cstr_aligned(mb,0)
nm=b'RuFlagMaterial'; nmb=struct.pack('<I',len(nm))+nm; nmb+=b'\0'*((-len(nmb))%4)
MAT=bytearray(nmb+bytes(mb[mp:]))
k=MAT.index(struct.pack('<ii',0,36)); struct.pack_into('<ii',MAT,k,0,436)
ADD=[(436,O[36]['tid'],28,TEX),(437,O[18]['tid'],21,bytes(MAT))]
# RU "ОЦЕНИ!" button: own 512x128 texture (pid 438) + material (pid 439, a copy of HUDMaterial2's)
h2=np.array(Image.open('/tmp/claude-0/ru/hud2_new.png').convert('RGBA'))
rt=np.zeros((128,512,4),np.uint8); rt[10:128,0:346]=h2[906:1024,0:346]
Image.fromarray(rt).save('/tmp/claude-0/ru/rurate_tex.png')
nm=b'RuRate'; nmb=struct.pack('<I',len(nm))+nm; nmb+=b'\0'*((-len(nmb))%4)
raw=rt[::-1].tobytes(); hdr=bytearray(b[p:t['data_off']-4]); struct.pack_into('<iii',hdr,0,512,128,len(raw))
TEX2=nmb+bytes(hdr)+struct.pack('<I',len(raw))+raw+b[t['data_off']+t['data_len']:]
mb=bytearray(s.data(O[16])); mn,mp=cstr_aligned(mb,0)
nm=b'RuRateMaterial'; nmb=struct.pack('<I',len(nm))+nm; nmb+=b'\0'*((-len(nmb))%4)
MAT2=bytearray(nmb+bytes(mb[mp:])); k=MAT2.index(struct.pack('<ii',0,24)); struct.pack_into('<ii',MAT2,k,0,438)
ADD+=[(438,O[36]['tid'],28,TEX2),(439,O[16]['tid'],21,bytes(MAT2))]
import sys as _s; _s.path.insert(0,'/tmp/claude-0/ru'); from tabdefs import build as _tb
new[425]=_tb(bytes(s.data(O[425])))
new[29]=tex_replace(29,np.array(Image.open('/tmp/claude-0/ru/atlas29_new.png').convert('RGBA')))
# rebuild
body=bytearray(); table={}
for o in sorted(s.objs,key=lambda o:o['start']):
    data=new.get(o['pid'],bytes(s.data(o)))
    body+=b'\0'*((-len(body))%8)
    table[o['pid']]=(len(body),len(data),o['tid'],o['cid']); body+=data
for pid,tid,cid,data in ADD:
    body+=b'\0'*((-len(body))%8); table[pid]=(len(body),len(data),tid,cid); body+=data
tb=b''.join(struct.pack('<iIIiHH',pid,*table[pid][:2],table[pid][2],table[pid][3],0) for pid in sorted(table))
meta=bytearray(d[:s.obj_table_off-4])+struct.pack('<I',len(table))+tb+d[s.next_off:20+s.meta_size]
doff=(len(meta)+15)&~15
out=meta+b'\0'*(doff-len(meta))+body
struct.pack_into('>IIII',out,0,len(meta)-20,len(out),9,doff)
os.makedirs('/tmp/claude-0/ru/out',exist_ok=True)
open('/tmp/claude-0/ru/out/sharedassets0.assets','wb').write(out)
for i in range(0,len(out),1<<20):
    open(f'/tmp/claude-0/ru/out/sharedassets0.assets.split{i>>20}','wb').write(out[i:i+(1<<20)])
print(len(d),'->',len(out), 'splits', (len(out)+(1<<20)-1)>>20)
# verify parse
s2=SF(out)
P2={o['pid']:o for o in s2.objs}
for pid in (26,27,34,35,36,37,436): print(parse_tex(s2.data(P2[pid])))
print(bytes(s2.data(P2[437])).hex()); print(s2.meta_size, s2.data_off, s2.nobj)
