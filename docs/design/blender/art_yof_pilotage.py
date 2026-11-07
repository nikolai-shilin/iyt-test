# Article yachtmaster-offshore/pilotage, its fourteen figures as Blender renders.
#   1  the four stages at the chart table: pilot and tide books, the passage chart with its track, the forecast, the plan
#   2  latest departure: the GRIB on the plotter (model B, front Sat 1200) and the sum in the notebook
#   3  a traffic separation scheme from the air: the lanes, the zone, the precautionary area where ships turn; A crossing
#   4  night orders: the order book under the red chart-table light, the radar glowing behind it
#   5  the pilotage plan page: clearing bearing, wheel-over, abort point, the tide and bridge sums, VTS
#   6  clearing lines at dusk in a swell: the light, its lines to the 2, 5 and 10 m contours, breakers inshore
#   7  port traffic signals at night: three reds in a column on the mole head, the yellow beside the top one
#   8  radar horizon: the Axiom at the wheel, 24 NM range, the cliff painting at the edge, a ship at 19 M
#   9  setting up the radar: gain to a faint speckle, a little sea clutter, rain off, a squall
#   10 clearing range: the VRM at 1.0 M on the screen, the cliff off to starboard, the reef that gives no echo
#   11 ARPA at night: the target's plots, its CPA 2.1 M at 0219; her lights far off on the starboard bow
#   12 GNSS jamming: the track jumping, SOG 41 kn, HDOP 7.8, five satellites
#   13 GNSS lost: the log book with the last fix, the plotter's NO FIX, the radar still painting
#   14 the Dutchman's log: a chip passing marks 18 m apart on a big yacht's side in 5.0 s
#   blender --background --factory-startup --python docs/design/blender/art_yof_pilotage.py -- --fig 1 [--samples 160]
# Textures come from art_yof_pilotage_tex.py into yachtmaster-offshore/pilotage/tex/.
import os, sys, math, random
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import bpy, bmesh
from mathutils import Vector
import common as C, kit as K, kit_instruments as KI, kit_world as KW, kit_night as N
import art_yof_pilotage_kit as A

arg = C.cli(); FIG = arg('--fig', 1); SAMPLES = arg('--samples', 160); SCALE = arg('--scale', 100)
OUT = arg('--out', os.path.join(A.outdir('pilotage'), f'{FIG}-3d.jpg'))
deg = math.radians
T = lambda n: A.tex('pilotage', n); AN = lambda n: A.anchors('pilotage', n)

C.reset()
M = K.mats()
labels, arrows, note, expo, extra = [], [], None, -0.5, {}

def scr(s, name, key, dx=0, dy=0):
    """World point of an anchor of a drawn screen texture."""
    a = AN(name)[key]; return tuple(A.screen_point(s, a[0] + dx, a[1] + dy))

def desk_plotter(png, at=(0.0, 0.26, 0.0), tilt=-12.0, width=0.30, rotz=0.0, emit=0.7):
    """The Axiom standing on its bracket at the back of the chart table."""
    C.obj('bracket', C.rbox('bracket', (width * 0.5, 0.06, 0.04), 0.01, 2), M['dark'], (at[0], at[1], 0.02))
    return A.plotter(png, (at[0], at[1], 0.03), tilt=tilt, width=width, rotz=rotz, emit=emit, pod=False)

