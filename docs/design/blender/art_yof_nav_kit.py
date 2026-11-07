# Shared parts for the Yachtmaster Offshore navigation renders (art_yof_charts.py, art_yof_compass.py, art_yof_dr.py),
# on top of common.py, kit.py, kit_instruments.py and art_checkin_nps_kit.py: the chart table with a paper chart whose
# pixels map to world points, plotting tools (dividers, Breton plotter, pencil, drawing compass, steel rule), log book
# and notebook pages, a calculator, a bulkhead clock, the pedestal steering compass. Textures from art_yof_nav_tex.py
# in each article's tex/ folder. Blender space, Z up, metres; the table top at z = 0.
import os, sys, math, json, subprocess
import bpy, bmesh
from mathutils import Vector
import common as C, kit as K, kit_instruments as KI
import art_checkin_nps_kit as A

HERE = os.path.dirname(os.path.abspath(__file__))
ARTS = os.path.join(HERE, '..', 'figure-style', 'articles', 'yachtmaster-offshore')
deg = math.radians

def outdir(article): return os.path.join(ARTS, article)

def tex(article, name, suffix=''):
    d = os.path.join(outdir(article), 'tex'); p = os.path.join(d, name + suffix + '.png')
    if not os.path.exists(p) or '--retex' in sys.argv:
        subprocess.run(['python3', os.path.join(HERE, 'art_yof_nav_tex.py'), article, name], check=True)
    return p

def meta(article, name): return json.load(open(os.path.join(outdir(article), 'tex', name + '.json')))

# ---------------------------------------------------------------- materials
def alpha_mat(name, path, rough=0.3, emit=0.0):
    """An image with its alpha: printed lines on clear plastic."""
    m, nt, b, out = C.new_mat(name)
    tx = C.node(nt, 'ShaderNodeTexImage'); tx.image = bpy.data.images.load(path); tx.interpolation = 'Cubic'
    C.link(nt, tx.outputs['Color'], b.inputs['Base Color']); C.link(nt, tx.outputs['Alpha'], b.inputs['Alpha']); C.setin(b, 'Roughness', rough)
    if emit: C.link(nt, tx.outputs['Color'], b.inputs['Emission Color']); C.setin(b, 'Emission Strength', emit)
    try: m.blend_method = 'BLEND'
    except Exception: pass
    return m

def acrylic_mat(name='acrylic-clear', tint='#f4f8fa'):
    m, nt, b, _ = C.new_mat(name)
    C.setin(b, 'Base Color', C.lin(tint)); C.setin(b, 'Roughness', 0.04); C.setin(b, 'IOR', 1.49); C.setin(b, 'Transmission Weight', 1.0)
    return m

def mats():
    M = K.mats()
    if 'brass' not in M:
        M['brass'] = C.simple('brass', '#b08a3e', 0.28, 1.0)
        M['steel'] = C.simple('divider-steel', '#c9ccd0', 0.22, 1.0)
        M['pencil'] = C.simple('pencil', '#e8b818', 0.45, coat=0.4)
        M['wood'] = C.simple('wood', '#d9b482', 0.7)
        M['graphite'] = C.simple('graphite', '#2a2a2c', 0.4, 0.4)
        M['blackplastic'] = C.simple('black-plastic', '#141618', 0.35, coat=0.5)
        M['cover'] = C.simple('book-cover', '#1f3358', 0.55)
        M['covergreen'] = C.simple('book-cover-green', '#2c4a36', 0.6)
    return M

# ---------------------------------------------------------------- the chart table
def chart_table(w=1.35, d=0.9, light='day', lamp=(0.0, -0.1, 0.85), lamp_power=14, port=True):
    """Teak top (z = 0) w x d centred on the origin, fiddles, a bulkhead behind (+y) and a side wall (-x); cabin light."""
    jo = KI.joinery_mat()
    C.obj('table', C.rbox('table', (w, d, 0.04), 0.006, 2), jo, (0, 0, -0.02))
    C.obj('fiddle-front', C.rbox('fiddle', (w, 0.025, 0.035), 0.008, 2), jo, (0, -d / 2 - 0.012, 0.015))
    C.obj('fiddle-back', C.rbox('fiddle', (w, 0.025, 0.06), 0.008, 2), jo, (0, d / 2 + 0.012, 0.03))
    KI.wall('bulkhead', -w, w, -0.05, 0.9, d / 2 + 0.03, jo)
    sw = KI.wall('side', -d, d, -0.05, 0.9, 0.0, jo); sw.rotation_euler = (0, 0, deg(90)); sw.location = (-w / 2 - 0.02, 0, 0)
    K.day_sky(sun_az=200, sun_el=40, strength=0.05)
    KI.area_light(lamp, (lamp[0], lamp[1] + 0.1, 0.0), lamp_power, 0.35, (1.0, 0.86, 0.68))
    if port: KI.area_light((w / 2 + 0.4, -0.3, 0.5), (0.0, 0.05, 0.0), 16, 0.4, (0.85, 0.92, 1.0))
    return jo

