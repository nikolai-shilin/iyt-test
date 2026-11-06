# Article charter-checkin/papers, its six figures as Blender renders.
#   1  the papers on the base desk: skipper's licence, VHF certificate, passports, crew list, booking, deposit card
#   2  the contract open at the deposit clause (limit highlighted, exclusions marked), the card terminal: pre-auth
#   3  17:30 at the helm, the plotter's route: 14 M to run at 5 kn, ETA 20:18 after sunset; a harbour 6 M abeam
#   4  the briefing's two bays at 18:00: A in the east bay under cliffs, B in the west bay open to the south
#   5  the check-in report on a clipboard in the cockpit: exact, counted, read off, signed by both
#   6  the base marina on Friday: A the fuel pontoon, B the return berth, C the visitor quay; NW breeze
#   blender --background --factory-startup --python docs/design/blender/art_checkin_papers.py -- --fig 1 [--samples 160]
# Textures (documents, plotter screen) come from art_checkin_nps_tex.py into charter-checkin/papers/tex/.
import os, sys, math, random
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import bpy, bmesh
from mathutils import Vector, noise as mnoise
import common as C, kit as K, kit_instruments as KI, kit_world as KW
import art_checkin_nps_kit as A
import q_encounter_props as P

arg = C.cli(); FIG = arg('--fig', 1); SAMPLES = arg('--samples', 160); SCALE = arg('--scale', 100)
OUT = arg('--out', os.path.join(A.outdir('papers'), f'{FIG}-3d.jpg'))
deg = math.radians
T = lambda n: A.tex('papers', n)

C.reset()
M = K.mats()
labels, arrows, note, expo, extra = [], [], None, -0.5, {}

def desk(wood='#6b4a2e', w=1.6, d=1.0):
    """A desk top at z = 0, lit by a window to the left and a soft ceiling light."""
    m = KI.joinery_mat('desk-wood')
    C.obj('desk', C.rbox('desk', (w, d, 0.04), 0.004, 2), m, (0, 0, -0.02))
    K.day_sky(sun_az=200, sun_el=40, strength=0.08)
    KI.area_light((-0.9, -0.3, 0.8), (0, 0.05, 0), 30, 1.0, (1.0, 0.96, 0.9))
    KI.area_light((0.3, -0.6, 1.3), (0, 0, 0), 14, 1.2, (0.95, 0.97, 1.0))

def slab(name, w, h, t, path, loc, rotz, rough=0.5, edge='#e9e4d8'):
    """A card, booklet or block of paper: a thin box with its face image on top."""
    o = C.obj(name + '-body', C.rbox(name + '-body', (w, h, t), min(0.002, t / 2), 2), C.simple(name + '-edge', edge, 0.7), (loc[0], loc[1], loc[2] + t / 2))
    o.rotation_euler = (0, 0, deg(rotz))
    f = A.quad(name, w * 0.998, h * 0.998, path, (loc[0], loc[1], loc[2] + t + 0.0004), rot=(0, 0, deg(rotz)), rough=rough)
    return f

def pen(at, rotz, color='#1d2a55'):
    pv = bpy.data.objects.new('pen', None); C.col.objects.link(pv)
    a = C.cyl('pen-body', 0.0055, 0.0055, 0.13, 24, C.simple('pen-body', color, 0.3, coat=0.8), (0, 0, 0)); a.parent = pv
    b = C.cyl('pen-tip', 0.0055, 0.0012, 0.02, 24, M['chrome'], (0, 0, 0.075)); b.parent = pv
    c = C.obj('pen-clip', C.rbox('clip', (0.002, 0.004, 0.05), 0.001, 1), M['chrome'], (0, 0.006, -0.04)); c.parent = pv
    pv.rotation_euler = (0, deg(90), deg(rotz)); pv.location = (at[0], at[1], 0.0056)
    return pv

