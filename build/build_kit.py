"""Blender 4.x: blender -b --threads 8 --python-exit-code 1 --python build/build_kit.py"""
import argparse, bpy, json, math, sys
from pathlib import Path
from mathutils import Vector
BUILD=Path(__file__).resolve().parent; OUT=BUILD.parent
sys.path.insert(0,str(BUILD))
from common import D, material, PALETTE, cube
import hero, l1
argv=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
ap=argparse.ArgumentParser();ap.add_argument('--first-only',action='store_true');ap.add_argument('--skip-render',action='store_true');ap.add_argument('--hero-only',action='store_true')
args=ap.parse_args(argv)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.preferences.filepaths.save_version=0
s=bpy.context.scene;s.name='Shuqiu Kuaipao | Modular Kitchen Library';s.unit_settings.system='METRIC';s.unit_settings.scale_length=1
s['ball_diameter_m']=D
s['note']='Neutral assets and editor-only previews. For Unity import the FBX files.'
roots = hero.build()+l1.build()
if not args.first_only:
    import l23,l4
    roots += l23.build()+l4.build()
roots = sorted(roots,key=lambda o:o.name)
assert len({r.name[:3] for r in roots})==len(roots),[r.name for r in roots]
for root in roots:
    root.name=root.users_collection[0].name
bpy.context.view_layer.update()
# Runtime meshes are exported with their editable hierarchy. Blender's display controls
# and per-proxy metadata are retained in the source; Unity can key off COL_ names.
def dims(verts):
    return [round(max(v[i] for v in verts)-min(v[i] for v in verts),5) for i in range(3)]
def measure(root):
    dg=bpy.context.evaluated_depsgraph_get(); points=[];ts=0;cts=0
    for o in root.children_recursive:
        if o.type!='MESH':continue
        ev=o.evaluated_get(dg);me=ev.to_mesh()
        if me is None:continue
        me.calc_loop_triangles()
        if o.name.startswith('COL_') or o.get('collision_proxy'):
            cts+=len(me.loop_triangles)
        else:
            ts+=len(me.loop_triangles)
            points.extend(o.matrix_world@v.co for v in me.vertices)
        ev.to_mesh_clear()
    return {'id':root.name[:3],'asset':root.name,'name':root.get('display_name',root.name),
            'render_triangles':ts,'proxy_triangles':cts,'visual_bounds_m':dims(points),
            'markers':[{ 'name':o.name.split('.')[0],'parent':o.parent.name.split('.')[0],
                         'position_m':[round(x,6) for x in o.location]} for o in root.children_recursive if o.get('marker')],
            'notes':{k:root[k] for k in root.keys() if isinstance(root[k],(str,int,float)) and k not in ['display_name','ball_diameter_m','canonical_axis']}}
records=[]
for r in roots:
    records.append(measure(r))
    bpy.ops.object.select_all(action='DESELECT')
    for o in [r]+list(r.children_recursive):
        o.hide_set(False);o.hide_viewport=False
        if o.type=='MESH' and (o.get('collision_proxy') or o.name.startswith('COL_')):
            o.name='COL_'+o.name.removeprefix('COL_')
        o.select_set(True)
    bpy.context.view_layer.objects.active=r
    bpy.ops.export_scene.fbx(filepath=str(OUT/'models'/(r.name+'.fbx')),use_selection=True,
        object_types={'EMPTY','MESH'},use_mesh_modifiers=True,add_leaf_bones=False,
        axis_forward='-Z',axis_up='Y',apply_scale_options='FBX_SCALE_UNITS',
        use_custom_props=True,bake_anim=False,path_mode='AUTO')
    for o in r.children_recursive:
        if o.name.startswith('COL_'):o.hide_render=True;o.hide_set(True)

(OUT/'docs'/'manifest.json').write_text(json.dumps({'units':'metres','blender_space':'Z up; +Y downstream',
    'ball_collision_diameter_m':D,'palette_srgb_hex':PALETTE,'assets':records},ensure_ascii=False,indent=2)+'\n')
