# Article charter-checkin/nav, its nine figures as Blender renders.
#   1  chartplotter at the berth, Sat 17:00, no satellites: NO FIX, the boat drawn 0.4 M out where it was on Friday
#   2  the helm instruments under way: log 6.0 kn through the water, SOG 4.2 kn over the ground, depth 42 m
#   3  the test run: the steering compass at 090 under the lubber line, the plotter beside it showing COG 098°T
#   4  from the helm: a ferry broad on the starboard bow crossing west, the plotter's AIS CPA alarm up
#   5  the fixed VHF (art_vhf.py): volume, squelch, DISTRESS under its cover, the 1 W / 25 W key, press to talk
#   6  the fixed VHF after a false DSC alert: the screen to cancel it, the handset up for the voice message on 16
#   7  our yacht at night from dead ahead, engine on: steaming light above the sidelights
#   8  the same under sail alone: the tricolour at the masthead
#   9  the same at anchor: the all-round white at the masthead only
#   blender --background --factory-startup --python docs/design/blender/art_checkin_nav.py -- --fig 1 [--samples 160]
# Textures (plotter screens, LCDs) come from art_checkin_nps_tex.py into charter-checkin/nav/tex/.
import os, sys, math, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import bpy, bmesh
from mathutils import Vector
import common as C, kit as K, kit_instruments as KI, kit_night as N
import art_checkin_nps_kit as A
import q_encounter_props as P

arg = C.cli(); FIG = arg('--fig', 1); SAMPLES = arg('--samples', 160); SCALE = arg('--scale', 100)
OUT = arg('--out', os.path.join(A.outdir('nav'), f'{FIG}-3d.jpg'))
deg = math.radians

# ---------------------------------------------------------------- 5, 6: the VHF set, by art_vhf.py and a spec
if FIG in (5, 6):
    if FIG == 5:
        spec = {'channel': '16', 'power': 'HI', 'note': 'Watch on 16 · 1 W in harbour, 25 W at sea',
                'parts': [['volume', 'volume'], ['squelch', 'squelch'], ['distress', 'DISTRESS, covered', 'red'], ['power', '1 W / 25 W'], ['ptt', 'press to talk']]}
    else:
        spec = {'channel': '16', 'power': 'HI', 'lines': ['DISTRESS SENT', 'CANCEL?  YES'], 'handset': 'lifted', 'note': 'False DSC alert sent',
                'parts': [['display', '1 · stop it on the set', 'red'], ['mic', '2 · then by voice on 16', 'blue']]}
    sys.argv = [sys.argv[0], '--', '--spec', json.dumps(spec), '--out', OUT, '--samples', str(SAMPLES), '--scale', str(SCALE)]
    exec(compile(open(os.path.join(HERE, 'art_vhf.py')).read(), 'art_vhf.py', 'exec'))
    if FIG == 6:   # the voice message under the note, as the card has it
        lp = os.path.splitext(OUT)[0] + '.labels.json'; L = json.load(open(lp))
        L['lines'] = ['ALL STATIONS × 3 · this is (name, call sign, MMSI)', 'position · CANCEL MY DISTRESS ALERT · OUT']
        json.dump(L, open(lp, 'w'))
    raise SystemExit(0)

C.reset()
M = K.mats()
labels, arrows, note, expo, extra = [], [], None, -0.5, {}

def helm_scene(sun_az=230, sun_el=35, sea='calm', wake=False):
    you = A.yacht('you').place(0, 0, heading=0)
    K.sea(sea, repeat=10); K.day_sky(sun_az=sun_az, sun_el=sun_el)
    if wake: K.wake(you, 40, 8, 1.0)
    return you

if FIG == 1:
    # in the base marina, stern-to the quay, neighbours either side; the plotter on the helm pod, no fix
    you = helm_scene(sun_az=255, sun_el=22)
    for i, x in enumerate((-4.7, 4.7, 9.4, -9.4)):
        P.clone_yacht(you, f'neighbour{i}', x, 0.6 * (i % 2), 0)
    C.obj('quay', C.rbox('quay', (80, 8, 2.2), 0.1, 2), C.concrete_mat('quay'), (0, -13.0, 0.3))
    K.breakwater((-120, 160), (60, 175), width=10.0, height=3.0)
    K.coast(distance=900, bearing=10, height=140, town=True)
    tx = A.tex('nav', 'nav1'); an = A.anchors('nav', 'nav1')
    objs, scr = A.plotter(tx, you.world((-1.25, -0.32, 4.6)), tilt=-14)
    K.camera(tuple(you.world((-1.72, -0.37, 4.98))), tuple(you.world((-1.2, -0.31, 4.73))), 34)
    labels = [(A.screen_point(scr, *an['nofix']), 'no fix', 'red'),
              (A.screen_point(scr, *an['boat']), 'last stored position')]
    note = 'Plotter screen at the berth, Sat 17:00'
    extra = {'lines': ['The boat is on its berth, 0.4 M from where it shows']}; expo = -0.5

