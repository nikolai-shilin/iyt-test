# Imports a third-party GLB as it is, prints what is inside (size, objects, materials, polygons) and renders a
# quick three-quarter view on calm water, to judge a model before building a figure from it.
#   blender --background --factory-startup --python docs/design/blender/inspect_model.py -- \
#     --model docs/design/blender/models/sun-odyssey-49ds.glb --out /tmp/preview.jpg
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector
import common as C

arg = C.cli()
MODEL = arg('--model', ''); OUT = arg('--out', 'preview.jpg'); SAMPLES = arg('--samples', 64); AZ = arg('--azimuth', 35.0); EL = arg('--elevation', 18.0)

C.reset()
bpy.ops.import_scene.gltf(filepath=os.path.abspath(MODEL))
meshes = [o for o in C.col.all_objects if o.type == 'MESH']
lo = Vector((1e9,) * 3); hi = Vector((-1e9,) * 3)
for o in meshes:
    for c in o.bound_box:
        w = o.matrix_world @ Vector(c); lo = Vector(map(min, lo, w)); hi = Vector(map(max, hi, w))
size = hi - lo
polys = sum(len(o.data.polygons) for o in meshes)
mats = sorted({s.material.name for o in meshes for s in o.material_slots if s.material})
print(f'MODEL {os.path.basename(MODEL)}: {len(meshes)} mesh objects, {polys} polygons, {len(mats)} materials')
print(f'SIZE x {size.x:.2f}  y {size.y:.2f}  z {size.z:.2f} m   (min z {lo.z:.2f})')
print('MATERIALS', mats[:40])
sharp = sum(1 for o in meshes for p in o.data.polygons if not p.use_smooth)
print(f'FLAT-SHADED polygons {sharp} of {polys}')

# calm sea at the lowest point of the hull plus a third of its depth (a rough waterline), sky, a 3/4 camera
centre = (lo + hi) / 2; L = max(size.x, size.y)
wm = bpy.data.meshes.new('sea'); wm.from_pydata([(-600, -600, 0), (600, -600, 0), (600, 600, 0), (-600, 600, 0)], [], [(0, 1, 2, 3)])
C.obj('sea', wm, C.water_mat(), (0, 0, lo.z + size.z * 0.12))
C.sky((-3, 5, -2), (0, 0, 0))
a, e = math.radians(AZ), math.radians(EL); dist = L * 1.5
pos = centre + Vector((math.cos(a) * math.cos(e), math.sin(a) * math.cos(e), math.sin(e))) * dist
cd = bpy.data.cameras.new('cam'); cd.lens = 40
cam = bpy.data.objects.new('cam', cd); C.col.objects.link(cam); bpy.context.scene.camera = cam
cam.location = pos; cam.rotation_euler = (centre - pos).to_track_quat('-Z', 'Y').to_euler()
C.render(OUT, SAMPLES, 50, -0.6)
