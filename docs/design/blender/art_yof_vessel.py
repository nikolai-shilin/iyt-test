# Article yachtmaster-offshore/vessel ("The vessel"), its nine figures as Blender renders:
#   1  haul-out: the yacht on the hard, her keel on long timber blocks, stands only steadying her; osmosis blisters
#      below the waterline, the rudder weeping water
#   2  the same yacht broadside on the hard, the rig up: keel bolts and grid, rudder bearings, forestay swages,
#      backstay chainplate, hull-to-deck joint
#   3  card, stability booklet: the yacht heeled 10° seen from astern: G, B moved to the low side, M, the lever GZ
#   4  card, launching the tender: the davit swings a 1 t RIB 2.8 m outboard, 4 m up; she lists about 6°
#   5  panel, roll period: at anchor in harbour, rolling slowly; beam 5.0 m, roll 8.0 s, GM 0.25 m
#   6  card, fuel path: the engine bay: tank, primary filter and separator, lift pump, fine filter, injection pump,
#      injectors, numbered in the order they are bled
#   7  panel, cooling: the raw-water circuit, the heat exchanger cut open, its tubes white with scale; 92° on the gauge
#   8  panel, overpropped: at full throttle, black smoke from the exhaust; the tachometer at 2700 of 3200
#   9  panel, charging: the charger's display in absorption: 14.4 V held, 9 A tapering
#   blender --background --factory-startup --python docs/design/blender/art_yof_vessel.py -- --fig 1 [--samples 160]
#   python3 docs/design/blender/art_yof_vessel.py --faces      the dial and display textures (system Python)
import os, sys, math, random, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
DIR = os.path.join(HERE, '..', 'figure-style', 'articles', 'yachtmaster-offshore', 'vessel'); TEX = os.path.join(DIR, 'tex')

def faces():
    from PIL import Image, ImageDraw, ImageFont
    os.makedirs(TEX, exist_ok=True)
    B = '/System/Library/Fonts/Supplemental/Arial Bold.ttf'; R = '/System/Library/Fonts/Supplemental/Arial.ttf'
    F = lambda p, n: ImageFont.truetype(p, n)
    def dial(out, lo, hi, step, label, red_from=None, unit=''):
        S = 1024; C = S / 2; im = Image.new('RGB', (S, S), (14, 15, 17)); d = ImageDraw.Draw(im)
        a0, a1 = -135, 135
        if red_from is not None:
            a = -90 + a0 + (a1 - a0) * (red_from - lo) / (hi - lo); d.arc([C - 470, C - 470, C + 470, C + 470], a, -90 + a1, fill=(200, 30, 30), width=30)
        v = lo
        while v <= hi + 1e-6:
            a = math.radians(a0 + (a1 - a0) * (v - lo) / (hi - lo))
            d.line([(C + math.sin(a) * 400, C - math.cos(a) * 400), (C + math.sin(a) * 470, C - math.cos(a) * 470)], fill=(235, 235, 230), width=12)
            d.text((C + math.sin(a) * 330, C - math.cos(a) * 330), label(v), font=F(B, 80), fill=(235, 235, 230), anchor='mm'); v += step
        d.text((C, C + 230), unit, font=F(R, 56), fill=(200, 200, 195), anchor='mm'); im.save(out)
    dial(os.path.join(TEX, 'tach.png'), 0, 4000, 500, lambda v: str(int(v / 1000)) if v % 1000 == 0 else '', red_from=3200, unit='RPM x 1000')
    dial(os.path.join(TEX, 'temp.png'), 40, 120, 20, lambda v: str(int(v)), red_from=100, unit='°C  WATER')
    w, h = 900, 520; im = Image.new('RGB', (w, h), (18, 24, 30)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w, 90], fill=(30, 40, 50)); d.text((30, 45), 'CHARGER', font=F(B, 50), fill=(190, 210, 225), anchor='lm')
    d.text((w - 30, 45), 'ABSORPTION', font=F(B, 50), fill=(255, 196, 40), anchor='rm')
    d.text((40, 200), '14.4 V', font=F(B, 140), fill=(120, 230, 160), anchor='lm'); d.text((40, 360), '9 A', font=F(B, 140), fill=(120, 230, 160), anchor='lm')
    for i, (t, on) in enumerate((('BULK', False), ('ABS', True), ('FLOAT', False))):
        x = 560 + i * 0; y = 170 + i * 100
        d.rounded_rectangle([600, y, 860, y + 76], 14, fill=(255, 196, 40) if on else (40, 50, 60)); d.text((730, y + 38), t, font=F(B, 46), fill=(20, 20, 20) if on else (120, 135, 150), anchor='mm')
    d.text((40, 470), 'current tapering', font=F(R, 40), fill=(150, 170, 185), anchor='lm'); im.save(os.path.join(TEX, 'charger.png'))
    print('faces in', TEX)

