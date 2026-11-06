# Writes docs/design/article-figs/<level>-<article>.json from data/theory/<level>/<article>.json: every figure in
# reading order with its section kicker, tile name and caption (tile note, else the figure's own caption).
#   python3 docs/design/blender/extract_article.py bareboat-skipper/colregs [--check]
import json, os, sys
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..')

def extract(article):
    level, name = article.split('/')
    d = json.load(open(os.path.join(ROOT, 'data', 'theory', level, name + '.json')))
    figs = []
    def add(fig, section, name=None, cap=None):
        e = {'n': len(figs) + 1, 'section': section, 'fig': fig, 'cap': cap}
        if name: e['name'] = name
        figs.append(e)
    for s in d['sections']:
        for b in s.get('blocks', []):
            if 'fig' in b: add(b['fig'], s['kicker'], b.get('name'), b.get('note') or b.get('cap'))
            for t in b.get('tiles', []) or []:
                if 'fig' in t: add(t['fig'], s['kicker'], t.get('name'), t.get('note') or t.get('cap'))
    return {'article': article, 'topic': d.get('topic'), 'lead': d.get('lead'), 'figs': figs}

if __name__ == '__main__':
    a = sys.argv[1]; out = extract(a)
    p = os.path.join(ROOT, 'docs', 'design', 'article-figs', a.replace('/', '-') + '.json')
    if '--check' in sys.argv:
        old = json.load(open(p)); print('same figs:', [f['fig'] for f in old['figs']] == [f['fig'] for f in out['figs']], len(old['figs']), len(out['figs']))
        for o, n in zip(old['figs'], out['figs']):
            if (o.get('cap'), o['section'], o.get('name')) != (n.get('cap'), n['section'], n.get('name')): print(' diff', o['n'], (o.get('cap'), o.get('name')), (n.get('cap'), n.get('name')))
    else:
        json.dump(out, open(p, 'w'), indent=1, ensure_ascii=False); print(p, len(out['figs']), 'figures')
