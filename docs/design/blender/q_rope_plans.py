# The plans shown with the answer for the rope questions that need one (q_rope.py): figure-schematic.js specs,
# built on the ropework article's own schematics (article-figures.html, 'bareboat-skipper/ropework'), each titled and
# keyed for its question's answer and reasoning. RU holds the Russian of every string they print.
# Plain Python (no Blender): python3 docs/design/blender/q_rope_plans.py  writes every <id>/plan.json and adds the
# plan's strings to that question's ru.json (bs-* ids under bareboat-skipper, ci-* under charter-checkin).
import os, json, math

HERE = os.path.dirname(os.path.abspath(__file__))
def qdir(level='bareboat-skipper'): return os.path.join(HERE, '..', 'figure-style', 'questions', level)
QDIR = qdir()
LEVEL_OF = {'bs': 'bareboat-skipper', 'ci': 'charter-checkin'}

def loop(cx, cz, r, a0, a1, n=24):
    return [[round(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)), 1), round(cz + r * math.sin(math.radians(a0 + (a1 - a0) * i / n)), 1)] for i in range(n + 1)]
def line(pts, c='line', w=9, dash=None):
    d = {'pts': pts, 'c': c, 'w': w}
    if dash: d['dash'] = dash
    return d
def ring(x, z, r, c='ink'): return {'x': x, 'z': z, 'r': r, 'c': c, 'dash': '0'}
def t(x, z, text, **o): return {'x': x, 'z': z, 'text': text, **o}
def plan(title, key, **sch): return {'noScale': True, 'sch': {'padPx': 70, 'title': title, 'key': key, **sch}}

def winch(title, key, texts=None):
    return plan(title, key, circles=[ring(0, 0, 90), ring(0, 0, 70)],
                paths=[line([[-420, 160], [-80, 50]]), line(loop(0, 0, 80, 150, 1000, 60)), line([[60, -55], [280, -200], [420, -260]])],
                texts=texts or [t(-330, 220, 'sheet · from the car'), t(0, -130, 'clockwise', kind='accent'), t(330, -300, 'tail · into the jaws')],
                fit=[{'x': -420, 'z': -320}, {'x': 420, 'z': 260}])

def cleat(title, key, texts=None):
    return plan(title, key, zones=[{'pts': [[-180, -40], [180, -40], [180, 40], [-180, 40]], 'c': 'ink', 'fill': 'rgba(0,0,0,.08)', 'dash': '0'}],
                paths=[line([[-420, -200], [-200, -60], [-120, -60]]), line(loop(0, 0, 130, 200, 560, 48)), line([[-130, 50], [130, -50]]), line([[-130, -50], [130, 50]]), line([[130, 50], [240, 160], [380, 200]])],
                texts=texts or [t(-380, -240, 'load', kind='red'), t(0, 110, 'cleat'), t(260, 230, 'locking hitch', kind='accent')],
                fit=[{'x': -420, 'z': -280}, {'x': 420, 'z': 260}])

def slip(title, key, fixing='bollard'):
    return plan(title, key, zones=[{'pts': [[-500, -320], [500, -320], [500, -180], [-500, -180]], 'c': 'ink', 'fill': '#d8c9a3', 'dash': '0'}],
                circles=[ring(0, -240, 16)], paths=[line([[-30, 120], [-16, -230]]), line(loop(0, -240, 18, 180, 360)), line([[16, -230], [30, 120]])],
                boats=[{'you': True, 'x': 0, 'z': 200, 'hdg': 0, 'noHeading': True, 'scale': 3.4}],
                texts=[t(0, -290, fixing), t(160, -40, 'both ends on board', kind='accent'), t(-300, -250, 'QUAY', pill=False, size=30)],
                fit=[{'x': -300, 'z': -320}, {'x': 300, 'z': 300}])

