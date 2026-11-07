# Article yachtmaster-offshore/seamanship, its seventeen figures as Blender renders (the 3D half of the before/after).
#   1  working load of a tow line: a bowline in 16 mm nylon over a quay bollard (rope_ring.py, re-routed)    (_b)
#   2  doubled lines in a surge: two bow lines to two bollards, A 6 m, B 12 m, both just taut
#   3  snubber rigged: the nylon hooked onto the chain, the chain slack below the hook (art_checkin_ground 5) (_b)
#   4  scope for a gale: the waterline cut-away in 18 m, 60 m of nylon then 80 m of chain to the anchor
#   5  room to swing: a 24 m yacht at anchor, her 83 m swing circle; a motor yacht lying differently beside her
#   6  anchor watch at 0200: the plotter at the helm, the track an arc, then a straight line away: dragging     (_b)
#   7  two anchors in a V: lying to a SW gale under the land, one anchor towards SW, one towards W
#   8  Bahamian moor: a channel with a reversing stream, an anchor up-stream and one down, the yacht between
#   9  springing off: astern on the stern spring, fender aft, the bow line let go, the bow swinging out
#   10 twin screws: starboard ahead, port astern, the thruster to starboard: she walks sideways
#   11 stern-to in a gusty crosswind: the anchor laid upwind, the chain snubbed, the stern placed on the engines
#   12 the tow at dusk: a watch aft on the line, the tow steering in our wake
#   13 towing lights, tow up to 200 m, from ahead: two masthead lights over the sidelights
#   14 towing lights, tow over 200 m, from ahead: three masthead lights
#   15 towing lights from astern: the yellow towing light over the white sternlight
#   16 hove-to in a gale: jib backed, main eased, helm to leeward, 50° off the wind
#   17 running before the seas: a 24 m motor yacht, the seas overtaking her
#   blender --background --factory-startup --python docs/design/blender/art_yof_seamanship.py -- --fig 2 [--samples 160] [--out x.jpg]
# The plotter screen of figure 6 comes from art_yof_seamanship_tex.py (system Python) into the article's tex/ folder;
# the schematics from art_yof_seamanship_plans.py.
import os, sys, math, random, subprocess, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import bpy, bmesh
from mathutils import Vector, Euler, Matrix, noise as mnoise
import common as C, kit as K, kit_world as KW, kit_night as N

arg = C.cli(); FIG = arg('--fig', 2); SAMPLES = arg('--samples', 160); SCALE = arg('--scale', 100)
ADIR = os.path.join(HERE, '..', 'figure-style', 'articles', 'yachtmaster-offshore', 'seamanship')
OUT = arg('--out', os.path.join(ADIR, f'{FIG}-3d.jpg'))
def deg(a): return math.radians(a)

if FIG in (1, 3):
    exec(compile(open(os.path.join(HERE, 'art_yof_seamanship_b.py')).read(), 'art_yof_seamanship_b.py', 'exec')); sys.exit(0)

def T(name):
    """tex/<name>.png, drawn by art_yof_seamanship_tex.py when missing."""
    d = os.path.join(ADIR, 'tex'); p = os.path.join(d, name + '.png')
    if not os.path.exists(p): subprocess.run(['python3', os.path.join(HERE, 'art_yof_seamanship_tex.py'), d, name], check=True)
    return p
def TA(name): T(name); return json.load(open(os.path.join(ADIR, 'tex', name + '.json')))

# the helpers of art_vhf_scenes.py (yacht without the spinnaker leftovers, sailing/motoring, drone, foam, land,
# plotter on the helm pod, vessels), taken from its source: importing it would run its figure
_src = open(os.path.join(HERE, 'art_vhf_scenes.py')).read()
C.reset()
exec(_src[_src.index('_load = K.load_yacht'):_src.index("if ART == 'channels' and FIG == 7")], globals())
import q_encounter_props as P

labels, arrows, note, extra, expo = [], [], None, {}, -0.6
def V(x, y, z=0.0): return Vector((x, y, z))
def fwd(h): return Vector((math.sin(deg(h)), math.cos(deg(h)), 0.0))
def V3(p): return C.V3((p.x, p.z, -p.y))
def furl(yt): N.cloth_furled(yt)

def dash_line(pts, dash, gap, width, mat, z=0.16, name='dash'):
    """Flat dashes on the water along a polyline (x, y)."""
    Pp = [Vector((p[0], p[1], 0)) for p in pts]; me = C.rbox(name, (dash, width, 0.06), 0.02, 2); me.materials.append(mat)
    for a, b in zip(Pp, Pp[1:]):
        L = (b - a).length; d = (b - a).normalized(); s = dash / 2
        while s < L:
            p = a + d * min(s, L - dash / 2)
            o = bpy.data.objects.new(name, me); C.col.objects.link(o); o.location = (p.x, p.y, z); o.rotation_euler = (0, 0, math.atan2(d.y, d.x)); o.visible_shadow = False
            s += dash + gap

def dash_circle(c, r, dash, gap, width, mat, z=0.16, name='circle'):
    n = max(8, int(2 * math.pi * r / (dash + gap)))
    pts = [(c[0] + r * math.cos(2 * math.pi * k / n), c[1] + r * math.sin(2 * math.pi * k / n)) for k in range(n + 1)]
    me = C.rbox(name, (dash, width, 0.06), 0.02, 2); me.materials.append(mat)
    for k in range(n):
        t = 2 * math.pi * (k + 0.5) / n; o = bpy.data.objects.new(name, me); C.col.objects.link(o)
        o.location = (c[0] + r * math.cos(t), c[1] + r * math.sin(t), z); o.rotation_euler = (0, 0, t + math.pi / 2); o.visible_shadow = False

def buoy(p, color='#ff6a00', r=0.45):
    o = sphere('buoy', r, C.simple('buoy-' + color, color, 0.35, coat=0.5), (p[0], p[1], 0.15)); return Vector((p[0], p[1], r))