if FIG == 1:
    A.chart_table()
    ch = A.quad('chart', 0.80, 0.5333, T('p1-chart'), (-0.13, 0.06, 0.0012), rough=0.85); ca = AN('p1-chart'); cs = ca['size']
    pb = A.book('pilot', 0.15, 0.21, 0.028, T('p1-pilot'), (-0.40, 0.21, 0.0), 14)
    tb = A.book('tides', 0.13, 0.19, 0.018, T('p1-tides'), (-0.27, 0.24, 0.0), -9)
    fc = A.sheet('forecast', 0.21, 0.297, T('p1-forecast'), (0.33, 0.20, 0.0008), rotz=10, curl=0.002)
    pl = A.sheet('plan', 0.21, 0.297, T('p1-plan'), (0.37, -0.10, 0.0016), rotz=-5, curl=0.002); pa = AN('p1-plan'); ps = pa['size']
    A.pencil((0.12, -0.20), 160)
    K.camera((0.0, -0.66, 0.66), (0.0, 0.03, 0.0), 34)
    labels = [(tuple(A.on_sheet(pb, 0.5, 0.75, 0.004)), 'Appraisal: pilot, tides'),
              (tuple(A.px_on(ch, (1380, 1080), cs)), 'Planning: track, waypoints', 'blue'),
              (tuple(A.on_sheet(fc, 0.5, 0.85, 0.004)), 'Execution: latest forecast'),
              (tuple(A.px_on(ch, ca['fix'], cs)), 'Monitoring: fix, compare')]
    note = 'The four stages'; expo = -0.4

elif FIG == 2:
    A.chart_table()
    objs, s = desk_plotter(T('p2-grib'), at=(0.08, 0.26, 0.0))
    nb = A.sheet('note', 0.21, 0.297, T('p2-note'), (-0.13, -0.06, 0.0008), rotz=4, curl=0.002); na = AN('p2-note'); ns = na['size']
    A.pencil((0.06, -0.17), 150)
    K.camera((-0.03, -0.52, 0.46), (0.0, 0.08, 0.08), 32)
    labels = [(scr(s, 'p2-grib', 'front'), 'front: model B Sat 1200', 'red'),
              (tuple(A.px_on(nb, na['crossing'], ns)), '120 M at 8 kn: 15 h'),
              (tuple(A.px_on(nb, na['leave'], ns)), 'leave by Fri 1500', 'blue')]
    note = 'Latest departure'; extra = {'lines': ['Sat 1200 − 6 h − 15 h = Fri 1500']}; expo = -0.4

elif FIG == 3:
    # lanes running E-W: W-going to the north, E-going to the south, the zone between; the precautionary area east
    K.sea('breeze', size=40.0, repeat=26, center=(-100, 0)); K.day_sky(sun_az=200, sun_el=42)
    def band(name, pts, rgba, z=0.18):
        me = bpy.data.meshes.new(name); me.from_pydata([(x, y, z) for x, y in pts], [], [tuple(range(len(pts)))])
        m, nt, b, out = C.new_mat(name)
        tp = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader'); mx.inputs['Fac'].default_value = rgba[3]
        b.inputs['Base Color'].default_value = rgba[:3] + (1,); b.inputs['Roughness'].default_value = 0.6
        nt.links.new(tp.outputs[0], mx.inputs[1]); nt.links.new(b.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], out.inputs['Surface'])
        o = C.obj(name, me, m); o.visible_shadow = False; return o
    band('zone', [(-2600, -100), (450, -100), (450, 100), (-2600, 100)], (0.85, 0.2, 0.55, 0.16))
    PC = Vector((1100, 0, 0)); R = 600
    band('precaution', [(PC.x + R * math.cos(t / 48 * math.tau), R * math.sin(t / 48 * math.tau)) for t in range(48)], (0.85, 0.2, 0.55, 0.10))
    mg = A.glow_mat('tss-mag', '#d23a96', 0.6)
    for yy in (-100, 100): A.dashed('zone-edge', (-2600, yy, 0), (450, yy, 0), 3.0, mg, 40, 26, 0.22)
    for yy in (-500, 500): A.dashed('lane-edge', (-2600, yy, 0), (450, yy, 0), 4.0, mg, 60, 40, 0.22)
    for t in range(0, 48, 2):
        a0, a1 = t / 48 * math.tau, (t + 1) / 48 * math.tau
        A.strip('pa-edge', (PC.x + R * math.cos(a0), R * math.sin(a0)), (PC.x + R * math.cos(a1), R * math.sin(a1)), 3.0, mg, 0.22)
    A.ship((-450, -300), 90, length=150); A.ship((-80, 300), 270, length=150); A.ship((1150, 160), 40, length=150)
    ya = A.sailing('you', 0, 60, -900, -700, heel=-8); ya.root.scale = (2.0,) * 3; K.wake(ya, 50, 9)
    yel = A.glow_mat('course', '#ffc400', 2.0)
    A.dashed('track-a', (-900, -650, 0), (-900, 640, 0), 6.0, yel, 30, 20, 0.3)
    A.ring('spot-b', (1100, -60), 80, yel, z=0.5, k=0.06)
    K.camera((-150, -1900, 2300), (60, -40, 0), 30)
    labels = [((300, 300, 6), 'W-going lane'), ((300, -300, 6), 'E-going lane'), ((300, 0, 6), 'separation zone'),
              ((-900, 0, 10), 'A: cross at right angles', 'blue'), ((1100, -60, 10), 'B: ships turn here', 'red'), ((1100, 520, 10), 'precautionary area')]
    arrows = [((-650, 300, 10), (-850, 300, 10), 'red'), ((-250, -300, 10), (-50, -300, 10), 'red')]
    note = 'Crossing a TSS'; extra = {'lines': ['Steady heading at right angles, clear of where ships alter']}; expo = -0.6