def roundturn(title, key):
    return plan(title, key, circles=[ring(-300, 0, 50)],
                paths=[line([[420, 0], [-240, 0]]), line(loop(-300, 0, 70, 0, 340)), line(loop(-300, 0, 84, 340, 700)), line([[-216, 0], [-60, 40], [20, 40]]),
                       line(loop(40, 10, 40, 180, 520)), line(loop(140, 10, 40, 180, 520)), line([[180, 30], [260, 90]])],
                texts=[t(-300, -140, 'round turn', kind='accent'), t(90, -80, 'two half hitches', kind='accent'), t(360, -50, 'standing part'), t(290, 130, 'end')],
                fit=[{'x': -400, 'z': -180}, {'x': 440, 'z': 180}])

PLANS = {
    'bs-020': winch('Winch · loading the sheet', ['Two or three turns, clockwise, before you start winding', 'Three turns grip without a riding turn; fingers clear of the drum']),
    'bs-220': winch('Self-tailing winch · the order', ['First the turns, clockwise on the drum: they do the gripping', 'Then over the stripper arm into the jaws: the jaws only hold the tail']),
    'bs-253': winch('Winch · more turns, more grip', ['More turns give more friction on the drum', 'Under heavy load the drum needs three or four turns']),
    'bs-262': winch('Winch · turns go on clockwise', ['Yacht winches only hold one way: the turns go on clockwise', 'Put on anticlockwise, they slip and the sheet runs out round the drum']),
    'bs-271': winch('Winch · the lead from below', ['The sheet arrives slightly below the drum: each new turn goes on under the others', 'Coming in from above it can ride over itself: a riding turn that jams']),
    'bs-016': cleat('Cleat hitch', ['A full turn round the base takes the load', 'Then figures of eight, and one locking hitch: it holds without jamming']),
    'bs-214': cleat('Cleat hitch · one locking hitch', ['One locking hitch is enough', 'More of them jam just when you need to let go']),
    'bs-215': cleat('Cleat hitch · far horn first', ['Lead the line to the far horn first, then a full turn round the base', 'The base turn takes the load and the line cannot trap itself']),
    'bs-243': slip('Made fast on board', ['The end comes back aboard: your crew makes it fast on your own cleat', 'From on board it can be adjusted or slipped without going ashore']),
    'bs-245': slip('Slip line · both ends on board', ['Both ends aboard, the middle round the bollard', 'To leave, let one end go and pull the line in by the other']),
    'bs-269': slip('Slip line · no knot in the end', ['A slip line must run free through the ring', 'A knot or an eye in the end can jam in the ring'], 'quay ring'),
    'bs-015': roundturn('Round turn and two half hitches', ['Two full turns round the ring take the load', 'While they hold, tie the two half hitches round the standing part']),
    'bs-248': roundturn('Round turn and two half hitches · casting off', ['The round turn takes the strain', 'Undo the half hitches first, while the turn still holds the load']),
    'bs-230': plan('Line handling · the snap-back zone', ['A stretched nylon line that parts whips back along its own path', 'Stand to one side of it, out of line with it'], padPx=60,
                   zones=[{'pts': [[-500, -320], [500, -320], [500, -180], [-500, -180]], 'c': 'ink', 'fill': '#d8c9a3', 'dash': '0'}, {'pts': [[-60, -200], [60, -200], [140, 260], [-140, 260]], 'c': 'red', 'fill': 'rgba(224,37,27,.12)'}],
                   circles=[ring(0, -240, 16)], paths=[line([[0, -230], [0, 180]])], boats=[{'x': 0, 'z': 240, 'hdg': 0, 'label': 'Yacht', 'noHeading': True, 'scale': 3.2}],
                   texts=[t(0, -290, 'bollard'), t(220, 40, 'snap-back zone', kind='red'), t(-300, 40, 'stand here', kind='accent'), t(300, -250, 'QUAY', pill=False, size=30)],
                   fit=[{'x': -360, 'z': -320}, {'x': 360, 'z': 320}]),
    'bs-257': plan('Sheet bend · two different lines', ['The thick line makes the bight', 'The thin line goes through it, round behind and under itself'],
                   paths=[line([[-420, -60], [80, -60]], 'ink', 16), line(loop(80, 0, 60, -90, 90), 'ink', 16), line([[80, 60], [-260, 60]], 'ink', 16),
                          line([[420, 0], [140, 0], [40, -100], [-20, -100], [-20, 100], [40, 100], [40, 0], [-160, 0]], 'red', 6)],
                   texts=[t(-330, -110, 'thick line'), t(330, -50, 'thin line', kind='red'), t(-200, 130, 'ends together', kind='accent')],
                   fit=[{'x': -420, 'z': -180}, {'x': 440, 'z': 180}]),
}

