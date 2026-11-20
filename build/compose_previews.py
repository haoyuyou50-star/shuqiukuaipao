from PIL import Image,ImageDraw,ImageFont,ImageOps,ImageFilter
from pathlib import Path
import json
P=Path(__file__).resolve().parents[1]; R=P/'previews'
B='/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
N='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
BG='#F8EEDB';PLAIN='#FFF8EA';INK='#392922';MUTE='#705C4F';RED='#A84134';TEAL='#2A6969'
def font(n,bold=False):return ImageFont.truetype(B if bold else N,n,index=2)
def board(w,h):
    im=Image.new('RGB',(w,h),BG)
    return im,ImageDraw.Draw(im)
def txt(d,xy,t,n=24,fill=INK,bold=False):d.text(xy,t,fill=fill,font=font(n,bold))
def put(im,asset,box,r=18,mode='fit'):
    orig=Image.open(asset).convert('RGB')
    orig=Image.blend(orig,orig.filter(ImageFilter.MedianFilter(3)),.63)
    img=ImageOps.fit(orig,box,Image.Resampling.LANCZOS) if mode=='fit' else ImageOps.contain(orig,box,Image.Resampling.LANCZOS)
    mask=Image.new('L',img.size);ImageDraw.Draw(mask).rounded_rectangle((0,0,img.width-1,img.height-1),r,fill=255)
    return img,mask
def jpeg(im,name):im.save(R/name,'JPEG',quality=87,optimize=True,progressive=True,subsampling=0)
def stamp(d,x,y,t,fill=RED):
    d.rounded_rectangle((x,y,x+129,y+38),20,fill=fill)
    d.text((x+64,y+19),t,anchor='mm',fill=PLAIN,font=font(17,True))
def heading(d,w,kicker,head,sub):
    txt(d,(50,39),kicker,20,RED,True);txt(d,(45,72),head,57,INK,True);txt(d,(50,150),sub,23,MUTE)
    d.line((50,197,w-50,197),fill='#CCB397',width=1)
im,d=board(1550,1272)
heading(d,1550,'SHUQIU KUAIPAO   /   MODEL LIBRARY','薯球快跑 · 第一单','01  虫洞送餐   /   双环占位与后厨模块   /   Blender 实模预览')
img,mask=put(im,R/'level01.png',(1450,915),24);im.paste(img,(50,220),mask)
for i,(n,t) in enumerate([('A08','盒盖起步坡'),('A05','实体圆环占位'),('A09','开口式薯条盒'),('A04','番茄酱碟')]):
    x=50+i*366
    stamp(d,x,1171,n,RED if i%2==0 else TEAL);txt(d,(x+147,1170),t,23,bold=True)
jpeg(im,'01-first-order.jpg')
im,d=board(1640,860)
heading(d,1640,'A01  /  ONE MESH · FOUR COLORS','一颗薯球，四种状态','沿用第一版的轮廓与小眼睛   /   不换碰撞尺寸   /   不叠加颗粒贴图')
img,mask=put(im,R/'ball-states.png',(1540,466),24);im.paste(img,(50,222),mask)
for i,(cn,en,h) in enumerate([('生坯','RAW','#E8C491'),('裹粉','DUSTED','#FFF7E5'),('初炸','FIRST FRY','#FFBD58'),('复炸','DOUBLE FRY','#E88F36')]):
    x=184+i*392
    d.ellipse((x-29,718,x+3,750),fill=h,outline='#927865',width=1)
    txt(d,(x+14,702),cn,32,INK,True);txt(d,(x+15,753),en,16,MUTE,True)
