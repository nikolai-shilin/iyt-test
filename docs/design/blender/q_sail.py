# Bareboat-skipper test questions, figure type "sail": our yacht seen from a drone, north up, sailing on the
# question's heading with the wind from its direction, the sails set for that wind (boom and genoa to leeward), the
# red no-go fan of ±45° round the wind when the figure has nogo. Printed: the wind arrow and the figure's note only,
# never the point of sail or the tack (that is what the questions ask). The plan (shown with the answer) names
# them and gives the reasoning. See q_misc.py for how to run it.
#   blender --background --factory-startup --python docs/design/blender/q_sail.py -- --id bs-004
#   python3 docs/design/blender/q_sail.py --all          plan.json and ru.json for every sail question
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import q_misc as Q

def rel_wind(f):
    """Wind relative to the bow, -180..180, + from starboard; and whether the boom goes to port."""
    w, h = f.get('wind', 0), f['hdg']
    rel = ((w - h + 540) % 360) - 180
    return rel, (rel > 0 or rel == -180)          # a dead run: boom to port, as figures.js draws it

def point_of_sail(off):
    if off < 10: return 'in irons'
    if off < 30: return 'in the no-go zone'
    if off < 52: return 'close-hauled'
    if off < 75: return 'close reach'
    if off < 110: return 'beam reach'
    if off < 155: return 'broad reach'
    return 'run'

# trim by the angle off the wind: boom angle off the centreline, heel
def trim(off):
    if off < 30: return 0, 0
    if off < 52: return 10, 14
    if off < 75: return 20, 12
    if off < 110: return 38, 9
    if off < 155: return 60, 5
    return 80, 2

