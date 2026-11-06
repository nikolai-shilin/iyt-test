# Bareboat Skipper test questions, figure type "encounter": one Blender render per question, from its spec in
# docs/design/figure-style/questions/bareboat-skipper/encounter.json (you, other at a bearing relative to your heading,
# distance in the 2D drawing's units, headings, sails and boom side, wind, note). Writes <id>/3d.jpg (1280 x 800) and
# 3d.labels.json, then <id>/plan.json and ru.json (q_encounter_plans.py).
# Views (VIEW below picks one per question; see the README beside the list for the rules):
#   drone   high oblique over both boats, when who is where and the crossing angle matter
#   helm    from our cockpit towards the other vessel, when the question is what you see
#   chase   behind and above our yacht towards a far ship, when our own sails would hide it from the cockpit
#   solo    one boat (tack, windward, marina, weather), a drone view of our yacht alone
#   fog     helm view into fog, the radar on the plotter showing the target
#   plotter the plotter close up (AIS-SART)
#   night   drone view at night, lights only
#   blender --background --factory-startup --python docs/design/blender/q_encounter.py -- --id bs-031 [--samples 128]
import os, sys, math, json, subprocess, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
import common as C, kit as K, kit_night as N
import q_encounter_props as P

QDIR = os.path.join(HERE, '..', 'figure-style', 'questions', 'bareboat-skipper')
arg = C.cli(); ID = arg('--id', 'bs-031'); SAMPLES = arg('--samples', 128); SCALE = arg('--scale', 100)
OUT = arg('--out', os.path.join(QDIR, ID, '3d.jpg'))
SPEC = next(x for x in json.load(open(os.path.join(QDIR, 'encounter.json'))) if x['id'] == ID)
F = SPEC['figure']; YOU = F['you']; OTH = F.get('other', {}); WIND = F.get('wind')
SOLO = OTH.get('dist', 80) < 1
def deg(a): return math.radians(a)
def fwd(h): return Vector((math.sin(deg(h)), math.cos(deg(h)), 0.0))

# ---------- per question: the view and anything the data does not say about the scene ----------
# keys: view, d (metres to the other), model (the other's kind), cam {az, el, k, lens}, sea, extra flags
VIEW = {
    'bs-025': dict(view='helm', model='mob', d=20),
    'bs-031': dict(view='drone'), 'bs-032': dict(view='drone'), 'bs-033': dict(view='drone'),
    'bs-034': dict(view='helm', model='motor', d=95),
    'bs-035': dict(view='drone', you_model='motor', model='motor', d=60),
    'bs-036': dict(view='drone', model='motor', slow=True),
    'bs-069': dict(view='solo', scene='strait', north=True),
    'bs-089': dict(view='solo', scene='berth'),
    'bs-099': dict(view='helm', model='mob', d=22),
    'bs-110': dict(view='solo'), 'bs-111': dict(view='solo', run=True), 'bs-120': dict(view='solo'), 'bs-121': dict(view='solo', heel=1.8),
    'bs-112': dict(view='drone', terms=True), 'bs-113': dict(view='drone', terms=True, model='ferry'),
    'bs-114': dict(view='drone', terms=True, model='trawler'), 'bs-115': dict(view='drone', terms=True, model='motor', L=8.0),
    'bs-116': dict(view='drone', terms=True, model='rib'),
    'bs-117': dict(view='drone'),
    'bs-336': dict(view='drone', model='swimmer', d=25, anchored=True, north=True),
    'bs-346': dict(view='helm', model='mob', d=18),
    'bs-372': dict(view='helm', model='motor', d=120, eye=(4.2, -1.55, 5.3)),
    'bs-382': dict(view='helm', model='motor', d=110, sea='fresh'),
    'bs-385': dict(view='helm', model='cargo', d=1400, L=150),
    'bs-386': dict(view='helm', model='cargo', d=700, L=140, shoal=True),
    'bs-387': dict(view='helm', model='motor', d=100),
    'bs-388': dict(view='chase', model='tanker', d=700, L=170, narrows=True),
    'bs-389': dict(view='helm', model='cargo', d=650, L=140, buoyed=True),
    'bs-392': dict(view='helm', model='motor', d=60, lane=True),
    'bs-395': dict(view='drone', model='motor', lane=True),
    'bs-402': dict(view='chase', model='cargo', d=700, L=160),
    'bs-404': dict(view='helm', d=150, hide_main=True, lens=35),
    'bs-405': dict(view='drone'), 'bs-406': dict(view='drone'), 'bs-407': dict(view='drone'), 'bs-408': dict(view='drone'),
    'bs-409': dict(view='drone', model='motor'), 'bs-410': dict(view='drone', model='motor'), 'bs-411': dict(view='drone', model='yacht_motor'),
    'bs-413': dict(view='drone'), 'bs-414': dict(view='drone', model='motor'),
    'bs-417': dict(view='helm', d=150, lens=50),
    'bs-419': dict(view='helm', model='cargo', d=650, L=140, lens=60),
    'bs-420': dict(view='helm', model='motor', d=100),
    'bs-421': dict(view='drone', model='ferry', L=45.0, fast=True),
    'bs-423': dict(view='helm', model='motor', d=140), 'bs-424': dict(view='drone', model='motor'), 'bs-425': dict(view='helm', model='motor', d=45),
    'bs-426': dict(view='chase', model='container', d=750, L=180),
    'bs-430': dict(view='drone', model='motor', trolling=True, L=9.0),
    'bs-431': dict(view='helm', model='seaplane', d=90),
    'bs-437': dict(view='helm', model='windsurfer', d=40, lens=40),
    'bs-438': dict(view='helm', model='trawler', d=75, cones=True, lens=70),
    'bs-444': dict(view='fog'), 'bs-445': dict(view='fog'), 'bs-446': dict(view='fog'),
    'bs-447': dict(view='helm', model='motor', d=120, mist=True),
    'bs-457': dict(view='helm', model='cargo', d=750, L=140),
    'bs-460': dict(view='helm', model='motor', d=90, rocks=True),
    'bs-637': dict(view='night', model='cargo', L=60.0),
    'bs-654': dict(view='solo', north=True),
    'bs-715': dict(view='solo', scene='storm', north=True),
    'bs-854': dict(view='solo', scene='fairway'),
    'bs-857': dict(view='drone', model='moored', d=13, scene='pontoon', you_still=True),
    'bs-859': dict(view='solo', scene='fairway', you_model='cat'),
    'bs-865': dict(view='drone', model='trawler', terms=True),
    'bs-947': dict(view='helm', d=160, flare=True, lens=45),
    'bs-960': dict(view='helm', model='dinghy', d=35, lens=55),
    'bs-962': dict(view='helm', model='yacht_motor', d=110, flagV=True, lens=45, eye=(10.3, -0.45, 5.15)),
    'bs-968': dict(view='plotter'),
    'bs-973': dict(view='drone', model='mob', d=30),
    'bs-974': dict(view='drone', model='mob', d=48),
    'bs-992': dict(view='helm', model='motor', d=55, tow=True, lens=40),
}
V = VIEW.get(ID, {'view': 'drone'})
VIEW_KIND = V['view']

