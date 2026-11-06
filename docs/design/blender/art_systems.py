# Article bareboat-skipper/systems, figures 1-7, as Blender renders.
#   1  key at ON, engine not started: oil and charge lamps lit, RPM 0
#   2  overheating: temperature 110° in the red, alarm lamp lit; inset: the exhaust with only a trickle of water
#   3  fuel: the gauge at 80 L, the instrument showing 4 L/h and 6 kn
#   4  prop walk: going astern in a marina, the stern walks to port
#   5  turning to port close past a moored yacht: the stern swings to starboard
#   6  batteries: the monitor with House 11.8 V (low), Engine 12.7 V, Solar 2 A, and the isolator switches
#   7  water: the tank gauge at 360 L
#   blender --background --factory-startup --python docs/design/blender/art_systems.py -- --fig 1 [--out x.jpg]
import os, sys, math, json, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
from mathutils import Vector
import common as C, kit as K, kit_instruments as KI

HERE = os.path.dirname(os.path.abspath(__file__)); TEX = os.path.join(HERE, 'textures')
OUTDIR = os.path.join(HERE, '..', 'figure-style', 'articles', 'bareboat-skipper', 'systems')
arg = C.cli(); FIG = arg('--fig', 1); SAMPLES = arg('--samples', 192); SCALE = arg('--scale', 100)
OUT = arg('--out', os.path.join(OUTDIR, f'{FIG}-3d.jpg')); INSET = arg('--inset', 0)

_load = K.load_yacht
def _yacht(*a, **k):
    """kit.load_yacht, minus the spinnaker's pale triangle and tack line the model keeps when the spinnaker is down."""
    yt = _load(*a, **k)
    for o in yt.objs:
        anc, q = [], o.parent
        while q: anc.append(q.name); q = q.parent
        if o.type == 'MESH' and (any(n.startswith('SPINNAKER') for n in anc) or
                                 any(sl.material and sl.material.name.startswith(('[Color_F12]', '[Color_H09]')) for sl in o.material_slots)):
            o.hide_render = True
    return yt
K.load_yacht = _yacht

def face(kind, *args):
    os.makedirs(TEX, exist_ok=True)
    out = os.path.join(TEX, 'sys-' + kind + ('-' + '-'.join(a.replace('|', '_').replace(' ', '').replace('/', '')[:40] for a in args) if args else '') + '.png')
    subprocess.run(['python3', os.path.join(HERE, 'art_systems_faces.py'), kind, out, *args], check=True)
    return out

def rect(name, w, h, path, loc, emit=0.0, rough=0.4):
    """A flat image facing -Y, w x h metres, centred at loc."""
    me = bpy.data.meshes.new(name); x, z = w / 2, h / 2
    me.from_pydata([(-x, 0, -z), (x, 0, -z), (x, 0, z), (-x, 0, z)], [], [(0, 1, 2, 3)])
    me.uv_layers.new(name='UVMap').data.foreach_set('uv', [0, 0, 1, 0, 1, 1, 0, 1])
    return C.obj(name, me, KI.image_mat(name, path, rough, emit), Vector(loc))

def lamp(x, z, color, lit):
    rgb = {'red': (1.0, 0.08, 0.05), 'amber': (1.0, 0.55, 0.05), 'green': (0.1, 1.0, 0.2)}[color]
    m, nt, b, out = C.new_mat('lamp-%s-%d' % (color, lit))
    C.setin(b, 'Base Color', rgb + (1,)) if not lit else None
    if lit:
        em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = rgb + (1,); em.inputs['Strength'].default_value = 1.3
        nt.links.new(em.outputs[0], out.inputs['Surface'])
    else:
        C.setin(b, 'Base Color', tuple(c * 0.25 for c in rgb) + (1,)); C.setin(b, 'Roughness', 0.15); C.setin(b, 'Coat Weight', 1.0)
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=12, radius=0.0075)
    for v in bm.verts: v.co.y = min(v.co.y, 0.0) * 0.8
    me = bpy.data.meshes.new('lamp'); bm.to_mesh(me); bm.free(); me.shade_smooth()
    C.obj('lamp', me, m, Vector((x, -0.0012, z)))
    if lit:
        ld = bpy.data.lights.new('lampglow', 'POINT'); ld.energy = 0.08; ld.color = rgb; ld.shadow_soft_size = 0.005
        lo = bpy.data.objects.new('lampglow', ld); C.col.objects.link(lo); lo.location = (x, -0.015, z)

