# Puts the new-style images of a level's test questions into the app. Reads
# docs/design/figure-style/questions/<level>/questions.json, one entry per figure, keyed by a slug:
#   id       the question (data/questions/<level>.json), to find its entry in data/bank/<level>/<topic>.json
#   render   the unlabelled Blender render, under docs/design/figure-style/ (an article's, or one made for the question)
#   plan     the schematic for the answer, without .png (an article's <n>-schematic, or questions/<level>/<slug>/plan);
#            its Russian copy is the same name with .ru.png. No plan: the answer shows none.
#   note, lines, labels   what is printed on the render: only the figure's own data, never the answer
# For each it writes <slug>/3d.jpg, 3d.labels.json and the labelled copies (label.py, and --ru through the level's
# ru.json), then miniapp/figs/q/<level>/<slug>[.ru].webp and -plan[.ru].webp, and sets "photo" and "plan" on the
# question's entry in the bank source. Rebuild the bank afterwards: python3 data/build_level.py <level>
#   python3 docs/design/blender/publish_q.py vhf-radio-operator
import json, os, shutil, subprocess, sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
STYLE = os.path.join(ROOT, 'docs', 'design', 'figure-style')

def webp(src, dst, width):
    im = Image.open(src).convert('RGB')
    if im.width > width: im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    im.save(dst, 'WEBP', quality=75, method=6); return im.size

def publish(level):
    qdir = os.path.join(STYLE, 'questions', level)
    spec = json.load(open(os.path.join(qdir, 'questions.json')))
    bank = {q['id']: q for q in json.load(open(os.path.join(ROOT, 'data', 'questions', f'{level}.json')))['questions']}
    out = os.path.join(ROOT, 'miniapp', 'figs', 'q', level); os.makedirs(out, exist_ok=True)
    marks = {}
    for slug, s in spec.items():
        d = os.path.join(qdir, slug); os.makedirs(d, exist_ok=True)
        r3d = os.path.join(d, '3d.jpg')
        if os.path.abspath(os.path.join(STYLE, s['render'])) != r3d: shutil.copy(os.path.join(STYLE, s['render']), r3d)
        json.dump({'note': s.get('note'), 'lines': s.get('lines', []), 'labels': s.get('labels', []), 'arrows': []},
                  open(os.path.join(d, '3d.labels.json'), 'w'), ensure_ascii=False, indent=1)
        shutil.copy(os.path.join(qdir, 'ru.json'), os.path.join(d, 'ru.json'))      # label.py --ru reads it beside the render
        subprocess.run(['python3', os.path.join(HERE, 'label.py'), r3d], check=True, capture_output=True)
        subprocess.run(['python3', os.path.join(HERE, 'label.py'), '--ru', r3d], check=True, capture_output=True)
        os.remove(os.path.join(d, 'ru.json'))
        webp(os.path.join(d, '3d-labelled.jpg'), os.path.join(out, f'{slug}.webp'), 960)
        webp(os.path.join(d, '3d-labelled.ru.jpg'), os.path.join(out, f'{slug}.ru.webp'), 960)
        mark = {'photo': f'q/{level}/{slug}'}
        if s.get('plan'):
            p = os.path.join(STYLE, s['plan'])
            w, h = webp(p + '.png', os.path.join(out, f'{slug}-plan.webp'), 960); mark['plan'] = round(w / h, 3)
            if not os.path.exists(p + '.ru.png'): raise SystemExit(f'{slug}: no Russian plan {p}.ru.png')
            webp(p + '.ru.png', os.path.join(out, f'{slug}-plan.ru.webp'), 960)
        marks[s['id']] = mark
    # the bank source: the entry with the question's text, in its topic's file (format kept: indent 1, no newline at the end)
    for qid, mark in marks.items():
        q = bank[qid]; p = os.path.join(ROOT, 'data', 'bank', level, f'{q["topic"]}.json')
        items = json.load(open(p)); hit = [x for x in items if x['q'] == q['q']]
        if len(hit) != 1: raise SystemExit(f'{qid}: {len(hit)} entries in {p} with its text')
        hit[0].pop('photo', None); hit[0].pop('plan', None); hit[0].update(mark)
        open(p, 'w').write(json.dumps(items, ensure_ascii=False, indent=1))
        print(qid, mark)

def publish_dirs(level, only=None):
    """A level whose figures are made per question (bareboat-skipper): docs/design/figure-style/questions/<level>/<id>/
    holds 3d.jpg + 3d.labels.json (a Blender render, labelled here) or q.png (a 2D image), plan.png when the answer
    has a plan, the Russian copies (.ru.png) and ru.json, the Russian of every string on them. The marks go into
    data/bank/photos.json by question text, which data/build_bank.py merges into the bank."""
    qdir = os.path.join(STYLE, 'questions', level)
    out = os.path.join(ROOT, 'miniapp', 'figs', 'q', level); os.makedirs(out, exist_ok=True)
    ph = os.path.join(ROOT, 'data', 'bank', 'photos.json')
    photos = json.load(open(ph)) if os.path.exists(ph) else {}
    lists = [f for f in sorted(os.listdir(qdir)) if f.endswith('.json') and f[:-5] not in ('questions', 'ru')]
    done, skipped = 0, []
    for f in lists:
        if only and f[:-5] not in only: continue
        for x in json.load(open(os.path.join(qdir, f))):
            d = os.path.join(qdir, x['id']); src = None
            if os.path.exists(os.path.join(d, '3d.jpg')) and os.path.exists(os.path.join(d, '3d.labels.json')):
                if not os.path.exists(os.path.join(d, 'ru.json')): skipped.append((x['id'], 'no ru.json')); continue
                for args in ([], ['--ru']):
                    subprocess.run(['python3', os.path.join(HERE, 'label.py'), *args, os.path.join(d, '3d.jpg')], check=True, capture_output=True)
                src = (os.path.join(d, '3d-labelled.jpg'), os.path.join(d, '3d-labelled.ru.jpg'))
            elif os.path.exists(os.path.join(d, 'q.png')):
                src = (os.path.join(d, 'q.png'), os.path.join(d, 'q.ru.png'))
            if not src: skipped.append((x['id'], 'no image')); continue
            if not os.path.exists(src[1]): skipped.append((x['id'], 'no Russian image')); continue
            webp(src[0], os.path.join(out, f"{x['id']}.webp"), 960); webp(src[1], os.path.join(out, f"{x['id']}.ru.webp"), 960)
            mark = {'photo': f"q/{level}/{x['id']}"}
            if os.path.exists(os.path.join(d, 'plan.png')):
                if not os.path.exists(os.path.join(d, 'plan.ru.png')): skipped.append((x['id'], 'no Russian plan')); continue
                w, h = webp(os.path.join(d, 'plan.png'), os.path.join(out, f"{x['id']}-plan.webp"), 960); mark['plan'] = round(w / h, 3)
                webp(os.path.join(d, 'plan.ru.png'), os.path.join(out, f"{x['id']}-plan.ru.webp"), 960)
            photos[x['q']] = mark; done += 1
    json.dump(photos, open(ph, 'w'), ensure_ascii=False, indent=1)
    print(level, done, 'published,', len(skipped), 'skipped', skipped[:20])

if __name__ == '__main__':
    #   python3 docs/design/blender/publish_q.py vhf-radio-operator            the questions.json way (a few figures)
    #   python3 docs/design/blender/publish_q.py --dirs bareboat-skipper [type ...]   per-question folders
    if sys.argv[1] == '--dirs': publish_dirs(sys.argv[2], sys.argv[3:] or None)
    else:
        for lv in sys.argv[1:]: publish(lv)
