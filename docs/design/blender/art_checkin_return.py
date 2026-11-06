# Article charter-checkin/return, figures 1-5, as Blender renders (art_checkin_sys_kit.py for the shared parts).
#   1  a catamaran's two engine panels side by side: port 2 214 h, starboard 2 187 h, both tanks full
#   2  card: the stern at the pontoon, the outboard gone from its bracket on the pushpit, the cut security cable hanging
#   3  bay: a drone view of the base marina: A the fuel dock with your yacht alongside it, B your empty berth on the pier
#   4  the panel at check-out: 1 412 h; your phone shows the check-in photo (1 371 h), the check-out form says 1 421
#   5  card: the damage settlement on the chart table: chip €350, pulpit €900 capped at €500, €850 from the deposit
#   blender --background --factory-startup --python docs/design/blender/art_checkin_return.py -- --fig 1 [--samples 160]
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
from mathutils import Vector
import common as C, kit as K, kit_instruments as KI, kit_world as KW
import art_checkin_sys_kit as A

arg = C.cli(); FIG = arg('--fig', 1); SAMPLES = arg('--samples', 160); SCALE = arg('--scale', 100)
OUT = arg('--out', os.path.join(A.outdir('return'), f'{FIG}-3d.jpg'))
A.use_article('return'); deg = math.radians

labels, arrows, note, expo, extra = [], [], None, -0.6, {}
C.reset(); A.frame_setup(); M = K.mats()

if FIG == 1:
    KI.wall('helm', -0.8, 0.8, -0.4, 0.4, 0.012, M['hull'])
    gp = A.engine_panel(at=(-0.2, 0.0), rpm=0, hours='2214.3', right='fuel', fuel=1.0, volts=12.7, key=False)
    gs = A.engine_panel(at=(0.2, 0.0), rpm=0, hours='2187.6', right='fuel', fuel=1.0, volts=12.7, key=False)
    for x, t in ((-0.2, 'PORT'), (0.2, 'STBD')): A.quad('side-' + t, 0.07, 0.0194, A.tex('sticker', t), (x, -0.0005, 0.095), 0.0, 0.6)
    K.day_sky(sun_az=200, sun_el=35, strength=0.18)
    K.camera((0.0, -0.95, 0.16), (0.0, 0, 0.03), 42)
    labels = [(Vector((gp['tach'][0], 0, gp['tach'][1] + 0.052)), 'Port 2 214 h'), (Vector((gs['tach'][0], 0, gs['tach'][1] + 0.052)), 'Stbd 2 187 h')]
    note = 'Catamaran: both hour meters on the form'
    extra = {'lines': ['Photograph each panel']}

elif FIG == 2:
    # the yacht stern-to the pontoon; the outboard bracket on her starboard pushpit is empty, the cable cut
    K.sea('calm', size=30.0, repeat=8); K.day_sky(sun_az=120, sun_el=38)
    y = K.load_yacht(name='yacht').place(0.0, 0.0, heading=0)
    A.clone_yacht(y, 'n1').place(-4.7, 0.3, heading=0)
    stern = y.world((-3.8, 0.13, 2.0)); edge = stern.y - 1.1; TOP = 0.45; W_P = 2.6
    C.tbox((40.0, 0.8, W_P - 0.1), (0.0, -0.05, -(edge - W_P / 2)), M['float'], 0.08, 2, 'float')
    plank_me = C.rbox('plank', (0.14, W_P, 0.035), 0.004, 1); plank_me.materials.append(M['planks'])
    xx = -20.0
    while xx < 20.0:
        o = bpy.data.objects.new('plank', plank_me); C.col.objects.link(o); o.location = (xx, edge - W_P / 2, TOP - 0.0175); xx += 0.155
    # the outboard mount on her starboard quarter (the model's own small bracket at the stern rail, model x -2.9)
    top = y.world((-2.95, -0.805, 4.08))
    teak = M['teak']; ss = M['chrome']
    pad = top + Vector((0.0, -0.08, -0.20))
    A.box('ob-pad', (0.30, 0.045, 0.22), pad, teak, 0.01)
    for dx in (-0.1, 0.1):
        A.box('ob-arm', (0.025, 0.12, 0.025), top + Vector((dx, -0.05, -0.12)), ss, 0.006)
        C.cyl('ob-clamp', 0.02, 0.02, 0.05, 16, ss, top + Vector((dx, 0.0, 0.0)), (0, deg(90), 0))
    # the security cable: a loop through the bracket, its end cut and frayed, a padlock still on the loop
    wire = C.simple('steel-cable', '#a9adb2', 0.35, 1.0)
    p = pad + Vector((0.12, -0.03, 0.08))
    pts = [p, p + Vector((0.05, -0.05, -0.15)), p + Vector((0.04, -0.08, -0.35)), p + Vector((-0.02, -0.06, -0.55)), p + Vector((-0.05, -0.03, -0.68))]
    A.hose('cable', pts, 0.006, wire)
    A.box('padlock', (0.04, 0.02, 0.05), pts[2] + Vector((0.0, -0.01, 0)), C.simple('brass', '#b8963c', 0.35, 1.0), 0.006)
    end = pts[-1]
    for k in range(5): C.cyl('fray', 0.0012, 0.0012, 0.03, 6, wire, end + Vector((0.004 * (k - 2), 0, -0.015)), (deg(10 * (k - 2)), deg(8 * (k - 2)), 0))
    K.camera(Vector((pad.x + 1.0, edge - 1.5, 1.75)), Vector((pad.x - 0.2, pad.y, pad.z - 0.3)), 34)
    labels = [(pad + Vector((0, 0, 0.13)), 'outboard gone from its bracket', 'red'), (end + Vector((0.02, 0, -0.02)), 'cut cable: keep it')]
    note = 'Photograph it, phone the base the same day'
    extra = {'lines': ['Theft: a police report as well']}; expo = -0.6

