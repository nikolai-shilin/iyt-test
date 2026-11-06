# Shared parts for the Charter Check-in system figures (art_checkin_electrics.py, _engine, _plumbing, _return; textures from art_checkin_sys_tex.py), on top
# of common.py, kit.py and kit_instruments.py: drawn textures in the article's tex/ folder, the engine panel of
# art_systems.py (lamps, gauges, key), switch-panel lamps, interior light, small fittings. Blender space, Z up, metres;
# a bulkhead is the plane y = 0 facing -Y (towards the camera).
import os, sys, math, subprocess
import bpy, bmesh
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
import common as C, kit as K, kit_instruments as KI

HERE = os.path.dirname(os.path.abspath(__file__))
ARTS = os.path.join(HERE, '..', 'figure-style', 'articles', 'charter-checkin')
deg = math.radians

def outdir(article): return os.path.join(ARTS, article)

_TEXD = [None]
def use_article(article):
    _TEXD[0] = os.path.join(outdir(article), 'tex'); os.makedirs(_TEXD[0], exist_ok=True)

def _name(kind, args):
    s = '-'.join(a.replace('|', '_').replace(' ', '').replace('/', '').replace('@', '')[:40] for a in args)
    return os.path.join(_TEXD[0], kind + ('-' + s if s else '') + '.png')

def tex(kind, *args):
    """A texture from art_checkin_sys_tex.py (system Python)."""
    out = _name(kind, args); subprocess.run(['python3', os.path.join(HERE, 'art_checkin_sys_tex.py'), kind, out, *args], check=True); return out

def sysface(kind, *args):
    """A face from art_systems_faces.py: temp | litres FULL | lcd W H TEXT | plate engine|power|water."""
    out = _name('sys-' + kind, args); subprocess.run(['python3', os.path.join(HERE, 'art_systems_faces.py'), kind, out, *args], check=True); return out

def face(kind, *args):
    """A gauge face from make_faces.py: tach HOURS | volts | fuel."""
    out = _name('mf-' + kind, args); subprocess.run(['python3', os.path.join(HERE, 'make_faces.py'), kind, out, *args], check=True); return out

# ---------------------------------------------------------------- yacht without the spinnaker's leftovers
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
K.load_yacht = _yacht

# ---------------------------------------------------------------- flat images, lamps
def quad(name, w, h, path, loc, emit=0.0, rough=0.4, normal='-Y', rot=None):
    """A flat image w x h metres centred at loc, facing -Y (on a bulkhead) or +Z (lying on a table)."""
    me = bpy.data.meshes.new(name); x, z = w / 2, h / 2
    pts = [(-x, 0, -z), (x, 0, -z), (x, 0, z), (-x, 0, z)] if normal == '-Y' else [(-x, -z, 0), (x, -z, 0), (x, z, 0), (-x, z, 0)]
    me.from_pydata(pts, [], [(0, 1, 2, 3)])
    me.uv_layers.new(name='UVMap').data.foreach_set('uv', [0, 0, 1, 0, 1, 1, 0, 1])
    o = C.obj(name, me, KI.image_mat(name, path, rough, emit), Vector(loc))
    if rot: o.rotation_euler = rot
    return o

def emit_mat(name, rgb, strength):
    m, nt, b, out = C.new_mat(name)
    em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = tuple(rgb) + (1,); em.inputs['Strength'].default_value = strength
    nt.links.new(em.outputs[0], out.inputs['Surface']); return m

RGB = {'red': (1.0, 0.08, 0.05), 'amber': (1.0, 0.55, 0.05), 'green': (0.1, 1.0, 0.2)}
def lamp(x, z, color, lit, y=0.0, r=0.0075, glow=0.08):
    """A warning lamp on a panel facing -Y (art_systems.py): lit glows, unlit is a dark coloured lens."""
    rgb = RGB[color]
    if lit: m = emit_mat('lamp-%s-on' % color, rgb, 1.3)
    else: m = C.simple('lamp-%s-off' % color, '#%02x%02x%02x' % tuple(int(c * 255 * 0.25) for c in rgb), 0.15, coat=1.0)
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=12, radius=r)
    for v in bm.verts: v.co.y = min(v.co.y, 0.0) * 0.8
    me = bpy.data.meshes.new('lamp'); bm.to_mesh(me); bm.free(); me.shade_smooth()
    C.obj('lamp', me, m, Vector((x, y - 0.0012, z)))
    if lit:
        ld = bpy.data.lights.new('lampglow', 'POINT'); ld.energy = glow; ld.color = rgb; ld.shadow_soft_size = 0.005
        lo = bpy.data.objects.new('lampglow', ld); C.col.objects.link(lo); lo.location = (x, y - 0.015, z)

