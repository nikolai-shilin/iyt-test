# Article yachtmaster-offshore/colregs: the night figures, as Blender renders. Each vessel carries the lights the Rules
# give her (Annex I heights and spacing, arcs: masthead 225° ahead, sidelights 112.5° each side, stern and towing
# light 135° astern, all-round 360°); a light shows only if we stand inside its arc. The camera stands on our deck
# (eye 2.8 m) and is fitted round her lights and hull. Figures:
#    7  pilot vessel on duty, under way, seen on her port bow: white over red, red sidelight
#    8  sailing vessel of 22 m, seen on her starboard bow: red over green at the masthead, green sidelight
#    9  hovercraft bow on: flashing yellow, masthead light, both sidelights
#   10  WIG craft lifting off, seen on her port side: high-intensity flashing red, masthead light, red sidelight
#   13  a 120 m ship 40° on her port bow (she bears 300° from us, heading 160°): two masthead lights, red
#   16  not under command, making way, from astern: two all-round reds over her sternlight
#   17  dredger at work, stopped, bow on: red-white-red, two reds on the blocked side, two greens to pass
#   18  tug and tow, restricted in her ability to manoeuvre, from astern: red-white-red, yellow towing light over
#       the sternlight; the tow's own sternlight to one side
#   19  trawler hauling her nets, stopped, beam on: green over white, white over red below (Annex II)
#   20  purse seiner hampered by her gear: red over white, two yellows flashing alternately (Annex II)
#   21  coaster aground (under 50 m): anchor light forward, two all-round reds
#   22  pair trawlers (Annex II): green over white each, searchlights forward and towards each other, the net between
#   23  a 150 m ship on her port bow sounding one short blast: the manoeuvring light flashing above her after masthead light
#   blender --background --factory-startup --python docs/design/blender/art_yof_colregs_night.py -- --fig 7 [--samples 128]
import os, sys, math, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import bpy, bmesh
from mathutils import Vector, Matrix, Euler
import common as C, kit as K
import q_lights_geo as G
import q_encounter_props as P

arg = C.cli(); FIG = arg('--fig', 7); SAMPLES = arg('--samples', 128); SCALE = arg('--scale', 100); EXPO = arg('--exposure', 0.75)
OUT = arg('--out', os.path.join(HERE, '..', 'figure-style', 'articles', 'yachtmaster-offshore', 'colregs', f'{FIG}-3d.jpg'))
def deg(a): return math.radians(a)

# ---------------------------------------------------------------------------------------------------- the night
def night(center=(0, 0), moon=0.0012, star_gain=2.5):
    K.night_sky(moon=moon, stars=True)
    for n in bpy.context.scene.world.node_tree.nodes:
        if n.type == 'VALTORGB' and abs(n.color_ramp.elements[0].color[0] - 0.6) < 1e-3:
            n.color_ramp.elements[0].color = (0.6 * star_gain, 0.62 * star_gain, 0.7 * star_gain, 1)
    m = bpy.data.objects.get('moon')
    if m:   # behind us and to one side: a faint sheen on hulls and sails, no glint in view
        m.data.angle = deg(2); m.rotation_euler = Vector((0.25, 0.8, -0.57)).to_track_quat('-Z', 'Y').to_euler()
    K.sea('calm', color='#050d14', foam=False, center=center)

RGB = {'r': (1.0, 0.05, 0.03), 'g': (0.05, 1.0, 0.25), 'w': (1.0, 0.92, 0.75), 'y': (1.0, 0.62, 0.06)}
GAIN = {'r': 0.55, 'g': 0.32, 'w': 5.0, 'y': 1.0}

def lamp(name, p, c, radius, power=30.0, gain=1.0):
    """A navigation light: a glowing lens sized to read in the picture, and a point lamp lighting her round it."""
    m, nt, b, out = C.new_mat(name + '-lens')
    em = C.node(nt, 'ShaderNodeEmission'); C.setin(em, 'Color', RGB[c] + (1,)); C.setin(em, 'Strength', GAIN[c] * gain)
    C.link(nt, em.outputs[0], out.inputs['Surface'])
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=20, v_segments=10, radius=radius)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = C.obj(name, me, m, Vector(p)); o.visible_shadow = False
    if power > 0:
        ld = bpy.data.lights.new(name, 'POINT'); ld.energy = power; ld.color = RGB[c]; ld.shadow_soft_size = max(0.05, radius * 0.3)
        lo = bpy.data.objects.new(name + '-lamp', ld); C.col.objects.link(lo); lo.location = Vector(p)
    return o

def dark(name, color, rough=0.55, metal=0.0): return C.simple(name, color, rough, metal)

# ---------------------------------------------------------------------------------------------------- vessels
# Every vessel is built in her own frame (x forward, y to port, z up, metres, origin amidships at the waterline)
# under a holder turned to her heading, so her lights are listed in that frame too.
def holder(name, pos, heading):
    return P.holder(name, pos, heading)

