# The schematics of article yachtmaster-offshore/colregs: writes figure-style/articles/yachtmaster-offshore/colregs/
# <n>-plan.json (figure-schematic.js specs, or an SVG of our own in the same style), and ru-plans.json, the Russian of
# every string here (merged into ru.json with the render labels).
#   python3 docs/design/blender/art_yof_colregs_plans.py
import json, math, os

HERE = os.path.dirname(os.path.abspath(__file__))
DIR = os.path.join(HERE, '..', 'figure-style', 'articles', 'yachtmaster-offshore', 'colregs')
RU = {}
def T(en, ru): RU[en] = ru; return en

def at(x, z, brg, d):
    """The point d metres from (x, z) on true bearing brg (plan: x east, z south)."""
    a = math.radians(brg); return dict(x=round(x + d * math.sin(a), 1), z=round(z - d * math.cos(a), 1))
def you(x=0, z=0, hdg=0, **o): b = dict(you=True, x=x, z=z, hdg=hdg, noHeading=True); b.update(o); return b
def boat(x, z, hdg, label, **o): b = dict(x=x, z=z, hdg=hdg, label=label, bearing=False, noHeading=True); b.update(o); return b
def line(a, b, c='ink', w=4, dash='10 10', arrow=False): d = dict(pts=[list(a), list(b)], c=c, w=w, dash=dash); d.update(arrow=True) if arrow else None; return d
def turn(pts, c='course'): return dict(pts=[list(p) for p in pts], c=c, dash='16 12', arrow=True)
def txt(x, z, text, kind='light', **o): d = dict(x=x, z=z, text=text, kind=kind); d.update(o); return d
def sch(title, key, **o): s = dict(padPx=80, title=title, key=list(key)); s.update(o); return dict(sch=s)
def xz(p): return (p['x'], p['z'])

# ---------------------------------------------------------------- SVG pieces, in the schematic's style
def esc(s): return str(s).replace('&', '&amp;').replace('<', '&lt;')
def stxt(x, y, s, size=26, w=700, fill='var(--muted)', a='middle'):
    return f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{w}" fill="{fill}" text-anchor="{a}">{esc(s)}</text>'
def pill(x, y, text, kind='light', size=24):
    n = max(len(text), len(RU.get(text, text))); w = n * size * 0.56 + size * 1.4; h = size * 1.7
    fill = {'accent': 'var(--accent)', 'red': '#e8231a'}.get(kind, 'var(--bg)'); ink = 'var(--ink)' if kind == 'light' else '#fff'
    stroke = 'var(--tag-line)' if kind == 'light' else fill
    return (f'<rect x="{x - w / 2:.1f}" y="{y - h / 2:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{h / 2:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="3"/>'
            + stxt(x, round(y + size * 0.36, 1), text, size, 700, ink))
SC = {'r': '#e0251b', 'g': '#1aa34a', 'w': '#ffffff', 'y': '#ffa800'}
def glow(x, y, c, r=13):
    return f'<circle cx="{x}" cy="{y}" r="{r * 2}" fill="{SC[c]}" opacity=".22"/><circle cx="{x}" cy="{y}" r="{r}" fill="{SC[c]}" stroke="{"#9aa4ae" if c == "w" else "none"}" stroke-width="2"/>'
def dim(x1, y1, x2, y2, text, kind='light'):
    v = abs(x1 - x2) < 1
    t = (lambda x, y: f'<line x1="{x - 12}" y1="{y}" x2="{x + 12}" y2="{y}" stroke="var(--ink)" stroke-width="4"/>') if v else (lambda x, y: f'<line x1="{x}" y1="{y - 12}" x2="{x}" y2="{y + 12}" stroke="var(--ink)" stroke-width="4"/>')
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="var(--ink)" stroke-width="4"/>' + t(x1, y1) + t(x2, y2) + pill((x1 + x2) / 2, (y1 + y2) / 2, text, kind, 22)
def frame(title, key, body, gid):
    W, H = 1280, 800; keyH = 40 + 40 * len(key) + 24
    s = f'<svg xmlns="http://www.w3.org/2000/svg" id="{gid}" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="Carlito, Arial, sans-serif" style="background:var(--bg)"><rect width="{W}" height="{H}" fill="var(--bg)"/>'
    s += body + f'<rect x="0" y="{H - keyH}" width="{W}" height="{keyH}" fill="var(--band)"/>' + stxt(30, H - keyH + 40, title, 30, 700, 'var(--ink)', 'start')
    for i, k in enumerate(key):
        s += stxt(30, H - keyH + 80 + 40 * i, '·', 27, 400, 'var(--ink)', 'start') + stxt(46, H - keyH + 80 + 40 * i, k, 27, 400, 'var(--ink)', 'start')
    return {'noScale': True, 'svg': s + '</svg>'}