def panel_base(plate_kind, w=0.34, h=0.15):
    M = K.mats()
    KI.wall('cockpit-side', -0.6, 0.6, -0.4, 0.35, 0.012, M['hull'])
    C.obj('panel', C.rbox('panel', (w + 0.012, 0.012, h + 0.012), 0.006, 3), M['dark'], (0.0, 0.006, 0.0))
    rect('plate', w, h, face('plate', plate_kind), (0, -0.0004, 0), 0.0, 0.5)

def px(x, y, w=0.34, h=0.15): return ((x / 2040 - 0.5) * w, (0.5 - y / 900) * h)

def key_switch(on):
    M = K.mats(); x, z = px(1250, 700)
    C.obj('key', KI._cyl_y(0.014, 0.01), M['chrome'], (x, -0.005, z))
    kb = C.obj('key-bit', C.rbox('kb', (0.006, 0.02, 0.022), 0.002, 2), M['dark'], (x, -0.016, z))
    if on: kb.rotation_euler = (0, math.radians(90), 0)
    for i, (xx, col) in enumerate(((1520, '#2a8a3a'), (1740, '#b3261e'))):
        bx, bz = px(xx, 700); C.obj('button', KI._cyl_y(0.009, 0.008), C.simple('btn%d' % i, col, 0.4, coat=0.5), (bx, -0.004, bz))

def panel_camera():
    K.day_sky(sun_az=200, sun_el=35, strength=0.18)
    K.camera((0.03, -0.47, 0.11), (0.0, 0, 0.0), 45)

labels, arrows, note, expo, extra = [], [], None, -0.6, {}
C.reset()

if FIG in (1, 2):
    panel_base('engine')
    lit = {'OIL': FIG == 1, 'CHARGE': FIG == 1, 'TEMP': FIG == 2}
    for xx, name in ((180, 'OIL'), (360, 'CHARGE'), (540, 'TEMP')):
        x, z = px(xx, 740); lamp(x, z, 'red' if name != 'CHARGE' else 'amber', lit[name])
    KI.gauge(KI.face_png('tach', '2312.1'), (-0.09, -0.001, 0.02), 0.048, value_angle=-135)
    t = 20 if FIG == 1 else 110
    KI.gauge(face('temp'), (0.045, -0.001, 0.03), 0.032, value_angle=-60 + max(0, t - 40) / 80 * 120)
    v = 12.3 if FIG == 1 else 14.1
    KI.gauge(KI.face_png('volts'), (0.12, -0.001, 0.03), 0.032, value_angle=-60 + (v - 8) / 8 * 120)
    key_switch(True)
    panel_camera()
    if FIG == 1:
        labels = [(((px(180, 740)[0] + px(360, 740)[0]) / 2, 0, px(180, 740)[1] + 0.012), 'oil + charge lamps ON', 'red'),
                  ((-0.09, 0, 0.07), 'RPM 0'), ((px(1250, 700)[0], 0, px(1250, 700)[1] + 0.014), 'key at ON', 'blue')]
        note = 'Key at ON, engine not yet started · buzzer sounding: normal'
    else:
        labels = [((0.045, 0, 0.066), 'Temp 110°', 'red'), (px(540, 740)[0:1] + (0, px(540, 740)[1] + 0.012), 'alarm', 'red'), ((0.12, 0, 0.066), 'Volts 14.1')]
        note = 'Alarm sounding · stop the engine, check the raw-water intake'
