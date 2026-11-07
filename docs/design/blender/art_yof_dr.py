# Article yachtmaster-offshore/dr, its sixteen figures as Blender renders.
#   1  night: the steering compass lit red, 237 under the lubber line (230 T, 4 W, 3 W)
#   2  the chart and log book: two DR legs, 240 T and 200 T 24.0 M each; 220 T 45.1 M, not 48 M
#   3  drone: port tack, heading 050, the wake trailing to windward: water track 055
#   4  drone: starboard tack, heading 310: water track 305
#   5  the chart: EP from the 0000 fix, leeway then three hours of stream: 236 T 21.9 M
#   6  the chart: one triangle for the whole crossing, the Breton plotter on the water track 352 T
#   7  the helm: steering compass at 351 C behind the wheel
#   8  from the cockpit: the sister yacht 30° on the port bow, her bearing steady at 090 T
#   9  the plotter at the helm: XTE 4.0 NM left of the route
#   10 the chart: the EP with the current used, the fix with the real one, 4.1 M apart toward 285
#   11 drone: the 0300 fix, the DR at 0600, the 0600 fix: the current between them
#   12 the chart: the same triangle, the Breton plotter on the current, 154 T
#   13 drone: close-hauled, water track 48° off the mark's bearing: VMG 4.7 kn
#   14 drone: landfall on a low coast 5 M north of the harbour, then south
#   15 a motor yacht on the plane, 20 kn
#   16 the motor yacht's helm: the fuel page, 15 kn 150 l/h, range 180 M
#   blender --background --factory-startup --python docs/design/blender/art_yof_dr.py -- --fig 1 [--samples 160]
import os, sys, math, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import bpy, bmesh
from mathutils import Vector
import common as C, kit as K, kit_instruments as KI, kit_night as N
import art_checkin_nps_kit as A
import art_yof_nav_kit as Y

ART = 'dr'
arg = C.cli(); FIG = arg('--fig', 1); SAMPLES = arg('--samples', 160); SCALE = arg('--scale', 100)
OUT = arg('--out', os.path.join(Y.outdir(ART), f'{FIG}-3d.jpg'))
deg = math.radians

C.reset()
M = Y.mats()
labels, arrows, note, expo, extra = [], [], None, -0.3, {}

def up(p, dz=0.004): return Vector(p) + Vector((0, 0, dz))
hv = A.hdg_vec

def cockpit(heading, sun_az=230, sun_el=45, sea='breeze', night=False):
    Y.steering_compass(heading, glow=(1.0, 0.08, 0.04) if night else None)
    if night: N.night_scene(sea, moon=0.003); Y.raise_sea(-1.4)
    else: K.sea(sea, center=(0, 0)); K.day_sky(sun_az=sun_az, sun_el=sun_el); Y.raise_sea(-1.4)
    sole = KI.wall('sole', -1.5, 1.5, -1.5, 1.5, 0, K.mats()['teak'])
    sole.data.vertices.foreach_set('co', [-1.2, -1.5, -0.75, 1.2, -1.5, -0.75, 1.2, 1.5, -0.75, -1.2, 1.5, -0.75]); sole.data.update()

