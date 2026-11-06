# Geometry helpers for the rope question images (q_rope.py): quay rings, chain, a sheet block, a rope clutch,
# knot centrelines (exported from the Three.js knot figures) bent onto bollards and rings, a clove hitch on a post.
# Blender space unless a name says Three (common.B maps Three.js (x, y, z) to Blender (x, -z, y)).
import os, math, json
import bpy, bmesh
from mathutils import Vector, Matrix
import common as C

HERE = os.path.dirname(os.path.abspath(__file__))
SCENES = os.path.join(HERE, 'scenes')

def V(x, y, z): return Vector((x, y, z))
def T3(P): return [C.V3((p.x, p.z, -p.y)) for p in P]          # Blender points -> Three.js points for common.*
def B3(P): return [C.B(*p) for p in P]                           # Three.js tuples -> Blender Vectors

def knot_path(name, i=0):
    """The centreline of an exported knot (Three.js space, R 0.006 braid) as tuples."""
    with open(os.path.join(SCENES, name + '.json')) as f: d = json.load(f)
    return [tuple(p) for p in d['ropes'][i]['P']]

def tubeP(name, P, r, mat, radial=16):
    return C.tube(name, [Vector(p) for p in P], r, radial, 1.0, mat)

def catenary(a, b, sag, n=24):
    return [a.lerp(b, i / n) - V(0, 0, sag * math.sin(math.pi * i / n)) for i in range(n + 1)]

def smooth_join(A, Bp, n=6):
    """Points easing from the end of path A to the start of path Bp (both Blender), excluding the ends."""
    a, b = A[-1], Bp[0]
    ta = (A[-1] - A[-2]).normalized() if len(A) > 1 else (b - a).normalized()
    tb = (Bp[1] - Bp[0]).normalized() if len(Bp) > 1 else (b - a).normalized()
    L = (b - a).length
    out = []
    for i in range(1, n):
        t = i / n
        h00, h10, h01, h11 = 2 * t**3 - 3 * t**2 + 1, t**3 - 2 * t**2 + t, -2 * t**3 + 3 * t**2, t**3 - t**2
        out.append(a * h00 + ta * (L * h10) + b * h01 + tb * (L * h11))
    return out

# ---------- metalwork ----------
def galv(): return C.galv_mat('q-galv')

def quay_ring(hinge, toward, R=0.10, r=0.013, lift=22.0, mat=None):
    """A mooring ring hinged in a staple on the quay top at `hinge`, lifted `lift` degrees towards `toward`
    (a horizontal direction). Returns a dict: tip (the bar farthest from the hinge), ex (the tip bar's axis),
    out (from the tip outwards, in the ring's plane), n (the ring plane's normal, upwards), r (bar radius)."""
    mat = mat or galv()
    t = Vector((toward.x, toward.y, 0)).normalized(); ex = Vector((-t.y, t.x, 0))
    a = math.radians(lift); out = t * math.cos(a) + V(0, 0, math.sin(a)); n = ex.cross(out).normalized()
    if n.z < 0: n = -n
    c = hinge + out * R + V(0, 0, r)
    ring = [c + (out * math.cos(k / 64 * math.tau) + ex * math.sin(k / 64 * math.tau)) * R for k in range(65)]
    tubeP('quay-ring', ring, r, mat, 20)
    # the staple: a low bridge over the ring's back, its feet leaded into the stone
    b0 = hinge - out * 0.0 + V(0, 0, 0.0)
    st = [b0 + ex * (-0.05) + V(0, 0, -0.01), b0 + ex * (-0.045) + V(0, 0, 0.028), b0 + ex * (-0.02) + V(0, 0, 0.036), b0 + ex * 0.02 + V(0, 0, 0.036), b0 + ex * 0.045 + V(0, 0, 0.028), b0 + ex * 0.05 + V(0, 0, -0.01)]
    tubeP('staple', C.catmull_centripetal(st, 10), 0.011, mat, 16)
    for s in (-1, 1):
        C.cyl('staple-lead', 0.022, 0.022, 0.006, 24, C.simple('lead', '#6d6f72', 0.6, 0.3), b0 + ex * (0.05 * s) + V(0, 0, 0.0))
    return {'tip': c + out * R, 'ex': ex, 'out': out, 'n': n, 'r': r, 'c': c, 'hinge': hinge}

def u_round_bar(ring, Rr, a0=55.0, a1=305.0, steps=14, spread=1.0):
    """A rope bight round the ring's tip bar: from above-outside, through the ring, out underneath.
    Angles from `out` towards `n`. The two legs are spread along the bar by about one rope diameter."""
    rho = ring['r'] + Rr; T = ring['tip']; o, n, ex = ring['out'], ring['n'], ring['ex']
    pts = []
    for k in range(steps + 1):
        f = k / steps; a = math.radians(a0 + (a1 - a0) * f)
        pts.append(T + (o * math.cos(a) + n * math.sin(a)) * rho + ex * ((f - 0.5) * 2.2 * Rr * spread))
    return pts

def chain(P, link_len=0.05, wire=0.0065, mat=None, start_upright=True):
    """Short-link chain lying along points P (Blender): alternate links flat and on edge."""
    mat = mat or galv()
    dense = C.catmull_centripetal([Vector(p) for p in P], 16)
    pts, L = C.spaced(dense, max(2, int(sum((b - a).length for a, b in zip(dense, dense[1:])) / (link_len * 0.78))))
    a_ = link_len / 2 + wire * 0.3; b_ = link_len * 0.34       # centreline half-length and half-width (links overlap)
    for i in range(len(pts) - 1):
        p, q = pts[i], pts[i + 1]; c = (p + q) / 2; d = (q - p).normalized()
        flat = (i % 2 == 0) != start_upright
        side = d.cross(V(0, 0, 1)).normalized() if flat else V(0, 0, 1)
        ring = []
        st = a_ - b_                                            # a stadium: two half circles joined by straights
        for k in range(48):
            t = k / 48 * math.tau; x, y = math.cos(t) * b_, math.sin(t) * b_
            x += st if math.cos(t) >= 0 else -st
            ring.append(c + d * x + side * y)
        ring.append(ring[0])
        lift = V(0, 0, wire + (0 if flat else b_ - wire * 0.2))
        tubeP(f'link{i}', [r + lift for r in ring], wire, mat, 12)
    return pts

