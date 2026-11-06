# Bareboat-skipper test questions, figure type "compass": what the navigator has in front of him for the sum the
# question asks, with the figure's numbers and nothing more. A plotted true course: the chart on the chart table,
# the course pencilled through the chart's compass rose, the variation printed in the rose (as charts do), no
# magnetic ring to read the answer off. A compass course: the steering compass with that figure under the lubber
# line. A GPS bearing: the chartplotter at the helm showing it. Deviation goes in the notes. No plan.
# See q_misc.py for how to run it.
#   blender --background --factory-startup --python docs/design/blender/q_compass.py -- --id bs-042
#   python3 docs/design/blender/q_compass.py --all          ru.json for every compass question
import os, sys, math, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import q_misc as Q

def ew(v): return f'{abs(v)}°{"W" if v < 0 else "E"}'

def texts(f):
    """(labels' texts, note, lines) for a figure, in the 2D figure's own words (figures.js)."""
    course = f'{f.get("courseLabel", "True course")} {f["course"]:03d}°'
    var = f'Variation {ew(f.get("variation", 0))}'
    dev = f'Deviation {ew(f["deviation"])}' if f.get('deviation') is not None else None
    kind = scene(f)
    if kind == 'chart': return [course, var], f.get('note'), [dev] if dev else []
    return [course], f.get('note'), [l for l in (dev, var) if l]

def scene(f):
    lab = f.get('courseLabel', 'True course')
    return 'compass' if lab.startswith(('Compass', 'Steering compass')) else 'plotter' if lab.startswith('GPS') else 'chart'

RU_WORDS = {'True course': 'ИК', 'Variation': 'Склонение', 'Deviation': 'Девиация'}
def meta(x):
    f = x['figure']; labels, note, lines = texts(f)
    ru = dict(x['ru']); words = dict(RU_WORDS); words.update(x['ru'])
    for s in labels + lines:
        for en, r in sorted(words.items(), key=lambda kv: -len(kv[0])):
            if s.startswith(en + ' '): ru[s] = r + s[len(en):]; break
    english = labels + lines + ([note] if note else [])
    if x['id'] in PLANS and Q.LEVEL != 'bareboat-skipper':     # another level's plan: the compass error worked out
        P = PLANS[x['id']](f, x); Q.save(x['id'], 'plan.json', {'svg': P.svg()}); english += P.texts
        for t in P.texts: ru.setdefault(t, PLAN_RU.get(t, Q.ru_number(t)))
    else: Q.drop(x['id'], 'plan.json')
    Q.write_ru(x['id'], english, ru)

# ---------- plans for other levels (charter check-in): {svg}, shown with the answer ----------
def box3(P, x, y, top, big, kind='light'):
    P.rect(x - 150, y - 80, 300, 160, fill='var(--bg)', stroke='var(--accent)' if kind == 'accent' else 'var(--ink)', sw=5, rx=18)
    P.text(x, y - 30, top, 30, 400, fill='var(--muted)', halo=False); P.text(x, y + 42, big, 60, halo=False)

def plan_deviation(f, x):
    """Compass, magnetic, true in a row, with the corrections between them; deviation is what is left over."""
    c, v = f['course'], f.get('variation', 0); t = int(re.search(r'COG (\d+)', f['note']).group(1)); dev = t - v - c
    P = Q.Plan('What the compass error is made of', [f'{c:03d}° compass + {abs(v)}°{"E" if v >= 0 else "W"} variation = {c + v:03d}°: the other {abs(dev)}° is deviation',
                                                     'Look for a phone or speaker by the binnacle; note what remains'], PLAN_RU)
    box3(P, 220, 220, 'compass', f'{c:03d}°'); box3(P, 640, 220, 'magnetic', f'{c + dev:03d}°'); box3(P, 1060, 220, 'true · plotter COG', f'{t:03d}°', 'accent')
    P.arrow(375, 220, 485, 220, w=6); P.arrow(795, 220, 905, 220, w=6)
    P.pill(430, 380, f'deviation {abs(dev)}°{"E" if dev >= 0 else "W"}', 'red', 32); P.pill(850, 380, f'variation {abs(v)}°{"E" if v >= 0 else "W"}', 'light', 32)
    P.pill(640, 500, 'a phone or speaker by the binnacle?', 'accent', 30)
    return P