elif FIG == 4:
    A.chart_table(night=True)
    objs, s = desk_plotter(T('p11-arpa'), at=(0.17, 0.26, 0.0), emit=0.9)
    ob = A.sheet('orders', 0.21, 0.297, T('p4-orders'), (-0.10, -0.04, 0.0008), rotz=3, curl=0.002); oa = AN('p4-orders'); os_ = oa['size']
    A.pencil((0.06, -0.19), 150)
    K.camera((-0.06, -0.40, 0.44), (-0.03, 0.05, 0.02), 36)
    labels = [(tuple(A.px_on(ob, oa['fix'], os_)), 'fix every 30 min offshore'),
              (tuple(A.px_on(ob, oa['call'], os_)), 'call me: CPA under 1 M', 'red'),
              (tuple(A.px_on(ob, oa['alarm'], os_)), 'watch alarm on', 'blue')]
    note = 'Night orders'; extra = {'lines': ['Within 3 M of a danger: a fix every 6 min', 'Close quarters: act first, then call']}; expo = 0.9

elif FIG == 5:
    A.chart_table()
    pg = A.sheet('pilotage-plan', 0.42, 0.297, T('p5-plan'), (-0.05, 0.02, 0.0008), rotz=-2, curl=0.002); pa = AN('p5-plan'); ps = pa['size']
    A.pencil((0.24, -0.17), 160)
    K.camera((-0.04, -0.33, 0.42), (-0.05, 0.03, 0.0), 36)
    labels = [(tuple(A.px_on(pg, pa['clearing'], ps)), 'clearing bearing', 'red'), (tuple(A.px_on(pg, pa['wheel'], ps)), 'wheel-over point', 'blue'),
              (tuple(A.px_on(pg, pa['abort'], ps)), 'abort point', 'red'), (tuple(A.px_on(pg, (pa['notes'][0], pa['notes'][1] - 40), ps)), 'tide and bridge sums')]
    note = 'In the plan'; extra = {'lines': ['VTS: name, position, intention, ETA; then listen']}; expo = -0.4

