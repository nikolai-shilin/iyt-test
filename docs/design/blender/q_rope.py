# Bareboat Skipper test images, figure type "rope" (knots, cleats, winches, lines): one Cycles render per question.
# Reads docs/design/figure-style/questions/bareboat-skipper/rope.json and writes <id>/3d.jpg, 3d.labels.json, ru.json.
# Most scenes are the rope library's own (rope_ring.py, render_scene.py, fig_winch.py, fig_rail.py, art_rope_a.py),
# run here unchanged with their ropes re-routed, parts hidden or added, and the labels and note taken from the
# question's figure only (the answer and its reasoning are never printed).
#   blender --background --factory-startup --python docs/design/blender/q_rope.py -- --id bs-011 [--samples 128] [--scale 100]
# A question that shares another's image (SAME) copies that render and writes its own labels.
import os, sys, math, json, random, shutil
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy, bmesh
from mathutils import Vector, Matrix
import common as C, kit as K
import q_rope_geo as G
from q_rope_geo import V, T3

arg = C.cli()
QID = arg('--id', 'bs-011'); SAMPLES = arg('--samples', 128); SCALE = arg('--scale', 100); OUTDIR = arg('--outdir', '')
QDIR = os.path.join(HERE, '..', 'figure-style', 'questions', 'bareboat-skipper')
with open(os.path.join(QDIR, 'rope.json')) as f: ITEMS = {q['id']: q for q in json.load(f)}
Q = ITEMS[QID]; FIG = Q['figure']
OUT = os.path.join(OUTDIR or os.path.join(QDIR, QID), '3d.jpg')
NOTE = FIG.get('note')
TEXTS = [l[2] for l in FIG.get('labels', [])]

def write_ru():
    """ru.json: the Russian of every English string on the image (the bank's own, from the list's ru map)."""
    ru = Q.get('ru', {}); out = {}
    for t in ([NOTE] if NOTE else []) + TEXTS:
        if t not in ru: raise SystemExit(f'{QID}: no Russian for {t!r}')
        out[t] = ru[t]
    with open(os.path.join(os.path.dirname(OUT), 'ru.json'), 'w') as f: json.dump(out, f, ensure_ascii=False, indent=1)

def labels_from(points):
    """points: {figure label text: 3D point} -> the render's label list, in the figure's order."""
    miss = [t for t in TEXTS if t not in points]
    if miss: raise SystemExit(f'{QID}: no place for labels {miss}')
    return [(tuple(points[t]), t) for t in TEXTS]

# ---------- running a library script with hooks ----------
_orig = dict(render=C.render, load_exported=C.load_exported, three_strand=C.three_strand, braid=C.braid, kcam=K.camera, lookat=C.camera_lookat)

def run_lib(script, argv, rope_fn=None, strand_fn=None, pre_render=None, points=None, cam=None, lookat=None, exposure=None, cammat=None):
    """Execute a library script as it is, with: rope_fn(i, P) re-routing exported ropes before the script's own
    re-routing; strand_fn(g, name, pts3) -> pts3 (or None to drop that rope) for ropes it builds with three_strand;
    pre_render(g) to hide or add parts; points(g) -> {label text: point} in the script's label space;
    cam (eye, look, lens) replacing kit.camera, lookat (pos3, target3, fov) replacing common.camera_lookat."""
    g = {'__name__': '__main__', '__file__': os.path.join(HERE, script)}
    sys.argv = ['blender', '--'] + [str(a) for a in argv]
    def render(out, samples=256, scale=100, exp=-0.6, labels=(), note=None, blend='', space='three', arrows=(), extra=None):
        if pre_render: pre_render(g)
        labs = labels_from(points(g)) if points else []
        _orig['render'](OUT, SAMPLES, SCALE, exp if exposure is None else exposure, labs, NOTE, '', space, (), None)
    C.render = render
    if rope_fn:
        def load_exported(path, rope_fn_inner=None, **kw):
            if 'rope_fn' in kw: rope_fn_inner = kw['rope_fn']
            f = (lambda i, P: rope_fn_inner(i, rope_fn(i, P))) if rope_fn_inner else rope_fn
            return _orig['load_exported'](path, rope_fn=f)
        C.load_exported = load_exported
    if strand_fn:
        def three_strand(name, pts3, *a, **k):
            p = strand_fn(g, name, pts3)
            if p is not None: _orig['three_strand'](name, p, *a, **k)
        C.three_strand = three_strand
    if cam:
        K.camera = lambda eye, look, lens=24.0: _orig['kcam'](cam[0], cam[1], cam[2])
    if cammat:   # replace an exported camera (common.camera_matrix) by a look-at camera, Three.js space
        C.camera_matrix = lambda m16, fov_y: _orig['lookat'](cammat[0], cammat[1], cammat[2])
    if lookat:
        C.camera_lookat = lambda pos3, target3, fov_y: _orig['lookat'](lookat[0], lookat[1], lookat[2])
    path = os.path.join(HERE, script)
    exec(compile(open(path).read(), path, 'exec'), g)
    return g

def hide(pred):
    for o in list(bpy.data.objects):
        if o.type == 'MESH' and pred(o): o.hide_render = True

def near(o, p, r):
    lo, hi = K.bbox([o]) if not o.hide_render else (None, None)
    if lo is None: return False
    return ((lo + hi) / 2 - Vector(p)).length < r

