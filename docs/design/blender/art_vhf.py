# The fixed VHF set (SIMRAD RS20S on a teak bulkhead, handset on its clip) for any "radio" figure, driven by a spec.
# The photographed front panel has "16 HI DISTRESS" baked into its LCD; a freshly drawn LCD (art_vhf_lcd.py, system
# Python + Pillow) is laid over it as a lit panel, so any channel, power and DSC text can be shown.
#
#   blender --background --factory-startup --python docs/design/blender/art_vhf.py -- --article calls --fig 2
#   blender --background --factory-startup --python docs/design/blender/art_vhf.py -- \
#       --spec '{"channel": "70", "power": "LO", "parts": [["display", "DSC only"]], "note": "Channel 70"}' --out /tmp/x.jpg
#
# CLI
#   --article A --fig N   render figure N of docs/design/article-figs/vhf-radio-operator-A.json to
#                         docs/design/figure-style/articles/vhf-radio-operator/A/N-3d.jpg (unless --out is given)
#   --spec JSON           an ad-hoc spec instead (needs --out); keys below
#   --out PATH            output JPEG; <out>.labels.json is written next to it, then run label.py on <out>
#   --samples 192 --scale 100   (labels only line up on full-size renders; drafts: --samples 32 --scale 50)
#
# Spec keys (all optional)
#   channel  "16"            big digits on the LCD; the channel name under it comes from a table (16 DISTRESS, 70 DSC...)
#   name     "DISTRESS"      override the name under the digits ("" for none)
#   power    "HI" | "LO"     the tag at the top of the LCD
#   tags     ["DSC", "INT"]  the outlined tags top right
#   lines    ["DISTRESS ALERT", "MMSI 238123450"]   a text screen instead of big digits (channel shown small)
#   parts    [[key, text], ...] or [[key, text, colour]]: pills anchored to a control. Keys: display, power (the HI/LO
#            tag), channel (channel knob), volume, squelch, onoff, scan, tri, ch16 (the 16/9 key), distress, mic, ptt,
#            handset. Colours: red, blue, green, yellow (label.py).
#   note     "..."           the dark note pill top left
#   cover    "open" | "closed"   the red DISTRESS cover; default open when a distress part says "hold" or "lift"
#   handset  "clip" | "lifted"   lifted: off its clip, held up in front of the set, the coiled cord stretched
#   camera   "front" | "high"    high looks down a little more (default when the cover is open)
# With --article, a figure without parts gets one pill: its power on the HI/LO tag if it is about power, else "channel N"
# on the display; set 6 and phonetic 3 get the handset lifted;
# its note is fig.note, else "name · cap".
import os, sys, json, math, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
from mathutils import Vector, Matrix
import common as C, kit as K, kit_instruments as KI

HERE = os.path.dirname(os.path.abspath(__file__)); DESIGN = os.path.join(HERE, '..')
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
def opt(name, default=None):
    return argv[argv.index(name) + 1] if name in argv else default
SAMPLES = int(opt('--samples', 192)); SCALE = int(opt('--scale', 100))

# ---------- the spec ----------
LIFTED = {('set', 6), ('phonetic', 3)}   # figures about microphone technique: the handset off its clip
if opt('--spec'):
    spec = json.loads(opt('--spec')); OUT = opt('--out', 'vhf.jpg')
else:
    art, n = opt('--article', 'set'), int(opt('--fig', 1))
    data = json.load(open(os.path.join(DESIGN, 'article-figs', f'vhf-radio-operator-{art}.json')))
    f = next(x for x in data['figs'] if x['n'] == n)
    spec = dict(f['fig'])
    if not spec.get('parts'):
        hi = spec.get('power', 'HI') == 'HI'; about = f"{f.get('name') or ''} {f.get('cap') or ''}"
        spec['parts'] = ([['power', '25 W, high' if hi else '1 W, low']] if ' W' in about or 'power' in about
                         else [['display', f"channel {spec.get('channel', '16')}"]])
    if (art, n) in LIFTED: spec.setdefault('handset', 'lifted')
    if not spec.get('note'):
        spec['note'] = ' · '.join(x for x in (f.get('name'), f.get('cap')) if x) or None
    OUT = opt('--out', os.path.join(DESIGN, 'figure-style', 'articles', 'vhf-radio-operator', art, f'{n}-3d.jpg'))