def other_kind():
    if V.get('model'): return V['model']
    if OTH.get('sail'): return 'yacht'
    lab = OTH.get('label') or ''
    return {'Ship': 'cargo', 'Ship in lane': 'cargo', 'Tanker': 'tanker', 'Container ship': 'container', 'Ferry': 'ferry',
            'Fast ferry': 'ferry', 'Trawler': 'trawler', 'Fishing boat': 'trawler', 'Fishing': 'trawler', 'RIB': 'rib',
            'Dinghy': 'dinghy', 'MOB': 'mob', 'Swimmer': 'swimmer', 'Seaplane': 'seaplane', 'Windsurfer': 'windsurfer'}.get(lab, 'motor')

LENGTH = {'motor': 12.0, 'yacht': 14.6, 'yacht_motor': 14.6, 'moored': 14.6, 'cargo': 140.0, 'tanker': 170.0, 'container': 180.0,
          'ferry': 55.0, 'trawler': 22.0, 'rib': 5.0, 'dinghy': 3.6, 'mob': 1.0, 'swimmer': 1.0, 'seaplane': 10.0, 'windsurfer': 3.0}

labels, arrows, lines = [], [], []
NOTE = F.get('note')
C.reset()

# ---------- our boat ----------
def boom_sign(spec):
    b = spec.get('boom', -14)
    return 1 if b > 0 else -1

def make_you(x=0.0, y=0.0):
    h = YOU.get('hdg', 0)
    if V.get('you_model') == 'motor':
        root, vis, top = P.motor_yacht((x, y), h, 12.0); return None, top, root
    if V.get('you_model') == 'cat':
        root, vis, top = P.catamaran((x, y), h); return None, top, root
    if YOU.get('sail'):
        yt = P.sailing_yacht('you', h, WIND, boom_sign(YOU), x, y, heel_k=V.get('heel', 1.0), genoa=not V.get('run'))
    else:
        yt = P.motor_yacht_sun('you', h, x, y)
    return yt, P.yacht_top(yt), yt.root

# ---------- the other ----------
def other_pos(d):
    a = YOU.get('hdg', 0) + OTH.get('bearing', 0)
    return Vector((math.sin(deg(a)) * d, math.cos(deg(a)) * d, 0.0))