# =====================================================================================================
# ring: a mooring line ashore (bollard, quay ring, kedge ring, shackle)
# =====================================================================================================
def ring_lib(variant):
    """rope_ring.py: a loop over a cast-iron bollard on a granite quay, a yacht alongside (Three.js space)."""
    def strand(g, name, pts):
        if name != 'rope': return pts
        d, vv, u = g['d'], g['vv'], g['u']; ground, Rb, Ye = g['ground'], g['R'], g['Ye']
        far = [p for p in pts if p.length > 1.0]            # from the quay edge to the cleat on board
        if variant == 'loop':
            return pts
        if variant == 'bowline':
            # a bowline, its knot half a metre off the bollard, its loop round the bollard's neck
            P = G.knot_path('knot-bowline'); S = 0.013 / 0.006; O = d * 0.5; O.y = 0
            up = Vector((0, 1, 0))
            Q3 = [O + vv * (x * S) + up * ((y - 0.006) * S + ground) + u * (z * S) for x, y, z in P]
            i0, i1 = G.BOWLINE_LOOP
            Tm = g['at'](math.cos(math.radians(-108)) * Rb, math.sin(math.radians(-108)) * Rb, Ye)
            Tp = g['at'](math.cos(math.radians(108)) * Rb, math.sin(math.radians(108)) * Rb, Ye)
            def leg(a, b, n=7):
                out = []
                for i in range(1, n):
                    t = i / n; p = a.lerp(b, t); r = math.hypot(p.x, p.z)
                    p.y = max(ground, a.y + (b.y - a.y) * t ** 2.2) if r > 0.2 else p.y
                    out.append(p)
                return out
            wrap = [g['at'](math.cos(math.radians(a)) * Rb, math.sin(math.radians(a)) * Rb, Ye + 0.004 * math.cos(math.radians(a))) for a in range(-108, 109, 12)]
            body = Q3[:i0 + 1] + leg(Q3[i0], Tm) + wrap + leg(Tp, Q3[i1]) + Q3[i1:]
            return _join3(list(reversed(far)), body)
        if variant == 'clove':
            # a clove hitch on the bollard's neck, worked loose: the turns slack, the end half drawn out
            cen = V(0, 0, 0)
            toward = Vector((d.x, -d.z, 0))
            turns, end = G.clove_on_post(cen, toward, r_turn=0.128, y0=0.2, pitch=0.07, loose=1.3)
            turns3 = [Vector((p.x, p.z, -p.y)) for p in turns]; end3 = [Vector((p.x, p.z, -p.y)) for p in end]
            for p in turns3 + end3:             # slack: the turns hang open and droop on the side away from the pull
                h = Vector((p.x, 0, p.z)); c = h.normalized().dot(d) if h.length > 1e-6 else 0
                p.y -= 0.045 * (1 - c) / 2; p.x += d.x * -0.02 * (1 - c); p.z += d.z * -0.02 * (1 - c)
            # the end falls to the setts beside the bollard
            e = end3[-1]; out = Vector((e.x, 0, e.z)).normalized()
            end3 += [e + out * 0.08 + Vector((0, -0.06, 0)), e + out * 0.16 + Vector((0, -0.15, 0)), Vector((e.x + out.x * 0.22, ground, e.z + out.z * 0.22)), Vector((e.x + out.x * 0.24 + vv.x * 0.1, ground, e.z + out.z * 0.24 + vv.z * 0.1))]
            lead = [d * 1.15, d * 0.85, d * 0.55, d * 0.3]
            for p, y in zip(lead, (ground, ground + 0.01, 0.06, 0.13)): p.y = y
            return _join3(list(reversed(far)), lead[1:] + turns3 + end3)
        if variant == 'theirs':
            return pts
    pre = None
    if variant == 'theirs':
        def pre(g):
            # our own line: a braided warp, its spliced eye lying on the setts beside the bollard, the line led off
            d, vv = g['d'], g['vv']; gr = 0.012
            c = vv * 0.42 + d * 0.32
            eye = [c + vv * (math.cos(a) * 0.16) + d * (math.sin(a) * 0.1) for a in [math.radians(x) for x in range(200, 520, 20)]]
            throat = c + vv * (-0.2) + d * 0.02
            tail = [throat + vv * (-0.25) + d * 0.08, throat + vv * (-0.55) + d * 0.3, throat + vv * (-0.7) + d * 0.7, throat + vv * (-0.75) + d * 1.2]
            pts = list(reversed(tail)) + [throat] + eye + [throat + vv * 0.01 + d * 0.015]
            for p in pts: p.y = gr
            C.braid('our-line', [C.V3((p.x, p.y, p.z)) for p in pts], gr, '#1b2c4c', '#e9e3d2', fine=1.3)
    # the bowline lies on the setts behind the bollard as the library camera sees it: look from the side instead
    look = {'bowline': ((0.95, 1.25, -1.28), (-0.25, 0.06, -0.36), 38), 'clove': ((1.05, 1.05, -0.95), (-0.12, 0.15, -0.2), 36)}.get(variant)
    g = run_lib('rope_ring.py', [], strand_fn=strand, pre_render=pre, points=lambda g: {'bollard': (0, 0.47, 0)}, lookat=look)

def _join3(A, Bp):
    """Two Three.js paths joined end to start with a short eased bridge (so there is no kink or jump)."""
    if not A: return Bp
    if not Bp: return A
    Ab = [C.B(p.x, p.y, p.z) for p in A[-3:]]; Bb = [C.B(p.x, p.y, p.z) for p in Bp[:3]]
    mid = G.smooth_join(Ab, Bb, 4)
    return A + [Vector((p.x, p.z, -p.y)) for p in mid] + Bp

# ---------- the article's quay scenes (art_rope_a.py, Blender space) ----------
def art8(variant):
    """Fig 8: a bar-tight stern line from the yacht's port quarter to a bollard, a round turn on it.
    The snap-back zone and the footprints (the article's answer) are left out."""
    def pre(g):
        hide(lambda o: o.name.startswith(('zone-', 'foot')))
    run_lib('art_rope_a.py', ['--fig', 8], pre_render=pre, points=lambda g: {'bollard': g['b'] + V(0, 0, 0.55)},
            cam=((0.4, 4.3, 2.55), (2.0, -0.9, 1.05), 30))

