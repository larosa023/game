"""Render a Tiled .tmx (csv layers + tile objects) to PNG for previewing. Missing tilesets drawn magenta.
usage: render_map.py map.tmx out.png [mapping tsx->image overrides as name=path ...]"""
import re,sys,os
from PIL import Image
tmx=sys.argv[1]; out=sys.argv[2]
over=dict(a.split('=',1) for a in sys.argv[3:])
base=os.path.dirname(tmx); s=open(tmx).read()
W,H,TW,TH=map(int,re.search(r'<map [^>]*width="(\d+)" height="(\d+)" tilewidth="(\d+)" tileheight="(\d+)"',s).groups())
ts=[]
for fg,src in re.findall(r'<tileset firstgid="(\d+)" source="([^"]+)"',s):
    p=os.path.normpath(os.path.join(base,src)); name=os.path.basename(src)
    img=None; cols=None
    if name in over: img=Image.open(over[name]).convert('RGBA')
    elif os.path.exists(p):
        t=open(p).read(); m=re.search(r'<image source="([^"]+)"',t)
        if m:
            ip=os.path.normpath(os.path.join(os.path.dirname(p),m.group(1)))
            if os.path.exists(ip): img=Image.open(ip).convert('RGBA')
    if img: cols=img.width//TW
    ts.append((int(fg),name,img,cols))
def tile(g):
    g&=0x1fffffff
    f,n,img,cols=[t for t in ts if t[0]<=g][-1]; i=g-f
    if img is None:
        return Image.new('RGBA',(TW,TH),(255,0,255,160))
    x,y=(i%cols)*TW,(i//cols)*TH
    return img.crop((x,y,x+TW,y+TH))
canvas=Image.new('RGBA',(W*TW,H*TH),(20,20,30,255))
for body in re.findall(r'<layer [^>]*>\s*<data encoding="csv">(.*?)</data>',s,re.S):
    gids=[int(v) for v in body.replace('\n','').split(',') if v.strip()]
    for k,g in enumerate(gids):
        if g: t=tile(g); canvas.alpha_composite(t,((k%W)*TW,(k//W)*TH))
for g,x,y in re.findall(r'<object [^>]*gid="(\d+)"[^>]*x="([\d.]+)" y="([\d.]+)"',s):
    t=tile(int(g)); canvas.alpha_composite(t,(int(float(x)),int(float(y))-TH))
canvas.save(out); print(out,canvas.size)