class Sheet:
    """A flat image on the table: w x h metres, centred at loc, turned rotz degrees; P(px, py) is the world point of a
    pixel of its image (W x H px)."""
    def __init__(s, name, path, w, h, W, H, loc=(0, 0, 0.0008), rotz=0.0, rough=0.85, emit=0.0, mat=None):
        s.w, s.h, s.W, s.H = w, h, W, H
        s.o = A.quad(name, w, h, path, loc, rot=(0, 0, deg(rotz)), emit=emit, rough=rough, mat=mat)
        bpy.context.view_layer.update()
    def P(s, px, py, dz=0.0):
        bpy.context.view_layer.update()
        return s.o.matrix_world @ Vector(((px / s.W - 0.5) * s.w, (0.5 - py / s.H) * s.h, dz))
    def dir(s, bearing):
        """World direction of a chart bearing (north = up the image)."""
        bpy.context.view_layer.update(); r = s.o.matrix_world.to_3x3()
        return (r @ Vector((math.sin(deg(bearing)), math.cos(deg(bearing)), 0))).normalized()

def chart(article, name, loc=(0, 0), rotz=0.0, z=0.0008):
    p = tex(article, name); m = meta(article, name)
    sh = Sheet(name, p, m['w_m'], m['h_m'], m['W'], m['H'], (loc[0], loc[1], z), rotz)
    sh.meta = m; sh.a = lambda k, dz=0.0: sh.P(*m['anchors'][k][:2], dz)
    return sh

def page(article, name, w, loc, rotz=0.0, z=0.0, cover=None, curl=0.0, emit=0.0):
    """A page image (log book, notebook, booklet) on a cover board; w metres wide."""
    p = tex(article, name); m = meta(article, name); h = w * m['h_px'] / m['w_px']
    if cover:
        cv = C.obj(name + '-cover', C.rbox(name + '-cover', (w + 0.012, h + 0.012, 0.006), 0.002, 2), cover, (loc[0], loc[1], z + 0.003)); cv.rotation_euler = (0, 0, deg(rotz))
        z += 0.0062
    sh = Sheet(name, p, w, h, m['w_px'], m['h_px'], (loc[0], loc[1], z + 0.0004), rotz, rough=0.8, emit=emit)
    sh.meta = m; sh.a = lambda k, dz=0.0: sh.P(*m['anchors'][k][:2], dz)
    return sh

def book(article, left, right, w, loc, rotz=0.0, cover=None):
    """An open book: two pages side by side, each w wide, the spine between them sagging a little."""
    r = deg(rotz); off = Vector((math.cos(r), math.sin(r), 0)) * (w / 2 + 0.004)
    L = page(article, left, w, tuple(Vector(loc) - off), rotz, 0.0, None) if left else None
    Rr = page(article, right, w, tuple(Vector(loc) + off), rotz, 0.0, None)
    hh = Rr.h
    cv = C.obj('book-cover', C.rbox('book-cover', (2 * w + 0.03, hh + 0.02, 0.012), 0.003, 2), cover or mats()['cover'], (loc[0], loc[1], -0.007)); cv.rotation_euler = (0, 0, r)
    for o in ([L.o] if L else []) + [Rr.o]: o.location.z += 0.0002
    return L, Rr

# ---------------------------------------------------------------- tools
def seg(name, a, b, r1, r2, mat, n=24): return A.rod(name, a, b, r1, r2, mat, n)

def dividers(pa, pb, lift=0.10, side=None, name='dividers'):
    """Brass dividers with steel points on pa and pb; the hinge lifted `lift`, leaning to `side` (a world vector)."""
    M = mats(); pa, pb = Vector(pa), Vector(pb)
    mid = (pa + pb) / 2; d = (pb - pa); n = side if side is not None else Vector((-d.y, d.x, 0)).normalized() * 0.35 * lift
    hinge = mid + Vector(n) + Vector((0, 0, lift))
    for nm, p0 in (('a', pa), ('b', pb)):
        q = p0 + (hinge - p0).normalized() * 0.018
        seg(name + '-point-' + nm, p0, q, 0.0006, 0.0022, M['steel']); seg(name + '-leg-' + nm, q, hinge, 0.0028, 0.0072, M['brass'])
    o = C.cyl(name + '-hinge', 0.009, 0.009, 0.012, 24, M['brass'], hinge, (0, 0, 0)); o.rotation_mode = 'QUATERNION'
    o.rotation_quaternion = (pb - pa).normalized().to_track_quat('Z', 'Y')
    seg(name + '-knob', hinge, hinge + Vector((0, 0, 0.022)), 0.005, 0.003, M['brass'])
    return hinge

