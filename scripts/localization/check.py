import sys,re,pickle,numpy as np; sys.path.insert(0,'/tmp/claude-0/ru'); from glyph import compose
from PIL import Image
D=pickle.load(open('/tmp/claude-0/ru/fonts.pkl','rb')); rows=[]
for name,(a,t) in D.items():
    a=(a>>4)*17  # 4444 quantisation
    im=Image.fromarray(a.astype(np.uint8),'RGBA'); E={}
    for line in t.splitlines():
        if line.startswith('char '):
            g={k:int(v) for k,v in re.findall(r'(\w+)=(-?\d+)',line)}
            E[g['id']]=(im.crop((g['x'],g['y'],g['x']+g['width'],g['y']+g['height'])) if g['width'] else None,g['xoffset'],g['yoffset'],g['xadvance'])
    rows.append(compose(E,'Бесплатные алмазы — Hello! Ёжик Щука',2))
W=max(r.width for r in rows); out=Image.new('RGB',(W,sum(r.height for r in rows)),(255,255,255)); y=0
for r in rows: out.paste(r,(0,y)); y+=r.height
out.save('/tmp/claude-0/ru/check.png')