# ---- Charter Check-in ----
def drum(title, key):
    turns = [line(loop(0, 0, 66 + 5 * k, 0, 360, 36), w=7) for k in range(5)]
    return plan(title, key, circles=[ring(0, 0, 60), ring(0, 0, 100)],
                paths=turns + [line([[0, 92], [180, 140], [420, 160]], w=7)],
                texts=[t(0, -150, 'sail fully out: line wound on', kind='accent'), t(330, 210, 'to cockpit'), t(-230, 40, 'furling drum')],
                fit=[{'x': -420, 'z': -220}, {'x': 440, 'z': 260}])

def ci_clove(title, key):
    return plan(title, key, paths=[line([[-440, 0], [440, 0]], 'ink', 14),
                                   line(loop(-80, 0, 55, 90, 450, 30), w=10), line([[-80, 55], [40, -55]], w=10), line(loop(40, 0, 55, 270, 630, 30), w=10),
                                   line([[-135, 10], [-150, 160], [-150, 330]], w=10), line([[95, 10], [150, 90], [200, 120]], w=10),
                                   line(loop(230, 120, 34, 180, 520, 24), w=10), line([[200, 140], [230, 220], [250, 300]], w=10)],
                texts=[t(-20, -120, 'clove hitch', kind='accent'), t(330, 60, 'slipped half hitch', kind='accent'), t(-300, 260, 'to the fender'), t(-330, -50, 'guardrail')],
                fit=[{'x': -440, 'z': -200}, {'x': 440, 'z': 340}])

def ci_chafe(title, key):
    return plan(title, key, zones=[{'pts': [[-500, -320], [500, -320], [500, -180], [-500, -180]], 'c': 'ink', 'fill': '#d8c9a3', 'dash': '0'}],
                circles=[ring(0, -250, 16), ring(0, 150, 22)],
                paths=[line([[0, -235], [0, 128]]), line([[0, -205], [0, -150]], 'course', 22), line([[0, 110], [0, 170]], 'course', 22)],
                boats=[{'you': True, 'x': 0, 'z': 260, 'hdg': 0, 'noHeading': True, 'scale': 3.4}],
                texts=[t(190, -170, 'chafe guard · quay edge', kind='accent'), t(190, 135, 'chafe guard · fairlead', kind='accent'), t(-170, -30, 'ease a little'), t(-300, -250, 'QUAY', pill=False, size=30)],
                fit=[{'x': -320, 'z': -320}, {'x': 320, 'z': 340}])

def ci_tape(title, key):
    return plan(title, key, zones=[{'pts': [[-70, -40], [70, -40], [70, 40], [-70, 40]], 'c': 'ink', 'fill': 'rgba(0,0,0,.12)', 'dash': '0'}],
                circles=[ring(-420, -250, 40)],
                paths=[line([[-470, -250], [-470, 0], [-380, 0], [420, 0]], w=9), line([[-150, 0], [-110, 0]], 'red', 24)],
                texts=[t(0, 80, 'clutch'), t(-130, -80, 'tape: full hoist', kind='accent'), t(330, -60, 'to the winch'), t(-250, -300, 'masthead sheave', kind='red')],
                fit=[{'x': -500, 'z': -340}, {'x': 440, 'z': 160}])

