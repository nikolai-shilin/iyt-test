# Article bareboat-skipper/weather, figures 1, 2, 3, 4 and 10: what the sailor sees under each pressure pattern.
#   1  a low: overcast, a rough sea, our yacht reefed and heeled      2  a high: clear sky, flat sea, motoring
#   3  Buys Ballot: back to the NE wind, the low's dark sky to the SE (left)
#   4  a depression passing north: a cold-front cloud wall arriving from the NW, the wind still SW
#   10 the meltemi: dry Aegean islands under a clear sky, a strong N wind on the sea, yachts beating and running
# Skies with cloud are a custom world: a sky gradient with a projected fbm cloud layer, denser in a given direction
# (cheap, and the sea reflects it). Clear skies use kit.day_sky.
#   blender --background --factory-startup --python docs/design/blender/art_weather_a.py -- --fig 1 [--out x.jpg]
import os, sys, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
from mathutils import Vector, noise as mnoise
import common as C, kit as K, kit_world as KW
from common import lin

HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.join(HERE, '..', 'figure-style', 'articles', 'bareboat-skipper', 'weather')
arg = C.cli(); FIG = arg('--fig', 1); SAMPLES = arg('--samples', 192); SCALE = arg('--scale', 100)
OUT = arg('--out', os.path.join(OUTDIR, f'{FIG}-3d.jpg'))
def deg(a): return math.radians(a)

# ---------- yacht: kit.load_yacht minus the spinnaker leftovers, sails set from the wind, optionally reefed ----------
_load = K.load_yacht
def _yacht(*a, **k):
    yt = _load(*a, **k)
    for o in yt.objs:
        anc, q = [], o.parent
        while q: anc.append(q.name); q = q.parent
        if o.type == 'MESH' and (any(n.startswith('SPINNAKER') for n in anc) or
                                 any(sl.material and sl.material.name.startswith(('[Color_F12]', '[Color_H09]')) for sl in o.material_slots)):
            o.hide_render = True
    return yt
K.load_yacht = _yacht

def sailing(name, hdg, wind, x, y, reef=0.0, heel=None):
    """A yacht under sail: boom and genoa to leeward. reef 0..1 lowers the main's head and rolls the genoa."""
    rel = ((wind - hdg + 540) % 360) - 180; stbd = rel > 0; off = abs(rel)
    boom = 10 if off < 60 else (35 if off < 120 else 70)
    yt = K.load_yacht(name=name)
    b = deg(boom if stbd else -boom); yt.boom_pivot.rotation_euler = (0, 0, b); side = 1 if b > 0 else -1
    WL = K.WL
    tack = Vector((-0.12, 0.0, 5.5 - WL)); head = Vector((-0.1, 0.0, 20.0 - WL - 6.0 * reef))
    clew = Vector((-5.4 * (1 - 0.15 * reef) * math.cos(b), 5.4 * (1 - 0.15 * reef) * math.sin(b), 5.55 - WL + 0.6 * reef))
    K.sail_surface(name + '-main', tack, head, clew, 0.10, side, twist=12, roach=0.06 * (1 - reef), parent=yt.root)
    gs = 1 if stbd else -1
    t0 = K.FORESTAY[0] - Vector((K.MAST.x, K.MAST.y, WL)); t1 = K.FORESTAY[1] - Vector((K.MAST.x, K.MAST.y, WL))
    t1 = t0.lerp(t1, 0.93 - 0.45 * reef)
    gclew = t0.lerp(Vector((-2.2, gs * 1.95, 4.35 - WL)), 1 - 0.45 * reef)
    if off > 150: gclew = t0.lerp(Vector((-0.8, gs * 3.4, 5.2 - WL)), 1 - 0.45 * reef)   # poled out on a run
    K.sail_surface(name + '-genoa', t0, t1, gclew, 0.12, gs, twist=8, parent=yt.root)
    h = heel if heel is not None else ((-12 if stbd else 12) if off < 120 else 0)
    return yt.place(x, y, heading=hdg, heel=h)

