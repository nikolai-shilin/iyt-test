# Article charter-checkin/electrics, figures 1-6, as Blender renders (art_checkin_sys_kit.py for the shared parts).
#   1  card: the battery switches on their bulkhead: ENGINE and HOUSE on, BOTH (emergency parallel) off
#   2  engine running at 1500 rpm, the charge lamp lit, the battery monitor at 12.3 V and -8 A: nothing going in
#   3  card: the house bank in its locker, two 100 Ah batteries, the monitor after a night at anchor: 55 Ah used
#   4  card: shore power at a stern-to berth: the cable from the boat's inlet to the pontoon pedestal and its switch
#   5  lights: a yacht under power at night seen from ahead: masthead light, green and red sidelights
#   6  lights: a yacht at anchor at night: the all-round white light at the masthead, nothing else
#   blender --background --factory-startup --python docs/design/blender/art_checkin_electrics.py -- --fig 1 [--samples 160]
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
from mathutils import Vector
import common as C, kit as K, kit_instruments as KI, kit_night as N
import art_checkin_sys_kit as A

arg = C.cli(); FIG = arg('--fig', 1); SAMPLES = arg('--samples', 160); SCALE = arg('--scale', 100)
OUT = arg('--out', os.path.join(A.outdir('electrics'), f'{FIG}-3d.jpg'))
A.use_article('electrics'); deg = math.radians

labels, arrows, note, expo, extra = [], [], None, -0.5, {}
C.reset(); A.frame_setup(); M = K.mats()

def rotary(x, z, label, on, y=0.0):
    """A red rotary battery switch on its round label plate; the lever vertical = ON, across = OFF."""
    red = C.simple('isolator-red', '#c4161c', 0.35, coat=0.6)
    A.quad('plate-' + label, 0.16, 0.16, A.tex('switch', label), (x, y - 0.0015, z), 0.0, 0.5)
    C.obj('iso-base', KI._cyl_y(0.034, 0.016), red, (x, y - 0.010, z))
    C.obj('iso-boss', KI._cyl_y(0.022, 0.012), C.simple('iso-boss', '#a01015', 0.4, coat=0.6), (x, y - 0.024, z))
    kn = C.obj('iso-lever', C.rbox('kn', (0.016, 0.03, 0.066), 0.006, 3), red, (x, y - 0.036, z))
    kn.rotation_euler = (0, deg(0 if on else 90), 0)
    tip = C.obj('iso-tip', C.rbox('tip', (0.008, 0.004, 0.016), 0.002, 1), C.simple('tip-white', '#f2f2ee', 0.4), (0, -0.016, -0.022))
    tip.parent = kn
    return Vector((x, y - 0.03, z))

if FIG == 1:
    # a white GRP liner beside the companionway, a teak board on it with three switches in a row, heavy cables
    # going down behind them to the batteries
    liner = A.frp_mat('liner', '#d9d6cd')
    KI.wall('liner', -0.8, 0.8, -0.6, 0.5, 0.0, liner)
    C.obj('board', C.rbox('board', (0.66, 0.02, 0.24), 0.008, 2), KI.joinery_mat('board-wood'), (0.0, -0.01, 0.0))
    xs = (-0.2, 0.0, 0.2)
    P = [rotary(x, 0.0, lab, on, y=-0.02) for x, lab, on in zip(xs, ('ENGINE', 'HOUSE', 'BOTH'), (True, True, False))]
    cab_r, cab_b = C.simple('cable-red', '#a3141a', 0.45), C.simple('cable-black', '#141416', 0.5)
    for i, x in enumerate(xs):
        for dx, mat in ((-0.025, cab_r), (0.025, cab_b)):
            A.hose('cable', [(x + dx, -0.005, -0.10), (x + dx, -0.03, -0.14), (x + dx * 1.4, -0.03, -0.3), (x + dx * 2 + 0.04 * (i - 1), -0.03, -0.6)], 0.009, mat)
    A.interior_light(7, 2.5, (0.0, 0.0, 0.0))
    K.camera((0.04, -1.25, 0.12), (0.0, 0.0, -0.04), 50)
    labels = [(A.shift_px(P[0], 0, -100), 'ENGINE: on'), (A.shift_px(P[1], 0, -100), 'HOUSE: on'),
              (A.shift_px(P[2], 0, -100), 'BOTH: off', 'red')]
    note = 'At sea and at anchor: ENGINE and HOUSE on, BOTH off'
    extra = {'lines': ['BOTH: only to start on a flat battery', 'Engine running: never switch ENGINE off']}

