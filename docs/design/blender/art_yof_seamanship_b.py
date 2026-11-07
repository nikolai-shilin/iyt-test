# Yachtmaster Offshore seamanship, the two figures that are the rope library's own scenes run with hooks (exec'd
# from art_yof_seamanship.py, which has set FIG, OUT, SAMPLES, SCALE, ADIR and HERE):
#   1  a bowline in the end of a nylon tow line over a cast-iron quay bollard: rope_ring.py with its rope re-routed
#      through the knot-bowline centreline (as q_rope.py ring_lib('bowline'))
#   3  the snubber: art_checkin_ground.py figure 5 as it is (the nylon on a chain hook, the chain hanging slack
#      between the roller and the hook), with this article's labels
import math
from mathutils import Vector
import common as C, kit as K

if FIG == 3:
    import art_checkin_gear as G
    def labels3(g):
        V_ = lambda x, y, z: Vector((x, y, z))
        Hk, rl, cl, fair = g['Hk'], g['g']['roller'], g['cl'], g['fair']
        slack = rl.lerp(Hk, 0.5) + V_(0.12, 0, -0.6)
        return [(tuple(Hk + V_(0, -0.05, 0.14)), 'nylon hooked to the chain', 'blue'),
                (tuple(slack), 'chain slack below the hook'),
                (tuple(cl.lerp(fair, 0.75) + V_(0, 0, 0.03)), 'made fast on the bow cleat')]
    _render = C.render
    g = {'__name__': '__main__', '__file__': os.path.join(HERE, 'art_checkin_ground.py')}
    sys.argv = ['blender', '--', '--fig', '5']
    def render(o, s=256, sc=100, exp=-0.6, labels=(), nt=None, blend='', space='three', arrows=(), extra=None, **kw):
        _render(OUT, SAMPLES, SCALE, exp, labels3(g), 'Snubber rigged', '', 'blender', (), {'lines': ['It spares the windlass, not the chain']})
    C.render = render
    path = os.path.join(HERE, 'art_checkin_ground.py')
    try: exec(compile(open(path).read(), path, 'exec'), g)
    finally: C.render = _render

else:   # FIG 1
    import q_rope_geo as QG
    _orig = dict(render=C.render, three_strand=C.three_strand, lookat=C.camera_lookat)
    def _join3(A, Bp):
        if not A: return Bp
        if not Bp: return A
        Ab = [C.B(p.x, p.y, p.z) for p in A[-3:]]; Bb = [C.B(p.x, p.y, p.z) for p in Bp[:3]]
        mid = QG.smooth_join(Ab, Bb, 4)
        return A + [Vector((p.x, p.z, -p.y)) for p in mid] + Bp
    def strand(g, name, pts):
        """(q_rope.ring_lib 'bowline') the knot half a metre off the bollard, its loop round the bollard's neck."""
        if name != 'rope': return pts
        d, vv, u = g['d'], g['vv'], g['u']; ground, Rb, Ye = g['ground'], g['R'], g['Ye']
        far = [p for p in pts if p.length > 1.0]
        P_ = QG.knot_path('knot-bowline'); S = 0.013 / 0.006; O = d * 0.5; O.y = 0
        up = Vector((0, 1, 0))
        Q3 = [O + vv * (x * S) + up * ((y - 0.006) * S + ground) + u * (z * S) for x, y, z in P_]
        i0, i1 = QG.BOWLINE_LOOP
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
        g['knot_at'] = O
        return _join3(list(reversed(far)), body)
    g = {'__name__': '__main__', '__file__': os.path.join(HERE, 'rope_ring.py')}
    sys.argv = ['blender', '--']
    def render(out, samples=256, scale=100, exp=-0.6, labels=(), note=None, blend='', space='three', arrows=(), extra=None):
        d, up = g['d'], Vector((0, 1, 0)); O = g.get('knot_at', d * 0.5)
        labs = [(tuple(O + up * 0.07), 'bowline: about 60% left', 'red'), (tuple(d * 1.15 + up * 0.05), '16 mm nylon: 6.0 t new')]
        _orig['render'](OUT, SAMPLES, SCALE, exp, labs, 'Working load of a tow line', '', 'three', (),
                        {'lines': ['6.0 t × 0.85 wet × 0.6 knot ÷ 5 ≈ 0.6 t']})
    C.render = render
    def three_strand(name, pts3, *a, **k):
        p = strand(g, name, pts3)
        if p is not None: _orig['three_strand'](name, p, *a, **k)
    C.three_strand = three_strand
    look = ((0.95, 1.25, -1.28), (-0.25, 0.06, -0.36), 38)
    C.camera_lookat = lambda pos3, target3, fov_y: _orig['lookat'](look[0], look[1], look[2])
    path = os.path.join(HERE, 'rope_ring.py')
    exec(compile(open(path).read(), path, 'exec'), g)
