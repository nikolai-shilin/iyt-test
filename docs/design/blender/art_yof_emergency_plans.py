# The schematics of the Yachtmaster Offshore emergency figures: writes
# docs/design/figure-style/articles/yachtmaster-offshore/emergency/<n>-plan.json, read by article-figures.html.
# A plan is a figure-schematic.js spec ({sch: ...}) where a plan view fits (the turn, the drift, the helicopter), else
# a drawn SVG in the same style: 1280 x 800, theme tokens, Carlito, the key along the bottom. SVG text is translated on
# the page by exact match through ru.json, so every text node is a whole string; pills are sized for the longer of the
# English and the Russian (RU below). Figures 12 (the log page) and 14 (the Q flag) have no plan: it adds nothing.
#   python3 docs/design/blender/art_yof_emergency_plans.py           write the plans
#   python3 docs/design/blender/art_yof_emergency_plans.py --ru      print RU (merged into ru.json by hand)
import json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ADIR = os.path.join(HERE, '..', 'figure-style', 'articles', 'yachtmaster-offshore', 'emergency')
W, H = 1280, 800
RED, GREEN, YEL, BLUE, ORANGE = '#e0251b', '#1aa34a', '#e0b400', 'var(--accent)', '#ff8a3d'

RU = {}
def ru(d): RU.update(d)

def esc(s): return str(s).replace('&', '&amp;').replace('<', '&lt;')
def txt(x, y, s, size=26, w=700, fill='var(--muted)', a='middle'):
    return f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" font-weight="{w}" fill="{fill}" text-anchor="{a}">{esc(s)}</text>'
def pill(x, y, text, kind='light', size=26, align='center'):
    n = max(len(text), len(RU.get(text, text)))
    w, h = n * size * 0.56 + size * 1.4, size * 1.7
    x = x + w / 2 if align == 'left' else x - w / 2 if align == 'right' else x
    fill = {'accent': BLUE, 'red': '#e8231a', 'green': GREEN, 'yellow': '#d9a400', 'ink': 'var(--ink)'}.get(kind, 'var(--bg)')
    ink = 'var(--ink)' if kind == 'light' else ('var(--bg)' if kind == 'ink' else '#fff')
    stroke = 'var(--tag-line)' if kind == 'light' else fill
    return f'<rect x="{x - w / 2:.1f}" y="{y - h / 2:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{h / 2:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="3"/>' + txt(x, y + size * 0.36, text, size, 700, ink)
def line(x1, y1, x2, y2, c='var(--ink)', w=5, dash=None):
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{c}" stroke-width="{w}" stroke-linecap="round"' + (f' stroke-dasharray="{dash}"' if dash else '') + '/>'
def path(d, c='var(--ink)', w=5, dash=None, fill='none', extra=''):
    return f'<path d="{d}" fill="{fill}" stroke="{c}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"' + (f' stroke-dasharray="{dash}"' if dash else '') + f' {extra}/>'
def arrow(x1, y1, x2, y2, c='var(--ink)', w=5, h=18, dash=None):
    a = math.atan2(y2 - y1, x2 - x1); p1 = (x2 - h * math.cos(a - .5), y2 - h * math.sin(a - .5)); p2 = (x2 - h * math.cos(a + .5), y2 - h * math.sin(a + .5))
    return line(x1, y1, x2, y2, c, w, dash) + f'<path d="M{x2:.1f} {y2:.1f} L{p1[0]:.1f} {p1[1]:.1f} L{p2[0]:.1f} {p2[1]:.1f} Z" fill="{c}"/>'
def rect(x, y, w, h, fill='var(--bg)', stroke='var(--ink)', sw=4, rx=10, extra=''):
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" {extra}/>'
def circle(x, y, r, fill='var(--bg)', stroke='var(--ink)', sw=4, dash=None):
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"' + (f' stroke-dasharray="{dash}"' if dash else '') + '/>'
def num(x, y, n, fill=BLUE): return circle(x, y, 24, fill, 'var(--bg)', 4) + txt(x, y + 10, n, 28, 700, '#fff')
def svg(body, title, key):
    keyH = 40 + 40 * len(key) + 24
    s = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="Carlito, Arial, sans-serif" style="background:var(--bg)"><rect width="{W}" height="{H}" fill="var(--bg)"/>'
    s += body + f'<rect x="0" y="{H - keyH}" width="{W}" height="{keyH}" fill="var(--band)"/>' + txt(30, H - keyH + 40, title, 30, 700, 'var(--ink)', 'start')
    for i, k in enumerate(key): s += txt(30, H - keyH + 80 + 40 * i, '·', 27, 400, 'var(--ink)', 'start') + txt(44, H - keyH + 80 + 40 * i, k, 27, 400, 'var(--ink)', 'start')
    return {'noScale': True, 'svg': s + '</svg>'}

def fwd(h): return math.sin(math.radians(h)), math.cos(math.radians(h))