scene_assets=list(roots)
# Thumbnail scene is intentionally separate from engine delivery.
s.render.engine='CYCLES';s.cycles.samples=44;s.cycles.adaptive_threshold=.045;s.cycles.use_denoising=False;s.cycles.max_bounces=3
s.render.threads_mode='FIXED';s.render.threads=8
s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB'
s.view_settings.view_transform='AgX';s.view_settings.look='AgX - Medium High Contrast';s.view_settings.exposure=-1.28
s.world=bpy.data.worlds.new('Studio fill');s.world.use_nodes=True
s.world.node_tree.nodes['Background'].inputs[0].default_value=(.61,.70,.83,1)
s.world.node_tree.nodes['Background'].inputs[1].default_value=.33
studio=bpy.data.collections.new('Z_Studio | Preview only');s.collection.children.link(studio)
def move_studio(o):
    studio.objects.link(o)
    for c in list(o.users_collection):
        if c!=studio:c.objects.unlink(o)
def aim(o,p):o.rotation_euler=(Vector(p)-o.location).to_track_quat('-Z','Y').to_euler()
def light(name, pos,power,size,color):
    d=bpy.data.lights.new(name,'AREA');d.energy=power;d.size=size;d.color=color; ob=bpy.data.objects.new(name,d);studio.objects.link(ob)
    ob.location=pos;aim(ob,(0,0,0));return ob
lights=[light('Key',(-.8,-1.0,1.4),115,1.05,(1,.87,.73)),
        light('Fill',(1.12,-.28,.95),63,1.35,(.75,.92,1)),
        light('Top',(.11,.92,1.40),112,1.0,(1,.95,.83))]
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.001))
floor=bpy.context.object;move_studio(floor);floor.name='Warm cream backdrop';floor.data.materials.append(material('F0DDBE'))
cd=bpy.data.cameras.new('Studio camera');cam=bpy.data.objects.new('Studio camera',cd);studio.objects.link(cam);s.camera=cam
cd.type='ORTHO';cd.clip_start=.004;cd.clip_end=100
def pose(target,offset,scale):
    cam.location=Vector(target)+Vector(offset);aim(cam,target);cd.ortho_scale=scale

def render(name,w,h):
    s.render.resolution_x=w;s.render.resolution_y=h;s.render.resolution_percentage=100
    s.render.filepath=str(OUT/'previews'/name)
    bpy.ops.render.render(write_still=True)

ids={r.name[:3]:r for r in scene_assets}
def isolate(use):
    for key,r in ids.items():
        for o in r.children_recursive:
            if o.type=='MESH':o.hide_render=(key not in use) or o.name.startswith('COL_')
def place(key,pos,rot=0):
    o=ids[key];o.location=pos;o.rotation_euler.z=rot
def stage_variant(root,color):
    next(o for o in root.children if o.name.startswith('Potato_BODY')).data.materials[0]=material(color)
def snapshot_variant():
    source=ids['A01'];c=source.users_collection[0];others=[]
    for i,key in enumerate(('pale','white','honey','orange')):
        for x in source.children:
            ob=x.copy()
            if x.name.startswith('Potato_BODY'):
                ob.data=x.data.copy();ob.data.materials[0]=material(key)
            c.objects.link(ob);ob.parent=None
            ob.location=x.location+Vector((-.254+i*.17,0,.032))
            ob.hide_render=False;ob.hide_set(False);others.append(ob)
    return others
