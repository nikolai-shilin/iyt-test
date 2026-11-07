# Article yachtmaster-offshore/weather, its twelve figures as Blender renders.
#   1  under a high to the north: fair-weather sky, wind ENE, our yacht running west
#   2  southern hemisphere, a low to the south: overcast to the south, WNW wind, reefed
#   3  a depression from space: the cloud spiral and its frontal band, moving NE; veer on its right, back on its left
#   4  the radiofax analysis on the chart table: main low 968, a secondary 994 at the triple point
#   5  a cold front's cloud wall on the western horizon, our yacht heading west towards it
#   6  the fax with the geostrophic scale, dividers on the isobar spacing, the working pencilled
#   7  the barometer on the bulkhead: 995 now, the set hand at 1005 three hours ago
#   8  a long ocean swell, 400 m from crest to crest, our yacht on its back
#   9  steep breaking seas over the shelf edge before a gale
#   10 making an offing: beating out to sea away from a lee shore as the gale builds
#   11 a high island in the NE trade wind: whitecaps off its flanks, a glassy wind shadow in its lee
#   12 a cumulonimbus cell to the NE, its rain shaft; our yacht reefed, heading east
#   blender --background --factory-startup --python docs/design/blender/art_yof_weather.py -- --fig 1 [--samples 160]
import os, sys, math, random
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import bpy, bmesh
from mathutils import Vector, noise as mnoise
import common as C, kit as K, kit_instruments as KI, kit_world as KW
import art_yof_pilotage_kit as A

arg = C.cli(); FIG = arg('--fig', 1); SAMPLES = arg('--samples', 160); SCALE = arg('--scale', 100)
OUT = arg('--out', os.path.join(A.outdir('weather'), f'{FIG}-3d.jpg'))
deg = math.radians
T = lambda n: A.tex('weather', n); AN = lambda n: A.anchors('weather', n)

C.reset()
M = K.mats()
labels, arrows, note, expo, extra = [], [], None, -0.5, {}

def wind_arrow(frm, c, L=24.0, z=8.0):
    """An overlay arrow blowing from bearing `frm` through the point c (x, y)."""
    dx, dy = math.sin(deg(frm)), math.cos(deg(frm))
    return ((c[0] + dx * L / 2, c[1] + dy * L / 2, z), (c[0] - dx * L / 2, c[1] - dy * L / 2, z), 'blue')

def swell_sea(L=400.0, amp=2.2, size=3000.0, step=6.0, dir_=0.0, color='#0b2c3a', chop=0.35):
    """A long swell: a mesh of sines (wavelength L along bearing dir_) with a short chop on it, the kit's sea material."""
    n = int(size / step); bm = bmesh.new(); V = []
    a = deg(dir_); ux, uy = math.sin(a), math.cos(a)
    for j in range(n + 1):
        for i in range(n + 1):
            x, y = -size / 2 + i * step, -size / 2 + j * step; s = x * ux + y * uy
            z = amp * math.sin(math.tau * s / L) + 0.25 * amp * math.sin(math.tau * s / (L * 0.47) + 1.3) + chop * mnoise.noise(Vector((x * 0.05, y * 0.05, 1.0)))
            V.append(bm.verts.new((x, y, z)))
    for j in range(n):
        for i in range(n):
            k = j * (n + 1) + i; f = bm.faces.new((V[k], V[k + 1], V[k + n + 2], V[k + n + 1])); f.smooth = True
    me = bpy.data.meshes.new('swell'); bm.to_mesh(me); bm.free()
    m = K.sea_mat(color, False); bs = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'); bs.inputs['Roughness'].default_value = 0.22
    o = C.obj('swell', me, m)
    far = bpy.data.meshes.new('far-sea'); far.from_pydata([(-9000, -9000, 0), (9000, -9000, 0), (9000, 9000, 0), (-9000, 9000, 0)], [], [(0, 1, 2, 3)])
    C.obj('far-sea', far, K.sea_mat(color, False, far=True), (0, 0, -4.0))
    return lambda x, y: amp * math.sin(math.tau * (x * ux + y * uy) / L) + 0.25 * amp * math.sin(math.tau * (x * ux + y * uy) / (L * 0.47) + 1.3)

def flat_patch(name, pts, z=0.55, color='#0b2c3a'):
    """A glassy patch of water (a wind shadow) laid over the waves."""
    me = bpy.data.meshes.new(name); me.from_pydata([(x, y, 0) for x, y in pts], [], [tuple(range(len(pts)))])
    m = K.sea_mat(color, False, far=True); o = C.obj(name, me, m, (0, 0, z)); o.visible_shadow = False
    return o

