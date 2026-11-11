# Article yachtmaster-offshore/tides, its eleven figures as Blender renders.
#   1  a harbour wall's tide gauge at 1100: the water at 2.0 m, HW 5.6 m due at 1500
#   2  the almanac's secondary-port differences with the pencilled interpolation: HW 0840, 4.8 m
#   3  the plotter's tide page for Southampton: LW 1000 0.6 m, the long double high water, the cursor at 1400 3.3 m
#   4  over the bank: a cut-away at the waterline, tide, charted depth, draught, the keel's lowest in a trough
#   5  a bridge on a surge tide at dusk: the masthead 0.7 m under the span
#   6  a river bar with the swell breaking on it, our yacht waiting outside for the flood
#   7  the tidal stream atlas, the arrow marked 18,34 ringed, today's rate pencilled
#   8  two yachts crossing one beam stream: the slow one set far, the fast one hardly
#   9  a headland with a race breaking downstream of it, the E-going stream
#   10 the same headland from above: A the inshore passage, B the race, C outside
#   11 an ocean plotting sheet: the 30 h DR, the EP 12 M NE of it, the current arrows
#   blender --background --factory-startup --python docs/design/blender/art_yof_tides.py -- --fig 1 [--samples 160]
import os, sys, math, random
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import bpy, bmesh
from mathutils import Vector
import common as C, kit as K, kit_instruments as KI, kit_world as KW
import art_yof_pilotage_kit as A

arg = C.cli(); FIG = arg('--fig', 1); SAMPLES = arg('--samples', 160); SCALE = arg('--scale', 100)
OUT = arg('--out', os.path.join(A.outdir('tides'), f'{FIG}-3d.jpg'))
deg = math.radians
T = lambda n: A.tex('tides', n); AN = lambda n: A.anchors('tides', n)

C.reset()
M = K.mats()
labels, arrows, note, expo, extra = [], [], None, -0.5, {}

def scr(s, name, key):
    a = AN(name)[key]; return tuple(A.screen_point(s, a[0], a[1]))

def quay_mat(hw=5.8):
    """Granite blocks, weed and wet below the high-water mark, pale and dry above it."""
    m, nt, b, _ = C.new_mat('quay-wall')
    oc = C.obj_coords(nt); sep = C.node(nt, 'ShaderNodeSeparateXYZ'); C.link(nt, oc, sep.inputs['Vector'])
    n1 = C.noise(nt, oc, 3.0, 6.0); n2 = C.noise(nt, oc, 40.0, 4.0)
    zt = C.math_(nt, 'ADD', sep.outputs['Z'], C.math_(nt, 'MULTIPLY', n1, 0.35))
    band = C.ramp(nt, [(0.0, '#1b2416'), (0.40, '#2c3a22'), (0.62, '#3b392f'), (0.80, '#4f4a3f'), (0.86, '#8f897d'), (1.0, '#9a948a')])
    zn = C.math_(nt, 'DIVIDE', C.math_(nt, 'ADD', zt, 1.0), hw + 2.0); C.link(nt, zn, band.inputs['Fac'])
    st = C.ramp(nt, [(0.3, (0.82, 0.82, 0.82, 1)), (0.7, (1, 1, 1, 1))]); C.link(nt, n2, st.inputs['Fac'])
    C.link(nt, C.mixc(nt, 1.0, band.outputs['Color'], st.outputs['Color'], 'MULTIPLY'), b.inputs['Base Color'])
    wet = C.math_(nt, 'LESS_THAN', zt, hw)
    rr = C.node(nt, 'ShaderNodeMix', data_type='FLOAT'); C.link(nt, wet, rr.inputs['Factor']); C.setin(rr, 2, 0.88); C.setin(rr, 3, 0.5); C.link(nt, rr.outputs[0], b.inputs['Roughness'])
    C.bump_from(nt, b, n2, 0.6, 0.004)
    return m

