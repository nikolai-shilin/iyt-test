# Lays out a q_lights scene from its spec (q_lights_specs.py) and the 2D figure's lights: the camera and every
# light's world position. Plain Python (q_lights_geo), so the dry check runs without Blender.
import math
import q_lights_geo as G

def target(l): return (l['x'] * 4.0, l['y'] * 4.0)   # the 320 x 200 drawing -> the 1280 x 800 picture

def layout(sp, lights):
    k = sp['kind']
    if k == 'vessel': return vessel(sp, lights)
    if k in ('screen', 'diptych'): return screen(sp, lights)
    return None

def vessel(sp, lights):
    s_t = G.s_of_lens(sp.get('lens', 110))
    D = sp.get('dist', 150.0); fixed = 'dist' in sp
    idx = list(sp['lights']) + (list(sp['tow']['lights']) if sp.get('tow') else [])
    tg = [target(lights[i]) for i in idx]
    for it in range(6):
        pos, hdg = G.vessel_frame(sp['bearing'], D, sp['R'])
        pts = {i: G.to_world(pos, hdg, p) for i, p in sp['lights'].items()}
        vessels = [dict(pos=pos, heading=hdg, hull=sp.get('hull'), deck=sp.get('deck', False))]
        if sp.get('tow'):
            t = sp['tow']; a = math.radians(sp['bearing'])
            fwd, right = (math.sin(a), math.cos(a)), (math.cos(a), -math.sin(a))
            tpos = (pos[0] + right[0] * t['right'] + fwd[0] * t['beyond'], pos[1] + right[1] * t['right'] + fwd[1] * t['beyond'], 0.0)
            tb = math.degrees(math.atan2(tpos[0] - G.EYE[0], tpos[1] - G.EYE[1]))
            th = (tb + 180 - t['R']) % 360
            pts.update({i: G.to_world(tpos, th, p) for i, p in t['lights'].items()})
            vessels.append(dict(pos=tpos, heading=th, hull=t.get('hull'), deck=False))
        P = [pts[i] for i in idx]
        if fixed or len(P) == 1:
            cam = G.fit(P, tg, s_fixed=s_t, yaw0=sp['bearing']); break
        cam = G.fit(P, tg, yaw0=sp['bearing'])
        if abs(cam['s'] / s_t - 1) < 0.03: break
        D = min(max(D * s_t / cam['s'], 20.0), 4000.0)
    return dict(cam=cam, points=pts, dist=D, vessels=vessels)

def screen(sp, lights):
    s = G.s_of_lens(sp.get('lens', 50)); eye = (0.0, 0.0, sp.get('eye', G.EYE[2]))
    ai, ad, az = sp['anchor']; b = math.radians(sp.get('bearing', 0))
    Pa = (eye[0] + math.sin(b) * ad, eye[1] + math.cos(b) * ad, az)
    tx, ty = target(lights[ai])
    cam = dict(eye=eye, s=s, yaw=sp.get('bearing', 0) - math.degrees(math.atan((tx - G.W / 2) / s)), pitch=0.0)
    for _ in range(6):   # aim so the anchor light sits exactly on its point
        cam['pitch'] = G.horizon_pitch(cam['yaw'], s, ty, Pa, eye)
        px, py, _ = G.project(Pa, cam)
        cam['yaw'] += math.degrees(math.atan((px - tx) / s))
    cam['pitch'] = G.horizon_pitch(cam['yaw'], s, ty, Pa, eye)
    pts = {ai: Pa}
    at = sp.get('at', {}); dflt = sp.get('dist', ad)
    for i, l in enumerate(lights):
        if i == ai and i not in at: continue
        a = at.get(i, dflt); d, z = (a if isinstance(a, tuple) else (a, None))
        pts[i] = G.on_ray(*target(l), cam, d, z)
    return dict(cam=cam, points=pts, dist=ad, vessels=[])