if FIG == 1:
    # a high to the north: fair-weather cumulus, a moderate ENE breeze, running west
    A.cloud_sky('#2c67a8', '#b6cbdb', '#9aa3ad', '#f4f5f6', cover=0.18, sharp=0.08, scale=3.4, sun=(160, 50, 3.4), haze=0.08, shade_scale=2.0)
    K.sea('breeze', repeat=10)
    y = A.sailing('you', 270, 67.5, 0, 0); K.wake(y, 40, 8, 1.0)
    A.drone(Vector((0, 0, 6)), 40, az=160, el=13, lens=30)
    arrows = [wind_arrow(67.5, (12, 10), 22, 9)]
    labels = [((12 + 11 * math.sin(deg(67.5)), 10 + 11 * math.cos(deg(67.5)), 10.5), 'Wind ENE', 'blue'), (tuple(A.compass(10, 1.2, 3000)), 'the high: to the north')]
    note = 'High north of you: wind ENE'; extra = {'lines': ['Clockwise round a high, slightly outwards']}; expo = -0.1

elif FIG == 2:
    # southern hemisphere, a low to the south: overcast heaped up southwards, WNW 6, reefed on a reach north
    A.cloud_sky('#59626b', '#8d949b', '#3e444b', '#6f767d', cover=0.85, sharp=0.4, scale=1.4, boost=(180, 70, 0.6, 0.8), sun=(20, 30, 1.4), haze=0.1, shade_scale=1.8)
    sea = K.sea(wind=14.0, wave_scale=0.75, chop=1.8, size=60.0, res=11, repeat=8, color='#20363e'); sea.modifiers['ocean'].foam_coverage = 0.3
    y = A.sailing('you', 0, 292.5, 0, 0, reef=0.5, heel=-18)
    A.drone(Vector((0, 2, 7)), 40, az=25, el=11, lens=28)
    arrows = [wind_arrow(292.5, (-14, 8), 22, 9)]
    labels = [((-14 + 11 * math.sin(deg(292.5)), 8 + 11 * math.cos(deg(292.5)), 10.5), 'Wind WNW', 'blue'), (tuple(A.compass(228, 0.4, 3000)), 'the low: to the south', 'red')]
    note = 'Southern hemisphere: low to the south'; extra = {'lines': ['Clockwise round a low: north of it the wind is WNW']}; expo = 0.4

elif FIG == 3:
    # the North Atlantic from orbit: the ocean, the depression's cloud on a plane above it, the sun from the south
    me = bpy.data.meshes.new('ocean'); me.from_pydata([(-3000, -3000, 0), (3000, -3000, 0), (3000, 3000, 0), (-3000, 3000, 0)], [], [(0, 1, 2, 3)])
    oc = C.obj('ocean', me, C.simple('ocean-deep', '#0b1f3a', 0.35))
    cl = A.quad('cloud', 2600, 2600, T('w3-sat'), (0, 0, 30), rough=0.9)
    m = cl.active_material; nt = m.node_tree; bs = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'); tx = next(n for n in nt.nodes if n.type == 'TEX_IMAGE')
    nt.links.new(tx.outputs['Alpha'], bs.inputs['Alpha'])
    K.day_sky(sun_az=170, sun_el=55, strength=0.3)
    cam = K.camera((0, -900, 3600), (0, -80, 0), 36)
    an = AN('w3-sat'); c = Vector(((an['centre'][0] / 2048 - 0.5) * 2600, (0.5 - an['centre'][1] / 2048) * 2600, 40))
    t = Vector((math.sin(deg(45)), math.cos(deg(45)), 0))
    arrows = [(tuple(c), tuple(c + t * 900), 'red')]
    labels = [(tuple(c), 'Low moving NE'), (tuple(c + Vector((600, -500, 0))), 'right of the track: veers, stronger', 'red'), (tuple(c + Vector((-760, 120, 0))), 'left: backs, lighter', 'blue')]
    note = 'Northern hemisphere · a low moving NE'; extra = {'lines': ['On the right its motion adds to its wind']}; expo = -0.3

