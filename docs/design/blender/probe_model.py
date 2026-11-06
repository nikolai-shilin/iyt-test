# Lists a GLB's parts grouped by material and by size, so a figure can find the hull, sails, boom and so on.
#   blender --background --factory-startup --python docs/design/blender/probe_model.py -- --model <file.glb> [--top 60]
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector
import common as C

arg = C.cli(); MODEL = arg('--model', ''); TOP = arg('--top', 60)
C.reset(); bpy.ops.import_scene.gltf(filepath=os.path.abspath(MODEL))
rows = []
for o in C.col.all_objects:
    if o.type != 'MESH': continue
    ws = [o.matrix_world @ Vector(c) for c in o.bound_box]
    lo = Vector([min(w[i] for w in ws) for i in range(3)]); hi = Vector([max(w[i] for w in ws) for i in range(3)])
    mats = ','.join(sorted({s.material.name for s in o.material_slots if s.material}))
    rows.append(((hi - lo).length, o.name, len(o.data.polygons), lo, hi, mats))
rows.sort(key=lambda r: -r[0])
for d, n, p, lo, hi, m in rows[:TOP]:
    print(f'{d:7.2f} | {n[:38]:38} | {p:6} | ({lo.x:6.2f},{lo.y:6.2f},{lo.z:6.2f})..({hi.x:6.2f},{hi.y:6.2f},{hi.z:6.2f}) | {m[:60]}')
by = {}
for d, n, p, lo, hi, m in rows:
    by.setdefault(m, [0, 0]); by[m][0] += 1; by[m][1] += p
print('--- by material (objects, polygons)')
for m, (k, p) in sorted(by.items(), key=lambda kv: -kv[1][1])[:50]:
    mat = bpy.data.materials.get(m.split(',')[0]) if m else None
    col = ''
    if mat and mat.node_tree:
        b = next((n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
        if b and not b.inputs['Base Color'].is_linked: col = tuple(round(c, 2) for c in b.inputs['Base Color'].default_value[:3])
        elif b: col = 'texture'
    print(f'{k:5} {p:7} | {m[:60]} | {col}')
