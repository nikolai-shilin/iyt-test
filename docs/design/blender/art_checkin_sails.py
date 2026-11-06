# Article charter-checkin/sails ("Sails, furlers and reefing"), its six figures as Blender renders:
#   1  both sails up at the pontoon in light wind: mainsail, genoa, its furler, mast, boom
#   2  the mainsail hoisted, every edge named: head, luff with its slides, leech, battens, clew, tack
#   3  the genoa furler: the drum full of line with the genoa fully out, the furling line led aft to the cockpit
#   4  in-mast furling: the main half out of the mast slot, the outhaul winched, the furling line eased
#   5  reef 1 in: the luff cringle on the hook at the mast, the leech cringle pulled down by the reef line, the bunt
#   6  boom gear: running with the wind astern, a preventer from the boom end to the bow and back to the cockpit
#   blender --background --factory-startup --python docs/design/blender/art_checkin_sails.py -- --fig 3 [--samples 160] [--out x.jpg]
#   python3 docs/design/blender/art_checkin_sails.py --plans      (the schematics, <n>-plan.json)
import os, sys, math, json, random
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
DIR = os.path.join(HERE, '..', 'figure-style', 'articles', 'charter-checkin', 'sails')

# ===================================================================================================== plans
def plans():
    t = lambda x, z, text, **o: {'x': x, 'z': z, 'text': text, **o}
    # a yacht outline in plan, bow north, 14 m: drawn as a zone so lines on deck lie on top of it
    hull = [[0, -7.6], [1.2, -5.5], [2.1, -2.5], [2.3, 1.0], [2.1, 4.5], [1.7, 6.4], [-1.7, 6.4], [-2.1, 4.5], [-2.3, 1.0], [-2.1, -2.5], [-1.2, -5.5]]
    deck = {'pts': hull, 'c': 'ink', 'fill': '#eef1f3', 'dash': '0'}
    cock = {'pts': [[-1.4, 2.6], [1.4, 2.6], [1.3, 6.0], [-1.3, 6.0]], 'c': 'ink', 'fill': 'rgba(0,0,0,.06)', 'dash': '0'}
    out = {}
    out[3] = {'noScale': True, 'sch': {'padPx': 60, 'minMpp': 0.01, 'title': 'Genoa furler · the line back to the cockpit', 'zones': [deck, cock],
              'circles': [{'x': 0, 'z': -7.2, 'r': 0.45, 'c': 'ink', 'dash': '0', 'fill': '#c9ced3'}],
              'paths': [{'pts': [[0.4, -7.0], [1.0, -6.2], [1.75, -4.5], [1.95, -2.0], [2.0, 1.0], [1.75, 2.9], [1.15, 3.3]], 'c': 'line', 'w': 7},
                        {'pts': [[0, -7.2], [-0.05, -1.4]], 'c': 'ink', 'w': 3, 'dash': '6 8'}],
              'texts': [t(-3.4, -7.6, 'drum: full of line'), t(4.1, -4.2, 'furling line', kind='accent'), t(4.1, 3.2, 'to the cockpit winch'), t(-0.1, 0.0, 'mast', pill=False, size=24)],
              'fit': [{'x': -6, 'z': -8.6}, {'x': 6, 'z': 7}],
              'key': ['Genoa fully out: the drum is full of furling line', 'Hauled in by hand it rolls the genoa away; it runs fair through its blocks']}}
    out[4] = {'noScale': True, 'sch': {'padPx': 60, 'minMpp': 0.01, 'title': 'In-mast furling · two lines, opposite ways', 'zones': [deck, cock],
              'paths': [{'pts': [[0, -1.4], [0, 4.2]], 'c': 'ink', 'w': 10},
                        {'pts': [[0.15, 4.1], [0.15, -1.1], [0.5, -0.8], [0.9, 1.0], [1.0, 2.9]], 'c': 'line', 'w': 6},
                        {'pts': [[-0.25, -1.1], [-0.6, -0.8], [-0.9, 1.0], [-1.0, 2.9]], 'c': 'red', 'w': 6}],
              'circles': [{'x': 0, 'z': -1.4, 'r': 0.3, 'c': 'ink', 'dash': '0', 'fill': '#c9ced3'}],
              'texts': [t(4.2, 3.2, 'outhaul: winch it', kind='accent'), t(-4.2, -0.6, 'furling line: ease it', kind='red'), t(1.6, 5.0, 'boom'), t(-1.9, -2.2, 'mast')],
              'fit': [{'x': -6.5, 'z': -8.6}, {'x': 6.5, 'z': 7}],
              'key': ['Unfurling: winch the outhaul while easing the furling line', 'Furling: boom at its mark, a little outhaul tension, take the furling line in']}}
    # 6: running, wind north, heading 170; the boom out to starboard, the preventer to the bow and back aft
    h = math.radians(170); fw = (math.sin(h), -math.cos(h)); sb = (math.cos(h), math.sin(h))   # x east, z south
    P = lambda f, s: [round(f * fw[0] + s * sb[0], 2), round(f * fw[1] + s * sb[1], 2)]
    mast = P(1.0, 0); bend = P(1.0 - 5.4 * math.cos(math.radians(78)), 5.4 * math.sin(math.radians(78)))
    other = P(1.0 - 5.4 * math.cos(math.radians(78)), -5.4 * math.sin(math.radians(78)))
    arc = [P(1.0 - 5.4 * math.cos(math.radians(a)), 5.4 * math.sin(math.radians(a))) for a in range(70, -75, -10)]
    out[6] = {'noScale': True, 'sch': {'wind': 0, 'padPx': 60, 'minMpp': 0.01, 'trueScale': True, 'title': 'Boom gear · wind astern',
              'boats': [{'you': True, 'x': 0, 'z': 0, 'hdg': 170, 'noHeading': True, 'L': 14, 'fill': 'rgba(20,24,28,.22)'}],
              'paths': [{'pts': [mast, bend], 'c': 'ink', 'w': 8}, {'pts': [bend, P(6.6, 0.9), P(5.6, 1.4), P(-3.5, 1.9)], 'c': 'line', 'w': 5},
                        {'pts': arc, 'c': 'red', 'w': 5, 'dash': '12 10', 'arrow': True}],
              'texts': [t(*P(-2.0, 7.4), 'boom'), t(*P(5.0, 4.6), 'preventer', kind='accent'), t(*P(-6.2, -6.8), 'accidental gybe', kind='red')],
              'fit': [{'x': -9, 'z': -10}, {'x': 9, 'z': 10}],
              'key': ['Wind astern: a small shift or a wave puts the wind behind the main, and the boom flies across', 'A preventer from the boom end to the bow and back to a cockpit winch holds it, and can be eased']}}
    for n, spec in out.items():
        with open(os.path.join(DIR, f'{n}-plan.json'), 'w') as f: json.dump(spec, f, ensure_ascii=False, indent=1)
    print('plans', sorted(out))

