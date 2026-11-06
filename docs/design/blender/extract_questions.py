# Lists a level's drawn test figures for the image generators, one file per figure type:
#   docs/design/figure-style/questions/<level>/<type>.json
#   [{id, topic, q, answer, why, figure, ru: {English text on the figure: its Russian}}]
# The answer and why are there to check an image against, never to print on it.
#   python3 docs/design/blender/extract_questions.py bareboat-skipper
import json, os, sys, collections
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'data'))
from i18n import figure_texts

def extract(level):
    bank = json.load(open(os.path.join(ROOT, 'data', 'questions', f'{level}.json')))['questions']
    ru = json.load(open(os.path.join(ROOT, 'data', 'questions', f'{level}.ru.json')))['questions']
    by = collections.defaultdict(list)
    for q in bank:
        f = q.get('figure')
        if not f or f['type'] == 'card': continue
        tr = (ru.get(q['id']) or {}).get('figure') or {}
        texts = {en: tr[p] for p, en in figure_texts(f).items() if p in tr}
        by[f['type']].append(dict(id=q['id'], topic=q['topic'], q=q['q'], answer=q['options'][q['answer']], why=q['why'], figure=f, ru=texts))
    out = os.path.join(ROOT, 'docs', 'design', 'figure-style', 'questions', level); os.makedirs(out, exist_ok=True)
    for t, xs in sorted(by.items()):
        json.dump(xs, open(os.path.join(out, f'{t}.json'), 'w'), ensure_ascii=False, indent=1); print(t, len(xs))

if __name__ == '__main__':
    extract(sys.argv[1])
