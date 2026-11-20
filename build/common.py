import bpy, math
from mathutils import Vector
D=.060
PALETTE={'cream':'FCEDD1','red':'D74E42','honey':'FFBD58','petrol':'2F7374','dark':'483129','pale':'E8C491','orange':'E88F36','white':'FFF7E5','mint':'A8C9B7','rust':'B66B37','oil':'F6B049','sauce':'BC352A'}
_active=None

def material(key):
    color=PALETTE.get(key,key).lstrip('#')
    name=f'Kitchen_{key}'
    if m:=bpy.data.materials.get(name): return m
    rgba=tuple(v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in [int(color[i:i+2],16)/255 for i in (0,2,4)])+(1,)
    m=bpy.data.materials.new(name);m.diffuse_color=rgba;m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=rgba
    p.inputs['Roughness'].default_value={'oil':.32,'sauce':.37,'petrol':.59,'cream':.65}.get(key,.61)
    return m

def move_to(o,parent):
    c=parent.users_collection[0] if parent else _active
    if c and c not in o.users_collection: c.objects.link(o)
    for k in list(o.users_collection):
        if c and k!=c:k.objects.unlink(o)
    if parent:o.parent=parent
    return o

def empty(name,loc=(0,0,0),parent=None):
    o=bpy.data.objects.new(name,None);(_active if parent is None else parent.users_collection[0]).objects.link(o)
    o.parent=parent;o.location=loc;o.empty_display_size=.014
    return o

def asset(key,label):
    global _active
    _active=bpy.data.collections.new(key);bpy.context.scene.collection.children.link(_active)
    o=empty(key);o['display_name']=label;o['canonical_axis']='Blender +Y downstream, +Z up';o['ball_diameter_m']=D
    return o

def marker(name,loc,parent=None):
    o=empty(name,loc,parent);o['marker']=True;return o

def bevel_obj(o,width):
    if width>0:
        m=o.modifiers.new('Toy edge','BEVEL');m.width=width;m.segments=2;m.limit_method='ANGLE';m.angle_limit=.23
        o.modifiers.new('Weighted shading','WEIGHTED_NORMAL')
    return o

def mesh(name,verts,faces,color='red',parent=None,bevel=0,smooth=False):
    d=bpy.data.meshes.new(name);d.from_pydata(verts,[],faces);d.validate();d.update()
    o=bpy.data.objects.new(name,d);(parent.users_collection[0] if parent else _active).objects.link(o);o.parent=parent
    if color:d.materials.append(material(color))
    for p in d.polygons:p.use_smooth=smooth
    return bevel_obj(o,bevel)

def cube(name,loc,dims,color='cream',bevel=.003,parent=None):
    a,b,c=[d/2 for d in dims]
    v=[(-a,-b,-c),(a,-b,-c),(a,b,-c),(-a,b,-c),(-a,-b,c),(a,-b,c),(a,b,c),(-a,b,c)]
    o=mesh(name,v,[(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],color,parent,bevel);o.location=loc;return o

def cylinder(name,loc,radius,depth,color='cream',sides=32,parent=None,bevel=.002):
    v=[(radius*math.cos(2*math.pi*j/sides),radius*math.sin(2*math.pi*j/sides),z) for z in [-depth/2,depth/2] for j in range(sides)]
    f=[tuple(reversed(range(sides))),tuple(range(sides,sides*2))]
    f.extend((j,(j+1)%sides,(j+1)%sides+sides,j+sides) for j in range(sides))
    o=mesh(name,v,f,color,parent,bevel);o.location=loc
    for p in list(o.data.polygons)[2:]:p.use_smooth=True
    return o

def collision(name,verts,faces,parent=None):
    if not name.startswith('COL_'):name='COL_'+name
    o=mesh(name,verts,faces,None,parent)
    o['collision_proxy']=True;o.display_type='WIRE';o.hide_render=True
    return o
