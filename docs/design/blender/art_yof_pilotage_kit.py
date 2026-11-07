# Shared parts for the Yachtmaster Offshore renders of art_yof_pilotage.py, art_yof_tides.py and art_yof_weather.py,
# on top of common.py, kit.py and the Charter Check-in helpers of art_checkin_nps_kit.py (image planes, sheets of
# paper, the Raymarine Axiom with a drawn screen, rings and strips on the water): the textures of each article from
# its art_yof_<article>_tex.py, a chart table, the cloudy sky and the sailing yacht of art_weather_a.py, land raised
# from polygons, foam patches for breaking water. Blender space, Z up, metres, sea at z = 0.
import os, sys, math, json, subprocess, random
import bpy, bmesh
import numpy as np
from mathutils import Vector, noise as mnoise
import common as C, kit as K, kit_instruments as KI, kit_world as KW
from common import lin
from art_checkin_nps_kit import (quad, sheet, on_sheet, plotter, screen_point, glow_mat, ring, strip, drone, hdg_vec, lamp,
                                 yacht, sphere, rod, emit_mat, shift_px, to_px, torus)

HERE = os.path.dirname(os.path.abspath(__file__))
ARTS = os.path.join(HERE, '..', 'figure-style', 'articles', 'yachtmaster-offshore')
deg = math.radians

def outdir(article): return os.path.join(ARTS, article)

def tex(article, name, ext='.png'):
    """tex/<name>.png of the article, drawn by art_yof_<article>_tex.py if missing (or with --retex)."""
    d = os.path.join(outdir(article), 'tex'); p = os.path.join(d, name + ext)
    if not os.path.exists(p) or '--retex' in sys.argv:
        subprocess.run(['python3', os.path.join(HERE, f'art_yof_{article}_tex.py'), d, name], check=True)
    return p

def anchors(article, name):
    return json.load(open(os.path.join(outdir(article), 'tex', name + '.json')))

def px_on(o, a, size):
    """World point of pixel a = (x, y) of an image of `size` (w, h) laid on the sheet/quad o."""
    return on_sheet(o, a[0] / size[0], 1 - a[1] / size[1], 0.003)

# ---------- the chart table ----------
def chart_table(night=False, w=1.1, d=0.75, light=1.0):
    """A varnished chart table at z = 0 with its fiddles and a bulkhead behind; a warm dome light and a portlight by
    day, a dim red lamp at night."""
    jo = KI.joinery_mat()
    C.obj('table', C.rbox('table', (w, d, 0.04), 0.006, 2), jo, (0.0, 0.0, -0.02))
    C.obj('fiddle-front', C.rbox('fiddle', (w, 0.025, 0.035), 0.008, 2), jo, (0.0, -d / 2 + 0.01, 0.015))
    C.obj('fiddle-back', C.rbox('fiddle', (w, 0.025, 0.06), 0.008, 2), jo, (0.0, d / 2 + 0.02, 0.03))
    KI.wall('bulkhead', -w, w, -0.05, 0.7, d / 2 + 0.035, jo)
    if night:
        K.night_sky(moon=0.001, stars=False)
        KI.area_light((0.1, -0.1, 0.6), (0.0, 0.0, 0.0), 2.2 * light, 0.25, (1.0, 0.16, 0.08))
        KI.area_light((-0.5, -0.4, 0.5), (0.0, 0.0, 0.0), 0.5 * light, 0.4, (0.9, 0.3, 0.25))
    else:
        K.day_sky(sun_az=200, sun_el=40, strength=0.05)
        KI.area_light((0.0, -0.15, 0.9), (0.0, 0.0, 0.0), 12 * light, 0.35, (1.0, 0.86, 0.68))
        KI.area_light((0.9, -0.3, 0.45), (0.0, 0.05, 0.0), 16 * light, 0.4, (0.85, 0.92, 1.0))