# ------------------------------------------------------------------------------------------------ 1 Scharnow
def p1():
    R = 26.0
    def track(Ls):
        x = y = 0.0; h = 130.0; pts = [(x, y)]; mk = {}
        def step(ds, dh):
            nonlocal x, y, h
            h += dh; x += math.sin(math.radians(h)) * ds; y += math.cos(math.radians(h)) * ds; pts.append((x, y))
        for i in range(240): step(R * math.radians(1), 1)
        mk['rev'] = (x, y)
        for i in range(10): step(Ls / 10, 0)
        for i in range(60): step(R * math.radians(1), -1)
        return pts, mk
    ux, uy = fwd(130); lo, hi = 0.0, 80.0
    for _ in range(40):
        mid = (lo + hi) / 2; pts, mk = track(mid); x, y = pts[-1]
        if x * uy - y * ux > 0: lo = mid
        else: hi = mid
    pts, mk = track((lo + hi) / 2)
    Z = lambda p: [round(p[0], 1), round(-p[1], 1)]
    bx, by = fwd(310); end = pts[-1]
    you = (end[0] + bx * 30, end[1] + by * 30)
    mob = (-ux * 150, -uy * 150)
    def T(p, h, d, text, kind='light'):
        dx, dy = fwd(h); return {'x': round(p[0] + dx * d, 1), 'z': round(-(p[1] + dy * d), 1), 'text': text, 'kind': kind}
    sch = {'padPx': 80, 'title': 'Scharnow turn from 130°T', 'key': ['Wheel hard to starboard; at 130° + 240° = 010°T, wheel hard to port', 'Steady on the reciprocal, 310°T: she comes back down her own wake'],
           'paths': [{'pts': [Z((-ux * 175, -uy * 175)), Z((0, 0))], 'c': 'ink', 'w': 4, 'dash': '10 10'},
                     {'pts': [Z(p) for p in pts[::6]] + [Z(end)], 'w': 6},
                     {'pts': [Z(end), Z(you)], 'w': 6, 'arrow': True}],
           'boats': [{'you': True, 'x': round(you[0], 1), 'z': round(-you[1], 1), 'hdg': 310, 'noHeading': True, 'scale': 2.0}],
           'circles': [{'x': round(mob[0], 1), 'z': round(-mob[1], 1), 'r': 2.5, 'c': 'red', 'dash': '1 0', 'fill': '#e0251b'}],
           'texts': [T((0, 0), 40, 62, '1 · 130°T: hard to starboard'), T(mk['rev'], 220, 34, '2 · 010°T: hard to port'),
                     T(you, 40, 52, '3 · steady on 310°T', 'accent'), T(mob, 40, 40, 'MOB: back along the wake', 'red')]}
    ru({'Scharnow turn from 130°T': 'Поворот Шарнова с курса 130° ист.',
        'Wheel hard to starboard; at 130° + 240° = 010°T, wheel hard to port': 'Штурвал право на борт; на 130° + 240° = 010° ист. — лево на борт',
        'Steady on the reciprocal, 310°T: she comes back down her own wake': 'Лечь на обратный курс 310° ист.: яхта идёт назад по своему следу',
        '1 · 130°T: hard to starboard': '1 · 130° ист.: право на борт', '2 · 010°T: hard to port': '2 · 010° ист.: лево на борт',
        '3 · steady on 310°T': '3 · курс 310° ист.', 'MOB: back along the wake': 'ЧЗБ: назад по следу'})
    return {'sch': sch}

# ------------------------------------------------------------------------------------------------ 2 the drift
def p2():
    sch = {'padPx': 110, 'wind': 270, 'title': 'Man overboard · a high-sided motor yacht', 'key': ['Stop upwind of him, beam-on, propellers still', 'She drifts faster than he does: let her come down onto him, lift amidships to leeward'],
           'boats': [{'you': True, 'x': 0, 'z': 0, 'hdg': 0, 'noHeading': True, 'scale': 3.4, 'label': 'stopped, beam-on'}],
           'circles': [{'x': 70, 'z': 0, 'r': 1.5, 'c': 'red', 'dash': '1 0', 'fill': '#e0251b'}],
           'paths': [{'pts': [[12, 0], [60, 0]], 'c': 'red', 'w': 7, 'arrow': True, 'dash': '14 10'}],
           'dims': [{'a': [0, -26], 'b': [70, -26], 'text': '70 m'}],
           'texts': [{'x': 70, 'z': 12, 'text': 'MOB', 'kind': 'red'}, {'x': 36, 'z': 9, 'text': 'drift'}],
           'fit': [{'x': -30, 'z': -40}, {'x': 90, 'z': 30}]}
    ru({'Man overboard · a high-sided motor yacht': 'Человек за бортом · высокобортная моторная яхта',
        'Stop upwind of him, beam-on, propellers still': 'Остановиться на ветре от него, лагом, винты стоят',
        'She drifts faster than he does: let her come down onto him, lift amidships to leeward': 'Её сносит быстрее, чем его: пусть дрейфует на него, подъём в середине подветренного борта',
        'stopped, beam-on': 'стоп, лагом', 'drift': 'дрейф', '70 m': '70 м', 'MOB': 'ЧЗБ'})
    return {'sch': sch}