# ---------------------------------------------------------------- the engine panel (art_systems.py layout)
PW, PH = 0.34, 0.15
def px(x, y, at=(0.0, 0.0)): return (at[0] + (x / 2040 - 0.5) * PW, at[1] + (0.5 - y / 900) * PH)

def panel_box(plate_png, at=(0.0, 0.0), w=PW, h=PH, y=0.0):
    M = K.mats()
    C.obj('panel', C.rbox('panel', (w + 0.012, 0.012, h + 0.012), 0.006, 3), M['dark'], (at[0], y + 0.006, at[1]))
    quad('plate', w, h, plate_png, (at[0], y - 0.0004, at[1]), 0.0, 0.5)

def engine_panel(at=(0.0, 0.0), rpm=0, hours='2312.1', right='temp', temp=80, volts=12.6, fuel=1.0, lit=(), key=True, stop_out=False, plate='engine'):
    """The engine panel: tachometer with hour counter, a second gauge (temp | volts | fuel) and volts, the OIL, CHARGE
    and TEMP lamps, key, START and STOP buttons. Returns the gauge centres {'tach','g2','g3'} as (x, z)."""
    M = K.mats(); ax, az = at
    panel_box(sysface('plate', 'engine'), at)
    for xx, name in ((180, 'OIL'), (360, 'CHARGE'), (540, 'TEMP')):
        x, z = px(xx, 740, at); lamp(x, z, 'amber' if name == 'CHARGE' else 'red', name in lit)
    KI.gauge(face('tach', hours), (ax - 0.09, -0.001, az + 0.02), 0.048, value_angle=-135 + rpm / 1000 * 67.5)
    g2 = (ax + 0.045, az + 0.03); g3 = (ax + 0.12, az + 0.03)
    if right == 'temp': KI.gauge(sysface('temp'), (g2[0], -0.001, g2[1]), 0.032, value_angle=-60 + max(0, min(125, temp) - 40) / 80 * 120)
    elif right == 'fuel': KI.gauge(face('fuel'), (g2[0], -0.001, g2[1]), 0.032, value_angle=-60 + fuel * 120)
    KI.gauge(face('volts'), (g3[0], -0.001, g3[1]), 0.032, value_angle=-60 + (volts - 8) / 8 * 120)
    x, z = px(1250, 700, at)
    C.obj('key', KI._cyl_y(0.014, 0.01), M['chrome'], (x, -0.005, z))
    if key:
        kb = C.obj('key-bit', C.rbox('kb', (0.006, 0.02, 0.022), 0.002, 2), M['dark'], (x, -0.016, z)); kb.rotation_euler = (0, deg(90), 0)
    for i, (xx, col) in enumerate(((1520, '#2a8a3a'), (1740, '#b3261e'))):
        bx, bz = px(xx, 700, at); C.obj('button', KI._cyl_y(0.009, 0.008), C.simple('btn%d' % i, col, 0.4, coat=0.5), (bx, -0.004, bz))
    return {'tach': (ax - 0.09, az + 0.02), 'g2': g2, 'g3': g3, 'key': px(1250, 700, at), 'oil': px(180, 740, at), 'charge': px(360, 740, at), 'temp': px(540, 740, at)}

# ---------------------------------------------------------------- light, camera, frame helpers
def interior_light(key=7, fill=2, at=(0.0, 0.0, 0.04), sky=0.08):
    """Daylight through a porthole and the companionway onto a bulkhead (art_vhf_misc.nav_light)."""
    K.day_sky(sun_az=150, sun_el=40, strength=sky)
    KI.area_light((at[0] + 0.5, -0.9, at[2] + 0.5), at, key, 0.6)
    KI.area_light((at[0] - 0.6, -0.8, at[2] + 0.26), at, fill, 1.0, (0.85, 0.9, 1.0))

