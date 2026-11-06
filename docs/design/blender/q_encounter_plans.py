# The plans (shown with the answer) and the Russian for q_encounter.py: for each question in encounter.json, a plan-view
# schematic in the format of figure-schematic.js ({sch: {boats, paths, texts, zones, circles, wind, title, key}}),
# metres, x east, z south, our boat at the origin; and ru.json, the Russian of every English string on the render
# (3d.labels.json) and on the plan. Pure Python: q_encounter.py calls write(id) after its render, or run it alone:
#   python3 docs/design/blender/q_encounter_plans.py [id ...]
import json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
QDIR = os.path.join(HERE, '..', 'figure-style', 'questions', 'bareboat-skipper')
LIST = {x['id']: x for x in json.load(open(os.path.join(QDIR, 'encounter.json')))}
BUILTIN = {'You': 'Вы', 'Other': 'Судно', 'Wind': 'Ветер', 'N': 'С', '?': '?'}

def rad(a): return math.radians(a)
def vec(h, r): return (r * math.sin(rad(h)), -r * math.cos(rad(h)))
def add(p, q): return (p[0] + q[0], p[1] + q[1])
def R(p): return [round(p[0], 1), round(p[1], 1)]

class Ctx:
    """Positions for one question: Y (us), O (the other at the data's bearing, D metres), headings."""
    def __init__(s, x, D):
        f = x['figure']; s.f = f; s.D = D
        s.hy = f['you'].get('hdg', 0); o = f.get('other', {}); s.ho = o.get('hdg', 180); s.rel = o.get('bearing', 0)
        s.Y = (0.0, 0.0); s.O = vec(s.hy + s.rel, D); s.you_turn = False
    def near(s, p, brg, frac):
        """A point frac*D from p on compass bearing brg."""
        return add(p, vec(brg, frac * s.D))
    def turn(s, p, h0, dh, step=0.1, n=4, lead=0.25):
        """A course from p: lead ahead on h0, then curving dh degrees over n steps; ends in an arrow. A turn of ours
        replaces our heading arrow."""
        if p == s.Y: s.you_turn = True; lead = min(lead, 0.25); pts = [add(p, vec(h0, 0.12 * s.D)), add(p, vec(h0, lead * s.D))]
        else: pts = [add(p, vec(h0, lead * s.D))]
        for i in range(1, n + 1): pts.append(add(pts[-1], vec(h0 + dh * i / n, step * s.D)))
        return {'pts': [R(q) for q in pts], 'c': 'course', 'dash': '16 12', 'arrow': True}
    def line(s, a, b, c='ink', w=4, dash='10 10', arrow=False):
        d = {'pts': [R(a), R(b)], 'c': c, 'w': w}
        if dash: d['dash'] = dash
        if arrow: d['arrow'] = True
        return d

# Each plan: D (metres to the other on the plan), title, key (two lines), and a function adding texts, paths and
# anything else. Strings are (English, Russian) pairs; t(p, s, kind) places a pill.
def T(p, s, kind=None, **o): return dict(x=round(p[0], 1), z=round(p[1], 1), text=s, **({'kind': kind} if kind else {}), **o)

PLANS = {}
def plan(ids, D, title, key, fn=None, **o):
    for i in ids.split(): PLANS[i] = dict(D=D, title=title, key=key, fn=fn, **o)

# ---- sailing vessels ----
plan('bs-031', 260, ('Sail meets sail · opposite tacks', 'Парус и парус · разные галсы'),
     [('You: the wind over your port side, port tack', 'Вы: ветер с левого борта, левый галс'), ('Port tack keeps clear of starboard tack (Rule 12)', 'Левый галс уступает правому (правило 12)')],
     lambda c: dict(texts=[T(c.near(c.Y, 135, 0.45), ('port tack: keep clear', 'левый галс: уступаете'), 'red'), T(c.near(c.O, 270, 0.4), ('starboard tack', 'правый галс'))]))
plan('bs-032', 240, ('Sail meets sail · same tack', 'Парус и парус · один галс'),
     [('Both on starboard tack, the wind from the south-east', 'Оба правым галсом, ветер с юго-востока'), ('Same tack: the windward boat keeps clear (Rule 12)', 'Один галс: наветренная яхта уступает (правило 12)')],
     lambda c: dict(texts=[T(c.near(c.Y, 120, 0.5), ('windward: keep clear', 'на ветре: уступаете'), 'red'), T(c.near(c.O, 0, 0.38), ('leeward', 'под ветром'))]))
plan('bs-033', 260, ('Motor-sailing meets sail', 'Под парусом и мотором — навстречу парусу'),
     [('Engine in gear: you are a power-driven vessel, sails or not (Rule 3)', 'Двигатель на передаче: вы — судно с мех. двигателем, хоть и под парусами (правило 3)'),
      ('Power keeps clear of sail: you give way; by day show a cone, point down', 'Механическое уступает парусному: уступаете вы; днём — конус вершиной вниз')],
     lambda c: dict(texts=[T(c.near(c.Y, 250, 0.45), ('power-driven: keep clear', 'с мех. двигателем: уступаете'), 'red'), T(c.near(c.O, 0, 0.38), ('under sail', 'под парусом'))],
                    paths=[c.turn(c.Y, 0, 70)]))
plan('bs-117', 200, ('The windward boat', 'Наветренная яхта'),
     [('The wind is from the north: the other yacht is nearer to it', 'Ветер с севера: другая яхта ближе к нему'), ('She is the windward boat; you are the leeward one', 'Она — наветренная, вы — подветренная')],
     lambda c: dict(texts=[T(c.near(c.O, 90, 0.55), ('windward', 'на ветре'), 'accent'), T(c.near(c.Y, 90, 0.55), ('leeward', 'под ветром'))]))
plan('bs-404', 260, ('Not sure of her tack', 'Её галс неизвестен'),
     [('You are on port tack; she is to windward and her mainsail is hidden', 'Вы на левом галсе; она на ветре, а её грот не виден'),
      ('Unsure of a windward boat’s tack: you keep clear (Rule 12(a)(iii))', 'Не уверены в галсе наветренной яхты — уступайте (правило 12(a)(iii))')],
     lambda c: dict(texts=[T(c.near(c.Y, 150, 0.42), ('port tack: keep clear', 'левый галс: уступаете'), 'red'), T(c.near(c.O, 270, 0.45), ('tack unknown', 'галс неизвестен'))]))
plan('bs-405', 240, ('Same tack · she is to windward', 'Один галс · она на ветре'),
     [('Both close-hauled on port tack; she is the windward boat', 'Оба в бейдевинд левым галсом; наветренная — она'),
      ('She keeps clear; you hold your course and speed (Rule 17)', 'Уступает она; вы сохраняете курс и скорость (правило 17)')],
     lambda c: dict(texts=[T(c.near(c.O, 300, 0.45), ('windward: keeps clear', 'на ветре: уступает'), 'red'), T(c.near(c.Y, 135, 0.42), ('you stand on', 'вы сохраняете курс'), 'accent')]))
plan('bs-406', 240, ('Opposite tacks · port gives way', 'Разные галсы · левый уступает'),
     [('You are on starboard tack, she is on port tack', 'Вы на правом галсе, она на левом'),
      ('On opposite tacks windward does not count: she keeps clear (Rule 12(a)(i))', 'На разных галсах наветренность не важна: уступает она (правило 12(a)(i))')],
     lambda c: dict(texts=[T(c.near(c.O, 200, 0.42), ('port tack: keeps clear', 'левый галс: уступает'), 'red'), T(c.near(c.Y, 20, 0.4), ('starboard tack: stand on', 'правый галс: курс сохраняете'), 'accent')]))
plan('bs-407', 240, ('Running · which tack?', 'Фордевинд · какой галс?'),
     [('Mainsail to port: the windward side is starboard, so you are on starboard tack', 'Грот слева: наветренный — правый борт, значит вы на правом галсе'),
      ('She has the wind on her port side: port tack, she keeps clear (Rule 12)', 'У неё ветер с левого борта: левый галс, уступает она (правило 12)')],
     lambda c: dict(texts=[T(c.near(c.O, 30, 0.42), ('port tack: keeps clear', 'левый галс: уступает'), 'red'), T(c.near(c.Y, 250, 0.45), ('starboard tack', 'правый галс'), 'accent')]))