def book(name, w, h, t, cover, loc, rotz, pages='#ece6d4'):
    """A closed book lying flat: a block of pages and the cover image on top."""
    o = C.obj(name + '-block', C.rbox(name, (w, h, t), 0.003, 2), C.simple(name + '-pages', pages, 0.8), (loc[0], loc[1], loc[2] + t / 2))
    o.rotation_euler = (0, 0, deg(rotz))
    return quad(name, w * 1.01, h * 1.01, cover, (loc[0], loc[1], loc[2] + t + 0.0006), rot=(0, 0, deg(rotz)), rough=0.5)

def pencil(at, rotz, z=0.004):
    a = deg(rotz)
    C.cyl('pencil', 0.0042, 0.0042, 0.17, 6, C.simple('pencil', '#e8b818', 0.45, coat=0.4), (at[0], at[1], z), (0, deg(90), a))
    tip = Vector((at[0] + math.cos(a) * 0.085, at[1] + math.sin(a) * 0.085, z))
    rod('pencil-tip', tip, tip + Vector((math.cos(a) * 0.016, math.sin(a) * 0.016, -0.002)), 0.0042, 0.0006, C.simple('wood', '#d9b482', 0.7))

def dividers(p0, p1, lift=0.10, side=Vector((0.06, -0.08, 0))):
    """Brass dividers with their points at p0 and p1 on the chart."""
    steel = C.simple('divider-steel', '#c9ccd0', 0.22, 1.0); brass = C.simple('brass', '#b08a3e', 0.28, 1.0)
    p0, p1 = Vector(p0), Vector(p1); hinge = (p0 + p1) / 2 + side + Vector((0, 0, lift))
    for nm, p in (('a', p0), ('b', p1)):
        q = p + (hinge - p).normalized() * 0.018
        rod('point-' + nm, p, q, 0.0006, 0.0022, steel); rod('leg-' + nm, q, hinge, 0.0028, 0.0075, brass)
    C.cyl('hinge', 0.009, 0.009, 0.012, 24, brass, hinge, (deg(90), 0, 0))

# ---------- the sea and the sky ----------
def compass(az, el, dist=3000.0, c=Vector((0, 0, 0))):
    a, e = deg(az), deg(el)
    return Vector(c) + Vector((math.sin(a) * math.cos(e), math.cos(a) * math.cos(e), math.sin(e))) * dist