# ------------------------------------------------------------------------------------------------ 3 engine-room fire
def p3():
    b = rect(260, 150, 760, 330, 'var(--band)', 'var(--ink)', 5, 18) + txt(640, 135, 'engine room', 28, 700, 'var(--ink)')
    for x in (390, 610): b += rect(x - 70, 250, 140, 130, '#5a6068', 'var(--ink)', 4, 10) + txt(x, 400 + 24, 'engine', 24, 700, 'var(--ink)')
    b += rect(780, 270, 120, 90, '#5a6068', 'var(--ink)', 4, 10) + txt(840, 384, 'generator', 24, 700, 'var(--ink)')
    for x in (300, 980):
        b += circle(x, 190, 26, 'var(--bg)', 'var(--ink)', 4) + line(x - 16, 174, x + 16, 206, RED, 5) + line(x + 16, 174, x - 16, 206, RED, 5)
    b += rect(930, 400, 90, 80, RED, 'var(--ink)', 4, 8) + txt(975, 450, 'CO₂', 24, 700, '#fff')
    b += line(1020, 300, 1020, 400, 'var(--bg)', 10) + line(1020, 300, 1020, 400, 'var(--ink)', 4, '8 8')
    for (x, y, n, t) in ((70, 560, '1', 'stop engines, generator'), (70, 610, '2', 'fans off, flaps and door shut'), (680, 560, '3', 'count everyone out'), (680, 610, '4', 'then release; keep it shut')):
        b += num(x, y, n, RED if n == '4' else BLUE) + txt(x + 40, y + 9, t, 28, 700, 'var(--ink)', 'start')
    b += pill(300, 110, 'fan, flap shut', 'light', 22) + pill(1060, 520, 'fixed system', 'red', 22)
    ru({'engine room': 'машинное отделение', 'engine': 'двигатель', 'generator': 'генератор', 'CO₂': 'CO₂', 'fan, flap shut': 'вентилятор, заслонка закрыта',
        'fixed system': 'стационарная система', 'stop engines, generator': 'стоп двигатели, генератор', 'fans off, flaps and door shut': 'вентиляторы, заслонки, дверь: закрыть',
        'count everyone out': 'все вышли: пересчитать', 'then release; keep it shut': 'затем пуск; не открывать',
        'Engine-room fire · in order': 'Пожар в машинном отделении · по порядку',
        'A fixed system works only in a closed space': 'Стационарная система работает только в закрытом отсеке',
        'Opened early, the fire reignites: cool the bulkhead for the hold time': 'Откроете рано — огонь вспыхнет снова: охлаждайте переборку всё время выдержки'})
    return svg(b, 'Engine-room fire · in order', ['A fixed system works only in a closed space', 'Opened early, the fire reignites: cool the bulkhead for the hold time'])

# ------------------------------------------------------------------------------------------------ 4 litres
def p4():
    x0, X = 300, lambda l: 300 + l * 1.25
    b = ''
    for y, lab, val, col in ((90, 'in', 650, RED), (190, 'pumps out', 250, BLUE), (290, 'net', 400, RED)):
        b += txt(270, y + 42, lab, 30, 700, 'var(--ink)', 'end') + rect(x0, y, X(val) - x0, 64, col, 'none', 0, 8, 'opacity=".85"') + txt(X(val) + 16, y + 43, f'{val} L/min', 30, 700, 'var(--ink)', 'start')
    # the time to go: 6,000 L at 400 L/min
    ty, tx0, tx1 = 450, 140, 1140; T = lambda m: tx0 + (tx1 - tx0) * m / 15
    b += rect(tx0, ty, tx1 - tx0, 60, 'var(--band)', 'var(--ink)', 4, 10)
    b += f'<rect x="{tx0}" y="{ty}" width="{tx1 - tx0}" height="60" rx="10" fill="{RED}" opacity=".25"/>'
    for m in (0, 5, 10, 15): b += line(T(m), ty + 60, T(m), ty + 78, 'var(--ink)', 4) + txt(T(m), ty + 110, f'{m} min', 26, 700, 'var(--ink)')
    b += txt((tx0 + tx1) / 2, ty + 41, '6,000 L more aboard', 30, 700, 'var(--ink)')
    b += pill(T(15) - 10, ty - 36, 'lost', 'red', 26, 'right')
    ru({'in': 'внутрь', 'pumps out': 'помпы наружу', 'net': 'чистых', '650 L/min': '650 л/мин', '250 L/min': '250 л/мин', '400 L/min': '400 л/мин',
        '6,000 L more aboard': 'ещё 6000 л на борту', '0 min': '0 мин', '5 min': '5 мин', '10 min': '10 мин', '15 min': '15 мин', 'lost': 'гибель',
        'How long have you got?': 'Сколько у вас времени?',
        'In 650 L/min, pumps 250 L/min: net 400 L/min': 'Внутрь 650 л/мин, помпы 250 л/мин: чистых 400 л/мин',
        '6,000 ÷ 400 = 15 min: distress alert and rafts now': '6000 ÷ 400 = 15 мин: сигнал бедствия и плоты — сейчас'})
    return svg(b, 'How long have you got?', ['In 650 L/min, pumps 250 L/min: net 400 L/min', '6,000 ÷ 400 = 15 min: distress alert and rafts now'])

