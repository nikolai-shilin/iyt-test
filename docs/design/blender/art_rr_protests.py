# Article racing-rules/protests: eight figures as Blender renders (art_rr_b_kit).
#    1  protesting: Blue on port fails to keep clear; you hail "Protest" and show a red flag on the backstay
#    2  the red flag on your backstay, close up
#    3  the written protest: a protest form filled in, stamped in at the race office
#    4  the hearing: the protest form, model boats, the chairman's notes and the rule book on the table
#    5  three boats on a run into the zone of the leeward mark: Green forces Red onto you
#    6  decisions: you protest Blue, but your own luff broke rule 16.1
#    7  redress: the committee boat dragged, the line moved, a wrong OCS
#    8  arbitration: the arbitrator's table, one chair per boat, no witnesses
# Paper textures by art_rr_b_tex.py (system Python), run on its own when one is missing.
#   blender --background --factory-startup --python docs/design/blender/art_rr_protests.py -- --fig 1 [--samples 144] [--scale 100]
import os, sys, json, math
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import bpy
from mathutils import Vector, Matrix
import common as C, kit as K
import kit_instruments as KI
import art_rr_b_kit as R

arg = C.cli(); FIG = arg('--fig', 1); SAMPLES = arg('--samples', 144); R.SCALE = arg('--scale', 100)
ART = 'protests'; OUT = arg('--out', os.path.join(R.ARTS, ART, f'{FIG}-3d.jpg'))
FIGS = {x['n']: x for x in json.load(open(os.path.join(HERE, '..', 'article-figs', f'racing-rules-{ART}.json')))['figs']}
deg = math.radians

# ---------------------------------------------------------------- the race office and the jury room
def paper(name, tex, w, h, centre, rot=0.0, z=0.0):
    """A sheet lying flat, image top towards +Y turned by `rot` degrees; returns px(u, v) -> world point."""
    me = bpy.data.meshes.new(name); x, y = w / 2, h / 2
    me.from_pydata([(-x, -y, 0), (x, -y, 0), (x, y, 0), (-x, y, 0)], [], [(0, 1, 2, 3)])
    me.uv_layers.new(name='UVMap').data.foreach_set('uv', [0, 0, 1, 0, 1, 1, 0, 1])
    o = C.obj(name, me, KI.image_mat(name, tex, 0.75), (centre[0], centre[1], z + 0.0015)); o.rotation_euler = (0, 0, deg(rot))
    return o

def px_on(o, tex, u, v, w, h):
    bpy.context.view_layer.update(); img = bpy.data.images.load(tex, check_existing=True); iw, ih = img.size
    return o.matrix_world @ Vector(((u / iw - 0.5) * w, (0.5 - v / ih) * h, 0.002))

def room(table=(1.8, 0.95), cloth='#1f3550', top=0.76):
    """A plain room: a floor, a wall behind, a table with a cloth, soft light from a window and the ceiling."""
    C.obj('floor', C.rbox('floor', (12, 12, 0.02), 0, 1), C.simple('floor', '#8d8478', 0.7), (0, 0, -0.01))
    KI.wall('wall', -6, 6, 0, 3, 2.2, C.simple('wall', '#d9d6cf', 0.9))
    tw, td = table
    C.obj('table', C.rbox('table', (tw, td, 0.04), 0.01, 2), C.simple('cloth', cloth, 0.9, sheen=0.5), (0, 0, top - 0.02))
    for sx in (-1, 1):
        for sy in (-1, 1):
            C.cyl('leg', 0.025, 0.025, top - 0.04, 12, C.simple('leg', '#2a2c30', 0.4, 0.6), (sx * (tw / 2 - 0.08), sy * (td / 2 - 0.08), (top - 0.04) / 2))
    K.day_sky(sun_az=150, sun_el=40, strength=0.05)
    KI.area_light((1.6, -2.2, 2.6), (0, 0, top), 260, 2.2)
    KI.area_light((-2.0, -1.0, 2.4), (0, 0, top), 90, 2.0, (0.85, 0.9, 1.0))
    KI.area_light((0, 0, 2.9), (0, 0, top), 120, 1.6)
    return top

def model_boat(name, colour, heading, at, sails=True, k=0.022):
    yt = R.load(name, colour, {'main': True, 'genoa': 'starboard' if heading > 180 else 'port', 'boom': (12 if heading > 180 else -12)} if sails else None)
    yt.place(at[0], at[1], heading=heading); yt.root.scale = (k,) * 3; yt.root.location.z = at[2] + K.WL * k
    bpy.context.view_layer.update(); return yt

def pen(at, rot):
    p = bpy.data.objects.new('pen', None); C.col.objects.link(p)
    C.cyl('pen-body', 0.0055, 0.0055, 0.13, 16, C.simple('pen-body', '#1d2a4a', 0.3, coat=0.8), (0, 0, 0)).parent = p
    C.cyl('pen-tip', 0.0055, 0.001, 0.02, 16, C.simple('pen-tip', '#c9c9c9', 0.3, 0.9), (0, 0, 0.075)).parent = p
    p.rotation_euler = (deg(90), 0, deg(rot)); p.location = Vector(at) + Vector((0, 0, 0.0056))
    return p

