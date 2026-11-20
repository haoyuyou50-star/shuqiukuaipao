"""Level 1: burger delivery, hinged takeout, fry chute, ketchup,."""
from math import radians, sin, cos
import bpy
from common import asset, cube, marker, empty, collision, material


def _mesh(name, coords, faces, mat, parent, bevel=0):
    me = bpy.data.meshes.new(name)
    me.from_pydata(coords, [], faces)
    me.update()
    ob = bpy.data.objects.new(name, me)
    (parent.users_collection[0] if parent.users_collection else bpy.context.collection).objects.link(ob)
    ob.parent = parent
    if mat:
        me.materials.append(mat)
    if bevel:
        mod = ob.modifiers.new('Rounded toy edges', 'BEVEL')
        mod.width, mod.segments = bevel, 3
        wn = ob.modifiers.new('Broad flat faces', 'WEIGHTED_NORMAL')
        wn.keep_sharp = True
    return ob


def _prism(name, poly, depth, mat, parent, bevel=.002):
    n = len(poly)
    coords = list(poly) + [(x, y, z-depth) for x, y, z in poly]
    faces = [tuple(range(n)), tuple(range(2*n-1, n-1, -1))]
    faces += [(i, i+n, ((i+1)%n)+n, (i+1)%n) for i in range(n)]
    return _mesh(name, coords, faces, mat, parent, bevel)


def _rect(name, x, y, z, w, d, h, mat, parent, bevel=.002):
    return _prism(name, [(x-w/2,y-d/2,z+h/2),(x+w/2,y-d/2,z+h/2),
                         (x+w/2,y+d/2,z+h/2),(x-w/2,y+d/2,z+h/2)], h, mat, parent, bevel)


def _wedge(name, sections, mat, parent, bevel=0):
    """sections = (x_left, x_right, y, surface_z), all in the parent's local frame."""
    return _prism(name, [(r,y,z) for l,r,y,z in sections] +
                  [(l,y,z) for l,r,y,z in reversed(sections)], .007, mat, parent, bevel)


def _rim(name, side, sections, thick, height, mat, parent, bevel=.0014):
    """One straight sloping wall segment; adjacent faces meet along exact stations."""
    # positive X wall: outer is farther right; negative X wall: farther left
    s0,s1 = sections
    x0=s0[1] if side>0 else s0[0]
    x1=s1[1] if side>0 else s1[0]
    _,_,y0,z0=s0
    _,_,y1,z1=s1
    p=[(x0,y0,z0),(x0+side*thick,y0,z0),(x1+side*thick,y1,z1),(x1,y1,z1)]
    if side<0:
        p=list(reversed(p))
    p=[(x,y,z+height) for x,y,z in p]
    return _prism(name,p,height+.004,mat,parent,bevel)


def _ring(name, levels, mat, parent, bevel=.0015):
    """Octagonal radial mesh, each level is radius plus height."""
    pts=[(r*cos(radians(11.25+i*22.5)),r*sin(radians(11.25+i*22.5)),z)
         for r,z in levels for i in range(16)]
    faces=[(j*16+i,j*16+(i+1)%16,(j+1)*16+(i+1)%16,(j+1)*16+i)
           for j in range(len(levels)-1) for i in range(16)]
    if levels[-1][0]:
        faces.append(tuple(range((len(levels)-1)*16,len(levels)*16)))
    if levels[0][0]:
        faces.append(tuple(range(15,-1,-1)))
    return _mesh(name,pts,faces,mat,parent,bevel)