elif FIG == 2:
    # motoring into a foul current: three displays on the helm pod, facing aft
    you = helm_scene(sun_az=200, sun_el=40, sea='breeze', wake=True)
    pod = you.world((-1.2, -0.32, 4.72))
    C.obj('pod-bar', C.rbox('pod-bar', (0.46, 0.10, 0.16), 0.03, 4), M['dark'], tuple(pod + Vector((0, 0.03, 0.0))))
    names = [('lcd-log', 'log 6.0 kn', None), ('lcd-sog', 'SOG 4.2 kn', 'blue'), ('lcd-depth', 'depth 42 m', None)]
    for i, (tn, txt, col) in enumerate(names):
        c = pod + Vector((-0.15 + i * 0.15, -0.025, 0.0))
        C.obj('bezel' + tn, C.rbox('bezel' + tn, (0.135, 0.02, 0.135), 0.008, 3), C.simple('bezel', '#121314', 0.3, coat=0.8), tuple(c))
        A.quad('screen-' + tn, 0.112, 0.112, A.tex('nav', tn), tuple(c + Vector((0, -0.0105, 0.0))), rot=(deg(90), 0, 0), emit=0.9, rough=0.15)
        labels.append((tuple(c + Vector((0, -0.01, 0.075))), txt, col) if col else (tuple(c + Vector((0, -0.01, 0.075))), txt))
    K.camera(tuple(you.world((-1.85, -0.36, 5.0))), tuple(pod + Vector((0, 0.3, 0.0))), 30)
    note = 'Log: through the water · SOG: over the ground'
    extra = {'lines': ['6.0 − 4.2: 1.8 kn of current against you']}; expo = -0.3

elif FIG == 3:
    # the steering compass on its pedestal, 090 under the lubber line; the plotter beside it: COG 098°T
    C.lathe('bowl', [(0.0, -0.02), (0.075, -0.02), (0.085, 0.0), (0.083, 0.012), (0.07, 0.016), (0.0, 0.016)], 96, M['dark'])
    C.lathe('pedestal', [(0.0, -0.75), (0.06, -0.75), (0.055, -0.03), (0.07, -0.02), (0.0, -0.02)], 64, C.simple('pedestal', '#cfd2d4', 0.25, 1.0))
    card = KI.disc('card', 0.058, KI.image_mat('card', os.path.join(KI.TEX, 'card.png'), 0.45), (0, 0, 0.022), normal='Z+')
    card.rotation_euler = (0, 0, deg(90))                       # 090 under the forward lubber line (+Y)
    C.obj('lubber', C.rbox('lubber', (0.003, 0.004, 0.02), 0.0005, 1), C.simple('lubber', '#e0201a', 0.4, coat=0.5), (0, 0.062, 0.03))
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=64, v_segments=32, radius=0.07)
    for v in list(bm.verts):
        if v.co.z < 0: v.co.z = 0
    me = bpy.data.meshes.new('dome'); bm.to_mesh(me); bm.free(); me.shade_smooth()
    C.obj('dome', me, KI.glass_mat('dome-glass'), (0, 0, 0.016))
    tx = A.tex('nav', 'nav3'); an = A.anchors('nav', 'nav3')
    C.cyl('post', 0.035, 0.04, 0.70, 32, C.simple('post', '#cfd2d4', 0.25, 1.0), (0.34, 0.12, -0.42))
    C.obj('pod', C.rbox('pod', (0.30, 0.13, 0.10), 0.03, 4), M['dark'], (0.34, 0.12, -0.04))
    objs, scr = A.plotter(tx, (0.34, 0.12, 0.0), tilt=-16, rotz=-14, width=0.26, pod=False)
    K.sea('breeze', center=(0, 0)); K.day_sky(sun_az=230, sun_el=45)
    for o in bpy.data.objects:
        if o.name.startswith(('ocean', 'far-sea')): o.location.z -= 1.4
    sole = KI.wall('sole', -1.5, 1.5, -1.5, 1.5, 0, M['teak'])
    sole.data.vertices.foreach_set('co', [-1.2, -1.5, -0.75, 1.2, -1.5, -0.75, 1.2, 1.5, -0.75, -1.2, 1.5, -0.75]); sole.data.update()
    K.camera((0.10, -0.55, 0.42), (0.16, 0.06, 0.03), 34)
    labels = [((0, 0.062, 0.075), 'compass 090°', 'blue'), (A.screen_point(scr, *an['cog']), 'plotter COG 098°T')]
    note = 'Compass 090°, plotter 098° true'
    extra = {'lines': ['3°E is variation, the other 5°E deviation']}; expo = -0.4

