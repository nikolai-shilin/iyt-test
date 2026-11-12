# Article racing-rules/penalties: nine figures as Blender renders (art_rr_b_kit).
#    1  two turns: you on port tack fail to keep clear of Grey on starboard
#    2  one turn: you touched the mark
#    3  taking the turns: the foam track of one turn on a run (gybe, luff, tack, bear away)
#    4  turns beyond the finishing line: come back to the course side, cross again
#    5  serious damage: your bow in Grey's side; retire, turns do not count
#    6  compelled: Blue pushes you onto the mark
#    7  within mark-room: Yellow leaves you too little room at the mark
#    8  the yellow flag (Scoring Penalty) and the red flag (a protest) on two backstays
#    9  the preparatory flags I, Z, U and black on the committee boat
#   blender --background --factory-startup --python docs/design/blender/art_rr_penalties.py -- --fig 1 [--samples 144] [--scale 100]
import os, sys, json, math
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import bpy
from mathutils import Vector
import common as C, kit as K
import art_rr_b_kit as R

arg = C.cli(); FIG = arg('--fig', 1); SAMPLES = arg('--samples', 144); R.SCALE = arg('--scale', 100)
ART = 'penalties'; OUT = arg('--out', os.path.join(R.ARTS, ART, f'{FIG}-3d.jpg'))
FIGS = {x['n']: x for x in json.load(open(os.path.join(HERE, '..', 'article-figs', f'racing-rules-{ART}.json')))['figs']}

def turn_words(ctx):
    L = ctx['labels']
    L.append((tuple(R.W(176, 124, 0.3)), 'gybe', None, (90, 10)))
    L.append((tuple(R.W(197, 82, 0.3)), 'luff', None, (90, 0)))
    L.append((tuple(R.W(165, 63, 0.3)), 'tack', None, (0, -40)))
    L.append((tuple(R.W(146, 88, 0.3)), 'bear away', None, (-110, 0)))

def hole(ctx):
    """Your bow in Grey's port side: a dark split in her topsides, chips of gelcoat on the water."""
    you, grey = ctx['boats']['You'], ctx['boats']['Grey']
    p = R.bow(you) + Vector((0, 0, 0.9)); n = R.right(grey.hdg) * -1
    o = C.obj('hole', K._sphere('hole', 0.6), C.simple('hole', '#0d0e10', 0.9), tuple(p)); o.scale = (1.4, 1.4, 0.7)
    for k in range(9):
        q = R.bow(you) + R.fwd(grey.hdg + 180) * (1.2 + k * 0.9) + n * (0.8 + (k % 3) * 0.6); q.z = 0.3
        c = C.obj('chip', C.rbox('chip', (0.25, 0.12, 0.03), 0.0, 1), C.simple('chip', '#e8e8e2', 0.6), tuple(q)); c.rotation_euler = (0, 0, k)
    ctx['labels'].append((tuple(p + Vector((0, 0, 0.4))), 'serious damage', 'red', (-160, 70)))

def two_backstays():
    """Figure 8: you and Grey reaching side by side, a yellow flag on your backstay, a red one on Grey's."""
    R.need_tex(ART, ['flag-yellow', 'flag-red'])
    K.sea('breeze', size=36.0, repeat=10)
    you = R.boat({'x': 160, 'y': 100, 'hdg': 300, 'you': True}, 0, name='you')
    grey = R.boat({'x': 140, 'y': 72, 'hdg': 300, 'label': 'Grey'}, 0, name='grey')
    R.wake(you); R.wake(grey)
    _, ya = R.backstay_flag(you, R.tex_path(ART, 'flag-yellow'), t=0.30, w=1.2, h=0.8, stream=R.fwd(160))
    _, ra = R.backstay_flag(grey, R.tex_path(ART, 'flag-red'), t=0.30, w=1.2, h=0.8, stream=R.fwd(160))
    mid = (you.centre + grey.centre) / 2
    eye = mid - R.fwd(300) * 42 + R.right(300) * 16 + Vector((0, 0, 13)); look = mid + R.fwd(300) * 2 + Vector((0, 0, 5.5))
    K.camera(tuple(eye), tuple(look), 40); K.day_sky(sun_az=200, sun_el=40)
    L = [(tuple(ya + Vector((0, 0, 0.45))), 'Yellow flag: you took the Scoring Penalty', 'blue'), (tuple(ra + Vector((0, 0, 0.45))), 'Red flag: Grey protests', 'red')]
    C.render(OUT, SAMPLES, R.SCALE, -0.6, L, 'Scoring Penalty · a yellow flag instead of turns', space='blender')

CFG = {
    1: dict(boats={'You': dict(text='You: port tack, failed to keep clear', color='blue'), 'Grey': dict(text='Grey: starboard tack')},
            note='A Part 2 rule broken: a Two-Turns Penalty'),
    2: dict(boats={'You': dict(text='You: touched the mark', color='blue')}, mark=dict(text='Mark'),
            note='Touching a mark (rule 31): a One-Turn Penalty', cam=dict(box=(300, 260, 980, 680))),
    3: dict(boats={'You': dict(text='You', color='blue', wake=False)}, extra=turn_words, cam=dict(box=(260, 230, 1020, 700)),
            note='Each turn: one tack and one gybe, both turns the same way'),
    4: dict(boats={'You': dict(text='You: back to the course side, cross again', color='blue', wake=False)},
            line=dict(text='Finish line', at=0.25, cb_text='Committee boat'), cam=dict(box=(110, 215, 1170, 720)),
            note='Turns beyond the line: come back, then cross it again'),
    5: dict(boats={'You': dict(text='You: retire', color='blue', nudge=(1.9, -1.9), wake_len=24), 'Grey': dict(text='Grey: holed')},
            extra=hole, cam=dict(box=(320, 260, 960, 690)), note='Serious damage: retire, turns do not count'),
    6: dict(boats={'You': dict(text='You: forced onto the mark', color='blue'), 'Blue': dict(text='Blue: pushes you', color='red')},
            mark=dict(text='Mark'), cam=dict(box=(260, 240, 1020, 700)), note='Compelled by Blue: exonerated, no penalty'),
    7: dict(boats={'You': dict(text='You: within your mark-room', color='blue', off=(170, 40)), 'Yellow': dict(text='Yellow: too little room', color='red')},
            mark=dict(text='Mark'), cam=dict(box=(260, 240, 1020, 700)), note='Sailing within mark-room: exonerated, no penalty'),
    9: dict(flags=[('I', 'I: round an end', 1), ('Z', 'Z: 20 %', 2), ('U', 'U: UFD', 3), ('black', 'Black: BFD', 4)], spacing=3.0,
            note='Starting penalties · turns cannot fix them'),
}
C.reset()
if FIG == 8: two_backstays()
elif 'flags' in CFG[FIG]: R.flags_scene(ART, CFG[FIG]['flags'], CFG[FIG], OUT, SAMPLES)
else: R.race(FIGS[FIG]['fig'], CFG[FIG], OUT, SAMPLES)
