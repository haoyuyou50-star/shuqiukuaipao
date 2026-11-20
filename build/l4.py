"""Kitchen Jr., batch 4: mechanical and modular rolling hardware.
Lengths are metres; Z-up, +Y downstream. Geometry is built without add-ons.
"""
from math import sin, cos, pi, radians
import bmesh
from common import asset, collision, cube, cylinder, empty, marker, mesh


def solid(g,n,verts,faces,material,bevel=.002):
    o=(mesh(n,verts,faces,color=material,parent=g,bevel=bevel) if material
       else collision(n,verts,faces,parent=g))
    bm=bmesh.new()
    bm.from_mesh(o.data)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    bm.to_mesh(o.data); bm.free()
    return o


def prism(g, n, outline, thickness, material, bevel=.002):
    """Closed prism, top perimeter may have varying elevation."""
    k = len(outline)
    verts = [(x,y,z) for x,y,z in outline]+[(x,y,z-thickness) for x,y,z in outline]
    faces = [tuple(range(k)), tuple(range(2*k-1,k-1,-1))]
    faces += [(i,k+i,k+(i+1)%k,(i+1)%k) for i in range(k)]
    return solid(g,n,verts,faces,material,bevel)


def arcwall(g, n, rx, ry, a0, a1, z, height, thick, material, bevel=.002, steps=18):
    verts=[]; faces=[]
    for i in range(steps+1):
        a=radians(a0+(a1-a0)*i/steps)
        for t,q in ((0,0),(thick,0),(thick,height),(0,height)):
            verts.append(((rx+t)*cos(a),(ry+t)*sin(a),z+q))
    faces.append((3,2,1,0))
    for i in range(steps):
        for k in range(4):
            faces.append((4*i+k,4*i+(k+1)%4,4*(i+1)+(k+1)%4,4*(i+1)+k))
    faces.append(tuple(4*steps+j for j in range(4)))
    o=solid(g,n,verts,faces,material,bevel)
    if material and bevel:
        o.modifiers[0].segments=1
    return o


def ringsector(g,n,r_inner,r_outer,a0,a1,z,thick,mat,fall=.0,steps=14):
    verts=[]; faces=[]
    for i in range(steps+1):
        a=radians(a0+(a1-a0)*i/steps)
        h=z-fall*i/steps
        for r,v in ((r_inner,h),(r_outer,h),(r_outer,h-thick),(r_inner,h-thick)):
            verts.append((r*cos(a),r*sin(a),v))
    for i in range(steps):
        for k in range(4):
            faces.append((4*i+k,4*i+(k+1)%4,4*(i+1)+(k+1)%4,4*(i+1)+k))
    faces += [(3,2,1,0),tuple(4*steps+j for j in range(4))]
    return solid(g,n,verts,faces,mat,.0015)


def rect(w,y0,y1,z0,z1,x=0):
    return [(x-w/2,y0,z0),(x+w/2,y0,z0),(x+w/2,y1,z1),(x-w/2,y1,z1)]


def drum(g,n,p,r,d,mat,direction='X'):
    o=cylinder(n,p,r,d,color=mat,sides=16,parent=g,bevel=.0016)
    if direction=='X': o.rotation_euler[1]=pi/2
    elif direction=='Y': o.rotation_euler[0]=pi/2
    return o