# ------------------------------------------------------------------------------------------------ 5 range
def p5():
    x0, x1, y = 120, 1160, 250; X = lambda m: x0 + (x1 - x0) * m / 120
    b = rect(x0, y, X(96) - x0, 80, BLUE, 'none', 0, 10, 'opacity=".9"') + rect(X(96), y, X(120) - X(96), 80, YEL, 'none', 0, 10, 'opacity=".9"')
    b += rect(x0, y, x1 - x0, 80, 'none', 'var(--ink)', 4, 10)
    b += txt(X(48), y + 51, 'under power: 96 M', 30, 700, '#fff') + txt(X(108), y + 51, '24 M', 28, 700, 'var(--ink)')
    b += txt(x0, y - 30, 'here', 28, 700, 'var(--ink)', 'start') + txt(x1, y - 30, 'port, 120 M', 28, 700, 'var(--ink)', 'end')
    b += pill(X(108), y + 140, 'jury rig', 'yellow', 26)
    # the fuel
    fy = 470; F = lambda l: x0 + (x1 - x0) * l / 90
    b += rect(x0, fy, F(72) - x0, 60, 'var(--accent)', 'none', 0, 8, 'opacity=".55"') + rect(F(72), fy, F(90) - F(72), 60, RED, 'none', 0, 8, 'opacity=".75"') + rect(x0, fy, x1 - x0, 60, 'none', 'var(--ink)', 4, 8)
    b += txt(F(36), fy + 40, 'usable 72 L ÷ 4.5 L/h = 16 h', 28, 700, 'var(--ink)') + txt(F(81), fy + 40, 'keep 18 L', 26, 700, '#fff')
    b += txt(x0, fy - 20, 'fuel 90 L', 28, 700, 'var(--ink)', 'start')
    ru({'under power: 96 M': 'под мотором: 96 миль', '24 M': '24 мили', 'here': 'вы здесь', 'port, 120 M': 'порт, 120 миль', 'jury rig': 'аварийный парус',
        'usable 72 L ÷ 4.5 L/h = 16 h': 'можно 72 л ÷ 4,5 л/ч = 16 ч', 'keep 18 L': 'резерв 18 л', 'fuel 90 L': 'топливо 90 л',
        'Range under power': 'Дальность под мотором',
        'Fuel 90 L, keep 20%: 72 L; 16 h × 6 kn = 96 M': 'Топливо 90 л, резерв 20%: 72 л; 16 ч × 6 уз = 96 миль',
        'Port 120 M off: a jury rig for the last 24 M': 'Порт в 120 милях: последние 24 мили под аварийным парусом'})
    return svg(b, 'Range under power', ['Fuel 90 L, keep 20%: 72 L; 16 h × 6 kn = 96 M', 'Port 120 M off: a jury rig for the last 24 M'])

# ------------------------------------------------------------------------------------------------ 6 no charging
def p6():
    b = rect(520, 230, 240, 150, '#2b2e33', 'var(--ink)', 4, 12) + rect(548, 214, 40, 16, RED, 'none', 0, 4) + rect(692, 214, 40, 16, '#111', 'none', 0, 4)
    b += txt(640, 322, '11.9 V', 46, 700, '#ffc43c')
    b += rect(530, 70, 220, 80, 'var(--band)', 'var(--ink)', 4, 10) + txt(640, 120, 'alternator', 28, 700, 'var(--ink)')
    b += line(640, 150, 640, 230, 'var(--muted)', 5, '10 8') + pill(640, 190, '0 A: belt gone', 'red', 24)
    on = ['nav lights', 'VHF']; off = ['plotter, radar', 'autopilot', 'fridge', 'instruments']
    for i, t in enumerate(on):
        y = 260 + i * 90; b += arrow(520, 305, 330, y, GREEN, 6) + pill(200, y, t, 'green', 28)
    for i, t in enumerate(off):
        y = 190 + i * 80; b += line(760, 305, 900, y, 'var(--muted)', 4, '8 8') + pill(1060, y, t, 'light', 26) + line(980, y, 1140, y, RED, 4)
    b += txt(200, 140, 'on', 32, 700, GREEN) + txt(1060, 140, 'off', 32, 700, 'var(--muted)')
    b += pill(640, 520, 'plot on paper', 'accent', 28)
    ru({'11.9 V': '11,9 В', 'alternator': 'генератор', '0 A: belt gone': '0 А: ремень порван', 'nav lights': 'ходовые огни', 'VHF': 'УКВ',
        'plotter, radar': 'плоттер, радар', 'autopilot': 'автопилот', 'fridge': 'холодильник', 'instruments': 'приборы', 'on': 'вкл.', 'off': 'выкл.',
        'plot on paper': 'прокладка на бумаге', 'No charging · 30 h to go': 'Нет зарядки · идти 30 ч',
        'No spare belt: the alternator gives 0 A, the house bank at 11.9 V': 'Запасного ремня нет: генератор 0 А, бытовой банк 11,9 В',
        'Nav lights and VHF stay on; everything else off, plot on paper': 'Ходовые огни и УКВ включены, остальное выключить, прокладка на бумаге'})
    return svg(b, 'No charging · 30 h to go', ['No spare belt: the alternator gives 0 A, the house bank at 11.9 V', 'Nav lights and VHF stay on; everything else off, plot on paper'])