def make_other(p, kind):
    h = OTH.get('hdg', 180); L = V.get('L') or LENGTH[kind]; yt = None
    if kind == 'yacht':
        if V.get('hide_main'):   # running: main and a poled-out genoa on the same side, the genoa hiding the main
            yt = P.yacht('other', sails={'main': True, 'genoa': None, 'boom': -45}).place(p.x, p.y, heading=h)
            t0 = K.FORESTAY[0] - Vector((K.MAST.x, K.MAST.y, K.WL)); t1 = t0.lerp(K.FORESTAY[1] - Vector((K.MAST.x, K.MAST.y, K.WL)), 0.93)
            K.sail_surface('genoa-poled', t0, t1, Vector((2.2, -6.2, 5.2 - K.WL)), 0.16, -1, twist=6, parent=yt.root)
        else:
            yt = P.sailing_yacht('other', h, WIND, boom_sign(OTH), p.x, p.y)
        return yt, P.yacht_top(yt), yt.root
    if kind in ('yacht_motor', 'moored'):
        yt = P.motor_yacht_sun('other', h, p.x, p.y); return yt, P.yacht_top(yt), yt.root
    if kind == 'motor':
        r, vis, top = P.motor_yacht((p.x, p.y), h, L); return None, top, r
    if kind in ('cargo', 'tanker', 'container'):
        r, vis, top = P.merchant((p.x, p.y), h, L, kind); return None, top, r
    if kind == 'ferry':
        r, vis, top = P.ferry((p.x, p.y), h, L); return None, top, r
    if kind == 'trawler':
        r, vis, top = P.trawler((p.x, p.y), h, booms=bool(V.get('cones'))); return None, top, r
    if kind == 'rib':
        r, vis, top = P.rib((p.x, p.y), h, 5.5); return None, top, r
    if kind == 'dinghy':
        r, vis, top = P.dinghy_with_person((p.x, p.y), h, arms='up'); return None, top, r
    if kind in ('mob', 'swimmer'):
        k = 2.2 if VIEW_KIND == 'drone' else 1.25
        top = P.in_water((p.x, p.y), kind, heading=YOU.get('hdg', 0) + 180, k=k); return None, top, None
    if kind == 'seaplane':
        r, vis, top = P.seaplane((p.x, p.y), h); return None, top, r
    if kind == 'windsurfer':
        r, vis, top = P.windsurfer((p.x, p.y), h, sail_side=boom_sign(OTH), k=1.0); return None, top, r
    raise SystemExit('unknown kind ' + kind)

def add_wake(kind, p, h, L, yt=None):
    if V.get('still') or kind in ('mob', 'swimmer', 'moored', 'windsurfer', 'seaplane', 'dinghy'): return
    if yt is not None:
        K.wake(yt, 28 if kind == 'yacht' else 45, 8, 0.9 if kind == 'yacht' else 1.3); return
    if kind in ('cargo', 'tanker', 'container'): P.wake_decal(p, h, L * 1.2, L * 0.12, stern=L * 0.5, strength=1.0)
    elif kind == 'ferry': P.wake_decal(p, h, L * (2.6 if V.get('fast') else 1.4), L * 0.2, stern=L * 0.5, strength=1.4 if V.get('fast') else 1.0)
    elif kind == 'motor': P.wake_decal(p, h, L * (1.6 if V.get('slow') else 3.4), L * 0.45, stern=L * 0.5, strength=0.8 if V.get('slow') else 1.3)
    elif kind == 'rib': P.wake_decal(p, h, 30, 3.5, stern=2.5, strength=1.2)
    elif kind == 'trawler': P.wake_decal(p, h, 45, 7, stern=11, strength=0.9)

# ---------- labels ----------
def pill(pt, text, color=None):
    if text and text.strip(): labels.append((tuple(pt), text, color) if color else (tuple(pt), text))

def you_text(): return YOU.get('label') or 'You'
def other_text(): return OTH.get('label') if OTH.get('label') is not None else 'Other'

def project(p):
    cam = bpy.context.scene.camera; bpy.context.view_layer.update()
    q = world_to_camera_view(bpy.context.scene, cam, Vector(p)); return Vector((q.x * C.W, (1 - q.y) * C.H, q.z))

def unproject(sx, sy, depth):
    """World point at screen pixel (sx, sy), `depth` m in front of the camera."""
    cam = bpy.context.scene.camera; cd = cam.data; bpy.context.view_layer.update()
    tx = math.tan(cd.angle_x / 2) if C.W >= C.H else math.tan(cd.angle_y / 2) * C.W / C.H
    ty = tx * C.H / C.W
    nx, ny = (sx / C.W) * 2 - 1, 1 - (sy / C.H) * 2
    d = cam.matrix_world.to_quaternion() @ Vector((nx * tx, ny * ty, -1.0))
    return cam.matrix_world.translation + d * depth

def free_spot(cands, avoid):
    """The candidate screen position farthest from every pill anchor and point to avoid."""
    pts = [project(l[0]) for l in labels] + [Vector((x, y, 1)) for x, y in avoid] + [Vector((260, 50, 1))]
    return max(cands, key=lambda c: min((Vector((c[0], c[1])) - Vector((p.x, p.y))).length for p in pts))

def arrow_on_screen(direction, depth, text, color='blue', cands=None, px=150):
    """A wind or north arrow: horizontal in the world along `direction` (unit vector it points to), placed where
    there is room on screen, scaled to about `px` pixels."""
    cands = cands or [(1050, 230), (1050, 560), (650, 140), (240, 600), (1050, 400)]
    cam = bpy.context.scene.camera; axis = cam.matrix_world.to_quaternion() @ Vector((0, 0, -1))
    if abs(axis.normalized().dot(direction.normalized())) > 0.82: print('arrow along the line of sight, left out:', text); return
    sx, sy = free_spot(cands, [])
    mid = unproject(sx, sy, depth); mid.z = max(mid.z, 0.5)
    a, b = project(mid - direction), project(mid + direction)
    s = px / max(8.0, (Vector((a.x, a.y)) - Vector((b.x, b.y))).length)
    p0, p1 = mid - direction * s, mid + direction * s
    arrows.append((tuple(p0), tuple(p1), color))
    a0, a1 = project(p0), project(p1)
    anchor = p0 - direction * s * 0.6 if a1.y < a0.y - 40 else p0 + Vector((0, 0, 0.02 * depth))   # pointing up: the pill under the tail
    labels.append((tuple(anchor), text, color) if color != 'yellow' else (tuple(anchor), text))

