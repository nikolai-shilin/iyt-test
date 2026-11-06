# Bareboat-skipper test questions, figure type "buoy": the mark as you would see it close to, from low down, in its
# real colours, shape and topmark (the article's marks, art_buoyage_a.py and art_buoyage_b.py), region B lateral
# marks with their own colours. Printed: the light's rhythm when the figure gives one, and the figure's note. Never
# the mark's name or which side to pass it: that is what the questions ask. The plan, shown with the answer, does.
# See q_misc.py for how to run it.
#   blender --background --factory-startup --python docs/design/blender/q_buoy.py -- --id bs-551
#   python3 docs/design/blender/q_buoy.py --all          plan.json and ru.json for every buoy question
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import q_misc as Q

def light_text(f):
    if not f.get('rhythm'): return None
    return f['rhythm'] + (' · ' + f['rhythmNote'] if f.get('rhythmNote') else '')

# ---------- plans (pure Python) ----------
COURSE = lambda pts: {'pts': pts, 'c': 'course', 'dash': '16 12', 'arrow': True}
MOLES = [[[-230, -300], [-60, -300], [-60, -190], [-230, -175]], [[60, -300], [230, -300], [230, -178], [60, -190]]]
RED, GREEN = '#e0251b', '#1aa34a'

def can(x, z, col, s=21):
    return [{'pts': [[x - s, z - s], [x + s, z - s], [x + s, z + s], [x - s, z + s]], 'c': 'ink', 'fill': col, 'dash': '0'},
            {'pts': [[x - 9, z - s - 30], [x + 9, z - s - 30], [x + 9, z - s - 12], [x - 9, z - s - 12]], 'c': 'ink', 'fill': col, 'dash': '0'}]

def cone(x, z, col, s=21):
    return [{'pts': [[x - s, z + s], [x, z - s], [x + s, z + s]], 'c': 'ink', 'fill': col, 'dash': '0'},
            {'pts': [[x - 10, z - s - 8], [x, z - s - 32], [x + 10, z - s - 8]], 'c': 'ink', 'fill': col, 'dash': '0'}]

def channel(x, region, going_out, hi_side, title, key):
    """A buoyed channel into a harbour to the north. Region A: red cans west (port going in), green cones east;
    region B the other way round. hi_side: 'w' or 'e', the mark in the question, ringed."""
    B = region == 'B'
    west, east = (('can', GREEN), ('cone', RED)) if B else (('can', RED), ('cone', GREEN))
    zones = []
    for (shape, col), sx in ((west, -1), (east, 1)):
        for i, z in enumerate((-130, -20, 90)):
            zones += (can if shape == 'can' else cone)(sx * (58 + 5 * i), z, col)
    hx, hz = (-1 if hi_side == 'w' else 1) * (68 if going_out else 63), (84 if going_out else -26)
    circles = [{'x': hx, 'z': hz, 'r': 50, 'fill': 'rgba(255,230,0,.16)', 'dash': '0'}]
    if going_out:
        boats = [{'you': True, 'x': 0, 'z': -95, 'hdg': 180, 'noHeading': True}]; paths = [COURSE([[0, -70], [0, 160]])]
        mine = 'port' if hi_side == 'e' else 'starboard'; where = [-150, 175, 'heading out to sea']
    else:
        boats = [{'you': True, 'x': 0, 'z': 140, 'hdg': 0, 'noHeading': True}]; paths = [COURSE([[0, 115], [0, -170]])]
        mine = 'port' if hi_side == 'w' else 'starboard'; where = [140, 150, 'coming in from sea']
    texts = [{'x': 0, 'z': -228, 'text': 'HARBOUR', 'pill': False, 'size': 30},
             {'x': hx + (-1 if hi_side == 'w' else 1) * 135, 'z': hz, 'text': f'leave to {mine}', 'kind': 'accent'},
             {'x': where[0], 'z': where[1], 'text': where[2]}]
    return {'sch': {'padPx': 50, 'mpp': 0.85, 'land': MOLES, 'zones': zones, 'circles': circles, 'boats': boats, 'paths': paths,
                    'texts': texts, 'fit': [{'x': -260, 'z': -250}, {'x': 260, 'z': 215}], 'title': title, 'key': key}}

