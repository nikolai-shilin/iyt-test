# Article bareboat-skipper/colregs, figures 8-13: day shapes, seen from our foredeck in daylight.
#   8 not under command: two balls          9 restricted in ability to manoeuvre: ball, diamond, ball
#  10 fishing: two cones, points together   11 constrained by her draught: a cylinder
#  12 motor-sailing: a cone, point down     13 aground: three balls
#   blender --background --factory-startup --python docs/design/blender/art_colregs_b.py -- --fig 8
import os, sys, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
from mathutils import Vector, Euler
import common as C, kit as K

arg = C.cli(); FIG = arg('--fig', 8); SAMPLES = arg('--samples', 192); SCALE = arg('--scale', 100)
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = arg('--out', os.path.join(HERE, '..', 'figure-style', 'articles', 'bareboat-skipper', 'colregs', f'{FIG}-3d.jpg'))
SH = 1.25            # day shapes drawn a little over their 0.6 m so they read at this distance
GAP = 1.5            # vertical spacing between shapes (Rule: at least 1.5 m)

def deg(a): return math.radians(a)

# ---------- day shapes ----------
def black():
    return K.mats()['black']

def ball(p, r=0.3 * SH): return K.ball(p, r)
def cone(p, up, r=0.3 * SH, h=0.6 * SH): return K.cone(p, r, h, up=up)
def diamond(p, r=0.3 * SH, h=1.2 * SH):
    K.cone(p + Vector((0, 0, h / 4)), r, h / 2, up=True); K.cone(p - Vector((0, 0, h / 4)), r, h / 2, up=False)
def cylinder(p, r=0.3 * SH, h=1.2 * SH):
    k = CYL_K; C.cyl('cylinder', r * k, r * k, h * k, 32, black(), p)
CYL_K = 1.0

def hoist(top, kinds, gap=GAP):
    """Shapes on a halyard hanging from `top`, top-down; returns the shapes' centres."""
    cs = []; z = 0.0
    for i, k in enumerate(kinds):
        half = {'ball': 0.3, 'cone-up': 0.3, 'cone-down': 0.3, 'diamond': 0.6, 'cylinder': 0.6}[k] * SH
        z += (0.35 if i == 0 else gap - prev) + half; prev = half
        c = top - Vector((0, 0, z)); cs.append(c)
        {'ball': lambda: ball(c), 'cone-up': lambda: cone(c, True), 'cone-down': lambda: cone(c, False),
         'diamond': lambda: diamond(c), 'cylinder': lambda: cylinder(c)}[k]()
    bottom = cs[-1] - Vector((0, 0, 0.9))
    C.tube('halyard', [top, bottom], 0.012, 6, 1.0, C.simple('halyard', '#202224', 0.6))
    return cs

# ---------- the trawler / workboat ----------
WL_T = 1.1           # the trawler model's waterline (model z)
def trawler(pos, heading, booms=True, heel=0.0, sink=0.0):
    root, objs = K.load_model('vessel-trawler.glb', drop_planes=False)
    bpy.context.view_layer.update()
    meshes = [o for o in objs if o.type == 'MESH']
    lo, hi = K.bbox(meshes); foot = max(hi.x - lo.x, hi.y - lo.y)
    for o in meshes:
        l, h = K.bbox([o])
        if max(h.x - l.x, h.y - l.y) > 0.9 * foot and len(o.data.polygons) <= 40: o.hide_render = True   # the sea slab
        elif not booms and (h.z - l.z) < 0.4 and max(h.x - l.x, h.y - l.y) > 8 and h.z < 1.0: o.hide_render = True
    M = K.mats(); red = C.simple('trawler-red', '#9b2a22', 0.45, coat=0.4)
    def rule(c, name):
        if c is None: return None
        l = sum(c) / 3
        if l < 0.2: return M['navy']
        if c[0] > 0.5 and c[1] < 0.3: return red
        return None
    K.recolor(objs, rule)
    root.location = (pos[0], pos[1], -WL_T + sink)
    root.rotation_euler = Euler((deg(heel), 0, deg(90 - heading)), 'XYZ')
    bpy.context.view_layer.update()
    return root

def tworld(root, p):
    return root.matrix_world @ Vector(p)

YARD = (-1.45, 2.35, 8.25)   # the end of the trawler's crosstree, where her shapes hang

# ---------- scenery ----------
def rock(name, p, size, seed):
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1.0)
    rnd = random.Random(seed)
    for v in bm.verts:
        n = v.co.normalized(); v.co = n * (1 + 0.25 * math.sin(n.x * 4 + seed) * math.cos(n.y * 3) + 0.12 * rnd.random())
        v.co = v.co * (1 + 0.3 * (rnd.random() - 0.5)); v.co.z *= 0.6
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    m = C.simple('wet-rock', '#4d4840', 0.55)
    o = C.obj(name, me, m, Vector(p)); o.scale = (size, size * (0.7 + rnd.random() * 0.5), size); return o

