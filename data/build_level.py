"""Builds the question banks of the levels whose questions live only in topic files (every level but Bareboat
Skipper, which has its own build_bank.py): the IYT levels with 20 questions per topic, and Racing Rules of Sailing
with 100 per topic (`per` in LEVELS; `title` and `note` when the level is not an IYT course).

  python3 data/build_level.py                      # all levels below
  python3 data/build_level.py international-crew   # one level

For each level, data/bank/<level>/<topic>.json is an array of {topic, difficulty, q, a, o, why, ref, fig} — the same
fields as build_bank.py — and data/bank/<level>/<topic>.ru.json is its Russian text in the same order:
{q, a, o, why, ref, fig}, where fig maps figure text paths (see i18n.py figure_texts) to the translation.
Writes data/questions/<level>.json and, when every topic has its .ru.json, data/questions/<level>.ru.json.
Ids come from position (<prefix>-001 …, topics in the order below), so never insert, delete or reorder a question
in a topic file — append new ones to the end of the last topic, or add a batch after it.
"""
import json, os, random, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from i18n import figure_texts  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
NOTE = ('Scenario questions written for study, close to the IYT {name} syllabus. Not official IYT exam content. '
        'figure is a spec for docs/design/figures.js (null = text question). Pass mark, exam size and time are app defaults to verify.')

RRS_NOTE = ('Scenario questions on the Racing Rules of Sailing 2025–2028 (World Sailing), written for study: real situations on the '
            'course, at the start, at marks, in protests. Not an official World Sailing publication; the rules themselves are the authority. '
            'figure is a spec for docs/design/figures.js (null = text question). Pass mark, exam size and time are app defaults.')

CHECKIN_NOTE = ('Scenario questions on the charter check-in, written for study: taking over a bareboat at the base — papers, the walk-round, '
                'engine, electrics, water and gas, instruments, safety gear, ground tackle — and handing it back. Not an IYT course and not '
                'any charter company\'s procedure; the contract and the base\'s briefing are the authority. figure is a spec for '
                'docs/design/figures.js (null = text question). Pass mark, exam size and time are app defaults.')