parts = [list(p) for p in spec.get('parts') or []]
dis_text = ' '.join(p[1].lower() for p in parts if p[0] == 'distress')
COVER = spec.get('cover') or ('open' if ('hold' in dis_text or 'lift' in dis_text) else 'closed')
HANDSET = spec.get('handset', 'clip')
CAMERA = spec.get('camera') or ('high' if COVER == 'open' else 'front')

# ---------- the LCD texture ----------
os.makedirs(os.path.dirname(os.path.abspath(OUT)), exist_ok=True)
import tempfile, hashlib
LCD_PNG = os.path.join(tempfile.gettempdir(), 'art_vhf-' + hashlib.md5(os.path.abspath(OUT).encode()).hexdigest()[:10] + '.png')
lcd = {k: spec[k] for k in ('channel', 'power', 'name', 'tags', 'lines') if k in spec}
subprocess.run(['python3', os.path.join(HERE, 'art_vhf_lcd.py'), LCD_PNG, json.dumps(lcd)], check=True)

# ---------- the set on its bulkhead (as fig_instruments.py --kind radio) ----------
C.reset()
root, objs = K.load_model('radio-vhf-simrad-rs20s.glb', drop_planes=False)
for o in objs:   # an untextured plane over the photo front
    if o.type == 'MESH' and all(sl.material is None for sl in o.material_slots) and len(o.data.polygons) <= 4:
        o.hide_render = True
bpy.context.view_layer.update()
KI.wall('bulkhead', -0.42, 0.40, -0.26, 0.30, 0.004, KI.joinery_mat())
seen = set()
for o in objs:
    for sl in getattr(o, 'material_slots', []):
        m = sl.material
        if not m or not m.use_nodes or m.name in seen: continue
        seen.add(m.name)
        b = next((nd for nd in m.node_tree.nodes if nd.type == 'BSDF_PRINCIPLED'), None)
        if b: b.inputs['Roughness'].default_value = 0.62; b.inputs['Specular IOR Level'].default_value = 0.25
front_img = None
for o in objs:
    if o.type == 'MESH' and any(sl.material and sl.material.name == 'Material-7503' for sl in o.material_slots):
        mw = o.matrix_world.copy(); mw.translation.y -= 0.0006; o.matrix_world = mw
        old = next(sl.material for sl in o.material_slots if sl.material and sl.material.name == 'Material-7503')
        front_img = next(nd.image for nd in old.node_tree.nodes if nd.type == 'TEX_IMAGE')
        m, nt, b, out = C.new_mat('vhf-front')
        uvn = C.node(nt, 'ShaderNodeUVMap'); uvn.uv_map = 'UVMap'
        tx = C.node(nt, 'ShaderNodeTexImage'); tx.image = front_img
        C.link(nt, uvn.outputs['UV'], tx.inputs['Vector']); C.link(nt, tx.outputs['Color'], b.inputs['Base Color'])
        C.setin(b, 'Roughness', 0.5)
        if COVER == 'open':   # the panel catches the red glow a little
            C.link(nt, tx.outputs['Color'], b.inputs['Emission Color']); C.setin(b, 'Emission Strength', 0.08)
        for sl in o.material_slots:
            if sl.material and sl.material.name == 'Material-7503': sl.material = m
for mat in bpy.data.materials:
    if mat.name in ('Fig30', '[Color M07]', '[Color_007]1') and mat.use_nodes:
        b = next((nd for nd in mat.node_tree.nodes if nd.type == 'BSDF_PRINCIPLED'), None)
        if b and not b.inputs['Base Color'].is_linked: b.inputs['Base Color'].default_value = (0.018, 0.019, 0.021, 1)

