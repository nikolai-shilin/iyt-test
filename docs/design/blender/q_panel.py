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

def ru_units(t):
    """A figure with its unit ('12.4 V', '160 L', '5 s'), in Russian; None for anything with words in it."""
    r = Q.ru_number(t)
    for en, ru_ in ((' Ah', ' А·ч'), (' V', ' В'), (' A', ' А'), (' L', ' л'), (' l', ' л'), (' s', ' с'), (' kn', ' уз'), (' h', ' ч'), (' m', ' м')):
        r = re.sub(en + r'\b', ru_, r)
    return None if re.search('[A-Za-z]', r) else r

def meta(x):
    f = x['figure']; ru = dict(x['ru'])
    english = [pill(g) for g in f['gauges']] + list(f.get('lines', []))
    for g in f['gauges']: ru[pill(g)] = f'{ru.get(g[0], g[0])} {ru_value(g[1], ru)}'
    plan = PLANS.get(x['id']) if Q.LEVEL != 'bareboat-skipper' else None
    if plan:      # the plan shown with the answer: an {svg} drawing that carries the reasoning
        P = plan(f); Q.save(x['id'], 'plan.json', {'svg': P.svg()})
        for t in P.texts:
            if t not in ru: ru[t] = PLAN_RU.get(t) or ru_units(t)
        ru = {k: v for k, v in ru.items() if v is not None}
        english += P.texts
    else: Q.drop(x['id'], 'plan.json')
    Q.write_ru(x['id'], english, ru)