def sailing(heading, port_tack, leeway=5):
    """Drone view from astern of a yacht close-hauled in a north wind: heading line, water track to leeward."""
    K.sea('breeze'); K.day_sky(sun_az=150, sun_el=42)
    sails = {'main': True, 'genoa': 'starboard' if port_tack else 'port', 'boom': -10 if port_tack else 10}
    you = A.yacht('you', sails=sails).place(0, 0, heading=heading, heel=14 if port_tack else -14)
    wt = heading + leeway if port_tack else heading - leeway
    w = K.wake(you, 46, 7, 1.1); w.rotation_euler = (0, 0, deg(-(wt - heading)))
    bow = you.world((10.8, 0.13, K.WL)); b0 = Vector((bow.x, bow.y, 0))
    white = A.glow_mat('heading-line', '#f4f1e6', 1.2); yel = A.glow_mat('water-track', '#ffc400', 2.0)
    Y.dashed('heading', tuple(b0), tuple(b0 + hv(heading) * 46), 0.45, white, 3.0, 2.2)
    Y.strip('track', (b0.x, b0.y), tuple(b0 + hv(wt) * 47), 0.5, yel)
    side = 1 if port_tack else -1
    wa = b0 + hv(heading - 30 * side) * 22
    arr = [((wa.x, wa.y + 12, 6.0), (wa.x, wa.y - 2, 6.0), 'blue')]
    h1 = b0 + hv(heading) * 30 + hv(heading - 90 * side) * 6; t1 = b0 + hv(wt) * 44 + hv(wt + 90 * side) * 5
    lab = [((h1.x, h1.y, 1.5), f'heading {heading:03d}°'), ((t1.x, t1.y, 1.5), f'water track {wt:03d}°', 'yellow'), ((wa.x, wa.y + 13, 6.0), 'Wind N', 'blue')]
    mast = you.world((K.MAST.x, K.MAST.y, K.WL))
    A.drone(Vector((mast.x, mast.y, 0)) + hv(heading) * 16, 74, az=heading + 180 + 22 * side, el=36, lens=30)
    return lab, arr

if FIG == 1:
    cockpit(237, night=True, sea='calm')
    K.camera((0.0, -0.36, 0.30), (0, 0.04, -0.01), 40)
    labels = [((0, 0.064, 0.058), '237°C under the lubber line', 'red')]
    note = 'T → M → C: 230°T + 4°W + 3°W = 237°C'
    extra = {'lines': ['And back: 237 − 3 − 4 = 230°T goes on the chart']}; expo = 0.5

elif FIG == 2:
    Y.chart_table(1.45, 0.9)
    ch = Y.chart(ART, 'twolegs', (0.08, 0.06))
    lb = Y.page(ART, 'log-dr', 0.34, (-0.36, -0.28), rotz=8, z=0.001, cover=M['cover'])
    Y.pencil(ch.a('D2') + Vector((0.05, -0.08, 0)), 120)
    c = (ch.a('fix') + ch.a('D2')) / 2 + Vector((-0.05, -0.04, 0))
    K.camera(tuple(c + Vector((0.02, -0.44, 0.52))), tuple(c), 32)
    labels = [(up(ch.a('fix')), '2000 fix'), (up(ch.a('D1')), '2300: altered to 200°T'), (up(ch.a('D2')), '0200 DR: 220°T, 45.1 M', 'blue')]
    note = 'DR: each leg a vector, course and distance'
    extra = {'lines': ['Not 220°T 48 M: add the vectors']}; expo = -0.1

elif FIG == 3:
    labels, arrows = sailing(50, True)
    note = 'Port tack: water track = heading + leeway'

elif FIG == 4:
    labels, arrows = sailing(310, False)
    note = 'Starboard tack: water track = heading − leeway'

elif FIG == 5:
    Y.chart_table(1.4, 0.9)
    ch = Y.chart(ART, 'ep', (0.0, 0.0))
    Y.pencil(ch.a('fix') + Vector((0.04, -0.09, 0)), 140)
    c = (ch.a('fix') + ch.a('EP')) / 2
    K.camera(tuple(c + Vector((0.0, -0.27, 0.36))), tuple(c + Vector((-0.03, -0.01, 0))), 32)
    labels = [(up(ch.a('fix')), '0000 fix'), (up(ch.a('fix').lerp(ch.a('H'), 0.35)), 'heading 250°T'), (up(ch.a('fix').lerp(ch.a('Wt'), 0.75)), 'water track 245°T, 21.0 M'),
              (up(ch.a('Wt')), 'stream 3.5 M toward 165°T', 'blue'), (up(ch.a('EP'), 0.01), '0300 EP')]
    note = 'EP: 236°T, 21.9 M from the fix'
    extra = {'lines': ['Leeway first, then the stream']}; expo = -0.1

