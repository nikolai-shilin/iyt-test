# Blender scene figures for vhf-radio-operator (the chart, encounter and lights ones), matching the schematics in
# article-figures.html:
#   channels 7  helm view: a ship on our starboard bow calls us on 16, asks for 13
#   channels 8  aerial: a high island between us and a friend 6 miles off; the radio path blocked
#   channels 9  aerial: a coast station mast high on a mountain hears us; friends behind a headland do not
#   distress 4  from the deck: a lighthouse on a headland bearing 040°, 3 miles
#   distress 6  night: a red parachute flare high on the starboard bow
#   gmdss 1     aerial: a coast station and the dome of its VHF range (sea area A1), our yacht inside
#   gmdss 2     an EPIRB afloat, the satellite overhead (406 MHz), a lifeboat homing on 121.5 MHz
#   gmdss 3     the plotter at the helm on radar: a SART's line of 12 dots
#   gmdss 5     helm view: a small boat ahead, the plotter showing no AIS targets
#   licences 3  a handheld VHF on a taverna table ashore; our yacht at anchor off the beach
#   sar 1       aerial: a yacht holed and sinking, the coast station on the coast, our yacht 3 miles off
#   sar 4       aerial: an island between the casualty and the lifeboat; our yacht in sight of both relays
#   sar 5       a rescue helicopter over our port quarter, the wire down, the yacht steady, wind 30° on the port bow
#   urgency 2   no engine, drifting in F6 onto a rocky lee shore
#   blender --background --factory-startup --python docs/design/blender/art_vhf_scenes.py -- --article sar --fig 5
#        [--samples 192] [--scale 100] [--out x.jpg]
# The two plotter screens (radar with a SART, chart with no AIS targets) are drawn by the system Python (Pillow):
#   python3 docs/design/blender/art_vhf_scenes.py --prep        (the scene runs it itself when they are missing)
import os, sys, math, random, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(HERE, 'textures')
SART_PNG = os.path.join(TEX, 'vhf-axiom-sart.png')
NOAIS_PNG = os.path.join(TEX, 'vhf-axiom-noais.png')
FRONT_BOX = (70, 72, 645, 432)          # the screen glass on axiom-front.png (828 x 481)
RW, RH = 920, 610                       # the radar picture, before it is fitted into the screen box
R_CX, R_CY, R_R = RW // 2, RH // 2 + 22, 268
SART_BRG, SART_R0, SART_STEP = 128.0, 0.34, 0.056   # the SART line: bearing, first dot (fraction of R), spacing

def radar_xy(brg, frac):
    a = math.radians(brg); return R_CX + frac * R_R * math.sin(a), R_CY - frac * R_R * math.cos(a)

def front_xy(x, y):
    """Radar-picture pixel -> pixel on the plotter's front texture."""
    x0, y0, x1, y1 = FRONT_BOX
    return x0 + x / RW * (x1 - x0), y0 + y / RH * (y1 - y0)

def prep():
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    F = lambda n: ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', n)
    front = Image.open(os.path.join(TEX, 'axiom-front.png')).convert('RGB')
    x0, y0, x1, y1 = FRONT_BOX
    # --- radar, heading up, 6 nm: sea clutter, a coast to the north-west, the SART's 12 dots
    im = Image.new('RGB', (RW, RH), (4, 10, 22)); d = ImageDraw.Draw(im)
    for k in range(1, 4):
        r = R_R * k / 3; d.ellipse([R_CX - r, R_CY - r, R_CX + r, R_CY + r], outline=(40, 120, 150), width=2)
    for a in range(0, 360, 30):
        t = math.radians(a); d.line([(R_CX, R_CY), (R_CX + R_R * math.sin(t), R_CY - R_R * math.cos(t))], fill=(18, 55, 75), width=1)
    d.line([(R_CX, R_CY), (R_CX, R_CY - R_R)], fill=(220, 230, 240), width=3)
    glow = Image.new('RGB', (RW, RH), (0, 0, 0)); g = ImageDraw.Draw(glow); rnd = random.Random(4)
    for _ in range(240):
        r = rnd.random() ** 1.7 * 55; t = rnd.random() * math.tau
        g.ellipse([R_CX + r * math.sin(t) - 2, R_CY - r * math.cos(t) - 2, R_CX + r * math.sin(t) + 2, R_CY - r * math.cos(t) + 2], fill=(190, 150, 30))
    for k in range(70):   # a stretch of coast echo to the north-west, out near the edge
        t = math.radians(290 + k * 0.55); r = R_R * (0.86 + 0.06 * math.sin(k * 0.4) + rnd.random() * 0.03)
        px, py = R_CX + r * math.sin(t), R_CY - r * math.cos(t)
        if math.hypot(px - R_CX, py - R_CY) < R_R - 4: g.ellipse([px - 5, py - 4, px + 5, py + 4], fill=(200, 160, 40))
    for k in range(12):   # the SART: 12 dots in a line, the first one where the liferaft is
        px, py = radar_xy(SART_BRG, SART_R0 + k * SART_STEP)
        g.ellipse([px - 8, py - 5, px + 8, py + 5], fill=(255, 215, 60))
    glow = glow.filter(ImageFilter.GaussianBlur(1.2)); im = Image.composite(glow, im, glow.convert('L').point(lambda v: 255 if v > 8 else 0))
    d = ImageDraw.Draw(im)
    d.ellipse([R_CX - 9, R_CY - 9, R_CX + 9, R_CY + 9], fill=(230, 236, 240))
    d.rectangle([0, 0, RW, 58], fill=(10, 18, 30))
    d.text((24, 14), 'RADAR', font=F(30), fill=(230, 236, 240)); d.text((180, 18), 'H-UP  6 nm', font=F(24), fill=(150, 175, 190))
    d.text((RW - 300, 18), 'GAIN AUTO  SEA AUTO', font=F(22), fill=(150, 175, 190))
    f = front.copy(); f.paste(im.resize((x1 - x0, y1 - y0), Image.LANCZOS), (x0, y0)); f.save(SART_PNG); print('wrote', SART_PNG)
    # --- chart, heading up: land, depth contours, our boat, and no AIS targets anywhere
    im = Image.new('RGB', (RW, RH), (178, 214, 236)); d = ImageDraw.Draw(im)
    d.polygon([(0, 58), (330, 58), (300, 120), (210, 170), (120, 160), (40, 230), (0, 250)], fill=(232, 214, 160))
    d.polygon([(RW, 58), (RW - 260, 58), (RW - 230, 110), (RW - 120, 150), (RW, 140)], fill=(232, 214, 160))
    for k, c in enumerate(((150, 196, 226), (205, 228, 242))):
        o = 26 + k * 34
        d.line([(0, 250 + o), (40 + o * 0.6, 230 + o), (120, 160 + o), (210, 170 + o), (300, 120 + o), (330 + o, 58)], fill=(110, 150, 190), width=2)
        d.line([(RW, 140 + o), (RW - 120, 150 + o), (RW - 230 - o * 0.3, 110 + o), (RW - 260 - o, 58)], fill=(110, 150, 190), width=2)
    for (px, py, t) in ((420, 210, '23'), (520, 330, '41'), (300, 420, '38'), (680, 260, '19'), (640, 470, '52'), (180, 330, '12')):
        d.text((px, py), t, font=F(18), fill=(70, 90, 110))
    bx, by = RW // 2, RH - 150
    d.line([(bx, by), (bx, 70)], fill=(30, 30, 30), width=2)                     # heading line
    d.polygon([(bx, by - 26), (bx - 15, by + 18), (bx + 15, by + 18)], fill=(20, 20, 24))
    d.rectangle([0, 0, RW, 58], fill=(10, 18, 30))
    d.text((24, 14), 'CHART', font=F(30), fill=(230, 236, 240)); d.text((175, 18), 'H-UP  0.5 nm', font=F(24), fill=(150, 175, 190))
    d.text((RW - 330, 16), 'AIS: 0 targets', font=F(28), fill=(255, 210, 70))
    d.rectangle([0, RH - 52, RW, RH], fill=(10, 18, 30))
    d.text((24, RH - 40), 'SOG 5.8 kn   COG 002°', font=F(24), fill=(200, 210, 220))
    f = front.copy(); f.paste(im.resize((x1 - x0, y1 - y0), Image.LANCZOS), (x0, y0)); f.save(NOAIS_PNG); print('wrote', NOAIS_PNG)

if __name__ == '__main__' and '--prep' in sys.argv:
    prep(); sys.exit(0)

sys.path.insert(0, HERE)
import bpy, bmesh
from mathutils import Vector, Euler, Matrix, noise as mnoise
import common as C, kit as K, kit_world as KW, kit_night as N

arg = C.cli(); ART = arg('--article', 'channels'); FIG = arg('--fig', 7); SAMPLES = arg('--samples', 192); SCALE = arg('--scale', 100)
OUT = arg('--out', os.path.join(HERE, '..', 'figure-style', 'articles', 'vhf-radio-operator', ART, f'{FIG}-3d.jpg'))
def deg(a): return math.radians(a)
C.reset()

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

labels, arrows, note, extra, expo = [], [], None, None, -0.6