def under(objs, h):
    for o in objs:
        if o.parent is None: o.parent = h
    return objs

def box(name, size, at, mat, r=0.0):
    return C.obj(name, C.rbox(name, size, r, 2), mat, Vector(at))

def merchant_geom(L, kind='cargo'):
    """Where P.merchant() puts her masts and bridge (the same numbers), for her lights."""
    Bm = L * 0.155; D = L * 0.075 if kind != 'tanker' else L * 0.06
    xa = -L / 2 + 0.03 * L; aw = 0.13 * L; zb = D + 0.10 * L; hb = 0.032 * L
    rx = xa + aw * 0.72; radar_top = zb + hb + 0.07 * L
    fmx = L / 2 - 0.09 * L; fore_top = D + L * 0.02 + 0.13 * L
    return dict(B=Bm, D=D, rx=rx, radar_top=radar_top, fmx=fmx, fore_top=fore_top, bridge=zb + hb * 0.5, stern=-L / 2)

def trawler(pos, heading, k=1.1):
    """The UK trawler model under a holder: model x -16.7 (stern) .. 2.4 (bow), centreline y 1.1, waterline z K.TRAWLER_WL,
    her mast top near model (-1.45, 1.1, 9.7). In her frame: length 19 m x k, mast at x +5.7k."""
    h = holder('trawler', pos, heading)
    root, vis, _ = P.trawler((0, 0), 90.0, booms=True)
    root.parent = h; root.scale = (k,) * 3
    root.rotation_euler = (0, 0, 0); root.location = (7.15 * k, -1.1 * k, -K.TRAWLER_WL * k)
    bpy.context.view_layer.update()
    return h

def pole(name, x, y, z0, z1, r=0.08, mat=None):
    return C.cyl(name, r, r * 0.8, z1 - z0, 12, mat or dark('pole', '#2a2c2f', 0.5, 0.4), (x, y, (z0 + z1) / 2))

def tug(pos, heading, L=30.0, B=9.5):
    """A harbour tug: low aft deck with the towing hook, the house and wheelhouse forward, a mast on the wheelhouse."""
    h = holder('tug', pos, heading)
    hullm = C.simple('tug-hull', '#1b1d20', 0.5); red = C.simple('tug-red', '#8c2a20', 0.45); white = C.simple('tug-white', '#c9ccc8', 0.5)
    win = C.simple('tug-win', '#0e1114', 0.1, coat=0.8)
    secs = []
    for i in range(31):
        t = i / 30; x = -L / 2 + t * L
        hb = (B / 2) * (0.92 + 0.08 * min(1, t / 0.1)) if t < 0.62 else (B / 2) * max(0.05, math.cos((t - 0.62) / 0.38 * math.pi / 2) ** 0.7)
        sheer = 2.2 + (1.4 * ((t - 0.6) / 0.4) ** 2 if t > 0.6 else 0.0)
        secs.append([Vector(p) for p in [(x, -hb * 1.04, sheer), (x, -hb, 0.4), (x, -hb * 0.7, -2.6), (x, hb * 0.7, -2.6), (x, hb, 0.4), (x, hb * 1.04, sheer)]])
    objs = [P._loft('tug-hull', secs, hullm, cap0=True)]
    objs.append(box('bulwark', (L * 0.98, B * 1.02, 0.25), (0, 0, 2.3), red, 0.1))
    objs.append(box('house', (L * 0.36, B * 0.7, 2.6), (L * 0.1, 0, 2.2 + 1.3), white, 0.1))
    objs.append(box('wheelhouse', (L * 0.2, B * 0.62, 2.4), (L * 0.14, 0, 4.8 + 1.2), white, 0.1))
    objs.append(box('wh-win', (L * 0.202, B * 0.622, 0.9), (L * 0.14, 0, 6.3), win))
    objs.append(box('funnel', (1.6, 2.2, 3.0), (-L * 0.06, 0, 5.8), red, 0.3))
    objs.append(box('hook-post', (0.6, 0.6, 2.2), (-L * 0.2, 0, 3.2), hullm))
    for s in (-1, 1):
        objs.append(C.cyl('bitt', 0.3, 0.3, 1.0, 12, hullm, (-L * 0.44, s * 1.6, 2.7)))
    objs.append(C.cyl('fender', 1.2, 1.2, 2.0, 24, C.simple('tyre', '#0c0c0c', 0.9), (L / 2 - 0.9, 0, 2.6), rot=(0, deg(90), 0)))
    objs.append(pole('tug-mast', L * 0.16, 0, 7.2, 14.6, 0.14, white))
    under(objs, h); bpy.context.view_layer.update()
    return h

