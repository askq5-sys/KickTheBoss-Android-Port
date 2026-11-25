import re, numpy as np
from PIL import Image, ImageFont, ImageDraw, ImageFilter
TEX='/tmp/claude-0/u4/tex/'
FONTS={ # name: (png, fnt)
 'arial':('26_FontBlackArialBevel','FontBlackArialBevel'),
 'stencil':('34_FontBrownStencil','FontBrownStencil'),
 'cooper':('37_FontCooperBlack','FontCooperBlack'),
 'typew':('35_FontTypeWriterBlack','FontTypeWriterBlack'),
 'papyrus':('27_FontPapyrusBlack','FontPapyrusBlack'),
}
def load(name):
    png,fn=FONTS[name]; im=Image.open(TEX+png+'.png').convert('RGBA'); t=open('/tmp/claude-0/fnt_%s.txt'%fn).read()
    ch={}
    for line in t.splitlines():
        if line.startswith('char '):
            kv=dict(re.findall(r'(\w+)=(-?\d+)',line)); ch[int(kv['id'])]={k:int(v) for k,v in kv.items()}
    com=dict(re.findall(r'(\w+)=(-?\d+)',[l for l in t.splitlines() if l.startswith('common')][0]))
    return im,t,ch,{k:int(v) for k,v in com.items()}
GF='/tmp/claude-0/gf/gfonts/ofl/'
def ttf(path,size,wght=None):
    f=ImageFont.truetype(path,size)
    if wght is not None:
        try: f.set_variation_by_axes([wght])
        except Exception as e: print('var fail',e)
    return f
def fit_size(path,target_h,ref='H',wght=None):
    lo,hi=4,200
    while lo<hi:
        m=(lo+hi+1)//2; f=ttf(path,m,wght); b=f.getbbox(ref)
        if b[3]-b[1]<=target_h: lo=m
        else: hi=m-1
    return lo

def render_glyph(font, c, base, color, effect=None, pad=2):
    # returns (img RGBA cropped, xoffset, yoffset, xadvance) BMFont style relative to line top where baseline=base
    S=font.size*3+20
    cv=Image.new('L',(S,S),0); d=ImageDraw.Draw(cv)
    ox,oy=S//4,S//4
    asc=font.getmetrics()[0]
    d.text((ox,oy),c,font=font,fill=255)  # top-left of ascent box at (ox,oy); baseline at oy+asc
    bl=oy+asc
    a=np.array(cv).astype(np.float32)/255
    rgba=np.zeros((S,S,4),np.float32)
    if effect=='shadow':  # papyrus: soft brown shadow down-right
        sh=Image.fromarray((a*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.0))
        sh=np.roll(np.roll(np.array(sh).astype(np.float32)/255,1,0),1,1)*0.85
        rgba[...,:3]=np.array((85,51,0),np.float32)/255; rgba[...,3]=sh
    elif effect=='bevel':  # faint light edge down-right
        hl=np.roll(np.roll(a,1,0),1,1)*0.35
        rgba[...,:3]=1.0; rgba[...,3]=hl
    # composite glyph colour over effect
    col=np.array(color,np.float32)/255
    A=a+rgba[...,3]*(1-a)
    rgb=(col*a[...,None]+rgba[...,:3]*rgba[...,3:4]*(1-a[...,None]))/np.maximum(A,1e-6)[...,None]
    out=np.dstack([rgb,A]); out=(np.clip(out,0,1)*255+0.5).astype(np.uint8)
    ys,xs=np.nonzero(out[...,3]>0)
    if len(xs)==0:
        return None,0,0,int(round(font.getlength(c)))
    x0,x1,y0,y1=xs.min(),xs.max()+1,ys.min(),ys.max()+1
    img=Image.fromarray(out[y0:y1,x0:x1],'RGBA')
    return img, int(x0-ox), int(y0-(bl-base)), int(round(font.getlength(c)))

def compose(entries, text, scale=2):
    # entries: id -> (img,xo,yo,xa)
    W=sum(entries[ord(c)][3] for c in text if ord(c) in entries)+20; H=110
    cv=Image.new('RGBA',(W,H),(235,225,200,255)); x=5
    for c in text:
        e=entries.get(ord(c))
        if e is None: x+=10; continue
        img,xo,yo,xa=e
        if img is not None: cv.alpha_composite(img,(max(0,x+xo),max(0,10+yo)))
        x+=xa
    return cv.resize((cv.width*scale,cv.height*scale),Image.LANCZOS)

def orig_entries(name):
    im,t,ch,com=load(name); E={}
    for i,g in ch.items():
        E[i]=(im.crop((g['x'],g['y'],g['x']+g['width'],g['y']+g['height'])) if g['width'] else None,g['xoffset'],g['yoffset'],g['xadvance'])
    return E,com