plan('bs-408', 1852, ('Stand-on · hold your course', 'Сохраняющее курс · держите курс'),
     [('She is on port tack, you on starboard: she must keep clear', 'Она на левом галсе, вы на правом: уступать должна она'),
      ('Hold course and speed so she can judge her action (Rule 17(a)(i))', 'Сохраняйте курс и скорость, чтобы ей было ясно, как маневрировать (правило 17(a)(i))')],
     lambda c: dict(texts=[T(c.near(c.O, 200, 0.4), ('port tack: keeps clear', 'левый галс: уступает'), 'red'), T(c.near(c.Y, 80, 0.4), ('hold course and speed', 'курс и скорость прежние'), 'accent')],
                    paths=[c.line(c.Y, c.near(c.Y, c.hy, 0.6), 'course', 6, '16 12', True)]))
plan('bs-413', 240, ('Overtaking under sail', 'Обгон под парусом'),
     [('You are catching her up from astern: you are the overtaking vessel', 'Вы догоняете её с кормы: обгоняете вы'),
      ('Rule 13 comes before the tack rules: you keep clear', 'Правило 13 важнее правил о галсах: уступаете вы')],
     lambda c: dict(texts=[T(c.near(c.Y, 120, 0.4), ('overtaking: keep clear', 'обгоняете: уступаете'), 'red')], paths=[c.turn(c.Y, c.hy, 25, 0.17)]))
plan('bs-414', 200, ('Overtaken under sail · stand on', 'Вас обгоняют под парусом · сохраняйте курс'),
     [('She is coming up from astern: she is overtaking and keeps clear (Rule 13)', 'Она подходит с кормы: она обгоняет и уступает (правило 13)'),
      ('You hold your course and speed (Rule 17)', 'Вы сохраняете курс и скорость (правило 17)')],
     lambda c: dict(texts=[T(c.near(c.O, 0, 0.4), ('overtaking: keeps clear', 'обгоняет: уступает'), 'red'), T(c.near(c.Y, 0, 0.4), ('you stand on', 'вы сохраняете курс'), 'accent')]))

# ---- power-driven vessels ----
plan('bs-034', 380, ('Crossing · she is on your starboard side', 'Пересечение курсов · судно у вас справа'),
     [('Steady bearing, range closing: risk of collision', 'Пеленг не меняется, дистанция сокращается: опасность столкновения'),
      ('Alter to starboard early and clearly, and pass astern of her (Rule 15)', 'Заранее и заметно поверните вправо и пройдите у неё за кормой (правило 15)')],
     lambda c: dict(texts=[T(c.near(c.Y, 250, 0.32), ('you give way', 'вы уступаете'), 'red')], paths=[c.turn(c.Y, 0, 80)]))
plan('bs-035', 400, ('Head-on · both turn to starboard', 'Встречные курсы · оба поворачивают вправо'),
     [('Two power-driven vessels meeting end-on (Rule 14)', 'Два судна с механическим двигателем идут навстречу (правило 14)'),
      ('Each alters to starboard and passes port side to port side', 'Каждое поворачивает вправо, расходятся левыми бортами')],
     lambda c: dict(paths=[c.turn(c.Y, 0, 40, 0.07, lead=0.2), c.turn(c.O, 180, 40, 0.07, lead=0.2)]), bearing=False, noHeading=True)
plan('bs-036', 420, ('Overtaking · you keep clear', 'Обгон · уступаете вы'),
     [('Coming up from well abaft her beam you are overtaking (Rule 13)', 'Вы подходите далеко позади её траверза — это обгон (правило 13)'),
      ('Overtaking comes first: under sail you keep clear of her too', 'Обгон важнее: и под парусом уступаете вы')],
     lambda c: dict(texts=[T(c.near(c.Y, 90, 0.5), ('overtaking: keep clear', 'обгоняете: уступаете'), 'red')], paths=[c.turn(c.Y, 0, 30, 0.2)]))
plan('bs-382', 300, ('Bearing in doubt', 'Пеленг под сомнением'),
     [('If you cannot tell whether the bearing changes, assume risk of collision (Rule 7(a))', 'Не понять, меняется ли пеленг, — считайте, что опасность столкновения есть (правило 7(a))'),
      ('She is on your starboard bow: act as the give-way vessel, early', 'Она справа по носу: действуйте заранее как уступающее судно')],
     lambda c: dict(texts=[T(c.near(c.Y, 250, 0.3), ('assume risk', 'опасность есть'), 'red')], paths=[c.turn(c.Y, 0, 80)]))
plan('bs-385', 5556, ('Give-way action · Rule 8', 'Манёвр уступающего · правило 8'),
     [('One early turn, big enough to see on radar', 'Один ранний поворот, заметный и на радаре'), ('Not a series of small alterations', 'А не серия мелких изменений курса')],
     lambda c: dict(texts=[T(c.near(c.Y, 290, 0.25), ('early and bold', 'рано и решительно'), 'accent')], paths=[c.turn(c.Y, 0, 70, 0.11)]))
plan('bs-386', 700, ('No room to turn · slow down', 'Повернуть некуда · сбавьте ход'),
     [('Shoal water close to starboard: you cannot turn that way', 'Справа близко мелководье: туда не повернуть'),
      ('Slow down or stop and let her pass ahead (Rules 8(e), 16)', 'Сбавьте ход или остановитесь и пропустите её вперёд (правила 8(e), 16)')],
     lambda c: dict(zones=[{'pts': [R(c.near(c.Y, 120, 0.18)), R(c.near(c.Y, 60, 0.25)), R(c.near(c.Y, 40, 0.45)), R(c.near(c.Y, 75, 0.5)), R(c.near(c.Y, 120, 0.35))], 'c': 'red', 'fill': 'rgba(224,37,27,.08)'}],
                    texts=[T(c.near(c.Y, 90, 0.42), ('shoal', 'мелко'), 'red'), T(c.near(c.Y, 225, 0.25), ('slow down or stop', 'сбавьте ход или стоп'), 'accent')]))
plan('bs-387', 300, ('After the alteration · keep checking', 'После манёвра · продолжайте следить'),
     [('You turned 40° to starboard to pass astern of her', 'Вы повернули на 40° вправо, чтобы пройти у неё за кормой'),
      ('Check her bearing until she is finally past and clear (Rule 8(d))', 'Следите за пеленгом, пока она окончательно не пройдёт (правило 8(d))')],
     lambda c: dict(texts=[T(c.near(c.Y, 120, 0.35), ('keep checking the bearing', 'следите за пеленгом'), 'accent')],
                    paths=[c.line(c.near(c.Y, 180, 0.4), c.Y, 'ink', 4, '6 10')]))
plan('bs-409', 260, ('Overtaken · she keeps clear', 'Вас обгоняют · уступает она'),
     [('She comes from more than 22.5° abaft your beam: she is overtaking', 'Она подходит с направления более 22,5° позади вашего траверза: это обгон'),
      ('The overtaking vessel keeps clear, whichever side she is on (Rule 13)', 'Обгоняющее судно уступает, с какого бы борта ни шло (правило 13)')],
     lambda c: dict(texts=[T(c.near(c.O, 230, 0.5), ('overtaking: keeps clear', 'обгоняет: уступает'), 'red'), T(c.near(c.Y, 0, 0.42), ('you stand on', 'вы сохраняете курс'), 'accent')],
                    paths=[c.line(c.Y, c.near(c.Y, c.hy + 112.5, 0.9), 'ink', 3, '4 10'), c.line(c.Y, c.near(c.Y, c.hy - 112.5, 0.9), 'ink', 3, '4 10')]))
plan('bs-410', 260, ('In doubt · assume you are overtaking', 'Сомневаетесь · считайте, что обгоняете'),
     [('About 20° abaft her beam: close to the 22.5° line', 'Около 20° позади её траверза: близко к границе 22,5°'),
      ('In doubt you are overtaking: keep out of her way (Rule 13(c))', 'В сомнении считайте себя обгоняющим и уступайте (правило 13(c))')],
     lambda c: dict(texts=[T(c.near(c.Y, 120, 0.4), ('overtaking: keep clear', 'обгоняете: уступаете'), 'red')],
                    paths=[c.line(c.O, c.near(c.O, c.ho + 112.5, 0.9), 'ink', 3, '4 10'), c.line(c.O, c.near(c.O, c.ho - 112.5, 0.9), 'ink', 3, '4 10')]))
