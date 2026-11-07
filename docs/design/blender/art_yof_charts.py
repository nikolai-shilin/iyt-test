# Article yachtmaster-offshore/charts, its eleven figures as Blender renders.
#   1  the chart table: a North Atlantic Mercator chart, 40-60N; pencil brackets show 40-50 and 50-60, 600 M each
#   2  Bay of Biscay chart: a 45.0 M leg along 48N, dividers on the latitude scale beside it; 42N pencilled (50.0')
#   3  the notebook with the mid-latitude sailing worked in pencil, a calculator, the chart behind
#   4  the table of meridional parts open beside the notebook with the Mercator sailing
#   5  1:350,000: a bank inside its 20 m contour, the 0600 EP 5 mm outside it, a steel rule across the gap
#   6  the Breton plotter on a 205 T track, its grid on the meridians, 211 against the 6 W mark
#   7  the log book from 2130 to 0415, the bulkhead clock at 04:15, the calculator at 7.333
#   8  night: a platform, white Mo(U) light in the middle, red lights at its ends
#   9  dusk: a wind farm, yellow lights on the towers flashing together, red aviation lights on the nacelles
#   10 the corner of a chart with its corrections record and stamp, the weekly Notices to Mariners on it
#   11 the plotter at the chart table showing an ENC: safety contour set 4.2 m, the 5 m contour drawn bold
#   blender --background --factory-startup --python docs/design/blender/art_yof_charts.py -- --fig 1 [--samples 160]
import os, sys, math, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import bpy, bmesh
from mathutils import Vector
import common as C, kit as K, kit_instruments as KI, kit_night as N
import art_checkin_nps_kit as A
import art_yof_nav_kit as Y

ART = 'charts'
arg = C.cli(); FIG = arg('--fig', 1); SAMPLES = arg('--samples', 160); SCALE = arg('--scale', 100)
OUT = arg('--out', os.path.join(Y.outdir(ART), f'{FIG}-3d.jpg'))
deg = math.radians

C.reset()
M = Y.mats()
labels, arrows, note, expo, extra = [], [], None, -0.3, {}

def up(p, dz=0.004): return Vector(p) + Vector((0, 0, dz))

if FIG == 1:
    Y.chart_table(1.5, 0.95)
    ch = Y.chart(ART, 'merc', (0.12, -0.02))
    # dividers open one degree on the right-hand latitude scale, 55-56N; a pencil
    m = ch.meta
    def latpx(lat):
        # the anchors give 40/50/60 rows; interpolate in meridional parts like the chart
        def MP(f, e2=0.00669438):
            q = math.radians(f)
            return 7915.7045 * math.log10(math.tan(math.pi / 4 + q / 2)) - 3437.7468 * (e2 * math.sin(q) + e2 ** 2 / 3 * math.sin(q) ** 3)
        T = type('T', (), {'MP': staticmethod(MP)})
        y40, y60 = m['anchors']['40'][1], m['anchors']['60'][1]
        return y40 + (T.MP(lat) - T.MP(40)) / (T.MP(60) - T.MP(40)) * (y60 - y40)
    xr = m['W'] - 110 - 120 + 17
    Y.dividers(ch.P(xr, latpx(55)), ch.P(xr, latpx(56)), 0.07, Vector((-0.05, 0, 0)))
    Y.pencil(ch.P(1500, 3900), 30)
    K.camera((0.06, -0.66, 0.80), (0.10, 0.02, 0.0), 34)
    labels = [(up(ch.a('60')), '60°N'), (up(ch.a('50')), '50°N'), (up(ch.a('40')), '40°N'),
              (up(ch.a('b2')), '600 M', 'blue'), (up(ch.a('b1')), '600 M', 'blue')]
    note = 'Mercator: the same 600 M takes more paper further north'
    extra = {'lines': ['Measure on the latitude scale beside the leg']}; expo = -0.1

