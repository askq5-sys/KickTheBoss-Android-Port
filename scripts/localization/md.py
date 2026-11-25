import sys,struct; sys.path.insert(0,'/tmp/claude-0/u4'); from sf import *
d=open('/tmp/claude-0/gd/assets/bin/Data/mainData','rb').read(); s=SF(d); O={o['pid']:o for o in s.objs}
def go(pid):
    b=bytes(s.data(O[pid])); n,=struct.unpack_from('<I',b,0); comps=[struct.unpack_from('<iii',b,4+12*i) for i in range(n)]
    name,_=cstr_aligned(b,4+12*n+4); return comps,name.decode(errors='replace')
def tr_of(gopid):
    return [c[2] for c in go(gopid)[0] if c[0]==4][0]
def tr(pid):
    b=bytes(s.data(O[pid])); g=struct.unpack_from('<i',b,4)[0]; pos=struct.unpack_from('<3f',b,24); sc=struct.unpack_from('<3f',b,36)
    n,=struct.unpack_from('<I',b,48); ch=[struct.unpack_from('<ii',b,52+8*i)[1] for i in range(n)]; fa=struct.unpack_from('<ii',b,52+8*n)[1]
    return dict(go=g,pos=pos,sc=sc,ch=ch,fa=fa)
