# Shared parts for the Charter Check-in renders of art_checkin_nav.py, art_checkin_papers.py, art_checkin_safety.py
# ("nps"), on top of common.py, kit.py, kit_instruments.py and the props of q_encounter_props.py: textures from
# art_checkin_nps_tex.py in the article's tex/ folder, the Raymarine Axiom with a drawn screen (as art_vhf_scenes.py),
# image planes, screen-space nudges for label anchors. Blender space, Z up, metres, sea at z = 0.
import os, sys, math, json, subprocess
import bpy, bmesh
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
import common as C, kit as K, kit_instruments as KI

HERE = os.path.dirname(os.path.abspath(__file__))
ARTS = os.path.join(HERE, '..', 'figure-style', 'articles', 'charter-checkin')
deg = math.radians

def outdir(article): return os.path.join(ARTS, article)

def tex(article, name, ext='.png'):
    """tex/<name>.png of the article, drawn by art_checkin_nps_tex.py if missing (or with --retex)."""
    d = os.path.join(outdir(article), 'tex'); p = os.path.join(d, name + ext)
    if not os.path.exists(p) or '--retex' in sys.argv:
        subprocess.run(['python3', os.path.join(HERE, 'art_checkin_nps_tex.py'), d, name], check=True)
    return p

def anchors(article, name):
    return json.load(open(os.path.join(outdir(article), 'tex', name + '.json')))

# ---------- the yacht without the spinnaker leftovers ----------
def yacht(name='yacht', sails=None, boom=None):
    yt = K.load_yacht(name=name, sails=sails, boom=boom)
    for o in yt.objs:
        anc, q = [], o.parent
        while q: anc.append(q.name); q = q.parent
        if o.type == 'MESH' and (any(n.startswith('SPINNAKER') for n in anc) or
                                 any(sl.material and sl.material.name.startswith(('[Color_F12]', '[Color_H09]')) for sl in o.material_slots)):
            o.hide_render = True
    return yt

# ---------- simple meshes ----------
def quad(name, w, h, path, loc, rot=(0, 0, 0), emit=0.0, rough=0.4, mat=None):
    """An image w x h metres lying in the XY plane (facing +Z), centred at loc, then rotated by rot (radians)."""
    me = bpy.data.meshes.new(name); x, y = w / 2, h / 2
    me.from_pydata([(-x, -y, 0), (x, -y, 0), (x, y, 0), (-x, y, 0)], [], [(0, 1, 2, 3)])
    me.uv_layers.new(name='UVMap').data.foreach_set('uv', [0, 0, 1, 0, 1, 1, 0, 1])
    o = C.obj(name, me, mat or KI.image_mat(name, path, rough, emit), Vector(loc)); o.rotation_euler = rot
    return o

def sheet(name, w, h, path, loc, rotz=0.0, rough=0.85, curl=0.0):
    """A sheet of paper lying on a table (z up), w x h, turned rotz degrees, its edges lifted `curl` m."""
    nu, nv = 12, 16; bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap'); V = []
    for j in range(nv + 1):
        for i in range(nu + 1):
            u, v = i / nu, j / nv; z = curl * ((2 * u - 1) ** 4 + 0.6 * (2 * v - 1) ** 4)
            V.append(bm.verts.new(((u - 0.5) * w, (v - 0.5) * h, z)))
    for j in range(nv):
        for i in range(nu):
            a = j * (nu + 1) + i; fc = bm.faces.new((V[a], V[a + 1], V[a + nu + 2], V[a + nu + 1])); fc.smooth = True
            for lp, (ii, jj) in zip(fc.loops, ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))): lp[uvl].uv = (ii / nu, jj / nv)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = C.obj(name, me, KI.image_mat(name, path, rough), Vector(loc)); o.rotation_euler = (0, 0, deg(rotz))
    return o

def on_sheet(o, u, v, dz=0.002):
    """World point at (u, v) of a sheet/quad (0..1 across its image, v up), a little above it."""
    bpy.context.view_layer.update(); me = o.data
    xs = [p.co.x for p in me.vertices]; ys = [p.co.y for p in me.vertices]
    loc = Vector((min(xs) + (max(xs) - min(xs)) * u, min(ys) + (max(ys) - min(ys)) * v, dz))
    return o.matrix_world @ loc

def sphere(name, r, mat, loc, seg=24, scale=(1, 1, 1)):
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=seg // 2, radius=r)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); me.shade_smooth()
    o = C.obj(name, me, mat, Vector(loc)); o.scale = scale
    return o