def cloud_sky(zenith, horizon, dark, light, cover=0.5, sharp=0.12, scale=2.2, boost=None, sun=(200, 35, 3.0),
              strength=1.0, haze=0.12, seed=3.0, wall=None, shade_scale=3.3):
    """art_weather_a.cloud_sky: a gradient sky with a projected cloud layer, piled up (boost) or walled (wall)
    towards a bearing; sun (az, el, energy) adds a sun lamp without a disc."""
    sc = bpy.context.scene; w = bpy.data.worlds.new('clouds'); sc.world = w
    nt = w.node_tree; nt.nodes.clear(); N = nt.nodes.new; L = nt.links.new
    def mth(op, a, b=None, c=None):
        n = N('ShaderNodeMath'); n.operation = op
        for i, v in enumerate((a, b, c)):
            if v is None: continue
            if isinstance(v, (int, float)): n.inputs[i].default_value = v
            else: L(v, n.inputs[i])
        return n.outputs[0]
    def mr(v, a, b, c=0.0, d=1.0):
        n = N('ShaderNodeMapRange'); n.clamp = True; L(v, n.inputs['Value'])
        for k, x in (('From Min', a), ('From Max', b), ('To Min', c), ('To Max', d)):
            if isinstance(x, (int, float)): n.inputs[k].default_value = x
            else: L(x, n.inputs[k])
        return n.outputs['Result']
    def mix(f, a, b):
        n = N('ShaderNodeMix'); n.data_type = 'RGBA'
        for s, v in ((n.inputs['Factor'], f), (n.inputs[6], a), (n.inputs[7], b)):
            if isinstance(v, (int, float, tuple)): s.default_value = v
            else: L(v, s)
        return n.outputs[2]
    tc = N('ShaderNodeTexCoord'); sp = N('ShaderNodeSeparateXYZ'); L(tc.outputs['Generated'], sp.inputs['Vector'])
    dx, dy, dz = sp.outputs['X'], sp.outputs['Y'], sp.outputs['Z']
    adz = mth('ADD', mth('ABSOLUTE', dz), 0.13)
    u, v = mth('DIVIDE', dx, adz), mth('DIVIDE', dy, adz)
    cv = N('ShaderNodeCombineXYZ'); L(u, cv.inputs['X']); L(v, cv.inputs['Y']); cv.inputs['Z'].default_value = seed
    n1 = N('ShaderNodeTexNoise'); n1.inputs['Scale'].default_value = scale; n1.inputs['Detail'].default_value = 9; n1.inputs['Roughness'].default_value = 0.62
    L(cv.outputs[0], n1.inputs['Vector'])
    n2 = N('ShaderNodeTexNoise'); n2.inputs['Scale'].default_value = scale * shade_scale; n2.inputs['Detail'].default_value = 6; L(cv.outputs[0], n2.inputs['Vector'])
    cov = cover; dk = 0.0
    if boost:
        az, spread, extra, xdark = boost
        a = deg(az); hl = mth('SQRT', mth('ADD', mth('MULTIPLY', dx, dx), mth('MULTIPLY', dy, dy)), None)
        dot = mth('DIVIDE', mth('ADD', mth('MULTIPLY', dx, math.sin(a)), mth('MULTIPLY', dy, math.cos(a))), mth('ADD', hl, 1e-4))
        wgt = mr(dot, math.cos(deg(spread)), 1.0)
        low = mr(dz, 0.45, 0.02)
        wgt = mth('MULTIPLY', wgt, mth('ADD', mth('MULTIPLY', low, 0.7), 0.3))
        cov = mth('ADD', cover, mth('MULTIPLY', wgt, extra)); dk = mth('MULTIPLY', wgt, xdark)
    lo_ = mth('SUBTRACT', 0.66, mth('MULTIPLY', cov, 0.36)) if not isinstance(cov, float) else 0.66 - cov * 0.36
    mask = mr(n1.outputs['Fac'], lo_, mth('ADD', lo_, sharp) if not isinstance(lo_, float) else lo_ + sharp)
    mask = mth('MULTIPLY', mask, mr(mth('ABSOLUTE', dz), 0.0, haze, 0.55, 1.0))
    shade = mix(n2.outputs['Fac'], lin(dark), lin(light))
    if not isinstance(dk, float): shade = mix(dk, shade, (0.012, 0.014, 0.018, 1))
    grad = mix(mr(dz, 0.0, 0.55), lin(horizon), lin(zenith))
    col = mix(mask, grad, shade)
    if wall:
        az, spread, top, wcol = wall
        a = deg(az); hl = mth('SQRT', mth('ADD', mth('MULTIPLY', dx, dx), mth('MULTIPLY', dy, dy)))
        dot = mth('DIVIDE', mth('ADD', mth('MULTIPLY', dx, math.sin(a)), mth('MULTIPLY', dy, math.cos(a))), mth('ADD', hl, 1e-4))
        wa = mr(dot, math.cos(deg(spread)), math.cos(deg(spread * 0.55)))
        ev = N('ShaderNodeCombineXYZ'); L(mth('MULTIPLY', dx, 4.5), ev.inputs['X']); L(mth('MULTIPLY', dy, 4.5), ev.inputs['Y']); ev.inputs['Z'].default_value = seed + 5
        en = N('ShaderNodeTexNoise'); en.inputs['Scale'].default_value = 1.0; en.inputs['Detail'].default_value = 3; en.inputs['Roughness'].default_value = 0.5; L(ev.outputs[0], en.inputs['Vector'])
        h = mth('MULTIPLY', mth('MULTIPLY', wa, top), mth('ADD', mth('MULTIPLY', en.outputs['Fac'], 0.9), 0.45))
        wm = mr(mth('SUBTRACT', h, dz), -0.006, 0.02)
        wm = mth('MULTIPLY', wm, mr(dz, -0.25, -0.02))
        bv = N('ShaderNodeCombineXYZ'); L(mth('MULTIPLY', dx, 16.0), bv.inputs['X']); L(mth('MULTIPLY', dy, 16.0), bv.inputs['Y']); L(mth('MULTIPLY', dz, 40.0), bv.inputs['Z'])
        bn = N('ShaderNodeTexNoise'); bn.inputs['Scale'].default_value = 1.0; bn.inputs['Detail'].default_value = 6; bn.inputs['Roughness'].default_value = 0.55; L(bv.outputs[0], bn.inputs['Vector'])
        up = mr(mth('DIVIDE', dz, mth('ADD', h, 1e-3)), 0.25, 1.0)
        body = mix(up, lin(wcol), lin('#5d636b'))
        body = mix(mth('MULTIPLY', mr(bn.outputs['Fac'], 0.4, 0.75), 0.55), body, lin('#8d939a'))
        rv = N('ShaderNodeCombineXYZ'); L(mth('MULTIPLY', dx, 22.0), rv.inputs['X']); L(mth('MULTIPLY', dy, 22.0), rv.inputs['Y']); L(mth('MULTIPLY', dz, 1.5), rv.inputs['Z'])
        rn = N('ShaderNodeTexNoise'); rn.inputs['Scale'].default_value = 1.0; rn.inputs['Detail'].default_value = 2; L(rv.outputs[0], rn.inputs['Vector'])
        rain = mth('MULTIPLY', mr(rn.outputs['Fac'], 0.4, 0.75), mr(up, 0.4, 0.0))
        body = mix(mth('MULTIPLY', rain, 0.4), body, lin('#5a6169'))
        col = mix(wm, col, body)
    bg = N('ShaderNodeBackground'); bg.inputs['Strength'].default_value = strength; L(col, bg.inputs['Color'])
    out = N('ShaderNodeOutputWorld'); L(bg.outputs[0], out.inputs['Surface'])
    if sun:
        az, el, en = sun
        ld = bpy.data.lights.new('sun', 'SUN'); ld.energy = en; ld.angle = deg(8 if en < 1.5 else 1.5); ld.color = (1.0, 0.96, 0.9)
        lo = bpy.data.objects.new('sun', ld); C.col.objects.link(lo)
        d = Vector((math.sin(deg(az)) * math.cos(deg(el)), math.cos(deg(az)) * math.cos(deg(el)), math.sin(deg(el))))
        lo.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    sc['exposure_offset'] = 0.0

