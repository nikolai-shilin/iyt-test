# The answer plans for the "lights" test questions, and the Russian of every English string in each question's
# 3d.labels.json and plan.json: writes figure-style/questions/<level>/<id>/plan.json and ru.json (level by id prefix).
# The plans are schematic() specs (figure-schematic.js) or an SVG of our own for a side view; shown after the
# answer, so they name the vessel and carry the reasoning, in agreement with the question's answer and why.
#   python3 docs/design/blender/q_lights_plans.py [ids...]
import json, math, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
QDIR = os.path.join(HERE, '..', 'figure-style', 'questions', 'bareboat-skipper')
LEVELS = {'bs': 'bareboat-skipper', 'ci': 'charter-checkin', 'yof': 'yachtmaster-offshore'}   # the level of a question, by its id's prefix
def qdir(qid): return os.path.join(HERE, '..', 'figure-style', 'questions', LEVELS.get(qid.split('-')[0], 'bareboat-skipper'))
LIST = {e['id']: e for lv in LEVELS.values() for e in json.load(open(os.path.join(HERE, '..', 'figure-style', 'questions', lv, 'lights.json')))}

RU = {}
def T(en, ru):
    """An English string of the plan, with its Russian."""
    RU[en] = ru; return en

# Russian for strings that recur
for en, ru in {
    'Power': 'Механическое', 'Other': 'Судно', 'Ship': 'Судно', 'Sail': 'Парусное', 'Yacht': 'Яхта', 'Tug': 'Буксировщик', 'Tow': 'Буксируемое',
    'under sail': 'под парусом', 'motoring': 'под мотором', 'bearing steady': 'пеленг не меняется',
}.items(): T(en, ru)

def at(rel, d):
    a = math.radians(rel); return dict(x=round(d * math.sin(a), 1), z=round(-d * math.cos(a), 1))

def you(hdg=0, **o):
    b = dict(you=True, x=0, z=0, hdg=hdg, noHeading=True); b.update(o); return b

def other(rel, d, hdg, label, **o):
    b = dict(at(rel, d), hdg=hdg, label=label, bearing=False, noHeading=True, labelAbove=True); b.update(o); return b

def turn(pts, c='course'): return dict(pts=pts, c=c, dash='16 12', arrow=True)
def line(a, b, c='red', w=4, dash='10 10'): return dict(pts=[a, b], c=c, w=w, dash=dash)
def txt(x, z, text, kind='light', **o): d = dict(x=x, z=z, text=text, kind=kind); d.update(o); return d

def sch(title, key, boats=(), night=True, pad=80, **o):
    s = dict(night=night, padPx=pad, title=title, key=list(key), boats=list(boats)); s.update(o)
    return dict(sch=s)

# ---------- side views drawn as SVG, in the schematic's style ----------
SCOL = {'r': '#e0251b', 'g': '#1aa34a', 'w': '#ffffff', 'y': '#ffa800'}

def esc(s): return str(s).replace('&', '&amp;').replace('<', '&lt;')

def stxt(x, y, s, size=26, w=700, fill='var(--muted)', a='middle'):
    return f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{w}" fill="{fill}" text-anchor="{a}">{esc(s)}</text>'

def pill(x, y, text, kind='light', size=24):
    w = len(text) * size * 0.58 + size * 1.4; h = size * 1.7
    fill = {'accent': 'var(--accent)', 'red': '#e8231a'}.get(kind, 'var(--bg)'); ink = 'var(--ink)' if kind == 'light' else '#fff'
    stroke = 'var(--tag-line)' if kind == 'light' else fill
    return (f'<rect x="{x - w / 2:.1f}" y="{y - h / 2:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{h / 2:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="3"/>'
            + stxt(x, round(y + size * 0.36, 1), text, size, 700, ink))

def glow(x, y, c, r=15):
    stroke = '#9aa4ae' if c == 'w' else 'none'
    return f'<circle cx="{x}" cy="{y}" r="{r * 2}" fill="{SCOL[c]}" opacity=".22"/><circle cx="{x}" cy="{y}" r="{r}" fill="{SCOL[c]}" stroke="{stroke}" stroke-width="2"/>'

def frame(title, key, body):
    W, H = 1280, 800; keyH = 40 + 40 * len(key) + 24
    s = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="Carlito, Arial, sans-serif" style="background:var(--bg)"><rect width="{W}" height="{H}" fill="var(--bg)"/>'
    s += body
    s += f'<rect x="0" y="{H - keyH}" width="{W}" height="{keyH}" fill="var(--band)"/>'
    ky = H - keyH + 40; s += stxt(30, ky, title, 30, 700, 'var(--ink)', 'start')
    for k in key:
        ky += 40; s += f'<text x="30" y="{ky}" font-size="27" font-weight="400" fill="var(--ink)" text-anchor="start"><tspan>· </tspan><tspan>{esc(k)}</tspan></text>'
    return s + '</svg>'

def svg_tricolour():
    """bs-060: one yacht under sail (tricolour at the masthead), the same yacht motoring (steaming light, deck-level
    sidelights and sternlight)."""
    def yacht(cx, sails):
        b = f'<path d="M{cx - 200} 455 L{cx + 210} 455 L{cx + 170} 500 L{cx - 180} 500 Z" fill="var(--ink)"/>'
        b += f'<line x1="{cx}" y1="455" x2="{cx}" y2="110" stroke="var(--ink)" stroke-width="7"/>'
        if sails: b += f'<path d="M{cx - 6} 118 L{cx - 6} 440 L{cx - 170} 440 Z" fill="none" stroke="var(--ink)" stroke-width="4"/><path d="M{cx + 8} 135 L{cx + 200} 448 L{cx + 8} 448 Z" fill="none" stroke="var(--ink)" stroke-width="4"/>'
        return b
    L, R = 330, 950
    body = yacht(L, True) + glow(L, 100, 'w', 13) + glow(L - 22, 104, 'r', 9) + glow(L + 22, 104, 'g', 9)
    body += pill(L + 175, 92, T('tricolour', 'трёхцветный'))
    body += pill(L, 560, T('Under sail: tricolour only', 'Под парусом: только трёхцветный'), 'accent', 26)
    body += yacht(R, False) + glow(R, 250, 'w', 13) + pill(R + 160, 240, T('steaming light', 'топовый'))
    body += glow(R + 195, 448, 'r', 11) + glow(R + 220, 448, 'g', 11) + glow(R - 196, 444, 'w', 11)
    body += pill(R + 120, 395, T('sidelights', 'бортовые')) + pill(R - 160, 395, T('sternlight', 'кормовой'))
    body += pill(R, 560, T('Engine on: tricolour off', 'Мотор включён: трёхцветный выключить'), 'red', 26)
    body += f'<line x1="640" y1="60" x2="640" y2="600" stroke="var(--line)" stroke-width="3"/>'
    return frame(T('Lights · from sail to engine', 'Огни · с паруса на мотор'),
                 [T('Under sail a yacht under 20 m may show one tricolour at the masthead', 'Под парусом яхта короче 20 м может нести один трёхцветный на топе'),
                  T('With the engine on: steaming light, deck-level sidelights and sternlight', 'С мотором: топовый, бортовые на уровне палубы и кормовой')], body)

def svg_anchor_ship():
    """bs-610: a ship at anchor in profile, bow to the left: the forward anchor light higher than the after one."""
    body = '<line x1="40" y1="470" x2="1240" y2="470" stroke="#3c8cbe" stroke-width="4"/>'
    body += '<path d="M170 400 L1080 400 L1060 470 L230 492 L150 420 Z" fill="var(--ink)"/>'   # hull, bow left (raked stem)
    body += '<rect x="900" y="330" width="140" height="70" fill="var(--ink)"/><line x1="230" y1="400" x2="230" y2="250" stroke="var(--ink)" stroke-width="6"/>'
    body += '<line x1="1000" y1="330" x2="1000" y2="300" stroke="var(--ink)" stroke-width="6"/>'
    body += glow(230, 240, 'w', 15) + glow(1000, 290, 'w', 15)
    for x in (380, 500, 620, 740, 860): body += glow(x, 388, 'w', 7)
    body += pill(230, 180, T('forward anchor light: higher', 'носовой якорный: выше'), 'accent')
    body += pill(1000, 230, T('after anchor light: lower', 'кормовой якорный: ниже'))
    body += pill(620, 340, T('deck lights', 'палубное освещение'))
    body += pill(170, 530, T('bow', 'нос'), 'accent', 26) + pill(1080, 530, T('stern', 'корма'), 'light', 26)
    body += f'<path d="M150 440 C 110 470 90 520 70 560" stroke="#4a4f55" stroke-width="5" fill="none" stroke-dasharray="10 6"/>'
    return frame(T('Lights · a ship at anchor, bow to the left', 'Огни · судно на якоре, носом влево'),
                 [T('At anchor the forward light is the higher one (Rule 30)', 'На якоре носовой огонь выше кормового (правило 30)'),
                  T('Under way it is the other way round: the forward masthead light is lower', 'На ходу наоборот: передний топовый ниже заднего')], body)

# ---------- marks ----------
def cardinal(kind, d, title, key):
    """A cardinal mark on the `d` side of a shoal, you passing on that side."""
    v = {'n': (0, -1), 'e': (1, 0), 's': (0, 1), 'w': (-1, 0)}[d]; t = (-v[1], v[0]) if d in 'ns' else (v[1], -v[0])
    if d in 'ns': t = (1, 0)
    else: t = (0, 1)
    m = (v[0] * 80, v[1] * 80); c = (v[0] * 150, v[1] * 150)
    a = (c[0] - t[0] * 200, c[1] - t[1] * 200); b = (c[0] + t[0] * 200, c[1] + t[1] * 200)
    hdg = (math.degrees(math.atan2(t[0], -t[1])) + 360) % 360
    shoal = [[-70, -50], [10, -75], [70, -30], [55, 45], [-20, 70], [-75, 30]]
    side = {'n': 'north', 'e': 'east', 's': 'south', 'w': 'west'}[d]
    side_ru = {'n': 'с севера', 'e': 'с востока', 's': 'с юга', 'w': 'с запада'}[d]
    return sch(title, key, night=False, pad=60, boats=[you(hdg, x=a[0], z=a[1])],
               zones=[dict(pts=shoal, c='red', fill='rgba(224,37,27,.08)')], rocks=[dict(x=0, z=0)],
               marks=[dict(x=m[0], z=m[1], kind=kind, bearing=False, hi=True)],
               paths=[turn([[a[0] + t[0] * 40, a[1] + t[1] * 40], list(b)])],
               texts=[txt(c[0] + v[0] * 60 + t[0] * 110, c[1] + v[1] * 60 + t[1] * 110, T(f'pass {side}', f'обходить {side_ru}'), 'accent'),
                      txt(-v[0] * 90, -v[1] * 90, T('shoal', 'мель'), 'red')],
               fit=[dict(x=-240, z=-240), dict(x=240, z=240)])

def channel(kind, mark_at, title, key, path=None, texts=(), extra_marks=()):
    """Coming in from sea (south) up a channel: the mark in question highlighted."""
    p = path or [[0, 210], [0, -230]]
    return sch(title, key, night=False, pad=60, boats=[you(0, x=p[0][0], z=p[0][1] + 40)],
               marks=[dict(x=mark_at[0], z=mark_at[1], kind=kind, bearing=False, hi=True)] + list(extra_marks),
               paths=[turn(p)], texts=[txt(-210, 230, T('from seaward', 'с моря'), 'light')] + list(texts),
               fit=[dict(x=-260, z=-260), dict(x=260, z=280)])

def rhythm(title, key, rows, T_=15, tick=5): return dict(rhythm=dict(T=T_, tick=tick, title=title, key=key, rows=rows))

# ---------- the plans ----------
P = {}
k = T   # short alias for key lines

P['bs-040'] = sch(T('Lights · crossing, she is on your starboard side', 'Огни · пересечение курсов, оно справа от вас'),
    [k('Masthead light over red: power-driven, her port side to you', 'Топовый над красным: судно с механическим двигателем, левым бортом к вам'),
     k('She has you on her port side: you give way, turn to starboard and pass astern', 'Вы у неё слева: уступаете вы — отворот вправо, пройти за кормой')],
    [you(power=True), other(45, 320, 305, 'Power', power=True)],
    paths=[line([0, 0], [208, -208]), turn([[20, -40], [80, -90], [200, -110]])],
    texts=[txt(30, -220, T('bearing 045° steady', 'КУ 045° не меняется'), 'red'), txt(-150, -40, T('you give way', 'вы уступаете'), 'red')],
    fit=[dict(x=-200, z=100), dict(x=320, z=-330)])

