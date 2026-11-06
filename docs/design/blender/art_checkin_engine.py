# Article charter-checkin/engine, figures 1-7, as Blender renders (art_checkin_sys_kit.py for the shared parts).
#   1  card: the engine bay, steps off, engine cold: dipstick, coolant bottle, belt, raw-water seacock and strainer,
#      fuel filter bowl, the dry tray under it
#   2  just started: 900 rpm, temperature 40°, the oil lamp still lit
#   3  card: it cranks but will not fire: the stop handle left pulled out beside the panel
#   4  day one in flat water: 2200 rpm, the instrument showing 6.0 kn, temperature 80°
#   5  card: the fuel gauge full (160 L), the instrument showing a burn of 4 L/h at cruising revs
#   6  the panel at check-in: hour counter 2312.1, fuel full, 12.6 V; the check-in form beside it says 2 290
#   7  overheating: 2200 rpm, temperature 105° in the red, TEMP lamp lit; inset: steam at the exhaust
#   blender --background --factory-startup --python docs/design/blender/art_checkin_engine.py -- --fig 1 [--samples 160]
import os, sys, math, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
from mathutils import Vector
import common as C, kit as K, kit_instruments as KI
import art_checkin_sys_kit as A

arg = C.cli(); FIG = arg('--fig', 1); SAMPLES = arg('--samples', 160); SCALE = arg('--scale', 100); INSET = arg('--inset', 0)
OUT = arg('--out', os.path.join(A.outdir('engine'), f'{FIG}-3d.jpg'))
A.use_article('engine'); deg = math.radians

labels, arrows, note, expo, extra = [], [], None, -0.6, {}
C.reset(); A.frame_setup(); M = K.mats()

def panel_scene(cam=((0.03, -0.52, 0.13), (0.0, 0, 0.026), 45), wall=(-0.6, 0.8)):
    KI.wall('cockpit-side', wall[0], wall[1], -0.4, 0.35, 0.012, M['hull'])
    K.day_sky(sun_az=200, sun_el=35, strength=0.18)
    K.camera(*cam)

def mfd(x, z, text):
    C.obj('mfd', C.rbox('mfd', (0.11, 0.014, 0.11), 0.008, 3), M['dark'], (x, 0.0, z))
    A.quad('mfd-screen', 0.09, 0.075, A.sysface('lcd', '540', '450', text), (x, -0.0075, z + 0.008), 1.2, 0.3)

