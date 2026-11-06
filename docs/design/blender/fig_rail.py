# The rail rope figure with a real yacht: the Sun Odyssey 49DS lies starboard side to the pontoon exported from
# figure-rope-3d.html (kindRail). Her hand-built stand-in is hidden; the fender hangs between her topsides and the
# pontoon edge, its line led up her side and over her top guardrail (found by ray casts on the real model), the end
# hanging inboard; the spring line runs from her midships cleat to the cleat hitch on the pontoon cleat.
#   blender --background --factory-startup --python docs/design/blender/fig_rail.py -- --out .../rope-rail.jpg
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
from mathutils import Vector
import common as C, kit as K

arg = C.cli(); OUT = arg('--out', 'rope-rail.jpg'); SAMPLES = arg('--samples', 256); SCALE = arg('--scale', 100)
HERE = os.path.dirname(os.path.abspath(__file__))
LIFT = 0.95                     # the exported scene has its water at -0.95; ours is at 0
FX = 1.15                       # where the fender hangs, along the boat (world x)
C3 = Vector((1.95, -0.553 + LIFT, -1.0))   # the pontoon cleat, Three.js space

C.reset()
y = K.load_yacht(name='yacht')
y.place(0.2, -1.69, heading=270)       # bow to -X like the stand-in; her starboard side faces the pontoon (+Y)
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get(); sc = bpy.context.scene

def side_y(x, z, start=3.0):
    """Outboard surface of the yacht (starboard, facing +Y) at (x, z): cast from the pontoon side towards her."""
    hit, loc, *_ = sc.ray_cast(dg, Vector((x, start, z)), Vector((0, -1, 0)))
    return loc.y if hit else None

# bring her alongside: her outermost point at the fender should leave just a fender's width to the pontoon edge
out_y = max(v for v in (side_y(FX, 0.1 + k * 0.05) for k in range(30)) if v is not None)
y.root.location.y += (0.78 - 0.225) - out_y
bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()
hull_y = side_y(FX, 0.45)
edge_z, edge_y = None, None
for k in range(80):                    # the deck edge: the highest z where the topsides are still near the hull line
    z = 0.6 + k * 0.02; yy = side_y(FX, z)
    if yy is not None and yy > hull_y - 0.25: edge_z, edge_y = z, yy
wire_z, wire_y = None, None
for k in range(140):                   # the top guardrail wire: the highest thin hit above the deck edge
    z = edge_z + 0.05 + k * 0.006; yy = side_y(FX, z)
    if yy is not None and yy > edge_y - 0.35: wire_z, wire_y = z, yy
print('RAIL hull_y', round(hull_y, 3), 'edge', round(edge_z, 3), round(edge_y, 3), 'wire', wire_z and round(wire_z, 3), wire_y and round(wire_y, 3))
if wire_z is None or wire_z < edge_z + 0.3:     # fall back to a standard 600 mm guardrail if the scan found none
    wire_z, wire_y = edge_z + 0.6, edge_y - 0.06

def T(p): return (p[0], p[2], -p[1])   # Blender -> Three.js space, for the exported rope points

# fender: a navy-socked cylinder, its top eye just below the toe rail line
fr, fl = 0.105, 0.42
band = [v for v in (side_y(FX, 0.12 + k * 0.05) for k in range(17)) if v is not None]   # waterline up to the eye
fc = Vector((FX, max(band) + fr + 0.004, 0.12 + fr + fl / 2))
bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=40, v_segments=20, radius=fr)
for v in bm.verts: v.co.z += fl / 2 if v.co.z > 0 else (-fl / 2 if v.co.z < 0 else 0)
for f in bm.faces: f.smooth = True
fme = bpy.data.meshes.new('fender'); bm.to_mesh(fme); bm.free()
C.obj('fender', fme, C.fabric_mat('fender-sock', '#1e2f55', '#5d75a8', 1400.0), fc)
eye = fc + Vector((0, 0, fl / 2 + fr + 0.012))
ring = bpy.data.meshes.new('eye'); C.obj('fender-eye', ring, None)
K.cone  # (kit helpers stay importable)
fline = [eye]; prev = eye.y
for z in (eye.z + 0.1, eye.z + 0.25, (eye.z + edge_z) / 2, edge_z - 0.05):   # up the outside of the flaring topsides
    yy = side_y(FX + 0.004, z); prev = max(prev, (yy if yy is not None else prev) + 0.012)
    fline.append(Vector((FX + 0.004, prev, z)))
fline += [Vector((FX + 0.006, edge_y + 0.03, edge_z + 0.03)), Vector((FX + 0.008, wire_y + 0.012, wire_z - 0.03)),
          Vector((FX + 0.009, wire_y + 0.004, wire_z + 0.008)), Vector((FX + 0.010, wire_y - 0.012, wire_z)),
          Vector((FX + 0.012, wire_y - 0.02, wire_z - 0.06)), Vector((FX + 0.016, wire_y - 0.035, wire_z - 0.22)), Vector((FX + 0.02, wire_y - 0.05, wire_z - 0.36))]

# spring line: off the midships cleat, over the toe rail, down to the pontoon cleat
cleat = y.world((3.66, -1.99, 3.60))
spring_head = [cleat + Vector((0.12, -0.02, 0.0)), cleat + Vector((0.0, 0.0, 0.03)), cleat + Vector((-0.06, 0.06, 0.02)),
               Vector((cleat.x - 0.1, edge_y + 0.03, edge_z + 0.04))]

def reroute(i, P):
    if i == 1:                                     # the fender line: built from the real yacht
        return [T(p) for p in fline]
    j = next(k for k, p in enumerate(P) if (Vector(p) + Vector((0, LIFT, 0)) - C3).length < 0.5)
    tail = [(p[0], p[1] + LIFT, p[2]) for p in P[j:]]
    a = Vector(T(spring_head[-1])); b = Vector(tail[0]); mid = []
    for t in (0.2, 0.4, 0.6, 0.8):                 # a slack bight between the toe rail and the pontoon
        q = a.lerp(b, t); q.y -= math.sin(t * math.pi) * 0.12; mid.append(tuple(q))
    return [T(p) for p in spring_head] + mid + tail

before = set(bpy.data.objects)
d = C.load_exported(os.path.join(HERE, 'scenes', 'rail'), rope_fn=reroute)
bpy.context.view_layer.update()
new = [o for o in bpy.data.objects if o not in before]
for o in new:                                       # lift the exported scene so its water sits at our z = 0
    if o.parent is None and not o.name.startswith(('rope', 'braid')): o.location.z += LIFT
bpy.context.view_layer.update()
for o in new:                                       # hide the stand-in yacht (everything on her side of the pontoon)
    if o.type != 'MESH' or o.name.startswith(('rope', 'braid')): continue
    lo, hi = K.bbox([o]); cy = (lo.y + hi.y) / 2
    names = {sl.material.name.split('.')[0] for sl in o.material_slots if sl.material}
    if cy < 0.74 or 'water' in names: o.hide_render = True
K.sea('calm', center=(0, 0))
C.sky(d['sun']['pos'], d['sun']['target'], 0.22); K.darken_visible_sky()
cam = C.camera_matrix(d['cam']['matrix'], d['cam']['fov']); cam.location.z += LIFT
C.focus_on_centre(cam, 11.0)
lab_wire = Vector((-0.6, side_y(-0.6, wire_z) or wire_y, wire_z))
C.render(OUT, SAMPLES, SCALE, -0.8, [(tuple(lab_wire), 'guardrail'), (tuple(fline[3]), 'fender line')], d['note'], space='blender')