jpeg(im,'02-potato-states.jpg')
M={a['id']:a for a in json.loads((P/'docs'/'manifest.json').read_text())['assets']}
groups=[
('03-batches-1-2.jpg','01–02   /   INTRO ORDERS','虫洞送餐 & 裹粉','起步短坡、宽口接球和可复用粉盘',['A01','A04','A05','A07','A08','A09','A02','A10','A19']),
('04-batches-3-4.jpg','03–04   /   FRY STATIONS','初炸 & 掐点回锅','独立弹板、锅沿灯、活动挡片、铲面与回旋围边',['A03','A06','A23','A11','A18','A20','A21','A22']),
('05-modules.jpg','MODULAR PARTS   /   REUSABLE SET','通用轨段与扩展厨具','小件可单独复用；轴心、限位和装配标记收录在源文件',['A12','A13','A14','A15','A16','A17','A24'])]
labels={'A01':'薯球','A02':'可拆铺粉层','A03':'自动炸锅','A04':'番茄酱碟','A05':'实体双环占位','A06':'条纹弹板嵌件','A07':'汉堡盒','A08':'外卖盒与活动盒盖','A09':'薯条盒接球槽','A10':'可复用浅盘','A11':'长柄锅铲','A12':'餐夹分岔件','A13':'带嘴量杯','A14':'擀面杖滚筒槽','A15':'直槽','A16':'弧槽','A17':'过渡坡','A18':'餐盘弧形围边','A19':'楔形垫块','A20':'转轴与支座','A21':'限位块','A22':'配重与夹具','A23':'活动挡片','A24':'星形脆片'}
for name,kicker,head,sub,items in groups:
    items=[x for x in items if x in M]
    if not items:continue
    w=1550; h=252+((len(items)+2)//3)*397
    im,d=board(w,h);heading(d,w,kicker,head,sub)
    for j,asset in enumerate(items):
        x=50+(j%3)*491;y=226+(j//3)*397
        d.rounded_rectangle((x,y,x+468,y+373),radius=19,fill=PLAIN)
        img,mask=put(im,R/'tiles'/f'{asset}.png',(468,292),15)
        im.paste(img,(x,y),mask)
        stamp(d,x+14,y+314,asset,TEAL)
        txt(d,(x+154,y+304),labels[asset],22,bold=True)
        txt(d,(x+155,y+336),f"{M[asset]['render_triangles']:,}  三角面 · 色块材质",15,MUTE)
    jpeg(im,name)

# Trace plot uses the original Bullet positions; this is not an illustration of a portal.
data=json.loads((P/'qa'/'level1_blender_result.json').read_text())
cases=data['cases'][1:]
if all('ball_center_trace_t_xyz' in c for c in cases):
    im,d=board(1550,845)
    heading(d,1550,'QA  /  REAL BULLET TRAJECTORIES','宽口接球，偏了也能收回来','60 mm 球 · 三次独立释放 · 图中为球心轨迹投影')
    d.rounded_rectangle((50,220,1500,674),18,fill=PLAIN)
    scale=2390
    xz=lambda x,y:(185+(y+.160)*scale,450-x*scale*.62)
    floor=cases[0]['floor']['floor_stations']
    for k in range(5):
        y=-.16+k*.1; x,_=xz(0,y)
        d.line((x,254,x,631),fill='#EDE1D0',width=1)
    d.line((86,450,1436,450),fill='#D5BF9F',width=2)
    channel=[xz(l,y) for y,l,_,z in floor]+[xz(r,y) for y,_,r,z in reversed(floor)]
    d.polygon(channel,fill='#F2DFC5',outline='#987C60',width=3)
    cx=.176+.085
    dx,dy=xz(0,cx); rx=scale*.074;ry=rx*.62
    d.ellipse((dx-rx,dy-ry,dx+rx,dy+ry),fill='#F3C3AF',outline='#BD6F56',width=3)
    for cs,col in zip(cases,(TEAL,'#BA472F','#A5731E')):
        pts=[xz(x,y) for t,x,y,z in cs['ball_center_trace_t_xyz']]
        d.line(pts,fill=col,width=5,joint='curve')
        for j in (0,-1):
            x,y=pts[j];d.ellipse((x-8,y-8,x+8,y+8),fill=col,outline=PLAIN,width=2)
    labels=[('接球宽口 228 mm',.006,253),('收口 100 mm',.166,253),('酱碟判定',.259,308)]
    for label,y,screenY in labels:
        x,_=xz(0,y);txt(d,(x-52,screenY),label,19,MUTE,True)
    for i,(a,b) in enumerate([('正中',TEAL),('左偏 80 mm','#BA472F'),('右偏 80 mm','#A5731E')]):
        x=57+i*293
        d.line((x,733,x+45,733),fill=b,width=5)
        txt(d,(x+57,714),a,24,INK,True)
    txt(d,(51,785),'通过：3/3 入碟判定 ｜ 此图不含传送、Unity/PICO 和球的最终静止测试',18,MUTE)
    jpeg(im,'06-funnel-qa.jpg')
