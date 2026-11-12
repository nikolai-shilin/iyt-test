# Article racing-rules/starting: seven figures as Blender renders (art_rr_b_kit): the flags on the committee boat,
# and the start in a drone view.
#    1  P and the orange flag on the committee boat          2  the preparatory flags I, Z, U and black
#    3  the triangle (the ends of the line and the first mark): stay out of it in the last minute
#    4  over at the gun: back below the line, then start    5  recalls: X and First Substitute
#    6  AP over H, N over A                                 7  before the gun: a boat reaching in to windward at the committee boat
#   blender --background --factory-startup --python docs/design/blender/art_rr_starting.py -- --fig 1 [--samples 144] [--scale 100]
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import bpy
from mathutils import Vector
import common as C, kit as K
import art_rr_b_kit as R

arg = C.cli(); FIG = arg('--fig', 1); SAMPLES = arg('--samples', 144); R.SCALE = arg('--scale', 100)
ART = 'starting'; OUT = arg('--out', os.path.join(R.ARTS, ART, f'{FIG}-3d.jpg'))
FIGS = {x['n']: x for x in json.load(open(os.path.join(HERE, '..', 'article-figs', f'racing-rules-{ART}.json')))['figs']}

def triangle(ctx):
    a, m, b = R.W(40, 135), R.W(160, 40), R.W(280, 135)
    R.polygon('triangle', [a.xy, m.xy, b.xy], '#ff4a3a', 0.10, z=0.27)
    R.dashes('triangle-edge', [a.xy, m.xy, b.xy], 2.6, 2.2, 0.45, '#ffb0a8', 0.9)

def over_points(ctx):
    ctx['labels'].append((tuple(R.W(168, 89, 0.3)), 'over at the gun', 'red', (170, -30)))
    ctx['labels'].append((tuple(R.W(140, 139, 0.3)), 'hull back on the pre-start side', None, (-60, 130)))

CFG = {
    1: dict(flags=[('P', 'P: up at 4, down at 1', 1), ('orange', 'Orange: this end of the line', 2)],
            note='The sequence · 5, 4, 1, go: times from the flags', spacing=4.0),
    2: dict(flags=[('I', 'I: round an end', 1), ('Z', 'Z: 20 % penalty', 2), ('U', 'U: disqualified', 3), ('black', 'Black: disqualified', 4)],
            note='Preparatory flags · what the last minute can cost', spacing=3.3),
    3: dict(boats={'You': dict(text='You: in the triangle', color='red')}, mark=dict(text='First mark'), track=None, extra=triangle,
            line=dict(text='Start line', at=0.25, cb_text='Committee boat')),
    4: dict(boats={'You': dict(text='You: now starting', color='blue', wake=False)}, track=dict(split=True), extra=over_points,
            line=dict(text='Start line', at=0.12, cb_text='Committee boat')),
    5: dict(flags=[('X', 'X: individual recall', 1), ('first-sub', 'First Substitute: general recall', 2)],
            note='Recalls · X for some, First Substitute for all', spacing=4.0),
    6: dict(flags=[('AP', 'AP: postponed', 1), ('H', 'over H: signals ashore', 1), ('N', 'N: abandoned', 2), ('A', 'over A: no more today', 2)],
            note='AP before the start, N after it', spacing=4.6),
    7: dict(boats={'You': dict(text='You: leeward, may hold your course', color='blue', off=(-300, 40)), 'A': dict(text='A: windward, no room', color='red')},
            line=dict(text='Start line', at=0.3, cb_text='Committee boat')),
}
C.reset()
cfg = CFG[FIG]
if 'flags' in cfg: R.flags_scene(ART, cfg['flags'], cfg, OUT, SAMPLES)
else: R.race(FIGS[FIG]['fig'], cfg, OUT, SAMPLES)
