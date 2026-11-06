# Article charter-checkin/hull ("Hull, deck and rig"), its five figures as Blender renders:
#   1  one mark, written properly: the port bow close, a 3 cm gelcoat chip with star cracks 40 cm aft of the stem,
#      a coin taped beside it for scale
#   2  hull, keel and rudder: the waterline cut-away seen broadside, the parts named
#   3  the guardrail: a loose stanchion, a frayed lifeline, a gate hook without its pin, on a side deck at the pontoon
#   4  mast and rigging: the bare rig broadside from the quay, sails stowed
#   5  ask for the base's rigger: a cap shroud's foot at the chainplate, a broken strand at the swage, rust streaks
#   blender --background --factory-startup --python docs/design/blender/art_checkin_hull.py -- --fig 3 [--samples 160] [--out x.jpg]
#   python3 docs/design/blender/art_checkin_hull.py --plans      (the schematics, <n>-plan.json)
import os, sys, math, json, random
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
DIR = os.path.join(HERE, '..', 'figure-style', 'articles', 'charter-checkin', 'hull')

# ===================================================================================================== plans
try: RU = json.load(open(os.path.join(DIR, 'ru.json')))
except Exception: RU = {}
def _t(x, y, s, size=26, w=700, f='var(--muted)', a='middle'):
    s = s.replace('&', '&amp;').replace('<', '&lt;')
    return f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{w}" fill="{f}" text-anchor="{a}">{s}</text>'

def _pill(x, y, text, kind='light', size=26):
    w = max(len(text), len(RU.get(text, ''))) * size * 0.58 + size * 1.4; h = size * 1.7   # wide enough for the Russian too
    fill = {'accent': 'var(--accent)', 'red': '#e8231a'}.get(kind, 'var(--bg)'); ink = 'var(--ink)' if kind == 'light' else '#fff'
    stroke = 'var(--tag-line)' if kind == 'light' else fill
    return f'<rect x="{x - w / 2:.1f}" y="{y - h / 2:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{h / 2:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="3"/>' + _t(x, y + size * 0.36, text, size, 700, ink)

def _frame(body, title, key, gid):
    W, H = 1280, 800; keyH = 40 + 40 * len(key) + 24
    s = f'<svg xmlns="http://www.w3.org/2000/svg" id="{gid}" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="Carlito, Arial, sans-serif" style="background:var(--bg)"><rect width="{W}" height="{H}" fill="var(--bg)"/>'
    s += body + f'<rect x="0" y="{H - keyH}" width="{W}" height="{keyH}" fill="var(--band)"/>'
    ky = H - keyH + 40; s += _t(30, ky, title, 30, 700, 'var(--ink)', 'start')
    for k in key: ky += 40; s += _t(30, ky, '· ' + k, 27, 400, 'var(--ink)', 'start')
    return s + '</svg>'

def form_svg():
    """The check-in form's boat outline, plan view, bow up: the mark drawn at the port bow, 40 cm aft of the stem,
    with what was written beside it, the two photos and the technician's initials."""
    b = '<path d="M 330 70 C 400 150 430 300 425 470 L 420 590 L 240 590 L 235 470 C 230 300 260 150 330 70 Z" fill="var(--bg)" stroke="var(--ink)" stroke-width="6" stroke-linejoin="round"/>'
    b += '<line x1="330" y1="70" x2="330" y2="590" stroke="var(--line)" stroke-width="3" stroke-dasharray="8 8"/>'
    b += _t(330, 330, 'outline on the form', 22, 400, 'var(--muted)')
    b += _t(190, 250, 'PORT', 26, 700, 'var(--ink)') + _t(470, 250, 'STBD', 26, 700, 'var(--ink)')
    # the mark: an X on the port bow, a dimension from the stem
    mx, my = 279, 150
    b += f'<path d="M{mx - 14} {my - 14} L{mx + 14} {my + 14} M{mx + 14} {my - 14} L{mx - 14} {my + 14}" stroke="#e8231a" stroke-width="7" stroke-linecap="round"/>'
    b += '<path d="M 330 70 C 312 92 296 118 285 140" fill="none" stroke="#e8231a" stroke-width="4" stroke-dasharray="6 6"/>'
    b += _pill(200, 40, '40 cm aft of the stem', 'red', 22)
    b += f'<line x1="{mx + 20}" y1="{my}" x2="560" y2="{my}" stroke="var(--ink)" stroke-width="3"/>'
    rows = [('What', 'gelcoat chip 3 cm, star cracks'), ('Where', 'port bow, 40 cm aft of the stem'), ('Photo 1', 'wide, to place it on the boat'),
            ('Photo 2', 'close up, a coin for scale'), ('Initials', 'technician')]
    y0 = 110
    b += '<rect x="560" y="80" width="680" height="300" rx="14" fill="var(--band)" stroke="var(--tag-line)" stroke-width="3"/>'
    for i, (k, v) in enumerate(rows):
        yy = y0 + 22 + i * 56
        b += _t(590, yy, k, 26, 700, 'var(--ink)', 'start') + _t(720, yy, v, 26, 400, 'var(--ink)', 'start')
    b += '<path d="M 980 352 c 20 -30 40 10 60 -20 c 14 -18 30 8 46 -10" fill="none" stroke="var(--accent)" stroke-width="4" stroke-linecap="round"/>'
    b += _pill(900, 480, 'what · how big · where', 'accent', 26) + _pill(900, 550, 'cracks, not scratches', 'light', 24)
    return _frame(b, 'One mark, written properly', ['On the form\'s outline, with the technician present and initialling', 'Two photos: one wide to place it, one close with a coin for scale'], 'ck-hull-1')