def dashes_under(p0, p1, z, mat, name, dash=0.7, gap=0.45, w=0.06):
    p0, p1 = Vector(p0), Vector(p1); d = p1 - p0; L = d.length; u = d / L; s = 0.0
    while s < L:
        e = min(s + dash, L); a, b = p0 + u * s, p0 + u * e; c = (a + b) / 2
        o = C.obj(name, C.rbox(name, ((b - a).length, w, w), 0.0, 1), mat, (c.x, c.y, z)); o.rotation_euler = (0, 0, math.atan2(u.y, u.x)); s = e + gap

if FIG == 1:
    WATER = 2.0
    C.obj('quay', C.rbox('quay', (40, 3.0, 10.5), 0.02, 2), quay_mat(), (0, 1.5, 2.75))
    C.obj('cope', C.rbox('cope', (40, 0.6, 0.25), 0.04, 3), C.concrete_mat('cope'), (0, 0.25, 8.12))
    jm = C.simple('joint', '#2e2b26', 0.95)
    for zz in (0.0, 0.9, 1.8, 2.7, 3.6, 4.5, 5.4, 6.3, 7.2):
        C.obj('course', C.rbox('course', (40, 0.02, 0.025), 0.0, 1), jm, (0, -0.005, zz))
    staff = A.quad('staff', 0.15, 7.4, T('t1-staff'), (0, -0.012, 3.5), rot=(deg(90), 0, 0), rough=0.5)
    C.obj('staff-back', C.rbox('sb', (0.17, 0.01, 7.42), 0.002, 1), C.simple('staff-back', '#d9d9d0', 0.6), (0, -0.006, 3.5))
    K.sea('calm', size=30.0, repeat=10); A.moved_sea(WATER)
    K.day_sky(sun_az=150, sun_el=38)
    y = A.yacht('moored').place(16.5, -2.15, heading=270); y.root.location.z = WATER
    for zz in [i * 0.3 + 0.2 for i in range(26)]: C.cyl('rung', 0.012, 0.012, 0.42, 10, M['galv'], (-3.5, -0.08, zz), (0, deg(90), 0))
    for xx in (-3.71, -3.29): C.cyl('rail', 0.016, 0.016, 8.0, 10, M['galv'], (xx, -0.08, 4.2))
    K.camera((-7.5, -10.5, 3.3), (1.5, 0, 3.0), 28)
    labels = [((0.0, -0.03, WATER), '1100 · 2.0 m', 'red'), ((0.0, -0.03, 5.6), 'HW 1500 · 5.6 m', 'blue')]
    note = 'LW 0900 0.8 m · HW 1500 5.6 m'; extra = {'lines': ['HW−4: factor 0.25 · 0.8 + 0.25 × 4.8 = 2.0 m']}; expo = -0.5

elif FIG == 2:
    A.chart_table()
    pg = A.sheet('almanac', 0.21, 0.297, T('t2-almanac'), (-0.05, -0.02, 0.0008), rotz=-3, curl=0.002); pa = AN('t2-almanac'); ps = pa['size']
    A.book('tides', 0.15, 0.21, 0.025, A.tex('pilotage', 'p1-tides'), (-0.34, 0.12, 0.0), 12)
    A.pencil((0.17, -0.12), 140)
    K.camera((-0.02, -0.40, 0.42), (-0.04, 0.0, 0.0), 36)
    labels = [(tuple(A.px_on(pg, pa['timediff'], ps)), 'time diffs −0030, −0010'), (tuple(A.px_on(pg, pa['hw'], ps)), 'HW 0840', 'blue'),
              (tuple(A.px_on(pg, pa['height'], ps)), 'HW 4.8 m', 'blue')]
    note = 'Secondary port: high water'; extra = {'lines': ['Standard port HW 0900 · 5.2 m: both halfway']}; expo = -0.4