SHOAL = [[-48, -22], [-12, -40], [34, -30], [46, 6], [20, 36], [-24, 38], [-50, 10]]
def cardinal(kind, d, title, key, two=False, shoal='shoal'):
    """As the article's: the shoal in the middle, the mark on its safe side, your course beyond the mark."""
    v = {'n': (0, -1), 'e': (1, 0), 's': (0, 1), 'w': (-1, 0)}[d]; t = (-v[1], v[0])
    m = (v[0] * 105, v[1] * 105); c = (v[0] * 175, v[1] * 175)
    a = (c[0] - t[0] * 190, c[1] - t[1] * 190); b = (c[0] + t[0] * 190, c[1] + t[1] * 190)
    hdg = (math.degrees(math.atan2(t[0], -t[1])) + 360) % 360
    marks = [{'x': m[0], 'z': m[1], 'kind': kind, 'bearing': False, 'hi': True}]
    if two:
        marks = [{'x': m[0] + t[0] * k, 'z': m[1] + t[1] * k, 'kind': kind, 'bearing': False, 'hi': k < 0} for k in (-62, 62)]
    side = {'n': 'north', 'e': 'east', 's': 'south', 'w': 'west'}[d]
    return {'sch': {'padPx': 60, 'zones': [{'pts': SHOAL, 'c': 'red', 'fill': 'rgba(224,37,27,.08)'}], 'rocks': [{'x': 0, 'z': 0}], 'marks': marks,
                    'boats': [{'you': True, 'x': a[0] + t[0] * 30, 'z': a[1] + t[1] * 30, 'hdg': hdg, 'noHeading': True}],
                    'paths': [COURSE([[a[0] + t[0] * 60, a[1] + t[1] * 60], list(b)])],
                    'texts': [{'x': c[0] + v[0] * 50 + t[0] * 110, 'z': c[1] + v[1] * 50 + t[1] * 110, 'text': f'safe water {side}', 'kind': 'accent'},
                              {'x': -v[0] * 85, 'z': -v[1] * 85, 'text': shoal, 'kind': 'red'}],
                    'fit': [{'x': -230, 'z': -230}, {'x': 230, 'z': 230}], 'title': title, 'key': key}}

PLANS = {
    'bs-051': lambda: channel(None, 'A', False, 'w', 'Lateral marks · entering harbour (IALA A)',
                              ['Region A, coming in from sea: red cans to port', 'Leave the red can on your port side']),
    'bs-551': lambda: channel(None, 'A', True, 'e', 'Lateral marks · heading out to sea (IALA A)',
                              ['Region A: green cones mark the starboard side going in', 'Going out the sides swap: leave it on your port side']),
    'bs-552': lambda: channel(None, 'B', False, 'e', 'Lateral marks · returning from sea (IALA B)',
                              ['Region B, the Americas: red cones to starboard returning', '"Red right returning": leave it on your starboard side']),
    'bs-553': lambda: channel(None, 'B', False, 'w', 'Lateral marks · entering from sea (IALA B)',
                              ['Region B, the Americas: green cans mark the port side going in', 'A port-hand mark: leave it on your port side']),
    'bs-052': lambda: cardinal('card-n', 'n', 'Cardinal marks · north', ['North cardinal: both cones up, black over yellow', 'The safe water lies to the north: pass north of it']),
    'bs-563': lambda: cardinal('card-e', 'e', 'Cardinal marks · east', ['East cardinal: cones base to base, black, yellow, black', 'The safe water lies to the east: pass east of it']),
    'bs-564': lambda: cardinal('card-w', 'w', 'Cardinal marks · west', ['West cardinal: cones point to point, yellow, black, yellow', 'The safe water lies to the west: pass west of it']),
    'bs-571': lambda: cardinal('card-e', 'e', 'Cardinal marks · east, in region B', ['Only lateral marks differ between regions A and B', 'An east cardinal is the same worldwide: pass east of it']),
    'bs-573': lambda: cardinal('card-s', 's', 'Cardinal marks · south', ['South cardinal: both cones down, yellow over black', 'Safe water to the south, so the danger lies north of it']),
    'bs-583': lambda: cardinal('card-e', 'e', 'A new danger · duplicated marks', ['A serious new danger may be marked by two identical marks', 'Treat it as real until the chart is corrected: pass east of both'],
                               two=True, shoal='new danger'),
    'bs-054': lambda: {'sch': {'padPx': 60, 'title': 'Isolated danger mark', 'marks': [{'x': 0, 'z': -6, 'kind': 'iso', 'bearing': False, 'hi': True}], 'circles': [{'x': 0, 'z': 10, 'r': 60, 'c': 'red'}],
            'boats': [{'you': True, 'x': -110, 'z': -110, 'hdg': 90, 'noHeading': True}], 'paths': [COURSE([[-80, -110], [150, -110]]), COURSE([[150, 130], [-150, 130]])],
            'texts': [{'x': 110, 'z': 40, 'text': 'danger under the mark', 'kind': 'red'}, {'x': 0, 'z': -150, 'text': 'pass on any side', 'kind': 'accent'}],
            'fit': [{'x': -170, 'z': -170}, {'x': 170, 'z': 160}],
            'key': ['Isolated danger: a small danger right under the mark', 'Safe water all round: pass on any side, but keep well clear']}},
    'bs-579': lambda: {'sch': {'padPx': 50, 'title': 'Special marks · a swimming area', 'land': [[[-300, -300], [300, -300], [300, -180], [-300, -180]]],
            'zones': [{'pts': [[-200, -180], [200, -180], [200, -80], [-200, -80]]}],
            'marks': [{'x': x, 'z': -80, 'kind': 'special', 'bearing': False, 'hi': x == 0} for x in (-200, -100, 0, 100, 200)],
            'boats': [{'you': True, 'x': -120, 'z': 80, 'hdg': 90, 'noHeading': True}], 'anchors': [{'x': -10, 'z': 80, 's': 0.8}],
            'texts': [{'x': 0, 'z': -135, 'text': 'swimming area', 'kind': 'accent'}, {'x': 0, 'z': -240, 'text': 'BEACH', 'pill': False, 'size': 30},
                      {'x': 120, 'z': 20, 'text': 'stay outside the line', 'kind': 'red'}],
            'fit': [{'x': -260, 'z': -300}, {'x': 260, 'z': 150}],
            'key': ['Yellow buoys in a line off a beach usually mark the swimming area', 'Stay outside it; check the chart or the local rules']}},
}

