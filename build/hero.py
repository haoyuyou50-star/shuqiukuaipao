import math,bpy
from common import *
from v01_shape import _body_shape,_base_dual

def build():
    p=asset('A01_Potato','薯球')
    mids,faces=_base_dual(); xyz=_body_shape(mids)
    center=(max(v.z for v in xyz)+min(v.z for v in xyz))/2
    ratio=.060/(max(v.z for v in xyz)-min(v.z for v in xyz))
    verts=[(v.x*ratio,v.y*ratio,(v.z-center)*ratio) for v in xyz]
    body=mesh('Potato_BODY',verts,faces,'honey',p,.00072)
    for p1 in body.data.polygons:p1.use_smooth=False
    for x,z in [(-.006,.006),(.006,.0067)]:
        hit,pt,n,_=body.ray_cast(Vector((x,-.1,z)),Vector((0,1,0)))
        assert hit
        bpy.ops.mesh.primitive_uv_sphere_add(segments=14,ring_count=7)
        o=move_to(bpy.context.object,p);o.name='Potato_Eye_L' if x<0 else 'Potato_Eye_R'
        o.location=pt+Vector((0,-.00030,0));o.rotation_euler.y=x*10
        for v in o.data.vertices:v.co.x*=.0020;v.co.y*=.00125;v.co.z*=.0031
        o.data.materials.append(material('dark'))
        for f in o.data.polygons:f.use_smooth=True
    p['collider']='sphere centered at root; diameter=0.060m'
    p['variants']='raw=pale; dusted=white; first_fry=honey; double_fry=orange'
    for color in ('pale','white','honey','orange'):material(color).use_fake_user=True
    r=asset('A05_RingReference','双环占位')
    def torus(name,key):
        v=[];f=[]
        for i in range(40):
            a=i*math.tau/40
            for j in range(8):
                b=j*math.tau/8; rr=.058+.009*math.cos(b)
                v.append((rr*math.cos(a),.009*math.sin(b),rr*math.sin(a)))
        for i in range(40):
            for j in range(8):
                f.append((i*8+j,i*8+(j+1)%8,((i+1)%40)*8+(j+1)%8,((i+1)%40)*8+j))
        return mesh(name,v,f,key,r,smooth=True)
    torus('Ring_Rim','petrol')
    cube('Hand_Grip',(0,0,-.077),(.038,.024,.026),'red',.008,r)
    marker('RING_CENTER',(0,0,0),r);marker('NORMAL_+Y',(0,.04,0),r);marker('GRIP',(0,0,-.078),r)
    r['placeholder_clear_ID_m']=.098
    b=asset('A06_BounceInsert','弹板嵌件')
    membrane=cylinder('Membrane',(0,0,0),.049,.006,'red',40,b,.002)
    membrane.rotation_euler.x=math.pi/2
    for x,height in [(-.024,.058),(-.012,.072),(0,.078),(.012,.072),(.024,.058)]:
        s=cube('Bounce_Rib',(x,-.0030,0),(.004,.0025,height),'cream',.00075,b)
        s.rotation_euler.y=.21
    marker('NORMAL_+Y',(0,.04,0),b)
    b['collider']='thin circular face sized to measured ring; placeholder 98mm'
    return [p,r,b]