# ------------------------------------------------------------------------------------------------ 7 1-10-1
def p7():
    y = 110; segs = [(60, 360, RED, '1 min', 'cold shock: breathe'), (360, 780, YEL, '10 min', 'swim now'), (780, 1220, BLUE, '1 hour', 'keep still')]
    b = ''
    for xa, xb, c, t, s in segs:
        b += rect(xa, y, xb - xa, 70, c, 'none', 0, 8, 'opacity=".85"') + txt((xa + xb) / 2, y + 45, s, 26, 700, '#fff') + line(xb, y - 10, xb, y + 84, 'var(--ink)', 4) + txt(xb, y + 116, t, 28, 700, 'var(--ink)', 'end')
    # HELP: a figure leaning back, knees up, arms crossed; the huddle: heads in a ring
    hx, hy = 330, 360
    b += path(f'M{hx - 120} {hy + 40} Q{hx} {hy + 20} {hx + 120} {hy + 40}', '#3c8cbe', 5)
    b += path(f'M{hx - 30} {hy - 40} L{hx + 10} {hy + 30}', 'var(--ink)', 34) + circle(hx - 44, hy - 64, 26, 'var(--ink)', 'none', 0)
    b += path(f'M{hx + 10} {hy + 30} L{hx + 70} {hy - 10} L{hx + 80} {hy + 50}', 'var(--ink)', 22)
    b += path(f'M{hx - 40} {hy - 20} L{hx + 20} {hy - 5} M{hx - 20} {hy + 5} L{hx + 20} {hy - 30}', '#ff6a2a', 12)
    b += txt(hx, hy + 110, 'alone: HELP', 30, 700, 'var(--ink)') + txt(hx, hy + 146, 'knees up, arms crossed, still', 26, 400, 'var(--ink)')
    cx, cy = 900, 350
    for k in range(4):
        a = math.radians(45 + k * 90); x, yy = cx + math.cos(a) * 52, cy + math.sin(a) * 52
        b += circle(x, yy, 34, '#ff6a2a', 'var(--ink)', 3) + circle(x - math.cos(a) * 6, yy - math.sin(a) * 6, 16, 'var(--ink)', 'none', 0)
    b += txt(cx, hy + 110, 'together: huddle', 30, 700, 'var(--ink)') + txt(cx, hy + 146, 'chests touching', 26, 400, 'var(--ink)')
    ru({'cold shock: breathe': 'холодовой шок: дыхание', 'swim now': 'плыть сейчас', 'keep still': 'не двигаться', '1 min': '1 мин', '10 min': '10 мин', '1 hour': '1 час',
        'alone: HELP': 'один: HELP', 'knees up, arms crossed, still': 'колени к груди, руки крестом, неподвижно', 'together: huddle': 'вместе: группой',
        'chests touching': 'грудь к груди', 'Cold water: 1-10-1': 'Холодная вода: 1-10-1',
        '1 minute of cold shock · 10 minutes of useful movement · 1 hour before hypothermia': '1 минута холодового шока · 10 минут полезных движений · 1 час до переохлаждения',
        'After that, keep still and keep warm: HELP alone, a huddle together': 'Дальше не двигаться и беречь тепло: HELP в одиночку, группой вместе'})
    return svg(b, 'Cold water: 1-10-1', ['1 minute of cold shock · 10 minutes of useful movement · 1 hour before hypothermia', 'After that, keep still and keep warm: HELP alone, a huddle together'])