def art6(variant):
    """Fig 6's scene: the yacht stern-to a granite quay, two bollards. Variants re-rig the starboard stern line:
    'handed' round the bollard with its end handed back on board (not made fast); 'ashore' made fast on the
    bollard in the ordinary way; 'slipring' a slip line through a quay ring; 'bowring' a bowline through a quay
    ring, bar tight; 'rtring' a round turn and two half hitches on a quay ring, bar tight."""
    st = {}
    QZ = 1.0
    def strand(g, name, pts3):
        if name != 'slip': return pts3
        cs, b, top = g['cs'], g['b'], g['top']
        a1, a2, wrap, leg1 = g['a1'], g['a2'], g['wrap'], g['leg1']
        if variant == 'handed':
            # round the bollard as a slip, the returning part led back aboard and its end lying loose on deck
            inb = V(-1, 0, 0); fwd = V(0, -1, 0)
            land = cs + inb * 0.06 + fwd * 0.10 + V(0, 0, 0.0)
            leg2 = G.catenary(wrap[-1], land, 0.25)[1:]
            deck = cs.z - 0.052
            tail = [land + inb * 0.12 + fwd * 0.12 + V(0, 0, deck - land.z + 0.012), cs + inb * 0.32 + fwd * 0.30 + V(0, 0, deck - cs.z + 0.012),
                    cs + inb * 0.50 + fwd * 0.22 + V(0, 0, deck - cs.z + 0.012), cs + inb * 0.62 + fwd * 0.42 + V(0, 0, deck - cs.z + 0.012)]
            return T3(leg1 + wrap + leg2 + tail)
        if variant == 'ashore':
            p = G.catenary(cs, b + V(0, -0.13, 0.3), 0.22) + [b + V(-0.13, 0.0, 0.3), b + V(0.0, 0.14, 0.31), b + V(0.13, 0.03, 0.3), b + V(0.05, -0.11, 0.29), b + V(0.4, 0.3, 0.04), b + V(0.6, 0.6, 0.03)]
            return T3(p)
        ring = st['ring']; Rr = 0.011
        if variant == 'slipring':
            sg = -1.0 if ring['ex'].dot(a1 - a2) > 0 else 1.0
            U = G.u_round_bar(ring, Rr, 50, 310, 16, 1.2 * sg)
            l1 = G.catenary(a1, U[0] + ring['out'] * 0.25 + V(0, 0, 0.05), 0.2)
            l2 = G.catenary(U[-1] + ring['out'] * 0.25 + V(0, 0, -0.01), a2, 0.2)
            return T3(l1 + G.smooth_join(l1, U, 4) + U + G.smooth_join(U, l2, 4) + l2)
        if variant == 'bowring':
            Lb = (cs - ring['tip']); Lb.normalize()
            s = Lb.cross(V(0, 0, 1)).normalized(); up = s.cross(Lb).normalized()
            S = Rr / 0.006; O = ring['tip'] + Lb * 0.40
            P = G.knot_path('knot-bowline')
            Qb = G.place_knot(P, O, s, up, -Lb, S)
            i0, i1 = G.BOWLINE_LOOP
            sg = -1.0 if ring['ex'].dot(Qb[i0] - Qb[i1]) > 0 else 1.0
            U = G.u_round_bar(ring, Rr, 45, 315, 16, 1.6 * sg)
            body = Qb[:i0 + 1] + G.smooth_join(Qb[:i0 + 1], U, 6) + U + G.smooth_join(U, Qb[i1:], 6) + Qb[i1:]
            head = [cs + (Qb[0] - cs) * t for t in (0.0, 0.25, 0.5, 0.75, 0.92)]
            return T3(head + body)
        if variant == 'rtring':
            Lb = (cs - ring['tip']); Lb.normalize()
            ex = ring['ex']
            if ex.dot(Lb.cross(V(0, 0, 1))) < 0: ex = -ex
            zax = Lb.cross(ex).normalized()
            S = Rr / 0.006; rho = ring['r'] + Rr
            P = G.knot_path('knot-roundturn')
            out = []
            for x, y, z in P:
                dd = math.hypot(x, z); w = 1.0 if dd < 0.06 else max(0.0, 1 - (dd - 0.06) / 0.08)
                k = (1 - w) * S + w * (rho / 0.054)                 # round the post: onto the ring's bar
                # the post's axis is the file's y; the bar's axis is ex
                out.append(ring['tip'] + Lb * (x * k) + zax * (z * k) + ex * ((y - 0.006) * S - 0.6 * Rr))
            out = list(reversed(out))                                 # start at the end, finish with the standing part
            tail = [cs + (out[-1] - cs) * t for t in (0.92, 0.75, 0.5, 0.25, 0.0)]
            return T3(out + tail)
        return pts3
    def setup_ring(g):
        b = g['b']
        hide(lambda o: o.name.startswith('bollard') and near(o, b + V(0, 0, 0.23), 0.3))
    pre = None
    if variant in ('slipring', 'bowring', 'rtring'):
        # the quay ring replaces the bollard the slip line used: built when the script makes that rope
        def pre(g): setup_ring(g)
        def strand_ring(g, name, pts3):
            if name == 'slip' and 'ring' not in st:
                b = g['b']; cs = g['cs']
                toward = cs - b; toward.z = 0
                st['ring'] = G.quay_ring(V(b.x, 0.36, QZ), toward, R=0.085, r=0.012, lift=24 if variant != 'slipring' else 14)
            return strand(g, name, pts3)
        sfn = strand_ring
    else:
        sfn = strand
    def pts(g):
        if variant in ('slipring', 'bowring', 'rtring'):
            return {'quay ring': st['ring']['c'] + V(0, 0, 0.03)}
        return {'bollard': g['b'] + V(0, 0, 0.62)}
    camv = {'bowring': ((-2.9, 1.25, 1.75), (-2.1, -0.15, 1.05), 40), 'rtring': ((-2.75, 1.05, 1.62), (-2.15, 0.05, 1.04), 50),
            'slipring': ((-3.05, 1.75, 1.95), (-2.05, -0.7, 1.08), 36)}.get(variant)
    run_lib('art_rope_a.py', ['--fig', 6], strand_fn=sfn, pre_render=pre, points=pts, cam=camv)