if FIG == 1:
    # the bay: the engine on its beds over a tray, the hull sides sloping in, the companionway steps lifted away.
    # The camera stands in the saloon looking aft at the engine's front: belt and pulleys towards us.
    frp = A.frp_mat('bay', '#cfcabd'); paint = C.simple('engine-paint', '#56606a', 0.42, 0.25, coat=0.3)
    darkp = C.simple('engine-dark', '#24272b', 0.5, 0.3); alu = M['alu']
    KI.wall('bay-floor', -0.6, 0.6, -0.6, 0.6, 0.0, frp).data.vertices.foreach_set('co', [-0.6, -0.8, 0, 0.6, -0.8, 0, 0.6, 0.7, 0, -0.6, 0.7, 0])
    for s in (-1, 1):   # hull sides sloping out, a bulkhead at the back
        me = bpy.data.meshes.new('side'); me.from_pydata([(s * 0.55, -0.8, 0.0), (s * 0.55, 0.7, 0.0), (s * 0.78, 0.7, 0.78), (s * 0.78, -0.8, 0.78)], [], [(0, 1, 2, 3)])
        C.obj('side', me, frp)
    KI.wall('back', -0.8, 0.8, 0.0, 0.8, 0.62, frp)
    # the cabin sole round the opening, the companionway bulkhead above the back of the bay
    sole = KI.joinery_mat('sole-wood')
    A.box('sole-front', (3.0, 1.0, 0.03), (0, -1.25, 0.785), sole); A.box('sole-l', (0.9, 1.5, 0.03), (-1.06, -0.05, 0.785), sole); A.box('sole-r', (0.9, 1.5, 0.03), (1.06, -0.05, 0.785), sole)
    A.box('sole-edge', (1.24, 0.03, 0.05), (0, -0.75, 0.77), sole, 0.004)
    KI.wall('companionway', -1.6, 1.6, 0.75, 2.0, 0.66, KI.joinery_mat('bulk-wood'))
    tray = C.simple('tray', '#2a2b2d', 0.6)
    A.box('tray', (0.78, 0.82, 0.012), (0, 0.15, 0.006), tray, 0.004)
    for s in (-1, 1): A.box('tray-lip', (0.012, 0.82, 0.06), (s * 0.39, 0.15, 0.03), tray, 0.003)
    A.box('tray-lip-f', (0.78, 0.012, 0.06), (0, -0.26, 0.03), tray, 0.003)
    for s in (-1, 1): A.box('bed', (0.07, 0.78, 0.14), (s * 0.26, 0.15, 0.08), frp, 0.01)
    # the engine: block, head, rocker cover, sump, a heat exchanger on top, gearbox / saildrive behind
    A.box('sump', (0.36, 0.48, 0.10), (0, 0.18, 0.21), darkp, 0.02)
    A.box('block', (0.42, 0.52, 0.26), (0, 0.18, 0.39), paint, 0.025)
    A.box('head', (0.38, 0.50, 0.10), (0, 0.18, 0.57), paint, 0.02)
    A.box('rocker', (0.26, 0.44, 0.07), (0.03, 0.18, 0.655), C.simple('rocker', '#8f1d1d', 0.35, 0.2, coat=0.6), 0.025)
    C.cyl('hx', 0.055, 0.055, 0.44, 32, paint, (-0.16, 0.18, 0.66), (deg(90), 0, 0))
    A.box('bell', (0.30, 0.16, 0.30), (0, 0.50, 0.32), paint, 0.04)
    for s in (-1, 1): A.box('mount', (0.08, 0.10, 0.06), (s * 0.26, -0.02, 0.18), darkp, 0.01)
    # front: crank pulley, water-pump pulley, alternator, the belt round them
    yF = -0.085
    pul = [((0.0, 0.25), 0.075), ((-0.02, 0.50), 0.05), ((0.17, 0.52), 0.042)]
    for (x, z), r in pul:
        C.obj('pulley', KI._cyl_y(r, 0.03), M['satin'], (x, yF, z)); C.obj('hub', KI._cyl_y(r * 0.35, 0.04), darkp, (x, yF - 0.004, z))
    C.obj('alternator', KI._cyl_y(0.075, 0.13), alu, (0.17, yF + 0.085, 0.52))
    # the belt: round the outside of the three pulleys, seen from the middle of them
    cx, cz = 0.05, 0.42
    pts = []
    for i in range(48):
        a = 2 * math.pi * i / 48
        d = Vector((math.cos(a), math.sin(a)))
        best = max(pul, key=lambda pr: (Vector(pr[0]) - Vector((cx, cz))).dot(d) + pr[1])
        (x, z), r = best
        q = Vector((x, z)) + d * (r + 0.006)
        pts.append(Vector((q.x, yF - 0.002, q.y)))
    pts.append(pts[0])
    C.tube('belt', pts, 0.0075, 8, 0.05, C.simple('belt', '#141414', 0.75))
    # the exhaust: a cast mixing elbow off the head on the left, a wet exhaust hose away aft; the wiring loom
    rust = C.simple('elbow', '#3b302a', 0.7, 0.4)
    A.hose('elbow', [(-0.19, 0.34, 0.56), (-0.27, 0.34, 0.6), (-0.33, 0.36, 0.52), (-0.34, 0.42, 0.40)], 0.035, rust)
    A.hose('exhaust-hose', [(-0.34, 0.42, 0.40), (-0.36, 0.55, 0.30), (-0.38, 0.75, 0.28)], 0.04, C.simple('hose-black2', '#18191b', 0.6))
    A.hose('loom', [(0.21, 0.45, 0.30), (0.215, 0.25, 0.33), (0.215, 0.05, 0.36), (0.18, -0.05, 0.47), (0.17, 0.0, 0.55)], 0.009, C.simple('loom', '#0e0e0f', 0.55))
    # dipstick: the yellow loop on the side of the block, near us
    dy = C.simple('dipstick-yellow', '#f1b80d', 0.4, coat=0.5)
    C.cyl('dip-tube', 0.006, 0.006, 0.3, 12, M['satin'], (0.225, 0.02, 0.42), (0, deg(8), 0))
    bpy.ops.mesh.primitive_torus_add(major_radius=0.022, minor_radius=0.006, location=(0.245, 0.02, 0.6), rotation=(deg(90), 0, 0))
    ring = bpy.context.active_object; ring.data.materials.append(dy); [setattr(p, 'use_smooth', True) for p in ring.data.polygons]
    dip = Vector((0.245, 0.02, 0.62))
    # coolant: a translucent expansion bottle on the back bulkhead at the left, green coolant half way
    bott = C.simple('bottle', '#e8e6dc', 0.35); bb = bott.node_tree.nodes['Principled BSDF']
    bb.inputs['Transmission Weight'].default_value = 0.55
    C.cyl('bottle', 0.05, 0.05, 0.16, 32, bott, (-0.44, 0.30, 0.62))
    C.cyl('coolant', 0.046, 0.046, 0.075, 32, C.simple('coolant', '#2fae4a', 0.2), (-0.44, 0.30, 0.58))
    C.cyl('bottle-cap', 0.022, 0.022, 0.025, 24, C.simple('cap-black', '#151515', 0.5), (-0.44, 0.30, 0.712))
    for zz, t in ((0.66, 'MAX'), (0.565, 'MIN')): C.cyl('mark', 0.0505, 0.0505, 0.003, 32, C.simple('mark', '#111111', 0.5), (-0.44, 0.30, zz))
    A.hose('coolant-hose', [(-0.44, 0.30, 0.54), (-0.34, 0.3, 0.58), (-0.2, 0.25, 0.68)], 0.007, M['rubber'])
    cool = Vector((-0.44, 0.28, 0.72))
    # raw water: a bronze seacock on the hull bottom at the right, lever along the pipe (open), hose up to the strainer
    bronze = C.simple('bronze', '#a7773f', 0.35, 1.0)
    sx = 0.45
    C.cyl('thruhull', 0.035, 0.04, 0.03, 24, bronze, (sx, -0.25, 0.015))
    C.cyl('seacock', 0.03, 0.03, 0.09, 24, bronze, (sx, -0.25, 0.075)); A.sphere('ball', 0.04, bronze, (sx, -0.25, 0.09))
    lev = A.box('lever', (0.016, 0.02, 0.14), (sx, -0.25, 0.155), C.simple('lever-red', '#b8191c', 0.4, coat=0.5), 0.005)   # upright: along the pipe = open
    A.hose('raw-hose', [(sx, -0.25, 0.14), (sx + 0.02, -0.24, 0.22), (sx + 0.06, -0.12, 0.30), (0.52, -0.02, 0.36)], 0.018, C.simple('hose-black', '#1a1b1d', 0.6))
    for zz in (0.16, 0.185): A.clip((sx + 0.004, -0.249, zz), (0, 0, 1), 0.018, M['satin'])
    # the strainer: a clear bowl on the hull side, lid on top, a hose on to the engine
    gl = KI.glass_mat('bowl-glass')
    C.cyl('strainer-bowl', 0.05, 0.05, 0.12, 32, gl, (0.55, 0.05, 0.42))
    C.cyl('strainer-basket', 0.04, 0.04, 0.10, 24, C.simple('basket', '#c9cdd1', 0.4, 1.0), (0.55, 0.05, 0.42))
    C.cyl('strainer-lid', 0.06, 0.06, 0.03, 32, bronze, (0.55, 0.05, 0.495)); C.cyl('strainer-base', 0.055, 0.055, 0.03, 32, bronze, (0.55, 0.05, 0.345))
    A.hose('raw-hose2', [(0.55, 0.05, 0.33), (0.5, 0.02, 0.28), (0.3, -0.04, 0.30), (0.2, -0.06, 0.38)], 0.018, C.simple('hose-black', '#1a1b1d', 0.6))
    strainer = Vector((0.55, 0.05, 0.52))
    # the fuel filter: a separator with a clear bowl on the bulkhead at the left, clear fuel in it
    C.obj('ff-bracket', C.rbox('ffb', (0.10, 0.02, 0.10), 0.005, 2), alu, (-0.46, 0.0, 0.40))
    C.cyl('ff-head', 0.045, 0.045, 0.04, 32, alu, (-0.46, -0.05, 0.42)); C.cyl('ff-element', 0.042, 0.042, 0.10, 32, C.simple('ff-white', '#e6e2d6', 0.5), (-0.46, -0.05, 0.35))
    C.cyl('ff-bowl', 0.04, 0.035, 0.06, 32, gl, (-0.46, -0.05, 0.27)); C.cyl('ff-fuel', 0.036, 0.032, 0.05, 32, C.simple('diesel', '#d9c06a', 0.1), (-0.46, -0.05, 0.268))
    C.cyl('ff-drain', 0.008, 0.008, 0.02, 12, C.simple('drain-red', '#c4161c', 0.4), (-0.46, -0.05, 0.235))
    A.hose('fuel-hose', [(-0.46, -0.05, 0.44), (-0.40, -0.06, 0.50), (-0.25, -0.05, 0.47), (-0.2, 0.0, 0.44)], 0.007, C.simple('fuel-hose', '#111111', 0.6))
    ff = Vector((-0.46, -0.05, 0.27))
    # torch light from above and behind the camera, warm, plus daylight through the companionway
    K.day_sky(sun_az=150, sun_el=40, strength=0.06)
    KI.area_light((0.15, -0.1, 1.6), (0, 0.15, 0.35), 26, 0.5); KI.area_light((-0.4, 0.1, 1.5), (0, 0.2, 0.3), 8, 0.8, (0.85, 0.9, 1.0))
    sp = bpy.data.lights.new('torch', 'SPOT'); sp.energy = 22; sp.spot_size = deg(36); sp.spot_blend = 0.6; sp.color = (1.0, 0.93, 0.82); sp.shadow_soft_size = 0.02
    so = bpy.data.objects.new('torch', sp); C.col.objects.link(so); so.location = (0.25, -0.45, 1.5)
    so.rotation_euler = (Vector((0.05, 0.1, 0.35)) - so.location).to_track_quat('-Z', 'Y').to_euler()
    KI.wall('bay-front', -0.8, 0.8, 0.0, 0.78, -0.8, frp)
    K.camera((0.02, -1.2, 1.6), (0.0, 0.14, 0.36), 31)
    belt_p = Vector((0.12, yF, 0.39))
    labels = [(dip + Vector((0, 0, 0.03)), 'oil: between the marks'),
              (cool + Vector((0, 0, 0.02)), 'coolant: MIN–MAX'),
              (belt_p, 'belt: 10 mm of give', 'blue'),
              (strainer + Vector((0, 0, 0.01)), 'strainer clear'),
              (Vector((sx, -0.25, 0.23)), 'seacock open', 'blue'),
              (ff + Vector((0, 0, -0.045)), 'filter bowl: clear fuel'),
              (Vector((-0.2, -0.2, 0.02)), 'tray dry')]
    note = 'Engine cold, steps off, a torch: before anyone starts it'; expo = -0.5