# per question: the scene (sea, boom, heel, flapping sails, wake) where the story needs it, and the plan's reasoning.
# arcs: turns drawn on the plan (from heading, to heading, pill); goes: a new heading as a dashed arrow (heading, pill)
SPEC = {
    'bs-001': dict(boom=18, title='Which tack · the wind over the starboard side',
                   key=['Wind over the starboard side, boom out to port', 'The tack is named after the side the wind comes over: starboard tack']),
    'bs-003': dict(title='Bearing away · from close-hauled to a run', arcs=[(315, 200, 'bear away')],
                   key=['Bearing away turns the bow away from the wind, here to port', 'Close-hauled, then a reach, then a run: ease the sheets as you turn']),
    'bs-004': dict(title='Points of sail · beam reach', key=['Wind from 270°, heading 000°: 90° off the bow', 'Wind on the beam: a beam reach, sails eased about halfway']),
    'bs-005': dict(boom=4, camber=0.035, heel=0, wake=0, title='The no-go zone',
                   key=['015° is only 15° off the wind, inside the no-go zone', 'The sails flap and the boat stops: bear away to 045° or more']),
    'bs-009': dict(arcs=[(350, 20, 'gybe')], title='Before a gybe',
                   key=['Running, wind on the port quarter: the stern is about to cross the wind', 'Centre the mainsheet and call "Gybe-ho" before you turn']),
    'bs-101': dict(title='Points of sail · broad reach', key=['Wind 135° off the bow, over the quarter', 'Between a beam reach and a run: a broad reach']),
    'bs-102': dict(title='Points of sail · close-hauled', key=['315° is 45° off the wind: as close as the sails stay full', 'Sails sheeted in hard: close-hauled']),
    'bs-103': dict(title='Points of sail · close reach', key=['060° is 60° off the wind', 'Between close-hauled (45°) and a beam reach (90°): a close reach']),
    'bs-104': dict(boom=35, title='Points of sail · run', key=['Wind dead astern: a run', 'Ease the main right out; the risk is an accidental gybe']),
    'bs-105': dict(boom=10, heel=10, title='Bearing away · ease the sheets', key=['Borne away from 45° to 90° off the wind: a beam reach', 'Ease both sheets until the sails just stop luffing']),
    'bs-106': dict(boom=8, heel=5, flap=0.18, wake=0.6, goes=[(65, 'bear away to 065°')], title='Headed · the wind has veered',
                   key=['The wind veered 20°: 045° is now only 25° off it, inside the no-go zone', 'You are headed: bear away to keep the sails full, or tack']),
    'bs-107': dict(goes=[(70, 'luff up: 070°')], title='Luffing up 20°', key=['Luffing up turns the bow towards the wind', '090° − 20° = 070°']),
    'bs-108': dict(goes=[(270, '270° · beam reach')], title='Bearing away 45°',
                   key=['Bearing away turns the bow away from the wind: 315° − 45° = 270°', 'Wind now on the beam: a beam reach']),
    'bs-109': dict(arcs=[(315, 45, 'tack: 045°')], title='Tacking through 90°',
                   key=['Tacking turns the bow through the wind, 45° each side of it', 'Close-hauled on 315° tacks to 045°']),
    'bs-127': dict(arcs=[(45, 315, 'tack: 315°')], title='Upwind · tacking',
                   key=['Upwind you zig-zag on the two close-hauled courses', 'Tack: turn the bow through the wind, from 045° to 315°']),
    'bs-153': dict(sea='calm', genoa_camber=0.03, genoa_pole=True, title='Dead run · goose-winged',
                   key=['On a dead run the main blankets the genoa', 'Goose-wing: set the genoa on the other side, held out by a pole']),
    'bs-175': dict(flap=0.35, wake=0, camber=0.015, genoa_camber=0.02, title='In irons',
                   key=['Head to wind with no way on: in irons', 'Back the genoa to push the bow off, then sail away']),
    'bs-325': dict(sea='fresh', preventer=True, title='Dead run in a swell',
                   key=['Rolling dead downwind, the boom can swing across hard', 'Rig a preventer and keep heads clear of the boom']),
    'bs-510': dict(goes=[(45, 'water track 045°')], title='Leeway · close-hauled',
                   key=['Wind on the port bow pushes you to starboard, downwind', 'Heading 040°T + leeway 5° = water track 045°T']),
    'bs-644': dict(heel=24, title='Overpowered · close-hauled',
                   key=['Close-hauled with the true wind rising: heeling hard, weather helm', 'Reef now, before the wind builds further']),
    'bs-645': dict(sea='calm', goes=[(315, 'beating back')], title='Running, then beating back',
                   key=['Running, your speed is taken off the true wind', 'Upwind it is added: much more wind and spray, so reef first']),
    # yachtmaster offshore
    'yof-760': dict(sea='fresh', arcs=[(50, 310, 'tack: 310°')], title='Damage on the lee bow · tack',
                    key=['On port tack she heels to starboard and buries the crack', 'Tack: on starboard tack she heels to port and the crack lifts clear']),
    # hove-to: the genoa backed to windward, the main eased a little, forereaching (name: the plan's own words, not the point of sail)
    'yof-844': dict(sea='fresh', backed=True, boom=22, heel=6, wake=0.45, name='hove-to, forereaching', goes=[(50, 'lie about 050°')],
                    title='Hove-to · stop the forereaching',
                    key=['Forereaching at 3 kn, nearly beam-on: the main is still driving', 'Ease the main further, lash the helm harder to leeward: she lies about 50° off']),
}