PL = {}
# ---------------------------------------------------------------- 1: a VLCC close, bridge and bow
L = 330; rx = -L / 2 + 0.03 * L + 0.72 * 0.13 * L
br = at(0, 0, 68, 700); ctr = dict(x=br['x'] + rx, z=br['z']); bow = dict(x=ctr['x'] - L / 2, z=ctr['z'])
PL[1] = sch(T('Rules 7 and 8 · a very large ship, close', 'Правила 7 и 8 · очень большое судно рядом'),
            [T('Her bridge, far aft, bears 068° and draws aft as she crosses', 'Её мостик далеко в корме: пеленг 068°, он смещается к корме'),
             T('Her bow, 290 m ahead of it, can hold a steady bearing: risk', 'Её нос, на 290 м впереди, может держать пеленг: опасность'),
             ], trueScale=True, padPx=70,
            boats=[you(L=21), boat(ctr['x'], ctr['z'], 270, 'VLCC', L=330)],
            paths=[line((0, 0), xz(br)), line((0, 0), xz(bow), 'red')],
            texts=[txt(br['x'] * 0.62 + 120, br['z'] * 0.62 + 40, T('bridge 068° · drawing aft', 'мостик 068° · уходит к корме')),
                   txt(bow['x'] * 0.55 - 120, bow['z'] * 0.55 - 30, T('bow 054° · steady?', 'нос 054° · не меняется?'), 'red')],
            fit=[dict(x=-120, z=80), dict(x=760, z=-470)])
# ---------------------------------------------------------------- 2: a steady bearing, one large alteration
ys = [(0, 0), (0, 300), (0, 600)]; rs = [600, 975, 1350]
sh = [at(x, z, 40, r) for (x, z), r in zip(ys, rs)]
PL[2] = sch(T('Risk of collision · a steady compass bearing', 'Опасность столкновения · пеленг не меняется'),
            [T('Three bearings, all 040°, the range closing: risk of collision', 'Три пеленга, все 040°, дистанция сокращается: опасность столкновения'),
             T('Act early, with one large alteration she can see: here, round her stern', 'Действуйте заранее, одним крупным заметным манёвром: здесь — за её кормой')],
            padPx=70,
            boats=[you(0, 0, 0, scale=1.8, labelAbove=True), boat(0, 300, 0, '', plain=True, scale=1.6), boat(0, 600, 0, '', plain=True, scale=1.6),
                   boat(sh[0]['x'], sh[0]['z'], 270, T('Ship', 'Судно'), scale=2.4, labelAbove=True), boat(sh[1]['x'], sh[1]['z'], 270, '', plain=True, scale=2.2), boat(sh[2]['x'], sh[2]['z'], 270, '', plain=True, scale=2.2)],
            paths=[line(p, xz(q)) for p, q in zip(ys, sh)] + [turn([(0, -50), (60, -160), (220, -230), (420, -220)])],
            texts=[txt(760, -60, T('040° · 040° · 040°', '040° · 040° · 040°'), 'red'), txt(-330, -260, T('one large alteration, early', 'один крупный манёвр, заранее'), 'accent'),
                   txt(-200, 300, T('6 min ago', '6 мин назад'), pill=False, size=24), txt(-200, 600, T('12 min ago', '12 мин назад'), pill=False, size=24)],
            fit=[dict(x=-420, z=660), dict(x=900, z=-700)])
# ---------------------------------------------------------------- 3, 4: the separation scheme
def tss(title, key, boats, paths, texts):
    land = [[-900, -420], [900, -420], [900, -330], [400, -345], [0, -335], [-400, -350], [-900, -340]]
    zones = [dict(pts=[[-900, -330], [900, -330], [900, -185], [-900, -185]], c='ink', fill='rgba(0,118,190,.07)'),
             dict(pts=[[-900, -170], [900, -170], [900, -40], [-900, -40]], c='ink', fill='rgba(0,0,0,.03)'),
             dict(pts=[[-900, -40], [900, -40], [900, 40], [-900, 40]], c='red', fill='rgba(224,37,27,.10)'),
             dict(pts=[[-900, 40], [900, 40], [900, 170], [-900, 170]], c='ink', fill='rgba(0,0,0,.03)')]
    return sch(title, key, padPx=40, land=[land], zones=zones, boats=boats, paths=paths, texts=texts, fit=[dict(x=-860, z=-420), dict(x=860, z=300)])