plan('bs-411', 200, ('Overtaking stays overtaking', 'Обгон остаётся обгоном'),
     [('You came up from astern of her: you are the overtaking vessel', 'Вы подошли с её кормы: вы обгоняющее судно'),
      ('A later change of bearing does not end it: keep clear until past and clear (Rule 13(d))', 'Изменение пеленга этого не отменяет: уступайте, пока не пройдёте (правило 13(d))')],
     lambda c: dict(texts=[T(c.near(c.Y, 120, 0.45), ('still overtaking: keep clear', 'всё ещё обгон: уступаете'), 'red')],
                    paths=[c.line(c.near(c.Y, 180, 0.6), c.near(c.Y, 180, 0.1), 'ink', 4, '6 10')]))
plan('bs-417', 300, ('Power meets sail end-on', 'Мотор и парус на встречных курсах'),
     [('Rule 14 is only for two power-driven vessels', 'Правило 14 — только для двух судов с механическим двигателем'),
      ('Power keeps clear of sail: you alone take action (Rule 18)', 'Механическое уступает парусному: маневрируете только вы (правило 18)')],
     lambda c: dict(texts=[T(c.near(c.Y, 250, 0.3), ('you keep clear', 'вы уступаете'), 'red'), T(c.near(c.O, 270, 0.35), ('under sail', 'под парусом'))], paths=[c.turn(c.Y, 0, 40, 0.08)]), bearing=False, noHeading=True)
plan('bs-419', 1500, ('Masts in line · head-on', 'Мачты в створе · встречные курсы'),
     [('Her masts in line by day: she is coming end-on', 'Днём её мачты в створе: она идёт прямо на вас'),
      ('Both power-driven: each alters to starboard (Rule 14)', 'Оба с механическим двигателем: каждый поворачивает вправо (правило 14)')],
     lambda c: dict(paths=[c.turn(c.Y, 0, 40, 0.07, lead=0.2), c.turn(c.O, 182, 40, 0.07, lead=0.2)]), bearing=False, noHeading=True)
plan('bs-420', 300, ('Crossing · she is on your port side', 'Пересечение курсов · судно у вас слева'),
     [('You are on her starboard side: she is the give-way vessel', 'Вы у неё справа: уступать должна она'),
      ('Hold your course and speed, and keep watching her (Rules 15, 17)', 'Сохраняйте курс и скорость и следите за ней (правила 15, 17)')],
     lambda c: dict(texts=[T(c.near(c.Y, 180, 0.35), ('you stand on', 'вы сохраняете курс'), 'accent'), T(c.near(c.O, 90, 0.42), ('she gives way', 'она уступает'), 'red')]))
plan('bs-421', 350, ('High-speed ferry · no priority', 'Скоростной паром · без преимуществ'),
     [('A high-speed craft is simply a power-driven vessel', 'Скоростное судно — просто судно с механическим двигателем'),
      ('You are on her starboard side: the ferry gives way (Rule 15)', 'Вы у неё справа: уступает паром (правило 15)')],
     lambda c: dict(texts=[T(c.near(c.O, 200, 0.4), ('gives way', 'уступает'), 'red'), T(c.near(c.Y, 90, 0.4), ('you stand on', 'вы сохраняете курс'), 'accent')]))
plan('bs-423', 926, ('Stand-on · she does nothing', 'Сохраняющее курс · она не маневрирует'),
     [('In doubt that the give-way vessel is acting: at least five short blasts', 'Сомневаетесь, что уступающее судно маневрирует, — не менее пяти коротких гудков'),
      ('Then be ready to act yourself (Rules 34(d), 17)', 'И будьте готовы действовать сами (правила 34(d), 17)')],
     lambda c: dict(texts=[T(c.near(c.Y, 180, 0.28), ('· · · · ·  five short blasts', '· · · · ·  пять коротких'), 'red')]))
plan('bs-424', 300, ('Acting as stand-on · which way?', 'Сохраняющее курс действует · куда?'),
     [('A power-driven vessel on your port side: do not turn to port (Rule 17(c))', 'Судно с механическим двигателем слева: не поворачивайте влево (правило 17(c))'),
      ('Turn to starboard, away from her, or slow down', 'Поворачивайте вправо, от неё, или сбавьте ход')],
     lambda c: dict(texts=[T(c.near(c.Y, 75, 0.45), ('to starboard', 'вправо'), 'accent'), T(c.near(c.Y, 225, 0.35), ('not to port', 'не влево'), 'red')], paths=[c.turn(c.Y, 0, 90, 0.12)]))
plan('bs-425', 120, ('Too close · act now', 'Слишком близко · действуйте'),
     [('Her action alone can no longer avoid a collision', 'Её манёвр один уже не может предотвратить столкновение'),
      ('The stand-on vessel must take the best action to avoid her (Rule 17(b))', 'Сохраняющее курс судно обязано сделать всё, чтобы его избежать (правило 17(b))')],
     lambda c: dict(texts=[T(c.near(c.Y, 120, 0.5), ('best action now', 'действуйте сейчас'), 'red')], paths=[c.turn(c.Y, 0, 90, 0.14)]))
plan('bs-426', 1400, ('Stand-on to a big ship · watch her', 'Курс сохраняете перед большим судном · следите'),
     [('Under sail you are stand-on, but she may not see you', 'Под парусом курс сохраняете вы, но вас могут не увидеть'),
      ('Big ships turn and stop slowly: act early if she does not alter (Rules 2, 17)', 'Большое судно долго поворачивает и тормозит: не уступает — действуйте заранее (правила 2, 17)')],
     lambda c: dict(texts=[T(c.near(c.O, 270, 0.3), ('blind arc, long to stop', 'мёртвая зона, долгий тормозной путь'), 'red'), T(c.near(c.Y, 200, 0.25), ('watch closely', 'следите внимательно'), 'accent')]))
plan('bs-430', 260, ('Trolling is not fishing', 'Троллинг — не лов рыбы'),
     [('Trolling lines do not restrict her: not “engaged in fishing” (Rule 3(d))', 'Дорожки её не стесняют: она не «занята ловом рыбы» (правило 3(d))'),
      ('Two power vessels crossing: you are on her starboard side, she keeps clear', 'Два судна с механическим двигателем: вы у неё справа, уступает она')],
     lambda c: dict(texts=[T(c.near(c.O, 160, 0.42), ('gives way', 'уступает'), 'red'), T(c.near(c.Y, 90, 0.4), ('you stand on', 'вы сохраняете курс'), 'accent')],
                    paths=[c.line(c.near(c.O, c.ho + 180, 0.04), c.near(c.O, c.ho + 172, 0.35), 'ink', 3, '8 8'), c.line(c.near(c.O, c.ho + 180, 0.04), c.near(c.O, c.ho + 188, 0.35), 'ink', 3, '8 8')]))
plan('bs-431', 300, ('A seaplane on the water', 'Гидросамолёт на воде'),
     [('A seaplane on the water keeps well clear of all vessels (Rule 18(e))', 'Гидросамолёт на воде держится в стороне от всех судов (правило 18(e))'),
      ('Hold your course, and keep watching it', 'Сохраняйте курс и следите за ним')],
     lambda c: dict(texts=[T(c.near(c.O, 160, 0.4), ('keeps clear', 'уступает'), 'red'), T(c.near(c.Y, 270, 0.42), ('you stand on', 'вы сохраняете курс'), 'accent')]))
plan('bs-437', 160, ('A windsurfer is a sailing vessel', 'Виндсёрфер — парусное судно'),
     [('Power keeps clear of sail: treat a board as a sailing vessel (Rule 18)', 'Механическое уступает парусному: доска — тоже парусное судно (правило 18)'),
      ('Give boards a wide berth', 'Обходите доски с большим запасом')],
     lambda c: dict(texts=[T(c.near(c.Y, 120, 0.4), ('you keep clear', 'вы уступаете'), 'red')], paths=[c.turn(c.Y, 0, 70, 0.14)]))