def rod(name, a, b, r1, r2, mat, seg=24):
    a, b = Vector(a), Vector(b); L = (b - a).length
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r1, radius2=r2, depth=L)
    for fc in bm.faces: fc.smooth = True
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = C.obj(name, me, mat, (a + b) / 2)
    o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = (b - a).normalized().to_track_quat('Z', 'Y')
    return o

def torus(name, R, r, mat, loc, rot=(0, 0, 0), seg=48):
    o = C.obj(name, KI._torus(R, r), mat, Vector(loc)); o.rotation_euler = rot; return o

def emit_mat(name, rgb, strength):
    m, nt, b, out = C.new_mat(name)
    em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = tuple(rgb) + (1,); em.inputs['Strength'].default_value = strength
    nt.links.new(em.outputs[0], out.inputs['Surface']); return m

def glow_mat(name, color, strength=2.0):
    m, nt, b, out = C.new_mat(name)
    C.setin(b, 'Base Color', C.lin(color)); C.setin(b, 'Roughness', 0.6)
    C.setin(b, 'Emission Color', C.lin(color)); C.setin(b, 'Emission Strength', strength)
    return m

def strip(name, a, b, w, mat, z=0.35):
    """A flat band on the water from a to b (x, y), w wide, at height z."""
    a, b = Vector((a[0], a[1], 0)), Vector((b[0], b[1], 0)); d = (b - a); n = Vector((-d.y, d.x, 0)).normalized() * w / 2
    me = bpy.data.meshes.new(name); me.from_pydata([tuple(a + n), tuple(b + n), tuple(b - n), tuple(a - n)], [], [(0, 1, 2, 3)])
    o = C.obj(name, me, mat, (0, 0, z)); o.visible_shadow = False
    return o

def ring(name, at, R, mat, z=0.4, k=0.09):
    o = C.obj(name, KI._torus(R, R * k), mat, (at[0], at[1], z)); o.visible_shadow = False
    return o

def T3(v):
    """Blender point -> Three.js point for common.braid / three_strand."""
    return C.V3((v.x, v.z, -v.y))

def line(name, pts, R=0.007, base='#e9e6dc', fleck='#1f3f78'):
    C.braid(name, [T3(Vector(p)) for p in pts], R, base, fleck, False, None, None, 1.4)

def sag(a, b, n=10, s=0.15):
    a, b = Vector(a), Vector(b)
    return [a.lerp(b, i / n) - Vector((0, 0, s * math.sin(math.pi * i / n))) for i in range(n + 1)]

# ---------- the Raymarine Axiom with a drawn screen (art_vhf_scenes.plotter, the screen texture given) ----------
def plotter(png, at, tilt=-14.0, width=0.235, rotz=0.0, emit=0.7, pod=True):
    """The Axiom, `width` m wide, its bottom centre at `at`, tilted back `tilt` degrees, turned rotz about Z; its
    screen shows the whole-front texture `png` (art_checkin_nps_tex.front). Returns (objs, screen object)."""
    M = K.mats()
    root, objs = K.load_model('chartplotter-raymarine-axiom.glb', drop_planes=False)
    bpy.context.view_layer.update(); lo, hi = K.bbox([o for o in objs if o.type == 'MESH'])
    k = width / (hi.x - lo.x); root.scale = (k,) * 3; bpy.context.view_layer.update(); lo, hi = K.bbox([o for o in objs if o.type == 'MESH'])
    at = Vector(at)
    root.location = (root.location.x - (lo.x + hi.x) / 2 + at.x, root.location.y - (lo.y + hi.y) / 2 + at.y, root.location.z - lo.z + at.z)
    piv = bpy.data.objects.new('plotter-pivot', None); C.col.objects.link(piv); piv.location = at
    bpy.context.view_layer.update(); mw = root.matrix_world.copy(); root.parent = piv; root.matrix_world = mw
    piv.rotation_euler = (deg(tilt), 0, deg(rotz))
    img = bpy.data.images.load(png); screen = None
    for o in objs:
        for sl in getattr(o, 'material_slots', []):
            if sl.material and sl.material.name.startswith('raymarine--displays'):
                mm, mnt, mb, _ = C.new_mat('axiom-screen')
                uv = mnt.nodes.new('ShaderNodeUVMap'); tx = mnt.nodes.new('ShaderNodeTexImage'); tx.image = img; tx.interpolation = 'Cubic'
                mnt.links.new(uv.outputs['UV'], tx.inputs['Vector']); mb.inputs['Base Color'].default_value = (0.01, 0.01, 0.012, 1)
                mnt.links.new(tx.outputs['Color'], mb.inputs['Emission Color']); mb.inputs['Emission Strength'].default_value = emit
                mb.inputs['Roughness'].default_value = 0.35; mb.inputs['Coat Weight'].default_value = 0.5; mb.inputs['Specular IOR Level'].default_value = 0.2
                sl.material = mm; screen = o
    if pod: C.obj('pod', C.rbox('pod', (width * 1.28, 0.14, 0.12), 0.035, 4), M['dark'], tuple(at - Vector((0, 0, 0.07))))
    bpy.context.view_layer.update()
    return objs, screen

