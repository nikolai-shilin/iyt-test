# Shared by the question generators (bareboat-skipper by default, --level for another) q_sail.py, q_buoy.py, q_panel.py and q_compass.py: the
# question lists, the per-question folder, the Russian file, and the yacht without its spinnaker leftovers.
# Each generator runs twice over:
#   python3 docs/design/blender/q_sail.py --id bs-004                 writes <id>/plan.json and <id>/ru.json only
#   blender --background --factory-startup --python docs/design/blender/q_sail.py -- --id bs-004 [--samples 128]
#                                                                      the same, then renders <id>/3d.jpg + 3d.labels.json
# and --all (system Python) writes the metadata for every question of the type. Add --level charter-checkin (both runs)
# for another level's lists and folders.
import os, sys, json, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
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

# --level <level> (default bareboat-skipper): read questions/<level>/<type>.json, write questions/<level>/<id>/.
# --outdir DIR writes the folders under DIR instead (a test render that leaves the level's own files alone).
LEVEL = arg('--level', 'bareboat-skipper')
QDIR = os.path.join(HERE, '..', 'figure-style', 'questions', LEVEL)
OUTDIR = os.path.abspath(arg('--outdir', QDIR))

def items(kind):
    return json.load(open(os.path.join(QDIR, f'{kind}.json')))

def item(kind, qid):
    for x in items(kind):
        if x['id'] == qid: return x
    raise SystemExit(f'{qid}: not in {kind}.json')

def folder(qid):
    d = os.path.join(OUTDIR, qid); os.makedirs(d, exist_ok=True); return d

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

# ---------- plans drawn as {svg} (the plan-view schematic look of q_chart.mjs: theme tokens, Carlito, pills, a faint
# grid, the title and key band along the bottom). Every text drawn is recorded, so ru.json can cover it. ----------
SW, SH = 1280, 800
RED, GREEN, AMBER = '#e8231a', '#1aa34a', '#e0b400'

class Plan:
    def __init__(self, title, key, ru=None):
        self.title, self.key, self.texts, self.body, self.ru = title, list(key), [], [], ru or {}
        self.band = 50 + 50 * len(self.key) + 34 if (title or key) else 0
        self.ha = SH - self.band                     # height of the drawing area
    @staticmethod
    def _w(s, size):
        cw = lambda c: .23 if c == ' ' else .26 if c in ".,:;'|il·()[]" else .34 if c in 'ftrI' else .78 if c in 'mwMW' \
            else .507 if c.isdigit() else .36 if c == '°' else .6 if c.isupper() else .5
        return sum(cw(c) for c in str(s)) * size
    def text(self, x, y, s, size=34, w=700, fill='var(--ink)', a='middle', halo=True):
        s = str(s); self.texts.append(s)
        h = 'stroke="var(--bg)" stroke-width="9" stroke-linejoin="round" paint-order="stroke"' if halo else ''
        e = s.replace('&', '&amp;').replace('<', '&lt;')
        self.body.append(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" font-weight="{w}" fill="{fill}" text-anchor="{a}" {h}>{e}</text>')
    def pill(self, x, y, s, kind='light', size=30, room=None):
        """kind light | accent | red | ink | green; room: the Russian, so the pill is wide enough for it too."""
        room = room or self.ru.get(s, '')
        w = max(self._w(s, size), self._w(room, size) * 1.04) + size * 1.3; h = size * 1.7
        fill = {'accent': 'var(--accent)', 'red': RED, 'ink': 'var(--ink)', 'green': GREEN}.get(kind, 'var(--bg)')
        ink = 'var(--ink)' if kind == 'light' else 'var(--bg)' if kind == 'ink' else '#fff'
        stroke = 'var(--tag-line)' if kind == 'light' else fill
        self.body.append(f'<rect x="{x - w / 2:.1f}" y="{y - h / 2:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{h / 2:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="3"/>')
        self.text(x, y + size * 0.36, s, size, fill=ink, halo=False)
    def raw(self, s): self.body.append(s)
    def line(self, x1, y1, x2, y2, c='var(--ink)', w=4, dash=None):
        self.body.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{c}" stroke-width="{w}" stroke-linecap="round" {f"stroke-dasharray={chr(34)}{dash}{chr(34)}" if dash else ""}/>')
    def rect(self, x, y, w, h, fill='none', stroke='none', sw=3, rx=0, dash=None, op=1):
        self.body.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" opacity="{op}" {f"stroke-dasharray={chr(34)}{dash}{chr(34)}" if dash else ""}/>')
    def arrow(self, x1, y1, x2, y2, c='var(--ink)', w=6, h=None, dash=None):
        import math
        a = math.atan2(y2 - y1, x2 - x1); h = h or max(18, w * 3.2)
        p1 = (x2 - h * math.cos(a - .5), y2 - h * math.sin(a - .5)); p2 = (x2 - h * math.cos(a + .5), y2 - h * math.sin(a + .5))
        self.line(x1, y1, x2 - h * 0.6 * math.cos(a), y2 - h * 0.6 * math.sin(a), c, w, dash)
        self.body.append(f'<path d="M{x2:.1f} {y2:.1f} L{p1[0]:.1f} {p1[1]:.1f} L{p2[0]:.1f} {p2[1]:.1f} Z" fill="{c}"/>')
    def svg(self):
        s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {SW} {SH}" width="{SW}" height="{SH}" font-family="Carlito, Arial, sans-serif" style="background:var(--bg)">',
             f'<rect width="{SW}" height="{SH}" fill="var(--bg)"/>']
        for gx in range(40, SW, 60): s.append(f'<line x1="{gx}" y1="0" x2="{gx}" y2="{self.ha}" stroke="var(--line)" stroke-width="2"/>')
        for gy in range(40, self.ha, 60): s.append(f'<line x1="0" y1="{gy}" x2="{SW}" y2="{gy}" stroke="var(--line)" stroke-width="2"/>')
        s += self.body
        if self.band:
            s.append(f'<rect x="0" y="{self.ha}" width="{SW}" height="{self.band}" fill="var(--band)"/>')
            b = self.body; self.body = []
            self.text(30, self.ha + 52, self.title, 40, a='start', halo=False)
            for i, l in enumerate(self.key):
                self.text(30, self.ha + 102 + 50 * i, '·', 34, 400, a='start', halo=False); self.texts.pop()
                self.text(48, self.ha + 102 + 50 * i, l, 34, 400, a='start', halo=False)
            s += self.body; self.body = b
        return ''.join(s) + '</svg>'

def ru_number(s):
    """A string of figures only: the Russian decimal comma."""
    import re
    return re.sub(r'(\d)\.(\d)', r'\1,\2', s)
