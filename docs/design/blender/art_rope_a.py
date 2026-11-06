# Ropework article (bareboat-skipper/ropework), figures 1, 6, 8 and 9 in Blender:
#   --fig 1   an eye splice on a galvanised thimble, shackled to a ring bolt on the quay (close-up)
#   --fig 6   a slip line: from the yacht's stern cleat round a quay bollard and back to the same cleat
#   --fig 8   the snap-back zone of a bar-tight mooring line, and where to stand
#   --fig 9   a halyard made fast on the mast cleat, its coil hung from the cleat
# Blender space, Z up, the sea at z = 0. Without --out it writes into the article folder.
#   blender --background --factory-startup --python docs/design/blender/art_rope_a.py -- --fig 6
import os, sys, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
from mathutils import Vector
import common as C, kit as K

arg = C.cli(); FIG = arg('--fig', 6); SAMPLES = arg('--samples', 192); SCALE = arg('--scale', 100)
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = arg('--out', os.path.join(HERE, '..', 'figure-style', 'articles', 'bareboat-skipper', 'ropework', f'{FIG}-3d.jpg'))
random.seed(7); rnd = random.random
QZ = 1.0                     # quay top above the water

def V(x, y, z): return Vector((x, y, z))
def T3(P): return [C.V3((p.x, p.z, -p.y)) for p in P]          # Blender points -> the Three.js points common.* takes

# ---------- materials ----------
def galv():
    m = C.galv_mat('galv-steel'); return m

# ---------- rope with a varying radius (for the splice) ----------
def strand_rope(name, P0, Rf, lay=0.06, tracer=True, core=True):
    """A three-strand rope along Blender points P0 whose radius follows Rf(t), t 0..1 along it."""
    dense = C.catmull_centripetal(P0, 24)
    L = sum((b - a).length for a, b in zip(dense, dense[1:]))
    n = max(8, math.ceil(L / min(0.002, lay / 32)))
    P, L = C.spaced(dense, n)
    T, N, Bn = C.frames(P, Vector((0, 0, 1)))
    mats = [C.rope_mat(f'{name}-yarn{k}', tracer=(tracer and k == 0)) for k in range(3)]
    for k in range(3):
        Q = []
        for i, p in enumerate(P):
            R = Rf(i / n); th = (i / n) * L / lay * math.tau + k * math.tau / 3
            Q.append(p + N[i] * (math.cos(th) * R * 0.56) + Bn[i] * (math.sin(th) * R * 0.56))
        # per-point radius: build the strand tube by hand
        _tube_var(f'{name}-s{k}', Q, [Rf(i / n) * 0.52 for i in range(len(Q))], mats[k])
    if core: _tube_var(f'{name}-core', P, [Rf(i / n) * 0.5 for i in range(len(P))], C.simple('rope-core', '#7d7466', 1.0))
    return P

def _tube_var(name, P, radii, mat, radial=12, uv_len=0.03):
    T, N, Bn = C.frames(P, Vector((0, 0, 1)))
    verts, faces, uvs, s = [], [], [], [0.0]
    for i in range(1, len(P)): s.append(s[-1] + (P[i] - P[i - 1]).length)
    for i, p in enumerate(P):
        for j in range(radial):
            a = j / radial * math.tau; verts.append(p + (N[i] * math.cos(a) + Bn[i] * math.sin(a)) * radii[i])
    for i in range(len(P) - 1):
        for j in range(radial):
            a, b = i * radial + j, i * radial + (j + 1) % radial
            faces.append((a, b, b + radial, a + radial))
            uvs += [(s[i] / uv_len, j / radial), (s[i] / uv_len, (j + 1) / radial), (s[i + 1] / uv_len, (j + 1) / radial), (s[i + 1] / uv_len, j / radial)]
    me = bpy.data.meshes.new(name); me.from_pydata([tuple(v) for v in verts], [], faces); me.update()
    lay = me.uv_layers.new(name='UVMap'); lay.data.foreach_set('uv', [c for uv in uvs for c in uv]); me.shade_smooth()
    return C.obj(name, me, mat)