# ---------- faces (system Python, Pillow) ----------
def faces():
    from PIL import Image, ImageDraw, ImageFont
    BOLD = '/System/Library/Fonts/Supplemental/Arial Bold.ttf'; REG = '/System/Library/Fonts/Supplemental/Arial.ttf'
    MONO = '/System/Library/Fonts/Menlo.ttc'
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
    # ---- the kinds the charter check-in panels add ----
    elif kind == 'water': dial(['E', '¼', '½', '¾', 'F'], -60, 60, 2, [(0, 0.125, RED)], [('WATER', 64)], font=100)
    elif kind == 'awa':       # apparent wind angle, the needle swinging: ghost needles where it has just been
        im = Image.new('RGBA', (S, S), (14, 15, 17, 255)); d = ImageDraw.Draw(im); R = 470
        d.arc([Cc - R, Cc - R, Cc + R, Cc + R], -90 - 60, -90 - 20, fill=RED, width=34); d.arc([Cc - R, Cc - R, Cc + R, Cc + R], -90 + 20, -90 + 60, fill=GRN, width=34)
        for i in range(-36, 37):
            t = math.radians(i * 5); major = i % 6 == 0; ri = R - (60 if major else 30)
            d.line([(Cc + math.sin(t) * ri, Cc - math.cos(t) * ri), (Cc + math.sin(t) * R, Cc - math.cos(t) * R)], fill=(235, 235, 230), width=12 if major else 5)
            if major and abs(i) not in (36,):
                rr = R - 125; d.text((Cc + math.sin(t) * rr, Cc - math.cos(t) * rr), str(abs(i * 5)), font=F(BOLD, 64), fill=(235, 235, 230), anchor='mm')
        d.text((Cc, Cc + 170), 'AWA', font=F(BOLD, 64), fill=(235, 235, 230), anchor='mm')
        ov = Image.new('RGBA', (S, S), (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
        for ang, al in ((-62, 70), (-15, 110), (48, 150), (118, 90), (165, 60), (24, 235)):
            t = math.radians(ang); od.line([(Cc - math.sin(t) * 60, Cc + math.cos(t) * 60), (Cc + math.sin(t) * (R - 40), Cc - math.cos(t) * (R - 40))], fill=(240, 138, 36, al), width=22)
        im = Image.alpha_composite(im, ov); d = ImageDraw.Draw(im)
        d.ellipse([Cc - 40, Cc - 40, Cc + 40, Cc + 40], fill=(30, 30, 32)); im.convert('RGB').save(out)
    elif kind == 'hours':     # the engine hour meter: a counter window under its caption
        im = Image.new('RGB', (640, 300), (20, 21, 23)); d = ImageDraw.Draw(im)
        d.text((320, 52), 'HOURS', font=F(BOLD, 52), fill=(205, 205, 200), anchor='mm')
        d.rounded_rectangle([34, 96, 606, 270], 18, fill=(150, 178, 160))
        size = 150
        while d.textlength(a[0], font=F(MONO, size)) > 520: size -= 6
        d.text((578, 183), a[0], font=F(MONO, size), fill=(20, 28, 24), anchor='rm'); im.save(out)
    elif kind == 'inst':      # a multifunction instrument head: what it shows, big, under its name
        im = Image.new('RGB', (640, 480), (8, 10, 12)); d = ImageDraw.Draw(im)
        d.text((34, 58), a[0], font=F(BOLD, 64), fill=(170, 190, 200), anchor='lm')
        size = 230
        while d.textlength(a[1], font=F(BOLD, size)) > 570: size -= 8
        d.text((320, 290), a[1], font=F(BOLD, size), fill=(245, 245, 240), anchor='mm'); im.save(out)
    elif kind in ('unit-plate', 'monitor-plate2'):
        # a small black plate: title at the top, captions at given pixel spots (x, y, text) of a 1200 x 1300 face
        if kind == 'monitor-plate2':
            w, h = 2400, 1300; im = Image.new('RGB', (w, h), (26, 27, 30)); d = ImageDraw.Draw(im)
            d.rounded_rectangle([12, 12, w - 12, h - 12], 50, outline=(70, 72, 76), width=7)
            d.text((w / 2, 120), a[0], font=F(BOLD, 72), fill=(200, 200, 195), anchor='mm'); im.save(out)
        else:
            w, h = 1200, 1300; im = Image.new('RGB', (w, h), (26, 27, 30)); d = ImageDraw.Draw(im)
            d.rounded_rectangle([12, 12, w - 12, h - 12], 50, outline=(70, 72, 76), width=7)
            if a[0]: d.text((w / 2, 110), a[0], font=F(BOLD, 80), fill=(200, 200, 195), anchor='mm')
            for c in a[1:]:
                x, y, t = c.split(':', 2); d.text((int(x), int(y)), t, font=F(BOLD, 72), fill=(200, 200, 195), anchor='mm')
            im.save(out)
    elif kind == 'name':      # an engraved name plate on the bulkhead under a panel
        im = Image.new('RGB', (800, 180), (28, 29, 31)); d = ImageDraw.Draw(im)
        d.rounded_rectangle([6, 6, 794, 174], 24, outline=(150, 150, 145), width=5)
        d.text((400, 92), a[0], font=F(BOLD, 84), fill=(230, 230, 225), anchor='mm'); im.save(out)

if '--face' in sys.argv: faces(); sys.exit(0)

# ---------- other levels (charter check-in): the units a figure puts on the bulkhead, left to right ----------
# engine (dials, hour meter, lamps, key), tach (a small engine panel: the rev counter, key, the charge lamp when the
# figure says so), monitor (battery monitor or solar controller tiles), ac (shore power and charger lamps), water
# (tank gauge, tank selector, pump switch), bilge (pump selector and its cycle counter), dc (voltmeter and the windlass
# breaker), nav (instrument heads). A unit shows a lamp, a selector or a switch only where the figure states it.
NAV = ('Depth', 'SOG', 'Log', 'Wind', 'AWS', 'AWA')
MON = ('Volts', 'Amps', 'Charge', 'Used Ah', 'Sun 22:00', 'Mon 07:00', 'Panel V', 'Battery V')

def units(f):
    gs = [list(g) for g in f['gauges']]; names = [g[0] for g in gs]; txt = ' '.join(f.get('lines', [])).lower()
    if any(n in NAV for n in names): return [('nav', gs, {})]
    if 'Water' in names: return [('water', gs, {'sel': 'selector' in txt, 'pump': 'pump' in txt and 'running' in txt})]
    if 'Bilge pump' in names: return [('bilge', gs, {})]
    if 'Windlass' in names:
        return [('tach', [g for g in gs if g[0] == 'Engine'], {}), ('dc', [g for g in gs if g[0] != 'Engine'], {})]
    if 'Panel V' in names: return [('monitor', gs, {'title': 'SOLAR CONTROLLER'})]
    port = [g for g in gs if g[0].startswith('Port')]; stbd = [g for g in gs if g[0].startswith('Stbd')]
    if port and stbd:      # a catamaran: both engine panels, each with its own name plate
        rest = [g for g in gs if g not in port + stbd]
        return [('engine', port + rest, {'name': 'PORT ENGINE'}),
                ('engine', stbd + [g + ['quiet'] for g in rest if g[0] == 'RPM'], {'name': 'STBD ENGINE'})]
    if 'Amps' in names or all(n in MON for n in names):
        out = [('monitor', [g for g in gs if g[0] in MON], {'title': 'BATTERY MONITOR'})]
        eng = [g for g in gs if g[0] not in MON]
        if eng: out.append(('tach', eng, {'charge': 'battery light on' in txt}))
        if 'shore power connected' in txt: out.append(('ac', [], {'charger': 'charger on' in txt}))
        return out
    return [('engine', gs, {})]

# ---------- the plans: drawings for the answer (system Python) ----------
RED, GREEN, AMBER = Q.RED, Q.GREEN, Q.AMBER
MUTED = 'var(--muted)'

def _vscale(P, readings, expect=None, y=420, lo=11.6, hi=14.6):
    """The battery's volts on one line: the resting charge (12.0 to 12.7 V) and the charger's band (13.8 to 14.4 V).
    readings: [(volts, pill text, kind, row)]; expect: (v0, v1, pill text)."""
    X = lambda v: 110 + (v - lo) / (hi - lo) * 1060
    P.rect(X(lo), y - 50, X(12.08) - X(lo), 50, fill=RED, op=.18)
    P.rect(X(12.08), y - 50, X(12.8) - X(12.08), 50, fill=AMBER, op=.22)
    P.rect(X(13.65), y - 50, X(14.55) - X(13.65), 50, fill=GREEN, op=.20)
    P.text((X(12.08) + X(12.8)) / 2, y - 16, 'at rest', 28, fill=MUTED, halo=False)
    P.text((X(13.65) + X(14.55)) / 2, y - 16, 'on charge', 28, fill=MUTED, halo=False)
    P.line(X(lo), y, X(hi), y, w=5)
    for v, cap in ((12.0, '0 %'), (12.2, '50 %'), (12.4, '75 %'), (12.7, '100 %'), (13.8, 'FLOAT'), (14.4, 'bulk')):
        P.line(X(v), y, X(v), y + 16, w=4); P.text(X(v), y + 52, f'{v:.1f}', 30, halo=False)
        P.text(X(v), y + 90, cap, 28, 400, fill=MUTED, halo=False)
    P.text(X(lo), y + 52, 'V', 30, fill=MUTED, a='start', halo=False)
    if expect:
        v0, v1, t = expect
        P.rect(X(v0) - 10, y - 62, X(v1) - X(v0) + 20, 74, stroke=GREEN, sw=6, rx=10, dash='14 10')
        P.pill(min(1080, max(200, (X(v0) + X(v1)) / 2)), y + 150, t, 'green', 28)
        P.line((X(v0) + X(v1)) / 2, y + 16, (X(v0) + X(v1)) / 2, y + 128, c=GREEN, w=4, dash='8 8')
    for v, t, kind, row in readings:
        py = y - 140 - 86 * row
        P.line(X(v), py + 24, X(v), y - 4, c=RED if kind == 'red' else 'var(--ink)', w=5)
        P.raw(f'<path d="M{X(v):.1f} {y - 2} l-12 -20 h24 Z" fill="{RED if kind == "red" else "var(--ink)"}"/>')
        P.pill(min(1100, max(180, X(v))), py, t, kind, 30)

def _bar(P, y, total, left, x0=140, x1=1140, h=96, used_text=None, left_text=None, floor=None, ticks=(), unit=''):
    """A tank or a bank as one bar: what is left (accent) and what has gone (red), the scale under it."""
    k = (x1 - x0) / total; xl = x0 + left * k
    P.rect(x0, y, xl - x0, h, fill='var(--accent)', op=.35); P.rect(xl, y, x1 - xl, h, fill=RED, op=.25)
    P.rect(x0, y, x1 - x0, h, stroke='var(--ink)', sw=4, rx=6)
    for t in ticks:
        P.line(x0 + t * k, y + h, x0 + t * k, y + h + 14, w=4); P.text(x0 + t * k, y + h + 50, f'{t}' + (f' {unit}' if t == ticks[-1] and unit else ''), 30, 400, halo=False)
    if floor is not None:
        P.line(x0 + floor[0] * k, y - 30, x0 + floor[0] * k, y + h + 18, c=RED, w=5, dash='12 9')
    if left_text: P.pill((x0 + xl) / 2, y + h / 2, left_text, 'light', 30)
    if used_text: P.pill((xl + x1) / 2, y - 50, used_text, 'red', 30)

def p_volts(title, key, readings, expect=None):
    def f(fig):
        P = Q.Plan(title, key, PLAN_RU); _vscale(P, readings, expect); return P
    return f

def p_ah(title, key, total, used, used_text, left_text, half=True):
    def f(fig):
        P = Q.Plan(title, key, PLAN_RU)
        _bar(P, 220, total, total - used, used_text=used_text, left_text=left_text, floor=(total / 2,) if half else None,
             ticks=(0, 50, 100, 150, 200), unit='Ah')
        if half: P.pill(140 + 500, 440, 'lead-acid: not below half', 'red', 28)
        return P
    return f

def p_lithium(fig):
    P = Q.Plan('Lithium: the volts barely move', ['Lithium holds 13.0–13.3 V over most of its charge',
                                                  "The volts say little: trust the monitor's 25 %"], PLAN_RU)
    x0, x1, y0, y1, vlo, vhi = 190, 1160, 520, 70, 11.8, 13.6
    X = lambda c: x0 + c / 100 * (x1 - x0); Y = lambda v: y0 - (v - vlo) / (vhi - vlo) * (y0 - y1)
    P.line(x0, y0, x1, y0, w=4); P.line(x0, y0, x0, y1, w=4)
    for c in (0, 25, 50, 75, 100): P.line(X(c), y0, X(c), y0 + 12, w=4); P.text(X(c), y0 + 46, f'{c} %', 28, 400, halo=False)
    for v in (12.0, 12.4, 12.8, 13.2, 13.6): P.line(x0 - 12, Y(v), x0, Y(v), w=4); P.text(x0 - 20, Y(v) + 10, f'{v:.1f} V', 28, 400, a='end', halo=False)
    li = [(0, 12.0), (4, 12.8), (10, 13.0), (30, 13.1), (60, 13.2), (90, 13.3), (97, 13.4), (100, 13.55)]
    la = [(0, 12.0), (25, 12.1), (50, 12.2), (75, 12.4), (100, 12.7)]
    for pts, c in ((li, 'var(--accent)'), (la, MUTED)):
        P.raw('<path d="' + ' '.join(('M' if i == 0 else 'L') + f'{X(a):.1f} {Y(b):.1f}' for i, (a, b) in enumerate(pts)) + f'" fill="none" stroke="{c}" stroke-width="7" stroke-linejoin="round"/>')
    P.pill(X(60), Y(13.2) - 46, 'lithium', 'accent', 30); P.pill(X(70), Y(12.33) + 52, 'lead-acid', 'light', 28)
    P.raw(f'<circle cx="{X(25):.1f}" cy="{Y(13.1):.1f}" r="16" fill="{RED}" stroke="var(--bg)" stroke-width="4"/>')
    P.pill(X(25) + 30, Y(13.1) - 120, '25 % · 13.1 V', 'red', 30); P.line(X(25), Y(13.1) - 20, X(25) + 20, Y(13.1) - 96, c=RED, w=4)
    return P

def p_fuel(fig):
    P = Q.Plan('Fuel for Friday: plan on the lower figure', ['Gauge ¼ of 160 L = 40 L · by hours 160 − 22 × 4 = 72 L',
                                                            '28 M at 6 kn ≈ 5 h ≈ 20 L, + 20 L reserve = 40 L: top up'], PLAN_RU)
    x0, x1 = 330, 1150; k = (x1 - x0) / 160
    for row, (lab, v) in enumerate((('by the gauge', 40), ('by the hours', 72))):
        y = 90 + row * 150
        P.text(x0 - 24, y + 56, lab, 32, a='end', halo=False)
        P.rect(x0, y, v * k, 84, fill='var(--accent)' if row else RED, op=.35); P.rect(x0, y, x1 - x0, 84, stroke='var(--ink)', sw=4, rx=6)
        P.text(x0 + v * k + 16, y + 56, f'{v} L', 34, a='start')
    for t in (0, 40, 80, 120, 160): P.line(x0 + t * k, 330, x0 + t * k, 344, w=4); P.text(x0 + t * k, 378, f'{t} L' if t == 160 else f'{t}', 30, 400, halo=False)
    P.line(x0 + 40 * k, 60, x0 + 40 * k, 340, c=RED, w=6, dash='14 10')
    P.pill(x0 + 40 * k + 150, 470, 'need: 20 L run + 20 L reserve', 'red', 30)
    return P

def p_water(fig):
    P = Q.Plan('Half the water gone on day one', ['75 l for six people for three days: about 4 l each a day',
                                                 'Short rinses, wash up in seawater, drink bottled'], PLAN_RU)
    _bar(P, 200, 150, 75, used_text='transom shower: 75 l', left_text='75 l left', ticks=(0, 50, 100, 150), unit='l')
    P.pill(640, 470, '75 l ÷ 6 crew ÷ 3 days ≈ 4 l', 'accent', 32)
    return P

def p_tanks(fig):
    P = Q.Plan('The gauge reads the selected tank', ['On tank 1 the gauge shows ¼: tank 1 is not full',
                                                    'Switch to tank 2 and look into both fillers before you sign'], PLAN_RU)
    for i, (x, lvl, cap) in enumerate(((120, .25, 'tank 1 · 300 l'), (900, None, 'tank 2 · 300 l'))):
        P.rect(x, 110, 260, 300, stroke='var(--ink)', sw=5, rx=14)
        if lvl: P.rect(x + 4, 110 + 300 * (1 - lvl), 252, 300 * lvl - 4, fill='var(--accent)', op=.45, rx=10)
        else: P.text(x + 130, 290, '?', 120, fill=MUTED, halo=False)
        P.text(x + 130, 460, cap, 32, halo=False)
    P.arrow(380, 300, 520, 300, c='var(--accent)', w=7); P.pill(640, 300, 'gauge: ¼', 'red', 32)
    P.pill(640, 200, 'selector: tank 1', 'accent', 28); P.line(780, 300, 900, 300, c=MUTED, w=4, dash='10 10')
    return P

def p_depth(fig):
    P = Q.Plan('Depth below the transducer, not the keel', ['No offset set: 3.3 m is measured from the transducer, 0.2 m down',
                                                           'Under the keel: 3.5 − 1.9 ≈ 1.6 m'], PLAN_RU)
    m = 120; s0 = 110; Y = lambda d: s0 + d * m
    P.raw(f'<rect x="0" y="{s0}" width="1280" height="{Y(3.5) - s0}" fill="var(--accent)" opacity=".08"/>')
    P.raw(f'<path d="M0 {Y(3.5)} C 200 {Y(3.45)} 400 {Y(3.55)} 640 {Y(3.5)} S 1000 {Y(3.45)} 1280 {Y(3.5)} V 616 H 0 Z" fill="#d8c9a3" stroke="#6b5a3a" stroke-width="5"/>')
    P.line(0, s0, 1280, s0, c='var(--accent)', w=5)
    hull = f'M170 {s0 - 70} L720 {s0 - 70} C 700 {s0 + 10} 640 {Y(0.6)} 520 {Y(0.65)} L 470 {Y(0.65)} L 455 {Y(1.9)} L 395 {Y(1.9)} L 380 {Y(0.65)} L 260 {Y(0.6)} C 220 {Y(0.5)} 185 {s0} 170 {s0 - 70} Z'
    P.raw(f'<path d="{hull}" fill="var(--bg)" stroke="var(--ink)" stroke-width="5" stroke-linejoin="round"/>')
    tx = 300; P.raw(f'<circle cx="{tx}" cy="{Y(0.2):.1f}" r="12" fill="{AMBER}" stroke="var(--ink)" stroke-width="4"/>')
    P.pill(tx - 40, Y(0.2) + 80, 'transducer', 'light', 26)
    def dim(x, a, b, t, kind='light'):
        P.line(x, Y(a), x, Y(b), w=4)
        for d in (a, b): P.line(x - 14, Y(d), x + 14, Y(d), w=4)
        P.pill(x, (Y(a) + Y(b)) / 2, t, kind, 28)
    dim(1150, 0, 3.5, 'plan: 3.5 m'); dim(940, 0.2, 3.5, 'sounder: 3.3 m', 'accent'); dim(600, 0, 1.9, 'draught 1.9 m')
    dim(425, 1.9, 3.5, '≈ 1.6 m', 'red')
    P.line(tx, Y(0.2), 940, Y(0.2), c=MUTED, w=3, dash='8 8')
    return P

def p_current(fig):
    P = Q.Plan('Log and SOG: the difference is the current', ['The log measures speed through the water: 6.0 kn',
                                                             'SOG 4.2 kn over the ground: 1.8 kn of current against you'], PLAN_RU)
    x0, k = 150, 150
    P.arrow(x0, 150, x0 + 6.0 * k, 150, c='var(--accent)', w=12, h=40); P.pill(x0 + 3.0 * k, 92, 'log: 6.0 kn through the water', 'accent', 30)
    P.arrow(x0 + 6.0 * k, 300, x0 + 4.2 * k, 300, c=RED, w=12, h=40); P.pill(x0 + 5.1 * k, 242, 'current 1.8 kn', 'red', 30)
    P.arrow(x0, 450, x0 + 4.2 * k, 450, c='var(--ink)', w=12, h=40); P.pill(x0 + 2.1 * k, 392, 'SOG 4.2 kn over the ground', 'light', 30)
    for x in (x0, x0 + 4.2 * k, x0 + 6.0 * k): P.line(x, 120, x, 480, c=MUTED, w=3, dash='8 10')
    return P

def p_eta(fig):
    P = Q.Plan('Arrival: by SOG, not by the log', ['24 M ÷ 4.0 kn over the ground = 6 h: about 17:00',
                                                  'Call the base now: a late boat is a late check-out'], PLAN_RU)
    x0, k = 120, 1040 / 8; X = lambda h: x0 + (h - 11) * k
    P.line(X(11), 420, X(19), 420, w=4)
    for h in range(11, 20): P.line(X(h), 420, X(h), 436, w=4); P.text(X(h), 474, f'{h}:00', 28, 400, halo=False)
    P.rect(X(11), 300, X(17) - X(11), 70, fill='var(--accent)', op=.4, rx=10); P.pill((X(11) + X(17)) / 2, 335, '24 M at 4 kn SOG: 6 h', 'light', 28)
    P.rect(X(11), 170, X(15) - X(11), 70, stroke=MUTED, sw=4, rx=10, dash='12 9'); P.pill((X(11) + X(15)) / 2, 205, 'by the log, 6 kn: 4 h', 'light', 26)
    P.line(X(18), 120, X(18), 430, c=RED, w=6); P.pill(X(18) + 10, 110, 'base closes 18:00', 'red', 28)
    P.pill(X(17), 540, 'ETA ≈ 17:00', 'accent', 32)
    return P

def p_lamps(fig):
    P = Q.Plan('Key on: a lamp test, not a fault', ['Key on: the oil and charge lamps and the buzzer come on',
                                                   'They go out seconds after the engine fires and pressure builds'], PLAN_RU)
    X = lambda t: 300 + t * 70
    for i, (lab, c) in enumerate((('oil lamp', RED), ('charge lamp', AMBER), ('buzzer', 'var(--ink)'))):
        y = 120 + i * 100; P.text(270, y + 44, lab, 32, a='end', halo=False)
        P.rect(X(0), y + 10, X(9.5) - X(0), 50, fill=c, op=.75, rx=8); P.line(X(9.5), y + 35, X(13), y + 35, c=MUTED, w=4)
    P.line(X(0), 90, X(0), 440, w=5); P.pill(X(0), 480, 'key ON', 'light', 28)
    P.line(X(8), 90, X(8), 440, c='var(--accent)', w=5, dash='12 9'); P.pill(X(8), 480, 'engine fires', 'accent', 28)
    P.pill((X(0) + X(8)) / 2, 72, 'lamp test: normal', 'green', 28)
    return P

def p_oil(fig):
    P = Q.Plan('The oil alarm after starting', ['The alarm sounds until oil pressure builds: a second or two',
                                               'Still sounding at 15 s: pull the stop handle'], PLAN_RU)
    X = lambda t: 220 + t * 48
    P.line(X(0), 360, X(20), 360, w=4)
    for t in (0, 5, 10, 15, 20): P.line(X(t), 360, X(t), 376, w=4); P.text(X(t), 414, f'{t} s', 28, 400, halo=False)
    P.rect(X(0), 250, X(2) - X(0), 80, fill=GREEN, op=.55, rx=8); P.pill(X(1) + 150, 200, 'normal: 1–2 s', 'green', 28)
    P.rect(X(2), 250, X(15) - X(2), 80, fill=RED, op=.3, rx=8)
    P.line(X(15), 150, X(15), 380, c=RED, w=6); P.pill(X(15), 120, 'still sounding: stop', 'red', 30)
    P.pill(X(0), 480, 'engine fires', 'accent', 28)
    return P

PLANS = {
    'ci-155': p_oil, 'ci-171': p_lamps, 'ci-195': p_fuel,
    'ci-203': p_volts('A rested bank: its volts tell the charge', ['Rested, no load: 12.7 V full, 12.4 V about 75 %', '12.2 V half, 12.0 V or less flat'],
                      [(12.7, '12.7 V at rest: full', 'accent', 0)]),
    'ci-204': p_volts('On charge, the charger sets the volts', ['On charge: 13.8 V float, 14.4 V bulk', "The bank's own state shows after an hour at rest"],
                      [(13.8, "13.8 V: the charger's float", 'accent', 0)], (12.0, 12.7, 'the bank itself: read at rest')),
    'ci-205': p_volts('Plugged in, yet not charging', ['On shore power the bank should read 13.8–14.4 V', '11.8 V with current going out: no charge'],
                      [(11.8, '11.8 V, −6 A', 'red', 0)], (13.8, 14.4, 'plugged in: expect this')),
    'ci-210': p_volts('Engine running, yet no charge', ['Running, it should show about 14 V and current going in', '12.3 V and −8 A: not charging — alternator or belt'],
                      [(12.3, '12.3 V, −8 A', 'red', 0)], (13.8, 14.4, 'engine running: expect this')),
    'ci-245': p_volts('After 40 Ah a healthy bank reads 12.4 V', ['40 Ah from 200 Ah should leave about 12.4 V', '11.9 V: the old bank holds far less than its label'],
                      [(11.9, 'Mon 07:00: 11.9 V', 'red', 0), (12.6, 'Sun 22:00: 12.6 V', 'light', 1)], (12.35, 12.45, 'healthy: ≈ 12.4 V')),
    'ci-248': p_volts('The monitor has lost count', ['A monitor that lost count shows what it was last set to', '12.1 V under a small load: near half or below'],
                      [(12.1, '12.1 V: near half', 'red', 0), (12.7, 'what 100 % would read', 'light', 1)]),
    'ci-212': p_ah('Overnight with the fridge on', ['5 A × 10 h = 50 Ah: a quarter of the 2 × 100 Ah bank', 'Lead-acid: stay above half; 50 Ah is fine'],
                   200, 50, 'fridge: 5 A × 10 h = 50 Ah', '150 Ah left'),
    'ci-221': p_ah('Used Ah: counted since the bank was last full', ['The monitor counts amp-hours out and in since the last full charge', '200 − 76 = 124 Ah left: the 62 % it shows'],
                   200, 76, 'drawn since full: 76 Ah', '124 Ah left = 62 %', half=False),
    'ci-241': p_lithium, 'ci-251': p_tanks, 'ci-284': p_water, 'ci-303': p_depth, 'ci-326': p_current, 'ci-350': p_eta,
}

PLAN_RU = {
    'at rest': 'в покое', 'on charge': 'на зарядке', 'FLOAT': 'FLOAT', 'bulk': 'основной', 'V': 'В', '0 %': '0 %',
    'A rested bank: its volts tell the charge': 'Банк в покое: напряжение показывает заряд',
    'Rested, no load: 12.7 V full, 12.4 V about 75 %': 'В покое, без нагрузки: 12,7 В — полный, 12,4 В — около 75 %',
    '12.2 V half, 12.0 V or less flat': '12,2 В — половина, 12,0 В и ниже — разряжен',
    '12.7 V at rest: full': '12,7 В в покое: полный',
    'On charge, the charger sets the volts': 'На зарядке напряжение задаёт зарядное',
    'On charge: 13.8 V float, 14.4 V bulk': 'На зарядке: 13,8 В FLOAT, 14,4 В основной заряд',
    "The bank's own state shows after an hour at rest": 'Состояние банка видно после часа в покое',
    "13.8 V: the charger's float": '13,8 В: FLOAT зарядного', 'the bank itself: read at rest': 'сам банк: читать в покое',
    'Plugged in, yet not charging': 'Подключено, но не заряжает',
    'On shore power the bank should read 13.8–14.4 V': 'На береговом питании банк должен показывать 13,8–14,4 В',
    '11.8 V with current going out: no charge': '11,8 В и ток уходит: заряда нет', '11.8 V, −6 A': '11,8 В, −6 А',
    'plugged in: expect this': 'подключено: ожидается так',
    'Engine running, yet no charge': 'Двигатель работает, а заряда нет',
    'Running, it should show about 14 V and current going in': 'На ходу должно быть около 14 В и ток в банк',
    '12.3 V and −8 A: not charging — alternator or belt': '12,3 В и −8 А: не заряжает — генератор или ремень',
    '12.3 V, −8 A': '12,3 В, −8 А', 'engine running: expect this': 'двигатель работает: ожидается так',
    'After 40 Ah a healthy bank reads 12.4 V': 'После 40 А·ч исправный банк показывает 12,4 В',
    '40 Ah from 200 Ah should leave about 12.4 V': '40 А·ч из 200 А·ч — должно остаться около 12,4 В',
    '11.9 V: the old bank holds far less than its label': '11,9 В: старый банк держит гораздо меньше номинала',
    'Mon 07:00: 11.9 V': 'Пн 07:00: 11,9 В', 'Sun 22:00: 12.6 V': 'Вс 22:00: 12,6 В', 'healthy: ≈ 12.4 V': 'исправный: ≈ 12,4 В',
    'The monitor has lost count': 'Монитор сбился со счёта',
    'A monitor that lost count shows what it was last set to': 'Сбившийся монитор показывает то, что в него ввели последним',
    '12.1 V under a small load: near half or below': '12,1 В под малой нагрузкой: около половины или ниже',
    '12.1 V: near half': '12,1 В: около половины', 'what 100 % would read': 'так выглядели бы 100 %',
    'Overnight with the fridge on': 'Ночь с включённым холодильником',
    '5 A × 10 h = 50 Ah: a quarter of the 2 × 100 Ah bank': '5 А × 10 ч = 50 А·ч: четверть банка 2 × 100 А·ч',
    'Lead-acid: stay above half; 50 Ah is fine': 'Свинцовый: не ниже половины; 50 А·ч — нормально',
    'fridge: 5 A × 10 h = 50 Ah': 'холодильник: 5 А × 10 ч = 50 А·ч', '150 Ah left': 'осталось 150 А·ч',
    'lead-acid: not below half': 'свинцовый: не ниже половины', '200 Ah': '200 А·ч',
    'Used Ah: counted since the bank was last full': 'Взято А·ч: счёт с последнего полного заряда',
    'The monitor counts amp-hours out and in since the last full charge': 'Монитор считает ампер-часы с последнего полного заряда',
    '200 − 76 = 124 Ah left: the 62 % it shows': '200 − 76 = 124 А·ч осталось: те самые 62 %',
    'drawn since full: 76 Ah': 'взято с полного: 76 А·ч', '124 Ah left = 62 %': 'осталось 124 А·ч = 62 %',
    'Lithium: the volts barely move': 'Литий: напряжение почти не меняется',
    'Lithium holds 13.0–13.3 V over most of its charge': 'Литий держит 13,0–13,3 В почти на всём заряде',
    "The volts say little: trust the monitor's 25 %": 'Вольты мало что говорят: верьте 25 % монитора',
    'lithium': 'литий', 'lead-acid': 'свинцовый', '25 % · 13.1 V': '25 % · 13,1 В',
    'Fuel for Friday: plan on the lower figure': 'Топливо на пятницу: считайте по меньшей цифре',
    'Gauge ¼ of 160 L = 40 L · by hours 160 − 22 × 4 = 72 L': 'Указатель ¼ от 160 л = 40 л · по моточасам 160 − 22 × 4 = 72 л',
    '28 M at 6 kn ≈ 5 h ≈ 20 L, + 20 L reserve = 40 L: top up': '28 миль на 6 уз ≈ 5 ч ≈ 20 л, + 20 л резерв = 40 л: дозаправиться',
    'by the gauge': 'по указателю', 'by the hours': 'по моточасам', '40 L': '40 л', '72 L': '72 л', '160 L': '160 л',
    'need: 20 L run + 20 L reserve': 'нужно: 20 л на переход + 20 л резерв',
    'Half the water gone on day one': 'Половина воды ушла в первый день',
    '75 l for six people for three days: about 4 l each a day': '75 л на шестерых на три дня: около 4 л на человека в день',
    'Short rinses, wash up in seawater, drink bottled': 'Короткий душ, посуда в забортной воде, пить бутилированную',
    'transom shower: 75 l': 'кормовой душ: 75 л', '75 l left': 'осталось 75 л', '150 l': '150 л',
    '75 l ÷ 6 crew ÷ 3 days ≈ 4 l': '75 л ÷ 6 человек ÷ 3 дня ≈ 4 л',
    'The gauge reads the selected tank': 'Указатель показывает выбранный танк',
    'On tank 1 the gauge shows ¼: tank 1 is not full': 'На танке 1 указатель показывает ¼: танк 1 не полон',
    'Switch to tank 2 and look into both fillers before you sign': 'Переключитесь на танк 2 и загляните в обе горловины до подписи',
    'tank 1 · 300 l': 'танк 1 · 300 л', 'tank 2 · 300 l': 'танк 2 · 300 л', 'gauge: ¼': 'указатель: ¼', 'selector: tank 1': 'селектор: танк 1',
    'Depth below the transducer, not the keel': 'Глубина под датчиком, а не под килем',
    'No offset set: 3.3 m is measured from the transducer, 0.2 m down': 'Смещение не задано: 3,3 м считаются от датчика, 0,2 м под водой',
    'Under the keel: 3.5 − 1.9 ≈ 1.6 m': 'Под килем: 3,5 − 1,9 ≈ 1,6 м',
    'transducer': 'датчик', 'plan: 3.5 m': 'план: 3,5 м', 'sounder: 3.3 m': 'эхолот: 3,3 м', 'draught 1.9 m': 'осадка 1,9 м', '≈ 1.6 m': '≈ 1,6 м',
    'Log and SOG: the difference is the current': 'Лаг и SOG: разница — это течение',
    'The log measures speed through the water: 6.0 kn': 'Лаг меряет скорость относительно воды: 6,0 уз',
    'SOG 4.2 kn over the ground: 1.8 kn of current against you': 'SOG 4,2 уз относительно грунта: 1,8 уз встречного течения',
    'log: 6.0 kn through the water': 'лаг: 6,0 уз относительно воды', 'current 1.8 kn': 'течение 1,8 уз',
    'SOG 4.2 kn over the ground': 'SOG 4,2 уз относительно грунта',
    'Arrival: by SOG, not by the log': 'Время прихода: по SOG, а не по лагу',
    '24 M ÷ 4.0 kn over the ground = 6 h: about 17:00': '24 мили ÷ 4,0 уз относительно грунта = 6 ч: около 17:00',
    'Call the base now: a late boat is a late check-out': 'Позвоните на базу сейчас: поздняя яхта — поздняя сдача',
    '24 M at 4 kn SOG: 6 h': '24 мили при SOG 4 уз: 6 ч', 'by the log, 6 kn: 4 h': 'по лагу, 6 уз: 4 ч',
    'base closes 18:00': 'база закрывается в 18:00', 'ETA ≈ 17:00': 'приход ≈ 17:00',
    'Key on: a lamp test, not a fault': 'Ключ в ON: проверка ламп, а не неисправность',
    'Key on: the oil and charge lamps and the buzzer come on': 'Ключ в ON: загораются лампы масла и заряда, звучит зуммер',
    'They go out seconds after the engine fires and pressure builds': 'Они гаснут через секунды после запуска, когда растёт давление',
    'oil lamp': 'лампа масла', 'charge lamp': 'лампа заряда', 'buzzer': 'зуммер', 'key ON': 'ключ в ON',
    'engine fires': 'двигатель запустился', 'lamp test: normal': 'проверка ламп: норма',
    'The oil alarm after starting': 'Сигнал масла после запуска',
    'The alarm sounds until oil pressure builds: a second or two': 'Сигнал звучит, пока не поднимется давление масла: секунду-две',
    'Still sounding at 15 s: pull the stop handle': 'Звучит и через 15 с: тяните рукоятку стоп',
    'normal: 1–2 s': 'норма: 1–2 с', 'still sounding: stop': 'всё ещё звучит: стоп',
}
PLAN_RU.update({f'{t} s': f'{t} с' for t in range(0, 21, 5)})

if not Q.IN_BLENDER:
    xs = Q.items('panel') if Q.flag('--all') else [Q.item('panel', Q.arg('--id', 'bs-083'))]
    for x in xs:
        other = Q.LEVEL != 'bareboat-skipper'
        meta(x); print(x['id'], [u[0] for u in units(x['figure'])] if other else layout(x['figure']), '+ plan' if other and x['id'] in PLANS else '', '+ ru')
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

# ---------- other levels: the units in a row on the bulkhead (see units() above) ----------
FRAC = {'Empty': 0.0, '1/8': 0.125, '1/4': 0.25, '1/2': 0.5, '3/4': 0.75, '7/8': 0.875, '4/4': 1.0, 'Full': 1.0}
def cdial(g):
    """(face kind, value) of a gauge drawn as a dial or meter on another level's engine panel; (None, None) for a lamp."""
    n, v = g[0], g[1]
    if n in ('Temp', 'Port temp', 'Stbd temp'): return 'temp', num(v)
    if n in ('Volts', 'Batt'): return 'volts', num(v)
    if n == 'RPM': return 'tach', num(v)
    if n == 'Engine': return 'tach', 0.0                       # 'stopped'
    if n in ('Hours', 'Port h', 'Stbd h'): return 'hours', v.replace(' ', '')
    if n == 'Fuel': return ('fuel', FRAC[v]) if v in FRAC else ('litres', num(v))
    if n == 'Water': return 'water', FRAC.get(v, 0.5)
    return dial_kind(g)

def tag(g, at):
    """The pill of a gauge at a point; none for a gauge marked 'quiet' (the second tach of a pair, already named)."""
    if len(g) > 3 and g[3] == 'quiet': return []
    return [(at, pill(g), 'red') if g[2] else (at, pill(g))]

def plate_img(name, w, h, path, cx, cz):
    rect(name, w, h, path, (cx, -0.0004, cz), 0.0, 0.5)

def box(cx, w, h):
    M = K.mats(); C.obj('panel', C.rbox('panel', (w + 0.012, 0.012, h + 0.012), 0.006, 3), M['dark'], (cx, 0.006, 0.0))

def key_at(x, z, on=True):
    M = K.mats(); C.obj('key', KI._cyl_y(0.016, 0.01), M['chrome'], (x, -0.005, z))
    kb = C.obj('key-bit', C.rbox('kb', (0.007, 0.022, 0.024), 0.002, 2), M['dark'], (x, -0.017, z))
    kb.rotation_euler = (0, math.radians(90 if on else 0), 0)

def hour_meter(x, z, value):
    C.obj('hm-box', C.rbox('hm', (0.084, 0.012, 0.044), 0.004, 2), C.simple('hm-black', '#141516', 0.4), (x, -0.002, z))
    rect('hm-face', 0.078, 0.0366, face('hours', value), (x, -0.0085, z), 0.6, 0.3)

def lit_lamps(gs, lines):
    """Which warning lamps the figure lights: a flagged oil, temperature, charge or battery reading, or 'battery
    light on' / 'charge light on' in its lines."""
    by = {g[0]: g for g in gs}; txt = ' '.join(lines).lower()
    temp = any(g[2] for g in gs if g[0] in ('Temp', 'Port temp', 'Stbd temp'))
    charge = bool(by.get('Batt', [0, 0, False])[2]) or bool(by.get('Charge', [0, '', False])[2] and by['Charge'][1] == 'ON') or \
        bool(re.search(r'(battery|charge)( warning)? light (still )?on', txt))
    return {'OIL': bool(by.get('Oil', [0, 0, False])[2]), 'TEMP': temp, 'CHARGE': charge}

def u_engine(cx, gs, lines, o):
    """The engine panel (same face as the bareboat one): dials and the hour meter across the top, lamps, key."""
    W, H = 0.40, 0.2167; box(cx, W, H); plate_img('plate', W, H, face('engine-plate'), cx, 0)
    P = lambda x, y: (cx + (x / 2400 - 0.5) * W, (0.5 - y / 1300) * H)
    labels = []; items = [(g, *cdial(g)) for g in gs if cdial(g)[0]]
    n = len(items); r = 0.046 if n <= 2 else 0.042
    xs = {1: [0.0], 2: [-0.1, 0.1] if o.get('name') else [-0.07, 0.07], 3: [-0.125, 0.0, 0.125]}.get(n, []); zc = 0.035
    for (g, kind, v), x in zip(items, xs):
        if kind == 'hours': hour_meter(cx + x, zc, v); labels += tag(g, (cx + x, 0, zc + 0.03))
        else: KI.gauge(face(kind), (cx + x, -0.001, zc), r, value_angle=angle(kind, v)); labels += tag(g, (cx + x, 0, zc + r + 0.008))
    lit = lit_lamps(gs, lines); by = {g[0]: g for g in gs}
    for xx, name in ((230, 'OIL'), (700, 'CHARGE'), (1170, 'TEMP')):
        x, z = P(xx, 1060); lamp(x, z, 'red' if name != 'CHARGE' else 'amber', lit[name])
        g = by.get({'OIL': 'Oil', 'CHARGE': 'Charge', 'TEMP': 'Temp'}[name])
        if g and not cdial(g)[0]: labels += tag(g, (x, 0, z + 0.012))
    x, z = P(1560, 1060); key_at(x, z, True)
    for i, (xx, col) in enumerate(((1840, '#2a8a3a'), (2110, '#b3261e'))):
        bx, bz = P(xx, 1060); C.obj('button', KI._cyl_y(0.011, 0.008), C.simple('btn%d' % i, col, 0.4, coat=0.5), (bx, -0.004, bz))
    if o.get('name'): rect('name', 0.12, 0.027, face('name', o['name']), (cx, 0.0105, -H / 2 - 0.035), 0.0, 0.4)
    return labels, W

def u_tach(cx, gs, lines, o):
    """A small engine panel: the rev counter, the key, and the charge lamp only when the figure says it is on."""
    W, H = 0.17, 0.2167; box(cx, W, H)
    caps = ['1300:1180:KEY'] + (['300:1180:CHARGE'] if o.get('charge') else [])
    plate_img('tach-plate', W, H, face('unit-plate', 'ENGINE', *[c.replace('1300', '850') for c in caps]), cx, 0)
    P = lambda x, y: (cx + (x / 1200 - 0.5) * W, (0.5 - y / 1300) * H)
    g = gs[0]; kind, v = cdial(g); r = 0.05; zc = 0.012
    KI.gauge(face(kind), (cx, -0.001, zc), r, value_angle=angle(kind, v)); labels = tag(g, (cx, 0, zc + r + 0.008))
    x, z = P(850, 1080); key_at(x, z, g[0] != 'Engine')
    if o.get('charge'): x, z = P(300, 1080); lamp(x, z, 'amber', True)
    return labels, W

def u_monitor(cx, gs, lines, o):
    """The battery monitor or the solar controller: a backlit tile per reading, red when the figure flags it."""
    W, H = 0.40, 0.2167; box(cx, W, H); plate_img('plate', W, H, face('monitor-plate2', o.get('title', 'BATTERY MONITOR')), cx, 0)
    n = len(gs); xs = {1: [0.0], 2: [-0.085, 0.085], 3: [-0.125, 0.0, 0.125]}[n]; tw = 0.105 if n == 3 else 0.13
    UNIT = {'Volts': 'V', 'Amps': 'A', 'Used Ah': 'Ah', 'Panel V': 'V', 'Battery V': 'V', 'Sun 22:00': 'V', 'Mon 07:00': 'V'}
    labels = []
    for g, x in zip(gs, xs):
        name = {'Battery V': 'BATT V'}.get(g[0]) or ' '.join(w if w in ('Ah', 'V') else w.upper() for w in g[0].split())
        if len(name) > 8: name = name.replace(' ', '|', 1)
        val = g[1] + (' ' + UNIT[g[0]] if g[0] in UNIT and re.fullmatch(r'[-+]?[\d.]+', g[1]) else '')
        rect('lcd', tw, tw * 0.72, lcd(480, 346, f'{name}|{val}' + ('@red' if g[2] else '')), (cx + x, -0.0008, -0.024), 1.2, 0.3)
        labels += tag(g, (cx + x, 0, -0.024 + tw * 0.36 + 0.006))
    return labels, W

def u_ac(cx, gs, lines, o):
    """The AC panel: the shore power lamp lit, the main breaker on, the charger lamp lit only when the figure says so."""
    W, H = 0.17, 0.2167; box(cx, W, H)
    ch = o.get('charger'); caps = ['850:760:CHARGER'] if ch else []
    plate_img('ac-plate', W, H, face('unit-plate', 'AC PANEL', ('350:760:SHORE' if ch else '600:760:SHORE POWER'), *caps, '600:1180:MAIN'), cx, 0)
    P = lambda x, y: (cx + (x / 1200 - 0.5) * W, (0.5 - y / 1300) * H)
    for xx, on in (((350 if ch else 600), True),) + (((850, True),) if ch else ()):
        x, z = P(xx, 560); lamp(x, z, 'green', on)
    x, z = P(600, 980)
    C.obj('breaker', C.rbox('breaker', (0.05, 0.016, 0.04), 0.003, 2), C.simple('breaker-black', '#121314', 0.4), (x, -0.006, z))
    lv = C.obj('breaker-lever', C.rbox('lever', (0.03, 0.012, 0.012), 0.002, 2), C.simple('breaker-white', '#e8e6e0', 0.4), (x, -0.017, z + 0.008))
    return [], W

def u_water(cx, gs, lines, o):
    """The fresh-water panel: the tank gauge; the tank selector and the pump switch when the figure mentions them."""
    W, H = 0.20, 0.2167; box(cx, W, H)
    caps = (['250:770:TANK 1', '570:770:TANK 2'] if o.get('sel') else []) + (['900:1110:PUMP'] if o.get('pump') else [])
    plate_img('water-plate', W, H, face('unit-plate', '', *caps, '600:1215:FRESH WATER'), cx, 0)
    P = lambda x, y: (cx + (x / 1200 - 0.5) * W, (0.5 - y / 1300) * H)
    g = gs[0]; kind, v = cdial(g); r = 0.042; zc = 0.038 if (o.get('sel') or o.get('pump')) else 0.012
    KI.gauge(face(kind), (cx, -0.001, zc), r, value_angle=angle('fuel', v)); labels = tag(g, (cx, 0, zc + r + 0.008))
    if o.get('sel'):      # the rotary selector, pointing at TANK 1 (the figure: 'on tank 1')
        x, z = P(410, 935); C.obj('knob', KI._cyl_y(0.017, 0.014), C.simple('knob', '#1a1b1d', 0.35), (x, -0.008, z))
        pt = C.obj('knob-pointer', C.rbox('kp', (0.004, 0.006, 0.016), 0.001, 1), C.simple('knob-white', '#f2f0ea', 0.4), (x, -0.016, z))
        piv = bpy.data.objects.new('knob-pivot', None); C.col.objects.link(piv); piv.location = (x, -0.016, z)
        pt.parent = piv; pt.location = (0, 0, 0.008); piv.rotation_euler = (0, math.radians(-40), 0)
    if o.get('pump'):     # the pump rocker on, its lamp lit (the figure: the pump is running)
        x, z = P(900, 950); lamp(x, P(900, 770)[1], 'green', True)
        sw = C.obj('rocker', C.rbox('rocker', (0.018, 0.012, 0.03), 0.004, 2), C.simple('rocker', '#202124', 0.4), (x, -0.008, z)); sw.rotation_euler = (math.radians(-14), 0, 0)
    return labels, W

def u_bilge(cx, gs, lines, o):
    """The bilge pump panel: the pump selector at AUTO and its cycle counter showing the figure's rate."""
    W, H = 0.20, 0.2167; box(cx, W, H); g = gs[0]
    plate_img('bilge-plate', W, H, face('unit-plate', '', '330:870:AUTO', '600:800:OFF', '870:870:MAN', '600:1215:BILGE PUMP'), cx, 0)
    P = lambda x, y: (cx + (x / 1200 - 0.5) * W, (0.5 - y / 1300) * H)
    x, z = P(600, 400); rect('bilge-lcd', 0.13, 0.065, lcd(480, 240, f'CYCLES|{g[1]}'), (x, -0.0008, z), 1.2, 0.3)
    labels = tag(g, (x, 0, z + 0.04))
    x, z = P(600, 980); C.obj('knob', KI._cyl_y(0.017, 0.014), C.simple('knob', '#1a1b1d', 0.35), (x, -0.008, z))
    pt = C.obj('knob-pointer', C.rbox('kp', (0.004, 0.006, 0.016), 0.001, 1), C.simple('knob-white', '#f2f0ea', 0.4), (x, -0.016, z))
    piv = bpy.data.objects.new('knob-pivot', None); C.col.objects.link(piv); piv.location = (x, -0.016, z)
    pt.parent = piv; pt.location = (0, 0, 0.008); piv.rotation_euler = (0, math.radians(-50), 0)
    return labels, W

def u_dc(cx, gs, lines, o):
    """The DC panel: the voltmeter and the windlass breaker, its lever down when the figure says OFF."""
    W, H = 0.20, 0.2167; box(cx, W, H); by = {g[0]: g for g in gs}
    plate_img('dc-plate', W, H, face('unit-plate', '', '820:900:ON', '820:1140:OFF', '600:1240:WINDLASS'), cx, 0)
    P = lambda x, y: (cx + (x / 1200 - 0.5) * W, (0.5 - y / 1300) * H)
    labels = []
    if 'Volts' in by:
        g = by['Volts']; r = 0.04; zc = 0.042
        KI.gauge(face('volts'), (cx, -0.001, zc), r, value_angle=angle('volts', num(g[1]))); labels += tag(g, (cx, 0, zc + r + 0.008))
    g = by['Windlass']; on = g[1] == 'ON'; x, z = P(600, 1020)
    C.obj('breaker', C.rbox('breaker', (0.034, 0.016, 0.05), 0.003, 2), C.simple('breaker-black', '#121314', 0.4), (x, -0.006, z))
    lv = C.obj('breaker-lever', C.rbox('lever', (0.012, 0.03, 0.008), 0.002, 2), C.simple('breaker-white', '#e8e6e0', 0.4), (x, -0.024, z + (0.012 if on else -0.012)))
    lv.rotation_euler = (math.radians(30 if on else -30), 0, 0)
    labels += tag(g, (x, 0, z + 0.03))
    return labels, W

def u_nav(cx, gs, lines, o):
    """Instrument heads in a row: each shows its name and the figure's value, as given (no unit the figure lacks)."""
    n = len(gs); S, gap = 0.115, 0.03; W = n * S + (n - 1) * gap; labels = []
    for i, g in enumerate(gs):
        x = cx - W / 2 + S / 2 + i * (S + gap)
        C.obj('head', C.rbox('head', (S, 0.022, S), 0.01, 3), C.simple('head-black', '#111214', 0.35, coat=0.6), (x, 0.0, 0.0))
        if g[0] == 'AWA' and not re.match(r'^-?\d', g[1]):      # the needle swinging: an analog wind dial
            KI.gauge(face('awa'), (x, -0.0115, 0.0), 0.045, value_angle=None, bezel='dark')
        else:
            rect('screen', 0.092, 0.069, face('inst', g[0], g[1]), (x, -0.0115, 0.002), 1.4, 0.12)
        labels += tag(g, (x, 0, S / 2 + 0.004))
    return labels, W

UNITS = {'engine': u_engine, 'tach': u_tach, 'monitor': u_monitor, 'ac': u_ac, 'water': u_water, 'bilge': u_bilge, 'dc': u_dc, 'nav': u_nav}
WIDTH = {'engine': 0.40, 'tach': 0.17, 'monitor': 0.40, 'ac': 0.17, 'water': 0.20, 'bilge': 0.20, 'dc': 0.20}

def compose(f):
    us = units(f); lines = list(f.get('lines', [])); gap = 0.03 if len(us) == 2 and us[0][0] == us[1][0] == 'engine' else 0.05
    wid = lambda u: WIDTH.get(u[0]) or (len(u[1]) * 0.115 + (len(u[1]) - 1) * 0.03)
    total = sum(wid(u) for u in us) + gap * (len(us) - 1)
    inside = any(u[0] in ('monitor', 'ac', 'water', 'bilge', 'dc') for u in us)
    half = max(0.9, total / 2 + 0.5)
    KI.wall('bulkhead', -half, half, -0.6, 0.6, 0.012, KI.joinery_mat() if inside else K.mats()['hull'])
    labels = []; x = -total / 2
    for u in us:
        w = wid(u); lab, _ = UNITS[u[0]](x + w / 2, u[1], lines, u[2]); labels += lab; x += w + gap
    K.day_sky(sun_az=200, sun_el=35, strength=0.12 if inside else 0.18)
    if inside: KI.area_light((0.4, -0.7, 0.4), (0, 0, 0), 6, 0.6)
    camera_on(0.0, -0.01 if any(u[2].get('name') for u in us) else 0.0, max(0.44, total + 0.04))
    return labels, -0.6

def render(x):
    f = x['figure']; C.reset(); kind = layout(f)
    if Q.LEVEL != 'bareboat-skipper' and kind in ('engine', 'monitor'): labels, expo = compose(f)
    else: labels, expo = {'engine': engine, 'monitor': monitor, 'gas': gas, 'co': co, 'fire': fire}[kind](f)
    lines = list(f.get('lines', []))
    note, rest = (lines[0], lines[1:]) if lines else (None, [])
    C.render(Q.out_jpg(x['id']), Q.arg('--samples', 128), Q.arg('--scale', 100), expo, labels, note, space='blender',
             extra={'lines': rest})

x = Q.item('panel', Q.arg('--id', 'bs-083'))
meta(x)
render(x)