PLANS = {'ci-313': plan_deviation}
PLAN_RU = {'What the compass error is made of': 'Из чего складывается ошибка компаса',
           '090° compass + 3°E variation = 093°: the other 5° is deviation': '090° по компасу + 3°E склонение = 093°: остальные 5° — девиация',
           'Look for a phone or speaker by the binnacle; note what remains': 'Ищите телефон или динамик у нактоуза; остаток запишите',
           'compass': 'компас', 'magnetic': 'магнитный', 'true · plotter COG': 'истинный, COG',
           'deviation 5°E': 'девиация 5°E', 'variation 3°E': 'склонение 3°E', 'a phone or speaker by the binnacle?': 'телефон или динамик у нактоуза?'}

# ---------- textures (system Python, Pillow) ----------
CHART_W, CHART_H, PX_W, PX_H = 0.80, 0.5333, 2400, 1600
ROSE = (1150, 860, 330)

def faces():
    from PIL import Image, ImageDraw, ImageFont
    BOLD = '/System/Library/Fonts/Supplemental/Arial Bold.ttf'; REG = '/System/Library/Fonts/Supplemental/Arial.ttf'
    ITAL = '/System/Library/Fonts/Supplemental/Arial Italic.ttf'
    F = lambda p, n: ImageFont.truetype(p, n)
    kind, out, a = Q.face_args()
    if kind == 'chart':
        course, var = int(a[0]), int(a[1])
        im = Image.new('RGB', (PX_W, PX_H), (236, 243, 244)); d = ImageDraw.Draw(im)
        coast = [(40, 40), (900, 40), (860, 120), (720, 170), (600, 300), (430, 360), (300, 520), (160, 600), (40, 640)]
        for k, col in ((150, (214, 232, 240)), (85, (200, 225, 238)), (35, (178, 214, 210))):
            d.polygon([(x + k * 0.8, y + k * 0.7) for x, y in coast], fill=col)
        d.polygon(coast, fill=(243, 229, 178)); d.line(coast[1:-1], fill=(90, 72, 40), width=4)
        for x, y, t in ((560, 620, '18'), (900, 420, '27'), (1500, 300, '41'), (1900, 520, '48'), (2100, 1100, '55'), (500, 1100, '33'),
                        (800, 1420, '46'), (1700, 1450, '58'), (2200, 300, '52'), (300, 900, '24'), (1600, 1200, '50'), (1950, 800, '51')):
            d.text((x, y), t, font=F(ITAL, 34), fill=(60, 70, 80), anchor='mm')
        cx, cy, R = ROSE; mag = (150, 40, 110)
        d.ellipse([cx - R, cy - R, cx + R, cy + R], outline=mag, width=5)
        d.ellipse([cx - R + 60, cy - R + 60, cx + R - 60, cy + R - 60], outline=mag, width=2)
        for deg in range(0, 360, 2):
            t = math.radians(deg); r0 = R - (40 if deg % 10 == 0 else 22)
            d.line([(cx + math.sin(t) * r0, cy - math.cos(t) * r0), (cx + math.sin(t) * R, cy - math.cos(t) * R)], fill=mag, width=3 if deg % 10 == 0 else 2)
        for deg in range(0, 360, 30):
            t = math.radians(deg); tx = Image.new('RGBA', (160, 80), (0, 0, 0, 0))
            ImageDraw.Draw(tx).text((80, 40), f'{deg:03d}', font=F(REG, 34), fill=mag + (255,), anchor='mm')
            tx = tx.rotate(-deg, expand=True, resample=Image.BICUBIC)
            im.paste(tx, (int(cx + math.sin(t) * (R - 78) - tx.width / 2), int(cy - math.cos(t) * (R - 78) - tx.height / 2)), tx)
        d.polygon([(cx, cy - R + 8), (cx - 18, cy - R + 70), (cx + 18, cy - R + 70)], fill=mag)          # true north
        t = math.radians(var); tip = (cx + math.sin(t) * (R - 110), cy - math.cos(t) * (R - 110))      # magnetic north, half-arrow
        d.line([(cx, cy), tip], fill=mag, width=4)
        uu, nn = (math.sin(t), -math.cos(t)), (math.cos(t), math.sin(t))
        d.polygon([tip, (tip[0] - uu[0] * 44 + nn[0] * 14, tip[1] - uu[1] * 44 + nn[1] * 14), (tip[0] - uu[0] * 44, tip[1] - uu[1] * 44)], fill=mag)
        d.text((cx, cy + 70), f'VAR {abs(var)}°{"W" if var < 0 else "E"} (2026)', font=F(BOLD, 34), fill=mag, anchor='mm')
        # the course, pencilled through the rose with its arrowheads
        pen = (62, 62, 66); u = (math.sin(math.radians(course)), -math.cos(math.radians(course)))
        p0 = (cx - u[0] * 700, cy - u[1] * 700); p1 = (cx + u[0] * 1000, cy + u[1] * 1000)
        d.line([p0, p1], fill=pen, width=5)
        for s in (620, 660):
            q = (cx + u[0] * s, cy + u[1] * s); n = (-u[1], u[0])
            d.line([(q[0] - u[0] * 30 + n[0] * 18, q[1] - u[1] * 30 + n[1] * 18), q, (q[0] - u[0] * 30 - n[0] * 18, q[1] - u[1] * 30 - n[1] * 18)], fill=pen, width=5)
        d.rectangle([20, 20, PX_W - 20, PX_H - 20], outline=(20, 20, 20), width=4)
        im.save(out)
    elif kind == 'plotter':
        brg = int(a[0]); front = os.path.join(Q.HERE, 'textures', 'axiom-front.png')
        sw, sh = 920, 610; sc = Image.new('RGB', (sw, sh), (212, 236, 247)); d = ImageDraw.Draw(sc)
        d.polygon([(0, 0), (380, 0), (330, 80), (180, 150), (0, 190)], fill=(240, 221, 150), outline=(138, 122, 64))
        d.polygon([(560, 610), (700, 470), (920, 420), (920, 610)], fill=(240, 221, 150), outline=(138, 122, 64))
        for x, y, t in ((420, 260, '24'), (700, 230, '38'), (260, 420, '31'), (820, 330, '45'), (540, 520, '19')):
            d.text((x, y), t, font=F(ITAL, 22), fill=(70, 100, 130), anchor='mm')
        bx, by = 600, 230; u = (math.sin(math.radians(brg)), -math.cos(math.radians(brg))); wx, wy = bx + u[0] * 260, by + u[1] * 260
        for k in range(0, 260, 22): d.line([(bx + u[0] * k, by + u[1] * k), (bx + u[0] * (k + 12), by + u[1] * (k + 12))], fill=(216, 27, 42), width=5)
        d.ellipse([wx - 13, wy - 13, wx + 13, wy + 13], outline=(216, 27, 42), width=5); d.text((wx + 22, wy), 'WPT 1', font=F(BOLD, 22), fill=(30, 30, 30), anchor='lm')
        d.polygon([(bx, by - 22), (bx + 13, by + 14), (bx, by + 7), (bx - 13, by + 14)], fill=(17, 17, 17))
        d.rectangle([0, 0, sw, 64], fill=(18, 22, 28)); d.text((24, 32), 'WPT 1', font=F(BOLD, 30), fill=(232, 238, 242), anchor='lm')
        d.text((300, 32), 'BRG', font=F(REG, 26), fill=(159, 178, 194), anchor='lm'); d.text((370, 32), f'{brg:03d}°T', font=F(BOLD, 34), fill=(232, 238, 242), anchor='lm')
        fr = Image.open(front).convert('RGB'); x0, y0, x1, y1 = 70, 72, 645, 432
        fr.paste(sc.resize((x1 - x0, y1 - y0), Image.LANCZOS), (x0, y0)); fr.save(out)