def ci_inmast(title, key):
    return plan(title, key, circles=[ring(-320, 0, 55), ring(-320, 0, 28)],
                zones=[{'pts': [[-300, -10], [180, -10], [-300, -140]], 'c': 'ink', 'fill': 'rgba(0,0,0,.06)', 'dash': '0'}],
                paths=[line([[-320, 0], [380, 0]], 'ink', 14), line([[180, -10], [380, -10], [400, 220]], w=8), line([[-320, 50], [-320, 240]], w=8)],
                texts=[t(330, 270, 'outhaul: on the winch', kind='accent'), t(-320, 290, 'furling line: eased under tension', kind='accent'), t(-150, -170, 'main'), t(-420, -60, 'mast')],
                fit=[{'x': -480, 'z': -220}, {'x': 460, 'z': 330}])

PLANS.update({
    'ci-102': drum('Furling drum · enough line to roll it all in', ['With the sail fully out, the drum must still hold the line that rolls it all in',
                                                                   'One turn left runs out mid-furl: have it rewound tight']),
    'ci-109': ci_inmast('In-mast main · unfurling', ['Pull the sail out with the outhaul on the winch', 'Ease the furling line with a little tension on: a slack roll bunches and jams in the slot']),
    'ci-123': ci_tape('Main halyard · the full-hoist mark', ['The tape marks full hoist: stop when it reaches the clutch', 'Winched past it, the headboard jams against the masthead sheave']),
    'ci-423': ci_clove('Fender line · clove hitch, slipped', ['A clove hitch on the guardrail, finished with a slipped half hitch', 'It re-sets in seconds; the slipped hitch stops it shaking loose']),
    'ci-430': ci_chafe('Stern lines · chafe guards', ['Chafe, not strain, parts mooring lines: sleeve them where they move', 'A guard at the fairlead and one at the quay edge; ease the line a little']),
    'ci-432': slip('Slip line · doubled through the ring', ['Just before leaving, double each line back through its ring', 'Both ends aboard: let one go and pull it in, nobody ashore needed'], 'quay ring'),
})