elif FIG == 3:
    # the base marina from a drone: bay units x 0.6 = metres; x east, y north
    U = lambda x, y: Vector(((x - 160) * 0.6, -(y - 100) * 0.6, 0))
    K.sea('calm', size=40.0, repeat=8, center=(-20, 0)); K.day_sky(sun_az=200, sun_el=50)
    conc = C.concrete_mat('quay'); QH = 1.2
    def quay(x0, y0, x1, y1):
        a, b = U(x0, y0), U(x1, y1)
        A.box('quay', (abs(b.x - a.x), abs(b.y - a.y), QH + 2), ((a.x + b.x) / 2, (a.y + b.y) / 2, QH / 2 - 1), conc, 0.1)
    quay(0, -40, 320, 40); quay(0, 40, 70, 66); quay(140, 40, 150, 140); quay(290, 40, 320, 180)
    plaster, roof = KW.plaster_mat(), KW.roof_mat()
    for i, (x, y, w, d, h) in enumerate(((20, 10, 22, 12, 7), (60, 6, 16, 10, 6), (110, 12, 30, 14, 9), (180, 8, 20, 12, 7), (230, 12, 26, 12, 8), (280, 8, 18, 10, 6))):
        c = U(x, y); A.box('building', (w * 0.6, d * 0.6, h), (c.x, c.y, QH + h / 2), plaster, 0.1); A.box('roof', (w * 0.6 + 0.4, d * 0.6 + 0.4, 0.5), (c.x, c.y, QH + h + 0.25), roof, 0.1)
    # the fuel pontoon off the corner of the left quay, a pump on it
    fp = U(66, 66); A.box('fuel-pontoon', (3.0, 18.0, 0.5), (fp.x + 1.5, fp.y - 9.0, 0.25), conc, 0.05)
    pump = Vector((fp.x + 1.6, fp.y - 6.0, 0.5)); A.box('pump', (0.8, 0.5, 1.5), pump + Vector((0, 0, 0.75)), C.simple('pump-red', '#c4161c', 0.4, coat=0.5), 0.05)
    A.box('pump-sign', (1.6, 0.1, 0.5), pump + Vector((0, 0, 2.2)), C.simple('pump-white', '#f0efe8', 0.4), 0.03)
    you = K.load_yacht(name='you').place(fp.x - 2.3, fp.y - 9.0, heading=180)
    # stern-to boats along the east side of the pier, a gap at B
    px = U(150, 100).x
    for i, yy in enumerate((-30, -25, -20, -15, -10, 5, 10, 15, 20, 25)):
        A.clone_yacht(you, 'm%d' % i).place(px + 9.9, yy, heading=90)
    for i, yy in enumerate((-22, -14, -6, 6, 14, 22)):
        A.clone_yacht(you, 'w%d' % i).place(U(140, 100).x - 9.9, yy, heading=270)
    B = Vector((px + 9.9, 0.0, 0.0))
    K.camera(Vector((-29.0, -58.0, 64.0)), Vector((-29.0, 10.0, 0.0)), 36)
    labels = [(you.world((4.93, 0.13, 18.0)), 'A fuel dock: fill up, keep the receipt', 'blue'), (B + Vector((0, 0, 3.0)), 'B your berth tonight')]
    note = 'A first, then B'
    expo = -0.6

