# The schematics of article yachtmaster-offshore/vessel: SVGs in the schematic's style (no plan view fits a hull
# section, a fuel line or a charge curve). Writes figure-style/articles/yachtmaster-offshore/vessel/<n>-plan.json and
# ru-plans.json (the Russian of every string here, merged into ru.json with the render labels).
#   python3 docs/design/blender/art_yof_vessel_plans.py
import json, math, os

HERE = os.path.dirname(os.path.abspath(__file__))
DIR = os.path.join(HERE, '..', 'figure-style', 'articles', 'yachtmaster-offshore', 'vessel')
RU = {}
def T(en, ru): RU[en] = ru; return en

RED, GREEN, YEL, BLUE, INK, MUTED = '#e0251b', '#1aa34a', '#e0b400', 'var(--accent)', 'var(--ink)', 'var(--muted)'
def esc(s): return str(s).replace('&', '&amp;').replace('<', '&lt;')
def txt(x, y, s, size=26, w=700, fill=MUTED, a='middle'):
    return f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" font-weight="{w}" fill="{fill}" text-anchor="{a}">{esc(s)}</text>'
def pill(x, y, text, kind='light', size=24):
    n = max(len(text), len(RU.get(text, text))); w = n * size * 0.56 + size * 1.4; h = size * 1.7
    fill = {'accent': BLUE, 'red': '#e8231a', 'green': GREEN}.get(kind, 'var(--bg)'); ink = INK if kind == 'light' else '#fff'
    stroke = 'var(--tag-line)' if kind == 'light' else fill
    return f'<rect x="{x - w / 2:.1f}" y="{y - h / 2:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{h / 2:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="3"/>' + txt(x, y + size * 0.36, text, size, 700, ink)
def line(x1, y1, x2, y2, c=INK, w=4, dash=None):
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{c}" stroke-width="{w}" stroke-linecap="round"' + (f' stroke-dasharray="{dash}"' if dash else '') + '/>'
def path(d, c=INK, w=4, fill='none', dash=None):
    return f'<path d="{d}" fill="{fill}" stroke="{c}" stroke-width="{w}" stroke-linejoin="round" stroke-linecap="round"' + (f' stroke-dasharray="{dash}"' if dash else '') + '/>'
def arrow(x1, y1, x2, y2, c=INK, w=5, h=18):
    a = math.atan2(y2 - y1, x2 - x1); p1 = (x2 - h * math.cos(a - .5), y2 - h * math.sin(a - .5)); p2 = (x2 - h * math.cos(a + .5), y2 - h * math.sin(a + .5))
    return line(x1, y1, x2, y2, c, w) + f'<path d="M{x2:.1f} {y2:.1f} L{p1[0]:.1f} {p1[1]:.1f} L{p2[0]:.1f} {p2[1]:.1f} Z" fill="{c}"/>'
def rect(x, y, w, h, fill='var(--bg)', stroke=INK, sw=4, rx=10):
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
def circle(x, y, r, fill='var(--bg)', stroke=INK, sw=4): return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
def frame(title, key, body, gid):
    W, H = 1280, 800; keyH = 40 + 40 * len(key) + 24
    s = f'<svg xmlns="http://www.w3.org/2000/svg" id="{gid}" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="Carlito, Arial, sans-serif" style="background:var(--bg)"><rect width="{W}" height="{H}" fill="var(--bg)"/>'
    s += body + f'<rect x="0" y="{H - keyH}" width="{W}" height="{keyH}" fill="var(--band)"/>' + txt(30, H - keyH + 40, title, 30, 700, INK, 'start')
    for i, k in enumerate(key): s += txt(30, H - keyH + 80 + 40 * i, '·', 27, 400, INK, 'start') + txt(46, H - keyH + 80 + 40 * i, k, 27, 400, INK, 'start')
    return {'noScale': True, 'svg': s + '</svg>'}