# ---------------------------------------------------------------------------------------------------- helpers
def sailing(name, hdg, wind, x, y, k=1.0):
    """A yacht under sail, boom and genoa to leeward, heeled to the wind; k scales her up for far aerial views."""
    rel = ((wind - hdg + 540) % 360) - 180; stbd = rel > 0; off = abs(rel)
    boom = 10 if off < 60 else (35 if off < 120 else 60)
    yt = K.load_yacht(name=name, sails={'main': True, 'genoa': 'port' if stbd else 'starboard', 'boom': boom if stbd else -boom})
    yt.place(x, y, heading=hdg, heel=(-12 if stbd else 12) if off < 120 else (-5 if stbd else 5))
    yt.root.scale = (k,) * 3
    return yt

def motoring(name, hdg, x, y, k=1.0, heel=0.0):
    yt = K.load_yacht(name=name).place(x, y, heading=hdg, heel=heel); yt.root.scale = (k,) * 3
    return yt

def top(yt, h=21.0):
    """A point just above her masthead (model space), for pills and radio paths."""
    return yt.world((K.MAST.x, K.MAST.y, h + K.WL))

def drone(c, dist, az, el, lens=32.0):
    a, e = deg(az), deg(el); c = Vector(c)
    eye = c + Vector((math.sin(a) * math.cos(e), math.cos(a) * math.cos(e), math.sin(e))) * dist
    return K.camera(tuple(eye), tuple(c), lens)

def flat_mat(name, color, emit=0.0, rough=0.5):
    m, nt, b, _ = C.new_mat(name)
    C.setin(b, 'Base Color', C.lin(color)); C.setin(b, 'Roughness', rough)
    if emit: C.setin(b, 'Emission Color', C.lin(color)); C.setin(b, 'Emission Strength', emit)
    return m

def rock_mat(name='rock', fog=0.0):
    m, nt, b, out = C.new_mat(name)
    oc = C.obj_coords(nt)
    rock = C.ramp(nt, [(0.3, '#6f6656'), (0.6, '#8d8370'), (0.8, '#5f6248')]); C.link(nt, C.noise(nt, oc, 0.02, 6.0), rock.inputs['Fac'])
    scrub = C.ramp(nt, [(0.35, (1, 1, 1, 1)), (0.65, C.lin('#6c7350'))]); C.link(nt, C.noise(nt, oc, 0.18, 6.0), scrub.inputs['Fac'])
    C.link(nt, C.mixc(nt, 1.0, rock.outputs['Color'], scrub.outputs['Color'], 'MULTIPLY'), b.inputs['Base Color']); b.inputs['Roughness'].default_value = 0.95
    C.bump_from(nt, b, C.noise(nt, oc, 0.3, 8.0), 0.6, 1.0)
    if fog: K.distance_fog(nt, b.outputs[0], out.inputs['Surface'], half=fog)
    return m

_LAND = {}
def land_mat(fog=0.0):
    """kit_world's dry hillside, hazed with distance when fog (m) is given."""
    key = round(fog)
    if key in _LAND: return _LAND[key]
    m = KW.land_mat()
    if fog:
        nt = m.node_tree; b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'); out = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')
        K.distance_fog(nt, b.outputs[0], out.inputs['Surface'], half=fog)
    _LAND[key] = m; return m

def aerial_land_mat(fog=6000.0, name='aerial-land', haze=2.5):
    """Dry Mediterranean land seen from a kilometre or more: olive and ochre in broad soft patches (no camouflage
    blotches), darker maquis in the hollows, bare rock on the steep slopes, a thin pale beach, haze with distance."""
    m, nt, b, out = C.new_mat(name)
    oc = C.obj_coords(nt); z = KW.world_z(nt)
    g = C.node(nt, 'ShaderNodeNewGeometry'); sn = C.node(nt, 'ShaderNodeSeparateXYZ'); C.link(nt, g.outputs['Normal'], sn.inputs['Vector'])
    big = C.ramp(nt, [(0.3, '#7a7148'), (0.5, '#646638'), (0.7, '#47512a')]); C.link(nt, C.noise(nt, oc, 0.0016, 4.0, 0.55), big.inputs['Fac'])
    fine = C.ramp(nt, [(0.35, (0.86, 0.86, 0.86, 1)), (0.65, (1.06, 1.06, 1.04, 1))]); C.link(nt, C.noise(nt, oc, 0.02, 6.0), fine.inputs['Fac'])
    col = C.mixc(nt, 1.0, big.outputs['Color'], fine.outputs['Color'], 'MULTIPLY')
    steep = C.node(nt, 'ShaderNodeMapRange', in_From_Min=0.9, in_From_Max=0.7); C.link(nt, sn.outputs['Z'], steep.inputs['Value'])
    col = C.mixc(nt, steep.outputs['Result'], col, C.lin('#6e6456'))
    sand = C.node(nt, 'ShaderNodeMapRange', in_From_Min=1.6, in_From_Max=0.6); C.link(nt, z, sand.inputs['Value'])
    col = C.mixc(nt, sand.outputs['Result'], col, C.lin('#cbbb93'))
    C.link(nt, col, b.inputs['Base Color']); C.setin(b, 'Roughness', 0.95)
    C.bump_from(nt, b, C.noise(nt, oc, 0.05, 8.0), 0.5, 2.0)
    if fog: K.distance_fog(nt, b.outputs[0], out.inputs['Surface'], half=fog * haze)
    return m

def heightfield(name, fn, x0, x1, y0, y1, step, mat):
    nx, ny = int((x1 - x0) / step), int((y1 - y0) / step); verts, faces = [], []
    for j in range(ny + 1):
        for i in range(nx + 1):
            x, y = x0 + (x1 - x0) * i / nx, y0 + (y1 - y0) * j / ny; verts.append((x, y, fn(x, y)))
    for j in range(ny):
        for i in range(nx):
            k = j * (nx + 1) + i; faces.append((k, k + 1, k + nx + 2, k + nx + 1))
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update(); me.shade_smooth()
    return C.obj(name, me, mat)

def nz(x, y, f, seed): return mnoise.noise(Vector((x * f, y * f, seed)))

def land_z(d, x, y, hmax=80.0, rise=0.35, rough=10.0, seed=1.0):
    """Height of land `d` metres inland of the shore (negative: under the sea): a beach, then hills to hmax."""
    if d <= 0: return max(-12.0, d * 0.25 - 0.5)
    h = hmax * (1 - math.exp(-d * rise / hmax)) + 0.6
    return h + rough * nz(x, y, 1 / 160, seed) * min(1.0, d / 80) + 3 * nz(x, y, 1 / 40, seed + 3) * min(1.0, d / 40)

def bump(x, y, px, py, h, rx, ry=None):
    ry = ry or rx; return h * math.exp(-(((x - px) / rx) ** 2 + ((y - py) / ry) ** 2))

def ground_z(x, y, top_=1500.0):
    bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()
    hit, loc, *_ = bpy.context.scene.ray_cast(dg, Vector((x, y, top_)), Vector((0, 0, -1)))
    return max(loc.z, 0.0) if hit else 0.0

def island(cx, cy, rx, ry, h, seed, mat, rot=0.0, step=None):
    """A rocky island: a noisy dome with a ragged shore (from art_weather_a)."""
    step = step or max(rx, ry) / 70.0
    nx, ny = int(2.6 * rx / step), int(2.6 * ry / step); verts, faces = [], []
    ca, sa = math.cos(rot), math.sin(rot)
    for j in range(ny + 1):
        for i in range(nx + 1):
            u, v = (i / nx - 0.5) * 2.6, (j / ny - 0.5) * 2.6
            r = math.hypot(u, v); ang = math.atan2(v, u)
            edge = 1.0 + 0.22 * mnoise.noise(Vector((math.cos(ang) * 1.3, math.sin(ang) * 1.3, seed))) + 0.08 * math.sin(ang * 5 + seed)
            t = max(0.0, 1 - r / edge)
            z = h * (t ** 0.9) * (0.75 + 0.5 * mnoise.noise(Vector((u * 1.8, v * 1.8, seed + 7)))) + 0.04 * h * mnoise.noise(Vector((u * 7, v * 7, seed))) * t
            z = z - 6.0 if t <= 0 else z + 0.4
            x, y = u * rx, v * ry
            verts.append((cx + x * ca - y * sa, cy + x * sa + y * ca, z))
    for j in range(ny):
        for i in range(nx):
            k = j * (nx + 1) + i; faces.append((k, k + 1, k + nx + 2, k + nx + 1))
    me = bpy.data.meshes.new('island'); me.from_pydata(verts, [], faces); me.update(); me.shade_smooth()
    return C.obj('island', me, mat)

def horizon_sea(color='#0c2e3a'):
    """kit.sea's flat far sea stops 8 km out; from a few hundred metres up the horizon lies much further:
    a far plane to 150 km, and a camera that sees it."""
    me = bpy.data.meshes.new('horizon-sea'); R = 150000
    me.from_pydata([(-R, -R, 0), (R, -R, 0), (R, R, 0), (-R, R, 0)], [], [(0, 1, 2, 3)])
    C.obj('horizon-sea', me, K.sea_mat(color, False, far=True), (0, 0, -0.05))

def glow_mat(name, color, emit=0.45):
    m, nt, b, _ = C.new_mat(name)
    C.setin(b, 'Base Color', C.lin(color)); C.setin(b, 'Roughness', 0.5)
    C.setin(b, 'Emission Color', C.lin(color)); C.setin(b, 'Emission Strength', emit)
    return m