elif FIG == 6:
    Y.chart_table(1.45, 0.95)
    ch = Y.chart(ART, 'cts', (0.0, 0.0))
    S, B = ch.a('S'), ch.a('B'); u = (B - S).normalized(); n = Vector((u.y, -u.x, 0))      # n: to the right of S->B
    brg = ch.meta['brgSB']
    idx, dc = Y.breton(ART, (S + B) / 2 + n * 0.072, brg)
    c = (ch.a('A') + B) / 2
    K.camera(tuple(c + Vector((0.20, -0.34, 0.50))), tuple(c + Vector((0.02, 0.0, 0))), 32)
    labels = [(up(ch.a('A').lerp(B, 0.3)), 'track 000°T, 41.6 M'), (up(ch.a('stream')), 'stream 6 M east'), (up(ch.a('arc')), '42 M swung from here'),
              (up(idx, 0.002), 'steer 352°T', 'blue')]
    note = 'One triangle for the whole crossing'
    extra = {'lines': ['Aim off asin(6.0 ÷ 42) = 8°']}; expo = -0.1

elif FIG == 7:
    cockpit(351, 240, 40)
    # the wheel behind the compass
    wm = C.simple('wheel', '#c9ccd0', 0.25, 1.0)
    w = C.obj('wheel', KI._torus(0.42, 0.016), wm, (0, -0.16, -0.30)); w.rotation_euler = (deg(90), 0, 0)
    for k in range(6):
        a = deg(k * 60 + 30); Y.seg('spoke', (0, -0.16, -0.30), (math.sin(a) * 0.41, -0.16, -0.30 + math.cos(a) * 0.41), 0.008, 0.008, wm, 8)
    C.cyl('hub', 0.05, 0.05, 0.06, 24, wm, (0, -0.13, -0.30), (deg(90), 0, 0))
    K.camera((0.0, -0.78, 0.22), (0, 0.04, -0.02), 40)
    labels = [((0, 0.064, 0.058), 'steer 351°C', 'blue')]
    note = '352°T, leeway 4°: 348°T · + 5°W = 353°M · − 2°E = 351°C'

elif FIG == 8:
    # our yacht heading 120 at 10 kn (motor-sailing); the sister 1.4 km off bearing 090, heading 180 under sail
    K.sea('breeze', repeat=10); K.day_sky(sun_az=200, sun_el=40)
    you = A.yacht('you').place(0, 0, heading=120)
    sp = hv(90) * 600
    sis = A.yacht('sister', sails={'main': True, 'genoa': 'port', 'boom': 22}).place(sp.x, sp.y, heading=180, heel=-8)
    K.wake(sis, 30, 6, 0.6)
    eye = you.world((-2.4, 0.9, 4.3)); look = eye + hv(90) * 100 + Vector((0, 0, -2.0))
    K.camera(tuple(eye), tuple(look), 45)
    top = sis.world((K.MAST.x, K.MAST.y, 22.0))
    labels = [(tuple(top + Vector((0, 0, 4))), 'Sister: 180°T, 5 kn'), (tuple(you.world((10.5, 0.13, 4.6))), 'you: 120°T, 10 kn', 'blue')]
    note = 'Her bearing stays 090°T: you will meet'
    extra = {'lines': ['sin A = 5 ÷ 10: steer 30° off her bearing · 2 h 46 min']}

elif FIG == 9:
    cockpit(87, 40, 40)
    an = json.load(open(Y.tex(ART, 'xte').replace('.png', '.json')))
    C.cyl('post', 0.035, 0.04, 0.70, 32, C.simple('post', '#cfd2d4', 0.25, 1.0), (0.34, 0.12, -0.42))
    C.obj('pod', C.rbox('pod', (0.30, 0.13, 0.10), 0.03, 4), K.mats()['dark'], (0.34, 0.12, -0.04))
    objs, scr = A.plotter(Y.tex(ART, 'xte'), (0.34, 0.12, 0.0), tilt=-16, rotz=-14, width=0.26, pod=False)
    K.camera((0.24, -0.20, 0.24), (0.34, 0.12, 0.07), 36)
    labels = [(A.screen_point(scr, *an['xte']), 'XTE 4.0 NM left', 'red'), (A.screen_point(scr, *an['bar']), 'you: 4.0 M left of the route')]
    note = '1 in 60: 4 × 60 ÷ 80 = 3° off track'
    extra = {'lines': ['48 M to go: 4 × 60 ÷ 48 = 5° more · alter 8° to starboard']}; expo = -0.4