if FIG == 1:
    desk()
    bk = A.sheet('booking', 0.21, 0.297, T('booking'), (0.17, 0.07, 0.0006), rotz=8, curl=0.002)
    cl = A.sheet('crewlist', 0.21, 0.297, T('crewlist'), (-0.06, 0.04, 0.0012), rotz=-6, curl=0.002)
    pp = []
    for i, (dx, dy, r) in enumerate(((-0.30, 0.09, 18), (-0.27, 0.04, 6), (-0.235, -0.01, -8))):
        pp.append(slab(f'passport{i}', 0.088, 0.125, 0.006, T('passport'), (dx, dy, i * 0.0062), r, rough=0.6, edge='#5a1520'))
    lic = slab('licence', 0.0856, 0.054, 0.0008, T('licence'), (-0.20, -0.17, 0.0), -8, rough=0.35, edge='#d8dde4')
    src = slab('src', 0.0856, 0.054, 0.0008, T('src'), (0.03, -0.20, 0.0), 6, rough=0.35, edge='#e9e4d8')
    crd = slab('card', 0.0856, 0.054, 0.0008, T('card'), (0.25, -0.16, 0.0), 14, rough=0.3, edge='#1c2b48')
    pen((0.30, 0.02), 100)
    K.camera((0.0, -0.62, 0.62), (0.0, -0.04, 0.0), 38)
    labels = [(tuple(A.on_sheet(lic, 0.5, 0.6, 0.004)), "skipper's licence, in date", 'blue'),
              (tuple(A.on_sheet(src, 0.5, 0.6, 0.004)), "VHF certificate"),
              (tuple(A.on_sheet(pp[2], 0.5, 1.0, 0.004)), 'passports, everyone aboard'),
              (tuple(A.on_sheet(cl, 0.45, 0.9, 0.004)), 'crew list, as sent'),
              (tuple(A.on_sheet(bk, 0.55, 0.95, 0.004)), 'booking papers'),
              (tuple(A.on_sheet(crd, 0.6, 0.6, 0.004)), 'deposit card')]
    note = 'In your hand luggage'; expo = -0.6

elif FIG == 2:
    desk()
    T('contract'); marks = A.anchors('papers', 'contract')
    ct = A.sheet('contract', 0.21, 0.297, T('contract'), (-0.05, 0.0, 0.0008), rotz=-4, curl=0.0025)
    # the card terminal: a dark body, its screen, a keypad; the card in its slot
    tc = Vector((0.15, -0.07, 0.0)); rz = 18
    piv = bpy.data.objects.new('terminal', None); C.col.objects.link(piv); piv.location = tc; piv.rotation_euler = (0, 0, deg(rz))
    body = C.obj('term-body', C.rbox('term', (0.08, 0.17, 0.028), 0.012, 4), C.simple('term', '#24272b', 0.45), (0, 0, 0.014)); body.parent = piv
    scr = A.quad('term-screen', 0.056, 0.07, T('terminal'), (0, 0.035, 0.0285), emit=0.6, rough=0.2); scr.parent = piv
    for i in range(4):
        for j in range(3):
            k = C.obj('key', C.rbox('key', (0.016, 0.011, 0.004), 0.002, 2), C.simple('key', '#3a3e44' if i < 3 else ('#b3261e', '#d9b300', '#2a8a3a')[j], 0.5), (-0.02 + j * 0.02, -0.012 - i * 0.016, 0.029)); k.parent = piv
    cd = slab('card', 0.0856, 0.054, 0.0008, T('card'), (0.21, -0.17, 0.0), -24, rough=0.3, edge='#1c2b48')
    pen((-0.21, -0.12), 70)
    bpy.context.view_layer.update()
    K.camera((0.01, -0.33, 0.37), (0.01, -0.02, 0.0), 40)
    labels = [(tuple(A.on_sheet(ct, 0.14, 1 - marks['limit'] + 0.012, 0.003)), 'limit: insured damage', 'blue'),
              (tuple(A.on_sheet(ct, 0.82, 1 - marks['excl'] + 0.012, 0.003)), 'outside: negligence, grounding', 'red'),
              (tuple(piv.matrix_world @ Vector((0, -0.075, 0.03))), 'blocked, not taken')]
    note = 'Deposit clause: how it often reads'
    extra = {'lines': ['Settled at check-out, against the form']}; expo = -0.6