def chair(at, facing):
    m = C.simple('chair', '#3b3f45', 0.5); f = R.fwd(facing); r = R.right(facing)
    seat = C.obj('seat', C.rbox('seat', (0.46, 0.44, 0.05), 0.01, 2), m, tuple(Vector(at) + Vector((0, 0, 0.46)))); seat.rotation_euler = (0, 0, deg(90 - facing))
    back = C.obj('back', C.rbox('back', (0.05, 0.44, 0.45), 0.01, 2), m, tuple(Vector(at) - f * 0.22 + Vector((0, 0, 0.72)))); back.rotation_euler = (0, 0, deg(90 - facing))
    for a in (-1, 1):
        for b in (-1, 1):
            C.cyl('chair-leg', 0.015, 0.015, 0.46, 8, m, tuple(Vector(at) + f * a * 0.19 + r * b * 0.19 + Vector((0, 0, 0.23))))
    return Vector(at) + Vector((0, 0, 0.95)) - f * 0.22

def tex(name):
    R.need_tex(ART, [name]); return R.tex_path(ART, name)

# ---------------------------------------------------------------- figures
def fig_form():
    t = room((1.6, 0.8), '#5a4632')
    tf = tex('protest-form'); w, h = 0.21, 0.297
    o = paper('form', tf, w, h, (0.0, 0.0), -4, t)
    pen(px_on(o, tf, 1050, 1300, w, h), 35)
    P = lambda u, v: tuple(px_on(o, tf, u, v, w, h))
    K.camera((0.0, -0.36, t + 0.66), (0.0, -0.01, t), 46)
    L = [(P(250, 480), 'who: you, the protestor', 'blue', (-250, -10)), (P(900, 700), 'against whom: the protestee', None, (270, -40)),
         (P(250, 920), 'what incident: where, when, what', None, (-250, 20)), (P(1000, 1125), 'hailed and a red flag', None, (220, 30)),
         (P(880, 1600), 'race office, within the time limit', 'red', (-260, 10))]
    C.render(OUT, SAMPLES, R.SCALE, -0.4, L, 'A valid protest · in writing, on time', space='blender')

def fig_hearing():
    t = room((1.8, 0.95))
    tf = tex('protest-form'); fo = paper('form', tf, 0.21, 0.297, (-0.62, -0.12), 8, t)
    tn = tex('notes'); no = paper('notes', tn, 0.2, 0.28, (0.6, -0.1), -6, t)
    pen(px_on(no, tn, 780, 1150, 0.2, 0.28), 60)
    tr = tex('rulebook'); C.obj('book-block', C.rbox('book', (0.15, 0.21, 0.018), 0.002, 2), C.simple('pages', '#efebe0', 0.8), (0.48, 0.25, t + 0.009)).rotation_euler = (0, 0, deg(-12))
    rb = paper('rulebook', tr, 0.15, 0.21, (0.48, 0.25), -12, t + 0.0185)
    tern = model_boat('tern', None, 315, (0.08, -0.05, t)); blue = model_boat('blue', R.HULL['Blue'], 45, (-0.22, -0.02, t))
    K.camera((0.0, -1.45, t + 1.2), (0.0, 0.06, t), 36)
    L = [(tuple(px_on(fo, tf, 620, 300, 0.21, 0.297)), '1 · valid? the written protest'), (tuple(tern.world((K.MAST.x, K.MAST.y, 15))), '2 · evidence: model boats', 'blue'),
         (tuple(px_on(no, tn, 500, 700, 0.2, 0.28)), '3 · the facts found'), (tuple(px_on(rb, tr, 450, 300, 0.15, 0.21)), '4 · rules applied: decision', 'red')]
    C.render(OUT, SAMPLES, R.SCALE, -0.4, L, 'Order of a hearing · validity first, then the facts', space='blender')