elif FIG == 4:
    A.chart_table()
    fx = A.quad('fax', 0.70, 0.496, T('w4-fax'), (-0.06, 0.06, 0.0012), rough=0.85); fa = AN('w4-fax'); fs = fa['size']
    A.pencil((0.26, -0.21), 160)
    K.camera((-0.02, -0.52, 0.56), (-0.04, 0.05, 0.0), 34)
    labels = [(tuple(A.px_on(fx, fa['main'], fs)), 'main low 968'), (tuple(A.px_on(fx, fa['secondary'], fs)), 'secondary 994', 'blue'),
              (tuple(A.px_on(fx, fa['oppose'], fs)), 'winds oppose'), (tuple(A.px_on(fx, fa['strongest'], fs)), 'winds add: strongest', 'red')]
    note = 'Secondary low at the triple point'; extra = {'lines': ['Northern hemisphere · secondary SE of the main low']}; expo = -0.4

elif FIG == 5:
    # morning, heading west: the cold front's wall low on the western horizon, the sun behind us
    A.cloud_sky('#3a6c9c', '#aebfcc', '#6a7179', '#c9ced3', cover=0.15, sharp=0.2, scale=2.4, sun=(95, 25, 3.0), haze=0.05, wall=(270, 70, 0.14, '#262b31'))
    K.sea('breeze', repeat=10)
    y = A.sailing('you', 270, 200, 0, 0, heel=-8); K.wake(y, 40, 8, 1.0)
    A.drone(Vector((-10, 0, 11)), 40, az=110, el=8, lens=26)
    labels = [(tuple(A.compass(300, 3.0, 2500)), 'cold front, 25 kn E', 'red'), (tuple(y.world((K.MAST.x, K.MAST.y, 12))), 'You: W at 5 kn', 'blue')]
    note = 'Cold front 120 M W'; extra = {'lines': ['Closing 25 + 5 = 30 kn: 120 ÷ 30 = 4 h · reef before then']}; expo = 0.1

elif FIG == 6:
    A.chart_table()
    fx = A.quad('fax', 0.70, 0.496, T('w6-fax'), (-0.06, 0.06, 0.0012), rough=0.85); fa = AN('w6-fax'); fs = fa['size']
    A.dividers(A.px_on(fx, fa['p0'], fs), A.px_on(fx, fa['p1'], fs), lift=0.07, side=Vector((-0.03, -0.07, 0)))
    K.camera((0.0, -0.50, 0.55), (-0.02, 0.05, 0.0), 34)
    labels = [(tuple(A.px_on(fx, fa['p1'], fs)), 'isobar spacing'), (tuple(A.px_on(fx, fa['scale'], fs)), 'geostrophic scale: 40 kn', 'blue'),
              (tuple(A.px_on(fx, (fa['work'][0], fa['work'][1] - 60), fs)), 'at the sea: 27 kn from 255°', 'red')]
    note = 'Wind from the isobars'; extra = {'lines': ['Curved round a low −15 %, at the sea × 0.8, backed 15°']}; expo = -0.4

elif FIG == 7:
    # the bulkhead by the chart table: the barometer, its needle at 995, the brass set hand left at 1005 at 0900
    jo = KI.joinery_mat()
    KI.wall('bulkhead', -1.0, 1.0, -0.6, 0.8, 0.0, jo)
    C.obj('table', C.rbox('table', (1.2, 0.6, 0.04), 0.006, 2), jo, (0.0, -0.32, -0.42))
    K.day_sky(sun_az=200, sun_el=40, strength=0.05)
    KI.area_light((0.4, -0.8, 0.5), (0.0, 0.0, 0.1), 10, 0.5, (1.0, 0.92, 0.8)); KI.area_light((-0.7, -0.6, 0.2), (0, 0, 0.1), 5, 0.4, (0.85, 0.92, 1.0))
    at = Vector((0.0, -0.02, 0.15)); r = 0.11; brass = C.simple('brass', '#b08a3e', 0.25, 1.0)
    C.obj('case', KI._cyl_y(r * 1.12, 0.035), brass, at + Vector((0, 0.0, 0)))
    KI.disc('dial', r, KI.image_mat('dial', T('w7-dial'), 0.5), at + Vector((0, -0.019, 0)))
    ring = C.obj('bezel', KI._torus(r * 1.08, r * 0.07), brass, at + Vector((0, -0.022, 0))); ring.rotation_euler = (deg(90), 0, 0)
    def hand(name, p, mat, w, L, y):
        piv = bpy.data.objects.new(name + '-pivot', None); C.col.objects.link(piv); piv.location = at + Vector((0, y, 0))
        o = C.obj(name, C.rbox(name, (w, 0.0015, L), 0.0005, 1), mat, (0, 0, L * 0.38)); o.parent = piv
        piv.rotation_euler = (0, deg(-135 + (p - 950) * 2.7), 0); return piv
    hand('needle', 995, C.simple('needle', '#141414', 0.4), 0.004, r * 0.9, -0.023)
    hand('set-hand', 1005, brass, 0.006, r * 0.82, -0.027)
    C.obj('hub', KI._cyl_y(r * 0.07, 0.008), brass, at + Vector((0, -0.028, 0)))
    KI.disc('glass', r * 1.02, KI.glass_mat(), at + Vector((0, -0.03, 0)))
    # a clock beside it, the time 1200
    ct = Vector((0.3, -0.02, 0.15)); C.obj('clock-case', KI._cyl_y(r * 1.12, 0.035), brass, ct)
    KI.disc('clock-face', r, C.simple('clock-face', '#eee9dc', 0.5), ct + Vector((0, -0.019, 0)))
    for a in range(0, 360, 30):
        tk = C.obj('tick', C.rbox('tick', (0.003, 0.001, 0.012), 0.0002, 1), M['dark'], ct + Vector((math.sin(deg(a)) * r * 0.85, -0.021, math.cos(deg(a)) * r * 0.85))); tk.rotation_euler = (0, deg(a), 0)
    for nm, L in (('hour', 0.055), ('minute', 0.08)): C.obj(nm, C.rbox(nm, (0.004, 0.0015, L), 0.0005, 1), M['dark'], ct + Vector((0, -0.023, L * 0.4)))
    K.camera((0.15, -0.66, 0.17), (0.15, 0.0, 0.15), 38)
    def tip(p, k=0.62): a = deg(-135 + (p - 950) * 2.7); return tuple(at + Vector((math.sin(a) * r * k, -0.03, math.cos(a) * r * k)))
    labels = [(tip(995, 0.3), 'now 995', 'red'), (tip(1005, 0.8), 'set hand: 1005 at 0900', 'blue'), (tuple(ct + Vector((0, -0.03, r))), 'clock: 1200')]
    note = 'Fall 10 hPa in 3 h: a storm likely'; extra = {'lines': ['6–9 hPa in 3 h: a gale likely']}; expo = -0.3