def sailing(name, hdg, wind, x, y, reef=0.0, heel=None, scale=1.0):
    """art_weather_a.sailing: a yacht under sail, boom and genoa to leeward; reef 0..1 shortens the main and genoa."""
    rel = ((wind - hdg + 540) % 360) - 180; stbd = rel > 0; off = abs(rel)
    boom = 10 if off < 60 else (35 if off < 120 else 70)
    yt = yacht(name)
    b = deg(boom if stbd else -boom); yt.boom_pivot.rotation_euler = (0, 0, b); side = 1 if b > 0 else -1
    WL = K.WL
    tack = Vector((-0.12, 0.0, 5.5 - WL)); head = Vector((-0.1, 0.0, 20.0 - WL - 6.0 * reef))
    clew = Vector((-5.4 * (1 - 0.15 * reef) * math.cos(b), 5.4 * (1 - 0.15 * reef) * math.sin(b), 5.55 - WL + 0.6 * reef))
    K.sail_surface(name + '-main', tack, head, clew, 0.10, side, twist=12, roach=0.06 * (1 - reef), parent=yt.root)
    gs = 1 if stbd else -1
    t0 = K.FORESTAY[0] - Vector((K.MAST.x, K.MAST.y, WL)); t1 = K.FORESTAY[1] - Vector((K.MAST.x, K.MAST.y, WL))
    t1 = t0.lerp(t1, 0.93 - 0.45 * reef)
    gclew = t0.lerp(Vector((-2.2, gs * 1.95, 4.35 - WL)), 1 - 0.45 * reef)
    if off > 150: gclew = t0.lerp(Vector((-0.8, gs * 3.4, 5.2 - WL)), 1 - 0.45 * reef)
    K.sail_surface(name + '-genoa', t0, t1, gclew, 0.12, gs, twist=8, parent=yt.root)
    h = heel if heel is not None else ((-12 if stbd else 12) if off < 120 else 0)
    if scale != 1.0: yt.root.scale = (scale,) * 3
    return yt.place(x, y, heading=hdg, heel=h)

