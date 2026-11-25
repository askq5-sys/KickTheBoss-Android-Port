import sys,struct,glob,os,numpy as np; sys.path.insert(0,'/tmp/claude-0/u4'); from sf import *
D='/tmp/claude-0/gd/assets/bin/Data/'
files=[f for f in glob.glob(D+'*') if os.path.isfile(f) and '.split' not in f]
out=[]
srcs=[(f,SF(open(f,'rb').read())) for f in files if not f.endswith(('.png','.xml','Config','File'))] 
def ok(v,s): return abs(v*s-round(v*s))<0.01
for fn,s in srcs:
    for o in s.objs:
        if o['cid']!=114: continue
        b=bytes(s.data(o))
        if b.find(struct.pack('<ff',1024.0,512.0))<0: continue
        n=len(b)//4; f=np.frombuffer(b[:n*4],'<f4')
        for i in range(n-3):
            x,y,w,h=[float(v) for v in f[i:i+4]]
            if 0<=x<1 and 0<y<1 and 0<w<0.6 and 0<h<0.6 and ok(x,1024) and ok(y,512) and ok(w,1024) and ok(h,512) and w*1024>=8 and h*512>=8:
                out.append((round(x*1024),round(512-(y+h)*512),round(w*1024),round(h*512),os.path.basename(fn)[:8],o['pid'],i*4))
hit=[r for r in out if r[0]<113 and r[0]+r[2]>0 and r[1]<490 and r[1]+r[3]>408]
print(len(out)); print(hit)
import pickle; pickle.dump(out,open('/tmp/claude-0/ru/rects2.pkl','wb'))