def uv_to_world(o, u, v, mat_prefix='axiom-screen'):
    me = o.data; me.calc_loop_triangles(); uvl = me.uv_layers.active.data; q = Vector((u, v))
    idx = {i for i, sl in enumerate(o.material_slots) if sl.material and sl.material.name.startswith(mat_prefix)}; hits = []
    for t in me.loop_triangles:
        if t.material_index not in idx: continue
        a, b, c = (Vector(uvl[l].uv) for l in t.loops)
        v0, v1, v2 = b - a, c - a, q - a
        d00, d01, d11, d20, d21 = v0.dot(v0), v0.dot(v1), v1.dot(v1), v2.dot(v0), v2.dot(v1)
        den = d00 * d11 - d01 * d01
        if abs(den) < 1e-12: continue
        w1 = (d11 * d20 - d01 * d21) / den; w2 = (d00 * d21 - d01 * d20) / den; w0 = 1 - w1 - w2
        if min(w0, w1, w2) >= -1e-4:
            P = [me.vertices[i].co for i in t.vertices]
            hits.append(o.matrix_world @ (P[0] * w0 + P[1] * w1 + P[2] * w2))
    if not hits: return None
    cam = bpy.context.scene.camera
    return min(hits, key=lambda h: (h - cam.matrix_world.translation).length) if cam else hits[0]

def screen_point(o, fx, fy):
    """World point of pixel (fx, fy) of the 828 x 481 front texture."""
    bpy.context.view_layer.update()
    for n in (0, 1, -1):          # the model's UVs sit one tile up (v 1..2)
        p = uv_to_world(o, fx / 828.0, 1 - fy / 481.0 + n)
        if p is not None: return p
    raise SystemExit(f'screen point {fx} {fy} not found')

# ---------- screen space ----------
def to_px(p):
    bpy.context.view_layer.update(); sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = C.W, C.H, 100
    q = world_to_camera_view(sc, sc.camera, Vector(p)); return Vector((q.x * C.W, (1 - q.y) * C.H))

def shift_px(p, dx, dy):
    """`p` moved by (dx, dy) pixels in the frame (dy down), at the same depth from the camera."""
    bpy.context.view_layer.update()
    m = bpy.context.scene.camera.matrix_world.to_3x3(); right, up = m @ Vector((1, 0, 0)), m @ Vector((0, 1, 0))
    p = Vector(p); a = to_px(p); kx = (to_px(p + right * 0.01) - a).length / 0.01; ky = (to_px(p + up * 0.01) - a).length / 0.01
    return p + right * (dx / kx) - up * (dy / ky)

def drone(c, D, az=180.0, el=37.0, lens=32.0):
    a, e = math.radians(az), math.radians(el)
    eye = Vector(c) + Vector((math.sin(a) * math.cos(e), math.cos(a) * math.cos(e), math.sin(e))) * D
    return K.camera(tuple(eye), tuple(c), lens)

def hdg_vec(h): a = math.radians(h); return Vector((math.sin(a), math.cos(a), 0))

# ---------- navigation lights that keep their colour (q_lights.lamp) ----------
RGB = {'r': (1.0, 0.05, 0.03), 'g': (0.05, 1.0, 0.25), 'w': (1.0, 0.92, 0.75)}
GAIN = {'r': 0.55, 'g': 0.32, 'w': 5.0}     # lens brightness: bright colours turn white under AgX

def lamp(name, p, c, radius, power=30.0, gain=1.0):
    """A glowing lens sized to read in the picture, and a point lamp that lights the hull and the water round it."""
    rgb = RGB[c]
    m, nt, b, out = C.new_mat(name + '-lens')
    em = C.node(nt, 'ShaderNodeEmission'); C.setin(em, 'Color', rgb + (1,)); C.setin(em, 'Strength', GAIN[c] * gain)
    C.link(nt, em.outputs[0], out.inputs['Surface'])
    o = sphere(name, radius, m, p, seg=20); o.visible_shadow = False
    if power > 0:
        ld = bpy.data.lights.new(name, 'POINT'); ld.energy = power; ld.color = rgb; ld.shadow_soft_size = max(0.05, radius * 0.3)
        lo = bpy.data.objects.new(name + '-lamp', ld); C.col.objects.link(lo); lo.location = Vector(p)
    return o