def guardrail_svg():
    """Elevation of the guardrail along the side deck: stanchions, two wires, the gate; the three faults in red."""
    b = '<rect x="40" y="520" width="1200" height="26" fill="#8a6a3a"/><rect x="40" y="546" width="1200" height="70" fill="var(--band)" stroke="var(--ink)" stroke-width="3"/>'
    b += _t(640, 592, 'SIDE DECK', 26, 700, 'var(--ink)')
    xs = [110, 330, 760, 1000, 1180]
    for x in xs:
        lean = 40 if x == 330 else 0
        b += f'<line x1="{x}" y1="520" x2="{x + lean}" y2="200" stroke="var(--ink)" stroke-width="12" stroke-linecap="round"/><rect x="{x - 24}" y="512" width="48" height="10" fill="var(--ink)"/>'
    # gate: an opening between 760 and 1000 with pelican hooks on the 1000 side
    b += '<line x1="560" y1="520" x2="560" y2="200" stroke="var(--ink)" stroke-width="12" stroke-linecap="round"/><line x1="560" y1="200" x2="610" y2="520" stroke="var(--ink)" stroke-width="6"/>'
    for yw in (205, 360):
        b += f'<line x1="110" y1="{yw}" x2="560" y2="{yw}" stroke="var(--ink)" stroke-width="5"/>'
        b += f'<line x1="560" y1="{yw}" x2="760" y2="{yw}" stroke="var(--ink)" stroke-width="5" stroke-dasharray="2 0"/>'
        b += f'<line x1="760" y1="{yw}" x2="1180" y2="{yw}" stroke="var(--ink)" stroke-width="5"/>'
    b += '<path d="M 1000 205 l -34 0 c -18 0 -18 22 0 22" fill="none" stroke="#e8231a" stroke-width="6"/>'
    b += '<line x1="560" y1="205" x2="760" y2="205" stroke="var(--bg)" stroke-width="0"/>'
    # frayed wire: whiskers
    for k in range(7):
        x = 180 + k * 9; b += f'<line x1="{x}" y1="205" x2="{x + (k % 3 - 1) * 10}" y2="{205 - 14 - (k % 2) * 8}" stroke="#e8231a" stroke-width="3"/>'
    b += f'<circle cx="370" cy="200" r="0"/>'
    b += _pill(210, 140, 'Lifeline: frayed', 'red', 26) + _pill(420, 300, 'Stanchion: loose', 'red', 26) + _pill(1000, 140, 'Gate hook: pin missing', 'red', 26)
    b += _t(880, 470, 'gate', 26, 700, 'var(--muted)')
    return _frame(b, 'Guardrail · fixed before you leave', ['A loose stanchion, a frayed wire, a hook that can open: each is the base\'s to fix now', 'An entry on the form does not hold anyone aboard'], 'ck-hull-3')

def plans():
    out = {1: {'noScale': True, 'svg': form_svg()}, 3: {'noScale': True, 'svg': guardrail_svg()}}
    for n, spec in out.items():
        with open(os.path.join(DIR, f'{n}-plan.json'), 'w') as f: json.dump(spec, f, ensure_ascii=False, indent=1)
    print('plans', sorted(out))