CLEAN = arg('--clean', 0)   # the scene alone, without the radio paths: a test question's view (the paths are the answer)
def radio_path(p0, p1, color, r=1.0, dash=None, gap=None, name='path', r1=None):
    if CLEAN: return None
    """A dashed line through the air (a radio path): short glowing rods from p0 to p1. r1: the radius at p1, so a
    path running away from a close camera can taper (dashes grow with it)."""
    p0, p1 = Vector(p0), Vector(p1); d = p1 - p0; L = d.length; u = d / L
    r1 = r if r1 is None else r1
    dash0 = dash or r * 9; gap0 = gap or r * 6
    m = glow_mat(name + '-mat', color)
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=1.0, radius2=1.0, depth=1.0)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); me.materials.append(m)
    a = 0.0
    while a < L:
        k = (r + (r1 - r) * a / L) / r; b = min(L, a + dash0 * k); rr = r * k
        o = bpy.data.objects.new(name, me); C.col.objects.link(o)
        o.location = p0 + u * ((a + b) / 2); o.scale = (rr, rr, b - a)
        o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = u.to_track_quat('Z', 'Y'); o.visible_shadow = False; o.visible_glossy = False
        a = b + gap0 * k
    return (p0 + p1) / 2

def foam_patch(at, r_in, r_out, size, z=0.08, scale=0.9, rot=0.0, sx=1.0, strength=1.0):
    """White water round a rock or under a helicopter: a transparent decal on the sea (from art_nav_b)."""
    fm, nt, b, out = C.new_mat('foam')
    oc = C.obj_coords(nt); sep = C.node(nt, 'ShaderNodeSeparateXYZ'); C.link(nt, oc, sep.inputs['Vector'])
    rad = C.math_(nt, 'SQRT', C.math_(nt, 'ADD', C.math_(nt, 'MULTIPLY', sep.outputs['X'], sep.outputs['X']), C.math_(nt, 'MULTIPLY', sep.outputs['Y'], sep.outputs['Y'])))
    ring = C.node(nt, 'ShaderNodeMapRange', in_From_Min=r_out, in_From_Max=r_in); C.link(nt, rad, ring.inputs['Value'])
    nzr = C.ramp(nt, [(0.42, (0, 0, 0, 1)), (0.62, (1, 1, 1, 1))]); C.link(nt, C.noise(nt, oc, scale, 8.0), nzr.inputs['Fac'])
    msk = C.math_(nt, 'MULTIPLY', C.math_(nt, 'MULTIPLY', ring.outputs['Result'], nzr.outputs['Color']), strength)
    C.setin(b, 'Base Color', C.lin('#eef3f4')); C.setin(b, 'Roughness', 0.8)
    tp = C.node(nt, 'ShaderNodeBsdfTransparent'); mx = C.node(nt, 'ShaderNodeMixShader')
    C.link(nt, msk, mx.inputs['Fac']); C.link(nt, tp.outputs[0], mx.inputs[1]); C.link(nt, b.outputs[0], mx.inputs[2]); C.link(nt, mx.outputs[0], out.inputs['Surface'])
    s = size; pm = bpy.data.meshes.new('foam'); pm.from_pydata([(-s, -s, 0), (s, -s, 0), (s, s, 0), (-s, s, 0)], [], [(0, 1, 2, 3)])
    o = C.obj('foam', pm, fm, (at[0], at[1], z)); o.visible_shadow = False; o.rotation_euler = (0, 0, rot); o.scale = (sx, 1, 1)
    return o

def rock(at, r, h, seed, mat):
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=4, radius=1.0)
    for v in bm.verts:
        n = mnoise.noise(v.co * 1.7 + Vector((seed, seed * 0.3, 0))); n2 = mnoise.noise(v.co * 5 + Vector((0, seed, 1)))
        v.co = Vector((v.co.x * r, v.co.y * r * 0.8, v.co.z * h)) * (1 + 0.28 * n + 0.08 * n2)
    for f in bm.faces: f.smooth = False
    me = bpy.data.meshes.new('rock'); bm.to_mesh(me); bm.free()
    return C.obj('rock', me, mat, (at[0], at[1], -h * 0.25))

def coast_mast(at, z0, h=48.0, name='mast'):
    """A coast radio station: a red and white lattice mast with whip and panel antennas, a white hut at its foot."""
    red, white = flat_mat(name + '-red', '#c0281e', 0.0, 0.5), flat_mat(name + '-white', '#e9e9e4', 0.0, 0.5)
    grey = C.simple(name + '-steel', '#8c9196', 0.45, 0.6)
    s0, s1, nseg = h * 0.09, h * 0.03, 7
    corners = [(1, 1), (1, -1), (-1, -1), (-1, 1)]
    def P(c, z):
        s = s0 + (s1 - s0) * (z / h); return Vector((at[0] + c[0] * s / 2, at[1] + c[1] * s / 2, z0 + z))
    r = h * 0.007
    for k in range(nseg):
        za, zb = h * k / nseg, h * (k + 1) / nseg; mat = red if k % 2 == 0 else white
        for c in corners: _rod(P(c, za), P(c, zb), r * 1.4, mat)
        for i in range(4):
            c0, c1 = corners[i], corners[(i + 1) % 4]
            _rod(P(c0, za), P(c1, zb), r * 0.7, grey); _rod(P(c1, za), P(c0, zb), r * 0.7, grey); _rod(P(c0, zb), P(c1, zb), r * 0.8, mat)
    tp = Vector((at[0], at[1], z0 + h))
    _rod(tp, tp + Vector((0, 0, h * 0.18)), r * 0.9, white)                       # VHF whips on the top
    for dx, dy in ((1, 0), (-1, 0), (0, 1)):
        b0 = tp + Vector((dx * s1 * 0.6, dy * s1 * 0.6, -h * 0.02)); _rod(b0, b0 + Vector((0, 0, h * 0.12)), r * 0.6, white)
    for a in (0, 120, 240):                                                       # panel antennas
        t = deg(a); p = Vector((at[0] + math.cos(t) * s1 * 0.8, at[1] + math.sin(t) * s1 * 0.8, z0 + h * 0.86))
        o = C.obj(name + '-panel', C.rbox('pan', (h * 0.012, h * 0.035, h * 0.09), h * 0.002, 1), white, tuple(p)); o.rotation_euler = (0, 0, t)
    C.obj(name + '-hut', C.rbox('hut', (h * 0.2, h * 0.14, h * 0.08), h * 0.004, 1), flat_mat(name + '-hutw', '#ecebe5', 0.0, 0.7), (at[0] + h * 0.16, at[1], z0 + h * 0.04))
    return tp + Vector((0, 0, h * 0.18))

def _rod(p0, p1, r, mat):
    p0, p1 = Vector(p0), Vector(p1); d = p1 - p0
    o = C.cyl('rod', r, r, d.length, 6, mat, (p0 + p1) / 2)
    o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = d.to_track_quat('Z', 'Y')
    return o

def dome(center, r, color='#7fc4ff', alpha=0.10, rim=0.35):
    """The range of a coast station: a translucent hemisphere over the sea, brighter at its rim."""
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=96, v_segments=48, radius=r)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -0.01], context='VERTS')
    for f in bm.faces: f.smooth = True
    me = bpy.data.meshes.new('dome'); bm.to_mesh(me); bm.free()
    m, nt, b, out = C.new_mat('dome'); nt.nodes.remove(b)
    em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = C.lin(color); em.inputs['Strength'].default_value = 0.6
    tp = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader')
    lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.5
    f = C.math_(nt, 'ADD', C.math_(nt, 'MULTIPLY', lw.outputs['Facing'], rim), alpha)
    nt.links.new(f, mx.inputs['Fac']); nt.links.new(tp.outputs[0], mx.inputs[1]); nt.links.new(em.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], out.inputs['Surface'])
    o = C.obj('dome', me, m, (center[0], center[1], 0.0)); o.visible_shadow = False
    return o

def ring_dashes(center, r, color, dash=40.0, gap=28.0, w=6.0, a0=0, a1=360, name='rim'):
    """A dashed circle (or arc) floating on the water: compass angles a0..a1 from north."""
    m = glow_mat(name + '-mat', color, 0.8); circ = deg(a1 - a0) * r; n = int(circ / (dash + gap))
    for k in range(n):
        t = deg(a0) + (k + 0.5) * (dash + gap) / r
        p = (center[0] + r * math.sin(t), center[1] + r * math.cos(t), 0.4)
        o = C.obj(name, C.rbox(name, (dash, w, 0.3), 0.0, 1), m, p); o.rotation_euler = (0, 0, -t); o.visible_shadow = False