PL[3] = tss(T('Traffic separation scheme · Rule 10', 'Система разделения движения · правило 10'),
            [T('Cross a lane on a heading at right angles to its traffic', 'Пересекайте полосу курсом под прямым углом к потоку'),
             T('Or follow the lane, in its direction of traffic', 'Или идите по полосе в направлении её потока')],
            [you(30, 230, 0), boat(-420, 105, 90, T('Yacht', 'Яхта'), scale=2.2), boat(-160, 105, 90, T('Ship', 'Судно'), scale=3.4, labelAbove=True), boat(260, -105, 270, T('Ship', 'Судно'), scale=3.4)],
            [turn([(30, 195), (30, -170)]), dict(pts=[[-80, 105], [40, 105]], c='ink', w=4, arrow=True), dict(pts=[[140, -105], [20, -105]], c='ink', w=4, arrow=True)],
            [txt(-560, -255, T('inshore traffic zone', 'зона прибрежного плавания'), pill=False), txt(560, -105, T('← lane: traffic west', '← полоса: поток на запад'), pill=False),
             txt(560, 0, T('separation zone', 'зона разделения'), pill=False), txt(560, 105, T('lane: traffic east →', 'полоса: поток на восток →'), pill=False),
             txt(170, 270, T('cross at right angles', 'пересекать под прямым углом'), 'accent'), txt(-420, 20, T('or follow the lane', 'или идти по полосе'))])
PL[4] = tss(T('Rule 10 · who may use which part', 'Правило 10 · кто где может идти'),
            [T('Join or leave a lane at its end, or from the side at a small angle', 'Входите в полосу и выходите из неё в её конце или сбоку под малым углом'),
             T('Separation zone: only to cross, in an emergency, or to fish · no anchoring', 'Зона разделения: только пересечь, в аварии или для лова · якорная стоянка запрещена')],
            [you(-300, 230, 68), boat(-120, -2, 250, T('Fishing', 'Лов рыбы'), scale=2.2), boat(-200, -255, 280, T('Yacht under 20 m', 'Яхта до 20 м'), scale=2.2), boat(250, 105, 90, T('Ship', 'Судно'), scale=3.4)],
            [turn([(-270, 215), (-120, 155), (60, 110)])],
            [txt(-560, -255, T('inshore traffic zone', 'зона прибрежного плавания'), pill=False), txt(600, -105, T('← lane: traffic west', '← полоса: поток на запад'), pill=False),
             txt(640, 0, T('separation zone', 'зона разделения'), pill=False), txt(640, 140, T('lane: traffic east →', 'полоса: поток на восток →'), pill=False),
             txt(-600, 200, T('join at a small angle', 'входить под малым углом'), 'accent'), txt(220, 0, T('fishing allowed', 'лов разрешён'), 'red')])
# ---------------------------------------------------------------- 5: overtaking, her sternlight arc
c5 = dict(x=0, z=0); y5 = at(0, 0, 165, 230)
wedge = [[0, 0]] + [[round(330 * math.sin(math.radians(a)), 1), round(-330 * math.cos(math.radians(a)), 1)] for a in range(158, 294, 9)] + [[0, 0]]
PL[5] = sch(T('Overtaking (Rule 13) · abaft her beam', 'Обгон (правило 13) · позади её траверза'),
            [T('More than 22.5° abaft her beam: at night only her sternlight shows', 'Более 22,5° позади траверза: ночью виден только кормовой огонь'),
             T('You overtake: keep clear until finally past and clear', 'Вы обгоняете: уступайте, пока окончательно не пройдёте'),
             ], padPx=70,
            zones=[dict(pts=wedge, c='course', fill='rgba(255,200,0,.12)')],
            boats=[boat(0, 0, 45, T('Coaster', 'Каботажное судно'), scale=3.4, noHeading=False), you(y5['x'], y5['z'], 20)],
            paths=[line((0, 0), xz(y5))],
            texts=[txt(y5['x'] + 140, y5['z'] - 60, T('120° from her bow', '120° от её носа'), 'accent'), txt(-210, 150, T('her sternlight arc', 'сектор кормового огня'))],
            fit=[dict(x=-340, z=-160), dict(x=340, z=340)])