def _tray(root, label, width, depth, floor_z, wall_h, color, bottom_thickness=.013, rear_open=False):
    """Molded shell with thick lip built as one continuous editable mesh."""
    def contour(w,d,z,corner):
        x,y=w/2,d/2
        return [(-x+corner,-y,z),(x-corner,-y,z),(x,-y+corner,z),
                (x,y-corner,z),(x-corner,y,z),(-x+corner,y,z),
                (-x,y-corner,z),(-x,-y+corner,z)]
    lip_z=floor_z+wall_h
    layers=[contour(width-.024,depth-.024,floor_z-bottom_thickness,.013),
            contour(width,depth,lip_z,.015),
            contour(width-.014,depth-.014,lip_z,.012),
            contour(width-.035,depth-.035,floor_z,.012)]
    verts=sum(layers,[])
    faces=[tuple(range(7,-1,-1)),tuple(range(24,32))]
    for j in range(3):
        for i in range(8):
            k=(i+1)%8
            if rear_open and i==4:
                continue
            faces.append((j*8+i,j*8+k,(j+1)*8+k,(j+1)*8+i))
    if rear_open:
        for i in (4,5):
            faces.append(tuple([i,i+8,i+16,i+24][::(1 if i==4 else -1)]))
    return _mesh(label,verts,faces,material(color),root,.0028)


def _track_surface_collision(parent,name,sections):
    a,b=sections
    # Flat surface + outward walls, multiple pieces rather than concave convex hull.
    left,right,y,z=a
    xl,xr,yy,zz=b
    collision(name+'_Floor',[(left,y,z),(right,y,z),(xr,yy,zz),(xl,yy,zz),
                              (left,y,z-.008),(right,y,z-.008),(xr,yy,zz-.008),(xl,yy,zz-.008)],
              [(0,1,2,3),(7,6,5,4),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],parent=parent)
    for side in (-1,1):
        x0=left if side<0 else right
        x1=xl if side<0 else xr
        verts=[(x0,y,z-.006),(x0+side*.008,y,z-.006),(x1+side*.008,yy,zz-.006),(x1,yy,zz-.006)]
        verts += [(x,y,z+.05) for x,y,z in verts[:]]
        faces=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
        if side<0:
            faces=[tuple(reversed(f)) for f in faces]
        collision(name+('_WallL' if side<0 else '_WallR'),verts,faces,parent=parent)


def _burger():
    root=asset('A07_HamburgerBox','Hamburger box')
    _tray(root,'Burger • molded cream base',.194,.168,.019,.026,'cream')
    lid=empty('Burger hinge • X', (0,.075,.047),parent=root)
    # Shell lid in the local closed plane, opened around its rear-running hinge.
    lid_shell=empty('Burger lid frame', (0,-.075,.0),parent=lid)
    _tray(lid_shell,'Burger • honey lid',.194,.168,.027,.006,'honey',.026)
    # The lid pivots while the single molded base stays fixed.
    lid.rotation_euler.x=radians(-102)
    for x in (-.056,.056):
        cube('Burger hinge knuckle',(x,.078,.045),(.034,.015,.013),'rust',.003,parent=root)
    cube('Burger front lock tab',(0,-.087,.027),(.050,.017,.014),'honey',.003,parent=root)
    for x,z,w in [(-.021,.024,.013),(0,.024,.013),(.021,.024,.013)]:
        cube('Burger red front tick',(x,-.096,z),(w,.002,.006),'red',.0006,parent=root)
    return root


def _takeout():
    root=asset('A08_TakeoutBoxRamp','Takeout box / lid ramp')
    _tray(root,'Takeout • scarlet base',.177,.205,.02,.031,'red',.017)
    _tray(root,'Takeout • paper lining',.161,.193,.024,.021,'cream',.004)
    hinge=empty('Takeout lid hinge • X',(0,.102,.054),parent=root)
    sections=[(-.068,.068,0,0),(-.049,.049,.156,-.045)]
    _wedge('Takeout • cream rolling lid',sections,material('cream'),hinge,.0024)
    for side in (-1,1):
        _rim('Takeout • red lid rail',side,sections,.010,.027,material('red'),hinge)
    _track_surface_collision(hinge,'Takeout_Lid',sections)
    cube('Takeout • pivot barrel', (0,.101,.050),(.151,.015,.016),'honey',.003,parent=root)
    for i in range(-3,4):
        cube('Takeout • paper pattern',(i*.020,-.102,.035),(.011,.002,.010),'cream',.0008,parent=root)
    marker('IN',(0,0,0),parent=hinge)
    marker('OUT',(0,.156,-.045),parent=hinge)
    hinge['axis']='local X'
    return root


