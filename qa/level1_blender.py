"""Level 1 asset QA. Run Blender headless; this does not exercise Unity.

Uses live collision proxy geometry from the generated A08/A09 kit, then
releases 60 mm rigid spheres against those proxies in Blender's Bullet world.
No project scene is overwritten. Meter coordinates: +Y downstream, +Z up.
"""
from pathlib import Path
from mathutils import Vector
import bpy
import json
import math
import sys

KIT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KIT / "build"))
from l1 import build
from hero import build as hero
from common import D

R = D / 2
TOL = 1e-6
SCENARIOS = (("center", 0), ("side_left", -.080), ("side_right", .080))


def select(o):
    bpy.ops.object.select_all(action="DESELECT")
    o.select_set(True)
    bpy.context.view_layer.objects.active = o


def rigid(o, mode, shape, friction=.40):
    select(o)
    bpy.ops.rigidbody.object_add(type=mode)
    body = o.rigid_body
    body.collision_shape = shape
    body.friction = friction
    body.restitution = .02
    body.use_margin = True
    body.collision_margin = .0005 if mode == "PASSIVE" else 0
    return body


def marker(root, name):
    for o in root.children_recursive:
        if o.get("marker") and (o.name == name or o.name.startswith(name + ".")):
            return o.matrix_world.translation.copy()
    raise ValueError(f"{root.name} does not have marker {name}")


def floor_sections(root):
    """Derive left/right floor endpoints from actual exported collision volumes."""
    by_y = {}
    for o in root.children_recursive:
        if not o.get("collision_proxy") or "_Floor" not in o.name:
            continue
        for v in o.data.vertices:
            w = o.matrix_world @ v.co
            y = round(w.y, 6)
            by_y.setdefault(y, []).append(tuple(w))
    assert len(by_y) >= 2
    return [(y, min(p[0] for p in xyz), max(p[0] for p in xyz),
             max(p[2] for p in xyz)) for y, xyz in sorted(by_y.items())]


def stations_summary(root):
    sec = floor_sections(root)
    a = marker(root, "IN")
    b = marker(root, "OUT")
    assert sec[0][0] == round(a.y, 6) and sec[-1][0] == round(b.y, 6)
    assert abs(sec[0][3]-a.z)<TOL and abs(sec[-1][3]-b.z)<TOL
    assert all(s[3]>t[3] for s,t in zip(sec,sec[1:]))
    assert min(right-left for _,left,right,_ in sec)>D
    return dict(inlet_width_mm=round((sec[0][2]-sec[0][1])*1000,1),
                outlet_width_mm=round((sec[-1][2]-sec[-1][1])*1000,1),
                travel_mm=round((b.y-a.y)*1000,1),
                drop_mm=round((a.z-b.z)*1000,1),
                floor_stations=[[round(v,6) for v in row] for row in sec])


def attach_proxies(root):
    for o in root.children_recursive:
        if o.get("collision_proxy"):
            rigid(o, "PASSIVE", "CONVEX_HULL")


def dish_points(root):
    o=next(o for o in root.children_recursive if o.type=='MESH' and 'ceramic dish' in o.name)
    world=[o.matrix_world @ v.co for v in o.data.vertices]
    rim_z = max(p.z for p in world)
    rim_r = min(math.hypot(p.x-root.location.x, p.y-root.location.y)
                for p in world if p.z > rim_z - .003)
    return rim_z, rim_r


def build_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system='METRIC'
    scene.render.fps=120
    scene.frame_end=300
    bpy.ops.rigidbody.world_add()
    scene.rigidbody_world.substeps_per_frame=5
    scene.rigidbody_world.solver_iterations=28
    scene.rigidbody_world.point_cache.frame_end=scene.frame_end
    assets = {o.name:o for o in [*hero(),*build()]}
    return scene, assets


def spawn(xyz):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=R, location=xyz)
    obj = bpy.context.object
    obj.name = "Test sphere, 60mm"
    b = rigid(obj,"ACTIVE","SPHERE",.40)
    b.mass = .028
    b.linear_damping = .025
    b.angular_damping = .025
    b.use_deactivation = False
    return obj