def moved_sea(dz):
    for o in bpy.data.objects:
        if o.name.startswith(('ocean', 'far-sea')): o.location.z += dz

def dashed(name, a, b, w, mat, dash=4.0, gap=3.0, z=0.35):
    a, b = Vector(a), Vector(b); L = (b - a).length; u = (b - a) / L; s = 0.0
    while s < L:
        e = min(s + dash, L); strip(name, tuple(a + u * s), tuple(a + u * e), w, mat, z); s = e + gap

def foam_mat(name='foam', density=0.5, scale=0.05, white='#e9eef0', emit=0.0):
    """Broken white water: a noisy mask of foam over a transparent base."""
    m, nt, b, out = C.new_mat(name)
    tc = nt.nodes.new('ShaderNodeTexCoord'); n1 = nt.nodes.new('ShaderNodeTexNoise'); n1.inputs['Scale'].default_value = 1.0
    mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (scale, scale * 2.4, scale)
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector']); nt.links.new(mp.outputs['Vector'], n1.inputs['Vector'])
    n1.inputs['Detail'].default_value = 8; n1.inputs['Roughness'].default_value = 0.7
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 0.62 - 0.25 * density; mr.inputs['From Max'].default_value = 0.72 - 0.2 * density
    nt.links.new(n1.outputs['Fac'], mr.inputs['Value'])
    ctr = nt.nodes.new('ShaderNodeMapping'); ctr.inputs['Location'].default_value = (-1.0, -1.0, 0.0); ctr.inputs['Scale'].default_value = (2.0, 2.0, 0.0)
    nt.links.new(tc.outputs['Generated'], ctr.inputs['Vector'])
    gr = nt.nodes.new('ShaderNodeTexGradient'); gr.gradient_type = 'SPHERICAL'; nt.links.new(ctr.outputs['Vector'], gr.inputs['Vector'])
    gm = nt.nodes.new('ShaderNodeMath'); gm.operation = 'MULTIPLY'; nt.links.new(mr.outputs['Result'], gm.inputs[0]); nt.links.new(gr.outputs['Fac'], gm.inputs[1])
    C.setin(b, 'Base Color', lin(white)); C.setin(b, 'Roughness', 0.7)
    if emit: C.setin(b, 'Emission Color', lin(white)); C.setin(b, 'Emission Strength', emit)
    tp = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(gm.outputs[0], mx.inputs['Fac']); nt.links.new(tp.outputs[0], mx.inputs[1]); nt.links.new(b.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs['Surface'])
    return m

def foam(name, c, rx, ry, rot=0.0, z=0.25, density=0.5, scale=0.05, emit=0.0):
    """An elliptical patch of breaking water centred at c (x, y), rx by ry metres, turned rot degrees."""
    me = bpy.data.meshes.new(name); n = 48
    me.from_pydata([(0, 0, 0)] + [(math.cos(i / n * math.tau) * 1.0, math.sin(i / n * math.tau) * 1.0, 0) for i in range(n)], [],
                   [(0, i + 1, (i + 1) % n + 1) for i in range(n)])
    o = C.obj(name, me, foam_mat(name + '-mat', density, scale * max(rx, ry), emit=emit), (c[0], c[1], z)); o.scale = (rx, ry, 1); o.rotation_euler = (0, 0, deg(rot))
    o.visible_shadow = False
    return o

