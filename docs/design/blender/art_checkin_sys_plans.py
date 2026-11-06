# The schematics of the Charter Check-in system figures (electrics, engine, plumbing, return): writes
# docs/design/figure-style/articles/charter-checkin/<article>/<n>-plan.json, read by article-figures.html.
# A plan is a figure-schematic.js spec ({sch: ...}) or, where no plan view fits (wiring, a tank budget, a valve),
# a drawn SVG in the same style: 1280 x 800, theme tokens, Carlito, the key along the bottom.
# SVG text is translated on the page by exact match through ru.json; pills here are sized for the longer of the
# English and the Russian (RU below), and RU is merged into each article's ru.json by --ru.
#   python3 docs/design/blender/art_checkin_sys_plans.py            write the plans
#   python3 docs/design/blender/art_checkin_sys_plans.py --ru       print {article: {English: Russian}} for the SVG text
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ARTS = os.path.join(HERE, '..', 'figure-style', 'articles', 'charter-checkin')
W, H = 1280, 800
RED, GREEN, YEL, BLUE = '#e0251b', '#1aa34a', '#e0b400', 'var(--accent)'

RU = {
    # electrics 1
    'Engine battery': 'Стартерная батарея', 'House bank': 'Бытовой банк', 'Starter': 'Стартер',
    'Lights, fridge, instruments': 'Свет, холодильник, приборы', 'ENGINE: on': 'ENGINE: вкл.', 'HOUSE: on': 'HOUSE: вкл.',
    'BOTH: off': 'BOTH: выкл.', 'Two banks, kept apart': 'Два банка, раздельно',
    'ENGINE feeds the starter; HOUSE runs everything else': 'ENGINE питает стартер, HOUSE — всё остальное',
    'BOTH joins them: only to start on a flat battery, then off': 'BOTH соединяет их: только пуск с севшим стартерным, потом выкл.',
    # electrics 3
    '200 Ah': '200 А·ч', 'usable: 100 Ah': 'полезных: 100 А·ч', 'keep: 100 Ah': 'не трогать: 100 А·ч',
    'fridge 50 Ah': 'холодильник 50 А·ч', 'a few Ah': 'несколько А·ч', 'left 45 Ah': 'осталось 45 А·ч',
    'One night at anchor · the house bank': 'Одна ночь на якоре · бытовой банк',
    '2 × 100 Ah = 200 Ah; half of a lead-acid bank is usable: 100 Ah': '2 × 100 А·ч = 200 А·ч; у свинцового банка полезна половина: 100 А·ч',
    'Fridge 5 A × 10 h = 50 Ah · morning: run the engine for an hour': 'Холодильник 5 А × 10 ч = 50 А·ч · утром час работы двигателя',
    # electrics 4
    'boat': 'яхта', 'pedestal': 'колонка', '230 V main off': 'главный 230 В выкл.', 'boat end': 'разъём яхты',
    'pedestal end': 'разъём колонки', 'pedestal switch': 'выключатель колонки', 'main and charger on': 'главный и зарядное вкл.',
    'Shore power · the cable goes live last': 'Береговое питание · кабель под током последним',
    'Connect: main off, boat end, pedestal end, pedestal switch, then main and charger': 'Подключение: главный выкл., яхта, колонка, выключатель колонки, затем главный и зарядное',
    'Leave: charger and main off, pedestal off, unplug the pedestal first, then the boat': 'Уход: зарядное и главный выкл., колонку выкл., сначала разъём колонки, потом яхты',
    # engine 5
    'tank 160 L': 'бак 160 л', '20 L': '20 л', 'to use: 140 L = 35 h': 'расход: 140 л = 35 ч', 'reserve 20 L': 'резерв 20 л',
    'plan: 36 h = 144 L': 'план: 36 ч = 144 л', 'fuel stop midweek': 'заправка в середине недели',
    'Fuel plan for the week': 'План топлива на неделю',
    'Tank 160 L, keep 20 L: 140 L ÷ 4 L/h = 35 h of motoring': 'Бак 160 л, резерв 20 л: 140 л ÷ 4 л/ч = 35 ч под мотором',
    'Plan 6 h a day × 6 days = 36 h = 144 L: more than you have': 'План 6 ч в день × 6 дней = 36 ч = 144 л: больше, чем есть',
    # plumbing 2
    'heads': 'гальюн', 'valve': 'кран', 'TANK': 'TANK', 'SEA': 'SEA', 'holding tank': 'танк сточных вод',
    'deck pump-out': 'откачка с палубы', 'vent': 'вент. штуцер', 'overboard': 'за борт', 'offshore only': 'только в море',
    'Heads and holding tank': 'Гальюн и танк сточных вод',
    'Harbours and bays: valve to TANK · discharge only offshore, where allowed': 'В гавани и бухте: кран на TANK · сброс только в море, где разрешено',
    'Waste at the hull vent: the tank is full · no-discharge waters: pump-out': 'Стоки из штуцера в борту: танк полон · сброс запрещён: откачка',
    # plumbing 3
    'open': 'открыт', 'closed': 'закрыт', 'lever along the pipe': 'рычаг вдоль трубы', 'lever across': 'рычаг поперёк',
    'hull': 'корпус', 'Seacock · a quarter turn': 'Кингстон · четверть оборота',
    'Lever along the pipe: open · across the pipe: closed': 'Рычаг вдоль трубы — открыт · поперёк — закрыт',
    'One that will not move is never forced: the base frees it': 'Заевший кингстон не ломают рычагом: его освобождает база',
    # plumbing 4
    'gas locker': 'газовый рундук', 'drain': 'дренаж', 'waterline': 'ватерлиния', 'gas sinks': 'газ опускается',
    'Gas is heavier than air · the locker drains overboard': 'Газ тяжелее воздуха · рундук дренируется за борт',
    'A leak runs down: the drain takes it over the side, above the waterline': 'Утечка стекает вниз: дренаж выводит её за борт, выше ватерлинии',
    'Drain clear, every bottle upright in the locker, the spare too': 'Дренаж чист, все баллоны стоят в рундуке, запасной тоже',
    # return 5
    'excess €500': 'франшиза €500', 'Mon: chip €350': 'пн: скол €350', 'Thu: pulpit €900': 'чт: релинг €900',
    'you pay €350': 'вы платите €350', 'you pay €500': 'вы платите €500',
    'Excess per incident · each repair capped': 'Франшиза на случай · каждый ремонт отдельно',
    'Two incidents: €350 + €500 = €850 from the deposit, not €1,250': 'Два случая: €350 + €500 = €850 из депозита, а не €1 250',
}