plan('bs-438', 300, ('Fishing vessel · keep clear', 'Судно, занятое ловом · уступите'),
     [('Two cones, points together: engaged in fishing', 'Два конуса вершинами вместе: занято ловом рыбы'),
      ('Power keeps clear of a vessel fishing, from whatever side (Rule 18(a))', 'Механическое уступает занятому ловом, с какой бы стороны оно ни было (правило 18(a))')],
     lambda c: dict(texts=[T(c.near(c.Y, 120, 0.35), ('you keep clear', 'вы уступаете'), 'red'), T(c.near(c.O, 0, 0.35), ('fishing', 'лов рыбы'))],
                    paths=[c.line(c.near(c.O, c.ho + 180, 0.08), c.near(c.O, c.ho + 170, 0.45), 'ink', 3, '8 8'), c.line(c.near(c.O, c.ho + 180, 0.08), c.near(c.O, c.ho + 190, 0.45), 'ink', 3, '8 8')]))
plan('bs-447', 200, ('In sight · the steering rules apply', 'На виду · действуют правила плавания'),
     [('In sight of each other, Rule 19 gives way to the crossing rule (Rules 11, 15)', 'На виду друг у друга вместо правила 19 действует правило пересечения (правила 11, 15)'),
      ('She is on your starboard side: you give way', 'Она справа: уступаете вы')],
     lambda c: dict(texts=[T(c.near(c.Y, 250, 0.32), ('you give way', 'вы уступаете'), 'red')], paths=[c.turn(c.Y, 0, 80, 0.12)]))
plan('bs-457', 1200, ('Signal the turn', 'Сигнал о повороте'),
     [('Power-driven vessels in sight signal their alterations (Rule 34(a))', 'Суда с механическим двигателем на виду друг у друга сигналят о манёвре (правило 34(a))'),
      ('One short blast: “I am altering my course to starboard”', 'Один короткий гудок: «Изменяю курс вправо»')],
     lambda c: dict(texts=[T(c.near(c.Y, 250, 0.22), ('·  one short blast', '·  один короткий'), 'accent')], paths=[c.turn(c.Y, 0, 80, 0.11)]))
plan('bs-460', 300, ('No room to starboard · slow down', 'Вправо некуда · сбавьте ход'),
     [('Rocks close to starboard: the usual turn is impossible', 'Справа близко камни: обычный поворот невозможен'),
      ('Slow down or stop until she has passed (Rules 2(b), 8(e))', 'Сбавьте ход или остановитесь, пока она не пройдёт (правила 2(b), 8(e))')],
     lambda c: dict(zones=[{'pts': [R(c.near(c.Y, 150, 0.15)), R(c.near(c.Y, 50, 0.15)), R(c.near(c.Y, 20, 0.75)), R(c.near(c.Y, 40, 0.8)), R(c.near(c.Y, 100, 0.3))], 'c': 'red', 'fill': 'rgba(224,37,27,.08)'}],
                    texts=[T(c.near(c.Y, 60, 0.42), ('rocks', 'камни'), 'red'), T(c.near(c.Y, 230, 0.3), ('slow down or stop', 'сбавьте ход или стоп'), 'accent')]), bearing=False, noHeading=True)
plan('bs-865', 260, ('Autopilot · take the wheel', 'Автопилот · возьмите штурвал'),
     [('Press Standby: it releases the autopilot drive', 'Нажмите Standby: привод автопилота отключится'),
      ('Then steer by hand, and keep clear of the fishing boat', 'Затем управляйте вручную и расходитесь с рыбаком')],
     lambda c: dict(texts=[T(c.near(c.Y, 250, 0.35), ('Standby, then the wheel', 'Standby, затем штурвал'), 'accent')], paths=[c.turn(c.Y, 0, 50, 0.12)]))

# ---- channels, lanes ----
def chan_zone(c, p, along, half, length):
    length = min(length, 2.0 * c.D)
    a, b = add(p, vec(along, length / 2)), add(p, vec(along + 180, length / 2))
    return {'pts': [R(add(a, vec(along - 90, half))), R(add(a, vec(along + 90, half))), R(add(b, vec(along + 90, half))), R(add(b, vec(along - 90, half)))], 'c': 'ink', 'fill': 'rgba(0,118,190,.08)'}
plan('bs-388', 600, ('Narrow channel · do not impede', 'Узкость · не мешайте'),
     [('She can only use the deep water: under sail you must not impede her (Rule 9)', 'Ей доступна только глубокая вода: под парусом вы не должны ей мешать (правило 9)'),
      ('Risk of collision does not change that: act early (Rule 8(f))', 'Опасность столкновения этого не отменяет: действуйте заранее (правило 8(f))')], bearing=False,
     fn=lambda c: dict(zones=[chan_zone(c, add(c.O, vec(185, 0.45 * c.D)), 5, 110, 1.3 * c.D)], texts=[T(add(c.O, (0, -260)), ('deep water', 'глубокая вода'), 'accent'), T(c.near(c.Y, 250, 0.3), ('keep out of her way', 'не мешайте ей'), 'red')]))
plan('bs-389', 650, ('Crossing a narrow channel', 'Пересечение узкости'),
     [('Do not cross if it will impede a vessel that can only use the channel (Rule 9(d))', 'Не пересекайте, если затрудните движение судна, идущего только по фарватеру (правило 9(d))'),
      ('Wait, and cross astern of her', 'Подождите и пересеките у неё за кормой')],
     lambda c: dict(zones=[chan_zone(c, add(c.O, vec(190, 0.4 * c.D)), 10, 80, 1.4 * c.D)], texts=[T(c.near(c.Y, 180, 0.22), ('wait', 'ждите'), 'red'), T(add(c.O, (-170, -60)), ('channel', 'фарватер'))]))
plan('bs-392', 260, ('Overtaking in a narrow channel', 'Обгон в узкости'),
     [('Two prolonged and two short: “I intend to overtake you on your port side” (Rule 34(c))', 'Два продолжительных и два коротких: «Намерен обогнать вас по левому борту» (правило 34(c))'),
      ('Wait for her agreement before you overtake (Rule 9(e))', 'Перед обгоном дождитесь её согласия (правило 9(e))')], bearing=False,
     fn=lambda c: dict(zones=[chan_zone(c, (-20, -0.45 * c.D), 0, 110, 1.6 * c.D)], texts=[T(c.near(c.Y, 250, 0.4), ('— — · ·', '— — · ·'), 'accent')], paths=[c.turn(c.Y, 0, -25, 0.2, 3)]))
plan('bs-395', 220, ('Being overtaken in a narrow channel', 'Вас обгоняют в узкости'),
     [('Her — — · · : “I intend to overtake you on your port side”', 'Её — — · · : «Намерен обогнать вас по левому борту»'),
      ('If you agree, answer — · — · and move over to starboard (Rule 9(e))', 'Если согласны, ответьте — · — · и примите вправо (правило 9(e))')],
     lambda c: dict(zones=[chan_zone(c, (0, -60), 90, 110, 900)], texts=[T(c.near(c.Y, 30, 0.45), ('— · — ·  agree', '— · — ·  согласен'), 'accent')],
                    paths=[c.turn(c.Y, 90, 20, 0.2, 3), c.turn(c.O, 90, -12, 0.25, 3)]))
plan('bs-402', 900, ('Crossing a traffic lane', 'Пересечение полосы движения'),
     [('Under sail you must not impede a power-driven vessel following the lane (Rule 10(j))', 'Под парусом нельзя мешать судну с мех. двигателем, идущему по полосе (правило 10(j))'),
      ('Steady bearing: you keep clear, early', 'Пеленг не меняется: уступаете вы, заранее')],
     lambda c: dict(zones=[chan_zone(c, add(c.O, (0, 0)), 90, 160, 3600)], texts=[T(add(c.O, (0, -230)), ('lane', 'полоса'), None), T(c.near(c.Y, 120, 0.3), ('you keep clear', 'вы уступаете'), 'red')]))

