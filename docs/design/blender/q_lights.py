# Test-question figures of type "lights" (bareboat-skipper): navigation lights at night, seen from our deck.
# Each question's 2D figure (figure-style/questions/bareboat-skipper/lights.json) gives its lights as coloured dots
# on a 320 x 200 drawing; this builds the 3D scene behind them (q_lights_specs.py: the vessel and her aspect, or
# the marks and the shore), fits the camera so every light lands where the figure has it, and renders
# <id>/3d.jpg with <id>/3d.labels.json (the figure's own light texts at their lights, its note as the note).
# Rule 1: it is night, so only the lights show; hulls are one plain, faint dark shape whatever the vessel.
#   blender --background --factory-startup --python docs/design/blender/q_lights.py -- --id bs-416 [--samples 128]
#   --level charter-checkin: questions/<level>/lights.json in, <level>/<id>/ out (default bareboat-skipper)
import os, sys, json, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy, bmesh
from mathutils import Vector, Matrix, Euler
import common as C, kit as K
import q_lights_geo as G
from q_lights_specs import SPECS
from q_lights_layout import layout, target

arg = C.cli(); QID = arg('--id', 'bs-416'); SAMPLES = arg('--samples', 128); SCALE = arg('--scale', 100)
EXPO = arg('--exposure', 0.75)
LEVEL = arg('--level', 'bareboat-skipper')
QDIR = os.path.join(HERE, '..', 'figure-style', 'questions', LEVEL)
OUT = arg('--out', os.path.join(QDIR, QID, '3d.jpg'))
ENTRY = {e['id']: e for e in json.load(open(os.path.join(QDIR, 'lights.json')))}[QID]
FIG = ENTRY['figure']; LIGHTS = FIG['lights']; SP = SPECS[QID]

def deg(a): return math.radians(a)

# ---------- the night ----------
def night(center=(0, 0), moon=0.0025, star_gain=2.5, sea_state='calm'):
    """kit.night_sky with brighter stars and the moon behind us; a near-black sea that still mirrors the lights."""
    K.night_sky(moon=moon, stars=True)
    for n in bpy.context.scene.world.node_tree.nodes:
        if n.type == 'VALTORGB' and abs(n.color_ramp.elements[0].color[0] - 0.6) < 1e-3:
            n.color_ramp.elements[0].color = (0.6 * star_gain, 0.62 * star_gain, 0.7 * star_gain, 1)
    m = bpy.data.objects.get('moon')
    if m:
        m.data.angle = deg(2)
        m.rotation_euler = Vector((0.25, 0.8, -0.57)).to_track_quat('-Z', 'Y').to_euler()
    K.sea(sea_state, color='#050d14', foam=False, center=center)

# ---------- lights ----------
RGB = {'r': (1.0, 0.05, 0.03), 'g': (0.05, 1.0, 0.25), 'w': (1.0, 0.92, 0.75), 'y': (1.0, 0.62, 0.06), 'b': (0.12, 0.3, 1.0)}
GAIN = {'r': 0.55, 'g': 0.32, 'w': 5.0, 'y': 1.0, 'b': 1.1}     # lens brightness: bright colours turn white under AgX

def ckey(c): return 'b' if str(c).startswith('#') else c

def lamp(name, p, c, radius, power=30.0, gain=1.0):
    """A navigation light: a glowing lens (sized to read in the picture) and a point lamp that lights her hull
    and the water round her."""
    k = ckey(c); rgb = RGB[k]
    m, nt, b, out = C.new_mat(name + '-lens')
    em = C.node(nt, 'ShaderNodeEmission'); C.setin(em, 'Color', rgb + (1,)); C.setin(em, 'Strength', GAIN[k] * gain)
    C.link(nt, em.outputs[0], out.inputs['Surface'])
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=20, v_segments=10, radius=radius)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = C.obj(name, me, m, Vector(p)); o.visible_shadow = False
    if power > 0:
        ld = bpy.data.lights.new(name, 'POINT'); ld.energy = power; ld.color = rgb; ld.shadow_soft_size = max(0.05, radius * 0.3)
        lo = bpy.data.objects.new(name + '-lamp', ld); C.col.objects.link(lo); lo.location = Vector(p)
    return o

