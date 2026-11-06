# Article bareboat-skipper/navigation, figures 1, 3, 5, 6, 8, as Blender renders.
#   1  latitude: the chart table, a paper chart with its latitude scale, dividers on the scale, a parallel rule
#   3  compass: the pedestal steering compass with 119 under the lubber line
#   5  dead reckoning: drone view, motoring east while the tide sets her south: heading line, ground track, DR and EP
#   6  leeway: drone view from astern, close-hauled, the wake trailing to windward of her centreline
#   8  rule of twelfths: a harbour wall with a tide staff, the water at 0.85 m
#   blender --background --factory-startup --python docs/design/blender/art_nav_a.py -- --fig 1 [--out x.jpg]
# The chart and staff textures are drawn with the system Python (Pillow): python3 art_nav_a.py --prep
import os, sys, math, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(HERE, 'textures')
CHART_PNG = os.path.join(TEX, 'nav-chart-latitude.png')
STAFF_PNG = os.path.join(TEX, 'nav-tide-staff.png')
CHART_W, CHART_H = 0.80, 0.5333            # the chart sheet on the table, metres (2400 x 1600 px)
PX_W, PX_H = 2400, 1600
LAT_Y = {50: 200, 40: 1400}                 # pixel rows of 37°50' and 37°40'; 120 px per minute
BOAT_PX = (1300, 500)                       # the 10:30 fix, at 37°47.5'