elif FIG == 10:
    Y.chart_table(1.4, 0.9)
    ch = Y.chart(ART, 'eperr', (0.0, 0.0))
    Y.pencil(ch.a('fix') + Vector((-0.08, -0.06, 0)), 30)
    c = (ch.a('Wd') + ch.a('EP') + ch.a('fix')) / 3
    K.camera(tuple(c + Vector((0.03, -0.22, 0.27))), tuple(c + Vector((0.0, -0.005, 0))), 32)
    labels = [(up(ch.a('Wd').lerp(ch.a('EP'), 0.3)), 'used: 180° 0.8 kn'), (up(ch.a('Wd').lerp(ch.a('fix'), 0.78)), 'real: 210° 0.8 kn', 'red'), (up(ch.a('EP'), 0.01), '1600 EP'),
              (up(ch.a('fix'), 0.01), 'fix', 'blue')]
    note = 'Current 30° wrong for 10 h: the fix 4.1 M toward 285° from the EP'
    extra = {'lines': ['Log 4% high · helm 2° off: each adds its share']}; expo = -0.1

elif FIG == 11:
    # 1 M = 10 m: the 0300 fix, the DR 180 m east, the 0600 fix 200 m along 100
    K.sea('calm', size=30.0, repeat=14); K.day_sky(sun_az=210, sun_el=45)
    F0 = Vector((-95, 18, 0)); DR = F0 + hv(90) * 180; F6 = F0 + hv(100) * 200
    you = A.yacht('you').place(F6.x - 7 * math.sin(deg(93)), F6.y - 7 * math.cos(deg(93)), heading=93); K.wake(you, 34, 8, 1.2)
    white = A.glow_mat('water', '#f4f1e6', 1.2); red = A.glow_mat('ground', '#c4161c', 0.8); yel = A.glow_mat('spot', '#ffc400', 2.5)
    Y.dashed('water', tuple(F0), tuple(DR), 0.7, white)
    Y.strip('ground', (F0.x, F0.y), tuple(F6 - hv(100) * 14), 0.8, red)
    for p in (F0, DR, F6): Y.ring('spot', p, 3.0, yel)
    arrows = [((DR.x + 4, DR.y - 2, 1.0), (F6.x + 3, F6.y + 6, 1.0), 'blue')]
    labels = [((F0.x, F0.y, 3.0), '0300 fix'), ((DR.x, DR.y, 3.0), 'DR', 'yellow'), ((F6.x + 8, F6.y - 4, 4.0), '0600 fix', 'yellow'),
              (((DR.x + F6.x) / 2 + 14, (DR.y + F6.y) / 2, 2.0), 'current 3.9 M', 'blue'), ((-5, 34, 2.0), 'water 090°T, 18 M'), ((-5, -8, 2.0), 'ground 100°T, 20 M', 'red')]
    A.drone(Vector((0, 0, 0)), 260, az=185, el=55, lens=34)
    note = 'Current = ground − water: set 154°T, 1.3 kn'

elif FIG == 12:
    Y.chart_table(1.4, 0.9)
    ch = Y.chart(ART, 'curfix', (0.0, 0.0))
    D, F6 = ch.a('DR'), ch.a('F6'); u = (F6 - D).normalized(); n = Vector((u.y, -u.x, 0))
    idx, dc = Y.breton(ART, (D + F6) / 2 + u * 0.05 - n * 0.072, 154)
    Y.pencil(ch.a('F0') + Vector((0.02, -0.08, 0)), 100)
    c = (ch.a('F0') + ch.a('F6')) / 2 + Vector((0.05, 0, 0))
    K.camera(tuple(c + Vector((0.0, -0.30, 0.38))), tuple(c), 32)
    labels = [(up(ch.a('water')), 'water 090°T, 18.0 M'), (up(ch.a('ground')), 'ground 100°T, 20.0 M'), (up(ch.a('F0')), '0300 fix'),
              (up(idx, 0.002), 'current 154°T, 3.9 M', 'blue')]
    note = 'Over 3 h: set 154°T, rate 1.3 kn'
    extra = {'lines': ['Heading 093°T, leeway 3° to port: water track 090°T']}; expo = -0.1