elif FIG == 8:
    # a long swell from the west, 400 m crest to crest, under a clear sky; our yacht on the back of one
    K.day_sky(sun_az=100, sun_el=12)
    hz = swell_sea(400.0, 5.0, 3600.0, 6.0, dir_=270.0, chop=0.3)
    yx, yy = 560.0, -260.0
    y = A.sailing('you', 20, 300, yx, yy, heel=-10); y.root.location.z = hz(yx, yy) + 0.2
    dz = (hz(yx + 2, yy) - hz(yx - 2, yy)) / 4; y.root.rotation_euler.y = -math.atan(dz)
    K.wake(y, 30, 6, 0.7)
    K.camera((500, -720, 42.0), (500, 300, 0.0), 32)
    cz = 5.0 * 1.25                                   # crests where sin = 1: x = -100 + 400 k (s = -x for a swell from 270)
    arrows = [((300, -60, cz + 6), (700, -60, cz + 6), 'yellow'), ((700, -60, cz + 6), (300, -60, cz + 6), 'yellow')]
    labels = [((500, -60, cz + 7), 'wavelength ≈ 400 m', 'yellow'), ((300, -330, cz + 2), 'period 16 s')]
    note = 'Swell with a period of 16 s'; extra = {'lines': ['1.56 × 16² = 400 m · feels the bottom at 200 m']}; expo = -0.3

elif FIG == 9:
    # over the shelf edge with the wind rising: steep, breaking seas; low cloud
    A.cloud_sky('#4f5961', '#848c93', '#3b4148', '#6c737a', cover=0.9, sharp=0.5, scale=1.2, sun=(220, 25, 1.2), haze=0.1, shade_scale=1.6)
    sea = K.sea(wind=16.0, wave_scale=1.2, chop=2.2, size=70.0, res=11, repeat=8, color='#1e3a42'); sea.modifiers['ocean'].foam_coverage = 0.45
    y = A.sailing('you', 330, 225, 0, 0, reef=0.6, heel=-10)
    A.drone(Vector((0, 4, 5)), 42, az=120, el=10, lens=28)
    labels = [((-30, 60, 6), 'shelf edge: 1000 → 200 m', 'red'), (tuple(y.world((K.MAST.x, K.MAST.y, 9))), 'steepest sea here')]
    note = 'Crossing the shelf edge'; extra = {'lines': ['SW 8 by 1800, swell 16 s: cross before the gale']}; expo = 0.4