elif FIG in (2, 4, 7):
    rpm, temp, lit = {2: (900, 40, ('OIL',)), 4: (2200, 80, ()), 7: (2200, 105, ('TEMP',))}[FIG]
    g = A.engine_panel(rpm=rpm, right='temp', temp=temp, volts=14.1 if FIG != 2 else 13.2, lit=lit)
    T = lambda k, dz=0.052: Vector((g[k][0], 0, g[k][1] + dz))
    if FIG == 4:
        mfd(0.27, 0.01, 'SOG|6.0 kn')
        panel_scene(((0.08, -0.66, 0.11), (0.065, 0, 0.0), 45))
        labels = [(T('tach'), '2200 rpm'), (T('g2', 0.036), 'Temp 80°'), (Vector((0.27, 0, 0.068)), '6.0 kn in flat water', 'blue')]
        note = 'Day one, flat water: note revs and speed'
        extra = {'lines': ['Later, same revs, less speed: a fouled propeller']}
    else:
        panel_scene()
        if FIG == 2:
            labels = [(T('tach'), 'RPM 900: running'), (T('oil', 0.012), 'oil lamp still on', 'red'), (T('g2', 0.036), 'Temp 40°')]
            note = 'Oil alarm still on 15 s after the start: stop'
            extra = {'lines': ['Lamps and buzzer at key-on: only a lamp test']}
        else:
            labels = [(T('g2', 0.036), 'Temp 105°', 'red'), (T('temp', 0.012), 'alarm', 'red'), (T('tach'), '2200 rpm')]
            note = 'Buzzer, steam at the exhaust · throttle back, neutral, stop'
            extra = {'lines': ['Let it cool, then strainer, impeller, belt']}

