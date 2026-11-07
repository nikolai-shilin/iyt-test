# Article yachtmaster-offshore/colregs: the daylight and fog figures, as Blender renders. Our yacht is the Sun Odyssey
# scaled to 21 m (the article is about yachts of 20 m or more). Figures:
#    1  a VLCC crossing from starboard, seen from our helm: her bridge (aft) at 068°, her bow 290 m ahead of it
#    2  card, risk and action: a ship crossing from starboard on a steady bearing; we have made one large, early
#       alteration to starboard, the old course dashed ahead (drone)
#    3  traffic separation scheme: coast and inshore zone, the westbound lane, the separation zone, the eastbound lane;
#       we cross at right angles, another yacht follows the lane
#    4  card, Rule 10: the same scheme lower down: joining the eastbound lane at a small angle, a trawler fishing in
#       the separation zone, a yacht in the inshore zone
#    5  overtaking: a coaster ahead to port, we are 120° from her bow, abaft her beam (chase view)
#    6  card, Rule 17: a ship crossing from our port side; we stand on, and if we must act: not to port
#   11  fog, overtaking: a ship's grey stern ahead, the radar showing her at 015°, same course, slower
#   12  card, fog signals: at anchor in fog, our bell on the mast; a ship at anchor ahead, bell forward, gong aft
#   14  card, Annex I: our yacht under power at dusk, broadside, her masthead light, sidelight and sternlight
#   15  dayshape: at anchor by day, a black ball 0.6 m across in the fore-triangle, crew beside it for scale
#   24  card, Annex IV: a yacht in distress: red hand flare, orange smoke, square flag and ball, arms raised
#   blender --background --factory-startup --python docs/design/blender/art_yof_colregs_day.py -- --fig 1 [--samples 160]
#   python3 docs/design/blender/art_yof_colregs_day.py --prep     the radar picture for figure 11 (system Python)
import os, sys, math, random
HERE = os.path.dirname(os.path.abspath(__file__))
DIR = os.path.join(HERE, '..', 'figure-style', 'articles', 'yachtmaster-offshore', 'colregs')
TEX = os.path.join(DIR, 'tex'); RADAR = os.path.join(TEX, 'radar-overtaking.png')

def prep_radar():
    """System Python: radar picture, head up, 0.75 nm range: a target 15° on the starboard bow, 0.4 nm, its trail
    showing it closing slowly from ahead (we overtake her), on the Axiom's own front texture."""
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    W, H = 920, 610
    im = Image.new('RGB', (W, H), (4, 10, 22)); d = ImageDraw.Draw(im)
    cx, cy, R = W // 2, H // 2 + 20, 270
    for k in range(1, 4):
        r = R * k / 3; d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(40, 120, 150), width=2)
    for a in range(0, 360, 30):
        t = math.radians(a); d.line([(cx, cy), (cx + R * math.sin(t), cy - R * math.cos(t))], fill=(18, 55, 75), width=1)
    d.line([(cx, cy), (cx, cy - R)], fill=(220, 230, 240), width=3)
    glow = Image.new('RGB', (W, H), (0, 0, 0)); g = ImageDraw.Draw(glow); rnd = random.Random(4)
    for _ in range(260):
        r = rnd.random() ** 1.6 * 60; t = rnd.random() * math.tau
        g.ellipse([cx + r * math.sin(t) - 2, cy - r * math.cos(t) - 2, cx + r * math.sin(t) + 2, cy - r * math.cos(t) + 2], fill=(200, 160, 30))
    tb, tr = math.radians(15), R * 0.53
    tx, ty = cx + tr * math.sin(tb), cy - tr * math.cos(tb)
    for k in range(7):    # a short trail straight up the screen: her relative motion, down towards us, slowly
        px, py = tx, ty - k * 6
        g.ellipse([px - 7, py - 5, px + 7, py + 5], fill=(int(120 - 14 * k), int(90 - 11 * k), 20))
    g.ellipse([tx - 13, ty - 9, tx + 13, ty + 9], fill=(255, 215, 60))
    glow = glow.filter(ImageFilter.GaussianBlur(1.5)); im = Image.composite(glow, im, glow.convert('L').point(lambda v: 255 if v > 8 else 0))
    d = ImageDraw.Draw(im)
    d.ellipse([tx - 22, ty - 22, tx + 22, ty + 22], outline=(80, 220, 255), width=3)
    F = lambda n: ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', n)
    d.rectangle([0, 0, W, 58], fill=(10, 18, 30))
    d.text((24, 14), 'RADAR', font=F(30), fill=(230, 236, 240)); d.text((180, 18), 'H-UP  0.75 nm', font=F(24), fill=(150, 175, 190))
    d.text((W - 400, 18), 'TGT 015°  0.4 nm  COG 000° 4 kn', font=F(24), fill=(255, 210, 70))
    d.ellipse([cx - 9, cy - 9, cx + 9, cy + 9], fill=(230, 236, 240))
    front = Image.open(os.path.join(HERE, 'textures', 'axiom-front.png')).convert('RGB')
    x0, y0, x1, y1 = 70, 72, 645, 432
    front.paste(im.resize((x1 - x0, y1 - y0), Image.LANCZOS), (x0, y0)); os.makedirs(TEX, exist_ok=True); front.save(RADAR)
    print('wrote', RADAR)