_FRIES_SECTIONS=(
    (-.114,.114,-.160,.088),
    (-.114,.114,-.092,.072),
    (-.087,.087,.018,.048),
    (-.050,.050,.125,.024),
    (-.050,.050,.176,.013),
)


def _fries():
    root=asset('A09_FryCartonCatch','Fry carton / funnel track')
    ss=_FRIES_SECTIONS
    for i,(a,b) in enumerate(zip(ss,ss[1:])):
        _wedge('Fries • connected cream floor %02d'%i,[a,b],material('cream'),root,0)
        for side in (-1,1):
            _rim('Fries • pale red retaining wall',side,[a,b],.010,.050,material('red'),root,0)
        _track_surface_collision(root,'Fries_%02d'%i,[a,b])
    for side in (-1,1):
        # Outer carton sheathing has the iconic tall curved lip without occluding the channel.
        stations=[(a[1]+.010,a[2],a[3],h) for a,h in zip(ss,[.058,.067,.067,.052,.044])]
        points=[]
        for x,y,z,h in stations:
            points.extend([(side*x,y,z-.010),(side*x,y,z+h)])
        faces=[(2*i,2*i+2,2*i+3,2*i+1) for i in range(len(stations)-1)]
        if side>0:
            faces=[tuple(reversed(f)) for f in faces]
        o=_mesh('Fries • external curved paper carton',points,faces,material('red'),root)
        mod=o.modifiers.new('Rolled card thickness','SOLIDIFY')
        mod.thickness=.007
        mod.offset=0
        for i in range(4):
            cube('Fries • warm paper seam', (side*.125,-.151+i*.013,.102),
                 (.0025,.007,.009),'honey',.0006,parent=root)
    for x in (-.077,.077):
        # Taper the concealed foot to the underside of the descending floor.
        y0,y1=-.139,-.016
        z0,z1=.075,.049
        a,b=x-.014,x+.014
        v=[(a,y0,.002),(b,y0,.002),(b,y1,.002),(a,y1,.002),
           (a,y0,z0),(b,y0,z0),(b,y1,z1),(a,y1,z1)]
        _mesh('Fries • wedged support foot',v,
              [(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],
              material('rust'),root,.002)
    marker('IN',(0,ss[0][2],ss[0][3]),parent=root)
    marker('OUT',(0,ss[-1][2],ss[-1][3]),parent=root)
    for offset in (0,.060,-.060):
        for left,right,y,z in ss:
            # 60 mm sphere, limited to 18 mm side drift by the outlet.
            drift=offset*(right-.032)/(ss[0][1]-.032)
            assert drift-.031 > left and drift+.031 < right
    root['nominal_ball_diameter_m']=.060
    root['through_path_center_and_start_offsets_m']='0, -0.060, +0.060 (analytic bounds)'
    root['outlet_clear_width_m']=.100
    return root


def _dish():
    root=asset('A04_KetchupDish','Ketchup dish / removable sauce')
    _ring('Ketchup • vanilla ceramic dish',
          [(.062,.002),(.067,.007),(.078,.026),(.084,.035),(.081,.040),(.074,.039),(.066,.027),(.059,.015)],
          material('cream'),root,.0025)
    _ring('Ketchup • independent sauce insert',
          [(.057,.016),(.060,.018),(.060,.022),(.056,.026),(.046,.028)],
          material('sauce'),root,.0016)
    _ring('Ketchup • shallow embossed spiral core',
          [(.027,.028),(.028,.030),(.023,.031),(.017,.031),(.012,.030)],
          material('sauce'),root,.001)
    return root



def build():
    return [_burger(),_takeout(),_fries(),_dish()]