if '--plans' in sys.argv:
    plans(); sys.exit(0)

# ===================================================================================================== Blender
import bpy, bmesh
from mathutils import Vector, Matrix, Euler, noise as mnoise
import common as C, kit as K, kit_world as KW, art_checkin_gear as G
from art_checkin_gear import V, deg

arg = C.cli(); FIG = arg('--fig', 1); SAMPLES = arg('--samples', 160); SCALE = arg('--scale', 100)
OUT = G.out_path('hull', FIG, arg('--out', ''))
labels, arrows, note, expo, extra = [], [], None, -0.6, {}
C.reset()

def parts_below(y):
    bpy.context.view_layer.update(); keel, rud = [], []
    for o in y.objs:
        if o.type != 'MESH' or o.hide_render: continue
        lo, hi = K.bbox([o])
        if lo.z < -0.7 and (hi.y - lo.y) < 0.9 and (hi.x - lo.x) < 4.0:
            (keel if (lo.x + hi.x) / 2 > -3.0 else rud).append(o)
    return keel, rud

def pontoon(edge_y, x0, x1, top=0.45, width=2.4, side=1):
    """A floating pontoon along x, its edge at edge_y, extending away from the boat (side +1: towards +y)."""
    M = K.mats(); cy = edge_y + side * width / 2
    C.obj('float', C.rbox('float', (x1 - x0, width - 0.1, 0.8), 0.06, 2), M['float'], ((x0 + x1) / 2, cy, top - 0.45))
    plank = C.rbox('plank', (0.14, width, 0.035), 0.004, 1); plank.materials.append(M['planks'])
    x = x0
    while x < x1:
        o = bpy.data.objects.new('plank', plank); C.col.objects.link(o); o.location = (x, cy, top - 0.0175); x += 0.155
    C.obj('rub', C.rbox('rub', (x1 - x0, 0.12, 0.08), 0.02, 2), M['rubber'], ((x0 + x1) / 2, edge_y + side * 0.03, top - 0.1))

