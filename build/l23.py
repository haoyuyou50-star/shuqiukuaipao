"""L02/L03 modular cooking props for 薯球快跑; metres, +Y downstream, Z up.

Tube/trim geometry is local and textureless. Each collision or trigger mesh is
independent of the color mesh. Positive/negative Y ends of the shallow tray
stay open; its separate wedge sets the installed slope.
"""
import math
import bpy
from common import asset, cube, mesh, cylinder, marker, empty, collision

def _roundrect(w,d,r,segments=4):
    # Counterclockwise, starting on the right side of the front-right arc.
    xy=[]
    for sx,sy,a in ((1,1,0),(-1,1,90),(-1,-1,180),(1,-1,270)):
        for i in range(segments+1):
            angle=math.radians(a+90*i/segments)
            xy.append((sx*(w*.5-r)+r*math.cos(angle),sy*(d*.5-r)+r*math.sin(angle)))
    return xy

def _ring_geometry(profiles,segments=4):
    rings=[[(*point,z) for point in _roundrect(w,d,r,segments)] for w,d,r,z in profiles]
    n=len(rings[0])
    return sum(rings,[]),[tuple((i*n+j,i*n+(j+1)%n,((i+1)%len(rings))*n+(j+1)%n,((i+1)%len(rings))*n+j)) for i in range(len(rings)) for j in range(n)]

def _slab_geometry(w,d,r,t,segments=4):
    lower=[(x,y,-t*.5) for x,y in _roundrect(w,d,r,segments)]
    upper=[(x,y,+t*.5) for x,y in _roundrect(w,d,r,segments)]
    n=len(lower)
    return lower+upper,[tuple(reversed(range(n))),tuple(range(n,n*2))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]

def _wedge_geometry(w,l,zlo,zhi):
    h=w/2
    d=l/2
    v=[(-h,-d,0),(h,-d,0),(h,d,0),(-h,d,0),(-h,-d,zhi),(h,-d,zhi),(h,d,zlo),(-h,d,zlo)]
    return v,[(3,2,1,0),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)]

def _tray_side_geometry(side):
    # Variable-height soft rails, zero intrusion into ±0.101m clearance.
    ys=[-.150,-.131,-.106,.106,.131,.150]
    hs=[.022,.036,.050,.050,.036,.022]
    v=[]
    for y,z in zip(ys,hs):
        v.extend([(side*.101,y,.013),(side*.126,y,.013),(side*.126,y,z),(side*.101,y,z)])
    f=[(3,2,1,0)]
    for s in range(len(ys)-1):
        for j in range(4):
            f.append((4*s+j,4*s+(j+1)%4,4*(s+1)+(j+1)%4,4*(s+1)+j))
    f.append(tuple(range(len(v)-4,len(v))))
    # Cross-section orientation is mirrored, so outward faces need the reverse order.
    if side>0: f=[tuple(reversed(face)) for face in f]
    return v,f

def _solid_box(name, center, size, parent):
    x,y,z=center
    w,d,h=[q/2 for q in size]
    verts=[(x+sx*w,y+sy*d,z+sz*h) for sx,sy,sz in
           [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]
    return collision(name,verts,[(3,2,1,0),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)],parent=parent)

def tray():
    root=asset('A10_ShallowTray','浅餐盘 · Reusable shallow tray')
    root['ball_diameter_m']=.060
    root['install_pitch_deg']=8.0
    root['floor_z_m']=.016
    root['clear_width_m']=.202
    # Continuous floor uses square-contact geometry near its two open ends.
    # Underneath it a soft exterior lip gives the prop a recognizable silhouette.
    lip=mesh('Pan / honey underside',*_slab_geometry(.246,.310,.025,.012),
         color='honey',parent=root,bevel=.002)
    # Shift only the lip so its base remains just above the common table datum.
    lip.location.z=.007
    cube('Pan / smooth vanilla floor',(0,0,.011),(.239,.300,.010),'cream',.002,parent=root)
    for side,label in ((-1,'L'),(1,'R')):
        mesh('Pan / soft side rail '+label,*_tray_side_geometry(side),
             color='honey',parent=root,bevel=.004)
        # Clean silicone grip inset; never traverses the rolling surface.
        cube('Pan / petrol grip '+label,(side*.125,0,.025),(.006,.078,.014),
             'petrol',.002,parent=root)
        _solid_box('COL_SideWall_'+label,(side*.114,0,.031),(.026,.288,.034),root)
    _solid_box('COL_TrayFloor',(0,0,.011),(.202,.300,.010),root)
    marker('IN',(0,-.150,.016),parent=root)
    marker('OUT',(0,.150,.016),parent=root)
    marker('SURFACE_Tray',(0,0,.016),parent=root)
    marker('MOUNT_FlourInsert',(0,0,.016),parent=root)
    return root