def wind_arrow(depth):
    if WIND is None: return
    arrow_on_screen(-fwd(WIND), depth, 'Wind', 'blue')

def north_arrow(depth):
    arrow_on_screen(Vector((0, 1, 0)), depth, 'N', 'yellow', cands=[(150, 640), (1130, 640), (640, 680), (1130, 160)], px=110)

# ---------- cameras ----------
def drone(c, D, az, el, k=2.6, lens=32.0):
    a, e = deg(az), deg(el); c = Vector(c)
    eye = c + Vector((math.sin(a) * math.cos(e), math.cos(a) * math.cos(e), math.sin(e))) * (k * D)
    return K.camera(tuple(eye), tuple(c), lens), eye

def pick_az(pa, hy, pb):
    """Camera azimuth (from the centre) for two boats: across the line between them, behind our boat, on our side."""
    line = math.degrees(math.atan2(pb.x - pa.x, pb.y - pa.y))
    def score(az):
        return 1.0 * abs(math.sin(deg(az - line))) + 0.55 * math.cos(deg(az - (hy + 180))) + 0.35 * math.cos(deg(az - (line + 180)))
    return max(range(0, 360, 5), key=score)

def helm_camera(yt, target, size, rel):
    """From our cockpit towards `target` (a world point at the other vessel). Forward of the beam: a 24 mm view with
    our bow on one side and the other vessel on the other; on the beam: from the side deck; aft: over the pushpit."""
    s = 1 if rel >= 0 else -1; a = abs(rel)
    if a <= 8:    eye_m, lens = (-2.0, -1.6, 5.1), 24.0          # dead ahead: from the starboard side, clear of the mast
    elif a <= 75: eye_m, lens = (-2.3, -0.9 * s, 5.1), 24.0
    elif a <= 125: eye_m, lens = (-2.0, -1.5 * s, 5.1), 26.0
    else:          eye_m, lens = (0.6, -0.5 * s, 5.5), 22.0
    eye_m = V.get('eye') or eye_m; lens = V.get('lens') or lens
    fovh = math.degrees(2 * math.atan(18.0 / lens))
    off = (s * min(0.36 * fovh, a) if a <= 75 else (s * 0.19 * fovh if a <= 125 else 0.0)) if lens < 40 else 0.0
    eye = yt.world(eye_m)
    b = math.degrees(math.atan2(target.x - eye.x, target.y - eye.y))
    hy = YOU.get('hdg', 0)
    if a <= 75: b = hy + rel - off
    elif a > 125: b = b
    else: b = hy + rel - off
    b += V.get('look', 0.0)
    vfov = 2 * math.atan(11.25 / lens)
    pitch = -math.atan(V.get('horizon', 0.3 if a <= 125 else 0.5) * math.tan(vfov / 2))
    look = eye + Vector((math.sin(deg(b)) * math.cos(pitch), math.cos(deg(b)) * math.cos(pitch), math.sin(pitch))) * 50
    cam = K.camera(tuple(eye), tuple(look), lens)
    cam.data.clip_start = 0.05
    return cam, b

# ---------- sea and sky ----------
def sea(state='breeze', center=(0, 0), size=40.0, repeat=12):
    K.sea(V.get('sea', state), size=size, repeat=repeat, center=center)

EXPO = -0.7; EXTRA = {}

# ================================================================================================ scenes
kind = None if SOLO else other_kind()