if '--plans' in sys.argv:
    plans(); sys.exit(0)

# ===================================================================================================== Blender
import bpy, bmesh
from mathutils import Vector, Matrix, Euler, noise as mnoise
import common as C, kit as K, kit_world as KW, art_checkin_gear as G
from art_checkin_gear import V, deg

arg = C.cli(); FIG = arg('--fig', 1); SAMPLES = arg('--samples', 160); SCALE = arg('--scale', 100)
OUT = G.out_path('sails', FIG, arg('--out', ''))
labels, arrows, note, expo, extra = [], [], None, -0.6, {}
C.reset()
MO = Vector((K.MAST.x, K.MAST.y, K.WL))

def hide_model(y, box, pred=None):
    """Hide the model's meshes inside a model-space box ((x0, y0, z0), (x1, y1, z1))."""
    bpy.context.view_layer.update(); (x0, y0, z0), (x1, y1, z1) = box
    for o in y.objs:
        if o.type != 'MESH' or o.hide_render: continue
        lo, hi = K.bbox([o]); M = y.root.matrix_world.inverted()
        lo, hi = M @ lo + MO, M @ hi + MO
        lo, hi = Vector(map(min, lo, hi)), Vector(map(max, lo, hi))
        if lo.x > x0 and hi.x < x1 and lo.y > y0 and hi.y < y1 and lo.z > z0 and hi.z < z1 and (pred is None or pred(o)):
            o.hide_render = True; o.hide_viewport = True

