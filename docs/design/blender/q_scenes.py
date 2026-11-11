# Test-question images for the figure types "bay", "anchor" and "dayshape" (Bareboat Skipper, Charter Check-in,
# Yachtmaster Offshore; the contract: docs/design/figure-style/questions/<level>/README.md). For one question id it renders <id>/3d.jpg with its
# 3d.labels.json (Blender, common.render) and writes <id>/plan.json and <id>/ru.json; with the system Python and
# --plans it writes only the plans and Russian for every id of the type.
#   blender --background --factory-startup --python docs/design/blender/q_scenes.py -- --type bay --id bs-072 [--samples 128]
#   python3 docs/design/blender/q_scenes.py --type bay --plans
#   --level charter-checkin | yachtmaster-offshore: questions/<level>/<type>.json in, questions/<level>/<id>/ out (default bareboat-skipper)
# What the scenes show (rule 1: never the answer):
#   bay       the figure's 320 x 200 drawing as a high drone view, north up: terrain raised from its `land` path (x east,
#             y south; s metres per drawing unit, per question below), the spots as yellow rings with blue letters, the
#             labels at their places, the wind as a red arrow. Pontoon / quay / seabed questions get their own scenes.
#   anchor    the cut-away at the waterline (as the article's chain figure): depth gauge, the yacht, chain and anchor;
#             when the asked answer is the length of chain the anchor has just reached the bottom (no scope shown).
#   dayshape  the shapes exactly as the data says, on the vessel the question names, nothing that tells her status.
import os, sys, math, json, random, re

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
QDIR = os.path.join(HERE, '..', 'figure-style', 'questions', 'bareboat-skipper')
try:
    import bpy, bmesh
    from mathutils import Vector, Matrix, Euler, noise as mnoise
    import numpy as np
    import common as C, kit as K, kit_world as KW
    BL = True
except ImportError:
    BL = False

ARGV = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
def arg(name, default):
    return type(default)(ARGV[ARGV.index(name) + 1]) if name in ARGV else default
TYPE = arg('--type', 'bay'); QID = arg('--id', ''); SAMPLES = arg('--samples', 128); SCALE = arg('--scale', 100)
LEVEL = arg('--level', 'bareboat-skipper')
QDIR = os.path.join(HERE, '..', 'figure-style', 'questions', LEVEL)

def deg(a): return math.radians(a)
def num(v): return ('%g' % v)

# ===================================================================================================== the data
def entries(t):
    with open(os.path.join(QDIR, f'{t}.json')) as f: return json.load(f)

DEFAULT_LAND = 'M0 0 H320 V60 C 260 70 230 110 200 130 C 170 150 120 140 80 120 C 50 105 20 90 0 100 Z'   # figures.js FIG.bay

def path_polys(d, n=14):
    """An SVG path of M/L/H/V/C/Z (absolute) as polygons in drawing units."""
    toks = re.findall(r'[MLHVCZ]|-?\d*\.?\d+', d)
    polys, cur, cmd, x, y, i = [], None, None, 0.0, 0.0, 0
    v = lambda k: float(toks[k])
    while i < len(toks):
        t = toks[i]
        if t in 'MLHVCZ':
            cmd = None if t == 'Z' else t; i += 1; continue
        if cmd == 'M': x, y = v(i), v(i + 1); i += 2; cur = [(x, y)]; polys.append(cur); cmd = 'L'
        elif cmd == 'L': x, y = v(i), v(i + 1); i += 2; cur.append((x, y))
        elif cmd == 'H': x = v(i); i += 1; cur.append((x, y))
        elif cmd == 'V': y = v(i); i += 1; cur.append((x, y))
        elif cmd == 'C':
            x1, y1, x2, y2, x3, y3 = (v(i + k) for k in range(6)); i += 6
            for k in range(1, n + 1):
                q = k / n; u = 1 - q
                cur.append((u ** 3 * x + 3 * u * u * q * x1 + 3 * u * q * q * x2 + q ** 3 * x3, u ** 3 * y + 3 * u * u * q * y1 + 3 * u * q * q * y2 + q ** 3 * y3))
            x, y = x3, y3
        else: i += 1
    return [p[:-1] if p[0] == p[-1] else p for p in polys]

# ===================================================================================================== per question
# bay: s = metres per drawing unit. kind: land (terrain from the path), pontoon, quay, seabed.
BAY = {
    'bs-065': dict(s=3, relief=75, town=(150, 40, 110), sun=(235, 45)),
    'bs-072': dict(s=3, relief=85, town=(70, 178, 50)),
    'bs-080': dict(kind='pontoon', s=0.16, boats=[dict(label='yacht pinned on', y=100, lines=('bow', 'stern'))]),
    'bs-123': dict(s=3, relief=80, cliff=True, own=(110, 168, 90)),
    'bs-337': dict(s=4, relief=70, beach=30, target=(200, 132), zoom=0.62, wind_at=(150, 178), town=(70, 45, 80), ribs=[(186, 148, 290), (214, 168, 75), (168, 160, 110)], yacht=('Y', 262, 168, 200)),
    'bs-694': dict(s=20, relief=650, noscale=True, sun=(230, 28)),
    'bs-701': dict(s=20, relief=230, noscale=True, sun=(230, 28)),
    'bs-708': dict(s=3, relief=80, dawn=True, yacht=('You', 150, 150, 0)),
    'bs-710': dict(s=5, relief=380, hill_len=200, valley=160, night=True, yacht=('A', 160, 125, 0), elev=40, target=(160, 92), zoom=0.95, wind_at=(255, 160)),
    'bs-713': dict(s=20, relief=320, noscale=True, sun=(230, 28)),
    'bs-726': dict(s=20, relief=230, noscale=True, sun=(230, 28)),
    'bs-730': dict(s=20, relief=230, noscale=True, sun=(230, 28)),
    'bs-736': dict(kind='seabed', s=0.15, noscale=True),
    'bs-748': dict(s=3, relief=120),
    'bs-749': dict(s=3, relief=85, wind_at=(70, 160), yacht=('you, at anchor', 150, 100, 90)),
    'bs-751': dict(s=1.2, relief=30, yacht=('yacht at anchor, 40 m chain out', 160, 118, 0)),
    'bs-755': dict(s=1.2, relief=30),
    'bs-791': dict(kind='quay', s=0.4),
    'bs-803': dict(s=0.5, relief=14, buoy=(160, 104), zoom=0.85, wind_at=(245, 168)),
    'bs-807': dict(kind='pontoon', s=0.16, boats=[dict(label='you, bow blowing off', y=100, off=16, lines=('stern',))]),
    'bs-809': dict(kind='pontoon', s=0.16, boats=[dict(label='you, motoring in', x=150, y=110, hdg=330)]),
    'bs-810': dict(kind='pontoon', s=0.16, boats=[dict(label='you, motoring in', x=150, y=110, hdg=330)]),
    'bs-813': dict(kind='pontoon', s=0.16, boats=[dict(label='yacht close ahead', y=4, lines=('bow', 'stern'), hull='navy'),
                                                   dict(label='you', y=100, lines=('bow', 'stern'))]),
}
# Charter Check-in. kind 'harbour': the drawing's land as quays (flat, walled), houses behind; pontoons (x1, y1, x2, y2,
# width m), moored yachts (x, y, heading), mooring buoys, fuel pumps, all in drawing units. 'land' gives the land path
# when the figure has none (the spots and labels stay where the figure has them). kind 'clear': a clear-water bay seen
# from above, its seabed (weed, sand, rocks) under the spots. quay 'rows': drawing y -> metres off the quay, as the
# figure's own distance labels say. 'ashore': x of the yachts lying to anchors with lines ashore along the north shore.
def _row(y0, y1, step, x, hdg): return [(x, y, hdg) for y in range(y0, y1 + 1, step)]
def _col(x0, x1, step, y, hdg, skip=()): return [(x, y, hdg) for x in range(x0, x1 + 1, step) if not any(a <= x <= b for a, b in skip)]
BAY.update({
    'ci-017': dict(kind='harbour', s=0.6, land='M0 0 H320 V100 H0 Z', pontoons=[(60, 100, 60, 113, 3.0), (145, 100, 145, 172, 2.6)],
                   moored=_row(110, 166, 8, 130, 270) + [(160, y, 90) for y in (112, 120, 128, 152, 160, 168)] + _col(207, 311, 8, 114, 180, skip=((244, 266),)),
                   fuel=[(60, 109)], target=(165, 128), zoom=0.92, elev=60, wind_at=(282, 172)),
    'ci-033': dict(kind='harbour', s=0.8, land='M0 0 H320 V30 H150 V55 H0 Z M150 165 H320 V200 H0 V185 H150 Z',
                   moored=_col(196, 270, 6, 155, 0, skip=((220, 240),)) + _col(10, 130, 6, 175, 0) + [(288, 82, 315)],
                   target=(160, 108), zoom=0.95, elev=60, wind_at=(35, 130)),
    'ci-035': dict(s=3, relief=150, cliff=True, land='M0 0 H320 V150 C 300 150 285 92 240 90 C 205 88 190 150 160 155 C 130 150 120 100 80 98 C 40 96 25 150 0 150 Z',
                   sun=(250, 30), wind_at=(160, 182)),
    'ci-420': dict(kind='harbour', s=0.5, pontoons=[(168, 58, 306, 58, 2.5), (172, 48, 172, 58, 1.6)],
                   moored=_col(184, 282, 9, 76, 180, skip=((205, 225),)) + _row(88, 124, 9, 77, 90) + [(200, 135, 180), (260, 135, 180)],
                   buoys=[(200, 150), (260, 150), (230, 180)], fuel=[(110, 45)], target=(170, 112), zoom=0.95, elev=60, wind_at=(295, 180)),
    'ci-434': dict(kind='quay', s=0.4, rows={72: 15.0, 128: 50.0, 182: 100.0}, plain=True, cam=((26.0, -150.0, 66.0), (2.0, -48.0, 0.0), 30)),
    'ci-441': dict(kind='clear', s=0.16, sun=(170, 60)),
    'ci-448': dict(s=0.8, relief=35, ashore=list(range(45, 206, 8)), target=(160, 100), zoom=0.95, wind_at=(70, 175)),
    'ci-457': dict(kind='harbour', s=0.5, moored=_row(58, 76, 9, 176, 90) + _row(108, 126, 9, 176, 90) + _row(58, 121, 9, 134, 270) + [(262, 150, 315), (205, 182, 315)],
                   fuel=[(30, 68)], target=(160, 115), zoom=0.95, elev=60, wind_at=(285, 186)),
    'ci-458': dict(kind='harbour', s=0.5, moored=_row(52, 88, 9, 166, 90) + _row(112, 130, 9, 166, 90) + _row(52, 133, 9, 124, 270),
                   fuel=[(62, 62)], target=(150, 105), zoom=0.95, elev=60, wind_at=(260, 180)),
})
PONTOON_W = 3.0   # a real pontoon's width: its outer edge on the edge of the drawing's land

# anchor: state 'drop' = the anchor has just reached the bottom (the asked answer is the length of chain);
# 'set' = chain laid out to `chain` metres. labels: which data lines sit at their places in the picture.
ANCHOR = {
    'bs-006': dict(state='set', chain=14, draft=1.9, labels={'Draft 1.9 m': 'draft'}, sea='breeze'),
    'bs-071': dict(state='drop', labels={'Bow roller 1 m above water': 'roller'}, sun=(250, 18)),
    'bs-737': dict(state='set', chain=26, weed=True, labels={}),
    'bs-740': dict(state='drop', labels={'Bow roller 1 m above water': 'roller'}),
    'bs-741': dict(state='drop', rope=6.0, labels={'Bow roller 1 m above water': 'roller', '6 m chain, then nylon rope': 'join'}, kedge=True),
    'bs-742': dict(state='drop', labels={'Bow roller 1 m above water': 'roller'}),
    'bs-743': dict(state='set', chain=30, labels={'Bow roller 1 m above water': 'roller'}),
    'bs-744': dict(state='set', chain=12, labels={'Bow roller 1 m above water': 'roller', 'Chain out: 12 m': 'chain'}),
    'bs-746': dict(state='set', chain=16, draft=1.9, flat=True, labels={'Draught 1.9 m': 'draft'}),
    'bs-761': dict(state='set', chain=28, dusk=True, labels={'Chain jerks at the roller': 'roller'}),
}

ANCHOR.update({
    'ci-407': dict(state='set', chain=30, labels={'Chain held on the gypsy': 'roller'}),
    'ci-411': dict(state='drop', labels={'Bow roller 1 m above water': 'roller'}),
    'ci-435': dict(state='set', chain=30, labels={}),
    'ci-436': dict(state='set', chain=40, taut=True, labels={'Chain bar-tight ahead': 'chain'}),
    'ci-439': dict(state='set', chain=35, dusk=True, labels={}),
})

# Yachtmaster Offshore. bay 'race': (x, y, r) a tide race, broken water round the figure's own 'race' label (drawing
# units); 'haze': a thicker sky haze (fog); 'far': a drawing tens of km across (camera clipping, sea to match). anchor 'deep': the camera stands off far enough to show the bottom in deep
# water, the water clearer; 'motor': a motor yacht of that length instead of our sailing yacht; 'snubber': a nylon
# bridle from both bow cleats to a hook on the chain, before any more chain is let out (labels 'hook', 'cleat').
BAY.update({
    'yof-339': dict(s=33, relief=50, cliff=True, race=(196, 140, 26), wind_at=(282, 60)),
    'yof-341': dict(s=100, far=True, noscale=True, relief=60, cliff=True, race=(196, 140, 26), wind_at=(282, 60)),
    'yof-380': dict(s=100, far=True, noscale=True, relief=45, race=(240, 128, 24), haze=7.0, sun=(200, 25), wind_at=(282, 175)),
    'yof-637': dict(s=200, far=True, relief=1900, cone=9000, noscale=True, sun=(250, 25), elev=40, zoom=0.8, target=(132, 112), wind_at=(270, 30)),
    'yof-690': dict(s=10, relief=120, sun=(230, 38), wind_at=(282, 150)),
    'yof-816': dict(s=8, relief=90, sun=(220, 30), wind_at=(250, 120)),
})
ANCHOR.update({
    'yof-814': dict(state='drop', deep=True, labels={'Bow roller 2 m above water': 'roller'}),
    'yof-823': dict(state='drop', deep=True, motor=24.0, labels={}),
    'yof-870': dict(state='set', chain=40, snubber=True, near=True, labels={'Snubber on a chain hook': 'hook', 'Made fast to both bow cleats': 'cleat'}),
})

# dayshape: the vessel and the view
DAY = {
    'bs-037': dict(vessel='trawler', booms=True, kinds=['cone-down', 'cone-up'], own='sail', brg=22, dist=100, hdg=60),
    'bs-075': dict(vessel='own-anchored', kinds=['ball']),
    'bs-427': dict(vessel='ship', kinds=['ball', 'ball'], own='sail', brg=28, dist=230, hdg=250),
    'bs-428': dict(vessel='trawler', booms=False, kinds=['ball', 'diamond', 'ball'], own='motor', brg=18, dist=95, hdg=100, harbour=True),
    'bs-429': dict(vessel='ship', kinds=['cylinder'], own='sail-port', brg=-24, dist=240, hdg=95, laden=True),
    'bs-432': dict(vessel='own-motorsail', kinds=[]),
    'bs-433': dict(vessel='yacht-motorsail', kinds=['cone-down'], own='sail-port', brg=-30, dist=62, hdg=300),
    'bs-434': dict(vessel='trawler', booms=False, kinds=['ball', 'ball', 'ball'], own='motor', brg=12, dist=110, hdg=235, coast=True),
    'bs-764': dict(vessel='yacht-anchored', kinds=['ball'], own='motor', brg=8, dist=48, hdg=200),
    'bs-820': dict(vessel='own-deck', kinds=['ball']),
    'yof-588': dict(vessel='own-motor-anchored', kinds=['ball'], length=22.0, ball=0.3),
}