def side_y(x, z, start=8.0, toward=-1):
    """The yacht's outboard surface facing +Y at (x, z), by a ray cast down from +Y."""
    bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()
    hit, loc, *_ = bpy.context.scene.ray_cast(dg, Vector((x, start, z)), Vector((0, toward, 0)))
    return loc.y if hit else None

def quay(x0, x1, edge, top=1.15, depth=14.0, name='quay'):
    """A concrete quay along X whose face is at y = edge, the land to the north (+Y), its top `top` m up."""
    m = C.granite_mat(name + '-stone', base='#8e8a82', per_object=False, scale=0.8, dark='#4a4743', light='#b8b3aa')
    C.tbox((x1 - x0, top + 3.0, depth), ((x0 + x1) / 2, top - (top + 3.0) / 2, -(edge + depth / 2)), m, 0.05, 2, name)
    C.tbox((x1 - x0, 0.25, 0.5), ((x0 + x1) / 2, top + 0.0, -(edge + 0.25)), C.granite_mat(name + '-coping', base='#c9c5bd', per_object=False, dark='#5e5b56', light='#e2ded6'), 0.03, 2, name + '-coping')
    return top + 0.125

def bollard(p, top):
    iron = C.iron_mat() if hasattr(C, 'iron_mat') else C.simple('iron', '#26282b', 0.5, 0.6)
    C.cyl('bollard', 0.17, 0.2, 0.5, 24, iron, (p[0], p[1], top + 0.25))
    C.cyl('bollard-cap', 0.24, 0.24, 0.07, 24, iron, (p[0], p[1], top + 0.52))
    return Vector((p[0], p[1], top + 0.3))

def fender(at, r=0.12, h=0.5):
    sock = C.fabric_mat('fender-sock', '#1e2f55', '#5d75a8', 1400.0)
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=r)
    for v in bm.verts: v.co.z += h / 2 if v.co.z > 0 else (-h / 2 if v.co.z < 0 else 0)
    for f in bm.faces: f.smooth = True
    me = bpy.data.meshes.new('fender'); bm.to_mesh(me); bm.free()
    return C.obj('fender', me, sock, tuple(at))

def rope(name, pts, R=0.012, color='navy'):
    """A mooring line: navy braid (reads on pale stone), or laid white nylon. Blender-space points."""
    if color == 'navy': C.braid(name, [V3(Vector(p)) for p in pts], R, '#1b2c4c', '#e9e3d2', whip='#141414', fine=1.4)
    elif color == 'red': C.braid(name, [V3(Vector(p)) for p in pts], R, '#b3161c', '#f2ece0', whip='#141414', fine=1.4)
    else: C.three_strand(name, [V3(Vector(p)) for p in pts], R, R * 6)

def sag(a, b, n, s):
    a, b = Vector(a), Vector(b)
    return [a.lerp(b, i / n) - Vector((0, 0, s * math.sin(math.pi * i / n))) for i in range(n + 1)]

def eye_round(post, r, z, start_dir, n=14):
    """A spliced eye round a post: points round it starting and ending on the side `start_dir` points to."""
    a0 = math.atan2(start_dir.y, start_dir.x)
    return [Vector((post.x + r * math.cos(a0 + 2 * math.pi * k / n), post.y + r * math.sin(a0 + 2 * math.pi * k / n), z)) for k in range(n + 1)]

def foam_ribbon(pts, w0, w1, a0, a1, name='wash', z=0.2):
    """(art_yof_emergency) foam along a path (x, y list, the source last): w0/a0 width and whiteness at the source,
    w1/a1 at the far end; broken foam fading to its edges."""
    P2 = [Vector((x, y, 0)) for x, y in pts]; n = len(P2)
    L = [0.0]
    for i in range(1, n): L.append(L[-1] + (P2[i] - P2[i - 1]).length)
    tot = L[-1]; verts, faces, uvs = [], [], []
    for i, p in enumerate(P2):
        d = (P2[min(n - 1, i + 1)] - P2[max(0, i - 1)]).normalized(); s_ = Vector((d.y, -d.x, 0))
        age = 1 - L[i] / tot; w = w0 + (w1 - w0) * age
        verts += [tuple(p + s_ * w / 2 + Vector((0, 0, z))), tuple(p - s_ * w / 2 + Vector((0, 0, z)))]
    for i in range(n - 1):
        a = 2 * i; faces.append((a, a + 1, a + 3, a + 2))
        age0, age1 = 1 - L[i] / tot, 1 - L[i + 1] / tot
        uvs += [(age0, 0), (age0, 1), (age1, 1), (age1, 0)]
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    me.uv_layers.new(name='UVMap').data.foreach_set('uv', [c for uv in uvs for c in uv])
    m, nt, b, out = C.new_mat(name)
    uvn = C.node(nt, 'ShaderNodeUVMap'); sep = C.node(nt, 'ShaderNodeSeparateXYZ'); C.link(nt, uvn.outputs['UV'], sep.inputs['Vector'])
    fade = C.node(nt, 'ShaderNodeMapRange', in_To_Min=a0, in_To_Max=a1); C.link(nt, sep.outputs['X'], fade.inputs['Value'])
    edge = C.math_(nt, 'MULTIPLY', C.math_(nt, 'MULTIPLY', sep.outputs['Y'], C.math_(nt, 'SUBTRACT', 1.0, sep.outputs['Y'])), 4.0)
    edge = C.math_(nt, 'POWER', edge, 0.6)
    oc = C.obj_coords(nt); nz_ = C.ramp(nt, [(0.35, (0.45, 0.45, 0.45, 1)), (0.65, (1, 1, 1, 1))]); C.link(nt, C.noise(nt, oc, 1.4, 8.0), nz_.inputs['Fac'])
    msk = C.math_(nt, 'MULTIPLY', C.math_(nt, 'MULTIPLY', fade.outputs['Result'], edge), nz_.outputs['Color'])
    C.setin(b, 'Base Color', C.lin('#eef3f4')); C.setin(b, 'Roughness', 0.8)
    tp = C.node(nt, 'ShaderNodeBsdfTransparent'); mx = C.node(nt, 'ShaderNodeMixShader')
    C.link(nt, msk, mx.inputs['Fac']); C.link(nt, tp.outputs[0], mx.inputs[1]); C.link(nt, b.outputs[0], mx.inputs[2]); C.link(nt, mx.outputs[0], out.inputs['Surface'])
    o = C.obj(name, me, m); o.visible_shadow = False
    return o