def esc(s): return str(s).replace('&', '&amp;').replace('<', '&lt;')
def txt(x, y, s, size=26, w=700, fill='var(--muted)', a='middle'):
    return f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{w}" fill="{fill}" text-anchor="{a}">{esc(s)}</text>'
def pill(x, y, text, kind='light', size=26, align='center'):
    n = max(len(text), len(RU.get(text, text)))
    w, h = n * size * 0.56 + size * 1.4, size * 1.7
    x = x + w / 2 if align == 'left' else x - w / 2 if align == 'right' else x
    fill = {'accent': BLUE, 'red': '#e8231a', 'green': GREEN}.get(kind, 'var(--bg)'); ink = 'var(--ink)' if kind == 'light' else '#fff'
    stroke = 'var(--tag-line)' if kind == 'light' else fill
    return f'<rect x="{x - w / 2:.1f}" y="{y - h / 2:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{h / 2:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="3"/>' + txt(x, y + size * 0.36, text, size, 700, ink)
def line(x1, y1, x2, y2, c='var(--ink)', w=5, dash=None):
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{c}" stroke-width="{w}" stroke-linecap="round"' + (f' stroke-dasharray="{dash}"' if dash else '') + '/>'
def path(d, c='var(--ink)', w=5, dash=None, fill='none'):
    return f'<path d="{d}" fill="{fill}" stroke="{c}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"' + (f' stroke-dasharray="{dash}"' if dash else '') + '/>'