def vessel(file, pos, heading, length, rule=None, flip=False, draft=0.8, hide=None):
    """A 3D Warehouse vessel: water and ground slabs dropped, its long axis turned to the heading, scaled to
    `length` m, its keel `draft` m under the water. flip turns her round if the model's bow points the other way."""
    root, objs = K.load_model(file, drop_planes=True)
    for o in objs:
        if o.type == 'MESH' and any(sl.material and ('Water' in sl.material.name or 'water' in sl.material.name) for sl in o.material_slots): o.hide_render = True
        if hide and o.type == 'MESH' and hide(o): o.hide_render = True
    bpy.context.view_layer.update()
    vis = [o for o in objs if o.type == 'MESH' and not o.hide_render]
    lo, hi = K.bbox(vis)
    along_y = (hi.y - lo.y) > (hi.x - lo.x)
    span = max(hi.x - lo.x, hi.y - lo.y); k = length / span
    holder = bpy.data.objects.new(file + '-at', None); C.col.objects.link(holder)
    root.parent = holder; root.location = (-(lo.x + hi.x) / 2, -(lo.y + hi.y) / 2, -lo.z)
    spin = bpy.data.objects.new(file + '-spin', None); C.col.objects.link(spin); holder.parent = spin
    holder.rotation_euler = (0, 0, deg(-90) if along_y else 0.0)
    spin.scale = (k,) * 3
    spin.location = (pos[0], pos[1], -draft)
    spin.rotation_euler = (0, 0, deg(90 - heading) + (math.pi if flip else 0.0))
    if rule: K.recolor(vis, rule)
    for o in vis:
        if not o.data.materials: o.data.materials.append(C.simple('vessel-grey', '#8a8f94', 0.5))
    bpy.context.view_layer.update()
    return spin, vis

def lifeboat(pos, heading, length=16.0):
    """An all-weather lifeboat: the 11 m motor yacht in navy and orange, scaled to a lifeboat's 16 m."""
    navy, orange = C.simple('lb-navy', '#1d2a48', 0.4, coat=0.5), C.simple('lb-orange', '#f0641e', 0.45, coat=0.3)
    def rule(c, n):
        if c is None: return orange
        l = sum(c) / 3
        if 'Glass' in n or 'glass' in n or l < 0.12: return None
        return navy if l < 0.5 else orange
    spin, vis = vessel('vessel-motor-yacht.glb', pos, heading, length, rule, flip=FLIP_MY, draft=0.9)
    return spin, vis

FLIP_MY = True       # the motor yacht's bow lies along the model's -X (checked on a draft)

def wake_strip(p, heading, L=30.0, w0=1.6, w1=7.0, alpha=0.4, z=0.06):
    a = deg(heading); u = Vector((math.sin(a), math.cos(a), 0)); s = Vector((u.y, -u.x, 0)); p = Vector((p[0], p[1], z))
    vs = [p + s * w0 / 2, p - s * w0 / 2, p - u * L - s * w1 / 2, p - u * L + s * w1 / 2]
    me = bpy.data.meshes.new('wake'); me.from_pydata([tuple(v) for v in vs], [], [(0, 1, 2, 3)])
    m, nt, b, out = C.new_mat('wake'); nt.nodes.remove(b)
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); bd = nt.nodes.new('ShaderNodeBsdfDiffuse'); bd.inputs['Color'].default_value = (0.9, 0.93, 0.94, 1)
    mx = nt.nodes.new('ShaderNodeMixShader'); mx.inputs['Fac'].default_value = alpha
    nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(bd.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], out.inputs['Surface'])
    o = C.obj('wake', me, m); o.visible_shadow = False

def plotter(you, png, at_model=(-1.25, -0.32, 4.6), tilt=-14.0):
    """The Raymarine Axiom on the helm pod in front of the wheel, its screen showing `png`. Returns (objs, screen obj)."""
    M = K.mats()
    pod_at = you.world(at_model)
    root, objs = K.load_model('chartplotter-raymarine-axiom.glb', drop_planes=False)
    bpy.context.view_layer.update(); lo, hi = K.bbox([o for o in objs if o.type == 'MESH'])
    k = 0.235 / (hi.x - lo.x); root.scale = (k,) * 3; bpy.context.view_layer.update(); lo, hi = K.bbox([o for o in objs if o.type == 'MESH'])
    root.location = (root.location.x - (lo.x + hi.x) / 2 + pod_at.x, root.location.y - (lo.y + hi.y) / 2 + pod_at.y, root.location.z - lo.z + pod_at.z)
    root.rotation_euler = (deg(tilt), 0, 0)
    img = bpy.data.images.load(png); screen = None
    for o in objs:
        for sl in getattr(o, 'material_slots', []):
            if sl.material and sl.material.name.startswith('raymarine--displays'):
                mm, mnt, mb, _ = C.new_mat('axiom-screen')
                uv = mnt.nodes.new('ShaderNodeUVMap'); tx = mnt.nodes.new('ShaderNodeTexImage'); tx.image = img
                mnt.links.new(uv.outputs['UV'], tx.inputs['Vector']); mb.inputs['Base Color'].default_value = (0.01, 0.01, 0.012, 1)
                mnt.links.new(tx.outputs['Color'], mb.inputs['Emission Color']); mb.inputs['Emission Strength'].default_value = 3.5
                mb.inputs['Roughness'].default_value = 0.6; mb.inputs['Coat Weight'].default_value = 0.0; mb.inputs['Specular IOR Level'].default_value = 0.0
                sl.material = mm; screen = o
    C.obj('pod', C.rbox('pod', (0.3, 0.14, 0.12), 0.035, 4), M['dark'], tuple(pod_at - Vector((0, 0, 0.07))))
    bpy.context.view_layer.update()
    return objs, screen

def uv_to_world(o, u, v, mat_prefix='axiom-screen'):
    """The world point on mesh `o` whose UV is (u, v), searching the faces that carry the screen material."""
    me = o.data; me.calc_loop_triangles(); uvl = me.uv_layers.active.data; q = Vector((u, v))
    idx = {i for i, sl in enumerate(o.material_slots) if sl.material and sl.material.name.startswith(mat_prefix)}; hits = []
    for t in me.loop_triangles:
        if t.material_index not in idx: continue
        a, b, c = (Vector(uvl[l].uv) for l in t.loops)
        v0, v1, v2 = b - a, c - a, q - a
        d00, d01, d11, d20, d21 = v0.dot(v0), v0.dot(v1), v1.dot(v1), v2.dot(v0), v2.dot(v1)
        den = d00 * d11 - d01 * d01
        if abs(den) < 1e-12: continue
        w1 = (d11 * d20 - d01 * d21) / den; w2 = (d00 * d21 - d01 * d20) / den; w0 = 1 - w1 - w2
        if min(w0, w1, w2) >= -1e-4:
            P = [me.vertices[i].co for i in t.vertices]
            hits.append(o.matrix_world @ (P[0] * w0 + P[1] * w1 + P[2] * w2))
    if not hits: return None
    cam = bpy.context.scene.camera
    return min(hits, key=lambda h: (h - cam.matrix_world.translation).length) if cam else hits[0]

def screen_point(o, fx, fy):
    """World point of pixel (fx, fy) of the 828 x 481 front texture."""
    for n in (0, 1, -1):          # the model's UVs sit one tile up (v 1..2)
        p = uv_to_world(o, fx / 828.0, 1 - fy / 481.0 + n)
        if p is not None: return p
    return None

def helm_camera(you, look_model=(9.0, -0.3, 3.55), lens=24.0, eye_model=(-2.05, -0.5, 5.05)):
    return K.camera(tuple(you.world(eye_model)), tuple(you.world(look_model)), lens)

def emit_mat(name, rgb, strength):
    m, nt, b, out = C.new_mat(name)
    em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = tuple(rgb) + (1,); em.inputs['Strength'].default_value = strength
    nt.links.new(em.outputs[0], out.inputs['Surface']); return m

def sphere(name, r, mat, loc, seg=24, scale=(1, 1, 1)):
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=seg // 2, radius=r)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); me.shade_smooth()
    o = C.obj(name, me, mat, Vector(loc)); o.scale = scale
    return o

def parent_to(objs, parent):
    for o in objs:
        mw = o.matrix_world.copy(); o.parent = parent; o.matrix_world = mw