def to_px(p):
    bpy.context.view_layer.update()
    q = world_to_camera_view(bpy.context.scene, bpy.context.scene.camera, Vector(p)); return Vector((q.x * C.W, (1 - q.y) * C.H))

def shift_px(p, dx, dy):
    """`p` moved by (dx, dy) pixels in the frame (dy down), at the same depth from the camera."""
    bpy.context.view_layer.update()
    m = bpy.context.scene.camera.matrix_world.to_3x3(); right, up = m @ Vector((1, 0, 0)), m @ Vector((0, 1, 0))
    p = Vector(p); a = to_px(p); kx = (to_px(p + right * 0.01) - a).length / 0.01; ky = (to_px(p + up * 0.01) - a).length / 0.01
    return p + right * (dx / kx) - up * (dy / ky)

def frame_setup():
    r = bpy.context.scene.render; r.resolution_x, r.resolution_y, r.resolution_percentage = C.W, C.H, 100

def hose(name, pts, r, mat, per=10):
    return C.tube(name, C.catmull_centripetal([Vector(p) for p in pts], per), r, 16, 1.0, mat)

def clip(at, axis, r, mat):
    """A stainless worm-drive hose clip round a hose of radius r at `at`, the hose along `axis` (a Vector)."""
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=False, segments=32, radius1=r * 1.08, radius2=r * 1.08, depth=0.009)
    me = bpy.data.meshes.new('clip'); bm.to_mesh(me); bm.free(); me.shade_smooth()
    o = C.obj('clip', me, mat, Vector(at)); o.rotation_euler = Vector(axis).to_track_quat('Z', 'Y').to_euler()
    sq = C.obj('clip-screw', C.rbox('cs', (0.012, 0.008, 0.009), 0.002, 1), mat, Vector(at))
    sq.rotation_euler = o.rotation_euler.copy(); bpy.context.view_layer.update()
    sq.location = Vector(at) + (o.matrix_world.to_3x3() @ Vector((0, r * 1.15, 0)))
    return o

def sphere(name, r, mat, loc, seg=32):
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=seg // 2, radius=r)
    for f in bm.faces: f.smooth = True
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    return C.obj(name, me, mat, Vector(loc))

def box(name, dims, loc, mat, r=0.0, seg=2):
    return C.obj(name, C.rbox(name, dims, r, seg), mat, Vector(loc))

def frp_mat(name='frp', color='#dcd8cc'):
    """Bare grey-white glassfibre of a bilge or locker: a little rough, faintly mottled."""
    m, nt, b, _ = C.new_mat(name)
    n = C.noise(nt, C.obj_coords(nt), 30.0, 4.0)
    c = C.ramp(nt, [(0.35, color), (0.7, '#c9c4b6')]); C.link(nt, n, c.inputs['Fac'])
    C.link(nt, c.outputs['Color'], b.inputs['Base Color']); C.setin(b, 'Roughness', 0.55)
    C.bump_from(nt, b, n, 0.08, 0.001)
    return m

def hit(origin, direction):
    """The first surface a ray from `origin` along `direction` meets (world space), or None."""
    bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()
    ok, loc, nrm, *_ = bpy.context.scene.ray_cast(dg, Vector(origin), Vector(direction).normalized())
    return (loc, nrm) if ok else (None, None)

def clone_yacht(yt, name='clone'):
    """Another yacht sharing the first one's meshes and materials (a glTF import of the Sun Odyssey takes ~40 s):
    the root empty and every object under it copied, linked data, the same hierarchy. Returns a kit.Yacht."""
    mp = {}
    def walk(o, parent):
        n = o.copy(); C.col.objects.link(n); n.parent = parent; mp[o] = n
        for ch in o.children: walk(ch, n)
    walk(yt.root, None); mp[yt.root].name = name
    return K.Yacht(mp[yt.root], [mp.get(o, o) for o in yt.objs], mp.get(yt.boom_pivot))
