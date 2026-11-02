"""Checks one topic file in data/bank/ before it goes into the bank.

Usage: python3 data/check_topic.py <topic>              # Bareboat Skipper, data/bank/<topic>.json (90 questions)
       python3 data/check_topic.py <level> <topic>      # other levels, data/bank/<level>/<topic>.json (20 or, per build_level.py, 100 questions)
Checks shape, the difficulty spread, near-duplicates (within the file and against data/build_bank.py),
answers that stand out by length, and that every figure renders with docs/design/figures.js.
Exit code 1 if there are errors; warnings are printed but do not fail.
"""
import json, os, re, subprocess, sys, difflib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TOPICS = ['terms', 'ropework', 'safety', 'colregs', 'navigation', 'buoyage', 'weather', 'anchoring', 'systems', 'emergency']
FIG_TYPES = {'encounter', 'lights', 'buoy', 'compass', 'chart', 'anchor', 'isobars', 'sail', 'dayshape', 'bay', 'panel', 'card', 'rope', 'race'}
WANT = 90


def base_questions():
    """Question texts already in build_bank.py (the first 100)."""
    src = open(os.path.join(HERE, 'build_bank.py')).read()
    return re.findall(r"^q\('\w+', \d, '((?:[^'\\]|\\.)*)'", src, re.M)


def norm(s):
    return re.sub(r'[^a-z0-9 ]', '', s.lower())


def main(topic, level=None):
    global WANT
    if level:
        sys.path.insert(0, HERE)
        from build_level import LEVELS, PER_TOPIC
        WANT = LEVELS[level].get('per', PER_TOPIC)
        path = os.path.join(HERE, 'bank', level, f'{topic}.json')
    else:
        path = os.path.join(HERE, 'bank', f'{topic}.json')
    items = json.load(open(path))
    err, warn = [], []
    if len(items) != WANT:
        err.append(f'{len(items)} questions, want {WANT}')
    for i, x in enumerate(items):
        tag = f'#{i + 1}'
        keys = {'topic', 'difficulty', 'q', 'a', 'o', 'why', 'ref', 'fig'}
        if set(x) != keys:
            err.append(f'{tag}: keys {sorted(set(x))}, want {sorted(keys)}'); continue
        if x['topic'] != topic: err.append(f'{tag}: topic {x["topic"]}')
        if x['difficulty'] not in (1, 2, 3): err.append(f'{tag}: difficulty {x["difficulty"]}')
        if not isinstance(x['o'], list) or len(x['o']) != 3: err.append(f'{tag}: need exactly 3 wrong options'); continue
        opts = [x['a']] + x['o']
        if any(not isinstance(o, str) or not o.strip() for o in opts): err.append(f'{tag}: empty option')
        if len({norm(o) for o in opts}) != 4: err.append(f'{tag}: duplicate options')
        if any(re.search(r'all of the above|none of the above', o, re.I) for o in opts): err.append(f'{tag}: "all/none of the above"')
        if '\n' in x['why'] or len(x['why']) > 160: err.append(f'{tag}: why must be one short line ({len(x["why"])} chars)')
        if not x['ref'].strip(): err.append(f'{tag}: empty ref')
        la, lw = len(x['a']), max(len(o) for o in x['o'])
        if la > 2 * lw and la - lw > 25: warn.append(f'{tag}: right answer much longer than the wrong ones ({la} vs {lw})')
        f = x['fig']
        if f is not None:
            if not isinstance(f, dict) or f.get('type') not in FIG_TYPES: err.append(f'{tag}: bad figure type {f!r:.60}')
    d = [x.get('difficulty') for x in items]
    spread = [d.count(k) for k in (1, 2, 3)]
    lo, hi = round(WANT * .2 * .67), round(WANT * .2 * 1.34)
    if not (lo <= spread[0] <= hi and round(WANT * .6 * .83) <= spread[1] <= round(WANT * .6 * 1.17) and lo <= spread[2] <= hi):
        err.append(f'difficulty spread {spread}, want about {round(WANT * .2)}/{round(WANT * .6)}/{round(WANT * .2)}')
    nfig = sum(1 for x in items if x.get('fig'))
    # near-duplicates
    texts = [norm(x['q']) for x in items]
    if level:  # the other topic files of the same level
        base = [norm(x['q']) for f in os.listdir(os.path.dirname(path)) if f.endswith('.json') and f.count('.') == 1 and f != f'{topic}.json'
                for x in json.load(open(os.path.join(os.path.dirname(path), f)))]
    else:
        base = [norm(t.replace("\\'", "'")) for t in base_questions()]
    for i, t in enumerate(texts):
        for j in range(i):
            if difflib.SequenceMatcher(None, t, texts[j]).ratio() > .82:
                err.append(f'#{i + 1} near-duplicate of #{j + 1}')
        for b in base:
            if difflib.SequenceMatcher(None, t, b).ratio() > .82:
                err.append(f'#{i + 1} near-duplicate of an existing question: {b[:60]}')
    # figures render
    figs = [x['fig'] for x in items if isinstance(x.get('fig'), dict)]
    js = ("const fs=require('fs');const figSvg=new Function(fs.readFileSync(process.argv[1],'utf8')+';return figSvg')();const figs=JSON.parse(require('fs').readFileSync(0,'utf8'));"
          "figs.forEach((f,i)=>{try{const s=figSvg(f);if(/undefined|NaN/.test(s))console.log(i+': renders undefined/NaN '+JSON.stringify(f).slice(0,90));}"
          "catch(e){console.log(i+': throws '+e.message+' '+JSON.stringify(f).slice(0,90));}});")
    r = subprocess.run(['node', '-e', js, os.path.join(ROOT, 'docs', 'design', 'figures.js')], input=json.dumps(figs), capture_output=True, text=True)
    for line in (r.stdout + r.stderr).strip().splitlines():
        err.append('figure ' + line)
    if level:
        check_ru(path, items, err)
    print(f'{topic}: {len(items)} questions, difficulty {spread}, {nfig} with figures')
    for w in warn: print('  warn:', w)
    for e in err: print('  ERROR:', e)
    if len(warn) > WANT * .15: print(f'  ERROR: {len(warn)} long right answers; keep options the same length and shape'); err.append('x')
    sys.exit(1 if err else 0)