def arrow(x1, y1, x2, y2, c='var(--ink)', w=5, h=18):
    import math
    a = math.atan2(y2 - y1, x2 - x1); p1 = (x2 - h * math.cos(a - .5), y2 - h * math.sin(a - .5)); p2 = (x2 - h * math.cos(a + .5), y2 - h * math.sin(a + .5))
    return line(x1, y1, x2, y2, c, w) + f'<path d="M{x2} {y2} L{p1[0]:.1f} {p1[1]:.1f} L{p2[0]:.1f} {p2[1]:.1f} Z" fill="{c}"/>'
def rect(x, y, w, h, fill='var(--bg)', stroke='var(--ink)', sw=4, rx=10):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
def circle(x, y, r, fill='var(--bg)', stroke='var(--ink)', sw=4):
    return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
def svg(body, title, key):
    keyH = 40 + 40 * len(key) + 24
    s = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="Carlito, Arial, sans-serif" style="background:var(--bg)"><rect width="{W}" height="{H}" fill="var(--bg)"/>'
    s += body + f'<rect x="0" y="{H - keyH}" width="{W}" height="{keyH}" fill="var(--band)"/>' + txt(30, H - keyH + 40, title, 30, 700, 'var(--ink)', 'start')
    for i, k in enumerate(key): s += txt(30, H - keyH + 80 + 40 * i, '·', 27, 400, 'var(--ink)', 'start') + txt(44, H - keyH + 80 + 40 * i, k, 27, 400, 'var(--ink)', 'start')   # the bullet apart: ru.json matches the line
    return s + '</svg>'

def battery(x, y, w=150, h=96):
    return rect(x - w / 2, y - h / 2, w, h, '#2b2e33', 'var(--ink)', 4, 8) + rect(x - w / 2 + 16, y - h / 2 - 14, 26, 14, RED, 'none', 0, 3) + rect(x + w / 2 - 42, y - h / 2 - 14, 26, 14, '#111', 'none', 0, 3)
def iso(x, y, on):
    k = f'<g transform="translate({x} {y}) rotate({0 if on else 90})"><rect x="-9" y="-34" width="18" height="68" rx="8" fill="#fff"/></g>'
    return circle(x, y, 44, '#c4161c', 'var(--ink)', 4) + k

