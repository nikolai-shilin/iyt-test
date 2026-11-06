# Puts an article's new figures into the app: for figure n (the reading order of extract_article.py) it writes
#   miniapp/figs/<level>/<article>/<n>.webp          the labelled Blender render (1280 x 800)
#   miniapp/figs/<level>/<article>/<n>-plan.webp     the plan-view schematic, when the figure has one (1200 wide)
# and the same with .ru before .webp from the Russian copies (<n>-3d-labelled.ru.jpg, <n>-schematic.ru.png), then marks
# the figure's block in data/theory/<level>/<article>.json and .ru.json with "photo": "<level>/<article>/<n>" and, with a
# schematic, "plan": its width / height. The app and the site show the photo (and the plan under it) in place of the
# drawn figure; a text card stays, under its photo.
#   python3 docs/design/blender/publish_figs.py bareboat-skipper/anchoring [...]
import json, os, re, sys
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extract_article import extract

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
ART = os.path.join(ROOT, 'docs', 'design', 'figure-style', 'articles')

def webp(src, dst, width):
    im = Image.open(src).convert('RGB')
    if im.width > width: im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    im.save(dst, 'WEBP', quality=80, method=6); return im.size

def publish(article):
    level, name = article.split('/')
    src, out = os.path.join(ART, level, name), os.path.join(ROOT, 'miniapp', 'figs', level, name)
    os.makedirs(out, exist_ok=True)
    figs = extract(article)['figs']; marks = {}
    made = json.load(open(os.path.join(ROOT, 'docs', 'design', 'article-figs', f'{level}-{name}.json')))['figs']
    if [f['fig'] for f in made] != [f['fig'] for f in figs]: raise SystemExit(f'{article}: the article\'s figures changed since the renders were made')
    for f in figs:
        n = f['n']; mark = {'photo': f'{level}/{name}/{n}'}
        webp(os.path.join(src, f'{n}-3d-labelled.jpg'), os.path.join(out, f'{n}.webp'), 1280)
        ru = os.path.join(src, f'{n}-3d-labelled.ru.jpg')
        if os.path.exists(ru): webp(ru, os.path.join(out, f'{n}.ru.webp'), 1280)
        sch = os.path.join(src, f'{n}-schematic.png')
        if os.path.exists(sch) and Image.open(sch).height > 80:      # "no schematic" captures as a thin strip
            w, h = webp(sch, os.path.join(out, f'{n}-plan.webp'), 1200); mark['plan'] = round(w / h, 3)
            sru = os.path.join(src, f'{n}-schematic.ru.png')
            if os.path.exists(sru): webp(sru, os.path.join(out, f'{n}-plan.ru.webp'), 1200)
        marks[n] = mark
    for lang in ('', '.ru'):
        # the files keep a hand-made compact layout: insert the keys as text, before each "fig": in reading order
        p = os.path.join(ROOT, 'data', 'theory', level, f'{name}{lang}.json')
        if not os.path.exists(p): continue
        txt = re.sub(r'"photo": "[^"]*", (?:"plan": [\d.]+, )?', '', open(p).read())
        at = [m.start() for m in re.finditer(r'"fig": \{', txt)]
        if len(at) != len(figs): raise SystemExit(f'{p}: {len(at)} figures, the English has {len(figs)}')
        for i in reversed(range(len(at))):
            m = marks[i + 1]
            if lang and not os.path.exists(os.path.join(out, f'{i + 1}.ru.webp')): continue   # Russian: only once its copy exists
            ins = f'"photo": "{m["photo"]}", ' + (f'"plan": {m["plan"]}, ' if 'plan' in m else '')
            txt = txt[:at[i]] + ins + txt[at[i]:]
        json.loads(txt)
        with open(p, 'w') as fh: fh.write(txt)
    have_ru = sum(os.path.exists(os.path.join(out, f'{n}.ru.webp')) for n in marks)
    print(article, len(figs), 'figures,', sum('plan' in m for m in marks.values()), 'with a plan,', have_ru, 'in Russian')

if __name__ == '__main__':
    for a in sys.argv[1:]: publish(a)
