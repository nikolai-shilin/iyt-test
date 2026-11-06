# Shared pieces for the Charter Check-in article figures of ground, hull and sails (art_checkin_ground.py,
# art_checkin_hull.py, art_checkin_sails.py): the yacht without the spinnaker's leftovers, deck hardware built by
# hand (bow roller, windlass, chain with paint marks, cleats, stanchions and lifelines, a furler drum), Blender text
# for printed panels, and run_lib to execute a library script (fig_rail.py, render_scene.py, fig_winch.py) with
# hooks, as q_rope.py does. Blender space, Z up, metres, the sea at z = 0. Import after common, kit, kit_world.
import os, sys, math, json
import bpy, bmesh
from mathutils import Vector, Matrix, Euler
import common as C, kit as K, kit_world as KW

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.join(HERE, '..', 'figure-style', 'articles', 'charter-checkin')
def deg(a): return math.radians(a)
def V(x, y, z): return Vector((x, y, z))

_load = K.load_yacht
def yacht(*a, **k):
    """kit.load_yacht, minus the spinnaker's pale triangle and tack line the model keeps when the spinnaker is down."""
    yt = _load(*a, **k)
    for o in yt.objs:
        anc, q = [], o.parent
        while q: anc.append(q.name); q = q.parent
        if o.type == 'MESH' and (any(n.startswith('SPINNAKER') for n in anc) or
                                 any(sl.material and sl.material.name.startswith(('[Color_F12]', '[Color_H09]')) for sl in o.material_slots)):
            o.hide_render = True
    return yt

def ray(p, d):
    bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()
    hit, loc, nrm, *_ = bpy.context.scene.ray_cast(dg, Vector(p), Vector(d).normalized())
    return (loc, nrm) if hit else (None, None)

def deck_z(x, y, top=30.0):
    loc, _ = ray((x, y, top), (0, 0, -1))
    return loc.z if loc else None

# ---------- materials ----------
def steel(): return C.simple('stainless', '#d4d7da', 0.18, 1.0)
def dull_steel(): return C.simple('stainless-dull', '#b9bdc1', 0.35, 1.0)
def black(): return C.simple('black-plastic', '#151618', 0.5)
def paint(color, name=None): return C.simple(name or ('paint-' + color), color, 0.55)

def emit_mat(name, color, strength=1.0):
    m, nt, b, out = C.new_mat(name)
    em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = C.lin(color); em.inputs['Strength'].default_value = strength
    nt.links.new(em.outputs[0], out.inputs['Surface']); return m

# ---------- simple shapes ----------
def box(name, dims, loc, mat, r=0.0, rot=(0, 0, 0)):
    o = C.obj(name, C.rbox(name, dims, r, 3 if r else 1), mat, Vector(loc)); o.rotation_euler = rot; return o

def cyl_between(name, a, b, r, mat, seg=24, r2=None):
    a, b = Vector(a), Vector(b); d = b - a
    o = C.cyl(name, r, r if r2 is None else r2, d.length, seg, mat, (a + b) / 2)
    o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = d.to_track_quat('Z', 'Y'); return o

def sphere(name, r, mat, loc, seg=32):
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=seg // 2, radius=r)
    for f in bm.faces: f.smooth = True
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); return C.obj(name, me, mat, Vector(loc))

def torus(name, R, r, mat, loc, rot=(0, 0, 0), seg=48):
    bm = bmesh.new(); ring = 12; vs = []
    for i in range(seg):
        a = i / seg * math.tau; row = []
        for j in range(ring):
            b = j / ring * math.tau
            row.append(bm.verts.new(((R + r * math.cos(b)) * math.cos(a), (R + r * math.cos(b)) * math.sin(a), r * math.sin(b))))
        vs.append(row)
    for i in range(seg):
        for j in range(ring):
            bm.faces.new((vs[i][j], vs[(i + 1) % seg][j], vs[(i + 1) % seg][(j + 1) % ring], vs[i][(j + 1) % ring])).smooth = True
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = C.obj(name, me, mat, Vector(loc)); o.rotation_euler = rot; return o

def tube(name, pts, r, mat, radial=12, caps=False):
    P = C.catmull_centripetal([Vector(p) for p in pts], 12)
    return C.tube(name, P, r, radial, 1.0, mat, caps=caps)

def line3(name, pts, R=0.007, lay=0.05, whip=None):
    """A laid three-strand line along Blender points."""
    C.three_strand(name, [C.V3((p[0], p[2], -p[1])) for p in pts], R, lay, whip=whip)

def braid3(name, pts, R, base, fleck, shiny=False, whip=None, fine=1.2):
    C.braid(name, [C.V3((p[0], p[2], -p[1])) for p in pts], R, base, fleck, shiny, whip, None, fine)

def catenary(a, b, sag, n=16):
    a, b = Vector(a), Vector(b)
    return [a.lerp(b, i / n) - Vector((0, 0, sag * math.sin(math.pi * i / n))) for i in range(n + 1)]