if __name__ == '__main__' and '--faces' in sys.argv:
    faces(); sys.exit(0)

sys.path.insert(0, HERE)
import bpy, bmesh
from mathutils import Vector, Euler
import common as C, kit as K, kit_instruments as KI
import q_encounter_props as P
from common import node, link, setin, math_, ramp, new_mat

arg = C.cli(); FIG = arg('--fig', 1); SAMPLES = arg('--samples', 160); SCALE = arg('--scale', 100)
OUT = arg('--out', os.path.join(DIR, f'{FIG}-3d.jpg'))
def deg(a): return math.radians(a)
def V(*a): return Vector(a)
labels, arrows, note, expo = [], [], None, -0.6
C.reset(); M = K.mats()
if not os.path.exists(os.path.join(TEX, 'charger.png')): subprocess.run(['python3', os.path.abspath(__file__), '--faces'], check=True)

def wl_mat(wl, name='hull-wl'):
    """Gelcoat over a boot stripe over dark antifouling, split at world height wl (the waterline)."""
    m, nt, b, _ = new_mat(name)
    g = node(nt, 'ShaderNodeNewGeometry'); s = node(nt, 'ShaderNodeSeparateXYZ'); link(nt, g.outputs['Position'], s.inputs['Vector'])
    zz = math_(nt, 'MULTIPLY_ADD', math_(nt, 'SUBTRACT', s.outputs['Z'], wl), 1.0, 0.5)
    c = ramp(nt, [(0.0, '#2b2e35'), (0.455, '#2b2e35'), (0.46, '#16213b'), (0.505, '#16213b'), (0.51, K.YACHT_WHITE), (1.0, K.YACHT_WHITE)], 'CONSTANT')
    link(nt, zz, c.inputs['Fac']); link(nt, c.outputs['Color'], b.inputs['Base Color']); setin(b, 'Roughness', 0.6)
    return m

def bottom_paint(yt, wl):
    bpy.context.view_layer.update(); m = wl_mat(wl)
    for o in yt.objs:
        if o.type != 'MESH' or o.hide_render: continue
        lo, hi = K.bbox([o])
        if lo.z < wl - 0.05:
            for s in o.material_slots: s.material = m

def ray(o, d):
    dg = bpy.context.evaluated_depsgraph_get(); hit, loc, n, i, ob, mt = bpy.context.scene.ray_cast(dg, Vector(o), Vector(d).normalized())
    return (loc, n) if hit else (None, None)

def hull_pt(yt, x, z, side=-1, k=1.0):
    """The hull surface at model (x, ., z), from outside on the starboard (side -1) or port (+1) side."""
    a = Vector(yt.world((x, K.MAST.y + side * 8, z))); b = Vector(yt.world((x, K.MAST.y, z)))
    loc, n = ray(a, b - a); return loc

def box(name, size, at, mat, r=0.0, rot=(0, 0, 0)):
    o = C.obj(name, C.rbox(name, size, r, 2), mat, Vector(at)); o.rotation_euler = rot; return o
def cyl_between(name, a, b, r, mat, seg=20):
    a, b = Vector(a), Vector(b); d = b - a
    o = C.cyl(name, r, r, d.length, seg, mat, tuple((a + b) / 2)); o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = d.to_track_quat('Z', 'Y'); return o
def hose(name, pts, r, mat): return C.tube(name, C.catmull_centripetal([Vector(p) for p in pts], 10), r, 12, 1.0, mat)