elif FIG == 3:
    # 17:30, motoring north, the sun low in the west; the plotter's route page
    you = A.yacht('you').place(0, 0, heading=0)
    K.sea('breeze', repeat=10); K.day_sky(sun_az=262, sun_el=14); K.wake(you, 40, 8, 1.0)
    K.coast(distance=6000, bearing=275, height=320, town=True, seed=5)
    tx = T('papers3'); an = A.anchors('papers', 'papers3')
    objs, scr = A.plotter(tx, you.world((-1.25, -0.32, 4.6)), tilt=-14)
    K.camera(tuple(you.world((-1.72, -0.30, 4.99))), tuple(you.world((-1.2, -0.36, 4.75))), 32)
    labels = [(A.screen_point(scr, *an['eta']), 'ETA 20:18: after dark', 'red')]
    note = '17:30 · 14 M to run · 5 kn · sunset 19:40'
    extra = {'lines': ['14 ÷ 5 = 2.8 h = 2 h 48 min: in at 20:18, not allowed', 'Harbour 6 M: 1 h 12 min, in at 18:42: divert']}; expo = -0.4

elif FIG == 4:
    # two bays on a coast running east-west, land to the north: the east bay under high cliffs, the west bay low
    def shore(x):
        w = 260 * math.exp(-((x + 380) / 190) ** 2)      # west bay
        e = 250 * math.exp(-((x - 380) / 170) ** 2)      # east bay
        return 40 - 120 * math.exp(-(x / 140) ** 2) + w + e + 10 * math.sin(x * 0.02)
    def hgt(x, y):
        d = y - shore(x)
        if d < 0: return max(-14.0, d * 0.1) - 0.4
        n = 14 * mnoise.noise(Vector((x * 0.006, y * 0.006, 2.0))) + 5 * mnoise.noise(Vector((x * 0.03, y * 0.03, 5.0)))
        cliff = 1.0 / (1.0 + math.exp(-(x - 200) / 40))             # 0 to the west, 1 round the east bay
        low = 1.2 + 70 * (1 - math.exp(-d / 260)) + n * min(1, d / 60)
        high = 1.0 + 210 * (1 - math.exp(-d / 14)) + 60 * (1 - math.exp(-d / 300)) + n
        return low * (1 - cliff) + high * cliff
    x0, x1, y0, y1, st = -2200, 2200, -260, 2600, 8.0
    nx, ny = int((x1 - x0) / st), int((y1 - y0) / st); V, Fc = [], []
    for j in range(ny + 1):
        for i in range(nx + 1):
            x, y = x0 + i * st, y0 + j * st; V.append((x, y, hgt(x, y)))
    for j in range(ny):
        for i in range(nx):
            a = j * (nx + 1) + i; Fc.append((a, a + 1, a + nx + 2, a + nx + 1))
    me = bpy.data.meshes.new('land'); me.from_pydata(V, [], Fc); me.update(); me.shade_smooth(); C.obj('land', me, KW.land_mat())
    K.sea('calm', size=40.0, repeat=24, center=(0, 150)); K.day_sky(sun_az=245, sun_el=24)
    random.seed(4); fol = C.simple('maquis', '#3c4a26', 0.9)
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0); tm = bpy.data.meshes.new('tree'); bm.to_mesh(tm); bm.free(); tm.materials.append(fol); tm.shade_smooth()
    for k in range(1600):
        x, y = random.uniform(-1500, 150), random.uniform(-100, 1500)
        if y - shore(x) < 30: continue
        o = bpy.data.objects.new('tree', tm); C.col.objects.link(o); s = random.uniform(3, 6); o.scale = (s, s, s * 0.8); o.location = (x, y, hgt(x, y) + s * 0.4)
    yl = A.glow_mat('spot', '#ffc400', 2.5)
    pA, pB = Vector((385, shore(385) - 95, 0)), Vector((-385, shore(-385) - 110, 0))
    A.ring('spot-A', pA, 32, yl, z=0.5, k=0.08); A.ring('spot-B', pB, 32, yl, z=0.5, k=0.08)
    yb = A.yacht('at-B').place(pB.x, pB.y, heading=10)
    A.drone(Vector((0, 260, 0)), 1750, az=185, el=33, lens=34)
    cliff = Vector((385, shore(385) + 70, hgt(385, shore(385) + 70) + 10))
    arrows = [((300, shore(300) + 320, 230), (370, shore(370) + 20, 80), 'blue'), ((470, shore(470) + 320, 230), (420, shore(420) + 20, 80), 'blue')]
    labels = [((pA.x, pA.y, 30), 'A · E bay, under cliffs'), ((pB.x, pB.y, 30), 'B · W bay, open S'),
              ((cliff.x + 40, cliff.y + 60, cliff.z + 110), 'night gusts off the cliffs', 'red'), ((20, 700, 200), 'Wind N', 'blue')]
    arrows.append(((20, 850, 180), (20, 550, 80), 'blue'))
    note = 'Briefing: E bay, night gusts in a northerly'
    extra = {'lines': ['A is calm at 18:00, not at night: anchor at B']}; expo = -0.5

