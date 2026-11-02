"""Builds the question banks of the levels whose questions live only in topic files (every level but Bareboat
Skipper, which has its own build_bank.py).

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

# topics: (id, English title, Russian title, Russian short name, icon for the mini app)
LEVELS = {
    'vhf-radio-operator': dict(
        prefix='vhf', name='VHF Radio Operator', passMark=70, examQuestions=30, examMinutes=45, version='2026-11-02b',
        topics=[
            ('set', 'The VHF set & its controls', 'УКВ-радиостанция и её органы управления', 'Радиостанция', 'wrench'),
            ('channels', 'Channels & range', 'Каналы и дальность связи', 'Каналы', 'radio'),
            ('calls', 'Routine calls & radio discipline', 'Обычные вызовы и порядок в эфире', 'Вызовы', 'user'),
            ('phonetic', 'Phonetic alphabet & procedure words', 'Фонетический алфавит и процедурные слова', 'Алфавит', 'book'),
            ('dsc', 'DSC & MMSI', 'ЦИВ (DSC) и MMSI', 'ЦИВ', 'target'),
            ('distress', 'Distress — MAYDAY', 'Бедствие — MAYDAY', 'MAYDAY', 'flag'),
            ('urgency', 'Urgency & safety — PAN-PAN, SÉCURITÉ', 'Срочность и безопасность — PAN-PAN, SÉCURITÉ', 'PAN-PAN', 'light'),
            ('sar', 'Search & rescue communications', 'Связь при поиске и спасании', 'Спасание', 'ring'),
            ('gmdss', 'GMDSS, EPIRB, SART, NAVTEX & AIS', 'ГМССБ, АРБ, САРТ, НАВТЕКС и АИС', 'ГМССБ', 'globe'),
            ('licences', 'Licences & regulations', 'Лицензии и правила радиосвязи', 'Правила', 'book'),
        ]),
    'international-crew': dict(
        prefix='ic', name='International Crew', passMark=70, examQuestions=30, examMinutes=45, version='2026-11-02b',
        topics=[
            ('boat', 'Parts of the boat & terms', 'Устройство яхты и термины', 'Термины', 'yacht'),
            ('sailing', 'Points of sail & sail handling', 'Курсы относительно ветра и работа с парусами', 'Паруса', 'wind'),
            ('knots', 'Knots & line handling', 'Узлы и работа с тросами', 'Узлы', 'rope'),
            ('deck', 'Deck work — winches, fenders & lines', 'Работа на палубе — лебёдки, кранцы, швартовы', 'Палуба', 'wrench'),
            ('helming', 'Helming & manoeuvres', 'Рулевой и манёвры', 'Руль', 'compass'),
            ('safety', 'Safety gear & personal safety', 'Спасательное снаряжение и личная безопасность', 'Безопасность', 'ring'),
            ('lookout', 'Lookout & rules of the road', 'Наблюдение и правила плавания', 'МППСС', 'light'),
            ('weather', 'Weather basics', 'Основы погоды', 'Погода', 'sun'),
            ('aboard', 'Life aboard', 'Жизнь на борту', 'Быт', 'user'),
            ('emergency', 'Emergencies & first aid', 'Аварии и первая помощь', 'Аварии', 'radio'),
        ]),
    'flotilla-skipper': dict(
        prefix='fs', name='Flotilla Skipper', passMark=70, examQuestions=40, examMinutes=60, version='2026-11-02b',
        topics=[
            ('power', 'Boat handling under power', 'Управление яхтой под мотором', 'Под мотором', 'yacht'),
            ('mooring', 'Mooring & anchoring', 'Швартовка и якорная стоянка', 'Швартовка', 'anchor'),
            ('sailing', 'Sail handling & reefing', 'Работа с парусами и рифление', 'Паруса', 'wind'),
            ('colregs', 'Rules of the road (COLREGs)', 'Правила плавания (МППСС-72)', 'МППСС', 'compass'),
            ('buoyage', 'Buoyage & lights', 'Навигационное ограждение и огни', 'Буи и огни', 'buoy'),
            ('pilotage', 'Charts & pilotage', 'Карты и лоцманская проводка', 'Карты', 'map'),
            ('weather', 'Weather & forecasts', 'Погода и прогнозы', 'Погода', 'sun'),
            ('systems', 'Engine & boat systems', 'Двигатель и системы яхты', 'Двигатель', 'wrench'),
            ('skipper', 'Skipper duties & flotilla routine', 'Обязанности шкипера и порядок во флотилии', 'Шкипер', 'user'),
            ('emergency', 'Safety & emergencies', 'Безопасность и аварии', 'Аварии', 'radio'),
        ]),
}
PER_TOPIC = 20


def load(level, topic, lang=None):
    p = os.path.join(HERE, 'bank', level, f'{topic}.{lang}.json' if lang else f'{topic}.json')
    return json.load(open(p)) if os.path.exists(p) else None


def build(level):
    L = LEVELS[level]
    Q, R = [], []
    for t, *_ in L['topics']:
        items = load(level, t)
        assert items and len(items) == PER_TOPIC, f'{level}/{t}: {len(items or [])} questions, want {PER_TOPIC}'
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
    bank = dict(level=level, title=f'IYT {L["name"]}', lang='en', passMark=L['passMark'], examQuestions=L['examQuestions'],
                examMinutes=L['examMinutes'], version=L['version'], note=NOTE.format(name=L['name']),
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