def build_core():
    roots=[]
    def a(code,label):
        o=asset(code,label); roots.append(o); return o

    s=a('A11_Spatula','Long-handle spatula')
    # Attach this root at 0.082 m relative to A20 table origin. Control a hinge
    # around local X. The pivot is the root, shared by mesh and collision.
    s['hinge_axis']='X'; s['home_angle_deg']=5.0; s['limit_angle_deg']=-9.0
    drum(s,'Fulcrum sleeve',(0,0,.0),.015,.107,'honey')
    handle=[(-.047,-.187,.025),(-.034,-.206,.025),(.034,-.206,.025),(.047,-.187,.025),
            (.053,-.120,.025),(.049,-.072,.025),(.046,0,.025),(-.046,0,.025),(-.049,-.072,.025),(-.053,-.120,.025)]
    paddle=[(-.046,-.002,.026),(.046,-.002,.026),(.058,.031,.025),(.064,.100,.024),
            (.060,.135,.023),(.049,.151,.023),(-.049,.151,.023),(-.060,.135,.023),(-.064,.100,.024),(-.058,.031,.025)]
    prism(s,'Tomato moulded grip',handle,.021,'red',.004)
    prism(s,'Vanilla paddle',paddle,.015,'cream',.004)
    for x in [-.052,.052]:
        prism(s,'Paddle guard '+str(x),[(x-.006,.029,.047),(x+.006,.029,.047),(x+.010,.123,.047),(x-.002,.123,.047)],.025,'cream',.003)
    for x in [-.042,.042]:
        prism(s,'Grip guard '+str(x),rect(.008,-.182,-.027,.042,.044,x),.023,'red')
    for y in (-.163,-.147,-.131):
        cube('Grip underside rib',(0,y,.007),(.063,.005,.006),'rust',.002,s)
    # Single continuous sloped collider with no seam between paddle and grip.
    prism(s,'Deck_COLLIDER',rect(.093,-.206,.151,.025,.023),.016,None,0)
    for x in (-.0485,.0485):
        prism(s,'Rail_COLLIDER',rect(.007,-.178,.125,.048,.048,x),.024,None,0)
    marker('IN',(0,-.206,.025),s)
    marker('OUT',(0,.151,.023),s)
    marker('WEIGHT',(0,-.102,.004),s)
    marker('ACTUATOR',(0,-.194,.007),s)
    marker('LIMIT_CONTACT',(0,.090,.009),s)

    x=a('A20_AxleSupport','Reusable axle and stand')
    cube('Diner stand foot',(0,0,.012),(.186,.104,.024),'petrol',.006,x)
    cube('Cream foot inset',(0,.003,.023),(.167,.080,.009),'cream',.003,x)
    for side in (-1,1):
        x0=side*.067
        profile=[(-.044,.026),(.044,.026),(.028,.055),(.018,.082),(-.014,.090),(-.029,.065)]
        v=[(u,y,z) for u in (x0-.016,x0+.016) for y,z in profile]
        faces=[(5,4,3,2,1,0),(6,7,8,9,10,11)]+[(j,(j+1)%6,(j+1)%6+6,j+6) for j in range(6)]
        solid(x,'Triangular stand '+str(side),v,faces,'petrol',.005)
        drum(x,'Enamel bearing '+str(side),(x0,0,.082),.027,.031,'petrol')
        drum(x,'Washer '+str(side),(side*.088,0,.082),.019,.008,'cream')
    drum(x,'Steel pin',(0,0,.082),.008,.194,'pale')
    for d in [-1,1]:
        drum(x,'Honey axle cap '+str(d),(d*.099,0,.082),.013,.008,'honey')
    marker('PIVOT',(0,0,.082),x)
    marker('AXLE_LEFT',(-.088,0,.082),x)
    marker('AXLE_RIGHT',(.088,0,.082),x)

    l=a('A21_StopBlock','Mechanical limit stop')
    cube('Cream stop base',(0,0,.010),(.097,.056,.020),'cream',.005,l)
    cube('Tomato stop block',(0,0,.044),(.070,.041,.053),'red',.004,l)
    cube('Dark stop buffer',(0,0,.071),(.058,.034,.012),'dark',.004,l)
    prism(l,'Buffer_COLLIDER',rect(.058,-.017,.017,.077,.077),.013,None,0)
    marker('CONTACT',(0,0,.077),l)

    w=a('A22_Counterweight','Counterweight')
    cube('Petrol body',(0,0,-.016),(.070,.044,.034),'petrol',.006,w)
    cube('Cream mounting pad',(0,0,.002),(.054,.033,.008),'cream',.002,w)
    for a_ in (-.023,.023):
        drum(w,'Honey weight cap '+str(a_),(a_,0,-.017),.012,.011,'honey')
    marker('MOUNT',(0,0,.006),w)
    w['physics']='Mass and damping are assigned by the engine; positive Y supports spatula blade; attach counterweight behind fulcrum.'

    g=a('A18_TrackGuards','Straight and curved track guards')
    c=empty('CURVED', (0,0,0),parent=g)
    # Curved and straight variants are laid out separately in the editable source.
    arcwall(c,'Cream curved guard',.100,.150,-62,62,.016,.045,.013,'cream')
    arcwall(c,'Tomato curved safety edge',.100,.150,-62,62,.061,.006,.013,'red',.0015)
    arcwall(c,'GuardArc_COLLIDER',.100,.150,-62,62,.016,.052,.013,None,0,16)
    for i,a_ in enumerate((-53,-28,4,28,53)):
        a_=radians(a_)
        drum(c,'Mount stud '+str(i),(.110*cos(a_),.158*sin(a_),.026),.008,.019,'honey','Z')
    marker('A10_TRAY_ORIGIN',(0,0,0),c)
    marker('OUT',(0,.150,.016),c)
    v=empty('STRAIGHT',(.26,0,0),parent=g)
    cube('Cream straight guard',(0,0,.038),(.013,.230,.045),'cream',.002,v)
    cube('Tomato straight safety edge',(0,0,.063),(.013,.230,.006),'red',.0015,v)
    for y in (-.093,0,.093):
        drum(v,'Mount stud '+str(y),(0,y,.025),.008,.019,'honey','Z')
    prism(v,'GuardStraight_COLLIDER',rect(.013,-.115,.115,.066,.066),.051,None,0)
    marker('MOUNT',(0,0,.016),v)
    return roots