elif FIG == 4:
    g = A.engine_panel(rpm=0, right='fuel', fuel=1.0, volts=12.6, lit=(), key=False, hours='1412.0')
    KI.wall('cockpit-side', -0.7, 0.8, -0.4, 0.35, 0.012, M['hull'])
    A.box('seat', (1.6, 0.5, 0.04), (0.0, -0.25, -0.14), M['teak'], 0.01)
    board = A.box('clipboard', (0.16, 0.004, 0.22), (0.27, -0.10, -0.02), C.simple('board', '#6b4a2a', 0.6), 0.004); board.rotation_euler = (deg(-28), 0, deg(-8))
    pg = A.quad('form', 0.148, 0.2095, A.tex('form', 'checkout'), (0.27, -0.103, -0.028), 0.0, 0.8, rot=(deg(-28), 0, deg(-8)))
    bpy.context.view_layer.update(); pg.location += pg.matrix_world.to_3x3() @ Vector((0, -0.0035, 0))
    C.obj('clip', C.rbox('clip', (0.06, 0.012, 0.02), 0.004, 2), M['satin'], (0.27, -0.09, 0.09)).rotation_euler = (deg(-28), 0, deg(-8))
    # the phone on the seat, showing the photo taken at check-in
    ph = A.box('phone', (0.075, 0.155, 0.008), (-0.02, -0.25, -0.12 + 0.0775 * math.sin(deg(32)) + 0.004), C.simple('phone', '#121214', 0.3, coat=0.8), 0.006)
    ph.rotation_euler = (deg(32), 0, deg(8))
    scr = A.quad('screen', 0.068, 0.1405, A.tex('phone', 'hours1371'), (0, 0, 0.0045), 0.9, 0.2, normal='+Z'); scr.parent = ph
    A.box('phone-prop', (0.12, 0.03, 0.03), (-0.02, -0.19, -0.105), M['dark'], 0.008)
    K.day_sky(sun_az=200, sun_el=35, strength=0.18)
    K.camera((0.06, -0.68, 0.22), (0.06, -0.06, -0.008), 37)
    bpy.context.view_layer.update()
    labels = [(Vector((g['tach'][0], 0, g['tach'][1] + 0.052)), 'now 1 412 h'),
              (scr.matrix_world @ Vector((0, 0.035, 0.002)), 'your check-in photo: 1 371 h', 'blue'),
              (A.shift_px(pg.matrix_world @ Vector((0.0, 0, 0.2095 * (0.5 - 630 / 1754))), 0, -20), 'form says 1 421', 'red')]
    note = 'Form says 1 421: corrected before you sign'
    extra = {'lines': ['41 hours this week, not 50']}

elif FIG == 5:
    # the settlement on the chart table, a pen beside it, the bulkhead behind
    wood = KI.joinery_mat('table-wood')
    A.box('table', (1.2, 0.8, 0.03), (0, 0.05, -0.015), wood)
    KI.wall('bulkhead', -0.8, 0.8, 0.0, 0.6, 0.45, KI.joinery_mat())
    pw, ph = 0.21, 0.297
    paper = A.quad('settlement', pw, ph, A.tex('form', 'settlement'), (0.0, 0.0, 0.001), 0.0, 0.85, normal='+Z', rot=(0, 0, deg(-4)))
    pen = C.cyl('pen', 0.005, 0.005, 0.14, 16, C.simple('pen', '#1a2a5a', 0.3, coat=0.6), (0.16, -0.02, 0.006), (deg(90), 0, deg(20)))
    C.cyl('pen-tip', 0.005, 0.001, 0.018, 16, M['chrome'], (0.16, -0.02, 0.006), (0, 0, 0))
    bpy.context.view_layer.update()
    at = lambda v: paper.matrix_world @ Vector((0.0, ph * (0.5 - v / 1754), 0.001))
    K.day_sky(sun_az=150, sun_el=40, strength=0.08)
    KI.area_light((0.3, -0.6, 0.9), (0, 0, 0), 12, 0.6); KI.area_light((-0.6, -0.4, 0.6), (0, 0, 0), 4, 1.0, (0.85, 0.9, 1.0))
    K.camera((0.03, -0.13, 0.44), (0.03, 0.0, 0.0), 40)
    labels = [(A.shift_px(at(440), 170, 0), 'chip: you pay €350'), (A.shift_px(at(700), 170, 0), 'pulpit €900: you pay €500', 'red'),
              (A.shift_px(at(950), 170, 0), 'from the deposit: €850', 'blue')]
    note = 'Excess €500 per incident: each repair capped'
    extra = {'lines': ['€350 + €500 = €850, not €1,250']}

C.render(OUT, SAMPLES, SCALE, expo, labels, note, space='blender', arrows=arrows, extra=extra)