# ---------------------------------------------------------------- textures (system Python)
def prep():
    from PIL import Image, ImageDraw, ImageFont
    BOLD = '/System/Library/Fonts/Supplemental/Arial Bold.ttf'; REG = '/System/Library/Fonts/Supplemental/Arial.ttf'
    ITAL = '/System/Library/Fonts/Supplemental/Arial Italic.ttf'
    f = lambda p, n: ImageFont.truetype(p, n)
    os.makedirs(TEX, exist_ok=True)
    # --- the chart: pale sea, a coast top right, contours, soundings, a latitude scale down the left border
    im = Image.new('RGB', (PX_W, PX_H), (236, 243, 244)); d = ImageDraw.Draw(im)
    coast = [(1650, 60), (2340, 60), (2340, 900), (2250, 860), (2180, 700), (2050, 640), (1960, 520), (1880, 470), (1800, 330), (1700, 260), (1660, 150)]
    for k, col in ((140, (214, 232, 240)), (80, (200, 225, 238)), (30, (178, 214, 210))):
        d.polygon([(x - k * 0.9, y + k * 0.6) for x, y in coast], fill=col)
    d.polygon(coast, fill=(243, 229, 178), outline=(110, 90, 50))
    d.line(coast + [coast[0]], fill=(90, 72, 40), width=4)
    for x, y, t in ((560, 380, '42'), (820, 720, '38'), (1050, 330, '31'), (1500, 640, '22'), (1700, 760, '14'), (700, 1100, '47'), (1150, 980, '36'),
                    (1450, 1200, '29'), (1550, 1060, '9'), (2250, 960, '11'), (900, 1380, '52'), (1330, 1450, '24'), (400, 800, '45')):
        d.text((x, y), t, font=f(ITAL, 34), fill=(60, 70, 80), anchor='mm')
    d.text((2050, 300), 'ANDROS', font=f(BOLD, 44), fill=(90, 72, 40), anchor='mm')
    # compass rose, lower right
    cx, cy, R = 1900, 1200, 240
    d.ellipse([cx - R, cy - R, cx + R, cy + R], outline=(150, 40, 110), width=4)
    d.ellipse([cx - R + 40, cy - R + 40, cx + R - 40, cy + R - 40], outline=(150, 40, 110), width=2)
    for a in range(0, 360, 5):
        r0 = R - (26 if a % 30 == 0 else 14); t = math.radians(a)
        d.line([(cx + math.sin(t) * r0, cy - math.cos(t) * r0), (cx + math.sin(t) * R, cy - math.cos(t) * R)], fill=(150, 40, 110), width=3 if a % 30 == 0 else 2)
    for a in range(0, 360, 30):
        t = math.radians(a); d.text((cx + math.sin(t) * (R - 56), cy - math.cos(t) * (R - 56)), str(a), font=f(REG, 24), fill=(150, 40, 110), anchor='mm')
    d.polygon([(cx, cy - R + 48), (cx - 16, cy), (cx + 16, cy)], fill=(150, 40, 110))
    # frame and the latitude scale: alternate black and white minutes, tenths ticked, labels every 5'
    x0, x1 = 60, 130
    d.rectangle([x0, 40, PX_W - 40, PX_H - 40], outline=(20, 20, 20), width=4)
    d.line([(x1, 40), (x1, PX_H - 40)], fill=(20, 20, 20), width=3)
    y50, y40 = LAT_Y[50], LAT_Y[40]; mpx = (y40 - y50) / 10
    for m in range(-1, 12):
        ya, yb = y50 + m * mpx, y50 + (m + 1) * mpx
        ya, yb = max(ya, 42), min(yb, PX_H - 42)
        if ya < yb: d.rectangle([x0 + 2, ya, x0 + 30, yb], fill=(20, 20, 20) if m % 2 == 0 else (250, 250, 248))
    for k in range(-10, 125):
        y = y50 + k * mpx / 10
        if 42 < y < PX_H - 42: d.line([(x0 + 30, y), (x0 + (60 if k % 10 == 0 else 50 if k % 5 == 0 else 42), y)], fill=(20, 20, 20), width=2)
    for mins, txt in ((50, "50'"), (45, "45'"), (40, "40'")):
        y = y50 + (50 - mins) * mpx
        d.text((x1 + 14, y), txt, font=f(BOLD, 36), fill=(20, 20, 20), anchor='lm')
    d.text((x1 + 14, y50 - 46), "37°", font=f(BOLD, 36), fill=(20, 20, 20), anchor='lm')
    # the two parallels across the chart, and a meridian
    for y in (y50, y40): d.line([(x1, y), (PX_W - 40, y)], fill=(70, 70, 70), width=3)
    d.line([(1200, 40), (1200, PX_H - 40)], fill=(70, 70, 70), width=3)
    d.text((1200, 70), "24°40'E", font=f(BOLD, 30), fill=(20, 20, 20), anchor='mm')
    # pencil: the track and the 10:30 fix, and the line ruled from the fix to the scale
    pencil = (70, 70, 74)
    d.line([(420, 1260), BOAT_PX], fill=pencil, width=4)
    bx, by = BOAT_PX
    d.ellipse([bx - 26, by - 26, bx + 26, by + 26], outline=pencil, width=4); d.ellipse([bx - 6, by - 6, bx + 6, by + 6], fill=pencil)
    d.text((bx + 40, by - 40), '10:30', font=f(REG, 40), fill=pencil, anchor='lm')
    for xx in range(x1 + 10, bx - 40, 34): d.line([(xx, by), (xx + 18, by)], fill=pencil, width=3)
    im.save(CHART_PNG)
    # --- the tide staff: 1 px = 1 mm, 0.15 x 3.2 m, from -0.2 m to 3.0 m; E-pattern graduations, metre numbers red
    W, Hh = 150, 3200
    im = Image.new('RGB', (W, Hh), (245, 245, 238)); d = ImageDraw.Draw(im)
    Y = lambda m: Hh - (m + 0.2) * 1000
    for cm in range(-20, 301, 2):
        y = Y(cm / 100)
        if cm % 10 == 0:
            col = (190, 30, 30) if (cm // 100) % 2 else (20, 20, 20)
            # E-shape: the tens of cm as solid blocks 5 cm tall, alternate sides
            if cm % 20 == 0: d.rectangle([12, y - 50, 70, y], fill=col)
            d.line([(12, y), (W - 12, y)], fill=col, width=4)
        else:
            d.line([(12, y), (40, y)], fill=(40, 40, 40), width=2)
    for m in range(0, 4):
        y = Y(m); d.rectangle([80, y - 120, W - 10, y - 8], fill=(245, 245, 238))
        d.text((W - 38, y - 64), str(m), font=f(BOLD, 110), fill=(190, 30, 30), anchor='mm')
    d.line([(10, 0), (10, Hh)], fill=(30, 30, 30), width=6)
    im.save(STAFF_PNG)
    print('wrote', CHART_PNG, STAFF_PNG)

try:
    import bpy
except ImportError:
    bpy = None
if bpy is None:
    if '--prep' in sys.argv: prep()
    sys.exit(0)

# ---------------------------------------------------------------- Blender
sys.path.insert(0, HERE)
import bmesh
from mathutils import Vector, Matrix
import common as C, kit as K, kit_instruments as KI

OUTDIR = os.path.join(HERE, '..', 'figure-style', 'articles', 'bareboat-skipper', 'navigation')
arg = C.cli(); FIG = arg('--fig', 1); SAMPLES = arg('--samples', 192); SCALE = arg('--scale', 100)
OUT = arg('--out', os.path.join(OUTDIR, f'{FIG}-3d.jpg'))
if not (os.path.exists(CHART_PNG) and os.path.exists(STAFF_PNG)):
    subprocess.run(['python3', os.path.abspath(__file__), '--prep'], check=True)

_load = K.load_yacht
def _yacht(*a, **k):
    """kit.load_yacht, minus the spinnaker's pale triangle and tack line the model keeps when the spinnaker is down."""
    yt = _load(*a, **k)
    for o in yt.objs:
        anc, q = [], o.parent
        while q: anc.append(q.name); q = q.parent
        if o.type == 'MESH' and (any(n.startswith('SPINNAKER') for n in anc) or
                                 any(sl.material and sl.material.name.startswith(('[Color_F12]', '[Color_H09]')) for sl in o.material_slots)):
            o.hide_render = True
    return yt
K.load_yacht = _yacht

def drone(c, D, az=180.0, el=37.0, lens=32.0):
    a, e = math.radians(az), math.radians(el)
    eye = Vector(c) + Vector((math.sin(a) * math.cos(e), math.cos(a) * math.cos(e), math.sin(e))) * D
    return K.camera(tuple(eye), tuple(c), lens)

def img_plane(name, w, h, path, loc, rough=0.8):
    me = bpy.data.meshes.new(name)
    me.from_pydata([(-w / 2, -h / 2, 0), (w / 2, -h / 2, 0), (w / 2, h / 2, 0), (-w / 2, h / 2, 0)], [], [(0, 1, 2, 3)])
    uv = me.uv_layers.new(name='UVMap'); uv.data.foreach_set('uv', [0, 0, 1, 0, 1, 1, 0, 1])
    return C.obj(name, me, KI.image_mat(name, path, rough), Vector(loc))

def seg(name, a, b, r1, r2, mat, seg=24):
    """A tapered rod from a (radius r1) to b (radius r2)."""
    a, b = Vector(a), Vector(b); L = (b - a).length
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r1, radius2=r2, depth=L)
    for fc in bm.faces: fc.smooth = True
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = C.obj(name, me, mat, (a + b) / 2)
    o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = (b - a).normalized().to_track_quat('Z', 'Y')
    return o