def check_ru(path, items, err):
    """The Russian file next to a topic file: same length, same shape, figure paths as i18n.figure_texts, translated."""
    rp = path[:-5] + '.ru.json'
    if not os.path.exists(rp):
        err.append('no Russian file ' + os.path.basename(rp)); return
    sys.path.insert(0, HERE)
    from i18n import figure_texts
    ru = json.load(open(rp))
    if len(ru) != len(items):
        err.append(f'ru: {len(ru)} entries for {len(items)} questions'); return
    for i, (x, r) in enumerate(zip(items, ru)):
        tag = f'ru #{i + 1}'
        if set(r) - {'q', 'a', 'o', 'why', 'ref', 'fig'} or not all(r.get(k) for k in ('q', 'a', 'o', 'why', 'ref')):
            err.append(f'{tag}: keys {sorted(r)}, want q a o why ref fig'); continue
        if not isinstance(r['o'], list) or len(r['o']) != 3: err.append(f'{tag}: need exactly 3 wrong options')
        if not re.search('[а-яё]', r['q'], re.I): err.append(f'{tag}: q is not in Russian')
        if r['q'] == x['q'] or r['why'] == x['why']: err.append(f'{tag}: untranslated')
        want, got = set(figure_texts(x['fig'])), set(r.get('fig') or {})
        if want != got: err.append(f'{tag}: figure paths {sorted(got)}, want {sorted(want)}')


if __name__ == '__main__':
    a = sys.argv[1:]
    if len(a) == 2:
        sys.path.insert(0, HERE)
        from build_level import LEVELS
        if a[0] not in LEVELS or a[1] not in [t[0] for t in LEVELS[a[0]]['topics']]:
            sys.exit('usage: check_topic.py <level> <topic> — levels and topics are in data/build_level.py')
        main(a[1], a[0])
    elif len(a) == 1 and a[0] in TOPICS:
        main(a[0])
    else:
        sys.exit('usage: check_topic.py <' + '|'.join(TOPICS) + '>  or  check_topic.py <level> <topic>')