# topics: (id, English title, Russian title, Russian short name, icon for the mini app)
LEVELS = {
    'vhf-radio-operator': dict(
        prefix='vhf', name='VHF Radio Operator', passMark=70, examQuestions=30, examMinutes=45, version='2026-11-02b',
        topics=[
            ('set', 'The VHF set & its controls', 'УКВ-радиостанция и её органы управления', 'Радиостанция', 'vhf'),
            ('channels', 'Channels & range', 'Каналы и дальность связи', 'Каналы', 'radio'),
            ('calls', 'Routine calls & radio discipline', 'Обычные вызовы и порядок в эфире', 'Вызовы', 'mic'),
            ('phonetic', 'Phonetic alphabet & procedure words', 'Фонетический алфавит и процедурные слова', 'Алфавит', 'flag-alpha'),
            ('dsc', 'DSC & MMSI', 'ЦИВ (DSC) и MMSI', 'ЦИВ', 'mmsi'),
            ('distress', 'Distress — MAYDAY', 'Бедствие — MAYDAY', 'MAYDAY', 'flare'),
            ('urgency', 'Urgency & safety — PAN-PAN, SÉCURITÉ', 'Срочность и безопасность — PAN-PAN, SÉCURITÉ', 'PAN-PAN', 'megaphone'),
            ('sar', 'Search & rescue communications', 'Связь при поиске и спасании', 'Спасание', 'lifebuoy'),
            ('gmdss', 'GMDSS, EPIRB, SART, NAVTEX & AIS', 'ГМССБ, АРБ, САРТ, НАВТЕКС и АИС', 'ГМССБ', 'beacon'),
            ('licences', 'Licences & regulations', 'Лицензии и правила радиосвязи', 'Правила', 'licence'),
        ]),
    'international-crew': dict(
        prefix='ic', name='International Crew', passMark=70, examQuestions=30, examMinutes=45, version='2026-11-02b',
        topics=[
            ('boat', 'Parts of the boat & terms', 'Устройство яхты и термины', 'Термины', 'yacht'),
            ('sailing', 'Points of sail & sail handling', 'Курсы относительно ветра и работа с парусами', 'Паруса', 'sail'),
            ('knots', 'Knots & line handling', 'Узлы и работа с тросами', 'Узлы', 'knot'),
            ('deck', 'Deck work — winches, fenders & lines', 'Работа на палубе — лебёдки, кранцы, швартовы', 'Палуба', 'cleat'),
            ('helming', 'Helming & manoeuvres', 'Рулевой и манёвры', 'Руль', 'wheel'),
            ('safety', 'Safety gear & personal safety', 'Спасательное снаряжение и личная безопасность', 'Безопасность', 'lifejacket'),
            ('lookout', 'Lookout & rules of the road', 'Наблюдение и правила плавания', 'МППСС', 'binoculars'),
            ('weather', 'Weather basics', 'Основы погоды', 'Погода', 'cloud'),
            ('aboard', 'Life aboard', 'Жизнь на борту', 'Быт', 'mug'),
            ('emergency', 'Emergencies & first aid', 'Аварии и первая помощь', 'Аварии', 'medkit'),
        ]),
    'flotilla-skipper': dict(
        prefix='fs', name='Flotilla Skipper', passMark=70, examQuestions=40, examMinutes=60, version='2026-11-02b',
        topics=[
            ('power', 'Boat handling under power', 'Управление яхтой под мотором', 'Под мотором', 'propeller'),
            ('mooring', 'Mooring & anchoring', 'Швартовка и якорная стоянка', 'Швартовка', 'anchor'),
            ('sailing', 'Sail handling & reefing', 'Работа с парусами и рифление', 'Паруса', 'sail'),
            ('colregs', 'Rules of the road (COLREGs)', 'Правила плавания (МППСС-72)', 'МППСС', 'rules'),
            ('buoyage', 'Buoyage & lights', 'Навигационное ограждение и огни', 'Буи и огни', 'buoy'),
            ('pilotage', 'Charts & pilotage', 'Карты и лоцманская проводка', 'Карты', 'lighthouse'),
            ('weather', 'Weather & forecasts', 'Погода и прогнозы', 'Погода', 'barometer'),
            ('systems', 'Engine & boat systems', 'Двигатель и системы яхты', 'Двигатель', 'gear'),
            ('skipper', 'Skipper duties & flotilla routine', 'Обязанности шкипера и порядок во флотилии', 'Шкипер', 'captain'),
            ('emergency', 'Safety & emergencies', 'Безопасность и аварии', 'Аварии', 'lifebuoy'),
        ]),
    # IYT Yachtmaster Coastal (iytworld.com/courses/yachtmaster-coastal): the course outline's 13 headings as ten topics of 100 —
    # charts and publications; DR and EP; position fixing; tides; pilotage; passage planning; COLREGs; meteorology; safety;
    # ropework, anchoring, boat handling and docking. IYT does not publish the theory exam's size, time or pass mark.
    'yachtmaster-coastal': dict(
        prefix='yc', name='Yachtmaster Coastal', per=100, passMark=70, examQuestions=50, examMinutes=90, version='2026-11-03',
        topics=[
            ('charts', 'Navigational charts & publications', 'Навигационные карты и пособия', 'Карты', 'map'),
            ('dr', 'Dead reckoning, estimated position & course to steer', 'Счисление, счислимое место и курс, которым править', 'Счисление', 'dividers'),
            ('fixing', 'Position fixing & the compass', 'Определение места и компас', 'Обсервация', 'compass'),
            ('tides', 'Tides & tidal streams', 'Приливы и приливо-отливные течения', 'Приливы', 'tide'),
            ('pilotage', 'Pilotage, buoyage & lights', 'Лоцманская проводка, навигационное ограждение и огни', 'Проводка', 'lighthouse'),
            ('passage', 'Passage planning & passage making', 'Планирование и выполнение перехода', 'Переход', 'route'),
            ('colregs', 'International collision regulations (COLREGs)', 'Международные правила предупреждения столкновений (МППСС-72)', 'МППСС', 'rules'),
            ('weather', 'Meteorology', 'Метеорология', 'Погода', 'barometer'),
            ('safety', 'Safety at sea & emergencies', 'Безопасность на море и аварийные ситуации', 'Безопасность', 'lifebuoy'),
            ('seamanship', 'Ropework, anchoring, boat handling & docking', 'Работа с тросами, якорная стоянка, управление и швартовка', 'Морская практика', 'cleat'),
        ]),
    # IYT Yachtmaster Offshore (iytworld.com/courses/yachtmaster-offshore): command up to 24 m, up to 150 nm offshore. The course
    # outline's 23 headings as ten topics of 100, a step above Coastal: UK tides, construction, stability and the power plant,
    # towing, maritime business and law. IYT does not publish the theory exam's size, time or pass mark.
    'yachtmaster-offshore': dict(
        prefix='yof', name='Yachtmaster Offshore', per=100, passMark=70, examQuestions=50, examMinutes=90, version='2026-11-04',
        topics=[
            ('charts', 'Charts, chartwork instruments & publications', 'Карты, штурманские инструменты и пособия', 'Карты', 'map'),
            ('compass', 'The compass, position lines & fixes', 'Компас, линии положения и обсервации', 'Компас', 'compass'),
            ('dr', 'Dead reckoning, EP & course to steer', 'Счисление, счислимое место и курс, которым править', 'Счисление', 'dividers'),
            ('tides', 'Tides, tidal streams, races & bars', 'Приливы, течения, сулои и бары', 'Приливы', 'tide'),
            ('pilotage', 'Pilotage, passage planning & electronic aids', 'Лоцманская проводка, планирование перехода и электронные средства', 'Проводка', 'lighthouse'),
            ('colregs', 'International collision regulations (COLREGs)', 'Международные правила предупреждения столкновений (МППСС-72)', 'МППСС', 'rules'),
            ('weather', 'Meteorology', 'Метеорология', 'Погода', 'barometer'),
            ('vessel', 'Construction, stability & the power plant', 'Конструкция, остойчивость и силовая установка', 'Яхта', 'yacht'),
            ('seamanship', 'Ropework, towing, anchoring & docking', 'Работа с тросами, буксировка, якорная стоянка и швартовка', 'Морская практика', 'cleat'),
            ('emergency', 'Emergencies, maritime business & law', 'Аварийные ситуации, морской бизнес и право', 'Аварии и право', 'lifebuoy'),
        ]),
    # IYT Yachtmaster Ocean (iytworld.com/courses/yachtmaster-ocean): celestial navigation, great circles, ocean weather and
    # passage planning — the course outline's 16 headings as ten topics of 100. Requires Yachtmaster Offshore; any ocean, up to
    # 24 m. IYT does not publish the exam's size, time or pass mark.
    'yachtmaster-ocean': dict(
        prefix='yo', name='Yachtmaster Ocean', per=100, passMark=70, examQuestions=50, examMinutes=120, version='2026-11-04',
        topics=[
            ('sphere', 'The Earth, the celestial sphere & the PZX triangle', 'Земля, небесная сфера и параллактический треугольник', 'Небесная сфера', 'globe'),
            ('sextant', 'The sextant & altitude corrections', 'Секстан и поправки высот', 'Секстан', 'sextant'),
            ('time', 'Measurement of time', 'Измерение времени', 'Время', 'timer'),
            ('meridian', 'Meridian altitudes & the pole star', 'Высота в меридиане и Полярная звезда', 'Меридиан', 'meridian'),
            ('sun', 'Sun sights', 'Наблюдения Солнца', 'Солнце', 'sun'),
            ('stars', 'Planets, moon & stars', 'Планеты, Луна и звёзды', 'Звёзды', 'star'),
            ('compass', 'Compass checking & satellite navigation', 'Проверка компаса и спутниковая навигация', 'Компас и GNSS', 'compass'),
            ('greatcircle', 'Great circle sailing', 'Плавание по дуге большого круга', 'Ортодромия', 'map'),
            ('weather', 'Ocean meteorology', 'Метеорология океана', 'Погода', 'wind'),
            ('passage', 'Ocean passage planning', 'Планирование океанского перехода', 'Переход', 'route'),
        ]),
    # Not an IYT course: the Racing Rules of Sailing (World Sailing, 2025–2028), as situations on the race course.
    'racing-rules': dict(
        prefix='rr', name='Racing Rules of Sailing', title='Racing Rules of Sailing', note=RRS_NOTE, per=100,
        passMark=70, examQuestions=40, examMinutes=60, version='2026-11-03',
        topics=[
            ('definitions', 'Definitions & basic principles', 'Определения и основные принципы', 'Определения', 'book'),
            ('rightofway', 'Right of way — opposite tacks, same tack, tacking (Rules 10–13)', 'Право дороги — разные галсы, один галс, поворот оверштаг (правила 10–13)', 'Право дороги', 'sail'),
            ('limits', 'General limitations — contact, acquiring right of way, changing course (Rules 14–17)', 'Общие ограничения — контакт, получение права дороги, изменение курса (правила 14–17)', 'Ограничения', 'wheel'),
            ('marks', 'Mark-room (Rule 18)', 'Место-у-знака (правило 18)', 'Знаки', 'buoy'),
            ('obstructions', 'Obstructions, room to tack & other situations (Rules 19–23)', 'Препятствия, место для поворота и другие ситуации (правила 19–23)', 'Препятствия', 'lighthouse'),
            ('starting', 'Starting — signals, recalls & starting penalties', 'Старт — сигналы, отзывы и наказания на старте', 'Старт', 'timer'),
            ('course', 'Sailing the course, marks & finishing', 'Прохождение дистанции, знаки и финиш', 'Дистанция', 'map'),
            ('propulsion', 'Propulsion & other requirements when racing', 'Движущая сила и другие требования во время гонки', 'Правило 42', 'wind'),
            ('penalties', 'Penalties at the time of an incident', 'Наказания в момент инцидента', 'Наказания', 'refresh'),
            ('protests', 'Protests, hearings, redress & scoring', 'Протесты, рассмотрение, исправление результата и очки', 'Протесты', 'trophy'),
        ]),
    # Not an IYT course: the charter check-in — taking over a bareboat at the base, Saturday to Saturday, and handing it back.
    'charter-checkin': dict(
        prefix='ci', name='Charter Check-in', title='Charter Check-in', note=CHECKIN_NOTE, per=50,
        passMark=70, examQuestions=40, examMinutes=60, version='2026-11-03b',
        topics=[
            ('papers', 'Documents, contract & base briefing', 'Документы, договор и брифинг на базе', 'Документы', 'licence'),
            ('hull', 'Hull, deck & rigging walk-round', 'Осмотр корпуса, палубы и такелажа', 'Корпус', 'yacht'),
            ('sails', 'Sails, furling & reefing gear', 'Паруса, закрутки и рифы', 'Паруса', 'sail'),
            ('engine', 'Engine, fuel & propulsion', 'Двигатель, топливо и движитель', 'Двигатель', 'propeller'),
            ('electrics', 'Batteries, electrics & shore power', 'Аккумуляторы, электрика и береговое питание', 'Электрика', 'battery'),
            ('plumbing', 'Water, gas, heads & bilge', 'Вода, газ, гальюны и трюм', 'Вода и газ', 'drop'),
            ('nav', 'Navigation, electronics & VHF', 'Навигация, электроника и УКВ', 'Навигация', 'compass'),
            ('safety', 'Safety equipment', 'Спасательное снаряжение', 'Безопасность', 'lifejacket'),
            ('ground', 'Anchor, mooring gear & dinghy', 'Якорь, швартовное имущество и тузик', 'Якорь', 'anchor'),
            ('return', 'Inventory, deposit & check-out', 'Инвентарь, депозит и сдача яхты', 'Сдача', 'clipboard'),
        ]),
}
PER_TOPIC = 20