def fig_arbitration():
    t = room((1.3, 0.85), '#2b3b2e')
    tf = tex('protest-form'); fo = paper('form', tf, 0.21, 0.297, (-0.32, -0.08), 5, t)
    ts = tex('penalty-slip'); so = paper('slip', ts, 0.21, 0.148, (0.3, -0.16), -6, t)
    # the desk card: a tent, its face towards the camera
    td = tex('desk-card'); cw, ch = 0.36, 0.11
    face = bpy.data.meshes.new('card'); face.from_pydata([(-cw / 2, 0, 0), (cw / 2, 0, 0), (cw / 2, 0, ch), (-cw / 2, 0, ch)], [], [(0, 1, 2, 3)])
    face.uv_layers.new(name='UVMap').data.foreach_set('uv', [0, 0, 1, 0, 1, 1, 0, 1])
    card = C.obj('card', face, KI.image_mat('card', td, 0.5), (0.0, 0.2, t)); card.rotation_euler = (deg(-18), 0, 0)
    back = C.obj('card-back', C.rbox('cb', (cw, 0.002, ch), 0, 1), C.simple('card-back', '#f2f2ee', 0.6), (0.0, 0.24, t + ch / 2 - 0.004)); back.rotation_euler = (deg(18), 0, 0)
    a = chair((0.0, 0.75, 0), 180)
    p1 = chair((-0.35, -0.75, 0), 0); p2 = chair((0.35, -0.75, 0), 0)
    K.camera((0.25, -2.25, t + 1.25), (0.0, 0.05, t - 0.05), 32)
    L = [(tuple(a + Vector((0, 0, 0.05))), 'one arbitrator'), (tuple(card.matrix_world @ Vector((0, 0, ch))), 'only if the NoR or SI say so', 'blue'),
         (tuple((p1 + p2) / 2 + Vector((0, 0, 0.0))), 'one per boat, who was on board', None, (0, 60)),
         (tuple(px_on(so, ts, 620, 120, 0.21, 0.148)), 'opinion: penalty, withdrawal or hearing', 'red', (170, 40))]
    C.render(OUT, SAMPLES, R.SCALE, -0.4, L, 'Arbitration (Appendix T) · no witnesses', space='blender')

def fig_flag_close():
    R.need_tex(ART, ['flag-red'])
    K.sea('breeze', size=36.0, repeat=10)
    you = R.boat({'x': 160, 'y': 100, 'hdg': 300, 'you': True}, 0, name='you'); R.wake(you)
    fl, a = R.backstay_flag(you, R.tex_path(ART, 'flag-red'), t=0.32, w=0.8, h=0.56, stream=R.fwd(150))
    eye = you.world((-11.5, -6.5, 7.8)); K.camera(tuple(eye), tuple(a + Vector((0, 0, -1.6))), 30); K.day_sky(sun_az=215, sun_el=42)
    L = [(tuple(a + Vector((0, 0, 0.42))), 'Red flag: hull over 6 m', 'red')]
    C.render(OUT, SAMPLES, R.SCALE, -0.6, L, FIGS[2]['fig']['note'], space='blender')

def red_flag(ctx):
    R.need_tex(ART, ['flag-red'])
    you = ctx['boats']['You']
    fl, a = R.backstay_flag(you, R.tex_path(ART, 'flag-red'), t=0.42, w=1.4, h=1.0, stream=R.fwd(180))
    ctx['labels'].append((tuple(a), 'red flag', 'red', (-150, 50)))

def dragged(ctx):
    """Figure 7: the line as laid (pin to the committee boat's first spot) and as it was after she dragged her
    anchor; the committee boat at her new spot, her anchor line trailing back."""
    a, b0, b1 = R.W(40, 112), R.W(280, 112), R.W(300, 146)
    R.dashes('line-dragged', [a.xy, (b1 - (b1 - a).normalized() * 3).xy], 3.0, 2.6, 0.5, '#ff6a5a', 0.95)
    root, vis, tp, deck = R.committee_boat(300, 146, 0.0)
    R.dashes('drag', [b0.xy, (b1 + R.fwd(0) * 8).xy], 1.4, 1.4, 0.35, '#ffd21a', 0.95)
    ctx['labels'] += [(tuple(tp + Vector((0, 0, 1))), 'Committee boat: dragged', 'red'), (tuple(a.lerp(b1, 0.42) + Vector((0, 0, 0.3))), 'the line after', 'red', (0, 70)),
                      (tuple(b0 + Vector((0, 0, 0.3))), 'where she was anchored')]
    ctx['pts'] += [b1, b0, tp]

CFG = {
    1: dict(boats={'You': dict(text='You: hail "Protest" at once', color='blue'), 'Blue': dict(text='Blue: port tack', color='red')}, extra=red_flag,
            cam=dict(box=(250, 240, 1030, 710)), note='Hail "Protest" at once; over 6 m, a red flag too'),
    5: dict(boats={'You': dict(text='You', color='blue', off=(170, -10)), 'Red': dict(text='Red: forced onto you', off=(30, -70)), 'Green': dict(text='Green: not a party', color='red', off=(-200, 10))},
            mark=dict(text='Leeward mark'), zone_text='zone', cam=dict(box=(200, 230, 1080, 720)),
            note='Green forced Red onto you, but is not a party'),
    6: dict(boats={'You': dict(text='You: your luff broke rule 16.1', color='blue'), 'Blue': dict(text='Blue: protested')},
            cam=dict(box=(260, 240, 1020, 710)), note='You protest Blue, but your luff broke rule 16.1'),
    7: dict(boats={'You': dict(text='You: scored OCS', color='blue')}, line=dict(text='the line as laid', at=0.3, cb=False), track=None, extra=dragged,
            cam=dict(box=(110, 215, 1170, 720)), note='The committee boat dragged: a wrong OCS, so redress'),
}
C.reset()
if FIG == 2: fig_flag_close()
elif FIG == 3: fig_form()
elif FIG == 4: fig_hearing()
elif FIG == 8: fig_arbitration()
else: R.race(FIGS[FIG]['fig'], CFG[FIG], OUT, SAMPLES)