def barge(pos, heading, L=50.0, B=12.0):
    h = holder('barge', pos, heading)
    m = C.simple('barge', '#2b2924', 0.7)
    secs = []
    for i in range(11):
        t = i / 10; x = -L / 2 + t * L; hb = B / 2
        z0 = -1.5 if 0.08 < t < 0.92 else 0.6
        secs.append([Vector(p) for p in [(x, -hb, 2.0), (x, -hb, z0), (x, hb, z0), (x, hb, 2.0)]])
    o = P._loft('barge-hull', secs, m, cap0=True, cap1=True)
    cargo = box('barge-cargo', (L * 0.8, B * 0.85, 2.5), (0, 0, 3.2), C.simple('barge-load', '#3a3732', 0.8), 0.4)
    under([o, cargo], h)
    return h

def hovercraft(pos, heading, L=24.0, B=11.0):
    """An air-cushion vessel: black skirt round a buoyancy raft, a cabin forward, two ducted propellers aft."""
    h = holder('hover', pos, heading)
    rubber = C.simple('skirt', '#121314', 0.85); body = C.simple('hover-body', '#b9bdc0', 0.45); win = C.simple('hover-win', '#0d1013', 0.1, coat=0.8)
    objs = []
    rr = B / 2; a = L / 2 - rr
    def ring(z, s):
        pts = []
        for i in range(25):
            t = -math.pi / 2 + math.pi * i / 24; pts.append(Vector((a + rr * s * math.cos(t), rr * s * math.sin(t), z)))
        for i in range(25):
            t = math.pi / 2 + math.pi * i / 24; pts.append(Vector((-a + rr * s * math.cos(t), rr * s * math.sin(t), z)))
        return pts + [pts[0].copy()]
    secs = [ring(0.0, 0.86), ring(0.6, 1.0), ring(1.4, 1.0), ring(1.9, 0.94)]
    objs.append(P._loft('skirt', secs, rubber, cap0=False))
    objs.append(box('raft', (L * 0.95, B * 0.9, 0.6), (0, 0, 2.1), body, 0.3))
    objs.append(box('cabin', (L * 0.5, B * 0.62, 2.6), (L * 0.12, 0, 3.7), body, 0.5))
    objs.append(box('cabin-win', (L * 0.502, B * 0.622, 0.8), (L * 0.12, 0, 4.2), win))
    for s in (-1, 1):
        d = C.cyl('duct', 2.2, 2.2, 1.2, 32, body, (-L * 0.36, s * 2.6, 5.0), rot=(0, deg(90), 0)); objs.append(d)
        objs.append(box('rudder', (0.2, 0.15, 3.6), (-L * 0.4, s * 2.6, 5.0), body))
    objs.append(pole('hover-mast', L * 0.2, 0, 5.0, 8.4, 0.09, body))
    under(objs, h)
    return h

def wig(pos, heading, L=20.0, alt=2.2):
    """A wing-in-ground craft just off the water: a boat-like fuselage, stubby low wings with end plates, a T-tail."""
    h = holder('wig', pos, heading)
    body = C.simple('wig-body', '#c3c7c9', 0.4); win = C.simple('wig-win', '#0d1013', 0.1, coat=0.8)
    secs = []
    for i in range(21):
        t = i / 20; x = -L / 2 + t * L
        r = 1.15 * (math.sin(math.pi * min(1, t * 1.25)) ** 0.5 if t < 0.8 else math.sin(math.pi * 0.8 * 1.25) ** 0.5 * (1 - (t - 0.8) / 0.2 * 0.85))
        r = max(0.12, r); zc = alt + 1.1 + (0.4 * t if t > 0.6 else 0) - (0.5 * (1 - t / 0.2) if t < 0.2 else 0)
        secs.append([Vector((x, r * math.cos(a) * 0.9, zc + r * math.sin(a))) for a in [j / 16 * math.tau for j in range(17)]])
    objs = [P._loft('fuselage', secs, body, cap0=True, cap1=True)]
    objs.append(box('canopy', (2.6, 1.3, 0.6), (L * 0.28, 0, alt + 2.25), win, 0.25))
    wing = box('wing', (5.0, 13.0, 0.35), (L * 0.05, 0, alt + 0.4), body, 0.12); objs.append(wing)
    for s in (-1, 1): objs.append(box('endplate', (5.0, 0.18, 1.3), (L * 0.05, s * 6.5, alt + 0.1), body, 0.06))
    objs.append(box('fin', (2.8, 0.25, 4.0), (-L * 0.42, 0, alt + 3.6), body, 0.1))
    objs.append(box('tailplane', (2.2, 6.5, 0.22), (-L * 0.44, 0, alt + 5.5), body, 0.08))
    objs.append(C.cyl('engine', 0.7, 0.7, 3.0, 20, body, (L * 0.08, 0, alt + 2.8), rot=(0, deg(90), 0)))
    under(objs, h)
    return h