def load(level, topic, lang=None):
    p = os.path.join(HERE, 'bank', level, f'{topic}.{lang}.json' if lang else f'{topic}.json')
    return json.load(open(p)) if os.path.exists(p) else None


def build(level):
    L = LEVELS[level]
    per = L.get('per', PER_TOPIC)
    Q, R = [], []
    for t, *_ in L['topics']:
        items = load(level, t)
        assert items and len(items) == per, f'{level}/{t}: {len(items or [])} questions, want {per}'
        assert all(x['topic'] == t for x in items), f'{level}/{t}: wrong topic field'
        ru = load(level, t, 'ru')
        assert ru is None or len(ru) == len(items), f'{level}/{t}.ru: {len(ru)} entries for {len(items)} questions'
        Q += items
        R += ru if ru else [None] * len(items)
    rnd = random.Random(2026)
    out, tr = [], {}
    for i, (x, r) in enumerate(zip(Q, R)):
        wrong = list(range(3)); rnd.shuffle(wrong); target = i % 4
        order = wrong[:]; order.insert(target, 'a')  # 'a' = the right answer, ints = index into o
        pick = lambda src: [src['a'] if k == 'a' else src['o'][k] for k in order]
        qid = f'{L["prefix"]}-{i + 1:03d}'
        out.append(dict(id=qid, topic=x['topic'], difficulty=x['difficulty'], q=x['q'], figure=x['fig'], options=pick(x),
                        answer=target, why=x['why'], ref=x['ref']))
        if r:
            want = set(figure_texts(x['fig']))
            got = set((r.get('fig') or {}))
            assert want == got, f'{qid}: Russian figure paths {sorted(got)}, want {sorted(want)}'
            tr[qid] = {k: v for k, v in dict(q=r['q'], options=pick(r), why=r['why'], ref=r['ref'], figure=r.get('fig') or {}).items() if v}
    bank = dict(level=level, title=L.get('title', f'IYT {L["name"]}'), lang='en', passMark=L['passMark'], examQuestions=L['examQuestions'],
                examMinutes=L['examMinutes'], version=L['version'], note=L.get('note', NOTE.format(name=L['name'])),
                topics=[dict(id=t, title=n, icon=ic, count=sum(1 for x in Q if x['topic'] == t)) for t, n, _, _, ic in L['topics']],
                questions=out)
    qdir = os.path.join(HERE, 'questions')
    json.dump(bank, open(os.path.join(qdir, f'{level}.json'), 'w'), ensure_ascii=False, indent=2)
    msg = f'{level}: {len(out)} questions, {sum(1 for x in out if x["figure"])} with figures, answers by position {[sum(1 for x in out if x["answer"] == k) for k in range(4)]}'
    if len(tr) == len(out):
        ov = dict(level=level, lang='ru', source=L['version'], note='Russian overlay, built by data/build_level.py from data/bank/<level>/<topic>.ru.json.',
                  topics={t: ru for t, _, ru, _, _ in L['topics']}, short={t: s for t, _, _, s, _ in L['topics']}, questions=tr)
        json.dump(ov, open(os.path.join(qdir, f'{level}.ru.json'), 'w'), ensure_ascii=False, indent=1)
        msg += ', Russian overlay written'
    else:
        msg += f', Russian for {len(tr)} of {len(out)} — overlay not written'
    print(msg)


if __name__ == '__main__':
    for lv in (sys.argv[1:] or LEVELS):
        build(lv)