def tubeP(name, P, r, mat, radial=16):
    return C.tube(name, [Vector(p) for p in P], r, radial, 1.0, mat)

# ---------- quay ----------
def quay(x0=-7.0, x1=7.0, depth=6.0, sett_rows=True):
    """A granite quay: its edge along y = 0 facing the water (-y), top at QZ, coping stones on the edge, setts behind."""
    coping = C.granite_mat('coping', base='#b3afa7', per_object=False, scale=0.8, dark='#3d3b38', light='#dedad3')
    x = x0
    while x < x1:
        o = C.obj('coping', C.rbox('coping', (0.9, 0.52, 0.3), 0.03, 4), coping, V(x + 0.45 + (rnd() - 0.5) * 0.01, 0.26, QZ - 0.15))
        o.rotation_euler.z = (rnd() - 0.5) * 0.01; x += 0.92
    wall = C.granite_mat('wall', base='#6f6a61', per_object=False, scale=0.5)
    C.obj('wall', C.rbox('wall', (x1 - x0, 0.2, QZ + 1.6), 0.0, 1), wall, V((x0 + x1) / 2, 0.1, (QZ - 1.6) / 2))
    stone = C.granite_mat('setts', per_object=True, dark='#8a857d', light='#c8c3ba', scale=1.3)
    sett = C.rbox('sett', (0.2, 0.11, 0.09), 0.014, 3); sett.materials.append(stone)
    y = 0.58; row = 0
    while y < depth and sett_rows:
        x = x0 + (0.11 if row % 2 else 0)
        while x < x1:
            o = bpy.data.objects.new('sett', sett); C.col.objects.link(o)
            o.location = V(x + (rnd() - 0.5) * 0.01, y + (rnd() - 0.5) * 0.008, QZ - 0.035 + (rnd() - 0.5) * 0.006)
            o.rotation_euler = ((rnd() - 0.5) * 0.04, (rnd() - 0.5) * 0.04, (rnd() - 0.5) * 0.06); x += 0.212
        y += 0.122; row += 1
    jm = bpy.data.meshes.new('joint'); jm.from_pydata([(x0, 0.5, 0), (x1, 0.5, 0), (x1, depth, 0), (x0, depth, 0)], [], [(0, 1, 2, 3)])
    C.obj('joint', jm, C.joint_mat(), V(0, 0, QZ - 0.035))

PROF = [(0, 0), (0.225, 0), (0.232, 0.012), (0.229, 0.032), (0.214, 0.044), (0.16, 0.048), (0.132, 0.058), (0.122, 0.085), (0.114, 0.16), (0.11, 0.23), (0.113, 0.3), (0.12, 0.345), (0.135, 0.372), (0.172, 0.382), (0.18, 0.395), (0.177, 0.41), (0.162, 0.42), (0.125, 0.442), (0.07, 0.458), (0, 0.462)]
def bollard(x, y):
    o = C.lathe('bollard', PROF, 96, C.iron_mat()); o.location = V(x, y, QZ)
    return V(x, y, QZ)

# ---------- yacht stern-to ----------
def yacht_stern_to(gap=1.3, x=0.0):
    y = K.load_yacht(name='yacht'); y.place(x, -(8.73 + gap), heading=180)
    bpy.context.view_layer.update()
    return y

def deck_z(xw, yw):
    dg = bpy.context.evaluated_depsgraph_get()
    hit, loc, *_ = bpy.context.scene.ray_cast(dg, V(xw, yw, 12), V(0, 0, -1))
    return loc.z if hit else None

