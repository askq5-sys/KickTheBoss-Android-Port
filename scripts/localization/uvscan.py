import sys,struct,glob,os,numpy as np; sys.path.insert(0,'/tmp/claude-0/u4'); from sf import *
D='/tmp/claude-0/gd/assets/bin/Data/'
files=[f for f in glob.glob(D+'*') if os.path.isfile(f) and '.split' not in f]
blobs=[]
for f in files:
    try: blobs.append(SF(open(f,'rb').read()))
    except Exception: pass
blobs.append(SF(open('/tmp/claude-0/sharedassets0.assets','rb').read()))
rects=set()
def ok(v,s): return abs(v*s-round(v*s))<0.02
for s in blobs:
    for o in s.objs:
        if o['cid']!=114: continue
        b=bytes(s.data(o)); n=len(b)//4
        if n<4: continue
        f=np.frombuffer(b[:n*4],'<f4')
        for i in range(n-3):
            x,y,w,h=f[i:i+4]
            if 0<=x<1 and 0<=y<1 and 0<w<=1 and 0<h<=1 and x+w<=1.0001 and y+h<=1.0001 and ok(x,1024) and ok(y,512) and ok(w,1024) and ok(h,512) and w*1024>=4 and h*512>=4:
                rects.add((round(x*1024),round(512-(y+h)*512),round(w*1024),round(h*512)))
print(len(rects))
hit=[r for r in rects if r[0]<113 and r[0]+r[2]>0 and r[1]<490 and r[1]+r[3]>408]
print('rects over our slot:',hit[:20])
import pickle; pickle.dump(rects,open('/tmp/claude-0/ru/rects.pkl','wb'))
