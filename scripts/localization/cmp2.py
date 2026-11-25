import sys; sys.path.insert(0,'/tmp/claude-0/ru'); from glyph import *
LIB='/usr/share/fonts/truetype/liberation/'
CFG={ # path, wght, color, effect, fit_ref, stencil gap
 'arial':(LIB+'LiberationSans-Bold.ttf',None,(17,17,17),'bevel','x',0),
 'stencil':(GF+'podkova/Podkova[wght].ttf',800,(68,34,17),None,'H',2),
 'cooper':(GF+'podkova/Podkova[wght].ttf',800,(34,17,17),None,'x',0),
 'typew':(GF+'podkova/Podkova[wght].ttf',500,(0,0,0),'bevel','x',0),
 'papyrus':(GF+'kurale/Kurale-Regular.ttf',None,(0,0,0),'shadow','x',0),
}
PAD={'arial':1,'stencil':0,'cooper':0,'typew':1,'papyrus':2}
def make(name):
    E,com=orig_entries(name); path,w,col,eff,ref,st=CFG[name]
    th=E[ord(ref)][0].height-PAD[name]
    sz=fit_size(path,th,ref=ref,wght=w); f=ttf(path,sz,w)
    sample='Hello World Aag Boss'
    if name=='stencil': sample=sample.upper()
    ow=sum(E[ord(c)][3] for c in sample); cw=sum(f.getlength(c) for c in sample)
    sx=max(0.75,min(1.1,ow/cw))
    return E,com,f,sz,sx
if __name__=='__main__':
    rows=[]
    for name in CFG:
        E,com,f,sz,sx=make(name); path,w,col,eff,ref,st=CFG[name]
        txt='Привет, ёжик! Aag ЩЮЯЖФ щюяжф ОБРАЗ'
        if name=='stencil': txt=txt.upper()
        ent=dict(E); ent.update({ord(c):render_glyph2(f,c,com['base'],col,eff,sx,st) for c in set(txt) if ord(c)>127})
        rows.append(compose(E,'Hello, World! Aag Boss' if name!='stencil' else 'HELLO, WORLD! AAG BOSS')); rows.append(compose(ent,txt)); print(name,sz,round(sx,3))
    W=max(r.width for r in rows); out=Image.new('RGB',(W,sum(r.height for r in rows)),(255,255,255)); y=0
    for r in rows: out.paste(r,(0,y)); y+=r.height
    out.save('/tmp/claude-0/ru/cmp_all.png')