# ------------------------------------------------------------------------------------------------ 8 helicopter
def p8():
    hx, hy = fwd(70 + 225); hx, hy = hx * 34, hy * 34
    wx, wy = fwd(40)
    sch = {'padPx': 110, 'wind': 40, 'title': 'Helicopter rescue · the course to steer', 'key': ['The pilot asks for the wind 30° on the port bow: 040°T + 30° = steer 070°T', 'Hold course and speed; he keeps station on you over the port quarter'],
           'boats': [{'you': True, 'x': 0, 'z': 0, 'hdg': 70, 'scale': 3.0, 'label': 'You'}],
           'circles': [{'x': round(hx, 1), 'z': round(-hy, 1), 'r': 9, 'c': 'ink', 'dash': '8 8'}],
           'paths': [{'pts': [[0, 0], [round(wx * 40, 1), round(-wy * 40, 1)]], 'c': 'red', 'w': 4, 'dash': '8 8'}],
           'texts': [{'x': round(hx, 1), 'z': round(-hy + 15, 1), 'text': 'helicopter'}, {'x': round(wx * 52, 1), 'z': round(-wy * 52, 1), 'text': 'wind 040°T', 'kind': 'red'},
                     {'x': round(fwd(55)[0] * 26, 1), 'z': round(-fwd(55)[1] * 26, 1), 'text': '30°'}],
           'fit': [{'x': -45, 'z': -55}, {'x': 55, 'z': 30}]}
    ru({'Helicopter rescue · the course to steer': 'Спасание вертолётом · какой курс держать',
        'The pilot asks for the wind 30° on the port bow: 040°T + 30° = steer 070°T': 'Пилот просит ветер 30° с левой скулы: 040° ист. + 30° = курс 070° ист.',
        'Hold course and speed; he keeps station on you over the port quarter': 'Держите курс и скорость; он держится над вашей левой раковиной',
        'helicopter': 'вертолёт', 'wind 040°T': 'ветер 040° ист.', '30°': '30°'})
    return {'sch': sch}

# ------------------------------------------------------------------------------------------------ 9 sea areas
def p9():
    b = rect(0, 0, 130, 560, '#d8c9a3', 'none', 0, 0) + line(130, 0, 130, 560, '#6b5a3a', 5)
    sx, sy = 130, 300
    for r, c, op in ((780, ORANGE, '.10'), (330, '#3c8cbe', '.16')):
        b += f'<path d="M{sx} {sy - r} A{r} {r} 0 0 1 {sx} {sy + r}" fill="{c}" fill-opacity="{op}" stroke="{c}" stroke-width="5" stroke-dasharray="16 10" clip-path="url(#emg9clip)"/>'
    b = f'<defs><clipPath id="emg9clip"><rect x="0" y="0" width="1280" height="560"/></clipPath></defs>' + b
    b += f'<path d="M{sx - 16} {sy} L{sx} {sy - 64} L{sx + 16} {sy} Z" fill="var(--ink)"/>' + circle(sx, sy - 68, 9, RED, 'none', 0) + pill(sx + 20, sy + 40, 'coast station', 'light', 22, 'left')
    for x, a, s1, s2, c in ((300, 'A1', 'VHF DSC', '≈ 30 M', 'accent'), (700, 'A2', 'MF DSC', '≈ 150 M', 'yellow'), (1080, 'A3', 'satellite', '', 'light')):
        b += txt(x, 140, a, 54, 700, 'var(--ink)') + txt(x, 185, s1, 30, 700, 'var(--ink)') + (txt(x, 222, s2, 28, 400, 'var(--ink)') if s2 else '')
    bx, by = 760, 400
    b += f'<g transform="translate({bx} {by}) rotate(20) scale(2.2)"><path d="M0 -22 C 7 -14 8 6 6 18 L -6 18 C -8 6 -7 -14 0 -22 Z" fill="var(--ink)"/><circle cx="0" cy="-2" r="4" fill="var(--accent)"/></g>'
    b += pill(bx, by + 76, 'You: MF DSC 2187.5 kHz', 'accent', 24)
    ru({'coast station': 'берег. станция', 'VHF DSC': 'УКВ ЦИВ', 'MF DSC': 'ПВ ЦИВ', 'satellite': 'спутник', '≈ 30 M': '≈ 30 миль', '≈ 150 M': '≈ 150 миль',
        'You: MF DSC 2187.5 kHz': 'Вы: ПВ ЦИВ 2187,5 кГц', 'GMDSS sea areas · what the shore hears': 'Морские районы ГМССБ · что слышит берег',
        'A1: VHF DSC · A2: MF DSC beyond it · A3: satellite · A4: the poles': 'A1: УКВ ЦИВ · A2: ПВ ЦИВ за ней · A3: спутник · A4: полярные воды',
        'Beyond VHF range: distress by MF DSC on 2187.5 kHz, speech on 2182 kHz': 'Вне зоны УКВ: бедствие по ПВ ЦИВ на 2187,5 кГц, голосом на 2182 кГц'})
    return svg(b, 'GMDSS sea areas · what the shore hears', ['A1: VHF DSC · A2: MF DSC beyond it · A3: satellite · A4: the poles', 'Beyond VHF range: distress by MF DSC on 2187.5 kHz, speech on 2182 kHz'])

