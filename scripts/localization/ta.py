import sys, struct; sys.path.insert(0,'/tmp/claude-0/u4'); from sf import *
DATA='/tmp/claude-0/gd/assets/bin/Data/'
def rewrite(path, repl):  # repl: pid -> new bytes
    d=open(path,'rb').read(); s=SF(d)
    out=bytearray(d[:s.data_off]); body=bytearray()
    for o in sorted(s.objs,key=lambda o:o['start']):
        data=repl.get(o['pid'],bytes(s.data(o)))
        body+=b'\0'*((-len(body))%8)
        struct.pack_into('<II',out,o['entry']+4,len(body),len(data)); body+=data
    out+=body; struct.pack_into('>I',out,4,len(out)); return bytes(out)
def get_text(fn):
    d=open(DATA+fn,'rb').read(); s=SF(d)
    o=[o for o in s.objs if o['cid']==49][0]; b=bytes(s.data(o)); n,p=cstr_aligned(b,0); t,q=cstr_aligned(b,p)
    return t, (o['pid'],b,p,q)
def set_text(fn, ctx, newtext):
    pid,b,p,q=ctx; body=struct.pack('<I',len(newtext))+newtext; body+=b'\0'*((-len(body))%4)
    return rewrite(DATA+fn,{pid:b[:p]+body+b[q:]})