elif FIG == 5:
    # the clipboard on the cockpit table, a pen, the sea beyond
    K.sea('calm', center=(0, 0)); K.day_sky(sun_az=230, sun_el=48)
    for o in bpy.data.objects:
        if o.name.startswith(('ocean', 'far-sea')): o.location.z -= 1.6
    C.obj('table', C.rbox('table', (0.9, 0.6, 0.03), 0.01, 2), M['teak'], (0, 0, -0.015))
    C.obj('board', C.rbox('board', (0.235, 0.33, 0.004), 0.006, 2), C.simple('hardboard', '#6a4b2c', 0.6), (0, 0, 0.002))
    fm = A.sheet('form', 0.21, 0.297, T('checkin'), (0, -0.012, 0.0045), rotz=0, curl=0.001)
    C.obj('clip', C.rbox('clip', (0.1, 0.035, 0.012), 0.004, 2), M['chrome'], (0, 0.15, 0.011))
    pen((0.16, -0.05), 75)
    piv = bpy.data.objects.new('board-tilt', None); C.col.objects.link(piv)
    K.camera((0.03, -0.33, 0.36), (0.0, 0.0, 0.0), 40)
    row = lambda i: 1 - (410 + 96 * i + 48) / 1754
    labels = [(tuple(A.on_sheet(fm, 0.86, row(0) + 0.012)), 'exact: size and place', 'blue'),
              (tuple(A.on_sheet(fm, 0.22, row(2) + 0.012)), 'counted', 'blue'),
              (tuple(A.on_sheet(fm, 0.86, row(5) + 0.012)), 'read off', 'blue'),
              (tuple(A.on_sheet(fm, 0.3, 1 - (410 + 96 * 7 + 170) / 1754 + 0.012)), 'signed by both')]
    note = 'A line that protects you'
    extra = {'lines': ["Vague: 'minor scratches, bow' protects nobody"]}; expo = -0.4