elif FIG == 2:
    KI.wall('cockpit-side', -0.6, 0.75, -0.4, 0.35, 0.012, M['hull'])
    g = A.engine_panel(rpm=1500, right='temp', temp=72, volts=12.3, lit=('CHARGE',))
    # the battery monitor beside it, on the same bulkhead
    bx, bz = 0.30, 0.01
    C.obj('mon', C.rbox('mon', (0.13, 0.016, 0.11), 0.008, 3), M['dark'], (bx, 0.0, bz))
    A.quad('mon-lcd', 0.104, 0.078, A.sysface('lcd', '520', '390', 'HOUSE|12.3 V@red|-8.0 A@red'), (bx, -0.0085, bz + 0.006), 1.2, 0.3)
    K.day_sky(sun_az=200, sun_el=35, strength=0.18)
    K.camera((0.10, -0.68, 0.11), (0.09, 0, 0.0), 45)
    labels = [(Vector((g['tach'][0], 0, g['tach'][1] + 0.052)), 'RPM 1500: running'),
              (Vector((g['charge'][0], 0, g['charge'][1] + 0.012)), 'charge lamp on', 'red'),
              (Vector((bx, 0, bz + 0.062)), '12.3 V, −8 A: nothing going in', 'red')]
    note = 'Engine running, the bank not charging · belt or alternator: before you leave'

elif FIG == 3:
    # the house bank under the saloon seat, cushion and lid lifted away; the battery monitor on the bulkhead behind
    frp = A.frp_mat('locker', '#d6d2c6'); wood = KI.joinery_mat()
    KI.wall('floor', -0.5, 0.5, -0.4, 0.4, 0.0, frp).data.vertices.foreach_set('co', [-0.5, -0.35, 0, 0.5, -0.35, 0, 0.5, 0.25, 0, -0.5, 0.25, 0])
    for name, dims, loc in (('front', (0.86, 0.02, 0.30), (0, -0.30, 0.15)), ('back', (0.86, 0.02, 0.30), (0, 0.24, 0.15)),
                            ('left', (0.02, 0.56, 0.30), (-0.42, -0.03, 0.15)), ('right', (0.02, 0.56, 0.30), (0.42, -0.03, 0.15))):
        A.box('locker-' + name, dims, loc, wood if name == 'front' else frp, 0.004)
    A.box('seat-edge', (0.88, 0.04, 0.03), (0, -0.30, 0.315), wood, 0.008)
    A.box('seat-back', (0.86, 0.09, 0.36), (0, 0.30, 0.58), C.fabric_mat('cushion', '#2b3a55'), 0.035)
    KI.wall('bulkhead', -1.6, 1.6, 0.0, 1.6, 0.36, wood)
    A.box('sole', (3.2, 1.6, 0.02), (0, -1.1, -0.01), KI.joinery_mat('sole-wood'))
    cush = C.fabric_mat('cushion', '#2b3a55')
    for sx in (-1, 1):   # the settee runs on either side of the open locker
        A.box('settee-front', (1.2, 0.02, 0.30), (sx * 1.04, -0.30, 0.15), wood, 0.004)
        A.box('settee-seat', (1.16, 0.56, 0.10), (sx * 1.04, -0.02, 0.36), cush, 0.03)
        A.box('settee-back', (1.16, 0.09, 0.36), (sx * 1.04, 0.30, 0.58), cush, 0.035)
    case = C.simple('battery-case', '#1f2124', 0.6)
    lead, red, blk = C.simple('lead', '#8d8f93', 0.45, 0.8), C.simple('term-red', '#b31a1a', 0.5), C.simple('term-black', '#18191b', 0.5)
    tops = []
    for i, x in enumerate((-0.19, 0.19)):
        A.box('battery', (0.33, 0.17, 0.21), (x, -0.04, 0.105), case, 0.008)
        A.quad('bat-label', 0.17, 0.0863, A.tex('battery', '12 V|100 Ah|AGM'), (x, -0.04, 0.2105), 0.0, 0.6, normal='+Z')
        for dx, cap in ((-0.13, red), (0.13, blk)):
            C.cyl('post', 0.009, 0.009, 0.02, 16, lead, (x + dx, -0.04, 0.22)); C.cyl('cover', 0.018, 0.012, 0.03, 16, cap, (x + dx, -0.04, 0.235))
        tops.append(Vector((x, -0.04, 0.21)))
    cr, cb = C.simple('cable-red', '#a3141a', 0.45), C.simple('cable-black', '#141416', 0.5)
    A.hose('link+', [(-0.32, -0.04, 0.25), (-0.12, 0.06, 0.28), (0.06, -0.04, 0.25)], 0.009, cr)
    A.hose('link-', [(-0.06, -0.04, 0.25), (0.12, 0.08, 0.27), (0.32, -0.04, 0.25)], 0.009, cb)
    A.hose('main+', [(0.06, -0.04, 0.25), (0.12, 0.10, 0.27), (0.30, 0.20, 0.27), (0.38, 0.22, 0.32)], 0.01, cr)
    A.hose('main-', [(0.32, -0.04, 0.25), (0.37, 0.08, 0.26), (0.40, 0.2, 0.28), (0.41, 0.22, 0.32)], 0.01, cb)
    # the battery monitor on the bulkhead above the seat back
    mx, mz = 0.40, 0.84
    C.obj('mon', C.rbox('mon', (0.13, 0.016, 0.11), 0.008, 3), M['dark'], (mx, 0.352, mz))
    A.quad('mon-lcd', 0.104, 0.078, A.sysface('lcd', '520', '390', 'HOUSE|-55 Ah|73 %'), (mx, 0.3435, mz + 0.006), 1.2, 0.3)
    K.day_sky(sun_az=150, sun_el=40, strength=0.08)
    KI.area_light((0.4, -0.7, 1.5), (0, 0, 0.2), 16, 0.8); KI.area_light((-0.8, -0.6, 1.1), (0, 0, 0.3), 5, 1.0, (0.85, 0.9, 1.0))
    K.camera((0.22, -1.5, 1.2), (0.12, 0.1, 0.6), 36)
    labels = [(A.shift_px(tops[0] + Vector((0.19, 0, 0.05)), 0, -10), 'house bank 2 × 100 Ah: 100 Ah usable'),
              (Vector((mx, 0.34, mz + 0.062)), 'morning: 55 Ah used', 'blue')]
    note = 'Fridge 5 A × 10 h = 50 Ah · anchor light and phones a few Ah more'
    extra = {'lines': ['Morning: run the engine for an hour']}