def pontoon(edge_y, x0, x1, top=0.45, width=2.4):
    M = K.mats(); cy = edge_y + width / 2
    C.obj('float', C.rbox('float', (x1 - x0, width - 0.1, 0.8), 0.06, 2), M['float'], ((x0 + x1) / 2, cy, top - 0.45))
    plank = C.rbox('plank', (0.14, width, 0.035), 0.004, 1); plank.materials.append(M['planks'])
    x = x0
    while x < x1:
        o = bpy.data.objects.new('plank', plank); C.col.objects.link(o); o.location = (x, cy, top - 0.0175); x += 0.155
    C.obj('rub', C.rbox('rub', (x1 - x0, 0.12, 0.08), 0.02, 2), M['rubber'], ((x0 + x1) / 2, edge_y + 0.03, top - 0.1))

def alongside(y):
    """Move the yacht (heading 90, port side +y) so a pontoon edge lies a fender off her widest point; returns the edge y."""
    bpy.context.view_layer.update(); best = None
    for x in (-3, -1, 1, 3):
        for z in (0.3, 0.8, 1.3):
            h, _ = G.ray((x, 8.0, z), (0, -1, 0))
            if h is not None: best = h.y if best is None else max(best, h.y)
    return best + 0.28

# ---------------------------------------------------------------------------------------------- 1  both sails up
if FIG == 1:
    y = G.yacht(name='yacht', sails={'main': True, 'genoa': 'starboard', 'boom': -6, 'camber': 0.08, 'genoa_camber': 0.09}).place(0, 0, heading=90)
    edge = alongside(y); pontoon(edge, -14, 14)
    for fx in (-3.0, 1.5, 5.0): G.box('fender', (0.22, 0.22, 0.6), (fx, edge - 0.12, 0.42), C.fabric_mat('fender-sock', '#1e2f55', '#5d75a8', 1400.0), 0.1)
    K.sea('calm', size=30.0, repeat=10); K.day_sky(sun_az=330, sun_el=45)
    K.coast(distance=900, bearing=200, height=80, town=True)
    W = lambda p: y.world(p)
    fs0 = W((10.62, 0.13, 3.95))
    c = W((4.0, 0.13, 10.0))
    K.camera((c.x - 2.0, c.y + 27.0, 2.2), (c.x + 0.5, c.y, 9.0), 32)
    labels = [(tuple(W((2.3, 0.6, 10.0))), 'mainsail'), (tuple(W((7.4, 0.2, 8.0))), 'genoa'), (tuple(fs0 + V(0, 0.05, 0.25)), 'furler', 'blue'),
              (tuple(W((4.93, 0.3, 15.5))), 'mast'), (tuple(W((1.5, 0.3, 5.75))), 'boom')]
    note = 'Both sails up at the pontoon, in light wind'; expo = -0.7