# ---- fog ----
plan('bs-444', 900, ('Fog · a target ahead', 'Туман · цель впереди'),
     [('Forward of your beam: avoid turning to port (Rule 19(d)(i))', 'Впереди траверза: не поворачивайте влево (правило 19(d)(i))'),
      ('Turn boldly to starboard, or slow right down', 'Решительно поверните вправо или сильно сбавьте ход')],
     lambda c: dict(texts=[T(c.near(c.Y, 270, 0.3), ('fog', 'туман'), None, pill=False, size=40)], paths=[c.turn(c.Y, 0, 100, 0.16, lead=0.15)]))
plan('bs-445', 700, ('Fog · a target on the quarter', 'Туман · цель на раковине'),
     [('Abaft the beam: avoid turning towards her (Rule 19(d)(ii))', 'Позади траверза: не поворачивайте в её сторону (правило 19(d)(ii))'),
      ('She is on your starboard quarter: alter to port, away from her', 'Она на правой раковине: поворачивайте влево, от неё')],
     lambda c: dict(texts=[T(c.near(c.Y, 90, 0.35), ('fog', 'туман'), None, pill=False, size=40)], paths=[c.turn(c.Y, 270, -60, 0.12)]))
plan('bs-446', 800, ('Fog · no stand-on vessel', 'Туман · сохраняющего курс нет'),
     [('Not in sight of each other: no give-way or stand-on vessel (Rule 19)', 'Суда не видят друг друга: нет ни уступающего, ни сохраняющего курс (правило 19)'),
      ('Both must act to avoid a close-quarters situation', 'Оба должны действовать, чтобы не допустить чрезмерного сближения')],
     lambda c: dict(texts=[T(c.near(c.Y, 90, 0.35), ('fog', 'туман'), None, pill=False, size=40), T(c.near(c.Y, 180, 0.25), ('both act', 'действуют оба'), 'red')]))

# ---- night ----
plan('bs-637', 260, ('Your lights from her bearing', 'Ваши огни с её стороны'),
     [('She bears 140° relative: more than 22.5° abaft your beam', 'Она на курсовом угле 140°: более 22,5° позади вашего траверза'),
      ('Only your sternlight (135° astern) shows; the sidelights stop at 112.5°', 'Ей виден только ваш кормовой огонь (135° за кормой); бортовые — только до 112,5°')],
     lambda c: dict(night=True, texts=[T(c.near(c.Y, 20, 0.35), ('sternlight only', 'только кормовой огонь'), 'accent')]), power=True)

# ---- positions (terms) ----
plan('bs-112', 250, ('Abeam to starboard', 'На траверзе справа'),
     [('Abeam: 90° from the bow', 'На траверзе: 90° от носа'), ('Starboard: the right-hand side, facing forward', 'Правый борт: справа, если смотреть вперёд')])
plan('bs-113', 250, ('On the starboard quarter', 'На правой раковине'),
     [('The quarter: about 45° abaft the beam, between the beam and the stern', 'Раковина: примерно 45° позади траверза, между траверзом и кормой'),
      ('Call it: “Ferry on the starboard quarter”', 'Докладывайте: «Паром на правой раковине»')])
plan('bs-114', 250, ('On the port bow', 'Слева по носу'),
     [('The bow: about 45° either side of dead ahead', 'По носу: примерно 45° от направления прямо вперёд'), ('Port: the left-hand side, facing forward', 'Левый борт: слева, если смотреть вперёд')])
plan('bs-115', 250, ('Fine on the starboard bow', 'Прямо по носу, немного справа'),
     [('“Fine”: close to the bow line; “broad”: nearer the beam', '«Немного»: близко к линии курса; ближе к траверзу — «справа по носу»'), ('Report it: “Motorboat fine on the starboard bow”', 'Докладывайте: «Катер прямо по носу, немного справа»')])
plan('bs-116', 250, ('Dead astern', 'Прямо за кормой'),
     [('Directly behind the stern: dead astern', 'Точно позади кормы: прямо за кормой'), ('The RIB is in your wake', 'РИБ идёт в вашей кильватерной струе')])

# ---- man overboard, swimmers ----
def mob_bits(c, extra=None, label=('MOB', 'ЧЗБ'), color='#ff5a00'):
    return dict(circles=[{'x': round(c.O[0], 1), 'z': round(c.O[1], 1), 'r': round(c.D * 0.035, 2), 'fill': color, 'c': 'red', 'dash': '0'}],
                texts=[T(add(c.O, (0, -0.16 * c.D)), label, 'red')] + (extra or []))
plan('bs-025', 40, ('Man overboard · the first seconds', 'Человек за бортом · первые секунды'),
     [('Shout “Man overboard!” and throw the danbuoy and horseshoe at once', 'Крикните «Человек за бортом!» и сразу бросьте буй с флагштоком и подкову'),
      ('One crew member points at the casualty and never looks away', 'Один из экипажа показывает на человека и не сводит с него глаз')],
     lambda c: dict(**mob_bits(c, [T(c.near(c.O, 90, 0.45), ('danbuoy + horseshoe', 'буй с флагштоком + подкова'), 'accent'), T(c.near(c.Y, 90, 0.45), ('point and shout', 'показать и крикнуть'))]),
                    paths=[c.line(c.near(c.Y, 200, 0.15), c.near(c.O, 20, 0.12), 'red', 4, '6 8', True)]), other=False)
plan('bs-099', 40, ('MOB · the final approach under power', 'ЧЗБ · последний заход под мотором'),
     [('Approach slowly, heading into the wind, so you can stop', 'Подходите медленно, носом на ветер, чтобы можно было остановиться'),
      ('Neutral as they come alongside near the bow: a turning prop by a swimmer is lethal', 'Нейтраль, когда человек у борта ближе к носу: вращающийся винт рядом смертельно опасен')],
     lambda c: dict(**mob_bits(c, [T(c.near(c.Y, 120, 0.45), ('slow, into the wind', 'медленно, против ветра'), 'accent'), T(c.near(c.O, 270, 0.45), ('neutral', 'нейтраль'), 'accent')]),
                    paths=[c.line(c.near(c.Y, 0, 0.12), c.near(c.O, 180, 0.12), 'course', 6, '16 12', True)]), other=False)
plan('bs-346', 40, ('MOB · mark the position', 'ЧЗБ · отметьте место'),
     [('Horseshoe thrown, spotter pointing: press MOB on the plotter', 'Подкова брошена, наблюдатель показывает: нажмите MOB на плоттере'),
      ('It fixes the position at once, in case you lose sight of the casualty', 'Место фиксируется сразу — на случай, если человек пропадёт из виду')],
     lambda c: dict(**mob_bits(c, [T(c.near(c.O, 270, 0.45), ('MOB waypoint', 'точка MOB'), 'accent')])), other=False)
plan('bs-973', 60, ('MOB · the quick-stop', 'ЧЗБ · быстрая остановка'),
     [('Tack at once, leaving the headsail backed', 'Сразу делайте поворот оверштаг, оставив передний парус обстененным'),
      ('The boat stops and stays close to the casualty', 'Яхта останавливается и остаётся рядом с человеком')],
     lambda c: dict(**mob_bits(c), paths=[{'pts': [R(c.near(c.Y, 0, 0.15)), R(c.near(c.Y, 345, 0.32)), R(c.near(c.Y, 315, 0.4)), R(c.near(c.Y, 275, 0.4)), R(c.near(c.Y, 235, 0.35)), R(c.near(c.Y, 195, 0.35)), R(c.near(c.O, 300, 0.3))], 'c': 'course', 'dash': '16 12', 'arrow': True}],
                    texts2=[T(c.near(c.Y, 300, 0.6), ('tack, headsail backed', 'оверштаг, парус обстенён'), 'accent')]), other=False)
plan('bs-974', 200, ('MOB · approach on a close reach', 'ЧЗБ · подход полным бейдевиндом'),
     [('Make the final approach on a close reach', 'Последний заход делайте полным бейдевиндом'), ('Ease the sheets to slow down, fill the sails to go', 'Потравите шкоты, чтобы сбросить ход, выберите — чтобы идти')],
     lambda c: dict(**mob_bits(c, [T(c.near(c.O, 180, 0.4), ('close reach, sheets eased', 'полный бейдевинд, шкоты потравлены'), 'accent')]),
                    paths=[c.line(c.near(c.O, 120, 0.7), c.near(c.O, 120, 0.1), 'course', 6, '16 12', True)]), other=False)