RU = {
    'Wind': 'Ветер', 'boom': 'гик', 'genoa': 'генуя', 'preventer': 'завал-таль', 'no-go zone': 'мёртвый сектор',
    'in irons': 'в левентике', 'in the no-go zone': 'в мёртвом секторе', 'close-hauled': 'бейдевинд', 'close reach': 'полный бейдевинд',
    'beam reach': 'галфвинд', 'broad reach': 'бакштаг', 'run': 'фордевинд', 'starboard tack': 'правый галс', 'port tack': 'левый галс',
    'bear away': 'уваливайтесь', 'gybe': 'поворот фордевинд', 'tack: 045°': 'оверштаг: 045°', 'tack: 315°': 'оверштаг: 315°',
    'bear away to 065°': 'увалиться на 065°', 'luff up: 070°': 'привестись: 070°', '270° · beam reach': '270° · галфвинд',
    'water track 045°': 'путь 045°', 'beating back': 'назад в лавировку', 'genoa poled out': 'генуя на спинакер-гике',
    'Which tack · the wind over the starboard side': 'Какой галс · ветер с правого борта',
    'Wind over the starboard side, boom out to port': 'Ветер с правого борта, гик слева',
    'The tack is named after the side the wind comes over: starboard tack': 'Галс называют по борту, с которого дует ветер: правый галс',
    'Bearing away · from close-hauled to a run': 'Уваливание · от бейдевинда к фордевинду',
    'Bearing away turns the bow away from the wind, here to port': 'Уваливаясь, отводите нос от ветра, здесь влево',
    'Close-hauled, then a reach, then a run: ease the sheets as you turn': 'Бейдевинд, галфвинд, бакштаг, фордевинд: травите шкоты по ходу поворота',
    'Points of sail · beam reach': 'Курсы относительно ветра · галфвинд',
    'Wind from 270°, heading 000°: 90° off the bow': 'Ветер 270°, курс 000°: 90° от носа',
    'Wind on the beam: a beam reach, sails eased about halfway': 'Ветер в борт: галфвинд, паруса потравлены наполовину',
    'The no-go zone': 'Мёртвый сектор',
    '015° is only 15° off the wind, inside the no-go zone': 'Курс 015° — всего 15° к ветру, внутри мёртвого сектора',
    'The sails flap and the boat stops: bear away to 045° or more': 'Паруса полощут, яхта встаёт: уваливайтесь до 045° и дальше',
    'Before a gybe': 'Перед поворотом фордевинд',
    'Running, wind on the port quarter: the stern is about to cross the wind': 'Фордевинд, ветер в левую раковину: корма вот-вот пересечёт ветер',
    'Centre the mainsheet and call "Gybe-ho" before you turn': 'Выберите грота-шкот в диаметраль и скомандуйте «Поворот фордевинд!»',
    'Points of sail · broad reach': 'Курсы относительно ветра · бакштаг',
    'Wind 135° off the bow, over the quarter': 'Ветер 135° от носа, в раковину',
    'Between a beam reach and a run: a broad reach': 'Между галфвиндом и фордевиндом: бакштаг',
    'Points of sail · close-hauled': 'Курсы относительно ветра · бейдевинд',
    '315° is 45° off the wind: as close as the sails stay full': 'Курс 315° — 45° к ветру: острее паруса не работают',
    'Sails sheeted in hard: close-hauled': 'Шкоты выбраны втугую: бейдевинд',
    'Points of sail · close reach': 'Курсы относительно ветра · полный бейдевинд',
    '060° is 60° off the wind': 'Курс 060° — 60° к ветру',
    'Between close-hauled (45°) and a beam reach (90°): a close reach': 'Между бейдевиндом (45°) и галфвиндом (90°): полный бейдевинд',
    'Points of sail · run': 'Курсы относительно ветра · фордевинд',
    'Wind dead astern: a run': 'Ветер точно в корму: фордевинд',
    'Ease the main right out; the risk is an accidental gybe': 'Грот вытравлен полностью; опасность — случайный переброс гика',
    'Bearing away · ease the sheets': 'Уваливание · травите шкоты',
    'Borne away from 45° to 90° off the wind: a beam reach': 'Увалились с 45° до 90° к ветру: галфвинд',
    'Ease both sheets until the sails just stop luffing': 'Травите оба шкота, пока паруса не окажутся на грани заполаскивания',
    'Headed · the wind has veered': 'Ветер зашёл · курс стал острее',
    'The wind veered 20°: 045° is now only 25° off it, inside the no-go zone': 'Ветер зашёл на 20°: курс 045° теперь лишь 25° к нему, в мёртвом секторе',
    'You are headed: bear away to keep the sails full, or tack': 'Ветер зашёл: уваливайтесь, чтобы паруса работали, или делайте поворот',
    'Luffing up 20°': 'Привестись на 20°',
    'Luffing up turns the bow towards the wind': 'Приводясь, поворачиваете нос к ветру',
    '090° − 20° = 070°': '090° − 20° = 070°',
    'Bearing away 45°': 'Увалиться на 45°',
    'Bearing away turns the bow away from the wind: 315° − 45° = 270°': 'Уваливаясь, отводите нос от ветра: 315° − 45° = 270°',
    'Wind now on the beam: a beam reach': 'Теперь ветер в борт: галфвинд',
    'Tacking through 90°': 'Поворот оверштаг на 90°',
    'Tacking turns the bow through the wind, 45° each side of it': 'Оверштаг проводит нос через ветер, по 45° в каждую сторону',
    'Close-hauled on 315° tacks to 045°': 'Бейдевинд 315° после поворота — 045°',
    'Upwind · tacking': 'Против ветра · лавировка',
    'Upwind you zig-zag on the two close-hauled courses': 'Против ветра идут зигзагом, двумя бейдевиндами',
    'Tack: turn the bow through the wind, from 045° to 315°': 'Поворот оверштаг: нос через ветер, с 045° на 315°',
    'Dead run · goose-winged': 'Чистый фордевинд · бабочкой',
    'On a dead run the main blankets the genoa': 'На чистом фордевинде грот закрывает генуе ветер',
    'Goose-wing: set the genoa on the other side, held out by a pole': 'Поставьте геную бабочкой на другой борт, вынесите её гиком',
    'In irons': 'В левентике',
    'Head to wind with no way on: in irons': 'Носом к ветру, хода нет: левентик',
    'Back the genoa to push the bow off, then sail away': 'Вынесите геную на ветер, она отбросит нос, и уходите',
    'Dead run in a swell': 'Чистый фордевинд на зыби',
    'Rolling dead downwind, the boom can swing across hard': 'Яхту валяет на фордевинде, гик может резко перебросить',
    'Rig a preventer and keep heads clear of the boom': 'Заведите завал-таль, головы — ниже гика',
    'Leeway · close-hauled': 'Дрейф · бейдевинд',
    'Wind on the port bow pushes you to starboard, downwind': 'Ветер слева по носу сносит вас вправо, под ветер',
    'Heading 040°T + leeway 5° = water track 045°T': 'ИК 040° + дрейф 5° = путь 045°',
    'Overpowered · close-hauled': 'Слишком много парусов · бейдевинд',
    'Close-hauled with the true wind rising: heeling hard, weather helm': 'Бейдевинд, ветер крепчает: большой крен, яхта приводится',
    'Reef now, before the wind builds further': 'Берите риф сейчас, пока ветер не усилился',
    'tack: 310°': 'оверштаг: 310°', 'Damage on the lee bow · tack': 'Пробоина в подветренной скуле · поворот',
    'On port tack she heels to starboard and buries the crack': 'На левом галсе крен на правый борт — трещина под водой',
    'Tack: on starboard tack she heels to port and the crack lifts clear': 'Поворот: на правом галсе крен на левый борт, трещина выходит из воды',
    'hove-to, forereaching': 'в дрейфе, идёт вперёд', 'lie about 050°': 'лечь около 050°', 'Hove-to · stop the forereaching': 'В дрейфе · остановите ход вперёд',
    'Forereaching at 3 kn, nearly beam-on: the main is still driving': 'Идёт вперёд 3 уз почти лагом: грот всё ещё тянет',
    'Ease the main further, lash the helm harder to leeward: she lies about 50° off': 'Потравите грот ещё, руль круче под ветер: встанет около 50° к ветру',
    'Running, then beating back': 'Фордевинд, потом назад в лавировку',
    'Running, your speed is taken off the true wind': 'На фордевинде скорость яхты вычитается из ветра',
    'Upwind it is added: much more wind and spray, so reef first': 'Против ветра — прибавляется: ветра и брызг куда больше, сначала риф',
}