P['bs-053'] = cardinal('card-s', 's', T('South cardinal · pass to the south', 'Южный кардинальный · обходить с юга'),
    [k('Q(6)+LFl 15s: six quick flashes and a long one, like six o’clock', 'Q(6)+LFl 15s: шесть частых и длительный, как 6 часов'),
     k('A south cardinal: the safe water is to the south of it', 'Южный кардинальный знак: безопасная вода к югу от него')])

P['bs-057'] = sch(T('Lights · sailing vessel, bow on', 'Огни · парусное судно, носом к вам'),
    [k('Red over green at the masthead, sidelights below, no white: sailing', 'Красный над зелёным на топе, ниже бортовые, белого нет: парусное'),
     k('The red over green is optional; never shown with a tricolour', 'Красный над зелёным — по желанию; вместе с трёхцветным не несут')],
    [you(), other(0, 260, 180, 'Sail', stack=['r', 'g'], stackDx=-150)], fit=[dict(x=-200, z=-380), dict(x=200, z=110)])

P['bs-058'] = sch(T('Lights · one steady white light, low', 'Огни · один постоянный белый, низко'),
    [k('A sternlight seen from astern, or the anchor light of a vessel at anchor', 'Кормовой огонь, видимый с кормы, или якорный огонь судна на якоре'),
     k('Only the bearing tells you which: take bearings and watch them', 'Различить можно только по пеленгу: берите пеленги и следите')],
    [you(), other(-30, 320, 345, T('Under way, from astern', 'На ходу, вид с кормы')), other(30, 320, 200, T('At anchor', 'На якоре'), anchorLight=True)],
    fit=[dict(x=-330, z=-470), dict(x=330, z=100)])

P['bs-059'] = sch(T('Lights · trawler, bow on', 'Огни · траулер, носом к вам'),
    [k('Green over white all round: trawling; sidelights: making way', 'Зелёный над белым, круговые: траление; бортовые — имеет ход'),
     k('Fishing has right of way over sail and power: you keep clear', 'Занятое ловом имеет преимущество перед парусным и механическим: уступаете вы')],
    [you(), other(0, 280, 180, T('Trawler', 'Траулер'), stack=['g', 'w'], stackDx=-150)],
    paths=[turn([[20, -40], [90, -120], [150, -260]])], texts=[txt(220, -150, T('keep clear', 'уступить'), 'red')],
    fit=[dict(x=-220, z=-400), dict(x=260, z=110)])

P['bs-060'] = dict(svg=svg_tricolour())

P['bs-364'] = sch(T('On watch · a ship on a steady bearing', 'На вахте · судно на постоянном пеленге'),
    [k('Two masthead lights and red: a big ship, her port side to you', 'Два топовых и красный: крупное судно, левым бортом к вам'),
     k('Steady bearing, closing: risk of collision — wake the skipper now', 'Пеленг не меняется, дистанция сокращается: опасность столкновения — будите шкипера')],
    [you(power=True), other(40, 520, 245, T('Ship over 50 m', 'Судно длиннее 50 м'), power=True, scale=3.4)],
    paths=[line([0, 0], [334, -398])], texts=[txt(80, -260, T('bearing steady', 'пеленг не меняется'), 'red')],
    fit=[dict(x=-200, z=100), dict(x=500, z=-560)])

P['bs-373'] = sch(T('Safe speed · a harbour against the town lights', 'Безопасная скорость · гавань на фоне огней города'),
    [k('Shore lights behind the entrance hide the lights of other vessels', 'Огни берега за входом скрывают огни других судов'),
     k('Rule 6: background light is a factor in a safe speed — slow down', 'Правило 6: фоновое освещение — фактор безопасной скорости; сбавьте ход')],
    [you(0, x=0, z=260), other(0, 0, 160, T('a vessel coming out', 'выходящее судно'), x=120, z=-90, power=True, labelAbove=False)],
    night=True, pad=50, land=[[[-500, -420], [500, -420], [500, -260], [70, -260], [70, -220], [-70, -220], [-70, -260], [-500, -260]]],
    texts=[txt(0, -350, T('TOWN LIGHTS', 'ОГНИ ГОРОДА'), pill=False, size=30), txt(-210, 60, T('slow down', 'сбавить ход'), 'red')],
    circles=[dict(x=-70, z=-225, r=12, fill='#e0251b', c='ink', dash='0'), dict(x=70, z=-225, r=12, fill='#1aa34a', c='ink', dash='0')],
    paths=[dict(pts=[[0, 225], [0, 40]], c='course', dash='6 12', w=5, arrow=True)], fit=[dict(x=-500, z=-420), dict(x=500, z=330)])

P['bs-412'] = sch(T('Lights · overtaking', 'Огни · обгон'),
    [k('Only her white sternlight: you are coming up from astern', 'Виден только её белый кормовой: вы подходите с кормы'),
     k('You are overtaking: keep clear of her until past and clear (Rule 13)', 'Вы обгоняете: держитесь в стороне, пока не пройдёте и не отойдёте (правило 13)')],
    [you(power=True), other(1, 260, 0, 'Other')], paths=[turn([[10, -40], [80, -140], [95, -330]])],
    texts=[txt(200, -150, T('pass clear', 'обойти'), 'accent')], fit=[dict(x=-200, z=-400), dict(x=260, z=100)])

P['bs-415'] = sch(T('Lights · a ship coming up astern', 'Огни · судно догоняет вас с кормы'),
    [k('Masthead lights in line and both sidelights: a ship heading straight at your stern', 'Топовые в створе и оба бортовых: судно идёт прямо на вашу корму'),
     k('She is overtaking and keeps clear: hold your course and speed, and watch her', 'Она обгоняет и уступает: сохраняйте курс и скорость и следите за ней')],
    [you(), other(180, 380, 0, T('Ship over 50 m', 'Судно длиннее 50 м'), power=True, scale=3.4, labelAbove=False)],
    texts=[txt(170, 0, T('stand on', 'сохранять курс'), 'accent')], fit=[dict(x=-200, z=-120), dict(x=220, z=480)])

P['bs-416'] = sch(T('Lights · head-on', 'Огни · встречные курсы'),
    [k('Masthead lights in line and both sidelights: she is meeting you head-on', 'Топовые в створе и оба бортовых: она идёт вам навстречу'),
     k('Rule 14: both alter course to starboard and pass port to port', 'Правило 14: оба отворачивают вправо и расходятся левыми бортами')],
    [you(power=True), other(2, 420, 180, T('Ship over 50 m', 'Судно длиннее 50 м'), power=True, scale=3.4)],
    paths=[turn([[0, -40], [55, -140], [70, -230]]), turn([[15, -380], [-40, -280], [-55, -190]])], fit=[dict(x=-200, z=-560), dict(x=220, z=100)])

P['bs-418'] = sch(T('Lights · in doubt, it is head-on', 'Огни · при сомнении — встречные курсы'),
    [k('Fine on your bow, both sidelights, her red coming and going', 'Почти прямо по носу, оба бортовых, красный то виден, то нет'),
     k('Rule 14(c): if in doubt, assume head-on and alter to starboard', 'Правило 14(c): если есть сомнение, считайте курсы встречными и отворачивайте вправо')],
    [you(power=True), other(12, 420, 190, T('Ship over 50 m', 'Судно длиннее 50 м'), power=True, scale=3.4)],
    paths=[turn([[0, -40], [55, -140], [75, -230]])], fit=[dict(x=-200, z=-560), dict(x=260, z=100)])

P['bs-422'] = sch(T('Lights · crossing, she is on your port side', 'Огни · пересечение курсов, оно слева от вас'),
    [k('Masthead light over green: power-driven, her starboard side to you', 'Топовый над зелёным: судно с механическим двигателем, правым бортом к вам'),
     k('You are on her starboard side: she gives way; hold course and speed, ready to act', 'Вы у неё справа: уступает она; сохраняйте курс и скорость, будьте готовы действовать')],
    [you(power=True), other(-40, 330, 60, 'Power', power=True)],
    paths=[line([0, 0], [-212, -253])], texts=[txt(150, -60, T('you stand on', 'вы сохраняете курс'), 'accent'), txt(-40, -200, T('bearing steady', 'пеленг не меняется'), 'red')],
    fit=[dict(x=-330, z=-360), dict(x=260, z=100)])

def tow_plan(rel, d, hdg, astern, title, key, label_tow='Tow', you_path=None, texts=()):
    tug = at(rel, d); f = (math.sin(math.radians(hdg)), -math.cos(math.radians(hdg)))
    tw = dict(x=round(tug['x'] - f[0] * astern, 1), z=round(tug['z'] - f[1] * astern, 1))
    boats = [you(power=True), dict(tug, hdg=hdg, label='Tug', bearing=False, noHeading=True, labelAbove=True, power=True, stack=['w', 'w', 'w'], stackDx=-120),
             dict(tw, hdg=hdg, label=label_tow, bearing=False, noHeading=True, labelAbove=True)]
    paths = [dict(pts=[[tug['x'] - f[0] * 30, tug['z'] - f[1] * 30], [tw['x'] + f[0] * 30, tw['z'] + f[1] * 30]], c='ink', w=4, dash='8 8')]
    if you_path: paths.append(turn(you_path))
    mid = dict(x=(tug['x'] + tw['x']) / 2, z=(tug['z'] + tw['z']) / 2)
    return sch(title, key, boats, paths=paths,
               texts=[txt(mid['x'], mid['z'] + 150, T('tow line: never cross', 'буксирный трос: не пересекать'), 'red')] + list(texts),
               fit=[dict(x=-150, z=120), dict(x=tug['x'], z=tug['z'] - 120), dict(x=tw['x'] + 60, z=tw['z'] - 80)])

P['bs-435'] = tow_plan(35, 520, 295, 300, T('Lights · a tow over 200 m', 'Огни · буксировка длиной более 200 м'),
    [k('Three masthead lights in a line: towing, the tow over 200 m long', 'Три топовых по вертикали: буксировка длиной более 200 м'),
     k('Never cross between tug and tow: pass well astern of the tow', 'Никогда не проходите между буксиром и буксируемым: обходите далеко за кормой буксируемого')],
    you_path=[[20, -40], [200, -40], [520, 20], [700, -60]])

P['bs-439'] = sch(T('Lights · sailing vessel, bow on', 'Огни · парусное судно, носом к вам'),
    [k('Red and green, no masthead light above them: a sailing vessel', 'Красный и зелёный без топового над ними: парусное судно'),
     k('Power gives way to sail (Rule 18): you keep clear', 'Механическое уступает парусному (правило 18): уступаете вы')],
    [you(power=True), other(30, 260, 210, 'Sail')], paths=[turn([[20, -40], [110, -90], [260, -110]])],
    texts=[txt(-140, -60, T('keep clear', 'уступить'), 'red'), txt(60, -260, T('bearing steady', 'пеленг не меняется'), 'red')],
    fit=[dict(x=-220, z=-330), dict(x=330, z=100)])

P['bs-440'] = sch(T('Lights · power crossing a sailing yacht', 'Огни · механическое пересекает курс парусной яхты'),
    [k('Masthead light over red: power-driven, crossing; her port side to you', 'Топовый над красным: механическое, пересекает курс, левым бортом к вам'),
     k('Power keeps clear of sail (Rule 18): hold your course and speed, watch her', 'Механическое уступает парусному (правило 18): сохраняйте курс и скорость, следите')],
    [you(tag='under sail'), other(35, 330, 295, 'Power', power=True)],
    paths=[line([0, 0], [189, -270])], texts=[txt(-170, -60, T('you stand on', 'вы сохраняете курс'), 'accent')],
    fit=[dict(x=-220, z=150), dict(x=330, z=-360)])

P['bs-441'] = sch(T('Lights · restricted in ability to manoeuvre', 'Огни · ограниченное в возможности маневрировать'),
    [k('Red-white-red all round, masthead light and green: RAM under way', 'Красный-белый-красный круговые, топовый и зелёный: ограничено в маневре, на ходу'),
     k('Under sail you still keep clear of her (Rule 18)', 'Под парусом вы всё равно уступаете ей (правило 18)')],
    [you(tag='under sail'), other(-35, 360, 70, T('Restricted in manoeuvre', 'Ограничено в маневре'), power=True, stack=['r', 'w', 'r'], stackDx=-130, scale=3.0)],
    paths=[turn([[0, -40], [20, -110], [-20, -200]], 'course')], texts=[txt(160, -40, T('you keep clear', 'уступаете вы'), 'red')],
    fit=[dict(x=-380, z=-420), dict(x=260, z=110)])