elif FIG == 2:
    Y.chart_table(1.4, 0.9)
    ch = Y.chart(ART, 'biscay', (0.12, 0.0))
    Y.dividers(ch.a('scale48a'), ch.a('scale48b'), 0.08, Vector((0.05, -0.01, 0)))
    Y.pencil(ch.P(1300, 2300), 160)
    K.camera((0.10, -0.46, 0.66), (0.08, 0.03, 0.0), 32)
    labels = [(up(ch.a('leg')), 'leg along 48°N'), (up(ch.a('scale48'), 0.03), "beside it: 45′ = 45.0 M", 'blue'),
              (up(ch.a('scale42')), "at 42°N: 50.0′", 'red')]
    note = 'Measure on the latitude scale beside the leg'
    extra = {'lines': ['50.0 × cos 48° ÷ cos 42° = 45.0 M']}; expo = -0.1

elif FIG == 3:
    Y.chart_table(1.4, 0.9)
    ch = Y.chart(ART, 'biscay', (0.25, 0.12), rotz=4)
    nb = Y.page(ART, 'midlat', 0.21, (-0.12, -0.10), rotz=-6, z=0.001, cover=M['covergreen'])
    Y.calculator((0.13, -0.17), 10, Y.tex(ART, 'calc-88.7'))
    Y.pencil(nb.P(1700, 2500), 70)
    K.camera((-0.12, -0.25, 0.40), (-0.12, -0.075, 0.0), 32)
    labels = [(up(nb.a('dlat')), "d.lat 76.6′ S"), (up(nb.a('mid')), 'mid-latitude 43°31.7′'),
              (up(nb.a('dr')), "DR 42°53.4′N 009°58.7′W", 'blue')]
    note = 'Mid-latitude sailing: 220°T, 100 M'
    extra = {'lines': ['Departure ÷ cos mid-latitude = d.long']}; expo = -0.1

elif FIG == 4:
    Y.chart_table(1.4, 0.9)
    nor = Y.page(ART, 'nories', 0.21, (-0.17, -0.02), rotz=3, z=0.0, cover=M['cover'])
    nb = Y.page(ART, 'mercsail', 0.21, (0.12, -0.05), rotz=-5, z=0.001, cover=M['covergreen'])
    Y.calculator((0.33, 0.02), -8, Y.tex(ART, 'calc-213'))
    Y.pencil(nb.P(1800, 2400), 60)
    K.camera((-0.03, -0.34, 0.44), (-0.03, -0.03, 0.0), 32)
    labels = [(up(nor.a('4800')), "48°00′: 3274.4"), (up(nor.a('4530')), "45°30′: 3056.1"), (up(nb.a('dmp')), 'DMP 218.3'),
              (up(nb.a('dist')), '213°T, 178.2 M', 'blue')]
    note = 'Mercator sailing: tan C = d.long ÷ DMP'
    extra = {'lines': ['Distance = d.lat ÷ cos C']}; expo = -0.1

elif FIG == 5:
    Y.chart_table(1.4, 0.9)
    ch = Y.chart(ART, 'bank', (0.0, 0.0))
    ep, edge = ch.a('ep'), ch.a('edge')
    uu = (ep - edge).normalized(); off = Vector((uu.y, -uu.x, 0)) * 0.0045
    Y.rule(ART, edge + off, edge + off + uu * 0.3, 0.025)        # its zero level with the 20 m line, its edge just beside the EP
    Y.pencil(ch.P(*ch.meta['anchors']['fix']) + Vector((0.03, 0.02, 0)), 200)
    c = (ep + ch.a('bank')) / 2
    K.camera(tuple(c + Vector((0.03, -0.11, 0.21))), tuple(c + Vector((0.0, 0.005, 0))), 34)
    mid = (ep + edge) / 2
    labels = [(up(ch.a('bank') - (ep - ch.a('bank')) * 0.5, 0.002), 'inside the 20 m contour'), (up(ep, 0.003), 'EP 5 mm off: 0.9 M', 'blue')]
    note = 'Scale 1:350,000: 1 mm is 350 m'
    extra = {'lines': ['Six hours of EP can be out by more than 0.9 M']}; expo = -0.1

