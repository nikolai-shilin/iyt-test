# The bollard-ring rope figure rebuilt in Blender and rendered with Cycles (path traced).
# Same scene as kindRing() in docs/design/figure-rope-3d.html: a mooring line with a loop dropped over a
# cast-iron bollard on a granite quay, a yacht alongside. Geometry, rope path and camera are ported 1:1.
#
# Run:  blender --background --factory-startup --python docs/design/blender/rope_ring.py -- \
#         --out docs/design/figure-style/blender/rope-ring.jpg --samples 256
import os, sys, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
from mathutils import Vector
import common as C
from common import B, tbox, cyl, lathe, rbox, obj, simple, granite_mat, joint_mat, iron_mat, gel_mat, water_mat, three_strand

arg = C.cli()
OUT = arg('--out', 'rope-ring.jpg'); SAMPLES = arg('--samples', 256); SCALE = arg('--scale', 100); BLEND = arg('--blend', '')
scene = C.reset(); col = C.col
random.seed(7)
rnd = random.random

# ---------- the scene (ringScene + bollard + ropePath, from figure-rope-3d.html) ----------
stone = granite_mat('setts', per_object=True, dark='#8a857d', light='#c8c3ba', scale=1.3)
coping = granite_mat('coping', base='#b3afa7', per_object=False, scale=0.8, dark='#3d3b38', light='#dedad3')

# setts: rows of granite blocks in a running bond, each slightly tilted and proud or sunk
sett_me = rbox('sett', (0.2, 0.11, 0.09), 0.014, 3); sett_me.materials.append(stone)
z = -1.0; row = 0
while z < 3.2:
    x = -3.4 + (0.11 if (round(z / 0.122) % 2) else 0)
    while x < 3.4:
        px, pz = x + (rnd() - 0.5) * 0.01, z + (rnd() - 0.5) * 0.008
        ex, ey, ez = (rnd() - 0.5) * 0.04, (rnd() - 0.5) * 0.06, (rnd() - 0.5) * 0.04
        py = -0.035 + (rnd() - 0.5) * 0.006
        o = bpy.data.objects.new('sett', sett_me); col.objects.link(o)
        o.location = B(px, py, pz); o.rotation_euler = (ex, -ez, ey)  # Three (x, y, z) Euler -> Blender (x, -z, y)
        x += 0.212
    z += 0.122

jm = bpy.data.meshes.new('joint'); jm.from_pydata([(-4, -3.6, 0), (4, -3.6, 0), (4, 1.4, 0), (-4, 1.4, 0)], [], [(0, 1, 2, 3)])
obj('joint', jm, joint_mat(), (0, 0, -0.045 + 0.01))

# coping stones along the quay edge
x = -3.6
while x < 3.6:
    o = tbox((0.9, 0.3, 0.52), (x + (rnd() - 0.5) * 0.01, -0.13, -1.31), coping, 0.03, 4, 'coping')
    o.rotation_euler.z = -(rnd() - 0.5) * 0.01
    x += 0.92
# the quay wall and the water
tbox((8, 1.0, 0.1), (0, -0.78, -1.62), granite_mat('wall', base='#7a746a', per_object=False, scale=0.5), 0.0, 1, 'wall')
wm = bpy.data.meshes.new('water'); wm.from_pydata([(-15, -15, 0), (15, -15, 0), (15, 15, 0), (-15, 15, 0)], [], [(0, 1, 2, 3)])
obj('water', wm, water_mat(), (0, 0, -0.9))

# the yacht alongside
gel = gel_mat()
tbox((11, 1.75, 3.4), (-0.6, -0.36, -3.52), gel, 0.38, 6, 'hull')
tbox((11.04, 0.07, 3.48), (-0.6, 0.46, -3.52), simple('strake', '#3b3e42', 0.5), 0.03, 3, 'strake')
tbox((11.02, 0.06, 3.44), (-0.6, 0.3, -3.52), simple('stripe', '#1d3557', 0.3, coat=0.8), 0.025, 3, 'stripe')
tbox((10.4, 0.02, 3.0), (-0.6, 0.52, -3.52), simple('deck', '#e4dfd2', 0.9), 0.0, 1, 'deck')
steel = simple('steel', '#d7dadd', 0.15, 1.0)
tbox((10.4, 0.05, 0.04), (-0.6, 0.555, -1.86), simple('toerail', '#8a8f94', 0.3, 0.8), 0.008, 2, 'toerail')
x = -4.6
while x < 4:
    cyl('stanchion', 0.014, 0.012, 0.62, 16, steel, B(x, 0.84, -1.9)); x += 1.6