elif FIG == 4:
    # a stern-to berth: the yacht's stern at the pontoon, the shore cable from her inlet to the pedestal
    K.sea('calm', size=30.0, repeat=8); K.day_sky(sun_az=120, sun_el=38)
    y = K.load_yacht(name='yacht').place(0.0, 0.0, heading=0)            # bow north, stern to the pontoon (south)
    A.clone_yacht(y, 'n1').place(-4.7, 0.3, heading=0); A.clone_yacht(y, 'n2').place(4.7, -0.2, heading=0)
    stern = y.world((-3.8, 0.13, 2.0)); edge = stern.y - 1.1; TOP = 0.45; W_P = 2.6
    C.tbox((40.0, 0.8, W_P - 0.1), (0.0, -0.05, -(edge - W_P / 2)), M['float'], 0.08, 2, 'float')
    plank_me = C.rbox('plank', (0.14, W_P, 0.035), 0.004, 1); plank_me.materials.append(M['planks'])
    xx = -20.0
    while xx < 20.0:
        o = bpy.data.objects.new('plank', plank_me); C.col.objects.link(o); o.location = (xx, edge - W_P / 2, TOP - 0.0175); xx += 0.155
    C.tbox((40.0, 0.12, 0.07), (0.0, TOP - 0.11, -(edge - 0.02)), M['rubber'], 0.02, 2, 'rubbing-strip')
    navy = C.simple('line-navy', '#1b2c4c', 0.8)
    for side in (-1, 1):   # stern lines to the pontoon cleats
        q = y.world((-3.5, 0.13 + side * 1.75, 3.62)); c = Vector((q.x - side * 0.5, edge - 0.3, TOP + 0.05))
        C.cyl('cleat-horn', 0.02, 0.02, 0.3, 16, M['galv'], c + Vector((0, 0, 0.06)), (0, math.pi / 2, 0))
        A.hose('stern-line', [q, q.lerp(c, 0.5) + Vector((0, 0, -0.35)), c + Vector((0, 0, 0.06))], 0.011, navy)
    # the pedestal on the pontoon, to starboard of her stern
    px0 = Vector((2.0, edge - 0.6, TOP))
    ped = C.simple('pedestal', '#e8eae6', 0.35, coat=0.4)
    A.box('pedestal', (0.26, 0.24, 1.0), px0 + Vector((0, 0, 0.5)), ped, 0.03)
    A.box('ped-cap', (0.30, 0.28, 0.06), px0 + Vector((0, 0, 1.02)), C.simple('ped-cap', '#1d5fa8', 0.35, coat=0.5), 0.02)
    A.quad('ped-front', 0.22, 0.366, A.tex('pedestal'), px0 + Vector((0, -0.1215, 0.72)), 0.0, 0.4)
    blue = C.simple('cee-blue', '#2a64b8', 0.4)
    sock = px0 + Vector((0, -0.13, 0.42))
    C.obj('socket', KI._cyl_y(0.045, 0.05), blue, sock + Vector((0, -0.01, 0)))
    C.obj('plug', KI._cyl_y(0.04, 0.10), blue, sock + Vector((0, -0.08, 0)))
    sw = px0 + Vector((0.0, -0.13, 0.81)); C.obj('switch', C.rbox('sw', (0.04, 0.025, 0.05), 0.004, 2), C.simple('sw-black', '#202224', 0.4), sw)
    # the boat's inlet on the transom, starboard side; the yellow cable between them, kept on the planks
    ix = y.world((-3.0, 0.13 - 0.9, 3.0)); hp, hn = A.hit(ix + Vector((0, -6, 0)), (0, 1, 0))
    inlet = hp if hp is not None else y.world((-3.83, -0.77, 3.0))
    C.obj('inlet', KI._cyl_y(0.05, 0.03), M['satin'], inlet + Vector((0, -0.01, 0)))
    C.obj('inlet-plug', KI._cyl_y(0.04, 0.09), blue, inlet + Vector((0, -0.06, 0)))
    cable = C.simple('shore-cable', '#e3b51c', 0.5, coat=0.2)
    pa = inlet + Vector((0, -0.11, 0)); pb = sock + Vector((0, -0.14, 0))
    A.hose('shore-cable', [pa, pa + Vector((0.05, -0.3, -0.45)), Vector((pa.x + 0.25, edge - 0.25, TOP + 0.016)), Vector((pa.x + 0.6, edge - 0.6, TOP + 0.016)),
                           Vector((pb.x - 0.3, pb.y - 0.25, TOP + 0.016)), Vector((pb.x - 0.05, pb.y - 0.12, TOP + 0.1)), pb], 0.014, cable)
    K.camera(Vector((-0.9, edge - 3.6, 1.6)), Vector((1.25, edge + 0.4, 1.0)), 30)
    labels = [(A.shift_px(inlet + Vector((0, -0.1, 0.08)), 0, -6), '1 boat end'),
              (A.shift_px(sock + Vector((0, -0.2, 0.06)), 0, -6), '2 pedestal end', 'blue'),
              (A.shift_px(sw + Vector((0, -0.02, 0.04)), 0, -6), '3 pedestal switch', 'blue')]
    note = "Connect with the boat's 230 V main off · then the main and the charger"
    extra = {'lines': ['Leave: unplug the pedestal first, then the boat']}
    expo = -0.6