elif FIG == 6:
    Y.chart_table(1.4, 0.9)
    ch = Y.chart(ART, 'breton-chart', (0.0, 0.0))
    A0 = ch.a('A'); u = ch.dir(205); n = Vector((-u.y, u.x, 0))       # n: to the left of the track (looking along it)
    cen = A0 + u * 0.20 - n * 0.072                                     # the plotter's edge on the track, to its right
    idx, dc = Y.breton(ART, cen, 205)
    var = dc + Vector((math.sin(deg(211)), math.cos(deg(211)), 0)) * 0.066 + Vector((0, 0, 0.005))
    Y.pencil(ch.P(*ch.meta['anchors']['A']) + Vector((-0.12, 0.06, 0)), -20)
    K.camera(tuple(dc + Vector((0.05, -0.22, 0.30))), tuple(dc + Vector((0.0, 0.02, 0))), 34)
    labels = [(up(A0 + u * 0.04), 'track 205°T'), (up(dc + Vector((-0.02, 0.035, 0)), 0.006), 'grid on the meridians'),
              (up(var, 0.002), '211° at 6°W', 'blue')]
    note = '205°T + 6°W = 211°M'
    extra = {'lines': ['205° at the index, 211° at the 6°W mark']}; expo = -0.1

elif FIG == 7:
    Y.chart_table(1.4, 0.9)
    ch = Y.chart(ART, 'breton-chart', (0.05, -0.10), rotz=-3)
    lb = Y.page(ART, 'log-speed', 0.40, (-0.02, 0.15), rotz=1, z=0.001, cover=M['cover'])
    Y.calculator((0.26, 0.08), -12, Y.tex(ART, 'calc-7.33'))
    Y.clock(Y.tex(ART, 'clock-0415'), (0.32, 0.445, 0.115))
    Y.pencil(lb.P(2600, 1900), 20)
    K.camera((0.03, -0.27, 0.44), (0.06, 0.22, 0.10), 32)
    labels = [(up(lb.a('r2130')), '2130 · log 512.4'), (up(lb.a('r0415')), '0415 · log 561.9'),
              (up(lb.a('speed')), '7.3 kn', 'blue'), ((0.32, 0.44, 0.195), '04:15')]
    note = '49.5 M in 6.75 h: 7.3 kn'
    extra = {'lines': ['Minutes are sixtieths: 45 min is 0.75 h']}; expo = -0.1