elif FIG == 13:
    # the mark dead to windward, north; close-hauled on port tack, water track 048 (heading 043, 5° leeway)
    K.sea('breeze'); K.day_sky(sun_az=150, sun_el=42)
    you = A.yacht('you', sails={'main': True, 'genoa': 'starboard', 'boom': -8}).place(0, 0, heading=43, heel=16)
    w = K.wake(you, 46, 7, 1.1); w.rotation_euler = (0, 0, deg(-5))
    o = Vector((0, -10, 0))
    white = A.glow_mat('course', '#f4f1e6', 1.2); yel = A.glow_mat('wt', '#ffc400', 2.0); blue = A.glow_mat('vmg', '#2a8cff', 1.8)
    Y.dashed('course', tuple(o), tuple(o + hv(0) * 90), 0.5, white, 3.0, 2.2)
    Y.strip('wt', (o.x, o.y), tuple(o + hv(48) * 70), 0.55, yel)
    pv = o + hv(0) * (70 * math.cos(deg(48)))
    Y.strip('vmg', (o.x - 1.5, o.y), (pv.x - 1.5, pv.y), 0.7, blue)
    Y.dashed('proj', tuple(o + hv(48) * 70), tuple(pv), 0.3, white, 1.5, 1.5)
    arrows = [((-22, 40, 6.0), (-22, 26, 6.0), 'blue')]
    A.drone(Vector((6, 24, 0)), 112, az=200, el=52, lens=30)
    e = o + hv(48) * 70
    labels = [((o.x, o.y + 62, 1.5), 'to the mark, 80 M'), ((e.x, e.y, 1.5), 'water track 7.0 kn', 'yellow'), ((pv.x - 4, pv.y - 12, 1.5), 'VMG 4.7 kn', 'blue'),
              ((-22, 42, 6.0), 'Wind', 'blue')]
    note = 'VMG = 7.0 × cos 48° = 4.7 kn'
    extra = {'lines': ['80 M at 4.7 kn: 17 h 05 · from 0600, arrive 2305']}

elif FIG == 14:
    # 1 M = 50 m: a low coast running north-south 600 m east; the harbour on it; you arrive 5 M (250 m) north of it
    K.sea('calm', size=40.0, repeat=14); K.day_sky(sun_az=230, sun_el=28)
    K.coast(distance=600, bearing=90, length=4000, height=14, town=False)
    H0 = Vector((585, -120, 0))
    H0 = Vector((650, -120, 0))
    K.breakwater((H0.x + 40, H0.y + 60), (H0.x - 60, H0.y + 25), 9, 3, light='red'); K.breakwater((H0.x + 40, H0.y - 60), (H0.x - 60, H0.y - 25), 9, 3, light='green')
    you = A.yacht('you').place(470, H0.y + 250, heading=92); K.wake(you, 40, 8, 1.0)
    white = A.glow_mat('track', '#f4f1e6', 1.2); yel = A.glow_mat('turn', '#ffc400', 2.0)
    Y.dashed('track', (-200, H0.y + 250 + 14), (455, H0.y + 250), 0.8, white, 6, 4)
    Y.strip('turn', (505, H0.y + 230), (520, H0.y + 70), 1.0, yel)
    A.drone(Vector((420, H0.y + 120, 0)), 520, az=262, el=42, lens=30)
    labels = [((H0.x - 30, H0.y, 8), 'Harbour'), ((470, H0.y + 250, 8), 'you: 5 M north'), ((512, H0.y + 150, 2), 'turn south', 'yellow'),
              ((150, H0.y + 254, 2), '092°T, 96 M')]
    note = 'Aim off: you know which way to turn'
    extra = {'lines': ['8 M of set, 5 M wanted: 3 × 60 ÷ 96 = 2° south']}; expo = -0.1