# ---------- text ----------
FONT = '/System/Library/Fonts/Supplemental/Arial Bold.ttf'
def text(body, loc, size, mat, rot=(deg(90), 0, 0), align='CENTER', depth=0.0, name='txt'):
    """Blender text, standing up facing -Y by default."""
    cu = bpy.data.curves.new(name, 'FONT'); cu.body = body; cu.size = size; cu.align_x = align; cu.align_y = 'CENTER'
    cu.extrude = depth
    try: cu.font = bpy.data.fonts.load(FONT, check_existing=True)
    except Exception: pass
    o = bpy.data.objects.new(name, cu); C.col.objects.link(o); o.location = Vector(loc); o.rotation_euler = rot
    cu.materials.append(mat); return o

# ---------- chain with paint marks ----------
def chain_marked(points, marks=(), link_len=0.2, wire=0.028, mark_len=0.75, colors=None):
    """KW.chain along points, with painted lengths: marks = arc lengths (m from the start) where a mark is painted;
    colors: one hex per mark. Returns the total length."""
    P = [Vector(p) for p in points]
    acc = [0.0]
    for a, b in zip(P, P[1:]): acc.append(acc[-1] + (b - a).length)
    def at(s):
        for j in range(len(acc) - 1):
            if acc[j + 1] >= s:
                t = (s - acc[j]) / max(1e-9, acc[j + 1] - acc[j]); return P[j].lerp(P[j + 1], t)
        return P[-1]
    def piece(s0, s1):
        out = [at(s0)] + [P[j] for j in range(len(P)) if s0 < acc[j] < s1] + [at(s1)]
        return out
    cuts = sorted((m, i) for i, m in enumerate(marks)); s = 0.0
    for m, i in cuts:
        if m - mark_len / 2 > s: KW.chain(piece(s, m - mark_len / 2), link_len, wire, 'chain')
        me = KW.chain(piece(m - mark_len / 2, m + mark_len / 2), link_len, wire, 'chain-mark')
        me.materials[0] = C.simple('chain-paint-%d' % i, (colors or ['#e8231a'] * 9)[i], 0.45, 0.2)
        s = m + mark_len / 2
    if s < acc[-1]: KW.chain(piece(s, acc[-1]), link_len, wire, 'chain')
    return acc[-1]

# ---------- running a library script with hooks (as q_rope.run_lib) ----------
_orig = dict(render=C.render, load_exported=C.load_exported, kcam=K.camera, lookat=C.camera_lookat, cammat=C.camera_matrix)

def run_lib(script, argv, out, samples, scale, labels_fn, note, rope_fn=None, pre_render=None, cammat=None, exposure=None, extra=None, arrows_fn=None):
    """Execute a library script as it is. rope_fn(g, i, P) re-routes exported ropes before the script's own
    re-routing; pre_render(g) hides or adds parts; labels_fn(g) -> [(blender point, text[, colour])];
    cammat (eye, look, fov) in Three.js space replaces an exported camera."""
    g = {'__name__': '__main__', '__file__': os.path.join(HERE, script)}
    sys.argv = ['blender', '--'] + [str(a) for a in argv]
    def render(o, s=256, sc=100, exp=-0.6, labels=(), nt=None, blend='', space='three', arrows=(), ex=None):
        if pre_render: pre_render(g)
        _orig['render'](out, samples, scale, exp if exposure is None else exposure, labels_fn(g), note, '', 'blender',
                        arrows_fn(g) if arrows_fn else (), extra)
    C.render = render
    if rope_fn:
        def load_exported(path, rope_fn_inner=None, **kw):
            if 'rope_fn' in kw: rope_fn_inner = kw['rope_fn']
            f = (lambda i, P: rope_fn_inner(i, rope_fn(g, i, P))) if rope_fn_inner else (lambda i, P: rope_fn(g, i, P))
            return _orig['load_exported'](path, rope_fn=f)
        C.load_exported = load_exported
    if cammat:
        C.camera_matrix = lambda m16, fov_y: _orig['lookat'](cammat[0], cammat[1], cammat[2])
    path = os.path.join(HERE, script)
    try:
        exec(compile(open(path).read(), path, 'exec'), g)
    finally:
        C.render, C.load_exported, C.camera_matrix = _orig['render'], _orig['load_exported'], _orig['cammat']
    return g

def out_path(article, fig, given=''):
    return given or os.path.join(ART, article, f'{fig}-3d.jpg')

def write_plans(article, plans):
    """plans: {n: spec}; writes <n>-plan.json into the article folder (system Python, no Blender needed)."""
    d = os.path.join(ART, article)
    for n, spec in plans.items():
        with open(os.path.join(d, f'{n}-plan.json'), 'w') as f: json.dump(spec, f, ensure_ascii=False, indent=1)
    print('plans', article, sorted(plans))