elif FIG == 6:
    s = 10.0; P = A.drawing(s)
    polys = [[P(*A.extend(p)) for p in poly] for poly in A.path_polys('M0 0 H120 C116 30 108 50 100 60 C92 80 70 130 50 200 H0 Z')]
    h = A.land(polys, (-3800, -2600, 2200, 2800), 16.0, relief=70, hill=260, beach=6, cliff=8)
    A.scrub(h, (-3000, -1500, -400, 2400), 900, minh=6, size=(4, 8))
    K.sea('fresh', size=60.0, res=10, repeat=26, center=(300, -300), color='#0d2a36')
    K.day_sky(sun_az=280, sun_el=6, strength=0.25, haze=3.2)
    L = Vector((*P(104, 58), 0)); lt = A.lighthouse((L.x - 25, L.y + 15), max(1.0, h(L.x - 25, L.y + 15)), 16, 2.2, lit=8.0)
    # breakers: the swell breaking along the shallows inside the 2 m and 5 m lines
    shore = [P(*q) for q in A.path_polys('M100 60 C92 80 70 130 50 200')[0]]
    random.seed(3)
    for i, (x, y) in enumerate(shore[:-1]):
        nx_, ny_ = shore[i + 1][1] - y, -(shore[i + 1][0] - x); n = math.hypot(nx_, ny_) or 1; nx_, ny_ = -nx_ / n, -ny_ / n
        for k, (off, rx) in enumerate(((60, 110), (190, 80))):
            A.foam(f'break{i}-{k}', (x + nx_ * off + random.uniform(-20, 20), y + ny_ * off), rx * 1.2, 45, rot=math.degrees(math.atan2(ny_, nx_)) + 90, z=1.4, density=1.0 - 0.2 * k, scale=0.12, emit=0.5)
    wh = A.glow_mat('clear-ab', '#f4f1e6', 1.4); rd = A.glow_mat('clear-c', '#e0301e', 2.2)
    ends = {'A': P(118, 180), 'B': P(169, 180), 'C': P(229, 180)}
    for k, e in ends.items(): A.dashed('line-' + k, (L.x, L.y, 0), (e[0], e[1], 0), 7.0 if k == 'C' else 5.0, rd if k == 'C' else wh, 40, 26, 0.6)
    you = A.sailing('you', 320, 250, *P(262, 172), reef=0.4, heel=-12); K.wake(you, 40, 8, 1.0)
    A.drone(Vector((250, -380, 0)), 2350, az=146, el=29, lens=30)
    labels = [((lt.x, lt.y, lt.z + 20), 'light'), ((*P(124, 168), 4), 'A · 2 m'), ((*P(172, 168), 4), 'B · 5 m'), ((*P(226, 164), 4), 'C · 10 m: keep seaward', 'red'),
              (tuple(you.world((K.MAST.x, K.MAST.y, 22))), 'You · light 306°', 'blue')]
    note = 'Night, swell: keep seaward of C'; extra = {'lines': ['Light bearing 314° or less: outside the 10 m line'], 'bloom': 0.6}; expo = -0.3

elif FIG == 7:
    # the harbour entrance to the north at night; the signal mast on the west mole head
    N.night_scene('calm', moon=0.003)
    C.obj('hills', C.rbox('hills', (5000, 400, 70), 8.0, 2), C.simple('night-hills', '#0d0f12', 0.9), (0, 1150, 30))
    KW.mole((-260, 520), (-45, 330), width=9.0, light=False); KW.mole((260, 520), (45, 330), width=9.0, light=False)
    rnd = random.Random(5)
    for k in range(60):                                         # the town's lights
        x, y = rnd.uniform(-900, 900), rnd.uniform(930, 960)
        N.light(f'town{k}', (x, y, rnd.uniform(4, 30)), rnd.choice(('white', 'yellow')), strength=6.0, power=0.0, radius=1.2)
    mast = Vector((-45, 330, 2.2))
    C.cyl('sig-mast', 0.25, 0.25, 12, 12, M['dark'], (mast.x, mast.y, mast.z + 6))
    C.obj('sig-board', C.rbox('board', (2.4, 0.3, 5.2), 0.1, 2), C.simple('board', '#14171a', 0.6), (mast.x - 0.4, mast.y - 0.4, mast.z + 9.6))
    for i, z in enumerate((11.4, 9.6, 7.8)): A.lamp(f'sig-red{i}', (mast.x, mast.y - 1.0, mast.z + z), 'r', 0.42, power=25.0, gain=1.2)
    A.sphere('sig-yellow', 0.42, A.emit_mat('sig-yellow', (1.0, 0.55, 0.02), 1.2), (mast.x - 1.3, mast.y - 1.0, mast.z + 11.4))
    N.light('mole-e', (45, 330, 8.0), 'green', strength=20.0, power=20.0, radius=0.4)
    K.camera((mast.x + 40, mast.y - 95, 3.0), (mast.x + 4, mast.y, mast.z + 7.5), 120)
    labels = [((mast.x, mast.y - 0.6, mast.z + 7.8), 'three reds: no entry', 'red'), ((mast.x - 1.3, mast.y - 0.6, mast.z + 11.4), 'yellow: named craft only', 'yellow')]
    note = 'Port traffic signals'; extra = {'lines': ['Hold off outside; VTS names who may proceed'], 'bloom': 0.6}; expo = 0.5