# ---------- a cloudy sky ----------
def cloud_sky(zenith, horizon, dark, light, cover=0.5, sharp=0.12, scale=2.2, boost=None, sun=(200, 35, 3.0),
              strength=1.0, haze=0.12, seed=3.0, wall=None, shade_scale=3.3):
    """World: a gradient sky with a projected cloud layer. cover 0..1 is the cloud fraction overhead; boost
    (az, spread_deg, extra_cover, extra_dark) piles cloud up towards compass bearing az, darker there.
    sun (az, el, energy) adds a sun lamp; its disc is not drawn (it sits behind the cloud in these skies)."""
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
        low = mr(dz, 0.45, 0.02)                               # the bank sits low on that horizon, rising to it
        wgt = mth('MULTIPLY', wgt, mth('ADD', mth('MULTIPLY', low, 0.7), 0.3))
        cov = mth('ADD', cover, mth('MULTIPLY', wgt, extra)); dk = mth('MULTIPLY', wgt, xdark)
    lo_ = mth('SUBTRACT', 0.66, mth('MULTIPLY', cov, 0.36)) if not isinstance(cov, float) else 0.66 - cov * 0.36
    mask = mr(n1.outputs['Fac'], lo_, mth('ADD', lo_, sharp) if not isinstance(lo_, float) else lo_ + sharp)
    # fade the layer into the haze at the horizon
    mask = mth('MULTIPLY', mask, mr(mth('ABSOLUTE', dz), 0.0, haze, 0.55, 1.0))
    shade = mix(n2.outputs['Fac'], lin(dark), lin(light))
    if not isinstance(dk, float): shade = mix(dk, shade, (0.012, 0.014, 0.018, 1))
    grad = mix(mr(dz, 0.0, 0.55), lin(horizon), lin(zenith))
    col = mix(mask, grad, shade)
    if wall:
        # a cloud wall low on one horizon: a dark mass whose top edge billows, rain shafts under it
        az, spread, top, wcol = wall
        a = deg(az); hl = mth('SQRT', mth('ADD', mth('MULTIPLY', dx, dx), mth('MULTIPLY', dy, dy)))
        dot = mth('DIVIDE', mth('ADD', mth('MULTIPLY', dx, math.sin(a)), mth('MULTIPLY', dy, math.cos(a))), mth('ADD', hl, 1e-4))
        wa = mr(dot, math.cos(deg(spread)), math.cos(deg(spread * 0.55)))
        ev = N('ShaderNodeCombineXYZ'); L(mth('MULTIPLY', dx, 4.5), ev.inputs['X']); L(mth('MULTIPLY', dy, 4.5), ev.inputs['Y']); ev.inputs['Z'].default_value = seed + 5
        en = N('ShaderNodeTexNoise'); en.inputs['Scale'].default_value = 1.0; en.inputs['Detail'].default_value = 3; en.inputs['Roughness'].default_value = 0.5; L(ev.outputs[0], en.inputs['Vector'])
        h = mth('MULTIPLY', mth('MULTIPLY', wa, top), mth('ADD', mth('MULTIPLY', en.outputs['Fac'], 0.9), 0.45))
        wm = mr(mth('SUBTRACT', h, dz), -0.006, 0.02)                    # 1 below the billowing top edge, soft
        wm = mth('MULTIPLY', wm, mr(dz, -0.25, -0.02))                    # and in reflections, fading below the horizon
        # cauliflower texture in the body, a sunlit upper part, darker underneath, rain shafts down to the sea
        bv = N('ShaderNodeCombineXYZ'); L(mth('MULTIPLY', dx, 16.0), bv.inputs['X']); L(mth('MULTIPLY', dy, 16.0), bv.inputs['Y']); L(mth('MULTIPLY', dz, 40.0), bv.inputs['Z'])
        bn = N('ShaderNodeTexNoise'); bn.inputs['Scale'].default_value = 1.0; bn.inputs['Detail'].default_value = 6; bn.inputs['Roughness'].default_value = 0.55; L(bv.outputs[0], bn.inputs['Vector'])
        up = mr(mth('DIVIDE', dz, mth('ADD', h, 1e-3)), 0.25, 1.0)        # 0 at the base, 1 at the top edge
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