def dark(name='night-dark', color='#181c21', rough=0.6): return C.simple(name, color, rough)

# ---------- shapes ----------
def capsule(L, B, n=12):
    """A plan outline: a rectangle with round ends (the same at both ends, so no bow shows)."""
    r = B / 2; a = L / 2 - r; pts = []
    for i in range(n + 1):
        t = -math.pi / 2 + math.pi * i / n; pts.append((a + r * math.cos(t), r * math.sin(t)))
    for i in range(n + 1):
        t = math.pi / 2 + math.pi * i / n; pts.append((-a + r * math.cos(t), r * math.sin(t)))
    return pts

def hull(pos, heading, L, B, fb, name='hull'):
    """A plain hull, its deck at `fb` above the water, dark; flat-ended so it never shows which end is the bow."""
    top = capsule(L, B); bot = [(x * 0.93, y * 0.72) for x, y in capsule(L, B)]
    n = len(top); verts = [(x, y, fb) for x, y in top] + [(x, y, -1.0) for x, y in bot]
    faces = [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)] + [tuple(range(n)), tuple(range(2 * n - 1, n - 1, -1))]
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    o = C.obj(name, me, dark('hull-night', '#15191e', 0.55)); o.location = Vector(pos)
    o.rotation_euler = (0, 0, deg(90 - heading))
    return o

def rig(pos, heading, L, B, fb, lights):
    """What carries her lights, as dark as the hull: a plain deckhouse amidships and a thin pole under each
    column of lights (from the deck, or from the deckhouse roof)."""
    lows = [p[2] for p in lights.values()]
    hh = fb + max(1.2, min(0.45 * (min(lows) - fb), 0.12 * L)) if lows else fb + 1.5
    me = C.rbox('house', (L * 0.22, B * 0.62, hh - fb), 0.15, 2)
    o = C.obj('house', me, dark('hull-night', '#15191e', 0.55))
    o.location = Vector(G.to_world(pos, heading, (0, 0, (fb + hh) / 2))); o.rotation_euler = (0, 0, deg(90 - heading))
    cols = {}
    for p in lights.values(): cols.setdefault((round(p[0] * 2) / 2, round(p[1] * 2) / 2), []).append(p[2])
    for (x, y), zs in cols.items():
        base = hh if abs(x) < L * 0.11 and abs(y) < B * 0.31 else fb
        if max(zs) - base < 0.8: continue
        w = Vector(G.to_world(pos, heading, (x, max(-B / 2, min(B / 2, y)), 0)))
        cyl('pole', max(0.06, L * 0.004), base, max(zs) - 0.1, (w.x, w.y), dark('pole-night', '#08090a', 0.95))

def cyl(name, r, z0, z1, at, mat=None):
    return C.cyl(name, r, r, z1 - z0, 20, mat or dark(), (at[0], at[1], (z0 + z1) / 2))

def body(kind, p):
    """What carries a light that is not on a vessel: dark, the same shape for every mark of a kind."""
    x, y, z = p
    if kind == 'buoy':      # a pillar buoy: float and a short pillar up to the light
        cyl('buoy-float', 1.0, -0.5, 0.8, (x, y)); cyl('buoy-pillar', 0.3, 0.8, z - 0.3, (x, y))
    elif kind == 'float':   # a small marker float on a pole
        cyl('float', 0.45, -0.3, 0.4, (x, y)); cyl('float-pole', 0.07, 0.4, z - 0.15, (x, y))
    elif kind == 'beacon':  # a beacon on a rock: a pillar from the water
        cyl('beacon-rock', 2.2, -0.5, 1.0, (x, y), dark('rock-night', '#1c1d1e', 0.9)); cyl('beacon', 0.7, 1.0, z - 0.4, (x, y))
    elif kind == 'tower':   # a harbour light: a short tower on the end of a low mole
        cyl('tower', 1.1, 2.0, z - 0.5, (x, y)); mole((x, y), (x - 160, y + 60), 2.0)
    elif kind == 'lighthouse':
        g = ground_z(x, y); cyl('lighthouse', 2.2, g - 1, z - 1.2, (x, y))