def flour():
    root=asset('A02_FlourInsert','铺粉区 · Independent flour insert')
    root['mount_on']='A10_ShallowTray / MOUNT_FlourInsert'
    root['trigger_only']=True
    root['surface_offset_m']=.001
    # Cosmetic only: thin centered slab reads as a simple flour patch installed
    # on any A10. Rolling collision remains the unbroken A10 floor.
    m=mesh('Flour / vanilla flour surface',*_slab_geometry(.190,.134,.013,.001,5),
           color='white',parent=root,bevel=.0003)
    m.location.z=.001
    # Low-contrast sparse marks at edge so the area reads as powder without noise.
    for side in (-1,1):
        for i in range(3):
            x=side*(.071+(.003 if i==1 else 0))
            y=(i-1)*.027
            cylinder('Flour / small edge accent',(x,y,.00155),.005+.001*(i%2),.0003,
                     'pale',9,parent=root,bevel=0)
    trigger=_solid_box('TRIG_FlourZone',(0,0,.025),(.192,.134,.050),root)
    trigger['physics_role']='trigger_only'
    marker('IN',(0,-.067,0),parent=root)
    marker('OUT',(0,.067,0),parent=root)
    return root

def wedge():
    root=asset('A19_WedgeBlock','楔形垫块 · 8° tray support')
    # Shorter than the supported deck, leaving both connector lips accessible.
    length=.248
    opposite=math.tan(math.radians(8))*length/2
    middle=.034
    hi=middle+opposite
    lo=middle-opposite
    mesh('Wedge / molded petrol shell',*_wedge_geometry(.197,length,lo,hi),
         color='petrol',parent=root,bevel=.006)
    for y in (-.084,.077):
        cube('Wedge / vanilla foot grip',(0,y,.003),(.142,.020,.006),
             'cream',.002,parent=root)
    for side in (-1,1):
        for i in range(3):
            cube('Wedge / height mark',(side*.098,-.080+i*.016,.017),
                   (.005,.007,.017-i*.003),'cream',.001,parent=root)
    collision('COL_Wedge',*_wedge_geometry(.193,length,lo,hi),parent=root)
    mount=marker('MOUNT_Tray',(0,0,middle),parent=root)
    mount.rotation_euler.x=math.radians(-8)
    marker('IN',(0,-length*.5,hi),parent=root)
    marker('OUT',(0,length*.5,lo),parent=root)
    root['support_angle_deg']=-8.0
    root['mount_height_m']=middle
    return root

def _ring(name,profiles,color,root,bev=0):
    return mesh(name,*_ring_geometry(profiles),color=color,parent=root,bevel=bev)