RU = {
    'HARBOUR': 'ГАВАНЬ', 'coming in from sea': 'вход с моря', 'heading out to sea': 'выход в море', 'leave to port': 'оставить слева',
    'leave to starboard': 'оставить справа', 'shoal': 'мель', 'new danger': 'новая опасность', 'safe water north': 'чисто к северу',
    'safe water east': 'чисто к востоку', 'safe water south': 'чисто к югу', 'safe water west': 'чисто к западу',
    'danger under the mark': 'опасность под знаком', 'pass on any side': 'можно с любой стороны', 'swimming area': 'зона купания',
    'BEACH': 'ПЛЯЖ', 'stay outside the line': 'не заходите за линию',
    'Lateral marks · entering harbour (IALA A)': 'Латеральные знаки · вход в гавань (МАМС А)',
    'Region A, coming in from sea: red cans to port': 'Регион А, вход с моря: красные цилиндры слева',
    'Leave the red can on your port side': 'Красный цилиндр оставляйте слева',
    'Lateral marks · heading out to sea (IALA A)': 'Латеральные знаки · выход в море (МАМС А)',
    'Region A: green cones mark the starboard side going in': 'Регион А: зелёные конусы — правая сторона на входе',
    'Going out the sides swap: leave it on your port side': 'На выходе стороны меняются: оставляйте его слева',
    'Lateral marks · returning from sea (IALA B)': 'Латеральные знаки · возврат с моря (МАМС В)',
    'Region B, the Americas: red cones to starboard returning': 'Регион В, Америка: красные конусы справа при возврате',
    '"Red right returning": leave it on your starboard side': '«Красный — справа при возврате»: оставляйте его справа',
    'Lateral marks · entering from sea (IALA B)': 'Латеральные знаки · вход с моря (МАМС В)',
    'Region B, the Americas: green cans mark the port side going in': 'Регион В, Америка: зелёные цилиндры — левая сторона на входе',
    'A port-hand mark: leave it on your port side': 'Знак левой стороны: оставляйте его слева',
    'Cardinal marks · north': 'Кардинальные знаки · северный',
    'North cardinal: both cones up, black over yellow': 'Северный: оба конуса вершинами вверх, чёрный над жёлтым',
    'The safe water lies to the north: pass north of it': 'Чистая вода к северу: обходите его с севера',
    'Cardinal marks · east': 'Кардинальные знаки · восточный',
    'East cardinal: cones base to base, black, yellow, black': 'Восточный: конусы основаниями вместе, чёрный, жёлтый, чёрный',
    'The safe water lies to the east: pass east of it': 'Чистая вода к востоку: обходите его с востока',
    'Cardinal marks · west': 'Кардинальные знаки · западный',
    'West cardinal: cones point to point, yellow, black, yellow': 'Западный: конусы вершинами вместе, жёлтый, чёрный, жёлтый',
    'The safe water lies to the west: pass west of it': 'Чистая вода к западу: обходите его с запада',
    'Cardinal marks · east, in region B': 'Кардинальные знаки · восточный, в регионе В',
    'Only lateral marks differ between regions A and B': 'Регионы А и В различаются только латеральными знаками',
    'An east cardinal is the same worldwide: pass east of it': 'Восточный кардинальный везде один: обходите его с востока',
    'Cardinal marks · south': 'Кардинальные знаки · южный',
    'South cardinal: both cones down, yellow over black': 'Южный: оба конуса вершинами вниз, жёлтый над чёрным',
    'Safe water to the south, so the danger lies north of it': 'Чистая вода к югу, значит опасность к северу от него',
    'A new danger · duplicated marks': 'Новая опасность · знаки-дубли',
    'A serious new danger may be marked by two identical marks': 'Серьёзную новую опасность могут обозначить двумя одинаковыми знаками',
    'Treat it as real until the chart is corrected: pass east of both': 'Пока карту не исправили, верьте знакам: обходите оба с востока',
    'Isolated danger mark': 'Знак отдельной опасности',
    'Isolated danger: a small danger right under the mark': 'Отдельная опасность: небольшая опасность прямо под знаком',
    'Safe water all round: pass on any side, but keep well clear': 'Вокруг чистая вода: можно с любой стороны, но держитесь подальше',
    'Special marks · a swimming area': 'Специальные знаки · зона купания',
    'Yellow buoys in a line off a beach usually mark the swimming area': 'Линия жёлтых буйков у пляжа обычно отмечает зону купания',
    'Stay outside it; check the chart or the local rules': 'Держитесь снаружи; сверьтесь с картой или местными правилами',
}