def glow_mat(name, color, strength=2.0):
    m, nt, b, out = C.new_mat(name)
    C.setin(b, 'Base Color', C.lin(color)); C.setin(b, 'Roughness', 0.6)
    C.setin(b, 'Emission Color', C.lin(color)); C.setin(b, 'Emission Strength', strength)
    return m

def strip(name, a, b, w, mat, z=0.35):
    """A flat band on the water from a to b (x, y), w wide, floating at height z."""
    a, b = Vector((a[0], a[1], 0)), Vector((b[0], b[1], 0)); d = (b - a); n = Vector((-d.y, d.x, 0)).normalized() * w / 2
    me = bpy.data.meshes.new(name); me.from_pydata([tuple(a + n), tuple(b + n), tuple(b - n), tuple(a - n)], [], [(0, 1, 2, 3)])
    o = C.obj(name, me, mat, (0, 0, z)); o.visible_shadow = False
    return o

def dashed(name, a, b, w, mat, dash=4.0, gap=3.0, z=0.35):
    a, b = Vector(a), Vector(b); L = (b - a).length; u = (b - a) / L; s = 0.0
    while s < L:
        e = min(s + dash, L); strip(name, tuple(a + u * s), tuple(a + u * e), w, mat, z); s = e + gap

def ring(name, at, R, mat, z=0.4):
    o = C.obj(name, KI._torus(R, R * 0.09), mat, (at[0], at[1], z)); o.visible_shadow = False
    return o