def pencil(at, ang, length=0.17, z=0.0043):
    """A hexagonal pencil lying on the table, its point at `at` turned `ang` degrees (world, from +x)."""
    M = mats(); at = Vector(at); u = Vector((math.cos(deg(ang)), math.sin(deg(ang)), 0))
    base = at - u * (length + 0.018); tipstart = at - u * 0.018
    seg('pencil-body', base + Vector((0, 0, z)), tipstart + Vector((0, 0, z)), 0.0043, 0.0043, M['pencil'], 6)
    seg('pencil-wood', tipstart + Vector((0, 0, z)), at + Vector((0, 0, 0.0012)), 0.0042, 0.0007, M['wood'], 12)
    seg('pencil-lead', at - u * 0.004 + Vector((0, 0, 0.0016)), at + Vector((0, 0, 0.0008)), 0.0011, 0.0003, M['graphite'], 8)
    seg('pencil-rubber', base - u * 0.012 + Vector((0, 0, z)), base + Vector((0, 0, z)), 0.0042, 0.0042, C.simple('rubber', '#d86a7a', 0.7), 12)

def breton(article, center, course, dial_north=0.0, name='breton'):
    """The Breton plotter, its long edge along `course` (chart bearing of the arrows), its dial turned so its grid lies
    on the meridians (dial_north = the chart's north as a world bearing, 0 if the chart is not turned).
    center: world point of the base centre on the chart. Returns the world point of the index."""
    base_png = tex(article, 'breton', '-base'); dial_png = tex(article, 'breton', '-dial')
    c = Vector(center); rz = deg(90 - course + dial_north)
    W_, H_ = 0.33, 0.14
    C.obj(name + '-slab', C.rbox(name + '-slab', (W_, H_, 0.0025), 0.002, 2), acrylic_mat(), (c.x, c.y, 0.0016)).rotation_euler = (0, 0, rz)
    A.quad(name + '-print', W_, H_, base_png, (c.x, c.y, 0.0031), rot=(0, 0, rz), mat=alpha_mat(name + '-print', base_png, 0.2))
    off = Vector((0, -0.004, 0)); off.rotate(__import__('mathutils').Euler((0, 0, rz)))
    dc = c + off
    C.cyl(name + '-dial', 0.0605, 0.0605, 0.0016, 96, acrylic_mat(name + '-dial-clear', '#f8fbff'), (dc.x, dc.y, 0.0040))
    A.quad(name + '-dial-print', 0.121, 0.121, dial_png, (dc.x, dc.y, 0.0049), rot=(0, 0, deg(-dial_north)), mat=alpha_mat(name + '-dial-print', dial_png, 0.2))
    u = Vector((math.cos(rz), math.sin(rz), 0))
    return dc + u * 0.064 + Vector((0, 0, 0.005)), dc

def drawing_compass(pivot, pt, lift=0.11):
    """A pencil compass: steel needle on `pivot`, pencil lead on `pt`, the hinge `lift` above."""
    M = mats(); a, b = Vector(pivot), Vector(pt)
    d = b - a; hinge = (a + b) / 2 + Vector((0, 0, lift))
    q = a + (hinge - a).normalized() * 0.02
    seg('dc-needle', a, q, 0.0005, 0.0018, M['steel']); seg('dc-leg-a', q, hinge, 0.0034, 0.006, M['steel'])
    r = b + (hinge - b).normalized() * 0.022
    seg('dc-lead', b, r, 0.0007, 0.0022, M['graphite']); seg('dc-holder', r, r + (hinge - b).normalized() * 0.014, 0.0035, 0.0035, M['blackplastic'])
    seg('dc-leg-b', r + (hinge - b).normalized() * 0.014, hinge, 0.0034, 0.006, M['steel'])
    C.cyl('dc-head', 0.009, 0.009, 0.014, 24, M['steel'], hinge, (deg(90), 0, math.atan2(d.y, d.x) + deg(90)))
    seg('dc-knob', hinge, hinge + Vector((0, 0, 0.03)), 0.0035, 0.0028, C.simple('knurl', '#3a3c40', 0.4, 0.6))
    return hinge