def block(at, heading, sheave_r=0.032, mat=None):
    """A single sheet block on a deck car: two cheeks, the sheave, a pin and a shackle to the car. heading:
    the direction the sheave's plane points along (horizontal Vector). Returns the sheave centre."""
    cheek = C.simple('block-cheek', '#151618', 0.35, 0.2, coat=0.6)
    steel = C.simple('block-steel', '#cfd2d4', 0.2, 1.0)
    sheave = C.simple('block-sheave', '#3a3d42', 0.4, 0.3)
    h = Vector((heading.x, heading.y, 0)).normalized(); ax = V(-h.y, h.x, 0)
    ang = math.atan2(h.y, h.x)
    car = C.obj('car', C.rbox('car', (0.11, 0.05, 0.022), 0.008, 3), steel, at + V(0, 0, 0.011)); car.rotation_euler.z = ang
    c = at + V(0, 0, 0.022 + 0.012 + sheave_r + 0.008)
    for s in (-1, 1):
        o = C.cyl('cheek', sheave_r + 0.011, sheave_r + 0.011, 0.007, 48, cheek, c + ax * (s * 0.0135))
        o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = ax.to_track_quat('Z', 'Y')
    o = C.cyl('sheave', sheave_r, sheave_r, 0.019, 48, sheave, c); o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = ax.to_track_quat('Z', 'Y')
    o = C.cyl('pin', 0.006, 0.006, 0.036, 16, steel, c); o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = ax.to_track_quat('Z', 'Y')
    # the swivel down to the car
    C.cyl('swivel', 0.008, 0.008, 0.03, 16, steel, at + V(0, 0, 0.034))
    return c, ax, h

def clutch(at, heading, length=0.13, mat=None):
    """A rope clutch on the coachroof: a black body the line runs through, its cam lever down (closed)."""
    body = C.simple('clutch-body', '#141517', 0.4, 0.2, coat=0.5)
    alu = C.simple('clutch-alu', '#c4c8cc', 0.32, 1.0)
    h = Vector((heading.x, heading.y, 0)).normalized(); ang = math.atan2(h.y, h.x)
    o = C.obj('clutch', C.rbox('clutch', (length, 0.05, 0.05), 0.012, 4), body, at + V(0, 0, 0.025)); o.rotation_euler.z = ang
    o = C.obj('clutch-base', C.rbox('clutch-base', (length + 0.02, 0.06, 0.008), 0.003, 2), alu, at + V(0, 0, 0.004)); o.rotation_euler.z = ang
    # the lever: lying back along the top, closed
    lv = C.obj('clutch-lever', C.rbox('clutch-lever', (length * 0.95, 0.034, 0.012), 0.006, 3), C.simple('clutch-lever', '#c8161d', 0.4, coat=0.6), at + h * (-0.005) + V(0, 0, 0.056))
    lv.rotation_euler.z = ang; lv.rotation_euler.y = 0.0
    return at + V(0, 0, 0.025)

# ---------- knots bent onto fittings ----------
BOWLINE_LOOP = (138, 252)   # indices of the big loop in knot-bowline's centreline

def place_knot(P3, origin, ax_x, ax_y, ax_z, s, y0=0.006):
    """Three.js knot points (lying on y = y0) -> Blender: file x along ax_x, file y (height) along ax_y, file z along ax_z."""
    return [origin + ax_x * (x * s) + ax_y * ((y - y0) * s) + ax_z * (z * s) for x, y, z in P3]

def clove_on_post(centre, toward, r_turn=0.15, y0=0.17, pitch=0.075, Rr=0.013, loose=1.0):
    """A clove hitch round a vertical post at `centre` (base point; y0.. heights above it), the standing part
    leaving towards `toward` (horizontal). Two turns, the second crossing the first, the end tucked under the
    second and hanging out. `loose` > 1 opens it up. Returns (standing-side start, points, end points)."""
    t = Vector((toward.x, toward.y, 0)).normalized(); s = V(-t.y, t.x, 0)
    th0 = math.atan2(t.y, t.x)
    def at(th, z, r): return centre + V(math.cos(th) * r, math.sin(th) * r, z)
    pts = []
    rr = r_turn * loose
    # turn 1: from the standing part (on the post's toward side) round, rising
    N = 40
    for k in range(N + 1):
        f = k / N; th = th0 + math.radians(-80 + 360 * f); pts.append(at(th, y0 + pitch * f * 0.9 + 0.01 * math.sin(f * math.pi), rr * (1.0 + 0.04 * math.sin(f * math.pi * 2))))
    # turn 2: crossing over the standing part, a full turn higher
    for k in range(1, N + 1):
        f = k / N; th = th0 + math.radians(280 + 360 * f); pts.append(at(th, y0 + pitch * (0.9 + f * 0.85), rr * (1.03 + 0.03 * math.sin(f * math.pi))))
    # the end: tucked under the second turn, out between the turns, then hanging
    end = []
    for k in range(1, 9):
        f = k / 8; th = th0 + math.radians(640 + 70 * f); end.append(at(th, y0 + pitch * (1.75 - 0.75 * f), rr * (1.03 - 0.06 * math.sin(f * math.pi))))
    return pts, end