if __name__ == '__main__' and '--prep' in sys.argv:
    prep_radar(); sys.exit(0)

sys.path.insert(0, HERE)
import subprocess
import bpy, bmesh
from mathutils import Vector, Euler
import common as C, kit as K
import q_encounter_props as P

arg = C.cli(); FIG = arg('--fig', 1); SAMPLES = arg('--samples', 160); SCALE = arg('--scale', 100)
OUT = arg('--out', os.path.join(DIR, f'{FIG}-3d.jpg'))
def deg(a): return math.radians(a)
def fwd(h): return Vector((math.sin(deg(h)), math.cos(deg(h)), 0.0))
def rgt(h): return Vector((math.cos(deg(h)), -math.sin(deg(h)), 0.0))
def pol(h, d, z=0.0): return Vector((math.sin(deg(h)) * d, math.cos(deg(h)) * d, z))
KS = 1.4                                  # our yacht: the 15 m model scaled to 21 m

def our_yacht(x=0.0, y=0.0, heading=0.0, heel=0.0, sails=None, name='you', k=KS):
    yt = P.yacht(name, sails=sails); yt.place(x, y, heading=heading, heel=heel); yt.root.scale = (k,) * 3
    bpy.context.view_layer.update(); return yt

def mast_top(yt, h=21.0): return tuple(yt.world((K.MAST.x, K.MAST.y, h)))

def dashes(p0, p1, dash=6.0, gap=4.0, w=0.9, mat=None, z=0.22):
    p0, p1 = Vector(p0), Vector(p1); d = p1 - p0; L = d.length; u = d / L; n = 0
    while n * (dash + gap) < L:
        a = p0 + u * (n * (dash + gap)); b = p0 + u * min(L, n * (dash + gap) + dash); c = (a + b) / 2
        o = C.obj('dash', C.rbox('dash', ((b - a).length, w, 0.08), 0.0, 1), mat, (c.x, c.y, z)); o.rotation_euler = (0, 0, math.atan2(u.y, u.x)); n += 1

def band(name, pts, rgba, z=0.18):
    me = bpy.data.meshes.new(name); me.from_pydata([(x, y, z) for x, y in pts], [], [tuple(range(len(pts)))])
    m, nt, b, out = C.new_mat(name)
    tp = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader'); mx.inputs['Fac'].default_value = rgba[3]
    b.inputs['Base Color'].default_value = rgba[:3] + (1,); b.inputs['Roughness'].default_value = 0.6
    nt.links.new(tp.outputs[0], mx.inputs[1]); nt.links.new(b.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], out.inputs['Surface'])
    o = C.obj(name, me, m); o.visible_shadow = False; return o

def special_buoy(p, k=2.2):
    M = K.mats(); h = 2.6 * k
    C.cyl('sp-body', 0.9 * k, 0.9 * k, 0.8 * k, 32, M['yellow'], (p[0], p[1], 0.25 * k))
    C.cyl('sp-pillar', 0.35 * k, 0.45 * k, h, 24, M['yellow'], (p[0], p[1], 0.6 * k + h / 2))
    for r in (45, -45):
        o = C.obj('sp-x', C.rbox('x', (0.9 * k, 0.12 * k, 0.12 * k), 0.02, 2), M['yellow'], (p[0], p[1], 0.9 * k + h)); o.rotation_euler = (0, deg(r), 0)