def rule(article, a, b, width=0.025, name='rule'):
    """A steel rule from a (its zero) towards b, lying on the chart; texture tex/rule.png."""
    p = tex(article, 'rule'); a, b = Vector(a), Vector(b); u = (b - a).normalized(); L = 0.30
    c = a + u * (L / 2 - 0.004) + Vector((-u.y, u.x, 0)) * (width / 2)
    rz = math.atan2(u.y, u.x)
    C.obj(name + '-steel', C.rbox(name, (L + 0.01, width, 0.0009), 0.0004, 1), C.simple('rule-steel', '#b8bcc0', 0.3, 1.0), (c.x, c.y, 0.0011)).rotation_euler = (0, 0, rz)
    A.quad(name + '-print', L + 0.008, width, p, (c.x, c.y, 0.0016), rot=(0, 0, rz), mat=alpha_mat(name + '-print', p, 0.3))

def calculator(loc, rotz, png):
    M = mats(); r = deg(rotz); loc = Vector((loc[0], loc[1], 0.0))
    C.obj('calc', C.rbox('calc', (0.085, 0.16, 0.016), 0.006, 3), C.simple('calc-body', '#26292d', 0.5), (loc.x, loc.y, 0.008)).rotation_euler = (0, 0, r)
    off = lambda x, y: loc + Vector((x * math.cos(r) - y * math.sin(r), x * math.sin(r) + y * math.cos(r), 0))
    A.quad('calc-lcd', 0.068, 0.026, png, tuple(off(0, 0.054) + Vector((0, 0, 0.0163))), rot=(0, 0, r), rough=0.2)
    keym = C.simple('calc-key', '#4a4f55', 0.5)
    for i in range(5):
        for j in range(4):
            k = off(-0.03 + j * 0.02, 0.022 - i * 0.02)
            C.obj('key', C.rbox('key', (0.015, 0.013, 0.004), 0.002, 2), C.simple('calc-key-op', '#c26a2a', 0.5) if j == 3 else keym, (k.x, k.y, 0.017)).rotation_euler = (0, 0, r)

def clock(png, at, r=0.075):
    """A brass bulkhead clock on a wall facing -y."""
    M = mats(); at = Vector(at)
    KI.disc('clock-face', r, KI.image_mat('clock-face', png, 0.5), at)
    o = C.obj('clock-bezel', KI._torus(r * 1.06, r * 0.08), M['brass'], at + Vector((0, -0.004, 0))); o.rotation_euler = (deg(90), 0, 0)
    C.obj('clock-case', KI._cyl_y(r * 1.08, 0.03), M['brass'], at + Vector((0, 0.016, 0)))
    KI.disc('clock-glass', r, KI.glass_mat('clock-glass'), at + Vector((0, -0.006, 0)))

def steering_compass(heading, at=(0, 0, 0), pedestal=True, card_png=None, glow=None):
    """The pedestal compass: bowl, card turned so `heading` is under the forward lubber line (+Y), dome.
    glow: an RGB to light the card from inside (night)."""
    M = K.mats(); at = Vector(at)
    C.lathe('bowl', [(0.0, -0.02), (0.075, -0.02), (0.085, 0.0), (0.083, 0.012), (0.07, 0.016), (0.0, 0.016)], 96, M['dark'])
    bpy.data.objects['bowl'].location = at
    if pedestal:
        C.lathe('pedestal', [(0.0, -0.75), (0.06, -0.75), (0.055, -0.03), (0.07, -0.02), (0.0, -0.02)], 64, C.simple('pedestal', '#cfd2d4', 0.25, 1.0))
        bpy.data.objects['pedestal'].location = at
    card = KI.disc('card', 0.058, KI.image_mat('card', card_png or os.path.join(KI.TEX, 'card.png'), 0.45, 0.12 if glow else 0.0), at + Vector((0, 0, 0.022)), normal='Z+')
    card.rotation_euler = (0, 0, deg(heading))
    C.obj('lubber', C.rbox('lubber', (0.003, 0.004, 0.02), 0.0005, 1), C.simple('lubber', '#e0201a', 0.4, coat=0.5), at + Vector((0, 0.062, 0.03)))
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=64, v_segments=32, radius=0.07)
    for v in list(bm.verts):
        if v.co.z < 0: v.co.z = 0
    me = bpy.data.meshes.new('dome'); bm.to_mesh(me); bm.free(); me.shade_smooth()
    C.obj('dome', me, KI.glass_mat('dome-glass'), at + Vector((0, 0, 0.016)))
    if glow:
        ld = bpy.data.lights.new('compass-glow', 'POINT'); ld.energy = 0.25; ld.color = glow; ld.shadow_soft_size = 0.02
        lo = bpy.data.objects.new('compass-glow', ld); C.col.objects.link(lo); lo.location = at + Vector((0, 0.05, 0.05))
    return card