# ---------------------------------------------------------------------------------------------- 2  the mainsail
elif FIG == 2:
    y = G.yacht(name='yacht', sails={'main': True, 'boom': -3}).place(0, 0, heading=90)
    K.sea('calm', size=30.0, repeat=10); K.day_sky(sun_az=210, sun_el=40)
    K.coast(distance=1800, bearing=0, height=90, town=False)
    b = math.radians(-3)
    T = lambda lx, ly, lz: y.world((lx + K.MAST.x, ly + K.MAST.y, lz + K.WL))
    tack, head = T(-0.12, 0.0, 5.5 - K.WL), T(-0.1, 0.0, 20.0 - K.WL)
    clew = T(-5.4 * math.cos(b), 5.4 * math.sin(b), 5.55 - K.WL)
    dark = C.simple('batten', '#40454b', 0.5)
    def hits(y_from, pts):
        out = []
        for p in pts:
            h, _ = G.ray((p.x, y_from, p.z), (0, 1, 0)); out.append(h)
        return out
    batten_lines = []
    for v, frac in ((0.24, 0.55), (0.46, 0.7), (0.66, 0.92), (0.84, 0.92)):
        L, R = tack.lerp(head, v), clew.lerp(head, v)
        hp = [h for h in hits(-20.0, [R.lerp(L, frac * i / 12) for i in range(13)]) if h is not None]
        hp = [h for h in hp if abs(h.y - hp[0].y) < 0.25 and h.x < L.x - 0.12]
        if len(hp) > 3:
            C.tube('batten', [h + Vector((0, -0.035, 0)) for h in hp], 0.055, 8, 1.0, dark); batten_lines.append(hp)
    # luff slides: small black cars every 0.7 m up the mast's track, the luff stitched to each
    slides = []
    for k in range(20):
        p = tack.lerp(head, (k + 0.5) / 20) + V(-0.05, 0, 0)
        G.box('slide', (0.05, 0.035, 0.09), p, C.simple('slide', '#151617', 0.45), 0.008); slides.append(p)
    c = tack.lerp(head, 0.45).lerp(clew.lerp(head, 0.45), 0.5)
    K.camera((c.x + 0.5, c.y - 21.0, c.z - 1.5), (c.x + 0.5, c.y, c.z + 0.9), 25)
    mid = lambda a, b2, t: tuple(a.lerp(b2, t))
    bl = batten_lines[1] if len(batten_lines) > 1 else [clew]
    labels = [(tuple(head + Vector((0.9, -0.3, -0.7))), 'head'), (tuple(tack + Vector((0.4, -0.3, -0.2))), 'tack'), (tuple(clew + Vector((-0.2, -0.3, -0.2))), 'clew'),
              (mid(tack, head, 0.58), 'luff'), (mid(clew, head, 0.3), 'leech'), (tuple(bl[2]), 'batten', 'blue'), (tuple(slides[3] + V(-0.06, -0.05, 0)), 'slides', 'blue')]
    note = 'Walk every edge with your eyes'; expo = -0.7

# ---------------------------------------------------------------------------------------------- 3  furler drum
elif FIG == 3:
    y = G.yacht(name='yacht', sails={'main': False, 'genoa': 'port', 'boom': 0, 'genoa_camber': 0.07}).place(0, 0, heading=90)
    hide_model(y, ((10.3, -0.2, 3.75), (10.85, 0.45, 4.15)))          # the model's furler drum
    W = lambda p: y.world(p)
    st, dk = G.steel(), C.simple('drum-black', '#1a1b1d', 0.4)
    base = W((10.62, 0.13, 3.72)); G.cyl_between('drum-post', base, base + V(0, 0, 0.12), 0.02, st, 16)
    d0 = base + V(0, 0, 0.12)
    G.cyl_between('drum-flange-lo', d0, d0 + V(0, 0, 0.01), 0.105, dk, 48)
    G.cyl_between('drum-core', d0, d0 + V(0, 0, 0.11), 0.045, dk, 32)
    G.cyl_between('drum-flange-hi', d0 + V(0, 0, 0.1), d0 + V(0, 0, 0.11), 0.105, dk, 48)
    G.cyl_between('drum-guard', d0 + V(0, 0, 0.0), d0 + V(0, 0, 0.11), 0.112, C.simple('drum-guard', '#2a2c2f', 0.4), 48)
    G.cyl_between('foil', d0 + V(0, 0, 0.11), W((5.3, 0.13, 19.5)), 0.018, C.simple('foil', '#c4c8cc', 0.3, 1.0), 16)
    # the drum full of furling line: layers of turns, the line leaving it aft along the starboard side
    for o in bpy.data.objects:
        if o.name.startswith('drum-guard'): o.hide_render = True
    turns = []
    for k in range(120):
        a = k * deg(20); layer = k // 36; zz = 0.02 + (k % 36) / 36 * 0.08
        r = 0.055 + layer * 0.011
        turns.append(d0 + V(r * math.cos(a), r * math.sin(a), zz))
    exitp = turns[-1]
    fl = [W((10.2, -0.42, 3.62)), W((9.4, -0.8, 3.62)), W((8.2, -1.2, 3.62)), W((6.5, -1.55, 3.62)), W((4.5, -1.7, 3.62))]
    for p in fl: p.z = (G.deck_z(p.x, p.y, top=2.6) or 1.6) + 0.06
    lead = [exitp + V(-0.05, -0.08, 0.0), exitp + V(-0.2, -0.2, -0.02)] + fl
    G.braid3('furling-line', turns + lead, 0.005, '#e9e3d2', '#c8161d', fine=1.6)
    # lead blocks on the stanchion bases, where the line turns aft
    for p in fl[1:4]: G.box('lead-block', (0.06, 0.035, 0.05), p + V(0, 0, 0.0), st, 0.012)
    K.sea('calm', size=30.0, repeat=10); K.day_sky(sun_az=200, sun_el=45)
    K.coast(distance=900, bearing=60, height=70, town=True)
    cam = KW.camera(V(6.75, -1.35, 2.75), V(5.2, -0.45, 1.75), 30); C.focus_on_centre(cam, 16.0)
    labels = [(tuple(d0 + V(0, 0, 0.13)), 'drum: full of line', 'blue'), (tuple(lead[2] + V(0, 0, 0.04)), 'furling line'),
              (tuple(fl[2] + V(0, 0, 0.05)), 'to the cockpit')]
    note = 'Genoa fully out: this line rolls it back in'; expo = -0.65