if VIEW_KIND in ('drone', 'night'):
    terms = V.get('terms')
    if VIEW_KIND == 'night':
        N.night_scene('calm', moon=0.008)
    else:
        sea('calm' if V.get('anchored') or V.get('scene') else 'breeze', size=40.0, repeat=14)
    yt, ytop, yroot = make_you()
    L = V.get('L') or LENGTH[kind]
    d = V.get('d') or OTH.get('dist', 80) * 0.6 + max(0.0, L - 15.0) * 0.45
    p = other_pos(d)
    ot, otop, oroot = make_other(p, kind)
    if VIEW_KIND != 'night':
        if not V.get('anchored') and not V.get('you_still'):
            if yt is not None: K.wake(yt, 28 if YOU.get('sail') else 45, 8, 0.9 if YOU.get('sail') else 1.3)
            else: P.wake_decal((0, 0), YOU.get('hdg', 0), 40, 5.5, stern=6, strength=1.3)
        add_wake(kind, p, OTH.get('hdg', 180), L, ot)
    if V.get('anchored'): P.anchor_chain(yt, YOU.get('hdg', 0))
    if V.get('lane'):
        P.channel(tuple((-P.right(YOU.get('hdg', 0)) * 18).xy), YOU.get('hdg', 0), half_width=40.0, n=6, spacing=45.0, start=-130.0)
    if V.get('scene') == 'pontoon':      # the moored yacht alongside a pontoon on her far side
        h = OTH.get('hdg', 0); r = P.right(h)
        P.pontoon(tuple(p + r * 4.6 - fwd(h) * 30), tuple(p + r * 4.6 + fwd(h) * 40), 2.6)
        for k_ in (-1, 1):
            P.clone_yacht(ot, 'moored2', *(p + fwd(h) * 17 * k_).xy, h)
    if V.get('trolling'):   # two rods out astern, the lines streaming into the wake
        h = OTH.get('hdg', 0); st = p - fwd(h) * L * 0.5
        for s_ in (-1, 1):
            tip = st + P.right(h) * s_ * 1.6 + Vector((0, 0, 3.2)); end = st - fwd(h) * 40 + P.right(h) * s_ * 6
            C.tube('troll-line', [tip, end], 0.05, 6, 1.0, C.simple('troll', '#f2f2f2', 0.5))
            C.tube('rod', [st + P.right(h) * s_ * 1.0 + Vector((0, 0, 1.6)), tip], 0.04, 6, 1.0, C.simple('rod', '#202020', 0.4))
            P.foam_patch((end.x, end.y, 0.25), 0.8, 7 + s_)
    if VIEW_KIND == 'night':
        N.yacht_lights(yt, sidelights=True, stern=True)
        h = OTH.get('hdg', 0); f_, r_ = fwd(h), P.right(h)
        N.light('ship-mh1', p + f_ * L * 0.38 + Vector((0, 0, L * 0.22)), 'white', strength=9.0, power=60.0, radius=0.4)
        N.light('ship-mh2', p - f_ * L * 0.3 + Vector((0, 0, L * 0.3)), 'white', strength=9.0, power=60.0, radius=0.4)
        N.light('ship-red', p - f_ * L * 0.32 - r_ * L * 0.08 + Vector((0, 0, L * 0.16)), 'red', strength=7.0, power=40.0, radius=0.35)
        N.light('ship-green', p - f_ * L * 0.32 + r_ * L * 0.08 + Vector((0, 0, L * 0.16)), 'green', strength=7.0, power=40.0, radius=0.35)
        N.light('ship-stern', p - f_ * L * 0.5 + Vector((0, 0, L * 0.08)), 'white', strength=9.0, power=40.0, radius=0.35)
        EXTRA['bloom'] = 1.0; EXPO = 0.6
    c = p / 2; D = max(d, 40.0)
    cam_cfg = V.get('cam', {})
    if terms: az = YOU.get('hdg', 0) + 180 + cam_cfg.get('daz', 0); el = cam_cfg.get('el', 68)
    else: az = cam_cfg.get('az', pick_az(Vector((0, 0, 0)), YOU.get('hdg', 0), p)); el = cam_cfg.get('el', 42)
    cam, eye = drone(c, D, az, el, k=cam_cfg.get('k', 2.5 if not terms else 2.7), lens=cam_cfg.get('lens', 32))
    if VIEW_KIND != 'night': K.day_sky(sun_az=az + 25, sun_el=50)
    pill(ytop + Vector((0, 0, 1.0)), you_text(), 'blue')
    pill(otop + Vector((0, 0, 1.0)), other_text())
    wind_arrow((eye - c).length)
    if V.get('north'): north_arrow((eye - c).length)

elif VIEW_KIND == 'helm':
    sea(V.get('sea', 'breeze'), size=40.0, repeat=12)
    yt, ytop, yroot = make_you()
    L = V.get('L') or LENGTH[kind]
    d = V.get('d') or OTH.get('dist', 80)
    p = other_pos(d)
    ot, otop, oroot = make_other(p, kind)
    add_wake(kind, p, OTH.get('hdg', 180), L, ot)
    rel = ((OTH.get('bearing', 0) + 540) % 360) - 180
    size = {'mob': 3.0, 'swimmer': 3.0, 'dinghy': 5.0}.get(kind, L)
    aim = Vector((p.x, p.y, 0))
    cam, look_az = helm_camera(yt, aim, size, rel)
    K.day_sky(sun_az=look_az + 200, sun_el=38)
    if V.get('cones'):   # two cones, points together, from the trawler's crosstree
        top = oroot.matrix_world @ Vector(P.YARD)
        K.cone(top - Vector((0, 0, 0.9)), 0.42, 0.85, up=False); K.cone(top - Vector((0, 0, 1.75)), 0.42, 0.85, up=True)
        C.tube('halyard', [top, top - Vector((0, 0, 2.6))], 0.015, 6, 1.0, C.simple('halyard', '#202224', 0.6))
    if V.get('flare'):
        hand = ot.world((-1.2, -0.6, 6.6)); P.red_flare(hand, wind_to=(WIND or 90) + 180, k=1.8)
        P.person(ot.world((-1.2, -0.3, 3.75)), OTH.get('hdg', 0) + 90, arms='wave', top='#d94a1c')
    if V.get('flagV'):
        hoist = ot.world((K.MAST.x + 0.05, -1.4, 14.0)); P.flag(hoist, OTH.get('hdg', 0) + 180, 1.9, 1.6, os.path.join(HERE, 'textures', 'vhfm-flag-V.png'))
        C.tube('flag-halyard', [ot.world((K.MAST.x, -1.3, 16.5)), hoist, hoist - Vector((0, 0, 1.6))], 0.012, 6, 1.0, C.simple('halyard', '#202224', 0.6))
    if V.get('tow'):     # the towline from her stern back to our bow, sagging into the water between
        h = OTH.get('hdg', 0); st = p - fwd(h) * 6.0 + Vector((0, 0, 1.4)); bow = yt.world((11.4, 0.13, 2.0)) + fwd(YOU.get('hdg', 0)) * 2.0
        pts = [st.lerp(bow, t / 16) + Vector((0, 0, -1.8 * math.sin(math.pi * t / 16))) for t in range(17)]
        C.tube('towline', pts, 0.035, 8, 1.0, C.simple('towline', '#e9e2c4', 0.7))
    if V.get('shoal'):
        P.shoal((30, 30), YOU.get('hdg', 0), 150, 34, seed=4)
    if V.get('rocks'):
        for i, (x, y_) in enumerate([(26, 30), (30, 70), (28, 115), (34, 160), (40, 205)]):
            P.rock('rock', (x, y_, -0.4), 1.6 + (i % 3) * 0.7, i); P.foam_patch((x - 1.5, y_, 0.3), 4.5, 30 + i)
        K.coast(distance=70, bearing=90, length=900, height=28, town=False, seed=6)
        K.coast(distance=150, bearing=270, length=900, height=34, town=False, seed=8)
    if V.get('lane'):
        P.channel((-20, 0), YOU.get('hdg', 0), half_width=45.0, n=5, spacing=55.0, start=10.0)
    if V.get('buoyed'):   # a channel running 010/190 across our way, the ship in it
        ax = p - fwd(10) * 600
        for i in range(10):
            q = ax + fwd(10) * (i * 110.0)
            K.lateral_buoy('port', topmark=True, light=False, at=tuple((q - P.right(10) * 70).xy), scale=1.4)
            K.lateral_buoy('starboard', topmark=True, light=False, at=tuple((q + P.right(10) * 70).xy), scale=1.4)
    if V.get('mist'):     # just thinning fog: a light haze over the water
        fm = bpy.data.meshes.new('fog'); import bmesh
        bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bm.to_mesh(fm); bm.free()
        fog = C.obj('fog', fm, None, (0, 0, 15)); fog.scale = (900, 900, 32)
        m, nt, b, out = C.new_mat('fog'); nt.nodes.remove(b)
        vs = nt.nodes.new('ShaderNodeVolumePrincipled'); vs.inputs['Density'].default_value = 0.0035; vs.inputs['Color'].default_value = (0.86, 0.88, 0.9, 1)
        nt.links.new(vs.outputs[0], out.inputs['Volume']); fog.data.materials.append(m)
        bpy.context.scene.cycles.volume_bounces = 1; bpy.context.scene.cycles.volume_step_rate = 4.0
    pill(otop + Vector((0, 0, max(0.6, 0.02 * d))), other_text())
    if WIND is not None and not YOU.get('sail') and kind not in ('mob',): wind_arrow(60.0)
    elif WIND is not None and YOU.get('sail'): wind_arrow(60.0)

