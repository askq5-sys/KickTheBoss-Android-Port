import sys; sys.path.insert(0,'/tmp/claude-0/ru'); sys.path.insert(0,'/tmp/claude-0/tr')
from ta import *; import ru, os
def split_row(line):
    pieces=line.split(','); out=[]; cur=None
    for pc in pieces:
        if cur is None:
            if pc.startswith('"') and not (len(pc)>1 and pc.endswith('"')): cur=pc
            else: out.append(pc)
        else:
            cur+=','+pc
            if pc.endswith('"'): out.append(cur); cur=None
    if cur is not None: out.append(cur)
    return out
def val(f): return f[1:-1] if len(f)>1 and f.startswith('"') and f.endswith('"') else f
def q(t):
    t=t.replace('́','')
    assert '"' not in t and '\n' not in t, t
    return '"%s"'%t if ',' in t else t
def patch(fn, setter, out_dir):
    t,ctx=get_text(fn); lines=t.decode('utf-8').split('\n'); miss=[]
    for i,l in enumerate(lines):
        if not l.strip(): continue
        f=split_row(l); setter(i,f,miss); lines[i]=','.join(f)
    data=set_text(fn,ctx,'\n'.join(lines).encode('utf-8'))
    open(os.path.join(out_dir,fn),'wb').write(data); return miss
def put(f,c,v):
    while len(f)<=c: f.append('')
    f[c]=q(v)
OUT='/tmp/claude-0/ru/out'
# hints
def s_h(i,f,m):
    if i==0: return
    k=val(f[0]).strip()
    if k in ru.HINTS: put(f,10,ru.HINTS[k])
    elif val(f[1]).strip(): m.append(k)
print('hints miss',patch('1b42fb407aa5446eb926ad0cc940da9d',s_h,OUT))
def s_w(i,f,m):
    if i==0: return
    k=val(f[0]).strip()
    if k in ru.WEAPONS: put(f,19,ru.WEAPONS[k])
    elif k: m.append(k); put(f,19,val(f[1]).strip())
    else: put(f,19,'')
print('weap miss',patch('56db9ce4af8cc4bcb969310fb31f5ef9',s_w,OUT))
def s_s(i,f,m):
    if i==0: return
    k=val(f[0]).strip()
    if k in ru.STORE: put(f,24,ru.STORE[k][0]); put(f,25,ru.STORE[k][1])
    else:
        if k: m.append(k)
        put(f,24,val(f[1]).strip() if len(f)>1 else ''); put(f,25,val(f[3]).strip() if len(f)>3 else '')
print('store miss',patch('6cf18816cb1cd48d180ca03dbc4618dd',s_s,OUT))
def s_m(i,f,m):
    if i==0: return
    k=val(f[0]).strip()
    if k in ru.MESSAGES: put(f,10,ru.MESSAGES[k])
    elif k: m.append(k); put(f,10,val(f[1]))
print('msg miss',patch('a046ecbc64a914324beca3a5de03af94',s_m,OUT))
def s_b(i,f,m):
    if i==0: put(f,12,'Russian'); return
    en=val(f[3]).strip() if len(f)>3 else ''
    if en in ru.BOSS: put(f,12,ru.BOSS[en])
    else:
        if en: m.append(en)
        put(f,12,en)
print('boss miss',patch('ff08e6c12d7f246ee9e7b8b6535287de',s_b,OUT))