def ship_top(vis):
    bpy.context.view_layer.update(); lo, hi = K.bbox(vis); return Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, hi.z))

def fog(center, density, size=(800, 800, 40)):
    fm = bpy.data.meshes.new('fog'); bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bm.to_mesh(fm); bm.free()
    o = C.obj('fog', fm, None, (center[0], center[1], size[2] / 2 - 1)); o.scale = size
    m, nt, b, out = C.new_mat('fog'); nt.nodes.remove(b)
    vs = nt.nodes.new('ShaderNodeVolumePrincipled'); vs.inputs['Density'].default_value = density; vs.inputs['Color'].default_value = (0.86, 0.88, 0.9, 1)
    nt.links.new(vs.outputs[0], out.inputs['Volume']); o.data.materials.append(m)
    bpy.context.scene.cycles.volume_bounces = 1; bpy.context.scene.cycles.volume_step_rate = 4.0

def plume(p, wind_to, color, n=14, k=1.0, density=0.5, rise=0.5, drift=0.35):
    """Smoke: volume puffs rising and drifting downwind."""
    sm, snt, sb, sout = C.new_mat('smoke-' + color); snt.nodes.remove(sb)
    vs = snt.nodes.new('ShaderNodeVolumePrincipled'); vs.inputs['Density'].default_value = density; vs.inputs['Color'].default_value = C.lin(color)
    vs.inputs['Emission Strength'].default_value = 0.6 if color.startswith('#ff') else 0.0; vs.inputs['Emission Color'].default_value = C.lin(color)
    snt.links.new(vs.outputs[0], sout.inputs['Volume'])
    d = fwd(wind_to); rnd = random.Random(5); p = Vector(p)
    for i in range(n):
        q = p + Vector((0, 0, (0.3 + i * rise) * k)) + d * (i * i * drift * 0.12 + i * drift) * k + Vector((rnd.uniform(-.3, .3), rnd.uniform(-.3, .3), 0)) * k
        C.obj('smoke', K._sphere('smoke', (0.35 + i * 0.16) * k), sm, tuple(q))

labels, arrows, note, expo = [], [], None, -0.6
C.reset(); M = K.mats()

if FIG == 1:
    K.sea('breeze'); K.day_sky(sun_az=150, sun_el=30)
    you = our_yacht(0, 0, 0, sails=None)
    L = 330.0; rx = -L / 2 + 0.03 * L + 0.72 * 0.13 * L
    bridge = pol(68, 700); pos = bridge - fwd(270) * rx
    h, vis, top = P.merchant(tuple(pos), 270, L, 'tanker'); h.scale = (1, 1, 0.55)     # laden: low in the water
    for m in bpy.data.materials:      # black topsides over the red bottom, as most crude carriers
        if m.name.startswith('ship-hull'):
            for n in m.node_tree.nodes:
                if n.type == 'VALTORGB' and len(n.color_ramp.elements) == 4:
                    for e in n.color_ramp.elements[2:]: e.color = C.lin('#22252a')
    bow = pos + fwd(270) * (L / 2)
    eye = you.world((-2.4, -0.9, 5.15)); look = Vector(eye) + pol(61.5, 100, -0.7)
    K.camera(tuple(eye), tuple(look), 62)
    labels = [(tuple(bridge + Vector((0, 0, 0.14 * L * 0.55 + 4))), 'her bridge: bearing drawing aft'), (tuple(bow + Vector((0, 0, 16))), 'her bow: bearing steady?', 'red')]
    note = 'Her bridge bears aft; her bow, 300 m ahead, may not'