elif FIG == 8:
    you, s = A.helm(T('p8-radar'))
    labels = [(scr(s, 'p8-radar', 'cliff'), 'cliff 64 m: paints at 24 M', 'blue'), (scr(s, 'p8-radar', 'ship'), "ship's bridge 30 m: 19 M")]
    note = 'Radar horizon: scanner 9 m, cliff 64 m'; extra = {'lines': ['2.2 × (√9 + √64) = 2.2 × 11 = 24 M']}; expo = -0.4

elif FIG == 9:
    you, s = A.helm(T('p9-radar'), sky=lambda: A.cloud_sky('#46688d', '#9fb2c2', '#4a5058', '#9aa1a8', cover=0.45, scale=2.4, boost=(300, 60, 0.6, 0.6), sun=(150, 30, 2.2)))
    labels = [(scr(s, 'p9-radar', 'gain'), 'gain: a faint speckle', 'blue'), (scr(s, 'p9-radar', 'clutter', 0, 40), 'sea clutter: a little left')]
    note = 'Setting up the picture'; extra = {'lines': ['Rain control only to look into a squall', 'Long scale to warn, short for small craft']}; expo = -0.2

elif FIG == 10:
    you, s = A.helm(T('p10-radar'), cam=('view', 42, -11, 18, (-1.95, -0.10, 5.12)))
    A.land([[(1960, -4000), (5000, -4000), (5000, 4000), (1960, 4000)]], (1700, -4200, 4200, 4200), 24.0, relief=160, hill=200, beach=2, cliff=70, seed=5.0)
    A.foam('reef', (1960 - 1110, 280), 110, 45, z=0.6, density=0.9, scale=0.15)
    labels = [(scr(s, 'p10-radar', 'vrm'), 'VRM 1.0 M', 'blue'), ((1990, 2400, 150), 'cliff: keep it outside 1.0 M'), ((850, 280, 3), 'reef 0.6 M off: no echo', 'red')]
    note = 'Clearing range'; extra = {'lines': ['Reef 0.6 M + margin 0.4 M = VRM 1.0 M']}; expo = -0.4

elif FIG == 11:
    you, s = A.helm(T('p11-arpa'), state='calm', night=True, cam=('view', 6, -15, 20, (-1.85, -0.31, 5.1)))
    # her lights 3.9 M off, 11° on the starboard bow, crossing to port: masthead lights and her red sidelight
    d = 3.9 * 1852; b = deg(11); bx, by = d * math.sin(b), d * math.cos(b)
    N.light('her-mast1', (bx - 40, by, 28), 'white', strength=40.0, power=0.0, radius=9.0)
    N.light('her-mast2', (bx + 30, by, 38), 'white', strength=40.0, power=0.0, radius=9.0)
    N.light('her-red', (bx - 10, by, 14), 'red', strength=60.0, power=0.0, radius=9.0)
    labels = [(scr(s, 'p11-arpa', 'p1'), '0206 · 191° 3.9 M'), 
              (scr(s, 'p11-arpa', 'box'), 'CPA 2.1 M at 0219', 'blue'), ((bx, by, 60), 'her lights')]
    note = 'Relative plot · own 180°T 9 kn'; extra = {'lines': ['3.2 M to the CPA at 15 kn relative: 13 min'], 'bloom': 0.8}; expo = 0.4

