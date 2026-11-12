# Article racing-rules/propulsion: seven figures as Blender renders (art_rr_b_kit).
#    1  rule 42.1: you back the mainsail at the line and move astern; Grey comes up on starboard (rule 21)
#    2  rule 42.2: gybe after gybe down an empty run, the foam track zigzagging behind you
#    3  rule 42.3: stopped head to wind, the sector you may scull out of shaded on the water
#    4  rule 42.3: aground on a sandbank, the crew in the water pushing the bow off
#    5  enforcement: the jury RIB with a yellow flag, flag O on the committee boat
#    6  no wind, foul tide: you at anchor below the windward mark, Blue and Red drifting back
#    7  flag Y on the committee boat: lifejackets on
#   blender --background --factory-startup --python docs/design/blender/art_rr_propulsion.py -- --fig 1 [--samples 144] [--scale 100]
import os, sys, json, math
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import bpy
from mathutils import Vector
import common as C, kit as K
import art_rr_b_kit as R
import q_encounter_props as P

arg = C.cli(); FIG = arg('--fig', 1); SAMPLES = arg('--samples', 144); R.SCALE = arg('--scale', 100)
ART = 'propulsion'; OUT = arg('--out', os.path.join(R.ARTS, ART, f'{FIG}-3d.jpg'))
FIGS = {x['n']: x for x in json.load(open(os.path.join(HERE, '..', 'article-figs', f'racing-rules-{ART}.json')))['figs']}

def scull_sector():
    """Figure 3 (a 'sail' figure, no race): you stopped head to wind at the middle, the 90° sector either side
    of the wind shaded red on the water; its edge is as far as sculling may turn you."""
    K.sea('breeze', size=36.0, repeat=10)
    you = R.boat({'x': 160, 'y': 100, 'hdg': 15, 'you': True}, 0, name='you')
    c = R.W(160, 100); Rr = 34.0; n = 30
    fan = [c.xy] + [(c + R.fwd(-45 + 90 * k / n) * Rr).xy for k in range(n + 1)]
    R.polygon('sector', fan, '#ff4a3a', 0.13, z=0.27)
    R.dashes('sector-edge', [(c + R.fwd(-45) * Rr).xy, c.xy, (c + R.fwd(45) * Rr).xy], 2.4, 2.0, 0.45, '#ffb0a8', 0.9)
    R.dashes('heading', [(R.bow(you) + R.fwd(15) * 2).xy, (c + R.fwd(15) * 26).xy], 1.6, 1.4, 0.35, '#ffd21a', 0.95)
    L = [(tuple(R.top(you)), 'You: stopped head to wind', 'blue'),
         (tuple(c + R.fwd(45) * 30 + Vector((0, 0, 0.3))), 'scull to here, no further', None, (60, -20)),
         (tuple(c + R.fwd(0) * 26 + Vector((0, 0, 0.3))), 'within 45° of the wind', 'red', (-40, -30))]
    pts = [c + R.fwd(a) * Rr for a in (-45, 0, 45)] + [c - R.fwd(15) * 10, R.top(you)]
    cam, D = R.drone(pts, 195, 60, 35, box=(260, 230, 1020, 720))
    arrows = []; R.wind_arrow(arrows, L, D, at=(170, 560))
    C.render(OUT, SAMPLES, R.SCALE, -0.6, L, FIGS[3]['fig']['note'], space='blender', arrows=arrows)

def sandbank(ctx):
    """Figure 4: the bank (y > 120 in the figure) awash, sand under a pale shallow fringe; two of the crew in the
    water at the bow, pushing her off."""
    y0 = R.W(0, 120).y
    sand = C.simple('sand', '#cdb98c', 0.9)
    me = bpy.data.meshes.new('bank'); xs = [-200 + 4 * k for k in range(101)]
    edge = [(x, y0 - 1.2 * math.sin(x * 0.11) - 0.8 * math.sin(x * 0.31 + 1)) for x in xs]
    n = len(edge); vs = [(x, y, 0.45) for x, y in edge] + [(x, y0 - 120, 0.45) for x in xs]
    me.from_pydata(vs, [], [(k, k + 1, n + k + 1, n + k) for k in range(n - 1)]); C.obj('bank', me, sand)
    sh = bpy.data.meshes.new('shallows'); sv = [(x, y + 6, 0.42) for x, y in edge] + [(x, y - 0.5, 0.42) for x, y in edge]
    sh.from_pydata(sv, [], [(k, k + 1, n + k + 1, n + k) for k in range(n - 1)])
    so = C.obj('shallows', sh, R._alpha_mat('shallows', '#7fe0d0', 0.35, emit=0.1)); so.visible_shadow = False
    R.dashes('bank-edge', edge, 4.0, 0.0, 0.6, '#f2efe0', 0.6, z=0.47)
    you = ctx['boats']['You']; b = R.bow(you)
    for s in (-1, 1):
        q = b + R.fwd(you.hdg) * 0.8 + R.right(you.hdg) * s * 1.1; q.z = -0.55
        P.person(tuple(q), you.hdg + 180, arms='side', top='#d2482a' if s < 0 else '#2a6fd2')
        P.ring_foam(Vector((q.x, q.y, 0)), 0.4)
    ctx['labels'].append((tuple(b + Vector((0, 0, 2.2))), 'crew pushing by hand: allowed', None, (190, -40)))
    ctx['labels'].append((tuple(R.W(200, 150, 0.2)), 'Sandbank'))
    ctx['pts'] += [R.W(200, 150), b]

