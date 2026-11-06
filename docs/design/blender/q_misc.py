# Shared by the bareboat-skipper question generators q_sail.py, q_buoy.py, q_panel.py and q_compass.py: the
# question lists, the per-question folder, the Russian file, and the yacht without its spinnaker leftovers.
# Each generator runs twice over:
#   python3 docs/design/blender/q_sail.py --id bs-004                 writes <id>/plan.json and <id>/ru.json only
#   blender --background --factory-startup --python docs/design/blender/q_sail.py -- --id bs-004 [--samples 128]
#                                                                      the same, then renders <id>/3d.jpg + 3d.labels.json
# and --all (system Python) writes the metadata for every question of the type.
import os, sys, json, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
QDIR = os.path.join(HERE, '..', 'figure-style', 'questions', 'bareboat-skipper')
FACES = os.path.join(tempfile.gettempdir(), 'iyt-q-faces')          # textures drawn for one render, not kept

try:
    import bpy  # noqa: F401
    IN_BLENDER = True
except ImportError:
    IN_BLENDER = False

def argv():
    return sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]

def arg(name, default):
    a = argv()
    return type(default)(a[a.index(name) + 1]) if name in a else default

def flag(name):
    return name in argv()

def items(kind):
    return json.load(open(os.path.join(QDIR, f'{kind}.json')))

def item(kind, qid):
    for x in items(kind):
        if x['id'] == qid: return x
    raise SystemExit(f'{qid}: not in {kind}.json')

def folder(qid):
    d = os.path.join(QDIR, qid); os.makedirs(d, exist_ok=True); return d

def out_jpg(qid):
    return os.path.join(folder(qid), '3d.jpg')

def save(qid, name, obj):
    with open(os.path.join(folder(qid), name), 'w') as f: json.dump(obj, f, ensure_ascii=False, indent=1)

def drop(qid, name):
    p = os.path.join(folder(qid), name)
    if os.path.exists(p): os.remove(p)

def plan_strings(A):
    """Every printed string of a plan spec: title, key lines, pills, mark and boat labels, tags."""
    out = []
    def walk(v, k=''):
        if isinstance(v, str):
            if k in ('title', 'text', 'label', 'tag') or k == 'key': out.append(v)
        elif isinstance(v, list): [walk(x, k) for x in v]
        elif isinstance(v, dict): [walk(x, kk) for kk, x in v.items()]
    walk(A); return out

def write_ru(qid, english, ru):
    """ru.json beside the render: the Russian of every English string printed on 3d.jpg and plan.png."""
    miss = [s for s in english if s not in ru]
    if miss: raise SystemExit(f'{qid}: no Russian for {miss}')
    save(qid, 'ru.json', {s: ru[s] for s in dict.fromkeys(english)})

def no_spinnaker(K):
    """kit.load_yacht, minus the spinnaker's pale triangle and tack line the model keeps when the spinnaker is
    down (the same local fix as art_colregs_a.py)."""
    if getattr(K.load_yacht, '_q_fixed', False): return
    _load = K.load_yacht
    def _yacht(*a, **k):
        yt = _load(*a, **k)
        for o in yt.objs:
            anc, q = [], o.parent
            while q: anc.append(q.name); q = q.parent
            if o.type == 'MESH' and (any(n.startswith('SPINNAKER') for n in anc) or
                                     any(sl.material and sl.material.name.startswith(('[Color_F12]', '[Color_H09]')) for sl in o.material_slots)):
                o.hide_render = True
        return yt
    _yacht._q_fixed = True
    K.load_yacht = _yacht

def face(script, kind, *args):
    """Run a Pillow face drawer with the system Python (Blender's has no PIL); returns the PNG path."""
    import subprocess, hashlib
    os.makedirs(FACES, exist_ok=True)
    h = hashlib.md5(('|'.join((kind,) + args)).encode()).hexdigest()[:10]
    out = os.path.join(FACES, f'{os.path.basename(script)[:-3]}-{kind}-{h}.png')
    subprocess.run(['python3', script, '--face', kind, out, *args], check=True)
    return out

def face_args():
    """In face mode (python3 q_x.py --face KIND OUT args...): (kind, out, args)."""
    a = sys.argv[sys.argv.index('--face') + 1:]
    return a[0], a[1], a[2:]