elif FIG == 3:
    g = A.engine_panel(rpm=0, right='temp', temp=20, volts=12.3, lit=('OIL', 'CHARGE'))
    # the stop handle: a T-handle on the cockpit side to the right of the panel, pulled out on its cable
    hx, hz = 0.27, -0.02
    C.obj('stop-boss', KI._cyl_y(0.018, 0.02), M['satin'], (hx, -0.006, hz))
    C.cyl('stop-cable', 0.004, 0.004, 0.11, 12, M['satin'], (hx, -0.07, hz), (deg(90), 0, 0))
    th = C.obj('stop-T', C.rbox('T', (0.07, 0.016, 0.018), 0.006, 3), C.simple('stop-black', '#141416', 0.45), (hx, -0.13, hz))
    A.quad('stop-label', 0.05, 0.016, A.tex('sticker', 'STOP'), (hx, -0.0005, hz + 0.035), 0.0, 0.6)
    panel_scene(((0.28, -0.78, 0.22), (0.09, -0.03, 0.03), 42))
    labels = [(Vector((hx, -0.13, hz + 0.02)), 'stop handle left out: push it in', 'red'),
              (Vector((g['key'][0], 0, g['key'][1] + 0.014)), 'key on: lamps lit')]
    note = 'It cranks but will not fire'
    extra = {'lines': ['Many tries: close the raw-water seacock', 'Half a turn, then solid: stop, call the base']}