def jury_and_o():
    """Figure 5: the committee boat flying O on a staff, the jury RIB close by, a judge holding up a yellow flag."""
    R.need_tex(ART, ['flag-O', 'flag-yellow'])
    K.sea('calm', size=30.0, repeat=10)
    root, vis, tp, deck = R.committee_boat(160, 100, 0.0, 14.0)
    bpy.context.view_layer.update(); lo, hi = K.bbox(vis)
    t = R.staff(Vector((hi.x - 0.3, (lo.y + hi.y) / 2 - 1.5, deck)), hi.z + 1.4 - deck)
    oa = R.hoist(t, R.fwd(180), [(R.tex_path(ART, 'flag-O'), '')], 1.5, 1.0)[0]
    rp = Vector((hi.x + 4, lo.y - 9, 0))
    rr, rv, rt = P.rib((rp.x, rp.y), 330, 5.5)
    P.wake_decal((rp.x, rp.y), 330, 18, 2.5, stern=2.8, strength=0.7)
    j = P.person(tuple(rp + Vector((0, 0, 0.55)) - R.fwd(330) * 0.6), 330 - 120, arms='wave', top='#2b3b55')
    sh = rp + Vector((0, 0, 0.55)) - R.fwd(330) * 0.6
    hand = sh + Vector((0, 0, 2.05)) + R.right(330 - 120) * 0.45
    C.tube('flag-stick', [hand - Vector((0, 0, 0.3)), hand + Vector((0, 0, 0.75))], 0.015, 6, 1.0, C.simple('stick', '#c9c2b0', 0.6))
    R.flag_mesh('judge-flag', hand + Vector((0, 0, 0.75)), R.fwd(200), 1.0, 0.7, tex=R.tex_path(ART, 'flag-yellow'))
    ya = hand + Vector((0, 0, 0.4)) + R.fwd(200) * 0.5
    pts = [oa + Vector((0, 0.8, 0.6)), oa - Vector((0, 0.8, 0.6)), ya + Vector((0, 0, 0.9)), rp + Vector((3, 0, 0)), rp - Vector((3, 0, 0)), Vector((hi.x, lo.y, deck)), Vector((hi.x, hi.y, deck))]
    R.drone(pts, 100, 9, 40, box=(150, 230, 1130, 720), sun=150, ground=False)
    L = [(tuple(oa + Vector((0, 0, 0.55))), 'Flag O: pumping, rocking, ooching allowed'), (tuple(ya + Vector((0, 0, 0.3))), 'Yellow flag: a rule 42 penalty', 'red')]
    C.render(OUT, SAMPLES, R.SCALE, -0.5, L, 'Rule 42 · judges on the water, class rules by flag', space='blender')

def anchored(ctx):
    you = ctx['boats']['You']; P.anchor_chain(you, you.hdg, 9.0)
    a0 = R.W(268, 62, 0.5); a1 = R.W(268, 97, 0.5)
    ctx['tide'] = (a0, a1)

def tide_arrow(ctx):
    a0, a1 = ctx['tide']; ctx['arrows'].append((tuple(a0), tuple(a1), 'red')); ctx['labels'].append((tuple(a0 + Vector((0, 0, 1))), 'Tide', 'red'))

CFG = {
    1: dict(boats={'You': dict(text='You: main backed, moving astern', color='blue', boom=(1, 62), heel=0, genoa=False, astern=True),
                   'Grey': dict(text='Grey: keep clear of her')},
            line=dict(text='Start line', at=0.18, cb_text='Committee boat'), cam=dict(box=(110, 215, 1170, 720)),
            note='A backed mainsail uses the wind · moving astern, you keep clear (rule 21)'),
    2: dict(boats={'You': dict(text='You: gybe after gybe', color='red', wake=False)}, track=dict(w=2.6),
            cam=dict(box=(300, 230, 980, 720)), note='Steady wind, nobody near: gybe after gybe is propulsion'),
    4: dict(boats={'You': dict(text='You: aground', color='blue', wake=False, heel=-6)}, obstruction=sandbank, sea='calm',
            cam=dict(box=(220, 230, 1060, 720)), note='Aground: the crew may push her off · no tow under engine'),
    6: dict(boats={'You': dict(text='You: at anchor, holding', color='blue', still=True, boom=(-1, 6), heel=0, genoa=False),
                   'Blue': dict(text='Blue: drifting back', astern=True, boom=(-1, 6), heel=0, genoa=False),
                   'Red': dict(text='Red: drifting back', astern=True, boom=(1, 6), heel=0, genoa=False)},
            mark=dict(text='Windward mark'), sea='calm', wind=False, extra=anchored, after=tide_arrow,
            note='No wind, foul tide: you anchor, the others drift back'),
    7: dict(flags=[('Y', 'Y: wear lifejackets', 1)], note='Flag Y with one sound: lifejackets for this race', spacing=3.0,
            cam=dict(box=(300, 220, 980, 700))),
}
C.reset()
if FIG == 3: scull_sector()
elif FIG == 5: jury_and_o()
elif 'flags' in CFG[FIG]: R.flags_scene(ART, CFG[FIG]['flags'], CFG[FIG], OUT, SAMPLES)
else: R.race(FIGS[FIG]['fig'], CFG[FIG], OUT, SAMPLES)