P['bs-442'] = sch(T('Lights · fishing, gear out to one side', 'Огни · лов рыбы, снасти в одну сторону'),
    [k('Red over white: fishing; the extra white shows the side her gear is on', 'Красный над белым: лов рыбы; дополнительный белый показывает сторону снастей'),
     k('Pass on the other side: to the right, away from the extra white (Rule 26(c))', 'Проходите с другой стороны: справа, подальше от дополнительного белого (правило 26(c))')],
    [you(0, x=0, z=260), dict(x=0, z=0, hdg=90, label=T('Fishing', 'Лов рыбы'), bearing=False, noHeading=True, labelAbove=True, stack=['r', 'w'], stackDx=110, scale=3.0)],
    night=False, pad=60,
    paths=[dict(pts=[[-60, 5], [-150, 30], [-260, 60]], c='ink', dash='8 8', w=3), turn([[20, 220], [140, 120], [170, -40], [150, -200]])],
    circles=[dict(x=-75, z=12, r=7, fill='#ffffff', c='ink', dash='0')],
    texts=[txt(-150, 110, T('extra white: the gear', 'дополнительный белый: снасти'), 'red'), txt(280, 60, T('pass this side', 'проходить здесь'), 'accent')],
    fit=[dict(x=-300, z=-220), dict(x=320, z=300)])

P['bs-458'] = sch(T('Light signals · doubt', 'Световые сигналы · сомнение'),
    [k('Five or more short, rapid flashes: she doubts you are keeping clear', 'Пять и более коротких частых вспышек: она сомневается, что вы уступаете'),
     k('You are the give-way vessel: act now, boldly — turn to starboard', 'Уступаете вы: действуйте сейчас и решительно — отворот вправо')],
    [you(power=True), other(35, 340, 285, 'Ship', power=True, scale=3.0)],
    paths=[turn([[20, -40], [90, -70], [200, -60]])], texts=[txt(390, -200, T('5 rapid flashes', '5 частых вспышек'), 'red')],
    fit=[dict(x=-200, z=100), dict(x=500, z=-470)])

P['bs-459'] = sch(T('Light signals · altering course to port', 'Световые сигналы · изменяю курс влево'),
    [k('Two flashes, like two short blasts: I am altering my course to port', 'Две вспышки, как два коротких звука: изменяю курс влево'),
     k('Rule 34(b): one flash to starboard, two to port, three astern', 'Правило 34(b): одна вспышка — вправо, две — влево, три — назад')],
    [you(power=True), other(-35, 340, 70, 'Ship', power=True, scale=3.0)],
    paths=[turn([[-160, -290], [-110, -330], [-60, -400]])], texts=[txt(-400, -200, T('2 flashes', '2 вспышки'), 'red'), txt(40, -420, T('her new course', 'её новый курс'))],
    fit=[dict(x=-500, z=-500), dict(x=200, z=100)])

def leading(side):
    """You off the line on `side` ('left' or 'right'); the front (low) light shows to your side of the rear."""
    sx = -130 if side == 'left' else 130
    if side == 'left':
        title = T('Leading lights · left of the line', 'Створные огни · левее створа')
        key = [k('Rear light showing left of the front: you are left of the line', 'Задний огонь левее переднего: вы левее линии створа'),
               k('Steer to starboard, towards the front light, until they line up', 'Отворачивайте вправо, в сторону переднего огня, пока они не встанут в створ')]
        tx, tt = (-180, 20), T('steer to starboard', 'вправо')
    else:
        title = T('Leading lights · right of the line', 'Створные огни · правее створа')
        key = [k('Front (low) light showing left of the rear: you are right of the line', 'Передний (нижний) огонь левее заднего: вы правее линии створа'),
               k('Steer to port, to the side the front light has moved to', 'Отворачивайте влево, туда, куда ушёл передний огонь')]
        tx, tt = (180, 20), T('steer to port', 'влево')
    return sch(title, key, [you(0, x=sx, z=150)], night=False, pad=50,
               land=[[[-260, -420], [260, -420], [260, -230], [-260, -230]]],
               circles=[dict(x=0, z=-245, r=18, fill='#fff3c4', c='ink', dash='0'), dict(x=0, z=-360, r=18, fill='#fff3c4', c='ink', dash='0')],
               paths=[dict(pts=[[0, -245], [0, 200]], c='course', dash='16 12'), dict(pts=[[sx, 150], [0, -245]], c='ink', dash='4 10', w=3),
                      dict(pts=[[sx, 150], [0, -360]], c='ink', dash='4 10', w=3), dict(pts=[[sx * 0.96, 105], [sx * 0.23, 10]], c='red', w=7, arrow=True)],
               texts=[txt(-110 if side == 'right' else 110, -245, T('front, low', 'передний, нижний')), txt(110 if side == 'right' else -110, -360, T('rear, high', 'задний, верхний')),
                      txt(-120 if side == 'right' else 120, 100, T('the leading line', 'линия створа'), 'accent'), txt(*tx, tt, 'red')],
               fit=[dict(x=0, z=250)])

P['bs-499'] = leading('left')
P['bs-593'] = leading('right')

P['bs-554'] = channel('lat-stbd', (70, -60), T('Lateral marks · a green light', 'Латеральные знаки · зелёный огонь'),
    [k('A green light: a starboard-hand mark (IALA region A)', 'Зелёный огонь: знак правой стороны (МАМС, регион А)'),
     k('Coming in from seaward, leave it on your starboard side', 'Входя с моря, оставляйте его справа')],
    extra_marks=[dict(x=-70, z=-170, kind='lat-port', bearing=False)], texts=[txt(190, -60, 'Fl G 5s')])

P['bs-555'] = channel('lat-port', (-70, -60), T('Lateral marks · a red light', 'Латеральные знаки · красный огонь'),
    [k('Red, any rhythm but Fl(2+1): a port-hand mark', 'Красный любого ритма, кроме Fl(2+1): знак левой стороны'),
     k('Isolated danger is white Fl(2); red Fl(2) is still port-hand', 'У знака отдельной опасности белый Fl(2); красный Fl(2) — левая сторона')],
    extra_marks=[dict(x=70, z=-170, kind='lat-stbd', bearing=False)], texts=[txt(-200, -60, 'Fl(2) R 6s')])

P['bs-559'] = sch(T('Preferred channel · main channel to port', 'Предпочтительный фарватер · основной слева'),
    [k('Fl(2+1) G: a modified starboard-hand mark at the fork', 'Fl(2+1) G: модифицированный знак правой стороны у развилки'),
     k('The main channel is to port: leave the mark to starboard', 'Основной фарватер слева: оставляйте знак справа')],
    [you(0, x=-20, z=250)], night=False, pad=50,
    zones=[dict(pts=[[-110, 300], [110, 300], [110, 40], [-260, -300], [-480, -300], [-110, 40]], c='ink', fill='rgba(60,140,190,.10)', dash='0'),
           dict(pts=[[60, 0], [300, -300], [420, -300], [110, 40]], c='ink', fill='rgba(60,140,190,.05)', dash='6 10')],
    marks=[dict(x=40, z=10, kind='lat-stbd', bearing=False, hi=True)],
    paths=[turn([[-20, 210], [-60, 60], [-200, -120], [-330, -260]])],
    texts=[txt(-380, -150, T('main channel', 'основной фарватер'), 'accent'), txt(330, -200, T('secondary', 'второстепенный')), txt(170, 60, 'Fl(2+1) G')],
    fit=[dict(x=-480, z=-300), dict(x=420, z=300)])

P['bs-561'] = channel('lat-port', (70, -120), T('Lateral marks · red fine to starboard', 'Латеральные знаки · красный чуть справа'),
    [k('A red light is a port-hand mark: going in, it must pass down your port side', 'Красный огонь — знак левой стороны: при входе он должен пройти у вас слева'),
     k('Alter to starboard and leave it to port', 'Отверните вправо и оставьте его слева')],
    path=[[0, 210], [40, 60], [150, -120], [150, -240]], texts=[txt(-150, -120, 'Fl R 4s')])

P['bs-562'] = channel('lat-stbd', (70, -60), T('Lateral marks · quick flashing green', 'Латеральные знаки · частый зелёный'),
    [k('Quick flashing is not only for cardinals: the colour decides', 'Частые проблески бывают не только у кардинальных: решает цвет'),
     k('Green is a starboard-hand mark in region A', 'Зелёный — знак правой стороны в регионе А')],
    extra_marks=[dict(x=-70, z=-170, kind='lat-port', bearing=False)], texts=[txt(190, -60, 'Q G')])

P['bs-565'] = cardinal('card-e', 'e', T('East cardinal · pass to the east', 'Восточный кардинальный · обходить с востока'),
    [k('Q(3) 10s: three quick flashes, like three o’clock', 'Q(3) 10s: три частых проблеска, как 3 часа'),
     k('An east cardinal: the safe water is to the east of it', 'Восточный кардинальный знак: безопасная вода к востоку')])

P['bs-567'] = cardinal('card-n', 'n', T('North cardinal · pass to the north', 'Северный кардинальный · обходить с севера'),
    [k('Uninterrupted quick or very quick flashes: a north cardinal', 'Непрерывные частые или очень частые проблески: северный кардинальный'),
     k('Pass to the north of it, clear of the shoal', 'Обходите его с севера, в стороне от мели')])

P['bs-574'] = cardinal('card-w', 'w', T('West cardinal · pass to the west', 'Западный кардинальный · обходить с запада'),
    [k('Nine quick flashes every 15 s: like nine o’clock', 'Девять частых проблесков каждые 15 с: как 9 часов'),
     k('A west cardinal: the safe water is to the west of it', 'Западный кардинальный знак: безопасная вода к западу')])

P['bs-576'] = sch(T('Isolated danger mark', 'Знак отдельной опасности'),
    [k('White Fl(2): an isolated danger with navigable water all round', 'Белый Fl(2): отдельная опасность, вокруг судоходная вода'),
     k('Pass well clear, on any side', 'Обходите с запасом, с любой стороны')],
    [you(90, x=-110, z=-110)], night=False, pad=60,
    marks=[dict(x=0, z=-6, kind='iso', bearing=False, hi=True)], rocks=[dict(x=0, z=60)], circles=[dict(x=0, z=10, r=60, c='red')],
    paths=[turn([[-80, -110], [150, -110]]), turn([[150, 130], [-150, 130]])],
    texts=[txt(130, 40, T('rock under the mark', 'камень под знаком'), 'red'), txt(0, -160, T('safe water all round', 'безопасная вода вокруг'), 'accent')],
    fit=[dict(x=-170, z=-180), dict(x=170, z=160)])

P['bs-577'] = sch(T('Safe water mark · the landfall', 'Знак безопасных вод · подход с моря'),
    [k('White LFl 10s, alone in open water: a safe water mark', 'Белый LFl 10s одиноко в открытом море: знак безопасных вод'),
     k('Safe water all round: the landfall or the middle of a channel', 'Вокруг безопасная вода: знак подхода или оси фарватера')],
    [you(0, x=10, z=250)], night=False, pad=50,
    land=[[[-300, -300], [-60, -300], [-60, -180], [-300, -180]], [[60, -300], [300, -300], [300, -180], [60, -180]]],
    marks=[dict(x=-45, z=40, kind='safe', bearing=False, hi=True)], paths=[turn([[10, 225], [10, -150]])],
    texts=[txt(0, -240, T('HARBOUR', 'ГАВАНЬ'), pill=False, size=30), txt(-200, 120, T('safe water all round', 'безопасная вода вокруг'), 'accent')],
    fit=[dict(x=-300, z=-300), dict(x=300, z=300)])

P['bs-580'] = sch(T('Special marks · a fish farm', 'Специальные знаки · рыбная ферма'),
    [k('Yellow lights mark special marks: here, the corners of a fish farm', 'Жёлтые огни — специальные знаки: здесь углы рыбной фермы'),
     k('Keep outside the square they mark', 'Держитесь снаружи отмеченного ими квадрата')],
    [you(0, x=-60, z=260)], night=False, pad=50,
    zones=[dict(pts=[[-110, -220], [110, -220], [110, -20], [-110, -20]])],
    marks=[dict(x=-110, z=-20, kind='special', bearing=False), dict(x=110, z=-20, kind='special', bearing=False, hi=True),
           dict(x=-110, z=-220, kind='special', bearing=False), dict(x=110, z=-220, kind='special', bearing=False)],
    paths=[turn([[-60, 220], [-160, 60], [-200, -120], [-180, -300]])],
    texts=[txt(0, -120, T('fish farm', 'рыбная ферма'), 'accent'), txt(240, 20, 'Fl(4) Y 12s')],
    fit=[dict(x=-280, z=-320), dict(x=300, z=300)])