# ---------------------------------------------------------------------------------------------- 1  one mark
if FIG == 1:
    y = G.yacht(name='yacht'); y.place(0, 0, heading=90)          # bow east: the port side faces +y
    bpy.context.view_layer.update()
    zc = 0.95
    stem, _ = G.ray((12.0, 0.0, zc), (-1, 0, 0))                    # the stem at this height
    xs = stem.x - 0.40
    hit, nrm = G.ray((xs, 6.0, zc), (0, -1, 0))                     # the port topsides 40 cm aft of it
    print('STEM', tuple(round(v, 3) for v in stem), 'CHIP', tuple(round(v, 3) for v in hit), tuple(round(v, 2) for v in nrm))
    n = nrm.normalized(); up = V(0, 0, 1); t = up.cross(n).normalized(); u = n.cross(t).normalized()
    P = lambda a, b, off=0.0: hit + t * a + u * b + n * off
    # the chip: a shallow crater where the gelcoat flaked off, the grey laminate showing, star cracks round it
    crater = G.sphere('chip', 0.015, C.simple('chip-laminate', '#7c7a6c', 0.9), P(0, 0, -0.0105), seg=40)
    crater.rotation_mode = 'QUATERNION'; crater.rotation_quaternion = n.to_track_quat('Z', 'Y'); crater.scale = (1.0, 0.8, 0.75)
    rnd = random.Random(3); crack = C.simple('crack', '#3d3d38', 0.6)
    for k in range(9):
        a = deg(k * 40 + rnd.uniform(-12, 12)); L = rnd.uniform(0.018, 0.034); pts = []
        for j in range(6):
            r = 0.012 + L * j / 5; w = rnd.uniform(-0.002, 0.002) * j
            pts.append(P(r * math.cos(a) - w * math.sin(a), r * math.sin(a) + w * math.cos(a), 0.0004))
        G.tube('crack', pts, 0.0008, crack, 6)
    # a 2-euro coin under a strip of masking tape, 6 cm aft of the chip
    coin = C.cyl('coin', 0.0129, 0.0129, 0.0022, 48, C.simple('coin', '#c9b37a', 0.3, 1.0), P(-0.07, -0.045, 0.0012))
    coin.rotation_mode = 'QUATERNION'; coin.rotation_quaternion = n.to_track_quat('Z', 'Y')
    G.box('coin-core', (0.0185, 0.0185, 0.0005), P(-0.07, -0.045, 0.0024), C.simple('coin-core', '#b9bcc0', 0.3, 1.0)).rotation_mode = 'QUATERNION'
    tape = G.box('tape', (0.05, 0.02, 0.0004), P(-0.07, -0.045, 0.0026), C.simple('masking-tape', '#e6dcb8', 0.8))
    tape.rotation_mode = 'QUATERNION'; tape.rotation_quaternion = n.to_track_quat('Z', 'X')
    for o in bpy.data.objects:
        if o.name.startswith('coin-core'): o.rotation_quaternion = n.to_track_quat('Z', 'Y'); o.hide_render = True
    # a pencil ring round the chip, as the technician drew it
    ring = [P(0.028 * math.cos(deg(a)), 0.024 * math.sin(deg(a)), 0.0004) for a in range(0, 370, 15)]
    G.tube('pencil-ring', ring, 0.0007, C.simple('pencil', '#2b2d30', 0.6), 6)
    pontoon(0.0 + 2.6, -4.0, 9.0)
    K.sea('calm', size=20.0, repeat=8)
    K.coast(distance=700, bearing=330, height=70, town=True)
    K.day_sky(sun_az=10, sun_el=48, strength=0.25, haze=2.0)
    mid = hit.lerp(V(stem.x, stem.y, zc), 0.5)
    cam = KW.camera(mid + V(0.32, 0.86, 0.14), mid + V(0.0, 0.0, -0.02), 35); C.focus_on_centre(cam, 16.0)
    stem_pt = V(stem.x, stem.y + 0.005, zc)
    stem2, _ = G.ray((12.0, 0.0, zc - 0.28), (-1, 0, 0))
    labels = [(tuple(P(0, 0.03, 0.003)), 'gelcoat chip 3 cm, star cracks', 'red'), (tuple(stem2 + V(0.0, 0.01, 0.0)), 'stem')]
    extra = {'lines': ['Photo 2: close up, a coin for scale', 'Initialled by the technician']}
    a0 = P(0.0, -0.09, 0.003); a1 = V(stem.x, stem.y, zc - 0.09)
    arrows = [(tuple(a0.lerp(a1, 0.5)), tuple(a1), 'yellow'), (tuple(a0.lerp(a1, 0.5)), tuple(a0), 'yellow')]
    labels.append((tuple(a0.lerp(a1, 0.5) + V(0, 0, -0.06)), '40 cm aft of the stem', 'yellow'))
    note = 'Port bow: one mark, written properly'; expo = -0.6

# ---------------------------------------------------------------------------------------------- 2  hull
elif FIG == 2:
    y = G.yacht(name='yacht').place(0, 0, heading=90)
    KW.antifoul_hull(y)
    keel, rud = parts_below(y)
    klo, khi = K.bbox(keel); rlo, rhi = K.bbox(rud)
    KW.water_body(depth=12.0, size=600.0, density=0.009, color='#16606a', absorb='#3aa39a', reflect=0.25, absorb_density=0.012, center=(0, 0))
    KW.far_sea_ring(inner=300.0)
    KW.seabed(z=-5.0, size=150.0, res=200, center=(0, 20), colors=('#7d8669', '#99a07e', '#8b9274'))
    KW.stones(50, ((-25, 12), (25, 45)), -5.0, scale=(0.15, 0.5))
    KW.seagrass(((-25, 14), (25, 50)), -5.0, clumps=900, length=0.55)
    K.coast(distance=1400, bearing=0, height=80, town=False)
    K.day_sky(sun_az=200, sun_el=50, strength=0.25, haze=2.0)
    bow, stern = y.world((10.85, 0.13, 3.6)), y.world((-3.75, 0.13, 3.4))
    mid_x = (bow.x + stern.x) / 2
    KW.camera(Vector((mid_x, -21.0, 0.002)), Vector((mid_x, 0.0, -0.1)), lens=30)
    kx = (klo.x + khi.x) / 2
    labels = [((bow.x - 0.25, -1.0, 0.95), 'bow'), ((stern.x + 0.25, -1.6, 1.0), 'stern'),
              ((mid_x - 2.5, -1.8, 0.9), 'topsides'), ((kx + 0.6, -0.6, klo.z + 0.3), 'keel'), (((rlo.x + rhi.x) / 2, -0.4, (rlo.z + rhi.z) / 2), 'rudder'),
              (y.world((10.4, -0.8, 4.35)), 'pulpit'), (y.world((-3.3, -1.2, 4.35)), 'pushpit'), ((stern.x - 2.5, -3.0, 0.05), 'waterline', 'blue')]
    note = 'Hull, keel and rudder'; expo = -0.7