elif FIG == 2:
    K.sea('breeze', size=40.0, repeat=14); K.day_sky(sun_az=200, sun_el=40)
    you = our_yacht(0, 0, 75, sails=None); K.wake(you, 40, 9, 1.3)
    dashes((0, 10, 0), (0, 260, 0), 8, 6, 1.2, C.simple('old-course', '#e9eef0', 0.6))
    sp = pol(38, 300); h, vis, top = P.merchant(tuple(sp), 270, 150, 'container')
    K.camera((-210, -260, 170), (60, 120, 0), 36)
    labels = [(tuple(top + Vector((0, 0, 6))), 'steady bearing: risk', 'red'), (mast_top(you, 22), 'one large alteration, early', 'blue'),
              ((0, 230, 4), 'old course')]
    arrows = [(tuple(you.world((14, 0.13, 6))), tuple(you.world((34, 0.13, 6))), 'blue')]
    note = 'Rules 7 and 8: a steady bearing means risk · act early and boldly'
elif FIG in (3, 4):
    # north up: the coast, the inshore traffic zone, the westbound lane, the separation zone, the eastbound lane
    K.sea('breeze', size=40.0, repeat=22); K.day_sky(sun_az=200, sun_el=45)
    LE, ZN, LW, IZ = (-170.0, -40.0), (-40.0, 40.0), (40.0, 170.0), (185.0, 330.0)
    band('zone', [(-1500, ZN[0]), (1500, ZN[0]), (1500, ZN[1]), (-1500, ZN[1])], (0.9, 0.35, 0.2, 0.14))
    band('inshore', [(-1500, IZ[0]), (1500, IZ[0]), (1500, IZ[1]), (-1500, IZ[1])], (0.2, 0.5, 0.9, 0.08))
    white = C.simple('lane-line', '#e9eef0', 0.6); yel = C.simple('course', '#f2c200', 0.4, coat=0.3)
    for yy in (ZN[0], ZN[1], LW[1] + 8):
        dashes((-1500, yy, 0), (1500, yy, 0), 14, 10, 0.8, white)
    for x in (-600, -300, 0, 300, 600):
        special_buoy((x + 150, ZN[0] + 4)); special_buoy((x, ZN[1] - 4))
    K.coast(distance=380, bearing=0, height=60, town=True)
    hE, vE, tE = P.merchant((-520 if FIG == 3 else 120, -105), 90, 120, 'container')
    hW, vW, tW = P.merchant((260 if FIG == 3 else -260, 105), 270, 120, 'cargo')
    if FIG == 3:
        you = our_yacht(30, -200, 0, sails={'main': True, 'genoa': 'starboard', 'boom': -25}, heel=4); K.wake(you, 60, 10)
        dashes((30, -175, 0), (30, 190, 0), 8, 6, 1.2, yel)
        oth = our_yacht(-230, -125, 90, sails={'main': True, 'genoa': 'starboard', 'boom': -40}, name='other', heel=3); K.wake(oth, 50, 9)
        K.camera((-60, -700, 330), (0, 30, 0), 34)
        labels = [((-470, IZ[0] + 60, 2), 'inshore traffic zone'), ((470, 105, 2), 'lane: traffic west'), ((470, 0, 2), 'separation zone', 'red'),
                  ((470, -105, 2), 'lane: traffic east'), (mast_top(you, 22), 'cross at right angles', 'blue'), (mast_top(oth, 22), 'or follow the lane')]
        arrows = [((-80, -105, 6), (40, -105, 6), 'blue'), ((150, 105, 6), (30, 105, 6), 'blue')]
        note = 'Traffic separation scheme · follow the lane, or cross it at right angles'
    else:
        you = our_yacht(-120, -150, 68, sails={'main': True, 'genoa': 'port', 'boom': 30}, heel=-4); K.wake(you, 60, 10)
        dashes(tuple(Vector((-120, -150, 0)) + fwd(68) * 25), tuple(Vector((-120, -150, 0)) + fwd(68) * 140), 8, 6, 1.2, yel)
        trw, tv, tt = P.trawler((90, 8), 250)
        ins = our_yacht(40, 250, 280, sails={'main': True, 'genoa': 'starboard', 'boom': -30}, name='inshore', k=1.0, heel=3)
        K.camera((-330, -470, 190), (-20, 20, 0), 36)
        labels = [(mast_top(you, 22), '(b) join at a small angle', 'blue'), (tuple(tt + Vector((0, 0, 3))), '(e) separation zone: fishing', 'red'),
                  (mast_top(ins, 22), '(d) inshore zone: under 20 m, sail, fishing')]
        note = 'Rule 10 · join or leave at a small angle; no anchoring in the scheme'