def build_expansions():
    roots=[]
    def a(code,label):
        o=asset(code,label); roots.append(o); return o

    a15=a('A15_StraightChannel','Straight chute')
    prism(a15,'Vanilla straight deck',rect(.118,-.105,.105,.028,.022),.015,'cream')
    prism(a15,'Straight_COLLIDER',rect(.106,-.105,.105,.028,.022),.012,None,0)
    for x in (-.055,.055):
        prism(a15,'Red upright rail',rect(.010,-.105,.105,.049,.043,x),.026,'red',.002)
        prism(a15,'Side_COLLIDER',rect(.008,-.105,.105,.05,.044,x),.028,None,0)
    marker('IN',(0,-.105,.028),a15)
    marker('OUT',(0,.105,.022),a15)

    a16=a('A16_ArcChannel','Falling arc channel')
    ringsector(a16,'Vanilla arc bed',.062,.175,-90,0,.056,.014,'cream',fall=.025)
    ringsector(a16,'Inner red skirting',.058,.066,-90,0,.081,.031,'red',fall=.025)
    ringsector(a16,'Outer red skirting',.171,.180,-90,0,.081,.031,'red',fall=.025)
    ringsector(a16,'Bed_COLLIDER',.063,.175,-90,0,.056,.014,None,fall=.025)
    ringsector(a16,'Inner_COLLIDER',.057,.066,-90,0,.079,.030,None,fall=.025)
    ringsector(a16,'Outer_COLLIDER',.171,.180,-90,0,.079,.030,None,fall=.025)
    marker('IN',(0,-.1185,.056),a16)
    marker('OUT',(.1185,0,.031),a16)
    a16['in_tangent']='+X'
    a16['out_tangent']='+Y'

    a17=a('A17_TransitionSlope','Transition ramp')
    prism(a17,'Vanilla wedge deck',rect(.114,-.081,.081,.056,.016),.012,'cream')
    prism(a17,'Ramp_COLLIDER',rect(.101,-.081,.081,.056,.016),.011,None,0)
    for x in (-.053,.053):
        prism(a17,'Red side lips',rect(.012,-.081,.081,.072,.032,x),.018,'red')
        prism(a17,'Rail_COLLIDER',rect(.010,-.081,.081,.072,.032,x),.017,None,0)
    for y,z in ((-.048,.021),(.037,.011)):
        cube('Petrol stand edge',(0,y,z),(.084,.012,.018),'petrol',.004,a17)
    marker('IN',(0,-.081,.056),a17)
    marker('OUT',(0,.081,.016),a17)

    t=a('A12_Tongs','Tongs diverter')
    left=empty('LEFT_PIVOT',(-.086,-.107,.028),parent=t)
    right=empty('RIGHT_PIVOT',(.086,-.107,.028),parent=t)
    for q,side in ((left,1),(right,-1)):
        ys=[(-.008,.016),(-.013,.037),(-.006,.092),(.006,.139),(.009,.168),
            (.019,.181),(.036,.181),(.046,.166),(.035,.141),(.025,.088),(.014,.037),(.011,.016)]
        prism(q,'Vanilla clamp arm',[(side*x,y,.020) for x,y in ys],.017,'cream',.003)
        cuff=[(.008,.137),(.006,.158),(.009,.176),(.02,.186),(.039,.182),(.048,.168),(.040,.140)]
        prism(q,'Tomato silicone tip',[(side*x,y,.025) for x,y in cuff],.020,'red',.003)
        prism(q,'TongsArm_COLLIDER',[(side*x,y,.023) for x,y in ys],.019,None,0)
        drum(t,'Honey hinge cap',(-side*.086,-.107,.029),.016,.028,'honey','Z')
    cube('Petrol hinge stand',(0,-.107,.015),(.205,.065,.030),'petrol',.005,t)
    marker('IN',(0,-.135,.019),t)
    t['neutral_collision_clearance_m']=.080
    t['assembly_note']='A15 bridge below arms provides floor; use one arm at a time for diverter, avoid pinch at opposed tip.'
    marker('OUT_LEFT',(-.05,.073,.040),t)
    marker('OUT_RIGHT',(.05,.073,.040),t)

    c=a('A13_TippingCup','Pouring measure')
    cup=empty('CUP_X_PIVOT',(0,-.016,.078),parent=c)
    segments=28
    # Mouth remains open; rim radius is locally extended into a downstream spout.
    v=[]; fs=[]
    for radius,z,spout in ((.058,-.055,0),(.076,.056,1),(.068,.056,1),(.051,-.046,0)):
        for j in range(segments):
            ang=j*2*pi/segments
            f=max(0, sin(ang))**22
            v.append((radius*cos(ang),(radius+.033*f*spout)*sin(ang)+.016,z-.011*f*spout))
    for k in range(3):
        for i in range(segments):
            j=(i+1)%segments
            fs.append((segments*k+i,segments*k+j,segments*(k+1)+j,segments*(k+1)+i))
    fs.extend([tuple(reversed(range(segments))),tuple(range(3*segments,4*segments))])
    solid(cup,'Open vanilla cup',v,fs,'cream',.003)
    # Compound convex wall pieces preserve the cup mouth when using a moving body.
    # The independently moving vessel should not use a single convex mesh hull.
    cylinder('CupFloorGuide',(0,.016,-.051),.054,.008,color='pale',sides=16,parent=cup,bevel=.001)
    floor=[(.050*cos(2*pi*i/16),.016+.050*sin(2*pi*i/16),-.045) for i in range(16)]
    prism(cup,'CupFloor_COLLIDER',floor,.008,None,0)
    qfaces=[(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)]
    for i in range(0,segments,2):
        j=(i+2)%segments
        # Approximate the taper with a narrow wall plate every ~26 degrees.
        upper=[v[segments+i],v[segments+j],v[2*segments+j],v[2*segments+i]]
        lower=[v[i],v[j],v[3*segments+j],v[3*segments+i]]
        solid(cup,'CupWall_COLLIDER',upper+lower,qfaces,None,0)
    for j,y in enumerate((-.036,-.017,.005,.029)):
        cube('Tomato measure marker '+str(j),(-.025,-.048,y),(.026+.010*(j%2),.005,.004),'red',.0012,cup)
    for side in (-1,1):
        cube('Petrol ear '+str(side),(side*.084,-.016,.041),(.019,.053,.080),'petrol',.006,c)
        drum(c,'Axle cap '+str(side),(side*.097,-.016,.078),.015,.012,'honey')
    cube('Cream foot',(0,-.014,.011),(.218,.146,.023),'cream',.006,c)
    marker('IN',(0,.016,.056),cup)
    marker('OUT',(0,.123,.045),cup)
    marker('COUNTERWEIGHT',(0,-.030,-.045),cup)

    rp=a('A14_RollingPin','Rolling pin pair')
    for side in (-1,1):
        axis=empty('ROLLER_'+('L' if side<0 else 'R'),(side*.036,0,.035),parent=rp)
        drum(axis,'Honey roller',(0,0,0),.020,.178,'honey','Y')
        drum(axis,'Roller collar front',(0,-.086,0),.021,.013,'cream','Y')
        drum(axis,'Roller collar back',(0,.086,0),.021,.013,'cream','Y')
        drum(axis,'Spindle',(0,0,0),.007,.220,'pale','Y')
        # Closed roller collision capsule analogue. Keep mesh separate for physics binding.
        nn=12
        vv=[(.019*cos(2*pi*j/nn),y,.019*sin(2*pi*j/nn)) for y in (-.088,.088) for j in range(nn)]
        ff=[tuple(range(nn)),tuple(reversed(range(nn,2*nn)))]
        ff.extend((i,nn+i,nn+(i+1)%nn,(i+1)%nn) for i in range(nn))
        solid(axis,'Roller_COLLIDER',vv,ff,None,0)
    for y in (-.105,.105):
        cube('Petrol axle cradle',(0,y,.014),(.144,.017,.034),'petrol',.004,rp)
    marker('IN',(0,-.113,.049),rp)
    marker('OUT',(0,.113,.049),rp)
    rp['collision_note']='Gap .032 m between rollers is smaller than reference ball; tune damping and end rails with actual level.'

    star=a('A24_StarCrumb','Collectible star crumb')
    profile=[]
    for j in range(10):
        a_=pi/2+2*pi*j/10; r=.023 if j%2==0 else .0115
        profile.append((r*cos(a_),r*sin(a_),.008))
    prism(star,'Honey crisp star',profile,.016,'honey',.0025)
    profile2=[(.74*x,.74*y,z+.001) for x,y,z in profile]
    prism(star,'Vanilla raised star stamp',profile2,.0035,'cream',.001)
    marker('TRIGGER_CENTER',(0,0,0),star)
    star['trigger_radius_m']=.027
    return roots


def build():
    return build_core()+build_expansions()
