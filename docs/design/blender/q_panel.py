# Bareboat-skipper test questions, figure type "panel": the instruments the question's gauges stand for, close up,
# each showing exactly the figure's value: the engine panel (dials for temperature, volts, revs, amps, fuel, heel;
# the OIL, CHARGE and TEMP warning lamps), the battery monitor (a backlit tile per reading), the gas control panel,
# the CO alarm, the saloon extinguisher with its gauge. A gauge flagged as an alarm reads in the red, or its lamp is
# lit, and its pill is red. Printed: the gauges' own names and values and the figure's lines, nothing else.
# See q_misc.py for how to run it.
#   blender --background --factory-startup --python docs/design/blender/q_panel.py -- --id bs-083
#   python3 docs/design/blender/q_panel.py --all          ru.json for every panel question (panels have no plan)
import os, sys, math, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import q_misc as Q

def num(v):
    m = re.match(r'^-?[\d.]+', v); return float(m.group()) if m else None

def pill(g):
    return f'{g[0]} {g[1]}'

def ru_value(v, ru):
    if v in ru: return ru[v]
    return re.sub(r'(\d)\.(\d)', r'\1,\2', v)

def layout(f):
    names = {g[0] for g in f['gauges']}
    if 'CO alarm' in names: return 'co'
    if 'Gas solenoid' in names: return 'gas'
    if 'Extinguisher' in names: return 'fire'
    if names & {'Temp', 'Oil', 'RPM', 'Heel', 'Burn'} or any(g[0] == 'Volts' for g in f['gauges']): return 'engine'
    return 'monitor'

def meta(x):
    f = x['figure']; ru = dict(x['ru'])
    english = [pill(g) for g in f['gauges']] + list(f.get('lines', []))
    for g in f['gauges']: ru[pill(g)] = f'{ru.get(g[0], g[0])} {ru_value(g[1], ru)}'
    Q.drop(x['id'], 'plan.json')
    Q.write_ru(x['id'], english, ru)