# ---------------------------------------------------------------------------------------------- 4  in-mast furling
elif FIG == 4:
    y = G.yacht(name='yacht', boom=0).place(0, 0, heading=90)
    W = lambda p: y.world(p)
    # the main half out of the mast: luff in the slot, clew 3 m out along the boom on the outhaul car
    tack = Vector((-0.16, 0.0, 5.62 - K.WL)); head = Vector((-0.14, 0.0, 19.5 - K.WL)); clew = Vector((-3.0, 0.0, 5.66 - K.WL))
    K.sail_surface('main-half', tack, head, clew, 0.02, -1, twist=2, parent=y.root)
    slot = C.simple('mast-slot', '#0b0c0d', 0.6)
    G.box('slot', (0.012, 0.03, 13.5), W((4.93 - 0.135, 0.13, 12.4)), slot)
    st = G.steel(); dk = C.simple('dark', '#1b1c1e', 0.45)
    car = W((4.93 - 3.0, 0.13, 5.7)); G.box('outhaul-car', (0.12, 0.06, 0.05), car, dk, 0.01)
    # outhaul: from the clew car along the boom to its end sheave, back inside... shown along the boom top to the
    # gooseneck, down the mast to a turning block, aft along the coachroof to the starboard winch
    bz = W((0, 0, 5.78)).z
    mast_foot = W((4.75, -0.12, 4.32)); mast_foot.z = G.deck_z(mast_foot.x, mast_foot.y, top=2.6) + 0.05
    winch = W((1.2, -0.75, 4.3)); winch.z = G.deck_z(winch.x, winch.y, top=2.6)
    G.cyl_between('winch-base', winch, winch + V(0, 0, 0.04), 0.085, st, 32)
    G.cyl_between('winch-drum', winch + V(0, 0, 0.04), winch + V(0, 0, 0.2), 0.065, st, 32, r2=0.055)
    G.cyl_between('winch-handle', winch + V(0, 0, 0.21), winch + V(0.0, -0.22, 0.24), 0.01, C.simple('handle', '#25282b', 0.4), 12)
    clutches = W((1.8, -0.6, 4.3)); clutches.z = G.deck_z(clutches.x, clutches.y, top=2.6)
    for k, dy in enumerate((0.0, 0.07)): G.box('clutch', (0.14, 0.05, 0.05), clutches + V(0, dy, 0.025), dk, 0.01)
    oh = [car + V(0.05, 0.02, 0.05), W((4.6, 0.17, 5.84)), W((4.75, 0.05, 5.6)), mast_foot + V(0, 0.0, 0.25), mast_foot + V(-0.15, 0, 0.0),
          clutches + V(0.4, 0.0, 0.03), clutches + V(0, 0.0, 0.03), clutches + V(-0.3, -0.06, 0.03)]
    oh += [winch + V(0.07 * math.cos(a), 0.07 * math.sin(a), 0.06 + 0.02 * k / 9) for k, a in enumerate(deg(t) for t in range(60, 420, 40))]
    oh += [winch + V(-0.05, 0.25, 0.14), winch + V(-0.3, 0.35, 0.02)]
    G.braid3('outhaul', oh, 0.006, '#1b2c4c', '#e9e3d2', whip='#141414', fine=1.4)
    # furling line: from the drum at the mast foot aft to its clutch, eased (a slack bight)
    fdrum = W((4.93, 0.13, 4.42)); fdrum.z = mast_foot.z + 0.08
    G.cyl_between('furl-drum', fdrum + V(0, 0, -0.06), fdrum + V(0, 0, 0.06), 0.08, dk, 32)
    fl = [fdrum + V(-0.06, -0.06, 0.0), mast_foot + V(-0.3, 0.07, -0.02), clutches + V(0.4, 0.07, 0.02), clutches + V(0, 0.07, 0.03), clutches + V(-0.3, 0.1, 0.03),
          clutches + V(-0.55, 0.2, -0.05), clutches + V(-0.75, 0.35, -0.02)]
    G.braid3('furling-line', fl, 0.006, '#e9e3d2', '#c8161d', fine=1.6)
    K.sea('calm', size=30.0, repeat=10); K.day_sky(sun_az=200, sun_el=45)
    K.coast(distance=900, bearing=60, height=70, town=True)
    cam = KW.camera(W((1.6, -4.6, 6.6)), W((3.4, 0.0, 5.2)), 30); C.focus_on_centre(cam, 16.0)
    labels = [(tuple(car + V(0, 0, 0.12)), 'outhaul: winch it', 'blue'), (tuple(W((4.93, 0.13, 6.4)) + V(-0.14, 0, 0)), 'slot in the mast'),
              (tuple(fl[2] + V(0, 0, 0.05)), 'furling line: ease it', 'red'), (tuple(winch + V(0, 0, 0.25)), 'winch')]
    note = 'Unfurling: winch the outhaul, ease the line'; expo = -0.65