elif FIG == 3:
    you, s = A.helm(T('t3-tide'))
    labels = [(scr(s, 't3-tide', 'cursor'), '1400 · 3.3 m', 'blue'), (scr(s, 't3-tide', 'lw'), 'LW 1000 · 0.6 m'), (scr(s, 't3-tide', 'stand'), 'double high water')]
    note = 'Hours from LW: a Solent curve'; extra = {'lines': ['LW+4: 0.6 + 0.75 × 3.6 = 3.3 m']}; expo = -0.4

elif FIG == 4:
    TIDE, CHART, DRAFT, LOW = 1.2, 5.4, 2.2, 1.3          # LOW: half the swell 1.0 + squat 0.3
    DEPTH = TIDE + CHART
    y = A.yacht('you').place(0, 0, heading=0).set_draft(DRAFT)
    KW.antifoul_hull(y); bpy.context.view_layer.update()
    keel = [o for o in y.objs if o.type == 'MESH' and not o.hide_render and K.bbox([o])[0].z < -DRAFT + 0.15]
    klo, khi = K.bbox(keel); kb = Vector(((klo.x + khi.x) / 2, (klo.y + khi.y) / 2, klo.z))
    KW.water_body(depth=10.0, size=700.0, density=0.035, color='#0f4a4f', absorb='#3aa79b', reflect=0.25, absorb_density=0.04)
    KW.far_sea_ring(inner=350.0)
    KW.seabed(z=-DEPTH, size=160.0, res=220, center=(0, 10), seed=9, colors=('#9a9a7c', '#bdb895', '#aeab89'))
    KW.stones(60, ((-25, -20), (30, 45)), -DEPTH, scale=(0.15, 0.5)); KW.seagrass(((-30, -25), (40, 50)), -DEPTH, clumps=900, length=0.5)
    K.coast(distance=1500, bearing=270, height=60, town=False)
    K.day_sky(sun_az=120, sun_el=55, strength=0.25, haze=2.0)
    dashes_under((3.0, -12.0, 0), (3.0, 26.0, 0), -TIDE, A.emit_mat('datum', (1.0, 0.75, 0.05), 3.0), 'datum')
    dashes_under((2.2, kb.y - 6, 0), (2.2, kb.y + 10, 0), -DRAFT - LOW, A.emit_mat('trough', (1.0, 0.08, 0.04), 3.0), 'trough')
    KW.camera(Vector((30.0, 3.5, 0.002)), Vector((0.0, 4.0, -2.6)), lens=30)
    g1, g2, g3 = Vector((3.4, kb.y - 7.0, 0)), Vector((3.4, kb.y + 1.2, 0)), Vector((3.4, kb.y + 9.5, 0))
    labels = [((g1.x, g1.y - 1.0, -1.0), 'draught 2.2 m', 'yellow'), ((g2.x, g2.y + 1.0, -DRAFT - LOW - 0.1), '½ swell 1.0 + squat 0.3', 'red'),
              ((g2.x, g2.y + 1.0, -DRAFT - LOW - 1.9), '3.1 m under the keel'),
              ((g3.x, g3.y + 1.0, -0.15), 'tide +1.2 m', 'blue'), ((g3.x, g3.y + 1.0, -TIDE - 3.2), 'charted 5.4 m', 'green'),
              ((3.0, 24.0, -TIDE + 0.15), 'chart datum')]
    mid = lambda a, b: (a + b) / 2
    arrows = [((g1.x, g1.y, -1.1), (g1.x, g1.y, -0.03), 'yellow'), ((g1.x, g1.y, -1.1), (g1.x, g1.y, -DRAFT + 0.03), 'yellow'),
              ((g2.x, g2.y, mid(-DRAFT, -DRAFT - LOW)), (g2.x, g2.y, -DRAFT - 0.02), 'red'), ((g2.x, g2.y, mid(-DRAFT, -DRAFT - LOW)), (g2.x, g2.y, -DRAFT - LOW + 0.02), 'red'),
              ((g3.x, g3.y, -TIDE / 2), (g3.x, g3.y, -0.03), 'blue'), ((g3.x, g3.y, -TIDE / 2), (g3.x, g3.y, -TIDE + 0.03), 'blue'),
              ((g3.x, g3.y, -TIDE - CHART / 2), (g3.x, g3.y, -TIDE - 0.03), 'green'), ((g3.x, g3.y, -TIDE - CHART / 2), (g3.x, g3.y, -DEPTH + 0.03), 'green')]
    note = 'In the troughs: 5.4 + 1.2 − 1.0 − 0.3 − 2.2'; extra = {'lines': ['= 3.1 m under the keel']}; expo = -0.55