elif FIG == 8:
    # a production platform 1.1 km off at night: its deck floodlit, the white Mo(U) light over the middle, red lights
    # at the ends of the deck; the yacht's bow in the foreground
    N.night_scene('breeze', moon=0.004)
    P0 = Vector((0, 1100, 0)); yaw = deg(12)
    R = lambda x, y, z: P0 + Vector((x * math.cos(yaw) - y * math.sin(yaw), x * math.sin(yaw) + y * math.cos(yaw), z))
    steel = C.simple('platform-steel', '#8a8f94', 0.6, 0.4); yel = C.simple('platform-yellow', '#d2a91a', 0.6); grey = C.simple('module', '#a9aeb2', 0.7)
    for lx in (-22, 22):
        for ly in (-16, 16):
            Y.seg('leg', R(lx * 1.15, ly * 1.15, -2), R(lx, ly, 24), 1.4, 1.2, yel, 16)
    for z in (6, 14):
        for (a, b) in (((-22, -16), (22, -16)), ((-22, 16), (22, 16)), ((-22, -16), (-22, 16)), ((22, -16), (22, 16))):
            Y.seg('brace', R(a[0] * 1.1, a[1] * 1.1, z), R(b[0] * 1.1, b[1] * 1.1, z), 0.45, 0.45, yel, 8)
    def box(name, dims, at, mat):
        o = C.obj(name, C.rbox(name, dims, 0.1, 1), mat, R(*at)); o.rotation_euler = (0, 0, yaw); return o
    box('deck1', (54, 40, 2.0), (0, 0, 25), steel); box('deck2', (54, 40, 1.6), (0, 0, 33), steel)
    for i, (dx, dy, w, d_, h) in enumerate(((-14, -6, 18, 22, 6), (6, -4, 16, 26, 9), (18, 8, 12, 14, 7), (-12, 10, 16, 12, 5))):
        box(f'module{i}', (w, d_, h), (dx, dy, 34 + h / 2), grey)
    box('helideck', (20, 20, 0.8), (-24, 14, 45), C.simple('helideck', '#3d6b3a', 0.7))
    Y.seg('helileg', R(-24, 14, 34), R(-24, 14, 45), 0.5, 0.5, steel, 8)
    Y.seg('flareboom', R(28, -8, 34), R(70, -12, 62), 0.8, 0.5, steel, 8)
    fl = A.emit_mat('flare', (1.0, 0.45, 0.12), 8.0); A.sphere('flare', 2.2, fl, R(70.5, -12, 64.5), scale=(0.7, 0.7, 1.5))
    Y.seg('crane', R(10, 6, 43), R(-8, -18, 58), 0.5, 0.35, C.simple('crane', '#c8401c', 0.6), 8)
    for i, (x, y) in enumerate(((-24, -18), (0, -18), (24, -18), (-24, 18), (24, 18), (0, 18), (-27, 0), (27, 0))):
        ld = bpy.data.lights.new(f'flood{i}', 'POINT'); ld.energy = 300; ld.color = (1.0, 0.82, 0.55); ld.shadow_soft_size = 1.0
        lo = bpy.data.objects.new(f'flood{i}', ld); C.col.objects.link(lo); lo.location = R(x, y, 38)
    for i, (x, y) in enumerate(((-26, -19), (26, 19), (26, -19), (-26, 19))):
        ld = bpy.data.lights.new(f'under{i}', 'POINT'); ld.energy = 120; ld.color = (1.0, 0.85, 0.6); lo = bpy.data.objects.new(f'under{i}', ld); C.col.objects.link(lo); lo.location = R(x, y, 23)
    wl = R(6, -4, 34 + 9 + 3.5); A.lamp('mou', wl, 'w', 1.5, 40000, gain=1.3)
    Y.seg('lightmast', R(6, -4, 43), wl, 0.25, 0.25, steel, 8)
    rl, rr = R(-28.5, -2, 27), R(28.5, 2, 27)
    A.lamp('red-w', rl, 'r', 1.1, 8000); A.lamp('red-e', rr, 'r', 1.1, 8000)
    K.camera((0, 0, 2.6), tuple(P0 + Vector((0, 0, 26))), 135)
    labels = [(wl + Vector((0, 0, 3)), 'white Mo(U) 15s'), (rl + Vector((0, 0, 2)), 'red at its ends', 'red')]
    note = 'Platform: white Mo(U), red at its ends'
    extra = {'bloom': 0.9, 'lines': ['In fog it sounds Mo(U) · keep out of its 500 m zone']}; expo = 0.3