P['bs-582'] = sch(T('Emergency wreck marking', 'Знак новой опасности'),
    [k('Blue and yellow flashes in turn: an emergency wreck-marking buoy', 'Синие и жёлтые проблески попеременно: буй ограждения новой опасности'),
     k('A new danger, not yet on the chart: give it a wide berth', 'Новая опасность, которой ещё нет на карте: обходите с большим запасом')],
    [you(90, x=-190, z=170)], night=False, pad=60, wrecks=[dict(x=0, z=0)],
    marks=[dict(x=-75, z=-50, kind='wreck', bearing=False, hi=True), dict(x=75, z=55, kind='wreck', bearing=False)],
    circles=[dict(x=0, z=0, r=120, c='red')], paths=[turn([[-160, 170], [200, 170]])],
    texts=[txt(0, -150, T('new wreck: keep well off', 'новое затонувшее судно: держитесь подальше'), 'red')],
    fit=[dict(x=-220, z=-170), dict(x=220, z=230)])

P['bs-586'] = rhythm(T('Light rhythm · isophase', 'Характер огня · изофазный'),
    [k('Iso: light and dark for equal times, 3 s + 3 s', 'Iso: свет и темнота поровну, 3 с + 3 с'),
     k('The period is the whole cycle: Iso 6s', 'Период — весь цикл: Iso 6s')],
    [dict(label='Iso 6s', note=T('3 s light, 3 s dark', '3 с свет, 3 с темнота'), period=6, flashes=[[0, 3]], hi=True),
     dict(label='Oc 6s', note=T('light longer than dark', 'света больше, чем темноты'), period=6, flashes=[[0, 4.5]]),
     dict(label='Fl 6s', note=T('light shorter than dark', 'света меньше, чем темноты'), period=6, flashes=[[0, 1]])], T_=18, tick=6)

P['bs-599'] = rhythm(T('Light rhythm · group flashing', 'Характер огня · группопроблесковый'),
    [k('Two flashes close together, then dark: group flashing, Fl(2)', 'Два проблеска подряд, затем темнота: группопроблесковый Fl(2)'),
     k('The period runs from the start of one group to the next: 10 s', 'Период — от начала одной группы до начала следующей: 10 с')],
    [dict(label='Fl(2) 10s', note=T('two flashes every 10 s', 'два проблеска каждые 10 с'), period=10, flashes=[[0, 0.6], [2, 0.6]], hi=True),
     dict(label='Fl 5s', note=T('one flash every 5 s', 'один проблеск каждые 5 с'), period=5, flashes=[[0, 0.6]])], T_=20, tick=5)

P['bs-594'] = sch(T('Harbour entrance · red and green', 'Вход в гавань · красный и зелёный'),
    [k('Region A: red marks the port side of the entrance, green the starboard side', 'Регион А: красный — левая сторона входа, зелёный — правая'),
     k('Enter between them, the green to starboard', 'Входите между ними, зелёный справа')],
    [you(0, x=0, z=260)], night=False, pad=50,
    land=[[[-460, -420], [460, -420], [460, -300], [-460, -300]]],
    quays=[dict(x1=-460, z1=-300, x2=-80, z2=-250), dict(x1=80, z1=-300, x2=460, z2=-250)],
    circles=[dict(x=-80, z=-255, r=16, fill='#e0251b', c='ink', dash='0'), dict(x=80, z=-255, r=16, fill='#1aa34a', c='ink', dash='0')],
    paths=[turn([[0, 220], [0, -330]])], texts=[txt(-200, -190, 'Fl R 3s'), txt(200, -190, 'Fl G 3s'), txt(150, 60, T('enter between', 'входить между'), 'accent')],
    fit=[dict(x=-460, z=-420), dict(x=460, z=320)])

P['bs-601'] = sch(T('Sector light · you are in the red', 'Секторный огонь · вы в красном секторе'),
    [k('A sectored light shows a different colour on each bearing', 'Секторный огонь показывает разный цвет на разных пеленгах'),
     k('Red sectors usually cover a danger: steer back into the white', 'Красные секторы обычно ограждают опасность: вернитесь в белый')],
    [you(90, x=150, z=380)], night=False, pad=50,
    land=[[[-500, -420], [500, -420], [500, -330], [60, -330], [0, -280], [-60, -330], [-500, -330]]],
    zones=[dict(pts=[[0, -290], [-160, 450], [140, 450]], c='ink', fill='rgba(255,220,80,.22)', dash='0'),
           dict(pts=[[0, -290], [140, 450], [470, 450]], c='red', fill='rgba(224,37,27,.16)', dash='0')],
    rocks=[dict(x=330, z=200)], circles=[dict(x=0, z=-290, r=16, fill='#fff3c4', c='ink', dash='0')],
    paths=[turn([[110, 380], [-10, 380]])],
    texts=[txt(-10, 140, T('white: safe', 'белый: безопасно'), 'accent'), txt(330, 110, T('red: danger', 'красный: опасность'), 'red'), txt(150, -260, T('lighthouse', 'маяк'))],
    fit=[dict(x=-500, z=-420), dict(x=500, z=460)])

P['bs-603'] = sch(T('Lights · power-driven vessel, bow on', 'Огни · судно с механическим двигателем, носом к вам'),
    [k('A masthead light over both sidelights: power-driven, heading towards you', 'Топовый над обоими бортовыми: механическое, идёт на вас'),
     k('Head-on: both alter course to starboard', 'Встречные курсы: оба отворачивают вправо')],
    [you(power=True), other(0, 260, 180, 'Power', power=True)], fit=[dict(x=-200, z=-380), dict(x=200, z=100)])

P['bs-604'] = sch(T('Lights · power-driven, port side', 'Огни · механическое, левый борт'),
    [k('White masthead light and a red sidelight: power-driven', 'Белый топовый и красный бортовой: судно с механическим двигателем'),
     k('Red is her port side: she is crossing from your right to your left', 'Красный — её левый борт: она пересекает ваш курс справа налево')],
    [you(), other(0, 260, 255, 'Power', power=True)], fit=[dict(x=-220, z=-380), dict(x=220, z=100)])

P['bs-605'] = sch(T('Lights · a large vessel, starboard side', 'Огни · крупное судно, правый борт'),
    [k('Two masthead lights, the after one higher: power-driven, over 50 m', 'Два топовых, задний выше: механическое, длиннее 50 м'),
     k('A green sidelight: her starboard side to you', 'Зелёный бортовой: она правым бортом к вам')],
    [you(), other(0, 420, 80, T('Ship over 50 m', 'Судно длиннее 50 м'), power=True, scale=3.6)], fit=[dict(x=-260, z=-540), dict(x=260, z=100)])

P['bs-606'] = sch(T('Lights · sailing vessel, starboard side', 'Огни · парусное судно, правый борт'),
    [k('A sidelight with no white light above it: a sailing vessel', 'Бортовой огонь без белого над ним: парусное судно'),
     k('Green: her starboard side to you, moving from your left to right', 'Зелёный: она правым бортом к вам, идёт слева направо')],
    [you(), other(4, 240, 104, 'Sail')], fit=[dict(x=-220, z=-360), dict(x=240, z=100)])

P['bs-607'] = sch(T('Lights · tricolour, port side', 'Огни · трёхцветный, левый борт'),
    [k('A single red light high at the masthead: the red sector of a tricolour', 'Один красный высоко на топе: красный сектор трёхцветного огня'),
     k('A sailing vessel under 20 m, her port side to you, moving right to left', 'Парусное судно короче 20 м, левым бортом к вам, идёт справа налево')],
    [you(), other(0, 220, 260, T('Sail, under 20 m', 'Парусное, короче 20 м'), tag=T('tricolour', 'трёхцветный'))], fit=[dict(x=-240, z=-360), dict(x=240, z=100)])

P['bs-608'] = sch(T('Lights · tricolour, bow on', 'Огни · трёхцветный, носом к вам'),
    [k('Green and red together at the masthead, no white: a tricolour seen from ahead', 'Зелёный и красный рядом на топе, без белого: трёхцветный, вид с носа'),
     k('A yacht under sail, coming towards you', 'Яхта под парусом идёт на вас')],
    [you(), other(0, 220, 180, T('Sail, under 20 m', 'Парусное, короче 20 м'), tag=T('tricolour', 'трёхцветный'))], fit=[dict(x=-200, z=-360), dict(x=200, z=100)])

P['bs-609'] = sch(T('Lights · motor-sailing', 'Огни · под парусом и мотором'),
    [k('A steaming light means the engine is running, whatever sails are set', 'Топовый огонь означает, что работает мотор, какие бы паруса ни стояли'),
     k('Motor-sailing she is a power-driven vessel under the rules', 'Под парусом и мотором по правилам она — судно с механическим двигателем')],
    [you(), other(0, 240, 180, 'Yacht', power=True, tag=T('sails up, engine on', 'паруса подняты, мотор работает'))], fit=[dict(x=-200, z=-380), dict(x=200, z=100)])

P['bs-610'] = dict(svg=svg_anchor_ship())

P['bs-611'] = sch(T('Lights · aground', 'Огни · на мели'),
    [k('Two all-round reds plus her anchor lights: a vessel aground', 'Два круговых красных плюс якорные огни: судно на мели'),
     k('The forward anchor light is the higher one: her bow is to the left', 'Носовой якорный выше: её нос слева'),
     k('Shallow water round her: keep well off', 'Вокруг неё мелко: держитесь подальше')],
    [dict(x=0, z=0, hdg=270, label=T('Aground', 'На мели'), bearing=False, noHeading=True, labelAbove=True, stack=['r', 'r'], stackDx=-160, scale=3.4),
     you(0, x=0, z=280)], night=False, pad=60,
    zones=[dict(pts=[[-200, -90], [150, -110], [220, 30], [60, 110], [-190, 80]], c='red', fill='rgba(224,37,27,.08)')], rocks=[dict(x=150, z=-60)],
    fit=[dict(x=-300, z=-160), dict(x=300, z=340)])

def work(title, key, hdg, label, stack, extra=None, scale=3.2):
    """A vessel with all-round lights, from above, her lights beside her (no sidelight arcs: she is stopped)."""
    s = dict(night=False, padPx=60, mpp=0.32, title=title, key=key,
             boats=[dict(x=0, z=0, hdg=hdg, label=label, stack=stack, stackDx=-140, noHeading=True, scale=scale, bearing=False)])
    s.update(extra or {}); return dict(sch=s)

P['bs-612'] = sch(T('Lights · not under command, making way', 'Огни · лишённое возможности управляться, на ходу'),
    [k('Two all-round reds and sidelights, no masthead light: not under command', 'Два круговых красных и бортовые, без топового: лишено возможности управляться'),
     k('The sidelights show she is making way through the water', 'Бортовые огни показывают, что она имеет ход относительно воды')],
    [you(), other(0, 260, 120, T('Not under command', 'Лишено возможности управляться'), stack=['r', 'r'], stackDx=-140)], fit=[dict(x=-240, z=-400), dict(x=240, z=100)])

P['bs-613'] = work(T('Lights · not under command, stopped', 'Огни · лишено возможности управляться, без хода'),
    [k('Two all-round reds and nothing else: not under command', 'Два круговых красных и больше ничего: лишено возможности управляться'),
     k('No sidelights: she is not making way; aground she would add anchor lights', 'Бортовых нет: хода нет; на мели добавились бы якорные огни')],
    200, T('Not under command', 'Лишено возможности управляться'), ['r', 'r'],
    dict(paths=[dict(pts=[[30, -20], [80, -40]], c='ink', w=4, arrow=True)], texts=[txt(95, -62, T('drifting', 'дрейфует'))], fit=[dict(x=-60, z=-60), dict(x=120, z=50)]))

P['bs-614'] = sch(T('Lights · restricted in ability to manoeuvre, under way', 'Огни · ограничено в возможности маневрировать, на ходу'),
    [k('Red-white-red all round: restricted in her ability to manoeuvre', 'Красный-белый-красный круговые: ограничено в возможности маневрировать'),
     k('Masthead light and sidelights as well: she is making way', 'Плюс топовый и бортовые: она имеет ход')],
    [you(), other(0, 280, 105, T('Restricted in manoeuvre', 'Ограничено в маневре'), power=True, stack=['r', 'w', 'r'], stackDx=-140, scale=3.0)],
    fit=[dict(x=-260, z=-420), dict(x=260, z=100)])

