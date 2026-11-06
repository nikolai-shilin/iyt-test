# Article charter-checkin/ground ("Ground tackle, lines and the dinghy"), its nine figures as Blender renders:
#   1  at the bow: the anchor on the roller with its pin, the swivel, a chain mark, the windlass, the open locker
#      with the bitter end lashed by a rope you can cut
#   2  the windlass does nothing: the DC panel at the chart table, 12.6 V, the WINDLASS breaker off
#   3  choosing the bottom: a drone view of a cove 6-8 m deep, dark weed at A, pale sand at B, rocks at C
#   4  how much chain: the waterline cut-away, 30 m of chain marked every 10 m in 6 m, the third mark at the roller
#   5  for the night: the snubber hooked onto the chain below the roller, made fast on a bow cleat, the chain slack
#   6  stern-to: the town quay with a gap between two boats, the drop points 15, 50 and 100 m off, wind east
#   7  fender: its line on the guardrail with a clove hitch and a slipped half hitch (fig_rail.py, re-routed)
#   8  stern line: through the fairlead to the cleat, a chafe guard where it moves (render_scene.py cleat)
#   9  outboard at the pontoon: the dinghy, tank vent and primer bulb, kill cord, clamps and lock bar, lanyard
#   blender --background --factory-startup --python docs/design/blender/art_checkin_ground.py -- --fig 3 [--samples 160] [--out x.jpg]
#   python3 docs/design/blender/art_checkin_ground.py --plans      (the schematics, <n>-plan.json)
import os, sys, math, json, random
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
DIR = os.path.join(HERE, '..', 'figure-style', 'articles', 'charter-checkin', 'ground')

# ===================================================================================================== plans
try: RU = json.load(open(os.path.join(DIR, 'ru.json')))
except Exception: RU = {}
def plans():
    t = lambda x, z, text, **o: {'x': x, 'z': z, 'text': text, **o}
    P = lambda px, py: [px - 160, py - 100]                      # the bay drawing: 1 unit = 1 m
    land = [[P(0, 0), P(320, 0), P(320, 30), P(0, 30)], [P(0, 30), P(40, 30), P(40, 200), P(0, 200)], [P(280, 30), P(320, 30), P(320, 200), P(280, 200)]]
    weed = [P(x, y) for x, y in ((70, 70), (100, 62), (138, 72), (150, 98), (136, 122), (104, 130), (76, 116), (62, 94))]
    out = {}
    out[3] = {'sch': {'wind': 0, 'padPx': 40, 'title': 'Anchoring · the bottom decides',
                      'land': land, 'zones': [{'pts': weed, 'c': 'ink', 'fill': 'rgba(50,95,45,.22)', 'dash': '6 8'}],
                      'rocks': [{'x': 0, 'z': -45}], 'spots': [{'x': -50, 'z': -5, 'label': 'A'}, {'x': 40, 'z': 30, 'label': 'B'}, {'x': 0, 'z': -45, 'label': 'C'}],
                      'texts': [t(-50, 30, 'dark weed'), t(40, 64, 'pale sand', kind='accent'), t(62, -45, 'rocks, 3 m', kind='red'),
                                t(0, -84, 'LAND', pill=False, size=30)],
                      'fit': [{'x': -160, 'z': -100}, {'x': 160, 'z': 100}],
                      'key': ['Depth 6–8 m across the bay', 'B: pale sand holds; the anchor skids over weed and jams in rock']}}
    out[4] = {'profile': {'depth': 6, 'bow': 1, 'chain': 30, 'formula': '(6 m + 1 m) × 4–5 ≈ 30 m',
                          'title': 'Scope · counted by the chain marks (depth drawn deeper to read)',
                          'key': ['All chain, a mark every 10 m: three marks out is 30 m', 'The bow roller 1 m above the water counts in the depth']}}
    out[5] = {'noScale': True, 'svg': snubber_svg()}
    nb = [{'x': x, 'z': 8.3, 'hdg': 180, 'plain': True, 'L': 14} for x in (-32, -27, -22, -17, -12, -7, 7, 12, 17, 22, 27, 32)]
    out[6] = {'sch': {'wind': 90, 'padPx': 50, 'trueScale': True, 'title': 'Stern-to · where to drop',
                      'quays': [{'x1': -45, 'z1': -14, 'x2': 45, 'z2': 0}], 'boats': nb + [{'you': True, 'x': 0, 'z': 44, 'hdg': 180, 'noHeading': True, 'L': 14}],
                      'spots': [{'x': 0, 'z': 15, 'label': 'A'}, {'x': 0, 'z': 52, 'label': 'B'}, {'x': 0, 'z': 100, 'label': 'C'}],
                      'paths': [{'pts': [[9, 36], [9, 12]], 'c': 'course', 'dash': '14 10', 'arrow': True}],
                      'dims': [{'a': [-38, 0], 'b': [-38, 50], 'text': '50 m', 'off': 0}],
                      'texts': [t(0, -26, 'town quay · gap between two boats'), t(16, 15, '15 m'), t(18, 56, '50 m'), t(16, 100, '100 m')],
                      'fit': [{'x': -45, 'z': -30}, {'x': 45, 'z': 110}],
                      'key': ['Boat 14 m, depth 5 m: drop about four boat lengths off', 'B: square to the gap, then reverse in paying out chain']}}
    out[7] = {'noScale': True, 'svg': fender_svg()}
    out[8] = {'noScale': True, 'svg': sternline_svg()}
    for n, spec in out.items():
        with open(os.path.join(DIR, f'{n}-plan.json'), 'w') as f: json.dump(spec, f, ensure_ascii=False, indent=1)
    print('plans', sorted(out))

# ---- hand-drawn schematics in figure-schematic.js's language: 1280 x 800, a key band along the bottom ----
def _frame(body, title, key, gid):
    W, H = 1280, 800; keyH = 40 + 40 * len(key) + 24
    s = f'<svg xmlns="http://www.w3.org/2000/svg" id="{gid}" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="Carlito, Arial, sans-serif" style="background:var(--bg)"><rect width="{W}" height="{H}" fill="var(--bg)"/>'
    s += body
    s += f'<rect x="0" y="{H - keyH}" width="{W}" height="{keyH}" fill="var(--band)"/>'
    ky = H - keyH + 40
    s += _t(30, ky, title, 30, 700, 'var(--ink)', 'start')
    for k in key: ky += 40; s += _t(30, ky, '· ' + k, 27, 400, 'var(--ink)', 'start')
    return s + '</svg>'

def _t(x, y, s, size=26, w=700, f='var(--muted)', a='middle'):
    s = s.replace('&', '&amp;').replace('<', '&lt;')
    return f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{w}" fill="{f}" text-anchor="{a}">{s}</text>'

def _pill(x, y, text, kind='light', size=26):
    w = max(len(text), len(RU.get(text, ''))) * size * 0.58 + size * 1.4; h = size * 1.7   # wide enough for the Russian too
    fill = {'accent': 'var(--accent)', 'red': '#e8231a'}.get(kind, 'var(--bg)'); ink = 'var(--ink)' if kind == 'light' else '#fff'
    stroke = 'var(--tag-line)' if kind == 'light' else fill
    return f'<rect x="{x - w / 2:.1f}" y="{y - h / 2:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{h / 2:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="3"/>' + _t(x, y + size * 0.36, text, size, 700, ink)

def _path(d, c='#8a6a3a', w=9, dash=None, extra=''):
    return f'<path d="{d}" fill="none" stroke="{c}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"{f" stroke-dasharray={chr(34)}{dash}{chr(34)}" if dash else ""} {extra}/>'

