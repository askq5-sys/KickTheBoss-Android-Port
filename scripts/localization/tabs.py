import sys,struct,numpy as np,pickle
sys.path.insert(0,'/tmp/claude-0/ru'); from glyph import *; from tk2d import *
from cmp2 import CFG
from PIL import Image
path,w,col,eff,ref,st=CFG['stencil']
CAP=16
sz=fit_size(path,CAP,ref='H',wght=w)
def line(text,sx,track=0):
    gl=[render_glyph3(path,w,sz,c,sz,col,None,sx,0,ss=4) for c in text]   # baseline at y=sz+8
    W=sum(g[3] for g in gl)+20; H=sz*3
    cv=Image.new('RGBA',(W,H),(0,0,0,0)); x=5
    for img,xo,yo,xa in gl:
        if img is not None: cv.alpha_composite(img,(x+xo,yo+8))
        x+=xa+track
    return cv
items=[('menuWeaponButton_r','ОРУЖИЕ',0.866,0),('menuStoreButton_r','МАГАЗИН',0.866,-1),('menuOptionButton_r','ОПЦИИ',0.866,0)]
cvs={k:line(t,sx,tr) for k,t,sx,tr in items}
# common vertical extent (same baseline in every label)
tops=[];bots=[]
for cv in cvs.values():
    a=np.array(cv)[...,3]; ys=np.nonzero(a.max(1)>0)[0]; tops.append(ys.min()); bots.append(ys.max()+1)
top,bot=min(tops),max(bots)
base_y=sz+8; cap_top=base_y-CAP
L={}
for k,cv in cvs.items():
    a=np.array(cv)[...,3]; xs=np.nonzero(a.max(0)>0)[0]
    L[k]=cv.crop((xs.min(),top,xs.max()+1,bot))
cap_center=(cap_top+base_y)/2-top      # in label pixels from the top
for k,v in L.items(): print(k,v.size)
s=SF(open('/tmp/claude-0/sharedassets0.assets','rb').read()); O={o['pid']:o for o in s.objs}
b=bytes(s.data(O[425])); cnt,defs,end=parse(b)
atlas=np.array(Image.open('/tmp/claude-0/u4/tex/29_atlas0.png').convert('RGBA'))
occ=atlas[...,3]>0
for D in defs:
    uv=np.array([struct.unpack_from('<2f',b,D['uv_off']+4+8*i) for i in range(D['nuv'])])*1024
    x0,x1=int(uv[:,0].min()),int(np.ceil(uv[:,0].max())); y0,y1=1024-int(np.ceil(uv[:,1].max())),1024-int(uv[:,1].min())
    occ[max(0,y0-2):y1+2,max(0,x0-2):x1+2]=True
place={}
for k,im in L.items():
    w2,h2=im.width+4,im.height+4
    ii=np.pad(occ.astype(np.int32).cumsum(0).cumsum(1),((1,0),(1,0)))
    S=ii[h2:,w2:]-ii[:-h2,w2:]-ii[h2:,:-w2]+ii[:-h2,:-w2]
    ys,xs=np.nonzero(S==0); j=np.lexsort((xs,ys))[0]; y,x=ys[j]+2,xs[j]+2
    occ[y-2:y+im.height+2,x-2:x+im.width+2]=True; place[k]=(x,y)
    atlas[y:y+im.height,x:x+im.width]=np.array(im)
Image.fromarray(atlas).save('/tmp/claude-0/ru/atlas29_new.png')
pickle.dump((place,{k:v.size for k,v in L.items()},cap_center),open('/tmp/claude-0/ru/tabs.pkl','wb'))
prev=Image.new('RGBA',(420,60),(150,95,50,255)); x=5
for k,im in L.items(): prev.alpha_composite(im,(x,20)); x+=im.width+20
prev.resize((1260,180),Image.LANCZOS).save('/tmp/claude-0/ru/tabs_prev.png')
print('cap_center',cap_center)
