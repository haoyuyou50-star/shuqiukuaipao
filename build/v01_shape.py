"""Reused silhouette from the first approved potato study."""
import bpy
from mathutils import Vector
from math import atan2
from random import Random

def _base_dual():
    # Dual of a subdivided icosphere: 42 organic-looking pentagonal/hexagonal facets.
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1)
    seed = bpy.context.object
    points = [v.co.copy() for v in seed.data.vertices]
    triangles = [tuple(p.vertices) for p in seed.data.polygons]
    mesh = seed.data
    bpy.data.objects.remove(seed, do_unlink=True)
    if mesh.users == 0:
        bpy.data.meshes.remove(mesh)
    mids = [sum((points[i] for i in tri), Vector((0,0,0))).normalized()
            for tri in triangles]
    near = [[] for _ in points]
    for q, tri in enumerate(triangles):
        for p in tri:
            near[p].append(q)
    faces = []
    for p, adj in zip(points, near):
        ax = p.cross(Vector((0, 0, 1)))
        if ax.length < 1e-5:
            ax = p.cross(Vector((0, 1, 0)))
        ax.normalize()
        ay = p.cross(ax).normalized()
        faces.append(tuple(sorted(adj, key=lambda q: atan2(mids[q].dot(ay), mids[q].dot(ax)))))
    return mids, faces

def _body_shape(mids):
    rng = Random(7139)
    verts = []
    for v in mids:
        # Similar body proportions for every material state, with a gently irregular perimeter.
        factor = 1 + rng.uniform(-.045, .045)
        x, y, z = v
        verts.append(Vector((x * .415 * factor + .021*z,
                             y * .385 * factor,
                             z * .416 * factor)))
    minz = min(v.z for v in verts)
    for v in verts:
        v.z -= minz
    return verts