# ---------- faces (system Python, Pillow) ----------
def faces():
    from PIL import Image, ImageDraw, ImageFont
    BOLD = '/System/Library/Fonts/Supplemental/Arial Bold.ttf'; REG = '/System/Library/Fonts/Supplemental/Arial.ttf'
    F = lambda p, n: ImageFont.truetype(p, n)
    kind, out, a = Q.face_args()
    S = 1024; Cc = S / 2
    def dial(labels, a0, a1, minor, reds=(), caption=(), light=False, font=92):
        bg, ink = ((236, 234, 226), (25, 25, 25)) if light else ((14, 15, 17), (235, 235, 230))
        im = Image.new('RGB', (S, S), bg); d = ImageDraw.Draw(im); R = 470
        for f0, f1, col in reds:
            d.arc([Cc - R, Cc - R, Cc + R, Cc + R], -90 + a0 + (a1 - a0) * f0, -90 + a0 + (a1 - a0) * f1, fill=col, width=34)
        n = (len(labels) - 1) * minor
        for i in range(n + 1):
            t = math.radians(a0 + (a1 - a0) * i / n); major = i % minor == 0; ri = R - (60 if major else 32)
            d.line([(Cc + math.sin(t) * ri, Cc - math.cos(t) * ri), (Cc + math.sin(t) * R, Cc - math.cos(t) * R)], fill=ink, width=12 if major else 6)
            if major and labels[i // minor]:
                rr = R - 130; d.text((Cc + math.sin(t) * rr, Cc - math.cos(t) * rr), labels[i // minor], font=F(BOLD, font), fill=ink, anchor='mm')
        for k, (txt, size) in enumerate(caption):
            d.text((Cc, Cc + 150 + k * 90), txt, font=F(BOLD if k == 0 else REG, size), fill=ink, anchor='mm')
        im.save(out)
    RED, GRN = (200, 30, 30), (40, 150, 60)
    if kind == 'temp': dial(['40', '60', '80', '100', '120'], -60, 60, 4, [(0.75, 1, RED)], [('°C', 80), ('WATER', 56)])
    elif kind == 'volts': dial(['8', '10', '12', '14', '16'], -60, 60, 4, [(0, 0.25, RED), (0.875, 1, RED)], [('VOLTS', 64)])
    elif kind == 'tach': dial(['0', '1', '2', '3', '4'], -135, 135, 5, [(0.875, 1, RED)], [('x1000 r/min', 52), ('RPM', 48)], font=110)
    elif kind == 'amps': dial(['0', '20', '40', '60'], -60, 60, 4, [], [('AMPS', 64)])
    elif kind == 'litres': dial(['0', '25', '50', '75', '100'], -60, 60, 2, [(0, 0.125, RED)], [('LITRES', 60)], font=78)
    elif kind == 'fuel': dial(['E', '¼', '½', '¾', 'F'], -60, 60, 2, [(0, 0.125, RED)], [('FUEL', 64)], font=100)
    elif kind == 'heel': dial(['40', '20', '0', '20', '40'], -60, 60, 2, [], [('HEEL °', 60)])
    elif kind == 'extinguisher':
        im = Image.new('RGB', (S, S), (236, 234, 226)); d = ImageDraw.Draw(im); R = 440
        for f0, f1, col in ((0, 0.33, RED), (0.33, 0.72, GRN), (0.72, 1, RED)):
            d.arc([Cc - R, Cc - R, Cc + R, Cc + R], -90 - 60 + 120 * f0, -90 - 60 + 120 * f1, fill=col, width=90)
        d.text((Cc - 250, Cc - 30), 'RECHARGE', font=F(BOLD, 52), fill=RED, anchor='mm'); d.text((Cc + 250, Cc - 30), 'OVER', font=F(BOLD, 52), fill=RED, anchor='mm')
        d.text((Cc, Cc + 140), 'PRESSURE', font=F(BOLD, 64), fill=(25, 25, 25), anchor='mm'); im.save(out)
    elif kind == 'engine-plate':
        w, h = 2400, 1300; im = Image.new('RGB', (w, h), (26, 27, 30)); d = ImageDraw.Draw(im)
        d.rounded_rectangle([12, 12, w - 12, h - 12], 50, outline=(70, 72, 76), width=7)
        for x, t in ((230, 'OIL'), (700, 'CHARGE'), (1170, 'TEMP'), (1560, 'KEY'), (1840, 'START'), (2110, 'STOP')):
            d.text((x, 1190), t, font=F(BOLD, 62), fill=(200, 200, 195), anchor='mm')
        im.save(out)
    elif kind == 'monitor-plate':
        w, h = 2400, 1300; im = Image.new('RGB', (w, h), (26, 27, 30)); d = ImageDraw.Draw(im)
        d.rounded_rectangle([12, 12, w - 12, h - 12], 50, outline=(70, 72, 76), width=7)
        d.text((w / 2, 120), 'BATTERY MONITOR', font=F(BOLD, 72), fill=(200, 200, 195), anchor='mm'); im.save(out)
    elif kind == 'gas-plate':
        w, h = 1600, 1000; im = Image.new('RGB', (w, h), (236, 234, 228)); d = ImageDraw.Draw(im)
        d.rounded_rectangle([10, 10, w - 10, h - 10], 40, outline=(150, 150, 145), width=6)
        d.text((400, 120), 'GAS SOLENOID', font=F(BOLD, 76), fill=(30, 30, 30), anchor='mm')
        d.text((1200, 120), 'GAS ALARM', font=F(BOLD, 76), fill=(30, 30, 30), anchor='mm')
        for x, t in ((400, a[0]), (1200, a[1])): d.text((x, 860), t, font=F(BOLD, 70), fill=(30, 30, 30), anchor='mm')
        d.line([(800, 200), (800, 920)], fill=(170, 170, 165), width=5); im.save(out)
    elif kind == 'co-screen':
        im = Image.new('RGB', (640, 300), (30, 6, 6)); d = ImageDraw.Draw(im)
        d.text((320, 95), 'CO', font=F(BOLD, 110), fill=(255, 80, 60), anchor='mm'); d.text((320, 225), a[0], font=F(BOLD, 96), fill=(255, 80, 60), anchor='mm'); im.save(out)
    elif kind == 'co-plate':
        im = Image.new('RGB', (800, 800), (241, 240, 236)); d = ImageDraw.Draw(im)
        d.text((400, 700), 'CARBON MONOXIDE ALARM', font=F(BOLD, 46), fill=(60, 60, 60), anchor='mm')
        for k in range(6): d.ellipse([200 + k * 70, 560, 230 + k * 70, 590], fill=(150, 150, 150))
        im.save(out)
    elif kind == 'blanket':
        im = Image.new('RGB', (600, 800), (190, 22, 28)); d = ImageDraw.Draw(im)
        d.text((300, 300), 'FIRE', font=F(BOLD, 120), fill=(255, 255, 255), anchor='mm'); d.text((300, 440), 'BLANKET', font=F(BOLD, 100), fill=(255, 255, 255), anchor='mm')
        d.text((300, 640), 'PULL', font=F(BOLD, 70), fill=(255, 255, 255), anchor='mm'); im.save(out)
    elif kind == 'ext-label':
        im = Image.new('RGB', (600, 900), (190, 22, 28)); d = ImageDraw.Draw(im)
        d.rectangle([60, 160, 540, 740], fill=(242, 240, 232))
        d.text((300, 260), 'FIRE', font=F(BOLD, 90), fill=(190, 22, 28), anchor='mm'); d.text((300, 370), 'EXTINGUISHER', font=F(BOLD, 52), fill=(190, 22, 28), anchor='mm')
        d.text((300, 520), '2 kg', font=F(BOLD, 80), fill=(30, 30, 30), anchor='mm'); d.text((300, 640), 'ABC POWDER', font=F(REG, 50), fill=(30, 30, 30), anchor='mm'); im.save(out)

if '--face' in sys.argv: faces(); sys.exit(0)

if not Q.IN_BLENDER:
    xs = Q.items('panel') if Q.flag('--all') else [Q.item('panel', Q.arg('--id', 'bs-083'))]
    for x in xs: meta(x); print(x['id'], layout(x['figure']), '+ ru')
    sys.exit(0)

# ---------- the render (Blender) ----------
import bpy, bmesh
from mathutils import Vector
import common as C, kit as K, kit_instruments as KI
ME = os.path.abspath(__file__)
def face(kind, *a): return Q.face(ME, kind, *a)
_s = open(os.path.join(Q.HERE, 'art_systems.py')).read(); exec(_s[_s.index('def rect('):_s.index('def panel_base(')], globals())   # rect(), lamp()

def lamp(x, z, color, lit):
    """A warning lamp: lit, it glows strongly; unlit, dark glass, so the two can never be confused."""
    rgb = {'red': (1.0, 0.08, 0.05), 'amber': (1.0, 0.55, 0.05), 'green': (0.1, 1.0, 0.2)}[color]
    m, nt, b, out = C.new_mat('lamp-%s-%d' % (color, lit))
    if lit:
        em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = rgb + (1,); em.inputs['Strength'].default_value = 2.8
        nt.links.new(em.outputs[0], out.inputs['Surface'])
    else:
        C.setin(b, 'Base Color', tuple(c * 0.06 for c in rgb) + (1,)); C.setin(b, 'Roughness', 0.35); C.setin(b, 'Coat Weight', 0.4)
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=12, radius=0.0075)
    for v in bm.verts: v.co.y = min(v.co.y, 0.0) * 0.8
    me = bpy.data.meshes.new('lamp'); bm.to_mesh(me); bm.free(); me.shade_smooth()
    C.obj('lamp', me, m, Vector((x, -0.0012, z)))
    if lit:
        ld = bpy.data.lights.new('lampglow', 'POINT'); ld.energy = 0.15; ld.color = rgb; ld.shadow_soft_size = 0.005
        lo = bpy.data.objects.new('lampglow', ld); C.col.objects.link(lo); lo.location = (x, -0.015, z)

def lcd(w, h, text):
    out = os.path.join(Q.FACES, 'lcd-%d-%d-%s.png' % (w, h, re.sub(r'[^A-Za-z0-9]', '', text)[:40]))
    os.makedirs(Q.FACES, exist_ok=True)
    import subprocess; subprocess.run(['python3', os.path.join(Q.HERE, 'art_systems_faces.py'), 'lcd', out, str(w), str(h), text], check=True)
    return out

# needle angle (clockwise from 12 o'clock) for a value on each dial
DIAL = {'temp': (40, 120, -60, 60), 'volts': (8, 16, -60, 60), 'tach': (0, 4000, -135, 135), 'amps': (0, 60, -60, 60),
        'litres': (0, 100, -60, 60), 'fuel': (0, 1, -60, 60), 'heel': (-40, 40, -60, 60)}
def angle(kind, v):
    lo, hi, a0, a1 = DIAL[kind]; v = max(lo - (hi - lo) * 0.04, min(hi + (hi - lo) * 0.04, v))
    return a0 + (a1 - a0) * (v - lo) / (hi - lo)

def dial_kind(g):
    n, v = g[0], g[1]
    if n == 'Temp': return 'temp', num(v)
    if n == 'Volts': return 'volts', num(v)
    if n == 'RPM': return 'tach', num(v)
    if n == 'Charge' and v.endswith('A'): return 'amps', num(v)
    if n == 'Fuel': return ('fuel', {'1/4': 0.25, '1/2': 0.5, '3/4': 0.75}.get(v, 0.5)) if '/' in v else ('litres', num(v))
    if n == 'Heel': return 'heel', num(v)
    return None, None

def bulkhead(mat=None):
    M = K.mats(); KI.wall('bulkhead', -0.9, 0.9, -0.6, 0.6, 0.012, mat or M['hull'])

def camera_on(cx, cz, w):
    """Square on to the bulkhead, a little from the right, the panel in the lower part of the frame (the notes sit
    over the top)."""
    d = w * 1.35
    K.camera((cx + 0.04 * d, -d, cz + 0.08 * d), (cx, 0, cz + 0.06 * w), 40)

def engine(f):
    """The engine panel: up to three dials across the top, the warning lamps below left, key, start and stop."""
    M = K.mats(); W, H = 0.40, 0.2167; bulkhead()
    C.obj('panel', C.rbox('panel', (W + 0.012, 0.012, H + 0.012), 0.006, 3), M['dark'], (0.0, 0.006, 0.0))
    rect('plate', W, H, face('engine-plate'), (0, -0.0004, 0), 0.0, 0.5)
    P = lambda x, y: ((x / 2400 - 0.5) * W, (0.5 - y / 1300) * H)
    labels = []; lines = list(f.get('lines', [])); gs = f['gauges']
    dials = [(g, *dial_kind(g)) for g in gs if dial_kind(g)[0]]
    n = len(dials); r = 0.046 if n <= 2 else 0.042
    xs = {1: [0.0], 2: [-0.07, 0.07], 3: [-0.125, 0.0, 0.125]}.get(n, [])
    zc = 0.035
    for (g, kind, v), x in zip(dials, xs):
        KI.gauge(face(kind), (x, -0.001, zc), r, value_angle=angle(kind, v))
        labels.append(((x, 0, zc + r + 0.008), pill(g), 'red') if g[2] else ((x, 0, zc + r + 0.008), pill(g)))
    # lamps: lit for an alarm on oil, temperature or charge, or when the figure's lines say the charge light is on
    by = {g[0]: g for g in gs}
    txt = ' '.join(lines).lower()
    lit = {'OIL': bool(by.get('Oil', [0, 0, False])[2]), 'TEMP': bool(by.get('Temp', [0, 0, False])[2]),
           'CHARGE': bool(by.get('Charge', [0, '', False])[2] and by['Charge'][1] == 'ON') or ('charge' in txt and 'light' in txt and ' on' in txt and 'off' not in txt)}
    for xx, name in ((230, 'OIL'), (700, 'CHARGE'), (1170, 'TEMP')):
        x, z = P(xx, 1060); lamp(x, z, 'red' if name != 'CHARGE' else 'amber', lit[name])
        g = by.get({'OIL': 'Oil', 'CHARGE': 'Charge', 'TEMP': 'Temp'}[name])
        if g and not dial_kind(g)[0]:     # a gauge drawn as its lamp: the pill points at the lamp
            labels.append(((x, 0, z + 0.012), pill(g), 'red') if g[2] else ((x, 0, z + 0.012), pill(g)))
    # key at ON, start and stop
    x, z = P(1560, 1060); C.obj('key', KI._cyl_y(0.016, 0.01), M['chrome'], (x, -0.005, z))
    kb = C.obj('key-bit', C.rbox('kb', (0.007, 0.022, 0.024), 0.002, 2), M['dark'], (x, -0.017, z)); kb.rotation_euler = (0, math.radians(90), 0)
    for i, (xx, col) in enumerate(((1840, '#2a8a3a'), (2110, '#b3261e'))):
        bx, bz = P(xx, 1060); C.obj('button', KI._cyl_y(0.011, 0.008), C.simple('btn%d' % i, col, 0.4, coat=0.5), (bx, -0.004, bz))
    extra = [g for g in gs if g[0] in ('Burn', 'Speed')]
    if extra:   # instruments beside the panel, one per reading the figure gives (speed log, fuel flow)
        for k, g in enumerate(extra):
            xx = 0.29 + 0.12 * k
            C.obj('inst', C.rbox('inst', (0.1, 0.014, 0.1), 0.008, 3), M['dark'], (xx, 0.0, 0.0))
            rect('inst-screen', 0.082, 0.062, lcd(480, 362, f'{g[0].upper()}|{g[1]}'), (xx, -0.0075, 0.004), 1.2, 0.3)
            labels.append(((xx, 0, 0.055), pill(g)))
        K.day_sky(sun_az=200, sun_el=35, strength=0.18); camera_on(0.09, 0.0, 0.66)
    else:
        K.day_sky(sun_az=200, sun_el=35, strength=0.18); camera_on(0.0, 0.0, 0.44)
    return labels, -0.6

def monitor(f):
    """The battery monitor: a backlit tile per reading, red when the figure flags it."""
    M = K.mats(); W, H = 0.40, 0.2167; bulkhead(KI.joinery_mat())
    C.obj('panel', C.rbox('panel', (W + 0.012, 0.012, H + 0.012), 0.006, 3), M['dark'], (0.0, 0.006, 0.0))
    rect('plate', W, H, face('monitor-plate'), (0, -0.0004, 0), 0.0, 0.5)
    gs = f['gauges']; n = len(gs); xs = {1: [0.0], 2: [-0.085, 0.085], 3: [-0.125, 0.0, 0.125]}[n]; tw = 0.105 if n == 3 else 0.13
    labels = []
    for g, x in zip(gs, xs):
        rect('lcd', tw, tw * 0.72, lcd(480, 346, f'{g[0].upper()}|{g[1]}' + ('@red' if g[2] else '')), (x, -0.0008, -0.012), 1.2, 0.3)
        labels.append(((x, 0, -0.012 + tw * 0.36 + 0.006), pill(g), 'red') if g[2] else ((x, 0, -0.012 + tw * 0.36 + 0.006), pill(g)))
    K.day_sky(sun_az=200, sun_el=35, strength=0.12)
    KI.area_light((0.4, -0.7, 0.4), (0, 0, 0), 6, 0.6)
    camera_on(0.0, 0.0, 0.44)
    return labels, -0.6

def gas(f):
    """The gas control panel on the galley bulkhead: solenoid switch with its lamp, the alarm with its lamp."""
    M = K.mats(); by = {g[0]: g for g in f['gauges']}; KI.wall('bulkhead', -0.9, 0.9, -0.6, 0.6, 0.012, KI.joinery_mat())
    W, H = 0.24, 0.15
    C.obj('gas-box', C.rbox('gas-box', (W + 0.01, 0.02, H + 0.01), 0.008, 3), C.simple('gas-white', '#e9e7e1', 0.4), (0, 0.002, 0))
    rect('gas-plate', W, H, face('gas-plate', by['Gas solenoid'][1], by['Gas alarm'][1]), (0, -0.0085, 0), 0.0, 0.45)
    on = by['Gas solenoid'][1] == 'ON'; ok = by['Gas alarm'][1] == 'OK'
    sw = C.obj('rocker', C.rbox('rocker', (0.022, 0.012, 0.036), 0.004, 2), C.simple('rocker', '#202124', 0.4), (-0.06, -0.016, 0.004))
    sw.rotation_euler = (math.radians(-14 if on else 14), 0, 0)
    for x, col, lit in ((-0.06, 'green', on), (0.06, 'green' if ok else 'red', True)):
        m, nt, b, out = C.new_mat('gaslamp%d' % (x > 0)); rgb = {'green': (0.1, 1.0, 0.2), 'red': (1.0, 0.08, 0.05)}[col]
        em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = rgb + (1,); em.inputs['Strength'].default_value = 1.4 if lit else 0.02
        nt.links.new(em.outputs[0], out.inputs['Surface'])
        bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=12, radius=0.008)
        for v in bm.verts: v.co.y = min(v.co.y, 0.0) * 0.8
        me = bpy.data.meshes.new('gl'); bm.to_mesh(me); bm.free(); me.shade_smooth(); C.obj('gaslamp', me, m, (x, -0.0095, -0.03))
    # the hob below, a cabin in daylight
    C.obj('worktop', C.rbox('worktop', (0.9, 0.5, 0.03), 0.006, 2), C.simple('worktop', '#c9c3b6', 0.35, coat=0.6), (0, -0.25, -0.33))
    K.day_sky(sun_az=200, sun_el=35, strength=0.12); KI.area_light((0.4, -0.8, 0.5), (0, 0, 0), 10, 0.8)
    labels = [((-0.06, 0, H / 2 + 0.006), pill(by['Gas solenoid'])), ((0.06, 0, H / 2 + 0.006), pill(by['Gas alarm']))]
    K.camera((0.05, -0.42, 0.05), (0.0, 0, 0.03), 40)
    return labels, -0.4

def co(f):
    """The CO alarm on the aft cabin bulkhead at night: its screen and red LED, a dim night light."""
    g = f['gauges'][0]; M = K.mats()
    w = bpy.data.worlds.new('dark'); bpy.context.scene.world = w; w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.004, 0.005, 0.008, 1)
    KI.wall('bulkhead', -1.2, 1.2, -0.8, 0.8, 0.012, KI.joinery_mat())
    body = C.obj('co-body', C.rbox('co', (0.13, 0.035, 0.13), 0.014, 3), C.simple('co-white', '#f1f0ec', 0.4), (0, -0.006, 0))
    rect('co-plate', 0.12, 0.12, face('co-plate'), (0, -0.0242, 0), 0.0, 0.4)
    rect('co-screen', 0.07, 0.033, face('co-screen', g[1]), (0, -0.0245, 0.02), 3.0, 0.3)
    led = C.obj('co-led', KI._cyl_y(0.005, 0.004), C.simple('led', '#ff2010', 0.2), (0.045, -0.026, -0.03))
    bb = led.data.materials[0].node_tree.nodes['Principled BSDF']; bb.inputs['Emission Color'].default_value = (1, 0.05, 0.02, 1); bb.inputs['Emission Strength'].default_value = 60
    pl = bpy.data.lights.new('led-glow', 'POINT'); pl.energy = 0.6; pl.color = (1, 0.1, 0.05); lo = bpy.data.objects.new('led-glow', pl); C.col.objects.link(lo); lo.location = (0.0, -0.08, 0.0)
    # a bunk below: cushion and a pillow, dimly lit by a red night light
    C.obj('bunk', C.rbox('bunk', (1.6, 0.7, 0.12), 0.04, 3), C.simple('cushion', '#3b4a5c', 0.8), (0, -0.35, -0.48))
    C.obj('pillow', C.rbox('pillow', (0.45, 0.3, 0.1), 0.05, 3), C.simple('pillow', '#d9d4c8', 0.8), (-0.4, -0.2, -0.37))
    KI.area_light((0.5, -0.6, 0.3), (0, 0, -0.1), 0.8, 0.5, (1.0, 0.75, 0.55))
    labels = [((0, 0, 0.075), pill(g), 'red' if g[2] else None)]
    K.camera((0.12, -0.62, 0.08), (0.0, 0, -0.04), 40)
    return [l if l[2] else l[:2] for l in labels], 0.2