def raise_sea(dz):
    for o in bpy.data.objects:
        if o.name.startswith(('ocean', 'far-sea')): o.location.z += dz

def hdg_vec(h): a = math.radians(h); return Vector((math.sin(a), math.cos(a), 0))

C.reset()
M = K.mats()
labels, arrows, note, expo = [], [], None, -0.6

if FIG == 1:
    # the chart table: teak top with a fiddle, the chart on it, soft cabin light from above and a portlight
    jo = KI.joinery_mat()
    C.obj('table', C.rbox('table', (1.1, 0.75, 0.04), 0.006, 2), jo, (0.05, 0.02, -0.02))
    C.obj('fiddle-front', C.rbox('fiddle', (1.1, 0.025, 0.035), 0.008, 2), jo, (0.05, -0.36, 0.015))
    C.obj('fiddle-back', C.rbox('fiddle', (1.1, 0.025, 0.06), 0.008, 2), jo, (0.05, 0.40, 0.03))
    KI.wall('bulkhead', -0.75, 0.75, -0.05, 0.6, 0.41, jo)
    sw = KI.wall('side', -0.6, 0.6, -0.05, 0.6, 0.0, jo); sw.rotation_euler = (0, 0, math.radians(90)); sw.location = (-0.52, 0, 0)
    chart = img_plane('chart', CHART_W, CHART_H, CHART_PNG, (0.0, 0.0, 0.0012), 0.85)
    P = lambda px, py: Vector(((px / PX_W - 0.5) * CHART_W, (0.5 - py / PX_H) * CHART_H, 0.0012))
    # the parallel rule: two black acrylic bars joined by brass links, its top edge on the fix's parallel
    acry = C.simple('acrylic', '#141618', 0.18, coat=1.0); brass = C.simple('brass', '#b08a3e', 0.28, 1.0)
    yb = P(0, BOAT_PX[1]).y; xa, xb = P(140, 0).x, P(1250, 0).x
    C.obj('rule-a', C.rbox('rule', (xb - xa, 0.055, 0.006), 0.002, 2), acry, ((xa + xb) / 2, yb - 0.0275, 0.004))
    C.obj('rule-b', C.rbox('rule', (xb - xa, 0.055, 0.006), 0.002, 2), acry, ((xa + xb) / 2 + 0.02, yb - 0.115, 0.004))
    for x in (xa + 0.08, xb - 0.08):
        C.obj('link', C.rbox('link', (0.016, 0.075, 0.003), 0.003, 2), brass, (x + 0.01, yb - 0.07, 0.0085)).rotation_euler = (0, 0, math.radians(-15))
    # dividers: points on the latitude scale at 37°47.5' and 37°50' (2.5'), the hinge raised
    steel = C.simple('divider-steel', '#c9ccd0', 0.22, 1.0)
    pa, pb = P(92, LAT_Y[50] + 2.5 * 120), P(92, LAT_Y[50])
    hinge = (pa + pb) / 2 + Vector((0.09, -0.11, 0.10))
    for nm, p0 in (('a', pa), ('b', pb)):          # brass legs with short steel points, easy to see on the white chart
        q = p0 + (hinge - p0).normalized() * 0.018
        seg('point-' + nm, p0, q, 0.0006, 0.0022, steel); seg('leg-' + nm, q, hinge, 0.0028, 0.0075, brass)
    C.cyl('hinge', 0.009, 0.009, 0.012, 24, brass, hinge, (math.radians(90), 0, 0))
    seg('knob', hinge, hinge + Vector((0.004, 0, 0.022)), 0.005, 0.003, brass)
    # a pencil lying by the fix, and a soft rubber
    pen = C.cyl('pencil', 0.0042, 0.0042, 0.17, 6, C.simple('pencil', '#e8b818', 0.45, coat=0.4), P(1550, 1080) + Vector((0, 0, 0.004)), (0, math.radians(90), math.radians(30)))
    tip = P(1550, 1080) + Vector((math.cos(math.radians(30)) * 0.085, math.sin(math.radians(30)) * 0.085, 0.004))
    seg('pencil-tip', tip, tip + Vector((math.cos(math.radians(30)) * 0.016, math.sin(math.radians(30)) * 0.016, -0.002)), 0.0042, 0.0006, C.simple('wood', '#d9b482', 0.7))
    # light: a warm dome light overhead, daylight through a portlight to the right; a dim world
    K.day_sky(sun_az=200, sun_el=40, strength=0.05)
    KI.area_light((0.0, -0.15, 0.9), (0.0, 0.0, 0.0), 12, 0.35, (1.0, 0.86, 0.68))
    KI.area_light((0.9, -0.3, 0.45), (0.0, 0.05, 0.0), 16, 0.4, (0.85, 0.92, 1.0))
    K.camera((-0.10, -0.50, 0.44), (-0.19, 0.04, 0.0), 34)
    labels = [(tuple(pa + Vector((0.0, 0, 0.02))), "37°47.5′ N", 'blue')]
    note = "Parallels 10′ apart · three-quarters up is 7.5′"; expo = -0.2