def stencil_cut(a, gap):
    from scipy import ndimage
    bg=a<0.5; lab,n=ndimage.label(bg)
    border=set(np.unique(np.concatenate([lab[0],lab[-1],lab[:,0],lab[:,-1]])))
    out=a.copy()
    for k in range(1,n+1):
        if k in border: continue
        ys,xs=np.nonzero(lab==k)
        if len(xs)<4: continue
        cx=int(round(xs.mean())); y0,y1=ys.min(),ys.max()
        x0=cx-gap//2; x1=x0+gap
        for x in range(x0,x1):
            y=y0-1
            while y>=0 and a[y,x]>=0.2: out[y,x]=0; y-=1
            y=y1+1
            while y<a.shape[0] and a[y,x]>=0.2: out[y,x]=0; y+=1
    return out

def render_glyph2(font, c, base, color, effect=None, sx=1.0, stencil=0):
    S=font.size*3+20
    cv=Image.new('L',(S,S),0); d=ImageDraw.Draw(cv)
    ox,oy=S//4,S//4; asc=font.getmetrics()[0]
    d.text((ox,oy),c,font=font,fill=255); bl=oy+asc
    if sx!=1.0:
        cv=cv.resize((max(1,int(round(S*sx))),S),Image.LANCZOS); ox=int(round(ox*sx))
    a=np.array(cv).astype(np.float32)/255
    if stencil: a=stencil_cut(a,stencil)
    H,W=a.shape
    eff=np.zeros((H,W),np.float32); ecol=np.zeros(3,np.float32)
    if effect=='shadow':
        sh=Image.fromarray((a*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.0))
        eff=np.roll(np.roll(np.array(sh).astype(np.float32)/255,1,0),1,1)*0.85; ecol=np.array((85,51,0),np.float32)/255
    elif effect=='bevel':
        eff=np.roll(np.roll(a,1,0),1,1)*0.35; ecol=np.ones(3,np.float32)
    col=np.array(color,np.float32)/255
    A=a+eff*(1-a)
    rgb=(col*a[...,None]+ecol*(eff*(1-a))[...,None])/np.maximum(A,1e-6)[...,None]
    out=(np.clip(np.dstack([rgb,A]),0,1)*255+0.5).astype(np.uint8)
    ys,xs=np.nonzero(out[...,3]>0)
    xa=int(round(font.getlength(c)*sx))
    if len(xs)==0: return None,0,0,xa
    x0,x1,y0,y1=xs.min(),xs.max()+1,ys.min(),ys.max()+1
    return Image.fromarray(out[y0:y1,x0:x1],'RGBA'), int(x0-ox), int(y0-(bl-base)), xa

def render_glyph3(path, wght, size, c, base, color, effect=None, sx=1.0, stencil=0, ss=4):
    """Supersampled: draw at size*ss, stencil-cut at that scale, downscale, then effects."""
    F=ttf(path,size*ss,wght); f1=ttf(path,size,wght)
    S=size*ss*3+20*ss
    cv=Image.new('L',(S,S),0); d=ImageDraw.Draw(cv)
    ox,oy=S//4,S//4; asc=F.getmetrics()[0]
    d.text((ox,oy),c,font=F,fill=255); bl=oy+asc
    a=np.array(cv).astype(np.float32)/255
    if stencil: a=stencil_cut(a,stencil*ss)
    W=int(round(S*sx/ss)); H=S//ss
    a=np.array(Image.fromarray((a*255).astype(np.uint8)).resize((W,H),Image.LANCZOS)).astype(np.float32)/255
    ox=ox*sx/ss; bl=bl/ss
    eff=np.zeros_like(a); ecol=np.zeros(3,np.float32)
    if effect=='shadow':
        sh=Image.fromarray((a*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.0))
        eff=np.roll(np.roll(np.array(sh).astype(np.float32)/255,1,0),1,1)*0.85; ecol=np.array((85,51,0),np.float32)/255
    elif effect=='bevel':
        eff=np.roll(np.roll(a,1,0),1,1)*0.35; ecol=np.ones(3,np.float32)
    col=np.array(color,np.float32)/255
    A=a+eff*(1-a)
    rgb=(col*a[...,None]+ecol*(eff*(1-a))[...,None])/np.maximum(A,1e-6)[...,None]
    out=(np.clip(np.dstack([rgb,A]),0,1)*255+0.5).astype(np.uint8)
    out[...,3][out[...,3]<8]=0
    ys,xs=np.nonzero(out[...,3]>0)
    xa=int(round(f1.getlength(c)*sx))
    if len(xs)==0: return None,0,0,xa
    x0,x1,y0,y1=xs.min(),xs.max()+1,ys.min(),ys.max()+1
    return Image.fromarray(out[y0:y1,x0:x1],'RGBA'), int(round(x0-ox)), int(round(y0-(bl-base))), xa