elif FIG == 5:
    # the river runs N-S under a bridge spanning E-W; the water at HW tonight, 14.9 m under the span
    ROOM = 14.9; k = 14.2 / 18.9
    K.sea('calm', size=30.0, repeat=12, center=(0, 0), color='#13303a')
    K.day_sky(sun_az=265, sun_el=3.0, strength=0.25, haze=3.0)
    con = C.concrete_mat('bridge')
    C.obj('deck', C.rbox('deck', (260, 12, 2.4), 0.2, 2), con, (0, 0, ROOM + 1.2))
    C.obj('parapet-s', C.rbox('par', (260, 0.4, 1.2), 0.05, 1), con, (0, -5.8, ROOM + 3.0)); C.obj('parapet-n', C.rbox('par', (260, 0.4, 1.2), 0.05, 1), con, (0, 5.8, ROOM + 3.0))
    for x in (-38, 38, -115, 115): C.obj('pier', C.rbox('pier', (5, 10, ROOM + 8), 0.3, 2), con, (x, 0, (ROOM - 8) / 2))
    for x0 in (-170, 170): C.obj('bank', C.rbox('bank', (90, 600, 12), 1.0, 2), KW.land_mat(), (x0, 0, 0.5))
    you = A.yacht('you'); you.root.scale = (k,) * 3; you.place(0, -2.0, heading=0); K.wake(you, 30, 6, 0.6)
    top = you.world((K.MAST.x, K.MAST.y, 20.9))
    for i in range(14): A.lamp(f'deck-lamp{i}', (-130 + i * 20, -6.2, ROOM + 4.4), 'w', 0.18, power=60.0, gain=0.5)
    K.camera((48, -34, 7.0), (0, -2, 9.5), 32)
    gx = 6.0
    arrows = [((gx, -6.5, ROOM / 2), (gx, -6.5, 0.15), 'blue'), ((gx, -6.5, ROOM / 2), (gx, -6.5, ROOM - 0.05), 'blue')]
    labels = [((gx, -6.5, ROOM * 0.45), 'room 14.9 m', 'blue'), ((top.x, top.y, top.z), '0.7 m to spare', 'red'), ((top.x - 0.6, top.y - 2.0, 3.0), 'air draught 14.2 m')]
    note = 'Bridge on a surge: HW tonight 6.1 m'; extra = {'lines': ['15.0 + 6.0 − 6.1 = 14.9 m · air draught 14.2 m'], 'bloom': 0.5}; expo = 0.0