elif FIG == 5:
    K.sea('breeze', size=40.0, repeat=12); K.day_sky(sun_az=230, sun_el=38)
    you = our_yacht(0, 0, 20, sails={'main': True, 'genoa': 'port', 'boom': 28}, heel=-5); K.wake(you, 40, 9)
    cp = pol(20 - 35, 230); h, vis, top = P.merchant(tuple(cp), 45, 80, 'cargo'); P.wake_decal(tuple(cp), 45, 90, 14, stern=40, strength=0.7)
    K.camera(tuple(you.world((-75, 14, 34))), tuple(cp * 0.45 + Vector((0, 0, 2))), 30)
    labels = [(tuple(top + Vector((0, 0, 4))), 'Coaster, heading 045°'), (mast_top(you, 22), 'You: 120° from her bow', 'blue')]
    note = 'Abaft her beam (120° from her bow): overtaking · you keep clear'
elif FIG == 6:
    K.sea('breeze', size=40.0, repeat=14); K.day_sky(sun_az=160, sun_el=42)
    you = our_yacht(0, 0, 0); K.wake(you, 45, 9, 1.3)
    sp = pol(-45, 280); h, vis, top = P.merchant(tuple(sp), 80, 120, 'container'); P.wake_decal(tuple(sp), 80, 110, 18, stern=60, strength=0.7)
    K.camera((150, -260, 190), (-70, 120, 0), 34)
    b = you.world((14, 0.13, 6))
    labels = [(tuple(top + Vector((0, 0, 5))), 'she is to give way', 'red'),
              (tuple(Vector(b) + Vector((52, 30, 2))), 'if you must act: to starboard', 'blue'), (tuple(Vector(b) + Vector((-58, 34, 2))), 'not to port (17(c))', 'red')]
    arrows = [(tuple(Vector(b) + Vector((4, 0, 0))), tuple(Vector(b) + Vector((46, 26, 0))), 'blue'), (tuple(Vector(b) + Vector((-4, 0, 0))), tuple(Vector(b) + Vector((-46, 26, 0))), 'red')]
    note = 'Rule 17 · keep your course and speed; act once she plainly does not'
elif FIG == 11:
    if not os.path.exists(RADAR): subprocess.run(['python3', os.path.abspath(__file__), '--prep'], check=True)
    you = our_yacht(0, 0, 0, k=1.0)
    K.sea('calm', size=30.0, repeat=10); K.day_sky(sun_az=180, sun_el=30, strength=0.18)
    fog((0, 120), 0.02)
    sp = Vector(you.world((10.5, 0.13, 2.0))) + pol(15, 115); sp.z = 0
    h, vis, top = P.merchant(tuple(sp), 0, 70, 'cargo')
    grey = C.simple('ship-fog', '#5d6166', 0.6); K.recolor(vis, lambda c, n: grey)
    for o in vis:
        for sl in o.material_slots: sl.material = grey
    pod_at = you.world((-1.25, -0.32, 4.6))
    root, objs = K.load_model('chartplotter-raymarine-axiom.glb', drop_planes=False)
    bpy.context.view_layer.update(); lo, hi = K.bbox([o for o in objs if o.type == 'MESH'])
    k = 0.235 / (hi.x - lo.x); root.scale = (k,) * 3; bpy.context.view_layer.update(); lo, hi = K.bbox([o for o in objs if o.type == 'MESH'])
    root.location = (root.location.x - (lo.x + hi.x) / 2 + pod_at.x, root.location.y - (lo.y + hi.y) / 2 + pod_at.y, root.location.z - lo.z + pod_at.z)
    root.rotation_euler = (deg(-14), 0, 0)
    img = bpy.data.images.load(RADAR)
    for o in objs:
        for sl in getattr(o, 'material_slots', []):
            if sl.material and sl.material.name.startswith('raymarine--displays'):
                mm, mnt, mb, _ = C.new_mat('axiom-radar')
                uv = mnt.nodes.new('ShaderNodeUVMap'); tx = mnt.nodes.new('ShaderNodeTexImage'); tx.image = img
                mnt.links.new(uv.outputs['UV'], tx.inputs['Vector']); mb.inputs['Base Color'].default_value = (0.01, 0.01, 0.012, 1)
                mnt.links.new(tx.outputs['Color'], mb.inputs['Emission Color']); mb.inputs['Emission Strength'].default_value = 4.0
                mb.inputs['Roughness'].default_value = 0.35; sl.material = mm
    C.obj('pod', C.rbox('pod', (0.3, 0.14, 0.12), 0.035, 4), M['dark'], tuple(pod_at - Vector((0, 0, 0.07))))
    bpy.context.view_layer.update(); plo, phi = K.bbox([o for o in objs if o.type == 'MESH'])
    eye = you.world((-2.05, -0.5, 5.05)); look = you.world((9.0, -0.3, 3.55))
    K.camera(tuple(eye), tuple(look), 24)
    labels = [(tuple(top - Vector((0, 0, 2))), 'Target: her stern, same course'), (tuple(Vector(((plo.x + phi.x) / 2, (plo.y + phi.y) / 2, phi.z + 0.01))), 'target 015° · slower: you overtake', 'blue')]
    note = 'Fog · overtaking her: a turn to port is allowed'; expo = -0.3