# ---------------------------------------------------------------------------------------------- 5  reef 1
elif FIG == 5:
    y = G.yacht(name='yacht', boom=-3).place(0, 0, heading=90)
    b = deg(-3); WL = K.WL
    R1 = 1.6                                                       # depth of the first reef up the luff
    tack = Vector((-0.12, 0.0, 5.9 - WL)); head = Vector((-0.1, 0.0, 20.0 - R1 - WL))
    clew = Vector((-5.15 * math.cos(b), 5.15 * math.sin(b), 5.95 - WL))
    K.sail_surface('main-reefed', tack, head, clew, 0.09, -1, twist=10, roach=0.06, parent=y.root)
    T = lambda p: y.root.matrix_world @ Vector(p)
    # the bunt: the reefed cloth gathered along the boom, lumpy, tied with reef points
    rnd = random.Random(6); bunt = []
    for k in range(26):
        u = k / 25; bunt.append(Vector((-0.25 - 4.8 * u, 5.4 * math.sin(b) * u + 0.0, 5.68 - WL)) + Vector((0, rnd.uniform(-0.03, 0.03), rnd.uniform(-0.02, 0.03))))
    bo = G.tube('bunt', [T(p) + V(0, -0.02, 0.0) for p in bunt], 0.15, K.mats()['cloth'], 16)
    tex = bpy.data.textures.new('lumps', 'CLOUDS'); tex.noise_scale = 0.18
    md = bo.modifiers.new('lumps', 'DISPLACE'); md.texture = tex; md.strength = 0.06
    for k in range(1, 8):
        p = T(bunt[int(k * 25 / 8)]); G.torus('reef-tie', 0.125, 0.008, C.simple('reef-tie', '#f2f2ee', 0.6), p + V(0, 0, -0.03), rot=(0, deg(90), 0))
    st = G.steel()
    # the hook at the mast (a ram's horn on the gooseneck) through the luff cringle; the leech cringle at the boom end
    gn = T((0.05, 0.0, 5.62 - WL)); G.tube('rams-horn', [gn + V(0, -0.06, -0.05), gn + V(0, -0.08, 0.04), gn + V(-0.03, -0.08, 0.1), gn + V(-0.07, -0.07, 0.07)], 0.009, st, 12)
    lc = T(tack) + V(-0.06, -0.07, 0.06); G.torus('luff-cringle', 0.03, 0.007, st, lc, rot=(deg(90), 0, 0))
    cc = T(clew); G.torus('leech-cringle', 0.03, 0.007, st, cc + V(0, -0.04, 0.02), rot=(deg(90), 0, 0))
    # the reef line: from the boom (its sheave near the end), up through the leech cringle, down round the boom
    bend = T((-5.3 * math.cos(b), 5.3 * math.sin(b), 5.5 - WL))
    rl = [bend + V(0.35, -0.08, 0.0), bend + V(0.1, -0.09, 0.05), cc + V(0.02, -0.06, 0.0), cc + V(-0.03, 0.0, 0.05), cc + V(-0.08, 0.08, 0.0), bend + V(-0.05, 0.1, -0.05), bend + V(-0.02, 0.0, -0.13), bend + V(0.04, -0.09, -0.06)]
    G.braid3('reef-line', rl, 0.006, '#e9e3d2', '#1f6fd6', fine=1.6)
    K.sea('calm', size=30.0, repeat=10); K.day_sky(sun_az=200, sun_el=40)
    K.coast(distance=1800, bearing=0, height=90, town=False)
    midb = T((-2.6, 0.0, 6.2 - WL))
    cam = KW.camera(midb + V(0.0, -5.6, 0.5), midb + V(0, 0, 0.1), 30); C.focus_on_centre(cam, 11.0)
    labels = [(tuple(T(bunt[13]) + V(0, -0.1, 0.12)), 'reef 1', 'blue'), (tuple(lc + V(0, 0, 0.05)), 'hook at the mast'), (tuple(cc + V(0, -0.05, 0.08)), 'reef line'),
              (tuple(T((-3.6, 0.0, 5.45 - WL)) + V(0, -0.1, -0.05)), 'boom')]
    note = 'The two cringles come down to the boom'; expo = -0.7