def art1(variant):
    """Fig 1: an eye splice shackled down, close up. Here with no thimble in the eye and a chain beyond the shackle."""
    def pre(g):
        hide(lambda o: o.name.startswith(('thimble', 'ring', 'eye-plate')))
        dx = V(0.016, 0, 0)
        for o in bpy.data.objects:
            if o.name.startswith(('pin', 'shackle-bow')): o.location += dx
        bow_end = V(-0.238 + 0.016 - 0.1125, 0.8, 0.0)
        G.chain([bow_end + V(-0.012, 0, 0), bow_end + V(-0.12, 0.01, 0), bow_end + V(-0.24, -0.02, 0), bow_end + V(-0.36, 0.03, 0), bow_end + V(-0.5, 0.06, 0)],
                link_len=0.052, wire=0.0062, start_upright=True)
    run_lib('art_rope_a.py', ['--fig', 1], pre_render=pre,
            points=lambda g: {'shackle': V(-0.30, 0.8, 0.04), 'eye splice': V(-0.06, 0.8, 0.03)},
            cam=((-0.08, 0.5, 0.44), (-0.22, 0.8, 0.0), 42))

# =====================================================================================================
# winch (fig_winch.py: the exported cockpit, a Lewmar self-tailer; Three.js space)
# =====================================================================================================
DRUM = (0.035, 0.17, 0.045)        # a point on the drum's face towards the camera, Three.js (after fig_winch's lift)
def winch(variant, handle=False, third=None, clutch=False):
    def rope(i, P):
        P = [list(p) for p in P]
        if variant == 'A': return P
        if variant == 'B':                       # turns on, the tail straight off the top turn (not in the jaws)
            head, tail = P[:2240], P[2400:]; dy = P[2240][1] - P[2400][1]
            for k, p in enumerate(tail): p[1] += dy * max(0.0, 1 - k / 120)
            return head + tail
        if variant == 'C':                       # only two turns on the drum
            head, tail = P[:2080], P[2240:]; dy = P[2240][1] - P[2079][1]
            for k in range(160): head[2080 - 160 + k][1] += dy * (k / 160)
            return head + tail
        if variant == 'F':                       # the turns put on anticlockwise: mirror the drum about the lead
            th0 = math.atan2(P[1400][2], P[1400][0]); out = []
            for x, y, z in P:
                r = math.hypot(x, z)
                w = 1.0 if r < 0.095 else max(0.0, (0.15 - r) / 0.055)
                if w > 0 and 0.03 < y < 0.24:
                    th = math.atan2(z, x); tm = 2 * th0 - th
                    dlt = (tm - th + math.pi) % math.tau - math.pi
                    th += dlt * w; x, z = r * math.cos(th), r * math.sin(th)
                out.append([x, y, z])
            return out
        if variant == 'G':                       # a riding turn: the first turn climbs over the second
            for i in range(1730, 1890):
                t = (i - 1730) / 160; b = math.sin(math.pi * t) ** 1.5
                x, y, z = P[i]; r = math.hypot(x, z); th = math.atan2(z, x)
                r2 = r + 0.0125 * b; P[i] = [r2 * math.cos(th), y + 0.034 * b, r2 * math.sin(th)]
            return P
        if variant in ('D', 'E'):                # not on the winch: led past it, slack, down to the cockpit
            coil = P[2680:]
            if variant == 'D':
                lead = P[:1500]
            else:                                # a halyard: along the coachroof top, through a closed clutch
                lead = [[x, 0.026 if -0.76 < x < -0.46 else 0.012, -0.055] for x in [-1.6 + 0.1 * k for k in range(12)]]
            mid = [[-0.33, 0.016, -0.08], [-0.24, 0.012, 0.04], [-0.2, 0.01, 0.15], [-0.19, -0.004, 0.19], [-0.18, -0.06, 0.2],
                   [-0.14, -0.18, 0.205], [-0.05, -0.29, 0.23], [0.1, -0.335, 0.26], [0.22, -0.345, 0.28]]
            return lead + mid + coil
        return P
    def pre(g):
        if not handle:
            for o in g['handle']: o.hide_render = True
        if clutch:
            G.clutch(C.B(-0.62, 0.0, -0.055), V(1, 0, 0), 0.14)
    pts = {}
    def points(g):
        p = {TEXTS[0]: (-0.62, -0.02, -0.39) if variant != 'E' else (-0.95, 0.03, -0.055),
             TEXTS[1]: (0.25, 0.03, 0.15) if variant not in ('D', 'E') else (-0.17, -0.1, 0.2)}
        if third:
            p[TEXTS[2]] = third
        return p
    # closer than the library's view, so the turns on the drum can be read
    run_lib('fig_winch.py', [], rope_fn=rope, pre_render=pre, points=points, cammat=((0.36, 0.66, 0.74), (-0.14, 0.1, -0.06), 40))