# ===================================================================================================== Russian
RU = {
    # bay plans
    'Sea breeze · warm land draws in cool sea air': 'Морской бриз · тёплая суша втягивает прохладный морской воздух',
    'sea breeze': 'морской бриз', 'A sea breeze: it dies away at sunset': 'Это морской бриз: к закату он стихнет',
    'Warm land draws air in from the sea on sunny afternoons': 'В солнечный день тёплая суша втягивает воздух с моря',
    'Anchoring · shelter from the forecast wind': 'Якорная стоянка · укрытие от ветра по прогнозу',
    'Only A lies under the land when the wind goes south': 'Когда задует с юга, берег прикроет только A',
    'Choose shelter from the forecast wind, not the present one': 'Выбирайте укрытие от ветра по прогнозу, а не от нынешнего',
    'Leaving a pontoon you are pinned on · spring the stern out': 'Отход от понтона, к которому прижимает · корму отводим на шпринге',
    'bow spring led aft': 'носовой шпринг, заведён назад', 'stern swings out': 'корму отводит',
    'Bow spring led aft, bow fendered, helm towards the pontoon': 'Носовой шпринг назад, кранец на нос, руль к понтону',
    'Gently ahead: she pivots on the bow, the stern swings out; then astern clear': 'Малый вперёд: яхта поворачивается на носу, корму отводит; затем задним ходом прочь',
    'Lee shore · the wind blows onto it': 'Подветренный берег · ветер дует на него',
    'lee shore: keep well off': 'подветренный берег: держитесь мористее',
    'A lee shore: if the engine or rig fails, the wind drives you onto the rocks': 'Подветренный берег: откажет мотор или рангоут — ветер вынесет на камни',
    'Keep well off it': 'Держитесь от него подальше',
    'Swimming from the yacht · be seen': 'Купание с яхты · чтобы вас видели',
    'bright tow float': 'яркий буксируемый буй', 'swim clear of the tenders': 'плывите в стороне от тендеров',
    'Insist on a bright tow float and a route clear of the tenders': 'Обязательно яркий буй на привязи и маршрут в стороне от тендеров',
    "A swimmer's head is almost invisible from a rib": 'Голову пловца с РИБа почти не видно',
    'Strait between high islands · the wind funnels': 'Пролив между высокими островами · ветер разгоняется',
    'F7 or more, steep seas': '7 баллов и больше, крутая волна',
    'Wind funnels and speeds up between high islands: expect F7 or more': 'Между высокими островами ветер сжимается и усиливается: ждите 7 баллов и больше',
    'Steep seas in the strait: consider waiting': 'В проливе крутая волна: подумайте, не переждать ли',
    'Shelter from the Tramontana': 'Укрытие от трамонтаны', 'B: in the lee of the island': 'B: под защитой острова',
    'The Tramontana is a northerly: shelter on the south side of the island': 'Трамонтана дует с севера: укрывайтесь у южного берега острова',
    'Land breeze · night air drains off the land': 'Береговой бриз · ночной воздух стекает с суши',
    'land breeze': 'береговой бриз', 'A land breeze: it fades after sunrise': 'Это береговой бриз: после восхода он стихнет',
    'At night the land cools below the sea and air drains offshore': 'Ночью суша остывает сильнее моря, и воздух стекает в море',
    'Katabatic wind · cold air pours down the valley': 'Катабатический ветер · холодный воздух скатывается по долине',
    'katabatic gusts': 'катабатические порывы',
    'On clear nights cold air drains down valleys and bursts out of their mouths': 'Ясной ночью холодный воздух стекает по долинам и вырывается из их устья',
    'Next time anchor away from the valley mouth': 'В следующий раз вставайте подальше от устья долины',
    'Fetch · the sea grows with the distance': 'Разгон · волна растёт с расстоянием',
    'short fetch: small sea': 'короткий разгон: волна мала', 'long fetch: bigger sea': 'длинный разгон: волна больше',
    'Waves grow with the distance the wind blows over open water': 'Волна растёт с расстоянием, которое ветер проходит над открытой водой',
    'A, near the windward shore, has the smallest sea': 'У A, под наветренным берегом, волна меньше всего',
    'The swell decides the night': 'Ночь решает зыбь', 'SW swell': 'зыбь с ЮЗ', 'B: hidden from the swell': 'B: укрыта от зыби',
    'B, on the north-east side, is tucked away from the SW swell': 'B, на северо-восточной стороне, укрыта от зыби с ЮЗ',
    'Swell can make an anchorage untenable even in light wind': 'Зыбь может сделать стоянку невыносимой даже в слабый ветер',
    'Shelter now and after the shift': 'Укрытие сейчас и после смены ветра', 'NW now': 'сейчас СЗ', 'SW after midnight': 'после полуночи ЮЗ',
    'B: in the lee of both': 'B: укрыта от обоих',
    'NW now, SW later: only B, on the east side, is sheltered from both': 'Сейчас СЗ, потом ЮЗ: от обоих укрыта только B, на восточной стороне',
    'Choose shelter for the wind you will have overnight': 'Выбирайте укрытие от ветра, который будет ночью',
    'Shelter from the swell': 'Укрытие от зыби', 'A: behind the headland': 'A: за мысом',
    'The headland blocks the SW swell at A': 'Мыс закрывает A от зыби с ЮЗ', 'Swell, not just wind, decides comfort': 'Покой на стоянке решает не только ветер, но и зыбь',
    'A bay open to the forecast wind': 'Бухта, открытая ветру по прогнозу', 'W F6 after midnight': 'после полуночи З, 6 баллов',
    'lee shore tonight': 'ночью подветренный берег',
    'With a westerly this shore becomes a lee shore': 'При западном ветре этот берег станет подветренным',
    'Leave before dark for a bay sheltered from the west': 'Уходите засветло в бухту, укрытую от запада',
    'Swinging room · keep the circles apart': 'Место для разворота · круги не должны пересекаться',
    'her anchor': 'её якорь', 'her chain': 'её цепь', 'C: both circles clear': 'C: круги не пересекаются',
    'A lies over her chain; from B the swinging circles overlap': 'A — над её цепью; у B круги разворота пересекаются',
    "Never drop over another boat's chain; keep both swinging circles apart": 'Не отдавайте якорь над чужой цепью; круги разворота не должны пересекаться',
    'Anchoring · the final approach': 'Постановка на якорь · последний подход', 'slowly, head to wind': 'медленно, носом на ветер',
    'Approach slowly head to wind and stop over the spot': 'Подходите медленно носом на ветер и остановитесь над точкой',
    'Head to wind you stop where you want and fall back in line': 'Носом на ветер вы встанете точно и спуститесь назад по линии ветра',
    'Mediterranean mooring · wind on the beam': 'Швартовка по-средиземноморски · боковой ветер', 'drop upwind': 'якорь на ветер',
    'From B, upwind, the chain holds the bow up to windward': 'Из точки B, с наветра, цепь удерживает нос на ветре',
    'your berth': 'ваше место', 'QUAY': 'ПРИЧАЛ',
    'Picking up a mooring buoy · into the wind': 'Подход к бую · против ветра', 'motor slowly up into the wind': 'медленно под мотором против ветра',
    'From A you motor slowly up into the wind to the buoy': 'Из A вы медленно идёте под мотором против ветра к бую',
    'Into the wind you can stop beside it': 'Против ветра можно остановиться рядом с ним',
    'Alongside · a bow breast line': 'Лагом · носовой прижимной', 'bow breast line': 'носовой прижимной',
    'A bow breast line, square to the pontoon, pulls the bow in': 'Носовой прижимной, под прямым углом к понтону, подтягивает нос',
    'Breast lines pull her in; springs stop the surge': 'Прижимные подтягивают яхту, шпринги гасят рывки',
    'Coming alongside · wind off the berth': 'Подход лагом · ветер с причала', 'steeper angle, line ashore fast': 'круче к понтону, быстро подать конец',
    'Wind off the berth blows you away: aim in at a steeper angle': 'Ветер с причала отжимает: подходите под более крутым углом',
    'Get a line ashore quickly': 'Быстро подайте конец на понтон',
    'Coming alongside · wind onto the berth': 'Подход лагом · ветер на причал', 'stop parallel, 1 m off': 'остановиться параллельно, в 1 м',
    'Stop parallel to the pontoon, a metre off': 'Остановитесь параллельно понтону, в метре от него',
    'Let the wind push you in, well fendered': 'Пусть ветер прижмёт вас; кранцы вывешены',
    'Springing off · stern out, leave astern': 'Отход на шпринге · корму отвести, уйти задним ходом',
    'Rig a bow spring led aft and fender the bow': 'Заведите носовой шпринг назад и вывесьте кранец на нос',
    'Gently ahead: she pivots on the bow, the stern swings out clear of the yacht ahead': 'Малый вперёд: яхта поворачивается на носу, корма отходит от понтона',
    'you': 'вы', 'Seabed · sand or seagrass': 'Грунт · песок или посидония', 'drop on the sand': 'якорь на песок',
    'B: on the sand, clear of the seagrass': 'B: на песке, в стороне от посидонии',
    'Posidonia seagrass is protected and holds poorly; anchor on sand': 'Посидония охраняется и плохо держит; отдавайте якорь на песок',
    'seagrass': 'посидония', 'sand': 'песок',
    # anchor plans
    'depth': 'глубина', 'Anchoring · depth under the keel': 'Якорная стоянка · вода под килем', 'draft 1.9 m': 'осадка 1,9 м',
    'draught 1.9 m': 'осадка 1,9 м', 'depth 2.4 m': 'глубина 2,4 м', '0.5 m under the keel': '0,5 м под килем',
    'low water': 'малая вода', 'At low water 2.4 m − 1.9 m = 0.5 m under the keel': 'В малую воду 2,4 м − 1,9 м = 0,5 м под килем',
    'Enough to stay, but a 0.3 m swell eats into it': 'Остаться можно, но зыбь 0,3 м съедает часть запаса',
    'Anchoring · how much chain': 'Якорная стоянка · сколько цепи', 'depth 5 m': 'глубина 5 м', 'bow 1 m': 'нос 1 м',
    'chain 24 m': 'цепь 24 м', '(5 m + 1 m) × 4 = 24 m': '(5 м + 1 м) × 4 = 24 м',
    'Measure from the bow roller: depth + bow height': 'Считайте от роульса: глубина + высота носа',
    'Settled weather: at least 4:1; more if wind is expected': 'Тихая погода: не меньше 4:1; ждёте ветра — больше',
    'Anchoring · the anchor is skating': 'Якорная стоянка · якорь ползёт', 'skating on hard sand': 'ползёт по твёрдому песку',
    'chain jerks and rumbles': 'цепь дёргается и грохочет', 'transit opening': 'створ расходится', 'hard sand, weed': 'твёрдый песок, водоросли',
    'A juddering chain and an opening transit: the anchor is not biting': 'Цепь дёргается, створ расходится: якорь не забирает',
    'Lift it and try another spot': 'Выберите его и попробуйте в другом месте',
    'depth 6 m': 'глубина 6 м', 'chain 35 m': 'цепь 35 м', '(6 m + 1 m) × 5 = 35 m': '(6 м + 1 м) × 5 = 35 м',
    'All-chain rode, the bow roller 1 m above the water': 'Только цепь, роульс в 1 м над водой', 'A gusty night: scope 5:1': 'Ночь с порывами: цепь 5:1',
    'Anchoring · a kedge on chain and rope': 'Якорная стоянка · верп на цепи и канате', 'depth 8 m': 'глубина 8 м',
    'rode 63 m': 'всего 63 м', '6 m chain': '6 м цепи', 'nylon rope': 'нейлоновый канат', '(8 m + 1 m) × 7 = 63 m': '(8 м + 1 м) × 7 = 63 м',
    'Chain and rope needs about 6–8:1, measured from the bow roller': 'Цепи с канатом нужно 6–8:1, считая от роульса',
    'Plan 7:1: 9 m × 7 = 63 m of rode in all': 'План 7:1: 9 м × 7 = 63 м всего',
    'Anchoring · use the high-water depth': 'Якорная стоянка · глубина в полную воду', 'chain 28 m': 'цепь 28 м',
    '(5 m + 1 m tide + 1 m) × 4 = 28 m': '(5 м + 1 м прилива + 1 м) × 4 = 28 м',
    '5 m at low water now; the tide will rise 1 m tonight': 'Сейчас малая вода, 5 м; ночью вода поднимется на 1 м',
    'Scope on the high-water depth plus bow height': 'Длину цепи считайте от глубины в полную воду плюс высота носа',
    'Anchoring · is the scope enough?': 'Якорная стоянка · хватит ли цепи?', 'chain 30 m': 'цепь 30 м',
    '30 m ÷ (6 m + 1 m) ≈ 4.3 : 1': '30 м ÷ (6 м + 1 м) ≈ 4,3 : 1', 'Chain out: 30 m, forecast F6 overnight': 'Вытравлено 30 м, ночью 6 баллов',
    'About 4:1 — aim for 5–7:1: let out more if there is room': 'Около 4:1 — нужно 5–7:1: травите ещё, если есть место',
    'Anchoring · too little chain': 'Якорная стоянка · слишком мало цепи', 'chain 12 m': 'цепь 12 м',
    '12 m ÷ (6 m + 1 m) ≈ 1.7 : 1': '12 м ÷ (6 м + 1 м) ≈ 1,7 : 1',
    'The steep chain lifts the shank and pulls the anchor out': 'Крутая цепь поднимает веретено и выдёргивает якорь',
    'An anchor holds only when the pull along the bottom is near horizontal': 'Якорь держит, только когда тяга у дна почти горизонтальна',
    'Anchoring · enough water at low water?': 'Якорная стоянка · хватит ли воды в малую воду?', 'depth 3 m at HW': 'глубина 3 м в ПВ',
    '2.3 m at LW': '2,3 м в МВ', 'falls 0.7 m': 'спадёт на 0,7 м', '0.4 m under the keel': '0,4 м под килем',
    '3 m − 0.7 m = 2.3 m at low water': '3 м − 0,7 м = 2,3 м в малую воду', '2.3 m − 1.9 m draught = 0.4 m under the keel': '2,3 м − 1,9 м осадки = 0,4 м под килем',
    'Anchoring · a snubber takes the shock': 'Якорная стоянка · демпфер гасит рывки', 'nylon snubber': 'нейлоновый демпфер',
    'bow cleat': 'носовая утка', 'chain hook': 'гак на цепи', 'windlass: no load': 'брашпиль без нагрузки', 'slack chain': 'цепь провисает',
    'A nylon snubber from a bow cleat to the chain': 'Нейлоновый демпфер от носовой утки к цепи',
    'It stretches in the gusts and takes the strain off the windlass': 'На порывах он растягивается и снимает нагрузку с брашпиля',
    # dayshape plans
    'Day shapes · fishing': 'Дневные знаки · лов рыбы', 'Fishing': 'Лов рыбы', 'two cones, points together': 'два конуса вершинами вместе',
    'You keep clear: sail gives way to a vessel engaged in fishing': 'Уступаете вы: парусное судно уступает судну, занятому ловом рыбы',
    'Rule 18: sail gives way to fishing, NUC and RAM': 'Правило 18: парусное уступает лову рыбы, лишённому возможности управляться и ограниченному в манёвре',
    'Day shape · at anchor': 'Дневной знак · на якоре', 'black ball forward': 'чёрный шар на носу',
    'One black ball, forward where it is best seen': 'Один чёрный шар в носовой части, где его лучше видно',
    'By day: at anchor; at night an all-round white light': 'Днём — на якоре; ночью — белый круговой огонь',
    'Day shapes · not under command': 'Дневные знаки · лишено возможности управляться', 'Not under command': 'Не управляется', 'two balls': 'два шара',
    'She cannot steer or stop: two black balls': 'Не может ни управляться, ни остановиться: два чёрных шара',
    'Rule 18: sail keeps clear of a vessel not under command': 'Правило 18: парусное уступает судну, лишённому возможности управляться',
    'Day shapes · restricted in ability to manoeuvre': 'Дневные знаки · ограничено в возможности маневрировать', 'Dredger': 'Земснаряд',
    'ball, diamond, ball': 'шар, ромб, шар', 'Her work limits how she moves: ball, diamond, ball': 'Работа ограничивает её манёвр: шар, ромб, шар',
    'Keep clear of her (Rule 18)': 'Уступайте ей (Правило 18)',
    'Day shapes · constrained by her draught': 'Дневные знаки · стеснено своей осадкой', 'Tanker': 'Танкер', 'cylinder': 'цилиндр',
    'Bound to the deep water by her draught: a cylinder': 'Осадка не пускает её с глубокой воды: цилиндр',
    'Keep out of her way: avoid impeding her (Rule 18(d))': 'Держитесь с её пути: не затрудняйте её движение (Правило 18(d))',
    'Day shapes · motor-sailing': 'Дневные знаки · под парусом и мотором', 'cone, point down': 'конус вершиной вниз',
    'Sails up and the engine in gear: you are power-driven': 'Паруса подняты, двигатель на передаче: вы — судно с механическим двигателем',
    'Hoist a cone, point down, forward (Rule 25(e))': 'Поднимите конус вершиной вниз в носовой части (Правило 25(e))',
    'Motor-sailing': 'Под парусом и мотором', 'starboard tack, motoring': 'правый галс, под мотором', 'port tack, sail only': 'левый галс, только паруса',
    'The cone shows she is motor-sailing: a power-driven vessel': 'Конус показывает: она идёт под парусом и мотором — судно с механическим двигателем',
    'She keeps clear of you under sail (Rule 18)': 'Она уступает вам, идущему под парусом (Правило 18)',
    'Day shapes · aground': 'Дневные знаки · на мели', 'Aground': 'На мели', 'three balls': 'три шара', 'shallow water': 'мелководье',
    'Three black balls: she is aground': 'Три чёрных шара: судно на мели', 'Shallow water round her: keep well clear': 'Вокруг мелко: держитесь подальше',
    'Yacht': 'Яхта', 'anchor': 'якорь', 'pass astern': 'проходите за кормой', 'black ball: at anchor': 'чёрный шар: на якоре',
    'A black ball: she is at anchor': 'Чёрный шар: яхта на якоре', 'Her chain runs out ahead: keep clear of her bow': 'Её цепь уходит вперёд: не проходите у неё по носу',
    'Day shape · under way again': 'Дневной знак · снова на ходу', 'ball still up': 'шар ещё поднят', 'lower the ball': 'опустите шар',
    'The ball says you are at anchor': 'Шар говорит, что вы на якоре', 'Take it down as soon as you are under way': 'Спустите его, как только снялись с якоря',
}

RU.update({
    # Charter Check-in bay plans
    'Friday return · fuel first': 'Возврат в пятницу · сначала топливо', '1 · fill up': '1 · заправиться', '2 · berth and report': '2 · встать и доложить',
    'Full to full: fill up at A before you return the boat': 'Полный бак на полный: заправьтесь у A, прежде чем сдавать яхту',
    'Then berth at B and report; the base refuels at fuel + €80': 'Потом встаньте у B и доложите; база заправит по цене топлива + €80',
    'Ferry wash · trust the briefing': 'Волна от парома · верьте брифингу', 'ferry wash': 'волна от парома', 'B: the S quay, clear of the wash': 'B: южный причал, волна не доходит',
    'The briefing names the N quay: the ferry wash throws boats onto it twice a day': 'Брифинг называет северный причал: волна от парома дважды в день бросает на него яхты',
    'Ask for B on the S quay, or anchor at C': 'Попросите место B у южного причала или встаньте на якорь у C',
    'Katabatic gusts · the bay under the cliffs': 'Катабатические порывы · бухта под скалами', 'night gusts to 40 kn': 'ночные порывы до 40 уз', 'B: clear of the cliffs': 'B: вдали от скал',
    'In a northerly, cold air pours off the cliffs after dark: gusts to 40 kn at A': 'При северном ветре после темноты холодный воздух срывается со скал: у A порывы до 40 уз',
    'B, the W bay, lies clear of the cliffs; calm at 18:00 says nothing about 02:00': 'B, западная бухта, вдали от скал; штиль в 18:00 ничего не говорит о 02:00',
    'Return · where and how the base says': 'Возврат · где и как скажет база', 'stern-to on the lazy line': 'кормой, на муринг',
    'B: the base pontoon, stern-to on the lazy line': 'B: понтон базы, кормой, на муринг',
    'Back by 17:00 on Friday: no anchor, on time': 'В пятницу к 17:00: без якоря и без опоздания',
    'Stern-to · where the anchor goes': 'Кормой к причалу · куда отдать якорь', 'drop here, then reverse in': 'отдать здесь и задним ходом к причалу',
    'B: about four boat lengths out, square to the gap': 'B: примерно в четырёх корпусах от причала, напротив места',
    '50 m in 5 m of water: real scope, and chain to spare to reach the quay': '50 м на глубине 5 м: цепи хватает с запасом, и до причала дотянется',
    'Lunch stop · drop on the sand': 'Обед на якоре · отдать на песок', 'B: on the sand': 'B: на песке',
    'B: the pale sand, where the anchor digs in and you can see it': 'B: светлый песок — якорь заглубится, и его видно',
    'Thick weed lets it skid; rock jams it': 'По густой траве якорь ползёт, в камнях заклинивает',
    'weed': 'трава', 'sand': 'песок', 'rocks': 'камни',
    'Lines ashore · do as the others do': 'Концы на берег · как все вокруг', 'drop well out, back in, line ashore': 'якорь подальше, задним ходом, конец на берег',
    'B: drop well out, back in and take a long line ashore': 'B: отдайте якорь подальше, сдайте назад и заведите длинный конец на берег',
    'Boats on lines ashore do not swing: a swinging boat among them hits one': 'Яхты с концами на берег не разворачивает: свободную яхту среди них ударит о соседей',
    'Return · call the base first': 'Возврат · сначала позвоните на базу', 'call the base: VHF or phone': 'вызвать базу: УКВ или телефон',
    'Call the base on the VHF or phone before entering': 'Перед входом вызовите базу по УКВ или телефону',
    'Take the berth they give you: alongside at the base by 18:00': 'Встаньте на место, которое дадут: у причала базы к 18:00',
    'Return · fuel, then the berth': 'Возврат · топливо, потом место', '1 · fill up, keep the receipt': '1 · заправиться, чек сохранить', '2 · your berth': '2 · ваше место',
    'Fuel dock A: fill the tank and keep the receipt': 'Топливный причал A: залейте полный бак и сохраните чек',
    'Then berth B: the base adds €50 if it refuels for you': 'Потом место B: если заправит база, добавят €50',
    # Charter Check-in anchor plans
    'Anchoring · snubber on, windlass off the load': 'Якорная стоянка · снаббер на цепь, брашпиль без нагрузки',
    'Hook the snubber on and take the load to a bow cleat': 'Зацепите снаббер за цепь и переведите нагрузку на носовую утку',
    'Then slacken the chain on the gypsy: the windlass is not a mooring point': 'Затем потравите цепь на звёздочке: брашпиль — не точка крепления',
    'snubber': 'снаббер', 'windlass: no load': 'брашпиль без нагрузки', 'chain hook': 'гак на цепи', 'slack chain': 'цепь провисает', 'bow cleat': 'носовая утка',
    'Anchoring · counting the marks': 'Якорная стоянка · считаем марки', 'chain 30 m': 'цепь 30 м', 'depth 6 m': 'глубина 6 м', 'bow 1 m': 'нос 1 м',
    '(6 m + 1 m) × 4–5 = 28–35 m': '(6 м + 1 м) × 4–5 = 28–35 м',
    'Measure from the bow roller: 6 m + 1 m = 7 m': 'Считайте от роульса: 6 м + 1 м = 7 м',
    '4–5 × 7 m = 28–35 m: three 10 m marks, 30 m': '4–5 × 7 м = 28–35 м: три марки по 10 м, 30 м',
    'Anchoring · set it under power': 'Якорная стоянка · проверить мотором', 'reverse, up to 1,500 rpm': 'задний ход, до 1500 об/мин',
    'transit ashore': 'створ на берегу', 'chain straight and still': 'цепь прямая и не дёргается',
    'Reverse slowly, then build up to about 1,500 rpm': 'Медленно назад, затем добавьте примерно до 1500 об/мин',
    'Watch a transit ashore: if it opens, the anchor is dragging': 'Следите за створом на берегу: если расходится — якорь ползёт',
    'Weighing anchor · motor up to the chain': 'Съёмка с якоря · подойти к цепи на моторе', 'motor slowly ahead': 'малый вперёд',
    'windlass lifts the slack': 'брашпиль выбирает слабину', 'bow points the chain': 'на носу показывают, куда идёт цепь',
    'Motor slowly up towards the anchor: the windlass only lifts the slack': 'Медленно подходите к якорю на моторе: брашпиль выбирает только слабину',
    'The bow shows the helm where the chain leads; the windlass never hauls the boat': 'С носа показывают рулевому, куда идёт цепь; брашпиль яхту не тянет',
    'Anchor alarm · the swinging circle': 'Якорная тревога · круг разворота', 'alarm radius ≈ 55 m': 'радиус тревоги ≈ 55 м', 'chain 35 m': 'цепь 35 м',
    'boat 14 m': 'яхта 14 м', 'GPS': 'GPS', 'drop point': 'точка отдачи',
    'Chain 35 m + boat 14 m (GPS at the stern) ≈ 49 m: set about 55 m': 'Цепь 35 м + яхта 14 м (GPS на корме) ≈ 49 м: ставьте около 55 м',
    'Tighter wakes you all night; wider tells you too late': 'Меньше — будет будить всю ночь; больше — предупредит слишком поздно',
})

