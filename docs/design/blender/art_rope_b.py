# Ropework article (bareboat-skipper/ropework), the knot tiles redrawn after a reviewer's notes (2026-11-11):
#   --fig 2   round turn and two half hitches on a post: the half hitches now wrap round the standing part
#             (together they are a clove hitch on it), instead of lying as flat loops beside it
#   --fig 4   sheet bend: a bight in the thick line; the thin line comes up through it, round behind both legs and
#             tucks under itself, so both short ends lie on the same side (the old drawing left the end loose in the bight)
# The deck and the post are the exported scenes knot-roundturn / knot-sheetbend (scenes/*.glb); only the ropes are new.
# Knot units as in figure-rope-3d.html: 1 unit = KS metres, plan x right, plan y up the page, h above the deck.
#   blender --background --factory-startup --python docs/design/blender/art_rope_b.py -- --fig 2 [--out x.jpg] [--samples 256]
import os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import common as C, kit as K

arg = C.cli()
FIG = arg('--fig', 2); SAMPLES = arg('--samples', 256); SCALE = arg('--scale', 100)
ART = os.path.join(HERE, '..', 'figure-style', 'articles', 'bareboat-skipper', 'ropework')
OUT = arg('--out', os.path.join(ART, f'{FIG}-3d.jpg'))
KS = 0.012
pi = math.pi

def T(x, y, h):
    """Knot units (plan x, plan y, height) -> Three.js space, as the exported scenes use it."""
    return [x * KS, h * KS, -y * KS]

def wrap(x0, x1, f0, f1, rho, off=lambda u: 0.0, n=16):
    """Round a cylinder (figure-rope-3d.html wrapPts): x along its axis, f the angle round it, rho the radius."""
    return [(x0 + (x1 - x0) * i / n, f0 + (f1 - f0) * i / n, rho + off(i / n)) for i in range(n + 1)]

def join(*parts):
    out = []
    for p in parts: out += p[1:] if out else p
    return out

# ---------------- fig 2: round turn and two half hitches ----------------
def round_turn():
    R, rr, Y = 0.5, 4.5, -4.5          # rope radius; round-turn radius on the post (radius 4); the standing part's line
    rho, X0, sx = 1.3, 13.0, 2.0        # half hitches: radius round the standing part, centre, spacing along it
    def hs(x):                          # the standing part: off the post low, lifted a little where the hitches choke it
        if x < 8: return 1.2 + 0.6 * max(0.0, x) / 8
        if x < 26: return 1.8
        return max(R, 1.8 - (x - 26) * 0.12)
    sp = [(x, Y, hs(x)) for x in (38, 34, 30, 26, 22, 18, 14, 10, 6, 3, 0.6)]
    # the round turn: 1.75 turns down round the post, climbing one rope diameter a turn
    turns = 1.75; th0, th1 = -pi / 2, -pi / 2 - turns * 2 * pi; h0, h1 = 1.2, 1.2 + turns * 1.0
    helix = [(rr * math.cos(th0 + (th1 - th0) * k / 40), rr * math.sin(th0 + (th1 - th0) * k / 40), h0 + (h1 - h0) * k / 40) for k in range(1, 41)]
    # two half hitches = a clove hitch round the standing part (the clove of figure-rope-3d.html's rail, its first turn
    # nearest the post). In the clove's frame f = -pi/2 is the side the end arrives on (here the post's side,
    # plan +y), f = 0 the top, f = +pi/2 the far side, f = pi underneath.
    def P(xl, f, r):
        return (X0 + xl * sx, Y - r * math.sin(f), hs(X0) + r * math.cos(f))
    clove = join(
        wrap(-1.2, 1.2, -pi / 2, pi / 2, rho),
        wrap(1.2, 1.2, pi / 2, 3 * pi / 2, rho),
        wrap(1.2, -1.2, 3 * pi / 2, 5 * pi / 2, rho, lambda u: 1.05 * math.sin(pi * u) ** 0.6),
        wrap(-1.2, -2.4, 5 * pi / 2, 7 * pi / 2, rho),
        wrap(-2.4, 0.0, 7 * pi / 2, 4 * pi + 0.42 * pi, rho))
    hitch = [P(*q) for q in clove]
    # the end off the post, straight into the first turn
    approach = [(5.0, 0.5, 2.0), (5.6, -0.9, 1.7), (X0 - 1.2 * sx - 1.0, Y + rho + 1.0, hs(X0) + 0.2)]
    # the end out of the clove (far side, up), then down onto the deck, pointing on along the standing part
    tail = [(X0 + 0.25 * sx, Y - rho - 1.2, hs(X0) + 1.4), (X0 + 0.5 * sx, Y - rho - 2.2, hs(X0) + 1.5),
            (X0 + 2.5, Y - rho - 3.4, 1.0), (X0 + 5.5, Y - rho - 3.9, R), (X0 + 8.0, Y - rho - 4.0, R)]
    pts = sp + helix + approach + hitch + tail
    labels = [(T(-3.2, -3.2, 2.6), 'round turn'), (T(30, Y, 1.6), 'standing part'),
              (T(X0, Y, hs(X0) + rho + 0.6), 'two half hitches'), (T(X0 + 8.0, Y - rho - 4.0, R), 'end')]
    cam = (T(9.5, -27.0, 24.0), T(8.5, -3.0, 1.0), 34)
    return [pts], labels, 'Round turn and two half hitches', cam