px = lambda u, v: Vector((u / 999 * 0.17, 0.0, (1 - v / 531) * 0.09))   # front photo pixels -> metres

def emit_mat(name, rgb, strength, rough=0.4):
    m, nt, b, out = C.new_mat(name)
    C.setin(b, 'Base Color', (*rgb, 1)); C.setin(b, 'Roughness', rough)
    C.setin(b, 'Emission Color', (*rgb, 1)); C.setin(b, 'Emission Strength', strength)
    return m

# ---------- the new LCD, lit, laid over the photographed one ----------
a, c = px(362, 142), px(625, 352)
me = bpy.data.meshes.new('lcd')
me.from_pydata([(a.x, -0.0012, c.z), (c.x, -0.0012, c.z), (c.x, -0.0012, a.z), (a.x, -0.0012, a.z)], [], [(0, 1, 2, 3)])
me.uv_layers.new(name='UVMap')
for li, uv in zip(me.loops, [(0, 0), (1, 0), (1, 1), (0, 1)]): me.uv_layers['UVMap'].data[li.index].uv = uv
m, nt, b, out = C.new_mat('lcd')
tx = C.node(nt, 'ShaderNodeTexImage'); tx.image = bpy.data.images.load(LCD_PNG); tx.interpolation = 'Cubic'
C.link(nt, tx.outputs['Color'], b.inputs['Base Color']); C.link(nt, tx.outputs['Color'], b.inputs['Emission Color'])
C.setin(b, 'Emission Strength', 0.55); C.setin(b, 'Roughness', 0.18); C.setin(b, 'Specular IOR Level', 0.5)
C.obj('lcd', me, m)

# ---------- the DISTRESS cover ----------
d0, d1 = px(712, 378), px(810, 465); dw, dh = d1.x - d0.x, d0.z - d1.z
if COVER == 'open':
    cov_m, nt, b, out = C.new_mat('cover')
    C.setin(b, 'Base Color', (*C.lin('#d0161c')[:3], 1)); C.setin(b, 'Roughness', 0.15)
    C.setin(b, 'Transmission Weight', 0.55); C.setin(b, 'IOR', 1.49)
    piv = bpy.data.objects.new('cover-hinge', None); C.col.objects.link(piv)
    piv.location = Vector(((d0.x + d1.x) / 2, -0.002, d0.z + 0.001))
    cov = C.obj('cover', C.rbox('cover', (dw * 1.1, 0.008, dh * 1.1), 0.002, 2), cov_m, (0, -0.004, -dh * 0.55))
    cov.parent = piv; piv.rotation_euler = (math.radians(-115), 0, 0)
    C.obj('distress-glow', C.rbox('btn', (dw * 0.8, 0.004, dh * 0.75), 0.0015, 2), emit_mat('distress-glow', (1.0, 0.012, 0.006), 0.22, 0.6),
          ((d0.x + d1.x) / 2, -0.0025, (d0.z + d1.z) / 2))
    ld = bpy.data.lights.new('glow', 'POINT'); ld.energy = 0.25; ld.color = (1.0, 0.15, 0.1); ld.shadow_soft_size = 0.01
    gl = bpy.data.objects.new('glow', ld); C.col.objects.link(gl); gl.location = ((d0.x + d1.x) / 2, -0.02, (d0.z + d1.z) / 2)