elif VIEW_KIND == 'chase':
    sea('breeze', size=40.0, repeat=14)
    yt, ytop, yroot = make_you(); add_wake('yacht', Vector((0, 0, 0)), YOU.get('hdg', 0), 14.6, yt)
    L = V.get('L') or LENGTH[kind]; d = V['d']; p = other_pos(d)
    ot, otop, oroot = make_other(p, kind); add_wake(kind, p, OTH.get('hdg', 180), L, ot)
    if V.get('narrows'):
        K.coast(distance=170, bearing=YOU.get('hdg', 0) + 270, length=5000, height=45, seed=5, town=False)
        K.coast(distance=360, bearing=YOU.get('hdg', 0) + 90, length=5000, height=55, seed=9, town=True)
    b = math.degrees(math.atan2(p.x, p.y))
    eye = -fwd(b) * 80 + Vector((0, 0, 36)); look = p * V.get('look_k', 0.3)
    cam = K.camera(tuple(eye), tuple(look), V.get('lens', 30))
    K.day_sky(sun_az=b + 200, sun_el=40)
    pill(ytop + Vector((0, 0, 1.0)), you_text(), 'blue'); pill(otop + Vector((0, 0, 4.0)), other_text())
    wind_arrow(120.0)

elif VIEW_KIND == 'solo':
    hdg = YOU.get('hdg', 0); scene = V.get('scene')
    if scene in ('fairway', 'berth'):
        sea('calm', size=30.0, repeat=10)
        # a marina: pontoons both sides of a fairway running along our heading, yachts moored stern-to
        f_, r_ = fwd(hdg), P.right(hdg)
        if V.get('you_model') == 'cat':
            yroot, vis, ytop = P.catamaran((0, 0), hdg); yt = None
            src = P.motor_yacht_sun('m0', hdg + 90, 999, 999)
        else:
            yt, ytop, yroot = make_you(); src = yt
        if scene == 'fairway':
            half = 16.0
            for sd in (-1, 1):
                base = r_ * sd * (half + 14.6 + 1.5)
                P.pontoon(tuple(base - f_ * 60), tuple(base + f_ * 60), 2.6)
                for i in range(-3, 4):
                    q = base - r_ * sd * (9.2) + f_ * (i * 5.2)
                    P.clone_yacht(src, 'moored', q.x, q.y, (hdg + (90 if sd > 0 else -90)) % 360 + 180)
        else:   # berth: bows-to a pontoon ahead of us, we have backed half out of our slot into the fairway
            P.pontoon(tuple(f_ * 7.6 - r_ * 45), tuple(f_ * 7.6 + r_ * 45), 2.6)
            P.pontoon(tuple(-f_ * 38.0 - r_ * 45), tuple(-f_ * 38.0 + r_ * 45), 2.6)
            for i in range(-4, 5):
                if i: P.clone_yacht(src, 'moored', *(r_ * (i * 5.0)).xy, hdg)
                q = -f_ * 30.5 + r_ * (i * 5.0 + 2.5); P.clone_yacht(src, 'moored', q.x, q.y, (hdg + 180) % 360)
            yt.place(*(-f_ * 6.0).xy, heading=hdg); ytop = P.yacht_top(yt); yroot = yt.root
        if src is not yt and src: src.root.location = (99999, 99999, 0)
        az = hdg + 180 + V.get('daz', 10); el = 62; D = 34
        cam, eye = drone(Vector(yroot.location) * 0.5 + fwd(hdg) * 6, D, az, el, k=2.2, lens=32)
        K.day_sky(sun_az=az + 25, sun_el=52)
        pill(ytop + Vector((0, 0, 1.0)), YOU.get('label') or 'You', 'blue')
    else:
        if scene == 'strait':
            sea('breeze', size=40.0, repeat=14)
            K.coast(distance=120, bearing=270, length=3000, height=70, seed=4, town=False)
            K.coast(distance=135, bearing=90, length=3000, height=85, seed=7, town=True)
        elif scene == 'storm':
            sea('calm', size=40.0, repeat=14)
        else:
            sea('breeze', size=40.0, repeat=14)
        yt, ytop, yroot = make_you()
        if YOU.get('sail') or scene == 'strait': K.wake(yt, 30, 8, 0.9)
        if scene == 'storm':
            P.cb_cloud((-40000, 2500, 0), r=5000, base=1300, top=12500)
            az, el, D, lens = 105, 16, 26, 26
            cam, eye = drone(Vector((0, 0, 4)), D, az, el, k=2.2, lens=lens)
            cam.rotation_euler = (Vector((-60, 10, 16)) - eye).to_track_quat('-Z', 'Y').to_euler(); cam.data.clip_end = 80000
            K.day_sky(sun_az=150, sun_el=35, strength=0.2)
        elif V.get('north') and scene != 'strait':
            az, el = 180 + 20, 50
            cam, eye = drone(Vector((0, 0, 3)), 30, az, el, k=2.3, lens=32); K.day_sky(sun_az=az + 25, sun_el=50)
        elif scene == 'strait':
            az = 180; eye = Vector((-12, -75, 32)); cam = K.camera(tuple(eye), (0, 230, 0), 26); K.day_sky(sun_az=205, sun_el=48)
        else:
            az, el = hdg + 180 + 35, 48
            cam, eye = drone(Vector((0, 0, 3)), 30, az, el, k=2.3, lens=32); K.day_sky(sun_az=az + 25, sun_el=50)
        pill(ytop + Vector((0, 0, 1.0)), you_text(), 'blue')
        dep = (eye - Vector((0, 0, 0))).length
        wind_arrow(dep * (0.5 if scene == 'storm' else 1.0))
    if V.get('north'): north_arrow((eye - Vector((0, 0, 0))).length * (0.5 if scene == 'storm' else 1.0))