# ---------------- fig 4: sheet bend ----------------
def sheet_bend():
    Rk, Rn = 0.625, 0.375               # thick, thin rope radii
    lift = 2 * Rn                       # how far the thick line rises where the thin passes under it
    xc = -2.8                           # where the thin line's collar passes behind both legs
    def hk(x, y):                       # the thick line's height: on the deck, lifted over the thin line
        h = Rk
        for cx, cy in ((3.5, 0.2), (xc, 2.0), (xc, -2.0)):
            d = math.hypot(x - cx, y - cy); h += lift * max(0.0, 1 - d / 2.2) ** 2 * (3 - 2 * max(0.0, 1 - d / 2.2)) if d < 2.2 else 0
        return h
    # the thick line's bight: standing part top left, the bend round at x = 3.5, its end bottom left (black whipping)
    thick2 = [(-17, 2.0), (-12, 2.0), (-8, 2.0), (-5, 2.0), (xc, 2.0), (-1, 2.02), (0.5, 2.0), (2.2, 1.75), (3.2, 1.0), (3.5, 0.2),
              (3.2, -0.8), (2.2, -1.75), (0.5, -2.0), (-1, -2.02), (xc, -2.0), (-5, -2.0), (-7, -2.0), (-9, -2.0)]
    thick = [(x, y, hk(x, y)) for x, y in thick2]
    over = Rk + Rn + Rk + 0.02           # the thin line's centre where it lies over the thick line
    thin = [(17, 0.2, Rn), (12, 0.2, Rn), (8, 0.2, Rn), (5.2, 0.2, Rn), (3.5, 0.2, Rn),       # under the bend of the bight
            (2.4, 0.1, 0.8), (1.5, -0.1, 1.25), (0.6, -0.45, 1.45),                            # up through the bight
            (-0.2, -1.2, 1.5), (-1.0, -2.0, over), (-1.7, -2.75, 1.2), (-2.4, -3.1, 0.6),        # over the end leg ...
            (xc, -2.9, Rn), (xc - 0.15, -2.0, Rn), (xc - 0.2, 0.0, Rn), (xc - 0.15, 2.0, Rn),   # ... round behind both legs
            (xc, 2.9, Rn), (-2.4, 3.1, 0.6), (-1.7, 2.75, 1.2), (-1.0, 2.0, over),               # ... over the standing leg
            (-0.6, 1.0, 0.9), (-0.25, 0.0, 0.5), (0.15, -0.86, Rn + 0.05),                       # under itself (its own diagonal)
            (0.5, -1.6, 0.9), (0.6, -2.0, over), (0.6, -2.9, 1.0), (0.0, -3.8, 0.6),             # out over the end leg
            (-1.8, -4.3, Rn), (-4.5, -4.4, Rn), (-7.0, -4.3, Rn)]                               # the end beside the thick end
    labels = [(T(-14, 2.0, 1.0), 'thick line'), (T(13, 0.2, 0.6), 'thin line'), (T(-6.0, -3.2, 1.0), 'ends together')]
    cam = (T(-0.5, -15.0, 25.0), T(-1.0, -0.6, 0.5), 34)
    return [thick, thin], labels, 'Sheet bend', cam

SCENE = {2: ('knot-roundturn', round_turn), 4: ('knot-sheetbend', sheet_bend)}[FIG]
ropes, labels, note, (cpos, ctgt, fov) = SCENE[1]()
C.reset()
d = C.load_exported(os.path.join(HERE, 'scenes', SCENE[0]), rope_fn=lambda i, P: [T(*q) for q in ropes[i]])
C.sky(d['sun']['pos'], d['sun']['target'], 0.22)
K.darken_visible_sky()
cam = C.camera_lookat(cpos, ctgt, fov)
C.focus_on_centre(cam, 16.0)
C.render(OUT, SAMPLES, SCALE, -0.6, labels, note)
