# Article yachtmaster-offshore/compass, its ten figures as Blender renders.
#   1  the pedestal steering compass, 248 under the lubber line (245 T + 3 W)
#   2  the chart's compass rose: its variation note 4°10'W 2016 (8'E), the pencilled 2026 value 2°50'W
#   3  the steering compass at 165 C, the sun low on the port bow: by the compass 119 C, tabled 122 M
#   4  the steering compass at 248 C beside a satellite compass head reading 240 T
#   5  the chart: two radar ranges swung as arcs with a pencil compass, crossing at X and Y; the EBL picks X
#   6  drone view: a four-point bearing, the light 45° on the bow at 0100 and abeam at 0130, 8 M off = the run
#   7  the chart: running fix with stream, the 0100 line moved along the ground run with a parallel rule
#   8  night, a heavy swell: a light just on the horizon, seen only from the crests
#   9  a lighthouse on its cliff 4 M off: 40 m above MHWS, the water 3.0 m below MHWS
#   10 the chart: one position line from the light, the EP beside it, the point nearest the EP
#   blender --background --factory-startup --python docs/design/blender/art_yof_compass.py -- --fig 1 [--samples 160]
import os, sys, math, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import bpy, bmesh
from mathutils import Vector
import common as C, kit as K, kit_instruments as KI, kit_night as N
import art_checkin_nps_kit as A
import art_yof_nav_kit as Y

ART = 'compass'
arg = C.cli(); FIG = arg('--fig', 1); SAMPLES = arg('--samples', 160); SCALE = arg('--scale', 100)
OUT = arg('--out', os.path.join(Y.outdir(ART), f'{FIG}-3d.jpg'))
deg = math.radians

C.reset()
M = Y.mats()
labels, arrows, note, expo, extra = [], [], None, -0.3, {}

def up(p, dz=0.004): return Vector(p) + Vector((0, 0, dz))

def cockpit(heading, sun_az=230, sun_el=45, sea='breeze'):
    """The compass on its pedestal in the cockpit, bow towards +Y, the teak sole 0.75 m below, the sea beyond."""
    Y.steering_compass(heading)
    K.sea(sea, center=(0, 0)); K.day_sky(sun_az=sun_az, sun_el=sun_el); Y.raise_sea(-1.4)
    sole = KI.wall('sole', -1.5, 1.5, -1.5, 1.5, 0, K.mats()['teak'])
    sole.data.vertices.foreach_set('co', [-1.2, -1.5, -0.75, 1.2, -1.5, -0.75, 1.2, 1.5, -0.75, -1.2, 1.5, -0.75]); sole.data.update()

if FIG == 1:
    cockpit(248, 200, 50)
    K.camera((0.0, -0.40, 0.34), (0, 0.04, -0.02), 40)
    labels = [((0, 0.064, 0.058), '248° under the lubber line', 'blue')]
    note = '245°T + 3°W = 248°M'
    extra = {'lines': ['The lubber line parallel to the fore-and-aft line']}

elif FIG == 2:
    Y.chart_table(1.4, 0.9)
    ch = Y.chart(ART, 'rose-var', (0.0, 0.0))
    Y.pencil(ch.a('pencil') + Vector((0.11, -0.03, 0)), 150)
    c = ch.a('rose')
    rc = (ch.a('var') + ch.a('pencil')) / 2
    K.camera(tuple(rc + Vector((0.0, -0.24, 0.30))), tuple(rc + Vector((0, 0.0, 0))), 34)
    labels = [(up(ch.a('var')), "4°10′W 2016 (8′E)"), (up(ch.a('pencil')), "2026: 2°50′W", 'blue')]
    note = '10 years × 8′E = 1°20′ less westerly'
    extra = {'lines': ["Old chart 1°30′W 2010 (9′E): now 0°54′E"]}; expo = -0.1

elif FIG == 3:
    # true heading 164 (165 C + 3 E dev - 4 W var): the sun at 118 T is 46° on the port bow, 12° up
    cockpit(165, sun_az=-46, sun_el=4, sea='breeze')
    K.camera((0.10, -0.44, 0.17), (-0.20, 0.30, 0.10), 24)
    sun = Vector((math.sin(deg(-46)) * math.cos(deg(4)), math.cos(deg(-46)) * math.cos(deg(4)), math.sin(deg(4)))) * 60
    labels = [((0, 0.064, 0.058), '165°C under the lubber line'), (tuple(sun + Vector((0, 0, 1.5))), 'sun: 119°C by the compass', 'blue')]
    note = 'Tabled 122°M, by the compass 119°C: deviation 3°E'
    extra = {'lines': ['Azimuth 118°T + 4°W = 122°M · reading low: easterly']}; expo = -0.6

