"""Translations of a question bank.

A translation is an overlay: data/questions/<level>.<lang>.json holds only the translated text, keyed by question id,
in the same option order as the source. Figure text is addressed by path inside the figure spec ("note",
"lines.1", "labels.0.2", "lights.1.t", "you.label"), so a translation can never move a coordinate.

  python3 data/i18n.py extract bareboat-skipper            # → stdout: every string to translate, as overlay JSON
  python3 data/i18n.py check bareboat-skipper ru           # checks the overlay against the source bank

Overlay shape:
  { "level": "...", "lang": "ru", "source": "<source version>",
    "topics": { "<topic id>": "<title>" },
    "questions": { "<id>": { "q": "...", "options": [4], "why": "...", "ref": "...", "figure": { "<path>": "..." } } } }
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TEXT_KEYS = ['note', 'title', 'tag', 'rhythmNote', 'courseLabel', 'hemisphere', 'depth', 'tide', 'center']
LIST_KEYS = ['lines', 'panel']  # lists of strings


def has_words(s):
    return isinstance(s, str) and re.search(r'[A-Za-z]', s) is not None


def figure_texts(f):
    """Every translatable string in a figure spec, as {path: text}."""
    out = {}
    if not f:
        return out
    for k in TEXT_KEYS:
        if has_words(f.get(k)):
            out[k] = f[k]
    for k in LIST_KEYS:
        for i, s in enumerate(f.get(k) or []):
            if has_words(s):
                out[f'{k}.{i}'] = s
    for i, l in enumerate(f.get('labels') or []):
        if len(l) > 2 and has_words(l[2]):
            out[f'labels.{i}.2'] = l[2]
    for i, m in enumerate(f.get('marks') or []):
        if len(m) > 3 and has_words(m[3]):
            out[f'marks.{i}.3'] = m[3]
    for i, g in enumerate(f.get('gauges') or []):
        for j in (0, 1):
            if has_words(g[j]):
                out[f'gauges.{i}.{j}'] = g[j]
    for i, l in enumerate(f.get('lights') or []):
        if has_words(l.get('t')):
            out[f'lights.{i}.t'] = l['t']
    for who in ('you', 'other'):
        if has_words((f.get(who) or {}).get('label')):
            out[f'{who}.label'] = f[who]['label']
    return out


def load(level, lang=None):
    name = f'{level}.{lang}.json' if lang else f'{level}.json'
    return json.loads((ROOT / 'questions' / name).read_text())


def extract(level):
    bank = load(level)
    return {
        'level': level, 'lang': 'xx', 'source': bank['version'],
        'topics': {t['id']: t['title'] for t in bank['topics']},
        'questions': {
            q['id']: {k: v for k, v in {
                'q': q['q'], 'options': q['options'], 'why': q['why'], 'ref': q['ref'], 'figure': figure_texts(q['figure']),
            }.items() if v}
            for q in bank['questions']
        },
    }


def check(level, lang):
    src, tr = extract(level), load(level, lang)
    errs, missing = [], []
    missing_t = set(src['topics']) - set(tr.get('topics', {}))
    if missing_t:
        errs.append(f'topics missing: {sorted(missing_t)}')
    for qid, s in src['questions'].items():
        t = tr['questions'].get(qid)
        if not t:
            missing.append(qid)
            continue
        for k in ('q', 'why', 'ref'):
            if not t.get(k):
                errs.append(f'{qid}: no {k}')
        if len(t.get('options') or []) != 4:
            errs.append(f'{qid}: needs 4 options')
        sf, tf = set(s.get('figure', {})), set(t.get('figure', {}))
        if sf != tf:
            errs.append(f'{qid}: figure paths differ — missing {sorted(sf - tf)}, extra {sorted(tf - sf)}')
        left = [k for k in ('q', 'why') if t.get(k) == s.get(k)]
        if left:
            errs.append(f'{qid}: untranslated {left}')
    extra = set(tr['questions']) - set(src['questions'])
    if extra:
        errs.append(f'unknown ids: {sorted(extra)}')
    if tr.get('source') != src['source']:
        errs.append(f"overlay made from {tr.get('source')}, bank is {src['source']} — re-check changed questions")
    done = len(src['questions']) - len(missing)
    print(f'{lang}: {done} of {len(src["questions"])} questions translated' + (f' — not yet: {", ".join(missing[:8])}{" …" if len(missing) > 8 else ""}' if missing else ''))
    if errs:
        print('\n'.join(errs))
    return not errs and not missing


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else ''
    if cmd == 'extract':
        print(json.dumps(extract(sys.argv[2]), ensure_ascii=False, indent=1))
    elif cmd == 'check':
        sys.exit(0 if check(sys.argv[2], sys.argv[3]) else 1)
    else:
        print(__doc__)