def compass(az, el, dist=3000.0, c=Vector((0, 0, 0))):
    """A point far off on compass bearing az, el degrees up, for pills in the sky."""
    a, e = deg(az), deg(el)
    return c + Vector((math.sin(a) * math.cos(e), math.cos(a) * math.cos(e), math.sin(e))) * dist

def drone(c, dist, az, el, lens=32.0):
    a, e = deg(az), deg(el)
    eye = c + Vector((math.sin(a) * math.cos(e), math.cos(a) * math.cos(e), math.sin(e))) * dist
    return K.camera(tuple(eye), tuple(c), lens)

# ---------- islands for the meltemi ----------
def island(cx, cy, rx, ry, h, seed, rot=0.0, step=None):
    step = step or max(rx, ry) / 70.0
    nx, ny = int(2.6 * rx / step), int(2.6 * ry / step); verts, faces = [], []
    ca, sa = math.cos(rot), math.sin(rot)
    for j in range(ny + 1):
        for i in range(nx + 1):
            u, v = (i / nx - 0.5) * 2.6, (j / ny - 0.5) * 2.6
            r = math.hypot(u, v); ang = math.atan2(v, u)
            edge = 1.0 + 0.22 * mnoise.noise(Vector((math.cos(ang) * 1.3, math.sin(ang) * 1.3, seed))) + 0.08 * math.sin(ang * 5 + seed)
            t = max(0.0, 1 - r / edge)
            z = h * (t ** 0.9) * (0.75 + 0.5 * mnoise.noise(Vector((u * 1.8, v * 1.8, seed + 7)))) + 9 * mnoise.noise(Vector((u * 7, v * 7, seed))) * t
            z = z - 6.0 if t <= 0 else z + 0.4
            x, y = u * rx, v * ry
            verts.append((cx + x * ca - y * sa, cy + x * sa + y * ca, z))
    for j in range(ny):
        for i in range(nx):
            k = j * (nx + 1) + i; faces.append((k, k + 1, k + nx + 2, k + nx + 1))
    me = bpy.data.meshes.new('island'); me.from_pydata(verts, [], faces); me.update(); me.shade_smooth()
    return C.obj('island', me, LAND)

# ---------- the figures ----------
C.reset()
labels, arrows, note, expo = [], [], None, -0.6

if FIG == 1:
    # a low: grey overcast, F6-7, our yacht reefed and well heeled on the wind
    cloud_sky(zenith='#596068', horizon='#8b9197', dark='#4b5158', light='#6a7178', cover=1.0, sharp=0.5, scale=1.2,
              sun=(230, 30, 1.1), strength=1.0, haze=0.10, shade_scale=1.6)
    sea = K.sea(wind=15.0, wave_scale=0.8, chop=1.9, size=60.0, res=11, repeat=8, color='#22383e')
    sea.modifiers['ocean'].foam_coverage = 0.32
    y = sailing('you', 0, 315, 0, 0, reef=0.55, heel=22)
    drone(Vector((0, 4, 6)), 34, 110, 14, 30)
    labels = [(tuple(y.world((K.MAST.x, K.MAST.y, 16.5))), 'Low · tight isobars, strong wind')]
    arrows = [((-14, 24, 15), (-2, 12, 13), 'blue')]; labels.append(((-14, 24, 16.5), 'Wind', 'blue'))
    note = 'Overcast, wind F6–7, a rough sea'; expo = 0.5
elif FIG == 2:
    # a high: clear sky, a flat sea, light airs: sails furled, motoring
    K.day_sky(sun_az=200, sun_el=52)
    K.sea(wind=2.2, wave_scale=0.05, chop=0.6, size=30.0, repeat=14)
    y = K.load_yacht(name='you').place(0, 0, heading=20)
    K.wake(y, 30, 6, 0.7)
    drone(Vector((0, 3, 4)), 36, 150, 16, 30)
    labels = [(tuple(y.world((K.MAST.x, K.MAST.y, 12.0))), 'High · wide isobars, light wind')]
    note = 'Clear sky, flat calm: motoring'