def raise_sea(dz):
    for o in bpy.data.objects:
        if o.name.startswith(('ocean', 'far-sea')): o.location.z += dz

# ---------------------------------------------------------------- outdoors (after art_nav_b.py)
def flat_mat(name, color, emit=0.0, rough=0.5):
    m, nt, b, _ = C.new_mat(name)
    C.setin(b, 'Base Color', C.lin(color)); C.setin(b, 'Roughness', rough)
    if emit: C.setin(b, 'Emission Color', C.lin(color)); C.setin(b, 'Emission Strength', emit)
    return m

def lighthouse(at, z0, h=26.0, r=2.6):
    """A white tower with a red band, black gallery, glazed lantern and red dome; returns the lantern centre."""
    white = flat_mat('lh-white', '#eeece6', rough=0.6); red = flat_mat('lh-red', '#b8261e', rough=0.45); black = flat_mat('lh-black', '#1a1b1d', rough=0.5)
    k = r / 2.6
    C.cyl('lh-tower', r, 1.8 * k, h, 32, white, (at[0], at[1], z0 + h / 2))
    C.cyl('lh-band', 2.25 * k, 2.05 * k, 3.0 * k, 32, red, (at[0], at[1], z0 + h * 0.62))
    C.cyl('lh-gallery', 2.5 * k, 2.5 * k, 0.4 * k, 32, black, (at[0], at[1], z0 + h + 0.2 * k))
    C.cyl('lh-lantern', 1.4 * k, 1.4 * k, 2.4 * k, 24, C.simple('lh-glass', '#2e3a40', 0.05, 0.3, coat=1.0), (at[0], at[1], z0 + h + 1.6 * k))
    C.cyl('lh-dome', 1.5 * k, 0.2 * k, 1.2 * k, 24, red, (at[0], at[1], z0 + h + 3.4 * k))
    C.obj('lh-house', C.rbox('lhh', (10 * k, 7 * k, 5 * k), 0.2, 2), white, (at[0] + 7 * k, at[1] + 2 * k, z0 + 2.5 * k))
    return Vector((at[0], at[1], z0 + h + 1.6 * k))

def headland(at, size=(240, 140, 70), seed=5, z_frac=0.25, name='headland'):
    """A noisy dome of dry land, sunk z_frac of its height."""
    from mathutils import noise as mnoise
    import kit_world as KW
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=64, v_segments=32, radius=1.0)
    for v in bm.verts:
        n = mnoise.noise(v.co * 2.5 + Vector((seed, 0, 0)))
        v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2])) * (1.0 + 0.12 * n)
    for f in bm.faces: f.smooth = True
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    return C.obj(name, me, KW.land_mat(), (at[0], at[1], -size[2] * z_frac))

def parallel_rule(a, b, side=1.0, gap=0.085):
    """Two black acrylic bars joined by brass links, one edge from a to b on the chart, the other `gap` to one side."""
    M = mats(); a, b = Vector(a), Vector(b); u = (b - a).normalized(); n = Vector((-u.y, u.x, 0)) * side; L = (b - a).length
    rz = math.atan2(u.y, u.x); acry = C.simple('rule-acrylic', '#141618', 0.18, coat=1.0)
    for k, off in ((0, 0.0275), (1, gap + 0.0275)):
        c = (a + b) / 2 + n * off + u * (0.02 * k)
        C.obj(f'prule-{k}', C.rbox('prule', (L, 0.055, 0.006), 0.002, 2), acry, (c.x, c.y, 0.004)).rotation_euler = (0, 0, rz)
    for t in (0.18, 0.82):
        c = a + u * (L * t) + n * (gap / 2 + 0.0275) + u * 0.01
        C.obj('prule-link', C.rbox('link', (0.016, gap + 0.02, 0.003), 0.003, 2), M['brass'], (c.x, c.y, 0.0085)).rotation_euler = (0, 0, rz - deg(15) * side)

def strip(name, a, b, w, mat, z=0.35): return A.strip(name, a, b, w, mat, z)
def dashed(name, a, b, w, mat, dash=4.0, gap=3.0, z=0.35):
    a, b = Vector(a), Vector(b); L = (b - a).length; u = (b - a) / L; s = 0.0
    while s < L:
        e = min(s + dash, L); A.strip(name, tuple(a + u * s), tuple(a + u * e), w, mat, z); s = e + gap
def ring(name, at, R, mat, z=0.4): return A.ring(name, at, R, mat, z)
def hdg_vec(h): return A.hdg_vec(h)