# =====================================================================================================
# cleat (render_scene.py --name cleat: a white three-strand line through a fairlead to a deck cleat; Three.js)
# =====================================================================================================
def cleat(variant):
    def rope(i, P):
        P = [tuple(p) for p in P]
        coil = P[2072:]
        if variant == 'full': return P
        if variant == 'started':                 # led to the cleat, round the far horn, the rest still loose
            return P[:1262] + [(0.11, 0.011, 0.06), (0.17, 0.009, 0.1), (0.23, 0.009, 0.135)] + coil
        if variant == 'approach':                # on a pontoon: the line from the boat lands beside the cleat
            lead = [(-1.05, 0.95, -1.35), (-0.88, 0.7, -1.1), (-0.7, 0.42, -0.86), (-0.52, 0.16, -0.6), (-0.38, 0.02, -0.38), (-0.3, 0.009, -0.27),
                    (-0.2, 0.009, -0.16), (-0.1, 0.009, -0.12), (0.02, 0.009, -0.14), (0.13, 0.009, -0.11), (0.2, 0.009, -0.02), (0.24, 0.009, 0.08)]
            return lead + coil
        if variant == 'toerail':                 # led straight over the toe rail, not through the fairlead
            lead = [(-0.36, -0.9, -1.28), (-0.3, -0.5, -0.92), (-0.24, -0.12, -0.62), (-0.205, 0.035, -0.515), (-0.19, 0.066, -0.47), (-0.18, 0.04, -0.425),
                    (-0.175, 0.012, -0.36), (-0.17, 0.009, -0.25)]
            return lead + P[1000:]
        if variant == 'three':                   # the cleat hitch finished with three locking hitches piled on top
            dy = 0.017
            def up(seg, k): return [(x, y + dy * k, z) for x, y, z in seg]
            s1, s2 = P[1533:1785], P[1785:1932]
            out = P[:1932] + up(s1, 1) + up(s2, 1) + up(s1, 2) + up(s2, 2)
            t = P[1932:]
            out += [(x, y + 2 * dy * max(0.0, 1 - k / 90), z) for k, (x, y, z) in enumerate(t)]
            return out
        if variant == 'two':                     # the spring (this line) under; the stern line goes on top (pre)
            return P
        return P
    def pre(g):
        if variant == 'approach':
            fl = C.concrete_mat('pontoon')
            for o in bpy.data.objects:
                if o.type != 'MESH': continue
                names = [s.material.name.split('.')[0] if s.material else '' for s in o.material_slots]
                lo, hi = K.bbox([o])
                if 'nonskid' in names: o.material_slots[0].material = fl
                elif 'water' in names: o.location.z += 0.72
                elif hi.y > 0.44 and lo.y > 0.4 and hi.z < 0.1 and lo.z > -1.3 and (hi.x - lo.x) > 0.05: o.hide_render = True
            C.obj('pontoon-body', C.rbox('pontoon-body', (3.0, 1.8, 0.5), 0.02, 2), fl, V(0, -0.43, -0.34))
        if variant == 'two':
            # a second fairlead aft, and the stern line (navy braid) made fast on top of the spring's hitch
            fl = [o for o in bpy.data.objects if o.type == 'MESH' and o.material_slots and o.material_slots[0].material and o.material_slots[0].material.name.startswith('chrome') and K.bbox([o])[0].x < -0.3]
            for o in fl:
                c = o.copy(); C.col.objects.link(c); c.location.x += 0.82
            P = g['d']['ropes'][0]['P']
            hitch = [(-x * 1.06, y + 0.019, z * 1.1) for x, y, z in P[1064:1953]]
            lead = [(0.62, -0.9, -1.25), (0.5, -0.4, -0.86), (0.42, 0.05, -0.46), (0.36, 0.016, -0.36), (0.25, 0.022, -0.17)]
            tail = [(-0.15, 0.03, 0.08), (-0.22, 0.012, 0.15), (-0.34, 0.009, 0.22), (-0.46, 0.009, 0.24)]
            path = lead + hitch + tail
            C.braid('stern-line', [C.V3(p) for p in path], 0.0085, '#1b2c4c', '#e9e3d2', whip='#141414', fine=1.3)
    lab = {
        'full': {'load': (-0.47, -0.17, -0.74), 'cleat on board': (0.13, 0.11, -0.01)},
        'started': {'cleat': (0.0, 0.1, 0.0)},
        'approach': {'load': (-0.3, 0.012, -0.27), 'pontoon cleat': (0.0, 0.095, 0.0)},
        'toerail': {'to the quay': (-0.2, 0.07, -0.5), 'cleat': (0.1, 0.09, 0.02)},
        'three': {'stern line': (-0.3, 0.03, -0.3), 'three locking hitches': (0.08, 0.15, 0.03)},
        'two': {'two lines': (0.36, 0.03, -0.36), 'spring under, stern line on top': (0.0, 0.13, 0.0)},
    }[variant]
    if variant == 'two':
        # render_scene keeps its data in d; keep a handle on it for pre()
        pass
    cm = {'toerail': ((0.42, 0.72, 0.52), (-0.16, 0.0, -0.3), 40)}.get(variant)   # back far enough to see the toe rail
    run_lib('render_scene.py', ['--name', 'cleat'], rope_fn=rope, pre_render=pre, points=lambda g: lab, cammat=cm)

# =====================================================================================================
# sheet: lines on a teak deck (render_scene.py scenes 'sheet' and 'knot-sheetbend'); a sheet block
# =====================================================================================================
def sheet_lines():
    run_lib('render_scene.py', ['--name', 'sheet'], points=lambda g: {'thin line': (0.3, 0.0035, -0.14), 'thick line': (-0.25, 0.009, 0.1)})