if '--face' in sys.argv: faces(); sys.exit(0)

if not Q.IN_BLENDER:
    xs = Q.items('compass') if Q.flag('--all') else [Q.item('compass', Q.arg('--id', 'bs-042'))]
    for x in xs: meta(x); print(x['id'], scene(x['figure']), texts(x['figure']))
    sys.exit(0)

# ---------- the render (Blender) ----------
import bpy, bmesh
from mathutils import Vector
import common as C, kit as K, kit_instruments as KI
ME = os.path.abspath(__file__)

def img_plane(name, w, h, path, loc, rough=0.8):
    me = bpy.data.meshes.new(name)
    me.from_pydata([(-w / 2, -h / 2, 0), (w / 2, -h / 2, 0), (w / 2, h / 2, 0), (-w / 2, h / 2, 0)], [], [(0, 1, 2, 3)])
    me.uv_layers.new(name='UVMap').data.foreach_set('uv', [0, 0, 1, 0, 1, 1, 0, 1])
    return C.obj(name, me, KI.image_mat(name, path, rough), Vector(loc))

def chart(f):
    """The chart table: a teak top with fiddles, the chart, a pencil and a parallel rule, cabin light."""
    M = K.mats(); jo = KI.joinery_mat()
    C.obj('table', C.rbox('table', (1.1, 0.75, 0.04), 0.006, 2), jo, (0.05, 0.02, -0.02))
    C.obj('fiddle-front', C.rbox('fiddle', (1.1, 0.025, 0.035), 0.008, 2), jo, (0.05, -0.36, 0.015))
    C.obj('fiddle-back', C.rbox('fiddle', (1.1, 0.025, 0.06), 0.008, 2), jo, (0.05, 0.40, 0.03))
    KI.wall('bulkhead', -0.75, 0.75, -0.05, 0.6, 0.41, jo)
    img_plane('chart', CHART_W, CHART_H, Q.face(ME, 'chart', str(f['course']), str(f.get('variation', 0))), (0.0, 0.0, 0.0012), 0.85)
    P = lambda px, py: Vector(((px / PX_W - 0.5) * CHART_W, (0.5 - py / PX_H) * CHART_H, 0.0012))
    cx, cy, R = ROSE; u = (math.sin(math.radians(f['course'])), -math.cos(math.radians(f['course'])))
    # the parallel rule laid along the course, just beside the pencilled line
    acry = C.simple('acrylic', '#141618', 0.18, coat=1.0); n = (-u[1], u[0])
    a0 = P(cx + u[0] * 380 + n[0] * 140, cy + u[1] * 380 + n[1] * 140); a1 = P(cx + u[0] * 1000 + n[0] * 140, cy + u[1] * 1000 + n[1] * 140)
    rl = C.obj('rule', C.rbox('rule', ((a1 - a0).length, 0.05, 0.006), 0.002, 2), acry, ((a0 + a1) / 2 + Vector((0, 0, 0.004))))
    rl.rotation_euler = (0, 0, math.atan2(a1.y - a0.y, a1.x - a0.x))
    pen_at = P(700, 1320)
    C.cyl('pencil', 0.0042, 0.0042, 0.17, 6, C.simple('pencil', '#e8b818', 0.45, coat=0.4), pen_at + Vector((0, 0, 0.004)), (0, math.radians(90), math.radians(20)))
    K.day_sky(sun_az=200, sun_el=40, strength=0.05)
    KI.area_light((0.0, -0.15, 0.9), (0.0, 0.0, 0.0), 12, 0.35, (1.0, 0.86, 0.68))
    KI.area_light((0.9, -0.3, 0.45), (0.0, 0.05, 0.0), 16, 0.4, (0.85, 0.92, 1.0))
    rose = P(cx, cy)
    K.camera((rose.x + 0.03, rose.y - 0.34, 0.40), (rose.x + 0.07, rose.y + 0.035, 0.0), 34)
    lab, _, _ = texts(f)
    on_line = P(cx + u[0] * 520, cy + u[1] * 520); var_at = P(cx - R - 10, cy - 60)
    return [(tuple(on_line + Vector((0, 0, 0.01))), lab[0], 'blue'), (tuple(var_at), lab[1])], -0.2