# ---------------------------------------------------------------------------------------------- 3  guardrail
elif FIG == 3:
    # a side deck at the pontoon, built here: topsides, deck with its toe rail, coachroof side, the guardrail
    hull = K.mats()['hull']; ns = C.nonskid_mat('deck-nonskid'); teak = C.teak_mat('toe-teak'); st = G.steel()
    X0, X1 = -5.0, 6.0; DZ = 1.25
    G.box('topsides', (X1 - X0, 0.08, DZ + 0.4), ((X0 + X1) / 2, 0.0, (DZ - 0.4) / 2), hull, 0.02)
    G.box('deck', (X1 - X0, 0.9, 0.05), ((X0 + X1) / 2, -0.45, DZ - 0.025), ns, 0.005)
    G.box('toe-rail', (X1 - X0, 0.05, 0.06), ((X0 + X1) / 2, -0.03, DZ + 0.03), teak, 0.012)
    G.box('coachroof-side', (X1 - X0 - 2, 0.06, 0.45), ((X0 + X1) / 2 - 0.5, -0.92, DZ + 0.22), hull, 0.03)
    G.box('coachroof', (X1 - X0 - 2, 1.5, 0.05), ((X0 + X1) / 2 - 0.5, -1.7, DZ + 0.45), ns, 0.01)
    for wx in (-2.0, 1.5): G.box('port-light', (0.6, 0.012, 0.12), (wx, -0.955, DZ + 0.25), C.simple('glass', '#0e1318', 0.05, 0.2, coat=1.0), 0.04)
    # stanchions every 2.1 m; the one at x = -0.6 loose, leaning out, its base lifted; the gate between 1.5 and 3.0
    SY = -0.09; H1, H2 = 0.62, 0.32
    def stanchion(x, lean=0.0, gate=False):
        b = V(x, SY, DZ)
        G.box('stanchion-base', (0.1, 0.07, 0.012), b + V(0, 0, 0.006), st, 0.004)
        G.cyl_between('base-socket', b, b + V(0, 0, 0.1), 0.019, st, 20)
        top = b + V(math.sin(deg(lean)) * H1, 0, H1)
        G.cyl_between('stanchion', b + V(0, 0, 0.05), top, 0.0125, st, 20)
        G.sphere('stanchion-top', 0.017, st, top)
        if gate:
            for sx in (-1, 1):
                if sx == (1 if x > 2 else -1): continue
                G.cyl_between('gate-brace', b + V(-0.3 * (1 if x > 2 else -1), 0.0, 0.0), b + V(0, 0, 0.45), 0.008, st, 12)
        return lambda h: b.lerp(top, h / H1)
    loose = stanchion(0.2, lean=14)
    G.box('base-gap', (0.003, 0.07, 0.012), V(0.2 - 0.05, SY, DZ + 0.016), C.simple('sealant-crack', '#2a2b2b', 0.8))
    S = {x: stanchion(x) for x in (-4.0, -1.9)}
    gA = stanchion(1.4, gate=True); gB = stanchion(2.9, gate=True); S[5.1] = stanchion(5.0)
    wire = C.simple('lifeline', '#e8e8e4', 0.3, 0.6)
    for h in (H1, H2):
        pts = [S[-4.0](h), S[-1.9](h), loose(h), gA(h)]
        for p, q in zip(pts, pts[1:]): G.cyl_between('lifeline', p, q, 0.0026, wire, 10)
        G.cyl_between('lifeline', gB(h), S[5.1](h), 0.0026, wire, 10)
    # the gate: wires from the gate stanchion B end in pelican hooks clipped to eyes on A; the upper hook's pin is gone
    def pelican(eye, pin=True):
        G.torus('eye', 0.012, 0.003, st, eye + V(0.012, 0, 0), rot=(deg(90), 0, 0))
        body = [eye + V(0.025, 0, 0.0), eye + V(0.06, 0, 0.005), eye + V(0.11, 0, 0.0)]
        G.tube('hook-body', [eye + V(0.012, 0, -0.012), eye + V(0.0, 0, -0.02), eye + V(-0.008, 0, -0.005), eye + V(0.012, 0, 0.012), eye + V(0.06, 0, 0.012), eye + V(0.13, 0, 0.004)], 0.0035, st, 10)
        G.cyl_between('hook-sleeve', eye + V(0.06, 0, 0.0), eye + V(0.12, 0, 0.0), 0.007, st, 14)
        G.torus('hook-lock', 0.008, 0.0028, st, eye + V(0.035, 0, 0.0), rot=(0, deg(90), 0))
        if pin:
            G.cyl_between('hook-pin', eye + V(0.035, -0.012, 0.0), eye + V(0.035, 0.012, 0.0), 0.0018, st, 8)
            G.torus('pin-ring', 0.007, 0.0012, st, eye + V(0.035, 0.016, 0.0), rot=(deg(90), 0, 0))
        else:
            G.cyl_between('pin-hole', eye + V(0.035, -0.0035, 0.0), eye + V(0.035, -0.0045, 0.0), 0.0019, C.simple('hole', '#050505', 0.9), 8)
        return eye + V(0.13, 0, 0)
    for h, pin in ((H1, True), (H2, False)):
        e = gA(h) + V(0.02, 0, 0); end = pelican(e, pin)
        G.cyl_between('gate-wire', end, gB(h), 0.0026, wire, 10)
    # the frayed lifeline: broken wire strands bristling out of the upper wire between the first two stanchions
    rnd = random.Random(8); fr = loose(H1).lerp(gA(H1), 0.5)
    for k in range(16):
        a = deg(rnd.uniform(0, 360)); L = rnd.uniform(0.03, 0.07)
        p = fr + V(rnd.uniform(-0.03, 0.03), 0, 0); d = V(rnd.uniform(-0.6, 0.6), math.cos(a), math.sin(a)).normalized()
        G.tube('strand', [p, p + d * L * 0.5 + V(0, 0, 0.003), p + d * L], 0.0009, C.simple('strand', '#d9d9d4', 0.3, 0.8), 5)
    G.cyl_between('winch-base', V(-1.2, -1.25, DZ + 0.45), V(-1.2, -1.25, DZ + 0.5), 0.09, st, 32)
    G.cyl_between('winch-drum', V(-1.2, -1.25, DZ + 0.5), V(-1.2, -1.25, DZ + 0.66), 0.07, st, 32, r2=0.06)
    G.cyl_between('cleat-horn', V(3.6, -0.3, DZ + 0.06), V(3.9, -0.3, DZ + 0.06), 0.016, st, 16)
    for dx in (-0.06, 0.06): G.cyl_between('cleat-leg', V(3.75 + dx, -0.3, DZ), V(3.75 + dx, -0.3, DZ + 0.06), 0.02, st, 12)
    pontoon(0.55, X0 - 2, X1 + 2, top=0.5, side=1)
    for fx in (-3.5, 0.5, 4.0):
        G.box('fender', (0.22, 0.22, 0.6), (fx, 0.2, 0.55), C.fabric_mat('fender-sock', '#1e2f55', '#5d75a8', 1400.0), 0.1)
    K.sea('calm', size=20.0, repeat=8)
    K.coast(distance=600, bearing=20, height=60, town=True)
    K.day_sky(sun_az=150, sun_el=45, strength=0.25, haze=2.0)
    cam = KW.camera(V(1.0, 1.55, 3.05), V(1.0, -0.45, 1.42), 28); C.focus_on_centre(cam, 16.0)
    labels = [(tuple(loose(H1 * 0.45) + V(0, 0, 0.0)), 'Stanchion: loose', 'red'), (tuple(fr + V(0, 0, 0.03)), 'Lifeline: frayed', 'red'),
              (tuple(gA(H2) + V(0.09, 0, 0.02)), 'Gate hook: pin missing', 'red')]
    note = 'Guardrail: all three fixed before you leave'; expo = -0.65