def mole(p0, p1, h=3.0, w=9.0):
    p0, p1 = Vector((p0[0], p0[1], 0)), Vector((p1[0], p1[1], 0)); d = p1 - p0
    o = C.obj('mole', C.rbox('mole', (d.length, w, h * 2), 1.0, 2), dark('mole-night', '#1b1d1f', 0.9))
    o.location = (p0 + p1) / 2; o.rotation_euler = (0, 0, math.atan2(d.y, d.x))

def ground_z(x, y):
    dg = bpy.context.evaluated_depsgraph_get()
    hit, loc, n, i, ob, mtx = bpy.context.scene.ray_cast(dg, Vector((x, y, 3000)), Vector((0, 0, -1)))
    return loc.z if hit and ob and ob.name.startswith('coast') else 0.0

def coast(distance, height, bearing=0.0):
    """A dark coastline, its haze and pale beach put out for the night."""
    K.coast(distance=distance, bearing=bearing, height=height, town=False, color='#20251d')
    m = bpy.data.materials.get('coast')
    for n in m.node_tree.nodes:
        if n.type == 'EMISSION': n.inputs['Strength'].default_value = 0.0
        if n.type == 'MIX' and n.data_type == 'RGBA' and not n.inputs[7].is_linked:
            c = n.inputs[7].default_value
            if c[0] > 0.5 and c[1] > 0.5: n.inputs[7].default_value = (c[0] * 0.12, c[1] * 0.12, c[2] * 0.12, 1)
    bpy.context.view_layer.update()

def clear_of_land(p, eye):
    """If the land hides a light from us, bring it forward along our line of sight (it stays on its picture point)."""
    dg = bpy.context.evaluated_depsgraph_get(); E = Vector(eye); P = Vector(p); d = P - E
    hit, loc, n, i, ob, mtx = bpy.context.scene.ray_cast(dg, E, d.normalized(), distance=d.length)
    if hit and ob and ob.name.startswith('coast'): return tuple(loc - d.normalized() * 3.0)
    return p

# ---------- camera ----------
def set_camera(cam):
    r, u, d = G.axes(cam['yaw'], cam['pitch'])
    cd = bpy.data.cameras.new('cam'); cd.sensor_fit = 'HORIZONTAL'; cd.sensor_width = G.SENSOR
    cd.lens = G.lens_of_s(cam['s']); cd.clip_start = 0.5; cd.clip_end = 20000
    o = bpy.data.objects.new('cam', cd); C.col.objects.link(o); bpy.context.scene.camera = o
    M = Matrix((r, u, tuple(-c for c in d))).transposed().to_4x4(); M.translation = Vector(cam.get('eye', G.EYE))
    o.matrix_world = M
    return o

def r_px(l): return 7.0 * (l.get('r', 6) / 6.0) ** 0.8    # the figure's dot size -> lens size in the picture

# ---------- labels ----------
def write_labels(cam, pts, extra_labels=()):
    """Overwrite <out>.labels.json: the figure's own texts at their lights (the pill's pointer just above each
    light), its note, bloom for the glow."""
    labs = []
    for i, l in enumerate(LIGHTS):
        if not l.get('t') or i not in pts: continue
        x, y, _ = G.project(pts[i], cam); labs.append({'text': l['t'], 'x': x, 'y': y - r_px(l) + 6})
    labs += list(extra_labels)
    with open(os.path.splitext(os.path.abspath(OUT))[0] + '.labels.json', 'w') as f:
        json.dump({'note': FIG.get('note'), 'labels': labs, 'arrows': [], 'bloom': 1.0}, f, ensure_ascii=False)

def report(cam, pts):
    idx = sorted(pts); px = [G.project(pts[i], cam)[:2] for i in idx]
    bad = G.check_order(px, [(LIGHTS[i]['x'], LIGHTS[i]['y']) for i in idx])
    print('LIGHTS', QID, 'lens %.0f' % G.lens_of_s(cam['s']), ' '.join('%d:%s(%.0f,%.0f)' % (i, LIGHTS[i]['c'], *p) for i, p in zip(idx, px)))
    for b in bad: print('  ORDER', b)