def sheet_bend_loose():
    """The single sheet bend, its thin line's turn worked a little loose."""
    def rope(i, P):
        if i != 1: return P
        cx, cz = -0.05, 0.0
        out = []
        for x, y, z in P:
            dd = math.hypot(x - cx, z - cz); w = max(0.0, 1 - dd / 0.13)
            out.append((x + (x - cx) * 0.22 * w, y, z + (z - cz) * 0.3 * w))
        return out
    run_lib('render_scene.py', ['--name', 'knot-sheetbend'], rope_fn=rope,
            points=lambda g: {'thin, slippery': (0.115, 0.009, -0.002), 'thick, stiff': (-0.125, 0.015, -0.024)})

def sheet_block():
    """A jib sheet block on its car on the side deck, the sheet run out of it: the end lies beside the block,
    the sheet led up and away towards the flogging sail."""
    C.reset()
    C.tbox((2.2, 0.04, 1.4), (0, -0.02, 0), C.nonskid_mat(), 0.004, 2, 'deck')
    C.tbox((2.2, 0.03, 0.06), (0, 0.015, -0.72), C.teak_mat(), 0.006, 2, 'toerail')
    C.tbox((2.2, 0.012, 0.03), (0, 0.006, -0.3), C.simple('track', '#c4c8cc', 0.3, 1.0), 0.003, 2, 'track')
    for k in range(-8, 9):
        C.cyl('track-pin', 0.004, 0.004, 0.004, 12, C.simple('pinm', '#2a2b2d', 0.4, 0.6), C.B(k * 0.12, 0.013, -0.3))
    at = C.B(0.0, 0.012, -0.3)
    c, ax, h = G.block(at, V(1, 0, 0))
    wm = bpy.data.meshes.new('sea'); wm.from_pydata([(-600, -600, 0), (600, -600, 0), (600, 600, 0), (-600, 600, 0)], [], [(0, 1, 2, 3)])
    C.obj('sea', wm, C.water_mat(), (0, 0, -1.1))
    R = 0.006
    # the sheet: from the end lying past the block on the deck, out over the toe rail and up to the clew (out of frame)
    endp = [C.B(0.18, R, -0.36), C.B(0.1, R, -0.335), C.B(0.02, R, -0.37), C.B(-0.08, R, -0.45), C.B(-0.2, R, -0.58), C.B(-0.3, 0.045, -0.71),
            C.B(-0.4, 0.15, -0.85), C.B(-0.55, 0.5, -1.15), C.B(-0.8, 1.2, -1.6)]
    C.braid('sheet', T3(list(reversed(endp))), R, '#e9e5da', '#2b4d8c', shiny=True, whip='#c8161d', fine=1.5)
    # the lazy (other) sheet's block and line further aft, for scale
    C.sky((-1.4, 3.0, -0.8), (0, 0, 0)); K.darken_visible_sky()
    cam = C.camera_lookat((0.62, 0.42, 0.36), (-0.02, 0.0, -0.36), 36)
    C.focus_on_centre(cam, 11.0)
    C.render(OUT, SAMPLES, SCALE, -0.7, labels_from({'sheet end': (0.18, 0.015, -0.36), 'block': (0.0, 0.11, -0.3)}), NOTE)

# =====================================================================================================
# rail (fig_rail.py: the fender line over the yacht's guardrail; Blender space)
# =====================================================================================================
def rail():
    run_lib('fig_rail.py', [], points=lambda g: {'guardrail': V(-0.6, g['side_y'](-0.6, g['wire_z']) or g['wire_y'], g['wire_z'])})

# =====================================================================================================
# custom scenes: the dinghy at the quay ring, the kedge on deck, the halyard on the mast cleat
# =====================================================================================================
def art_helpers():
    """art_rope_a.py's helpers (quay, bollard, yacht stern-to, cleats) without running its figures."""
    path = os.path.join(HERE, 'art_rope_a.py'); src = open(path).read()
    head = src.split('\nC.reset()\nif FIG == 1:')[0]
    g = {'__name__': 'art_rope_a_helpers', '__file__': path}
    sys.argv = ['blender', '--', '--fig', '0']
    exec(compile(head, path, 'exec'), g)
    return g

def dinghy_ring():
    A = art_helpers(); C.reset(); random.seed(7)
    QZ = A['QZ']
    K.sea('calm', center=(0, -10))
    A['quay'](-5.0, 5.0, 4.0)
    ring = G.quay_ring(V(0.0, 0.36, QZ), V(0, -1, 0), R=0.085, r=0.012, lift=30)
    # the RIB lying off the quay wall, her bow towards it
    root, objs = K.load_model('tender-rib.glb')
    M = K.mats()
    def rule(c, name):
        if c is None: return None
        l = sum(c) / 3
        return M['dark'] if l < 0.2 else C.simple('tube-grey', '#9aa0a6', 0.55) if l > 0.6 else None
    K.recolor(objs, rule)
    bpy.context.view_layer.update(); vis = [o for o in objs if o.type == 'MESH' and not o.hide_render]
    lo, hi = K.bbox(vis); L = max(hi.x - lo.x, hi.y - lo.y)
    # the model lies along x with her bow towards +x: turn her bow to the quay (+y), a painter's length off
    root.rotation_euler.z = math.radians(90)
    bpy.context.view_layer.update(); lo, hi = K.bbox(vis)
    root.location += V(0.35 - (lo.x + hi.x) / 2, -2.3 - hi.y, -lo.z - 0.32)
    bpy.context.view_layer.update(); lo, hi = K.bbox(vis)
    print('RIB', lo, hi)
    bow = V((lo.x + hi.x) / 2, hi.y - 0.12, 0.3)
    Rr = 0.008
    U = G.u_round_bar(ring, Rr, 40, 320, 16, 1.4)
    up_edge = V(0.02, 0.0, QZ + Rr + 0.004)
    lead = [bow, bow.lerp(up_edge, 0.5) + V(0, 0, -0.006), up_edge + V(0, -0.02, -0.004), up_edge + V(0, 0.08, 0.0)]
    # the end: through the ring and out the other side, lying loose on the quay (not yet made fast)
    endp = [U[-1] + ring['out'] * 0.05 + V(0, 0, -0.01), V(0.12, 0.32, QZ + Rr), V(0.3, 0.42, QZ + Rr), V(0.45, 0.62, QZ + Rr), V(0.48, 0.85, QZ + Rr)]
    path = lead + G.smooth_join(lead, U, 4) + U + endp
    C.three_strand('painter', T3(path), Rr, 0.05, whip='#f2eee2')
    K.day_sky(sun_az=215, sun_el=40); K.darken_visible_sky()
    cam = K.camera((1.45, 1.7, 2.05), (0.1, -0.55, 0.85), 30); C.focus_on_centre(cam, 11.0)
    C.render(OUT, SAMPLES, SCALE, -0.7, labels_from({'quay ring': ring['c'] + V(0, 0, 0.03)}), NOTE, space='blender')