elif FIG in (6, 9, 10):
    if FIG == 6:
        s = 4.0; P = A.drawing(s); path = 'M0 0 H128 V84 H0 Z M192 0 H320 V84 H192 Z'
    else:
        s = 6.0; P = A.drawing(s); path = 'M110 0 H210 V10 C205 50 185 80 165 95 C150 85 130 55 115 20 Z'
    polys = [[P(*A.extend(p, 260)) for p in poly] for poly in A.path_polys(path)]
    box = (P(-260, 0)[0], P(0, 360)[1], P(580, 0)[0], P(0, -260)[1])
    h = A.land(polys, box, 8.0 if FIG == 6 else 10.0, relief=30 if FIG == 6 else 70, hill=90 if FIG == 6 else 140, beach=8 if FIG == 6 else 3, cliff=0 if FIG == 6 else 10)
    A.scrub(h, box, 900, minh=4, size=(2.5, 5) if FIG == 6 else (3, 6))
    random.seed(FIG)
    if FIG == 6:
        K.sea('fresh', size=48.0, res=10, repeat=14, center=P(160, 140), color='#123642')
        K.day_sky(sun_az=230, sun_el=35, haze=2.2)
        for i in range(16):        # the swell breaking along the bar
            x = random.uniform(112, 208); A.foam(f'bar{i}', P(x, random.uniform(108, 120)), random.uniform(18, 36), random.uniform(5, 9), rot=random.uniform(-8, 8), density=0.8, scale=0.2)
        A.foam('bar-wide', P(160, 114), 210, 20, density=0.45, scale=0.12)
        you = A.yacht('you').place(*P(160, 176), heading=0); K.wake(you, 20, 6, 0.4)
        A.drone(Vector((*P(160, 120), 0)), 560, az=150, el=34, lens=30)
        labels = [((*P(160, 112), 4), 'bar 0.4 m: breaks under 2.6 m', 'red'), ((*P(160, 50), 3), 'river'),
                  (tuple(you.world((K.MAST.x, K.MAST.y, 21))), 'You: wait for 2.2 m of tide', 'blue')]
        note = 'Swell 2.0 m on the bar'; extra = {'lines': ['Charted 0.4 m + tide 2.2 m = 2.6 m: cross on the flood']}; expo = -0.5
    else:
        K.sea('breeze', size=40.0, res=10, repeat=26, center=P(170, 120), color='#0f3442')
        K.day_sky(sun_az=210, sun_el=40, haze=2.0)
        rc = P(222, 120) if FIG == 9 else P(176, 136)
        for i in range(26):        # the race: steep breaking water downstream (east) of the point
            a = random.uniform(0, math.tau); r = random.uniform(0, 1) ** 0.6
            c = (rc[0] + math.cos(a) * r * 190, rc[1] + math.sin(a) * r * 90)
            A.foam(f'race{i}', c, random.uniform(14, 34), random.uniform(5, 10), rot=random.uniform(-30, 30) + 90, density=0.85, scale=0.25)
        A.foam('race-wide', rc, 240, 110, density=0.35, scale=0.1)
        if FIG == 9:
            you = A.sailing('you', 90, 200, *P(40, 150), heel=6); K.wake(you, 40, 8, 1.0)
            A.drone(Vector((*P(160, 110), 0)), 1500, az=220, el=24, lens=30)
            arrows = [((*P(40, 104), 6), (*P(110, 104), 6), 'blue')]
            labels = [((*P(160, 40), h(*P(160, 40)) + 10), 'headland'), ((*P(222, 112), 8), 'race: downstream of the point', 'red'),
                      ((*P(40, 104), 8), 'E-going stream', 'blue'), (tuple(you.world((K.MAST.x, K.MAST.y, 21))), 'You', 'blue')]
            note = 'The race lies downstream'; extra = {'lines': ['Here E and SE of the point; it moves W when the stream turns']}; expo = -0.5
        else:
            yl = A.glow_mat('spot', '#ffc400', 2.5)
            for L_, (x, y) in zip('ABC', ((166, 110), (170, 136), (168, 166))): A.ring('spot-' + L_, P(x, y), 34, yl, z=0.5, k=0.07)
            A.drone(Vector((*P(170, 120), 0)), 1500, az=180, el=56, lens=30)
            arrows = [((*P(60, 150), 8), (*P(115, 150), 8), 'blue')]
            labels = [((*P(166, 110), 6), 'A · inshore passage'), ((*P(170, 136), 6), 'B · the race', 'red'), ((*P(168, 166), 6), 'C · outside: the default', 'blue'),
                      ((*P(60, 150), 8), 'Wind W', 'blue')]
            note = 'Rounding a headland with a race'; extra = {'lines': ['A: settled weather, neaps, daylight · C otherwise']}; expo = -0.5

