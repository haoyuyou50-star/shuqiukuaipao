"""Confirm on-disk FBX importability, scale, meshes, proxies and marker hierarchy with Blender."""
from pathlib import Path
import collections
import json
import math

import bpy

KIT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((KIT / "docs" / "manifest.json").read_text())
TOL_M = 0.0001


def inspect(source, spec):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.unit_settings.system = 'METRIC'
    status = bpy.ops.import_scene.fbx(filepath=str(source))
    if 'FINISHED' not in status:
        return dict(asset=spec['asset'], passed=False, problems=['import failed'])
    root = bpy.data.objects.get(spec['asset'])
    if root is None:
        return dict(asset=spec['asset'], passed=False, problems=['asset root missing'])
    visual_count, proxy_count = 0, 0
    min_xyz, max_xyz = [math.inf]*3, [-math.inf]*3
    markers = collections.defaultdict(list)
    problems = []
    for ob in root.children_recursive:
        if ob.type == 'MESH':
            ob.data.calc_loop_triangles()
            tris = len(ob.data.loop_triangles)
            if tris == 0:
                problems.append(f'empty mesh: {ob.name}')
            if ob.name.startswith('COL_'):
                proxy_count += tris
                continue
            visual_count += tris
            if not any(m is not None for m in ob.data.materials):
                problems.append(f'no display material: {ob.name}')
            for v in ob.data.vertices:
                p = ob.matrix_world @ v.co
                for i, value in enumerate(p):
                    min_xyz[i] = min(min_xyz[i], value)
                    max_xyz[i] = max(max_xyz[i], value)
        elif ob.type == 'EMPTY':
            markers[(ob.name.split('.')[0], ob.parent.name.split('.')[0])].append(ob)
    result_bounds = [round(a-b, 5) for a, b in zip(max_xyz, min_xyz)]
    if visual_count != spec['render_triangles']:
        problems.append(f'visual triangles {visual_count} != {spec["render_triangles"]}')
    if proxy_count != spec['proxy_triangles']:
        problems.append(f'proxy triangles {proxy_count} != {spec["proxy_triangles"]}')
    if not all(abs(a-b)<TOL_M for a,b in zip(result_bounds,spec['visual_bounds_m'])):
        problems.append(f'metre extents {result_bounds} != {spec["visual_bounds_m"]}')
    for m in spec['markers']:
        key = (m['name'],m['parent'])
        if not any((max(abs(p-q) for p,q in zip(ob.location,m['position_m']))<TOL_M)
                   for ob in markers.get(key,[])):
            problems.append(f'marker placement or parent mismatch: {key}')
    return dict(asset=spec['asset'], passed=not problems, visual_triangles=visual_count,
                proxy_triangles=proxy_count, checked_markers=len(spec['markers']),
                bounds_m=result_bounds, problems=problems)


def main():
    seen = {p.stem for p in (KIT / 'models').glob('*.fbx')}
    expected = {a['asset'] for a in MANIFEST['assets']}
    reports = [inspect(KIT/'models'/(a['asset']+'.fbx'),a) for a in MANIFEST['assets'] if a['asset'] in seen]
    missing, unexpected = sorted(expected-seen), sorted(seen-expected)
    result = dict(test='Blender re-import of generated FBX; not a Unity import',
                  blender=bpy.app.version_string, total=len(expected), missing=missing, unexpected=unexpected,
                  passed_count=sum(x['passed'] for x in reports), reports=reports)
    (KIT/'qa'/'fbx_roundtrip_result.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    for x in reports:
        if not x['passed']:
            print(x['asset'], *x['problems'],sep=': ')
    print(f"{result['passed_count']}/{result['total']} FBX verified; missing={missing}, unexpected={unexpected}")
    if missing or unexpected or any(not x['passed'] for x in reports):
        raise RuntimeError('FBX manifest mismatch')


if __name__ == '__main__':
    main()