P['bs-615'] = work(T('Lights · restricted in ability to manoeuvre, at anchor', 'Огни · ограничено в маневре, на якоре'),
    [k('Red-white-red all round: restricted in ability to manoeuvre', 'Красный-белый-красный круговые: ограничено в возможности маневрировать'),
     k('An anchor light and no sidelights: she is at anchor', 'Якорный огонь и нет бортовых: она на якоре')],
    90, T('Restricted in manoeuvre', 'Ограничено в маневре'), ['r', 'w', 'r'],
    dict(anchors=[dict(x=48, z=0, s=0.8)], paths=[dict(pts=[[22, 0], [40, 0]], c='line', w=3, dash='4 4')], fit=[dict(x=-60, z=-50), dict(x=120, z=50)]))

P['bs-616'] = sch(T('Lights · a dredger at work', 'Огни · земснаряд за работой'),
    [k('Red-white-red: restricted in ability to manoeuvre, at work', 'Красный-белый-красный: ограничено в маневре, ведёт работы'),
     k('Rule 27(d): two reds mark the obstructed side, two greens the side to pass', 'Правило 27(d): два красных — сторона препятствия, два зелёных — сторона прохода')],
    [dict(x=0, z=-150, hdg=180, label=T('Dredger', 'Земснаряд'), bearing=False, noHeading=True, labelAbove=True, stack=['r', 'w', 'r'], stackDx=-150, scale=3.2),
     you(0, x=0, z=200)], night=False, pad=60,
    zones=[dict(pts=[[-60, -230], [-260, -230], [-260, -60], [-60, -60]], c='red', fill='rgba(224,37,27,.10)')],
    paths=[turn([[20, 160], [120, 40], [140, -150], [120, -300]])],
    texts=[txt(-170, -20, T('two reds: obstructed', 'два красных: препятствие'), 'red'), txt(250, -150, T('two greens: pass here', 'два зелёных: проход здесь'), 'accent')],
    fit=[dict(x=-280, z=-320), dict(x=330, z=260)])

P['bs-617'] = work(T('Lights · trawling, not making way', 'Огни · траление, без хода'),
    [k('Green over white all round: trawling', 'Зелёный над белым, круговые: траление'),
     k('No sidelights: she is not making way', 'Бортовых нет: хода нет')],
    270, T('Trawler', 'Траулер'), ['g', 'w'],
    dict(paths=[dict(pts=[[22, -4], [95, -10]], c='ink', dash='8 8', w=3), dict(pts=[[22, 4], [95, 10]], c='ink', dash='8 8', w=3)],
         texts=[txt(112, -24, T('the trawl', 'трал'))], fit=[dict(x=-60, z=-40), dict(x=140, z=40)]))

P['bs-618'] = sch(T('Lights · fishing, making way', 'Огни · лов рыбы, на ходу'),
    [k('Red over white all round: fishing other than trawling', 'Красный над белым, круговые: лов рыбы, кроме траления'),
     k('A sidelight as well: she is making way, her port side to you', 'Плюс бортовой: она имеет ход, левым бортом к вам')],
    [you(), other(0, 240, 255, T('Fishing', 'Лов рыбы'), stack=['r', 'w'], stackDx=-130)], fit=[dict(x=-240, z=-380), dict(x=240, z=100)])

P['bs-619'] = work(T('Lights · fishing, gear out', 'Огни · лов рыбы, снасти выставлены'),
    [k('Red over white: fishing; not making way', 'Красный над белым: лов рыбы; хода нет'),
     k('The extra, lower white shows her gear, out more than 150 m: keep clear of that side', 'Дополнительный нижний белый показывает снасти дальше 150 м: держитесь в стороне')],
    270, T('Fishing', 'Лов рыбы'), ['r', 'w'],
    dict(paths=[dict(pts=[[20, 3], [70, 12], [140, 20]], c='ink', dash='8 8', w=3)], circles=[dict(x=28, z=4, r=2.2, fill='#ffffff', c='ink', dash='0')],
         texts=[txt(105, -25, T('gear: towards the extra white', 'снасти: в сторону доп. белого'), 'red')], fit=[dict(x=-60, z=-40), dict(x=160, z=40)]))

P['bs-620'] = sch(T('Lights · towing, seen from astern', 'Огни · буксировка, вид с кормы'),
    [k('A yellow towing light above the white sternlight: she is towing', 'Жёлтый буксировочный над белым кормовым: она буксирует'),
     k('Keep well clear and look out for what she tows', 'Держитесь подальше и ищите то, что она буксирует')],
    [you(), other(0, 260, 0, T('Towing', 'Буксирует'), stack=['y', 'w'], stackDx=-130)], fit=[dict(x=-220, z=-380), dict(x=220, z=100)])

P['bs-621'] = tow_plan(0, 300, 255, 260, T('Lights · towing, tow over 200 m', 'Огни · буксировка длиной более 200 м'),
    [k('Three masthead lights in a vertical line: towing', 'Три топовых по вертикали: буксировка'),
     k('The tow, from her stern to its end, is more than 200 m long', 'Длина буксира — от её кормы до конца буксируемого — более 200 м')])

P['bs-622'] = tow_plan(-10, 330, 260, 400, T('Lights · tug and tow', 'Огни · буксир и буксируемое'),
    [k('The lone red light is the tow: a towed vessel shows only sidelights and sternlight', 'Одинокий красный — буксируемое: оно несёт только бортовые и кормовой'),
     k('The tow line lies between them: never cross between tug and tow', 'Между ними буксирный трос: не проходите между буксиром и буксируемым')],
    texts=[txt(150, -150, T('about 400 m', 'около 400 м'))])

P['bs-623'] = sch(T('Lights · pilot vessel on duty', 'Огни · лоцманское судно при исполнении'),
    [k('White over red all round: a pilot vessel on duty, "white hat, red nose"', 'Белый над красным, круговые: лоцманское судно при исполнении'),
     k('A sidelight as well: she is under way', 'Плюс бортовой: она на ходу')],
    [you(), other(0, 240, 255, T('Pilot', 'Лоцман'), stack=['w', 'r'], stackDx=-130), other(-30, 520, 90, 'Ship', scale=3.4, plain=True)],
    fit=[dict(x=-300, z=-500), dict(x=240, z=100)])

P['bs-624'] = sch(T('Lights · constrained by her draught', 'Огни · стеснённое своей осадкой'),
    [k('Three all-round reds in a vertical line, and the lights of a power-driven vessel', 'Три круговых красных по вертикали и огни механического судна'),
     k('Constrained by her draught: do not impede her; keep out of her deep channel', 'Стеснено своей осадкой: не затрудняйте её движение, держитесь вне её фарватера')],
    [you(0, x=0, z=150), dict(x=0, z=-200, hdg=80, label=T('Tanker', 'Танкер'), bearing=False, noHeading=True, labelAbove=True, power=True, stack=['r', 'r', 'r'], stackDx=-170, scale=3.6)],
    zones=[dict(pts=[[-480, -280], [480, -280], [480, -120], [-480, -120]], c='ink', fill='rgba(0,118,190,.08)')],
    texts=[txt(300, -80, T('deep-water channel', 'глубоководный фарватер'), 'accent')], fit=[dict(x=-480, z=-360), dict(x=480, z=220)])

P['bs-625'] = sch(T('Lights · mine clearance', 'Огни · траление мин'),
    [k('Three all-round greens, one at the masthead and one at each yardarm: mine clearance', 'Три круговых зелёных, на топе и на концах рея: траление мин'),
     k('Dangerous within 1000 m: stay outside', 'Опасно ближе 1000 м: держитесь снаружи')],
    [you(0, x=0, z=1250), dict(x=0, z=0, hdg=180, label=T('Minesweeper', 'Тральщик'), bearing=False, noHeading=True, labelAbove=True, power=True, scale=3.2)],
    circles=[dict(x=0, z=0, r=1000, c='red')], dims=[dict(a=[0, 0], b=[707, 707], text=T('1000 m', '1000 м'))], texts=[txt(-900, -820, T('keep out', 'не входить'), 'red')],
    fit=[dict(x=-1050, z=-1050), dict(x=1050, z=1300)], pad=30)

P['bs-626'] = dict(noScale=True, sch=dict(night=True, padPx=50, mpp=0.02, title=T('Lights · how far each light carries', 'Огни · дальность видимости'),
    key=[k('Masthead lights carry 5–6 M, sidelights only 2–3 M', 'Топовые видны на 5–6 миль, бортовые — лишь на 2–3'),
         k('So the white masthead light appears first, the red only when closer', 'Поэтому сначала появляется белый топовый, а красный — лишь ближе')],
    boats=[dict(x=0, z=0, hdg=270, label='Power', power=True, bearing=False, noHeading=True, labelAbove=True), you(0, x=0, z=4.2)],
    circles=[dict(x=0, z=0, r=5, c='ink'), dict(x=0, z=0, r=2, c='red')],
    texts=[txt(6.6, -2.6, T('masthead light: 5 M', 'топовый: 5 миль')), txt(4.4, 0.6, T('sidelight: 2 M', 'бортовой: 2 мили'), 'red')],
    fit=[dict(x=-5.2, z=-5.2), dict(x=5.2, z=5.2)]))

P['bs-627'] = sch(T('Lights · she altered course to port', 'Огни · она изменила курс влево'),
    [k('A minute ago both sidelights: she was bow on', 'Минуту назад оба бортовых: она шла носом к вам'),
     k('Now only green: her bow has swung to her port, your right', 'Теперь только зелёный: её нос ушёл влево, для вас вправо')],
    [you(), other(0, 260, 180, T('before', 'было'), plain=True, labelAbove=False), other(0, 260, 120, 'Power', power=True)],
    paths=[dict(pts=[[-40, -330], [-10, -350], [40, -340]], c='red', w=5, arrow=True)], fit=[dict(x=-240, z=-420), dict(x=240, z=100)])

# ---------- write ----------
def strings(o, out):
    if isinstance(o, str): out.append(o)
    elif isinstance(o, list): [strings(x, out) for x in o]
    elif isinstance(o, dict): [strings(v, out) for kk, v in o.items() if kk not in ('kind', 'c', 'dash', 'fill', 'svg')]

def label_room(plan):
    """Fit points that keep each boat's label pill (drawn above or below the hull) inside the frame."""
    sp = plan.get('sch')
    if not sp or 'mpp' in sp: return
    pts = [(b['x'], b['z']) for b in sp.get('boats', [])] + [(f['x'], f['z']) for f in sp.get('fit', [])]
    if not pts: return
    span = max(max(p[0] for p in pts) - min(p[0] for p in pts), max(p[1] for p in pts) - min(p[1] for p in pts), 1)
    for b in sp.get('boats', []):
        if b.get('plain'): continue
        room = span * (0.16 + 0.04 * max(0, b.get('scale', 2.6) - 2.6))
        sp.setdefault('fit', []).append(dict(x=b['x'], z=b['z'] + (-room if b.get('labelAbove') else room)))

# ---------- Charter Check-in: our own lights tested at the pontoon ----------
def svg_bow_on():
    """ci-213: our yacht bow on, as from the pontoon ahead: steaming light, red to port (on your right as you face
    her), the starboard green dead."""
    cx = 640
    b = f'<path d="M{cx - 230} 470 L{cx + 230} 470 L{cx + 150} 540 L{cx - 150} 540 Z" fill="var(--ink)"/>'
    b += f'<path d="M{cx - 40} 470 L{cx + 40} 470 L{cx + 12} 560 L{cx - 12} 560 Z" fill="var(--ink)"/>'
    b += f'<line x1="{cx}" y1="470" x2="{cx}" y2="90" stroke="var(--ink)" stroke-width="8"/>'
    b += f'<line x1="{cx - 260}" y1="480" x2="{cx + 260}" y2="480" stroke="#3c8cbe" stroke-width="4"/>'
    b += glow(cx, 250, 'w', 15) + pill(cx + 190, 245, T('steaming light: on', 'топовый: горит'))
    b += glow(cx + 120, 440, 'r', 14) + pill(cx + 300, 410, T('port: red, on', 'левый: красный, горит'))
    gx = cx - 120
    b += f'<circle cx="{gx}" cy="440" r="14" fill="none" stroke="{SCOL["g"]}" stroke-width="4"/>'
    b += f'<path d="M{gx - 20} 420 L{gx + 20} 460 M{gx + 20} 420 L{gx - 20} 460" stroke="#e8231a" stroke-width="6"/>'
    b += pill(gx - 190, 410, T('starboard: green, dead', 'правый: зелёный, не горит'), 'red')
    b += pill(cx - 260, 620, T('her starboard: your left', 'её правый борт: слева от вас')) + pill(cx + 260, 620, T('her port: your right', 'её левый борт: справа от вас'))
    return frame(T('Nav lights · the starboard light is dead', 'Ходовые огни · правый не горит'),
                 [T('Seen from ahead: the steaming light and both sidelights should show', 'С носа должны быть видны топовый и оба бортовых огня'),
                  T('Note it on the form; the base replaces the bulb before you sail', 'Запишите в акт; лампу база меняет до выхода')], b)