def meta(x):
    f = x['figure']; english = [s for s in (f.get('note'), light_text(f)) if s]
    ru = dict(RU); ru.update(x['ru'])
    lt = light_text(f)
    if lt:     # the rhythm is international, as on the chart; its note through the bank's Russian
        ru[lt] = f['rhythm'] + (' · ' + x['ru'].get(f['rhythmNote'], f['rhythmNote']) if f.get('rhythmNote') else '')
    if x['id'] in PLANS:
        A = PLANS[x['id']](); Q.save(x['id'], 'plan.json', A); english += Q.plan_strings(A)
    else: Q.drop(x['id'], 'plan.json')
    Q.write_ru(x['id'], english, ru)

if not Q.IN_BLENDER:
    xs = Q.items('buoy') if Q.flag('--all') else [Q.item('buoy', Q.arg('--id', 'bs-551'))]
    for x in xs: meta(x); print(x['id'], 'plan' if x['id'] in PLANS else 'no plan', '+ ru')
    sys.exit(0)

# ---------- the render (Blender) ----------
import bpy, bmesh
from mathutils import Vector
import common as C, kit as K
from common import node, link, setin, math_, mixc, lin
def deg(a): return math.radians(a)
# the article's mark builders, taken as they are (their files are scripts, so only the functions are run here)
_a = open(os.path.join(Q.HERE, 'art_buoyage_a.py')).read(); exec(_a[_a.index('def frame('):_a.index('C.reset()')], globals())
_b = open(os.path.join(Q.HERE, 'art_buoyage_b.py')).read(); exec(_b[_b.index('PAINT = '):_b.index('# ---------- lighthouses')], globals())

def meshes_under(root):
    out = []
    def walk(o):
        if o.type == 'MESH' and not o.hide_render: out.append(o)
        for ch in o.children: walk(ch)
    walk(root); return out

def lateral(color, shape, light, at=(0, 0)):
    """The scanned lateral marker in red or green with a can or cone topmark of the same colour (any region)."""
    root, objs = K.lateral_buoy('port' if color == 'red' else 'starboard', topmark=False, light=light, at=(0, 0))
    if color == 'red': deepen(objs, 1.25, 0.8)
    else: deepen(objs, 1.15, 0.6, 0.83)
    bpy.context.view_layer.update(); lo, hi = K.bbox(objs)
    top = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, hi.z)); M = K.mats(); col = M[color]
    if shape == 'can': C.cyl('topmark', 0.32, 0.32, 0.6, 24, col, top + Vector((0, 0, 0.55))).parent = root
    else: C.cyl('topmark', 0.38, 0.0, 0.7, 24, col, top + Vector((0, 0, 0.6))).parent = root
    C.cyl('topmark-post', 0.03, 0.03, 0.3, 8, M['black'], top + Vector((0, 0, 0.1))).parent = root
    root.location = (at[0], at[1], 0.0)
    return root

