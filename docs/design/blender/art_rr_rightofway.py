# Article racing-rules/rightofway: the seven race figures as Blender renders (art_rr_b_kit.race): rules 10 to 13.
#    1  rule 10 on a beat: port tack and starboard tack converging
#    2  rule 10 on a run: booms to starboard (port tack) and to port (starboard tack)
#    3  rule 11: windward and leeward, overlapped on starboard tack
#    4  rule 11 at the start: a windward boat barging at the committee boat
#    5  rule 12: you pass the boat ahead to windward
#    6  rule 12: you pass the boat ahead to leeward
#    7  rule 13: a boat past head to wind, not yet close-hauled, and a starboard-tack boat
#   blender --background --factory-startup --python docs/design/blender/art_rr_rightofway.py -- --fig 1 [--samples 144] [--scale 100]
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import bpy
import common as C, kit as K
import art_rr_b_kit as R

arg = C.cli(); FIG = arg('--fig', 1); SAMPLES = arg('--samples', 144); R.SCALE = arg('--scale', 100)
ART = 'rightofway'; OUT = arg('--out', os.path.join(R.ARTS, ART, f'{FIG}-3d.jpg'))
FIGS = {x['n']: x for x in json.load(open(os.path.join(HERE, '..', 'article-figs', f'racing-rules-{ART}.json')))['figs']}

CFG = {
    1: dict(boats={'port': dict(text='Port tack: keeps clear', color='red'), 'starboard': dict(text='Starboard tack')},
            note='Rule 10 · port crosses ahead, ducks astern or tacks'),
    2: dict(boats={0: dict(text='Boom to starboard: port tack', color='red'), 1: dict(text='Boom to port: starboard tack')},
            note='Rule 10 on a run · the port-tack boat keeps clear'),
    3: dict(boats={'windward': dict(text='Windward: keeps clear', color='red'), 'leeward': dict(text='Leeward')},
            note='Rule 11 · windward keeps clear: hull, boom and sails'),
    4: dict(boats={0: dict(text='Leeward: may hold her course', off=(-250, 30)), 'windward': dict(text='Windward: no room for her', color='red')},
            line=dict(text='Start line', at=0.45, cb_text='Committee boat', pin=True), cam=dict(box=(130, 215, 1150, 620)),
            note='Rule 11 at the start · no mark-room at the committee boat'),
    5: dict(boats={0: dict(text='Clear ahead'), 'You': dict(text='You: keep clear, rule 12 then 11', color='blue')},
            note='Passing to windward · you keep clear all the way'),
    6: dict(boats={0: dict(text='Windward once overlapped', color='red'), 'You': dict(text='You: leeward, right of way', color='blue')},
            note='Passing to leeward · overlapped, you have right of way'),
    7: dict(boats={'starboard': dict(text='Starboard tack'), 'tacking': dict(text='Tacking: keeps clear', color='red')},
            note='Rule 13 · past head to wind, not yet close-hauled: she keeps clear'),
}
C.reset()
R.race(FIGS[FIG]['fig'], CFG[FIG], OUT, SAMPLES)