# ---------- the handset ----------
HS = ['Node_35', 'Node_92', 'Node_95', 'Node_98', 'Node_101']
hs_objs = [o for o in objs if o.type == 'MESH' and o.parent and (o.parent.name.split('.')[0] in HS or o.parent.name.startswith('Component#1'))]
MIC0, PTT0 = Vector((0.200, -0.053, 0.090)), Vector((0.1785, -0.044, 0.078))   # grille centre, the PTT bar on its left side
hs_xf = Matrix.Identity(4)
if HANDSET == 'lifted':
    # off its clip and held out in front of the set, turned a little to the camera; the handset mesh carries its own
    # cable down to the socket, so that tail is cut off and a coiled cord drawn from the socket to the strain relief
    pivot = Vector((0.20, -0.04, 0.04))
    hs_xf = (Matrix.Translation(Vector((-0.005, -0.075, 0.0)) + pivot) @ Matrix.Rotation(math.radians(-22), 4, 'Z')
             @ Matrix.Rotation(math.radians(10), 4, 'X') @ Matrix.Translation(-pivot))
    for o in hs_objs:
        mw = o.matrix_world.copy()
        if len(o.data.polygons) > 1000:
            bm = bmesh.new(); bm.from_mesh(o.data)
            bmesh.ops.delete(bm, geom=[v for v in bm.verts if (mw @ v.co).z < 0.036], context='VERTS')
            bm.to_mesh(o.data); bm.free()
        o.matrix_world = hs_xf @ mw
    for o in objs:
        if o.type == 'MESH' and o.parent and o.parent.name.split('.')[0] == 'Node_106': o.hide_render = True
    s0 = Vector((0.147, -0.035, 0.012)); s1 = hs_xf @ Vector((0.200, -0.041, 0.036))
    pts = []; N = 420; turns = 30; R = 0.005; sag = Vector((0, 0, -0.035)); axis = s1 - s0
    for i in range(N + 1):
        t = i / N; base = s0.lerp(s1, t) + sag * math.sin(math.pi * t)
        tang = (axis + sag * math.pi * math.cos(math.pi * t)).normalized()
        u = tang.cross(Vector((0, 0, 1))).normalized() if abs(tang.z) < 0.95 else Vector((1, 0, 0)); v = tang.cross(u)
        ang = 2 * math.pi * turns * t; k = min(1.0, t * 14, (1 - t) * 14)
        pts.append(base + (u * math.cos(ang) + v * math.sin(ang)) * R * k)
    C.tube('cord', pts, 0.0016, 10, 0.01, C.simple('cord', '#141517', 0.4))
MIC, PTT = hs_xf @ MIC0, hs_xf @ PTT0

# ---------- light and camera ----------
K.day_sky(sun_az=150, sun_el=40, strength=0.08)
KI.area_light((0.5, -0.9, 0.55), (0.05, 0, 0.04), 7, 0.6)
KI.area_light((-0.6, -0.8, 0.3), (0, 0, 0.04), 2, 1.0, (0.85, 0.9, 1.0))
if HANDSET == 'lifted':
    K.camera((0.15, -0.50, 0.13), (0.12, -0.03, 0.05), 50)
elif len(parts) >= 5 or {'display', 'power'} <= {q[0] for q in parts}:   # crowded: the set bigger in frame, the handset at the right edge
    K.camera((0.15, -0.37, 0.115), (0.112, 0, 0.05), 50)
elif CAMERA == 'high':
    K.camera((0.18, -0.43, 0.16), (0.113, 0, 0.05), 50)
else:
    K.camera((0.16, -0.46, 0.12), (0.113, 0, 0.052), 50)

# ---------- labels ----------
# label.py draws each pill centred above its anchor, so the layout is done here: every control has a few anchor
# points (first is preferred) and each pill takes the one where it overlaps least with the pills already placed,
# the note pill, and the other labelled controls.
cov_top = None
if COVER == 'open':
    bpy.context.view_layer.update(); cov_top = max((cov.matrix_world @ Vector(v.co) for v in cov.data.vertices), key=lambda q: q.z)