def helicopter(at, heading):
    """A twin-engine SAR helicopter (about 17 m), white with a red tail, the rescue winch over the starboard door.
    Built nose along +X, then turned to `heading`. Returns (root, winch hook point in world space)."""
    white = C.simple('heli-white', '#e4e4df', 0.4, coat=0.4); red = C.simple('heli-red', '#c4231c', 0.4, coat=0.4)
    dark = C.simple('heli-dark', '#1c1e21', 0.5); glass = C.simple('heli-glass', '#1a2630', 0.08, 0.2, coat=1.0)
    blade = C.simple('heli-blade', '#2a2c2f', 0.5)
    made = []
    made.append(sphere('h-body', 1.0, white, (0.6, 0, 0), 48, (4.2, 1.45, 1.5)))
    made.append(sphere('h-nose-glass', 1.0, glass, (3.0, 0, 0.35), 40, (1.75, 1.2, 0.95)))
    made.append(C.obj('h-cabin', C.rbox('cab', (4.6, 2.7, 2.2), 0.6, 4), white, (-0.4, 0, 0.2)))
    made.append(C.obj('h-stripe', C.rbox('str', (6.4, 2.76, 0.35), 0.15, 2), red, (0.3, 0, -0.35)))
    made.append(C.obj('h-engines', C.rbox('eng', (3.6, 1.7, 0.8), 0.35, 3), white, (-0.4, 0, 1.55)))
    for s in (-1, 1):
        made.append(C.obj('h-sponson', C.rbox('sp', (2.2, 0.7, 0.6), 0.25, 3), red, (-0.6, s * 1.55, -0.85)))
        made.append(C.cyl('h-wheel', 0.33, 0.33, 0.22, 16, dark, (-0.6, s * 1.75, -1.25), (deg(90), 0, 0)))
        made.append(C.obj('h-window', C.rbox('win', (1.0, 0.05, 0.7), 0.1, 2), glass, (0.3, s * 1.36, 0.55)))
    made.append(C.cyl('h-nosewheel', 0.25, 0.25, 0.18, 16, dark, (2.9, 0, -1.25), (deg(90), 0, 0)))
    o = C.cyl('h-boom', 0.62, 0.26, 7.6, 24, red, (-6.4, 0, 0.75), (0, deg(-86), 0)); made.append(o)
    made.append(C.obj('h-fin', C.rbox('fin', (1.5, 0.22, 2.4), 0.15, 2), red, (-10.0, 0, 1.75)))
    made[-1].rotation_euler = (0, deg(-18), 0)
    made.append(C.obj('h-stab', C.rbox('stab', (0.9, 3.0, 0.12), 0.05, 1), red, (-9.0, 0, 0.9)))
    made.append(C.cyl('h-tailrotor', 1.25, 1.25, 0.05, 32, C.simple('h-tr', '#3a3c40', 0.5), (-10.4, 0.3, 2.3), (deg(90), 0, 0)))
    made.append(C.cyl('h-mast', 0.25, 0.2, 0.7, 16, dark, (0.4, 0, 2.3)))
    hub = Vector((0.4, 0, 2.7)); made.append(sphere('h-hub', 0.35, dark, hub, 16))
    for k in range(5):
        a = deg(18 + k * 72)
        o = C.obj('h-blade', C.rbox('bl', (7.6, 0.55, 0.1), 0.04, 1), blade, (hub.x + math.cos(a) * 4.0, hub.y + math.sin(a) * 4.0, hub.z + 0.05))
        o.rotation_euler = (0, 0, a); made.append(o)
    # the turning rotor: a faint grey disc
    m, nt, b, out = C.new_mat('rotor-blur'); tp = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader')
    b.inputs['Base Color'].default_value = C.lin('#3a3c40'); mx.inputs['Fac'].default_value = 0.22
    nt.links.new(tp.outputs[0], mx.inputs[1]); nt.links.new(b.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], out.inputs['Surface'])
    disc = C.cyl('h-disc', 8.0, 8.0, 0.04, 64, m, (hub.x, hub.y, hub.z + 0.05)); disc.visible_shadow = False; made.append(disc)
    # the hoist: an arm out over the starboard door (-Y is starboard with the nose along +X)
    made.append(C.obj('h-hoist-arm', C.rbox('arm', (0.3, 1.3, 0.25), 0.05, 1), white, (0.8, -1.9, 1.35)))
    made.append(C.cyl('h-hoist', 0.24, 0.24, 0.55, 16, dark, (0.8, -2.45, 1.2)))
    root = bpy.data.objects.new('heli', None); C.col.objects.link(root)
    bpy.context.view_layer.update(); parent_to(made, root)
    root.location = at; root.rotation_euler = (deg(-4), 0, deg(90 - heading))   # a little nose-up into the wind
    bpy.context.view_layer.update()
    return root, root.matrix_world @ Vector((0.8, -2.45, 0.9))

def handheld(at, rot=0.0):
    """A handheld VHF standing on a table: black body, grey LCD, keypad, a stubby antenna."""
    black = C.simple('hh-black', '#17181a', 0.55, coat=0.2); lcd = flat_mat('hh-lcd', '#9fae9a', 0.25, 0.3)
    key = C.simple('hh-key', '#3a3d42', 0.6); orange = C.simple('hh-orange', '#e85a12', 0.5)
    made = [C.obj('hh-body', C.rbox('hh', (0.06, 0.034, 0.13), 0.008, 3), black, (0, 0, 0.065)),
            C.obj('hh-lcd', C.rbox('lcd', (0.044, 0.004, 0.03), 0.002, 1), lcd, (0, -0.0175, 0.103)),
            C.cyl('hh-ant', 0.0065, 0.005, 0.15, 12, black, (0.018, 0.004, 0.205)),
            C.cyl('hh-knob', 0.009, 0.009, 0.014, 12, orange, (-0.016, 0.004, 0.137))]
    for i in range(3):
        for j in range(4):
            made.append(C.obj('hh-key', C.rbox('k', (0.011, 0.004, 0.007), 0.002, 1), key, (-0.015 + i * 0.015, -0.0175, 0.075 - j * 0.012)))
    made.append(C.obj('hh-16', C.rbox('k16', (0.014, 0.004, 0.008), 0.002, 1), C.simple('hh-red', '#c4231c', 0.5), (0.0, -0.0175, 0.022)))
    root = bpy.data.objects.new('handheld', None); C.col.objects.link(root)
    bpy.context.view_layer.update(); parent_to(made, root); root.location = at; root.rotation_euler = (0, 0, rot)
    return root

# ---------------------------------------------------------------------------------------------------- figures
if ART == 'channels' and FIG == 7:
    # from the helm: a ship 40° on our starboard bow, 380 m, crossing to the west, calling us
    K.sea('breeze', size=40.0, repeat=14); K.day_sky(sun_az=215, sun_el=34)
    you = sailing('you', 0, 60, 0, 0)
    bow = you.world((10.5, 0.13, 2.0))
    sp = N.at_bearing(bow, 38, 230)
    navy = C.simple('ship-hull', '#24324a', 0.45, coat=0.3)
    def srule(c, n):
        if c is None: return None
        return navy if (c[2] > c[0] + 0.08 and sum(c) / 3 > 0.35) else None
    ship, svis = vessel('vessel-ferry.glb', (sp.x, sp.y), 250, 62.0, srule, draft=2.2)
    bpy.context.view_layer.update(); lo, hi = K.bbox(svis)
    wake_strip(((lo.x + hi.x) / 2 + 30 * math.sin(deg(250)), (lo.y + hi.y) / 2 + 30 * math.cos(deg(250))), 250, 70, 6, 22, 0.35)
    K.camera(tuple(you.world((-2.2, -0.9, 5.15))), (sp.x - 20, sp.y - 30, -22), 30)
    labels = [(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, hi.z + 4), 'Ship · calls on 16, go to 13'),
              (((lo.x + hi.x) / 2 - 75, (lo.y + hi.y) / 2 - 60, 0.5), 'stbd 040° · 380 m')]
    note = 'Working channels · a ship calls you'; expo = -0.5

elif ART == 'channels' and FIG == 8:
    # aerial from the south, low: a 300 m island, us to the west of it, a friend 6 miles off to the east
    K.sea('breeze', size=40.0, repeat=12, center=(-450, -80)); horizon_sea(); K.day_sky(sun_az=205, sun_el=38)
    LAND = aerial_land_mat(6000)
    island(0, 140, 340, 420, 300, 4.0, LAND, rot=deg(10))
    you = sailing('you', 80, 20, -720, -60, k=2.4); fr = sailing('friend', 260, 20, 780, 200, k=2.4)
    K.wake(you, 40, 8)
    a, b = top(you, 19), top(fr, 19)
    radio_path(a, b, '#d42020', r=4.0, name='blocked')
    drone((30, 80, 110), 2200, 186, 15, 32)
    t = (-370 - a.x) / (b.x - a.x); hit = a.lerp(b, t)
    labels = [(tuple(top(you, 25)), 'You', 'blue'), (tuple(top(fr, 25)), 'friend'), (tuple(hit + Vector((0, 0, 25))), 'blocked', 'red'),
              ((0, 140, 345), 'island, 300 m high')]
    note = 'Range · an island in the way'
elif ART == 'channels' and FIG == 9:
    # aerial: a tall headland running south from the mainland; the coast station on a mountain to the north;
    # us west of the headland, friends 3 miles off behind it to the east
    K.sea('breeze', size=40.0, repeat=12, center=(-400, -100)); horizon_sea(); K.day_sky(sun_az=215, sun_el=38)
    def shore(x): return 1400 + 120 * math.sin(x / 420) + 60 * math.sin(x / 150)
    MX, MY = -350, 2700
    def fn(x, y):
        z = land_z(y - shore(x), x, y, hmax=110, rise=0.4, seed=2.0)
        mtn = bump(x, y, MX, MY, 780, 560, 640)
        z = max(z, mtn * (1 + 0.08 * nz(x, y, 1 / 140, 5)) - 3)                                   # the mountain with the station
        ridge = 230 * math.exp(-((x - 260) / 150) ** 2) / (1 + math.exp(-(y + 250) / 90))     # the headland, from the coast south
        ridge *= (1 + 0.15 * nz(x, y, 1 / 90, 7)) * min(1.0, max(0.0, (y + 420) / 260))
        return max(z, ridge - 8)
    heightfield('land', fn, -6000, 6000, -700, 7000, 30, aerial_land_mat(7000))
    mz = ground_z(MX, MY)
    mast_top = coast_mast((MX, MY), mz - 3, 110)
    you = sailing('you', 20, 300, -520, -120, k=2.4); fr = sailing('f1', 200, 300, 900, -60, k=2.4)
    K.wake(you, 40, 8)
    a = top(you, 19)
    radio_path(a, mast_top, '#f2c200', r=5.0, name='clear')
    radio_path(a, top(fr, 19), '#d42020', r=5.0, name='blocked')
    drone((150, 950, 320), 3400, 198, 19, 32)
    labels = [(tuple(top(you, 25)), 'You', 'blue'), (tuple(top(fr, 25)), 'friends 3 miles off'),
              (tuple(mast_top - Vector((0, 0, 75))), 'coast station on a mountain'), ((262, 420, 245), 'headland'),
              (tuple(a.lerp(top(fr, 19), 0.5) + Vector((0, 0, 30))), 'blocked', 'red')]
    note = 'Range · height wins'
