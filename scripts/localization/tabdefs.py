import sys,struct,pickle; sys.path.insert(0,'/tmp/claude-0/ru'); from tk2d import *
def build(b):
    place,sizes,capc=pickle.load(open('/tmp/claude-0/ru/tabs.pkl','rb'))
    cnt,defs,end=parse(b)
    D=[d for d in defs if d['name']==b'menuWeaponButton'][0]
    tpl=b[D['start']:D['end']]; n,q0=rd_str(tpl,0); rest=tpl[q0:]
    new=b''
    T=0.003125; cx,cy=-0.0015625,-0.003125
    for name,(x,y) in place.items():
        w,h=sizes[name]; nm=name.encode(); nb=struct.pack('<I',len(nm))+nm; nb+=b'\0'*((-len(nb))%4)
        r=bytearray(rest)
        x0,x1=cx-w*T/2,cx+w*T/2; y1=cy+capc*T; y0=y1-h*T
        struct.pack_into('<I6f',r,0,2,cx,(y0+y1)/2,0.0,w*T,h*T,0.0)
        struct.pack_into('<I6f',r,28,2,cx,(y0+y1)/2,0.0,w*T,h*T,0.0)
        struct.pack_into('<I12f',r,64,4,x0,y0,0,x1,y0,0,x0,y1,0,x1,y1,0)
        uvo=D['uv_off']-D['start']-q0
        u0,u1=x/1024,(x+w)/1024; v0,v1=(1024-y-h)/1024,(1024-y)/1024
        assert struct.unpack_from('<I',r,uvo)[0]==4
        struct.pack_into('<8f',r,uvo+4,u0,v0,u1,v0,u0,v1,u1,v1)
        new+=nb+bytes(r)
    out=bytearray(b[:end])+new+b[end:]
    struct.pack_into('<I',out,36,cnt+len(place))
    c2,d2,e2=parse(bytes(out)); assert c2==cnt+3 and bytes(out[e2:])==b[end:]
    return bytes(out)
