import sys, re, numpy as np, pickle
sys.path.insert(0,'/tmp/claude-0/ru'); from glyph import *; from cmp2 import CFG, make
CH=[chr(c) for c in range(0x410,0x450)]+['Ё','ё','—']
def pack(occ, sizes):
    H,W=occ.shape; occ=occ.copy(); pos={}
    order=sorted(sizes,key=lambda k:-sizes[k][1])
    for k in order:
        w,h=sizes[k]; w2,h2=w+2,h+2
        ii=np.pad(occ.astype(np.int32).cumsum(0).cumsum(1),((1,0),(1,0)))
        if H-h2<0: return None
        S=ii[h2:,w2:]-ii[:-h2,w2:]-ii[h2:,:-w2]+ii[:-h2,:-w2]
        ys,xs=np.nonzero(S==0)
        if len(ys)==0: return None
        j=np.lexsort((xs,ys))[0]; y,x=ys[j],xs[j]
        occ[y:y+h2,x:x+w2]=True; pos[k]=(x+1,y+1)
    return pos
out={}
for name in CFG:
    E,com,f,sz,sx=make(name); path,w,col,eff,ref,st=CFG[name]
    im,t,ch,_=load(name)
    glyphs={}
    for c in CH:
        src=c.upper() if name=='stencil' else c
        if name=='stencil' and c=='—': src=c
        glyphs[ord(c)]=render_glyph3(path,w,sz,src,com['base'],col,eff,sx,st)
    a=np.array(im); occ=a[...,3]>0
    for g in ch.values(): occ[g['y']:g['y']+g['height'],g['x']:g['x']+g['width']]=True
    sizes={k:(v[0].width,v[0].height) for k,v in glyphs.items() if v[0] is not None}
    H0=a.shape[0]; newH=H0
    pos=pack(occ,sizes)
    if pos is None:
        newH=H0*2; occ2=np.zeros((newH,a.shape[1]),bool); occ2[:H0]=occ; pos=pack(occ2,sizes)
        big=np.zeros((newH,a.shape[1],4),np.uint8); big[:H0]=a; a=big
    img=Image.fromarray(a,'RGBA')
    lines=[]
    for k,(gimg,xo,yo,xa) in glyphs.items():
        if gimg is None: x=y=gw=gh=0
        else: x,y=pos[k]; gw,gh=gimg.size; img.paste(gimg,(x,y))
        lines.append(f'char id={k} x={x} y={y} width={gw} height={gh} xoffset={xo} yoffset={yo} xadvance={xa} page=0 chnl=0 letter="{chr(k)}"')
    L=t.split('\n'); last=max(i for i,l in enumerate(L) if l.startswith('char '))
    L=L[:last+1]+lines+L[last+1:]
    n=sum(1 for l in L if l.startswith('char '))
    L=[re.sub(r'chars count=\d+',f'chars count={n}',l) for l in L]
    L=[re.sub(r'scaleH=\d+',f'scaleH={newH}',l) for l in L]
    out[name]=(img,'\n'.join(L)); img.save(f'/tmp/claude-0/ru/atlas_{name}.png')
    print(name, 'H',H0,'->',newH, 'glyphs',len(lines))
pickle.dump({k:(np.array(v[0]),v[1]) for k,v in out.items()},open('/tmp/claude-0/ru/fonts.pkl','wb'))