def pilot_boat(pos, heading, L=16.0):
    """The 11 m motor yacht stretched to a 16 m pilot boat, a light mast on her wheelhouse."""
    spin, vis, top = P.motor_yacht(pos, heading + 180, L, hull='#1e2226')   # the model's bow lies opposite motor_yacht()'s heading
    h = holder('pilot', pos, heading)
    pole('pilot-mast', 0.6, 0, top.z - 0.4, top.z + 3.6, 0.07).parent = h
    bpy.context.view_layer.update()
    return h, top.z

def big_yacht(pos, heading, k=1.45):
    """The Sun Odyssey under main and genoa, scaled to a 22 m yacht. Its own frame: the mast foot at the waterline;
    returns (yacht, to_frame) so lights can be given in model space."""
    yt = P.yacht('sail', sails={'main': True, 'genoa': 'starboard', 'boom': -16})
    yt.place(pos[0], pos[1], heading=heading, heel=3); yt.root.scale = (k,) * 3
    bpy.context.view_layer.update()
    return yt

# ---------------------------------------------------------------------------------------------------- lights
# kinds: 'mast' (225° ahead), 'side' (r port / g starboard, 112.5°), 'stern' and 'tow' (135° astern), 'round'
def visible(kind, c, R):
    a = ((R + 540) % 360) - 180
    if kind == 'mast': return abs(a) <= 112.5
    if kind == 'side': return (0 <= a <= 112.5) if c == 'g' else (-112.5 <= a <= 0)
    if kind in ('stern', 'tow'): return abs(a) >= 112.5
    return True

def aspect(pos, heading, eye=G.EYE):
    """Our bearing from her bow (+ to starboard), from where she lies and heads."""
    b = math.degrees(math.atan2(eye[0] - pos[0], eye[1] - pos[1]))
    return ((b - heading + 540) % 360) - 180

# ---------------------------------------------------------------------------------------------------- camera
def set_camera(cam):
    r, u, d = G.axes(cam['yaw'], cam['pitch'])
    cd = bpy.data.cameras.new('cam'); cd.sensor_fit = 'HORIZONTAL'; cd.sensor_width = G.SENSOR
    cd.lens = G.lens_of_s(cam['s']); cd.clip_start = 0.5; cd.clip_end = 20000
    o = bpy.data.objects.new('cam', cd); C.col.objects.link(o); bpy.context.scene.camera = o
    M = Matrix((r, u, tuple(-c for c in d))).transposed().to_4x4(); M.translation = Vector(cam.get('eye', G.EYE)); o.matrix_world = M
    return o

def fit_box(points, box=(220, 150, 1060, 600), eye=G.EYE, lens_range=(30, 600)):
    """yaw, pitch and scale that bring every point inside the picture box (x0, y0, x1, y1), centred in it."""
    az = [math.degrees(math.atan2(p[0] - eye[0], p[1] - eye[1])) for p in points]
    ref = az[0]; az = [((a - ref + 180) % 360) - 180 + ref for a in az]
    el = [math.degrees(math.atan2(p[2] - eye[2], math.hypot(p[0] - eye[0], p[1] - eye[1]))) for p in points]
    sa, se = max(max(az) - min(az), 0.05), max(max(el) - min(el), 0.05)
    k = min((box[2] - box[0]) / sa, (box[3] - box[1]) / se)                      # px per degree
    s = k * 180 / math.pi; s = min(max(s, G.s_of_lens(lens_range[0])), G.s_of_lens(lens_range[1])); k = s * math.pi / 180
    cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
    yaw = (max(az) + min(az)) / 2 - (cx - G.W / 2) / k
    pitch = (max(el) + min(el)) / 2 + (cy - G.H / 2) / k
    cam = dict(yaw=yaw, pitch=pitch, s=s, eye=eye)
    for _ in range(4):   # small-angle start, then correct the centre with the exact projection
        px = [G.project(p, cam) for p in points]
        mx = (max(q[0] for q in px) + min(q[0] for q in px)) / 2; my = (max(q[1] for q in px) + min(q[1] for q in px)) / 2
        cam['yaw'] += (mx - cx) / k; cam['pitch'] -= (my - cy) / k
    return cam

# ---------------------------------------------------------------------------------------------------- scenes
L_PX = 7.0              # a light's lens radius in the picture, px
lights, hulls, labels, note = [], [], [], None

def put(pos, heading, items, tag=''):
    """items: (kind, colour, (x, y, z) in her frame, size); keeps only the lights whose arc we stand in."""
    R = aspect(pos, heading)
    for i, (kind, c, p, *rest) in enumerate(items):
        if visible(kind, c, R): lights.append(dict(p=G.to_world(pos, heading, p), c=c, k=(rest[0] if rest else 1.0), name=f'{tag}{kind}-{c}-{len(lights)}', id=f'{tag}{i}'))
    return R

def ends(pos, heading, L, z=0.0, B=0.0):
    for x in (-L / 2, L / 2):
        hulls.append(G.to_world(pos, heading, (x, B / 2, z))); hulls.append(G.to_world(pos, heading, (x, -B / 2, z)))