RU.update({
    # Yachtmaster Offshore bay plans
    'Portland Bill · the inshore passage': 'Портленд-Билл · прибрежный проход', 'A: a few cables off': 'A: в нескольких кабельтовых',
    'At neaps, in settled weather and at the right time: close in, a few cables off': 'В квадратуру, в устойчивую погоду и в нужное время — у самого берега, в нескольких кабельтовых',
    'Close in you pass the race at its shortest': 'У берега сулой проходится по самому короткому пути',
    "St Alban's Head · wind against a spring stream": 'Сент-Олбанс-Хед · ветер против сизигийного течения', 'C: 4 M off, outside the race': 'C: в 4 милях, вне сулоя',
    'Wind against a spring stream: the race and the inshore passage are rough': 'Ветер против сизигийного течения: в сулое и у берега бурно',
    'Keep well outside, or wait for the stream to turn': 'Держитесь далеко мористее или дождитесь смены течения',
    'Pointe de Barfleur in fog · outside the race': 'Мыс Барфлёр в тумане · мористее сулоя', 'C: 6 M off': 'C: в 6 милях',
    'In fog you can neither see the race nor pilot the inshore passage by eye': 'В тумане не видно ни сулоя, ни ориентиров прибрежного прохода',
    'Pass outside its charted limit and fix often': 'Проходите за его границей по карте и часто определяйтесь',
    'A high island in the trade wind': 'Высокий остров в пассате', 'B: acceleration zone': 'B: зона усиления', 'C, D: wind shadow': 'C, D: ветровая тень',
    'Under the trade inversion the wind goes round the island, not over it': 'Под пассатной инверсией ветер обтекает остров, а не переваливает через него',
    'It speeds up off the ends (B) and drops in the lee': 'У его оконечностей он усиливается (B), а под ветром стихает',
    'Swell wraps round a point': 'Зыбь огибает мыс', 'A: still rolling': 'A: всё равно качает',
    'Swell bends as it feels the bottom and wraps round the point into the bay': 'Зыбь, почувствовав дно, преломляется и заходит за мыс в бухту',
    'At A it is smaller but still rolling — a long swell most of all': 'В A она ниже, но качает — особенно длинная зыбь',
    'Riding out a gale · an open moor': 'Шторм на якоре · два якоря вразнос', 'SW anchor': 'якорь на SW', 'W anchor': 'якорь на W',
    'Two anchors ahead in a V across the expected wind: one SW, one W': 'Два якоря впереди, клином поперёк ожидаемого ветра: один на SW, другой на W',
    'Both share the load as it veers; 180° apart is for a reversing stream': 'Ветер заходит — нагрузку несут оба; на 180° ставят при реверсивном течении',
    # anchor
    'Anchoring · chain and nylon in a gale': 'Якорная стоянка · цепь и нейлон в шторм', '(18 m + 2 m) × 7 = 140 m': '(18 м + 2 м) × 7 = 140 м',
    'Chain and rope at 7:1, measured from the bow roller: 140 m': 'Цепь с тросом 7:1, считая от роульса: 140 м', '140 m − 80 m of chain = 60 m of nylon': '140 м − 80 м цепи = 60 м нейлона',
    'Anchoring in deep water · power it down': 'Якорь на большой глубине · травить брашпилем',
    'A free-falling anchor and chain gather speed the band brake may not hold, and the chain piles up': 'Свободно падающие якорь и цепь разгоняются так, что ленточный тормоз может не удержать, а цепь ложится кучей',
    'Lower it under power all the way to the bottom, then pay out under control': 'Опускайте брашпилем до самого дна, потом травите под контролем',
    'depth 32 m': 'глубина 32 м', 'windlass powers it down': 'брашпиль травит якорь', 'all the way to the bottom': 'до самого дна', 'let go: 32 m of chain runs away': 'отдать: 32 м цепи убегают',
    'Anchoring · the snubber takes the load': 'Якорная стоянка · нагрузку берёт демпфер',
    'Let out chain until it hangs in a slack loop below the hook': 'Травите цепь, пока она не провиснет петлёй ниже гака',
    'Then the snubber stretches; a taut chain sends the shocks to the windlass': 'Тогда тянется демпфер; натянутая цепь передаёт рывки на брашпиль',
    'depth 18 m': 'глубина 18 м', 'bow 2 m': 'нос 2 м', 'chain 140 m': 'цепь 140 м',
    # day shape
    'Day shapes · the size matters': 'Знаки · важен размер', '0.6 m: at least, from 20 m': '0,6 м: минимум, от 20 м', '0.3 m: your ball': '0,3 м: ваш шар',
    'your yacht: 22 m': 'ваша яхта: 22 м', 'Annex I 6: a ball is at least 0.6 m across': 'Приложение I, 6: шар диаметром не менее 0,6 м',
    'Only a vessel under 20 m may use smaller shapes to suit her size': 'Знаки меньше — только для судов короче 20 м, по их размеру',
})

# ===================================================================================================== plans
def P3(s):
    return lambda x, y: [round((x - 160) * s, 2), round((y - 100) * s, 2)]

def bay_plan(e, cfg):
    f = e['figure']; s = cfg.get('s', 3); P = P3(s); kind = cfg.get('kind', 'land')
    if cfg.get('rows'):    # distances off the quay (drawing y 40) as the figure's labels give them
        rows = cfg['rows']; P = lambda x, y: [round((x - 160) * s, 2), round((40 - 100) * s + rows.get(y, (y - 40) * s), 2)]
    def pt(x, y, **o): a = P(x, y); return {'x': a[0], 'z': a[1], **o}
    sch = {'padPx': 40, 'fit': [pt(0, 0), pt(320, 200)] + ([pt(320, max(cfg['rows']) + 12)] if cfg.get('rows') else [])}
    if f.get('wind') is not None: sch['wind'] = f['wind']
    texts, paths, extra = [], [], {}
    data_labels = [(l[0], l[1], l[2]) for l in f.get('labels', [])]
    spots = [sp for sp in f.get('spots', []) if len(sp[2]) == 1 and sp[2] in 'ABCD']
    if kind in ('land', 'seabed', 'harbour', 'clear', 'quay') and (kind != 'quay' or cfg.get('rows')):
        sch['land'] = [[P(x, y) for x, y in poly] for poly in path_polys(f.get('land') or cfg.get('land') or DEFAULT_LAND, 8)]
    if kind == 'harbour' or cfg.get('ashore'):
        boats = [dict(plain=True, x=P(x, y)[0], z=P(x, y)[1], hdg=h, L=14) for x, y, h in cfg.get('moored', [])]
        boats += [dict(plain=True, x=P(x, 45 + 3.75 + 9.1)[0], z=P(x, 45 + 3.75 + 9.1)[1], hdg=180, L=14) for x in cfg.get('ashore', [])]
        if boats: extra_boats = boats
        q = []
        for x1, y1, x2, y2, w in cfg.get('pontoons', []):
            a, b = P(x1, y1), P(x2, y2); hw = w / 2
            q.append({'x1': round(min(a[0], b[0]) - (hw if x1 == x2 else 0), 2), 'z1': round(min(a[1], b[1]) - (hw if y1 == y2 else 0), 2),
                      'x2': round(max(a[0], b[0]) + (hw if x1 == x2 else 0), 2), 'z2': round(max(a[1], b[1]) + (hw if y1 == y2 else 0), 2)})
        if q: sch['quays'] = q
    sch['spots'] = [pt(x, y, label=l) for x, y, l in spots]
    ex = PLAN_BAY.get(e['id'], {})
    for x, y, t in data_labels:
        if t in ex.get('skip', ()): continue
        texts.append(pt(x, y, text=t, pill=False, size=28))
    for x, y, t, k in ex.get('texts', []): texts.append(pt(x, y, text=t, kind=k))
    for pts, c in ex.get('paths', []): paths.append({'pts': [P(*p) for p in pts], 'c': c, 'w': 7, 'arrow': True, **({'dash': '16 12'} if c == 'course' else {})})
    sch.update(title=ex['title'], key=[f['note']] + ex['key'], texts=texts, paths=paths)
    for k in ('boats', 'quays', 'circles', 'anchors', 'zones'):
        if k in ex: sch[k] = ex[k](P) if callable(ex[k]) else ex[k]
    if 'extra_boats' in locals(): sch['boats'] = extra_boats + sch.get('boats', [])
    if ex.get('trueScale'): sch['trueScale'] = True
    out = {'sch': sch}
    if cfg.get('noscale'): out['noScale'] = True
    return out

def pont_quay(s, south=168):
    x1 = round((50 - 160) * s - PONTOON_W, 2); return [{'x1': x1, 'z1': round(-100 * s - 30, 2), 'x2': round((50 - 160) * s, 2), 'z2': round((south - 100) * s, 2)}]

def _alongside(P, y=100, hdg=0, dx=0.0):
    a = P(50, y); return {'x': round(a[0] + 0.35 + 2.25 + dx, 2), 'z': a[1], 'hdg': hdg, 'L': 14}

PLAN_BAY = {
    'bs-065': dict(title='Sea breeze · warm land draws in cool sea air', key=['A sea breeze: it dies away at sunset', 'Warm land draws air in from the sea on sunny afternoons'],
                   texts=[(225, 150, 'sea breeze', 'accent')], paths=[([(160, 185), (160, 90)], 'red')]),
    'bs-072': dict(title='Anchoring · shelter from the forecast wind', key=['Only A lies under the land when the wind goes south', 'Choose shelter from the forecast wind, not the present one']),
    'bs-080': dict(title='Leaving a pontoon you are pinned on · spring the stern out', trueScale=True, skip=('yacht pinned on',),
                   quays=lambda P: pont_quay(0.16, 200), boats=lambda P: [dict(you=True, noHeading=True, **_alongside(P))],
                   texts=[(118, 30, 'bow spring led aft', 'accent'), (170, 175, 'stern swings out', 'light')],
                   paths=[([(53, 62), (47, 128)], 'line'), ([(80, 140), (125, 165)], 'course')],
                   key=['Bow spring led aft, bow fendered, helm towards the pontoon', 'Gently ahead: she pivots on the bow, the stern swings out; then astern clear']),
    'bs-123': dict(title='Lee shore · the wind blows onto it', texts=[(160, 120, 'lee shore: keep well off', 'accent')], paths=[([(20, 178), (300, 178)], 'course')],
                   key=['A lee shore: if the engine or rig fails, the wind drives you onto the rocks', 'Keep well off it']),
    'bs-337': dict(title='Swimming from the yacht · be seen', boats=lambda P: [dict(you=True, noHeading=True, label='Y', x=P(262, 168)[0], z=P(262, 168)[1], hdg=200)],
                   texts=[(282, 112, 'bright tow float', 'accent'), (90, 175, 'swim clear of the tenders', 'light')], paths=[([(262, 155), (290, 128), (262, 92)], 'course')],
                   zones=lambda P: [{'pts': [P(150, 130), P(235, 140), P(240, 178), P(150, 175)], 'c': 'red', 'fill': 'rgba(224,37,27,.08)'}],
                   key=['Insist on a bright tow float and a route clear of the tenders', "A swimmer's head is almost invisible from a rib"]),
    'bs-694': dict(title='Strait between high islands · the wind funnels', texts=[(163, 140, 'F7 or more, steep seas', 'red')], paths=[([(175, 8), (163, 80)], 'red'), ([(160, 118), (140, 192)], 'red')],
                   key=['Wind funnels and speeds up between high islands: expect F7 or more', 'Steep seas in the strait: consider waiting']),
    'bs-701': dict(title='Shelter from the Tramontana', texts=[(160, 190, 'B: in the lee of the island', 'accent')],
                   key=['The Tramontana is a northerly: shelter on the south side of the island']),
    'bs-708': dict(title='Land breeze · night air drains off the land', texts=[(235, 150, 'land breeze', 'accent')], paths=[([(105, 95), (105, 185)], 'red')],
                   boats=lambda P: [dict(you=True, noHeading=True, x=P(150, 150)[0], z=P(150, 150)[1], hdg=0)], skip=(),
                   key=['A land breeze: it fades after sunrise', 'At night the land cools below the sea and air drains offshore']),
    'bs-710': dict(title='Katabatic wind · cold air pours down the valley', texts=[(235, 125, 'katabatic gusts', 'red')], paths=[([(160, 70), (160, 110)], 'red')],
                   key=['On clear nights cold air drains down valleys and bursts out of their mouths', 'Next time anchor away from the valley mouth']),
    'bs-713': dict(title='Fetch · the sea grows with the distance', texts=[(160, 98, 'short fetch: small sea', 'accent'), (160, 122, 'long fetch: bigger sea', 'red')],
                   key=['Waves grow with the distance the wind blows over open water', 'A, near the windward shore, has the smallest sea']),
    'bs-726': dict(title='The swell decides the night', texts=[(40, 185, 'SW swell', 'light'), (255, 15, 'B: hidden from the swell', 'accent')], paths=[([(10, 200), (60, 160)], 'ink'), ([(90, 200), (130, 165)], 'ink')],
                   key=['B, on the north-east side, is tucked away from the SW swell', 'Swell can make an anchorage untenable even in light wind']),
    'bs-730': dict(title='Shelter now and after the shift', texts=[(40, 20, 'NW now', 'red'), (40, 185, 'SW after midnight', 'red'), (272, 120, 'B: in the lee of both', 'accent')],
                   paths=[([(10, 5), (55, 45)], 'red'), ([(10, 200), (55, 160)], 'red')],
                   key=['NW now, SW later: only B, on the east side, is sheltered from both', 'Choose shelter for the wind you will have overnight']),
    'bs-736': dict(title='Seabed · sand or seagrass', texts=[(220, 170, 'drop on the sand', 'accent')],
                   zones=lambda P: [{'pts': [P(40, 60), P(175, 60), P(175, 175), P(40, 175)], 'c': 'ink', 'fill': 'rgba(40,80,30,.25)', 'dash': '0'},
                                    {'pts': [P(190, 90), P(255, 88), P(262, 140), P(195, 145)], 'c': 'course', 'fill': 'rgba(240,220,160,.5)'}],
                   key=['B: on the sand, clear of the seagrass', 'Posidonia seagrass is protected and holds poorly; anchor on sand']),
    'bs-748': dict(title='Shelter from the swell', texts=[(130, 186, 'SW swell', 'light'), (160, 100, 'A: behind the headland', 'accent')],
                   paths=[([(95, 200), (140, 160)], 'ink'), ([(175, 200), (220, 160)], 'ink')],
                   key=['The headland blocks the SW swell at A', 'Swell, not just wind, decides comfort']),
    'bs-749': dict(title='A bay open to the forecast wind', skip=('you, at anchor',), texts=[(70, 60, 'W F6 after midnight', 'red'), (200, 170, 'lee shore tonight', 'accent')], paths=[([(15, 100), (110, 100)], 'red')],
                   boats=lambda P: [dict(you=True, noHeading=True, x=P(150, 100)[0], z=P(150, 100)[1], hdg=90)],
                   key=['With a westerly this shore becomes a lee shore', 'Leave before dark for a bay sheltered from the west']),
    'bs-751': dict(title='Swinging room · keep the circles apart', trueScale=True, skip=('yacht at anchor, 40 m chain out',),
                   boats=lambda P: [dict(plain=True, x=P(160, 118)[0], z=P(160, 118)[1], hdg=0, L=13)],
                   anchors=lambda P: [{'x': P(160, 85)[0], 'z': P(160, 85)[1], 's': 0.7}],
                   circles=lambda P: [{'x': P(160, 85)[0], 'z': P(160, 85)[1], 'r': 50, 'c': 'ink'}, {'x': P(55, 115)[0], 'z': P(55, 115)[1], 'r': 50}],
                   texts=[(205, 68, 'her chain', 'light'), (55, 168, 'C: both circles clear', 'accent')], paths=[([(160, 108), (160, 88)], 'ink')],
                   key=['A lies over her chain; from B the swinging circles overlap', "Never drop over another boat's chain; keep both swinging circles apart"]),
    'bs-755': dict(title='Anchoring · the final approach', trueScale=True, boats=lambda P: [dict(you=True, noHeading=True, x=P(160, 165)[0], z=P(160, 165)[1], hdg=0, L=13)],
                   texts=[(232, 140, 'slowly, head to wind', 'accent')], paths=[([(160, 150), (160, 110)], 'course')],
                   key=['Approach slowly head to wind and stop over the spot', 'Head to wind you stop where you want and fall back in line']),
    'bs-791': dict(title='Mediterranean mooring · wind on the beam', trueScale=True, skip=('your berth',),
                   quays=lambda P: [{'x1': -40, 'z1': -34, 'x2': 40, 'z2': -24}],
                   boats=lambda P: [dict(plain=True, x=x, z=-15.0, hdg=180, L=14) for x in (-25, -20, -15, -10, -5, 5, 10, 15, 20, 25)],
                   texts=[(160, 70, 'your berth', 'accent'), (230, 170, 'drop upwind', 'light')], paths=[([(225, 128), (165, 72)], 'course')],
                   key=['From B, upwind, the chain holds the bow up to windward']),
    'bs-803': dict(title='Picking up a mooring buoy · into the wind', trueScale=True,
                   boats=lambda P: [dict(you=True, noHeading=True, x=P(240, 100)[0] + 16, z=P(240, 100)[1], hdg=270, L=13)],
                   circles=lambda P: [{'x': P(160, 104)[0], 'z': P(160, 104)[1], 'r': 1.0, 'fill': '#f2f1ec', 'c': 'ink', 'dash': '0'}],
                   texts=[(200, 140, 'motor slowly up into the wind', 'accent')], paths=[([(250, 100), (172, 103)], 'course')],
                   key=['From A you motor slowly up into the wind to the buoy', 'Into the wind you can stop beside it']),
    'bs-807': dict(title='Alongside · a bow breast line', trueScale=True, skip=('you, bow blowing off',),
                   quays=lambda P: pont_quay(0.16), boats=lambda P: [dict(you=True, noHeading=True, **_alongside(P, 100, 0))],
                   texts=[(125, 40, 'bow breast line', 'accent')], paths=[([(56, 66), (40, 66)], 'line')],
                   key=['A bow breast line, square to the pontoon, pulls the bow in', 'Breast lines pull her in; springs stop the surge']),
    'bs-809': dict(title='Coming alongside · wind off the berth', trueScale=True, skip=('you, motoring in',),
                   quays=lambda P: pont_quay(0.16), boats=lambda P: [dict(you=True, noHeading=True, x=P(150, 110)[0], z=P(150, 110)[1], hdg=310, L=14)],
                   texts=[(205, 55, 'steeper angle, line ashore fast', 'accent')], paths=[([(140, 95), (72, 40)], 'course')],
                   key=['Wind off the berth blows you away: aim in at a steeper angle', 'Get a line ashore quickly']),
    'bs-810': dict(title='Coming alongside · wind onto the berth', trueScale=True, skip=('you, motoring in',),
                   quays=lambda P: pont_quay(0.16), boats=lambda P: [dict(you=True, noHeading=True, **_alongside(P, 100, 0, 6.0))],
                   texts=[(200, 30, 'stop parallel, 1 m off', 'accent')],
                   key=['Stop parallel to the pontoon, a metre off', 'Let the wind push you in, well fendered']),
    'bs-813': dict(title='Springing off · stern out, leave astern', trueScale=True, skip=('yacht close ahead', 'you'),
                   quays=lambda P: pont_quay(0.16), boats=lambda P: [dict(plain=True, **_alongside(P, 4)), dict(you=True, noHeading=True, **_alongside(P, 100))],
                   texts=[(150, 40, 'bow spring led aft', 'accent'), (170, 180, 'stern swings out', 'light')], paths=[([(53, 62), (47, 128)], 'line'), ([(80, 140), (125, 165)], 'course')],
                   key=['Rig a bow spring led aft and fender the bow', 'Gently ahead: she pivots on the bow, the stern swings out clear of the yacht ahead']),
}