def compass(f):
    """The pedestal steering compass seen from the helm, the course under the lubber line (art_nav_a.py fig 3)."""
    M = K.mats()
    C.lathe('bowl', [(0.0, -0.02), (0.075, -0.02), (0.085, 0.0), (0.083, 0.012), (0.07, 0.016), (0.0, 0.016)], 96, M['dark'])
    C.lathe('pedestal', [(0.0, -0.75), (0.06, -0.75), (0.055, -0.03), (0.07, -0.02), (0.0, -0.02)], 64, C.simple('pedestal', '#cfd2d4', 0.25, 1.0))
    import subprocess; os.makedirs(Q.FACES, exist_ok=True); card_png = os.path.join(Q.FACES, 'compass-card.png')
    subprocess.run(['python3', os.path.join(Q.HERE, 'make_faces.py'), 'card', card_png], check=True)
    card = KI.disc('card', 0.058, KI.image_mat('card', card_png, 0.45), (0, 0, 0.022), normal='Z+')
    card.rotation_euler = (0, 0, math.radians(f['course']))       # the course comes to the forward lubber line (+Y)
    C.obj('lubber', C.rbox('lubber', (0.003, 0.004, 0.02), 0.0005, 1), C.simple('lubber', '#e0201a', 0.4, coat=0.5), (0, 0.062, 0.03))
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=64, v_segments=32, radius=0.07)
    for v in list(bm.verts):
        if v.co.z < 0: v.co.z = 0
    me = bpy.data.meshes.new('dome'); bm.to_mesh(me); bm.free(); me.shade_smooth()
    C.obj('dome', me, KI.glass_mat('dome-glass'), (0, 0, 0.016))
    K.sea('breeze', center=(0, 0)); K.day_sky(sun_az=230, sun_el=45)
    for o in bpy.data.objects:
        if o.name.startswith(('ocean', 'far-sea')): o.location.z -= 1.4
    KI.wall('sole', -1.5, 1.5, -1.5, 1.5, 0, M['teak'])
    sole = bpy.data.objects['sole']; sole.data.vertices.foreach_set('co', [-1.2, -1.5, -0.75, 1.2, -1.5, -0.75, 1.2, 1.5, -0.75, -1.2, 1.5, -0.75]); sole.data.update()
    K.camera((0.0, -0.46, 0.36), (0, 0.035, -0.02), 40)
    lab, _, _ = texts(f)
    return [((0, 0.065, 0.06), lab[0], 'blue')], -0.4