def foam_patch(p, r, seed=1):
    """Breaking white water: a noise-masked white decal on the sea."""
    me = bpy.data.meshes.new('foam'); bm = bmesh.new(); bmesh.ops.create_circle(bm, cap_ends=True, segments=48, radius=r); bm.to_mesh(me); bm.free()
    m, nt, b, out = C.new_mat('foam%d' % seed)
    oc = C.obj_coords(nt); n = C.noise(nt, oc, 1.6, 8.0, 0.65)
    sep = C.node(nt, 'ShaderNodeSeparateXYZ'); C.link(nt, oc, sep.inputs['Vector'])
    rr = C.math_(nt, 'SUBTRACT', 1.0, C.math_(nt, 'DIVIDE', C.math_(nt, 'LENGTH' if False else 'SQRT', C.math_(nt, 'ADD', C.math_(nt, 'MULTIPLY', sep.outputs['X'], sep.outputs['X']), C.math_(nt, 'MULTIPLY', sep.outputs['Y'], sep.outputs['Y']))), r))
    mask = C.math_(nt, 'MULTIPLY', C.math_(nt, 'GREATER_THAN', n, 0.4), C.math_(nt, 'POWER', C.math_(nt, 'MAXIMUM', rr, 0.0), 0.35))
    C.setin(b, 'Base Color', C.lin('#eef2f2')); C.setin(b, 'Roughness', 0.8)
    tp = C.node(nt, 'ShaderNodeBsdfTransparent'); mx = C.node(nt, 'ShaderNodeMixShader')
    C.link(nt, mask, mx.inputs['Fac']); C.link(nt, tp.outputs[0], mx.inputs[1]); C.link(nt, b.outputs[0], mx.inputs[2]); C.link(nt, mx.outputs[0], out.inputs['Surface'])
    o = C.obj('foam', me, m, Vector(p)); o.visible_shadow = False; return o

def ferry(pos, heading, length=85.0):
    root, objs = K.load_model('vessel-ferry.glb', drop_planes=False)
    bpy.context.view_layer.update()
    meshes = [o for o in objs if o.type == 'MESH']
    for o in meshes:
        l, h = K.bbox([o])
        if (h.y - l.y) > 60: o.hide_render = True                       # the sea it came on
    vis = [o for o in meshes if not o.hide_render]
    lo, hi = K.bbox(vis)
    k = length / (hi.x - lo.x); root.scale = (k,) * 3
    bpy.context.view_layer.update(); lo, hi = K.bbox(vis)
    c = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, 0))
    root.location = Vector(root.location) - c
    piv = bpy.data.objects.new('ferry-pivot', None); C.col.objects.link(piv)
    root.parent = piv; piv.location = (pos[0], pos[1], -2.4 * k); piv.rotation_euler = (0, 0, deg(90 - heading))
    bpy.context.view_layer.update()
    return piv, vis, k

# ---------- the scene ----------
C.reset()
me = K.load_yacht(name='own'); me.place(0, 0, heading=0)
eye = me.world((7.2, -1.2, 5.1))          # starboard side deck, just aft of the forestay
labels = []
if FIG in (8, 9, 10, 13):
    K.sea('breeze' if FIG != 13 else 'fresh'); K.day_sky(sun_az=150, sun_el=40)
    dist = {8: 95, 9: 90, 10: 100, 13: 100}[FIG]
    p = Vector((math.sin(deg(22)) * dist, math.cos(deg(22)) * dist, 0)) + Vector((eye.x, eye.y, 0))
    hdg = {8: 110, 9: 95, 10: 60, 13: 235}[FIG]
    t = trawler(p, hdg, booms=(FIG == 10), heel=(-13 if FIG == 13 else 0), sink=(0.5 if FIG == 13 else 0))
    top = tworld(t, YARD)
    kinds = {8: ['ball', 'ball'], 9: ['ball', 'diamond', 'ball'], 10: ['cone-down', 'cone-up'], 13: ['ball', 'ball', 'ball']}[FIG]
    cs = hoist(top, kinds, gap=(1.35 if FIG in (9, 13) else GAP))
    if FIG == 9:     # lifting a buoy: a derrick over her side, the wire down to a lateral mark half out of the water
        foot = tworld(t, (-4.0, -1.4, 3.2)); tip = tworld(t, (-5.5, -5.6, 8.2))   # over her near (starboard) side
        C.tube('derrick', [foot, tip], 0.12, 12, 1.0, C.simple('derrick', '#d9a01c', 0.45, 0.2))
        b, bo = K.lateral_buoy('starboard', topmark=False, light=False, at=(0, 0), scale=0.55)
        bt = tworld(t, (-5.5, -5.6, 0)); b.location = (bt.x, bt.y, 0.9); b.rotation_euler = (deg(12), deg(8), 0)
        bpy.context.view_layer.update(); blo, bhi = K.bbox([o for o in bo if o.type == 'MESH'])
        C.tube('wire', [tip, Vector(((blo.x + bhi.x) / 2, (blo.y + bhi.y) / 2, bhi.z))], 0.02, 6, 1.0, C.simple('wire', '#3a3c3e', 0.4, 0.8))
        foam_patch((bt.x, bt.y, 0.3), 3.5, 2)
    if FIG == 10:    # the trawl warps leading astern into the water
        for side in (-1, 1):
            a = tworld(t, (-15.5, 1.1 + side * 1.6, 2.2)); z = tworld(t, (-45.0, 1.1 + side * 7.0, -WL_T))
            C.tube('warp', [a.lerp(z, s / 8) + Vector((0, 0, -0.6 * math.sin(math.pi * s / 8))) for s in range(9)], 0.03, 6, 1.0, C.simple('warp', '#1a1a1a', 0.6))
    if FIG == 13:    # on a rocky shoal: rocks breaking the surface, white water round her
        rnd = random.Random(5)
        for i in range(14):
            a = rnd.random() * math.tau; r = 9 + rnd.random() * 14
            q = p + Vector((math.cos(a) * r, math.sin(a) * r, -0.35 + rnd.random() * 0.25))
            rock('rock%d' % i, q, 0.9 + rnd.random() * 1.8, i)
            if rnd.random() < 0.8: foam_patch((q.x, q.y, 0.35), 3.0 + rnd.random() * 3.0, i)
        foam_patch((p.x, p.y, 0.3), 14.0, 99)
    bpy.context.view_layer.update(); vlo, vhi = K.bbox([o for o in t.children_recursive if o.type == 'MESH' and not o.hide_render])
    look = Vector(((vlo.x + vhi.x) / 2, (vlo.y + vhi.y) / 2, cs[0].z * 0.42)); lens = 95
    names = {8: 'two black balls', 9: 'ball, diamond, ball', 10: 'two cones, points together', 13: 'three black balls'}
    labels = [(tuple(cs[0] + Vector((0, 0, 1.1))), names[FIG])]