elif FIG == 3:
    # Buys Ballot: running SW before a NE wind; to the left (SE) the sky is dark where the low lies
    cloud_sky(zenith='#2f5f93', horizon='#a9bfd0', dark='#3a4049', light='#c9ced3', cover=0.28, sharp=0.18, scale=2.6,
              boost=(175, 70, 0.95, 0.75), sun=(260, 40, 3.2), strength=1.0, haze=0.08, wall=(185, 45, 0.13, '#30363d'))
    K.sea('breeze', repeat=10)
    y = sailing('you', 225, 45, 0, 0)
    eye = y.world((-3.6, 0.13, 5.2)); look = y.world((14.0, 0.13, 6.4))
    K.camera(tuple(eye), tuple(look), 20)
    fwd = (look - eye).normalized()
    p0 = eye + fwd * 12 + Vector((0, 0, 1.6)) + Vector((-fwd.y, fwd.x, 0)) * -3.5; p1 = p0 + fwd * 22
    arrows = [(tuple(p0), tuple(p1), 'blue')]; labels = [(tuple(p0 + Vector((0, 0, 0.6))), 'Wind NE, from behind', 'blue')]
    labels.append((tuple(compass(196, 12)), 'the low: SE', 'red'))
    note = 'Back to the wind: the low is on your left'; expo = 0.2
elif FIG == 4:
    # a cold front coming in from the NW: a dark cloud wall over the sea; the wind still SW
    cloud_sky(zenith='#33618f', horizon='#a2b6c4', dark='#6a7179', light='#c9ced3', cover=0.12, sharp=0.2, scale=2.4,
              sun=(150, 42, 3.0), strength=1.0, haze=0.05, wall=(318, 80, 0.17, '#262b31'))
    K.sea('breeze', repeat=10)
    y = sailing('you', 300, 225, 0, 0)
    drone(Vector((0, 0, 6)), 40, 145, 12, 26)
    labels = [(tuple(compass(330, 4.5, 2500)), 'cold front', 'red')]
    arrows = [((-30, -14, 9), (-16, 0, 8), 'blue')]; labels.append(((-30, -14, 10.5), 'Wind SW now', 'blue'))
    note = 'Low passing north: SW, then NW'; expo = 0.2
else:
    # the meltemi: Aegean islands, a clear sky, N 6-7 on the sea, yachts beating north and running south
    K.day_sky(sun_az=235, sun_el=48, haze=1.2)
    LAND = KW.land_mat()
    sea = K.sea(wind=13.0, wave_scale=1.0, chop=1.7, size=140.0, res=11, repeat=14, center=(0, 500), color='#0b3445')
    sea.modifiers['ocean'].foam_coverage = 0.1
    for cx, cy, rx, ry, h, s, r in ((-900, 1500, 700, 420, 260, 1.0, 0.3), (750, 1150, 520, 300, 190, 2.0, -0.4),
                                    (-150, 2600, 900, 380, 320, 3.0, 0.1), (1500, 2300, 600, 350, 230, 4.0, 0.6), (-1900, 900, 500, 380, 200, 5.0, 0.0)):
        island(cx, cy, rx, ry, h, s, r)
    yts = [sailing('y1', 340, 0, -40, 40, heel=-16), sailing('y2', 20, 0, 60, 150, heel=16), sailing('y3', 180, 0, 75, 10, heel=0),
           sailing('y4', 345, 0, -150, 260, heel=-15)]
    for yt in yts: K.wake(yt, 40, 8, 1.0)
    K.camera((30, -220, 80), (0, 400, 0), 34)
    arrows = [((-120, 900, 120), (-120, 520, 70), 'red')]
    labels = [((-120, 900, 135), 'meltemi N 6–7', 'red')]
    note = 'Aegean, July: N 6–7 under a clear sky'; expo = -0.4

C.render(OUT, SAMPLES, SCALE, expo, labels, note, space='blender', arrows=arrows)