def svg_anchor_light():
    """ci-214: the all-round white at the masthead, our yacht in profile at the pontoon."""
    b = '<line x1="60" y1="500" x2="1220" y2="500" stroke="#3c8cbe" stroke-width="4"/>'
    b += '<path d="M330 455 L950 455 L900 510 L380 520 Z" fill="var(--ink)"/>'
    b += '<line x1="600" y1="455" x2="600" y2="110" stroke="var(--ink)" stroke-width="8"/>'
    b += glow(600, 98, 'w', 16)
    for a in range(0, 360, 45):
        x1 = 600 + 34 * math.cos(math.radians(a)); y1 = 98 + 34 * math.sin(math.radians(a)); x2 = 600 + 60 * math.cos(math.radians(a)); y2 = 98 + 60 * math.sin(math.radians(a))
        b += f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" stroke="#9aa4ae" stroke-width="4"/>'
    b += pill(860, 100, T('all-round white: anchor light', 'белый круговой: якорный огонь'), 'accent', 26)
    b += pill(640, 600, T('ANCHOR breaker on: only this light', 'автомат ЯКОРНЫЙ: горит только он'))
    return frame(T('Anchor light · all-round white at the masthead', 'Якорный огонь · белый круговой на топе'),
                 [T('At anchor at night a vessel shows one all-round white light (Rule 30)', 'На якоре ночью судно несёт один белый круговой огонь (правило 30)'),
                  T('Test it at the pontoon at night, where you can see it', 'Проверьте его на понтоне ночью, где его видно')], b)

P['ci-213'] = dict(svg=svg_bow_on())
P['ci-214'] = dict(svg=svg_anchor_light())

# ---------- Yachtmaster Offshore ----------
def svg_signal_mast():
    """yof-404: the port's signal mast, three reds in a column, the yellow to the left of the top one."""
    cx = 700
    b = '<line x1="40" y1="560" x2="1240" y2="560" stroke="#3c8cbe" stroke-width="4"/>'
    b += f'<rect x="{cx - 120}" y="520" width="240" height="40" fill="var(--ink)"/><line x1="{cx}" y1="520" x2="{cx}" y2="70" stroke="var(--ink)" stroke-width="8"/>'
    b += f'<line x1="{cx}" y1="110" x2="{cx - 130}" y2="110" stroke="var(--ink)" stroke-width="6"/>'
    for y in (110, 220, 330): b += glow(cx, y, 'r', 18)
    b += glow(cx - 130, 110, 'y', 18)
    b += pill(cx + 230, 220, T('three reds: no entry', 'три красных: вход запрещён'), 'red', 26)
    b += pill(cx - 330, 110, T('yellow: exempts under 20 m', 'жёлтый: для судов до 20 м'), 'light', 24)
    b += pill(cx - 330, 430, T('your ketch: 23 m — wait outside', 'ваш кеч 23 м — ждите снаружи'), 'accent', 26)
    return frame(T('Port traffic signals · no entry, with an exemption', 'Сигналы движения в порту · вход запрещён, с исключением'),
                 [T('Three reds in a column: vessels shall not proceed', 'Три красных по вертикали: суда не должны входить и выходить'),
                  T('The yellow exempts only the vessels the port names: here under 20 m', 'Жёлтый освобождает лишь суда, названные портом: здесь до 20 м')], b)

def platform_plan(title, key, ends=True):
    """yof-026, yof-098: a platform from above, its main white light and its red end lights, the 500 m zone."""
    deck = [[-110, -40], [110, -40], [110, 40], [-110, 40]]
    c = [dict(x=0, z=0, r=500, c='red'), dict(x=0, z=0, r=20, fill='#ffffff', c='ink', dash='0')]
    if ends: c += [dict(x=-110, z=0, r=20, fill='#e0251b', c='ink', dash='0'), dict(x=110, z=0, r=20, fill='#e0251b', c='ink', dash='0')]
    return sch(title, key, [you(90, x=-700, z=700)], night=False, pad=50, zones=[dict(pts=deck, c='ink', fill='rgba(0,0,0,.25)')], circles=c,
               paths=[turn([[-660, 660], [-560, 600], [-300, 590], [300, 590], [620, 540]])],
               texts=[txt(0, -560, T('500 m safety zone: keep out', 'зона безопасности 500 м: не входить'), 'red'), txt(0, 640, T('pass outside', 'проходить снаружи'), 'accent')]
                     + ([txt(-260, -170, T('red Mo(U): the ends', 'красный Mo(U): края')), txt(250, 170, T('white Mo(U)', 'белый Mo(U)'))] if ends else [txt(120, 90, T('white Mo(U)', 'белый Mo(U)'))]),
               fit=[dict(x=-760, z=-560), dict(x=760, z=760)])

P['yof-026'] = rhythm(T('Light rhythm · Morse U: an offshore platform', 'Характер огня · Морзе U: морская платформа'),
    [k('An offshore platform: white Mo(U), · · —, usually every 15 s; the reds mark its ends', 'Морская платформа: белый Mo(U), · · —, обычно каждые 15 с; красные — её края'),
     k('A safe-water mark flashes Mo(A), · —: one short, one long', 'Знак безопасных вод — Mo(A), · —: короткий и длинный')],
    [dict(label=T('Mo(U) 15s', 'Mo(U) 15s'), note=T('· · — : the platform', '· · — : платформа'), period=15, flashes=[[0, 0.5], [1.2, 0.5], [2.4, 1.6]], hi=True),
     dict(label=T('Mo(A) 6s', 'Mo(A) 6s'), note=T('· — : safe water', '· — : безопасные воды'), period=6, flashes=[[0, 0.5], [1.2, 1.6]])], T_=15, tick=5)

P['yof-076'] = sch(T('Wind farm at night · the yellows mark its outline', 'Ветропарк ночью · жёлтые обозначают его границу'),
    [k('Corner and edge turbines: yellow lights flashing together, for vessels', 'Угловые и крайние турбины: жёлтые огни, мигают вместе — для судов'),
     k('The red lights high on the nacelles are for aircraft, not for you', 'Красные огни высоко на гондолах — для авиации, не для вас')],
    [you(0, x=-900, z=900)], night=False, pad=50,
    circles=[dict(x=x, z=z, r=48, fill='#ffa800' if (abs(x) == 900 or abs(z) == 600) else '#9aa4ae', c='ink', dash='0')
             for x in (-900, -300, 300, 900) for z in (-600, 0, 600)],
    zones=[dict(pts=[[-900, -600], [900, -600], [900, 600], [-900, 600]], c='ink', fill='rgba(255,168,0,.06)')],
    paths=[turn([[-900, 860], [-1050, 700], [-1080, 0], [-1080, -700]])],
    texts=[txt(-1100, 300, T('yellow: the edge', 'жёлтые: граница'), 'accent'), txt(0, 0, T('red: aircraft only', 'красные: только для авиации'))],
    fit=[dict(x=-1200, z=-760), dict(x=1000, z=1000)])

P['yof-098'] = platform_plan(T('A large structure · red lights at its ends', 'Большое сооружение · красные огни по краям'),
    [k('Main light white Mo(U); red Mo(U) lights mark the ends of a large platform', 'Основной огонь белый Mo(U); красные Mo(U) обозначают края большой платформы'),
     k('Pass outside the reds, clear of the 500 m safety zone', 'Проходите снаружи от красных, вне зоны безопасности 500 м')])

P['yof-404'] = dict(svg=svg_signal_mast())

P['yof-504'] = sch(T('Lights · a warship recovering aircraft', 'Огни · военный корабль принимает вертолёт'),
    [k('Red-white-red all round: launching or recovering aircraft makes her RAM (Rule 3(g)(iv))', 'Красный-белый-красный круговые: приём вертолёта — она ограничена в манёвре (правило 3(g)(iv))'),
     k('Rule 18(b): a sailing vessel keeps clear of a vessel restricted in her ability to manoeuvre', 'Правило 18(b): парусное судно уступает судну, ограниченному в манёвре')],
    [you(tag='under sail'), other(-30, 380, 80, T('Warship, RAM', 'Военный корабль, ограничен в манёвре'), power=True, stack=['r', 'w', 'r'], stackDx=-150, scale=3.4)],
    paths=[line([0, 0], [-190, -329]), turn([[0, -40], [-30, -120], [-110, -170]])],
    texts=[txt(170, -60, T('you keep clear', 'уступаете вы'), 'red'), txt(-480, -200, T('helicopter landing aft', 'вертолёт садится на корму'))],
    fit=[dict(x=-700, z=-470), dict(x=240, z=110)])

P['yof-514'] = sch(T('Narrow channel · a trawler in the fairway', 'Узкость · траулер на фарватере'),
    [k('Rule 9(c): fishing must not impede a vessel navigating within the channel', 'Правило 9(c): занятое ловом не должно затруднять движение судна в узкости'),
     k('Once risk of collision exists, Rule 18 still binds you: you keep clear (8(f)(iii))', 'Если возникла опасность столкновения, правило 18 продолжает действовать: уступаете вы (8(f)(iii))')],
    [you(power=True, x=40, z=0), other(0, 360, 180, T('Trawler', 'Траулер'), x=10, z=-360, stack=['g', 'w'], stackDx=-120)],
    zones=[dict(pts=[[-130, -560], [130, -560], [130, 120], [-130, 120]], c='ink', fill='rgba(0,118,190,.08)')],
    paths=[turn([[40, -40], [80, -120], [90, -230]])],
    texts=[txt(-330, -150, T('narrow channel', 'узкость'), 'accent'), txt(480, -420, T('she must not impede you', 'она не должна мешать'), 'light'),
           txt(480, -150, T('risk: you keep clear', 'опасность: уступаете вы'), 'red')],
    fit=[dict(x=-600, z=-600), dict(x=760, z=160)])

P['yof-517'] = sch(T('Traffic separation · fishing in the zone', 'Разделение движения · лов в зоне разделения'),
    [k('Red over white all round, no sidelights: fishing other than trawling, not making way', 'Красный над белым, круговые, без бортовых: лов рыбы (не траление), без хода'),
     k('Rule 10(e)(ii): a vessel may fish inside the separation zone', 'Правило 10(e)(ii): в зоне разделения ловить рыбу можно')],
    [you(power=True, x=0, z=300), dict(x=0, z=0, hdg=90, label=T('Fishing', 'Лов рыбы'), bearing=False, noHeading=True, labelAbove=True, stack=['r', 'w'], stackDx=-130, scale=3.0)],
    night=False, pad=50,
    zones=[dict(pts=[[-560, -260], [560, -260], [560, -90], [-560, -90]], c='ink', fill='rgba(0,118,190,.08)'),
           dict(pts=[[-560, -90], [560, -90], [560, 90], [-560, 90]], c='course', fill='rgba(255,200,0,.14)'),
           dict(pts=[[-560, 90], [560, 90], [560, 260], [-560, 260]], c='ink', fill='rgba(0,118,190,.08)')],
    texts=[txt(380, 0, T('separation zone', 'зона разделения'), 'accent'), txt(-380, -175, T('lane →', 'полоса →')), txt(-380, 175, T('← lane', '← полоса'))],
    paths=[dict(pts=[[60, 260], [60, -330]], c='course', dash='16 12', w=5, arrow=True)],
    fit=[dict(x=-560, z=-340), dict(x=560, z=380)])

P['yof-523'] = sch(T('Lights · in doubt, take the worse case', 'Огни · при сомнении — худший вариант'),
    [k('Red over green says sail; the white below it says power: lights that do not agree', 'Красный над зелёным — парус; белый под ними — мотор: огни противоречат друг другу'),
     k('In doubt (Rules 2 and 7(a)) treat her as a sailing vessel: you keep clear, early', 'При сомнении (правила 2 и 7(a)) считайте её парусной: уступаете вы, заранее')],
    [you(power=True), other(-25, 330, 145, T('Sail? Power?', 'Парус? Мотор?'), stack=['r', 'g', 'w'], stackDx=-140)],
    paths=[line([0, 0], [-139, -299])],
    texts=[txt(180, -60, T('keep clear, early', 'уступить, заранее'), 'red'), txt(-260, -170, T('bearing steady', 'пеленг не меняется'), 'red')],
    fit=[dict(x=-400, z=-430), dict(x=260, z=110)])