# ------------------------------------------------------------------------------------------------ electrics
def electrics():
    P = {}
    b = ''
    # positives in red: battery -> switch -> load; BOTH dashed between the two battery positives
    b += line(250, 470, 250, 300, RED, 7) + line(250, 210, 250, 120, RED, 7) + line(950, 470, 950, 300, RED, 7) + line(950, 210, 950, 120, RED, 7)
    b += path('M300 470 L600 470 L600 300', RED, 6, '14 10') + path('M600 300 L600 470 M600 470 L870 470', RED, 6, '14 10')
    b += battery(250, 520) + battery(900, 520) + battery(1040, 520)
    b += rect(140, 60, 220, 64, 'var(--band)', 'var(--ink)', 3) + txt(250, 101, 'Starter', 26, 700, 'var(--ink)')
    b += rect(760, 60, 380, 64, 'var(--band)', 'var(--ink)', 3) + txt(950, 101, 'Lights, fridge, instruments', 26, 700, 'var(--ink)')
    b += iso(250, 255, True) + iso(950, 255, True) + iso(600, 255, False)
    b += pill(400, 255, 'ENGINE: on') + pill(1110, 255, 'HOUSE: on') + pill(600, 345, 'BOTH: off', 'red')
    b += txt(250, 610, 'Engine battery', 26, 700, 'var(--ink)') + txt(970, 610, 'House bank', 26, 700, 'var(--ink)')
    P[1] = {'noScale': True, 'svg': svg(b, 'Two banks, kept apart', ['ENGINE feeds the starter; HOUSE runs everything else', 'BOTH joins them: only to start on a flat battery, then off'])}
    # 3: the house bank's budget for one night
    x0, x1, y0, hh = 100, 1180, 250, 170; X = lambda ah: x0 + (x1 - x0) * ah / 200
    b = rect(x0, y0, x1 - x0, hh, 'var(--band)', 'var(--ink)', 4, 12)
    b += f'<rect x="{X(100)}" y="{y0}" width="{X(200) - X(100)}" height="{hh}" fill="var(--line)"/>'
    b += f'<rect x="{X(0)}" y="{y0}" width="{X(50) - X(0)}" height="{hh}" fill="{RED}" opacity=".85"/>' + f'<rect x="{X(50)}" y="{y0}" width="{X(55) - X(50)}" height="{hh}" fill="{YEL}"/>'
    b += rect(x0, y0, x1 - x0, hh, 'none', 'var(--ink)', 4, 12) + line(X(100), y0 - 30, X(100), y0 + hh + 30, 'var(--ink)', 5, '10 8')
    b += txt(X(25), y0 + hh / 2 + 10, 'fridge 50 Ah', 28, 700, '#fff') + txt(X(77), y0 + hh / 2 + 10, 'left 45 Ah', 28, 700, 'var(--ink)') + txt(X(150), y0 + hh / 2 + 10, 'keep: 100 Ah', 28, 700, 'var(--muted)')
    b += pill(X(52.5), y0 + hh + 56, 'a few Ah', 'light', 24) + line(X(52.5), y0 + hh, X(52.5), y0 + hh + 36, 'var(--ink)', 3)
    b += pill(X(50), y0 - 60, 'usable: 100 Ah', 'accent', 28) + txt(X(200), y0 - 50, '200 Ah', 28, 700, 'var(--ink)', 'end')
    P[3] = {'noScale': True, 'svg': svg(b, 'One night at anchor · the house bank', ['2 × 100 Ah = 200 Ah; half of a lead-acid bank is usable: 100 Ah', 'Fridge 5 A × 10 h = 50 Ah · morning: run the engine for an hour'])}
    # 4: the shore-power sequence
    b = rect(70, 110, 390, 380, 'var(--band)', 'var(--ink)', 4, 30) + txt(265, 470, 'boat', 32, 700, 'var(--ink)')
    b += rect(960, 150, 160, 340, 'var(--band)', 'var(--ink)', 4, 14) + txt(1040, 530, 'pedestal', 28, 700, 'var(--ink)')
    b += path('M460 390 C 600 560, 820 560, 960 390', YEL, 12)
    steps = [(120, 170, '0', '230 V main off', 'red', (160, 170, 'left')), (460, 390, '1', 'boat end', 'accent', (460, 320, 'center')),
             (960, 390, '2', 'pedestal end', 'accent', (960, 320, 'center')), (1040, 210, '3', 'pedestal switch', 'accent', (1000, 210, 'right')),
             (120, 250, '4', 'main and charger on', 'accent', (160, 250, 'left'))]
    for x, y, n, t, k, (lx, ly, al) in steps:
        b += pill(lx, ly, t, 'red' if k == 'red' else 'light', 26, al) + circle(x, y, 26, RED if k == 'red' else BLUE, 'var(--bg)', 4) + txt(x, y + 10, n, 28, 700, '#fff')
    P[4] = {'noScale': True, 'svg': svg(b, 'Shore power · the cable goes live last', ['Connect: main off, boat end, pedestal end, pedestal switch, then main and charger', 'Leave: charger and main off, pedestal off, unplug the pedestal first, then the boat'])}
    # 5, 6: the lights in plan view
    P[5] = {'noScale': True, 'sch': {'padPx': 90, 'night': True, 'title': 'Navigation lights under power', 'key': ['Masthead light: white over 225° ahead · sidelights: green starboard, red port', 'Sternlight: white over 135° astern'],
            'boats': [{'you': True, 'x': 0, 'z': 0, 'hdg': 0, 'power': True, 'noHeading': True, 'scale': 4.2, 'label': 'Under power'}],
            'texts': [{'x': 0, 'z': -230, 'text': 'masthead: white 225°', 'kind': 'light'}, {'x': 230, 'z': -60, 'text': 'green 112.5°', 'kind': 'light'},
                      {'x': -230, 'z': -60, 'text': 'red 112.5°', 'kind': 'light'}, {'x': 0, 'z': 240, 'text': 'sternlight: white 135°', 'kind': 'light'}],
            'fit': [{'x': -330, 'z': -280}, {'x': 330, 'z': 280}]}}
    P[6] = {'noScale': True, 'sch': {'padPx': 90, 'night': True, 'title': 'At anchor · one all-round white light', 'key': ['Seen alike from every side, at the masthead', 'Overnight on: anchor light, bilge pump, gas alarm'],
            'boats': [{'you': True, 'x': 0, 'z': 0, 'hdg': 30, 'anchorLight': True, 'noHeading': True, 'scale': 4.2, 'label': 'At anchor'}],
            'anchors': [{'x': 170, 'z': -250, 's': 1.2}], 'paths': [{'pts': [[45, -75], [110, -170], [160, -215]], 'c': 'ink', 'w': 4, 'dash': '10 8'}],
            'texts': [{'x': -150, 'z': -200, 'text': 'all-round white: 360°', 'kind': 'light'}],
            'fit': [{'x': -300, 'z': -280}, {'x': 300, 'z': 260}]}}
    return P