# ---------------------------------------------------------------- 6: Rule 17
s6 = at(0, 0, -45, 400)
PL[6] = sch(T('Rule 17 · the stand-on vessel', 'Правило 17 · судно, сохраняющее курс'),
            [T('(a) Keep your course and speed; (a)(ii) you may act once she plainly does not', '(a) Сохраняйте курс и скорость; (a)(ii) можно действовать, если она явно не уступает'),
             T('(c) Power-driven: no turn to port for a vessel on your own port side', '(c) Судно с двигателем: не поворачивать влево для судна слева')],
            boats=[you(0, 0, 0, noHeading=False), boat(s6['x'], s6['z'], 80, T('Ship', 'Судно'), scale=3.4, noHeading=False, tag=T('she gives way', 'она уступает'))],
            paths=[turn([(0, -60), (40, -130), (120, -160)]), turn([(0, -60), (-40, -130), (-110, -160)], 'red')],
            texts=[txt(200, -200, T('to starboard', 'вправо'), 'accent'), txt(-150, -20, T('not to port', 'не влево'), 'red')],
            fit=[dict(x=-300, z=120), dict(x=300, z=-320)])
# ---------------------------------------------------------------- 11: fog, overtaking a target
t11 = at(0, 0, 15, 700)
PL[11] = sch(T('Restricted visibility (Rule 19) · overtaking a target', 'Ограниченная видимость (правило 19) · обгон цели'),
             [T('Forward of the beam, not in sight: avoid a turn to port, unless overtaking her', 'Цель впереди траверза, не видна: не поворачивать влево, если только не обгоняете её'),
              T('Overtaking her: a turn to port is allowed; or slow right down', 'При обгоне поворот влево допустим; или резко сбавьте ход')],
             boats=[you(0, 0, 0), boat(t11['x'], t11['z'], 0, T('Radar target', 'Цель на радаре'), scale=3.0, noHeading=False)],
             paths=[line((0, 0), xz(t11)), turn([(0, -60), (-40, -180), (-130, -300)])],
             texts=[txt(-250, -260, T('turn to port: allowed', 'влево: допустимо'), 'accent'), txt(t11['x'] + 300, t11['z'] + 250, T('015° · same course, slower', '015° · тем же курсом, медленнее')),
                    txt(260, -60, T('fog', 'туман'), pill=False, size=40)],
             fit=[dict(x=-350, z=120), dict(x=400, z=-760)])
# ---------------------------------------------------------------- 12: fog signals as a strip of sound
def fogsig():
    rows = [(T('Power, making way', 'С двигателем, на ходу'), [('L', 0)], T('every 2 min', 'каждые 2 мин')),
            (T('Power, stopped', 'С двигателем, без хода'), [('L', 0), ('L', 1)], T('every 2 min', 'каждые 2 мин')),
            (T('NUC, RAM, sail, fishing, towing', 'НУ, ОМ, парус, лов, буксир'), [('L', 0), ('S', 1), ('S', 1.6)], T('every 2 min', 'каждые 2 мин')),
            (T('At anchor', 'На якоре'), [('B', 0)], T('bell 5 s each minute · 100 m+: gong aft', 'колокол 5 с каждую минуту · от 100 м: гонг в корме')),
            (T('Aground', 'На мели'), [('K', 0), ('K', 0.25), ('K', 0.5), ('B', 0.9), ('K', 2.4), ('K', 2.65), ('K', 2.9)], T('3 strokes, the bell, 3 strokes', '3 удара, колокол, 3 удара'))]
    b = ''; x0 = 560; u = 150
    for i, (lab, sig, note) in enumerate(rows):
        y = 70 + i * 104
        b += stxt(40, y + 10, lab, 28, 700, 'var(--ink)', 'start') + stxt(40, y + 44, note, 22, 400, 'var(--ink)', 'start')
        b += f'<rect x="{x0 - 20}" y="{y - 26}" width="680" height="64" rx="12" fill="#141b26"/>'
        for kind, t in sig:
            x = x0 + t * u
            if kind == 'L': b += f'<rect x="{x}" y="{y - 10}" width="{u * 0.8:.0f}" height="30" rx="8" fill="var(--accent)"/>'
            elif kind == 'S': b += f'<rect x="{x}" y="{y - 10}" width="{u * 0.18:.0f}" height="30" rx="8" fill="var(--accent)"/>'
            elif kind == 'K': b += f'<rect x="{x}" y="{y - 14}" width="10" height="38" rx="4" fill="#ffa800"/>'
            else:
                pts = ' '.join(f'{x + k * 8:.0f},{y + (-14 if k % 2 else 22)}' for k in range(int(u * 1.3 / 8)))
                b += f'<polyline points="{pts}" fill="none" stroke="#ffa800" stroke-width="4"/>'
    b += pill(x0 + 90, 600, T('prolonged: 4–6 s', 'продолжительный: 4–6 с'), 'accent') + pill(x0 + 420, 600, T('short: about 1 s', 'короткий: около 1 с'))
    return frame(T('Fog signals (Rule 35)', 'Сигналы в тумане (правило 35)'),
                 [T('From 20 m you carry a bell; at anchor add short, prolonged, short to warn', 'От 20 м обязателен колокол; на якоре можно добавить короткий, продолжительный, короткий')], b, 'yof-col-12')