plan('bs-336', 50, ('Swimming off the stern', 'Купание с кормы'),
     [('At anchor the current sets south, away from the boat: a tired swimmer drifts off', 'На якоре течение на юг, от яхты: уставшего пловца относит'),
      ('First stream a floating line astern for them to grab', 'Сначала выпустите за корму плавучий конец, чтобы было за что схватиться')],
     lambda c: dict(**mob_bits(c, [T(add(c.O, (0.35 * c.D, 0)), ('floating line', 'плавучий конец'), 'accent'), T(add(c.Y, (-0.4 * c.D, 0.3 * c.D)), ('current', 'течение'))],
                                label=('Swimmer', 'Пловец'), color='#ffd21a'),
                    paths=[{'pts': [[0, 8], [3, 20], [-2, 32], [2, 45], [0, 55]], 'c': 'line', 'w': 6}, c.line((-0.4 * c.D, 0.05 * c.D), (-0.4 * c.D, 0.55 * c.D), 'ink', 4, None, True)],
                    anchors=[{'x': 0, 'z': -0.55 * c.D, 's': 0.8}]), other=False)

# ---- signals and distress ----
plan('bs-947', 300, ('A red flare · distress', 'Красный фальшфейер · бедствие'),
     [('A red hand flare is a distress signal', 'Красный фальшфейер — сигнал бедствия'),
      ('No MAYDAY heard: send a MAYDAY RELAY on 16, then go to help', 'MAYDAY не слышно: передайте MAYDAY RELAY на 16-м канале и идите на помощь')],
     lambda c: dict(texts=[T(c.near(c.O, 0, 0.35), ('red flare', 'красный фальшфейер'), 'red'), T(c.near(c.Y, 230, 0.3), ('MAYDAY RELAY · ch 16', 'MAYDAY RELAY · 16 канал'), 'accent')],
                    paths=[c.line(c.near(c.Y, 40, 0.12), c.near(c.O, 220, 0.15), 'course', 6, '16 12', True)]))
plan('bs-960', 200, ('Arms raised and lowered · distress', 'Руки поднимают и опускают · бедствие'),
     [('Slowly raising and lowering outstretched arms is a distress signal', 'Медленно поднимать и опускать разведённые в стороны руки — сигнал бедствия'),
      ('They are in distress and need help', 'Они терпят бедствие и нуждаются в помощи')],
     lambda c: dict(texts=[T(c.near(c.O, 0, 0.4), ('distress', 'бедствие'), 'red')], paths=[c.line(c.near(c.Y, 30, 0.12), c.near(c.O, 210, 0.15), 'course', 6, '16 12', True)]))
plan('bs-962', 250, ('Flag V · I require assistance', 'Флаг V · Нуждаюсь в помощи'),
     [('Code flag V: “I require assistance”', 'Флаг МСС V: «Нуждаюсь в помощи»'), ('Not distress: that is NC, flares or MAYDAY', 'Это не бедствие: бедствие — это NC, сигнальные ракеты или MAYDAY')],
     lambda c: dict(texts=[T(c.near(c.O, 0, 0.38), ('assistance, not distress', 'помощь, не бедствие'), 'accent')]))
plan('bs-968', 5556, ('AIS-SART · survivors', 'АИС-SART · терпящие бедствие'),
     [('An AIS-SART marks survivors in distress', 'АИС-SART обозначает терпящих бедствие'), ('Tell the coastguard, and go to assist', 'Сообщите береговой охране и идите на помощь')],
     lambda c: dict(**mob_bits(c, [T(c.near(c.Y, 120, 0.25), ('coastguard, then go', 'береговая охрана, затем идти'), 'accent')], label=('SART', 'SART'), color='#e0251b'),
                    paths=[c.line(c.near(c.Y, -25, 0.08), c.near(c.O, 155, 0.08), 'course', 6, '16 12', True)]), other=False)
plan('bs-992', 120, ('Being towed · a bridle', 'Вас буксируют · брайдель'),
     [('Make the towline fast to a bridle between both bow cleats', 'Закрепите буксирный конец на брайделе между обеими носовыми утками'), ('It spreads the load over two strong points', 'Так нагрузка распределяется на две прочные точки')],
     lambda c: dict(paths=[{'pts': [R(c.near(c.O, 180, 0.08)), [0, -0.3 * c.D]], 'c': 'line', 'w': 6}, {'pts': [[0, -0.3 * c.D], [-3, -9]], 'c': 'line', 'w': 6}, {'pts': [[0, -0.3 * c.D], [3, -9]], 'c': 'line', 'w': 6}],
                    texts=[T((0.32 * c.D, -0.2 * c.D), ('bridle', 'брайдель'), 'accent')]), bearing=False, noHeading=True)

# ---- one boat: tacks, sides, weather, handling ----
plan('bs-110', 60, ('Which tack? · port tack', 'Какой галс? · левый'),
     [('The wind comes over your port side: port tack', 'Ветер приходит с левого борта: левый галс'), ('The boom is out on the other side, to starboard', 'Гик вынесен на другой борт, вправо')],
     lambda c: dict(texts=[T((-0.45 * c.D, 0), ('wind over port side', 'ветер с левого борта'), 'red'), T((0.45 * c.D, 0.1 * c.D), ('boom to starboard', 'гик справа'))]))
plan('bs-111', 60, ('Dead run · which tack?', 'Чистый фордевинд · какой галс?'),
     [('On a run the tack is named for the side opposite the main boom', 'На фордевинде галс называют по борту, противоположному гику грота'), ('Boom to starboard: port tack', 'Гик справа: левый галс')],
     lambda c: dict(texts=[T((0.45 * c.D, 0.1 * c.D), ('boom to starboard', 'гик справа')), T((-0.45 * c.D, 0), ('port tack', 'левый галс'), 'accent')]))
plan('bs-120', 60, ('Seasick · go to leeward', 'Морская болезнь · к подветренному борту'),
     [('Wind from the east, over the starboard side: port is to leeward', 'Ветер с востока, с правого борта: левый борт — подветренный'), ('Send them to the port side, so it blows away from the boat', 'Отправьте к левому борту — туда, куда уносит ветер')],
     lambda c: dict(texts=[T((-0.45 * c.D, 0), ('leeward: here', 'подветренный: сюда'), 'accent'), T((0.45 * c.D, 0), ('windward', 'наветренный'))]))
plan('bs-121', 60, ('Everyone to windward', 'Все на наветренный борт'),
     [('Wind from the west, over the port side: port is the high, windward side', 'Ветер с запада, с левого борта: левый — высокий, наветренный борт'), ('Crew weight to windward reduces the heel', 'Вес экипажа на ветре уменьшает крен')],
     lambda c: dict(texts=[T((-0.45 * c.D, 0), ('windward: sit here', 'наветренный: сюда'), 'accent'), T((0.45 * c.D, 0), ('leeward', 'подветренный'))]))
plan('bs-654', 120, ("Buys Ballot's law", 'Закон Бейс-Балло'),
     [('Back to the wind, northern hemisphere: the low is on your left', 'Спиной к ветру, в северном полушарии: низкое давление слева'), ('Facing south-west, left is south-east: the low lies to the south-east', 'Лицом на юго-запад, слева юго-восток: центр низкого давления на юго-востоке')],
     lambda c: dict(texts=[T((0.75 * c.D, 0.75 * c.D), ('L', 'Н'), None, pill=False, size=72), T((0.75 * c.D, 0.45 * c.D), ('the low: SE', 'низкое: ЮВ'), 'red')],
                    paths=[c.line((0.1 * c.D, 0.1 * c.D), (0.6 * c.D, 0.6 * c.D), 'ink', 4, '10 10', True)]), noScale=True)