elif ART == 'distress' and FIG == 4:
    # from the deck: a lighthouse on a headland bearing 040°, 3 miles (brought in to 1.5 km so it reads)
    K.sea('breeze'); K.day_sky(sun_az=150, sun_el=34)
    you = K.load_yacht(name='you').place(0, 0, heading=0)
    D = 1500.0; brg = deg(40); L = Vector((D * math.sin(brg), D * math.cos(brg), 0))
    side = Vector((math.cos(brg), -math.sin(brg), 0)); fwd = Vector((math.sin(brg), math.cos(brg), 0))
    def fn(x, y):
        p = Vector((x, y, 0)) - L; s, f = p.dot(side), p.dot(fwd)
        r = math.hypot(s / 330, (f - 230) / 330)
        z = 120 * max(0.0, 1 - r ** 2.2) ** 0.6                                           # a steep, rounded cape
        z += 70 * max(0.0, 1 - math.hypot((s + 900) / 900, (f - 520) / 300) ** 2) + 55 * max(0.0, 1 - math.hypot((s - 1100) / 900, (f - 640) / 380) ** 2)
        z += 16 * nz(x, y, 1 / 140, 3) * min(1.0, max(z, 0) / 30) + 5 * nz(x, y, 1 / 35, 9) - 8
        return z
    heightfield('cape', fn, L.x - 2600, L.x + 2600, L.y - 1600, L.y + 2400, 10, aerial_land_mat(6000, 'cape-land'))
    pt = L + fwd * 30; zp = max(ground_z(pt.x, pt.y), 6)
    C.cyl('lt-tower', 2.6, 2.0, 15.0, 24, flat_mat('lt-white', '#f2f0ea', 0.0, 0.5), (pt.x, pt.y, zp + 7.5))
    C.cyl('lt-lantern', 1.7, 1.7, 2.4, 24, C.simple('lt-glass', '#2b3036', 0.2, 0.4), (pt.x, pt.y, zp + 16.2))
    C.cyl('lt-roof', 2.0, 0.2, 1.6, 24, flat_mat('lt-roof', '#8a1d18', 0.0, 0.5), (pt.x, pt.y, zp + 18.2))
    C.cyl('lt-gallery', 2.4, 2.4, 0.4, 24, flat_mat('lt-black', '#1a1b1d', 0.0, 0.5), (pt.x, pt.y, zp + 15.0))
    C.obj('lt-house', C.rbox('lth', (10, 6, 4.5), 0.2, 2), flat_mat('lt-white2', '#ecebe5', 0.0, 0.6), (pt.x - 8, pt.y + 4, zp + 2.2))
    eye = you.world((3.2, -1.3, 5.3)); K.camera(tuple(eye), (pt.x, pt.y, zp - 12), 110)
    labels = [((pt.x, pt.y, zp + 24), 'Lt 040° · say: 220° from the light, 3 miles')]
    note = 'Your position · bearing FROM the light'
elif ART == 'distress' and FIG == 6:
    # night: a red parachute flare high on the starboard bow, 040°
    you = K.load_yacht(name='you'); you.place(0, 0, heading=0)
    N.night_scene('calm'); N.our_lights(you, steaming=False); N.cloth_furled(you)
    fp = Vector((950 * math.sin(deg(40)), 950 * math.cos(deg(40)), 175))
    sphere('flare', 6.0, emit_mat('flare-core', (1.0, 0.05, 0.015), 9.0), fp)
    ld = bpy.data.lights.new('flare-light', 'POINT'); ld.energy = 2.0e7; ld.color = (1.0, 0.12, 0.05); ld.shadow_soft_size = 3.0
    lo = bpy.data.objects.new('flare-light', ld); C.col.objects.link(lo); lo.location = fp
    sm = emit_mat('flare-trail', (0.75, 0.16, 0.12), 0.3)
    pts = [fp + Vector((-14 * t * t, 3 * t, -80 * t)) for t in [i / 14 for i in range(15)]]
    for i in range(14):
        _rod(pts[i], pts[i + 1], 1.0 + 2.6 * (i / 14), sm)
    N.foredeck_camera(you, bearing=36, lens=28, pitch=4.0)
    labels = [(tuple(fp + Vector((0, 0, 22))), 'red parachute flare · 040°', 'red')]
    note = 'MAYDAY RELAY · you saw a flare'; expo = 0.6; extra = {'bloom': 1.2}
elif ART == 'gmdss' and FIG == 1:
    # aerial: a coast with the coast station; the dome of its VHF range over the sea (sea area A1), us inside
    K.sea('breeze', size=40.0, repeat=12, center=(150, 500)); horizon_sea(); K.day_sky(sun_az=205, sun_el=40)
    def shore(x): return 1500 + 140 * math.sin(x / 520) + 50 * math.sin(x / 140)
    def fn(x, y): return max(land_z(y - shore(x), x, y, hmax=160, rise=0.3, seed=1.0), bump(x, y, 0, 1950, 300, 330, 280) - 3)
    heightfield('land', fn, -7000, 7000, 1000, 9000, 40, aerial_land_mat(8000))
    gz = ground_z(0, 1950); mtop = coast_mast((0, 1950), gz - 3, 110)
    dome((0, 1650), 1650, '#8fd0ff', 0.07, 0.30)
    ring_dashes((0, 1650), 1650, '#f2c200', 60, 40, 9, 92, 268)
    you = sailing('you', 80, 20, 250, 760, k=3.0); K.wake(you, 40, 8)
    drone((0, 1000, 180), 3900, 182, 20, 32)
    labels = [(tuple(mtop + Vector((0, 0, 60))), 'VHF DSC coast station'), (tuple(top(you, 26)), 'You', 'blue'),
              ((950, 420, 380), 'A1 · in VHF DSC range', 'blue'), ((0, -330, 30), 'beyond VHF range: EPIRB', 'red')]
    note = 'GMDSS sea area A1'
elif ART == 'gmdss' and FIG == 2:
    # an EPIRB afloat close to the camera; the satellite overhead (406 MHz up), a lifeboat coming in on 121.5 MHz
    K.sea('calm', size=24.0, repeat=10); K.day_sky(sun_az=230, sun_el=38)
    yel, blk = C.simple('epirb-yellow', '#f2b705', 0.4, coat=0.5), C.simple('epirb-black', '#16171a', 0.5)
    C.cyl('epirb-body', 0.06, 0.055, 0.34, 32, yel, (0, 0, 0.05))
    C.cyl('epirb-collar', 0.075, 0.075, 0.07, 32, blk, (0, 0, -0.03))
    C.cyl('epirb-cap', 0.05, 0.035, 0.05, 32, blk, (0, 0, 0.245))
    sphere('epirb-strobe', 0.034, emit_mat('strobe', (1, 1, 1), 30.0), (0, 0, 0.285), 20, (1, 1, 1.3))
    C.cyl('epirb-ant', 0.006, 0.004, 0.42, 8, blk, (0.02, 0, 0.47))
    C.obj('epirb-label', C.rbox('lbl', (0.07, 0.002, 0.11), 0.0, 1), flat_mat('epirb-lbl', '#f4f2ea', 0.0, 0.6), (0, -0.058, 0.07))
    sl = bpy.data.lights.new('strobe', 'POINT'); sl.energy = 6.0; sl.shadow_soft_size = 0.03
    so = bpy.data.objects.new('strobe', sl); C.col.objects.link(so); so.location = (0, 0, 0.29)
    lb, lvis = lifeboat((15, 44), 200)
    bpy.context.view_layer.update(); llo, lhi = K.bbox(lvis)
    lbc = Vector(((llo.x + lhi.x) / 2, (llo.y + lhi.y) / 2, lhi.z))
    wake_strip((lbc.x + 7 * math.sin(deg(200)), lbc.y + 7 * math.cos(deg(200))), 200, 40, 3, 14, 0.5)
    # the satellite, high to the north-east: gold body, two dark panels turned to face down at us, a dish
    S = Vector((34, 78, 40)); s = 1.6
    parts = [C.obj('sat-body', C.rbox('sb', (1.6 * s, 1.6 * s, 2.0 * s), 0.08, 2), C.simple('sat-foil', '#c9a040', 0.35, 1.0), (0, 0, 0))]
    pan = C.simple('sat-panel', '#22397a', 0.3, 0.5, coat=0.6)
    for k_ in (-1, 1):
        parts.append(C.obj('sat-panel', C.rbox('sp', (5.2 * s, 0.06 * s, 1.6 * s), 0.02, 1), pan, (k_ * 3.6 * s, 0, 0)))
    parts.append(sphere('sat-dish', 0.8 * s, C.simple('sat-dish', '#e8e6e0', 0.4), (0, -1.0 * s, -0.4 * s), 24, (1, 0.3, 1)))
    sat = bpy.data.objects.new('sat', None); C.col.objects.link(sat); bpy.context.view_layer.update(); parent_to(parts, sat)
    sat.location = S; sat.rotation_euler = (deg(-35), 0, deg(200))
    ep = Vector((0.02, 0, 0.7))
    radio_path(ep, S, '#f2c200', r=0.012, r1=0.6, dash=0.18, gap=0.12, name='up406')
    radio_path(ep + Vector((0, 0.0, -0.1)), lbc + Vector((0, 0, -1.2)), '#d42020', r=0.012, r1=0.35, dash=0.18, gap=0.12, name='home121')
    K.camera((0.42, -1.3, 0.42), (0.6, 12.0, 2.6), 20)
    labels = [((0.06, -0.02, 0.2), 'EPIRB'), (tuple(S + Vector((0, 0, 6))), 'satellite'),
              (tuple(ep.lerp(S, 0.12)), '406 MHz', 'yellow'), (tuple(ep + (lbc - ep).normalized() * 3.0), '121.5 MHz homing', 'red'),
              (tuple(lbc + Vector((0, 0, 7))), 'lifeboat')]
    note = 'EPIRB · alarm and homing'; expo = -0.5