PL[12] = fogsig()
# ---------------------------------------------------------------- 13: ship 40° on her port bow, at night
y13 = at(0, 0, 120, 820)
PL[13] = sch(T('Lights · 40° on her port bow', 'Огни · 40° слева по её носу'),
             [T('Inside her masthead arc and her red sector: two masthead lights and red', 'В секторе топовых огней и красного: два топовых и красный'),
              T('Forward masthead low, after one high: she heads to your left, closing', 'Передний топовый ниже, задний выше: она идёт влево от вас, сближаясь')],
             night=True, boats=[boat(0, 0, 160, T('Ship 120 m', 'Судно 120 м'), power=True, scale=3.6, labelAbove=True), you(y13['x'], y13['z'], 0)],
             paths=[line((0, 0), xz(y13))], texts=[txt(y13['x'] - 60, y13['z'] - 110, T('you: 40° on her port bow', 'вы: 40° слева по её носу'), 'accent')],
             fit=[dict(x=-300, z=-250), dict(x=900, z=560)])
# ---------------------------------------------------------------- 14: Annex I heights, a ship in profile
def annex1():
    b = '<line x1="40" y1="500" x2="1240" y2="500" stroke="#3c8cbe" stroke-width="4"/>'
    b += '<path d="M150 440 L1110 440 L1090 520 L230 530 L130 450 Z" fill="var(--ink)"/>'
    b += '<rect x="950" y="320" width="130" height="120" fill="var(--ink)"/><line x1="260" y1="440" x2="260" y2="250" stroke="var(--ink)" stroke-width="7"/><line x1="1010" y1="320" x2="1010" y2="160" stroke="var(--ink)" stroke-width="7"/>'
    b += glow(260, 250, 'w') + glow(1010, 160, 'w') + glow(1010, 110, 'w', 11) + glow(1060, 380, 'r')
    b += dim(200, 440, 200, 250, T('≥ 6 m, or her breadth', '≥ 6 м или её ширина'))
    b += dim(1140, 250, 1140, 160, T('4.5 m+ higher', 'выше на 4,5 м+'))
    b += dim(1180, 440, 1180, 380, T('≤ ¾', '≤ ¾'))
    b += dim(260, 590, 1010, 590, T('at least half her length apart', 'не менее половины длины'))
    b += pill(420, 200, T('forward masthead light: 6 M', 'передний топовый: 6 миль'), 'light') + pill(770, 110, T('manoeuvring light, 2 m+ apart: 5 M', 'маневроуказательный огонь, 2 м+: 5 миль'), 'accent')
    b += pill(880, 470, T('sidelight: 3 M', 'бортовой: 3 мили'), 'red')
    b += f'<line x1="260" y1="250" x2="1010" y2="250" stroke="var(--line)" stroke-width="3" stroke-dasharray="8 8"/>'
    return frame(T('Annex I · lights on a ship of 50 m or more', 'Приложение I · огни судна 50 м и более'),
                 [T('From 20 m: masthead 5 M (6 M from 50 m), the others 2 M (3 M from 50 m)', 'От 20 м: топовый 5 миль (от 50 м — 6), прочие 2 мили (от 50 м — 3)'),
                  T('Lights in a vertical line: 2 m apart, the lowest at least 4 m above the hull', 'Огни по вертикали: через 2 м, нижний не ниже 4 м над корпусом')], b, 'yof-col-14')
