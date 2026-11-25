import sys, struct; sys.path.insert(0,'/tmp/claude-0/u4'); from sf import *
FN='ba4c3803e66ef48d990ccbd626b5d502'
d=open('/tmp/claude-0/gd/assets/bin/Data/'+FN,'rb').read(); s=SF(d); O={o['pid']:o for o in s.objs}
def D(pid): return bytearray(s.data(O[pid]))
objs={o['pid']:(o['tid'],o['cid'],D(o['pid'])) for o in s.objs}
# new grid
X=[-1.83,-0.61,0.61,1.83]; Y=[0.9,0.0,-0.9]
GRID={'langEnglish':(X[0],Y[0]),'langChinese_Simp':(X[1],Y[0]),'langChinese_Trad':(X[2],Y[0]),'langJapanese':(X[3],Y[0]),
      'langKorean':(X[0],Y[1]),'langFrench':(X[1],Y[1]),'langSpanish':(X[2],Y[1]),'langGerman':(X[3],Y[1]),
      'langSwedish':(X[1],Y[2]),'lang9':(X[2],Y[2])}
def go_parse(b):
    n,=struct.unpack_from('<I',b,0); comps=[list(struct.unpack_from('<iii',b,4+12*i)) for i in range(n)]
    p=4+12*n+4; name,q=cstr_aligned(b,p); return comps,name.decode(),p,q
# clone Swedish (GO 1)
SE_GO=1; comps,name,p,q=go_parse(objs[1][2])
NEW={'go':70,'tr':71,'mb':72,'mf':73,'mr':74}
mapc={4:'tr',114:'mb',33:'mf',23:'mr'}
src={}
gb=bytearray(objs[1][2][:4])
for cid,fid,pid in comps: gb+=struct.pack('<iii',cid,0,NEW[mapc[cid]]); src[mapc[cid]]=pid
nm=b'lang9'; nb=struct.pack('<I',len(nm))+nm; nb+=b'\0'*((-len(nb))%4)
gb+=objs[1][2][4+12*len(comps):p]+nb+objs[1][2][q:]
objs[70]=(objs[1][0],1,gb)
for k in ('tr','mb','mf','mr'):
    tid,cid,b=objs[src[k]]; b=bytearray(b); struct.pack_into('<i',b,4,70); objs[NEW[k]]=(tid,cid,b)
mb=objs[72][2]; assert abs(struct.unpack_from('<f',mb,404)[0]-0.3671875)<1e-6
struct.pack_into('<ff',mb,120,128.0,128.0)
struct.pack_into('<4f',mb,404,0.0,54/128,105/128,74/128)
mr=objs[74][2]; assert struct.unpack_from('<ii',mr,32)==(1,18),struct.unpack_from('<ii',mr,32); struct.pack_into('<ii',mr,32,1,437)
# root transform children
tid,cid,rt=objs[19]; n,=struct.unpack_from('<I',rt,48)
rt=rt[:52+8*n]+struct.pack('<ii',0,71)+rt[52+8*n:]; struct.pack_into('<I',rt,48,n+1); objs[19]=(tid,cid,rt)
# positions
for pid,(tid,cid,b) in list(objs.items()):
    if cid!=1: continue
    comps,name,_,_=go_parse(b)
    if name in GRID:
        tp=[c[2] for c in comps if c[0]==4][0]; t=objs[tp][2]
        struct.pack_into('<ff',t,24,*GRID[name])
# rebuild file
pids=sorted(objs); table=bytearray(); body=bytearray()
for pid in pids:
    tid,cid,b=objs[pid]; body+=b'\0'*((-len(body))%8)
    table+=struct.pack('<iIIiHH',pid,len(body),len(b),tid,cid,0); body+=bytes(b)
head=bytearray(d[:s.obj_table_off-4])+struct.pack('<I',len(pids))+table+d[s.next_off:20+s.meta_size]
meta_size=len(head)-20; assert len(head)<=s.data_off
out=head+b'\0'*(s.data_off-len(head))+body
struct.pack_into('>II',out,0,meta_size,len(out))
open('/tmp/claude-0/ru/out/'+FN,'wb').write(out)
s2=SF(out); print(s2.nobj, s2.externals, len(out))