def snubber_svg():
    """Side view at the bow: the gypsy, the chain over the roller hanging slack, the snubber from a cleat to a
    hook on the chain below the roller, taking the load down to the water."""
    b = ''
    b += '<rect x="0" y="380" width="1280" height="236" fill="rgba(60,140,190,.14)"/><line x1="0" y1="380" x2="1280" y2="380" stroke="#3c8cbe" stroke-width="5"/>'
    # the bow in profile, stem to the right
    b += '<path d="M120 210 L760 210 C 820 214 860 230 880 250 L 820 380 L 700 470 L 120 470 Z" fill="var(--ink)"/>'
    b += '<rect x="700" y="196" width="190" height="20" rx="6" fill="#9aa3ab"/><circle cx="880" cy="206" r="20" fill="#c9ced3" stroke="var(--ink)" stroke-width="4"/>'
    # windlass and its gypsy
    b += '<rect x="520" y="150" width="70" height="60" rx="10" fill="#9aa3ab" stroke="var(--ink)" stroke-width="4"/><circle cx="555" cy="150" r="34" fill="#c9ced3" stroke="var(--ink)" stroke-width="5"/>'
    # cleat
    b += '<rect x="400" y="196" width="80" height="14" rx="5" fill="#c9ced3" stroke="var(--ink)" stroke-width="3"/>'
    # chain: gypsy -> roller (slack, a dip between) -> down to the hook point and on to the anchor
    b += _path('M 555 116 C 640 110 640 240 720 238 C 800 236 840 190 880 186 C 930 182 960 300 990 420 L 1040 520 L 1110 580', '#4a4f55', 9, '12 6')
    # the snubber: cleat, over the toe rail, down to the hook on the chain
    b += _path('M 440 200 C 600 200 800 222 896 230 C 940 260 975 330 992 425', '#8a6a3a', 10)
    b += '<path d="M 980 418 l 24 10 l -8 22 z" fill="var(--accent)" stroke="var(--ink)" stroke-width="3"/>'
    b += _pill(560, 70, 'gypsy: chain slack', 'light', 26) + _pill(330, 260, 'snubber on a cleat', 'accent', 26)
    b += _pill(1110, 380, 'hook on the chain', 'light', 26) + _pill(1190, 520, 'to the anchor', 'red', 24)
    return _frame(b, 'For the night · the snubber takes the load', ['Hook on below the roller, made fast on a cleat: the chain behind it hangs slack', 'The windlass and gypsy carry nothing: they lift chain, nothing more'], 'ck-ground-5')

def fender_svg():
    """The guardrail wire across, the fender line coming up to it: a clove hitch, the end slipped round the standing part."""
    b = '<line x1="80" y1="250" x2="1200" y2="250" stroke="var(--ink)" stroke-width="22" stroke-linecap="round"/>'
    rope = '#8a6a3a'
    # clove hitch: two turns round the wire, the second crossing over the first
    b += _path('M 560 610 L 560 300 C 560 225 610 225 615 250', rope, 12)
    b += _path('M 615 250 C 620 290 650 290 660 250 C 665 210 700 210 705 250', rope, 12)
    b += _path('M 560 290 L 650 210', rope, 12)
    b += _path('M 705 250 C 712 300 700 330 690 360 C 670 410 600 420 572 440 C 540 462 560 492 600 488 C 650 482 690 470 700 520 C 705 560 690 590 680 640', rope, 12)
    # the fender
    b += '<rect x="510" y="610" width="100" height="160" rx="46" fill="#1e2f55"/>'
    b += _pill(240, 190, 'guardrail', 'light', 26) + _pill(900, 200, 'clove hitch', 'accent', 26) + _pill(890, 470, 'slipped half hitch', 'accent', 26)
    b += _pill(330, 520, 'fender line', 'light', 26) + _pill(860, 620, 'pull the end to free it', 'light', 24)
    return _frame(b, 'Fender · on the guardrail', ['Clove hitch round the wire, backed up by a slipped half hitch round the standing part', 'Pull the end and re-tie: the fender height changes in seconds'], 'ck-ground-7')

def sternline_svg():
    """Plan view: the stern line from the cleat through the fairlead over the deck edge to the quay, a chafe guard
    on it where it moves, at the fairlead and at the quay edge."""
    b = '<rect x="0" y="40" width="1280" height="200" fill="#bdb8ad" stroke="var(--ink)" stroke-width="4"/>'
    b += _t(150, 110, 'QUAY', 30, 700, 'var(--ink)')
    b += '<path d="M 200 640 L 1080 640 L 1080 380 L 200 380 Z" fill="#e7e3da" stroke="var(--ink)" stroke-width="5"/>'   # the transom corner of the deck
    b += '<circle cx="640" cy="160" r="30" fill="var(--ink)"/>'                                                        # quay ring / bollard
    b += '<rect x="560" y="365" width="70" height="30" rx="10" fill="#c9ced3" stroke="var(--ink)" stroke-width="4"/>'   # fairlead
    b += '<rect x="510" y="520" width="190" height="34" rx="12" fill="#c9ced3" stroke="var(--ink)" stroke-width="4"/>'  # cleat
    b += _path('M 520 537 C 520 500 600 500 600 537 C 600 570 680 570 680 537 L 595 455 L 595 380 L 640 190', '#8a6a3a', 11)
    for (x1, y1, x2, y2) in ((595, 430, 595, 360), (626, 260, 638, 205)):
        b += f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#2b2f33" stroke-width="22" stroke-linecap="round" opacity=".85"/>'
    b += _pill(330, 470, 'cleat', 'light', 26) + _pill(860, 360, 'fairlead', 'light', 26) + _pill(900, 260, 'chafe guard', 'accent', 26)
    b += _pill(330, 300, 'stern line', 'light', 26) + _pill(880, 160, 'quay edge', 'light', 24)
    return _frame(b, 'Stern line · guarded where it moves', ['A boat length at least: to the quay and back', 'A sleeve or a piece of hose at the fairlead and at the quay edge: chafe parts lines'], 'ck-ground-8')

if '--plans' in sys.argv:
    plans(); sys.exit(0)

# ===================================================================================================== Blender
import bpy, bmesh
from mathutils import Vector, Matrix, Euler, noise as mnoise
import common as C, kit as K, kit_world as KW, art_checkin_gear as G
from art_checkin_gear import V, deg

arg = C.cli(); FIG = arg('--fig', 1); SAMPLES = arg('--samples', 160); SCALE = arg('--scale', 100)
OUT = G.out_path('ground', FIG, arg('--out', ''))
labels, arrows, note, expo, extra = [], [], None, -0.6, {}

def T3(p): return (p[0], p[2], -p[1])          # Blender -> Three.js point