def lights_at(cam, pts, power=30.0):
    for i, p in pts.items():
        l = LIGHTS[i]; depth = G.project(p, cam)[2]
        lamp(f'light{i}', p, l['c'], radius=r_px(l) * depth / cam['s'], power=power)

def render(cam, pts, extra_labels=()):
    report(cam, pts)
    C.render(OUT, SAMPLES, SCALE, EXPO, [], FIG.get('note'), space='blender', extra={'bloom': 1.0})
    write_labels(cam, pts, extra_labels)

# ---------- the scenes ----------
C.reset()
kind = SP['kind']

if kind == 'vessel':
    lay = layout(SP, LIGHTS); cam = lay['cam']; pts = lay['points']
    night(center=tuple(lay['vessels'][0]['pos'][:2]))
    for k, v in enumerate(lay['vessels']):
        if v['hull']:
            hull(v['pos'], v['heading'], *v['hull'], name=f'hull{k}')
            own = SP['lights'] if k == 0 else SP['tow']['lights']
            if not v['deck'] and SP.get('poles', True): rig(v['pos'], v['heading'], *v['hull'], own)
    set_camera(cam)
    lights_at(cam, pts, power=40.0)
    if SP.get('deck'):    # deck lights: lamps that light her deck
        for i in pts:
            if LIGHTS[i].get('r', 6) <= 3:
                ld = bpy.data.lights.new(f'deck{i}', 'POINT'); ld.energy = 2500; ld.color = RGB['w']; ld.shadow_soft_size = 0.5
                lo = bpy.data.objects.new(f'deck{i}', ld); C.col.objects.link(lo); lo.location = Vector(pts[i]) + Vector((0, 0, 1.5))
    render(cam, pts)

elif kind == 'screen':
    lay = layout(SP, LIGHTS); cam = lay['cam']; pts = dict(lay['points'])
    ai = SP['anchor'][0]
    night(center=tuple(pts[ai][:2]))
    if SP.get('coast'):
        coast(SP['coast']['distance'], SP['coast']['height'], SP.get('bearing', 0))
        for i in list(pts):
            if i != ai: pts[i] = clear_of_land(pts[i], cam['eye'])
    for i, kd in SP.get('bodies', {}).items(): body(kd, pts[i])
    if SP.get('moles'):   # harbour entrance: the two mole heads carry the lights, the moles run out to each side
        a, b = SP['moles']; pa, pb = Vector(pts[a]), Vector(pts[b]); side = (pb - pa).normalized(); side.z = 0
        back = Vector((-side.y, side.x, 0))
        for p, sgn in ((pa, -1), (pb, 1)):
            head = Vector((p.x, p.y, 0))
            mole(head, head + side * sgn * 220 + back * 120, 3.0)
            cyl('mole-tower', 0.9, 3.0, p.z - 0.4, (p.x, p.y))
    set_camera(cam)
    lights_at(cam, pts, power=0.0 if SP.get('coast') and len(pts) > 3 else 20.0)
    render(cam, pts)