def simulate_trial(name, offset=None):
    scene, a = build_scene()
    ramp, chute, dish = [a[id] for id in ('A08_TakeoutBoxRamp','A09_FryCartonCatch','A04_KetchupDish')]
    sphere, ring = [a[id] for id in ('A01_Potato','A05_RingReference')]
    assert abs(float(sphere['ball_diameter_m'])-D)<TOL
    assert float(ring['placeholder_clear_ID_m'])>D
    if offset is not None:
        ramp.location.x = -2
        chute.location.z = .071
    else:
        chute.location.x = +2
    bpy.context.view_layer.update()
    start_object = ramp if offset is None else chute
    a_min,a_max = marker(start_object,'IN'), marker(start_object,'OUT')
    if offset is not None:
        dish.location.y = a_max.y + .085
        bpy.context.view_layer.update()
    rim_z, dish_r = dish_points(dish)
    assert dish_r > R
    y = a_min.y + (.015 if offset is None else .021)
    s = floor_sections(start_object)
    t = (y-s[0][0])/(s[1][0]-s[0][0])
    dz = s[1][3]-s[0][3]
    z = s[0][3] + dz*t
    v = spawn((offset or 0, y, z + R*math.hypot(1, dz/(s[1][0]-s[0][0])) + (.001 if offset is None else .012)))
    attach_proxies(start_object)
    scene.frame_set(1)
    launch = None
    target = None
    min_wall_clearance = math.inf
    trace = []
    for f in range(1,scene.frame_end+1):
        scene.frame_set(f)
        xyz = v.evaluated_get(bpy.context.evaluated_depsgraph_get()).matrix_world.translation
        x,y,z = xyz
        trace.append([round(f/scene.render.fps,5), round(x,6),round(y,6), round(z,6)])
        if y >= a_max.y and launch is None:
            launch = dict(frame=f, x_mm=round(x*1000,1), y_mm=round(y*1000,1), z_mm=round(z*1000,1))
        inside_dish = (y-dish.location.y)**2+x*x <= (dish_r-R)**2
        if launch and ((offset is None) or (inside_dish and z-R <= rim_z and z>rim_z)):
            target=dict(frame=f,x_mm=round(x*1000,1),y_mm=round(y*1000,1),z_mm=round(z*1000,1))
            break
        if a_min.y <= y <= a_max.y:
            for sa,sb in zip(s,s[1:]):
                if sa[0] <= y <= sb[0]:
                    for j in (1,2):
                        rise=sb[j]-sa[j]
                        run=sb[0]-sa[0]
                        wall_x=sa[j] + rise/run*(y-sa[0])
                        min_wall_clearance=min(min_wall_clearance,abs(wall_x-x)/math.hypot(1,rise/run)-R)
        if z < -.05 or (offset is not None and y > dish.location.y+dish_r+.09):
            break
    return dict(name=name, start_offset_mm=None if offset is None else round(offset*1000),
                floor=stations_summary(start_object), exit=launch, target=target,
                minimum_wall_clearance_mm=round(min_wall_clearance*1000,2),
                dish=dict(rim_height_mm=round(rim_z*1000,1), inner_rim_radius_mm=round(dish_r*1000,1),
                          chute_lift_mm=71, rim_center_after_out_mm=85) if offset is not None else None,
                final=trace[-1], steps=len(trace), ball_center_trace_t_xyz=trace,
                result="PASS" if target and (not offset or min_wall_clearance < .002) else "FAIL")


def main():
    cases=[simulate_trial("starter_ramp")]+[simulate_trial(n,v) for n,v in SCENARIOS]
    result=dict(engine="Blender "+bpy.app.version_string+" / Bullet", convention="m | +Y downstream | +Z up",
                nominal_ball_diameter_mm=round(D*1000), caveat="At the dish, a sphere entering the volume of the actual modeled inner rim marks a geometric trigger hit; this is not a stability/settling criterion. No Unity trigger, XR or portal SDK is exercised.",
                cases=cases, passed=all(c["result"]=="PASS" for c in cases))
    fn=KIT/"qa"/"level1_blender_result.json"
    fn.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print("L1_QA_RESULT "+json.dumps(result,ensure_ascii=False))
    if not result["passed"]:
        raise RuntimeError("Some trials failed")


if __name__=='__main__':
    main()