elif FIG == 4:
    cockpit(248, 210, 45)
    # a satellite compass head on a small pod to starboard of the compass, facing aft
    pod = Vector((0.20, 0.06, -0.03))
    C.cyl('post', 0.03, 0.035, 0.70, 32, C.simple('post', '#cfd2d4', 0.25, 1.0), tuple(pod + Vector((0, 0, -0.38))))
    C.obj('podbox', C.rbox('podbox', (0.16, 0.06, 0.16), 0.02, 3), M['dark'], tuple(pod + Vector((0, 0.02, 0.02))))
    C.obj('bezel', C.rbox('bezel', (0.135, 0.02, 0.135), 0.008, 3), C.simple('bezel', '#121314', 0.3, coat=0.8), tuple(pod + Vector((0, -0.012, 0.02))))
    A.quad('lcd', 0.112, 0.112, Y.tex(ART, 'lcd-sat'), tuple(pod + Vector((0, -0.0225, 0.02))), rot=(deg(90), 0, 0), emit=0.9, rough=0.15)
    K.camera((0.06, -0.45, 0.30), (0.09, 0.05, 0.0), 36)
    labels = [((0, 0.064, 0.058), 'compass 248°C'), (tuple(pod + Vector((0, -0.02, 0.10))), 'satellite compass 240°T', 'blue')]
    note = '240°T + 3°W = 243°M: deviation 5°W'
    extra = {'lines': ['The compass reads 248°C: 5° high on this heading']}

elif FIG == 5:
    Y.chart_table(1.4, 0.9)
    ch = Y.chart(ART, 'radar-chart', (0.0, 0.0))
    m = ch.meta; B = ch.a('B'); X = ch.a('X')
    # the pencil compass swinging B's arc through X
    rB = m['rB']; brg = math.degrees(math.atan2(m['anchors']['X'][0] - m['anchors']['B'][0], -(m['anchors']['X'][1] - m['anchors']['B'][1]))) - 16
    pt = ch.P(m['anchors']['B'][0] + math.sin(deg(brg)) * rB, m['anchors']['B'][1] - math.cos(deg(brg)) * rB)
    Y.drawing_compass(B, pt, 0.11)
    c = (ch.a('A') + ch.a('B')) / 2
    K.camera(tuple(c + Vector((0.02, -0.30, 0.36))), tuple(c + Vector((0.0, 0.0, 0))), 32)
    labels = [(up(ch.a('A')), 'A: 9.3 M'), (up(ch.a('B'), 0.03), 'B: 7.8 M'), (up(X), 'X: the fix', 'blue'), (up(ch.a('Y')), 'Y', 'red'),
              (up(ch.a('ebl')), 'EBL on A ≈ 333°T')]
    note = 'Two radar ranges: the arcs cross twice'
    extra = {'lines': ['Even a rough bearing picks X']}; expo = -0.1

elif FIG == 6:
    # 8 M shrunk to 175 m: the light on its islet at (0, 175); the 0100 position 175 m west of abeam; heading 090
    K.sea('breeze', size=40.0, repeat=14); K.day_sky(sun_az=210, sun_el=45)
    L = Vector((0, 175, 0))
    Y.headland((0, 190), (60, 42, 22), seed=3)
    lamp = Y.lighthouse((0, 180), 14.0, 18.0, 2.2)
    you = A.yacht('you').place(-6, 0, heading=90); K.wake(you, 40, 8, 1.1)
    white = A.glow_mat('track', '#f4f1e6', 1.2); yel = A.glow_mat('brg', '#ffc400', 2.0); blue = A.glow_mat('abeam', '#2a8cff', 1.6)
    P0 = Vector((-175, 0, 0))
    Y.dashed('track', (-270, 0), (60, 0), 0.9, white, 5, 4)
    Y.strip('brg45', (P0.x, P0.y), (L.x - 9, L.y - 9), 0.9, yel)
    Y.strip('abeam', (0, 8), (0, L.y - 14), 0.9, blue)
    Y.ring('p0', (P0.x, P0.y), 4.0, yel); Y.ring('p1', (0, 0), 4.0, yel)
    A.drone(Vector((-85, 85, 0)), 380, az=180, el=62, lens=31)
    labels = [((P0.x, P0.y, 4), '0100: light 45° on the bow'), ((0, -6, 7), '0130: abeam'), ((-92, -2, 2), 'run 8 M'),
              ((2, 95, 2), '8 M off', 'blue'), (tuple(lamp + Vector((0, 0, 6))), 'Light')]
    note = 'Four-point bearing: abeam, the distance off equals the run'

