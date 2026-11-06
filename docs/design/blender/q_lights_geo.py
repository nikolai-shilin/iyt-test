# Geometry for q_lights.py, plain Python (no bpy) so it runs in Blender and in the system Python alike:
# the pinhole camera of the renders (1280 x 800, sensor 36 mm wide), fitting a camera to the 2D figure's light
# positions, placing a vessel's lights in the world, and placing a light on the ray through a picture point.
# World: Blender space, metres, sea surface z = 0, our yacht heading north (+Y), the eye at EYE.
import math

W, H = 1280, 800
SENSOR = 36.0
EYE = (0.0, 0.0, 2.8)           # standing on our foredeck

def s_of_lens(lens): return lens / SENSOR * W            # pixels per radian at the centre
def lens_of_s(s): return s * SENSOR / W

def axes(yaw, pitch):
    """Camera axes for a compass yaw (degrees, clockwise from north) and a pitch (degrees, up +): right, up, forward."""
    a, p = math.radians(yaw), math.radians(pitch)
    d = (math.sin(a) * math.cos(p), math.cos(a) * math.cos(p), math.sin(p))
    r = (math.cos(a), -math.sin(a), 0.0)
    u = (r[1] * d[2] - r[2] * d[1], r[2] * d[0] - r[0] * d[2], r[0] * d[1] - r[1] * d[0])
    return r, u, d

def project(P, cam):
    """World point -> picture pixel (x right, y down) and depth. cam = {'yaw','pitch','s','eye'}."""
    r, u, d = axes(cam['yaw'], cam['pitch']); E = cam.get('eye', EYE)
    v = (P[0] - E[0], P[1] - E[1], P[2] - E[2])
    xc = sum(a * b for a, b in zip(v, r)); yc = sum(a * b for a, b in zip(v, u)); zc = sum(a * b for a, b in zip(v, d))
    return (W / 2 + cam['s'] * xc / zc, H / 2 - cam['s'] * yc / zc, zc)

def ray(px, py, cam):
    """The world direction through picture point (px, py)."""
    r, u, d = axes(cam['yaw'], cam['pitch'])
    x, y = (px - W / 2) / cam['s'], -(py - H / 2) / cam['s']
    v = tuple(d[i] + x * r[i] + y * u[i] for i in range(3)); n = math.sqrt(sum(c * c for c in v))
    return tuple(c / n for c in v)

def on_ray(px, py, cam, dist, z=None):
    """The point on the ray through (px, py) at horizontal distance `dist` from the eye; with z, keep its plan
    position and put it at that height instead."""
    E = cam.get('eye', EYE); v = ray(px, py, cam); hz = math.hypot(v[0], v[1]); t = dist / hz
    p = (E[0] + v[0] * t, E[1] + v[1] * t, E[2] + v[2] * t)
    return (p[0], p[1], z) if z is not None else p

def horizon_pitch(yaw, s, y_px, P, eye=EYE):
    """The pitch that puts world point P at picture row y_px (camera yawed to P's bearing or anything near)."""
    dx, dy, dz = P[0] - eye[0], P[1] - eye[1], P[2] - eye[2]
    el = math.degrees(math.atan2(dz, math.hypot(dx, dy)))
    return el + math.degrees(math.atan((y_px - H / 2) / s))