PL[14] = annex1()
# ---------------------------------------------------------------- 15: day shapes and their sizes
def shapes():
    k = 300  # px per metre
    b = ''; y0 = 380
    def ball(x): return f'<circle cx="{x}" cy="{y0}" r="{0.3 * k}" fill="var(--ink)"/>'
    def cone(x, up=True):
        a, c = (y0 - 0.3 * k, y0 + 0.3 * k) if up else (y0 + 0.3 * k, y0 - 0.3 * k)
        return f'<path d="M{x} {a} L{x + 0.3 * k} {c} L{x - 0.3 * k} {c} Z" fill="var(--ink)"/>'
    def cyl(x): return f'<rect x="{x - 0.3 * k}" y="{y0 - 0.6 * k}" width="{0.6 * k}" height="{1.2 * k}" fill="var(--ink)"/>'
    xs = [220, 560, 900]
    b += ball(xs[0]) + cone(xs[1]) + cyl(xs[2])
    b += dim(xs[0] - 0.3 * k, y0 + 0.3 * k + 50, xs[0] + 0.3 * k, y0 + 0.3 * k + 50, T('0.6 m+', '0,6 м+'))
    b += dim(xs[1] - 0.3 * k, y0 + 0.3 * k + 50, xs[1] + 0.3 * k, y0 + 0.3 * k + 50, T('base 0.6 m', 'основание 0,6 м')) + dim(xs[1] + 0.3 * k + 50, y0 - 0.3 * k, xs[1] + 0.3 * k + 50, y0 + 0.3 * k, T('0.6 m', '0,6 м'))
    b += dim(xs[2] + 0.3 * k + 50, y0 - 0.6 * k, xs[2] + 0.3 * k + 50, y0 + 0.6 * k, T('1.2 m', '1,2 м')) + dim(xs[2] - 0.3 * k, y0 + 0.6 * k + 40, xs[2] + 0.3 * k, y0 + 0.6 * k + 40, T('0.6 m', '0,6 м'))
    b += stxt(xs[0], 120, T('ball', 'шар'), 30, 700, 'var(--ink)') + stxt(xs[1], 120, T('cone', 'конус'), 30, 700, 'var(--ink)') + stxt(xs[2], 120, T('cylinder', 'цилиндр'), 30, 700, 'var(--ink)')
    return frame(T('Day shapes from 20 m (Annex I, 6)', 'Знаки от 20 м (приложение I, 6)'),
                 [T('Black; shapes in a line at least 1.5 m apart; a diamond is two cones base to base', 'Чёрные; знаки по вертикали не ближе 1,5 м; ромб — два конуса основаниями'),
                  T('Under 20 m they may be smaller, in proportion to her size', 'До 20 м могут быть меньше, соразмерно судну')], b, 'yof-col-15')
PL[15] = shapes()
# ---------------------------------------------------------------- the lights tiles: her arcs, the lights that show all round, where we are
def tile(title, key, label, R, d=450, hdg=0, stack=(), power=True, night=True, extra=None, scale=3.4, yt=None, stackDx=None):
    y = at(0, 0, hdg + R, d)
    b = [boat(0, 0, hdg, label, power=power, scale=scale, stackDx=stackDx if stackDx is not None else (-150 if R >= 0 else 150), labelAbove=abs(R) >= 90),
         you(y['x'], y['z'], (hdg + R + 180) % 360, tag=yt or T('you', 'вы'), scale=2.2)]
    xs, zs = [0, y['x']], [0, y['z']]
    if stack: b[0]['stack'] = list(stack)
    s = sch(title, key, night=night, padPx=70, boats=b, paths=[line((0, 0), xz(y))], texts=[],
            fit=[dict(x=min(xs) - 220, z=min(zs) - 200), dict(x=max(xs) + 220, z=max(zs) + 170)])
    if extra: extra(s['sch'])
    return s
PL[7] = tile(T('Pilot vessel on duty · Rule 29', 'Лоцманское судно при исполнении · правило 29'),
             [T('White over red, all round, at or near the masthead', 'Белый над красным, круговые, на топе или рядом'),
              T('Under way: sidelights and sternlight too · at anchor: anchor lights', 'На ходу ещё бортовые и кормовой · на якоре — якорные')],
             T('Pilot', 'Лоцман'), -55, stack='wr', power=False, yt=T('you: on her port bow', 'вы: слева по её носу'))
PL[8] = tile(T('Sailing vessel of 20 m or more · Rule 25', 'Парусное судно от 20 м · правило 25'),
             [T('Sidelights and sternlight apart: no tricolour from 20 m', 'Бортовые и кормовой раздельно: от 20 м без трёхцветного'),
              T('Red over green at the masthead: optional, never with the engine driving', 'Красный над зелёным на топе: по желанию, но не под мотором')],
             T('Sail', 'Парусное'), 58, stack='rg', power=False, yt=T('you: on her starboard bow', 'вы: справа по её носу'))