# ======================================================================================================== the yard
def yard(lift=2.4, heading=90):
    """The yacht on the hard: concrete, timber blocks under the keel, three stands a side, the sea beyond the quay."""
    yt = P.yacht('yacht'); yt.place(0, 0, heading=heading); yt.root.location.z = lift
    bpy.context.view_layer.update(); bottom_paint(yt, lift)
    conc = C.concrete_mat('yard')
    g = bpy.data.meshes.new('yard'); g.from_pydata([(-200, -200, 0), (200, -200, 0), (200, 28, 0), (-200, 28, 0)], [], [(0, 1, 2, 3)])
    C.obj('yard', g, conc)
    box('quay-edge', (400, 1.0, 1.6), (0, 28.5, -0.8), conc)
    K.sea('calm', size=30.0, repeat=6, center=(0, 120)); bpy.data.objects['ocean'].location.z = -1.2; bpy.data.objects['far-sea'].location.z = -1.22
    K.coast(distance=1600, bearing=0, height=90)
    wood = C.simple('block-wood', '#6e5636', 0.85)
    kb = Vector(yt.world((3.5, K.MAST.y, 0.0)))
    for dx in (-0.7, 0.7):
        box('keel-block', (0.9, 0.5, kb.z), tuple(kb + V(dx, 0, 0) - V(0, 0, kb.z / 2)), wood, 0.02)
    steel = C.simple('stand-blue', '#2c5d9e', 0.45, 0.4); pads = []
    for x in (-0.8, 3.6, 7.8):
        pair = []
        for side in (-1, 1):
            p = hull_pt(yt, x, 2.25, side)
            if p is None: continue
            foot = Vector((p.x, p.y + side * 0.9 * (1 if heading == 90 else 1), 0.0))
            cyl_between('stand', foot, p, 0.05, steel); C.cyl('stand-foot', 0.35, 0.35, 0.05, 16, steel, tuple(foot + V(0, 0, 0.025)))
            box('stand-pad', (0.3, 0.06, 0.3), tuple(p), C.simple('pad', '#1c1c1c', 0.8)); pair.append(foot + V(0, 0, 0.6))
        if len(pair) == 2: C.tube('stand-chain', [pair[0], pair[1]], 0.012, 6, 1.0, C.simple('chain', '#3a3c3e', 0.5, 0.8))
    yt2 = P.yacht('neighbour'); yt2.place(-24, 14, heading=heading); yt2.root.location.z = lift
    return yt

if FIG in (1, 2):
    K.day_sky(sun_az=200, sun_el=40)
    LIFT = 2.4; yt = yard(LIFT)
    W = lambda p: tuple(yt.world(p))
    if FIG == 1:
        # osmosis: blisters on the starboard bottom, forward of the keel, just below the boot top
        rnd = random.Random(3); blister = C.simple('blister', '#3a3d44', 0.45)
        for i in range(70):
            x = rnd.uniform(5.2, 8.6); z = rnd.uniform(1.55, 1.93)
            p = hull_pt(yt, x, z, -1)
            if p is None: continue
            r = rnd.uniform(0.025, 0.055); o = C.obj('blister', K._sphere('blister', r), blister, tuple(p)); o.scale = (1, 1, 0.8)
        # the rudder weeping: a dark wet streak down its trailing edge, a puddle on the concrete
        wet = C.simple('wet', '#14161a', 0.08, coat=1.0)
        rb = Vector(W((-2.85, K.MAST.y, 0.55))); rt = Vector(W((-2.85, K.MAST.y, 1.9)))
        C.tube('weep', [rt, rb, rb - V(0, 0, 0.02)], 0.012, 8, 1.0, wet)
        pm = bpy.data.meshes.new('puddle'); bm = bmesh.new(); bmesh.ops.create_circle(bm, cap_ends=True, segments=40, radius=0.5); bm.to_mesh(pm); bm.free()
        pu = C.obj('puddle', pm, wet, (rb.x, rb.y, 0.004)); pu.scale = (1.4, 0.8, 1)
        cam_eye = V(5.5, -7.5, 1.35); cam_at = Vector(W((3.0, K.MAST.y, 1.4)))
        K.camera(tuple(cam_eye), tuple(cam_at), 24)
        labels = [(W((7.0, -1.0, 1.7)), 'osmosis: blisters below the waterline', 'red'), (W((3.5, K.MAST.y, 0.0)), 'keel on long blocks: her weight'),
                  (W((-2.6, K.MAST.y, 0.8)), 'rudder weeping: wet inside?', 'red'), (W((-0.8, -1.9, 2.4)), 'stands only steady her', 'blue')]
        note = 'Haul-out · the keel takes the weight; look below the waterline'
    else:
        cam_eye = V(-1.3, -14.0, 1.8); K.camera(tuple(cam_eye), tuple(V(-1.3, 0, 4.6)), 22)
        hd = hull_pt(yt, 2.0, 3.25, -1)
        labels = [(W((3.5, K.MAST.y, 1.5)), 'keel bolts, keel grid'), (W((-2.4, K.MAST.y, 1.95)), 'rudder bearings'),
                  (W((10.6, K.MAST.y, 4.6)), 'forestay: swages', 'blue'), (W((-3.6, K.MAST.y, 3.3)), 'backstay: chainplate', 'blue'),
                  (tuple(hd) if hd else W((2.0, -2.1, 3.25)), 'hull-to-deck joint')]
        note = 'Structure and rig · where the loads go, and where to look'
    expo = -0.55

