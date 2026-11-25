from PIL import Image, ImageDraw, ImageFont
import numpy as np, cv2
SRC='/tmp/claude-0/u4/tex/24_HUDMaterial2.png'
im=np.array(Image.open(SRC).convert('RGBA'))
LIB='/usr/share/fonts/truetype/liberation/'
def fix(im, x0, x1, y0, y1, text):
    reg=im[y0-4:y1+4, x0-4:x1+4].astype(int)
    m=((reg[...,1]-reg[...,2])<75)&(reg[...,3]>150)
    m[:4,:]=m[-4:,:]=False; m[:,:4]=m[:,-4:]=False
    m=cv2.dilate(m.astype(np.uint8),np.ones((3,3),np.uint8),iterations=1)
    rgb=np.ascontiguousarray(reg[...,:3][...,::-1].astype(np.uint8))
    out=cv2.inpaint(rgb,m,5,cv2.INPAINT_TELEA)[...,::-1]
    reg2=reg.copy(); reg2[...,:3]=out
    # text: white fill, brownish outline
    W,H=x1-x0,y1-y0
    S=4; big=Image.new('RGBA',((W+8)*S,(H+8)*S),(0,0,0,0)); d=ImageDraw.Draw(big)
    f=ImageFont.truetype(LIB+'LiberationSans-Bold.ttf',int(H*S*1.05))
    bb=d.textbbox((0,0),text,font=f,stroke_width=int(1.6*S))
    tw,th=bb[2]-bb[0],bb[3]-bb[1]
    tmp=Image.new('RGBA',(tw+4,th+4),(0,0,0,0)); dt=ImageDraw.Draw(tmp)
    dt.text((-bb[0]+2,-bb[1]+2),text,font=f,fill=(255,255,255,255),stroke_width=int(1.6*S),stroke_fill=(150,118,88,255))
    tw2=min(W*S,int(tw*1.0)); sx=min(1.0,(W*S)/tw); tmp=tmp.resize((int(tmp.width*sx),int(tmp.height*min(1.0,(H*S+8)/th))),Image.LANCZOS)
    big.alpha_composite(tmp,(((W+8)*S-tmp.width)//2,((H+8)*S-tmp.height)//2))
    small=np.array(big.resize((W+8,H+8),Image.LANCZOS)).astype(float)/255
    a=small[...,3:4]
    base=reg2.astype(float)/255
    base[...,:3]=small[...,:3]*a+base[...,:3]*(1-a)
    im[y0-4:y1+4, x0-4:x1+4]=(np.clip(base,0,1)*255+0.5).astype(np.uint8)
fix(im,35,128,953,981,'ОЦЕНИ!')
fix(im,208,302,953,981,'ОЦЕНИ!')
Image.fromarray(im).save('/tmp/claude-0/ru/hud2_new.png')
c=Image.fromarray(im).crop((0,890,340,1024)); bg=Image.new('RGBA',c.size,(90,140,90,255)); bg.alpha_composite(c); bg.resize((c.width*3,c.height*3),Image.LANCZOS).save('/tmp/claude-0/ru/rate_new.png')