P['yof-524'] = sch(T('Lights · a pilot vessel on duty', 'Огни · лоцманское судно при исполнении'),
    [k('White over red all round: a pilot vessel on duty, here under way (red sidelight)', 'Белый над красным, круговые: лоцманское судно при исполнении, на ходу (красный бортовой)'),
     k('A pilot vessel is power-driven, with no special place in Rule 18: she keeps out of your way', 'Лоцманское судно — механическое, особого места в правиле 18 у него нет: уступает оно')],
    [you(tag='under sail'), other(30, 330, 225, T('Pilot', 'Лоцман'), power=True, stack=['w', 'r'], stackDx=-130)],
    paths=[line([0, 0], [165, -286])],
    texts=[txt(-170, -60, T('you stand on', 'вы сохраняете курс'), 'accent'), txt(330, -120, T('she keeps clear', 'уступает она'), 'red')],
    fit=[dict(x=-230, z=-430), dict(x=420, z=110)])

P['yof-526'] = sch(T('Lights · a WIG craft in flight', 'Огни · экраноплан в полёте'),
    [k('Rule 23(c): a WIG craft taking off, landing or flying near the surface adds a flashing red', 'Правило 23(c): экраноплан при взлёте, посадке и полёте у поверхности добавляет проблесковый красный'),
     k('Rule 18(f): she keeps well clear of all vessels and avoids impeding them', 'Правило 18(f): экраноплан держится в стороне от всех судов и не затрудняет их движение')],
    [you(), other(0, 340, 250, T('WIG craft', 'Экраноплан'), power=True, stack=['r'], stackDx=140)],
    paths=[dict(pts=[[-60, -330], [-260, -400], [-480, -470]], c='ink', w=4, dash='8 8', arrow=True)],
    texts=[txt(-300, -280, T('very fast, just above the water', 'очень быстро, над самой водой')), txt(170, -60, T('she keeps clear', 'уступает она'), 'red')],
    fit=[dict(x=-520, z=-500), dict(x=260, z=110)])

P['yof-539'] = work(T('Lights · a trawler hauling her nets', 'Огни · траулер выбирает сети'),
    [k('Green over white: trawling; below them white over red: hauling nets (Annex II)', 'Зелёный над белым: траление; ниже белый над красным: выбирает сети (Приложение II)'),
     k('Two whites below: shooting nets; two reds: the net fast on an obstruction', 'Два белых ниже — выметывает сети; два красных — сеть зацепилась за препятствие')],
    270, T('Trawler', 'Траулер'), ['g', 'w', 'w', 'r'],
    dict(paths=[dict(pts=[[22, -4], [70, -6]], c='ink', dash='8 8', w=3), dict(pts=[[22, 4], [70, 6]], c='ink', dash='8 8', w=3)],
         texts=[txt(95, -26, T('hauling: white over red', 'выбирает: белый над красным'), 'accent')], fit=[dict(x=-70, z=-50), dict(x=150, z=50)]))

P['yof-540'] = work(T('Lights · a purse seiner hampered by her net', 'Огни · кошельковый сейнер, стеснённый сетью'),
    [k('Red over white: fishing; two yellows flashing in turn below: a purse seiner (Annex II 3)', 'Красный над белым: лов рыбы; ниже два жёлтых, мигающих поочерёдно: кошельковый сейнер (Приложение II 3)'),
     k('Her net circles round her and she cannot move off it: keep well clear', 'Её сеть кольцом вокруг судна, и уйти от неё она не может: держитесь подальше')],
    270, T('Purse seiner', 'Кошельковый сейнер'), ['r', 'w', 'y', 'y'],
    dict(circles=[dict(x=30, z=0, r=38, c='ink', dash='8 8')], texts=[txt(30, -52, T('the net', 'сеть'), 'red')], fit=[dict(x=-70, z=-60), dict(x=110, z=60)]))

P['yof-541'] = work(T('Lights · a trawler with her net fast', 'Огни · траулер, сеть зацепилась'),
    [k('Green over white: trawling; two reds below them: her net is fast on an obstruction', 'Зелёный над белым: траление; два красных ниже: сеть зацепилась за препятствие'),
     k('She cannot move off; two reds alone would mean not under command', 'Уйти она не может; два красных без огней лова означали бы «лишено возможности управляться»')],
    270, T('Trawler', 'Траулер'), ['g', 'w', 'r', 'r'],
    dict(paths=[dict(pts=[[22, 0], [110, 10]], c='ink', dash='8 8', w=3)], rocks=[dict(x=120, z=12)],
         texts=[txt(120, -18, T('net fast', 'сеть зацепилась'), 'red')], fit=[dict(x=-70, z=-50), dict(x=150, z=50)]))

P['yof-542'] = sch(T('Lights · a dredger at anchor', 'Огни · земснаряд на якоре'),
    [k('Red-white-red, and the red and green pairs: RAM, dredging (Rule 27(d))', 'Красный-белый-красный, пары красных и зелёных: ограничен в манёвре, ведёт дноуглубление (правило 27(d))'),
     k('At anchor these replace her anchor lights (27(d)(iv)); pass on the side of the greens', 'На якоре они заменяют якорные огни (27(d)(iv)); проходите со стороны зелёных')],
    [dict(x=0, z=-150, hdg=180, label=T('Dredger at anchor', 'Земснаряд на якоре'), bearing=False, noHeading=True, labelAbove=True, stack=['r', 'w', 'r'], stackDx=-150, scale=3.2),
     you(0, x=0, z=200)], night=False, pad=60,
    anchors=[dict(x=0, z=-20, s=0.8)],
    zones=[dict(pts=[[-60, -230], [-260, -230], [-260, -60], [-60, -60]], c='red', fill='rgba(224,37,27,.10)')],
    paths=[dict(pts=[[0, -75], [0, -45]], c='line', w=3, dash='4 4'), turn([[40, 170], [180, 60], [200, -150], [180, -300]])],
    texts=[txt(-170, -20, T('two reds: obstructed', 'два красных: препятствие'), 'red'), txt(250, -150, T('two greens: pass here', 'два зелёных: проход здесь'), 'accent'),
           txt(260, -330, T('no anchor light needed', 'якорный огонь не нужен'))],
    fit=[dict(x=-280, z=-480), dict(x=480, z=260)])

P['yof-548'] = sch(T('Light signals · one flash', 'Световые сигналы · одна вспышка'),
    [k('One flash of about a second: “I am altering my course to starboard” (Rule 34(b))', 'Одна вспышка около секунды: «Изменяю курс вправо» (правило 34(b))'),
     k('The light is all-round white, seen at least 5 M; it may go with or without the sound', 'Огонь белый круговой, видимость не менее 5 миль; подаётся со звуком или без')],
    [you(power=True), other(15, 360, 255, 'Ship', power=True, scale=3.2)],
    paths=[turn([[60, -330], [20, -340], [-20, -370], [-40, -420]])],
    texts=[txt(330, -460, T('one flash: turning to starboard', 'одна вспышка: поворачиваю вправо'), 'red')],
    fit=[dict(x=-200, z=-520), dict(x=420, z=110)])

P['yof-563'] = sch(T('Lights · constrained by her draught, in a lane', 'Огни · стеснено осадкой, в полосе движения'),
    [k('Three all-round reds in a column: constrained by her draught (Rule 28)', 'Три круговых красных по вертикали: стеснено своей осадкой (правило 28)'),
     k('Rules 18(d) and 10(j): you avoid impeding her — act early, pass astern of her', 'Правила 18(d) и 10(j): не затрудняйте её движение — заранее, за её кормой')],
    [you(tag='under sail'), other(-30, 380, 90, T('Constrained by draught', 'Стеснено осадкой'), power=True, stack=['r', 'r', 'r'], stackDx=-150, scale=3.6)],
    zones=[dict(pts=[[-700, -420], [500, -420], [500, -240], [-700, -240]], c='ink', fill='rgba(0,118,190,.08)')],
    paths=[line([0, 0], [-190, -329]), turn([[0, -40], [-40, -110], [-160, -150], [-330, -150]])],
    texts=[txt(380, -330, T('eastbound lane', 'полоса на восток'), 'accent'), txt(170, -60, T('do not impede her', 'не мешайте ей'), 'red')],
    fit=[dict(x=-700, z=-480), dict(x=500, z=110)])

P['yof-565'] = dict(sch=dict(night=True, padPx=70, title=T('Lights · a tricolour, tack unknown', 'Огни · трёхцветный, галс неизвестен'), wind=0,
    key=[k('Her red shows you are on her port side: her heading is between 150° and 262°T', 'Виден её красный — вы с её левого борта: её курс между 150° и 262° ист.'),
         k('In a north wind that is either tack: on port tack you keep clear (Rule 12(a)(iii))', 'При ветре N это любой галс: на левом галсе вы уступаете (правило 12(a)(iii))')],
    boats=[you(45, tag=T('port tack', 'левый галс')),
           dict(x=-170, z=-300, hdg=200, label=T('She: tack unknown', 'Она: галс неизвестен'), bearing=False, noHeading=True, labelAbove=True)],
    paths=[line([0, 0], [-170, -300]),
           dict(pts=[[-150, -240], [-115, -100]], c='ink', w=4, dash='8 8', arrow=True), dict(pts=[[-225, -280], [-370, -225]], c='ink', w=4, dash='8 8', arrow=True)],
    texts=[txt(200, 60, T('you keep clear', 'уступаете вы'), 'red'), txt(-60, -60, T('160°T: port tack?', '160° ист.: левый галс?')),
           txt(-470, -260, T('250°T: starboard tack?', '250° ист.: правый галс?')), txt(120, -200, T('she bears 330°T', 'она на 330° ист.'))],
    fit=[dict(x=-640, z=-520), dict(x=330, z=160)]))

P['yof-567'] = dict(noScale=True, **sch(T('Head-on in doubt · turn to starboard, boldly', 'Сомнение во встречном · решительно вправо'),
    [k('Two masthead lights almost in line, only her green: end-on or nearly so', 'Два топовых почти в створе, виден лишь зелёный: встречный или почти встречный'),
     k('Rule 14(c): assume head-on; a bold, early turn to starboard opens the 0.3 M CPA, port to port', 'Правило 14(c): считайте курсы встречными; ранний крупный поворот вправо увеличит CPA 0,3 мили — левыми бортами')],
    [you(power=True), other(3, 560, 180, 'Ship', power=True, scale=3.2)],
    paths=[turn([[0, -40], [60, -110], [150, -150], [230, -170]]), dict(pts=[[29, -500], [29, 60]], c='red', w=3, dash='8 10')],
    texts=[txt(-200, -300, T('as she is: stbd to stbd, 0.3 M', 'сейчас: правыми бортами, 0,3 мили'), 'red'), txt(260, -60, T('bold turn to starboard', 'решительно вправо'), 'accent'),
           txt(-160, -540, T('6 M', '6 миль'))],
    fit=[dict(x=-330, z=-760), dict(x=330, z=110)]))

P['yof-572'] = sch(T('Lights · not under command, making way', 'Огни · лишённое возможности управляться, на ходу'),
    [k('Two all-round reds; making way she adds sidelights and a sternlight: from astern you see the sternlight', 'Два круговых красных; на ходу добавляет бортовые и кормовой — с кормы виден кормовой'),
     k('You are overtaking a vessel not under command: you keep clear (Rules 13 and 18)', 'Вы обгоняете судно, лишённое возможности управляться: уступаете вы (правила 13 и 18)')],
    [you(power=True), other(0, 300, 0, T('Not under command', 'Лишено возможности управляться'), stack=['r', 'r'], stackDx=-150, labelAbove=False)],
    paths=[turn([[10, -40], [90, -140], [110, -330]])],
    texts=[txt(230, -160, T('keep clear', 'уступить'), 'red'), txt(-230, -60, T('9 kn vs 3 kn', '9 уз против 3 уз'))],
    fit=[dict(x=-260, z=-420), dict(x=300, z=110)])