# ---------- the plan (pure Python) ----------
def ray(b, d):
    a = math.radians(b); return [round(d * math.sin(a), 1), round(-d * math.cos(a), 1)]

def adiff(a, b):
    return abs(((a - b + 540) % 360) - 180)

MPP, SC = 1.3, 2.2                    # the plan's metres per pixel and boat scale (fixed: pills are placed in pixels)

def pill_box(text, cx, cy, size=24):
    w = len(text) * size * 0.58 + size * 1.4; h = size * 1.7
    return (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)

def hit(a, b, pad=18):
    return not (a[2] + pad < b[0] or b[2] + pad < a[0] or a[3] + pad < b[1] or b[3] + pad < a[1])

def plan(x):
    f = x['figure']; s = SPEC.get(x['id'], {}); w, h = f.get('wind', 0), f['hdg']
    rel, port = rel_wind(f); off = abs(rel); b = s.get('boom', trim(off)[0])
    pos = point_of_sail(off)
    tack = '' if off < 30 else ('starboard tack' if port else 'port tack')
    nogo = {'pts': [[0, 0], ray(w - 45, 260), ray(w - 20, 280), ray(w, 285), ray(w + 20, 280), ray(w + 45, 260)], 'c': 'red', 'fill': 'rgba(224,37,27,.08)'}
    mast = ray(h, 18); bb = h + 180 + (b if port else -b)
    end = [mast[0] + ray(bb, 150)[0], mast[1] + ray(bb, 150)[1]]
    paths = [{'pts': [mast, end], 'c': 'line', 'w': 12}]
    R = 26 * SC                                         # schematic(): the boat's radius in pixels
    px = lambda p: (p[0] / MPP, p[1] / MPP)
    # what is already drawn, in pixels from the boat: hull, the You pill, the heading arrow and its figure, the corners
    boxes = [(-R * 0.75, -R * 0.75, R * 0.75, R * 0.75), pill_box('You', 0, R + 30, 28), (-560, -328, 290, -235)]
    hx, hy = ray(h, R + 104); boxes.append((hx - 40, hy - 22, hx + 40, hy + 22))
    boxes += [(550 - 90, -328, 640, -120), (-640, -328, -500, -200)]
    pts = [ray(h, d) for d in range(0, int(R + 70), 12)]
    def seg(a, c, n=12): return [[a[0] + (c[0] - a[0]) * k / n, a[1] + (c[1] - a[1]) * k / n] for k in range(n + 1)]
    pts += [px(p) for p in seg(mast, end)]
    texts = []
    def place(text, cands, kind='accent'):      # cands: (bearing, radius in pixels)
        for b_, r_ in cands:
            cx, cy = ray(b_, r_); bx = pill_box(text, cx, cy)
            if bx[0] < -630 or bx[2] > 630 or bx[1] < -320 or bx[3] > 320: continue
            if any(hit(bx, o) for o in boxes) or any(bx[0] - 6 < q[0] < bx[2] + 6 and bx[1] - 6 < q[1] < bx[3] + 6 for q in pts): continue
            boxes.append(bx); texts.append({'x': round(cx * MPP, 1), 'z': round(cy * MPP, 1), 'text': text, 'kind': kind}); return
        raise SystemExit(f"{x['id']}: no room for {text!r}")
    around = lambda b0, r0: [(b0 + db, r0 + dr) for dr in (0, 30, 60, -25, 90, -50) for db in (0, 12, -12, 24, -24, 36, -36, 50, -50, 65, -65)]
    if s.get('genoa_pole'):     # the genoa poled out on the other side
        fs = ray(h, 90); ge = h + 180 + (-1 if port else 1) * 80; ce = [fs[0] + ray(ge, 150)[0], fs[1] + ray(ge, 150)[1]]
        paths.append({'pts': [fs, ce], 'c': 'course', 'w': 8, 'dash': '12 8'}); pts += [px(p) for p in seg(fs, ce)]
    if s.get('preventer'):      # boom end led forward to the bow
        bow = ray(h, 70); paths.append({'pts': [end, bow], 'c': 'line', 'w': 6, 'dash': '10 8'}); pts += [px(p) for p in seg(end, bow)]
    for to, text in s.get('goes', []):
        a_, c_ = ray(to, 140), ray(to, 300)
        paths.append({'pts': [a_, c_], 'c': 'course', 'w': 6, 'dash': '14 10', 'arrow': True}); pts += [px(p) for p in seg(a_, c_)]
    arcs = []
    for a0, a1, text in s.get('arcs', []):
        d = ((a1 - a0 + 540) % 360) - 180; n = 14
        ap = [ray(a0 + d * k / n, 290) for k in range(n + 1)]
        paths.append({'pts': ap, 'c': 'course', 'w': 6, 'arrow': True}); pts += [px(p) for p in ap]; arcs.append((a0 + d / 2, text))
    pts = [p for p in pts if (p[0] ** 2 + p[1] ** 2) ** 0.5 > R * 0.75]
    for to, text in s.get('goes', []): place(text, around(to, 270))
    for mid, text in arcs: place(text, around(mid, 270))
    place('no-go zone', around(w, 245), 'red')
    if s.get('genoa_pole'): place('genoa poled out', around(ge, 150))
    if s.get('preventer'): place('preventer', around(math.degrees(math.atan2(end[0] + bow[0], -(end[1] + bow[1]))), 140))
    place('boom', around(bb, 130), 'light')
    name = s.get('name') or pos + (' · ' + tack if tack else '')
    place(name, [(bb2, r_) for r_ in (200, 235, 270, 300) for bb2 in (180, 0, 160, 200, 20, 340, 135, 225, 45, 315, 90, 270)])
    title = s.get('title') or f'Points of sail · {pos}'
    return {'noScale': True, 'sch': {'padPx': 70, 'mpp': MPP, 'wind': w, 'title': title, 'key': s['key'], 'zones': [nogo],
            'boats': [{'you': True, 'x': 0, 'z': 0, 'hdg': h, 'noHeading': False, 'scale': SC}], 'paths': paths, 'texts': texts,
            'fit': [{'x': -830, 'z': -425}, {'x': 830, 'z': 425}]}}, name