elif ART == 'gmdss' and FIG in (3, 5):
    png = SART_PNG if FIG == 3 else NOAIS_PNG
    if not os.path.exists(png):
        subprocess.run(['python3', os.path.abspath(__file__), '--prep'], check=True)
    you = K.load_yacht(name='you'); you.place(0, 0, heading=0)
    K.sea('breeze' if FIG == 5 else 'calm', size=36.0, repeat=10); K.day_sky(sun_az=200, sun_el=36, strength=0.2)
    objs, scr = plotter(you, png)
    bpy.context.view_layer.update(); plo, phi = K.bbox([o for o in objs if o.type == 'MESH'])
    if FIG == 3:
        # close to the screen: radar with the SART's line of dots
        pc = Vector(((plo.x + phi.x) / 2, (plo.y + phi.y) / 2, (plo.z + phi.z) / 2))
        K.camera(tuple(pc + Vector((0.025, -0.27, 0.12))), tuple(pc + Vector((0.0, 0.0, 0.015))), 35)
        first = screen_point(scr, *front_xy(*radar_xy(SART_BRG, SART_R0)))
        last = screen_point(scr, *front_xy(*radar_xy(SART_BRG, SART_R0 + 11 * SART_STEP)))
        centre = screen_point(scr, *front_xy(R_CX, R_CY))
        print('SART anchors', first, last, centre)
        labels = [(tuple(first), 'SART · 12 dots, the first is the raft', 'red')]
        note = 'SART on the radar screen'; expo = -0.4
    else:
        # helm view: a small motorboat 25° on the starboard bow, about 150 m, no AIS: the plotter shows nothing
        bow = you.world((10.5, 0.13, 2.0)); sp = N.at_bearing(bow, 25, 95)
        white = C.simple('mb-white', '#c9cac6', 0.4, coat=0.4)
        def rule(c, n):
            if c is None: return white
            return None if sum(c) / 3 < 0.25 or 'lass' in n else white
        mb, mvis = vessel('vessel-motor-yacht.glb', (sp.x, sp.y), 250, 9.0, rule, flip=FLIP_MY, draft=0.5)
        bpy.context.view_layer.update(); mlo, mhi = K.bbox(mvis)
        wake_strip(((mlo.x + mhi.x) / 2 - 4 * math.sin(deg(250)), (mlo.y + mhi.y) / 2 - 4 * math.cos(deg(250))), 250, 30, 2, 9, 0.45)
        helm_camera(you, look_model=(9.0, -2.6, 3.7), lens=24)
        top_ = screen_point(scr, 400, 92)
        labels = [(((mlo.x + mhi.x) / 2, (mlo.y + mhi.y) / 2, mhi.z + 1.5), 'No AIS · not on the plotter', 'red'),
                  (tuple(top_), 'AIS: no targets', 'blue')]
        note = 'AIS · not every boat shows'; expo = -0.4