def stern_cleat(y, side):
    """A deck cleat on the aft quarter (side +1 port, -1 starboard), placed on the deck found by a ray cast."""
    p = y.world((-3.25, 0.13 + side * 1.45, 6.0)); z = deck_z(p.x, p.y)
    base = V(p.x, p.y, z)
    cm = C.simple('cleat-steel', '#cfd2d4', 0.22, 1.0)
    bar = C.cyl('cleat-horns', 0.013, 0.013, 0.2, 24, cm, base + V(0, 0, 0.055), (0, math.pi / 2, 0))   # along world x = fore-aft
    for dx in (-0.045, 0.045): C.cyl('cleat-leg', 0.014, 0.018, 0.05, 20, cm, base + V(dx, 0, 0.027))
    return base + V(0, 0, 0.055)

# ---------- labels / render ----------
def finish(labels, note, eye, look, lens, fstop=11.0, arrows=(), exposure=-0.7):
    cam = K.camera(eye, look, lens); C.focus_on_centre(cam, fstop)
    C.render(OUT, SAMPLES, SCALE, exposure, labels, note, space='blender', arrows=arrows)

def catenary(a, b, sag, n=24):
    return [a.lerp(b, i / n) - V(0, 0, sag * math.sin(math.pi * i / n)) for i in range(n + 1)]

C.reset()
if FIG == 1:
    # ---------------- eye splice on a thimble, shackled to a ring bolt ----------------
    QZ = 0.0
    slab = C.granite_mat('slab', base='#a9a59d', per_object=False, scale=2.2, dark='#5a5853', light='#d6d2ca')
    C.obj('slab', C.rbox('slab', (1.6, 1.2, 0.3), 0.02, 3), slab, V(-0.05, 0.8, -0.15))
    R = 0.009; zr = R + 0.004
    # thimble: a teardrop, its point towards the throat (+x), lying flat
    def tear(scale_out=0.0, z=zr, n=64):
        pts = []
        for i in range(n + 1):
            a = i / n * math.tau
            # teardrop: round end at -x, point at +x
            x = -0.045 * math.cos(a) + 0.018 * (1 - math.cos(a)) ** 1.6 * 0.6
            yy = 0.034 * math.sin(a) * (1 - 0.55 * (1 - math.cos(a)) / 2)
            c = V(x - 0.20, yy + 0.8, z)
            out = V(x + 0.045, yy, 0); out = out.normalized() if out.length else V(1, 0, 0)
            pts.append(c + out * scale_out)
        return pts
    gm = C.galv_mat('thimble-galv')
    tubeP('thimble-groove', tear(-R - 0.002, zr), 0.0065, gm)
    for dz in (-R * 0.95, R * 0.95): tubeP('thimble-flange', tear(-R * 0.35, zr + dz), 0.0032, gm)
    # the eye: rope round the thimble groove, both legs meeting at the throat and laid side by side into the splice
    eye = tear(0.0, zr)
    k0 = min(range(len(eye)), key=lambda i: abs(eye[i].x - eye[0].x))
    throat = V(-0.135, 0.8, zr)
    eye_path = [throat + V(0, -0.012, 0)] + [p for p in eye[8:-8]] + [throat + V(0, 0.012, 0)]
    strand_rope('eye', eye_path, lambda t: R, lay=0.055)
    # splice: the tail's strands tucked into the standing part, a thick section tapering over 0.22 m
    sp = [throat + V(0.01 + 0.03 * i, 0, 0) for i in range(9)]
    strand_rope('splice', sp, lambda t: R * (1.45 - 0.45 * t ** 0.8), lay=0.05)
    # the standing part off across the quay
    sp2 = [throat + V(0.25, 0, 0)] + [throat + V(0.25 + 0.15 * i, 0.03 * math.sin(i * 0.8), 0) for i in range(1, 9)]
    C.three_strand('standing', T3(sp2), R, 0.055)
    # three tapering tucked tails lying on the splice
    for k in range(3):
        a = k * math.tau / 3; tail = []
        for i in range(10):
            t = i / 9; tail.append(throat + V(0.02 + 0.2 * t, math.cos(a + t * 2.4) * R * 1.3, zr + math.sin(a + t * 2.4) * R * 1.3))
        _tube_var(f'tail{k}', C.spaced(C.catmull_centripetal(tail, 12), 40)[0], [R * 0.45 * (1 - i / 41) + 0.0008 for i in range(41)], C.rope_mat(f'tailm{k}'))
    # ring bolt: an eye plate in the setts with a ring standing in it
    rb = V(-0.40, 0.8, 0)
    C.obj('eye-plate', C.rbox('plate', (0.1, 0.07, 0.012), 0.004, 2), gm, rb + V(0, 0, 0.006))
    bm = bmesh.new(); ring_pts = [rb + V(0, 0.055 * math.cos(i / 48 * math.tau), 0.066 + 0.055 * math.sin(i / 48 * math.tau)) for i in range(49)]
    tubeP('ring', ring_pts, 0.009, gm)
    # shackle: pin through the thimble's round end, the bow round the ring's bottom
    pin = V(-0.238, 0.8, 0)
    C.cyl('pin', 0.006, 0.006, 0.05, 16, gm, pin + V(0, 0, zr))
    C.cyl('pin-head', 0.0095, 0.0095, 0.006, 16, gm, pin + V(0, 0, zr + 0.026))
    bow = []
    for i in range(25):
        a = math.pi * i / 24
        bow.append(V(pin.x - 0.0 - 0.15 * math.sin(a) * 0.75, 0.8, zr + 0.02 * math.cos(a)))
    tubeP('shackle-bow', bow, 0.0065, gm)
    K.day_sky(sun_az=200, sun_el=40); K.darken_visible_sky()
    labels = [((-0.18, 0.775, 0.022), 'thimble'), ((0.02, 0.8, 0.03), 'eye splice', 'blue'), ((-0.33, 0.8, 0.075), 'shackle')]
    finish(labels, 'A thimble inside the eye takes the chafe', (-0.10, 0.36, 0.46), (-0.20, 0.8, 0.0), 44, fstop=16.0)