def meta(x):
    """plan.json and ru.json for one question; returns the 3D labels' texts (for the render)."""
    f = x['figure']; A, name = plan(x)
    Q.save(x['id'], 'plan.json', A)
    ru = dict(RU); ru.update(x['ru'])
    pos, _, tack = name.partition(' · ')
    ru[name] = RU[name] if name in RU else RU[pos] + (' · ' + RU[tack] if tack else '')
    english = ['Wind'] + ([f['note']] if f.get('note') else []) + Q.plan_strings(A)
    Q.write_ru(x['id'], english, ru)

if not Q.IN_BLENDER:
    xs = Q.items('sail') if Q.flag('--all') else [Q.item('sail', Q.arg('--id', 'bs-004'))]
    for x in xs: meta(x); print(x['id'], 'plan + ru')
    sys.exit(0)

# ---------- the render (Blender) ----------
import bpy, bmesh
from mathutils import Vector
import common as C, kit as K
Q.no_spinnaker(K)

def no_go_fan(wind, r=34.0, half=45.0, z=0.35):
    """A thin red, half-transparent fan on the water round the wind, as in art_terms_b.py, turned to the wind."""
    bm = bmesh.new(); c = bm.verts.new((0, 0, z)); ring = []
    for i in range(25):
        a = math.radians(wind - half + 2 * half * i / 24); ring.append(bm.verts.new((r * math.sin(a), r * math.cos(a), z)))
    for i in range(24): bm.faces.new((c, ring[i], ring[i + 1]))
    me = bpy.data.meshes.new('nogo'); bm.to_mesh(me); bm.free()
    m, nt, b, out = C.new_mat('nogo')
    em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (0.9, 0.05, 0.03, 1); em.inputs['Strength'].default_value = 1.6
    tp = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader'); mx.inputs['Fac'].default_value = 0.18
    nt.links.new(tp.outputs[0], mx.inputs[1]); nt.links.new(em.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], out.inputs['Surface'])
    o = C.obj('nogo', me, m); o.visible_shadow = False
    o.visible_diffuse = o.visible_glossy = o.visible_transmission = False     # it must not tint the sails red
    edge = C.simple('nogo-edge', '#e0251b', 0.6)
    for s in (-1, 1):
        a = math.radians(wind + s * half); d = Vector((math.sin(a), math.cos(a), 0))
        for k in range(8):
            p0 = d * (5 + k * 3.8); p1 = d * (5 + k * 3.8 + 2.2)
            C.tube('nogo-edge', [p0 + Vector((0, 0, z + 0.05)), p1 + Vector((0, 0, z + 0.05))], 0.18, 6, 1.0, edge)
    return [Vector((r * math.sin(math.radians(wind + t)), r * math.cos(math.radians(wind + t)), 0)) for t in (-45, -22, 0, 22, 45)]