def at(bearing, dist, R):
    return G.vessel_frame(bearing, dist, R)      # (position, heading) so that we see her from her bearing R

C.reset()
extra_lab = []   # (world point, text, colour) labels
SPOT = []        # searchlights (fig 22)
VOL = None       # haze for the searchlight beams

if FIG == 7:
    pos, hdg = at(4, 230, -55); L = 16.0
    h, top = pilot_boat(pos, hdg, L)
    put(pos, hdg, [('round', 'w', (0.6, 0, top + 3.5)), ('round', 'r', (0.6, 0, top + 2.5)),
                   ('side', 'r', (1.6, 2.6, top - 0.6)), ('side', 'g', (1.6, -2.6, top - 0.6)), ('stern', 'w', (-L / 2 + 0.3, 0, 1.8))])
    ends(pos, hdg, L, 0.5, 4.2)
    labels = [('0', 'white over red: pilot on duty'), ('2', 'red sidelight: under way')]
    note = 'Pilot vessel on duty, under way · seen on her port bow'
elif FIG == 8:
    pos, hdg = at(-3, 210, 58); k = 1.45
    yt = big_yacht(pos, hdg, k)
    def mp(q): return tuple(yt.world(q))
    for i, (kind, c, q) in enumerate([('round', 'r', (5.06, 0.13, 21.25)), ('round', 'g', (5.06, 0.13, 19.87)),
                       ('side', 'r', (10.0, 0.95, 4.25)), ('side', 'g', (10.0, -0.69, 4.25)), ('stern', 'w', (-3.75, 0.13, 4.3))]):
        if visible(kind, c, aspect(pos, hdg)): lights.append(dict(p=mp(q), c=c, k=1.0, name=f'{kind}-{c}-{len(lights)}', id=str(i)))
    hulls += [mp((11.3, 0.13, 3.0)), mp((-4.2, 0.13, 3.0)), mp((5.06, 0.13, 22.0))]
    labels = [('0', 'red over green: sailing (optional)'), ('3', 'green sidelight')]
    note = 'Sailing vessel of 22 m · no tricolour from 20 m: sidelights apart'
elif FIG == 9:
    pos, hdg = at(0, 260, 0); L = 24.0
    hovercraft(pos, hdg, L)
    put(pos, hdg, [('round', 'y', (L * 0.2, 0, 8.7), 1.25), ('mast', 'w', (L * 0.2, 0, 7.6)),
                   ('side', 'r', (L * 0.12, 3.45, 4.2)), ('side', 'g', (L * 0.12, -3.45, 4.2)), ('stern', 'w', (-L / 2, 0, 3.0))])
    ends(pos, hdg, L, 0.0, 11.0)
    labels = [('0', 'flashing yellow: air-cushion'), ('3', 'green'), ('2', 'red')]
    note = 'Hovercraft, bow on · masthead light, both sidelights, flashing yellow'
elif FIG == 10:
    pos, hdg = at(-4, 240, -80); L = 20.0; alt = 2.2
    wig(pos, hdg, L, alt)
    put(pos, hdg, [('round', 'r', (-L * 0.43, 0, alt + 5.8), 1.25), ('mast', 'w', (L * 0.26, 0, alt + 2.7)),
                   ('side', 'r', (L * 0.12, 6.6, alt + 0.75)), ('side', 'g', (L * 0.12, -6.6, alt + 0.75)), ('stern', 'w', (-L / 2, 0, alt + 1.4))])
    ends(pos, hdg, L, alt + 0.3, 0)
    labels = [('0', 'flashing red: WIG craft near the surface'), ('1', 'masthead'), ('2', 'red sidelight')]
    note = 'WIG craft taking off, seen on her port side'
elif FIG == 13:
    pos, hdg = at(-60, 820, -40); L = 120.0; g = merchant_geom(L)
    P.merchant(pos, hdg, L, 'container')
    put(pos, hdg, [('mast', 'w', (g['fmx'], 0, g['fore_top'] + 0.4)), ('mast', 'w', (g['rx'], 0, g['radar_top'] + 0.4)),
                   ('side', 'r', (g['rx'], g['B'] / 2 + 0.4, g['bridge'])), ('side', 'g', (g['rx'], -g['B'] / 2 - 0.4, g['bridge'])),
                   ('stern', 'w', (-L / 2 + 0.5, 0, g['D'] + 1.0))])
    ends(pos, hdg, L, 0.0, g['B'])
    labels = [('0', 'forward masthead light: lower'), ('1', 'after masthead light: higher'), ('2', 'red sidelight')]
    note = 'Ship of 120 m, 40° on her port bow: two masthead lights and red'
