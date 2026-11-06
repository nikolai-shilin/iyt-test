# The winch rope figure with a real winch: the scene exported from figure-rope-3d.html (kindWinch), its hand-built
# winches swapped for the Lewmar self-tailing winch from 3D Warehouse, the sheet's last turns lowered into that
# winch's jaws and the lock-in handle seated on its top.
#   blender --background --factory-startup --python docs/design/blender/fig_winch.py -- --out .../rope-winch.jpg
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
from mathutils import Vector
import common as C, kit as K

arg = C.cli(); OUT = arg('--out', 'rope-winch.jpg'); SAMPLES = arg('--samples', 256); SCALE = arg('--scale', 100)
HERE = os.path.dirname(os.path.abspath(__file__))
Y0 = 0.05                      # top of the winch pad (Three.js y = Blender z)
K_UNIT = 0.040                 # Lewmar model units to metres: 6.19 tall -> 248 mm, a 46-size winch
AXIS = Vector((2.129, 1.708))   # first winch's axis in the model file (centre of its body)
OLD_TOP = Y0 + 0.179           # top of the hand-built winch
NEW_TOP = Y0 + 6.19 * K_UNIT   # top of the Lewmar
DRUM_R = 1.25 * K_UNIT + 0.006  # sheet centreline round the Lewmar drum

def lerp_map(z, xs, ys):
    for i in range(len(xs) - 1):
        if z <= xs[i + 1]:
            t = (z - xs[i]) / (xs[i + 1] - xs[i]); return ys[i] + (ys[i + 1] - ys[i]) * max(0, min(1, t))
    return ys[-1]

def reroute(i, P):
    """Move the sheet's turns from the hand-built winch (drum r 77 mm, turns 36-90 mm up, jaws at 137 mm) onto the
    Lewmar: its drum (r 50 mm, 80-180 mm up) and its jaws (about 205 mm up). Three.js space, y up."""
    out = []
    for x, y, z in P:
        r = math.hypot(x, z)
        if r < 0.14 and Y0 < y < Y0 + 0.22:
            w = 1.0 if r < 0.095 else (0.14 - r) / 0.045        # blend out over the lead-in and the tail
            ny = lerp_map(y, [Y0, Y0 + 0.036, Y0 + 0.09, Y0 + 0.137, Y0 + 0.22], [Y0, Y0 + 0.095, Y0 + 0.165, Y0 + 0.205, Y0 + 0.24])
            nr = r * (DRUM_R / 0.077) if r < 0.095 else r
            y = y + (ny - y) * w; k = 1 + (nr / max(r, 1e-6) - 1) * w; x, z = x * k, z * k
        out.append((x, y, z))
    return out

C.reset()
d = C.load_exported(os.path.join(HERE, 'scenes', 'winch'), rope_fn=reroute)
bpy.context.view_layer.update()
# hide the hand-built winches (primary at x 0, secondary at x 0.78 scaled 0.82); keep pads and the handle
handle = []
for o in list(C.col.all_objects):
    if o.type != 'MESH' or o.hide_render: continue
    lo, hi = K.bbox([o]); c = (lo + hi) / 2
    for cx, s in ((0.0, 1.0), (0.78, 0.82)):
        near = math.hypot(c.x - cx, c.y) < 0.145 * s and (hi.x - lo.x) < 0.24 * s and (hi.y - lo.y) < 0.24 * s
        if near and lo.z >= Y0 - 0.006 and lo.z < Y0 + 0.17 and hi.z <= Y0 + 0.235 * s and not o.name.startswith(('rope', 'braid')):
            o.hide_render = True
        if near and (hi.z - lo.z) < 0.005 and (hi.x - lo.x) > 0.08 * s: o.hide_render = True   # the old winch's top ring
    if lo.z > Y0 + 0.17 and math.hypot(c.x, c.y) < 0.32 and hi.z < Y0 + 0.4: handle.append(o)
for o in handle:                                  # seat the handle on the Lewmar's top
    if not o.hide_render:
        mw = o.matrix_world.copy(); mw.translation.z -= OLD_TOP - NEW_TOP; o.matrix_world = mw

def lewmar(at, scale):
    """The first winch from the Lewmar file, its axis at `at`, the base on the pad."""
    root, objs = K.load_model('winch-lewmar-st.glb', drop_planes=False)
    for o in objs:                                # drop the second winch in the file (its vertices lie at y > 6)
        if o.type != 'MESH': continue
        bm = bmesh.new(); bm.from_mesh(o.data); mw = o.matrix_world
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if (mw @ v.co).y > 6.0], context='VERTS')
        bm.to_mesh(o.data); bm.free()
    root.scale = (K_UNIT * scale,) * 3
    root.location = (at[0] - AXIS.x * K_UNIT * scale, at[1] - AXIS.y * K_UNIT * scale, Y0)
    M = K.mats()
    def rule(c, name):
        if 'Concrete' in name: return M['chrome']     # the body: base flange and drum, polished
        if 'Aluminum' in name: return M['satin']      # top cap and stripper arm
        return M['dark']                              # the self-tailer jaws: black
    K.recolor(objs, rule)
    return root
_w = lewmar((0.0, 0.0), 1.0); lewmar((0.78, 0.0), 0.82)
bpy.context.view_layer.update()
_lo, _hi = K.bbox([o for o in _w.children_recursive if o.type == 'MESH'])
print('LEWMAR bbox', tuple(round(v, 3) for v in _lo), tuple(round(v, 3) for v in _hi))

C.sky(d['sun']['pos'], d['sun']['target'], 0.22)
K.darken_visible_sky()
cam = C.camera_matrix(d['cam']['matrix'], d['cam']['fov'])
C.focus_on_centre(cam, 8.0)
C.render(OUT, SAMPLES, SCALE, -0.7, [(l['p'], l['text']) for l in d['labels'][:2]] + [((0.235, NEW_TOP + 0.09, 0.08), 'handle still in the winch')], d['note'])