elif FIG == 3:
    panel_base('engine')
    for xx in (180, 360, 540):
        x, z = px(xx, 740); lamp(x, z, 'red', False)
    KI.gauge(KI.face_png('tach', '2312.1'), (-0.09, -0.001, 0.02), 0.048, value_angle=-135 + 2.2 * 67.5)
    KI.gauge(face('litres', '100'), (0.045, -0.001, 0.03), 0.032, value_angle=-60 + 0.8 * 120)
    key_switch(True)
    # a multifunction instrument beside it on the bulkhead: speed and fuel flow
    M = K.mats()
    C.obj('mfd', C.rbox('mfd', (0.11, 0.014, 0.11), 0.008, 3), M['dark'], (0.27, 0.0, 0.01))
    rect('mfd-screen', 0.09, 0.075, face('lcd', '540', '450', 'SOG 6.0 kn|FUEL|4.0 L/h'), (0.27, -0.0075, 0.018), 1.2, 0.3)
    panel_camera(); K.camera((0.08, -0.66, 0.11), (0.065, 0, 0.0), 45)
    labels = [((0.045, 0, 0.066), 'Fuel 80 L'), ((0.27, 0, 0.07), 'Speed 6 kn · burn 4 L/h', 'blue')]
    note = 'Reserve 20 L: 60 ÷ 4 = 15 h · 15 h × 6 kn = 90 miles'
elif FIG == 6:
    panel_base('power')
    for xx, txt in ((330, 'HOUSE|11.8 V@red'), (1020, 'ENGINE|12.7 V'), (1710, 'SOLAR|2.0 A')):
        x, z = px(xx, 430); rect('lcd', 0.085, 0.06, face('lcd', '480', '340', txt), (x, -0.0008, z), 1.2, 0.3)
    # battery isolators below the panel: red rotary switches on the bulkhead, house ON, engine OFF (isolated)
    M = K.mats(); red = C.simple('isolator', '#c4161c', 0.35, coat=0.6)
    for i, (x, on) in enumerate(((-0.08, True), (0.08, False))):
        C.obj('iso-base', KI._cyl_y(0.03, 0.012), red, (x, -0.004, -0.15))
        kn = C.obj('iso-knob', C.rbox('kn', (0.012, 0.03, 0.05), 0.004, 2), red, (x, -0.022, -0.15))
        kn.rotation_euler = (0, math.radians(0 if on else 90), 0)
    panel_camera(); K.camera((0.0, -0.55, 0.06), (0.0, 0, -0.035), 38)
    labels = [(px(330, 400)[0:1] + (0, 0.05), 'House 11.8 V: flat', 'red'), (px(1020, 400)[0:1] + (0, 0.05), 'Engine 12.7 V'), (px(1710, 400)[0:1] + (0, 0.05), 'Solar 2 A'),
              ((-0.08, 0, -0.11), 'house ON'), ((0.08, 0, -0.11), 'engine isolated', 'blue')]
    note = 'Fridge and anchor light ran all night · the engine battery was isolated: she starts'
elif FIG == 7:
    panel_base('water')
    KI.gauge(face('litres', '400'), (px(1020, 420)[0], -0.001, px(1020, 420)[1]), 0.045, value_angle=-60 + 0.9 * 120)
    panel_camera()
    labels = [((px(1020, 420)[0], 0, px(1020, 420)[1] + 0.06), 'Tanks 360 L'), ((0.13, 0, 0.0), '6 crew × 20 L = 120 L a day', 'blue')]
    note = '360 ÷ 120 = 3 days of water'
elif FIG == 22:
    # inset for fig 2: the exhaust outlet on the topsides, only a trickle of water dribbling out
    M = K.mats()
    KI.wall('topsides', -1.2, 1.2, -0.3, 0.9, 0.0, M['hull'])
    KI.wall('boot', -1.2, 1.2, -0.3, 0.05, -0.002, M['boot'])
    C.obj('exh-flange', KI._cyl_y(0.045, 0.012), M['chrome'], (0.0, -0.006, 0.32))
    C.obj('exh-hole', KI._cyl_y(0.03, 0.014), C.simple('hole', '#050505', 0.9), (0.0, -0.008, 0.32))
    water = C.simple('trickle', '#d8e6ea', 0.05); bw = water.node_tree.nodes['Principled BSDF'] if 'Principled BSDF' in water.node_tree.nodes else None
    pts = [Vector((0.0, -0.016, 0.30)), Vector((0.0, -0.03, 0.27)), Vector((0.002, -0.034, 0.18)), Vector((0.003, -0.036, 0.06)), Vector((0.004, -0.037, 0.0))]
    C.tube('trickle', C.catmull_centripetal(pts, 12), 0.004, 10, 1.0, water)
    K.sea('calm', size=8.0, repeat=6, center=(0, -2)); K.day_sky(sun_az=200, sun_el=35)
    K.camera((0.25, -1.1, 0.42), (0.0, 0, 0.22), 50)
    expo = -0.6