def flap(strength):
    tex = bpy.data.textures.new('flap', 'CLOUDS'); tex.noise_scale = 0.9
    for o in bpy.data.objects:
        if o.name.startswith(('main', 'genoa')) and o.type == 'MESH':
            md = o.modifiers.new('flap', 'DISPLACE'); md.texture = tex; md.strength = strength; md.mid_level = 0.5
            o.modifiers.move(len(o.modifiers) - 1, 0)

def fit_camera(pts, bearing, el, lens):
    """A camera on compass `bearing` from the action, `el` degrees up, that holds every point inside the frame with
    room for the note at the top: aim at their middle, back off until they fit, re-aim at what it sees."""
    from bpy_extras.object_utils import world_to_camera_view
    sc = bpy.context.scene; cam = K.camera((0, -1, 1), (0, 0, 0), lens)
    a, e = math.radians(bearing), math.radians(el)
    back = Vector((math.sin(a) * math.cos(e), math.cos(a) * math.cos(e), math.sin(e)))
    c = sum(pts, Vector()) / len(pts); c.z = 0
    U0, U1, V0, V1 = 0.07, 0.93, 0.08, 0.84                  # v from the bottom; the note sits over the top 16 %
    def aim(c, D):
        cam.location = c + back * D; cam.rotation_euler = (-back).to_track_quat('-Z', 'Y').to_euler(); bpy.context.view_layer.update()
        q = [world_to_camera_view(sc, cam, p) for p in pts]
        return min(v.x for v in q), max(v.x for v in q), min(v.y for v in q), max(v.y for v in q)
    D = 40.0
    for _ in range(4):
        lo, hi = 20.0, 400.0
        for _ in range(30):
            D = (lo + hi) / 2; u0, u1, v0, v1 = aim(c, D)
            if u0 >= U0 and u1 <= U1 and v0 >= V0 and v1 <= V1: hi = D
            else: lo = D
        D = hi; u0, u1, v0, v1 = aim(c, D)
        # re-aim: move the look point by the frame's offset, in metres at the look distance
        fw = 2 * D * math.tan(cam.data.angle_x / 2) if hasattr(cam.data, 'angle_x') else D * 1.2; fh = fw * 800 / 1280
        right = cam.matrix_world.to_quaternion() @ Vector((1, 0, 0)); up = cam.matrix_world.to_quaternion() @ Vector((0, 1, 0))
        du = (u0 + u1) / 2 - (U0 + U1) / 2; dv = (v0 + v1) / 2 - (V0 + V1) / 2
        up_g = Vector((up.x, up.y, 0)); up_g = up_g.normalized() / max(0.3, math.sin(e)) if up_g.length else up_g
        c = c + right * du * fw + up_g * dv * fh; c.z = 0
    aim(c, D * 1.02)
    return cam