elif FIG == 5:
    g = A.engine_panel(rpm=2200, right='fuel', fuel=1.0, volts=14.1, lit=())
    mfd(0.27, 0.01, 'FUEL|4.0 L/h')
    panel_scene(((0.08, -0.66, 0.11), (0.065, 0, 0.0), 45))
    labels = [(Vector((g['g2'][0], 0, g['g2'][1] + 0.036)), 'Fuel: full, 160 L'), (Vector((0.27, 0, 0.068)), '4 L/h at 2200 rpm', 'blue')]
    note = 'Keep 20 L: 140 ÷ 4 = 35 h of motoring'
    extra = {'lines': ['Plan 6 h × 6 days = 36 h: a fuel stop midweek']}

elif FIG == 6:
    g = A.engine_panel(rpm=0, right='fuel', fuel=1.0, volts=12.6, lit=(), key=False)
    # the check-in form on a clipboard, propped on the cockpit seat in front of the panel
    board = A.box('clipboard', (0.16, 0.004, 0.22), (0.25, -0.13, -0.08), C.simple('board', '#6b4a2a', 0.6), 0.004); board.rotation_euler = (deg(-28), 0, deg(-8))
    pg = A.quad('form', 0.148, 0.2095, A.tex('form', 'checkin'), (0.25, -0.133, -0.088), 0.0, 0.8, rot=(deg(-28), 0, deg(-8)))
    bpy.context.view_layer.update(); pg.location += pg.matrix_world.to_3x3() @ Vector((0, -0.0035, 0))
    C.obj('clip', C.rbox('clip', (0.06, 0.012, 0.02), 0.004, 2), M['satin'], (0.25, -0.12, 0.03)).rotation_euler = (deg(-28), 0, deg(-8))
    A.box('seat', (1.4, 0.4, 0.04), (0.0, -0.18, -0.215), M['teak'], 0.01)
    panel_scene(((0.12, -0.76, 0.19), (0.10, -0.05, 0.0), 42))
    bpy.context.view_layer.update()
    labels = [(Vector((g['tach'][0], 0, g['tach'][1] + 0.052)), 'hour meter 2312.1', 'blue'),
              (Vector((g['g2'][0], 0, g['g2'][1] + 0.036)), 'fuel full'),
              (A.shift_px(pg.matrix_world @ Vector((0.0, 0, 0.2095 * (0.5 - 630 / 1754))), 0, -20), 'form says 2 290', 'red')]
    note = 'Form says 2,290: have it corrected'
    extra = {'lines': ['Photograph the panel before you sign']}