plan('bs-715', 400, ('A thunderstorm approaching', 'Приближается гроза'),
     [('Ahead of the cell the light easterly drops away', 'Перед ячейкой слабый восточный ветер стихает'), ('Then a hard gust hits from the storm: the cold downdraught’s gust front', 'Затем со стороны грозы бьёт сильный порыв — фронт холодного нисходящего потока')],
     lambda c: dict(zones=[{'pts': [[-1.0 * c.D, -0.55 * c.D], [-0.5 * c.D, -0.55 * c.D], [-0.35 * c.D, 0], [-0.5 * c.D, 0.55 * c.D], [-1.0 * c.D, 0.55 * c.D]], 'c': 'red', 'fill': 'rgba(40,50,70,.18)'}],
                    paths=[c.line((-0.32 * c.D, 0), (-0.1 * c.D, 0), 'red', 9, None, True), c.line((-0.75 * c.D, -0.4 * c.D), (-0.5 * c.D, -0.4 * c.D), 'ink', 4, None, True)],
                    texts=[T((-0.75 * c.D, 0), ('Cb', 'Cb'), None, pill=False, size=40), T((-0.2 * c.D, -0.15 * c.D), ('gust front', 'фронт порывов'), 'red'), T((-0.62 * c.D, -0.48 * c.D), ('moving east', 'идёт на восток'))]), noScale=True)
plan('bs-069', 300, ('Wind against tide', 'Ветер против течения'),
     [('Wind from the north, the current setting north: they oppose', 'Ветер с севера, течение на север: навстречу друг другу'), ('Expect short, steep, breaking seas, worse than the wind alone suggests', 'Ждите короткую, крутую, обрушивающуюся волну — хуже, чем по одному ветру')],
     lambda c: dict(land=[[[-1.2 * c.D, -1.4 * c.D], [-0.5 * c.D, -1.4 * c.D], [-0.45 * c.D, -0.6 * c.D], [-0.55 * c.D, 0.3 * c.D], [-1.2 * c.D, 0.3 * c.D]],
                          [[1.2 * c.D, -1.4 * c.D], [0.55 * c.D, -1.4 * c.D], [0.45 * c.D, -0.6 * c.D], [0.6 * c.D, 0.3 * c.D], [1.2 * c.D, 0.3 * c.D]]],
                    paths=[c.line((-0.2 * c.D, -0.3 * c.D), (-0.2 * c.D, -0.95 * c.D), 'ink', 5, None, True), c.line((0.2 * c.D, -0.3 * c.D), (0.2 * c.D, -0.95 * c.D), 'ink', 5, None, True)],
                    texts=[T((0, -1.05 * c.D), ('current 2 kn', 'течение 2 уз')), T((0, -0.6 * c.D), ('steep, breaking seas', 'крутая обрушивающаяся волна'), 'red')],
                    fit=[{'x': -1.0 * c.D, 'z': -1.4 * c.D}, {'x': 1.0 * c.D, 'z': 0.3 * c.D}]))
plan('bs-089', 40, ('Prop walk going astern', 'Заброс кормы на заднем ходу'),
     [('A right-handed propeller kicks the stern to port in astern', 'Винт правого вращения на заднем ходу забрасывает корму влево'), ('Berth port side to: a burst astern pulls the stern in alongside', 'Швартуйтесь левым бортом: короткий задний ход прижмёт корму к причалу')],
     lambda c: dict(paths=[c.line((0, 0.2 * c.D), (-0.35 * c.D, 0.35 * c.D), 'red', 7, None, True), c.line((0.25 * c.D, -0.1 * c.D), (0.25 * c.D, 0.5 * c.D), 'ink', 4, None, True)],
                    texts=[T((-0.5 * c.D, 0.52 * c.D), ('stern walks to port', 'корму заносит влево'), 'red'), T((0.55 * c.D, 0.2 * c.D), ('astern', 'задний ход'))],
                    quays=[{'x1': -0.75 * c.D, 'z1': -0.6 * c.D, 'x2': -0.62 * c.D, 'z2': 0.6 * c.D}],
                    texts2=[T((-0.85 * c.D, -0.4 * c.D), ('port side to', 'левым бортом'), 'accent')],
                    fit=[{'x': -0.85 * c.D, 'z': -0.6 * c.D}, {'x': 0.7 * c.D, 'z': 0.6 * c.D}]))
plan('bs-854', 40, ('Turning in a narrow fairway', 'Разворот в узком проходе'),
     [('Astern kicks the stern to port: turn to starboard, so it helps', 'Задний ход забрасывает корму влево: разворачивайтесь вправо — он поможет'), ('Short bursts ahead with full starboard helm, astern in between', 'Короткие толчки вперёд с рулём вправо до упора, между ними — задний ход')],
     lambda c: dict(paths=[{'pts': [R((math.sin(rad(a)) * 0.38 * c.D, -math.cos(rad(a)) * 0.38 * c.D)) for a in range(-20, 200, 20)], 'c': 'course', 'dash': '16 12', 'arrow': True}],
                    quays=[{'x1': -0.95 * c.D, 'z1': -0.9 * c.D, 'x2': -0.7 * c.D, 'z2': 0.9 * c.D}, {'x1': 0.7 * c.D, 'z1': -0.9 * c.D, 'x2': 0.95 * c.D, 'z2': 0.9 * c.D}],
                    texts=[T((0, -0.62 * c.D), ('turn to starboard', 'разворот вправо'), 'accent')], fit=[{'x': -0.95 * c.D, 'z': -0.9 * c.D}, {'x': 0.95 * c.D, 'z': 0.9 * c.D}]))
plan('bs-857', 40, ('The stern swings out', 'Корму заносит наружу'),
     [('Going ahead, a yacht pivots about a third of her length from the bow', 'На переднем ходу яхта поворачивается вокруг точки примерно в трети длины от носа'),
      ('Turn to port and the stern swings to starboard, towards the moored yacht', 'Поворот влево — корму заносит вправо, к стоящей яхте')],
     lambda c: dict(paths=[c.line((0, -0.1 * c.D), (-0.25 * c.D, -0.3 * c.D), 'course', 6, None, True), c.line((0, 0.15 * c.D), (0.25 * c.D, 0.3 * c.D), 'red', 7, None, True)],
                    texts=[T((0.3 * c.D, 0.45 * c.D), ('stern swings out', 'корму заносит'), 'red'), T((-0.35 * c.D, -0.45 * c.D), ('turn to port', 'поворот влево'), 'accent')]), bearing=False)
plan('bs-859', 30, ('Spinning a catamaran', 'Разворот катамарана на месте'),
     [('Port engine ahead, starboard engine astern: she spins to starboard', 'Левый двигатель вперёд, правый назад: катамаран разворачивается вправо'), ('Engines far apart give a strong turning couple', 'Двигатели далеко друг от друга дают сильный разворачивающий момент')],
     lambda c: dict(paths=[c.line((-0.38 * c.D, 0.2 * c.D), (-0.38 * c.D, -0.3 * c.D), 'course', 7, None, True), c.line((0.38 * c.D, -0.25 * c.D), (0.38 * c.D, 0.25 * c.D), 'red', 7, None, True)],
                    texts=[T((-0.6 * c.D, -0.2 * c.D), ('port ahead', 'левый вперёд'), 'accent'), T((0.62 * c.D, 0.2 * c.D), ('starboard astern', 'правый назад'), 'red')],
                    fit=[{'x': -0.8 * c.D, 'z': -0.5 * c.D}, {'x': 0.8 * c.D, 'z': 0.5 * c.D}]))
plan('bs-372', 300, ('Lookout under the genoa', 'Наблюдение из-под генуи'),
     [('Starboard tack, genoa to port: it hides the leeward bow', 'Правый галс, генуя слева: она закрывает подветренную скулу'), ('Look under the genoa to leeward, regularly (Rule 5)', 'Регулярно заглядывайте под геную с подветренной стороны (правило 5)')],
     lambda c: dict(zones=[{'pts': [[0, 0], R(c.near(c.Y, c.hy - 8, 1.3)), R(c.near(c.Y, c.hy - 50, 1.45)), R(c.near(c.Y, c.hy - 95, 1.3))], 'c': 'red', 'fill': 'rgba(224,37,27,.08)'}],
                    texts=[T(c.near(c.Y, c.hy - 40, 0.55), ('hidden by the genoa', 'закрыто генуей'), 'red')]), bearing=False)