elif FIG == 16:
    pos, hdg = at(2, 380, 180); L = 90.0; g = merchant_geom(L)
    P.merchant(pos, hdg, L, 'cargo')
    rt = g['radar_top'] + 0.4
    put(pos, hdg, [('round', 'r', (g['rx'], 0, rt)), ('round', 'r', (g['rx'], 0, rt - 2.2)),
                   ('side', 'r', (g['rx'], g['B'] / 2 + 0.4, g['bridge'])), ('side', 'g', (g['rx'], -g['B'] / 2 - 0.4, g['bridge'])),
                   ('stern', 'w', (-L / 2 + 0.4, 0, g['D'] + 1.0))])
    ends(pos, hdg, L, 0.0, g['B'])
    labels = [('0', 'two all-round reds: not under command'), ('4', 'sternlight: making way')]
    note = 'Not under command, making way · seen from astern'
elif FIG == 17:
    pos, hdg = at(0, 300, 0); L = 70.0; g = merchant_geom(L)
    P.merchant(pos, hdg, L, 'cargo')
    x = g['fmx']; t = g['fore_top'] + 0.4; yd = g['B'] / 2 + 0.6; zw = g['D'] + 7.0
    h = holder('yard', pos, hdg)
    for o in (box('dredge-yard', (0.4, 2 * yd, 0.35), (x - 2.0, 0, zw + 0.5), dark('yard', '#2b2d30')),
              pole('dredge-post-p', x - 2.0, yd, g['D'], zw + 0.5, 0.12), pole('dredge-post-s', x - 2.0, -yd, g['D'], zw + 0.5, 0.12)):
        o.parent = h
    put(pos, hdg, [('round', 'r', (x, 0, t)), ('round', 'w', (x, 0, t - 2.1)), ('round', 'r', (x, 0, t - 4.2)),
                   ('round', 'r', (x - 2.0, -yd, zw)), ('round', 'r', (x - 2.0, -yd, zw - 2.1)),
                   ('round', 'g', (x - 2.0, yd, zw)), ('round', 'g', (x - 2.0, yd, zw - 2.1))])
    ends(pos, hdg, L, 0.0, g['B'])
    labels = [('0', 'red, white, red: restricted'), ('4', 'reds: blocked side'), ('6', 'greens: pass here')]
    note = 'Dredger at work, stopped, bow on · pass on the side of the greens'
elif FIG == 18:
    pos, hdg = at(4, 260, 150); L = 30.0
    tug(pos, hdg, L)
    fwd = Vector((math.sin(deg(hdg)), math.cos(deg(hdg)), 0)); tp = Vector(pos) - fwd * 190
    barge(tuple(tp), hdg + 4, 50.0)
    mx = L * 0.16
    put(pos, hdg, [('round', 'r', (mx - 0.35, 0, 14.3)), ('round', 'w', (mx - 0.35, 0, 12.3)), ('round', 'r', (mx - 0.35, 0, 10.3)),
                   ('mast', 'w', (mx + 0.25, 0, 13.8)), ('mast', 'w', (mx + 0.25, 0, 11.8)),
                   ('tow', 'y', (-L / 2 + 0.6, 0, 5.4)), ('stern', 'w', (-L / 2 + 0.6, 0, 3.4)),
                   ('side', 'r', (L * 0.14, 3.1, 6.0)), ('side', 'g', (L * 0.14, -3.1, 6.0))], tag='tug-')
    put(tuple(tp), hdg + 4, [('side', 'r', (24.0, 6.1, 2.6)), ('side', 'g', (24.0, -6.1, 2.6)), ('stern', 'w', (-25.0, 0, 2.6))], tag='tow-')
    # the tow line: from her hook down into the sea and up to the barge's bow
    a = Vector(G.to_world(pos, hdg, (-L * 0.2, 0, 3.6))); b = Vector(G.to_world(tuple(tp), hdg + 4, (25.0, 0, 2.2)))
    C.tube('towline', [a.lerp(b, s / 24) + Vector((0, 0, -3.2 * math.sin(math.pi * s / 24))) for s in range(25)], 0.12, 8, 1.0, dark('towline', '#202020', 0.8))
    ends(pos, hdg, L, 0.0, 9.5)
    labels = [('tug-0', 'red, white, red: restricted'), ('tug-5', 'yellow over white: towing')]
    note = 'Tug and tow, restricted in her ability to manoeuvre · from astern'
elif FIG == 19:
    pos, hdg = at(0, 210, 90); k = 1.15
    trawler(pos, hdg, k)
    mx = 5.7 * k; top = 8.6 * k
    h = holder('mast-ext', pos, hdg); pole('mast-ext', mx, 0, top - 0.4, top + 3.6, 0.07).parent = h
    put(pos, hdg, [('round', 'g', (mx, 0, top + 3.4)), ('round', 'w', (mx, 0, top + 1.4)),
                   ('round', 'w', (mx - 0.4, 0, top - 0.9)), ('round', 'r', (mx - 0.4, 0, top - 2.0))])
    ends(pos, hdg, 22.0, 0.0, 6.0)
    # her warps over the stern, down into the sea
    for s in (-1, 1):
        a = Vector(G.to_world(pos, hdg, (-9.5 * k, s * 1.4, 2.6))); z = Vector(G.to_world(pos, hdg, (-30.0, s * 5.0, -0.3)))
        C.tube('warp', [a.lerp(z, t / 8) + Vector((0, 0, -0.5 * math.sin(math.pi * t / 8))) for t in range(9)], 0.04, 6, 1.0, dark('warp', '#151515', 0.6))
    labels = [('0', 'green over white: trawling'), ('2', 'white over red: hauling')]
    note = 'Trawler hauling her nets, stopped · Annex II lights below her own'