A = {'display': [px(530, 146), px(440, 146), px(495, 372), px(400, 366), px(590, 366), px(380, 250), px(610, 250)],   # LCD edges: keep the digits clear
     'power': [px(470, 160), px(470, 172)],
     'channel': [px(125, 150), px(125, 95), px(90, 180)],
     'volume': [px(183, 330), px(183, 372), px(150, 300)],
     'squelch': [px(85, 288), px(150, 360), px(610, 318)],   # the VOL/SQL knob and its legend
     'onoff': [px(122, 432), px(122, 455)], 'scan': [px(378, 432), px(378, 455)], 'tri': [px(492, 432), px(492, 455)],
     'ch16': [px(595, 432), px(598, 462), px(580, 410)],
     'distress': ([cov_top + Vector((0, -0.002, -0.002)), px(760, 420) + Vector((0, -0.004, 0))] if cov_top is not None
                  else [px(760, 420), px(760, 380), px(800, 385), px(760, 455)]),
     'mic': [hs_xf @ q for q in (MIC0, Vector((0.200, -0.053, 0.102)), Vector((0.207, -0.053, 0.080)))],
     'ptt': [hs_xf @ q for q in (PTT0, Vector((0.1785, -0.044, 0.070)), Vector((0.1785, -0.044, 0.084)))],
     'handset': [hs_xf @ q for q in (Vector((0.20, -0.05, 0.05)), Vector((0.20, -0.05, 0.03)))]}
from bpy_extras.object_utils import world_to_camera_view
bpy.context.view_layer.update(); scn = bpy.context.scene
scn.render.resolution_x, scn.render.resolution_y = C.W, C.H
def to_px(p): q = world_to_camera_view(scn, scn.camera, Vector(p)); return q.x * C.W, (1 - q.y) * C.H
def rect(x, y, text):   # the pill label.py will draw for an anchor at (x, y)
    w = 16.5 * len(text) + 34; cx = max(w / 2 + 12, min(C.W - w / 2 - 12, x)); return (cx - w / 2, y - 4 - 70, cx + w / 2, y - 4 - 18)
def overlap(r1, r2): return max(0, min(r1[2], r2[2]) - max(r1[0], r2[0])) * max(0, min(r1[3], r2[3]) - max(r1[1], r2[1]))
note_txt = spec.get('note')
_d0, _d1 = to_px(px(415, 200)), to_px(px(575, 290)); digits = (_d0[0], _d0[1], _d1[0], _d1[1])
placed = [(28, 27, 28 + 15.5 * len(note_txt) + 36, 77)] if note_txt else []
others = {p[0]: to_px(A[p[0]][0]) for p in parts if p[0] in A}
import itertools
use = [p for p in parts if p[0] in A]
for p in parts:
    if p[0] not in A: print('VHF unknown part', p[0])
cands = [[(i, c, rect(*to_px(c), p[1])) for i, c in enumerate(A[p[0]])] for p in use]
def cost_of(combo):
    c = sum(600 * i + 2000 * (r[1] < 0) for i, _, r in combo)
    rs = [r for _, _, r in combo]
    c += sum(3 * overlap(r1, r2) for j, r1 in enumerate(rs) for r2 in rs[j + 1:]) + sum(3 * overlap(r, q) for r in rs for q in placed)
    c += sum(2 * overlap(r, digits) for r in rs)   # nor the channel number
    for (_, _, r), p in zip(combo, use):   # a pill should not hide another labelled control
        c += sum(1500 for k, (ox, oy) in others.items() if k != p[0] and r[0] - 6 < ox < r[2] + 6 and r[1] - 6 < oy < r[3] + 6)
    return c
best = min(itertools.product(*cands), key=cost_of) if use else ()
if os.environ.get("VHF_DEBUG"):
    for combo in sorted(itertools.product(*cands), key=cost_of)[:6]: print("VHF combo", round(cost_of(combo)), [(i, [round(v) for v in r]) for i, _, r in combo], "digits", [round(v) for v in digits])
print('VHF layout cost', round(cost_of(best)) if use else 0)
labels = [(tuple(c), p[1], *(p[2:3])) for (_, c, _), p in zip(best, use)]
C.render(OUT, SAMPLES, SCALE, -0.4, labels, note_txt, space='blender')