elif FIG == 6:
    # the base marina: the quay along the north; the base pontoon running south with charter yachts stern-to on
    # its west side and one empty berth; the fuel pontoon to the west; the visitor quay to the east
    K.sea('calm', size=30.0, repeat=14, center=(0, 0)); K.day_sky(sun_az=240, sun_el=40)
    con = C.concrete_mat('quay')
    C.obj('quay-n', C.rbox('quay-n', (200, 30, 2.4), 0.2, 2), con, (0, 88, 0.2))
    C.obj('quay-e', C.rbox('quay-e', (16, 112, 2.4), 0.2, 2), con, (80, 16.9, 0.2))
    pont = C.planks_mat('pontoon-planks')
    C.obj('base-pontoon', C.rbox('bp', (3.0, 64, 0.6), 0.1, 2), pont, (10, 41, 0.25))
    C.obj('fuel-pontoon', C.rbox('fp', (20, 4.0, 0.6), 0.1, 2), pont, (-42, 30, 0.25))
    C.obj('fuel-walk', C.rbox('fw', (2.5, 44, 0.6), 0.1, 2), pont, (-42, 52, 0.25))
    C.obj('pump', C.rbox('pump', (0.8, 0.6, 1.6), 0.08, 2), C.simple('pump', '#e9e7e1', 0.4), (-42, 31, 1.35))
    A.quad('fuel-sign', 2.4, 0.8, T('sign-fuel'), (-42, 28.6, 3.2), rot=(deg(90), 0, 0))
    C.cyl('sign-post', 0.06, 0.06, 2.8, 12, M['galv'], (-42, 28.8, 1.6))
    A.quad('base-sign', 6.4, 1.2, T('sign-base'), (10, 72.6, 3.2), rot=(deg(90), 0, 0))
    base = A.yacht('base0').place(-0.3, 66, heading=270)    # stern-to the pontoon's west side, bows west
    slots = [66 - 4.7 * i for i in range(10)]; B_Y = slots[4]  # one berth empty: the return berth
    k = 0
    for y in slots[1:]:
        if y != B_Y: P.clone_yacht(base, f'base{k}', -0.3, y, 270); k += 1
    for y in slots[:9]: P.clone_yacht(base, f'east{k}', 20.3, y, 90); k += 1            # her east side, bows east
    for i, y in enumerate((40, 30, 15)): P.clone_yacht(base, f'visitor{i}', 63.5, y, 270)
    you = P.clone_yacht(base, 'you', -30, -22, 340); K.wake(you, 30, 7, 0.8)
    yl = A.glow_mat('spot', '#ffc400', 2.5)
    pA, pB, pC = Vector((-42, 24, 0)), Vector((2.0, B_Y, 0)), Vector((65, 0, 0))
    for nm, p in (('A', pA), ('B', pB), ('C', pC)): A.ring('spot-' + nm, p, 5.5, yl, z=0.45, k=0.08)
    wh = A.glow_mat('route', '#f4f1e6', 1.2)
    for a, b in (((-33, -12), (-41, 17)), ((-36, 25), (-6, B_Y - 1))):
        a, b = Vector((a[0], a[1], 0)), Vector((b[0], b[1], 0)); L = (b - a).length; u = (b - a) / L; s_ = 0.0
        while s_ < L:
            e = min(s_ + 3.0, L); A.strip('route', tuple(a + u * s_), tuple(a + u * e), 0.5, wh, 0.35); s_ = e + 2.2
    A.drone(Vector((8, 22, 0)), 140, az=200, el=44, lens=32)
    arrows = [((40, 62, 14), (52, 48, 14), 'blue')]
    labels = [((pA.x, pA.y, 4.5), 'A · fuel pontoon'), ((pB.x, pB.y, 4.0), 'B · return berth', 'blue'), ((pC.x, pC.y, 4.0), 'C · visitor quay'),
              ((40, 64, 16), 'Wind NW', 'blue')]
    note = 'Full to full: A first, then B'
    extra = {'lines': ['In the evening before check-out, tanks full']}; expo = -0.5

C.render(OUT, SAMPLES, SCALE, expo, labels, note, space='blender', arrows=arrows, extra=extra)