elif FIG == 3:
    C.lathe('bowl', [(0.0, -0.02), (0.075, -0.02), (0.085, 0.0), (0.083, 0.012), (0.07, 0.016), (0.0, 0.016)], 96, M['dark'])
    C.lathe('pedestal', [(0.0, -0.75), (0.06, -0.75), (0.055, -0.03), (0.07, -0.02), (0.0, -0.02)], 64, C.simple('pedestal', '#cfd2d4', 0.25, 1.0))
    card = KI.disc('card', 0.058, KI.image_mat('card', KI.face_png('card'), 0.45), (0, 0, 0.022), normal='Z+')
    card.rotation_euler = (0, 0, math.radians(119))            # 119 comes to the forward lubber line (+Y)
    C.obj('lubber', C.rbox('lubber', (0.003, 0.004, 0.02), 0.0005, 1), C.simple('lubber', '#e0201a', 0.4, coat=0.5), (0, 0.062, 0.03))
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=64, v_segments=32, radius=0.07)
    for v in list(bm.verts):
        if v.co.z < 0: v.co.z = 0
    me = bpy.data.meshes.new('dome'); bm.to_mesh(me); bm.free(); me.shade_smooth()
    C.obj('dome', me, KI.glass_mat('dome-glass'), (0, 0, 0.016))
    K.sea('breeze', center=(0, 0)); K.day_sky(sun_az=230, sun_el=45)
    raise_sea(-1.4)
    KI.wall('sole', -1.5, 1.5, -1.5, 1.5, 0, M['teak'])
    sole = bpy.data.objects['sole']; sole.data.vertices.foreach_set('co', [-1.2, -1.5, -0.75, 1.2, -1.5, -0.75, 1.2, 1.5, -0.75, -1.2, 1.5, -0.75]); sole.data.update()
    K.camera((0.0, -0.46, 0.36), (0, 0.035, -0.02), 40)
    labels = [((0, 0.065, 0.06), '119°C · steer', 'blue')]
    note = '120°T − 3°E = 117°M · + 2°W = 119°C'; expo = -0.4