def fit(points, targets, s_fixed=None, s_range=(s_of_lens(35), s_of_lens(400)), eye=EYE, yaw0=None):
    """Least-squares camera (yaw, pitch, s) that brings world `points` to picture `targets` (pixels).
    One point: s fixed (s_fixed or a 110 mm lens), only the aim is solved."""
    cam = {'eye': eye}
    az = [math.degrees(math.atan2(p[0] - eye[0], p[1] - eye[1])) for p in points]
    ref = yaw0 if yaw0 is not None else az[0]
    az = [((a - ref + 180) % 360) - 180 + ref for a in az]
    el = [math.degrees(math.atan2(p[2] - eye[2], math.hypot(p[0] - eye[0], p[1] - eye[1]))) for p in points]
    n = len(points)
    if s_fixed is None and n >= 2:
        # small-angle start: X - 640 = k (az - yaw), Y - 400 = -k (el - pitch), k in px per degree
        ma, me = sum(az) / n, sum(el) / n; mx, my = sum(t[0] for t in targets) / n, sum(t[1] for t in targets) / n
        num = sum((a - ma) * (t[0] - mx) - (e - me) * (t[1] - my) for a, e, t in zip(az, el, targets))
        den = sum((a - ma) ** 2 + (e - me) ** 2 for a, e in zip(az, el))
        k = num / den if den > 1e-12 and num > 0 else s_of_lens(110) * math.pi / 180
        s = k * 180 / math.pi
    else:
        s = s_fixed or s_of_lens(110)
    s = min(max(s, s_range[0]), s_range[1])
    k = s * math.pi / 180
    yaw = sum(a - (t[0] - W / 2) / k for a, t in zip(az, targets)) / n
    pitch = sum(e + (t[1] - H / 2) / k for e, t in zip(el, targets)) / n
    cam.update(yaw=yaw, pitch=pitch, s=s)
    free_s = s_fixed is None and n >= 2
    def err(c):
        return sum((project(p, c)[0] - t[0]) ** 2 + (project(p, c)[1] - t[1]) ** 2 for p, t in zip(points, targets))
    # refine with the exact projection (coordinate search, small steps)
    steps = {'yaw': 0.5, 'pitch': 0.5, 's': s * 0.1}
    for _ in range(200):
        better = False
        for key in (('yaw', 'pitch', 's') if free_s else ('yaw', 'pitch')):
            for sign in (1, -1):
                c = dict(cam); c[key] += sign * steps[key]
                if key == 's': c['s'] = min(max(c['s'], s_range[0]), s_range[1])
                if err(c) < err(cam): cam = c; better = True
        if not better:
            steps = {k2: v / 2 for k2, v in steps.items()}
            if steps['yaw'] < 1e-5: break
    return cam

# ---------- vessels ----------
def vessel_frame(bearing, dist, rel_view, eye=EYE):
    """A vessel `dist` m away on relative `bearing` (our heading north), placed so that we are on her relative
    bearing `rel_view` (0 = we see her bow on, 90 = her starboard beam, 180 = her stern, -90 = her port beam).
    Returns (position, heading) in compass degrees."""
    a = math.radians(bearing)
    pos = (eye[0] + math.sin(a) * dist, eye[1] + math.cos(a) * dist, 0.0)
    heading = (bearing + 180 - rel_view) % 360
    return pos, heading

def to_world(pos, heading, p):
    """Vessel coordinates (x forward, y to port, z up, origin amidships at the waterline) -> world."""
    h = math.radians(heading)
    f = (math.sin(h), math.cos(h)); port = (-math.cos(h), math.sin(h))
    return (pos[0] + f[0] * p[0] + port[0] * p[1], pos[1] + f[1] * p[0] + port[1] * p[1], pos[2] + p[2])

def check_order(px, data, thr=8):
    """Pairs of lights whose left/right or up/down order in the render differs from the data's (where the data
    separates them by at least `thr` units of its 320 x 200 drawing). Returns a list of complaints."""
    bad = []
    for i in range(len(data)):
        for j in range(i + 1, len(data)):
            dx, dy = data[j][0] - data[i][0], data[j][1] - data[i][1]
            rx, ry = px[j][0] - px[i][0], px[j][1] - px[i][1]
            if abs(dx) >= thr and dx * rx <= 0: bad.append(f'x-order {i}-{j}: data {dx:+.0f} render {rx:+.0f}px')
            if abs(dy) >= thr and dy * ry <= 0: bad.append(f'y-order {i}-{j}: data {dy:+.0f} render {ry:+.0f}px')
    return bad