PLAN_BAY.update({
    'ci-017': dict(title='Friday return · fuel first', trueScale=True, texts=[(105, 182, '1 · fill up', 'accent'), (240, 182, '2 · berth and report', 'accent')],
                   paths=[([(110, 198), (66, 128)], 'course'), ([(72, 126), (100, 160), (152, 142)], 'course')],
                   key=['Full to full: fill up at A before you return the boat', 'Then berth at B and report; the base refuels at fuel + €80']),
    'ci-033': dict(title='Ferry wash · trust the briefing', trueScale=True, texts=[(70, 122, 'ferry wash', 'red'), (215, 118, 'B: the S quay, clear of the wash', 'accent')],
                   paths=[([(20, 120), (45, 80)], 'red'), ([(70, 120), (70, 80)], 'red'), ([(120, 120), (95, 80)], 'red')],
                   key=['The briefing names the N quay: the ferry wash throws boats onto it twice a day', 'Ask for B on the S quay, or anchor at C']),
    'ci-035': dict(title='Katabatic gusts · the bay under the cliffs', texts=[(240, 160, 'night gusts to 40 kn', 'red'), (80, 175, 'B: clear of the cliffs', 'accent')],
                   paths=[([(232, 40), (238, 92)], 'red'), ([(262, 45), (250, 94)], 'red')],
                   key=['In a northerly, cold air pours off the cliffs after dark: gusts to 40 kn at A', 'B, the W bay, lies clear of the cliffs; calm at 18:00 says nothing about 02:00']),
    'ci-420': dict(title='Return · where and how the base says', trueScale=True, texts=[(255, 108, 'stern-to on the lazy line', 'accent')],
                   paths=[([(215, 118), (215, 66)], 'course')],
                   key=['B: the base pontoon, stern-to on the lazy line', 'Back by 17:00 on Friday: no anchor, on time']),
    'ci-434': dict(title='Stern-to · where the anchor goes', trueScale=True, skip=(), texts=[(62, 128, 'drop here, then reverse in', 'accent')],
                   boats=lambda P: [dict(plain=True, x=x, z=round(P(160, 40)[1] + 1.6 + 7.3, 2), hdg=180, L=14) for x in (-30, -25, -20, -15, -10, -5, 5, 10, 15, 20, 25, 30)],
                   paths=[([(160, 128), (160, 44)], 'course')],
                   key=['B: about four boat lengths out, square to the gap', '50 m in 5 m of water: real scope, and chain to spare to reach the quay']),
    'ci-441': dict(title='Lunch stop · drop on the sand', skip=(), texts=[(255, 172, 'B: on the sand', 'accent')],
                   zones=lambda P: [{'pts': [P(70, 70), P(150, 70), P(155, 120), P(65, 122)], 'c': 'ink', 'fill': 'rgba(40,80,30,.25)', 'dash': '0'},
                                    {'pts': [P(165, 112), P(240, 110), P(245, 150), P(170, 155)], 'c': 'course', 'fill': 'rgba(240,220,160,.5)'},
                                    {'pts': [P(130, 38), P(195, 36), P(200, 72), P(128, 72)], 'c': 'ink', 'fill': 'rgba(90,90,90,.3)', 'dash': '0'}],
                   key=['B: the pale sand, where the anchor digs in and you can see it', 'Thick weed lets it skid; rock jams it']),
    'ci-448': dict(title='Lines ashore · do as the others do', trueScale=True, texts=[(240, 135, 'drop well out, back in, line ashore', 'accent')],
                   paths=[([(232, 105), (232, 60)], 'course'), ([(232, 52), (234, 40)], 'line')],
                   key=['B: drop well out, back in and take a long line ashore', 'Boats on lines ashore do not swing: a swinging boat among them hits one']),
    'ci-457': dict(title='Return · call the base first', trueScale=True, texts=[(90, 172, 'call the base: VHF or phone', 'accent')],
                   paths=[([(240, 198), (230, 130), (190, 96)], 'course')],
                   key=['Call the base on the VHF or phone before entering', 'Take the berth they give you: alongside at the base by 18:00']),
    'ci-458': dict(title='Return · fuel, then the berth', trueScale=True, texts=[(90, 182, '1 · fill up, keep the receipt', 'accent'), (240, 150, '2 · your berth', 'accent')],
                   paths=[([(220, 195), (160, 160), (70, 96)], 'course'), ([(75, 102), (130, 150), (176, 104)], 'course')],
                   key=['Fuel dock A: fill the tank and keep the receipt', 'Then berth B: the base adds €50 if it refuels for you']),
})

# ---- Yachtmaster Offshore ----
PLAN_BAY.update({
    'yof-339': dict(title='Portland Bill · the inshore passage', texts=[(95, 118, 'A: a few cables off', 'accent')],
                    key=['At neaps, in settled weather and at the right time: close in, a few cables off', 'Close in you pass the race at its shortest'],
                    paths=[([(232, 78), (196, 104), (166, 113), (136, 98), (112, 60)], 'course')]),
    'yof-341': dict(title="St Alban's Head · wind against a spring stream", texts=[(250, 182, 'C: 4 M off, outside the race', 'accent')],
                    key=['Wind against a spring stream: the race and the inshore passage are rough', 'Keep well outside, or wait for the stream to turn'],
                    paths=[([(250, 120), (210, 166), (168, 176), (120, 160), (80, 110)], 'course')]),
    'yof-380': dict(title='Pointe de Barfleur in fog · outside the race', texts=[(290, 160, 'C: 6 M off', 'accent')],
                    key=['In fog you can neither see the race nor pilot the inshore passage by eye', 'Pass outside its charted limit and fix often'],
                    paths=[([(60, 18), (240, 30), (290, 104), (250, 190)], 'course')]),
    'yof-637': dict(title='A high island in the trade wind', texts=[(250, 160, 'B: acceleration zone', 'red'), (60, 120, 'C, D: wind shadow', 'accent')],
                    key=['Under the trade inversion the wind goes round the island, not over it', 'It speeds up off the ends (B) and drops in the lee'],
                    paths=[([(250, 40), (222, 120), (200, 170), (150, 195)], 'red'), ([(130, 8), (80, 40), (50, 90)], 'red')]),
    'yof-690': dict(title='Swell wraps round a point', texts=[(272, 92, 'A: still rolling', 'red')],
                    key=['Swell bends as it feels the bottom and wraps round the point into the bay', 'At A it is smaller but still rolling — a long swell most of all'],
                    paths=[([(20, 110), (110, 140), (172, 168), (215, 128)], 'ink'), ([(20, 160), (120, 185), (200, 175), (232, 120)], 'ink')]),
    'yof-816': dict(title='Riding out a gale · an open moor', texts=[(150, 125, 'SW anchor', 'accent'), (150, 45, 'W anchor', 'accent')],
                    key=['Two anchors ahead in a V across the expected wind: one SW, one W', 'Both share the load as it veers; 180° apart is for a reversing stream'],
                    boats=lambda P: [dict(you=True, noHeading=True, x=P(200, 70)[0], z=P(200, 70)[1], hdg=235, L=14)],
                    anchors=lambda P: [dict(x=P(172, 98)[0], z=P(172, 98)[1], s=0.8), dict(x=P(165, 70)[0], z=P(165, 70)[1], s=0.8)],
                    paths=[([(194, 76), (176, 94)], 'ink'), ([(193, 70), (170, 70)], 'ink')]),
})

def anchor_plan(e, cfg):
    i = e['id']
    if i == 'yof-814': return prof_ci(18, 2, 140, '(18 m + 2 m) × 7 = 140 m', 'Anchoring · chain and nylon in a gale', ['Chain and rope at 7:1, measured from the bow roller: 140 m', '140 m − 80 m of chain = 60 m of nylon'])
    if i == 'yof-823': return {'svg': deep_svg()}
    if i == 'yof-870': return {'svg': snubber_svg('Anchoring · the snubber takes the load', ['Let out chain until it hangs in a slack loop below the hook', 'Then the snubber stretches; a taut chain sends the shocks to the windlass'])}
    if i == 'ci-411': return prof_ci(6, 1, 30, '(6 m + 1 m) × 4–5 = 28–35 m', 'Anchoring · counting the marks', ['Measure from the bow roller: 6 m + 1 m = 7 m', '4–5 × 7 m = 28–35 m: three 10 m marks, 30 m'])
    if i == 'ci-439': return alarm_plan()
    if i == 'ci-407': return {'svg': snubber_svg('Anchoring · snubber on, windlass off the load', ['Hook the snubber on and take the load to a bow cleat', 'Then slacken the chain on the gypsy: the windlass is not a mooring point'], 'snubber')}
    prof = prof_ci
    if i == 'bs-071': return prof(5, 1, 24, '(5 m + 1 m) × 4 = 24 m', 'Anchoring · how much chain', ['Measure from the bow roller: depth + bow height', 'Settled weather: at least 4:1; more if wind is expected'])
    if i == 'bs-740': return prof(6, 1, 35, '(6 m + 1 m) × 5 = 35 m', 'Anchoring · how much chain', ['All-chain rode, the bow roller 1 m above the water', 'A gusty night: scope 5:1'])
    if i == 'bs-742': return prof(6, 1, 28, '(5 m + 1 m tide + 1 m) × 4 = 28 m', 'Anchoring · use the high-water depth', ['5 m at low water now; the tide will rise 1 m tonight', 'Scope on the high-water depth plus bow height'])
    if i == 'bs-743': return prof(6, 1, 30, '30 m ÷ (6 m + 1 m) ≈ 4.3 : 1', 'Anchoring · is the scope enough?', ['Chain out: 30 m, forecast F6 overnight', 'About 4:1 — aim for 5–7:1: let out more if there is room'])
    if i == 'bs-744': return prof(6, 1, 12, '12 m ÷ (6 m + 1 m) ≈ 1.7 : 1', 'Anchoring · too little chain', ['The steep chain lifts the shank and pulls the anchor out', 'An anchor holds only when the pull along the bottom is near horizontal'])
    return {'svg': anchor_svg(i)}

def prof_ci(d, b, c, formula, title, key): return {'profile': {'depth': d, 'bow': b, 'chain': c, 'formula': formula, 'title': title, 'key': key}}

def alarm_plan():
    """ci-439: the anchor alarm's circle round the drop point, the boat lying back on 35 m of chain in an easterly."""
    return {'sch': {'padPx': 70, 'trueScale': True, 'minMpp': 0.05, 'wind': 90, 'title': 'Anchor alarm · the swinging circle',
                    'key': ['Chain 35 m + boat 14 m (GPS at the stern) ≈ 49 m: set about 55 m', 'Tighter wakes you all night; wider tells you too late'],
                    'anchors': [{'x': 0, 'z': 0, 's': 0.8}],
                    'circles': [{'x': 0, 'z': 0, 'r': 55, 'c': 'red'}, {'x': -48.5, 'z': 0, 'r': 1.2, 'fill': 'var(--accent)', 'c': 'ink', 'dash': '0'}],
                    'boats': [{'you': True, 'x': -41.5, 'z': 0, 'hdg': 90, 'L': 14, 'noHeading': True}],
                    'paths': [{'pts': [[-3, 0], [-34.5, 0]], 'c': 'ink', 'w': 5, 'dash': '8 8'}],
                    'texts': [{'x': 0, 'z': -62, 'text': 'alarm radius ≈ 55 m', 'kind': 'red'}, {'x': -17, 'z': -8, 'text': 'chain 35 m'},
                              {'x': -42, 'z': -17, 'text': 'boat 14 m'}, {'x': -63, 'z': 0, 'text': 'GPS', 'kind': 'accent'}, {'x': 16, 'z': 8, 'text': 'drop point'}],
                    'fit': [{'x': -60, 'z': -66}, {'x': 60, 'z': 60}]}}

# ---- hand-drawn side views (the same language as figure-schematic.js) ----
def _t(x, y, s, size=26, w=700, f='var(--muted)', a='middle'):
    s = str(s).replace('&', '&amp;').replace('<', '&lt;')
    return f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" font-weight="{w}" fill="{f}" text-anchor="{a}">{s}</text>'
def _pill(x, y, text, kind='light', size=26):
    w = len(text) * size * 0.58 + size * 1.4; h = size * 1.7
    fill = {'accent': 'var(--accent)', 'red': '#e8231a'}.get(kind, 'var(--bg)'); ink = 'var(--ink)' if kind == 'light' else '#fff'; st = 'var(--tag-line)' if kind == 'light' else fill
    return f'<rect x="{x - w / 2:.1f}" y="{y - h / 2:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{h / 2:.1f}" fill="{fill}" stroke="{st}" stroke-width="3"/>' + _t(x, y + size * 0.36, text, size, f=ink)
def _dim(x1, y1, x2, y2, text, kind='light'):
    tk = lambda x, y: f'<line x1="{x - 14}" y1="{y}" x2="{x + 14}" y2="{y}" stroke="var(--ink)" stroke-width="4"/>'
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="var(--ink)" stroke-width="4"/>' + tk(x1, y1) + tk(x2, y2) + _pill((x1 + x2) / 2, (y1 + y2) / 2, text, kind, 24)
def _anchor(x, y, s=1.0):
    return (f'<g transform="translate({x} {y}) scale({s})" fill="none" stroke="var(--ink)" stroke-width="6" stroke-linecap="round"><circle cx="0" cy="-30" r="8"/>'
            '<line x1="0" y1="-22" x2="0" y2="28"/><line x1="-16" y1="-10" x2="16" y2="-10"/><path d="M-26 8 C -24 26 -12 32 0 32 C 12 32 24 26 26 8"/><path d="M-30 14 L-26 6 L-18 12 M30 14 L26 6 L18 12"/></g>')
def _hull(hx, sea, L=460, keel=150, bow_up=30):
    """A yacht in profile, bow to the left at hx, waterline at sea; keel fin `keel` px deep."""
    k0 = hx + L * 0.42
    return (f'<path d="M{hx} {sea - bow_up} L{hx + L} {sea - bow_up + 12} L{hx + L - 10} {sea + 18} L{hx + L * 0.15} {sea + 24} Z" fill="var(--ink)"/>'
            f'<path d="M{k0} {sea + 20} L{k0 + 70} {sea + 20} L{k0 + 60} {sea + keel} L{k0 + 10} {sea + keel} Z" fill="var(--ink)"/>'
            f'<line x1="{hx + L * 0.42}" y1="{sea - bow_up}" x2="{hx + L * 0.42}" y2="{sea - bow_up - 170}" stroke="var(--ink)" stroke-width="6"/>'), k0 + 35
def _frame(body, title, key, formula=''):
    W, H = 1280, 800; keyH = 40 + 40 * len(key) + 24; area = H - keyH
    s = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="Carlito, Arial, sans-serif" style="background:var(--bg)"><rect width="{W}" height="{H}" fill="var(--bg)"/>'
    s += body + (_t(40, 70, formula, 40, f='var(--ink)', a='start') if formula else '')
    s += f'<rect x="0" y="{area}" width="{W}" height="{keyH}" fill="var(--band)"/>'
    ky = area + 40; s += _t(30, ky, title, 30, f='var(--ink)', a='start')
    for line in key: ky += 40; s += _t(30, ky, '· ' + line, 27, 400, 'var(--ink)', 'start')
    return s + '</svg>'
def _water(sea, bed, area=636):
    return (f'<rect x="0" y="{sea}" width="1280" height="{bed - sea}" fill="rgba(60,140,190,.14)"/><line x1="0" y1="{sea}" x2="1280" y2="{sea}" stroke="#3c8cbe" stroke-width="5"/>'
            f'<rect x="0" y="{bed}" width="1280" height="{area - bed}" fill="#e3d6b4"/><line x1="0" y1="{bed}" x2="1280" y2="{bed}" stroke="#8a7650" stroke-width="5"/>')

ANCHOR_SVG_TEXT = {}
def anchor_svg(i):
    if i in ('bs-006', 'bs-746'):
        hw = i == 'bs-746'; sea = 190; my = 100.0                       # px per metre (depth drawn true to the draught)
        depth = 3.0 if hw else 2.4; lw = sea + 0.7 * my if hw else sea; bed = sea + depth * my
        hull, kx = _hull(300, lw); keel = lw + 1.9 * my
        hull = hull.replace(f'{lw + 150}', f'{keel}')
        b = _water(lw, bed)
        if hw: b += f'<line x1="0" y1="{sea}" x2="1280" y2="{sea}" stroke="#3c8cbe" stroke-width="4" stroke-dasharray="14 10"/>' + _t(30, sea - 12, 'HW', 26, f='#3c8cbe', a='start') + _t(30, lw - 12, 'LW', 26, f='#3c8cbe', a='start')
        b += hull
        b += _dim(150, lw, 150, keel, 'draught 1.9 m' if hw else 'draft 1.9 m')
        b += _dim(1000, sea, 1000, bed, 'depth 3 m at HW' if hw else 'depth 2.4 m')
        if hw: b += _dim(1150, sea, 1150, lw, 'falls 0.7 m') + _pill(1110, (lw + bed) / 2 + 30, '2.3 m at LW', 'light', 24)
        b += f'<rect x="{kx - 40}" y="{keel}" width="80" height="{bed - keel}" fill="rgba(255,200,0,.35)"/>' + _pill(kx + 230, (keel + bed) / 2, '0.4 m under the keel' if hw else '0.5 m under the keel', 'accent', 28)
        if hw: return _frame(b, 'Anchoring · enough water at low water?', ['3 m − 0.7 m = 2.3 m at low water', '2.3 m − 1.9 m draught = 0.4 m under the keel'])
        b += _pill(1000, sea - 40, 'low water', 'light', 24)
        return _frame(b, 'Anchoring · depth under the keel', ['At low water 2.4 m − 1.9 m = 0.5 m under the keel', 'Enough to stay, but a 0.3 m swell eats into it'])
    if i == 'bs-737':
        sea, bed = 175, 520
        hull, _ = _hull(760, sea, 400, 120)
        b = _water(sea, bed) + hull
        b += f'<path d="M760 {sea - 30} Q 560 {sea + 120} 330 {bed - 8}" fill="none" stroke="#4a4f55" stroke-width="8" stroke-dasharray="12 6"/>'
        b += f'<path d="M330 {bed - 4} L 520 {bed - 4}" stroke="#8a7650" stroke-width="5" stroke-dasharray="6 8"/>' + _anchor(310, bed - 30, 1.1)
        b += f'<path d="M420 {bed + 40} L 560 {bed + 40}" stroke="#e8231a" stroke-width="8"/><path d="M560 {bed + 40} L 536 {bed + 28} L 536 {bed + 52} Z" fill="#e8231a"/>'
        b += _pill(490, bed + 85, 'skating on hard sand', 'red', 26) + _pill(560, sea + 70, 'chain jerks and rumbles', 'light', 24) + _pill(190, 50, 'transit opening', 'light', 24)
        b += '<line x1="120" y1="80" x2="120" y2="170" stroke="var(--ink)" stroke-width="5"/><line x1="260" y1="90" x2="260" y2="170" stroke="var(--ink)" stroke-width="5"/>'
        return _frame(b, 'Anchoring · the anchor is skating', ['A juddering chain and an opening transit: the anchor is not biting', 'Lift it and try another spot'])
    if i == 'bs-741':
        sea, bed = 175, 560; hx = 800; bowY = sea - 40; ax = 120
        hull, _ = _hull(hx, sea, 300, 90, 40)
        b = _water(sea, bed) + hull + f'<circle cx="{hx}" cy="{bowY}" r="9" fill="var(--accent)" stroke="var(--bg)" stroke-width="3"/>'
        pts = [(hx + (ax - hx) * t, bowY + (bed - 8 - bowY) * (1 - (1 - t) ** 2.4)) for t in (k / 40 for k in range(41))]
        j = 33
        b += '<path d="M' + ' L'.join(f'{x:.1f} {y:.1f}' for x, y in pts[:j + 1]) + '" fill="none" stroke="#d8c08a" stroke-width="7"/>'
        b += '<path d="M' + ' L'.join(f'{x:.1f} {y:.1f}' for x, y in pts[j:]) + '" fill="none" stroke="#4a4f55" stroke-width="9" stroke-dasharray="12 6"/>' + _anchor(ax - 10, bed - 32, 1.2)
        b += _dim(hx + 360, sea, hx + 360, bed, 'depth 8 m') + _dim(hx - 46, bowY, hx - 46, sea, 'bow 1 m')
        b += _pill(560, sea + 150, 'nylon rope', 'light', 24) + _pill(230, bed - 90, '6 m chain', 'light', 24) + _pill(520, sea + 70, 'rode 63 m', 'accent', 30)
        return _frame(b, 'Anchoring · a kedge on chain and rope', ['Chain and rope needs about 6–8:1, measured from the bow roller', 'Plan 7:1: 9 m × 7 = 63 m of rode in all'], '(8 m + 1 m) × 7 = 63 m')
    if i == 'bs-761':
        return snubber_svg('Anchoring · a snubber takes the shock', ['A nylon snubber from a bow cleat to the chain', 'It stretches in the gusts and takes the strain off the windlass'])
    if i == 'ci-435':
        sea, bed = 300, 560
        hull, _ = _hull(560, sea, 420, 120)
        b = _water(sea, bed) + hull
        b += f'<path d="M560 {sea - 30} L 140 {bed - 8}" fill="none" stroke="#4a4f55" stroke-width="8" stroke-dasharray="12 6"/>' + _anchor(120, bed - 30, 1.1)
        b += f'<path d="M1040 {sea + 60} L 1180 {sea + 60}" stroke="#e8231a" stroke-width="8"/><path d="M1180 {sea + 60} L 1156 {sea + 48} L 1156 {sea + 72} Z" fill="#e8231a"/>'
        b += _pill(1060, sea + 120, 'reverse, up to 1,500 rpm', 'accent', 28) + _pill(330, sea + 150, 'chain straight and still', 'light', 24)
        b += '<line x1="1080" y1="130" x2="1080" y2="230" stroke="var(--ink)" stroke-width="6"/><line x1="1200" y1="100" x2="1200" y2="230" stroke="var(--ink)" stroke-width="6"/>'
        b += '<line x1="1000" y1="215" x2="1270" y2="175" stroke="var(--muted)" stroke-width="3" stroke-dasharray="10 8"/>' + _pill(1140, 70, 'transit ashore', 'light', 24)
        return _frame(b, 'Anchoring · set it under power', ['Reverse slowly, then build up to about 1,500 rpm', 'Watch a transit ashore: if it opens, the anchor is dragging'])
    if i == 'ci-436':
        sea, bed = 240, 580
        hull, _ = _hull(760, sea, 400, 120)
        b = _water(sea, bed) + hull
        b += f'<path d="M760 {sea - 30} Q 560 {sea + 170} 330 {bed - 8}" fill="none" stroke="#4a4f55" stroke-width="8" stroke-dasharray="12 6"/>' + _anchor(310, bed - 30, 1.1)
        b += f'<path d="M740 {sea - 80} L 560 {sea - 80}" stroke="#e0b400" stroke-width="8" stroke-dasharray="16 12"/><path d="M548 {sea - 80} L 574 {sea - 94} L 574 {sea - 66} Z" fill="#e0b400"/>'
        b += _pill(640, sea - 130, 'motor slowly ahead', 'accent', 28) + _pill(900, sea - 200, 'windlass lifts the slack', 'light', 24) + _pill(510, sea + 120, 'bow points the chain', 'light', 24)
        return _frame(b, 'Weighing anchor · motor up to the chain', ['Motor slowly up towards the anchor: the windlass only lifts the slack', 'The bow shows the helm where the chain leads; the windlass never hauls the boat'])
    raise KeyError(i)