elif FIG == 12:
    you, s = A.helm(T('p12-gnss'))
    labels = [(scr(s, 'p12-gnss', 'sog'), 'SOG 41 kn: impossible', 'red'), (scr(s, 'p12-gnss', 'track'), 'position jumping', 'red'),
              (scr(s, 'p12-gnss', 'hdop'), 'HDOP 7.8 · 5 satellites')]
    note = 'Jamming: radar, log and compass steady'; extra = {'lines': ['Go by radar ranges, depth and DR']}; expo = -0.4

elif FIG == 13:
    A.chart_table()
    objs, s = desk_plotter(T('p13-nofix'), at=(0.15, 0.24, 0.0), width=0.36)
    lg = A.sheet('log', 0.42, 0.297, T('p13-log'), (-0.14, -0.06, 0.0008), rotz=2, curl=0.002); la = AN('p13-log'); ls = la['size']
    A.pencil((0.12, -0.24), 165)
    K.camera((-0.02, -0.56, 0.50), (0.02, 0.08, 0.10), 34)
    labels = [(tuple(A.px_on(lg, la['lost'], ls)), 'last fix, time and log', 'red'), (scr(s, 'p13-nofix', 'nofix'), 'NO FIX', 'red'),
              (scr(s, 'p13-nofix', 'radar'), 'radar still paints', 'blue')]
    note = 'GNSS lost: start a DR'; extra = {'lines': ['Still good: radar, compass, log, sounder']}; expo = -0.4

elif FIG == 14:
    # a 20 m yacht (the 49 scaled up) on starboard tack, the chip drifting aft past her side; marks 18 m apart
    K.sea('calm', size=30.0, repeat=10); K.day_sky(sun_az=210, sun_el=40)
    k = 1.35
    you = A.sailing('you', 90, 30, 0, 0, heel=-8, scale=k); K.wake(you, 40, 8, 0.8)
    yl = A.glow_mat('mark', '#ffc400', 2.0)
    fwd, aft = you.world((9.6, -1.0, 3.4)), you.world((9.6 - 18 / k, -1.65, 3.4))
    for nm, p in (('m1', fwd), ('m2', aft)): C.cyl('mark-' + nm, 0.11, 0.11, 1.8, 16, yl, (p.x, p.y, p.z + 0.9))
    side = (aft - you.world((9.6 - 18 / k, 0.13, 3.4))).normalized(); side.z = 0
    chip = Vector((aft.x, aft.y, 0)) + side * 3.0
    C.obj('chip', C.rbox('chip', (0.35, 0.22, 0.1), 0.02, 2), C.simple('chip-wood', '#c58b4a', 0.7), (chip.x, chip.y, 0.25))
    A.ring('chip-ring', (chip.x, chip.y), 1.1, yl, z=0.3, k=0.1)
    c0 = Vector((fwd.x, fwd.y, 0)) + side * 3.0
    A.dashed('run', c0, chip - (chip - c0).normalized() * 1.3, 0.25, A.glow_mat('run', '#f4f1e6', 1.2), 1.2, 0.8, 0.3)
    mid = (c0 + chip) / 2
    A.drone(Vector((mid.x, mid.y, 2)), 46, az=200, el=32, lens=32)
    labels = [((fwd.x, fwd.y, fwd.z + 1.6), 'mark 1 · 0 s'), ((aft.x, aft.y, aft.z + 1.6), 'mark 2 · 5.0 s', 'blue'),
              ((chip.x, chip.y, 0.6), 'chip'), ((mid.x, mid.y, 0.4), '18 m', 'yellow')]
    note = "Dutchman's log: 18 m in 5.0 s"; extra = {'lines': ['3.6 m/s × 3,600 ÷ 1,852 = 7.0 kn, through the water']}; expo = -0.5

C.render(OUT, SAMPLES, SCALE, expo, labels, note, space='blender', arrows=arrows, extra=extra)