elif FIG in (5, 6):
    N.night_scene('calm')
    y = K.load_yacht(name='yacht'); N.cloth_furled(y)
    if FIG == 5:
        # motoring towards us: masthead light on the front of the mast, the bicolour on the pulpit
        y.place(0.0, 0.0, heading=186)
        mh = y.world((5.45, 0.13, 11.5)); N.light('masthead', mh, 'white', strength=9.0, power=30.0, radius=0.12)
        red, green = y.world((10.2, 0.58, 4.22)), y.world((10.2, -0.32, 4.22))
        N.light('port-red', red, 'red', strength=2.5, power=10.0, radius=0.06)
        N.light('stbd-green', green, 'green', strength=2.5, power=10.0, radius=0.06)
        K.wake(y, 18, 3, 0.5)
        ld = bpy.data.lights.new('moonfill', 'SUN'); ld.energy = 0.02; ld.color = (0.7, 0.8, 1.0)
        lo = bpy.data.objects.new('moonfill', ld); C.col.objects.link(lo); lo.rotation_euler = (deg(60), 0, deg(160))
        K.camera(Vector((3.0, -34.0, 2.0)), Vector((0.2, 0.0, 6.5)), 45)
        labels = [(mh + Vector((0, 0, 0.6)), 'masthead light: white, ahead'),
                  ((red + green) / 2 + Vector((0, 0, 0.5)), 'green starboard · red port')]
        note = 'Under power, seen from ahead'
        extra = {'bloom': 1.0, 'lines': ['Test them after dark, from the pontoon']}; expo = 0.6
    else:
        y.place(0.0, 0.0, heading=60)
        top = y.world((5.06, 0.13, 20.8)); N.light('anchor-light', top, 'white', strength=12.0, power=40.0, radius=0.16)
        ld = bpy.data.lights.new('moonfill', 'SUN'); ld.energy = 0.02; ld.color = (0.7, 0.8, 1.0)
        lo = bpy.data.objects.new('moonfill', ld); C.col.objects.link(lo); lo.rotation_euler = (deg(60), 0, deg(160))
        K.camera(Vector((-6.0, -44.0, 2.5)), Vector((0.5, 0.0, 12.6)), 32)
        labels = [(top + Vector((0, 0, 0.8)), 'all-round white at the masthead')]
        note = 'At anchor, every night · no sidelights, no masthead light'
        extra = {'bloom': 1.0, 'lines': ['Overnight on: anchor light, bilge pump, gas alarm']}; expo = 0.8

C.render(OUT, SAMPLES, SCALE, expo, labels, note, space='blender', arrows=arrows, extra=extra)