PL[9] = tile(T('Air-cushion vessel · Rule 23(b)', 'Судно на воздушной подушке · правило 23(b)'),
             [T('Power-driven lights: masthead light, sidelights, sternlight', 'Огни судна с двигателем: топовый, бортовые, кормовой'),
              T('On the cushion, in addition: an all-round flashing yellow', 'На подушке дополнительно: круговой проблесковый жёлтый')],
             T('Hovercraft', 'Судно на ВП'), 0, stack='y', yt=T('you: dead ahead', 'вы: прямо по носу'))
PL[10] = tile(T('WIG craft · Rule 23(c)', 'Экраноплан · правило 23(c)'),
              [T('Taking off, landing, or in flight near the surface:', 'При взлёте, посадке и полёте у поверхности:'),
               T('power-driven lights, and a high-intensity all-round flashing red', 'огни судна с двигателем и яркий круговой проблесковый красный')],
              T('WIG craft', 'Экраноплан'), -80, stack='r', yt=T('you: on her port beam', 'вы: на её левом траверзе'))
PL[16] = tile(T('Not under command · Rule 27(a)', 'Лишено управления · правило 27(a)'),
              [T('Two all-round reds in a vertical line; by day two balls', 'Два круговых красных по вертикали; днём два шара'),
               T('Making way through the water: sidelights and sternlight too, no masthead light', 'Имея ход относительно воды: ещё бортовые и кормовой, без топового')],
              T('Not under command', 'Лишено управления'), 180, stack='rr', power=False, yt=T('you: astern', 'вы: за кормой'))
def dredger_extra(s):
    s['circles'] = [dict(x=40, z=10, r=16, fill='#e0251b', c='ink', dash='0'), dict(x=-40, z=10, r=16, fill='#1aa34a', c='ink', dash='0')]
    s['zones'] = [dict(pts=[[60, -60], [300, -60], [300, 120], [60, 120]], c='red', fill='rgba(224,37,27,.10)')]
    s['texts'] += [txt(190, -110, T('obstruction', 'препятствие'), 'red'), txt(-250, -110, T('pass this side', 'проходить здесь'), 'accent')]
PL[17] = tile(T('Dredger at work · Rule 27(d)', 'Земснаряд за работой · правило 27(d)'),
              [T('Red, white, red: restricted · two reds: the side that is blocked', 'Красный-белый-красный: ограничено · два красных: сторона с препятствием'),
               T('Two greens: the side to pass · stopped, she shows no sidelights', 'Два зелёных: сторона прохода · без хода бортовых нет')],
              T('Dredger', 'Земснаряд'), 0, stack='rwr', night=False, extra=dredger_extra, stackDx=-110, yt=T('you: ahead', 'вы: впереди'))
def tow_extra(s):
    s['boats'].append(boat(0, 300, 0, T('Tow', 'Буксируемое'), scale=3.0, power=False))
    s['paths'].append(dict(pts=[[0, 50], [0, 250]], c='ink', w=4))
    s['fit'] = [dict(x=-300, z=-200), dict(x=520, z=640)]
PL[18] = tile(T('Towing, restricted · Rules 24 and 27(c)', 'Буксировка, ограничено · правила 24 и 27(c)'),
              [T('Unable to deviate from her course: red, white, red, with the towing lights', 'Не может отклониться от курса: красный-белый-красный и огни буксировки'),
               T('From astern: the yellow towing light over her sternlight', 'С кормы: жёлтый буксировочный над кормовым')],
              T('Tug', 'Буксировщик'), 150, d=560, stack='rwr', extra=tow_extra, scale=3.0, yt=T('you: on her quarter', 'вы: на её раковине'))
def warps(s):
    s['paths'] += [dict(pts=[[-8, 30], [-60, 200]], c='ink', w=3, dash='8 8'), dict(pts=[[8, 30], [60, 200]], c='ink', w=3, dash='8 8')]
    s['texts'].append(txt(0, 240, T('the trawl', 'трал'), pill=False))
PL[19] = tile(T('Trawler hauling her nets · Annex II', 'Траулер выбирает сети · приложение II'),
              [T('Trawling: green over white; stopped, no sidelights', 'Траление: зелёный над белым; без хода — без бортовых'),
               T('Fishing in company, hauling: white over red, lower down', 'Лов рядом с другими, выборка: белый над красным, ниже')],
              T('Trawler', 'Траулер'), 90, stack='gwwr', night=False, extra=warps, yt=T('you: on her beam', 'вы: на её траверзе'))