if not args.skip_render:
    # Coordinated catalog plates. Scale is deliberately normalized per asset for inspection;
    # real sizes remain in FBX and manifest.
    (OUT/'previews'/'tiles').mkdir(exist_ok=True)
    if not args.hero_only:
        for r in roots:
            k=r.name[:3];isolate({k})
            r.location=(0,0,0);r.rotation_euler=(0,0,0)
            bpy.context.view_layer.update()
            dg=bpy.context.evaluated_depsgraph_get(); bb=[]
            for o in r.children_recursive:
                if o.type=='MESH' and not o.hide_render:
                    bb.extend(o.matrix_world@Vector(v) for v in o.evaluated_get(dg).bound_box)
            lo=Vector([min(v[j] for v in bb) for j in range(3)]); hi=Vector([max(v[j] for v in bb) for j in range(3)])
            r.location.z=-lo.z+.001
            target=(lo+hi)/2; target.z+=r.location.z
            offset=Vector((.47,-.72,.66));basis=(-offset).to_track_quat('-Z','Y')
            axes=[basis@Vector((1,0,0)),basis@Vector((0,1,0))]
            spans=[max(v.dot(a) for v in bb)-min(v.dot(a) for v in bb) for a in axes]
            pose(target,offset,max(.099,spans[0]*1.32,spans[1]*1.74))
            render('tiles/'+k+'.png',615,490)
            r.location.z=0
        isolate(set()); source=ids['A01']; source.location=(0,0,0)
        variants=snapshot_variant()
        pose((0,0,.033),(.015,-.55,.25),.67)
        render('ball-states.png',1640,515)
        for o in variants:bpy.data.objects.remove(o,do_unlink=True)
    isolate({'A01','A04','A05','A07','A08','A09'})
    # Presentation scene only. Exact validation arrangement is in the QA scripts.
    place('A07',(-.415,.143,0),math.radians(-14));place('A08',(-.236,-.292,0))
    burger_hinge=next(o for o in ids['A07'].children if o.name.startswith('Burger hinge') and o.type=='EMPTY')
    burger_hinge.rotation_euler.x=math.radians(-21)
    place('A09',(.159,.033,.071));place('A04',(.159,.294,0))
    place('A01',(-.232,-.171,.079),math.radians(10));place('A05',(-.236,.008,.111),math.radians(8))
    place_ring=ids['A05'];c=place_ring.users_collection[0];copies=[]
    staging=cube('Photo only / carton stacking block',(.159,.066,.034),(.194,.147,.068),'honey',.008,place_ring)
    staging.parent=None;staging.location=(.159,.066,.034);copies.append(staging)
    bpy.context.view_layer.update()
    for x in list(place_ring.children):
        if x.type!='MESH':continue
        ob=x.copy();ob.data=x.data.copy();c.objects.link(ob)
        ob.location=x.location;ob.parent=None
        ob.matrix_world=x.matrix_world.copy();ob.location.x+=.395;ob.location.y-=.215;ob.location.z+=.091
        if x.name.startswith('Ring_Rim'):ob.data.materials[0]=material('orange')
        copies.append(ob)
    pose((-.064,-.022,.081),(.56,-.91,1.28),1.10)
    render('level01-review.png' if args.hero_only else 'level01.png',1620,1070)
    for o in copies:bpy.data.objects.remove(o,do_unlink=True)
    burger_hinge.rotation_euler.x=math.radians(-102)
    if args.hero_only:sys.exit(0)

# Editable layout and room-sized metrology; no reference image or private Feishu material.
for i,r in enumerate(scene_assets):
    r.location=((i%5-2)*.52,((len(scene_assets)-1)//5-i//5)*.58,0);r.rotation_euler=(0,0,0)
    for o in r.children_recursive:
        if o.type=='MESH':o.hide_render=o.name.startswith('COL_')
    if r.name.startswith('A01'):r.location.z=.031
    if r.name.startswith('A05'):r.location.z=.088
    if r.name.startswith('A06'):r.location.z=.050
pose((0,max(0,((len(scene_assets)-1)//5)*.29),0),(.08,-3.4,4),3.42)
s.render.resolution_x=1500;s.render.resolution_y=1100;s.render.filepath='//studio.png'
bpy.ops.object.select_all(action='DESELECT')
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            sp=area.spaces.active;sp.clip_start=.004;sp.shading.color_type='MATERIAL';sp.shading.show_cavity=True
            sp.region_3d.view_distance=3.6;sp.region_3d.view_location=(0,.95,0)
            sp.region_3d.view_rotation=cam.rotation_euler.to_quaternion()
            sp.overlay.show_extras=False;sp.overlay.show_floor=False
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'source'/'Shuqiu_ModularKitchen.blend'),compress=True)
print('ASSETS',len(roots))