# ---------- land from polygons ----------
def sdist(X, Y, poly):
    """Signed distance (positive inside) from points X, Y to the closed polygon poly [(x, y)]."""
    P = np.array(poly, float); A = P; B = np.roll(P, -1, axis=0)
    dmin = np.full(X.shape, 1e12); inside = np.zeros(X.shape, bool)
    for (x1, y1), (x2, y2) in zip(A, B):
        dx, dy = x2 - x1, y2 - y1; L2 = dx * dx + dy * dy or 1e-9
        t = np.clip(((X - x1) * dx + (Y - y1) * dy) / L2, 0, 1)
        dmin = np.minimum(dmin, np.hypot(X - x1 - t * dx, Y - y1 - t * dy))
        cond = ((y1 > Y) != (y2 > Y)) & (X < (x2 - x1) * (Y - y1) / ((y2 - y1) if y2 != y1 else 1e-9) + x1)
        inside ^= cond
    return np.where(inside, dmin, -dmin)

def land(polys, box, step, relief=80.0, hill=120.0, cliff=0.0, beach=4.0, seed=11.0, rough=0.35, name='land', mat=None, floor=-14.0):
    """Terrain over box (x0, y0, x1, y1) raised inside the polygons: a beach, then hills `relief` m high reached over
    `hill` m; cliff (m) adds a steep face at the shore. Returns the height function h(x, y)."""
    x0, y0, x1, y1 = box
    nx, ny = int((x1 - x0) / step), int((y1 - y0) / step)
    gx, gy = np.meshgrid(x0 + np.arange(nx + 1) * step, y0 + np.arange(ny + 1) * step)
    X, Y = gx.ravel(), gy.ravel()
    def H(X, Y):
        d = np.max(np.stack([sdist(X, Y, p) for p in polys]), axis=0)
        n1 = np.array([mnoise.noise(Vector((x * 0.004, y * 0.004, seed))) for x, y in zip(X, Y)])
        n2 = np.array([mnoise.noise(Vector((x * 0.02, y * 0.02, seed + 3))) for x, y in zip(X, Y)])
        dl = np.maximum(0.0, d - beach)
        h = 1.2 + relief * (1 - np.exp(-dl / hill)) + (rough * relief * n1 + 0.08 * relief * n2) * np.clip(dl / (hill * 0.5), 0, 1)
        if cliff: h = h + cliff * np.clip(d / max(1.0, step * 1.5), 0, 1) ** 0.5
        h = np.where(d < beach, 1.2 * np.clip(d / max(beach, 1e-3), 0, 1), h)
        return np.where(d < 0, np.maximum(floor, d * 0.12), h) - 0.3
    Z = H(X, Y)
    verts = list(zip(X.tolist(), Y.tolist(), Z.tolist()))
    faces = [(j * (nx + 1) + i, j * (nx + 1) + i + 1, (j + 1) * (nx + 1) + i + 1, (j + 1) * (nx + 1) + i) for j in range(ny) for i in range(nx)]
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update(); me.shade_smooth()
    C.obj(name, me, mat or KW.land_mat())
    return lambda x, y: float(H(np.array([x], float), np.array([y], float))[0])

def scrub(hfun, box, n=800, minh=4.0, seed=31, size=(2.2, 4.6), polys=None):
    """Dark green bushes scattered over the land (h > minh)."""
    random.seed(seed); m = C.simple('foliage', '#3c4a26', 0.9)
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    for v in bm.verts: v.co *= 1.0 + 0.2 * mnoise.noise(v.co * 2.0); v.co.z *= 0.8
    me = bpy.data.meshes.new('tree'); bm.to_mesh(me); bm.free(); me.materials.append(m); me.shade_smooth()
    k = 0
    for _ in range(n * 5):
        if k >= n: break
        x, y = random.uniform(box[0], box[2]), random.uniform(box[1], box[3]); h = hfun(x, y)
        if h < minh or mnoise.noise(Vector((x * 0.012, y * 0.012, 3.0))) < -0.1: continue
        o = bpy.data.objects.new('tree', me); C.col.objects.link(o); s = random.uniform(*size); o.scale = (s, s, s * random.uniform(0.8, 1.3)); o.location = (x, y, h + s * 0.4); k += 1