elif FIG == 20:
    pos, hdg = at(0, 220, -90); k = 1.15
    trawler(pos, hdg, k)
    mx = 5.7 * k; top = 8.6 * k
    h = holder('mast-ext', pos, hdg); pole('mast-ext', mx, 0, top - 0.4, top + 3.6, 0.07).parent = h
    put(pos, hdg, [('round', 'r', (mx, 0, top + 3.4)), ('round', 'w', (mx, 0, top + 1.4)),
                   ('round', 'y', (mx - 0.4, 0, top - 0.9)), ('round', 'y', (mx - 0.4, 0, top - 2.0))])
    ends(pos, hdg, 22.0, 0.0, 6.0)
    # the purse seine: a ring of corks round her, a little skiff at the far side
    cork = C.simple('cork', '#c9a23a', 0.7); ctr = Vector(G.to_world(pos, hdg, (-4.0, 30.0, 0.0)))
    for i in range(90):
        a = i / 90 * math.tau; q = ctr + Vector((math.cos(a) * 34, math.sin(a) * 34, 0.12))
        if (q - Vector(pos)).length > 8: C.cyl('cork', 0.25, 0.25, 0.25, 8, cork, tuple(q))
    labels = [('0', 'red over white: fishing'), ('2', 'two yellows, flashing in turn')]
    note = 'Purse seiner hampered by her gear (Annex II)'
elif FIG == 21:
    pos, hdg = at(2, 260, 90); L = 45.0; g = merchant_geom(L)
    P.merchant(pos, hdg, L, 'cargo')
    hd = bpy.data.objects['ship']; hd.rotation_euler = (deg(-5), deg(1.5), hd.rotation_euler[2]); hd.location.z = 0.5
    rt = g['radar_top'] + 0.4
    put(pos, hdg, [('round', 'r', (g['rx'], 0, rt)), ('round', 'r', (g['rx'], 0, rt - 2.1)), ('round', 'w', (L / 2 - 2.5, 0, g['D'] + 3.0))])
    rocks = []
    for i in range(10):
        import random as _r; rr = _r.Random(i)
        q = Vector(G.to_world(pos, hdg, (rr.uniform(-30, 30), rr.uniform(-14, 14), -0.4)))
        P.rock('rock%d' % i, q, rr.uniform(0.8, 2.0), i)
    P.foam_patch(G.to_world(pos, hdg, (0, -9, 0.3)), 16.0, 3)
    ends(pos, hdg, L, 0.0, g['B'])
    labels = [('0', 'two all-round reds'), ('2', 'anchor light')]
    note = 'Aground, under 50 m: anchor light and two reds'
elif FIG == 22:
    sep = 90.0
    pA, hA = at(-11, 165, 14); pB = (pA[0] + sep * math.cos(deg(hA)), pA[1] - sep * math.sin(deg(hA)), 0.0)
    k = 1.15
    for i, (p, hd) in enumerate(((pA, hA), (pB, hA))):
        trawler(p, hd, k); mx = 5.7 * k; top = 8.6 * k
        h = holder('mast-ext%d' % i, p, hd); pole('mast-ext', mx, 0, top - 0.4, top + 2.6, 0.07).parent = h
        put(p, hd, [('round', 'g', (mx, 0, top + 2.4)), ('round', 'w', (mx, 0, top + 0.4)),
                    ('side', 'r', (3.0 * k, 2.6, 4.0)), ('side', 'g', (3.0 * k, -2.6, 4.0)), ('stern', 'w', (-9.5 * k, 0, 3.0))], tag=f'p{i}-')
        # her searchlight, forward and towards the other of the pair
        towards = 1 if i == 1 else -1                       # A's partner lies to her starboard, B's to her port
        src = Vector(G.to_world(p, hd, (6.5 * k, 0, 6.2 * k)))
        aim = Vector(G.to_world(p, hd, (120.0, towards * 55.0, 0.0)))
        SPOT.append((src, aim))
        a = Vector(G.to_world(p, hd, (-9.5 * k, -towards * 0.5, 2.6)))
        net = Vector(G.to_world(pA, hA, (-170.0, -sep / 2, -0.4)))
        C.tube('warp', [a.lerp(net, t / 12) + Vector((0, 0, -0.8 * math.sin(math.pi * t / 12))) for t in range(13)], 0.05, 6, 1.0, dark('warp', '#151515', 0.6))
        ends(p, hd, 22.0, 0.0, 6.0)
    labels = [('p0-0', 'green over white: trawling'), ('p1-0', 'green over white: trawling')]
    extra_lab.append((tuple(Vector(G.to_world(pA, hA, (0.0, -sep / 2, 1.0)))), 'never between them: the net', 'red'))
    note = 'Pair trawlers (Annex II): searchlights forward and towards each other'