# ------------------------------------------------------------------------------------------------ engine
def engine():
    x0, x1, y0, hh = 100, 1180, 250, 110; X = lambda l: x0 + (x1 - x0) * l / 160
    b = f'<rect x="{X(0)}" y="{y0}" width="{X(140) - X(0)}" height="{hh}" fill="{BLUE}" opacity=".85"/>' + f'<rect x="{X(140)}" y="{y0}" width="{X(160) - X(140)}" height="{hh}" fill="{RED}" opacity=".85"/>'
    b += rect(x0, y0, x1 - x0, hh, 'none', 'var(--ink)', 4, 10)
    b += txt(X(70), y0 + hh / 2 + 10, 'to use: 140 L = 35 h', 30, 700, '#fff') + txt(X(150), y0 + hh / 2 + 10, '20 L', 26, 700, '#fff')
    b += txt(X(0), y0 - 24, 'tank 160 L', 28, 700, 'var(--ink)', 'start') + pill(X(150), y0 - 40, 'reserve 20 L', 'red', 24)
    yp = y0 + hh + 70
    b += path(f'M{X(0)} {yp} L{X(144)} {yp}', YEL, 14) + line(X(144), yp - 26, X(144), yp + 26, 'var(--ink)', 4)
    b += pill(X(60), yp + 60, 'plan: 36 h = 144 L', 'light', 28) + pill(X(144) + 20, yp + 60, 'fuel stop midweek', 'accent', 26, 'right')
    return {5: {'noScale': True, 'svg': svg(b, 'Fuel plan for the week', ['Tank 160 L, keep 20 L: 140 L ÷ 4 L/h = 35 h of motoring', 'Plan 6 h a day × 6 days = 36 h = 144 L: more than you have'])}}