elif FIG == 4:
    # motoring north; a ferry on the starboard bow (050° relative) crossing west; the plotter's CPA alarm
    you = helm_scene(sun_az=150, sun_el=40, sea='breeze', wake=True)
    fp = A.hdg_vec(50) * 2000                                  # 1.08 M off: CPA 0.34 M in 4 min (6 kn, her 15 kn)
    root, vis, top = P.ferry((fp.x, fp.y), 270, 130.0)
    P.wake_decal((fp.x, fp.y), 270, 160, 24, stern=65, strength=1.0)
    K.coast(distance=7000, bearing=330, height=260, town=False)
    tx = A.tex('nav', 'nav4'); an = A.anchors('nav', 'nav4')
    objs, scr = A.plotter(tx, you.world((-1.25, -0.32, 4.6)), tilt=-14)
    eye = you.world((-1.78, -0.46, 5.0))
    look = eye + A.hdg_vec(12) * 10 + Vector((0, 0, -2.1))
    K.camera(tuple(eye), tuple(look), 18)
    labels = [(tuple(top + Vector((0, 0, 4))), 'Ferry'), (A.screen_point(scr, *an['alarm']), 'CPA alarm', 'red')]
    note = 'CPA alarm: it sounds while there is time to act'
    extra = {'lines': ['Her AIS target: CPA 0.34 M in 4 minutes']}; expo = -0.4

elif FIG in (7, 8, 9):
    # our yacht at night seen from dead ahead, 46 m off, from a dinghy's height
    sails = {'main': True, 'genoa': 'port', 'boom': 18} if FIG == 8 else None
    y = A.yacht('you', sails=sails).place(0, 0, heading=180)
    N.night_scene('calm'); N.cloth_furled(y)
    if FIG == 7:
        red, green = y.world((10.2, 0.58, 4.22)), y.world((10.2, -0.32, 4.22))       # on the pulpit legs
        A.lamp('red', red, 'r', 0.13, 12); A.lamp('green', green, 'g', 0.13, 12)
        st = y.world((5.45, 0.13, 11.5)); A.lamp('steaming', st, 'w', 0.17, 14, gain=1.4)
        ld = bpy.data.lights.new('steaming-deck', 'SPOT'); ld.energy = 140; ld.color = (1.0, 0.86, 0.66); ld.spot_size = deg(100); ld.spot_blend = 0.7
        lo = bpy.data.objects.new('steaming-deck', ld); C.col.objects.link(lo); lo.location = y.world((5.6, 0.13, 11.4))
        tgt = y.world((9.5, 0.13, 3.6)); lo.rotation_euler = (tgt - lo.location).to_track_quat('-Z', 'Y').to_euler()
        mid = (red + green) / 2
        labels = [(tuple(st + Vector((0, 0, 0.6))), 'steaming light'), (tuple(mid + Vector((0, 0, 0.6))), 'sidelights')]
        note = 'Engine on: NAV + STEAMING'
        extra = {'bloom': 1.0, 'lines': ['Sails up or not, she is a power-driven vessel']}
    elif FIG == 8:
        tr, tg = y.world((5.06, 0.32, 20.75)), y.world((5.06, -0.06, 20.75))
        A.lamp('tri-red', tr, 'r', 0.2, 14); A.lamp('tri-green', tg, 'g', 0.2, 14)
        labels = [(tuple((tr + tg) / 2 + Vector((0, 0, 0.6))), 'tricolour')]
        note = 'Sail alone: TRICOLOUR, or NAV'
        extra = {'bloom': 1.0, 'lines': ['Never both']}
    else:
        top = y.world((5.06, 0.13, 20.8)); A.lamp('anchor-light', top, 'w', 0.14, 30, gain=0.6)
        labels = [(tuple(top + Vector((0, 0, 0.6))), 'all-round white')]
        note = 'At anchor: ANCHOR only'
        extra = {'bloom': 1.0, 'lines': ['Sidelights off: they mean under way']}
    bow = y.world((10.8, 0.13, 2.0))
    eye = Vector((bow.x + 0.5, bow.y - 38.0, 2.0)); look = Vector((y.root.location.x, y.root.location.y, 9.5))
    K.camera(tuple(eye), tuple(look), 38)
    expo = 0.8

C.render(OUT, SAMPLES, SCALE, expo, labels, note, space='blender', arrows=arrows, extra=extra)
