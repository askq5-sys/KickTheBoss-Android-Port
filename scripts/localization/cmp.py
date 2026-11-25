import sys; sys.path.insert(0,'/tmp/claude-0/ru'); from glyph import *
LIB='/usr/share/fonts/truetype/liberation/'
CAND={
 'arial':[(LIB+'LiberationSans-Bold.ttf',None)],
 'stencil':[(GF+'sirinstencil/SirinStencil-Regular.ttf',None),(GF+'stalinistone/StalinistOne-Regular.ttf',None)],
 'cooper':[(GF+'podkova/Podkova[wght].ttf',800),(GF+'yesevaone/YesevaOne-Regular.ttf',None),(GF+'ptserif/PT_Serif-Web-Bold.ttf',None),(GF+'rubik/Rubik[wght].ttf',900)],
 'typew':[(GF+'kellyslab/KellySlab-Regular.ttf',None),(GF+'podkova/Podkova[wght].ttf',500),(GF+'ptserif/PT_Serif-Web-Regular.ttf',None)],
 'papyrus':[(GF+'kurale/Kurale-Regular.ttf',None)],
}
COL={'arial':(17,17,17),'stencil':(68,34,17),'cooper':(34,17,17),'typew':(0,0,0),'papyrus':(0,0,0)}
EFF={'arial':'bevel','typew':'bevel','papyrus':'shadow'}
name=sys.argv[1]
E,com=orig_entries(name); H=E[ord('H')][0].height
rows=[compose(E,'Hello, World! Aag Boss')]
for path,w in CAND[name]:
    f0=ttf(path,20,w)
    sz=fit_size(path,H-1,wght=w); f=ttf(path,sz,w)
    txt='Hello Aag ПРИВЕТ Привет, ёжик! ЩЮЯЖФ щюяжф'
    if name=='stencil': txt=txt.upper()
    ent={ord(c):render_glyph(f,c,com['base'],COL[name],EFF.get(name)) for c in set(txt)}
    rows.append(compose(ent,txt)); print(path.split('/')[-1],sz)
W=max(r.width for r in rows); out=Image.new('RGB',(W,sum(r.height for r in rows)),(255,255,255)); y=0
for r in rows: out.paste(r,(0,y)); y+=r.height
out.save('/tmp/claude-0/ru/cmp_%s.png'%name)