elif VIEW_KIND in ('fog', 'plotter'):
    you = P.motor_yacht_sun('own', 0, 0, 0)   # radar and chart are heading-up: our heading changes nothing seen
    sea('calm', size=30.0, repeat=10)
    K.day_sky(sun_az=180, sun_el=30, strength=0.18 if VIEW_KIND == 'fog' else 0.25)
    rel = ((OTH.get('bearing', 0) + 540) % 360) - 180
    png = os.path.join(tempfile.gettempdir(), f'q-encounter-{ID}.png')
    if VIEW_KIND == 'fog':
        import bmesh
        fm = bpy.data.meshes.new('fog'); bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bm.to_mesh(fm); bm.free()
        fog = C.obj('fog', fm, None, (0, 120, 15)); fog.scale = (700, 700, 32)
        m, nt, b, out = C.new_mat('fog'); nt.nodes.remove(b)
        vs = nt.nodes.new('ShaderNodeVolumePrincipled'); vs.inputs['Density'].default_value = 0.022; vs.inputs['Color'].default_value = (0.86, 0.88, 0.9, 1)
        nt.links.new(vs.outputs[0], out.inputs['Volume']); fog.data.materials.append(m)
        bpy.context.scene.cycles.volume_bounces = 1; bpy.context.scene.cycles.volume_step_rate = 4.0
        res = json.loads(subprocess.run(['python3', os.path.join(HERE, 'q_encounter_tex.py'), 'radar', str(rel), '0.66', png], capture_output=True, text=True, check=True).stdout)
    else:
        res = json.loads(subprocess.run(['python3', os.path.join(HERE, 'q_encounter_tex.py'), 'sart', str(rel), '0.88', png, '3.0 nm'], capture_output=True, text=True, check=True).stdout)
    pod_at = you.world((-1.25, -0.32, 4.6))
    root, objs = K.load_model('chartplotter-raymarine-axiom.glb', drop_planes=False)
    bpy.context.view_layer.update(); lo, hi = K.bbox([o for o in objs if o.type == 'MESH'])
    k = 0.235 / (hi.x - lo.x); root.scale = (k,) * 3; bpy.context.view_layer.update(); lo, hi = K.bbox([o for o in objs if o.type == 'MESH'])
    root.location = (root.location.x - (lo.x + hi.x) / 2 + pod_at.x, root.location.y - (lo.y + hi.y) / 2 + pod_at.y, root.location.z - lo.z + pod_at.z)
    root.rotation_euler = (deg(-14), 0, 0)
    img = bpy.data.images.load(png); screen = None
    for o in objs:
        for sl in getattr(o, 'material_slots', []):
            if sl.material and sl.material.name.startswith('raymarine--displays'):
                mm, mnt, mb, _ = C.new_mat('axiom-screen')
                uv = mnt.nodes.new('ShaderNodeUVMap'); tx = mnt.nodes.new('ShaderNodeTexImage'); tx.image = img
                mnt.links.new(uv.outputs['UV'], tx.inputs['Vector']); mb.inputs['Base Color'].default_value = (0.01, 0.01, 0.012, 1)
                mnt.links.new(tx.outputs['Color'], mb.inputs['Emission Color']); mb.inputs['Emission Strength'].default_value = 4.0 if VIEW_KIND == 'fog' else 0.7
                mb.inputs['Roughness'].default_value = 0.6; mb.inputs['Coat Weight'].default_value = 0.0; mb.inputs['Specular IOR Level'].default_value = 0.0
                sl.material = mm; screen = o
    C.obj('pod', C.rbox('pod', (0.3, 0.14, 0.12), 0.035, 4), K.mats()['dark'], tuple(pod_at - Vector((0, 0, 0.07))))
    if VIEW_KIND == 'fog':
        eye = you.world((-1.92, -0.42, 5.0)); look = you.world((9.0, -0.3, 3.1)); K.camera(tuple(eye), tuple(look), 26)
    else:
        eye = you.world((-1.9, -0.36, 5.0)); look = you.world((-1.25, -0.32, 4.72)); K.camera(tuple(eye), tuple(look), 42)
    bpy.context.view_layer.update()
    # the target on the screen: the world point under its texture pixel
    def uv_to_world(o, u, v):
        me = o.data; me.calc_loop_triangles(); uvl = me.uv_layers.active.data; q = Vector((u, v))
        idx = {i for i, sl in enumerate(o.material_slots) if sl.material and sl.material.name.startswith('axiom-screen')}; hits = []
        for t in me.loop_triangles:
            if t.material_index not in idx: continue
            a, b_, c_ = (Vector(uvl[l].uv) for l in t.loops)
            v0, v1, v2 = b_ - a, c_ - a, q - a
            d00, d01, d11, d20, d21 = v0.dot(v0), v0.dot(v1), v1.dot(v1), v2.dot(v0), v2.dot(v1)
            den = d00 * d11 - d01 * d01
            if abs(den) < 1e-12: continue
            w1 = (d11 * d20 - d01 * d21) / den; w2 = (d00 * d21 - d01 * d20) / den; w0 = 1 - w1 - w2
            if min(w0, w1, w2) >= -1e-4:
                Pp = [me.vertices[i].co for i in t.vertices]; hits.append(o.matrix_world @ (Pp[0] * w0 + Pp[1] * w1 + Pp[2] * w2))
        if not hits: return None
        camp = bpy.context.scene.camera.matrix_world.translation
        return min(hits, key=lambda h: (h - camp).length)
    fx, fy = res['px']; pt = None
    for n in (0, 1, -1):
        pt = uv_to_world(screen, fx / 828.0, 1 - fy / 481.0 + n)
        if pt is not None: break
    pill(pt + Vector((0, 0, 0.004)), other_text())
    EXPO = -0.3 if VIEW_KIND == 'fog' else -0.5