elif FIG == 12:
    you = our_yacht(0, 0, 0, k=1.0)
    K.sea('calm', size=30.0, repeat=10); K.day_sky(sun_az=180, sun_el=30, strength=0.18)
    fog((0, 150), 0.0045, (900, 900, 60))
    # anchored: the chain from the stemhead into the sea ahead
    sh = Vector(you.world((10.9, 0.13, 3.7)))
    C.tube('chain', [sh.lerp(sh + Vector((0, 9, -sh.z - 1)), t / 10) + Vector((0, 0, -0.6 * math.sin(math.pi * t / 10))) for t in range(11)], 0.03, 6, 1.0, C.simple('chain', '#3a3c3e', 0.5, 0.8))
    # our bell on the front of the mast, at chest height
    brass = C.simple('brass', '#b58a3a', 0.25, 1.0)
    bp = Vector(you.world((K.MAST.x + 0.32, K.MAST.y, 5.3)))
    bell = C.lathe('bell', [(0, 0.0), (0.06, 0.0), (0.09, -0.04), (0.11, -0.13), (0.15, -0.2), (0.155, -0.215), (0, -0.215)], 40, brass); bell.location = bp
    C.cyl('bell-bracket', 0.015, 0.015, 0.2, 8, brass, tuple(bp + Vector((0, -0.1, 0.02))), rot=(deg(90), 0, 0))
    sp = pol(18, 230); h, vis, top = P.merchant(tuple(sp), 0, 140, 'cargo')
    fl = 140 / 2 - 0.09 * 140
    K.ball(tuple(Vector(sp) + Vector((0, fl, 140 * 0.075 + 140 * 0.02 + 140 * 0.13 - 2.5))), 0.6)
    eye = you.world((3.2, 0.9, 5.5)); look = Vector(eye) + pol(10, 40, -2.5)
    K.camera(tuple(eye), tuple(look), 26)
    labels = [(tuple(bp + Vector((0, 0, 0.12))), 'your bell: rung 5 s every minute', 'blue'), (tuple(top + Vector((0, -20, -6))), 'at anchor, 100 m+: bell forward, gong aft')]
    note = 'Fog signals (Rule 35) · at anchor'; expo = -0.35
elif FIG == 14:
    K.sea('calm', size=30.0, repeat=10, color='#08202b'); K.day_sky(sun_az=40, sun_el=1.5, strength=0.12)
    you = our_yacht(0, 0, 270)
    import kit_night as N
    for o in you.objs:
        if o.type == 'MESH' and (o.name.startswith('Geom3D_genoa') or o.name.startswith('Geom3D_Forestay')):
            for sl in o.material_slots: sl.material = C.simple('furled-cloth', '#a9a69d', 0.8)
    st = you.world((5.45, 0.13, 11.5)); sd = you.world((10.2, 0.58, 4.22)); sn = you.world((-3.75, 0.13, 4.3))
    N.light('steaming', st, 'white', strength=9.0, power=4.0, radius=0.12)
    N.light('port', sd, 'red', strength=8.0, power=3.0, radius=0.12)
    K.camera((6, -62, 6.0), (2, 0, 7.0), 40)
    labels = [(tuple(st + Vector((0, 0, 0.3))), 'masthead light: 6 m+ up, seen 5 M'), (tuple(sd + Vector((0, 0, 0.3))), 'sidelight: ≤ ¾ of its height, 2 M', 'red')]
    note = 'Under power, 21 m · Rule 22 and Annex I'; expo = 0.2