# ======================================================================================================== afloat
elif FIG in (3, 5):
    heel = 10 if FIG == 3 else -8
    K.sea('calm', size=30.0, repeat=10); K.day_sky(sun_az=150, sun_el=38)
    yt = P.yacht('yacht'); yt.place(0, 0, heading=0, heel=heel)
    if FIG == 5:
        K.coast(distance=700, bearing=40, height=70, town=True); K.breakwater((-160, 220), (60, 260), 10, 3)
        sh = Vector(yt.world((10.9, K.MAST.y, 3.7)))
        C.tube('chain', [sh.lerp(sh + V(0, 10, -sh.z - 1), t / 10) + V(0, 0, -0.6 * math.sin(math.pi * t / 10)) for t in range(11)], 0.03, 6, 1.0, C.simple('chain', '#3a3c3e', 0.5, 0.8))
    K.camera((0.6, -24, 3.2), (0, 0, 4.2), 40) if FIG == 5 else K.camera((0.4, -15, 2.4), (0, 0, 2.6), 32)
    W = lambda p: Vector(yt.world(p))
    if FIG == 3:
        # G fixed in the hull (KG 2.60 m), M on the centreline above it (KM 3.20 m); B moved to the low side
        G = W((4.0, K.MAST.y, 2.6)); Mt = W((4.0, K.MAST.y, 3.2))
        low = V(1, 0, 0) if (W((4, K.MAST.y - 1, 2)) - W((4, K.MAST.y, 2))).x > 0 else V(-1, 0, 0)
        Bp = V(G.x, G.y, 0) + V(0, 0, -0.45) + V(1, 0, 0) * 0.55 * (1 if heel > 0 else -1)
        Zp = V(Bp.x, G.y, G.z)
        for p, c in ((G, '#d62828'), (Bp, '#1384d6'), (Mt, '#202020')): C.obj('dot', K._sphere('dot', 0.09), C.simple('dot' + c, c, 0.4), tuple(p))
        labels = [(tuple(G), 'G: weight, down', 'red'), (tuple(Bp), 'B: buoyancy, up, to the low side', 'blue')]
        arrows = [(tuple(G), tuple(G - V(0, 0, 1.8)), 'red'), (tuple(Bp), tuple(Bp + V(0, 0, 1.8)), 'blue')]
        note = 'Heeled 10°: righting lever GZ ≈ GM × sin θ = 0.10 m'
    else:
        top = W((K.MAST.x, K.MAST.y, 9.5))
        labels = [(tuple(top), 'roll period 8.0 s (6.0 s before)', 'red'), (tuple(W((3.0, K.MAST.y - 2.3, 3.4))), 'beam 5.0 m'),
                  (tuple(W((3.0, K.MAST.y, 1.0))), 'GM 0.25 m: find the free water', 'red')]
        arrows = [(tuple(top + V(-1.6, 0, -1.2)), tuple(top + V(2.6, 0, -1.8)), 'red')]
        note = 'A slow, lazy roll: GM has fallen · slack tanks, water below?'