def settle_frame(top=135.0, bottom=40.0, side=50.0, max_deg=8.0):
    """Turn the camera a little so every pill anchor sits inside the frame, below the note band."""
    cam = bpy.context.scene.camera
    for _ in range(6):
        pts = [project(l[0]) for l in labels]
        pts = [q for q in pts if q.z > 0]
        if not pts: return
        ys, xs = [q.y for q in pts], [q.x for q in pts]
        dy = (top - min(ys)) if min(ys) < top else ((C.H - bottom) - max(ys) if max(ys) > C.H - bottom else 0.0)
        dx = (side - min(xs)) if min(xs) < side else ((C.W - side) - max(xs) if max(xs) > C.W - side else 0.0)
        if abs(dy) < 2 and abs(dx) < 2: return
        vf = cam.data.angle_y if C.W < C.H else 2 * math.atan(math.tan(cam.data.angle_x / 2) * C.H / C.W)
        hf = cam.data.angle_x
        pitch = max(-deg(max_deg), min(deg(max_deg), dy / C.H * vf))
        yaw = max(-deg(max_deg), min(deg(max_deg), dx / C.W * hf))
        q = cam.matrix_world.to_quaternion()
        from mathutils import Quaternion
        rq = Quaternion(q @ Vector((1, 0, 0)), pitch) @ Quaternion(Vector((0, 0, 1)), yaw)
        cam.rotation_euler = (rq @ q).to_euler(); bpy.context.view_layer.update()
if VIEW_KIND not in ('fog', 'plotter'): settle_frame()
C.render(OUT, SAMPLES, SCALE, EXPO, labels, NOTE, space='blender', arrows=arrows, extra={**({'lines': lines} if lines else {}), **EXTRA})

# ---------- the plan and the Russian ----------
try:
    import q_encounter_plans as PL
    PL.write(ID)
except Exception as e:
    print('plan not written:', e)