RU = {
    # Charter Check-in plans
    'sail fully out: line wound on': 'парус раскрыт: линь намотан', 'to cockpit': 'в кокпит', 'furling drum': 'барабан закрутки',
    'Furling drum · enough line to roll it all in': 'Барабан закрутки · линя хватит, чтобы скрутить парус',
    'With the sail fully out, the drum must still hold the line that rolls it all in': 'Когда парус раскрыт полностью, на барабане должен остаться весь линь, которым его скручивают',
    'One turn left runs out mid-furl: have it rewound tight': 'Один виток кончится на середине закрутки: попросите плотно перемотать',
    'In-mast main · unfurling': 'Грот в мачте · раскрываем', 'outhaul: on the winch': 'аутхол: на лебёдке',
    'furling line: eased under tension': 'линь закрутки: травить с натяжением', 'main': 'грот', 'mast': 'мачта',
    'Pull the sail out with the outhaul on the winch': 'Вытягивайте парус аутхолом на лебёдке',
    'Ease the furling line with a little tension on: a slack roll bunches and jams in the slot': 'Линь закрутки травите, придерживая: слабый рулон сбивается и заклинивает в щели',
    'Main halyard · the full-hoist mark': 'Грота-фал · метка полного подъёма', 'clutch': 'стопор', 'tape: full hoist': 'изолента: поднят полностью',
    'to the winch': 'на лебёдку', 'masthead sheave': 'шкив на топе мачты',
    'The tape marks full hoist: stop when it reaches the clutch': 'Изолента отмечает полный подъём: остановитесь, когда она дошла до стопора',
    'Winched past it, the headboard jams against the masthead sheave': 'Если тянуть дальше, фаловый угол упрётся в шкив на топе и заклинит',
    'Fender line · clove hitch, slipped': 'Конец кранца · выбленочный узел со слипом', 'clove hitch': 'выбленочный узел',
    'slipped half hitch': 'полуштык со слипом', 'to the fender': 'к кранцу', 'guardrail': 'леер',
    'A clove hitch on the guardrail, finished with a slipped half hitch': 'Выбленочный узел на леере, закреплённый полуштыком со слипом',
    'It re-sets in seconds; the slipped hitch stops it shaking loose': 'Высота меняется за секунды; полуштык не даёт узлу разболтаться',
    'Stern lines · chafe guards': 'Кормовые швартовы · защита от перетирания', 'chafe guard · quay edge': 'защита · кромка причала',
    'chafe guard · fairlead': 'защита · клюз', 'ease a little': 'чуть потравить',
    'Chafe, not strain, parts mooring lines: sleeve them where they move': 'Швартовы рвёт перетирание, а не нагрузка: защитите их там, где они ходят',
    'A guard at the fairlead and one at the quay edge; ease the line a little': 'Защита у клюза и у кромки причала; швартов чуть потравите',
    'Slip line · doubled through the ring': 'Швартов на слип · через рым вдвое',
    'Just before leaving, double each line back through its ring': 'Перед самым отходом проведите каждый швартов через рым и обратно на борт',
    'Both ends aboard: let one go and pull it in, nobody ashore needed': 'Оба конца на борту: отдайте один и выберите швартов — никого на берегу не нужно',
    # the article's own (figure-style/articles/bareboat-skipper/ropework/ru.json)
    'sheet · from the car': 'шкот · от каретки', 'clockwise': 'по часовой', 'tail · into the jaws': 'хвост · в губки',
    'Winch · the lead from below': 'Лебёдка · трос подходит снизу', 'Coming in from above it can ride over itself: a riding turn that jams': 'Сверху трос ложится на себя: захлёст, который заклинит',
    'load': 'нагрузка', 'cleat': 'утка', 'locking hitch': 'запирающий шлаг', 'Cleat hitch': 'Крепление на утке',
    'bollard': 'пал', 'both ends on board': 'оба конца на борту', 'QUAY': 'ПРИЧАЛ', 'Slip line · both ends on board': 'Швартов на слип · оба конца на борту',
    'Round turn and two half hitches': 'Круглый штык с двумя полуштыками', 'round turn': 'два шлага', 'two half hitches': 'два полуштыка', 'standing part': 'коренной конец', 'end': 'ходовой конец',
    'Two full turns round the ring take the load': 'Два шлага вокруг рыма держат нагрузку',
    'Line handling · the snap-back zone': 'Работа с тросами · зона удара', 'snap-back zone': 'зона удара троса', 'stand here': 'стоять здесь', 'Yacht': 'Яхта',
    'Sheet bend · two different lines': 'Шкотовый узел · два разных троса', 'thick line': 'толстый трос', 'thin line': 'тонкий трос', 'ends together': 'концы вместе',
    # new
    'Winch · loading the sheet': 'Лебёдка · кладём шкот',
    'Two or three turns, clockwise, before you start winding': 'Два-три шлага по часовой, прежде чем крутить',
    'Three turns grip without a riding turn; fingers clear of the drum': 'Три шлага держат без захлёста; пальцы — подальше от барабана',
    'Self-tailing winch · the order': 'Самостопорящая лебёдка · порядок',
    'First the turns, clockwise on the drum: they do the gripping': 'Сначала шлаги по часовой на барабан: держат они',
    'Then over the stripper arm into the jaws: the jaws only hold the tail': 'Затем через съёмник в губки: губки лишь держат хвост',
    'Winch · more turns, more grip': 'Лебёдка · больше шлагов — крепче держит',
    'More turns give more friction on the drum': 'Больше шлагов — больше трения на барабане',
    'Under heavy load the drum needs three or four turns': 'Под большой нагрузкой нужно три-четыре шлага',
    'Winch · turns go on clockwise': 'Лебёдка · шлаги — по часовой',
    'Yacht winches only hold one way: the turns go on clockwise': 'Яхтенная лебёдка держит в одну сторону: шлаги кладут по часовой',
    'Put on anticlockwise, they slip and the sheet runs out round the drum': 'Положенные против часовой проскальзывают, и шкот стравливается по барабану',
    'The sheet arrives slightly below the drum: each new turn goes on under the others': 'Шкот подходит чуть ниже барабана: каждый новый шлаг ложится под прежние',
    'A full turn round the base takes the load': 'Полный шлаг вокруг основания держит нагрузку',
    'Then figures of eight, and one locking hitch: it holds without jamming': 'Затем восьмёрки и один запирающий шлаг: держит и не заклинивает',
    'Cleat hitch · one locking hitch': 'Крепление на утке · один запирающий шлаг',
    'One locking hitch is enough': 'Одного запирающего шлага достаточно',
    'More of them jam just when you need to let go': 'Лишние заклинят как раз тогда, когда надо отдать',
    'Cleat hitch · far horn first': 'Крепление на утке · сначала дальний рог',
    'Lead the line to the far horn first, then a full turn round the base': 'Сначала заведите трос за дальний рог, затем полный шлаг вокруг основания',
    'The base turn takes the load and the line cannot trap itself': 'Шлаг вокруг основания держит нагрузку, и трос не зажимает сам себя',
    'Made fast on board': 'Крепим на борту',
    'The end comes back aboard: your crew makes it fast on your own cleat': 'Конец возвращают на борт: экипаж крепит его на вашей утке',
    'From on board it can be adjusted or slipped without going ashore': 'С борта его можно подобрать или отдать, не сходя на берег',
    'Both ends aboard, the middle round the bollard': 'Оба конца на борту, середина — вокруг пала',
    'To leave, let one end go and pull the line in by the other': 'При отходе отдайте один конец и выберите трос за другой',
    'Slip line · no knot in the end': 'Швартов на слип · без узла на конце',
    'A slip line must run free through the ring': 'Швартов на слип должен свободно проходить через рым',
    'A knot or an eye in the end can jam in the ring': 'Узел или огон на конце может застрять в рыме',
    'quay ring': 'рым на причале',
    'While they hold, tie the two half hitches round the standing part': 'Пока они держат, завяжите два полуштыка на коренном конце',
    'Round turn and two half hitches · casting off': 'Круглый штык с двумя полуштыками · отдаём',
    'The round turn takes the strain': 'Нагрузку держат два шлага',
    'Undo the half hitches first, while the turn still holds the load': 'Сначала отдайте полуштыки, пока шлаги держат нагрузку',
    'A stretched nylon line that parts whips back along its own path': 'Лопнувший натянутый нейлоновый трос бьёт назад вдоль своей линии',
    'Stand to one side of it, out of line with it': 'Стойте сбоку, не на его линии',
    'The thick line makes the bight': 'Петлю делают из толстого троса',
    'The thin line goes through it, round behind and under itself': 'Тонкий — сквозь неё, вокруг сзади и под себя',
}