def fire(f):
    """The saloon extinguisher on its bracket, its pressure gauge reading as flagged, the fire blanket beside it."""
    by = {g[0]: g for g in f['gauges']}; M = K.mats(); KI.wall('bulkhead', -0.9, 0.9, -0.7, 0.6, 0.012, KI.joinery_mat())
    red = C.simple('ext-red', '#b8141b', 0.3, coat=0.8); X = 0.13
    C.cyl('ext-body', 0.055, 0.055, 0.34, 48, red, (X, -0.07, -0.08))
    C.lathe('ext-top', [(0.0, 0.0), (0.055, 0.0), (0.05, 0.03), (0.03, 0.05), (0.0, 0.05)], 48, red).location = (X, -0.07, 0.09)
    C.cyl('ext-neck', 0.018, 0.018, 0.04, 24, M['chrome'], (X, -0.07, 0.155))
    C.obj('ext-head', C.rbox('ext-head', (0.08, 0.03, 0.03), 0.006, 2), C.simple('ext-black', '#151516', 0.4), (X + 0.015, -0.07, 0.185))
    C.obj('ext-lever', C.rbox('ext-lever', (0.09, 0.02, 0.008), 0.003, 2), M['chrome'], (X + 0.02, -0.07, 0.205))
    rect('ext-label', 0.06, 0.09, face('ext-label'), (X, -0.126, -0.08), 0.0, 0.4)
    # the pressure gauge on the valve, facing us
    low = by['Extinguisher'][2]
    KI.gauge(face('extinguisher'), (X - 0.01, -0.09, 0.2), 0.026, value_angle=-47 if low else 0, needle_color='#151516')
    C.obj('bracket', C.rbox('bracket', (0.03, 0.06, 0.22), 0.004, 2), C.simple('bracket', '#2a2b2e', 0.4, 0.5), (X, -0.012, -0.06))
    # the fire blanket: a soft red pouch with its pull tapes
    B = -0.14
    C.obj('blanket', C.rbox('blanket', (0.16, 0.04, 0.22), 0.02, 3), C.simple('blanket', '#a8161c', 0.7), (B, -0.02, 0.0))
    rect('blanket-face', 0.15, 0.2, face('blanket'), (B, -0.041, 0.0), 0.0, 0.7)
    for x in (B - 0.04, B + 0.04): C.tube('tape', [Vector((x, -0.042, -0.11)), Vector((x, -0.046, -0.15)), Vector((x + 0.004, -0.044, -0.19))], 0.004, 6, 1.0, C.simple('tape', '#1a1a1a', 0.6))
    K.day_sky(sun_az=200, sun_el=35, strength=0.12); KI.area_light((0.5, -0.9, 0.5), (0, 0, 0), 14, 0.8)
    labels = [((X - 0.01, 0, 0.232), pill(by['Extinguisher']), 'red' if low else None), ((B, 0, 0.12), pill(by['Fire blanket']), 'red' if by['Fire blanket'][2] else None)]
    K.camera((0.04, -0.98, 0.14), (0.0, 0, 0.05), 40)
    return [l if l[2] else l[:2] for l in labels], -0.3

def render(x):
    f = x['figure']; C.reset()
    labels, expo = {'engine': engine, 'monitor': monitor, 'gas': gas, 'co': co, 'fire': fire}[layout(f)](f)
    lines = list(f.get('lines', []))
    note, rest = (lines[0], lines[1:]) if lines else (None, [])
    C.render(Q.out_jpg(x['id']), Q.arg('--samples', 128), Q.arg('--scale', 100), expo, labels, note, space='blender',
             extra={'lines': rest})

x = Q.item('panel', Q.arg('--id', 'bs-083'))
meta(x)
render(x)