# ------------------------------------------------------------------------------------------------ 10 who sees what
def p10():
    b = ''
    rows = [(110, 'EPIRB', '406 MHz', 'satellite → MRCC', 'registered to you, flag state'), (260, 'radar SART', 'radar sweep', "a ship's radar: 12 dots", 'flashes when swept'),
            (410, 'AIS-SART', 'AIS', 'every AIS screen', 'with its position')]
    for y, a, via, to, sub in rows:
        b += rect(60, y - 40, 260, 80, '#f2b705', 'var(--ink)', 4, 14) + txt(190, y + 10, a, 32, 700, 'var(--ink)')
        b += arrow(330, y, 800, y, 'var(--muted)', 5, 20, '12 10') + pill(565, y - 36, via, 'light', 24)
        b += rect(820, y - 40, 400, 80, 'var(--band)', 'var(--ink)', 4, 14) + txt(1020, y + 10, to, 28, 700, 'var(--ink)')
        b += txt(565, y + 40, sub, 24, 400, 'var(--ink)')
    ru({'EPIRB': 'АРБ', 'radar SART': 'радио-SART', 'AIS-SART': 'AIS-SART', '406 MHz': '406 МГц', 'radar sweep': 'луч РЛС', 'AIS': 'AIS',
        'satellite → MRCC': 'спутник → MRCC', "a ship's radar: 12 dots": 'РЛС судна: 12 точек', 'every AIS screen': 'все экраны AIS',
        'registered to you, flag state': 'зарегистрирован на вас у флага', 'flashes when swept': 'отвечает на облучение', 'with its position': 'с координатами',
        'In the grab bag · who sees what': 'В аварийной сумке · кто что увидит',
        'False alert from the EPIRB: switch it off and tell the MRCC': 'Ложный сигнал АРБ: выключить и сообщить в MRCC',
        'NAVTEX: nav, gale and SAR messages always print': 'NAVTEX: навигационные, штормовые и SAR печатаются всегда'})
    return svg(b, 'In the grab bag · who sees what', ['False alert from the EPIRB: switch it off and tell the MRCC', 'NAVTEX: nav, gale and SAR messages always print'])

# ------------------------------------------------------------------------------------------------ 11 silence
def p11():
    b = ''; y = 200
    steps = [(70, 250, 'MAYDAY', RED, 'distress'), (340, 600, 'SEELONCE MAYDAY', RED, 'silence'), (690, 900, 'PRUDONCE', '#d9a400', 'restricted working'), (990, 1230, 'SEELONCE FEENEE', GREEN, 'normal working')]
    for i, (xa, xb, t, c, s) in enumerate(steps):
        b += rect(xa, y, xb - xa, 90, c, 'none', 0, 14) + txt((xa + xb) / 2, y + 56, t, 30 if len(t) < 12 else 26, 700, '#fff') + txt((xa + xb) / 2, y + 140, s, 26, 700, 'var(--ink)')
        if i: b += arrow(steps[i - 1][1] + 8, y + 45, xa - 8, y + 45, 'var(--ink)', 5, 18)
    b += pill(470, 120, 'casualty or control station', 'light', 22) + line(470, 140, 470, y, 'var(--muted)', 3)
    b += rect(340, 400, 260, 70, 'none', RED, 4, 14, 'stroke-dasharray="10 8"') + txt(470, 444, 'SEELONCE DISTRESS', 26, 700, RED)
    b += txt(470, 505, 'from any other station nearby', 24, 400, 'var(--ink)')
    ru({'MAYDAY': 'MAYDAY', 'SEELONCE MAYDAY': 'SEELONCE MAYDAY', 'PRUDONCE': 'PRUDONCE', 'SEELONCE FEENEE': 'SEELONCE FEENEE', 'SEELONCE DISTRESS': 'SEELONCE DISTRESS',
        'distress': 'бедствие', 'silence': 'молчание', 'restricted working': 'ограниченная работа', 'normal working': 'обычная работа',
        'casualty or control station': 'бедствующий или ведущий связь', 'from any other station nearby': 'от любой другой станции рядом',
        'Silence on channel 16': 'Молчание на 16-м канале',
        'Silence is imposed by the casualty or the station controlling the distress': 'Молчание объявляет бедствующий или станция, ведущая связь при бедствии',
        'Only SEELONCE FEENEE ends it: normal working on 16 again': 'Снимает его только SEELONCE FEENEE: на 16-м снова обычная работа'})
    return svg(b, 'Silence on channel 16', ['Silence is imposed by the casualty or the station controlling the distress', 'Only SEELONCE FEENEE ends it: normal working on 16 again'])