def seine(s):
    s['circles'] = [dict(x=-30, z=-110, r=110, c='course')]
    s['texts'].append(txt(-30, -250, T('the purse seine', 'кошельковый невод'), pill=False))
PL[20] = tile(T('Purse seiner · Annex II', 'Кошельковый сейнер · приложение II'),
              [T('Fishing, not trawling: red over white', 'Лов, не траление: красный над белым'),
               T('Hampered by her gear: two yellows, flashing alternately', 'Стеснена орудиями лова: два жёлтых, мигающих поочерёдно')],
              T('Purse seiner', 'Сейнер'), -90, stack='rwyy', night=False, extra=seine, yt=T('you: on her beam', 'вы: на её траверзе'))
def reef(s):
    s['zones'] = [dict(pts=[[-130, -70], [60, -110], [140, -10], [90, 80], [-80, 90], [-150, 20]], c='red', fill='rgba(224,37,27,.08)')]
    s['rocks'] = [dict(x=-90, z=40), dict(x=90, z=-60)]
PL[21] = tile(T('Aground · Rule 30(d)', 'На мели · правило 30(d)'),
              [T('Under 50 m: one anchor light and two all-round reds', 'До 50 м: один якорный огонь и два круговых красных'),
               T('By day: three balls in a vertical line', 'Днём: три шара по вертикали')],
              T('Aground', 'На мели'), 90, stack='rr', night=False, extra=reef, yt=T('you: keep well off', 'вы: держитесь подальше'))
PL[22] = sch(T('Pair trawlers · Annex II', 'Парное траление · приложение II'),
             [T('By night each may direct a searchlight forward and towards the other', 'Ночью каждый может светить прожектором вперёд и в сторону другого'),
              T('Their net lies between and astern of them: never pass between', 'Их трал между ними и за кормой: никогда не проходите между ними')],
             night=True, padPx=70,
             boats=[boat(-200, 0, 0, T('Trawler', 'Траулер'), stack=['g', 'w'], stackDx=-110, scale=2.0, power=True), boat(200, 0, 0, T('Trawler', 'Траулер'), stack=['g', 'w'], stackDx=110, scale=2.0, power=True), you(0, -560, 180, scale=2.0)],
             zones=[dict(pts=[[-190, 60], [190, 60], [30, 420], [-30, 420]], c='red', fill='rgba(224,37,27,.10)')],
             paths=[dict(pts=[[-190, -80], [-50, -330]], c='course', w=10), dict(pts=[[190, -80], [50, -330]], c='course', w=10),
                    dict(pts=[[-190, 60], [-30, 420]], c='ink', w=3, dash='8 8'), dict(pts=[[190, 60], [30, 420]], c='ink', w=3, dash='8 8')],
             texts=[txt(0, 370, T('never between', 'никогда между ними'), 'red'), txt(0, -380, T('searchlights', 'прожекторы'))],
             fit=[dict(x=-420, z=-640), dict(x=420, z=440)])
def turning(s):
    s['paths'].append(turn([(0, -110), (40, -240), (140, -320)]))
    s['texts'] += [txt(300, -330, T('altering to starboard', 'поворот вправо'), 'accent'), txt(0, 200, T('one flash, one short blast', 'одна вспышка, один короткий'), 'red')]
    s['fit'] = [dict(x=-450, z=-480), dict(x=450, z=260)]
PL[23] = tile(T('Manoeuvring light · Rule 34(b)', 'Маневроуказательный огонь · правило 34(b)'),
              [T('One short blast, and one flash: I am altering my course to starboard', 'Один короткий и одна вспышка: изменяю курс вправо'),
               T('All-round white, 5 M, at least 2 m above or below the after masthead light', 'Круговой белый, 5 миль, не ближе 2 м от заднего топового')],
              T('Ship', 'Судно'), -38, d=480, extra=turning, scale=3.6, yt=T('you: on her port bow', 'вы: слева по её носу'))

for n, p in PL.items():
    with open(os.path.join(DIR, f'{n}-plan.json'), 'w') as f: json.dump(p, f, ensure_ascii=False)
RU.update({'You': 'Вы', 'Other': 'Судно'})
with open(os.path.join(DIR, 'ru-plans.json'), 'w') as f: json.dump(RU, f, ensure_ascii=False, indent=1)
print('plans', sorted(PL), 'ru', len(RU))