elif FIG in (6, 8):
    K.sea('calm', center=(0, -10))
    quay()
    y = yacht_stern_to(gap=1.4, x=0.0)
    K.day_sky(sun_az=230 if FIG == 6 else 210, sun_el=42); K.darken_visible_sky()
    cs = stern_cleat(y, -1); cp = stern_cleat(y, +1)                 # starboard (world +x) and port (world -x)
    print('CLEATS', cs, cp)
    if FIG == 6:
        b = bollard(-2.1, 0.75)
        top = b + V(0, 0, 0.30)
        # the line: from the starboard cleat over the stern, round the far side of the bollard, back to the same cleat
        d = (top - cs); d.z = 0; d.normalize(); side = V(-d.y, d.x, 0)
        a1 = cs + side * 0.02; a2 = cs - side * 0.02
        wrap = [top + V(math.cos(t) * 0.135, math.sin(t) * 0.135, 0) for t in [math.atan2(-d.y, -d.x) + s for s in ()]]
        ang0 = math.atan2(side.y, side.x)
        wrap = [top + V(math.cos(ang0 - math.pi * k / 10) * 0.135, math.sin(ang0 - math.pi * k / 10) * 0.135, 0.02 * math.sin(math.pi * k / 10)) for k in range(11)]
        leg1 = catenary(a1, wrap[0], 0.25)[:-1]; leg2 = catenary(wrap[-1], a2, 0.25)[1:]
        pts = leg1 + wrap + leg2
        C.three_strand('slip', T3(pts), 0.011, 0.07)
        # the other stern line, made fast normally on a second bollard
        b2 = bollard(2.1, 0.75)
        C.three_strand('stern-port', T3(catenary(cp, b2 + V(0, -0.13, 0.3), 0.22) + [b2 + V(0.13, 0.0, 0.3), b2 + V(0.0, 0.14, 0.31), b2 + V(-0.13, 0.03, 0.3), b2 + V(-0.05, -0.11, 0.29), b2 + V(-0.4, 0.3, 0.04), b2 + V(-0.6, 0.6, 0.03)]), 0.011, 0.07)
        mid = a1.lerp(top, 0.12); mid.z -= 0.1
        labels = [(tuple(b + V(0, 0, 0.62)), 'bollard'), (tuple(mid + V(0, 0, 0.05)), 'both ends on board', 'blue')]
        finish(labels, 'Slip line: round the bollard and back to the same cleat', (-4.4, 3.4, 2.7), (-1.5, -1.0, 1.25), 34, fstop=11.0)
    else:
        b = bollard(2.3, 0.75)
        top = b + V(0, 0, 0.30)
        # a bar-tight line from the port quarter to the bollard, a round turn on it
        line = [cp, cp.lerp(top, 0.5), top + V(0.0, -0.13, 0)] + [top + V(math.sin(k / 8 * math.tau) * 0.135, -math.cos(k / 8 * math.tau) * 0.135, 0.015 * k / 8) for k in range(1, 9)] + [top + V(0.25, 0.2, -0.25), top + V(0.6, 0.4, -0.29)]
        C.three_strand('tight', T3(line), 0.012, 0.075)
        # snap-back zone: a red wedge on the quay along the line and beyond the bollard, and one over the stern
        d = (top - cp); d.z = 0; d.normalize(); s = V(-d.y, d.x, 0)
        def wedge(name, p0, p1, w0, w1, z):
            me = bpy.data.meshes.new(name)
            me.from_pydata([tuple(p0 + s * w0 + V(0, 0, z - p0.z)), tuple(p1 + s * w1 + V(0, 0, z - p1.z)), tuple(p1 - s * w1 + V(0, 0, z - p1.z)), tuple(p0 - s * w0 + V(0, 0, z - p0.z))], [], [(0, 1, 2, 3)])
            m, nt, bsdf, out = C.new_mat(name + '-m')
            em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (0.9, 0.06, 0.04, 1); em.inputs['Strength'].default_value = 0.6
            tp = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader'); mx.inputs['Fac'].default_value = 0.42
            nt.links.new(tp.outputs[0], mx.inputs[1]); nt.links.new(em.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], out.inputs['Surface'])
            o = C.obj(name, me, m); o.visible_shadow = False; return o
        e0 = V(top.x - d.x * (top.y - 0.02) / max(d.y, 1e-3), 0.02, QZ)
        wedge('zone-quay', V(e0.x, 0.02, QZ), top + d * 3.0, 0.35, 1.6, QZ + 0.012)
        wedge('zone-water', cp, V(e0.x, 0.0, QZ), 0.5, 0.35, QZ - 0.02)
        # where to stand: two yellow footprints on the quay, well off the line
        foot_m = C.simple('footprint', '#ffd400', 0.5)
        st = top + s * 1.9 + d * 0.6; st.z = QZ + 0.006
        for k, off in enumerate((-0.09, 0.09)):
            bm = bmesh.new(); bmesh.ops.create_circle(bm, cap_ends=True, segments=24, radius=0.075)
            for v in bm.verts: v.co.y *= 2.1
            me = bpy.data.meshes.new('foot'); bm.to_mesh(me); bm.free()
            o = C.obj('foot', me, foot_m, st + s * off); o.rotation_euler.z = math.atan2(-s.y, -s.x) + math.pi / 2
        labels = [(tuple(top + d * 1.6 + V(0, 0, 0.05)), 'snap-back zone', 'red'), (tuple(st + V(0, 0, 0.1)), 'stand to one side', 'blue'), (tuple(b + V(0, 0, 0.55)), 'bollard')]
        finish(labels, 'A parting line whips back: stand to one side', (-2.4, 6.2, 3.6), (2.7, -0.4, 1.0), 30, fstop=11.0)