def strings(A):
    """Every printed string of a plan: title, key lines, texts, boat labels."""
    s = A['sch']; out = [s['title']] + list(s.get('key', []))
    out += [x['text'] for x in s.get('texts', [])] + [b['label'] for b in s.get('boats', []) if b.get('label')]
    return out

def ru_for(qid):
    A = PLANS.get(qid)
    if not A: return {}
    miss = [x for x in strings(A) if x not in RU]
    if miss: raise SystemExit(f'{qid}: plan strings without Russian: {miss}')
    return {x: RU[x] for x in strings(A)}

def write(qid, level=None):
    d = os.path.join(qdir(level or LEVEL_OF.get(qid[:2], 'bareboat-skipper')), qid); os.makedirs(d, exist_ok=True)
    p = os.path.join(d, 'plan.json')
    if qid in PLANS:
        with open(p, 'w') as f: json.dump(PLANS[qid], f, ensure_ascii=False, indent=1)
    rp = os.path.join(d, 'ru.json')
    ru = json.load(open(rp)) if os.path.exists(rp) else {}
    for k, v in ru_for(qid).items(): ru.setdefault(k, v)   # the image's own (the bank's) wording wins
    with open(rp, 'w') as f: json.dump(ru, f, ensure_ascii=False, indent=1)

if __name__ == '__main__':
    for q in PLANS: write(q)
    print('plans', len(PLANS))