elif FIG == 11:  # a large ship in a buoyed channel, a cylinder at her foremast; we keep out of the channel
    K.sea('breeze'); K.day_sky(sun_az=210, sun_el=38)
    CYL_K = 2.0
    piv, vis, k = ferry((60, 260), heading=250)
    for i in range(5):
        K.lateral_buoy('port', topmark=True, light=False, at=(-40 + i * 95, 175 - i * 30), scale=1.0)
        K.lateral_buoy('starboard', topmark=True, light=False, at=(-10 + i * 95, 345 - i * 30), scale=1.0)
    bpy.context.view_layer.update(); lo, hi = K.bbox(vis)
    mast = max(vis, key=lambda o: K.bbox([o])[1].z); ml, mh = K.bbox([mast])
    top = Vector(((ml.x + mh.x) / 2, (ml.y + mh.y) / 2, mh.z - 0.3))
    cs = hoist(top, ['cylinder'], gap=GAP); SHC = 2.0
    look = cs[0] + Vector((0, 0, -9.0)); lens = 75
    labels = [(tuple(cs[0] + Vector((0, 0, 1.4))), 'cylinder')]
else:            # 12: a yacht motor-sailing, a cone point down forward of her mast, a wake behind her
    K.sea('breeze'); K.day_sky(sun_az=160, sun_el=42)
    p = Vector((math.sin(deg(25)) * 62, math.cos(deg(25)) * 62, 0)) + Vector((eye.x, eye.y, 0))
    o = K.load_yacht(name='other', sails={'main': True, 'genoa': None, 'boom': 18}); o.place(p.x, p.y, heading=290, heel=-4)
    K.wake(o, 40, 9, 1.2)
    top = o.world((6.6, 0.13, 13.2)); cs = hoist(top, ['cone-down'])
    C.tube('halyard-up', [o.world((4.95, 0.13, 13.6)), top], 0.01, 6, 1.0, C.simple('halyard2', '#202224', 0.6))
    look = o.world((4.9, 0.13, 8.5)); lens = 60
    labels = [(tuple(cs[0] + Vector((0, 0, 0.9))), 'cone, point down')]

NOTES = {8: 'Not under command · two balls', 9: 'Restricted in ability to manoeuvre · ball, diamond, ball',
         10: 'Fishing · two cones, points together', 11: 'Constrained by her draught · cylinder',
         12: 'Motor-sailing · cone, point down', 13: 'Aground · three balls'}
cd = bpy.data.cameras.new('cam'); cd.lens = lens; cd.clip_end = 6000
cam = bpy.data.objects.new('cam', cd); C.col.objects.link(cam); bpy.context.scene.camera = cam
cam.location = eye; cam.rotation_euler = (look - eye).to_track_quat('-Z', 'Y').to_euler()
C.focus_on_centre(cam, 11.0)
C.render(OUT, SAMPLES, SCALE, -0.7, labels, NOTES[FIG], space='blender')