elif FIG == 7:
    Y.chart_table(1.4, 0.9)
    ch = Y.chart(ART, 'runfix', (0.0, 0.0))
    F = ch.a('fix'); u = ch.dir(50)
    Y.dividers(ch.a('Wt'), ch.a('G'), 0.09, Vector((0.03, -0.02, 0)))
    Y.pencil(ch.a('G') + Vector((0.06, -0.10, 0)), 120)
    c = (ch.a('P0') + ch.a('fix') + ch.a('L')) / 3
    K.camera(tuple(c + Vector((0.0, -0.30, 0.38))), tuple(c + Vector((0, -0.01, 0))), 32)
    labels = [(up(ch.a('pl1')), '0100 line 050°T'), (up(ch.a('pl3')), '0300 line 330°T'), (up(ch.a('P0').lerp(ch.a('fix'), 0.4)), 'ground 087°T 16.1 M'),
              (up(F), 'fix', 'blue')]
    note = 'Running fix: the 0100 line moved 16.1 M along 087°T'
    extra = {'lines': ['Ground run = water track + stream, added as vectors']}; expo = -0.1

elif FIG == 8:
    # night, a long swell; our eye 4 m up; the light 17.8 M off is on the horizon: shown here just over a crest
    # late twilight: the swell still shows against the last light in the west
    K.sea(None, wind=16, wave_scale=1.6, chop=1.1, size=140, repeat=10, color='#06121a', foam=False)
    K.day_sky(sun_az=300, sun_el=-4.0, strength=0.3)
    lp = Vector((-60, 2600, 0.4))
    A.lamp('rising', lp, 'w', 4.0, 0, gain=2.0)
    K.camera((0, 0, 4.0), (-30, 1400, 2.0), 50)
    labels = [(tuple(lp + Vector((0, 0, 10))), 'light on the horizon')]
    note = 'Seen only from the crests: you stand at its rising range'
    extra = {'bloom': 1.2, 'lines': ['Rising range 2.08 × (√H + √h): 43 m and 4 m give 17.8 M']}; expo = 1.2

elif FIG == 9:
    # the headland 4 M off, compressed: cliff, MHWS line on the rock, the water 3.0 m below it, the light 40 m above MHWS
    K.sea('calm', size=40.0, repeat=10); K.day_sky(sun_az=230, sun_el=30)
    D = 2400.0
    Y.headland((0, D + 160), (330, 100, 50), seed=8, z_frac=0.12)
    rock = C.granite_mat('cliff', base='#57504a', per_object=False, scale=0.6, dark='#2c2824', light='#7d7366', dirt=True)
    cliff = C.obj("cliff", C.rbox("cliff", (100, 50, 31), 2.0, 3), rock, (0, D, 15.5))
    wet = C.simple('weed', '#2d2a1f', 0.85)
    C.obj('wetband', C.rbox('wetband', (101, 51, 3.0), 0.2, 1), wet, (0, D - 0.4, 1.5))
    lamp = Y.lighthouse((10, D + 8), 31.0, 11.0, 1.6)      # lantern at 43 m above the water now (40 above MHWS)
    K.camera((-30, 0, 4), (0, D, 20), 300)
    labels = [(tuple(lamp + Vector((0, 0, 3))), 'light 40 m above MHWS'), ((-42, D - 25, 3.2), 'MHWS'), ((38, D - 25, 0.3), 'water now 3.0 m lower', 'blue')]
    note = 'Vertical sextant angle 0°20.0′ of the 43 m: 4.0 M off'
    extra = {'lines': ['1.854 × 43 ÷ 20.0 = 4.0 M · tide added to H']}

elif FIG == 10:
    Y.chart_table(1.4, 0.9)
    ch = Y.chart(ART, 'oneline', (0.0, 0.0))
    Ld = ch.a('L'); u = ch.dir(200)
    Y.pencil(ch.a('EP') + Vector((0.09, -0.02, 0)), 170)
    c = (ch.a('L') + ch.a('EP')) / 2
    K.camera(tuple(c + Vector((0.04, -0.22, 0.30))), tuple(c + Vector((0.0, -0.02, 0))), 32)
    labels = [(up(ch.a('line')), 'light bears 020°T'), (up(ch.a('EP')), 'EP'), (up(ch.a('Q')), 'here', 'blue')]
    note = 'One position line only'
    extra = {'lines': ['Put yourself on the line at the point nearest the EP']}; expo = -0.1

C.render(OUT, SAMPLES, SCALE, expo, labels, note, space='blender', arrows=arrows, extra=extra)