def kedge():
    """The kedge (a Delta) lying on the foredeck teak, a galvanised ring in its shank's eye, the nylon warp
    coiled beside it, its end not yet bent on."""
    C.reset(); random.seed(3)
    C.tbox((3.0, 0.04, 2.2), (0, -0.02, 0), C.teak_mat(), 0.004, 2, 'deck')
    wm = bpy.data.meshes.new('sea'); wm.from_pydata([(-600, -600, 0), (600, -600, 0), (600, 600, 0), (-600, 600, 0)], [], [(0, 1, 2, 3)])
    C.obj('sea', wm, C.water_mat(), (0, 0, -1.3))
    root, objs = K.load_model('anchor-delta.glb', drop_planes=False)
    # in the file the shank's tip (its eye) is at x 0.48, the blade towards +x
    root.matrix_world = Matrix.Rotation(math.radians(200), 4, 'Z') @ Matrix.Translation((-0.48, -1.17, 0.0))
    bpy.context.view_layer.update(); lo, hi = K.bbox(objs); root.location.z += 0.0 - lo.z
    bpy.context.view_layer.update()
    K.recolor(objs, lambda c, n: C.galv_mat('anchor-galv'))
    hole = root.matrix_world @ Vector((0.48, 1.17, 0.52))
    sh = (root.matrix_world.to_3x3() @ Vector((1, 0, 0))); sh.z = 0; sh.normalize()      # from the eye towards the blade
    ex = V(-sh.y, sh.x, 0)
    gm = C.galv_mat('ring-galv')
    rc = hole - sh * 0.03 + V(0, 0, -0.012)
    ringp = [rc + (sh * math.cos(a) + V(0, 0, 1) * math.sin(a)) * 0.04 for a in [k / 48 * math.tau for k in range(49)]]
    G.tubeP('kedge-ring', ringp, 0.0075, gm, 16)
    # the warp: a loose coil on the teak beside the anchor, its end led up to the ring, not yet through it
    R = 0.008; cc = hole + sh * 0.15 + ex * 0.42; cc.z = R
    coil = []
    for k in range(5):
        rr = 0.16 + 0.011 * k
        for i in range(24):
            a = i / 24 * math.tau + k * 0.3
            coil.append(cc + V(math.cos(a) * rr * 1.05, math.sin(a) * rr * 0.92, 0.0) + V(0, 0, R * 1.4 * (k % 2)))
    tip = rc - sh * 0.09 + ex * 0.05; tip.z = R
    endp = [coil[-1].lerp(tip, t) for t in (0.33, 0.66)] + [tip]
    for p in endp: p.z = R
    C.three_strand('warp', T3(coil + endp), R, 0.05, whip='#f2eee2')
    K.day_sky(sun_az=200, sun_el=45); K.darken_visible_sky()
    cam = K.camera(tuple(rc + sh * 0.25 + ex * (-0.75) + V(0, 0, 1.05)), tuple(rc + sh * 0.2 + ex * 0.15 + V(0, 0, -0.05)), 32); C.focus_on_centre(cam, 11.0)
    C.render(OUT, SAMPLES, SCALE, -0.7, labels_from({'kedge ring': rc + V(0, 0, 0.045)}), NOTE, space='blender')