# ------------------------------------------------------------------------------------------------ plumbing
def plumbing():
    P = {}
    # 2: heads -> Y-valve -> tank or overboard
    pipe = '#8a6a3a'
    b = rect(90, 150, 190, 170, 'var(--band)', 'var(--ink)', 4, 30) + txt(185, 245, 'heads', 30, 700, 'var(--ink)')
    b += path('M280 235 L470 235', pipe, 12) + circle(510, 235, 40, 'var(--bg)', 'var(--ink)', 5) + txt(510, 300, 'valve', 24)
    b += f'<g transform="translate(510 235) rotate(-45)"><rect x="-7" y="-46" width="14" height="46" rx="6" fill="{BLUE}"/></g>'
    b += path('M540 205 L700 120 L780 120', pipe, 12) + path('M540 265 L700 360 L700 470', pipe, 12, '16 10')
    b += rect(780, 70, 300, 200, 'var(--band)', 'var(--ink)', 4, 16) + txt(930, 180, 'holding tank', 30, 700, 'var(--ink)')
    b += pill(620, 120, 'TANK', 'accent', 26) + pill(610, 350, 'SEA', 'light', 26)
    b += path('M1080 110 L1180 110 L1180 60', pipe, 6) + txt(1180, 46, 'vent', 22)
    b += path('M930 70 L930 30', pipe, 10) + pill(930, 28, 'deck pump-out', 'light', 22)
    b += path('M930 270 L930 470', pipe, 12, '16 10') + pill(1080, 410, 'offshore only', 'red', 24)
    b += line(560, 500, 1150, 500, '#3c8cbe', 5) + txt(700, 545, 'overboard', 24) + txt(930, 545, 'overboard', 24)
    P[2] = {'noScale': True, 'svg': svg(b, 'Heads and holding tank', ['Harbours and bays: valve to TANK · discharge only offshore, where allowed', 'Waste at the hull vent: the tank is full · no-discharge waters: pump-out'])}
    # 3: a ball-valve seacock, open and closed
    def cock(cx, open_):
        s = rect(cx - 160, 470, 320, 26, '#d8c9a3', '#6b5a3a', 4, 4) + txt(cx + 120, 530, 'hull', 22)
        s += rect(cx - 30, 330, 60, 140, '#a7773f', 'var(--ink)', 4, 8) + circle(cx, 400, 52, '#a7773f', 'var(--ink)', 4)
        s += rect(cx - 24, 120, 48, 210, '#2a2b2d', 'var(--ink)', 3, 8)                       # the hose up from it
        for yy in (250, 290): s += rect(cx - 32, yy, 64, 14, '#c8ccd0', 'var(--ink)', 2, 4)
        lev = f'<rect x="{cx + 40}" y="290" width="22" height="150" rx="9" fill="{RED}" stroke="var(--ink)" stroke-width="3"/>' if open_ else \
              f'<rect x="{cx + 40}" y="390" width="150" height="22" rx="9" fill="{RED}" stroke="var(--ink)" stroke-width="3"/>'
        s += lev + circle(cx + 51, 400, 10, 'var(--ink)', 'none', 0)
        s += pill(cx, 70, 'open' if open_ else 'closed', 'green' if open_ else 'red', 30)
        s += txt(cx, 580, 'lever along the pipe' if open_ else 'lever across', 26, 700, 'var(--ink)')
        return s
    P[3] = {'noScale': True, 'svg': svg(cock(360, True) + cock(900, False), 'Seacock · a quarter turn', ['Lever along the pipe: open · across the pipe: closed', 'One that will not move is never forced: the base frees it'])}
    # 4: the gas locker drains overboard
    b = path('M120 140 L120 470 Q 120 560 300 600 L1160 600', 'var(--ink)', 6)            # the hull section, the waterline
    b += line(80, 560, 1200, 560, '#3c8cbe', 5) + txt(1150, 590, 'waterline', 22, 700, '#3c8cbe', 'end')
    b += rect(300, 150, 420, 300, 'var(--band)', 'var(--ink)', 4, 10) + txt(510, 140, 'gas locker', 28, 700, 'var(--ink)')
    for x in (400, 600):
        b += rect(x - 55, 250, 110, 190, '#c94c1e', 'var(--ink)', 3, 30) + rect(x - 18, 225, 36, 28, '#8a8d91', 'var(--ink)', 2, 4)
    b += path('M520 450 L520 490 L120 490', 'var(--ink)', 8) + circle(120, 490, 9, 'var(--ink)', 'none', 0) + pill(330, 525, 'drain', 'accent', 24)
    for i, x in enumerate((470, 520, 570)): b += arrow(x, 330 + i * 8, x, 420 + i * 8, RED, 4, 14)
    b += pill(860, 380, 'gas sinks', 'red', 26) + arrow(760, 380, 690, 380, RED, 4)
    P[4] = {'noScale': True, 'svg': svg(b, 'Gas is heavier than air · the locker drains overboard', ['A leak runs down: the drain takes it over the side, above the waterline', 'Drain clear, every bottle upright in the locker, the spare too'])}
    return P