def plotter(f):
    """The chartplotter on its pod at the helm, by day, the bearing to the waypoint in its data bar."""
    M = K.mats()
    pod = C.obj('pod', C.rbox('pod', (0.34, 0.16, 0.14), 0.04, 4), M['dark'], (0.0, 0.03, -0.09))
    C.cyl('binnacle', 0.06, 0.07, 0.9, 32, C.simple('binnacle', '#c9cdd1', 0.25, 1.0), (0.0, 0.03, -0.6))
    root, objs = K.load_model('chartplotter-raymarine-axiom.glb', drop_planes=False)
    bpy.context.view_layer.update(); lo, hi = K.bbox([o for o in objs if o.type == 'MESH'])
    k = 0.235 / (hi.x - lo.x); root.scale = (k,) * 3; bpy.context.view_layer.update()
    lo, hi = K.bbox([o for o in objs if o.type == 'MESH'])
    root.location = (root.location.x - (lo.x + hi.x) / 2, root.location.y - (lo.y + hi.y) / 2, root.location.z - lo.z - 0.02)
    root.rotation_euler = (math.radians(-12), 0, 0)
    img = bpy.data.images.load(Q.face(ME, 'plotter', str(f['course'])))
    for o in objs:
        for sl in getattr(o, 'material_slots', []):
            if sl.material and sl.material.name.startswith('raymarine--displays'):
                m, nt, b, out = C.new_mat('axiom-screen')
                uv = nt.nodes.new('ShaderNodeUVMap'); tx = nt.nodes.new('ShaderNodeTexImage'); tx.image = img
                nt.links.new(uv.outputs['UV'], tx.inputs['Vector']); b.inputs['Base Color'].default_value = (0.01, 0.01, 0.012, 1)
                nt.links.new(tx.outputs['Color'], b.inputs['Emission Color']); b.inputs['Emission Strength'].default_value = 1.6
                b.inputs['Roughness'].default_value = 0.12; b.inputs['Coat Weight'].default_value = 1.0
                sl.material = m
    bpy.ops.mesh.primitive_torus_add(major_radius=0.55, minor_radius=0.018, location=(0.0, -0.32, -0.25), rotation=(math.radians(80), 0, 0))
    w = bpy.context.active_object; w.data.materials.append(C.simple('wheel', '#1d1e20', 0.5)); [setattr(p, 'use_smooth', True) for p in w.data.polygons]
    deckm = bpy.data.meshes.new('cockpit'); deckm.from_pydata([(-3, -3, -1.0), (3, -3, -1.0), (3, 3, -1.0), (-3, 3, -1.0)], [], [(0, 1, 2, 3)])
    C.obj('cockpit', deckm, M['teak'])
    K.sea('breeze')
    for o in bpy.data.objects:
        if o.name.startswith(('ocean', 'far-sea')): o.location.z -= 2.4
    K.day_sky(sun_az=150, sun_el=40, strength=0.2)
    bpy.context.view_layer.update(); lo, hi = K.bbox([o for o in objs if o.type == 'MESH'])
    c = (lo + hi) / 2
    K.camera((0.06, -0.56, 0.24), tuple(c + Vector((0.01, 0, -0.008))), 50)
    lab, _, _ = texts(f)
    return [((c.x - 0.03, c.y, hi.z + 0.004), lab[0], 'blue')], -0.3

def render(x):
    f = x['figure']; C.reset()
    labels, expo = {'chart': chart, 'compass': compass, 'plotter': plotter}[scene(f)](f)
    _, note, lines = texts(f)
    if not note and lines: note, lines = lines[0], lines[1:]
    C.render(Q.out_jpg(x['id']), Q.arg('--samples', 128), Q.arg('--scale', 100), expo, labels, note, space='blender', extra={'lines': lines})

x = Q.item('compass', Q.arg('--id', 'bs-042'))
meta(x)
render(x)