elif FIG == 10:
    # a W gale building; the coast under our lee to the east; beating out west for sea room
    A.cloud_sky('#525b63', '#8e959b', '#3c4249', '#71787f', cover=0.85, sharp=0.45, scale=1.3, sun=(200, 22, 1.2), haze=0.1, shade_scale=1.6)
    sea = K.sea(wind=15.0, wave_scale=0.9, chop=1.9, size=60.0, res=11, repeat=8, color='#21373f'); sea.modifiers['ocean'].foam_coverage = 0.35
    K.coast(distance=3600, bearing=90, length=16000, height=260, town=False, seed=12)
    y = A.sailing('you', 300, 260, 0, 0, reef=0.65, heel=-20); K.wake(y, 40, 8, 1.2)
    A.drone(Vector((0, 2, 6)), 40, az=250, el=9, lens=26)
    arrows = [wind_arrow(270, (-6, -14), 20, 10)]
    labels = [(tuple(A.compass(80, 2.5, 3600)), 'lee shore', 'red'), ((-16, -14, 11.5), 'W gale for 24 h', 'blue'), (tuple(y.world((K.MAST.x, K.MAST.y, 8))), 'making offing', 'blue')]
    note = 'Sea room: drift 24 h × 2 kn = 48 M'; extra = {'lines': ['Only 40 M to the lee shore: make offing before you heave to']}; expo = 0.3

elif FIG == 11:
    # a high volcanic island in the NE trade: cumulus capping it, whitecaps off its NW and SE flanks, a glassy lee SW
    s = 20.0; P = A.drawing(s)
    poly = [P(*p) for p in A.path_polys('M150 50 C185 50 200 75 198 98 C196 125 175 142 150 142 C120 142 102 122 102 96 C102 70 120 50 150 50 Z')[0]]
    h = A.land([poly], (-2400, -2400, 2400, 2400), 22.0, relief=700, hill=650, beach=10, rough=0.25)
    A.scrub(h, (-1100, -1100, 1100, 1100), 900, minh=8, size=(9, 16))
    A.cloud_sky('#2f6aa8', '#b8cad8', '#9aa3ad', '#f4f5f6', cover=0.2, sharp=0.08, scale=3.2, sun=(250, 45, 3.2), haze=0.08, shade_scale=2.0)
    K.sea('breeze', size=60.0, res=8, repeat=40, center=(0, 0), color='#0b3a52')
    for k_, (cx, cy) in enumerate((P(84, 42), P(216, 152))):          # acceleration zones: whitecaps
        A.foam(f'wc{k_}a', (cx, cy), 700, 280, rot=-45, z=1.0, density=0.35, scale=1.2)
        A.foam(f'wc{k_}b', (cx, cy), 450, 180, rot=-45, z=1.05, density=0.3, scale=1.6)
    flat_patch('lee', [P(104, 112), P(122, 134), P(118, 160), P(92, 176), P(62, 178), P(56, 150), P(80, 128)], z=1.0, color='#123f56')
    A.drone(Vector((-300, -400, 0)), 4600, az=215, el=42, lens=30)
    arrows = [wind_arrow(45, P(250, 30), 900, 200)]
    labels = [((*P(82, 40), 30), 'stronger', 'red'), ((*P(218, 154), 30), 'stronger', 'red'), ((*P(84, 160), 30), 'wind shadow', 'blue'),
              ((*P(250, 30), 220), 'NE trade wind', 'blue')]
    note = 'High island in the NE trade wind'; extra = {'lines': ['Faster round its flanks, a calm lee downwind']}; expo = -0.4

elif FIG == 12:
    # a cumulonimbus to the NE moving south: its dark base and rain shaft; reefed, heading east at 6 kn
    A.cloud_sky('#3b6898', '#a8bccb', '#4b525a', '#b7bcc1', cover=0.3, sharp=0.2, scale=2.2, boost=(55, 35, 0.9, 0.9), sun=(230, 35, 2.6), haze=0.06, wall=(55, 26, 0.32, '#1f242a'))
    K.sea('breeze', repeat=10)
    y = A.sailing('you', 90, 30, 0, 0, reef=0.5, heel=-12); K.wake(y, 40, 8, 1.0)
    A.drone(Vector((4, 4, 8)), 42, az=225, el=8, lens=24)
    labels = [(tuple(A.compass(55, 9, 2500)), 'Cb cell, moving S 18 kn', 'red'), (tuple(y.world((K.MAST.x, K.MAST.y, 17))), 'You, 6 kn: pass astern of it', 'blue')]
    note = 'Plot the cell like a ship'; extra = {'lines': ['CAPE 1800 J/kg: thunderstorms likely']}; expo = 0.0

C.render(OUT, SAMPLES, SCALE, expo, labels, note, space='blender', arrows=arrows, extra=extra)
