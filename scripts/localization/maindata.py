import sys,struct; sys.path.insert(0,'/tmp/claude-0/u4'); from sf import *
SRC='/tmp/claude-0/gd/assets/bin/Data/mainData'
d=open(SRC,'rb').read(); s=SF(d); O={o['pid']:o for o in s.objs}
objs={o['pid']:[o['tid'],o['cid'],bytearray(s.data(o))] for o in s.objs}
def go_parse(b):
    n,=struct.unpack_from('<I',b,0); comps=[list(struct.unpack_from('<iii',b,4+12*i)) for i in range(n)]
    p=4+12*n+4; name,q=cstr_aligned(b,p); return comps,name.decode(),p,q
def sstr(t):
    t=t.encode(); r=struct.pack('<I',len(t))+t; return r+b'\0'*((-len(r))%4)
def rename(gopid,new):
    b=objs[gopid][2]; comps,name,p,q=go_parse(b); objs[gopid][2]=bytearray(b[:p]+sstr(new)+b[q:]); return name
nxt=[max(objs)+1]
def newpid(): nxt[0]+=1; return nxt[0]-1
def clone(gopid,newname):
    b=objs[gopid][2]; comps,name,p,q=go_parse(b)
    m={}
    for cid,fid,pid in comps: m[pid]=newpid()
    g=newpid()
    gb=bytearray(b[:4])
    for cid,fid,pid in comps: gb+=struct.pack('<iii',cid,0,m[pid])
    gb+=b[4+12*len(comps):p]+sstr(newname)+b[q:]
    objs[g]=[objs[gopid][0],1,gb]
    for cid,fid,pid in comps:
        tid,c,cb=objs[pid]; cb=bytearray(cb); struct.pack_into('<i',cb,4,g); objs[m[pid]]=[tid,c,cb]
    tr=[m[pid] for cid,fid,pid in comps if cid==4][0]
    return g,{cid:m[pid] for cid,fid,pid in comps},tr
assert rename(59,'Bald')=='Rate'; assert rename(97,'Lady')=='Credits'
gR,cR,tR=clone(59,'Dork'); gC,cC,tC=clone(97,'Ugly')
# Russian Rate: own material + UVs in the 512x128 RuRate texture
mb=objs[cR[114]][2]; assert struct.unpack_from('<ff',mb,120)==(1024.0,1024.0)
struct.pack_into('<ff',mb,120,512.0,128.0)
for off in (404,516,632,748):
    x,y,w,h=struct.unpack_from('<4f',mb,off); X=round(x*1024)
    struct.pack_into('<4f',mb,off,X/512,0.0,172/512,118/128)
mr=objs[cR[23]][2]; assert struct.unpack_from('<ii',mr,32)==(1,16); struct.pack_into('<ii',mr,32,1,439)
# Russian credits text
tb=objs[cC[114]][2]; t,q=cstr_aligned(tb,24); assert t==b'Developed by'
objs[cC[114]][2]=bytearray(tb[:24]+sstr('Разработано')+tb[q:])
# Russian copies start hidden (scale 0); the game code shows the right pair
for t_ in (tR,tC): struct.pack_into('<3f',objs[t_][2],36,0.0,0.0,0.0)
# add to ListContainer2 (transform 256)
pb=objs[256][2]; n,=struct.unpack_from('<I',pb,48)
for t_ in (tR,tC):
    assert struct.unpack_from('<ii',objs[t_][2],52)[1]==256 or True
pb=pb[:52+8*n]+struct.pack('<ii',0,tR)+struct.pack('<ii',0,tC)+pb[52+8*n:]; struct.pack_into('<I',pb,48,n+2); objs[256][2]=pb
# check the copies' father
for t_ in (tR,tC):
    tb_=objs[t_][2]; nn,=struct.unpack_from('<I',tb_,48); assert nn==0 and struct.unpack_from('<ii',tb_,52)[1]==256
pids=sorted(objs); table=bytearray(); body=bytearray()
for pid in pids:
    tid,cid,b=objs[pid]; body+=b'\0'*((-len(body))%8)
    table+=struct.pack('<iIIiHH',pid,len(body),len(b),tid,cid,0); body+=bytes(b)
head=bytearray(d[:s.obj_table_off-4])+struct.pack('<I',len(pids))+table+d[s.next_off:20+s.meta_size]
meta_size=len(head)-20; doff=max(s.data_off,(len(head)+15)&~15)
out=head+b'\0'*(doff-len(head))+body
struct.pack_into('>IIII',out,0,meta_size,len(out),9,doff)
open('/tmp/claude-0/ru/out/mainData','wb').write(out)
s2=SF(out); print('ok',s2.nobj,s2.data_off,len(out), gR,cR,gC,cC)