# ---------------------------------------------------------------------------------------------- 7  fender
if FIG == 7:
    R = 0.009
    def rope(g, i, P):
        if i != 1: return P
        fl, FX, wz, wy, ez, ey = g['fline'], g['FX'], g['wire_z'], g['wire_y'], g['edge_z'], g['edge_y']
        r = 0.0045 + R                                   # rope centre round the wire
        x0 = FX
        def ring(th, x): return V(x, wy + r * math.cos(deg(th)), wz + r * math.sin(deg(th)))
        side = g['side_y']; eye = fl[0]; prof = []
        for k in range(60):                              # the topsides at FX, from the fender eye up to the toe rail
            z = eye.z + 0.02 + k * 0.02; yy = side(FX + 0.004, z)
            if yy is None or yy < wy - 0.12: break
            prof.append(V(FX + 0.004, yy + 0.013, z))
        top = prof[-1] if prof else V(FX, wy, wz - 0.4)
        up = [eye] + prof[::4] + [V(FX + 0.005, top.y + 0.004, top.z + 0.03)]
        print('FENDER top', tuple(round(v, 3) for v in top), 'wire', round(wy, 3), round(wz, 3))
        approach = [V(FX + 0.006, wy + 0.03, wz - 0.07), ring(-50, x0)]
        hitch = []
        n = 72
        for k in range(1, n + 1):                        # two turns round the wire, walking along it, crossing
            th = -50 + 720 * k / n
            x = x0 - 0.026 * (k / n) * 2 + (0.0 if k < n / 2 else -0.004)
            hitch.append(ring(th, x))
        xe = hitch[-1].x
        # the end tucked under the crossing comes down outboard, beside the standing part: a slipped half hitch
        # round the standing part 9 cm below the wire, the end left as a bight you pull to free it
        sp = lambda z: V(FX + 0.006, wy + 0.03 - (wz - 0.07 - z) * 0.05, z)
        zc = wz - 0.24
        c = sp(zc)
        tail = [V(xe - 0.004, wy + 0.025, wz - 0.05), V(xe + 0.004, wy + 0.04, zc + 0.03)]
        for k in range(0, 13):                           # round the standing part
            a = deg(200 - 330 * k / 12)
            tail.append(c + V(0.026 * math.cos(a), 0.024 * math.sin(a) + 0.004, -0.006 * k / 12))
        tail += [c + V(-0.03, 0.035, -0.035), c + V(-0.05, 0.04, -0.075), c + V(-0.045, 0.045, -0.105), c + V(-0.022, 0.042, -0.095),
                 c + V(-0.012, 0.035, -0.05), c + V(0.004, 0.03, -0.02), c + V(0.03, 0.03, -0.06), c + V(0.045, 0.034, -0.16), c + V(0.05, 0.034, -0.25)]
        new = up + approach + hitch + tail
        g['__hitch'] = (hitch, tail, c); fl[:] = new
        return P
    def labs(g):
        hitch, tail, c = g['__hitch']
        wz, wy = g['wire_z'], g['wire_y']
        fl = g['fline']; lo = min(fl, key=lambda p: abs(p.z - 1.4))
        return [((g['FX'] - 0.75, wy, wz), 'guardrail'), (tuple(lo), 'fender line'),
                (tuple(hitch[len(hitch) // 2] + V(0, 0, 0.03)), 'clove hitch', 'blue'), (tuple(c + V(-0.03, 0.04, -0.1)), 'slipped half hitch', 'blue')]
    # closer than the library's view: from the pontoon, the hitch on the wire at eye height
    G.run_lib('fig_rail.py', [], OUT, SAMPLES, SCALE, labs, 'Fender: clove hitch, slipped half hitch', rope_fn=rope,
              cammat=(T3((1.72, 1.28, 1.62 - 0.95)), T3((1.1, 0.45, 1.76 - 0.95)), 40))
    sys.exit(0)

# ---------------------------------------------------------------------------------------------- 8  stern line
if FIG == 8:
    def pre(g):
        P = [C.B(*p) for p in g['d']['ropes'][0]['P']]
        R = g['d']['ropes'][0]['R']
        hose = C.simple('chafe-hose', '#2f3336', 0.45, coat=0.6)
        # the chafe guard: a length of split hose over the line where it bears on the fairlead
        seg = P[560:880]
        G.tube('chafe-guard', seg[::8] + [seg[-1]], R * 2.1, hose, 20, caps=True)
        g['__guard'] = seg
        mid = seg[len(seg) // 2]; best = None
        for o in bpy.data.objects:                       # the fairlead: the chrome part nearest the guard's middle
            if o.type != 'MESH' or not o.material_slots or not o.material_slots[0].material: continue
            if not o.material_slots[0].material.name.startswith('chrome'): continue
            lo, hi = K.bbox([o]); c = (lo + hi) / 2
            if best is None or (c - mid).length < (best - mid).length: best = c
        g['__fairlead'] = best
    def labs(g):
        seg = g['__guard']; P = [C.B(*p) for p in g['d']['ropes'][0]['P']]
        return [(tuple(seg[int(len(seg) * 0.12)]), 'stern line, to the quay'), (tuple(seg[int(len(seg) * 0.5)] + V(0, 0, 0.02)), 'chafe guard', 'blue'),
                (tuple(g['__fairlead'] + V(0, 0, 0.03)), 'fairlead'), (tuple(C.B(0.13, 0.11, -0.01)), 'cleat')]
    G.run_lib('render_scene.py', ['--name', 'cleat'], OUT, SAMPLES, SCALE, labs, 'Stern line: chafe guard where it moves', pre_render=pre,
              cammat=((0.62, 0.45, -0.72), (-0.15, -0.08, -0.33), 42))
    sys.exit(0)

C.reset()
# ---------------------------------------------------------------------------------------------- 3  the bottom
if FIG == 3:
    import numpy as np
    import q_scenes as Q
    DPATH = 'M0 0 H320 V30 H0 Z M0 30 H40 V200 H0 Z M280 30 H320 V200 H280 Z'
    land = Q.Land(DPATH, 1.0); cfg = dict(relief=32.0, beach=6.0, hill_len=260)
    P = lambda px, py: (px - 160.0, -(py - 100.0))
    A, B, Cc = P(110, 95), P(200, 130), P(160, 55)
    step = 2.5; x0, x1, y0, y1 = -320.0, 320.0, -300.0, 330.0
    nx, ny = int((x1 - x0) / step), int((y1 - y0) / step)
    gx, gy = np.meshgrid(x0 + np.arange(nx + 1) * step, y0 + np.arange(ny + 1) * step)
    X, Y = gx.ravel(), gy.ravel()
    Hl, D = Q.heights(land, X, Y, cfg)
    dd = np.maximum(0.0, -D)
    sea = -np.minimum(6.0, 0.3 * dd) - 2.0 * np.clip((dd - 20.0) / 90.0, 0, 1)
    rc = np.hypot(X - Cc[0], Y - Cc[1]); sea = np.where(rc < 26, np.maximum(sea, -5.0 - 1.0 * np.clip((rc - 14) / 12, 0, 1)), sea)
    Z = np.where(D >= 0, Hl, sea)
    verts = list(zip(X.tolist(), Y.tolist(), Z.tolist()))
    fl, fs = [], []
    for j in range(ny):
        for i in range(nx):
            q = (j * (nx + 1) + i, j * (nx + 1) + i + 1, (j + 1) * (nx + 1) + i + 1, (j + 1) * (nx + 1) + i)
            (fs if max(Z[k] for k in q) < -0.6 else fl).append(q)
    for name, faces in (('land', fl), ('seabed', fs)):
        me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update(); me.shade_smooth()
        o = C.obj(name, me, KW.land_mat() if name == 'land' else None)
        if name == 'seabed':
            # the bottom by its cover: pale sand, a dark seagrass meadow round A, grey rock round C
            m, nt, b, _ = C.new_mat('bottom')
            geo = C.node(nt, 'ShaderNodeNewGeometry'); pos = geo.outputs['Position']
            def blob(c, r, sc):
                d = C.node(nt, 'ShaderNodeVectorMath', operation='DISTANCE'); C.setin(d, 1, (c[0], c[1], 0.0))
                sep = C.node(nt, 'ShaderNodeSeparateXYZ'); C.link(nt, pos, sep.inputs[0])
                cmb = C.node(nt, 'ShaderNodeCombineXYZ'); C.link(nt, sep.outputs['X'], cmb.inputs['X']); C.link(nt, sep.outputs['Y'], cmb.inputs['Y'])
                C.link(nt, cmb.outputs[0], d.inputs[0])
                n = C.noise(nt, pos, sc, 4.0)
                dn = C.math_(nt, 'ADD', C.math_(nt, 'MULTIPLY_ADD', n, r * 0.9, d.outputs['Value']), -r * 0.45)
                mr = C.node(nt, 'ShaderNodeMapRange', in_From_Min=r * 1.05, in_From_Max=r * 0.85); C.link(nt, dn, mr.inputs['Value'])
                return mr.outputs['Result']
            sand = C.ramp(nt, [(0.35, '#cdbf98'), (0.6, '#e4d8b6'), (0.8, '#d8caa4')]); C.link(nt, C.noise(nt, pos, 0.05, 4.0), sand.inputs['Fac'])
            weedc = C.ramp(nt, [(0.35, '#16220f'), (0.55, '#2c3d1c'), (0.75, '#3c4a25')]); C.link(nt, C.noise(nt, pos, 0.35, 8.0), weedc.inputs['Fac'])
            rock = C.ramp(nt, [(0.3, '#4a4840'), (0.6, '#6f6a5e'), (0.8, '#585348')]); C.link(nt, C.noise(nt, pos, 0.5, 6.0), rock.inputs['Fac'])
            wk = blob(A, 34.0, 0.03); rk = blob(Cc, 20.0, 0.06)
            col = C.mixc(nt, wk, sand.outputs['Color'], weedc.outputs['Color']); col = C.mixc(nt, rk, col, rock.outputs['Color'])
            C.link(nt, col, b.inputs['Base Color']); C.setin(b, 'Roughness', 0.95)
            C.bump_from(nt, b, C.noise(nt, pos, 0.8, 8.0), 0.6, 0.15)
            me.materials.append(m)
    # boulders at C rising to 3 m below the surface
    rnd = random.Random(5); rm = C.simple('boulder', '#5b5850', 0.85)
    for k in range(70):
        a = rnd.uniform(0, math.tau); r = 17 * math.sqrt(rnd.random())
        sc = rnd.uniform(0.8, 2.6) * (1.0 if r < 9 else 0.6)
        bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
        for v in bm.verts: v.co *= 1 + 0.3 * mnoise.noise(v.co * 1.4 + Vector((k, 0, 0)))
        me = bpy.data.meshes.new('boulder'); bm.to_mesh(me); bm.free(); me.shade_smooth()
        top = -3.0 if r < 6 else -5.0 + rnd.uniform(0, 1.5)
        o = C.obj('boulder', me, rm, (Cc[0] + r * math.cos(a), Cc[1] + r * math.sin(a), top - sc * 0.55)); o.scale = (sc * 1.3, sc, sc * 0.75)
    KW.water_body(depth=16.0, size=760.0, density=0.004, color='#0d5c7a', absorb='#2a9ec0', reflect=0.3, absorb_density=0.18, center=(0, 0))
    KW.far_sea_ring(inner=380.0)
    Q.trees_on(land, cfg, None, n=900)
    for (x, y), l in ((A, 'A'), (B, 'B'), (Cc, 'C')): Q.spot_ring(x, y, 6.5, 'spot' + l).visible_shadow = False
    K.day_sky(sun_az=235, sun_el=42, strength=0.25, haze=2.0)
    tgt = (0.0, -2.0); e, az = deg(58), deg(180); Dd = 235.0
    KW.camera(Vector((tgt[0] + math.sin(az) * Dd * math.cos(e), tgt[1] + math.cos(az) * Dd * math.cos(e), Dd * math.sin(e))), Vector((tgt[0], tgt[1], 0.0)), 30)
    labels = [((A[0], A[1], 4.0), 'A', 'blue'), ((B[0], B[1], 4.0), 'B', 'blue'), ((Cc[0], Cc[1], 4.0), 'C', 'blue'),
              ((A[0], A[1] - 18, 0.5), 'dark weed'), ((B[0], B[1] - 18, 0.5), 'pale sand'), ((Cc[0] + 34, Cc[1], 0.5), 'rocks, 3 m')]
    wx, wy = 98.0, 30.0
    arrows = [((wx, wy + 32, 18.0), (wx, wy - 22, 18.0), 'red')]
    labels.append(((wx, wy + 34, 18.0), 'Wind N', 'red'))
    note = 'Depth 6–8 m across the bay'; expo = -0.6

# ---------------------------------------------------------------------------------------------- 4  scope
elif FIG == 4:
    DEPTH, CHAIN = 6.0, 30.0
    y = G.yacht(); y.place(0, 0, heading=0)
    KW.antifoul_hull(y)
    bow = y.world((10.95, 0.13, 3.72))
    sb = -DEPTH + 0.07
    H = bow.z - sb
    X = 11.0; a = 5.0
    for _ in range(80):
        f = a * (math.cosh(X / a) - 1) - H; df = (math.cosh(X / a) - 1) - (X / a) * math.sinh(X / a); a -= f / df
    hang_len = a * math.sinh(X / a); lie_len = CHAIN - hang_len
    hang = [Vector((0.0, bow.y + (X - x), sb + a * (math.cosh(x / a) - 1))) for x in (X * (1 - i / 160) for i in range(161))]
    touch = hang[-1]; anc_y = touch.y + lie_len - 0.6
    lie = [Vector((0.25 * math.sin(t * 9) * t, touch.y + (anc_y - touch.y) * t, sb)) for t in (i / 120 for i in range(1, 121))]
    root, objs = K.load_model('anchor-delta.glb', drop_planes=False)
    S = Matrix.Diagonal((1.7, 1.7, 1.7, 1.0))
    ang = 48 + (270 - math.degrees(math.atan2(-2.2, -2.6)) % 360)
    end = lie[-1]
    root.matrix_world = Matrix.Rotation(math.radians(ang), 4, 'Z') @ S @ Matrix.Translation((-0.48, -1.17, 0.0))
    bpy.context.view_layer.update()
    shackle = root.matrix_world @ Vector((0.48, 1.17, 0.52))
    root.matrix_world = Matrix.Translation((end.x - shackle.x, end.y - shackle.y + 0.05, 0)) @ root.matrix_world
    bpy.context.view_layer.update(); alo, ahi = K.bbox(objs)
    root.location.z += (-DEPTH - 0.25) - alo.z
    path = [bow + V(0, -0.6, 0.15), bow + V(0, -0.25, 0.08)] + hang + lie
    s0 = (path[1] - path[0]).length + (path[2] - path[1]).length
    # marks every 10 m from the anchor: 10 m red, 20 m yellow, 30 m (three marks) at the roller
    G.chain_marked(path, marks=(s0 + 0.1, s0 + 10.0, s0 + 20.0), link_len=0.2, wire=0.028, mark_len=1.5, colors=('#1f6fd6', '#f2c200', '#e8231a'))
    KW.water_body(depth=14.0, size=700.0, density=0.02, color='#0f4a4f', absorb='#2f8f86', reflect=0.25, absorb_density=0.035, center=(0, 15))
    KW.far_sea_ring(inner=350.0)
    KW.seabed(z=-DEPTH, size=170.0, res=260, center=(0, 18), colors=('#8d8f74', '#a9a888', '#9a9a7e'))
    KW.stones(50, ((-16, -12), (-3, 46)), -DEPTH, scale=(0.15, 0.6))
    KW.seagrass(((-22, -14), (-3, 50)), -DEPTH, clumps=900, length=0.55)
    KW.stones(60, ((7, -14), (26, 46)), -DEPTH, seed=8, scale=(0.15, 0.55))
    KW.seagrass(((7, -16), (26, 52)), -DEPTH, clumps=900, seed=9, length=0.5)
    K.coast(distance=1500, bearing=270, height=90, town=False)
    K.day_sky(sun_az=120, sun_el=55, strength=0.25, haze=2.0)
    mid_y = (-10.5 + anc_y + 2.5) / 2
    KW.camera(Vector((32.0, mid_y, 0.002)), Vector((0.0, mid_y, -1.7)), lens=22)
    m10 = path[0]
    def at(s):
        acc = 0.0
        for p, q in zip(path, path[1:]):
            L = (q - p).length
            if acc + L >= s: return p.lerp(q, (s - acc) / L)
            acc += L
        return path[-1]
    gy = -9.6; gx = 2.0
    labels = [((bow.x, bow.y + 0.3, bow.z + 0.5), 'roller 1 m above water'),
              (tuple(at(s0 + 10.0) + V(0, 0, 0.3)), '20 m mark', 'yellow'), (tuple(at(s0 + 20.0) + V(0, 0, 0.3)), '10 m mark', 'red'),
              ((gx, gy - 2.6, -DEPTH / 2 - 0.2), 'depth 6 m', 'blue'), ((0.0, anc_y + 0.6, -DEPTH + 0.6), 'anchor')]
    arrows = [((gx, gy, -2.8), (gx, gy, -0.05), 'blue'), ((gx, gy, -2.8), (gx, gy, -DEPTH + 0.05), 'blue')]
    note = '(6 m + 1 m) × 4–5 ≈ 30 m'; extra = {'lines': ['All chain, marks every 10 m', 'Three marks out: the third at the roller']}; expo = -0.55

# ---------------------------------------------------------------------------------------------- 6  stern-to
elif FIG == 6:
    import q_scenes as Q
    concrete = C.concrete_mat('quay-concrete')
    C.obj('quay', C.rbox('quay', (180, 30, 3.0), 0.15, 2), concrete, (0, 15, -0.3))
    C.obj('quay-edge', C.rbox('quay-edge', (180, 0.5, 0.25), 0.05, 2), C.simple('quay-cap', '#cfcac0', 0.8), (0, 0.25, 1.32))
    wm, rm = KW.plaster_mat(), KW.roof_mat(); random.seed(7); x = -90
    while x < 90:
        w = random.uniform(7, 11); hgt = random.uniform(7, 13)
        o = bpy.data.objects.new('house', KW.house_mesh(w, 10, hgt, 2.4, wm, rm, f'h{x:.0f}')); C.col.objects.link(o)
        o.location = (x + w / 2, 36, 1.2); x += w + random.uniform(0.0, 1.2)
    SRC = {'white': Q.yacht_source('white', 'src-white'), 'navy': Q.yacht_source('navy', 'src-navy')}
    line_m = C.simple('mooring-line', '#e7e2d4', 0.7); bol = C.simple('bollard', '#2a2b2d', 0.5, 0.3)
    XS = (-32, -27, -22, -17, -12, -7, 7, 12, 17, 22, 27, 32)
    for xc in XS:
        Q.YachtInstance(SRC['navy' if xc in (-17, 22) else 'white'], f'moored{xc}').place(xc, -1.6 - 8.7, heading=180)
        for side in (-1, 1):
            bp = Vector((xc + side * 1.4, 0.7, 1.2)); C.cyl('bollard', 0.12, 0.12, 0.35, 16, bol, bp + Vector((0, 0, 0.17)))
            s = Vector((xc + side * 1.6, -1.9, 1.75))
            C.tube('stern-line', [s.lerp(bp + Vector((0, 0, 0.3)), t / 8) + Vector((0, 0, -0.25 * math.sin(math.pi * t / 8))) for t in range(9)], 0.012, 8, 1.0, line_m)
    you = Q.YachtInstance(SRC['white'], 'you').place(0, -50 + 5.9, heading=180)
    K.sea('calm', size=30.0, res=10, repeat=14, center=(0, -55))
    K.day_sky(sun_az=215, sun_el=45, strength=0.25, haze=2.0)
    for yy, l in ((-15, 'A'), (-50, 'B'), (-100, 'C')): Q.spot_ring(0, yy, 3.2, 'spot' + l)
    KW.camera(Vector((20, -158, 78)), Vector((0, -46, 0)), lens=28)
    labels = [((0, -15, 1.5), 'A · 15 m', 'blue'), ((0, -51, 1.0), 'B · 50 m: square to the gap', 'blue'), ((0, -100, 1.5), 'C · 100 m', 'blue'),
              ((-17, 4, 4.0), 'town quay · gap between two boats')]
    arrows = [((5.0, -31, 0.4), (5.0, -10, 0.4), 'yellow'), ((48, -78, 5), (26, -78, 5), 'red')]
    labels.append(((48, -78, 5.5), 'Wind E', 'red'))
    note = 'Boat 14 m · depth 5 m'; expo = -0.6


# ---------------------------------------------------------------------------------------------- 1, 5  the bow
def DZ(x, yy): return G.deck_z(x, yy, top=1.8)

def bow_gear(y, open_locker=False):
    """Clear the model's own low-detail bow gear and build ours: a stemhead roller with its pin, the Delta anchor
    stowed on it, a swivel, a vertical windlass with its gypsy; returns the key points (world)."""
    bpy.context.view_layer.update()
    mo = Vector((K.MAST.x, K.MAST.y, K.WL))
    for o in y.objs:
        if o.type != 'MESH' or o.hide_render: continue
        lo, hi = K.bbox([o]); lo, hi = lo + mo, hi + mo          # model space (heading 90 at the origin)
        lid = hi.x < 10.25 and (hi.y - lo.y) > 0.5
        if lo.x > 9.5 and hi.x < 11.5 and lo.y > -0.4 and hi.y < 0.62 and lo.z > 3.2 and hi.z < 3.8 and (open_locker or not lid):
            o.hide_render = True; o.hide_viewport = True
    bpy.context.view_layer.update()
    W = lambda x, yy, z: y.world((x, yy, z))
    st, dk = G.steel(), G.dull_steel()
    dz = DZ(5.8, 0.0); dzw = DZ(5.48, 0.0)
    print('DECK z', round(dz, 3), round(dzw, 3))
    # the roller fitting: two cheek plates on a base plate, running out over the stem
    for sy in (-0.058, 0.058):
        G.box('cheek', (0.62, 0.01, 0.11), (5.97, sy, dz + 0.05), st, 0.003)
    G.box('roller-base', (0.42, 0.13, 0.012), (5.84, 0, dz + 0.004), st, 0.003)
    rol = G.cyl_between('roller', (6.19, -0.052, dz + 0.055), (6.19, 0.052, dz + 0.055), 0.05, C.simple('roller-nylon', '#1d1f22', 0.45), 32)
    G.cyl_between('roller-axle', (6.19, -0.07, dz + 0.055), (6.19, 0.07, dz + 0.055), 0.012, st, 16)
    # the roller pin: across the cheeks above the shank, a ring at its head and a lanyard to the fitting
    pin = (6.04, 0, dz + 0.145)
    G.cyl_between('roller-pin', (6.04, -0.08, dz + 0.145), (6.04, 0.075, dz + 0.145), 0.009, st, 16)
    G.torus('pin-ring', 0.022, 0.0035, st, (6.04, -0.084, dz + 0.145), rot=(deg(90), 0, 0))
    G.tube('pin-lanyard', [(6.04, -0.09, dz + 0.125), (6.0, -0.1, dz + 0.07), (5.93, -0.075, dz + 0.04)], 0.0025, C.simple('lanyard', '#c8161d', 0.6), 8)
    # the anchor: a Delta, its shank lying along the cheeks, the blade hanging under the roller
    root, objs = K.load_model('anchor-delta.glb', drop_planes=False)
    K.recolor(objs, lambda c, n: C.galv_mat('anchor-galv'))
    eye_l = Vector((0.48, 1.17, 0.52))
    root.matrix_world = (Matrix.Translation((5.72, 0, dz + 0.14)) @ Matrix.Rotation(deg(17), 4, 'Y')
                         @ Matrix.Diagonal((0.9, 0.9, 0.9, 1.0)) @ Matrix.Translation(-eye_l))
    bpy.context.view_layer.update()
    eye = root.matrix_world @ eye_l
    # the swivel between the anchor's shank and the chain
    sv0, sv1 = eye + V(-0.03, 0, -0.005), eye + V(-0.17, 0, -0.03)
    G.cyl_between('swivel-body', sv0.lerp(sv1, 0.3), sv0.lerp(sv1, 0.75), 0.019, st, 24)
    G.torus('swivel-jaw', 0.03, 0.007, st, sv0.lerp(sv1, 0.12), rot=(deg(90), 0, 0))
    G.torus('swivel-eye', 0.026, 0.007, st, sv1, rot=(0, deg(90), 0))
    # the windlass: a vertical one, its base on the deck, gypsy, warping drum and clutch nut on top
    wx = 5.42; wb = V(wx, 0.0, dzw)
    G.cyl_between('wl-base', wb, wb + V(0, 0, 0.05), 0.135, st, 48)
    gyp = G.cyl_between('wl-gypsy', wb + V(0, 0, 0.05), wb + V(0, 0, 0.12), 0.09, dk, 12)
    G.cyl_between('wl-drum', wb + V(0, 0, 0.12), wb + V(0, 0, 0.23), 0.072, st, 48, r2=0.06)
    G.cyl_between('wl-cap', wb + V(0, 0, 0.23), wb + V(0, 0, 0.26), 0.035, st, 6)
    # the deck pipe the chain drops through, just aft of the windlass
    pz = DZ(wx + 0.05, 0.17)
    hole = C.cyl('chain-pipe', 0.045, 0.045, 0.012, 32, C.simple('pipe-black', '#050506', 0.9), (wx + 0.05, 0.17, pz + 0.004))
    C.cyl('chain-pipe-rim', 0.06, 0.06, 0.008, 32, st, (wx + 0.05, 0.17, pz + 0.002))
    # bow cleats, one each side
    cleats = []
    for sy in (-1, 1):
        cx, cy = 4.05, sy * 0.66
        cz = DZ(cx, cy)
        G.cyl_between('cleat-horn', (cx - 0.13, cy, cz + 0.06), (cx + 0.13, cy, cz + 0.06), 0.016, st, 20)
        for dx in (-0.05, 0.05): G.cyl_between('cleat-leg', (cx + dx, cy, cz), (cx + dx, cy, cz + 0.06), 0.02, st, 16, r2=0.016)
        cleats.append(V(cx, cy, cz + 0.06))
    return dict(dz=dz, dzw=dzw, roller=V(6.19, 0, dz + 0.055), pin=V(*pin), eye=eye, swivel=sv1, wl=wb, gypsy=wb + V(0, 0, 0.085),
                hole=V(wx + 0.05, 0.17, pz), cleats=cleats, anchor=objs)

if FIG in (1, 5):
    y = G.yacht(name='yacht'); y.place(0, 0, heading=90)
    KW.antifoul_hull(y)
    g = bow_gear(y, open_locker=(FIG == 1))
    dz, dzw = g['dz'], g['dzw']
    K.sea('calm', size=30, repeat=8)
    K.coast(distance=900, bearing=20, height=70, town=True)
if FIG == 1:
    # chain: swivel aft along the cheeks, round the gypsy, down the deck pipe
    gy = g['gypsy']
    ch = [g['swivel'] + V(-0.02, 0, -0.005), V(5.57, 0, dz + 0.06)]
    ch += [gy + V(0.09 * math.cos(a), 0.09 * math.sin(a), 0) for a in (deg(k) for k in range(-40, 100, 20))]
    ch += [g['hole'] + V(0.01, 0, 0.06), g['hole'] + V(0, 0, -0.3)]
    KW.chain(ch, link_len=0.05, wire=0.0065)
    # the anchor locker, open: a well cut into the foredeck, the lid stood up to port
    lx0, lx1, ly = 4.70, 5.27, 0.36                 # the model's locker opening, its lid hidden
    ldz = DZ(4.6, 0.0)
    well = C.simple('locker-gel', '#d9dad4', 0.5)
    D = 0.42
    # (walls fill the opening; the lid stands up on its port hinge)
    for (cx, cy, sx, sy) in ((lx0, 0, 0.01, 2 * ly), (lx1, 0, 0.01, 2 * ly), ((lx0 + lx1) / 2, -ly, lx1 - lx0, 0.01), ((lx0 + lx1) / 2, ly, lx1 - lx0, 0.01)):
        G.box('locker-wall', (sx, sy, D), (cx, cy, ldz - D / 2), well)
    G.box('locker-floor', (lx1 - lx0, 2 * ly, 0.01), ((lx0 + lx1) / 2, 0, ldz - D), well)
    lid = None and G.box('locker-lid', (lx1 - lx0, 0.02, 2 * ly), ((lx0 + lx1) / 2, ly + 0.02, ldz + ly), K.mats()['nonskid'], 0.01)
    # the chain in the locker: a pile, a painted mark on top (red and yellow links: 20 m on the form's code)
    rnd = random.Random(4); fl = ldz - D + 0.02
    pile = []
    cx0, cy0 = (lx0 + lx1) / 2 - 0.02, -0.04
    for k in range(70):
        a = k * 0.9; r = 0.04 + 0.11 * (k % 9) / 9
        pile.append(V(cx0 + r * math.cos(a), cy0 + r * math.sin(a) * 1.2, fl + 0.015 * (k / 9)))
    KW.chain(pile, link_len=0.05, wire=0.0065)
    mk = [V(cx0 - 0.12, cy0 + 0.1, fl + 0.09), V(cx0 - 0.02, cy0 + 0.12, fl + 0.1), V(cx0 + 0.08, cy0 + 0.06, fl + 0.1), V(cx0 + 0.13, cy0 - 0.04, fl + 0.1)]
    G.chain_marked(mk, marks=(0.07, 0.2), link_len=0.05, wire=0.0065, mark_len=0.1, colors=('#e8231a', '#f2c200'))
    # the bitter end: the last link lashed with turns of light line to a U-bolt on the locker's forward wall
    ub = V(lx1 - 0.012, -0.12, ldz - 0.12)
    G.tube('u-bolt', [ub + V(0, -0.03, -0.02), ub + V(-0.03, -0.03, 0), ub + V(-0.04, 0, 0.01), ub + V(-0.03, 0.03, 0), ub + V(0, 0.03, -0.02)], 0.006, G.steel(), 10)
    last = V(lx1 - 0.13, -0.12, ldz - 0.17)
    KW.chain([V(cx0 + 0.1, cy0 - 0.12, fl + 0.02), last + V(-0.05, 0, -0.08), last], link_len=0.05, wire=0.0065)
    lash = []
    for k in range(5):
        lash += [last + V(0.0, 0.004 * k - 0.008, 0.012), ub + V(-0.04, 0.004 * k - 0.008, 0.008), ub + V(-0.03, 0.004 * k - 0.008, -0.014), last + V(0.008, 0.004 * k - 0.008, -0.012)]
    G.tube('lashing', lash, 0.0028, C.simple('lashing-line', '#efe9da', 0.7), 8)
    G.tube('lashing-tail', [last + V(0.008, 0.02, -0.012), last + V(-0.02, 0.05, -0.05), last + V(-0.06, 0.07, -0.09)], 0.0028, C.simple('lashing-line', '#efe9da', 0.7), 8)
    K.day_sky(sun_az=110, sun_el=68, strength=0.25, haze=2.0)
    cam = KW.camera(V(4.3, -0.62, dz + 0.98), V(5.42, 0.03, dz - 0.16), 27)
    if arg('--probe', 0): cam = KW.camera(V(5.9, -1.6, dz + 0.3), V(5.9, 0.0, dz - 0.1), 30)
    C.focus_on_centre(cam, 14.0)
    labels = [(tuple(g['pin'] + V(0, 0, 0.03)), 'roller pin'), (tuple(g['swivel'] + V(0.05, 0, 0.04)), 'swivel'),
              (tuple(mk[1] + V(0, 0, 0.02)), 'chain marks: code on the form', 'blue'), (tuple(last + V(0.02, 0, 0.03)), 'bitter end: rope lashing', 'blue'),
              (tuple(g['wl'] + V(-0.06, -0.08, 0.2)), 'windlass')]
    note = 'At the bow'; expo = -0.6
elif FIG == 5:
    rl = g['roller']; gy = g['gypsy']
    for o in g['anchor']: o.hide_render = True                 # the anchor is down: only the chain on the roller
    for o in bpy.data.objects:
        if o.name.startswith('swivel'): o.hide_render = True
    # the chain, slack: from the deck pipe up round the gypsy, a slack bight on the deck, over the roller, down
    # in a hanging loop behind the hook; the hook on the chain takes the snubber, the chain beyond leads to the anchor
    Hk = V(7.05, 0.0, 0.42)
    ch = [g['hole'] + V(0, 0, -0.3), g['hole'] + V(0.01, 0, 0.06)]
    ch += [gy + V(0.09 * math.cos(a), 0.09 * math.sin(a), 0) for a in (deg(k) for k in range(100, -60, -20))]
    ch += [gy + V(0.16, -0.06, -0.06), V(5.72, -0.02, dz + 0.02), V(5.86, 0, dz + 0.05), rl + V(-0.05, 0, 0.05), rl + V(0.04, 0, 0.055), rl + V(0.07, 0, 0.0)]
    ch += [rl.lerp(Hk, t) + V(0.12 * math.sin(math.pi * t), 0, -0.55 * math.sin(math.pi * t) - 0.05 * t) for t in (0.15, 0.3, 0.45, 0.6, 0.75, 0.9)] + [Hk]
    ch += [Hk + V(0.6 * t, 0, -1.6 * t) for t in (0.25, 0.5, 0.75, 1.0)] + [Hk + V(1.4, 0, -3.5)]
    KW.chain(ch, link_len=0.05, wire=0.0065)
    # the chain hook and the snubber: a nylon three-strand from the starboard bow cleat, out through a fairlead
    st = G.steel()
    G.tube('hook', [Hk + V(-0.02, 0, 0.09), Hk + V(-0.01, 0, 0.03), Hk + V(0.02, 0, -0.01), Hk + V(0.045, 0, 0.01), Hk + V(0.04, 0, 0.04)], 0.012, st, 12)
    cl = g['cleats'][0]
    fair = V(5.62, -0.36, DZ(5.62, -0.36) + 0.03)
    G.box('fairlead', (0.12, 0.04, 0.05), fair + V(0, 0, -0.005), st, 0.008)
    turns = [cl + V(0.1 * math.cos(a), 0.035 * math.sin(a) - 0.0, 0.012 + 0.006 * k) for k, a in enumerate(deg(t) for t in range(0, 720, 45))]
    snub = turns + [cl + V(0.25, 0.05, 0.0), fair + V(-0.25, 0.04, -0.005), fair, fair + V(0.12, -0.05, -0.04)]
    snub += [fair.lerp(Hk + V(-0.02, 0, 0.1), t) for t in (0.35, 0.7)] + [Hk + V(-0.02, 0, 0.11)]
    G.line3('snubber', snub, R=0.009, lay=0.06)
    K.day_sky(sun_az=210, sun_el=40, strength=0.25, haze=2.0)
    cam = KW.camera(V(4.75, -1.25, dz + 1.7), V(6.45, 0.0, 0.75), 32)
    C.focus_on_centre(cam, 14.0)
    labels = [(tuple(Hk + V(0, -0.05, 0.12)), 'snubber hooked on', 'blue'), (tuple(cl.lerp(fair, 0.8) + V(0, 0, 0.03)), 'snubber: load on a cleat'),
              (tuple(g['wl'] + V(0.1, 0, 0.13)), 'chain slack on the gypsy')]
    note = 'For the night'; expo = -0.6


# ---------------------------------------------------------------------------------------------- 2  the panel
if FIG == 2:
    import kit_instruments as KI
    jm = KI.joinery_mat()
    KI.wall('bulkhead', -0.6, 0.6, -0.45, 0.45, 0.012, jm)
    G.box('panel', (0.3, 0.012, 0.44), (0.0, 0.006, 0.0), C.simple('panel-anod', '#202326', 0.42, 0.5), 0.004)
    for sx in (-0.13, 0.13):
        for sz in (-0.2, 0.2): G.cyl_between('screw', (sx, -0.001, sz), (sx, -0.004, sz), 0.004, G.steel(), 12)
    white = C.simple('print-white', '#f2f2ee', 0.5); red = C.simple('print-red', '#e8231a', 0.45)
    # the voltmeter: a small LCD at the top
    G.box('lcd-bezel', (0.11, 0.008, 0.05), (0.0, -0.002, 0.168), C.simple('bezel', '#0b0c0d', 0.3), 0.004)
    G.box('lcd', (0.092, 0.002, 0.036), (0.0, -0.0065, 0.168), C.simple('lcd-glass', '#0d1a12', 0.08, coat=1.0))
    G.text('12.6 V', (0.0, -0.0085, 0.167), 0.026, G.emit_mat('lcd-digits', '#ffb23a', 4.0), name='lcd-text')
    G.text('VOLTS', (0.0, -0.0005, 0.132), 0.011, white, name='lbl')
    # breakers: a row each, the circuit printed on the left, a toggle on the right with its LED
    names = ['NAV LIGHTS', 'ANCHOR LIGHT', 'CABIN LIGHTS', 'FRIDGE', 'WATER PUMP', 'INSTRUMENTS', 'VHF']
    on = {'CABIN LIGHTS', 'FRIDGE', 'INSTRUMENTS', 'VHF'}
    tog = C.simple('toggle-black', '#0e0f10', 0.35); st = G.steel()
    def toggle(x, z, up, big=False):
        r = 0.011 if big else 0.008
        G.cyl_between('bush', (x, 0, z), (x, -0.012, z), r, st, 20)
        a = deg(30 if up else -30); L = 0.032 if big else 0.024
        tip = Vector((x, -0.012 - L * math.cos(a), z + L * math.sin(a)))
        G.cyl_between('lever', (x, -0.012, z), tip, r * 0.45, tog if not big else red, 12, r2=r * 0.55)
        return tip
    for i, n in enumerate(names):
        z = 0.095 - i * 0.035
        G.text(n, (-0.12, -0.0005, z), 0.0125, white, align='LEFT', name='lbl')
        toggle(0.08, z, n in on)
        led = G.sphere('led', 0.003, G.emit_mat('led-on', '#2bff5a', 6.0) if n in on else C.simple('led-off', '#1b3b22', 0.2), (0.115, -0.002, z))
    # the windlass breaker: its own heavy breaker at the foot of the panel, the red lever down: OFF
    zw = -0.175
    G.box('wl-breaker', (0.075, 0.03, 0.05), (0.06, -0.015, zw), C.simple('breaker-body', '#111214', 0.45), 0.005)
    wtip = toggle(0.06, zw, False, big=True)
    G.text('WINDLASS', (-0.12, -0.0005, zw + 0.008), 0.016, red, align='LEFT', name='lbl')
    G.text('80 A', (-0.12, -0.0005, zw - 0.016), 0.011, white, align='LEFT', name='lbl')
    G.text('ON ↑   OFF ↓', (0.06, -0.0005, zw - 0.042), 0.009, white, name='lbl')
    # the chart table below, a lamp to read by
    G.box('chart-table', (1.2, 0.5, 0.03), (0.0, -0.25, -0.33), jm, 0.01)
    KI.area_light((-0.35, -0.7, 0.45), (0.0, 0.0, 0.0), 25.0, 0.6)
    KI.area_light((0.4, -0.6, -0.1), (0.0, 0.0, 0.0), 8.0, 0.4, (0.9, 0.95, 1.0))
    K.day_sky(sun_az=200, sun_el=35, strength=0.12)
    cam = KW.camera(V(0.05, -0.95, 0.0), V(0.0, 0.0, 0.0), 40); C.focus_on_centre(cam, 8.0)
    labels = [((0.0, -0.01, 0.198), 'Volts 12.6'), (tuple(wtip + V(0, 0, 0.012)), 'Windlass breaker: OFF', 'red')]
    note = 'Foot switch: nothing'; extra = {'lines': ['Engine stopped', 'Breaker on, engine running, try again']}; expo = -0.3

# ---------------------------------------------------------------------------------------------- 9  outboard
if FIG == 9:
    # the dinghy: a small RIB built here, grey hypalon tubes round a GRP hull, the transom at x = 0
    hyp = C.simple('hypalon', '#9fa4a6', 0.62); grp = C.simple('rib-grp', '#e4e4de', 0.4, coat=0.4)
    tub = []
    for k in range(13): tub.append((0.05 + 2.05 * k / 12, 0.56, 0.12))
    for k in range(1, 18):
        a = deg(90 - 180 * k / 18); tub.append((2.1 + 0.56 * math.cos(a) * 0.9, 0.56 * math.sin(a), 0.12 + 0.06 * math.cos(a)))
    for k in range(13): tub.append((2.1 - 2.05 * k / 12, -0.56, 0.12))
    G.tube('tubes', tub, 0.2, hyp, 28)
    for sy in (-0.56, 0.56):
        G.cyl_between('tube-cone', (0.05, sy, 0.12), (-0.28, sy, 0.12), 0.2, hyp, 28, r2=0.08)
        G.tube('rubbing-strake', [(t[0], sy * 1.36, 0.07) for t in tub if abs(t[1] - sy) < 1e-6], 0.02, C.simple('strake', '#3a3e42', 0.5), 10)
    G.box('floor', (2.1, 0.92, 0.03), (1.05, 0, 0.02), grp, 0.01)
    G.box('hull', (2.2, 1.0, 0.22), (1.1, 0, -0.1), grp, 0.06)
    G.box('transom', (0.05, 0.95, 0.45), (0.0, 0, 0.09), grp, 0.01)
    G.box('seat', (0.26, 1.0, 0.03), (1.15, 0, 0.27), C.simple('seat', '#d8d6cf', 0.5), 0.01)
    G.text('IRIS · SB 49', (1.2, -0.765, 0.15), 0.07, C.simple('tube-print', '#1d2c4f', 0.5), rot=(deg(90), 0, 0), name='tube-name')
    st, dk = G.steel(), C.simple('outboard-dark', '#25282b', 0.45)
    cowl = C.simple('cowling', '#d5d7d8', 0.32, coat=0.6)
    TZ = 0.31                                                    # top of the transom
    G.box('clamp-bracket', (0.13, 0.17, 0.11), (0.0, 0, TZ + 0.03), dk, 0.012)
    # clamp screws on the inboard face, their T-handles, the lock bar through both, a padlock on it
    for sy in (-0.06, 0.06):
        G.cyl_between('clamp-screw', (0.06, sy, TZ - 0.07), (0.13, sy, TZ - 0.07), 0.009, st, 16)
        G.cyl_between('t-handle', (0.13, sy - 0.045, TZ - 0.07), (0.13, sy + 0.045, TZ - 0.07), 0.008, dk, 12)
        G.box('clamp-pad', (0.02, 0.05, 0.05), (0.055, sy, TZ - 0.07), dk, 0.006)
    G.box('lock-bar', (0.012, 0.2, 0.025), (0.142, 0, TZ - 0.07), st, 0.003)
    G.box('padlock', (0.02, 0.045, 0.05), (0.15, 0.0, TZ - 0.115), C.simple('brass', '#b8902e', 0.3, 1.0), 0.006)
    G.torus('padlock-shackle', 0.014, 0.004, st, (0.15, 0, TZ - 0.085), rot=(0, deg(90), 0))
    # the motor: leg, lower unit and propeller, the cowled powerhead, tiller and grip
    G.box('leg', (0.09, 0.07, 0.78), (-0.13, 0, TZ - 0.32), dk, 0.02)
    G.box('cav-plate', (0.22, 0.17, 0.012), (-0.17, 0, -0.3), dk, 0.006)
    G.cyl_between('torpedo', (-0.03, 0, -0.43), (-0.3, 0, -0.43), 0.042, dk, 20, r2=0.03)
    for k in range(3):
        bl = G.box('prop-blade', (0.01, 0.06, 0.1), (-0.32, 0, -0.43), dk, 0.004); bl.rotation_euler = (deg(120 * k), 0, deg(15))
        bl.location = (-0.32, 0.05 * math.sin(deg(120 * k + 90)), -0.43 + 0.05 * math.cos(deg(120 * k + 90)))
    G.box('pan', (0.36, 0.24, 0.1), (-0.15, 0, TZ + 0.13), dk, 0.03)
    G.box('cowling', (0.38, 0.26, 0.24), (-0.15, 0, TZ + 0.3), cowl, 0.07)
    G.box('cowl-stripe', (0.385, 0.265, 0.025), (-0.15, 0, TZ + 0.24), C.simple('stripe', '#c8161d', 0.4), 0.012)
    G.tube('carry-handle', [(-0.33, -0.05, TZ + 0.36), (-0.37, -0.05, TZ + 0.4), (-0.37, 0.05, TZ + 0.4), (-0.33, 0.05, TZ + 0.36)], 0.011, dk, 10)
    G.cyl_between('tiller', (0.03, 0, TZ + 0.17), (0.5, 0, TZ + 0.22), 0.019, dk, 16)
    G.cyl_between('grip', (0.38, 0, TZ + 0.21), (0.55, 0, TZ + 0.23), 0.025, C.simple('grip', '#151617', 0.8), 20)
    # the gear lever on the starboard side, upright: neutral
    G.cyl_between('gear-lever', (-0.05, 0.135, TZ + 0.16), (-0.03, 0.165, TZ + 0.26), 0.008, dk, 10)
    G.sphere('gear-knob', 0.016, C.simple('knob', '#151617', 0.5), (-0.03, 0.165, TZ + 0.27))
    # the stop switch at the front, its red kill cord coiled, the clip, the wrist strap on the seat
    sw = V(0.06, -0.085, TZ + 0.2)
    G.box('stop-switch', (0.03, 0.03, 0.03), sw, C.simple('switch-red', '#c8161d', 0.4), 0.006)
    coil = [sw + V(0.02 + 0.012 * k / 6.0 * 6, -0.02 - 0.02 * math.sin(k * 0.9), -0.02 * math.cos(k * 0.9) - 0.012 * k) for k in range(18)]
    coil += [V(0.3, -0.32, 0.2), V(0.48, -0.5, 0.33)]
    G.tube('kill-cord', coil, 0.004, C.simple('kill-cord', '#e01b1b', 0.45), 8)
    G.torus('wrist-strap', 0.045, 0.008, C.simple('strap', '#e01b1b', 0.6), (0.53, -0.53, 0.33), rot=(deg(10), 0, 0))
    # the fuel tank on the floor: red, vent screw on its cap opened; the hose with the primer bulb to the motor
    loc, _ = G.ray((0.95, 0.2, 1.0), (0, 0, -1)); floor = loc.z if loc else 0.04
    tank_c = V(0.95, 0.2, floor + 0.11)
    G.box('tank', (0.36, 0.24, 0.22), tank_c, C.simple('tank-red', '#c4161c', 0.45, coat=0.3), 0.04)
    G.cyl_between('tank-cap', tank_c + V(-0.08, 0.04, 0.11), tank_c + V(-0.08, 0.04, 0.14), 0.035, C.simple('cap-black', '#121314', 0.5), 24)
    vent = tank_c + V(-0.08, 0.04, 0.14)
    G.cyl_between('vent-screw', vent, vent + V(0, 0, 0.025), 0.009, C.simple('vent', '#3a3d40', 0.5), 12)
    G.cyl_between('tank-handle', tank_c + V(0.06, -0.08, 0.12), tank_c + V(0.06, 0.08, 0.12), 0.01, C.simple('cap-black', '#121314', 0.5), 12)
    hose_a = tank_c + V(-0.18, -0.02, 0.06)
    bulb_c = V(0.38, 0.06, floor + 0.04)
    hose = [hose_a, hose_a + V(-0.04, -0.01, -0.07), V(0.58, 0.1, floor + 0.012), bulb_c + V(0.06, 0.005, -0.01)]
    G.tube('hose-1', hose, 0.008, C.simple('hose', '#101112', 0.6), 10)
    bulb = G.sphere('primer-bulb', 0.03, C.simple('bulb', '#121314', 0.55), bulb_c); bulb.scale = (1.9, 1.0, 1.0); bulb.rotation_euler = (0, 0, deg(-10))
    G.tube('hose-2', [bulb_c + V(-0.06, -0.005, -0.01), V(0.2, 0.05, floor + 0.012), V(0.09, 0.06, floor + 0.03), V(0.07, 0.06, TZ - 0.05), V(0.035, 0.06, TZ + 0.08)], 0.008, C.simple('hose', '#101112', 0.6), 10)
    # the lanyard: tied to the carry handle, led up to whoever passes the motor between boats
    G.braid3('lanyard', [(-0.37, 0.0, TZ + 0.41), (-0.36, 0.06, TZ + 0.5), (-0.2, 0.3, TZ + 0.85), (0.1, 0.7, 1.5), (0.4, 1.0, 2.2)], 0.006, '#1b2c4c', '#e9e3d2', whip='#141414')
    # the pontoon, the dinghy lying alongside it to port
    M = K.mats(); edge = 0.8; TOP = 0.48
    C.obj('float', C.rbox('float', (8.0, 2.4, 0.7), 0.06, 2), M['float'], (1.0, edge + 1.2, TOP - 0.42))
    plank = C.rbox('plank', (0.14, 2.4, 0.035), 0.004, 1); plank.materials.append(M['planks'])
    xx = -3.0
    while xx < 5.0:
        o = bpy.data.objects.new('plank', plank); C.col.objects.link(o); o.location = (xx, edge + 1.2, TOP); xx += 0.155
    C.obj('rub', C.rbox('rub', (8.0, 0.1, 0.08), 0.02, 2), M['rubber'], (1.0, edge + 0.03, TOP - 0.1))
    K.sea('calm', size=20.0, repeat=6)
    K.coast(distance=600, bearing=200, height=60, town=True)
    K.day_sky(sun_az=150, sun_el=50, strength=0.25, haze=2.0)
    cam = KW.camera(V(1.45, 1.15, 1.3), V(0.22, -0.02, 0.37), 34); C.focus_on_centre(cam, 11.0)
    labels = [(tuple(vent + V(0, 0, 0.03)), 'tank vent open'), (tuple(bulb_c + V(0, 0, 0.035)), 'bulb squeezed firm'),
              ((0.53, -0.53, 0.36), 'kill cord', 'red'), ((0.15, 0.0, TZ - 0.04), 'clamps tight, lock bar on'),
              ((-0.03, 0.165, TZ + 0.29), 'start in neutral'), ((-0.37, 0.02, TZ + 0.44), 'lanyard on the handle', 'blue')]
    note = 'Outboard, at the pontoon'; expo = -0.6

# ======================================================================================================= render
C.render(OUT, SAMPLES, SCALE, expo, labels, note, space='blender', arrows=arrows, extra=extra)
