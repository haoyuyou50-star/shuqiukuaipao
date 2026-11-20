"""Replay the exported first-level Bullet samples in Blender at 1/5 speed.
Builds a separate authoring scene, not a Unity level and not a live teleport demo.
"""
import bpy, sys, json
from pathlib import Path
from mathutils import Vector,Quaternion
from math import pi
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P/'build'))
from common import cube, material
import l1,hero
cases=json.loads((P/'qa'/'level1_blender_result.json').read_text())['cases']
assert [c['name'] for c in cases]==['starter_ramp','center','side_left','side_right']
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.preferences.filepaths.save_version=0
s=bpy.context.scene;s.name='L01 | Physics sample replay (1:5 speed)';s.unit_settings.system='METRIC';s.unit_settings.scale_length=1
s['method']='One template per entrance trial; motion sampled from Blender Bullet. 24fps plays 120Hz recorded samples at 1/5 speed. No portal or Unity runtime.'
s.render.fps=24;s.frame_end=185
s.world=bpy.data.worlds.new('Fixture ambient')
s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs[0].default_value=(.50,.59,.68,1)
s.world.node_tree.nodes['Background'].inputs[1].default_value=.25
s.view_settings.view_transform='AgX';s.view_settings.exposure=-.42
s.render.engine='CYCLES';s.cycles.samples=24;s.cycles.use_denoising=False
def prune(root):
    for o in list(root.children_recursive):
        if o.name.startswith('COL_'):bpy.data.objects.remove(o,do_unlink=True)
def remove(root):
    co=root.users_collection[0]
    for o in reversed(list(root.children_recursive)):bpy.data.objects.remove(o,do_unlink=True)
    bpy.data.objects.remove(root,do_unlink=True)
    bpy.data.collections.remove(co)
def text(name,p,body):
    d=bpy.data.curves.new(name,'FONT');d.body=body;d.size=.017;d.extrude=0
    o=bpy.data.objects.new(name,d);s.collection.objects.link(o);o.location=p
    d.materials.append(material('petrol'))
zones=[(-.57,-.11),(-.19,0),(.19,0),(.57,0)]
colors=['honey','honey','orange','pale']
title=['00 LID RAMP','01 CENTER','02 LEFT -80 mm','03 RIGHT +80 mm']
for i,((x,y),c,color,lab) in enumerate(zip(zones,cases,colors,title)):
    assets=l1.build();ball,ring,bounce=hero.build(); remove(ring);remove(bounce)
    for prop in assets:
        tag=prop.name[:3]
        if (not i and tag=='A08') or (i and tag in {'A09','A04'}):
            lift=.071 if tag=='A09' else 0
            oy=y+.261 if tag=='A04' else y
            prop.location=(x,oy,lift);prune(prop)
            if tag=='A09':
                co=cube('Test plinth',(0,-.044,-.0355),(.224,.122,.071),'pale',.004,prop)
                co['fixture_only']=True
        else:remove(prop)
    next(o for o in ball.children if o.name.startswith('Potato_BODY')).data.materials[0]=material(color)
    text(lab,(x-.086,-.250,.001),lab)
    prev=None;q=Quaternion()
    for f,(t,dx,dy,z) in enumerate(c['ball_center_trace_t_xyz'],1):
        v=Vector((dx,dy,z))
        if prev is not None:
            delta=v-prev;horizontal=Vector((delta.x,delta.y,0))
            if horizontal.length>1e-6:q=Quaternion(Vector((0,0,1)).cross(horizontal).normalized(),horizontal.length/.03)@q
        prev=v;ball.location=v+Vector((x,y,0))
        ball.rotation_mode='QUATERNION';ball.rotation_quaternion=q
        ball.keyframe_insert(data_path='location',frame=f,group='Measured path')
        ball.keyframe_insert(data_path='rotation_quaternion',frame=f,group='Visual roll')
    for fc in ball.animation_data.action.fcurves:
        for k in fc.keyframe_points:k.interpolation='LINEAR'
for frame,label in [(1,'Release  |  1:5 slow motion'),(52,'Chute convergence'),(100,'Dish entrance')]:
    s.timeline_markers.new(label,frame=frame)
text('Banner',(-.68,-.319,.001),'L01 / BULLET TRACE REPLAY   -   SESSION PLACEMENT, NOT A UNITY LEVEL')
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.001))
floor=bpy.context.object;floor.name='Studio';floor.data.materials.append(material('F0E1C8'))
def aim(o,p):o.rotation_euler=(Vector(p)-o.location).to_track_quat('-Z','Y').to_euler()
for n,p,e in [('Key',(-.65,-.72,1.35),92),('Fill',(1.0,.4,1.15),55)]:
    l=bpy.data.lights.new(n,'AREA');l.energy=e;l.size=1
    o=bpy.data.objects.new(n,l);s.collection.objects.link(o);o.location=p;aim(o,(0,0,0))
c=bpy.data.cameras.new('Fixture view');c.type='ORTHO';c.ortho_scale=1.69
cam=bpy.data.objects.new('Fixture view',c);s.collection.objects.link(cam);cam.location=(.02,-1.47,1.94);aim(cam,(0,.000,.05));s.camera=cam
s.render.resolution_x=1560;s.render.resolution_y=720;s.render.resolution_percentage=100
s.frame_set(1);bpy.ops.object.select_all(action='DESELECT')
for sc in bpy.data.screens:
    for ar in sc.areas:
        if ar.type=='VIEW_3D':
            ar.spaces.active.overlay.show_overlays=False
            ar.spaces.active.shading.color_type='MATERIAL'
            ar.spaces.active.shading.show_cavity=True
            ar.spaces.active.region_3d.view_perspective='CAMERA'
            ar.spaces.active.region_3d.view_camera_zoom=13
bpy.ops.wm.save_as_mainfile(filepath=str(P/'source'/'Level01_Bullet_Trace.blend'),compress=True)
print('L1 visual fixture saved',[(k,len(c['ball_center_trace_t_xyz'])) for k,c in enumerate(cases)])