# ---- layout: the frame as figure-schematic.js fits it, then every text pill moved off boats, labels, headings ----
W_, H_ = 1280, 800
def frame(sch):
    keyH = 40 + 40 * len(sch.get('key', [])) + 24; pad = sch.get('padPx', 170)
    pts = [(b['x'], b['z']) for b in sch.get('boats', [])] + [(q['x'], q['z']) for q in sch.get('fit', [])] + \
          [(a['x'], a['z']) for a in sch.get('anchors', [])]
    for c in sch.get('circles', []): pts += [(c['x'] - c['r'], c['z'] - c['r']), (c['x'] + c['r'], c['z'] + c['r'])]
    for pth in sch.get('paths', []) + sch.get('zones', []): pts += [tuple(q) for q in pth['pts']]
    for poly in sch.get('land', []): pass
    xs, zs = [q[0] for q in pts], [q[1] for q in pts]
    areaW, areaH = W_ - 2 * pad, H_ - keyH - 2 * pad
    mpp = max((max(xs) - min(xs)) / areaW, (max(zs) - min(zs)) / areaH, sch.get('minMpp', 0.08))
    cx = W_ / 2 - (min(xs) + max(xs)) / 2 / mpp; cy = pad + areaH / 2 - (min(zs) + max(zs)) / 2 / mpp
    return mpp, cx, cy, keyH

def layout(sch):
    mpp, cx, cy, keyH = frame(sch)
    P = lambda x, z: (cx + x / mpp, cy + z / mpp)
    M = lambda px, py: ((px - cx) * mpp, (py - cy) * mpp)
    obs = [(0, 0, 150, 150), (W_ - 200, 0, W_, 200), (0, H_ - keyH - 70, 240, H_ - keyH)]     # compass, wind, scale bar
    def rect(x, y, w, h): return (x - w / 2, y - h / 2, x + w / 2, y + h / 2)
    def pillw(t, s): return len(t) * s * 0.58 + s * 1.4
    boats = sch.get('boats', []); you = next((b for b in boats if b.get('you')), None)
    for b in boats:
        x, y = P(b['x'], b['z']); R = 26 * 2.6
        obs.append(rect(x, y, 2 * R, 2 * R))
        lab = b.get('label') or ('You' if b.get('you') else 'Other')
        obs.append(rect(x, y + R + 30, pillw(lab, 28) + 10, 50))
        if not b.get('noHeading'):
            for k in range(0, 9):
                d = R + k * 16; a = math.radians(b['hdg']); obs.append(rect(x + d * math.sin(a), y - d * math.cos(a), 34, 34))
        if you and b is not you and b.get('bearing', True) is not False:
            x1, y1 = P(you['x'], you['z']); a = math.atan2(y - y1, x - x1)
            mx, my = x1 + (x - x1) * 0.42 - math.sin(a) * 56, y1 + (y - y1) * 0.42 + math.cos(a) * 56
            obs.append(rect(mx, my, 260, 42))
            for k in range(1, 12): obs.append(rect(x1 + (x - x1) * k / 12, y1 + (y - y1) * k / 12, 14, 14))
    for c in sch.get('circles', []):
        x, y = P(c['x'], c['z']); r = max(10, c['r'] / mpp); obs.append(rect(x, y, 2 * r + 8, 2 * r + 8))
    for pth in sch.get('paths', []):
        q = [P(*pt) for pt in pth['pts']]
        for (x1, y1), (x2, y2) in zip(q, q[1:]):
            n = max(1, int(math.hypot(x2 - x1, y2 - y1) / 14))
            for k in range(n + 1): obs.append(rect(x1 + (x2 - x1) * k / n, y1 + (y2 - y1) * k / n, 16, 16))
    for a in sch.get('anchors', []):
        x, y = P(a['x'], a['z']); obs.append(rect(x, y, 70, 80))
    def hit(r):
        o = 0.0
        for q in obs:
            ix = min(r[2], q[2]) - max(r[0], q[0]); iy = min(r[3], q[3]) - max(r[1], q[1])
            if ix > 0 and iy > 0: o += ix * iy
        if r[0] < 8 or r[2] > W_ - 8 or r[1] < 8 or r[3] > H_ - keyH - 8: o += 1e6
        return o
    for t in sch.get('texts', []):
        if t.get('pill') is False: continue
        s = t.get('size', 24); w, h = pillw(t['text'], s), s * 1.7
        x0, y0 = P(t['x'], t['z']); best = None
        for r in range(0, 520, 24):
            for k in range(0, 24 if r else 1):
                a = math.radians(k * 15); x, y = x0 + r * math.cos(a), y0 + r * math.sin(a)
                sc = hit(rect(x, y, w + 12, h + 10)) * 10 + r
                if best is None or sc < best[0]: best = (sc, x, y)
            if best and best[0] < r + 24 and best[0] < 1e5: break
        _, x, y = best
        t['x'], t['z'] = [round(v, 1) for v in M(x, y)]; t['free'] = True
        obs.append(rect(x, y, w + 12, h + 10))
    return sch

def write(qid):
    x = LIST[qid]; p = PLANS[qid]; c = Ctx(x, p['D']); f = x['figure']
    en_ru = dict(BUILTIN); en_ru.update(x.get('ru', {}))
    def S(v):
        if isinstance(v, tuple): en_ru[v[0]] = v[1]; return v[0]
        return v
    def walk(v):
        if isinstance(v, tuple): return S(v)
        if isinstance(v, list): return [walk(a) for a in v]
        if isinstance(v, dict): return {k: walk(a) for k, a in v.items()}
        return v
    solo = f.get('other', {}).get('dist', 80) < 1
    you = {'you': True, 'x': 0, 'z': 0, 'hdg': c.hy}
    if f['you'].get('label'): you['label'] = f['you']['label']
    boats = [you]
    extra = walk(p['fn'](c)) if p['fn'] else {}
    if p.get('you_still') or p.get('noHeading') or c.you_turn: you['noHeading'] = True
    has_other = not solo and p.get('other', True)
    if has_other:
        o = f['other']; ob = {'x': round(c.O[0], 1), 'z': round(c.O[1], 1), 'hdg': c.ho}
        if o.get('label') and o['label'].strip(): ob['label'] = o['label']
        if p.get('bearing') is False: ob['bearing'] = False
        if p.get('power'): ob['power'] = True
        if p.get('noHeading'): ob['noHeading'] = True
        boats.append(ob)
    sch = {'padPx': 80, 'title': S(p['title']), 'key': [S(k) for k in p['key']], 'boats': boats}
    if f.get('wind') is not None and p.get('wind', True): sch['wind'] = f['wind']
    texts = extra.pop('texts', []) + extra.pop('texts2', [])
    night = extra.pop('night', False)
    sch.update(extra)
    if night: sch['night'] = True
    if texts: sch['texts'] = texts
    k = 0.3 * c.D
    fit = sch.get('fit', []) + [{'x': -k, 'z': -k}, {'x': k, 'z': k}]
    if has_other: fit += [{'x': c.O[0] - k, 'z': c.O[1] - k}, {'x': c.O[0] + k, 'z': c.O[1] + k}]
    sch['fit'] = [{'x': round(q['x'], 1), 'z': round(q['z'], 1)} for q in fit]
    layout(sch)
    out = {'sch': sch}
    if p.get('noScale'): out['noScale'] = True
    d = os.path.join(QDIR, qid); os.makedirs(d, exist_ok=True)
    json.dump(out, open(os.path.join(d, 'plan.json'), 'w'), ensure_ascii=False, indent=1)
    # the render's strings (note, lines, labels in 3d.labels.json) must all be in ru.json
    lab = os.path.join(d, '3d.labels.json')
    if os.path.exists(lab):
        L = json.load(open(lab))
        for s in [L.get('note')] + L.get('lines', []) + [l['text'] for l in L.get('labels', [])]:
            if s and s not in en_ru: print(qid, 'no Russian for', repr(s))
    json.dump(en_ru, open(os.path.join(d, 'ru.json'), 'w'), ensure_ascii=False, indent=1)
    return out

if __name__ == '__main__':
    ids = sys.argv[1:] or list(LIST)
    missing = [i for i in LIST if i not in PLANS]
    if missing: print('no plan for', missing)
    for i in ids:
        if i in PLANS: write(i)
    print('plans written:', len([i for i in ids if i in PLANS]))