P['yof-573'] = work(T('Lights · not under command, drifting', 'Огни · лишено возможности управляться, в дрейфе'),
    [k('Two all-round reds: not under command; she moves only with the current', 'Два круговых красных: лишено возможности управляться; движется лишь с течением'),
     k('Rule 27(a)(iii): sidelights and sternlight only when making way through the water — so none', 'Правило 27(a)(iii): бортовые и кормовой — лишь при ходе относительно воды, а его нет')],
    200, T('Not under command', 'Лишено возможности управляться'), ['r', 'r'],
    dict(paths=[dict(pts=[[30, 15], [90, -7]], c='ink', w=4, arrow=True), dict(pts=[[-60, 45], [0, 23]], c='course', w=4, dash='8 8', arrow=True)],
         texts=[txt(105, -30, T('over the ground: 070° 2 kn', 'над грунтом: 070° 2 уз')), txt(-60, 70, T('current 070° 2 kn', 'течение 070° 2 уз'), 'accent')],
         fit=[dict(x=-80, z=-60), dict(x=140, z=80)]))

def tow_astern(title, key, ram=False):
    """yof-575, yof-577: you right astern of a tow, the tug ahead of her barge; seen from astern."""
    tug = dict(x=0, z=-1150, hdg=0, label=T('Tug', 'Буксировщик'), bearing=False, noHeading=True, labelAbove=True, power=True,
               stack=(['r', 'w', 'r', 'y', 'w'] if ram else ['y', 'w']), stackDx=-130)
    tow = dict(x=0, z=-600, hdg=0, label=T('Tow', 'Буксируемое'), bearing=False, noHeading=True, labelAbove=False)
    return sch(title, key, [you(power=True), tug, tow],
               paths=[dict(pts=[[0, -1060], [0, -690]], c='ink', w=4, dash='8 8'), turn([[30, -60], [330, -300], [380, -700]])],
               texts=[txt(260, -880, T('tow line', 'буксирный трос')), txt(-620, -330, T('from astern: no masthead lights', 'с кормы: топовых не видно'), 'red')],
               fit=[dict(x=-1000, z=-1300), dict(x=600, z=110)])

P['yof-575'] = tow_astern(T('Lights · a tow seen from astern', 'Огни · буксировка с кормы'),
    [k('The length shows in two or three masthead lights, seen only from ahead and abeam (Rule 24(a))', 'Длину показывают два или три топовых — их видно только с носа и с траверза (правило 24(a))'),
     k('From astern only the yellow towing light and the sternlights: you cannot tell the length', 'С кормы — только жёлтый буксировочный и кормовые огни: длину не определить')])

P['yof-577'] = tow_astern(T('Lights · a tow that cannot deviate', 'Огни · буксировка, не может отклониться от курса'),
    [k('Red-white-red over the yellow towing light and sternlight: a tug restricted by her tow (Rule 27(c))', 'Красный-белый-красный над жёлтым буксировочным и кормовым: буксировщик ограничен в манёвре (правило 27(c))'),
     k('The low white on the left is her tow: never pass between them', 'Низкий белый слева — буксируемое: никогда не проходите между ними')], ram=True)

P['yof-578'] = sch(T('Lights · a dredger under way, from astern', 'Огни · земснаряд на ходу, с кормы'),
    [k('Rule 27(d): the two greens mark the side to pass, the two reds the obstruction', 'Правило 27(d): два зелёных — сторона прохода, два красных — препятствие'),
     k('From astern her port side, with the greens, is on your left; you overtake and keep clear (Rule 13)', 'С кормы её левый борт с зелёными — слева от вас; вы обгоняете и уступаете (правило 13)')],
    [dict(x=0, z=-250, hdg=0, label=T('Dredger', 'Земснаряд'), bearing=False, noHeading=True, labelAbove=True, stack=['r', 'w', 'r'], stackDx=150, scale=3.2),
     you(0, x=0, z=150)], night=False, pad=60,
    zones=[dict(pts=[[60, -350], [260, -350], [260, -150], [60, -150]], c='red', fill='rgba(224,37,27,.10)')],
    paths=[turn([[-20, 110], [-130, 0], [-150, -250], [-120, -420]])],
    texts=[txt(170, -100, T('two reds: obstructed', 'два красных: препятствие'), 'red'), txt(-280, -250, T('two greens: pass here', 'два зелёных: проход здесь'), 'accent')],
    fit=[dict(x=-330, z=-470), dict(x=300, z=210)])

P['yof-579'] = sch(T('Lights · a small boat with divers down', 'Огни · малое судно, водолазы под водой'),
    [k('Red-white-red: too small for all the RAM lights, she shows these when diving (Rule 27(e)(i))', 'Красный-белый-красный: малое судно с водолазами несёт только их (правило 27(e)(i))'),
     k('Divers may be in the water round her: slow right down and pass wide', 'Вокруг могут быть водолазы: сильно сбавьте ход и обходите широко')],
    [you(power=True, x=0, z=300), dict(x=0, z=-150, hdg=90, label=T('Diving boat', 'Судно с водолазами'), bearing=False, noHeading=True, labelAbove=True, stack=['r', 'w', 'r'], stackDx=-140, scale=2.6)],
    night=False, pad=60, circles=[dict(x=0, z=-150, r=120, c='red')],
    paths=[turn([[20, 260], [150, 100], [210, -150], [160, -380]])],
    texts=[txt(-230, -20, T('divers may be down', 'возможны водолазы'), 'red'), txt(330, 120, T('slow, pass wide', 'малым ходом, широко'), 'accent'),
           txt(-260, 200, T('dive site', 'место погружений'))],
    fit=[dict(x=-360, z=-420), dict(x=360, z=350)])

P['yof-580'] = work(T('Lights · RAM at anchor', 'Огни · ограничено в манёвре, на якоре'),
    [k('Red-white-red all round: restricted in ability to manoeuvre, servicing a buoy', 'Красный-белый-красный, круговые: ограничено в манёвре, обслуживает буй'),
     k('Rule 27(b)(iv): at anchor she adds her anchor light; only 27(d) work drops it', 'Правило 27(b)(iv): на якоре добавляет якорный огонь; не несут его лишь при работах по 27(d)')],
    90, T('Buoy tender', 'Судно обслуживания буёв'), ['r', 'w', 'r'],
    dict(anchors=[dict(x=48, z=0, s=0.8)], paths=[dict(pts=[[22, 0], [40, 0]], c='line', w=3, dash='4 4')],
         circles=[dict(x=26, z=0, r=2.6, fill='#ffffff', c='ink', dash='0')],
         marks=[dict(x=-95, z=20, kind='lat-port', bearing=False)],
         texts=[txt(40, -28, T('anchor light: correct', 'якорный огонь: верно'), 'accent'), txt(-95, 48, T('the buoy', 'буй'))],
         fit=[dict(x=-130, z=-50), dict(x=120, z=70)]))

P['yof-581'] = sch(T('Lights · a trawler shooting her nets', 'Огни · траулер выметывает сети'),
    [k('Green over white: trawling; two whites below them: shooting nets (Annex II 2(a)(i))', 'Зелёный над белым: траление; два белых ниже: выметывает сети (Приложение II 2(a)(i))'),
     k('Her trawl is paying out astern, towards you: keep well clear of her stern', 'Трал уходит за корму — в вашу сторону: держитесь подальше от её кормы')],
    [you(power=True), other(0, 420, 350, T('Trawler', 'Траулер'), stack=['g', 'w', 'w', 'w'], stackDx=-150)],
    paths=[dict(pts=[[-8, -395], [0, -300], [10, -220]], c='ink', w=3, dash='8 8'), dict(pts=[[-2, -395], [30, -300], [45, -230]], c='ink', w=3, dash='8 8'),
           turn([[-10, -40], [-120, -120], [-170, -300]])],
    texts=[txt(160, -260, T('trawl paying out', 'трал уходит за корму'), 'red'), txt(-260, -150, T('keep clear', 'уступить'), 'accent'), txt(170, -60, T('1 M', '1 миля'))],
    fit=[dict(x=-330, z=-560), dict(x=260, z=110)])

P['yof-583'] = sch(T('Lights · a hovercraft head-on', 'Огни · судно на воздушной подушке на встречном курсе'),
    [k('Flashing yellow all round: an air-cushion vessel in the non-displacement mode (Rule 23(b))', 'Проблесковый жёлтый круговой: судно на воздушной подушке в неводоизмещающем режиме (правило 23(b))'),
     k('She is power-driven, end-on: Rule 14 — both alter to starboard, port to port', 'Она — механическое судно, курсы встречные: правило 14 — обе вправо, левыми бортами')],
    [you(power=True), other(0, 420, 180, T('Hovercraft', 'Судно на воздушной подушке'), power=True, stack=['y'], stackDx=-130)],
    paths=[turn([[0, -40], [55, -140], [70, -230]]), turn([[15, -380], [-40, -280], [-55, -190]])],
    texts=[txt(220, -150, T('turn to starboard', 'отворот вправо'), 'accent')], fit=[dict(x=-240, z=-560), dict(x=280, z=100)])

P['yof-584'] = sch(T('Lights · two masthead lights, length unknown', 'Огни · два топовых, длина неизвестна'),
    [k('From 50 m two masthead lights are required; under 50 m a second one is allowed (Rule 23(a)(ii))', 'С 50 м два топовых обязательны; короче 50 м второй разрешён (правило 23(a)(ii))'),
     k('A tug’s two or three are in a vertical line; these are one aft and higher, as on any vessel', 'У буксировщика два-три топовых по вертикали; здесь задний выше — как у обычного судна')],
    [you(power=True), other(10, 380, 135, T('Power, under or over 50 m?', 'Механическое: меньше или больше 50 м?'), power=True, scale=3.0)],
    texts=[txt(-330, -150, T('two masthead lights: not proof of 50 m', 'два топовых: ещё не 50 м'), 'red')],
    fit=[dict(x=-700, z=-600), dict(x=400, z=110)])

P['yof-589'] = sch(T('Lights · aground', 'Огни · на мели'),
    [k('Rule 30(d): aground — her anchor light and two all-round reds', 'Правило 30(d): на мели — якорный огонь и два круговых красных'),
     k('You saw the white from every side: all-round, not a 135° sternlight — she is not NUC under way', 'Белый виден со всех сторон: он круговой, не кормовой на 135° — это не НУК на ходу')],
    [dict(x=0, z=0, hdg=90, label=T('Aground', 'На мели'), bearing=False, noHeading=True, labelAbove=True, stack=['r', 'r'], stackDx=-160, scale=3.2)],
    night=False, pad=60,
    zones=[dict(pts=[[-200, -90], [150, -110], [220, 30], [60, 110], [-190, 80]], c='red', fill='rgba(224,37,27,.08)')],
    circles=[dict(x=0, z=0, r=330, c='course')],
    texts=[txt(0, 140, T('charted shoal', 'отмель по карте'), 'red'), txt(290, -290, T('seen from every side', 'видно со всех сторон'), 'accent')],
    fit=[dict(x=-360, z=-360), dict(x=360, z=360)])

def main(ids):
    for qid in ids:
        e = LIST[qid]; d = os.path.join(qdir(qid), qid); os.makedirs(d, exist_ok=True)
        plan = P[qid]; label_room(plan)
        with open(os.path.join(d, 'plan.json'), 'w') as f: json.dump(plan, f, ensure_ascii=False, indent=1)
        ru = {}
        lab_path = os.path.join(d, '3d.labels.json')
        lab = json.load(open(lab_path)) if os.path.exists(lab_path) else {'note': e['figure'].get('note'), 'labels': [{'text': l['t']} for l in e['figure']['lights'] if l.get('t')]}
        texts = ([lab['note']] if lab.get('note') else []) + [L['text'] for L in lab.get('labels', [])] + list(lab.get('lines', []))
        for t in texts:
            ru[t] = e['ru'].get(t, RU.get(t))
            if ru[t] is None: print('NO RU', qid, repr(t))
        ss = []; strings(plan, ss)
        if 'svg' in plan:
            ss += [re.sub(r'&amp;', '&', m) for m in re.findall(r'>([^<>]+)</t(?:ext|span)>', plan['svg'])]
        for t in ss:
            if t in ru: continue
            if t in RU: ru[t] = RU[t]
            elif t in e['ru']: ru[t] = e['ru'][t]
            elif re.match(r'^(Fl|Iso|Oc|Q|VQ|LFl|Al)\b', t): ru[t] = t      # a chart abbreviation reads the same
        if 'rhythm' in plan:   # the time axis of a rhythm plan: '5 s'
            for t in range(0, plan['rhythm']['T'] + 1, plan['rhythm'].get('tick', 5)): ru[f'{t} s'] = f'{t} с'
        with open(os.path.join(d, 'ru.json'), 'w') as f: json.dump(ru, f, ensure_ascii=False, indent=1)

if __name__ == '__main__':
    ids = sys.argv[1:] or list(LIST)
    missing = [i for i in ids if i not in P]
    if missing: print('no plan for', missing)
    main([i for i in ids if i in P])