elif kind == 'diptych':
    # one light that alternates: the same buoy at two moments, side by side, blue on the left, yellow on the right
    import numpy as np
    lay = layout(SP, LIGHTS); camA = lay['cam']; P = lay['points'][0]
    night(center=tuple(P[:2])); body('buoy', P)
    s = camA['s']; tx_b = target(LIGHTS[1])[0]
    camB = dict(camA); camB['yaw'] = camA['yaw'] - math.degrees(math.atan((tx_b - target(LIGHTS[0])[0]) / s))
    depth = G.project(P, camA)[2]
    blue = lamp('wreck-light', P, LIGHTS[0]['c'], radius=r_px(LIGHTS[0]) * depth / s, power=20.0)
    lampB = bpy.data.objects['wreck-light-lamp']
    tmp = os.path.splitext(os.path.abspath(OUT))[0] + '-a.jpg'
    camo = set_camera(camA)
    report(camA, {0: P})
    C.render(tmp, SAMPLES, SCALE, EXPO, [], FIG.get('note'), space='blender')
    # moment two: the lens and its lamp turn yellow, the camera turns so the buoy sits on the right
    em = next(n for n in blue.active_material.node_tree.nodes if n.type == 'EMISSION')
    em.inputs['Color'].default_value = RGB['y'] + (1,); em.inputs['Strength'].default_value = GAIN['y']
    lampB.data.color = RGB['y']
    r, u, d = G.axes(camB['yaw'], camB['pitch'])
    M = Matrix((r, u, tuple(-c for c in d))).transposed().to_4x4(); M.translation = Vector(camB.get('eye', G.EYE)); camo.matrix_world = M
    report(camB, {1: P})
    C.render(OUT, SAMPLES, SCALE, EXPO, [], FIG.get('note'), space='blender')
    A = bpy.data.images.load(tmp); B = bpy.data.images.load(os.path.abspath(OUT))
    w, h = A.size; a = np.array(A.pixels[:]).reshape(h, w, 4); bb = np.array(B.pixels[:]).reshape(h, w, 4)
    cut = w // 2; out = bb.copy(); out[:, :cut] = a[:, :cut]
    out[:, cut - 2:cut + 2, :3] = 0.0           # a thin dark seam between the two moments
    img = bpy.data.images.new('diptych', w, h); img.pixels = out.ravel().tolist()
    img.filepath_raw = os.path.abspath(OUT); img.file_format = 'JPEG'; img.save()
    os.remove(tmp); os.remove(os.path.splitext(tmp)[0] + '.labels.json')
    labs = [{'text': LIGHTS[0]['t'], 'x': target(LIGHTS[0])[0], 'y': G.project(P, camA)[1] - r_px(LIGHTS[0]) + 6},
            {'text': LIGHTS[1]['t'], 'x': G.project(P, camB)[0], 'y': G.project(P, camB)[1] - r_px(LIGHTS[1]) + 6}]
    with open(os.path.splitext(os.path.abspath(OUT))[0] + '.labels.json', 'w') as f:
        json.dump({'note': FIG.get('note'), 'labels': labs, 'arrows': [], 'bloom': 1.0}, f, ensure_ascii=False)

elif kind == 'yacht':
    # a yacht motor-sailing, bow on: sails set (the question says so), steaming light on the mast, sidelights
    MODEL = {0: (5.45, 0.13, 11.5), 1: (8.3, -1.25, 3.7), 2: (8.3, 1.51, 3.7)}   # model space (bow +X, port +Y)
    def place(D):
        pos, hdg = G.vessel_frame(SP['bearing'], D, 0.0); return pos, hdg
    def model_world(pos, hdg, p):   # as kit.Yacht.world: model point relative to the mast foot at the waterline
        q = (p[0] - K.MAST.x, p[1] - K.MAST.y, p[2] - K.WL)
        return G.to_world(pos, hdg, q)
    D = 120.0; s_t = G.s_of_lens(110)
    tg = [target(LIGHTS[i]) for i in MODEL]
    for _ in range(6):
        pos, hdg = place(D); pts = {i: model_world(pos, hdg, p) for i, p in MODEL.items()}
        cam = G.fit([pts[i] for i in MODEL], tg, yaw0=SP['bearing'])
        if abs(cam['s'] / s_t - 1) < 0.03: break
        D *= s_t / cam['s']
    night(center=tuple(pos[:2]), moon=0.004)
    y = K.load_yacht(name='other', sails={'main': True, 'genoa': 'starboard', 'boom': -14}); y.place(pos[0], pos[1], heading=hdg, heel=3)
    set_camera(cam)
    lights_at(cam, pts, power=0.0)
    st = pts[0]   # the steaming light also lights her foredeck and the foot of the genoa a little
    ld = bpy.data.lights.new('steam-spot', 'SPOT'); ld.energy = 5; ld.color = RGB['w']; ld.spot_size = deg(110); ld.spot_blend = 0.7
    lo = bpy.data.objects.new('steam-spot', ld); C.col.objects.link(lo); lo.location = Vector(st)
    lo.rotation_euler = (Vector(model_world(pos, hdg, (9.5, 0.13, 3.6))) - Vector(st)).to_track_quat('-Z', 'Y').to_euler()
    render(cam, pts)