def wash(src, heading, L, w0, w1, a0=0.9, a1=0.1):
    """Propeller wash or thruster jet: an elongated patch of broken white water from `src` running `L` m towards
    compass `heading` (art_vhf_scenes.foam_patch, stretched along its run)."""
    u = fwd(heading); c = (src[0] + u.x * L * 0.45, src[1] + u.y * L * 0.45); r = w1 / 2
    return foam_patch(c, 0.0, r, r * 1.05, z=0.12, scale=1.6, rot=deg(90 - heading), sx=max(1.0, L / w1 * 0.95), strength=min(1.0, a0 + 0.1))

def motor_yacht(pos, heading, length):
    """q_encounter_props.motor_yacht puts her bow on the opposite of `heading`: turn her round."""
    return P.motor_yacht(pos, (heading + 180) % 360, length)

def yellow(): return flat_mat('swing', '#ffbf00', 0.45)
def inkm(): return flat_mat('rode', '#1b1d20', 0.0, 0.8)

def arrow_mesh(a, b, w, mat, z=0.25, name='flow'):
    """A flat arrow lying on the water from a to b (x, y)."""
    a, b = Vector((a[0], a[1], 0)), Vector((b[0], b[1], 0)); d = (b - a).normalized(); s = Vector((-d.y, d.x, 0)); hl = w * 2.2
    q = b - d * hl
    vs = [a + s * w / 2, q + s * w / 2, q + s * w * 1.3, b, q - s * w * 1.3, q - s * w / 2, a - s * w / 2]
    me = bpy.data.meshes.new(name); me.from_pydata([tuple(v + Vector((0, 0, z))) for v in vs], [], [(0, 1, 5, 6), (2, 3, 4)]); me.update()
    o = C.obj(name, me, mat); o.visible_shadow = False; return o