for y in (0.85, 1.13):
    cyl('lifeline', 0.0035, 0.0035, 9.4, 8, steel, B(-0.6, y, -1.9), (0, math.pi / 2, 0))
tbox((0.2, 0.05, 0.09), (-1.25, 0.575, -1.9), steel, 0.02, 2, 'cleat')
# a fender between the hull and the coping
bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=0.1)
for v in bm.verts: v.co.z += 0.21 if v.co.z > 0 else (-0.21 if v.co.z < 0 else 0)
for f in bm.faces: f.smooth = True
fm = bpy.data.meshes.new('fender'); bm.to_mesh(fm); bm.free()
m_f = simple('fender', '#f6f6f2', 0.35, coat=0.6)
obj('fender', fm, m_f, B(0.9, -0.32, -1.68))

# the bollard
prof = [(0, 0), (0.225, 0), (0.232, 0.012), (0.229, 0.032), (0.214, 0.044), (0.16, 0.048), (0.132, 0.058), (0.122, 0.085), (0.114, 0.16), (0.11, 0.23), (0.113, 0.3), (0.12, 0.345), (0.135, 0.372), (0.172, 0.382), (0.18, 0.395), (0.177, 0.41), (0.162, 0.42), (0.125, 0.442), (0.07, 0.458), (0, 0.462)]
iron = iron_mat()
lathe('bollard', prof, 128, iron)
for k in range(4):
    a = k * math.pi / 2 + math.pi / 4
    cyl('bolt', 0.019, 0.019, 0.016, 6, iron, B(math.cos(a) * 0.185, 0.053, math.sin(a) * 0.185))

# the rope: ropePath(F), ported
def v3(x, y, z): return Vector((x, y, z))
F = v3(-1.25, 0.6, -1.9)
d = v3(F.x, 0, F.z).normalized(); u = -d; vv = v3(0, 1, 0).cross(u).normalized()
def at(along, side, y):
    p = u * along + vv * side; p.y = y; return p
R, Ye, ground = 0.141, 0.07, 0.024
K = d * 0.3; K.y = ground
def legY(r):
    if r < 0.215: return Ye - (r - 0.141) * 0.15
    if r < 0.3: return ground + (Ye - 0.012 - ground) * (1 - (r - 0.215) / 0.085) ** 2
    return ground
def leg(sg, rev):
    ang = math.radians(108); Tp = at(math.cos(ang) * R, sg * math.sin(ang) * R, Ye); pts = []
    for i in range(1, 8):
        t = i / 8; p = Tp.lerp(K, t); p.y = legY(math.hypot(p.x, p.z)); pts.append(p)
    return pts[::-1] if rev else pts
pts = []
p = K + vv * 0.04; p.y = ground; pts.append(p)
pts += leg(-1, True)
for a in range(-108, 109, 12):
    r = math.radians(a); pts.append(at(math.cos(r) * R, math.sin(r) * R, Ye + 0.004 * math.cos(r)))
pts += leg(1, False)
pts.append(K.copy())
for s in (0.55, 0.85, 1.15, 1.45, 1.66):
    p = d * s; p.y = ground + (0.008 if s > 1.0 else 0); pts.append(p)
edge = d * 1.79; edge.y = 0.032; pts.append(edge)
E2 = d * 1.83; E2.y = 0.05
for i in range(1, 7):
    t = i / 6; p = E2.lerp(F, t); p.y -= math.sin(t * math.pi) * 0.05; pts.append(p)
pts.append(F + v3(-0.03, 0.0, -0.06))
three_strand('rope', pts)

# ---------- light, camera, render ----------
C.sky((-2.6, 4.2, -0.6), (-0.2, 0, -0.3))
import kit as K; K.darken_visible_sky()   # the darker daylight look shared with the figure types
cam_pos3 = (-d * 1.3); cam_pos3.y = 1.6; cam_pos3 += v3(0.2, 0, -0.02)
cam = C.camera_lookat(tuple(cam_pos3), (-0.27, 0.02, -0.48), 36)
cam.data.dof.use_dof = True; cam.data.dof.focus_distance = (B(0, 0.25, 0) - cam.location).length; cam.data.dof.aperture_fstop = 5.6
C.render(OUT, SAMPLES, SCALE, -0.6, [((0, 0.47, 0), 'Bollard')], 'Loop in the end of a line', BLEND)