elif FIG == 9:
    # dusk: a wind farm, three rows of turbines 900 m apart, the nearest 1.4 km off
    K.sea('breeze', color='#081822', repeat=10)
    K.day_sky(sun_az=250, sun_el=-1.5, strength=0.4)
    white = C.simple('turbine', '#c9cdd0', 0.5); yel = C.simple('tp-yellow', '#e0b012', 0.55)
    tips = []; nacs = []
    for row in range(3):
        for col in range(-3, 4):
            p = Vector((col * 700 + row * 250 - 150, 650 + row * 700, 0))
            C.cyl('tp', 3.2, 3.2, 22, 24, yel, p + Vector((0, 0, 9)))
            C.cyl('deck', 6, 6, 0.6, 24, C.simple('tp-deck', '#7a7d80', 0.6), p + Vector((0, 0, 20)))
            C.cyl('tower', 3.0, 2.0, 95, 24, white, p + Vector((0, 0, 20 + 47.5)))
            hub = p + Vector((0, -6, 117))
            o = C.obj('nacelle', C.rbox('nacelle', (5, 14, 5), 0.8, 2), white, p + Vector((0, 1, 117)))
            A.sphere('hub', 2.4, white, hub)
            a0 = (row * 37 + col * 53) % 120
            for b in range(3):
                t = deg(a0 + b * 120); tip = hub + Vector((math.sin(t) * 75, -0.5, math.cos(t) * 75))
                Y.seg('blade', hub + Vector((math.sin(t) * 2, 0, math.cos(t) * 2)), tip, 1.8, 0.35, white, 10)
            tips.append(p + Vector((0, -3.3, 19.5))); nacs.append(p + Vector((0, 1, 120.0)))
            A.lamp('yel', p + Vector((0, -3.4, 18.5)), 'w', 1.3, 400, gain=0.2)
            bpy.data.objects[-1].active_material = A.emit_mat('yellow-lamp', (1.0, 0.62, 0.05), 6.0) if False else bpy.data.objects[-1].active_material
            A.lamp('avi', p + Vector((0, 1, 120.0)), 'r', 2.0, 0, gain=2.5)
    for o in bpy.data.objects:
        if o.name.startswith('yel') and o.type == 'MESH': o.active_material = A.emit_mat('yellow-lamp', (1.0, 0.5, 0.0), 2.5)
    K.camera((0, 0, 2.6), (-100, 1200, 70), 42)
    ny = min(tips, key=lambda p: p.length); nn = min(nacs, key=lambda p: p.length)
    labels = [(ny + Vector((0, 0, 8)), 'yellow, flashing together'), (nn + Vector((0, 0, 8)), 'red aviation light', 'red')]
    note = 'Wind farm: the yellow lights flash together'
    extra = {'bloom': 0.8, 'lines': ['Check blade-tip height · never anchor among its cables']}; expo = 1.0

elif FIG == 10:
    Y.chart_table(1.4, 0.9)
    ch = Y.chart(ART, 'corrections', (0.30, 0.16))
    nm = Y.page(ART, 'nm', 0.20, (0.24, -0.06), rotz=-8, z=0.001)
    Y.pencil(ch.a('pnotice') + Vector((0.05, -0.06, 0)), 120)
    K.camera((0.08, -0.40, 0.38), (0.08, -0.01, 0.0), 32)
    labels = [(up(ch.a('stamp')), 'last corrected: Week 31'), (up(nm.a('week')), 'now Week 36: apply 32–36', 'blue'),
              (up(ch.a('smallcorr')), 'each one logged in the margin'), (up(ch.a('pnotice')), '(P) notice in pencil')]
    note = 'Corrections before sailing'
    extra = {'lines': ['A New Edition replaces the chart']}; expo = -0.1

elif FIG == 11:
    Y.chart_table(1.4, 0.9, lamp_power=6)
    ch = Y.chart(ART, 'bank', (0.0, -0.05))
    png = Y.tex(ART, 'enc'); an = Y.meta(ART, 'enc') if os.path.exists(os.path.join(Y.outdir(ART), 'tex', 'enc.json')) else {}
    an = json.load(open(os.path.join(Y.outdir(ART), 'tex', 'enc.json')))
    objs, scr = A.plotter(png, (0.0, 0.30, 0.075), tilt=-12, width=0.30, emit=0.9)
    K.camera((0.03, -0.06, 0.30), (0.0, 0.30, 0.17), 40)
    labels = [(A.screen_point(scr, *an['contour']), 'safety contour: 5 m, bold'), (A.screen_point(scr, *an['settings']), 'set to 4.2 m', 'blue')]
    note = 'Safety contour: 2.1 + 0.3 + 0.8 + 1.0 = 4.2 m'
    extra = {'lines': ['The next deeper contour in the cell is drawn bold']}; expo = -0.2

C.render(OUT, SAMPLES, SCALE, expo, labels, note, space='blender', arrows=arrows, extra=extra)