# ======================================================================================================== figures
if FIG == 2:
    # alongside a quay, port side to; two bow lines from the same cleat: A to a bollard 6 m off, B to one 12 m off
    K.sea('calm', size=30.0, repeat=8); K.day_sky(sun_az=200, sun_el=46)
    y = K.load_yacht(name='alongside'); y.place(1.43, 0.0, heading=90); furl(y)
    out_y = max(v for v in (side_y(x, z) for x in (-2, 1, 4) for z in (0.3, 0.8, 1.3)) if v is not None)
    edge = out_y + 0.28
    top = quay(-30, 40, edge)
    for fx in (-3.0, 1.5, 5.0):
        hy = max(v for v in (side_y(fx, z, start=edge - 0.01) for z in (0.25, 0.45, 0.7)) if v is not None)
        fender((fx, hy + 0.12, 0.45))
    bowc = y.world((8.9, 0.84, 3.58))
    ba = bollard((bowc.x + 4.5, edge + 1.3), top); bb = bollard((bowc.x + 11.4, edge + 1.3), top)
    rail = y.world((9.4, 1.05, 3.85))
    def line(name, b, s):
        col = 'red' if name == 'line-a' else 'navy'
        d = (Vector((bowc.x, bowc.y, 0)) - Vector((b.x, b.y, 0))).normalized()
        eye = eye_round(b, 0.24, b.z - 0.08, d)
        pts = [bowc + V(-0.15, 0, 0.04), bowc + V(0.1, 0.02, 0.05), rail + V(0, 0, 0.04)] + sag(rail + V(0, 0, 0.04), eye[0], 10, s)[1:] + eye[1:]
        rope(name, pts, 0.02, col)
        return pts
    la = line('line-a', ba, 0.05); lb = line('line-b', bb, 0.12)
    c = bowc.lerp(bb, 0.32); c.z = 1.0
    drone(c, 17, 172, 58, 32)
    labels = [(tuple(la[len(la) // 2 - 2] + V(0, 0, 0.35)), 'A: 6 m, takes two-thirds', 'red'), (tuple(lb[len(lb) // 2] + V(0, 0, 0.35)), 'B: 12 m, takes one-third')]
    note = 'Doubled lines in a surge'
    extra = {'lines': ['Make doubled lines the same length']}

elif FIG == 4:
    # a gale on 140 m of rode in 18 m of clear water, from a drone astern: 60 m of nylon from the bow roller down to
    # the join, 80 m of chain on along the sand to the anchor (the rode drawn heavier than life so it reads)
    DEPTH = 18.0
    y = K.load_yacht(); y.place(0, 0, heading=0); KW.antifoul_hull(y); furl(y)
    bow = y.world((10.95, 0.13, 3.72)); sb = -DEPTH + 0.1
    J = Vector((0.0, bow.y + 57.5, -10.8)); L1 = (J - bow).length
    nyl = [bow.lerp(J, i / 40) - Vector((0, 0, 0.9 * math.sin(math.pi * i / 40))) for i in range(41)]
    H = J.z - sb; X = 26.0; a = 10.0
    for _ in range(80):
        f = a * (math.cosh(X / a) - 1) - H; df = (math.cosh(X / a) - 1) - (X / a) * math.sinh(X / a); a -= f / df
    hang_len = a * math.sinh(X / a); lie_len = 80.0 - hang_len
    hang = [Vector((0.0, J.y + (X - x), sb + a * (math.cosh(x / a) - 1))) for x in (X * (1 - i / 120) for i in range(121))]
    touch = hang[-1]
    lie = [Vector((0.8 * math.sin(t * 7) * t, touch.y + lie_len * t, sb)) for t in (i / 120 for i in range(1, 121))]
    print('nylon', round(L1, 1), 'catenary a', round(a, 2), 'hanging', round(hang_len, 1), 'lying', round(lie_len, 1), 'total horiz', round(lie[-1].y - bow.y, 1))
    C.tube('nylon', nyl, 0.11, 12, 1.0, C.simple('nylon', '#f4eedb', 0.6))
    KW.chain(hang + lie, link_len=0.5, wire=0.07)
    C.cyl('shackle', 0.2, 0.2, 0.6, 12, C.simple('shackle', '#9aa0a5', 0.4, 0.8), tuple(J), (deg(90), 0, 0))
    root, objs = K.load_model('anchor-delta.glb', drop_planes=False)
    S = Matrix.Diagonal((2.6, 2.6, 2.6, 1.0)); end = lie[-1]
    root.matrix_world = Matrix.Rotation(deg(180), 4, 'Z') @ S @ Matrix.Translation((-0.48, -1.17, 0.0))
    bpy.context.view_layer.update(); sh = root.matrix_world @ Vector((0.48, 1.17, 0.52))
    root.matrix_world = Matrix.Translation((end.x - sh.x, end.y - sh.y + 0.1, 0)) @ root.matrix_world
    bpy.context.view_layer.update(); alo, ahi = K.bbox(objs); root.location.z += (sb - 0.35) - alo.z
    cy = (bow.y + end.y) / 2
    KW.water_body(depth=DEPTH + 6, size=1600.0, density=0.016, color='#1f8f96', absorb='#3fb0b0', reflect=0.35, absorb_density=0.035, center=(0, cy))
    KW.far_sea_ring(inner=800.0)
    KW.seabed(z=-DEPTH, size=1400.0, res=400, center=(0, cy), colors=('#b29f78', '#c9b88f', '#bba981'))
    KW.stones(50, ((-60, -40), (60, 200)), -DEPTH, scale=(0.3, 1.0))
    KW.seagrass(((-90, 60), (-25, 200)), -DEPTH, clumps=900, length=0.9)
    K.coast(distance=1400, bearing=0, height=90, town=True)
    K.day_sky(sun_az=150, sun_el=62, strength=0.25, haze=2.0)
    KW.camera(Vector((96.0, 22.0, 54.0)), Vector((-4.0, 58.0, -16.0)), lens=22)
    labels = [((bow.x, bow.y + 0.5, bow.z + 1.0), 'bow roller 2 m up'),
              (tuple(nyl[22] + V(0, 0, 1.0)), '60 m nylon'),
              (tuple(lie[70] + V(0, 0, 1.0)), '80 m chain to the anchor, 18 m down', 'blue')]
    note = '(18 + 2) × 7 = 140 m'
    extra = {'lines': ['Gale, chain and rope: scope 7:1 from the roller']}
    expo = -0.55

elif FIG == 5:
    # a 24 m yacht at anchor lying to the north wind, 59 m of chain along the bottom: swing radius 83 m;
    # a motor yacht beside her lies to the stream instead, so the two circles must not overlap
    K.sea('calm', size=40.0, repeat=14, center=(60, -10)); K.day_sky(sun_az=200, sun_el=52)
    yt = K.load_yacht(name='you'); yt.root.scale = (1.6,) * 3
    stem_off = (10.8 - K.MAST.x) * 1.6
    yt.place(0.0, -59.0 - stem_off, heading=0); furl(yt)
    yl = yellow(); ink = inkm()
    dash_circle((0, 0), 83.0, 6.0, 4.0, 1.4, yl, name='swing')
    dash_line([(0, -59.0), (0, -1.0)], 2.4, 1.6, 0.5, ink, name='rode')
    buoy((0, 0))
    A2 = Vector((133.0, -8.0, 0)); R2 = 50.0
    spin, vis, tp = motor_yacht((A2.x - 30.0, A2.y), 90, 17.0)
    bpy.context.view_layer.update(); mlo, mhi = K.bbox(vis)
    dash_circle((A2.x, A2.y), R2, 6.0, 4.0, 1.4, flat_mat('swing2', '#ff8a3d', 0.45), name='swing2')
    dash_line([(mhi.x + 0.5, A2.y), (A2.x - 1.0, A2.y)], 2.4, 1.6, 0.5, ink, name='rode2')
    buoy((A2.x, A2.y))
    drone((62, -8, 0), 305, 192, 68, 30)
    labels = [((-83.0, 0, 2), 'swing radius 83 m', 'blue'), ((0, -30, 2), 'chain on the bottom ≈ 59 m'),
              (tuple(yt.world((K.MAST.x, K.MAST.y, 12.0))), '24 m of yacht'),
              ((A2.x, A2.y + R2, 2), 'lying differently: add both radii', 'yellow')]
    note = 'Room to swing'
    extra = {'lines': ['√(60² − 12²) ≈ 59 m + 24 m = 83 m']}

elif FIG == 7:
    # lying to a SW gale under the land, heading 247; one anchor out towards SW, one towards W, rodes in a V
    K.sea('breeze', size=36.0, repeat=12, center=(-30, -20)); K.day_sky(sun_az=160, sun_el=30, strength=0.2, haze=2.4)
    y = K.load_yacht(name='you').place(0, 0, heading=247, heel=0); furl(y)
    bow = y.world((10.9, 0.13, 2.0)); bow.z = 0
    a_sw = bow + fwd(225) * 52; a_w = bow + fwd(272) * 50
    ink = inkm()
    dash_line([(bow.x, bow.y), (a_sw.x, a_sw.y)], 2.2, 1.4, 0.45, ink); dash_line([(bow.x, bow.y), (a_w.x, a_w.y)], 2.2, 1.4, 0.45, ink)
    buoy(a_sw); buoy(a_w)
    K.coast(distance=230, bearing=250, length=3000, height=70, town=False)
    c = bow + fwd(247) * 22
    drone((c.x, c.y, 6.0), 100, 100, 17, 30)
    w0 = bow + fwd(170) * 38 + V(0, 0, 9); w1 = w0 + fwd(45) * 20
    arrows = [(tuple(w0), tuple(w1), 'red')]
    labels = [(tuple(a_sw + V(0, 0, 2)), 'anchor towards SW'), (tuple(a_w + V(0, 0, 2)), 'anchor towards W'),
              (tuple(w1 + V(0, 0, 2.5)), 'gale SW 8, veering W', 'red')]
    note = 'Two anchors in a V across the shift'
    extra = {'lines': ['Each takes its share as the wind veers']}

elif FIG == 8:
    # a channel 110 m wide running east-west; the flood runs east. First anchor up-stream (west), the yacht
    # dropped back twice the scope, second anchor, hove back to the middle: both rodes to a swivel at her bow
    K.sea('calm', size=30.0, repeat=14); K.day_sky(sun_az=200, sun_el=50)
    def bank(x, yy):
        d = abs(yy) - 58 - 6 * math.sin(x / 47) - 3 * math.sin(x / 13)
        return max(-3.0, min(9.0, d * 0.28)) + 1.5 * nz(x, yy, 0.03, 2.0) * min(1, max(0, d / 10))
    heightfield('banks', bank, -320, 320, -260, 260, 3.0, land_mat())
    y = K.load_yacht(name='you').place(0, 0, heading=270); furl(y)
    bow = y.world((10.9, 0.13, 2.0)); bow.z = 0
    A1 = V(-80, 0); A2 = V(80, 0); ink = inkm()
    dash_line([(bow.x, bow.y), (A1.x, A1.y)], 2.6, 1.6, 0.8, ink); dash_line([(bow.x + 14, 0.0), (A2.x, A2.y)], 2.6, 1.6, 0.8, ink)
    buoy(A1, r=0.9); buoy(A2, r=0.9)
    sphere('swivel-mark', 0.35, C.simple('swivel', '#c8ccd0', 0.3, 0.9), (bow.x - 1.2, bow.y, 0.2))
    drone((0, -4, 0), 150, 170, 48, 30)
    arrows = [((-48, -26, 3), (-12, -26, 3), 'blue'), ((22, 26, 3), (58, 26, 3), 'blue')]
    labels = [(tuple(A1 + V(0, 0, 2)), 'first anchor, up-stream'), (tuple(A2 + V(0, 0, 2)), 'second anchor'),
              (tuple(bow + V(0, 0, 4)), 'swivel joins the rodes', 'blue'), ((-30, -26, 5), 'flood', 'blue')]
    note = 'Bahamian moor: in line with the stream'
    extra = {'lines': ['Weigh the slack anchor first']}

elif FIG == 9:
    # springing off a quay, port side to: motoring slow astern against the stern spring, a fender at the quarter;
    # the stern holds, the bow swings out. The bow line has been let go.
    K.sea('calm', size=30.0, repeat=8); K.day_sky(sun_az=200, sun_el=46)
    y = K.load_yacht(name='you'); y.place(0, 0, heading=122); furl(y)
    bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()
    q = y.world((-2.2, K.MAST.y + 2.05, 2.5))                 # port quarter, near the rubbing strake
    hits = [bpy.context.scene.ray_cast(dg, Vector((x, 30.0, 1.4)), Vector((0, -1, 0))) for x in (-5.0, -4.0, -3.0)]
    hy = max(h[1].y for h in hits if h[0]); edge = hy + 0.3
    top = quay(-34, 34, edge)
    fq = y.world((-1.6, K.MAST.y + 2.2, 2.4)); fender((fq.x, edge - 0.13, 0.5))
    qc = y.world((-1.46, 2.05, 3.58)); b1 = bollard((qc.x + 7.5, edge + 0.7), top)
    d = (Vector((qc.x, qc.y, 0)) - Vector((b1.x, b1.y, 0))).normalized()
    eye = eye_round(b1, 0.24, b1.z - 0.08, d)
    sp = [qc + V(-0.1, 0, 0.04), qc + V(0.15, 0.05, 0.05), qc + V(0.25, 0.4, 0.15)] + sag(qc + V(0.25, 0.4, 0.15), eye[0], 10, 0.05)[1:] + eye[1:]
    rope('stern-spring', sp, 0.02, 'red')
    # the bow line, let go from the quay: off the bow cleat, over the rail and trailing in the water
    bc = y.world((8.9, 0.84, 3.58)); br = y.world((9.6, 1.0, 3.85))
    tail = [br + V(0, 0, 0.05), br + V(0.2, 0.6, -0.8), br + V(0.6, 1.6, -br.z + 0.05), br + V(2.2, 2.0, 0.03 - br.z), br + V(3.6, 1.6, 0.03 - br.z), br + V(4.6, 2.4, 0.03 - br.z)]
    rope('bow-line', [bc + V(-0.15, 0, 0.04), bc + V(0.1, 0, 0.05)] + tail, 0.02)
    st = y.world((-3.6, K.MAST.y, 2.0)); fwd_ = fwd(122)
    foam_patch((st.x + fwd_.x * 3.5, st.y + fwd_.y * 3.5), 0.0, 2.6, 4, scale=2.0, sx=1.6, rot=deg(90 - 122), strength=0.6)
    stem = y.world((10.6, K.MAST.y, 3.8))
    c = y.world((3.0, K.MAST.y, 1.5))
    drone(c + V(0, 2.0, 0), 25, 196, 64, 32)
    arrows = [(tuple(stem + V(0.6, 1.2, 1.0)), tuple(stem + V(1.8, -2.6, 1.0)), 'blue')]
    labels = [(tuple(sp[len(sp) // 2 - 3] + V(0, 0, 0.4)), 'stern spring'), (tuple(V(fq.x, edge - 0.13, 0.9)), 'fender aft'),
              (tuple(br + V(2.2, 2.0, 0.6 - br.z)), 'bow line: let go'), (tuple(st + V(-1.0, -1.5, 0.3)), 'engine slow astern', 'blue')]
    note = 'Astern on the spring: the bow swings out'

elif FIG == 10:
    # a 16 m twin-screw motor yacht: starboard engine ahead, port astern, the bow thruster to starboard; the stern
    # and the bow both go to starboard and she walks sideways onto the pontoon
    K.sea('calm', size=30.0, repeat=8); K.day_sky(sun_az=210, sun_el=48)
    spin, vis, tp = motor_yacht((0, 0), 0, 16.0)
    bpy.context.view_layer.update(); lo, hi = K.bbox(vis)
    cx = (lo.x + hi.x) / 2; bw = (hi.x - lo.x) / 2
    px = (hi.x - lo.x) * 0.22
    wash((cx + px, lo.y + 1.2), 180, 15.0, 1.4, 4.5)                   # starboard ahead: wash aft
    wash((cx - bw - 0.5, lo.y + 2.4), 0, 8.0, 1.2, 3.2)                # port astern: wash thrown forward along her side
    wash((cx - bw + 0.1, hi.y - 2.4), 270, 6.0, 0.9, 3.0)              # thruster: water thrown out to port
    pz = hi.x + 7.0
    C.tbox((2.4, 0.6, 40), (pz + 1.2, 0.2, 0.0), K.mats()['float'], 0.08, 2, 'pontoon')
    pl = C.rbox('plank', (2.4, 0.035, 0.14), 0.004, 1); pl.materials.append(K.mats()['planks'])
    for k in range(240):
        o = bpy.data.objects.new('plank', pl); C.col.objects.link(o); o.location = (pz + 1.2, -18.0 + k * 0.155, 0.52)
    cc = Vector((cx + 2.5, (lo.y + hi.y) / 2 - 2.0, 0))
    drone(cc, 37, 200, 60, 32)
    arrows = [((cx + bw + 0.6, -3.0, 2.5), (pz - 0.5, -3.0, 2.5), 'blue'), ((cx + bw + 0.6, 4.0, 2.5), (pz - 0.5, 4.0, 2.5), 'blue')]
    labels = [((cx + px + 0.8, lo.y - 4.0, 0.5), 'starboard engine ahead', 'green'), ((cx - bw - 0.9, lo.y + 5.0, 0.5), 'port engine astern', 'red'),
              ((cx - bw - 3.0, hi.y - 2.2, 0.8), 'thruster to starboard'), ((pz - 2.0, 0.5, 4.0), 'she walks sideways', 'blue')]
    note = 'Starboard ahead, port astern, thruster to starboard'

elif FIG == 11:
    # stern-to on a town quay with a crosswind gusting 26 kn from the west: our 16 m motor yacht between two
    # yachts, her anchor laid out upwind to the south-west and the chain snubbed, the engines placing the stern
    K.sea('breeze', size=36.0, repeat=10, center=(0, -40)); K.day_sky(sun_az=200, sun_el=44)
    top = quay(-60, 60, 0.0)
    KW.town(cx=0, width=160, depth=60, n=60) if False else None
    spin, vis, tp = motor_yacht((0, -10), 180, 16.0)
    bpy.context.view_layer.update(); lo, hi = K.bbox(vis); spin.location.y += (-1.2 - hi.y); bpy.context.view_layer.update(); lo, hi = K.bbox(vis)
    nb = []
    for k, x in enumerate((-6.6, 6.6, 12.4)):
        yt = K.load_yacht(name=f'nb{k}'); furl(yt)
        yt.place(x, -1.2 - (K.MAST.x + 3.8), heading=180); nb.append(yt)
    ink = inkm()
    bowp = Vector(((lo.x + hi.x) / 2, lo.y, 0)); anc = Vector((-26.0, -62.0, 0))
    dash_line([(bowp.x, bowp.y), (anc.x, anc.y)], 2.2, 1.4, 0.7, ink); buoy(anc, r=0.7)
    for k, x in enumerate((-1.5, 1.5)):
        st = V(x * 0.8 + (lo.x + hi.x) / 2, hi.y - 0.2, top)
        rope(f'stern-line{k}', sag(V(x + (lo.x + hi.x) / 2, hi.y - 0.6, 1.3), V(x * 2.2 + (lo.x + hi.x) / 2, 1.0, top + 0.05), 8, 0.12), 0.011)
    for x in (-3.3, 3.3, 9.5, 15.3, -9.9):
        bollard((x, 0.7), top)
    cc = Vector(((lo.x + hi.x) / 2 - 8, -20, 0))
    drone(cc, 70, 196, 42, 30)
    arrows = [((-36, -12, 5), (-14, -12, 5), 'red'), ((-36, -22, 5), (-14, -22, 5), 'red')]
    labels = [((-30, -12, 7), 'gusts 26 kn on the beam', 'red'), (tuple(bowp.lerp(anc, 0.55) + V(0, 0, 1.5)), 'anchor upwind, chain snubbed', 'blue'),
              (tuple(V(hi.x, hi.y - 4.0, hi.z * 0.6)), 'engines place the stern')]
    note = 'Stern-to in a gusty crosswind'
    extra = {'lines': ['Bow windage ≈ 270 kgf: more than the 160 kgf thruster']}

elif FIG == 12:
    # dusk: our yacht motoring north, towing another on a long nylon line to a bridle on her bow; one of the crew on
    # watch at our stern beside the line, a knife at hand
    K.sea('breeze', size=40.0, repeat=12, center=(0, -40)); K.day_sky(sun_az=250, sun_el=4.0, strength=0.22, haze=2.6)
    L = 52.0
    you = K.load_yacht(name='you').place(0, 0, heading=0); furl(you)
    tow = K.load_yacht(name='tow', hull='navy').place(0, -L - 14.6, heading=4); furl(tow)
    K.wake(you, 40, 9, 0.9); K.wake(tow, 24, 6, 0.5)
    bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()
    def deck(yt, mx, my):
        p = yt.world((mx, my, 8.0)); hit, loc, *_ = bpy.context.scene.ray_cast(dg, p, Vector((0, 0, -1)))
        return loc if hit else yt.world((mx, my, 3.6))
    stern = deck(you, -3.2, K.MAST.y) + V(0, 0, 0.15)
    bl = deck(tow, 9.0, K.MAST.y + 0.75) + V(0, 0, 0.08); br = deck(tow, 9.0, K.MAST.y - 0.75) + V(0, 0, 0.08)
    stem = tow.world((10.7, K.MAST.y, 4.0)); apex = stem + V(0, 4.0, -1.4)
    lp = sag(stern, apex, 16, 1.3)
    C.three_strand('towline', [V3(p) for p in lp], 0.014, 0.08)
    for nm, cl in (('bridle-l', bl), ('bridle-r', br)):
        C.three_strand(nm, [V3(p) for p in [cl, cl.lerp(stem, 0.6) + V(0, 0, 0.05), stem + V(0, 0.3, 0) + (cl - stem) * 0.1, apex]], 0.012, 0.07)
    watch = deck(you, -2.2, K.MAST.y + 0.7)
    head = P.person(watch, 180, 'down', top='#c0392b', sit=True)
    # navigation lights: ours (sidelights, sternlight, the yellow towing light over it), the tow's sidelights and sternlight
    N.light('own-stern', you.world((-3.75, 0.13, 4.3)), 'white', strength=6.0, power=3.0, radius=0.06)
    N.light('own-towing', you.world((-3.75, 0.13, 4.75)), 'yellow', strength=2.0, power=3.0, radius=0.06)
    N.yacht_lights(tow, sidelights=True, stern=True)
    c = stern.lerp(stem, 0.45); c.z = 1.5
    drone(c, 88, 236, 25, 32)
    labels = [(tuple(head + V(0, 0, 0.3)), 'watch aft, knife to hand', 'blue'), (tuple(lp[5] + V(0, 0, 1.2)), 'check for chafe hourly'),
              (tuple(tow.world((K.MAST.x, K.MAST.y, 13.0))), 'tow steers in our wake')]
    note = 'Night orders for the tow'
    extra = {'bloom': 0.6}; expo = -0.15

elif FIG in (13, 14, 15):
    # night: a tug towing a yacht. From ahead (13: tow up to 200 m, two masthead lights; 14: over 200 m, three), her
    # sidelights, the tow's sidelights beyond; from astern (15): her yellow towing light over the white sternlight,
    # the tow's sternlight nearer. Only the lights a viewer there would see are lit.
    N.night_scene('calm', moon=0.004)
    dist = {13: 150.0, 14: 300.0, 15: 150.0}[FIG]; ahead = FIG in (13, 14)
    lt = N.ship((0, 0, 0), 0.0, lights=('masthead', 'red', 'green', 'stern'))
    hide_ = ('ship-stern', 'ship-masthead') if ahead else ('ship-masthead', 'ship-red', 'ship-green', 'ship-stern')
    for o in bpy.data.objects:
        if o.name.startswith(hide_): o.hide_render = True
    stern_p = lt['stern'] + V(0, -0.5, 0.6)
    mh = lt['masthead'] + V(0, 0, 1.2); extra_mh = []
    if ahead:                                        # her masthead lights in a vertical line, 2 m apart, over the sidelights
        for k in range(2 if FIG == 13 else 3):
            p = mh + V(0, 0, 2.0 * k); N.light(f'ship-mh{k}', p, 'white', strength=9.0, power=40.0, radius=0.45); extra_mh.append(p)
    tl = stern_p + V(0, 0, 2.0)
    if not ahead:
        N.light('ship-towing', tl, 'yellow', strength=2.2, power=40.0, radius=0.45); N.light('ship-sternlt', stern_p, 'white', strength=9.0, power=40.0, radius=0.45)
    tow = K.load_yacht(name='tow', hull='navy').place(stern_p.x, stern_p.y - dist - 5.0, heading=0.0); furl(tow)
    dark = C.simple('tow-night', '#2a2e33', 0.6)
    for o in tow.objs:
        if o.type == 'MESH':
            for sl in o.material_slots: sl.material = dark
    tlts = N.yacht_lights(tow, sidelights=ahead, stern=not ahead)
    tw = tow.world((10.7, K.MAST.y, 3.9))
    C.tube('towline', sag(stern_p + V(0, 0, -1.0), tw, 40, 2.0), 0.05, 8, 1.0, C.simple('towline-night', '#3a3d40', 0.7))
    if ahead:
        brg = 6.0 if FIG == 13 else 4.0; R = 520.0          # we are fine on her starboard bow
        eye = V(math.sin(deg(brg)) * R, math.cos(deg(brg)) * R + 20, 3.0)
        look = V(0, -dist * 0.45, 6.0)
        K.camera(tuple(eye), tuple(look), 260 if FIG == 13 else 200)
        top_ = max([mh] + extra_mh, key=lambda p: p.z)
        labels = [(tuple(top_ + V(0, 0, 1.2)), 'two masthead lights: tow up to 200 m' if FIG == 13 else 'three masthead lights: tow over 200 m'),
                  (tuple(lt['green'] + V(0, 0, 0.6)), 'sidelights', 'green'),
                  (tuple(tlts['green'] + V(0, 0, 1.5)), 'the tow', 'blue')]
        note = 'Towing, seen from ahead'
    else:
        brg = 176.0; R = 420.0
        eye = V(math.sin(deg(brg)) * R, math.cos(deg(brg)) * R + stern_p.y, 3.0)
        look = V(0, stern_p.y - dist * 0.45, 3.5)
        K.camera(tuple(eye), tuple(look), 170)
        labels = [(tuple(tl + V(0, 0, 1.2)), 'yellow towing light over the sternlight', 'yellow'),
                  (tuple(tlts['stern'] + V(0, 0, 1.0)), "the tow's sternlight", 'blue')]
        note = 'Towing, seen from astern'
    bpy.context.scene.camera.data.clip_end = 5000
    extra = {'bloom': 1.3}; expo = -0.3

elif FIG == 16:
    # hove-to on port tack in a gale from the north: heading 050, the jib backed to port (windward), the main eased
    # to starboard, the helm to leeward; she lies quiet, drifting slowly to leeward, a slick to windward
    K.sea('fresh', size=48.0, repeat=10); K.day_sky(sun_az=230, sun_el=22, strength=0.18, haze=3.0)
    y = K.load_yacht(name='you', sails={'main': True, 'genoa': 'port', 'boom': -24}).place(0, 0, heading=50, heel=7)
    c = y.world((3.0, K.MAST.y, 6.0))
    drone(c, 44, 268, 22, 32)
    w0 = c + V(-4, 16, 9); w1 = w0 + V(0, -11, 0)
    arrows = [(tuple(w0), tuple(w1), 'red')]
    labels = [(tuple(y.world((7.6, K.MAST.y + 1.4, 9.0))), 'jib backed to windward', 'blue'), (tuple(y.world((1.0, K.MAST.y - 2.3, 12.0))), 'main eased'),
              (tuple(y.world((-3.4, K.MAST.y, 5.2))), 'helm to leeward'), (tuple(w0 + V(0, 0, 2.5)), 'Wind', 'red')]
    note = 'Hove-to, 50° off the wind'
    extra = {'lines': ['Forereaching? Ease the main']}

elif FIG == 17:
    # a 24 m motor yacht running before a 6-second sea: the crests run at 18 kn, she can make 11: they overtake her
    hd = 60.0
    o = K.sea('fresh', size=90.0, repeat=8)
    md = o.modifiers['ocean']; md.wave_scale = 2.2; md.wind_velocity = 18.0; md.wave_alignment = 0.9; md.choppiness = 1.0; md.spatial_size = 90
    md.wave_direction = deg(90 - hd)
    K.day_sky(sun_az=200, sun_el=28, strength=0.2, haze=2.6)
    spin, vis, tp = motor_yacht((0, 0), hd, 24.0)
    spin.location.z -= 0.2
    bpy.context.view_layer.update(); lo, hi = K.bbox(vis)
    K.wake if False else None
    wash((-fwd(hd).x * 11, -fwd(hd).y * 11), hd + 180, 45.0, 3.0, 12.0, 0.7, 0.05)
    c = Vector((0, 0, 2.5))
    eye = c - fwd(hd) * 58 + fwd(hd + 90) * 30 + V(0, 0, 13)
    K.camera(tuple(eye), tuple(c + fwd(hd) * 6), 30)
    crest = c - fwd(hd) * 34 + fwd(hd + 90) * 6; crest.z = 2.0
    labels = [(tuple(crest), 'seas 18 kn, period 6 s', 'blue'), (tuple(tp + V(0, 0, 1.5)), 'she makes 11 kn at most')]
    note = 'Can she run with the seas?'
    extra = {'lines': ['She cannot keep up: slow down, let them pass under her']}

elif FIG == 6:
    # 0200 at the helm: the plotter on the pod showing the track since 2200; an arc while she swung, then a straight
    # line away downwind since the wind shifted: dragging
    png = T('drag'); A = TA('drag')
    you = K.load_yacht(name='you').place(0, 0, heading=0); furl(you)
    N.night_scene('breeze', moon=0.003)
    N.our_lights(you, steaming=False)
    light_ = bpy.data.lights.new('anchor-light', 'POINT'); light_.energy = 3.0; light_.color = (1.0, 0.92, 0.8)
    lo_ = bpy.data.objects.new('anchor-light', light_); C.col.objects.link(lo_); lo_.location = you.world((K.MAST.x, K.MAST.y, 21.0))
    objs, scr = plotter(you, png)
    for m in bpy.data.materials:
        if m.name.startswith('axiom-screen'):
            b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'); b.inputs['Emission Strength'].default_value = 0.55
    ld = bpy.data.lights.new('red-night', 'AREA'); ld.energy = 14.0; ld.size = 0.6; ld.color = (1.0, 0.2, 0.1)
    rl = bpy.data.objects.new('red-night', ld); C.col.objects.link(rl)
    bpy.context.view_layer.update(); plo, phi = K.bbox([o for o in objs if o.type == 'MESH'])
    pc = (plo + phi) / 2
    rl.location = pc + V(0.7, -0.8, 0.5); rl.rotation_euler = (pc - rl.location).to_track_quat('-Z', 'Y').to_euler()
    K.camera(tuple(pc + V(0.03, -0.34, 0.16)), tuple(pc + V(0.0, 0.0, 0.012)), 40)
    sp = lambda k: tuple(screen_point(scr, *A[k]))
    labels = [(sp('arc'), 'arc: swinging', 'blue'), (sp('drag'), 'straight: dragging', 'red')]
    note = 'Plotter, 0200 · wind shifted at 0130'
    extra = {'lines': ['Track since 2200'], 'bloom': 0.4}; expo = -0.3

else:
    raise SystemExit(f'no figure {FIG}')

C.render(OUT, SAMPLES, SCALE, expo, labels, note, space='blender', arrows=arrows, extra=extra)