elif ART == 'licences' and FIG == 3:
    # a taverna terrace above a beach: a handheld VHF on the table; our yacht at anchor off the beach
    K.sea('calm', size=30.0, repeat=12, center=(20, 160)); K.day_sky(sun_az=250, sun_el=40)
    TZ = 2.6                                                       # terrace level
    def shore(x): return 22 + 0.00009 * x * x + 3 * math.sin(x / 23)
    def fn(x, y):
        d = shore(x) - y                                           # inland is to the south (towards the camera)
        if d <= 0: return max(-10, d * 0.1 - 0.3)
        z = land_z(d, x, y, hmax=60, rise=0.18, rough=6, seed=8.0)
        if abs(x) < 140: z = min(z, 0.25 + d * 0.035)              # the beach below the taverna
        return z + bump(x, y, -420, 300, 140, 240, 200) + bump(x, y, 520, 420, 110, 260, 220)  # headlands either side
    heightfield('shore', fn, -1400, 1400, -80, 1400, 5, land_mat(3000))
    stone = C.granite_mat('paving', base='#cfc6b4', per_object=False, scale=0.6, dark='#a49a86', light='#e2dacb', dirt=False)
    C.obj('terrace', C.rbox('ter', (18, 10, TZ), 0.05, 1), stone, (0, -7.0, TZ / 2))
    wall_w = flat_mat('wall-white', '#efede6', 0.0, 0.8)
    C.obj('wall', C.rbox('wall', (18, 0.3, 0.5), 0.05, 2), wall_w, (0, -2.15, TZ + 0.25))
    # the taverna: whitewashed, blue door and shutters, its side wall along the left of the terrace
    C.obj('taverna', C.rbox('tav', (4.0, 9.0, TZ + 4.2), 0.08, 2), wall_w, (-4.3, -4.4, (TZ + 4.2) / 2))
    blue = C.simple('tav-blue', '#1f5fa8', 0.5)
    C.obj('door', C.rbox('door', (0.08, 1.1, 2.2), 0.02, 1), blue, (-2.28, -5.2, TZ + 1.1))
    for y_ in (-3.4, -1.9, -0.4):
        C.obj('shutter', C.rbox('sh', (0.08, 1.0, 1.1), 0.02, 1), blue, (-2.28, y_, TZ + 2.2))
    C.obj('tav-roof', C.rbox('roof', (4.3, 9.3, 0.25), 0.04, 1), wall_w, (-4.3, -4.4, TZ + 4.3))
    wood = C.simple('table-wood', '#7a5434', 0.6); cloth = C.fabric_mat('tablecloth', '#e9e6dd', '#d8d4c8', 300.0)
    chair = C.simple('chair-wood', '#2c5c9a', 0.55)
    def table(x, y):
        C.obj('table-top', C.rbox('tt', (0.8, 0.8, 0.04), 0.01, 1), cloth, (x, y, TZ + 0.74))
        for dx, dy in ((-0.34, -0.34), (0.34, -0.34), (0.34, 0.34), (-0.34, 0.34)):
            C.obj('table-leg', C.rbox('tl', (0.04, 0.04, 0.72), 0.005, 1), wood, (x + dx, y + dy, TZ + 0.36))
    def chair_at(x, y, rot):
        root = bpy.data.objects.new('chair', None); C.col.objects.link(root)
        parts = [C.obj('seat', C.rbox('seat', (0.42, 0.42, 0.04), 0.01, 1), chair, (0, 0, 0.45)),
                 C.obj('back', C.rbox('back', (0.42, 0.03, 0.45), 0.01, 1), chair, (0, 0.2, 0.7))]
        for dx, dy in ((-0.18, -0.18), (0.18, -0.18), (0.18, 0.18), (-0.18, 0.18)):
            parts.append(C.obj('cleg', C.rbox('cl', (0.035, 0.035, 0.45), 0.005, 1), chair, (dx, dy, 0.225)))
        bpy.context.view_layer.update(); parent_to(parts, root); root.location = (x, y, TZ); root.rotation_euler = (0, 0, rot)
    table(0.3, -3.6); chair_at(1.0, -3.55, deg(90))
    table(3.4, -3.3); chair_at(3.4, -3.95, 0); chair_at(3.4, -2.65, deg(180))
    # an umbrella over the near table
    C.cyl('umb-pole', 0.03, 0.03, 2.5, 12, wood, (-2.0, -3.4, TZ + 1.25))
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=False, segments=12, radius1=1.6, radius2=0.03, depth=0.55)
    me = bpy.data.meshes.new('umbrella'); bm.to_mesh(me); bm.free()
    C.obj('umbrella', me, C.fabric_mat('umb-cloth', '#e9e3d2', '#d9d0bb', 200.0), (-2.0, -3.4, TZ + 2.35))
    # on the table: the handheld VHF, a glass, a plate
    hh = handheld((0.2, -3.75, TZ + 0.76), deg(-15))
    glass_m = C.simple('glass', '#dfe8ea', 0.05, coat=1.0); next(n for n in glass_m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED').inputs['Transmission Weight'].default_value = 1.0
    C.cyl('glass', 0.035, 0.03, 0.11, 24, glass_m, (0.48, -3.5, TZ + 0.815))
    C.cyl('plate', 0.12, 0.1, 0.02, 32, flat_mat('plate', '#f3f1ea', 0.0, 0.3), (0.45, -3.82, TZ + 0.77))
    # our yacht at anchor 250 m off, head to the breeze
    yt = K.load_yacht(name='anchored').place(38, 190, heading=330); N.cloth_furled(yt)
    K.camera((-0.25, -5.55, TZ + 1.3), (1.5, 40.0, TZ - 6.0), 30)
    labels = [((0.2, -3.75, TZ + 0.98), 'handheld at the taverna · not allowed', 'red'), (tuple(top(yt, 20)), 'afloat: licensed', 'blue')]
    note = 'Where the licence is valid'; expo = -0.5
elif ART == 'sar' and FIG == 1:
    # aerial: Thalassa holed and sinking, the coast station on the coast to the north, us 3 miles off to the south-east
    K.sea('breeze', size=40.0, repeat=12, center=(100, 0)); horizon_sea(); K.day_sky(sun_az=205, sun_el=40)
    def shore(x): return 820 + 110 * math.sin(x / 500) + 40 * math.sin(x / 160)
    def fn(x, y): return max(land_z(y - shore(x), x, y, hmax=120, rise=0.35, seed=3.0), bump(x, y, -420, 1080, 190, 230, 200) - 3)
    heightfield('land', fn, -7000, 7000, 500, 9000, 30, aerial_land_mat(6000))
    gz = ground_z(-420, 1080); mtop = coast_mast((-420, 1080), gz - 3, 90)
    cas = motoring('thalassa', 300, -170, 210, k=2.4, heel=24)
    cas.root.location.z = -2.2                                      # settled low in the water
    C.cyl('raft', 2.6, 2.6, 1.1, 24, C.simple('raft-orange', '#e8641c', 0.6), (-140, 190, 0.45))
    C.cyl('raft-canopy', 2.4, 0.7, 1.9, 24, C.simple('raft-canopy', '#e8641c', 0.6), (-140, 190, 1.9))
    foam_patch((-170, 210), 8, 30, 36, scale=0.35)
    you = sailing('you', 300, 20, 255, -115, k=2.4); K.wake(you, 50, 8)
    blk = flat_mat('dash-black', '#1b1d20', 0.0, 0.6)
    p0, p1 = Vector((228, -95, 0)), Vector((-130, 175, 0)); u = (p1 - p0).normalized(); L = (p1 - p0).length
    for k in range(int(L / 30)):
        c = p0 + u * (k * 30 + 10)
        o = C.obj('dash', C.rbox('dash', (18, 5.5, 0.3), 0.0, 1), blk, (c.x, c.y, 0.5)); o.rotation_euler = (0, 0, math.atan2(u.y, u.x))
    drone((70, 330, 120), 1350, 165, 21, 32)
    labels = [(tuple(mtop + Vector((0, 0, 30))), 'coast station'), (tuple(top(cas, 16) + Vector((0, 0, 8))), 'Thalassa · holed, sinking', 'red'),
              (tuple(top(you, 25)), 'You', 'blue'), (tuple(p0.lerp(p1, 0.5) + Vector((45, 0, 5))), '3 miles')]
    note = 'Hearing a MAYDAY · what to note'
elif ART == 'sar' and FIG == 4:
    # aerial: the casualty west of an island, the lifeboat east of it; MRCC on the coast to the north; us to the south
    K.sea('breeze', size=40.0, repeat=12, center=(0, 0)); horizon_sea(); K.day_sky(sun_az=205, sun_el=40)
    LAND = aerial_land_mat(6000)
    def shore(x): return 1300 + 110 * math.sin(x / 640) + 40 * math.sin(x / 150)
    heightfield('land', lambda x, y: land_z(y - shore(x), x, y, hmax=140, rise=0.3, seed=6.0), -7000, 7000, 1000, 9000, 32, LAND)
    island(0, 330, 240, 190, 150, 9.0, LAND, rot=deg(-8))
    gz = ground_z(-160, 1460); mtop = coast_mast((-160, 1460), gz - 3, 70)
    C.obj('mrcc', C.rbox('mrcc', (60, 30, 16), 1.0, 2), flat_mat('mrcc-white', '#ecebe5', 0.0, 0.7), (-70, 1450, ground_z(-70, 1450) + 6))
    cas = motoring('casualty', 0, -500, 340, k=2.4, heel=14); foam_patch((-500, 340), 6, 24, 28, scale=0.35)
    lb, lvis = lifeboat((540, 380), 270, 16.0 * 2.4)
    bpy.context.view_layer.update(); llo, lhi = K.bbox(lvis); lbc = Vector(((llo.x + lhi.x) / 2, (llo.y + lhi.y) / 2, lhi.z))
    wake_strip((lbc.x + 22, lbc.y), 270, 140, 10, 40, 0.45)
    you = sailing('you', 0, 300, 0, -260, k=2.4); K.wake(you, 50, 8)
    a = top(you, 19)
    radio_path(a, top(cas, 19), '#f2c200', r=3.5, name='to-cas'); radio_path(a, lbc + Vector((0, 0, 8)), '#f2c200', r=3.5, name='to-lb')
    drone((0, 330, 50), 1900, 180, 20, 32)
    labels = [(tuple(top(you, 25)), 'you hear both: relay', 'blue'), (tuple(top(cas, 25)), 'casualty', 'red'),
              (tuple(lbc + Vector((0, 0, 30))), 'lifeboat'), ((0, 330, 175), 'island'), (tuple(mtop + Vector((0, 0, 30))), 'MRCC')]
    note = 'On scene · relay between them'
elif ART == 'sar' and FIG == 5:
    # a SAR helicopter over our port quarter, nose into the wind (330°), the hoist wire down to the stern;
    # we motor steady on 000°, sails down, deck cleared; wind 30° on the port bow
    K.sea('breeze', size=36.0, repeat=10); K.day_sky(sun_az=150, sun_el=40)
    you = motoring('you', 0, 0, 0); N.cloth_furled(you); K.wake(you, 30, 6, 0.7)
    stern = you.world((-3.4, 1.0, 3.7))
    hc = Vector((stern.x - 6.0, stern.y - 8.0, 30.0))
    heli, hook = helicopter(hc, 330)
    for o in heli.children: o.visible_shadow = False
    _rod(hook, stern + Vector((0, 0, 0.3)), 0.025, C.simple('wire', '#b9bcbf', 0.3, 1.0))
    sphere('hook', 0.18, C.simple('hook', '#d8a21a', 0.4, 0.6), stern + Vector((0, 0, 0.45)), 12)
    drone((-3.5, -7.0, 17.5), 68, 248, 10, 32)
    w = deg(330); u = Vector((math.sin(w), math.cos(w), 0))
    wa = Vector((-8, 15, 13)); arrows = [(tuple(wa), tuple(wa - u * 13), 'blue')]
    labels = [(tuple(wa + Vector((0, 0, 2.5))), 'wind 30° on the port bow', 'blue'), (tuple(you.world((10.4, 0.13, 6.5))), 'steady course 000°', 'blue'),
              (tuple(hc + Vector((0, 0, 6.0))), 'rescue helicopter'), (tuple(hook.lerp(stern, 0.45)), 'let the wire earth first', 'red')]
    note = 'Helicopter rescue · the brief'
elif ART == 'urgency' and FIG == 2:
    # F6 from the north, no engine: the yacht lies beam-on and drifts south onto rocks; a rocky shore downwind
    sea = K.sea(wind=14.0, wave_scale=0.75, chop=1.8, size=85.0, res=11, repeat=8, color='#1f3a42', center=(0, -150))
    sea.modifiers['ocean'].foam_coverage = 0.12
    K.day_sky(sun_az=240, sun_el=28, strength=0.22, haze=2.4)
    RK = rock_mat('shore-rock', 9000)
    def shore(x): return -430 + 40 * math.sin(x / 140) + 18 * math.sin(x / 47)
    heightfield('shore', lambda x, y: land_z(shore(x) - y, x, y, hmax=110, rise=0.6, rough=14, seed=12.0), -2600, 2600, -1600, -360, 9, RK)
    rnd = random.Random(3)
    for i in range(16):
        x = rnd.uniform(-420, 380); yy = shore(x) + rnd.uniform(14, 90); r = rnd.uniform(5, 14)
        rock((x, yy), r, r * rnd.uniform(0.5, 0.9), i * 1.7, RK); foam_patch((x, yy), r * 0.9, r * 2.6, r * 3.2, scale=0.25)
    for k in range(40):                                              # surf along the foot of the cliffs
        x = -900 + k * 46; foam_patch((x, shore(x) + 6), 2, 30, 34, scale=0.12, sx=1.6)
    you = motoring('you', 250, 0, 0, heel=10); N.cloth_furled(you)
    K.camera((24, 80, 27), (0, -250, -12), 30)
    labels = [(tuple(top(you, 21)), 'You · no engine', 'blue'), ((-40, -335, 16), 'drifting onto a lee shore', 'red'),
              ((150, -420, 45), 'rocks 1 mile downwind')]
    arrows = [((0, -22, 2), (0, -120, 2), 'red'), ((32, 40, 15), (32, -90, 8), 'red')]
    labels.append(((32, 42, 18), 'wind F6, onshore', 'red'))
    note = 'PAN-PAN becomes MAYDAY'; expo = -0.4
else:
    raise SystemExit(f'no figure {ART} {FIG}')

bpy.context.scene.camera.data.clip_end = 400000
C.render(OUT, SAMPLES, SCALE, expo, labels, note, space='blender', arrows=arrows, extra=extra)