elif FIG == 5:
    # one hour, 6 M by log east, 1.5 M of tide south, shrunk to 120 m by 30 m: start, DR ahead on the heading, EP south of it
    K.sea('calm', size=30.0, repeat=14); K.day_sky(sun_az=210, sun_el=45)
    S0, DR, EP = Vector((-70, 12, 0)), Vector((50, 12, 0)), Vector((50, -18, 0))
    you = K.load_yacht(name='you').place(EP.x - 7, EP.y, heading=90); K.wake(you, 34, 8, 1.2)
    white = glow_mat('heading-line', '#f4f1e6', 1.2); red = glow_mat('ground-track', '#c4161c', 0.8); yel = glow_mat('spot', '#ffc400', 2.5)
    dashed('heading', S0, DR, 0.6, white)
    strip('track', S0, EP + Vector((-14, 0, 0)), 0.7, red)
    for p in (S0, DR, EP): ring('spot', p, 2.6, yel)
    arrows = [((DR.x + 9, DR.y - 2, 1.0), (DR.x + 9, EP.y + 5, 1.0), 'blue')]
    labels = [((S0.x, S0.y, 3.0), '10:00 fix'), ((DR.x, DR.y, 3.0), 'DR', 'yellow'), ((EP.x + 6, EP.y - 3, 4.0), 'EP', 'yellow'),
              ((DR.x + 9, (DR.y + EP.y) / 2 + 2, 2.0), 'tide 1.5 kn', 'blue'), ((-10, -2, 2.0), 'ground track', 'red'), ((-10, 14, 2.0), 'heading 090°')]
    drone(Vector((-8, -4, 0)), 150, az=190, el=52, lens=34)
    note = 'Course 090°T, log 6 M · tide 180°T 1.5 kn → EP'

elif FIG == 6:
    # close-hauled heading 050°T with the wind from the north: port tack, heeled to starboard, slipping 5° to leeward
    K.sea('breeze'); K.day_sky(sun_az=150, sun_el=42)
    you = K.load_yacht(name='you', sails={'main': True, 'genoa': 'starboard', 'boom': -10}).place(0, 0, heading=50, heel=14)
    w = K.wake(you, 46, 7, 1.1); w.rotation_euler = (0, 0, math.radians(-5))     # the wake runs back along the water track
    bow = you.world((10.8, 0.13, K.WL))
    white = glow_mat('heading-line', '#f4f1e6', 1.2); yel = glow_mat('water-track', '#ffc400', 2.0)
    dashed('heading', (bow.x, bow.y, 0), tuple(Vector((bow.x, bow.y, 0)) + hdg_vec(50) * 46), 0.45, white, 3.0, 2.2)
    strip('track', (bow.x, bow.y), tuple(Vector((bow.x, bow.y, 0)) + hdg_vec(55) * 47), 0.5, yel)
    e1 = Vector((bow.x, bow.y, 0)) + hdg_vec(50) * 47; e2 = Vector((bow.x, bow.y, 0)) + hdg_vec(55) * 48
    c = Vector((bow.x, bow.y, 0)) + hdg_vec(52) * 30
    wa = Vector((bow.x, bow.y, 0)) + hdg_vec(20) * 22
    arrows = [((wa.x, wa.y + 12, 6.0), (wa.x, wa.y - 2, 6.0), 'blue')]
    h1 = Vector((bow.x, bow.y, 0)) + hdg_vec(50) * 30 + hdg_vec(320) * 7; t1 = e2 + hdg_vec(140) * 5
    labels = [((h1.x, h1.y, 1.5), 'heading 050°'), ((t1.x, t1.y, 1.5), 'water track 055°', 'yellow'),
              ((wa.x, wa.y + 13, 6.0), 'Wind N', 'blue')]
    mast = you.world((K.MAST.x, K.MAST.y, K.WL)); drone(Vector((mast.x, mast.y, 0)) + hdg_vec(50) * 16, 74, az=228, el=36, lens=30)
    note = 'Heading 050°T · leeway 5° · water track 055°T'