elif FIG == 23:
    pos, hdg = at(6, 560, -38); L = 150.0; g = merchant_geom(L)
    P.merchant(pos, hdg, L, 'container')
    rt = g['radar_top'] + 0.4
    put(pos, hdg, [('mast', 'w', (g['fmx'], 0, g['fore_top'] + 0.4)), ('mast', 'w', (g['rx'], 0, rt)), ('round', 'w', (g['rx'], 0, rt + 3.0), 1.5),
                   ('side', 'r', (g['rx'], g['B'] / 2 + 0.4, g['bridge'])), ('side', 'g', (g['rx'], -g['B'] / 2 - 0.4, g['bridge'])),
                   ('stern', 'w', (-L / 2 + 0.5, 0, g['D'] + 1.0))])
    ends(pos, hdg, L, 0.0, g['B'])
    labels = [('2', 'manoeuvring light: one flash'), ('0', 'masthead lights'), ('3', 'red sidelight')]
    note = 'One flash with one short blast: I am altering my course to starboard'

# the night round the first vessel, the camera fitted round her lights and hull
pts = [l['p'] for l in lights if not l['name'].startswith('tow-')] + hulls
cx = sum(p[0] for p in pts) / len(pts); cy = sum(p[1] for p in pts) / len(pts)
night(center=(cx, cy))
cam = fit_box(pts, box=(250, 175, 1030, 610) if FIG not in (22,) else (150, 220, 1130, 600))
set_camera(cam)
for l in lights:
    depth = G.project(l['p'], cam)[2]
    lamp(l['name'], l['p'], l['c'], radius=L_PX * l['k'] * depth / cam['s'], power=40.0 if FIG not in (13, 23) else 300.0)
for src, aim in SPOT:
    ld = bpy.data.lights.new('searchlight', 'SPOT'); ld.energy = 2.5e6; ld.color = (1.0, 0.95, 0.85); ld.spot_size = deg(7); ld.spot_blend = 0.3; ld.shadow_soft_size = 0.2
    lo = bpy.data.objects.new('searchlight', ld); C.col.objects.link(lo); lo.location = src
    lo.rotation_euler = (aim - src).to_track_quat('-Z', 'Y').to_euler()
    lamp('searchlight-lens', tuple(src), 'w', radius=L_PX * 0.9 * G.project(tuple(src), cam)[2] / cam['s'], power=0)
if SPOT:   # a thin haze over the sea so the beams show
    fm = bpy.data.meshes.new('haze'); bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bm.to_mesh(fm); bm.free()
    hz = C.obj('haze', fm, None, (cx, cy, 12)); hz.scale = (900, 900, 24)
    m, nt, b, out = C.new_mat('haze'); nt.nodes.remove(b)
    vs = nt.nodes.new('ShaderNodeVolumeScatter'); vs.inputs['Density'].default_value = 0.0005; vs.inputs['Color'].default_value = (0.8, 0.85, 0.9, 1)
    nt.links.new(vs.outputs[0], out.inputs['Volume']); hz.data.materials.append(m)
    bpy.context.scene.cycles.volume_bounces = 0; bpy.context.scene.cycles.volume_step_rate = 4.0

lab = []
ids = {l['id']: l for l in lights}
for i, text in labels:
    if i not in ids: print('NO LIGHT', i, text); continue
    l = ids[i]; x, y, d = G.project(l['p'], cam); lab.append({'text': text, 'x': x, 'y': y - L_PX * l['k'] + 4}); continue
    x, y, d = G.project(lights[i]['p'], cam); lab.append({'text': text, 'x': x, 'y': y - L_PX * lights[i]['k'] + 4})
for p, text, colr in extra_lab:
    x, y, d = G.project(p, cam); e = {'text': text, 'x': x, 'y': y - 4}
    if not (40 < x < G.W - 40 and 60 < y < G.H): print('LABEL OFF FRAME', text); continue
    if colr: e['color'] = colr
    lab.append(e)
print('LIGHTS', FIG, 'lens %.0f' % G.lens_of_s(cam['s']), ' '.join('%s(%.0f,%.0f)' % (l['c'], *G.project(l['p'], cam)[:2]) for l in lights))
C.render(OUT, SAMPLES, SCALE, EXPO, [], note, space='blender', extra={'bloom': 1.0})
with open(os.path.splitext(os.path.abspath(OUT))[0] + '.labels.json', 'w') as f:
    json.dump({'note': note, 'labels': lab, 'arrows': [], 'bloom': 1.0}, f, ensure_ascii=False)