elif FIG == 77:
    # inset for fig 7: the exhaust outlet on the transom, white steam blowing aft off it
    KI.wall('topsides', -8, 0, -0.3, 1.0, 0.0, M['hull'])
    KI.wall('boot', -8, 0, -0.3, 0.05, -0.002, M['boot'])
    tr = bpy.data.meshes.new('transom'); tr.from_pydata([(0, 0, -0.3), (0, 2.2, -0.3), (0, 2.2, 1.0), (0, 0, 1.0)], [], [(0, 1, 2, 3)]); C.obj('transom', tr, M['hull'])
    A.box('rubbing-strake', (8, 0.05, 0.06), (-4, -0.02, 1.0), M['strake'], 0.01)
    A.box('pushpit', (0.02, 2.2, 0.02), (-0.15, 1.1, 1.65), M['satin'], 0.008)
    for yy in (0.05, 1.1, 2.15): C.cyl('pushpit-leg', 0.012, 0.012, 0.65, 12, M['satin'], (-0.15, yy, 1.33))
    A.box('stanchion-rail', (8, 0.02, 0.02), (-4, 0.05, 1.65), M['satin'], 0.008)
    for xx in range(-8, 0, 2): C.cyl('stanchion', 0.012, 0.012, 0.65, 12, M['satin'], (xx * 1.0, 0.05, 1.33))
    ex = Vector((0.0, 0.45, 0.32))
    fl = C.obj('exh-flange', KI._cyl_y(0.045, 0.012), M['chrome'], ex + Vector((0.006, 0, 0))); fl.rotation_euler = (0, 0, deg(90))
    hl = C.obj('exh-hole', KI._cyl_y(0.03, 0.014), C.simple('hole', '#050505', 0.9), ex + Vector((0.008, 0, 0))); hl.rotation_euler = (0, 0, deg(90))
    def steam_mat(dens):
        m, nt, b, out = C.new_mat('steam'); nt.nodes.remove(b)
        vol = nt.nodes.new('ShaderNodeVolumePrincipled'); vol.inputs['Color'].default_value = (0.95, 0.96, 0.97, 1)
        vol.inputs['Emission Strength'].default_value = 0.25; vol.inputs['Emission Color'].default_value = (1, 1, 1, 1)
        tc = nt.nodes.new('ShaderNodeTexCoord'); nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 2.2; nz.inputs['Detail'].default_value = 8.0
        nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
        gr = nt.nodes.new('ShaderNodeTexGradient'); gr.gradient_type = 'SPHERICAL'; nt.links.new(tc.outputs['Object'], gr.inputs['Vector'])
        mul = nt.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'; nt.links.new(nz.outputs['Fac'], mul.inputs[0]); nt.links.new(gr.outputs['Fac'], mul.inputs[1])
        rp = nt.nodes.new('ShaderNodeMapRange'); rp.inputs['From Min'].default_value = 0.1; rp.inputs['From Max'].default_value = 0.45; rp.inputs['To Max'].default_value = dens
        nt.links.new(mul.outputs[0], rp.inputs['Value']); nt.links.new(rp.outputs['Result'], vol.inputs['Density']); nt.links.new(vol.outputs[0], out.inputs['Volume'])
        return m
    # puffs of steam blowing out of the outlet and rising; the small ones near the outlet denser, so each reads alike
    for i, (p, s) in enumerate((((0.05, 0.45, 0.33), 0.05), ((0.13, 0.44, 0.36), 0.08), ((0.25, 0.42, 0.42), 0.12), ((0.42, 0.38, 0.51), 0.17), ((0.64, 0.33, 0.63), 0.23))):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=1.0, location=p); o = bpy.context.active_object; o.data.materials.append(steam_mat(2.4 / s))
        o.scale = (1.3 * s, s, 0.9 * s); o.rotation_euler = (0.3 * i, 0.5 * i, 0.2); o.visible_shadow = False
    K.sea('calm', size=8.0, repeat=6, center=(0, -2)); K.day_sky(sun_az=200, sun_el=35)
    K.camera((1.0, -1.9, 0.55), (0.25, 0.3, 0.45), 40)
    expo = -0.6

C.render(OUT, SAMPLES, SCALE, expo, labels, note, space='blender', arrows=arrows, extra=extra)

if FIG == 7 and not INSET:
    ins = os.path.splitext(OUT)[0] + '-inset.jpg'
    subprocess.run([bpy.app.binary_path, '--background', '--factory-startup', '--python', os.path.abspath(__file__), '--',
                    '--fig', '77', '--out', ins, '--samples', str(SAMPLES), '--inset', '1'], check=True)
    subprocess.run(['python3', os.path.join(A.HERE, 'art_checkin_sys_tex.py'), 'inset', OUT, ins, 'steam at the exhaust'], check=True)