elif FIG == 7:
    A.chart_table()
    pg = A.sheet('atlas', 0.42, 0.297, T('t7-atlas'), (-0.04, 0.02, 0.0008), rotz=-2, curl=0.002); pa = AN('t7-atlas'); ps = pa['size']
    A.book('tides', 0.15, 0.21, 0.025, A.tex('pilotage', 'p1-tides'), (0.36, 0.18, 0.0), -10)
    A.pencil((0.25, -0.18), 150)
    K.camera((0.0, -0.46, 0.50), (-0.03, 0.03, 0.0), 36)
    labels = [(tuple(A.px_on(pg, pa['arrow'], ps)), '18,34: 1.8 kn neaps, 3.4 springs'), (tuple(A.px_on(pg, pa['today'], ps)), 'today, range 4.2 m: 2.6 kn', 'blue')]
    note = 'Rate for today'; extra = {'lines': ['Ranges: springs 5.6 m, neaps 2.8 m · 1.8 + ½ × 1.6 = 2.6 kn']}; expo = -0.4

elif FIG == 8:
    # A to B 30 M north (10 m to the mile here), a 2 kn stream setting east: the slow yacht set 10 M, the fast one 3 M
    K.sea('breeze', size=40.0, repeat=14, center=(30, 150)); K.day_sky(sun_az=200, sun_el=45)
    wh = A.glow_mat('course', '#f4f1e6', 1.3); rd = A.glow_mat('slow', '#e0301e', 1.6); bl = A.glow_mat('fast', '#1d8ad6', 1.6); yl = A.glow_mat('spot', '#ffc400', 2.5)
    A.dashed('course', (0, 0, 0), (0, 300, 0), 1.2, wh, 8, 6, 0.3)
    A.strip('slow-track', (0, 0), (100, 300), 2.6, rd, 0.3); A.strip('fast-track', (0, 0), (30, 300), 2.6, bl, 0.3)
    for L_, p in (('A', (0, 0)), ('B', (0, 300))): A.ring('spot-' + L_, p, 9, yl, z=0.5, k=0.08)
    slow = A.sailing('slow', 0, 290, 40, 120, heel=10); K.wake(slow, 30, 6, 0.8)
    root, vis = A.ship((22, 220), 0, model='vessel-motor-yacht.glb')
    A.drone(Vector((40, 150, 0)), 470, az=95, el=60, lens=32)
    arrows = [((-90, 60, 6), (-40, 60, 6), 'blue'), ((-90, 200, 6), (-40, 200, 6), 'blue')]
    labels = [((40, 120, 18), '6 kn: 5 h, set 10 M', 'red'), ((22, 220, 10), '20 kn: 1 h 30, set 3 M', 'blue'), ((-40, 60, 6), 'stream 2 kn', 'blue'),
              ((0, -8, 3), 'A'), ((0, 308, 3), 'B')]
    note = 'Two yachts, one stream: leg 30 M'; extra = {'lines': ['Set = rate × time in the stream: the slow yacht is set further']}; expo = -0.5

elif FIG == 11:
    A.chart_table()
    ch = A.quad('sheet', 0.80, 0.5333, T('t11-sheet'), (-0.05, 0.05, 0.0012), rough=0.85); ca = AN('t11-sheet'); cs = ca['size']
    A.dividers(A.px_on(ch, ca['dr'], cs), A.px_on(ch, ca['ep'], cs), lift=0.07, side=Vector((-0.05, -0.06, 0)))
    A.pencil((0.25, -0.20), 160)
    K.camera((0.02, -0.56, 0.58), (0.0, 0.05, 0.0), 34)
    labels = [(tuple(A.px_on(ch, ca['dr'], cs)), 'DR after 30 h'), (tuple(A.px_on(ch, ca['ep'], cs)), 'EP: 12 M NE', 'blue'), (tuple(A.px_on(ch, ca['cur'], cs)), 'mean current NE 0.4 kn')]
    note = 'Current in the DR'; extra = {'lines': ['30 h × 0.4 kn = 12 M · the tidal streams cancel out']}; expo = -0.4

C.render(OUT, SAMPLES, SCALE, expo, labels, note, space='blender', arrows=arrows, extra=extra)