# ---------------------------------------------------------------------------------------------- 4  mast and rigging
elif FIG == 4:
    y = G.yacht(name='yacht'); y.place(0, 0, heading=90)
    K.sea('calm', size=30.0, repeat=10); K.day_sky(sun_az=200, sun_el=40)
    K.coast(distance=1800, bearing=0, height=90, town=False)
    W = lambda p: y.world(p)
    fs0, fs1 = W((10.62, 0.13, 3.95)), W((5.25, 0.13, 20.1))
    bs0, bs1 = W((-3.7, 0.13, 3.9)), W((4.93, 0.13, 20.6))
    c = W((3.4, 0.13, 11.0))
    K.camera((c.x + 0.5, c.y - 42.0, 3.2), (c.x + 0.5, c.y, 11.2), 36)
    labels = [(tuple(W((4.93, -0.2, 14.5))), 'mast: straight?', 'blue'), (tuple(W((2.4, -0.4, 5.7))), 'boom'),
              (tuple(fs0.lerp(fs1, 0.45)), 'forestay'), (tuple(bs0.lerp(bs1, 0.5)), 'backstay'), (tuple(W((4.93, -0.2, 21.0))), 'masthead: binoculars')]
    note = 'Sight up the mast; binoculars for the masthead'; expo = -0.7