else:
    # 4 and 5: drone views in a marina
    K.sea('calm', size=30.0, repeat=10); K.day_sky(sun_az=210, sun_el=45)
    pl = K.mats()['planks']
    def pontoon(x0, x1, y, w=2.2):
        C.tbox((abs(x1 - x0), 0.5, w), ((x0 + x1) / 2, 0.25, -y), pl, 0.05, 2, 'pontoon')
    def moored(x, y, hdg, name):
        return K.load_yacht(name=name).place(x, y, heading=hdg)
    if FIG == 4:
        # reversing into a berth between two yachts lying stern-to the pontoon behind her
        pontoon(-40, 40, -24); [moored(x, -15.0, 0, 'm%d' % i) for i, x in enumerate((-12, 12))]
        you = K.load_yacht(name='you').place(0, -3, heading=0)
        stern = you.world((-3.6, 0.13, K.WL)); stern.z = 0.3
        w = K.wake(you, 7, 2.6, 1.6); mw = w.matrix_world.copy(); w.parent = None
        w.location = you.world((-4.6, 3.7, K.WL)); w.location.z = 0.25; w.rotation_euler = (0, 0, math.radians(-90))   # wash streaming forward up her port side
        K.camera((5, -30, 44), (0, -9, 0), 34)
        arrows = [(tuple(you.world((-1, 0.13, 7))), tuple(you.world((-9, 0.13, 7))), 'blue'), (tuple(stern + Vector((0, 0, 2.5))), tuple(stern + Vector((-6, 0, 2.5))), 'red')]
        labels = [(tuple(you.world((-5, 0.13, 9))), 'engine astern', 'blue'), (tuple(stern + Vector((-6, 0, 4.5))), 'stern walks to port', 'red')]
        note = 'Engine astern, rudder centred: the stern walks to port'
    else:
        # turning to port out of a berth, a yacht moored alongside the pontoon on her starboard side
        C.tbox((2.2, 0.5, 34), (13.6, 0.25, 0), pl, 0.05, 2, 'pontoon')
        moored(10.2, 0.0, 0, 'moored')
        you = K.load_yacht(name='you').place(0.5, -1.5, heading=315); K.wake(you, 12, 4, 0.8)
        stern = you.world((-3.8, 0.13, K.WL))
        K.camera((9, -18, 46), (5, 0, 0), 34)
        arrows = [(tuple(you.world((12, 0.13, 6))), tuple(you.world((19, 4, 6))), 'yellow'), (tuple(stern + Vector((0, 0, 3))), tuple(stern + Vector((4.5, -1.0, 3))), 'red')]
        labels = [(tuple(you.world((12, 0.13, 7))), 'turning to port', 'blue'), (tuple(stern + Vector((5, -1.5, 5))), 'stern swings to starboard', 'red'),
                  ((10.2, 0.0, 19.0), 'Moored')]
        note = 'Turn to port: your stern swings to starboard, towards her'
    expo = -0.7

C.render(OUT, SAMPLES, SCALE, expo, labels, note, space='blender', arrows=arrows)

if FIG == 2 and not INSET:
    # the exhaust inset: rendered in a second Blender run, pasted into the corner with its own label
    ins = os.path.splitext(OUT)[0] + '-inset.jpg'
    subprocess.run([bpy.app.binary_path, '--background', '--factory-startup', '--python', os.path.abspath(__file__), '--',
                    '--fig', '22', '--out', ins, '--samples', str(SAMPLES), '--inset', '1'], check=True)
    subprocess.run(['python3', os.path.join(HERE, 'art_systems_faces.py'), 'inset', OUT, ins], check=True)
