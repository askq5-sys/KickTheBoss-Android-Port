import sys,struct; sys.path.insert(0,'/tmp/claude-0/u4'); from sf import *
def rd_str(b,p):
    n,=struct.unpack_from('<I',b,p); v=b[p+4:p+4+n]; p=(p+4+n+3)&~3; return v,p
def rd_arr(b,p,elem):
    n,=struct.unpack_from('<I',b,p); return n,p+4+n*elem
def parse_def(b,p):
    st=p; D={'start':p}
    D['name'],p=rd_str(b,p)
    for k,e in [('bounds',12),('ubounds',12)]: n,p=rd_arr(b,p,e)
    D['texel']=p; p+=8
    D['pos_off']=p; n,p=rd_arr(b,p,12)
    n,p=rd_arr(b,p,12); n,p=rd_arr(b,p,16)
    D['uv_off']=p; n,p=rd_arr(b,p,8); D['nuv']=n
    n,p=rd_arr(b,p,4)
    D['mat']=struct.unpack_from('<iii',b,p); p+=12
    D['guid'],p=rd_str(b,p)
    D['extract']=struct.unpack_from('<5i',b,p); p+=20
    D['flipped'],D['complex'],D['ctype']=struct.unpack_from('<3i',b,p); p+=12
    n,p=rd_arr(b,p,12); n,p=rd_arr(b,p,4); n,p=rd_arr(b,p,4); p+=8
    D['end']=p; return D
def parse(b):
    cnt=struct.unpack_from('<I',b,36)[0]; p=40; defs=[]
    for i in range(cnt):
        D=parse_def(b,p); defs.append(D); p=D['end']
    return cnt,defs,p
if __name__=='__main__':
    s=SF(open('/tmp/claude-0/sharedassets0.assets','rb').read()); O={o['pid']:o for o in s.objs}
    b=bytes(s.data(O[425])); cnt,defs,p=parse(b)
    print(cnt,p,len(b)); print(b[p:p+120].hex())
    for D in defs:
        uv=[struct.unpack_from('<2f',b,D['uv_off']+4+8*i) for i in range(D['nuv'])]
        print(D['name'].decode(), D['mat'], D['flipped'], [tuple(round(v*1024) for v in u) for u in uv][:4])