def low_camera(target_objs, dist, lens, eye_h=1.8, aim=0.5, side=0.0):
    bpy.context.view_layer.update(); lo, hi = K.bbox(target_objs)
    c = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, 0)); mid = Vector((c.x, c.y, hi.z * aim))
    K.camera(Vector((c.x + side, c.y - dist, eye_h)), mid, lens)
    return c, hi.z

def render(x):
    f = x['figure']; k = f['kind']; B = f.get('region') == 'B'; qid = x['id']
    C.reset(); expo = -0.6; labels = []
    K.day_sky(sun_az=215, sun_el=34)
    K.sea('breeze', size=30.0, repeat=10)
    lt = light_text(f)
    if k in ('lat-port', 'lat-stbd'):
        port = k == 'lat-port'
        color = ('green' if port else 'red') if B else ('red' if port else 'green')
        root = lateral(color, 'can' if port else 'cone', bool(f.get('rhythm')))
        objs = meshes_under(root)
        if qid == 'bs-551':          # heading out to sea: open water ahead, the land behind us
            K.coast(distance=5200, bearing=0, height=60, town=False)
        else:                        # coming in: the harbour and its town beyond the mark
            K.coast(distance=900, bearing=0, height=110, town=True)
            K.breakwater((-260, 330), (-60, 300)); K.breakwater((260, 320), (60, 300))
        c, top = low_camera(objs, 27.0, 42, eye_h=2.4, aim=0.78)
    elif k.startswith('card'):
        which = {'n': 'north', 'e': 'east', 's': 'south', 'w': 'west'}[k[-1]]
        allo = []
        spots = [(-3.6, 0), (3.6, 0)] if qid == 'bs-583' else [(0, 0)]
        for at in spots:
            root, objs = K.cardinal_buoy(which, at=at, height=4.6); paint_cardinal(objs); allo += [o for o in objs if o.type == 'MESH' and not o.hide_render]
        K.coast(distance=2600, bearing=350, height=80, town=False); expo = -1.1
        c, top = low_camera(allo, 19.0 if qid != 'bs-583' else 24.0, 45, eye_h=1.6, aim=0.72)
    elif k == 'special' and qid == 'bs-579':
        # a line of small yellow buoys parallel to the beach, between us and the shore
        K.coast(distance=150, bearing=0, height=30, town=False)
        yel = C.simple('swim-buoy', '#f2c000', 0.4, coat=0.3); allo = []
        for i in range(-4, 5):
            allo.append(sphere(f'swim{i}', 0.45, yel, (i * 9.0, 70.0, 0.15)))
        rope = C.simple('float-line', '#e9e6dc', 0.7)
        for i in range(-4, 4):
            C.tube('float-line', [Vector((i * 9.0 + 0.4, 70.0, 0.06)), Vector((i * 9.0 + 4.5, 70.0, 0.01)), Vector((i * 9.0 + 8.6, 70.0, 0.06))], 0.025, 6, 1.0, rope)
        K.camera(Vector((-22, 40, 3.6)), Vector((4, 72, 1.2)), 36)
        c, top = Vector((0, 70, 0)), 0.5
    else:                            # iso, safe, special, wreck: the article's repainted marks
        root, top3, lightp = mark(k, (0, 0), heading=20)
        if lt: lamp_on(lightp, {'special': 'yellow', 'wreck': 'yellow'}.get(k, 'white'))
        objs = meshes_under(root)
        K.coast(distance=1600 if qid in ('bs-055', 'bs-056') else 2600, bearing=350, height=90 if qid != 'bs-056' else 50, town=qid == 'bs-055')
        c, top = low_camera(objs, 29.0, 45, eye_h=1.8, aim=0.6)
    if lt: labels = [((c.x, c.y, top + 0.9), lt)]
    C.render(Q.out_jpg(qid), Q.arg('--samples', 128), Q.arg('--scale', 100), expo, labels, f.get('note'), space='blender')

def lamp_on(p, col):
    o = K.nav_light('mark-light', p, col, power=3.0, radius=0.11)

x = Q.item('buoy', Q.arg('--id', 'bs-551'))
meta(x)
render(x)