# ---------------------------------------------------------------------------------------------- 6  boom gear
elif FIG == 6:
    y = G.yacht(name='you', sails={'main': True, 'genoa': None, 'boom': -78}).place(0, 0, heading=170, heel=2)
    K.wake(y, 30, 7, 1.0)
    K.sea('breeze', size=40.0, repeat=10); K.day_sky(sun_az=215, sun_el=42)
    T = lambda p: y.root.matrix_world @ Vector(p)
    bang = deg(-78); bend = T((-5.3 * math.cos(bang), 5.3 * math.sin(bang), 5.6 - K.WL))
    bow = y.world((10.7, 0.13, 3.75)); block = y.world((10.3, -0.6, 3.7))
    cockpit = y.world((0.6, -1.6, 3.7))
    pv = [bend] + [bend.lerp(block, t) - V(0, 0, 0.6 * math.sin(math.pi * t)) for t in (0.25, 0.5, 0.75)] + [block, y.world((8.5, -1.25, 3.75)), y.world((5.0, -1.95, 3.75)), cockpit]
    G.tube('preventer', pv, 0.035, C.simple('preventer', '#e8231a', 0.5), 10)       # drawn heavier than life to read
    c = Vector((0, 0, 0))
    a, e, dist = math.radians(180), math.radians(55), 34.0
    eye = c + Vector((math.sin(a) * math.cos(e), math.cos(a) * math.cos(e), math.sin(e))) * dist
    K.camera(tuple(eye + V(0, 2.5, 0)), tuple(c + V(0, 2.5, 0)), 34)
    other = T((-5.3 * math.cos(-bang), 5.3 * math.sin(-bang), 5.6 - K.WL))
    bmid = T((-2.4 * math.cos(bang), 2.4 * math.sin(bang), 5.6 - K.WL))
    labels = [(tuple(bmid + V(0, 0, 0.4)), 'boom'), (tuple(pv[2] + V(0, 0, 0.3)), 'preventer', 'red'), ((11, 9, 6), 'Wind astern', 'blue')]
    arrows = [((11, 8, 6), (11, 0, 6), 'blue'), (tuple(bend + V(0, 0, 1.2)), tuple(other + V(0, 0, 1.2)), 'yellow')]
    labels.append((tuple(bend.lerp(other, 0.5) + V(0, 0, 1.3)), 'accidental gybe', 'yellow'))
    note = 'Wind astern: an accidental gybe throws the boom across'; expo = -0.7

C.render(OUT, SAMPLES, SCALE, expo, labels, note, space='blender', arrows=arrows, extra=extra)