# ---------------------------------------------------------------------------------------------- 5  the rigger
elif FIG == 5:
    hull = K.mats()['hull']; ns = C.nonskid_mat('deck-nonskid'); teak = C.teak_mat('toe-teak'); st = G.steel()
    DZ = 1.25
    G.box('topsides', (3.0, 0.08, DZ + 0.4), (0.0, 0.0, (DZ - 0.4) / 2), hull, 0.02)
    G.box('deck', (3.0, 1.0, 0.05), (0.0, -0.5, DZ - 0.025), ns, 0.005)
    G.box('toe-rail', (3.0, 0.05, 0.06), (0.0, -0.03, DZ + 0.03), teak, 0.012)
    # the chainplate through the deck, the toggle, the turnbuckle with split pins taped, the swage and the wire
    cp = V(0.0, -0.16, DZ)
    G.box('chainplate-cover', (0.12, 0.05, 0.008), cp + V(0, 0, 0.004), st, 0.004)
    G.box('chainplate', (0.012, 0.035, 0.12), cp + V(0, 0, 0.06), st, 0.003)
    G.cyl_between('toggle-pin', cp + V(-0.02, 0, 0.1), cp + V(0.02, 0, 0.1), 0.006, st, 12)
    G.box('toggle', (0.03, 0.03, 0.06), cp + V(0, 0, 0.13), st, 0.006)
    up = V(0.0, 0.08, 1.0).normalized()          # the shroud leans in towards the mast
    b0 = cp + V(0, 0, 0.115)
    G.cyl_between('turnbuckle-stud', b0, b0 + up * 0.06, 0.006, st, 12)
    G.cyl_between('turnbuckle-body', b0 + up * 0.04, b0 + up * 0.16, 0.012, st, 20)
    G.cyl_between('tape', b0 + up * 0.04, b0 + up * 0.075, 0.0135, C.simple('rigging-tape', '#efefea', 0.7), 20)
    G.cyl_between('turnbuckle-stud2', b0 + up * 0.16, b0 + up * 0.2, 0.006, st, 12)
    sw0 = b0 + up * 0.2
    G.cyl_between('swage', sw0, sw0 + up * 0.1, 0.0085, st, 20, r2=0.0065)
    top = sw0 + up * 2.4
    G.cyl_between('shroud', sw0 + up * 0.1, top, 0.004, C.simple('wire-1x19', '#d4d6d8', 0.25, 0.9), 12)
    # a broken strand: one wire of the 1x19 sprung out of the lay just above the swage, curling back (a meat hook)
    s0 = sw0 + up * 0.105
    G.tube('broken-strand', [s0 + V(-0.004, 0, 0), s0 + up * 0.02 + V(-0.006, 0, 0), s0 + up * 0.035 + V(-0.02, 0.004, 0), s0 + up * 0.03 + V(-0.035, 0.01, 0), s0 + up * 0.015 + V(-0.04, 0.012, 0)], 0.0008, st, 6)
    # rust weeping from the chainplate: brown streaks down the deck and over the toe rail onto the topsides
    rust_m, nt, bsdf, out = C.new_mat('rust-streak')
    C.setin(bsdf, 'Base Color', C.lin('#7a3d16')); C.setin(bsdf, 'Roughness', 0.7)
    tc = C.node(nt, 'ShaderNodeTexCoord'); sep = C.node(nt, 'ShaderNodeSeparateXYZ'); C.link(nt, tc.outputs['UV'], sep.inputs[0])
    n1 = C.noise(nt, tc.outputs['UV'], 18.0, 3.0)
    streak = C.node(nt, 'ShaderNodeTexWave', wave_type='BANDS', bands_direction='X', in_Scale=9.0, in_Distortion=3.0); C.link(nt, tc.outputs['UV'], streak.inputs['Vector'])
    fade = C.node(nt, 'ShaderNodeMapRange', in_From_Min=0.0, in_From_Max=1.0, in_To_Min=0.0, in_To_Max=0.9); C.link(nt, sep.outputs['Y'], fade.inputs['Value'])
    side = C.node(nt, 'ShaderNodeMapRange', in_From_Min=0.0, in_From_Max=0.5, in_To_Min=0.0, in_To_Max=1.0); C.link(nt, C.math_(nt, 'SUBTRACT', 0.5, C.math_(nt, 'ABSOLUTE', C.math_(nt, 'SUBTRACT', sep.outputs['X'], 0.5))), side.inputs['Value'])
    a = C.math_(nt, 'MULTIPLY', C.math_(nt, 'MULTIPLY', fade.outputs['Result'], side.outputs['Result']), C.math_(nt, 'MULTIPLY_ADD', streak.outputs['Fac'], 0.6, 0.4))
    tp = C.node(nt, 'ShaderNodeBsdfTransparent'); mx = C.node(nt, 'ShaderNodeMixShader')
    C.link(nt, a, mx.inputs['Fac']); C.link(nt, tp.outputs[0], mx.inputs[1]); C.link(nt, bsdf.outputs[0], mx.inputs[2]); C.link(nt, mx.outputs[0], out.inputs['Surface'])
    def decal(name, corners):
        me = bpy.data.meshes.new(name); me.from_pydata([tuple(c) for c in corners], [], [(0, 1, 2, 3)])
        me.uv_layers.new(name='UVMap').data.foreach_set('uv', [0, 1, 1, 1, 1, 0, 0, 0]); o = C.obj(name, me, rust_m); o.visible_shadow = False; return o
    rnd = random.Random(2)
    rust = [C.simple('rust-%d' % k, c, 0.75) for k, c in enumerate(('#7a3d16', '#8f4a1b', '#6a3412'))]
    for k, m in enumerate(rust): m.node_tree.nodes['Principled BSDF'].inputs['Alpha'].default_value = (0.45, 0.6, 0.35)[k]
    for k in range(9):                                           # streaks from the plate over the deck to the toe rail
        x = rnd.uniform(-0.04, 0.04); L = rnd.uniform(0.07, 0.13); w = rnd.uniform(0.004, 0.012)
        G.box('rust', (w, L, 0.0008), cp + V(x, L / 2 + 0.004, 0.0012), rust[k % 3])
    for k in range(8):                                           # and down the topsides below the toe rail
        x = rnd.uniform(-0.05, 0.05); L = rnd.uniform(0.08, 0.3); w = rnd.uniform(0.002, 0.007)
        G.box('rust', (w, 0.0008, L), V(x, 0.0405, DZ - 0.005 - L / 2), rust[k % 3])
        G.box('rust', (w, 0.0008, 0.06), V(x, -0.002, DZ + 0.032), rust[k % 3]).rotation_euler = (deg(90), 0, 0)
    pontoon(0.6, -3.0, 3.0, top=0.5, side=1)
    K.sea('calm', size=20.0, repeat=6)
    K.coast(distance=600, bearing=10, height=60, town=True)
    K.day_sky(sun_az=160, sun_el=45, strength=0.25, haze=2.0)
    cam = KW.camera(V(0.5, 0.8, DZ + 0.24), V(0.0, -0.1, DZ + 0.2), 33); C.focus_on_centre(cam, 14.0)
    labels = [(tuple(s0 + up * 0.03 + V(-0.035, 0.01, 0.0)), 'broken strand at the swage', 'red'), (tuple(V(0.0, 0.045, DZ - 0.1)), 'rust streaks below the chainplate', 'red'),
              (tuple(b0 + up * 0.1 + V(-0.014, 0, 0)), 'turnbuckle, pin taped')]
    note = 'Ask for the base\'s rigger'; expo = -0.6

C.render(OUT, SAMPLES, SCALE, expo, labels, note, space='blender', arrows=arrows, extra=extra)