def snubber_svg(title, key, snub='nylon snubber'):
    if True:
        sea, bed = 330, 600
        b = _water(sea, bed)
        b += f'<path d="M420 {sea - 120} L1280 {sea - 100} L1280 {sea + 40} L560 {sea + 30} Z" fill="var(--ink)"/>'          # the bow, close up
        b += f'<rect x="620" y="{sea - 160}" width="90" height="40" rx="8" fill="var(--muted)"/>'                                # windlass
        b += f'<rect x="760" y="{sea - 136}" width="60" height="16" rx="6" fill="var(--ink)"/>'                                  # cleat
        b += f'<circle cx="440" cy="{sea - 118}" r="16" fill="var(--accent)"/>'                                                   # roller
        b += f'<path d="M665 {sea - 140} L440 {sea - 134} Q 400 {sea - 60} 330 {sea + 60} L 260 {bed - 10}" fill="none" stroke="#4a4f55" stroke-width="9" stroke-dasharray="12 6"/>'
        b += f'<path d="M790 {sea - 128} Q 560 {sea - 30} 365 {sea + 10}" fill="none" stroke="var(--accent)" stroke-width="9"/><circle cx="365" cy="{sea + 10}" r="10" fill="var(--accent)"/>'
        b += _pill(540, sea - 40 + 70, snub, 'accent', 28) + _pill(860, sea - 190, 'bow cleat', 'light', 24) + _pill(665, sea - 220, 'windlass: no load', 'light', 24)
        b += _pill(220, sea + 20, 'chain hook', 'light', 24) + _pill(340, bed - 60, 'slack chain', 'light', 24)
        return _frame(b, title, key)

def deep_svg():
    """yof-823: a motor yacht over 32 m of water, the anchor powered down on the windlass, not let go."""
    sea, bed = 150, 600
    b = _water(sea, bed) + f'<path d="M760 {sea - 60} L1240 {sea - 50} L1225 {sea + 30} L800 {sea + 34} Z" fill="var(--ink)"/>'
    b += f'<path d="M880 {sea - 60} L1150 {sea - 60} L1130 {sea - 110} L920 {sea - 110} Z" fill="var(--ink)"/>'
    b += f'<circle cx="772" cy="{sea - 56}" r="12" fill="var(--accent)"/>'
    b += f'<path d="M772 {sea - 50} L 760 {bed - 40}" fill="none" stroke="#4a4f55" stroke-width="8" stroke-dasharray="12 6"/>' + _anchor(758, bed - 34, 1.1)
    b += _dim(640, sea, 640, bed, 'depth 32 m') + _pill(1000, 300, 'windlass powers it down', 'accent', 28)
    b += _pill(1000, 380, 'all the way to the bottom', 'accent', 26) + _pill(330, 300, 'let go: 32 m of chain runs away', 'red', 24)
    return _frame(b, 'Anchoring in deep water · power it down', ['A free-falling anchor and chain gather speed the band brake may not hold, and the chain piles up',
                                                                  'Lower it under power all the way to the bottom, then pay out under control'])

def day_plan(e, cfg):
    i = e['id']
    def shape(title, label, tag, key, hdg=270, you=(0, 260, 0), extra=None):
        sch = {'padPx': 70, 'title': title, 'key': key, 'boats': [{'x': 0, 'z': 0, 'hdg': hdg, 'label': label, 'tag': tag, 'bearing': False, 'scale': 3.2, 'noHeading': False},
               {'you': True, 'x': you[0], 'z': you[1], 'hdg': you[2], 'noHeading': True}], 'fit': [{'x': -200, 'z': -160}, {'x': 200, 'z': 380}]}
        sch.update(extra or {}); return {'sch': sch}
    anch = lambda title, tag, key, hdg=240, extra=None: {'sch': {'padPx': 80, 'trueScale': True, 'minMpp': 0.04, 'title': title, 'key': key,
            'boats': [{'x': 0, 'z': 0, 'hdg': hdg, 'label': 'Yacht', 'tag': tag, 'noHeading': True}],
            'circles': [{'x': -4.4, 'z': -2.1, 'r': 1.25, 'fill': '#fff', 'c': 'ink', 'dash': '0'}, {'x': -4.4, 'z': -2.1, 'r': 0.8, 'fill': 'var(--ink)', 'c': 'ink', 'dash': '0'}],
            'anchors': [{'x': -21, 'z': 12, 's': 0.9}], 'paths': [{'pts': [[-5.2, 3], [-21, 12]], 'c': 'ink', 'dash': '8 8', 'w': 4}], 'fit': [{'x': 6, 'z': -6}], **(extra or {})}}
    if i == 'bs-037': return shape('Day shapes · fishing', 'Fishing', 'two cones, points together', ['You keep clear: sail gives way to a vessel engaged in fishing', 'Rule 18: sail gives way to fishing, NUC and RAM'], hdg=240)
    if i == 'bs-075': return anch('Day shape · at anchor', 'black ball forward', ['One black ball, forward where it is best seen', 'By day: at anchor; at night an all-round white light'])
    if i == 'bs-427': return shape('Day shapes · not under command', 'Not under command', 'two balls', ['She cannot steer or stop: two black balls', 'Rule 18: sail keeps clear of a vessel not under command'])
    if i == 'bs-428': return shape('Day shapes · restricted in ability to manoeuvre', 'Dredger', 'ball, diamond, ball', ['Her work limits how she moves: ball, diamond, ball', 'Keep clear of her (Rule 18)'], hdg=270)
    if i == 'bs-429': return shape('Day shapes · constrained by her draught', 'Tanker', 'cylinder', ['Bound to the deep water by her draught: a cylinder', 'Keep out of her way: avoid impeding her (Rule 18(d))'], hdg=95)
    if i == 'bs-432':
        return {'sch': {'padPx': 80, 'trueScale': True, 'minMpp': 0.04, 'title': 'Day shapes · motor-sailing', 'key': ['Sails up and the engine in gear: you are power-driven', 'Hoist a cone, point down, forward (Rule 25(e))'],
                'boats': [{'you': True, 'x': 0, 'z': 0, 'hdg': 240, 'tag': 'cone, point down', 'noHeading': True}], 'fit': [{'x': -12, 'z': -9}, {'x': 12, 'z': 10}]}}
    if i == 'bs-433': return shape('Day shapes · motor-sailing', 'Motor-sailing', 'starboard tack, motoring', ['The cone shows she is motor-sailing: a power-driven vessel', 'She keeps clear of you under sail (Rule 18)'],
                                   hdg=300, you=(130, 230, 45), extra={'wind': 0, 'texts': [{'x': 300, 'z': 345, 'text': 'port tack, sail only'}], 'fit': [{'x': -200, 'z': -160}, {'x': 380, 'z': 380}]})
    if i == 'bs-434': return shape('Day shapes · aground', 'Aground', 'three balls', ['Three black balls: she is aground', 'Shallow water round her: keep well clear'], hdg=235,
                                   extra={'zones': [{'pts': [[-170, -120], [150, -140], [190, 90], [-150, 110]], 'c': 'red', 'fill': 'rgba(224,37,27,.08)'}], 'texts': [{'x': 120, 'z': -110, 'text': 'shallow water', 'kind': 'red'}]})
    if i == 'bs-764': return anch('Day shape · at anchor', 'black ball: at anchor', ['A black ball: she is at anchor', 'Her chain runs out ahead: keep clear of her bow'],
                                  extra={'boats': [{'x': 0, 'z': 0, 'hdg': 240, 'label': 'Yacht', 'tag': 'black ball: at anchor', 'noHeading': True, 'bearing': False}, {'you': True, 'x': 22, 'z': 14, 'hdg': 300, 'noHeading': True, 'L': 13}],
                                         'paths': [{'pts': [[-5.2, 3], [-21, 12]], 'c': 'ink', 'dash': '8 8', 'w': 4}, {'pts': [[19, 9], [14, 0], [10, -9]], 'c': 'course', 'dash': '14 10', 'arrow': True}], 'texts': [{'x': 22, 'z': -5, 'text': 'pass astern', 'kind': 'accent'}], 'fit': [{'x': 6, 'z': -6}, {'x': 30, 'z': 24}]})
    if i == 'bs-820':
        return {'sch': {'padPx': 80, 'trueScale': True, 'minMpp': 0.04, 'title': 'Day shape · under way again', 'key': ['The ball says you are at anchor', 'Take it down as soon as you are under way'],
                'boats': [{'you': True, 'x': 0, 'z': 0, 'hdg': 300, 'tag': 'ball still up', 'noHeading': True}], 'circles': [{'x': -0.6, 'z': -5.2, 'r': 1.25, 'fill': '#fff', 'c': 'ink', 'dash': '0'}, {'x': -0.6, 'z': -5.2, 'r': 0.8, 'fill': 'var(--ink)', 'c': 'ink', 'dash': '0'}],
                'texts': [{'x': -6, 'z': -9, 'text': 'lower the ball', 'kind': 'accent'}], 'fit': [{'x': -14, 'z': -12}, {'x': 12, 'z': 10}]}}
    if i == 'yof-588':
        b = _water(470, 600, 600)
        b += f'<circle cx="420" cy="300" r="90" fill="var(--ink)"/><circle cx="820" cy="345" r="45" fill="var(--ink)"/>'
        b += _dim(300, 420, 540, 420, '0.6 m: at least, from 20 m', 'accent') + _dim(760, 420, 880, 420, '0.3 m: your ball', 'red')
        b += _pill(620, 140, 'your yacht: 22 m', 'light', 26)
        return {'svg': _frame(b, 'Day shapes · the size matters', ['Annex I 6: a ball is at least 0.6 m across', 'Only a vessel under 20 m may use smaller shapes to suit her size'])}
    raise KeyError(i)

def make_plan(t, e):
    return {'bay': lambda: bay_plan(e, BAY[e['id']]), 'anchor': lambda: anchor_plan(e, ANCHOR[e['id']]), 'dayshape': lambda: day_plan(e, DAY[e['id']])}[t]()

# ---- the Russian of every string ----
SKIP = {'kind', 'color', 'type', 'side', 'which', 'shape', 'id', 'fill', 'stroke', 'anchor', 'd', 'c', 'dash', 'svg', 'font', 'align', 'dir', 'style', 'cls', 'class', 'icon'}
CODE = re.compile(r'^(red|blue|green|yellow|accent|white|black|grey|gray|orange|ink|muted|course|line|light|dash|dashed|dotted|solid|middle|start|end|top|bottom|[a-zA-Z]{1,2}|[\d\s.,:°′″\'"+-]*)$')
def strings(v, k='', out=None):
    out = [] if out is None else out
    if isinstance(v, str):
        if k not in SKIP and not CODE.match(v): out.append(v)
    elif isinstance(v, list): [strings(x, k, out) for x in v]
    elif isinstance(v, dict): [strings(x, kk, out) for kk, x in v.items()]
    return out

def ru_number(s):
    return re.sub(r'(\d)\.(\d)', r'\1,\2', s).replace(' m', ' м')

def write_plan_ru(t, e, labels=None):
    d = os.path.join(QDIR, e['id']); os.makedirs(d, exist_ok=True)
    plan = make_plan(t, e)
    with open(os.path.join(d, 'plan.json'), 'w') as f: json.dump(plan, f, ensure_ascii=False, indent=1)
    if labels is None:
        lp = os.path.join(d, '3d.labels.json')
        labels = json.load(open(lp)) if os.path.exists(lp) else {}
    want = []
    if labels.get('note'): want.append(labels['note'])
    want += [L['text'] for L in labels.get('labels', [])] + list(labels.get('lines', []))
    want += strings(plan)
    if 'profile' in plan:
        p = plan['profile']; want += [f"depth {num(p['depth'])} m", f"bow {num(p['bow'])} m", f"chain {num(p['chain'])} m"]
    if 'svg' in plan:
        want += [re.sub(r'^· ', '', html_unescape(x)) for x in re.findall(r'<text[^>]*>([^<]*)</text>', plan['svg'])]
    ru, missing = {}, []
    src = {**e.get('ru', {}), **RU}
    for s in want:
        if s in ru: continue
        if s in src: ru[s] = src[s]
        elif ' · ' in s and all(p in src for p in s.split(' · ')): ru[s] = ' · '.join(src[p] for p in s.split(' · '))
        elif re.fullmatch(r'[A-Z]|You|Y|HW|LW|[\d.,:\s×÷≈()+=m−-]+', s) or CODE.match(s): ru[s] = {'You': 'Вы', 'HW': 'ПВ', 'LW': 'МВ'}.get(s, ru_number(s))
        else: missing.append(s)
    # the key lines are drawn with a leading '· '
    for s in list(ru): ru.setdefault('· ' + s, '· ' + ru[s])
    if missing: print('MISSING RU', e['id'], missing)
    with open(os.path.join(d, 'ru.json'), 'w') as f: json.dump(ru, f, ensure_ascii=False, indent=1)
    return missing

def html_unescape(s): return s.replace('&lt;', '<').replace('&amp;', '&')