elif FIG == 4:
    K.sea('calm', size=30.0, repeat=10); K.day_sky(sun_az=150, sun_el=40)
    yt = P.yacht('yacht'); yt.place(0, 0, heading=0, heel=6)    # listing to starboard, the tender's side
    W = lambda p: Vector(yt.world(p))
    steel = C.simple('davit', '#4a4f55', 0.3, 0.8)
    base = W((-1.0, K.MAST.y - 1.6, 3.4)); post = W((-1.0, K.MAST.y - 1.6, 6.6)); tip = W((-1.0, K.MAST.y - 4.5, 7.6))
    cyl_between('davit-post', base, post, 0.16, steel); cyl_between('davit-jib', post, tip, 0.12, steel)
    spin, vis, top = P.rib((tip.x, tip.y), 0, 4.0)
    bpy.context.view_layer.update(); lo, hi = K.bbox(vis)
    for o in [spin]: o.location.z += 3.2
    bpy.context.view_layer.update(); lo, hi = K.bbox(vis); hook = V((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, hi.z + 1.0)
    C.tube('wire', [tip, hook], 0.012, 6, 1.0, C.simple('wire', '#2a2c2e', 0.4, 0.8))
    for c in ((lo.x + 0.3, lo.y + 0.4), (hi.x - 0.3, lo.y + 0.4), (lo.x + 0.3, hi.y - 0.4), (hi.x - 0.3, hi.y - 0.4)):
        C.tube('sling', [hook, V(c[0], c[1], hi.z - 0.2)], 0.008, 6, 1.0, C.simple('sling', '#e0b400', 0.6))
    K.camera((16, -20, 5.5), tuple(W((0.0, K.MAST.y - 2.5, 5.0))), 34)
    labels = [(tuple(tip + V(0, 0, 0.2)), 'the weight acts at the crane head', 'blue'), (tuple(hook - V(0, 0, 0.6)), 'tender 1.0 t: 4.0 m up, 2.8 m out'),
              (tuple(W((K.MAST.x, K.MAST.y, 21.0))), 'list about 6°', 'red')]
    note = 'Launching the tender · G rises and moves outboard: she lists'

# ======================================================================================================== the engine bay
def engine_bay(cut=False):
    """A four-cylinder marine diesel on its beds, seen from the port side and a little forward."""
    paint = C.simple('engine-paint', '#4f6170', 0.42, 0.25, coat=0.3); dark = C.simple('engine-dark', '#24272b', 0.5, 0.3)
    alu = M['alu'] if 'alu' in M else C.simple('alu', '#b9bdc1', 0.35, 1.0); frp = C.simple('bay', '#d4d0c4', 0.6)
    box('bay-floor', (2.6, 1.8, 0.05), (0, 0, -0.02), frp)
    box('bay-back', (0.05, 1.8, 1.4), (-1.3, 0, 0.7), frp)
    box('bay-side', (3.0, 0.05, 1.8), (0, -0.9, 0.9), frp); box('bay-front', (0.05, 1.8, 1.8), (1.3, 0, 0.9), frp)
    for s in (-1, 1): box('bed', (1.4, 0.12, 0.18), (0, s * 0.32, 0.09), frp)
    box('sump', (0.9, 0.42, 0.25), (0, 0, 0.32), paint, 0.03)
    box('block', (0.95, 0.5, 0.42), (0, 0, 0.65), paint, 0.04)
    box('head', (0.9, 0.42, 0.18), (0, 0.04, 0.95), paint, 0.03)
    box('rocker', (0.8, 0.3, 0.12), (0, 0.06, 1.1), C.simple('rocker', '#2f3d4a', 0.4, 0.3), 0.04)
    box('bellhousing', (0.2, 0.55, 0.5), (-0.58, 0, 0.55), paint, 0.05)
    box('gearbox', (0.32, 0.3, 0.32), (-0.8, 0, 0.45), C.simple('gearbox', '#2d3134', 0.4, 0.4), 0.04)
    box('exhaust-manifold', (0.8, 0.08, 0.14), (0, -0.28, 0.9), C.simple('manifold', '#6a3f2a', 0.6, 0.5), 0.03)
    return paint, dark

if FIG in (6, 7):
    paint, dark = engine_bay()
    K.day_sky(sun_az=200, sun_el=35, strength=0.12); KI.area_light((0.8, 1.6, 2.2), (0, 0, 0.6), 220, 1.2)
    KI.area_light((1.8, -0.4, 1.2), (0, 0, 0.6), 60, 1.0, (0.9, 0.95, 1.0))
    fuel = C.simple('fuel-line', '#1c1c1c', 0.5); hp = C.simple('hp-pipe', '#c8ccd0', 0.25, 1.0); red = C.simple('handle', '#c4161c', 0.4)
    if FIG == 6:
        tank = box('tank', (0.6, 0.5, 0.7), (-1.0, 0.75, 0.38), C.simple('tank', '#9ea4a9', 0.35, 0.9), 0.03)
        # primary filter and water separator on the bulkhead: a black head over a clear bowl with a little water
        pf = V(-0.2, 0.86, 0.75); C.cyl('pf-head', 0.08, 0.08, 0.08, 24, dark, tuple(pf + V(0, 0, 0.1)))
        C.cyl('pf-bowl', 0.07, 0.07, 0.18, 24, M['glass'], tuple(pf - V(0, 0, 0.03)))
        C.cyl('pf-water', 0.065, 0.065, 0.04, 24, C.simple('water-bowl', '#b0c4cc', 0.1), tuple(pf - V(0, 0, 0.1)))
        C.cyl('pf-fuel', 0.065, 0.065, 0.09, 24, C.simple('diesel', '#b8902a', 0.15), tuple(pf - V(0, 0, 0.035)))
        box('pf-bracket', (0.06, 0.04, 0.72), tuple(pf + V(0, -0.1, -0.25)), dark); box('pf-arm', (0.06, 0.1, 0.04), tuple(pf + V(0, -0.05, 0.12)), dark)
        box('ff-bracket', (0.22, 0.04, 0.04), (0.56, 0.3, 0.86), dark)
        lp = V(0.2, 0.29, 0.62); box('lift-pump', (0.1, 0.08, 0.1), tuple(lp), dark, 0.02); box('lift-lever', (0.02, 0.03, 0.1), tuple(lp + V(0.04, 0.05, -0.06)), red)
        ff = V(0.66, 0.3, 0.8); C.cyl('fine-filter', 0.055, 0.055, 0.15, 24, C.simple('filter-white', '#e4e0d6', 0.5), tuple(ff))
        ip = V(0.05, 0.32, 0.82); box('injection-pump', (0.34, 0.12, 0.14), tuple(ip), C.simple('ip', '#8a8f94', 0.35, 0.8), 0.02)
        inj = [V(-0.3 + i * 0.2, 0.12, 1.05) for i in range(4)]
        for q in inj: C.cyl('injector', 0.018, 0.018, 0.14, 12, hp, tuple(q))
        hose('fl1', [V(-0.75, 0.78, 0.6), V(-0.5, 0.85, 0.55), pf + V(0, 0, 0.13)], 0.009, fuel)
        hose('fl2', [pf + V(0.05, 0, 0.13), V(0.05, 0.6, 0.55), lp + V(-0.05, 0, 0)], 0.009, fuel)
        hose('fl3', [lp + V(0.05, 0, 0.03), V(0.35, 0.36, 0.7), ff - V(0, 0, 0.08)], 0.009, fuel)
        hose('fl4', [ff + V(0, 0, 0.08), V(0.32, 0.36, 0.92), ip + V(0.17, 0, 0.0)], 0.009, fuel)
        for i, q in enumerate(inj):
            hose('hp%d' % i, [ip + V(-0.12 + i * 0.08, -0.02, 0.07), V(q.x * 0.5 + ip.x * 0.5, 0.2, 1.0), q + V(0, 0.01, 0.06)], 0.005, hp)
        K.camera((0.6, 2.7, 1.6), (0.0, 0.4, 0.72), 32)
        labels = [(tuple(tank.location + V(0, 0, 0.36)), 'tank'), (tuple(pf + V(0, 0, -0.12)), '1 primary filter, separator', 'blue'),
                  (tuple(lp + V(0, 0, 0.06)), '2 lift pump', 'blue'), (tuple(ff + V(0, 0, 0.09)), '3 fine filter', 'blue'),
                  (tuple(ip + V(0.14, 0, 0.08)), '4 injection pump', 'blue'), (tuple(inj[1] + V(0, 0, 0.08)), '5 injectors: crack each union', 'red')]
        note = 'Bleed in the order the fuel flows, then crack each injector union while cranking'
    else:
        # raw water: seacock, strainer, the impeller pump, the heat exchanger cut open, the exhaust elbow
        hosem = C.simple('raw-hose', '#1a1a1a', 0.6); bronze = C.simple('bronze', '#9a6a32', 0.35, 0.9)
        sc = V(0.75, 0.55, 0.06); C.cyl('seacock', 0.04, 0.04, 0.1, 16, bronze, tuple(sc)); box('sc-lever', (0.18, 0.02, 0.02), tuple(sc + V(0, 0, 0.07)), red)
        st = V(0.85, 0.55, 0.32); C.cyl('strainer', 0.07, 0.07, 0.22, 24, M['glass'], tuple(st)); C.cyl('strainer-lid', 0.08, 0.08, 0.03, 24, bronze, tuple(st + V(0, 0, 0.12)))
        pu = V(0.56, 0.18, 0.5); C.cyl('impeller-pump', 0.07, 0.07, 0.08, 24, bronze, tuple(pu), rot=(deg(90), 0, 0))
        hx = V(0.0, 0.33, 0.98)
        shell = C.cyl('exchanger', 0.09, 0.09, 0.7, 32, C.simple('hx-shell', '#3d4c59', 0.4, 0.6), tuple(hx), rot=(0, deg(90), 0))
        # cut away: a boolean slot in the shell, the tube bundle inside, white with scale
        cutter = box('cut', (0.5, 0.2, 0.2), tuple(hx + V(0, 0.08, 0.06)), dark); cutter.hide_render = True
        md = shell.modifiers.new('cut', 'BOOLEAN'); md.object = cutter; md.operation = 'DIFFERENCE'
        scale_m = C.simple('scale', '#e8e4d8', 0.95)
        for i in range(12):
            a = i / 12 * math.tau; o = C.cyl('hx-tube', 0.012, 0.012, 0.66, 10, scale_m, tuple(hx + V(0, math.cos(a) * 0.05, math.sin(a) * 0.05)), rot=(0, deg(90), 0))
        hose('rw1', [sc + V(0, 0, 0.05), st - V(0, 0, 0.12)], 0.02, hosem)
        hose('rw2', [st + V(-0.05, 0, 0.08), V(0.7, 0.35, 0.5), pu + V(0.04, 0, 0)], 0.02, hosem)
        hose('rw3', [pu + V(-0.04, 0, 0.03), V(0.45, 0.33, 0.8), hx + V(0.36, 0, 0)], 0.02, hosem)
        el = V(-0.42, 0.0, 1.05); hose('elbow', [hx + V(-0.36, 0, 0), V(-0.45, 0.2, 1.05), el, V(-0.5, -0.3, 1.0)], 0.035, C.simple('elbow', '#6a3f2a', 0.6, 0.5))
        K.camera((0.9, 2.3, 1.55), (0.15, 0.35, 0.72), 30)
        labels = [(tuple(sc + V(0, 0, 0.1)), 'seacock'), (tuple(st + V(0, 0, 0.16)), 'strainer: clear'), (tuple(pu + V(0, 0, 0.08)), 'impeller: flow strong', 'blue'),
                  (tuple(hx + V(0.1, 0, 0.12)), 'exchanger tubes: scale', 'red'), (tuple(V(-0.5, -0.3, 1.04)), 'exhaust')]
        note = '92° with strong flow and full coolant: descale the exchanger tubes'
    expo = -0.4

elif FIG == 8:
    K.sea('fresh', size=40.0, repeat=10); K.day_sky(sun_az=200, sun_el=35)
    yt = P.yacht('yacht'); yt.place(0, 0, heading=0); yt.root.scale = (1.4,) * 3; K.wake(yt, 50, 8, 1.6)
    ex = Vector(yt.world((-3.5, K.MAST.y - 1.3, 2.35)))
    sm, snt, sb, sout = new_mat('black-smoke'); snt.nodes.remove(sb)
    vs = snt.nodes.new('ShaderNodeVolumePrincipled'); vs.inputs['Density'].default_value = 1.4; vs.inputs['Color'].default_value = (0.04, 0.04, 0.045, 1)
    snt.links.new(vs.outputs[0], sout.inputs['Volume'])
    rnd = random.Random(2)
    for i in range(16):
        q = ex + V(-0.25 * i - 0.2, -0.5 - 0.9 * i, 0.15 + 0.18 * i) + V(rnd.uniform(-.2, .2), rnd.uniform(-.2, .2), rnd.uniform(-.1, .1))
        C.obj('smoke', K._sphere('smoke', 0.25 + 0.09 * i), sm, tuple(q))
    K.camera(tuple(Vector(yt.world((-28, -12, 9)))), tuple(Vector(yt.world((-2, -1.5, 4)))), 32)
    labels = [(tuple(ex + V(-1.0, -4.0, 1.6)), 'black smoke at full throttle', 'red'), (tuple(Vector(yt.world((-1.5, K.MAST.y, 5.6)))), 'tachometer: 2700, rated 3200', 'blue')]
    note = 'Rated revs never reached at full throttle: overpropped'

elif FIG == 9:
    KI.wall('bulkhead', -1.4, 1.4, -1.0, 0.8, 0.012, KI.joinery_mat())
    box('charger-box', (0.36, 0.1, 0.26), (0.0, -0.04, 0.12), C.simple('charger', '#2c3034', 0.45, 0.3), 0.02)
    m = KI.image_mat('charger-screen', os.path.join(TEX, 'charger.png'), 0.3, 1.1)
    me = bpy.data.meshes.new('screen'); me.from_pydata([(-0.13, 0, -0.075), (0.13, 0, -0.075), (0.13, 0, 0.075), (-0.13, 0, 0.075)], [], [(0, 1, 2, 3)])
    me.uv_layers.new(name='UVMap').data.foreach_set('uv', [0, 0, 1, 0, 1, 1, 0, 1]); C.obj('screen', me, m, (0.0, -0.0905, 0.13))
    bat = C.simple('battery', '#1e2022', 0.5)
    for i, x in enumerate((-0.42, 0.0, 0.42)):
        box('battery', (0.34, 0.18, 0.22), (x, -0.12, -0.48), bat, 0.01)
        C.cyl('post+', 0.012, 0.012, 0.03, 12, C.simple('red-cap', '#c4161c', 0.4), (x - 0.11, -0.12, -0.355)); C.cyl('post-', 0.012, 0.012, 0.03, 12, M['dark'], (x + 0.11, -0.12, -0.355))
    hose('pos-cable', [V(-0.08, -0.05, 0.0), V(-0.15, -0.12, -0.2), V(-0.53, -0.12, -0.33)], 0.008, C.simple('cable-red', '#a51b1b', 0.5))
    hose('neg-cable', [V(0.08, -0.05, 0.0), V(0.2, -0.12, -0.2), V(0.53, -0.12, -0.33)], 0.008, C.simple('cable-black', '#151515', 0.5))
    K.day_sky(sun_az=200, sun_el=35, strength=0.15); KI.area_light((0.3, -1.2, 0.6), (0, 0, 0), 25, 0.8)
    K.camera((0.1, -1.7, 0.0), (0.0, 0, -0.1), 32)
    labels = [((0.0, -0.09, 0.25), 'absorption: 14.4 V held, 9 A tapering', 'blue'), ((0.0, -0.12, -0.36), 'house bank, 3 × 200 Ah')]
    note = 'Bulk done; voltage held, current tapering: normal'; expo = -0.5

C.render(OUT, SAMPLES, SCALE, expo, labels, note, space='blender', arrows=arrows)