elif FIG == 8:
    # a harbour wall, its sea face at y = 0 facing -y; chart datum at z = 0, the water at 0.85 m
    WATER = 0.85
    m, nt, b, _ = C.new_mat('quay-wall')
    oc = C.obj_coords(nt); sep = C.node(nt, 'ShaderNodeSeparateXYZ'); C.link(nt, oc, sep.inputs['Vector'])
    n1 = C.noise(nt, oc, 3.0, 6.0); n2 = C.noise(nt, oc, 40.0, 4.0)
    zt = C.math_(nt, 'ADD', sep.outputs['Z'], C.math_(nt, 'MULTIPLY', n1, 0.35))
    band = C.ramp(nt, [(0.0, '#1b2416'), (0.40, '#2c3a22'), (0.44, '#3b392f'), (0.88, '#4f4a3f'), (0.93, '#8f897d'), (1.0, '#9a948a')])
    zn = C.math_(nt, 'DIVIDE', C.math_(nt, 'ADD', zt, 0.6), 3.6); C.link(nt, zn, band.inputs['Fac'])
    st = C.ramp(nt, [(0.3, (0.82, 0.82, 0.82, 1)), (0.7, (1, 1, 1, 1))]); C.link(nt, n2, st.inputs['Fac'])
    C.link(nt, C.mixc(nt, 1.0, band.outputs['Color'], st.outputs['Color'], 'MULTIPLY'), b.inputs['Base Color'])
    wet = C.math_(nt, 'LESS_THAN', zt, 2.3)
    rr = C.node(nt, 'ShaderNodeMix', data_type='FLOAT'); C.link(nt, wet, rr.inputs['Factor']); C.setin(rr, 2, 0.88); C.setin(rr, 3, 0.45); C.link(nt, rr.outputs[0], b.inputs['Roughness'])
    # blocks: horizontal courses and staggered joints
    C.bump_from(nt, b, C.math_(nt, 'MULTIPLY', n2, 1.0), 0.6, 0.004)
    wall = C.obj('quay', C.rbox('quay', (40, 3.0, 6.0), 0.02, 2), m, (0, 1.5, -0.5))
    C.obj('cope', C.rbox('cope', (40, 0.6, 0.25), 0.04, 3), C.concrete_mat('cope'), (0, 0.25, 2.62))
    # joints between blocks, dark lines on the face
    jm = C.simple('joint', '#2e2b26', 0.95)
    for zz in (0.0, 0.9, 1.8):
        C.obj('course', C.rbox('course', (40, 0.02, 0.025), 0.0, 1), jm, (0, -0.005, zz))
    for i, xx in enumerate(range(-20, 21, 2)):
        for zz in (0.45, 1.35, 2.2):
            C.obj('vjoint', C.rbox('vj', (0.025, 0.02, 0.85), 0.0, 1), jm, (xx + (1 if int(zz * 10) % 2 else 0), -0.005, zz))
    # the tide staff, bolted to the wall
    staff = img_plane('staff', 0.15, 3.2, STAFF_PNG, (0, -0.012, 1.4), 0.5); staff.rotation_euler = (math.radians(90), 0, 0)
    C.obj('staff-back', C.rbox('sb', (0.17, 0.01, 3.22), 0.002, 1), C.simple('staff-back', '#d9d9d0', 0.6), (0, -0.006, 1.4))
    for zz in (0.1, 1.4, 2.7): C.cyl('bolt', 0.008, 0.008, 0.01, 12, M['satin'], (0, -0.016, zz), (math.radians(90), 0, 0))
    K.sea('calm', size=30.0, repeat=10); raise_sea(WATER)
    K.day_sky(sun_az=150, sun_el=38)
    # a yacht lying alongside further along, and a ladder in the wall
    y = K.load_yacht(name='moored').place(11.5, -2.15, heading=270); y.root.location.z = WATER
    for zz in [i * 0.3 - 0.4 for i in range(11)]: C.cyl('rung', 0.012, 0.012, 0.42, 10, M['galv'], (-3.5, -0.08, zz), (0, math.radians(90), 0))
    for xx in (-3.71, -3.29): C.cyl('rail', 0.016, 0.016, 3.4, 10, M['galv'], (xx, -0.08, 1.0))
    K.camera((-1.9, -4.3, 1.35), (3.0, 0, 1.25), 30)
    labels = [((0.0, -0.03, WATER), '10:00 · 0.85 m', 'red')]
    note = 'LW 08:00 0.4 m · HW 14:00 2.2 m'; expo = -0.5

C.render(OUT, SAMPLES, SCALE, expo, labels, note, space='blender', arrows=arrows)