# ===================================================================================================== Blender
if BL:
    def spot_ring(x, y, r=7.0, name='spot', z=0.35):
        """A yellow ring on the water marking a candidate spot (as the article's anchoring figure)."""
        bm = bmesh.new(); seg, ring = 72, 10; tube = r * 0.07; vs = []
        for i in range(seg):
            a = i / seg * math.tau; row = []
            for j in range(ring):
                b = j / ring * math.tau
                row.append(bm.verts.new(((r + tube * math.cos(b)) * math.cos(a), (r + tube * math.cos(b)) * math.sin(a), tube * math.sin(b) * 0.5)))
            vs.append(row)
        for i in range(seg):
            for j in range(ring):
                bm.faces.new((vs[i][j], vs[(i + 1) % seg][j], vs[(i + 1) % seg][(j + 1) % ring], vs[i][(j + 1) % ring])).smooth = True
        me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
        m, nt, b, _ = C.new_mat('ring-yellow'); C.setin(b, 'Base Color', C.lin('#ffc400')); C.setin(b, 'Emission Color', C.lin('#ffc400'))
        C.setin(b, 'Emission Strength', 0.6); C.setin(b, 'Roughness', 0.5)
        return C.obj(name, me, m, (x, y, z))

    def sphere(name, r, mat, loc, seg=32):
        bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=seg // 2, radius=r)
        for f in bm.faces: f.smooth = True
        me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); return C.obj(name, me, mat, loc)

    def torus(name, R, r, mat, loc, rot=(0, 0, 0)):
        bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, location=loc, rotation=rot, major_segments=48, minor_segments=12)
        o = bpy.context.active_object; o.name = name; o.data.materials.append(mat)
        for p in o.data.polygons: p.use_smooth = True
        return o

    def flat_sea(half=60000.0):
        me = bpy.data.meshes.new('flat-sea'); me.from_pydata([(-half, -half, 0), (half, -half, 0), (half, half, 0), (-half, half, 0)], [], [(0, 1, 2, 3)])
        return C.obj('flat-sea', me, K.sea_mat('#0c2e3a', False, far=True))

    def rib(x, y, hdg):
        root, objs = K.load_model('tender-rib.glb', drop_planes=False)
        piv = bpy.data.objects.new('rib-pivot', None); C.col.objects.link(piv)
        root.parent = piv; root.location = (-3.3, -1.75, -0.1)
        piv.location = (x, y, 0.0); piv.rotation_euler = (0, 0, deg(90 - hdg)); piv.scale = (1.4,) * 3
        return piv

    # ---------------------------------------------------------------- land from the drawing's path
    class Land:
        def __init__(self, d, s):
            self.s = s; self.polys = [np.array(p, float) for p in path_polys(d, 16)]
            coast = []
            for p in self.polys:
                for (x1, y1), (x2, y2) in zip(p, np.roll(p, -1, axis=0)):
                    border = any(abs(x1 - v) < 1e-6 and abs(x2 - v) < 1e-6 for v in (0, 320)) or any(abs(y1 - v) < 1e-6 and abs(y2 - v) < 1e-6 for v in (0, 200))
                    if not border: coast.append((x1, y1, x2, y2))
            self.coast = coast
        def dist(self, X, Y):
            """Metres inland (negative at sea) for Blender points; outside the drawing the land carries on."""
            s = self.s; px = X / s + 160; py = 100 - Y / s
            cx = np.clip(px, 0.01, 319.99); cy = np.clip(py, 0.01, 199.99); beyond = np.hypot(px - cx, py - cy)
            inside = np.zeros(px.shape, bool)
            for p in self.polys:
                x1, y1 = p[:, 0], p[:, 1]; x2, y2 = np.roll(x1, -1), np.roll(y1, -1); par = np.zeros(px.shape, bool)
                for k in range(len(x1)):
                    if y1[k] == y2[k]: continue
                    c = (y1[k] > cy) != (y2[k] > cy)
                    xi = (x2[k] - x1[k]) * (cy - y1[k]) / (y2[k] - y1[k]) + x1[k]
                    par ^= c & (cx < xi)
                inside |= par
            dmin = np.full(px.shape, 1e9)
            for x1, y1, x2, y2 in self.coast:
                dx, dy = x2 - x1, y2 - y1; L2 = dx * dx + dy * dy + 1e-12
                t = np.clip(((cx - x1) * dx + (cy - y1) * dy) / L2, 0, 1)
                dmin = np.minimum(dmin, np.hypot(cx - x1 - t * dx, cy - y1 - t * dy))
            return np.where(inside, dmin + beyond, -dmin - beyond) * s

    def heights(land, X, Y, cfg, seed=11.0):
        s = land.s; k = s / 3.0; relief = cfg.get('relief', 100.0); cliff = cfg.get('cliff', False)
        d = land.dist(X, Y)
        bw = cfg.get('beach', 0.0 if cliff else 12.0 * min(1.0, k) ** 0.5)
        n1 = np.array([mnoise.noise(Vector((x * 0.006 / k, y * 0.006 / k, seed))) for x, y in zip(X, Y)])
        n2 = np.array([mnoise.noise(Vector((x * 0.025 / k, y * 0.025 / k, seed + 2))) for x, y in zip(X, Y)])
        dl = np.maximum(0.0, d - bw)
        hills = 1.4 + relief * (1 - np.exp(-dl / (cfg.get('hill_len', 95) * k))) + 0.45 * relief * (1 - np.exp(-np.maximum(0, d - 300 * k) / (400 * k)))
        rough = (0.35 * relief * n1 + 0.1 * relief * n2) * np.clip((d - bw - 15 * k) / (60 * k), 0, 1)
        if cliff: hills = hills + 20.0 * np.clip(d / 6.0, 0, 1) ** 0.5
        if cfg.get('cone'):      # a volcanic island: one peak rising to `relief` `cone` metres in from the shore
            hills = 1.4 + relief * np.clip(dl / cfg['cone'], 0, 1) ** 1.15; rough = rough * 0.25
        if cfg.get('valley') is not None:
            px = X / s + 160; py = 100 - Y / s
            v = np.exp(-((px - cfg['valley']) / (16 + 0.25 * np.maximum(0, 95 - py))) ** 2) * (py < 100)
            hills = hills * (1 - 0.82 * v); rough = rough * (1 - 0.7 * v)
        ld = np.where(d < bw, 1.4 * np.clip(d / max(bw, 1e-3), 0, 1), hills + rough)
        sea = np.maximum(-14.0, d * 0.12)
        return np.where(d < 0, sea, ld) - 0.3, d

    def terrain(land, cfg):
        s = land.s; step = max(1.0, s * 1.6) if s >= 1 else 0.8
        x0, x1 = (-160 - 160) * s, (480 - 160) * s; y0, y1 = -(330 - 100) * s, -(-250 - 100) * s
        nx, ny = int((x1 - x0) / step), int((y1 - y0) / step)
        gx, gy = np.meshgrid(x0 + np.arange(nx + 1) * step, y0 + np.arange(ny + 1) * step)
        X, Y = gx.ravel(), gy.ravel()
        H, D = heights(land, X, Y, cfg)
        ks = max(1.0, s / 3.0)          # big scenes: the land material's pattern scaled with the drawing
        verts = list(zip((X / ks).tolist(), (Y / ks).tolist(), (H / ks).tolist()))
        faces = [(j * (nx + 1) + i, j * (nx + 1) + i + 1, (j + 1) * (nx + 1) + i + 1, (j + 1) * (nx + 1) + i) for j in range(ny) for i in range(nx)]
        me = bpy.data.meshes.new('land'); me.from_pydata(verts, [], faces); me.update(); me.shade_smooth()
        o = C.obj('land', me, KW.land_mat()); o.scale = (ks,) * 3
        return lambda x, y: float(heights(land, np.array([x], float), np.array([y], float), cfg)[0][0])

    def trees_on(land, cfg, hfun, n=1400, seed=31):
        s = land.s; random.seed(seed)
        m = C.simple('foliage', '#3c4a26', 0.9)
        bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
        for v in bm.verts: v.co *= 1.0 + 0.2 * mnoise.noise(v.co * 2.0); v.co.z *= 0.8
        me = bpy.data.meshes.new('tree'); bm.to_mesh(me); bm.free(); me.materials.append(m); me.shade_smooth()
        X = np.array([random.uniform(-260 * s, 260 * s) for _ in range(n * 4)]); Y = np.array([random.uniform(-150 * s, 260 * s) for _ in range(n * 4)])
        H, D = heights(land, X, Y, cfg)
        k = 0
        for x, y, h, d in zip(X, Y, H, D):
            if k >= n: break
            if d < max(8.0, 10 * s) or mnoise.noise(Vector((x * 0.012, y * 0.012, 3.0))) < -0.05: continue
            o = bpy.data.objects.new('tree', me); C.col.objects.link(o)
            sc = random.uniform(2.2, 4.6); o.scale = (sc, sc, sc * random.uniform(0.8, 1.3)); o.location = (x, y, h + sc * 0.45); k += 1

    def town_on(land, cfg, px, py, n, seed=21):
        s = land.s; random.seed(seed)
        wm, rm = KW.plaster_mat(), KW.roof_mat()
        protos = [KW.house_mesh(random.uniform(7, 12), random.uniform(6, 9), random.uniform(4, 8), random.uniform(2.0, 3.0), wm, rm, f'house{k}') for k in range(10)]
        X = np.array([(px - 160) * s + random.gauss(0, 30 * s) for _ in range(n * 6)]); Y = np.array([-(py - 100) * s + random.gauss(0, 14 * s) for _ in range(n * 6)])
        H, D = heights(land, X, Y, cfg)
        placed = []
        for x, y, h, d in zip(X, Y, H, D):
            if len(placed) >= n: break
            if d < 22 or d > 220 or any((x - a) ** 2 + (y - b) ** 2 < 110 for a, b in placed): continue
            placed.append((x, y)); o = bpy.data.objects.new('house', random.choice(protos)); C.col.objects.link(o)
            o.location = (x, y, h - 0.4); o.rotation_euler = (0, 0, deg(random.choice((0, 90)) + random.uniform(-8, 8)))
        return placed

    def drone(s, target=(0.0, 0.0), elev=60.0, zoom=1.0, az=180.0, lens=30.0, aim_z=0.0):
        D = 176.0 * s * zoom / math.tan(math.atan(18.0 / lens))
        a, e = deg(az), deg(elev)
        eye = Vector((target[0] + math.sin(a) * D * math.cos(e), target[1] + math.cos(a) * D * math.cos(e), D * math.sin(e)))
        return KW.camera(eye, Vector((target[0], target[1], aim_z)), lens=lens)

    def wind_arrow(wind, c, L, z):
        """Label-overlay arrow pointing downwind, centred on c (Blender x, y)."""
        dx, dy = math.sin(deg(wind)), math.cos(deg(wind))
        return ((c[0] + dx * L / 2, c[1] + dy * L / 2, z), (c[0] - dx * L / 2, c[1] - dy * L / 2, z), 'red')

    def yacht_at(x, y, hdg, name='yacht', **kw):
        return K.load_yacht(name=name, **kw).place(x, y, heading=hdg)

    # ---------------------------------------------------------------- bay scenes
    def scene_bay(e, cfg):
        f = e['figure']; kind = cfg.get('kind', 'land')
        if kind == 'pontoon': return scene_pontoon(e, cfg)
        if kind == 'quay': return scene_quay(e, cfg)
        if kind == 'seabed': return scene_seabed(e, cfg)
        if kind == 'harbour': return scene_harbour(e, cfg)
        if kind == 'clear': return scene_clear(e, cfg)
        s = cfg['s']; P = lambda px, py: (( px - 160) * s, -(py - 100) * s)
        land = Land(f.get('land') or cfg.get('land') or DEFAULT_LAND, s)
        hfun = terrain(land, cfg)
        if s <= 6 and not cfg.get('night'): trees_on(land, cfg, hfun, n=1300 if s <= 4 else 700)
        if cfg.get('town'): town_on(land, cfg, *cfg['town'])
        if s <= 4:
            size = 40.0 if s > 1 else 30.0; rep = max(8, min(26, int(math.ceil(330 * s * 1.25 / size))))
            K.sea('calm' if s < 1 else 'breeze', size=size, res=9, repeat=rep, center=(0, 0))
        else:
            flat_sea(max(60000.0, 700.0 * s) if cfg.get('far') else 60000.0)
        if cfg.get('cliff'):   # rocks at the foot of the cliffs
            rnd = random.Random(4); rm = C.simple('wet-rock', '#4d4840', 0.6)
            bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
            for v in bm.verts: v.co *= 1 + 0.3 * mnoise.noise(v.co * 1.7)
            rme = bpy.data.meshes.new('rock'); bm.to_mesh(rme); bm.free(); rme.materials.append(rm)
            X = np.array([rnd.uniform(-170 * s, 170 * s) for _ in range(900)]); Y = np.array([rnd.uniform(-20 * s, 120 * s) for _ in range(900)])
            D = land.dist(X, Y)
            for x, y, d in zip(X, Y, D):
                if -12 < d < 1:
                    o = bpy.data.objects.new('rock', rme); C.col.objects.link(o); sc = rnd.uniform(1.0, 3.2)
                    o.scale = (sc, sc * rnd.uniform(0.7, 1.3), sc * 0.7); o.location = (x, y, rnd.uniform(-0.8, 0.4))
        if cfg.get('race'):      # a tide race: patches of broken water round the figure's own 'race' label
            rx, ry, rr = cfg['race']; rnd = random.Random(7)
            for k in range(22):
                a = rnd.uniform(0, math.tau); d = rr * math.sqrt(rnd.random())
                X, Y = P(rx + d * math.cos(a) - 6, ry + d * math.sin(a) * 0.7)
                race_patch(X, Y, rnd.uniform(0.25, 0.5) * rr * s * 0.45, k)
        labels, arrows = [], []
        ring_r = 6.5 * s
        for x, y, l in f.get('spots', []):
            X, Y = P(x, y)
            if l in 'ABCD' and len(l) == 1:
                spot_ring(X, Y, ring_r, 'spot' + l)
                labels.append(((X, Y, 4.0 * s), l, 'blue'))
        if cfg.get('ashore'): lines_ashore(cfg, P, hfun)
        yt = cfg.get('yacht')
        if yt:
            lab, x, y, hdg = yt; X, Y = P(x, y)
            yy = yacht_at(X, Y, hdg, name='you')
            if cfg.get('night'):
                import kit_night as N
                N.light('anchor-light', yy.world((5.06, 0.13, 20.8)), 'white', strength=14.0, power=60.0, radius=0.2)
            if lab not in 'ABC': labels.append(((X, Y, 20.0), lab, 'blue') if lab in ('Y', 'You') or lab.startswith('you') else ((X, Y, 20.0), lab))
        if cfg.get('own'):
            x, y, hdg = cfg['own']; X, Y = P(x, y)
            K.load_yacht(name='own', sails={'main': True, 'genoa': 'port', 'boom': 28}).place(X, Y, heading=hdg, heel=-8)
        for x, y, hdg in cfg.get('ribs', []):
            rib(*P(x, y), hdg)
        if cfg.get('buoy'):
            bx, by = P(*cfg['buoy']); mooring_buoy(bx, by)
        skip = {'you, at anchor', 'yacht at anchor, 40 m chain out'}
        for l in f.get('labels', []):
            x, y, t = l[0], l[1], l[2]
            if t in skip: continue
            X, Y = P(x, y); z = max(0.0, hfun(X, Y)) + (3.0 * s if s >= 1 else 2.0)
            if t == 'buoy': X, Y = P(*cfg['buoy']); z = 1.6
            labels.append(((X, Y, z), t))
        if f.get('wind') is not None and not cfg.get('nowind'):
            cx, cy = P(*cfg.get('wind_at', (282, 150)))
            arrows.append(wind_arrow(f['wind'], (cx, cy), 55 * s * cfg.get('zoom', 1.0), 8.0 * s))
        if cfg.get('night'):
            K.night_sky(moon=0.0035, stars=True)
            for o in bpy.data.objects:
                if o.name == 'moon': o.rotation_euler = (deg(55), 0, deg(-25))
            expo = 0.9
        elif cfg.get('dawn'):
            K.day_sky(sun_az=75, sun_el=7, strength=0.25, haze=3.0); expo = 0.3
        else:
            az, el = cfg.get('sun', (210, 40)); K.day_sky(sun_az=az, sun_el=el, strength=0.25, haze=cfg.get('haze', 2.2)); expo = -0.7
        cam = drone(s, target=P(*cfg.get('target', (160, 100))), elev=cfg.get('elev', 55), zoom=cfg.get('zoom', 1.0))
        if cfg.get('far'): cam.data.clip_start = 5.0; cam.data.clip_end = 2000.0 * s     # a drawing tens of km across
        return labels, arrows, f.get('note'), expo, []

    def race_patch(X, Y, R, seed):
        """Broken white water on a disc of radius R: noise-cut foam, fading to its edge."""
        me = bpy.data.meshes.new('race'); me.from_pydata([(-1, -1, 0), (1, -1, 0), (1, 1, 0), (-1, 1, 0)], [], [(0, 1, 2, 3)])
        m, nt, b, out = C.new_mat(f'race{seed}')
        tc = nt.nodes.new('ShaderNodeTexCoord')
        nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 6.0; nz.inputs['Detail'].default_value = 8.0
        nz.noise_dimensions = '4D'; nz.inputs['W'].default_value = float(seed); nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
        cr = nt.nodes.new('ShaderNodeValToRGB'); cr.color_ramp.elements[0].position = 0.55; cr.color_ramp.elements[1].position = 0.68
        nt.links.new(nz.outputs['Fac'], cr.inputs['Fac'])
        ln = nt.nodes.new('ShaderNodeVectorMath'); ln.operation = 'LENGTH'; nt.links.new(tc.outputs['Object'], ln.inputs[0])
        mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 0.45; mr.inputs['From Max'].default_value = 1.0
        mr.inputs['To Min'].default_value = 1.0; mr.inputs['To Max'].default_value = 0.0; nt.links.new(ln.outputs['Value'], mr.inputs['Value'])
        mu = nt.nodes.new('ShaderNodeMath'); mu.operation = 'MULTIPLY'; nt.links.new(cr.outputs['Color'], mu.inputs[0]); nt.links.new(mr.outputs['Result'], mu.inputs[1])
        tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader')
        C.setin(b, 'Base Color', (0.85, 0.88, 0.9, 1)); C.setin(b, 'Roughness', 0.8)
        nt.links.new(mu.outputs[0], mx.inputs['Fac']); nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(b.outputs[0], mx.inputs[2])
        nt.links.new(mx.outputs[0], out.inputs['Surface'])
        o = C.obj('race', me, m, (X, Y, 0.25)); o.scale = (R, R * 0.7, 1); o.rotation_euler = (0, 0, seed * 0.7); o.visible_shadow = False
        return o

    def mooring_buoy(x, y):
        fl = sphere('float', 0.55, C.simple('buoy-float', '#eceae3', 0.45, coat=0.5), (x, y, 0.18)); fl.scale.z = 0.75
        torus('band', 0.535, 0.045, C.simple('buoy-band', '#c8102e', 0.45, coat=0.4), (x, y, 0.24))
        C.cyl('eye-post', 0.035, 0.045, 0.2, 16, K.mats()['galv'], (x, y, 0.66))
        torus('ring', 0.10, 0.016, K.mats()['galv'], (x, y, 0.86), rot=(0, deg(90), 0))

    def hull_extent(y, side=-1):
        """World x of the hull's widest point on one side (the yacht heading north): ray casts from outboard."""
        bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get(); best = None
        c = y.root.location
        for dy in (-3, -1, 1, 3, 5):
            for z in (0.4, 0.9, 1.4):
                hit, loc, *_ = bpy.context.scene.ray_cast(dg, Vector((c.x + side * 12, c.y + dy, z)), Vector((-side, 0, 0)))
                if hit: best = loc.x if best is None else (min(best, loc.x) if side < 0 else max(best, loc.x))
        return best

    def mooring_line(name, a, b, sag=0.3, mat=None):
        pts = [a.lerp(b, t / 10) - Vector((0, 0, sag * math.sin(math.pi * t / 10))) for t in range(11)]
        C.tube(name, pts, 0.014, 8, 1.0, mat or C.simple('mooring-line', '#e7e2d4', 0.7))

    def scene_pontoon(e, cfg):
        f = e['figure']; s = cfg['s']; P = lambda px, py: ((px - 160) * s, -(py - 100) * s)
        land = path_polys(f['land'])[0]; ys = [p[1] for p in land]; south = max(ys)
        edge = P(50 if max(p[0] for p in land) >= 50 else 40, 0)[0]
        ytop, ybot = 70.0, P(0, south)[1] if south < 200 else -60.0
        M = K.mats(); TOP = 0.5
        L = ytop - ybot; cy = (ytop + ybot) / 2
        C.obj('float', C.rbox('float', (PONTOON_W - 0.1, L, 0.8), 0.06, 2), M['float'], (edge - PONTOON_W / 2, cy, TOP - 0.45))
        deck = C.obj('deck', C.rbox('deck', (PONTOON_W, L, 0.06), 0.01, 1), M['planks'], (edge - PONTOON_W / 2, cy, TOP))
        C.obj('rub', C.rbox('rub', (0.12, L, 0.08), 0.02, 2), M['rubber'], (edge + 0.04, cy, TOP - 0.12))
        # the shore beyond the marina: a quay and town far to the west, so the pontoon reads as one
        K.coast(distance=420, bearing=300, height=60, town=True)
        K.sea('calm', size=30.0, res=9, repeat=8, center=(0, 0))
        def cleat(yc):
            p = Vector((edge - 0.3, yc, TOP + 0.03))
            C.cyl('cleat-horn', 0.022, 0.022, 0.34, 20, M['galv'], p + Vector((0, 0, 0.085)), (math.pi / 2, 0, 0))
            for dy in (-0.07, 0.07): C.cyl('cleat-leg', 0.025, 0.032, 0.08, 16, M['galv'], p + Vector((0, dy, 0.04)))
            return p + Vector((0, 0, 0.09))
        sock = C.fabric_mat('fender-sock', '#1e2f55', '#5d75a8', 1400.0)
        labels, arrows = [], []
        for b in cfg['boats']:
            if 'x' in b:     # motoring in, clear of the pontoon
                X, Y = P(b['x'], b['y']); y = yacht_at(X, Y, b['hdg'], name='you')
                K.wake(y, 22, 6, 0.6)
                labels.append(((X, Y, 4.0), b['label'], 'blue'))
                continue
            Yc = P(0, b['y'])[1]
            y = yacht_at(0.0, Yc, 0, name='y' + b['label'][:4], hull=b.get('hull', 'white'))
            west = hull_extent(y, -1); y.root.location.x += (edge + 0.35) - west
            if b.get('off'):   # bow blown off: pivot about the stern quarter, which stays on its fender
                st = y.world((-3.4, 2.1, 2.3)); y.root.rotation_euler.z -= deg(b['off'])
                bpy.context.view_layer.update(); st2 = y.world((-3.4, 2.1, 2.3)); y.root.location += Vector((st.x - st2.x, st.y - st2.y, 0))
            bpy.context.view_layer.update()
            for fy in ((-2.5, 1.5, 5.0) if not b.get('off') else (-2.8,)):
                C.obj('fender', C.rbox('fender', (0.22, 0.22, 0.6), 0.1, 3), sock, (edge + 0.15, y.root.location.y + fy, 0.45))
            if 'bow' in b.get('lines', ()): mooring_line('bow-line', y.world((8.9, 0.84, 3.58)), cleat(y.world((8.9, 0, 0)).y + 4.0))
            if 'stern' in b.get('lines', ()): mooring_line('stern-line', y.world((-1.46, 2.05, 3.58)), cleat(y.world((-3.5, 0, 0)).y - 3.0))
            c = y.world((3.0, 0.13, 2.0))
            labels.append(((c.x, c.y, 4.0), b['label'], 'blue' if b['label'].startswith('you') else None))
        for l in f.get('labels', []):
            if l[2] == 'PONTOON': labels.append(((edge - PONTOON_W / 2, -9.0 if e['id'] != 'bs-813' else -10.0, TOP + 0.6), 'PONTOON'))
        labels = [L if L[2:] != (None,) else L[:2] for L in labels]
        cx = 9.0
        arrows.append(wind_arrow(f['wind'], (cx, P(0, 150)[1] if e['id'] != 'bs-813' else -14.0), 9.0, 5.0))
        K.day_sky(sun_az=230, sun_el=50)
        tgt = (-5.0, 0.0) if e['id'] != 'bs-813' else (-6.0, 3.0)
        KW.camera(Vector((tgt[0], tgt[1] - 30, 42)), Vector((tgt[0], tgt[1], 0)), lens=30 if e['id'] != 'bs-813' else 26)
        return labels, arrows, f['note'], -0.6, []

    class YachtInstance:
        """A placed copy of a yacht loaded once (a collection instance)."""
        def __init__(self, src_coll, name):
            self.e = bpy.data.objects.new(name, None); self.e.instance_type = 'COLLECTION'; self.e.instance_collection = src_coll; C.col.objects.link(self.e)
        def place(self, x, y, heading=0.0):
            self.e.location = (x, y, 0.0); self.e.rotation_euler = (0, 0, math.radians(90 - heading)); return self

    def yacht_source(hull='white', name='src'):
        y = K.load_yacht(name=name, hull=hull)
        coll = bpy.data.collections.new(name + '-coll'); bpy.context.scene.collection.children.link(coll)
        for o in [y.root] + list(y.root.children_recursive):
            for c in list(o.users_collection): c.objects.unlink(o)
            coll.objects.link(o)
        y.root.rotation_euler = (0, 0, 0)
        for lc in bpy.context.view_layer.layer_collection.children:
            if lc.collection == coll: lc.exclude = True
        return coll

    def scene_quay(e, cfg):
        f = e['figure']; s = cfg['s']; rows = cfg.get('rows', {})
        P = lambda px, py: ((px - 160) * s, -rows[py] if py in rows else -(py - 40) * s)   # the quay face (y 40) at 0
        concrete = C.concrete_mat('quay-concrete')
        C.obj('quay', C.rbox('quay', (160, 30, 3.0), 0.15, 2), concrete, (0, 15, -0.3))
        C.obj('quay-edge', C.rbox('quay-edge', (160, 0.5, 0.25), 0.05, 2), C.simple('quay-cap', '#cfcac0', 0.8), (0, 0.25, 1.32))
        wm, rm = KW.plaster_mat(), KW.roof_mat(); random.seed(7); x = -80
        while x < 80:
            w = random.uniform(7, 11); hgt = random.uniform(7, 13)
            o = bpy.data.objects.new('house', KW.house_mesh(w, 10, hgt, 2.4, wm, rm, f'h{x:.0f}')); C.col.objects.link(o)
            o.location = (x + w / 2, 36, 1.2); x += w + random.uniform(0.0, 1.2)
        SRC = {'white': yacht_source('white', 'src-white'), 'navy': yacht_source('navy', 'src-navy')}
        for xc in (-30, -25, -20, -15, -10, -5, 5, 10, 15, 20, 25, 30):
            YachtInstance(SRC['navy' if xc in (-20, 15) else 'white'], f'moored{xc}').place(xc, -1.6 - 8.7, heading=180)
        K.sea('calm', size=30.0, res=10, repeat=12, center=(0, -40))
        K.day_sky(sun_az=215, sun_el=42, strength=0.25, haze=2.0)
        labels, arrows = [], []
        for x, y, l in f['spots']:
            X, Y = P(x, y); spot_ring(X, Y, 3.2, 'spot' + l); labels.append(((X, Y, 2.0), l, 'blue'))
        for l in f['labels']:
            X, Y = P(l[0], l[1])
            if cfg.get('plain'): labels.append(((X, 6.0, 3.0), l[2]) if l[1] < 40 else ((X, Y, 1.5), l[2]))
            else: labels.append(((X, 6.0, 3.0), l[2]) if l[2] == 'QUAY' else ((X, Y, 1.5), l[2], 'blue'))
        if cfg.get('cam'):
            eye, look, lens = cfg['cam']; arrows.append(wind_arrow(f['wind'], (40, -70), 22, 4.0))
            KW.camera(Vector(eye), Vector(look), lens=lens)
            return labels, arrows, f['note'], -0.6, []
        arrows.append(wind_arrow(f['wind'], (34, -28), 14, 4.0))
        KW.camera(Vector((0, -92, 46)), Vector((0, -20, 0)), lens=32)
        return labels, arrows, f['note'], -0.6, []

    def scene_seabed(e, cfg):
        f = e['figure']
        y = K.load_yacht(); y.place(0, 0, heading=0); KW.antifoul_hull(y)
        DEPTH = 6.0
        KW.water_body(depth=12.0, size=400.0, density=0.11, color='#0f5a5f', absorb='#2f9f96', reflect=0.35, absorb_density=0.14, center=(0, 40))
        KW.far_sea_ring(inner=200.0)
        KW.seabed(z=-DEPTH, size=120.0, res=240, center=(0, 30), colors=('#a8996f', '#c9b98f', '#b9a87f'))
        A, B = Vector((-4.5, 19.0)), Vector((4.8, 15.5))
        KW.seagrass(((-14, 7), (16, 32)), -DEPTH, clumps=16000, length=0.85, patches=False, seed=12)
        for o in list(bpy.data.objects):     # the pale sand patch round B
            if o.name.startswith('grass'):
                d = ((o.location.x - B.x) / 4.2) ** 2 + ((o.location.y - B.y) / 3.2) ** 2
                if d < 1.0 + 0.25 * mnoise.noise(Vector((o.location.x * 0.6, o.location.y * 0.6, 1.0))): bpy.data.objects.remove(o)
        K.coast(distance=170, bearing=0, height=70, town=False)
        K.day_sky(sun_az=160, sun_el=62, strength=0.25, haze=2.0)
        eye = Vector((0.4, 9.0, 7.0)); look = Vector((0.2, 17.0, -DEPTH))
        KW.camera(eye, look, lens=26)
        labels = [((A.x, A.y, -DEPTH + 1.0), 'A', 'blue'), ((B.x, B.y, -DEPTH + 0.4), 'B', 'blue'),
                  ((A.x - 1.0, A.y - 4.0, -DEPTH + 0.8), 'dark seagrass meadow'), ((B.x + 0.5, B.y - 3.0, -DEPTH + 0.2), 'pale sand patch')]
        return labels, [], f['note'], -0.5, []

    # ---------------------------------------------------------------- Charter Check-in: harbours, a clear bay, lines ashore
    def ext_poly(poly, far=220.0):
        """Land touching the drawing's border carries on past it."""
        out = []
        for x, y in poly:
            out.append((-far if x <= 0 else 320 + far if x >= 320 else x, -far if y <= 0 else 200 + far if y >= 200 else y))
        return out

    def inside(poly, x, y):
        c = False
        for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
            if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1: c = not c
        return c

    def edge_dist(poly, x, y):
        best = 1e9
        for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
            dx, dy = x2 - x1, y2 - y1; L2 = dx * dx + dy * dy + 1e-9
            t = max(0.0, min(1.0, ((x - x1) * dx + (y - y1) * dy) / L2)); best = min(best, math.hypot(x - x1 - t * dx, y - y1 - t * dy))
        return best

    QH = 1.5    # quay top above the water
    def quay_slab(name, poly_m, mat):
        bm = bmesh.new(); vs = [bm.verts.new((x, y, QH)) for x, y in poly_m]
        f = bm.faces.new(vs)
        if f.normal.z < 0: f.normal_flip()
        r = bmesh.ops.extrude_face_region(bm, geom=[f]); nv = [v for v in r['geom'] if isinstance(v, bmesh.types.BMVert)]
        bmesh.ops.translate(bm, verts=nv, vec=(0, 0, -(QH + 4.0)))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
        return C.obj(name, me, mat)

    def fuel_pump(x, y):
        red = C.simple('pump-red', '#c8161d', 0.4, coat=0.5)
        C.obj('pump', C.rbox('pump', (0.7, 0.5, 1.4), 0.06, 2), red, (x, y, QH + 0.7))
        C.obj('pump-top', C.rbox('pump-top', (0.76, 0.56, 0.2), 0.04, 2), C.simple('pump-white', '#f1f0ea', 0.4), (x, y, QH + 1.5))

    def pontoon_deck(name, a, b, w):
        M = K.mats(); d = (b - a); L = d.length; c = (a + b) / 2; ang = math.atan2(d.y, d.x)
        o = C.obj(name + '-float', C.rbox(name + '-float', (L, w - 0.1, 0.8), 0.06, 2), M['float'], (c.x, c.y, 0.05)); o.rotation_euler.z = ang
        o = C.obj(name, C.rbox(name, (L, w, 0.06), 0.01, 1), M['planks'], (c.x, c.y, 0.5)); o.rotation_euler.z = ang

    def scene_harbour(e, cfg):
        f = e['figure']; s = cfg['s']; P = lambda px, py: ((px - 160) * s, -(py - 100) * s)
        polys = [ext_poly(p) for p in path_polys(f.get('land') or cfg.get('land'), 8)]
        concrete = C.concrete_mat('harbour-quay')
        for k, poly in enumerate(polys):
            quay_slab(f'quay{k}', [P(x, y) for x, y in poly], concrete)
        # houses behind the quays: away from the water's edge
        random.seed(17); wm, rm = KW.plaster_mat(), KW.roof_mat()
        protos = [KW.house_mesh(random.uniform(7, 11), random.uniform(6, 9), random.uniform(4, 9), random.uniform(2.0, 3.0), wm, rm, f'hh{k}') for k in range(8)]
        placed = []
        for _ in range(4000):
            x = random.uniform(-200, 520); y = random.uniform(-200, 400)
            poly = next((p for p in polys if inside(p, x, y)), None)
            if poly is None or edge_dist(poly, x, y) * s < 9.0 or any(math.hypot(x - a, y - b) * s < 11 for a, b in placed): continue
            placed.append((x, y)); X, Y = P(x, y)
            o = bpy.data.objects.new('house', random.choice(protos)); C.col.objects.link(o); o.location = (X, Y, QH); o.rotation_euler.z = deg(random.choice((0, 90)))
            if len(placed) > 260: break
        for x1, y1, x2, y2, w in cfg.get('pontoons', []):
            a = Vector(P(x1, y1)); b = Vector(P(x2, y2))
            pontoon_deck('pontoon', a, b, w)
        if cfg.get('moored'):
            SRC = {'white': yacht_source('white', 'src-white'), 'navy': yacht_source('navy', 'src-navy')}
            for k, (x, y, h) in enumerate(cfg['moored']):
                YachtInstance(SRC['navy' if k % 5 == 2 else 'white'], f'moored{k}').place(*P(x, y), heading=h)
        for x, y in cfg.get('buoys', []): mooring_buoy(*P(x, y))
        for x, y in cfg.get('fuel', []): fuel_pump(*P(x, y))
        size = 30.0; rep = max(8, min(26, int(math.ceil(330 * s * 1.6 / size))))
        K.sea('calm', size=size, res=9, repeat=rep, center=(0, 0))
        labels, arrows = [], []
        for x, y, l in f.get('spots', []):
            X, Y = P(x, y); spot_ring(X, Y, 3.4, 'spot' + l); labels.append(((X, Y, 2.5), l, 'blue'))
        for x, y, t in f.get('labels', []):
            X, Y = P(x, y); onland = any(inside(p, x, y) for p in polys)
            labels.append(((X, Y, QH + 4.0 if onland else 1.5), t))
        if f.get('wind') is not None:
            cx, cy = P(*cfg.get('wind_at', (282, 150)))
            arrows.append(wind_arrow(f['wind'], (cx, cy), 50 * s * cfg.get('zoom', 1.0), 6.0))
        az, el = cfg.get('sun', (210, 42)); K.day_sky(sun_az=az, sun_el=el, strength=0.25, haze=2.2)
        drone(s, target=P(*cfg.get('target', (160, 100))), elev=cfg.get('elev', 55), zoom=cfg.get('zoom', 1.0))
        return labels, arrows, f.get('note'), -0.7, []

    def lines_ashore(cfg, P, hfun):
        """Yachts lying to their anchors, bows out (south), sterns held by long lines to the north shore."""
        s = cfg['s']; SRC = {'white': yacht_source('white', 'src-white'), 'navy': yacht_source('navy', 'src-navy')}
        line_m = C.simple('shore-line', '#e7e2d4', 0.7)
        for k, x in enumerate(cfg['ashore']):
            X, Y = P(x, 45 + 3.0 / s + 7.3 / s)
            YachtInstance(SRC['navy' if k % 4 == 1 else 'white'], f'ashore{k}').place(X, Y, heading=180)
            stern = Vector((X, Y + 7.0, 1.4)); sx, sy = P(x + (k % 3 - 1) * 2, 40)
            shore = Vector((sx, sy, max(0.6, hfun(sx, sy) + 0.5)))
            mooring_line(f'line-ashore{k}', stern, shore, sag=0.5, mat=line_m)

    def scene_clear(e, cfg):
        """A clear-water bay seen from the bow as the yacht comes in (as bs-736's seabed view): the weed meadow round
        A, the pale sand patch at B, rocks rising to 3 m at C, ahead. The drawing's layout kept: A west, B south-east,
        C north (further ahead)."""
        f = e['figure']
        y = K.load_yacht(); y.place(0, 0, heading=0); KW.antifoul_hull(y)
        DEPTH = 7.0
        KW.water_body(depth=12.0, size=400.0, density=0.11, color='#0f5a5f', absorb='#2f9f96', reflect=0.35, absorb_density=0.14, center=(0, 40))
        KW.far_sea_ring(inner=200.0)
        KW.seabed(z=-DEPTH, size=120.0, res=240, center=(0, 30), colors=('#a8996f', '#c9b98f', '#b9a87f'))
        A, B, Cc = Vector((-4.6, 19.5)), Vector((4.6, 16.0)), Vector((0.8, 25.8))
        KW.seagrass(((-15, 7), (17, 33)), -DEPTH, clumps=16000, length=0.85, patches=False, seed=12)
        for o in list(bpy.data.objects):     # the sand patch round B and the rocks round C: no weed
            if o.name.startswith('grass'):
                q = o.location
                d = ((q.x - B.x) / 4.2) ** 2 + ((q.y - B.y) / 3.2) ** 2
                d2 = ((q.x - Cc.x) / 5.5) ** 2 + ((q.y - Cc.y) / 3.0) ** 2
                if d < 1.0 + 0.25 * mnoise.noise(Vector((q.x * 0.6, q.y * 0.6, 1.0))) or d2 < 1.0: bpy.data.objects.remove(o)
        rnd = random.Random(4); rm = C.simple('reef-rock', '#5d5a50', 0.8)
        bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1.0)
        for v in bm.verts: v.co *= 1 + 0.3 * mnoise.noise(v.co * 1.7)
        for fa in bm.faces: fa.smooth = True
        rme = bpy.data.meshes.new('reef'); bm.to_mesh(rme); bm.free(); rme.materials.append(rm)
        for k in range(16):
            o = bpy.data.objects.new('reef', rme); C.col.objects.link(o); sc = rnd.uniform(0.9, 1.8)
            o.scale = (sc, sc * rnd.uniform(0.7, 1.3), sc * rnd.uniform(1.0, 1.6))
            o.location = (Cc.x + rnd.uniform(-4.0, 4.0), Cc.y + rnd.uniform(-2.0, 2.0), -DEPTH + sc * 0.8 + (2.4 if k < 5 else 0.0))
        K.coast(distance=170, bearing=0, height=70, town=False)
        az, el = cfg.get('sun', (160, 62)); K.day_sky(sun_az=az, sun_el=el, strength=0.25, haze=2.0)
        KW.camera(Vector((0.4, 8.0, 7.5)), Vector((0.3, 21.5, -DEPTH)), lens=24)
        pos = {'A': (A, -DEPTH + 1.0), 'B': (B, -DEPTH + 0.4), 'C': (Cc, -3.0)}
        labels = [((p.x, p.y, z), l, 'blue') for l, (p, z) in pos.items() if any(sp[2] == l for sp in f.get('spots', []))]
        at = {'dark weed': (A + Vector((-1.0, -4.0)), -DEPTH + 0.8), 'pale sand': (B + Vector((1.2, -1.6)), -DEPTH + 0.2), 'rocks, 3 m': (Cc + Vector((3.5, 0.0)), -3.2)}
        for x, yy, t in f.get('labels', []):
            p, z = at[t]; labels.append(((p.x, p.y, z), t))
        return labels, [], f.get('note'), -0.5, []

    # ---------------------------------------------------------------- anchor: the cut-away
    def scene_anchor(e, cfg):
        f = e['figure']; dep = float(f['depth'].split()[0]); draft = cfg.get('draft', 2.0)
        if cfg.get('motor'):    # a motor yacht of that length, her bow roller at the stem, about 2.5 m up
            import q_encounter_props as EP
            spin, mvis, mtop = EP.motor_yacht((0, 0), 180, cfg['motor']); bpy.context.view_layer.update()   # bow north: the model's bow lies on -heading
            mlo, mhi = K.bbox(mvis); bow = Vector(((mlo.x + mhi.x) / 2, mhi.y - 0.6, 2.5)); y = None
        else:
            y = K.load_yacht(); y.place(0, 0, heading=0).set_draft(draft)
            KW.antifoul_hull(y); bpy.context.view_layer.update()
            bow = y.world((10.95, 0.13, 3.72))
        sb = -dep + 0.07
        H = bow.z - sb
        state = cfg['state']; labels, arrows = [], []
        anchor_file = 'anchor-cqr.glb' if cfg.get('kedge') else 'anchor-delta.glb'
        root, objs = K.load_model(anchor_file, drop_planes=False)
        meshes = [o for o in objs if o.type == 'MESH']
        if cfg.get('kedge'):
            lo, hi = K.bbox(meshes); k = 1.3 / max(hi.x - lo.x, hi.y - lo.y, hi.z - lo.z); root.scale = (k,) * 3
        else:
            S = Matrix.Diagonal((1.7, 1.7, 1.7, 1.0)); root.matrix_world = Matrix.Rotation(deg(48 + 90), 4, 'Z') @ S @ Matrix.Translation((-0.48, -1.17, 0.0))
        bpy.context.view_layer.update()
        def put_anchor(at):
            lo, hi = K.bbox(meshes); c = (lo + hi) / 2
            root.location += Vector((at.x - c.x, at.y - c.y, (-dep - 0.12) - lo.z)); bpy.context.view_layer.update()
            lo, hi = K.bbox(meshes); return Vector(((lo.x + hi.x) / 2, hi.y if not cfg.get('kedge') else (lo.y + hi.y) / 2, sb + 0.15))
        if state == 'drop':
            at = Vector((bow.x, bow.y + 1.4, sb)); sh = put_anchor(at)
            if cfg.get('rope'):
                join = Vector((bow.x + 0.05, bow.y + 0.9, sb + cfg['rope']))
                KW.chain([sh + Vector((0, 0, 0.1)), sh + Vector((0, -0.2, 0.6)), join], link_len=0.2, wire=0.028)
                C.tube('rope', [join, bow.lerp(join, 0.5) + Vector((0.08, 0.1, 0)), bow], 0.03, 10, 1.0, C.simple('nylon', '#ece6d6', 0.6))
                labels.append(((join.x, join.y, join.z), '6 m chain, then nylon rope'))
            else:
                mid = bow.lerp(sh, 0.5) + Vector((0, 0.25, 0))
                KW.chain(KW.bezier(bow, mid + Vector((0, 0.1, 0.8)), mid + Vector((0, 0.15, -0.8)), sh + Vector((0, -0.1, 0.25)), 60) + [sh], link_len=0.2, wire=0.028)
        else:
            L = cfg['chain']
            if L < H * 2.0 or cfg.get('taut'):    # short and steep (or bar-tight): nearly straight, a little sag
                hor = math.sqrt(max(1.0, L * L - H * H)); end = Vector((bow.x, bow.y + hor, sb))
                pts = [bow.lerp(end, t) - Vector((0, 0, 0.35 * math.sin(math.pi * t))) for t in (i / 60 for i in range(61))]
                hang, lie = pts, []
            else:
                X = 12.5
                for _ in range(30):
                    a = 5.0
                    for _ in range(80):
                        fa = a * (math.cosh(X / a) - 1) - H; df = (math.cosh(X / a) - 1) - (X / a) * math.sinh(X / a); a -= fa / df
                    if a * math.sinh(X / a) < L - 3: break
                    X *= 0.85
                hang_len = a * math.sinh(X / a); lie_len = L - hang_len
                hang = [Vector((bow.x, bow.y + (X - x), sb + a * (math.cosh(x / a) - 1))) for x in (X * (1 - i / 160) for i in range(161))]
                touch = hang[-1]
                lie = [Vector((bow.x + 0.25 * math.sin(t * 9) * t, touch.y + (lie_len - 0.6) * t, sb)) for t in (i / 120 for i in range(1, 121))]
                end = lie[-1]
            sh = put_anchor(end + Vector((0, 0.9, 0)))
            KW.chain(hang + lie, link_len=0.2 if L < 20 else 0.26, wire=0.028 if L < 20 else 0.036)
            if 'Chain out: 12 m' in cfg['labels']:
                m = hang[len(hang) // 2]; labels.append(((m.x, m.y, m.z), 'Chain out: 12 m'))
            if cfg.get('snubber'):   # the hook on the chain 2.5 m out from the roller, the bridle back to both bow cleats, still slack
                acc = 0.0; hook = hang[-1]
                for a_, b_ in zip(hang, hang[1:]):
                    acc += (b_ - a_).length
                    if acc >= 2.5: hook = b_; break
                nyl = C.simple('snubber', '#f1ecd9', 0.6)
                C.cyl('chain-hook', 0.05, 0.03, 0.18, 12, K.mats()['galv'], tuple(hook + Vector((0, 0, 0.08))))
                for sd in (-1, 1):
                    cl = Vector((bow.x + sd * 0.55, bow.y - 1.2, bow.z + 0.05))
                    C.obj('cleat', C.rbox('cleat', (0.08, 0.28, 0.06), 0.02, 2), K.mats()['galv'], tuple(cl))
                    mid = cl.lerp(hook, 0.5) - Vector((0, 0, 0.45))
                    C.tube('snubber', [cl.lerp(mid, t / 6) if t <= 6 else mid.lerp(hook, (t - 6) / 6) for t in range(13)], 0.022, 10, 1.0, nyl)
                for text, where in cfg['labels'].items():
                    if where == 'hook': labels.append(((hook.x, hook.y, hook.z - 0.2), text))
                    if where == 'cleat': labels.append(((bow.x - 0.55, bow.y - 1.2, bow.z + 0.4), text))
            for text, where in cfg['labels'].items():
                if where == 'chain' and text != 'Chain out: 12 m':
                    m = hang[len(hang) // 3]; labels.append(((m.x, m.y, m.z), text))
        far = max(bow.y + 4, (sh.y if state == 'set' else bow.y) + 4)
        wd = (0.007, 0.012) if cfg.get('deep') else (0.02, 0.035)
        KW.water_body(depth=dep + 8, size=600.0, density=wd[0], color='#0f4a4f', absorb='#2f8f86', reflect=0.25, absorb_density=wd[1], center=(0, 15))
        KW.far_sea_ring(inner=300.0)
        cols = ('#8f8c78', '#a7a387', '#9a977f') if cfg.get('weed') else ('#8f9a7e', '#b2b593', '#a3a886') if cfg.get('flat') else ('#7d8669', '#99a07e', '#8b9274')
        KW.seabed(z=-dep, size=500.0 if cfg.get('deep') else 170.0, res=320 if cfg.get('deep') else 260, center=(0, 18), colors=cols)
        if not cfg.get('flat'):
            KW.stones(60 if not cfg.get('weed') else 30, ((-16, -12), (-3, 52)), -dep, scale=(0.15, 0.6))
            KW.stones(60, ((7, -14), (26, 52)), -dep, seed=8, scale=(0.15, 0.55))
        gl = 0.3 if cfg.get('weed') else 0.62
        KW.seagrass(((-22, -14), (-3, 56)), -dep, clumps=700 if cfg.get('weed') else 1400, length=gl)
        KW.seagrass(((7, -16), (26, 58)), -dep, clumps=800 if cfg.get('weed') else 1600, seed=9, length=gl)
        K.coast(distance=1500, bearing=270, height=90, town=False)
        if cfg.get('dusk'): K.day_sky(sun_az=250, sun_el=5, strength=0.2, haze=3.0); expo = 0.2
        else:
            az, el = cfg.get('sun', (120, 55)); K.day_sky(sun_az=az, sun_el=el, strength=0.25, haze=2.0); expo = -0.55
        dl = f['depth'] + (f" · {f['tide']}" if f.get('tide') else '')
        if cfg.get('deep'):
            # deep water: stand off far enough to see from the bow down to the bottom
            dist = dep * 1.7 + 6; mid = bow.y + 2.0
            KW.camera(Vector((dist, mid, 0.002)), Vector((0.0, mid, -dep * 0.42)), lens=20)
            gx, gy = 2.2, bow.y - 6.0
            labels.append(((gx, gy - 2.6 * (dist / 34), -dep / 2 - 0.2), dl, 'blue'))
            arrows += [((gx, gy, -dep * 0.45), (gx, gy, -0.05), 'blue'), ((gx, gy, -dep * 0.45), (gx, gy, -dep + 0.05), 'blue')]
            for text, where in cfg['labels'].items():
                if where == 'roller': labels.append(((bow.x, bow.y + 0.3, bow.z + 0.5), text))
        elif cfg.get('draft'):
            # as the original sounder figure: the camera at the waterline off the keel, draft and depth gauges side by side
            keel = [o for o in y.objs if o.type == 'MESH' and not o.hide_render and K.bbox([o])[0].z < -draft + 0.15]
            klo, khi = K.bbox(keel); kb = Vector(((klo.x + khi.x) / 2, (klo.y + khi.y) / 2, klo.z))
            KW.camera(Vector((13.0, kb.y + 0.6, 0.002)), Vector((0.0, kb.y + 1.2, -0.5)), lens=16)
            gx = 3.5; dg = Vector((gx, kb.y - 1.0, 0)); sg = Vector((gx, kb.y + 6.5, 0))
            labels.append(((sg.x + 3.0, sg.y - 1.0, -dep + 0.05), dl, 'blue'))
            arrows += [((sg.x, sg.y, -dep * 0.5), (sg.x, sg.y, -0.03), 'blue'), ((sg.x, sg.y, -dep * 0.5), (sg.x, sg.y, -dep + 0.03), 'blue')]
            for text, where in cfg['labels'].items():
                labels.append(((dg.x, dg.y - 2.2, -0.75), text, 'yellow'))
                arrows += [((dg.x, dg.y, -0.95), (dg.x, dg.y, -0.03), 'yellow'), ((dg.x, dg.y, -0.95), (dg.x, dg.y, -draft + 0.03), 'yellow')]
        else:
            near = state == 'drop' or (cfg['chain'] < 2.0 * H and not cfg.get('taut')) or cfg.get('near', False)
            if near: y0, y1 = bow.y - 13.0, max(bow.y + 6.0, far + 1.5)
            else: y0, y1 = -10.5, far + 2.5
            mid = (y0 + y1) / 2; dist = max(21.0, (y1 - y0) * (0.62 if near else 0.5) + (6 if near else 3))
            KW.camera(Vector((dist, mid, 0.002)), Vector((0.0, mid, -min(1.7, dep * (0.35 if near else 0.22)))), lens=21 if dist > 26 else 24)
            gx = 2.2; gy = bow.y - 7.5 if near else min(bow.y + 4.5, y1 - 2)
            labels.append(((gx, gy - 2.6 * (dist / 34), -dep / 2 - 0.2), dl, 'blue'))
            arrows += [((gx, gy, -dep * 0.45), (gx, gy, -0.05), 'blue'), ((gx, gy, -dep * 0.45), (gx, gy, -dep + 0.05), 'blue')]
            for text, where in cfg['labels'].items():
                if where == 'roller': labels.append(((bow.x, bow.y + 0.3, bow.z + 0.5), text))
        used = set(cfg['labels'])
        lines = [l for l in f.get('lines', []) if l not in used]
        return labels, arrows, f.get('title'), expo, lines

    # ---------------------------------------------------------------- day shapes
    SH = 1.25; GAP = 1.5
    def hoist(top, kinds, k=1.0, gap=GAP):
        """Shapes on a halyard hanging from `top`, top-down (as the article's day-shape figures)."""
        cs = []; z = 0.0; prev = 0.0; r = 0.3 * SH * k
        for i, kd in enumerate(kinds):
            half = {'ball': 0.3, 'cone-up': 0.3, 'cone-down': 0.3, 'diamond': 0.6, 'cylinder': 0.6}[kd] * SH * k
            z += (0.35 * k if i == 0 else gap * k - prev) + half; prev = half
            c = top - Vector((0, 0, z)); cs.append(c)
            if kd == 'ball': K.ball(c, r)
            elif kd in ('cone-up', 'cone-down'): K.cone(c, r, 0.6 * SH * k, up=(kd == 'cone-up'))
            elif kd == 'diamond':
                h = 1.2 * SH * k; K.cone(c + Vector((0, 0, h / 4)), r, h / 2, up=True); K.cone(c - Vector((0, 0, h / 4)), r, h / 2, up=False)
            elif kd == 'cylinder': C.cyl('cylinder', r, r, 1.2 * SH * k, 32, K.mats()['black'], c)
        bottom = (cs[-1] if cs else top) - Vector((0, 0, 0.9 * k))
        C.tube('halyard', [top, bottom], 0.012 * max(1, k * 0.7), 6, 1.0, C.simple('halyard', '#202224', 0.6))
        return cs

    WL_T = K.TRAWLER_WL
    def trawler(pos, heading, booms=True):
        root, objs = K.load_model('vessel-trawler.glb', drop_planes=False)
        bpy.context.view_layer.update()
        meshes = [o for o in objs if o.type == 'MESH']
        lo, hi = K.bbox(meshes); foot = max(hi.x - lo.x, hi.y - lo.y)
        for o in meshes:
            l, h = K.bbox([o])
            if max(h.x - l.x, h.y - l.y) > 0.9 * foot and len(o.data.polygons) <= 40: o.hide_render = True
            elif not booms and (h.z - l.z) < 0.4 and max(h.x - l.x, h.y - l.y) > 8 and h.z < 1.0: o.hide_render = True
        M = K.mats(); red = C.simple('trawler-red', '#9b2a22', 0.45, coat=0.4)
        def rule(c, name):
            if c is None: return None
            l = sum(c) / 3
            if l < 0.2: return M['navy']
            if c[0] > 0.5 and c[1] < 0.3: return red
            return None
        K.recolor(objs, rule)
        root.location = (pos[0], pos[1], -WL_T); root.rotation_euler = Euler((0, 0, deg(90 - heading)), 'XYZ')
        bpy.context.view_layer.update()
        K.trawler_paint(objs)                         # dark hull, red boot-top (her planking texture read pale)
        return root
    YARD = (-1.45, 2.35, 8.25)

    def ferry(pos, heading, length=85.0, sink=0.0):
        root, objs = K.load_model('vessel-ferry.glb', drop_planes=False)
        bpy.context.view_layer.update()
        meshes = [o for o in objs if o.type == 'MESH']
        for o in meshes:
            l, h = K.bbox([o])
            if (h.y - l.y) > 60: o.hide_render = True
        vis = [o for o in meshes if not o.hide_render]
        lo, hi = K.bbox(vis); k = length / (hi.x - lo.x); root.scale = (k,) * 3
        bpy.context.view_layer.update(); lo, hi = K.bbox(vis)
        c = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, 0)); root.location = Vector(root.location) - c
        piv = bpy.data.objects.new('ferry-pivot', None); C.col.objects.link(piv)
        root.parent = piv; piv.location = (pos[0], pos[1], -K.FERRY_WL * k - sink); piv.rotation_euler = (0, 0, deg(90 - heading))
        bpy.context.view_layer.update()
        return piv, vis, k

    def forestay_ball(y, t=0.42):
        a, b = K.FORESTAY; p = a.lerp(b, t)
        top = y.world((p.x, p.y, p.z)); cs = hoist(top, ['ball'])
        C.tube('downhaul', [cs[0] - Vector((0, 0, 0.4)), y.world((9.4, 0.13, 3.9))], 0.006, 6, 1.0, C.simple('downhaul', '#202224', 0.6))
        return cs[0]

    def scene_day(e, cfg):
        f = e['figure']; v = cfg['vessel']; labels = []
        own = cfg.get('own')
        if v.startswith('own'):
            if v == 'own-motorsail':
                y = K.load_yacht(name='own', sails={'main': True, 'genoa': None, 'boom': 14}); y.place(0, 0, heading=60, heel=-3)
                K.wake(y, 38, 8, 1.0)
                K.sea('breeze'); K.day_sky(sun_az=200, sun_el=40); K.coast(distance=1300, bearing=10, height=110, town=True)
                KW.camera(y.world((-16.0, -30.0, 14.0)), y.world((2.0, 0.13, 7.5)), lens=32); C.focus_on_centre(bpy.context.scene.camera, 16.0)
                return labels, [], f['note'], -0.7, []
            if v == 'own-anchored':
                y = K.load_yacht(name='own'); y.place(0, 0, heading=20); b = forestay_ball(y)
                for i, (brg, d, h) in enumerate(((268, 55, 25), (300, 95, 15), (248, 120, 20), (322, 150, 22), (282, 190, 18))):
                    K.load_yacht(name=f'other{i}', hull='navy' if i % 2 else 'white').place(d * math.sin(deg(brg)), d * math.cos(deg(brg)), heading=h)
                K.sea('calm'); K.day_sky(sun_az=230, sun_el=42); K.coast(distance=380, bearing=20, height=110, town=True)
                KW.camera(y.world((8.0, -26.0, 7.0)), y.world((5.0, 0.13, 7.5)), lens=32); C.focus_on_centre(bpy.context.scene.camera, 16.0)
                return labels, [], f['note'], -0.7, []
            if v == 'own-motor-anchored':   # our motor yacht at anchor, the data's ball hoisted at her radar mast
                import q_encounter_props as EP
                spin, mvis, mtop = EP.motor_yacht((0, 0), 200, cfg['length']); bpy.context.view_layer.update()   # bow to 020 (the model's bow lies on -heading)
                k = cfg['ball'] / 2 / (0.3 * SH)          # hoist() draws a ball of radius 0.3 * SH * k
                fw = Vector((math.sin(deg(20)), math.cos(deg(20)), 0))
                top = mtop + fw * 0.6 + Vector((0, 0, 1.4)); hoist(top, ['ball'], k=k)      # from a short staff on her roof
                C.cyl('ball-staff', 0.03, 0.025, 3.4, 8, K.mats()['galv'], tuple(top - Vector((0, 0, 1.65))))
                mlo, mhi = K.bbox(mvis); stem = Vector((0, 0, 0)) + fw * (cfg['length'] / 2 - 0.6) + Vector((0, 0, 2.4))
                C.tube('chain', [stem.lerp(stem + fw * 7 + Vector((0, 0, -2.6)), t / 10) - Vector((0, 0, 0.3 * math.sin(math.pi * t / 10))) for t in range(11)], 0.03, 8, 1.0, C.simple('chain', '#6b6e70', 0.5, 0.8))
                for i, (brg, d, h) in enumerate(((290, 70, 25), (250, 120, 15), (320, 150, 22))):
                    K.load_yacht(name=f'other{i}', hull='navy' if i % 2 else 'white').place(d * math.sin(deg(brg)), d * math.cos(deg(brg)), heading=h)
                K.sea('calm'); K.day_sky(sun_az=230, sun_el=42); K.coast(distance=420, bearing=10, height=110, town=True)
                eye = Vector((34.0, -24.0, 3.4)); KW.camera(eye, top - Vector((0, 0, 3.4)), lens=42); C.focus_on_centre(bpy.context.scene.camera, 16.0)
                return labels, [], f['note'], -0.7, []
            # own-deck: from the cockpit, looking forward past the mast to the ball under the forestay
            y = K.load_yacht(name='own'); y.place(0, 0, heading=0); b = forestay_ball(y)
            K.wake(y, 30, 7, 0.7)
            K.sea('calm'); K.day_sky(sun_az=150, sun_el=40); K.coast(distance=420, bearing=300, height=120, town=True); K.coast(distance=900, bearing=60, height=90, town=False, seed=5)
            eye = y.world((1.6, -1.9, 5.6)); KW.camera(eye, y.world((9.0, 0.13, 7.6)), lens=22)
            return labels, [], f['note'], -0.6, []
        # we are on our own boat, looking at the other vessel from the foredeck
        sails = {'sail': {'main': True, 'genoa': 'port', 'boom': 10}, 'sail-port': {'main': True, 'genoa': 'starboard', 'boom': -10}}.get(own)
        me = K.load_yacht(name='own', sails=sails); me.place(0, 0, heading=0, heel=(-10 if own == 'sail' else 10 if own == 'sail-port' else 0))
        eye = me.world((7.2, -1.2, 5.1)) if own != 'sail-port' else me.world((7.2, 1.4, 5.1))
        brg, dist = cfg['brg'], cfg['dist']
        p = Vector((math.sin(deg(brg)) * dist, math.cos(deg(brg)) * dist, 0)) + Vector((eye.x, eye.y, 0))
        K.sea('breeze'); K.day_sky(sun_az=150, sun_el=40)
        if cfg.get('harbour'):
            K.breakwater((p.x - 160, p.y + 170), (p.x - 20, p.y + 130), width=10, height=3.0, light='green')
            K.coast(distance=520, bearing=brg + 10, height=110, town=True)
        if cfg.get('coast'): K.coast(distance=650, bearing=brg, height=150, town=True)
        if v == 'trawler':
            t = trawler(p, cfg['hdg'], booms=cfg.get('booms', True))
            top = t.matrix_world @ Vector(YARD); cs = hoist(top, cfg['kinds'], gap=1.35 if len(cfg['kinds']) == 3 else GAP)
            bpy.context.view_layer.update(); vlo, vhi = K.bbox([o for o in t.children_recursive if o.type == 'MESH' and not o.hide_render])
            look = Vector(((vlo.x + vhi.x) / 2, (vlo.y + vhi.y) / 2, cs[0].z * 0.42)); lens = 95
        elif v == 'ship':
            piv, vis, k = ferry(p, cfg['hdg'], sink=1.2 if cfg.get('laden') else 0.0)
            bpy.context.view_layer.update(); lo, hi = K.bbox(vis)
            mast = max(vis, key=lambda o: K.bbox([o])[1].z); ml, mh = K.bbox([mast])
            top = Vector(((ml.x + mh.x) / 2, (ml.y + mh.y) / 2, mh.z - 0.3))
            cs = hoist(top, cfg['kinds'], k=2.0); look = cs[-1] + Vector((0, 0, -9.0)); lens = 75
        elif v == 'yacht-motorsail':
            o = K.load_yacht(name='other', sails={'main': True, 'genoa': None, 'boom': 18}); o.place(p.x, p.y, heading=cfg['hdg'], heel=-4)
            K.wake(o, 30, 8, 0.9)
            top = o.world((6.6, 0.13, 13.2)); cs = hoist(top, cfg['kinds'])
            C.tube('halyard-up', [o.world((4.95, 0.13, 13.6)), top], 0.01, 6, 1.0, C.simple('halyard2', '#202224', 0.6))
            look = o.world((4.9, 0.13, 8.5)); lens = 55
        else:   # yacht-anchored
            o = K.load_yacht(name='other'); o.place(p.x, p.y, heading=cfg['hdg']); b = forestay_ball(o)
            K.coast(distance=700, bearing=brg - 5, height=140, town=True)
            K.load_yacht(name='far1', hull='navy').place(p.x - 60, p.y + 90, heading=cfg['hdg'] + 8)
            look = o.world((4.5, 0.13, 6.5)); lens = 40
        cd = bpy.data.cameras.new('cam'); cd.lens = lens; cd.clip_end = 6000
        cam = bpy.data.objects.new('cam', cd); C.col.objects.link(cam); bpy.context.scene.camera = cam
        cam.location = eye; cam.rotation_euler = (look - eye).to_track_quat('-Z', 'Y').to_euler()
        C.focus_on_centre(cam, 11.0)
        return labels, [], f['note'], -0.7, []

    # ---------------------------------------------------------------- main
    def main():
        e = next(x for x in entries(TYPE) if x['id'] == QID)
        C.reset()
        fn = {'bay': lambda: scene_bay(e, BAY[QID]), 'anchor': lambda: scene_anchor(e, ANCHOR[QID]), 'dayshape': lambda: scene_day(e, DAY[QID])}[TYPE]
        labels, arrows, note, expo, lines = fn()
        out = os.path.join(QDIR, QID, '3d.jpg')
        extra = {'lines': lines}
        if TYPE == 'bay' and BAY[QID].get('night'): extra['bloom'] = 0.8
        C.render(out, SAMPLES, SCALE, expo, labels, note, space='blender', arrows=arrows, extra=extra)
        with open(os.path.join(QDIR, QID, '3d.labels.json')) as fh: lab = json.load(fh)
        write_plan_ru(TYPE, e, lab)

if __name__ == '__main__':
    if '--plans' in ARGV or not BL:
        miss = 0
        for e in entries(TYPE):
            if QID and e['id'] != QID: continue
            miss += len(write_plan_ru(TYPE, e))
        print('plans written', TYPE, 'missing ru:', miss)
    else:
        main()