PL = {}
# ------------------------------------------------------------------ 1, 2: the yacht in profile on the hard
def profile(rig):
    b = ''
    hull = 'M190 330 L1050 300 C 1020 380 960 420 860 430 L330 440 C 260 430 210 390 190 330 Z'
    keel = 'M600 432 L700 430 L690 560 L590 560 Z'; rudder = 'M300 436 L330 436 L325 520 L300 520 Z'
    if not rig:
        b += line(60, 588, 1220, 588, '#8a8a84', 6) + rect(560, 560, 160, 28, '#8a6a3a', INK, 3, 3)
        b += path(hull, INK, 4, 'var(--band)') + path('M200 385 L1040 345', '#3c8cbe', 4, dash='14 8')
        b += path(keel, INK, 4, 'var(--ink)') + path(rudder, INK, 4, 'var(--ink)')
        for x, y in ((300, 438), (520, 446), (860, 432)):
            b += line(x, y, x + 40, 588, '#2c5d9e', 6) + line(x - 30, 588, x + 70, 588, '#2c5d9e', 6)
        for i in range(14): b += circle(780 + (i % 7) * 26, 395 + (i // 7) * 18, 6, '#3a3d44', INK, 1)
        b += arrow(640, 250, 640, 410, RED, 7) + pill(640, 220, T('her weight: on the keel', 'её вес — на киле'), 'red')
        b += pill(860, 360, T('osmosis: below the waterline', 'осмос — ниже ватерлинии'), 'red') + pill(1010, 250, T('waterline', 'ватерлиния'))
        b += pill(640, 620, T('long timber blocks', 'длинные брусья')) + pill(230, 620, T('stands: steady only', 'подпорки: только страхуют'), 'accent')
        b += pill(230, 520, T('rudder: wet inside?', 'перо руля: вода внутри?'))
        return frame(T('On the hard · the keel takes the weight', 'На берегу · вес на киле'),
                     [T('Slings on the builder\'s marks, the keel on long blocks; stands and chains only steady her', 'Стропы — по меткам верфи, киль — на длинных брусьях; подпорки лишь страхуют'),
                      T('Blisters under the gelcoat: osmosis · a rudder that weeps is wet inside', 'Пузыри под гелькоутом — осмос · сочится перо руля — внутри вода')], b, 'yof-ves-1')
    b += path(hull, INK, 4, 'var(--band)') + path(keel, INK, 4, 'var(--ink)') + path(rudder, INK, 4, 'var(--ink)') + line(60, 386, 1220, 342, '#3c8cbe', 4)
    b += line(600, 330, 600, 40, INK, 8) + line(600, 40, 1045, 300, INK, 4) + line(600, 40, 195, 330, INK, 4) + line(600, 60, 560, 320, INK, 3)
    for x, y, t, k, lx, ly in ((645, 445, T('keel bolts, grid', 'килевые болты, флоры'), 'light', 760, 500), (315, 438, T('rudder bearings', 'подшипники баллера'), 'light', 330, 580),
                               (1040, 300, T('forestay: swages', 'штаг: опрессовки'), 'accent', 1080, 220), (200, 330, T('backstay: chainplate', 'ахтерштаг: путенс'), 'accent', 190, 240),
                               (820, 312, T('hull-to-deck joint', 'стык корпуса и палубы'), 'light', 880, 400), (560, 320, T('shroud: chainplate, bulkhead', 'ванта: путенс, переборка'), 'light', 420, 150)):
        b += circle(x, y, 9, '#e8231a', 'var(--bg)', 3) + line(x, y, lx, ly, MUTED, 2) + pill(lx, ly, t, k)
    return frame(T('Keel, rudder, rig · where the loads go', 'Киль, руль, рангоут · куда идут нагрузки'),
                 [T('Rust weeping at a keel nut, or a nut that turns without torque rising: draw a bolt', 'Ржавчина у гайки или гайка тянется без роста момента: вынуть болт'),
                  T('A door that jams on one tack: the chainplate bulkhead is moving', 'Дверь заедает на одном галсе: переборка путенсов «ходит»')], b, 'yof-ves-2')
PL[1] = profile(False); PL[2] = profile(True)
# ------------------------------------------------------------------ 3: the righting lever
def gz():
    cx, wl = 640, 400; th = math.radians(10)
    def rot(x, y): return (cx + (x - cx) * math.cos(th) - (y - wl) * math.sin(th), wl + (x - cx) * math.sin(th) + (y - wl) * math.cos(th))
    sec = [(440, 280), (840, 280), (830, 400), (760, 470), (690, 490), (590, 490), (520, 470), (450, 400)]
    q = [rot(*p) for p in sec]
    b = path('M' + ' L'.join(f'{x:.1f} {y:.1f}' for x, y in q) + ' Z', INK, 4, 'var(--band)')
    b += path('M' + ' L'.join(f'{x:.1f} {y:.1f}' for x, y in [rot(620, 490), rot(660, 490), rot(655, 640), rot(625, 640)]) + ' Z', INK, 4, INK)
    b += line(300, wl, 980, wl, '#3c8cbe', 5)
    k = 150; Kp = rot(640, 640); G = rot(640, 640 - 2.6 * k); Mt = (G[0] + (rot(640, 640 - 3.2 * k)[0] - G[0]), rot(640, 640 - 3.2 * k)[1])
    Mt = rot(640, 640 - 3.2 * k)
    Bx = G[0] + 90; B = (Bx, 450); Z = (Bx, G[1])
    b += line(*rot(640, 230), *rot(640, 660), MUTED, 2, '8 8') + line(Mt[0], Mt[1] - 30, Mt[0], 560, MUTED, 2, '4 6')
    b += arrow(G[0], G[1], G[0], G[1] + 150, RED, 6) + arrow(B[0], B[1], B[0], B[1] - 170, BLUE, 6)
    b += line(G[0], G[1], Z[0], Z[1], INK, 6) + circle(*G, 10, RED, 'var(--bg)', 3) + circle(*B, 10, BLUE, 'var(--bg)', 3) + circle(*Mt, 9, INK, 'var(--bg)', 3) + circle(*Z, 7, INK, 'var(--bg)', 3)
    b += txt(G[0] - 24, G[1] + 8, 'G', 30, 700, RED, 'end') + txt(B[0] + 22, B[1] + 34, 'B', 30, 700, BLUE, 'start') + txt(Mt[0] + 18, Mt[1] - 6, 'M', 30, 700, INK, 'start') + txt(Z[0] + 16, Z[1] - 10, 'Z', 30, 700, INK, 'start')
    b += pill(Z[0] + 150, Z[1] + 10, T('GZ = 0.10 m', 'GZ = 0,10 м'), 'accent') + pill(1070, 180, T('KM 3.20 m · KG 2.60 m', 'KM 3,20 м · KG 2,60 м')) + pill(1070, 240, T('GM = 0.60 m', 'GM = 0,60 м'))
    b += pill(260, 560, T('heeled 10°', 'крен 10°')) + pill(B[0] + 180, B[1] + 110, T('B moves to the low side', 'B смещается к низкому борту'), 'accent')
    return frame(T('Stability · the righting lever', 'Остойчивость · плечо восстанавливающего момента'),
                 [T('Small angles: GZ ≈ GM × sin θ = 0.60 × 0.17 = 0.10 m', 'Малые углы: GZ ≈ GM × sin θ = 0,60 × 0,17 = 0,10 м'),
                  T('Righting moment = Δ × GZ = 30 t × 0.10 m = 3 t·m', 'Восстанавливающий момент = Δ × GZ = 30 т × 0,10 м = 3 т·м')], b, 'yof-ves-3')
PL[3] = gz()
# ------------------------------------------------------------------ 4: a weight on the crane head
def tender():
    b = line(200, 470, 1100, 470, '#3c8cbe', 5)
    b += path('M420 360 L860 360 L850 470 L780 540 L500 540 L430 470 Z', INK, 4, 'var(--band)')
    b += line(780, 360, 780, 220, INK, 8) + line(780, 220, 1000, 190, INK, 7) + line(1000, 190, 1000, 300, MUTED, 3)
    b += rect(940, 300, 120, 50, '#3b4046', INK, 3, 20)
    b += circle(640, 430, 11, RED, 'var(--bg)', 3) + circle(640, 400, 11, RED, 'var(--bg)', 3) + circle(655, 400, 11, '#ffa800', 'var(--bg)', 3)
    b += arrow(640, 430, 640, 404, RED, 4, 12) + arrow(640, 400, 652, 400, '#ffa800', 4, 10)
    b += pill(1000, 150, T('the weight acts here', 'вес приложен здесь'), 'accent') + pill(1000, 390, T('tender 1.0 t', 'тузик 1,0 т'))
    b += pill(440, 300, T('G up 1.0 × 4.0 ÷ 40 = 0.10 m', 'G вверх: 1,0 × 4,0 ÷ 40 = 0,10 м'), 'red') + pill(420, 590, T('G out 1.0 × 2.8 ÷ 40 = 0.07 m', 'G вбок: 1,0 × 2,8 ÷ 40 = 0,07 м'))
    b += pill(900, 590, T('tan θ = 0.07 ÷ 0.70: about 6°', 'tg θ = 0,07 ÷ 0,70: около 6°'), 'red')
    b += line(1100, 190, 1100, 470, INK, 3) + txt(1125, 340, T('4.0 m', '4,0 м'), 24, 700, INK, 'start')
    return frame(T('Launching the tender · Δ 40 t, GM 0.80 m', 'Спуск тузика · Δ 40 т, GM 0,80 м'),
                 [T('Lifted, the tender\'s weight acts at the crane head: G rises, GM falls to 0.70 m', 'Поднятый, вес тузика приложен к ноку крана: G растёт, GM падает до 0,70 м'),
                  T('Swung outboard, G moves out too: she lists until G sits under M again', 'Вынесенный за борт, G смещается вбок: крен, пока G не окажется под M')], b, 'yof-ves-4')
PL[4] = tender()
# ------------------------------------------------------------------ 5: free surface and the roll period
def roll():
    b = line(150, 380, 1130, 380, '#3c8cbe', 5)
    b += path('M380 260 L900 260 L890 390 L800 470 L480 470 L390 390 Z', INK, 4, 'var(--band)')
    b += rect(450, 400, 380, 50, 'var(--bg)', INK, 3, 4) + path('M452 430 L828 412 L828 448 L452 448 Z', '#3c8cbe', 0, '#3c8cbe') + line(640, 400, 640, 450, INK, 3, '6 6')
    b += pill(640, 520, T('slack tank: the free surface', 'неполный танк: свободная поверхность'), 'red') + pill(640, 220, T('beam 5.0 m', 'ширина 5,0 м'))
    b += line(380, 240, 900, 240, INK, 3)
    b += pill(1060, 150, T('roll 6.0 s → GM 0.44 m', 'период 6,0 с → GM 0,44 м')) + pill(1060, 210, T('roll 8.0 s → GM 0.25 m', 'период 8,0 с → GM 0,25 м'), 'red')
    b += pill(230, 150, T('centreline division: loss ÷ 4', 'продольная переборка: потеря ÷ 4'), 'accent')
    return frame(T('Roll period · Period ≈ 0.8 × beam ÷ √GM', 'Период качки · T ≈ 0,8 × ширина ÷ √GM'),
                 [T('√GM = 0.8 × 5.0 ÷ 8.0 = 0.5: GM 0.25 m · a slow, lazy roll means GM has fallen', '√GM = 0,8 × 5,0 ÷ 8,0 = 0,5: GM 0,25 м · медленная вялая качка — GM упала'),
                  T('The free-surface loss goes with the tank\'s width cubed: run tanks down one at a time', 'Потеря от свободной поверхности ~ куб ширины танка: расходуйте танки по одному')], b, 'yof-ves-5')
PL[5] = roll()
# ------------------------------------------------------------------ 6: the fuel path and the bleeding order
def fuel():
    steps = [([T('tank', 'бак')], None), ([T('primary filter', 'фильтр-'), T('and separator', 'сепаратор')], '1'), ([T('lift', 'подкачивающий'), T('pump', 'насос')], '2'),
             ([T('fine', 'фильтр тонкой'), T('filter', 'очистки')], '3'), ([T('injection', 'топливный'), T('pump', 'насос')], '4'), ([T('injectors', 'форсунки')], '5')]
    b = ''; xs = [120 + i * 208 for i in range(6)]
    for i, (ws, n) in enumerate(steps):
        x = xs[i]; y = 300; ws = [w for w in ws if w]
        b += rect(x - 90, y - 60, 180, 120, 'var(--band)', INK, 4, 14)
        for k, w in enumerate(ws): b += txt(x, y + 8 + (k - (len(ws) - 1) / 2) * 30, w, 22, 700, INK)
        if i: b += arrow(xs[i - 1] + 92, y, x - 94, y, '#8a6a3a', 6)
        if n: b += circle(x, y - 100, 26, BLUE, 'var(--bg)', 4) + txt(x, y - 90, n, 28, 700, '#fff')
    b += pill(990, 450, T('crack each union, crank', 'отдать гайки, крутить стартером'), 'red') + pill(xs[2] - 40, 450, T('air in: runs, then falters', 'подсос воздуха: работает и глохнет'))
    return {'noScale': True, 'svg': frame(T('Fuel path · bleed in the order it flows', 'Топливная система · прокачка по ходу топлива'),
                 [T('Rising filter vacuum: sludge stirred up by the sea · switch filters, polish the fuel', 'Растёт разрежение на фильтре: качка подняла осадок · переключить фильтр, очистить топливо'),
                  T('A suction-side leak draws in air without a drip', 'Негерметичность на всасывании тянет воздух без капель')], b, 'yof-ves-6')['svg']}
PL[6] = fuel()
# ------------------------------------------------------------------ 7: the raw-water circuit
def cooling():
    st = [(T('seacock', 'кингстон'), 140), (T('strainer', 'фильтр'), 330), (T('impeller', 'крыльчатка'), 520), (T('heat exchanger', 'теплообменник'), 760), (T('exhaust', 'выхлоп'), 1060)]
    b = ''; y = 300
    for i, (t, x) in enumerate(st):
        w = 280 if i == 3 else 150
        b += rect(x - w / 2, y - 55, w, 110, 'var(--band)' if i != 3 else 'rgba(224,37,27,.10)', RED if i == 3 else INK, 4, 14) + txt(x, y + (-22 if i == 3 else 9), t, 26, 700, INK)
        if i: px = st[i - 1][1] + (140 if i - 1 == 3 else 75); b += arrow(px + 4, y, x - w / 2 - 6, y, '#3c8cbe', 7)
    for k in range(4): b += line(650, 296 + k * 14, 870, 296 + k * 14, '#c9c4b5', 6)
    b += pill(760, 200, T('tubes furred with scale', 'трубки в накипи'), 'red')
    b += path('M700 355 C 700 470, 560 470, 560 520 L960 520 C 960 470, 820 470, 820 355', 'var(--accent)', 6) + pill(760, 560, T('engine coolant: full', 'антифриз: полный'), 'accent')
    b += pill(330, 440, T('flow strong', 'проток сильный')) + pill(1060, 440, T('92°', '92°'), 'red')
    return frame(T('Cooling · strong flow, still too hot', 'Охлаждение · проток сильный, а температура высокая'),
                 [T('Seacock, strainer, impeller, exchanger, exhaust: flow strong, coolant full', 'Кингстон, фильтр, крыльчатка, теплообменник, выхлоп: проток сильный, антифриз полный'),
                  T('Then the heat is not crossing the tubes: descale the exchanger', 'Значит, тепло не проходит через трубки: удалить накипь в теплообменнике')], b, 'yof-ves-7')
PL[7] = cooling()
# ------------------------------------------------------------------ 8: revs at full throttle
def revs():
    x0, x1, y = 120, 1160, 330; X = lambda r: x0 + (x1 - x0) * r / 3600
    b = rect(x0, y - 40, x1 - x0, 80, 'var(--band)', INK, 4, 10)
    b += f'<rect x="{x0}" y="{y - 40}" width="{X(2700) - x0:.1f}" height="80" rx="10" fill="#3d4c59"/>'
    for r in range(0, 3601, 500): b += line(X(r), y + 44, X(r), y + 60, INK, 3) + txt(X(r), y + 90, str(r), 22, 700, MUTED)
    b += line(X(3200), y - 70, X(3200), y + 70, RED, 6) + pill(X(3200) + 20, y - 160, T('rated 3200', 'номинал 3200'), 'red')
    b += line(X(3100), y - 50, X(3100), y + 50, BLUE, 6, '10 6') + pill(X(3100) - 40, y + 140, T('aim 3100', 'цель 3100'), 'accent')
    b += pill(X(2700) - 80, y - 100, T('full throttle 2700', 'полный газ 2700'))
    b += arrow(X(2700), y + 200, X(3100), y + 200, BLUE, 6) + pill((X(2700) + X(3100)) / 2, y + 250, T('400 ÷ 200 ≈ 2 in less pitch', '400 ÷ 200 ≈ на 2 дюйма меньше шаг'), 'accent')
    b += pill(380, 180, T('black smoke: too much fuel for the air', 'чёрный дым: топлива больше, чем воздуха'), 'red')
    return frame(T('Propeller · overpropped', 'Винт · «тяжёлый»'),
                 [T('Rated revs never reached at full throttle: too much pitch', 'На полном газу не выходит на номинал: шаг слишком велик'),
                  T('Rated revs at part throttle: too little pitch', 'Номинал уже на частичном газу: шаг слишком мал')], b, 'yof-ves-8')
PL[8] = revs()
# ------------------------------------------------------------------ 9: the charge curve
def charge():
    x0, x1, yb, yt = 140, 1180, 560, 90
    b = line(x0, yb, x1, yb, INK, 4) + line(x0, yb, x0, yt, INK, 4)
    xa, xb = 470, 870
    b += f'<rect x="{x0}" y="{yt}" width="{xa - x0}" height="{yb - yt}" fill="rgba(0,118,190,.05)"/><rect x="{xa}" y="{yt}" width="{xb - xa}" height="{yb - yt}" fill="rgba(255,200,0,.12)"/>'
    b += txt((x0 + xa) / 2, yt + 34, T('BULK', 'BULK'), 28, 700, INK) + txt((xa + xb) / 2, yt + 34, T('ABSORPTION', 'ABSORPTION'), 28, 700, INK) + txt((xb + x1) / 2, yt + 34, T('FLOAT', 'FLOAT'), 28, 700, INK)
    b += path(f'M{x0} 330 C 300 260, 420 190, {xa} 170 L{xb} 170 L{xb + 30} 250 L{x1} 250', BLUE, 7)
    b += path(f'M{x0} 260 L{xa} 260 C 600 400, 760 480, {xb} 500 L{x1} 520', RED, 7, dash='16 10')
    b += txt(x1 - 10, 236, T('volts', 'вольты'), 26, 700, BLUE, 'end') + txt(x1 - 10, 506, T('amps', 'амперы'), 26, 700, RED, 'end')
    b += circle(650, 170, 13, YEL, INK, 4) + circle(650, 395, 13, YEL, INK, 4)
    b += pill(650, 225, T('14.4 V held', 'держит 14,4 В'), 'accent') + pill(760, 350, T('9 A, falling: normal', '9 А, падает: норма'))
    b += pill(300, 610, T('time', 'время'))
    return frame(T('Charging · bulk, absorption, float', 'Заряд · bulk, absorption, float'),
                 [T('Absorption holds the voltage while the current tapers: the bank is filling', 'Absorption держит напряжение, ток спадает: банк дозаряжается'),
                  T('An hour a day never finishes absorption: the bank sulphates', 'Час в день не завершает absorption: банк сульфатируется')], b, 'yof-ves-9')
PL[9] = charge()

for n, p in PL.items():
    with open(os.path.join(DIR, f'{n}-plan.json'), 'w') as f: json.dump(p, f, ensure_ascii=False)
with open(os.path.join(DIR, 'ru-plans.json'), 'w') as f: json.dump(RU, f, ensure_ascii=False, indent=1)
print('plans', sorted(PL), 'ru', len(RU))