elif FIG == 15:
    import q_encounter_props as P
    K.sea('breeze', repeat=10); K.day_sky(sun_az=230, sun_el=35)
    spin, vis = P.motor_yacht((0, 0), 250, 13.0)[:2]      # this model's bow lies opposite to motor_yacht()'s heading
    spin.rotation_euler.y = deg(-3.0); spin.location.z += 0.25
    root = bpy.data.objects.new('wake-ref', None); C.col.objects.link(root)
    root.location = tuple(hv(70) * 6.5); root.rotation_euler = (0, 0, deg(90 - 70))
    K.wake(type('W', (), {'root': root})(), 70, 12, 1.6)
    A.drone(Vector((0, 0, 1.0)), 34, az=150, el=16, lens=40)
    labels = [((0, 0, 3.2), '20 kn: 220 l/h, 11.0 l/M')]
    note = 'Litres per mile = l/h ÷ speed'
    extra = {'lines': ['From 2000 l: 218 M at 12 kn, 182 M at 20 kn']}

elif FIG == 16:
    # the helm console of the motor yacht: the fuel page on the display, wheel and throttles
    K.sea('breeze'); K.day_sky(sun_az=200, sun_el=35); Y.raise_sea(-1.8)
    dash = C.simple('dash', '#1c1f23', 0.6)
    C.obj('console', C.rbox('console', (1.2, 0.5, 0.9), 0.04, 3), dash, (0, 0.25, -0.45))
    top = C.obj('console-top', C.rbox('ctop', (1.2, 0.45, 0.04), 0.02, 3), dash, (0, 0.22, 0.02)); top.rotation_euler = (deg(-22), 0, 0)
    m = Y.meta(ART, 'fuel'); png = Y.tex(ART, 'fuel')
    C.obj('mfd-bezel', C.rbox('mfdb', (0.42, 0.03, 0.27), 0.01, 3), C.simple('bezel', '#0d0e10', 0.3, coat=0.8), (0, 0.28, 0.20)).rotation_euler = (deg(-20), 0, 0)
    scr = A.quad('mfd', 0.39, 0.39 * m['h_px'] / m['w_px'], png, (0, 0.264, 0.205), rot=(deg(70), 0, 0), emit=1.0, rough=0.15)
    wm = C.simple('wheel', '#c9ccd0', 0.25, 1.0)
    wh = C.obj('wheel', KI._torus(0.19, 0.014), C.simple('wheel-rim', '#222428', 0.5), (-0.36, -0.02, 0.02)); wh.rotation_euler = (deg(68), 0, 0)
    for k in range(3):
        a = deg(k * 120 + 90); Y.seg('spoke', (-0.36, -0.02, 0.02), (-0.36 + math.cos(a) * 0.18, -0.02 + math.sin(a) * 0.18 * math.cos(deg(68)), 0.02 + math.sin(a) * 0.18 * math.sin(deg(68))), 0.008, 0.008, wm, 8)
    for dx in (0.36, 0.42):
        Y.seg('throttle', (dx, 0.05, 0.05), (dx, 0.0, 0.17), 0.008, 0.008, wm, 8); A.sphere('knob', 0.02, C.simple('knob', '#111111', 0.4), (dx, 0.0, 0.18))
    bpy.context.view_layer.update()
    sp = lambda k: scr.matrix_world @ Vector(((m['anchors'][k][0] / m['w_px'] - 0.5) * 0.39, (0.5 - m['anchors'][k][1] / m['h_px']) * 0.39 * m['h_px'] / m['w_px'], 0.002))
    K.camera((-0.12, -0.48, 0.50), (0.0, 0.26, 0.19), 34)
    labels = [(sp('flow'), '15 kn: 150 l/h'), (sp('range'), 'range 180 M: short of 200', 'red')]
    note = 'Fast first, then slow'
    extra = {'lines': ['10 h at 15 kn: 150 M, 1500 l · 50 M at 8 kn: 300 l']}; expo = -0.3

C.render(OUT, SAMPLES, SCALE, expo, labels, note, space='blender', arrows=arrows, extra=extra)