# ------------------------------------------------------------------------------------------------ return
def ret():
    P = {}
    # 3: the bay figure as a plan: the fuel dock A, then the berth B (bay units x 0.6 = metres from the centre, as in the render)
    c = lambda x, y: [round((x - 160) * 0.6, 1), round((y - 100) * 0.6, 1)]
    land = [[c(0, 0), c(320, 0), c(320, 40), c(0, 40)], [c(0, 40), c(70, 40), c(70, 66), c(0, 66)], [c(140, 40), c(150, 40), c(150, 140), c(140, 140)], [c(290, 40), c(320, 40), c(320, 180), c(290, 180)]]
    A, B = c(62, 90), c(180, 100)
    P[3] = {'sch': {'padPx': 50, 'title': 'Back at the base · fuel first', 'key': ['A first: fill up at the fuel dock and keep the receipt', 'Then B, your berth, before the time in the contract'],
            'land': land, 'spots': [{'x': A[0], 'z': A[1], 'label': 'A'}, {'x': B[0], 'z': B[1], 'label': 'B'}],
            'boats': [{'you': True, 'x': c(110, 175)[0], 'z': c(110, 175)[1], 'hdg': 300, 'noHeading': True}],
            'paths': [{'pts': [c(110, 165), c(90, 120), A], 'c': 'course', 'w': 5, 'dash': '14 10', 'arrow': True}, {'pts': [c(72, 96), c(120, 150), c(170, 150), B], 'c': 'course', 'w': 5, 'dash': '14 10', 'arrow': True}],
            'texts': [{'x': c(64, 114)[0], 'z': c(64, 114)[1], 'text': 'fuel dock', 'kind': 'accent'}, {'x': c(215, 122)[0], 'z': c(215, 122)[1], 'text': 'your berth tonight'}],
            'fit': [c(0, 0), c(320, 200)]}}
    P[3]['sch']['fit'] = [{'x': p[0], 'z': p[1]} for p in P[3]['sch']['fit']]
    # 5: two incidents, each capped at the excess
    x0, base, k = 220, 470, 0.33
    b = line(120, base, 1180, base, 'var(--ink)', 4)
    b += line(120, base - 500 * k, 1180, base - 500 * k, RED, 5, '14 10') + pill(1060, base - 500 * k - 34, 'excess €500', 'red', 24)
    for i, (rep, pay, lab, pl) in enumerate(((350, 350, 'Mon: chip €350', 'you pay €350'), (900, 500, 'Thu: pulpit €900', 'you pay €500'))):
        x = 330 + i * 420
        b += f'<rect x="{x - 90}" y="{base - rep * k}" width="180" height="{rep * k}" fill="var(--line)" stroke="var(--ink)" stroke-width="3"/>'
        b += f'<rect x="{x - 90}" y="{base - pay * k}" width="180" height="{pay * k}" fill="{BLUE}" opacity=".85"/>'
        b += txt(x, base + 40, lab, 26, 700, 'var(--ink)') + pill(x + 210, base - pay * k / 2, pl, 'accent', 24)
    P[5] = {'noScale': True, 'svg': svg(b, 'Excess per incident · each repair capped', ['Two incidents: €350 + €500 = €850 from the deposit, not €1,250'])}
    return P

if __name__ == '__main__':
    if '--ru' in sys.argv: print(json.dumps(RU, ensure_ascii=False, indent=1)); sys.exit()
    for art, P in (('electrics', electrics()), ('engine', engine()), ('plumbing', plumbing()), ('return', ret())):
        for n, spec in P.items():
            p = os.path.join(ARTS, art, f'{n}-plan.json'); json.dump(spec, open(p, 'w'), ensure_ascii=False); print(p)