else:  # FIG 9: the coiled halyard on the mast cleat
    K.sea('calm')
    y = K.load_yacht(name='yacht'); y.place(0, 0, heading=0)
    K.coast(distance=900, bearing=60, height=90, town=False)
    K.day_sky(sun_az=150, sun_el=40); K.darken_visible_sky()
    bpy.context.view_layer.update()
    # the mast's starboard face (model -y side, world +x after heading 0) and a cleat on it
    face = y.world((5.065, 0.07, 4.62)); out = (y.world((5.065, -1.0, 4.62)) - face).normalized(); up = V(0, 0, 1)
    fwd = out.cross(up).normalized()
    cm = C.simple('mast-cleat', '#c9cdd1', 0.3, 1.0)
    cleat = face + out * 0.045
    C.cyl('cleat-horns', 0.011, 0.011, 0.17, 24, cm, cleat)                       # vertical, along the mast
    for dz in (-0.04, 0.04):
        o = C.cyl('cleat-leg', 0.011, 0.014, 0.05, 16, cm, face + out * 0.022 + V(0, 0, dz)); o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = out.to_track_quat('Z', 'Y')
    hr = 0.0052
    # the halyard: out of the mast exit above, down the face to the cleat; a turn round the base, figures of eight, a hitch
    top = face + out * 0.03 + V(0, 0, 1.4)
    p = [top, top.lerp(cleat + out * 0.02 + V(0, 0, 0.12), 0.6), cleat + out * 0.02 + V(0, 0, 0.12), cleat + fwd * 0.02 + out * 0.01 + V(0, 0, 0.03)]
    for k in range(3):
        sgn = 1 if k % 2 == 0 else -1
        p += [cleat - fwd * 0.02 * sgn + out * 0.022 + V(0, 0, -0.07 * sgn), cleat + fwd * 0.02 * sgn + out * 0.022 + V(0, 0, -0.085 * sgn),
              cleat + fwd * 0.02 * sgn - out * 0.006 + V(0, 0, 0.0)]
    p += [cleat + out * 0.03 + V(0, 0, 0.05), cleat + out * 0.035 + V(0, 0, 0.09)]
    hang = cleat + out * 0.035 + V(0, 0, 0.088)
    # the coil: loops hanging from the upper horn, each a little different, in a plane facing out from the mast
    loops = 7; coil = []
    for k in range(loops):
        w = 0.13 + 0.006 * (k - 3); L = 0.55 + 0.015 * math.sin(k * 1.7); tilt = (k - 3) * 0.012
        for i in range(1, 25):
            a = i / 24 * math.tau
            coil.append(hang + fwd * (math.sin(a) * w + tilt) + out * (0.01 + 0.004 * k) + V(0, 0, -L * (1 - math.cos(a)) / 2))
    # the twisted loop pulled through the coil and over the horn
    twist = [hang + out * 0.06 + V(0, 0, -0.25), hang + out * 0.05 + fwd * 0.02 + V(0, 0, -0.1), hang + out * 0.02 + V(0, 0, 0.03), hang - out * 0.005 + fwd * 0.012 + V(0, 0, 0.02), hang + out * 0.04 - fwd * 0.03 + V(0, 0, -0.12), hang + out * 0.07 - fwd * 0.05 + V(0, 0, -0.32), hang + out * 0.07 - fwd * 0.04 + V(0, 0, -0.42)]
    C.braid('halyard', T3(p + coil + twist), hr, '#c4262e', '#f3f1ea', shiny=True, fine=1.6, whip='#f4f1e6')
    labels = [(tuple(cleat + out * 0.03 + V(0, 0, 0.11)), 'mast cleat'), (tuple(top + V(0, 0, -0.75)), 'halyard'), (tuple(hang + V(0, 0, -0.62) + out * 0.03), 'coil, hung from the cleat', 'blue')]
    eye = cleat + out * 1.3 - fwd * 0.25 + V(0, 0, -0.05); look = cleat + V(0, 0, -0.12)
    finish(labels, 'Pull a loop through the coil, twist it, hang it', tuple(eye), tuple(look), 28, fstop=8.0)