def render(x):
    f = x['figure']; s = SPEC.get(x['id'], {}); w, h = f.get('wind', 0), f['hdg']
    rel, port = rel_wind(f); off = abs(rel)
    b, heel = trim(off); b = s.get('boom', b); heel = s.get('heel', heel)
    sails = {'main': True, 'genoa': 'port' if port != bool(s.get('backed')) else 'starboard', 'boom': b if port else -b}   # backed: to windward
    if 'camber' in s: sails['camber'] = s['camber']
    if 'genoa_camber' in s: sails['genoa_camber'] = s['genoa_camber']
    C.reset()
    y = K.load_yacht(name='you', sails=sails).place(0, 0, heading=h, heel=-heel if port else heel)
    if s.get('flap', 0.35 if off < 10 else 0): flap(s.get('flap', 0.35))
    wake = s.get('wake', 0 if off < 10 else 1.0)
    if wake: K.wake(y, 30 if off > 150 else 26, 7, wake)
    K.sea(s.get('sea', 'breeze'), size=40.0, repeat=10)
    # the sun over the camera's left shoulder (set below, once the camera's side is known)
    pts = [y.world(p) for p in ((10.8, 0.13, 3.5), (-3.8, 0.13, 3.5), (K.MAST.x, K.MAST.y, 22.5))]
    pts += [y.world((K.MAST.x - 5.5 * math.cos(math.radians(b)), K.MAST.y + (1 if port else -1) * 5.5 * math.sin(math.radians(b)), 3.6))]
    if f.get('nogo'): pts += no_go_fan(w)
    # the wind arrow upwind of the boat, 60° off the wind axis on the side clear of her bow and wake
    u = Vector((math.sin(math.radians(w)), math.cos(math.radians(w)), 0))
    side = max((60, -60), key=lambda d: min(adiff(w + d, h), adiff(w + d, h + 180)))
    a = math.radians(w + side); mid = Vector((math.sin(a), math.cos(a), 0)) * 22 + Vector((0, 0, 6))
    w0, w1 = mid + u * 7.5, mid - u * 7.5; pts += [w0, w1, w0 + Vector((0, 0, 7))]
    # the camera high over her quarter, looking down at her from astern so port is left and starboard right;
    # with the no-go fan, swung towards downwind so the fan lies ahead of it. Distance and aim fit every point.
    ca = h + 180
    if f.get('nogo'):
        d = ((w + 180 - ca + 540) % 360) - 180; ca += d * 0.6
    fit_camera(pts, ca, 50.0, 30.0)
    K.day_sky(sun_az=ca - 35, sun_el=42)
    labels = [(tuple(w0 + Vector((0, 0, 2))), 'Wind', 'blue')]
    C.render(Q.out_jpg(x['id']), Q.arg('--samples', 128), Q.arg('--scale', 100), -0.7, labels, f.get('note'), space='blender',
             arrows=[(tuple(w0), tuple(w1), 'blue')])

x = Q.item('sail', Q.arg('--id', 'bs-004'))
meta(x)
render(x)