elif FIG == 15:
    K.sea('calm', size=30.0, repeat=10); K.day_sky(sun_az=150, sun_el=40)
    you = our_yacht(0, 0, 210)
    sh = Vector(you.world((10.9, 0.13, 3.7))); f = fwd(210)
    C.tube('chain', [sh.lerp(sh + f * 12 + Vector((0, 0, -sh.z - 1)), t / 10) + Vector((0, 0, -0.8 * math.sin(math.pi * t / 10))) for t in range(11)], 0.035, 6, 1.0, C.simple('chain', '#3a3c3e', 0.5, 0.8))
    hal_top = Vector(you.world((8.6, 0.13, 13.5))); bc = Vector(you.world((8.6, 0.13, 9.6)))
    K.ball(tuple(bc), 0.3)
    C.tube('ball-halyard', [hal_top, bc + Vector((0, 0, 0.3))], 0.008, 6, 1.0, C.simple('hal', '#202224', 0.6))
    C.tube('ball-down', [bc - Vector((0, 0, 0.3)), Vector(you.world((8.6, 0.13, 4.0)))], 0.008, 6, 1.0, C.simple('hal', '#202224', 0.6))
    P.person(tuple(Vector(you.world((9.2, -0.6, 3.75)))), 210 + 160, arms='down', top='#1f5aa6')
    eye = Vector(you.world((14, -24, 5))); K.camera(tuple(eye), tuple(Vector(you.world((7.5, 0.13, 7.0)))), 50)
    labels = [(tuple(bc + Vector((0, 0, 0.45))), 'black ball, 0.6 m across'), (tuple(sh + Vector((0, 0, 0.4)) + f * 4), 'at anchor', 'blue')]
    note = 'Shapes from 20 m: a ball at least 0.6 m across'
elif FIG == 24:
    K.sea('breeze', size=36.0, repeat=10); K.day_sky(sun_az=160, sun_el=35)
    you = our_yacht(0, 0, 300, k=1.0, heel=2)
    wind_to = 215.0
    hand = P.person(tuple(Vector(you.world((-1.2, -0.9, 3.45)))), 300 - 90, arms='side', top='#d23a1e')
    fp = Vector(you.world((-1.2, -1.7, 4.95))); P.red_flare(tuple(fp), wind_to, 0.6)
    P.person(tuple(Vector(you.world((8.0, 0.13, 3.75)))), 300 + 180, arms='up', top='#1f5aa6')
    can = Vector(you.world((-9.0, 2.5, 2.0))); can.z = 0.1
    C.cyl('smoke-can', 0.12, 0.12, 0.3, 16, C.simple('can', '#ff6a00', 0.5), tuple(can))
    plume(can, wind_to, '#ff6a00', n=14, k=0.9, density=0.9, rise=0.35, drift=0.5)
    sp = Vector(you.world((K.MAST.x, K.MAST.y - 0.1, 12.0))); fl = Vector(you.world((K.MAST.x - 0.2, -1.6, 10.6)))
    K.ball(tuple(fl + Vector((0, 0, 0.55))), 0.3)
    P.flag(tuple(fl), wind_to, 0.9, 0.9, color='#1a3f8a')
    labels = [(tuple(fp + Vector((0, 0, 0.6))), 'red hand flare', 'red'), (tuple(can + Vector((0, 0, 7.5)) + fwd(215) * 13), 'orange smoke'),
              (tuple(fl + Vector((0, 0, 1.0))), 'square flag and a ball'), (tuple(Vector(you.world((8.0, 0.13, 6.4)))), 'arms raised and lowered', 'blue')]
    K.camera(tuple(Vector(you.world((10, -30, 9)))), tuple(Vector(you.world((1, 0, 5.5)))), 34)
    note = 'Annex IV · distress signals, a few of them'

C.render(OUT, SAMPLES, SCALE, expo, labels, note, space='blender', arrows=arrows)