def mast_cleat():
    """The halyard made fast on the mast cleat (as in the article's figure 9), its tail coiled and lying on the
    coachroof at the mast foot (the hanging of the coil is the answer, so it is not shown)."""
    C.reset()
    K.sea('calm')
    y = K.load_yacht(name='yacht'); y.place(0, 0, heading=0)
    K.coast(distance=900, bearing=60, height=90, town=False)
    K.day_sky(sun_az=150, sun_el=40); K.darken_visible_sky()
    bpy.context.view_layer.update()
    face = y.world((5.065, 0.07, 4.62)); out = (y.world((5.065, -1.0, 4.62)) - face).normalized(); up = V(0, 0, 1)
    fwd = out.cross(up).normalized()
    cm = C.simple('mast-cleat', '#c9cdd1', 0.3, 1.0)
    cleat = face + out * 0.045
    C.cyl('cleat-horns', 0.011, 0.011, 0.17, 24, cm, cleat)
    for dz in (-0.04, 0.04):
        o = C.cyl('cleat-leg', 0.011, 0.014, 0.05, 16, cm, face + out * 0.022 + V(0, 0, dz)); o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = out.to_track_quat('Z', 'Y')
    top = face + out * 0.03 + V(0, 0, 1.4)
    p = [top, top.lerp(cleat + out * 0.02 + V(0, 0, 0.12), 0.6), cleat + out * 0.02 + V(0, 0, 0.12), cleat + fwd * 0.02 + out * 0.01 + V(0, 0, 0.03)]
    for k in range(3):
        sgn = 1 if k % 2 == 0 else -1
        p += [cleat - fwd * 0.02 * sgn + out * 0.022 + V(0, 0, -0.07 * sgn), cleat + fwd * 0.02 * sgn + out * 0.022 + V(0, 0, -0.085 * sgn), cleat + fwd * 0.02 * sgn - out * 0.006 + V(0, 0, 0.0)]
    # the tail: off the cleat, down the mast to the coachroof, a coil lying there
    dg = bpy.context.evaluated_depsgraph_get()
    base = face + out * 0.32 + fwd * 0.05
    hit, loc, *_ = bpy.context.scene.ray_cast(dg, base + V(0, 0, 2.0), V(0, 0, -1))
    deck = loc.z if hit else face.z - 1.1
    hr = 0.0052
    p += [cleat + out * 0.03 - fwd * 0.03 + V(0, 0, -0.06), face + out * 0.05 - fwd * 0.04 + V(0, 0, -0.35), face + out * 0.08 - fwd * 0.02 + V(0, 0, deck - face.z + 0.12)]
    cc = face + out * 0.34 + fwd * 0.04; cc.z = deck + hr
    coil = []
    for k in range(7):
        rr = 0.13 + 0.006 * (k - 3)
        for i in range(24):
            a = i / 24 * math.tau + k * 0.5
            coil.append(cc + out * (math.cos(a) * rr) + fwd * (math.sin(a) * rr * 1.1) + V(0, 0, hr * 1.5 * (k % 3)))
    first = coil[0]
    p += [first + V(0, 0, 0.02)]
    C.braid('halyard', T3(p + coil), hr, '#c4262e', '#f3f1ea', shiny=True, fine=1.6, whip='#f4f1e6')
    labels = labels_from({'mast cleat': cleat + out * 0.03 + V(0, 0, 0.11), 'halyard': cleat + out * 0.035 + V(0, 0, 0.24)})
    eye = cleat + out * 1.3 - fwd * 0.6 + V(0, 0, 0.12); look = cleat + V(0, 0, -0.32) + out * 0.2
    cam = K.camera(tuple(eye), tuple(look), 19); C.focus_on_centre(cam, 8.0)
    C.render(OUT, SAMPLES, SCALE, -0.7, labels, NOTE, space='blender')

# =====================================================================================================
SPEC = {
    # ring
    'bs-011': lambda: ring_lib('loop'),
    'bs-279': lambda: ring_lib('bowline'),
    'bs-268': lambda: ring_lib('theirs'),
    'bs-210': lambda: ring_lib('clove'),
    'bs-230': lambda: art8('plain'),
    'bs-260': 'bs-230',
    'bs-243': lambda: art6('handed'),
    'bs-245': lambda: art6('ashore'),
    'bs-269': lambda: art6('slipring'),
    'bs-261': lambda: art6('bowring'),
    'bs-248': lambda: art6('rtring'),
    'bs-015': dinghy_ring,
    'bs-209': kedge,
    'bs-240': lambda: art1('nothimble'),
    # sheet
    'bs-012': sheet_block,
    'bs-211': sheet_bend_loose,
    'bs-257': sheet_lines,
    # rail
    'bs-013': rail,
    # cleat
    'bs-016': lambda: cleat('started'),
    'bs-201': lambda: cleat('toerail'),
    'bs-214': lambda: cleat('three'),
    'bs-215': lambda: cleat('approach'),
    'bs-216': lambda: cleat('full'),
    'bs-235': mast_cleat,
    'bs-278': lambda: cleat('two'),
    # winch
    'bs-017': lambda: winch('G', third=(0.02, 0.185, 0.07)),
    'bs-020': lambda: winch('D'),
    'bs-124': lambda: winch('A'),
    'bs-125': lambda: winch('D'),
    'bs-159': lambda: winch('E', clutch=True),
    'bs-198': lambda: winch('A', handle=True, third=(0.235, 0.05 + 6.19 * 0.040 + 0.09, 0.08)),
    'bs-218': lambda: winch('D'),
    'bs-219': lambda: winch('A'),
    'bs-220': lambda: winch('D', third=(0.0, 0.05 + 6.19 * 0.040 + 0.03, 0.0)),
    'bs-222': lambda: winch('B'),
    'bs-253': lambda: winch('C'),
    'bs-259': lambda: winch('A', handle=True),
    'bs-262': lambda: winch('F', third=(0.0, 0.31, 0.0)),
    'bs-271': lambda: winch('A'),
    'bs-277': lambda: winch('A'),
}

def same_as(src):
    """Copy another question's render and write this question's labels at the same anchors (by position in the
    figure's own label list; the texts are this question's)."""
    sdir = os.path.join(QDIR, src)
    shutil.copyfile(os.path.join(sdir, '3d.jpg'), OUT)
    with open(os.path.join(sdir, '3d.labels.json')) as f: L = json.load(f)
    with open(os.path.join(QDIR, 'rope.json')) as f: srcq = {q['id']: q for q in json.load(f)}[src]
    stexts = [l[2] for l in srcq['figure'].get('labels', [])]
    anchors = {l['text']: l for l in L['labels']}
    labs = []
    for i, t in enumerate(TEXTS):
        a = anchors[stexts[i]]; labs.append({'text': t, 'x': a['x'], 'y': a['y'], **({'color': a['color']} if 'color' in a else {})})
    with open(os.path.join(os.path.dirname(OUT), '3d.labels.json'), 'w') as f:
        json.dump({'note': NOTE, 'labels': labs, 'arrows': []}, f)

os.makedirs(os.path.dirname(OUT), exist_ok=True)
s = SPEC[QID]
if isinstance(s, str): same_as(s)
else: s()
write_ru()
if not OUTDIR:
    import q_rope_plans; q_rope_plans.write(QID)
print('Q_ROPE DONE', QID, OUT)