def fryer():
    root=asset('A03_AutomaticFryer','自动炸锅 · Double-fry launch station')
    root['ball_diameter_m']=.060
    root['clear_mouth_m']=.160
    root['rim_plane_z_m']=.130
    # Feet plinth, distinct ceramic seam, colored housing, deep visible cavity.
    for x in (-.088,.088):
        for y in (-.075,.075):
            cube('Fryer / rubber foot',(x,y,.007),(.037,.034,.014),'dark',.005,parent=root)
    for label,dim,loc,mat in (
        ('vanilla plinth',(.235,.197,.021),(0,0,.023),'cream'),
        ('tomato lower housing',(.241,.202,.071),(0,0,.064),'red'),
        ('front fascia',(.182,.012,.049),(0,-.103,.059),'cream'),
    ):
        cube('Fryer / '+label,loc,dim,mat,.008,parent=root)
    # Outer lip and deep inside wall are contiguous watertight annular surfaces.
    _ring('Fryer / cavity side wall',[
        (.231,.199,.025,.088),(.238,.206,.028,.120),(.204,.180,.027,.121),
        (.174,.157,.020,.094)], 'red',root,.002)
    _ring('Fryer / soft rolled rim',[
        (.238,.208,.028,.114),(.245,.215,.028,.124),(.241,.211,.028,.130),
        (.181,.162,.019,.130),(.174,.155,.019,.125),(.174,.155,.019,.117)],
        'cream',root,.0014)
    _ring('Fryer / interior oil lining',[
        (.195,.178,.022,.092),(.176,.157,.019,.125),(.170,.151,.018,.124),
        (.162,.143,.017,.091)], 'dark',root,.0008)
    # Oil and six individually named lamps are distinct ready-to-key parts.
    oil=mesh('Fryer / independent amber oil',*_slab_geometry(.168,.150,.018,.007,5),
             color='oil',parent=root,bevel=.0015)
    oil.location.z=.104
    for x,y,r in ((-.058,.041,.006),(.057,-.038,.007),(.046,.055,.004),(-.048,-.040,.0045)):
        dot=cylinder('Fryer / oil dot',(x,y,.108),r,.0016,'honey',10,parent=root,bevel=.0004)
        dot.modifiers[0].segments=1
    for i,x in enumerate((-.068,-.041,-.014,.014,.041,.068),1):
        lamp=cube('RIM_LIGHT_%02d / insert'%i,(x,-.090,.1305),(.018,.007,.003),
             'honey',.0015,parent=root)
        lamp['lamp_index']=i
        lamp.modifiers[0].segments=1
        lamp_mat=lamp.data.materials[0].copy()
        lamp_mat.name='Fryer_Lamp_%02d'%i
        lamp.data.materials[0]=lamp_mat
    face=cylinder('Fryer / petrol thermostat',( .054,-.114,.062),.017,.013,
                  'petrol',20,parent=root,bevel=.003)
    face.rotation_euler.x=math.pi/2
    face.modifiers[0].segments=1
    cube('Fryer / dial pointer',(.054,-.121,.068),(.004,.003,.011),
              'cream',.001,parent=root)
    for i in range(3):
        cube('Fryer / vent stripe',(-.063+i*.012,-.110,.057),(.006,.004,.022),
             'red',.001,parent=root)
    # Moulded side handles visible but not collision obstacles for the ball.
    for side in (-1,1):
        cube('Fryer / side grip',(side*.129,.008,.099),(.025,.061,.017),'petrol',.005,parent=root)
    for o in root.children:
        if o.name.startswith(('Fryer / rubber foot','Fryer / vent stripe','Fryer / side grip',
                              'Fryer / interior oil lining','Fryer / cavity side wall','Fryer / dial pointer')):
            o.modifiers[0].segments=1
    _solid_box('COL_FryerBase',(0,0,.057),(.218,.189,.093),root)
    for side,label in ((-1,'L'),(1,'R')):
        _solid_box('COL_FryerRimSide_'+label,(side*.102,0,.117),(.029,.188,.026),root)
        _solid_box('COL_FryerRimEnd_'+label,(0,side*.094,.117),(.218,.027,.026),root)
    trigger=_solid_box('TRIG_PotMouth',(0,0,.118),(.165,.148,.024),root)
    trigger['physics_role']='trigger_only'
    marker('IN',(0,-.092,.130),parent=root)
    marker('OUT',(0,0,.163),parent=root)
    marker('POS_FryBallCenter',(0,0,.135),parent=root)
    marker('POS_LaunchBallCenter',(0,0,.163),parent=root)
    marker('REF_LaunchVector',(0,0,.243),parent=root)
    marker('MOUNT_ProgressUI',(0,-.121,.152),parent=root)
    marker('SURFACE_Oil',(0,0,.108),parent=root)
    return root

def stopper():
    root=asset('A23_StopperGate','活动挡片 · Independent release gate')
    root['rotation_axis']='local +X'
    root['closed_deg']=0.0
    root['open_max_deg']=88.0
    root['clear_width_m']=.122
    # Clamp-style mounts sit outside the ball route.
    for side,name in ((-1,'L'),(1,'R')):
        cube('Gate / mounting foot '+name,(side*.074,.0,.007),
             (.027,.040,.014),'cream',.003,parent=root)
        cube('Gate / support '+name,(side*.074,.0,.047),
             (.018,.022,.080),'petrol',.003,parent=root)
        shaft=cylinder('Gate / hinge cap '+name,(side*.078,0,.090),.013,.017,
                'honey',16,parent=root,bevel=.002)
        shaft.rotation_euler.y=math.pi/2
    axis=empty('PIVOT_Stopper_X',(0,0,.090),parent=root)
    cube('Gate / independent tomato flap',(0,0,-.038),
         (.118,.014,.076),'red',.004,parent=axis)
    cube('Gate / vanilla release stripe',(0,-.0075,-.050),(.084,.003,.007),
         'cream',.001,parent=axis)
    for side in (-1,1):
        shaft=cylinder('Gate / moving shoulder',(side*.056,0,0),
                       .009,.012,'red',16,parent=axis,bevel=.002)
        shaft.rotation_euler.y=math.pi/2
    cube('Gate / offset linkage lever',(.054,.017,-.012),(.016,.039,.013),
         'honey',.003,parent=axis)
    marker('ACTUATE_Lever',(.054,.034,-.012),parent=axis)
    _solid_box('COL_StopperFlap',(0,0,-.038),(.118,.013,.075),axis)
    marker('IN',(0,-.030,.014),parent=root)
    marker('OUT',(0,.030,.014),parent=root)
    return root

def build():
    """Create the five batch 2/3 roots within the active scene."""
    return [tray(),flour(),wedge(),fryer(),stopper()]