def lighthouse(at, z0, h=14.0, r=1.6, lit=False, color='#f2f0ea'):
    """A white tower with a lantern; lit=True puts a bright white lamp in the lantern."""
    M = K.mats()
    C.cyl('lh-tower', r, r * 0.8, h, 32, C.simple('lh-white', color, 0.5), (at[0], at[1], z0 + h / 2))
    C.cyl('lh-gallery', r * 1.1, r * 1.1, 0.3, 32, M['dark'], (at[0], at[1], z0 + h + 0.15))
    if lit: lamp('lh-light', (at[0], at[1], z0 + h + 1.0), 'w', lit if isinstance(lit, float) else 0.9, power=8000.0, gain=3.0)
    else: C.cyl('lh-lantern', r * 0.6, r * 0.6, 1.4, 24, C.simple('lantern', '#2a3540', 0.2, 0.6), (at[0], at[1], z0 + h + 1.0))
    C.cyl('lh-roof', r * 0.7, 0.1, 0.8, 24, C.simple('lh-roof', '#b02a20', 0.5), (at[0], at[1], z0 + h + 2.1))
    return Vector((at[0], at[1], z0 + h + 1.0))

def ship(pos, heading, model='vessel-ferry.glb', length=None):
    """A model ship floating at pos, bow on `heading` (the ferry's bow is along +X)."""
    root, objs = K.load_model(model, drop_planes=False)
    for o in objs:
        if o.type == 'MESH' and any(sl.material and ('Water' in sl.material.name or 'water' in sl.material.name) for sl in o.material_slots): o.hide_render = True
    bpy.context.view_layer.update()
    vis = [o for o in objs if o.type == 'MESH' and not o.hide_render]
    lo, hi = K.bbox(vis); cx, cy = (lo.x + hi.x) / 2, (lo.y + hi.y) / 2
    for o in objs:
        if o.parent == root: o.location = Vector(o.location) - Vector((cx, cy, 1.0))
    if length: k = length / (hi.x - lo.x); root.scale = (k,) * 3
    root.location = Vector((pos[0], pos[1], 0.0)); root.rotation_euler = (0, 0, deg(90 - heading))
    return root, vis

# ---------- the figures' 320 x 200 drawings ----------
from art_yof_pilotage_svg import path_polys

def extend(p, far=400.0):
    """Points on the drawing's frame pushed out beyond it, so the land runs on past the picture."""
    x, y = p
    return (x - far if x <= 0 else x + far if x >= 320 else x, y - far if y <= 0 else y + far if y >= 200 else y)

def drawing(s):
    """Drawing units (x right, y down, 320 x 200, centre 160, 100) -> Blender metres at s m per unit, north up."""
    return lambda px, py: ((px - 160) * s, -(py - 100) * s)

def helm(png, sky=None, state='breeze', cam='ahead', night=False):
    """Our yacht heading north (000), the Axiom on its pod at the wheel showing `png`; the camera over the
    helmsman's shoulder. Returns (yacht, screen)."""
    you = yacht('you').place(0, 0, heading=0)
    if night:
        import kit_night as N
        N.night_scene(state)
    else:
        K.sea(state, repeat=10)
        if sky: sky()
        else: K.day_sky(sun_az=230, sun_el=35)
        K.wake(you, 40, 8, 1.0)
    objs, scr = plotter(png, you.world((-1.25, -0.32, 4.6)), tilt=-14, emit=0.9 if night else 0.7)
    if cam == 'ahead': K.camera(tuple(you.world((-1.66, -0.31, 4.98))), tuple(you.world((-1.25, -0.33, 4.73))), 46)
    else:      # ('view', yaw to starboard, pitch, lens, eye): a wider look that keeps the horizon in the picture
        _, yaw, pitch, lens, eye = cam
        d = Vector((math.cos(deg(pitch)) * math.cos(deg(yaw)), -math.cos(deg(pitch)) * math.sin(deg(yaw)), math.sin(deg(pitch))))
        K.camera(tuple(you.world(eye)), tuple(you.world(Vector(eye) + d * 10)), lens)
    return you, scr