elif kind == 'pontoon':
    # our own yacht at night, lying in a marina berth: a finger pontoon along her starboard side, the main pontoon
    # across, ahead of her bow; we stand on it and look back at her. Only the lights the question switches on burn
    # (the data's lights, matched to her fittings by colour); a dead lantern is there, unlit.
    y = K.load_yacht(name='own'); y.place(0, 0, heading=0)
    night(center=(0, 0), moon=0.003)
    bpy.context.view_layer.update()
    bow = y.world((10.95, 0.13, 3.72))
    M = K.mats(); TOP = 0.5
    def deck_box(name, cx, cy, sx, sy):
        C.obj(name + '-float', C.rbox(name + '-float', (sx - 0.1, sy - 0.1, 0.8), 0.06, 2), dark('float-night', '#2a2d30', 0.8), (cx, cy, TOP - 0.45))
        C.obj(name, C.rbox(name, (sx, sy, 0.06), 0.01, 1), dark('planks-night', '#3a3530', 0.85), (cx, cy, TOP))
    ahead = bow.y + 6.5
    deck_box('main-pontoon', 0.0, ahead + 1.25, 40.0, 2.5)
    deck_box('finger', 3.35, (ahead - 12.0) / 2 + 0.5, 1.2, ahead + 12.0)
    FIT = {'steaming': (5.45, 0.13, 11.5), 'port': (8.3, 1.51, 3.7), 'starboard': (8.3, -1.25, 3.7), 'anchor': (5.06, 0.13, 21.0)}
    colour_fit = {'r': 'port', 'g': 'starboard'}
    pts = {}
    for i, l in enumerate(LIGHTS):
        f = colour_fit.get(l['c']) or ('anchor' if SP.get('anchor') else 'steaming')
        pts[i] = tuple(y.world(FIT[f]))
    for f in SP.get('dead', ()):          # an unlit lantern: dark glass where the light should be
        m = C.simple('dead-lens', '#0e2a16' if f == 'starboard' else '#2a0e0e', 0.15, coat=0.8)
        C.obj('dead-lens', C.rbox('dead-lens', (0.09, 0.05, 0.07), 0.015, 2), m, tuple(y.world(FIT[f])))
    eye = Vector((bow.x, ahead + 1.6, TOP + 1.65)) + Vector(SP.get('eye_off', (0, 0, 0)))
    look = Vector(SP.get('look', (bow.x, bow.y - 4.0, SP.get('look_z', 4.5))))
    d = look - eye
    cam = {'yaw': math.degrees(math.atan2(d.x, d.y)), 'pitch': math.degrees(math.atan2(d.z, math.hypot(d.x, d.y))), 's': G.s_of_lens(SP.get('lens', 28)), 'eye': tuple(eye)}
    set_camera(cam)
    lights_at(cam, pts, power=6.0)
    render(cam, pts)

elif kind == 'masthead':
    # our own yacht under sail, seen from a little astern and below: her tricolour lantern at the masthead,
    # red to port, green to starboard, white astern (spread a little so the three read apart)
    y = K.load_yacht(name='own', sails={'main': True, 'genoa': 'port', 'boom': 16}); y.place(0, 0, heading=0, heel=-4)
    night(center=(0, 0), moon=0.0015)
    MODEL = {0: (5.12, 0.42, 21.05), 1: (5.12, -0.16, 21.05), 2: (4.84, 0.13, 21.10)}
    pts = {i: tuple(y.world(p)) for i, p in MODEL.items()}
    eye = (0.0, -34.0, 3.2)
    cam = G.fit([pts[i] for i in MODEL], [target(LIGHTS[i]) for i in MODEL], eye=eye, yaw0=0.0,
                s_range=(G.s_of_lens(60), G.s_of_lens(500)))
    set_camera(cam)
    lights_at(cam, pts, power=0.0)
    C.cyl('lantern-base', 0.06, 0.06, 0.34, 12, dark(), tuple(y.world((5.0, 0.13, 20.88))))
    render(cam, pts)