# ------------------------------------------------------------------------------------------------ 13 limits
def p13():
    coast = 'C 520 120 600 230 540 330 C 500 420 560 500 520 560'
    b = '<defs><clipPath id="emg13clip"><rect x="0" y="0" width="1280" height="560"/></clipPath></defs><g clip-path="url(#emg13clip)">'
    b += path('M560 -20 L560 0 ' + coast + ' L520 600', '#3c8cbe', 230, extra='stroke-opacity=".16" stroke-linecap="butt"')
    b += path('M0 0 L560 0 ' + coast + ' L0 560 Z', '#6b5a3a', 5, fill='#d8c9a3')
    b += path('M675 0 C 635 120 715 230 655 330 C 615 420 675 500 635 560', '#3c8cbe', 5, '16 10') + '</g>'
    b += pill(700, 80, 'cruising area: within 60 M of the coast', 'accent', 24) + txt(240, 260, 'land', 30, 700, '#6b5a3a')
    b += path('M560 420 C 760 430 960 470 1130 480', YEL, 7, '16 12') + circle(1150, 485, 30, '#d8c9a3', '#6b5a3a', 4)
    b += pill(940, 380, 'outside: extension in writing', 'red', 24) + txt(1150, 545, 'island', 24, 700, 'var(--ink)')
    b += rect(760, 180, 440, 70, 'var(--band)', 'var(--ink)', 3, 12) + txt(980, 225, 'season: 1 April – 31 October', 26, 700, 'var(--ink)')
    ru({'cruising area: within 60 M of the coast': 'район плавания: до 60 миль от берега', 'land': 'берег', 'outside: extension in writing': 'за пределами: продление письменно',
        'island': 'остров', 'season: 1 April – 31 October': 'сезон: 1 апреля – 31 октября', 'Before the passage: the policy': 'Перед переходом: полис',
        'Outside the area or the season: only with a written extension': 'Вне района или сезона — только с письменным продлением',
        "Warranties: skipper's certificate, private use, crew · disclose every material fact": 'Гарантии: сертификат шкипера, частное использование, экипаж · раскрыть все существенные факты'})
    return svg(b, 'Before the passage: the policy', ['Outside the area or the season: only with a written extension', "Warranties: skipper's certificate, private use, crew · disclose every material fact"])

# ------------------------------------------------------------------------------------------------ 15 salvage
def p15():
    x0, x1 = 120, 1160
    b = txt(x0, 110, 'saved', 30, 700, 'var(--ink)', 'start')
    b += rect(x0, 130, x1 - x0, 80, 'var(--band)', 'var(--ink)', 4, 10) + txt((x0 + x1) / 2, 182, 'value saved: yacht and property', 28, 700, 'var(--ink)')
    b += rect(x0, 240, (x1 - x0) * 0.35, 70, GREEN, 'none', 0, 10, 'opacity=".85"') + txt(x0 + 20, 285, 'award', 28, 700, '#fff', 'start')
    b += line(x1, 120, x1, 330, RED, 5, '10 8') + pill(x1 - 10, 360, 'never more than the value saved', 'red', 24, 'right')
    b += txt(x0, 450, 'lost', 30, 700, 'var(--ink)', 'start')
    b += rect(x0, 470, x1 - x0, 70, 'none', 'var(--muted)', 4, 10, 'stroke-dasharray="12 10"') + txt((x0 + x1) / 2, 515, 'no cure, no pay: no award', 28, 700, 'var(--muted)')
    ru({'saved': 'спасено', 'lost': 'потеряно', 'value saved: yacht and property': 'спасённая стоимость: яхта и имущество', 'award': 'вознаграждение',
        'never more than the value saved': 'не больше спасённой стоимости', 'no cure, no pay: no award': 'нет спасения — нет вознаграждения',
        'Salvage Convention 1989 · no cure, no pay': 'Конвенция о спасании 1989 · нет спасения — нет оплаты',
        'No danger: a towage price · beyond the contract: salvage for extra work': 'Нет опасности — цена буксировки · сверх договора — спасание за лишнюю работу',
        'The master signs the agreement; those who save lives get a share': 'Договор подписывает капитан; спасшие людей получают долю'})
    return svg(b, 'Salvage Convention 1989 · no cure, no pay', ['No danger: a towage price · beyond the contract: salvage for extra work', 'The master signs the agreement; those who save lives get a share'])

PLANS = {1: p1, 2: p2, 3: p3, 4: p4, 5: p5, 6: p6, 7: p7, 8: p8, 9: p9, 10: p10, 11: p11, 13: p13, 15: p15}

if __name__ == '__main__':
    out = {n: f() for n, f in PLANS.items()}
    if '--ru' in sys.argv: print(json.dumps(RU, ensure_ascii=False, indent=1)); sys.exit()
    # pills are sized from RU, which each plan fills as it runs: draw twice so every pill sees its Russian
    out = {n: f() for n, f in PLANS.items()}
    for n, spec in out.items():
        p = os.path.join(ADIR, f'{n}-plan.json'); json.dump(spec, open(p, 'w'), ensure_ascii=False); print(p)
