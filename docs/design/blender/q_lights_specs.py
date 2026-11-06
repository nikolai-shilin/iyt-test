# The scenes behind the "lights" test questions (figure-style/questions/bareboat-skipper/lights.json), one per id.
# Plain Python, read by q_lights.py (Blender) and by the dry check (python3 q_lights_specs.py prints how each
# scene's lights land against the 2D figure's).
#
# kind 'vessel': a real vessel, its lights in her own coordinates (x forward, y to port, z up, metres, origin
#   amidships at the waterline), `R` our bearing from her bow (0 bow on, 90 her starboard beam, -90 her port beam,
#   180 her stern), `bearing` hers from us (relative, + to starboard). The camera is fitted to the 2D figure's
#   light positions, and her distance is set so the lens comes out near `lens`. `hull` (length, beam, freeboard):
#   a faint dark hull, the same plain shape for every vessel so it never tells her type. `tow`: what she tows, its
#   own hull and lights, `right` and `beyond` metres from her across and along our line of sight (the tow line
#   bends behind a tug that has turned), and its own aspect `R`. `poles=False`: no poles under her lights (a
#   sailing vessel's mast stays unseen).
# kind 'screen': lights with no hull to fit (marks, shore lights, a light alone): the camera is set by `lens` and
#   `bearing`, the `anchor` light (index, distance, height) sets the pitch, and every light goes on the ray through
#   its own point of the 2D figure at its distance (`dist`, or `at` {index: distance or (distance, height)}).
#   `bodies`: a dark buoy or beacon under these lights; `coast`: a dark coastline behind.
# Lights are listed by their index in the figure's `lights`; colours come from the figure.

SPECS = {
    # ---------- power-driven vessels ----------
    'bs-040': dict(kind='vessel', bearing=45, R=-80, hull=(30, 7, 2.5), lights={0: (2, 0, 11), 1: (0, 3.5, 6)}),
    'bs-440': dict(kind='vessel', bearing=35, R=-80, hull=(30, 7, 2.5), lights={0: (2, 0, 11), 1: (0, 3.5, 6)}),
    'bs-422': dict(kind='vessel', bearing=-40, R=80, hull=(30, 7, 2.5), lights={0: (2, 0, 11), 1: (0, -3.5, 6)}),
    'bs-604': dict(kind='vessel', bearing=0, R=-75, hull=(14, 4.5, 1.4), lights={0: (-0.5, 0, 6.5), 1: (1.5, 1.9, 2.6)}),
    'bs-626': dict(kind='vessel', bearing=0, R=-80, hull=(14, 4.5, 1.4), lights={0: (-0.5, 0, 6.5), 1: (1.5, 1.9, 2.6)}),
    'bs-627': dict(kind='vessel', bearing=0, R=60, hull=(14, 4.5, 1.4), lights={0: (-1, 0, 6.5), 1: (3, -1.9, 2.6)}),
    'bs-603': dict(kind='vessel', bearing=0, R=0, hull=(20, 5.5, 1.8), lights={0: (3, 0, 9.5), 1: (1, -2.4, 3.8), 2: (1, 2.4, 3.8)}),
    'bs-458': dict(kind='vessel', bearing=35, R=-70, hull=(36, 8, 3), lights={0: (5, 0, 12), 1: (5, 2.5, 6.5), 2: (3.5, 0, 15.5)}),
    'bs-459': dict(kind='vessel', bearing=-35, R=75, hull=(36, 8, 3), lights={0: (5, 0, 12), 1: (5, -2.5, 6.5), 2: (3.5, 0, 15.5)}),
    # over 50 m: two masthead lights, the after one higher
    'bs-364': dict(kind='vessel', bearing=40, R=-25, hull=(90, 14, 7), lights={0: (22, 0, 17), 1: (-8, 0, 25), 2: (12, 5, 10)}),
    'bs-416': dict(kind='vessel', bearing=2, R=0, hull=(110, 16, 8), lights={0: (-20, 0, 42), 1: (20, 0, 30), 2: (10, -8, 11), 3: (10, 8, 11)}),
    'bs-415': dict(kind='vessel', bearing=180, R=0, hull=(110, 16, 8), lights={0: (-20, 0, 42), 1: (20, 0, 30), 2: (10, -8, 11), 3: (10, 8, 11)}),
    'bs-418': dict(kind='vessel', bearing=12, R=1.5, hull=(110, 16, 8), lights={0: (-20, 0, 42), 1: (20, 0, 30), 2: (10, -8, 11), 3: (10, 8, 11)}),
    'bs-605': dict(kind='vessel', bearing=0, R=100, hull=(90, 15, 7), lights={0: (-17, 0, 30), 1: (16, 0, 22), 2: (16, -7.5, 12)}),
    # ---------- sailing vessels ----------
    'bs-439': dict(kind='vessel', bearing=30, R=0, hull=(13, 4, 1.2), lights={0: (5, -1.0, 1.6), 1: (5, 1.0, 1.6)}, poles=False),
    'bs-606': dict(kind='vessel', bearing=4, R=80, dist=90, hull=(13, 4, 1.2), lights={0: (4, -1.6, 1.6)}, poles=False),
    'bs-607': dict(kind='vessel', bearing=0, R=-80, dist=75, lens=40, hull=(11, 3.6, 1.1), lights={0: (0.5, 0, 16.5)}, poles=False),
    'bs-608': dict(kind='vessel', bearing=0, R=0, lens=60, hull=(11, 3.6, 1.1), lights={0: (0.5, -0.9, 16.5), 1: (0.5, 0.9, 16.5)}, poles=False),
    'bs-057': dict(kind='vessel', bearing=0, R=0, hull=(24, 6, 1.8), lights={0: (1, 0, 26), 1: (1, 0, 18.5), 2: (4, -2.4, 2.4), 3: (4, 2.4, 2.4)}, poles=False),
    # ---------- fishing ----------
    'bs-059': dict(kind='vessel', bearing=0, R=0, hull=(22, 6, 2), lights={0: (2, 0, 10.6), 1: (2, 0, 7.5), 2: (1, -2.8, 3.5), 3: (1, 2.8, 3.5)}),
    'bs-617': dict(kind='vessel', bearing=0, R=90, hull=(22, 6, 2), lights={0: (1, 0, 9.6), 1: (1, 0, 7)}),
    'bs-618': dict(kind='vessel', bearing=0, R=-75, hull=(18, 5, 1.6), lights={0: (-1, 0, 8.8), 1: (-1, 0, 6.5), 2: (1.5, 2.4, 3)}),
    'bs-442': dict(kind='vessel', bearing=3, R=90, hull=(18, 5, 1.6), lights={0: (1, 0, 9.6), 1: (1, 0, 6.5), 2: (-6, 0, 4)}),
    'bs-619': dict(kind='vessel', bearing=0, R=-90, hull=(18, 5, 1.6), lights={0: (1, 0, 9.4), 1: (1, 0, 6.5), 2: (-8, 0, 3.5)}),
    # ---------- not under command, restricted, constrained, aground, at anchor ----------
    'bs-612': dict(kind='vessel', bearing=0, R=60, hull=(35, 8, 3), lights={0: (-4, 0, 14), 1: (-4, 0, 11), 2: (6, -4, 5.5)}),
    'bs-613': dict(kind='vessel', bearing=0, R=90, hull=(35, 8, 3), lights={0: (0, 0, 14.5), 1: (0, 0, 11)}),
    'bs-441': dict(kind='vessel', bearing=-35, R=75, hull=(50, 10, 3.5), lights={0: (-8, 0, 22), 1: (-8, 0, 18), 2: (-8, 0, 14), 3: (8, 0, 19.5), 4: (-8, -5, 9)}),
    'bs-614': dict(kind='vessel', bearing=0, R=75, hull=(50, 10, 3.5), lights={0: (-8, 0, 22), 1: (-8, 0, 18), 2: (-8, 0, 14), 3: (10, 0, 13.8), 4: (12, -5, 7)}),
    'bs-615': dict(kind='vessel', bearing=0, R=90, hull=(40, 9, 3), lights={0: (-5, 0, 20), 1: (-5, 0, 16), 2: (-5, 0, 12), 3: (14, 0, 8.7)}),
    'bs-616': dict(kind='vessel', bearing=0, R=0, hull=(45, 16, 3), lights={0: (0, 0, 19), 1: (0, 0, 15.5), 2: (0, 0, 12), 3: (0, -8, 9.5), 4: (0, -8, 6), 5: (0, 8, 9.5), 6: (0, 8, 6)}),
    'bs-624': dict(kind='vessel', bearing=0, R=100, hull=(90, 15, 7), lights={0: (0, 0, 40), 1: (0, 0, 34), 2: (0, 0, 28), 3: (-25, 0, 31), 4: (25, 0, 24.5), 5: (25, -7.5, 13)}),
    'bs-625': dict(kind='vessel', bearing=0, R=0, hull=(50, 9, 3), lights={0: (2, 0, 20), 1: (2, -4, 17.5), 2: (2, 4, 17.5), 3: (6, 0, 12.5), 4: (4, -2.8, 5), 5: (4, 2.8, 5)}),
    'bs-611': dict(kind='vessel', bearing=0, R=-18, hull=(70, 12, 5), lights={0: (0, 0, 25.5), 1: (0, 0, 20), 2: (32, 0, 14), 3: (-32, 0, 9.5)}),
    'bs-610': dict(kind='vessel', bearing=0, R=-90, hull=(130, 20, 8), deck=True,
                   lights={0: (58, 0, 24), 1: (-58, 0, 16), 2: (36, 0, 9.2), 3: (18, 0, 9.2), 4: (0, 0, 9.2), 5: (-18, 0, 9.2), 6: (-36, 0, 9.2)}),
    # ---------- towing, pilot ----------
    'bs-620': dict(kind='vessel', bearing=0, R=180, hull=(25, 7, 2), lights={0: (-12, 0, 4.9), 1: (-12, 0, 2.6)}),
    'bs-621': dict(kind='vessel', bearing=0, R=-75, hull=(24, 7, 2.5), lights={0: (2, 0, 17), 1: (2, 0, 13.5), 2: (2, 0, 10), 3: (6, 3.2, 4.6)}),
    'bs-623': dict(kind='vessel', bearing=0, R=-75, hull=(18, 5, 1.6), lights={0: (-1, 0, 8.8), 1: (-1, 0, 6.5), 2: (1.5, 2.4, 3)}),
    'bs-435': dict(kind='vessel', bearing=35, R=-80, hull=(24, 7, 2.5), lights={0: (2, 0, 17), 1: (2, 0, 13.5), 2: (2, 0, 10), 3: (2.5, 3.2, 4.6)},
                   tow=dict(right=62, beyond=250, R=-60, hull=(45, 11, 2), lights={4: (20, 5.5, 3.2)})),
    'bs-622': dict(kind='vessel', bearing=0, R=-80, hull=(24, 7, 2.5), lights={0: (2, 0, 17), 1: (2, 0, 13.5), 2: (2, 0, 10), 3: (3.5, 3.2, 4.6)},
                   tow=dict(right=112, beyond=350, R=-60, hull=(45, 11, 2), lights={4: (20, 5.5, 3.2)})),
    # a single sternlight ahead of us
    'bs-412': dict(kind='vessel', bearing=1, R=180, dist=220, hull=(14, 4.5, 1.4), lights={0: (-7, 0, 1.8)}),

    # ---------- marks: one light, low on the water, on a dark buoy ----------
    'bs-053': dict(kind='screen', lens=50, bearing=0, anchor=(0, 160, 4.2), bodies={0: 'buoy'}),
    'bs-554': dict(kind='screen', lens=50, bearing=0, anchor=(0, 160, 3.4), bodies={0: 'buoy'}),
    'bs-555': dict(kind='screen', lens=50, bearing=0, anchor=(0, 160, 3.4), bodies={0: 'buoy'}),
    'bs-559': dict(kind='screen', lens=50, bearing=0, anchor=(0, 160, 3.4), bodies={0: 'buoy'}),
    'bs-561': dict(kind='screen', lens=50, bearing=8, anchor=(0, 160, 3.4), bodies={0: 'buoy'}),
    'bs-562': dict(kind='screen', lens=50, bearing=0, anchor=(0, 160, 3.4), bodies={0: 'buoy'}),
    'bs-565': dict(kind='screen', lens=50, bearing=0, anchor=(0, 160, 4.2), bodies={0: 'buoy'}),
    'bs-567': dict(kind='screen', lens=50, bearing=0, anchor=(0, 160, 4.2), bodies={0: 'buoy'}),
    'bs-574': dict(kind='screen', lens=50, bearing=0, anchor=(0, 160, 4.2), bodies={0: 'buoy'}),
    'bs-577': dict(kind='screen', lens=50, bearing=0, anchor=(0, 170, 4.0), bodies={0: 'buoy'}),
    'bs-576': dict(kind='screen', lens=50, bearing=0, anchor=(0, 220, 7.5), bodies={0: 'beacon'}),
    'bs-058': dict(kind='screen', lens=50, bearing=0, anchor=(0, 320, 2.4)),
    'bs-580': dict(kind='screen', lens=60, bearing=0, eye=5.0, anchor=(2, 70, 1.8), at={0: (130, 1.8), 1: (130, 1.8), 2: (70, 1.8), 3: (70, 1.8)},
                   bodies={0: 'float', 1: 'float', 2: 'float', 3: 'float'}),
    'bs-582': dict(kind='diptych', lens=50, bearing=0, anchor=(0, 160, 4.0), bodies={0: 'buoy'}),
    # ---------- harbours and the shore ----------
    'bs-594': dict(kind='screen', lens=50, bearing=0, anchor=(0, 320, 7.0), at={1: 320}, moles=(0, 1), coast=dict(distance=1300, height=70)),
    'bs-586': dict(kind='screen', lens=50, bearing=0, anchor=(0, 700, 11.0), bodies={0: 'tower'}, coast=dict(distance=1100, height=60)),
    'bs-599': dict(kind='screen', lens=50, bearing=0, anchor=(0, 1500, 30.0), bodies={0: 'tower'}, coast=dict(distance=1450, height=80)),
    'bs-601': dict(kind='screen', lens=50, bearing=0, anchor=(0, 2600, 60.0), bodies={0: 'lighthouse'}, coast=dict(distance=2500, height=110)),
    'bs-373': dict(kind='screen', lens=45, bearing=0, anchor=(11, 600, 8.0), dist=1250, at={11: 600, 12: 600, 13: 330}, moles=(11, 12),
                   coast=dict(distance=1150, height=60)),
    'bs-499': dict(kind='screen', lens=110, bearing=0, anchor=(1, 1200, 6.0), at={0: 1500}, coast=dict(distance=1150, height=30)),
    'bs-593': dict(kind='screen', lens=110, bearing=0, anchor=(0, 1200, 6.0), at={1: 1500}, coast=dict(distance=1150, height=30)),
    # ---------- two scenes of their own ----------
    'bs-609': dict(kind='yacht', bearing=0),      # the Sun Odyssey bow on, sails up, steaming light and sidelights
    'bs-060': dict(kind='masthead'),              # our own masthead tricolour, seen from astern and below
    # ---------- Charter Check-in: our own yacht at the pontoon, lights tested at night ----------
    'ci-213': dict(kind='pontoon', dead=('starboard',), lens=24, look_z=5.5),                 # NAV LIGHTS on, seen from ahead
    'ci-214': dict(kind='pontoon', anchor=True, lens=18, eye_off=(2.2, 2.5, 0.0), look=(0.13, 2.0, 11.0)),   # ANCHOR breaker on
}

if __name__ == '__main__':
    # dry check: fit each vessel scene's camera and print where its lights land against the figure's
    import json, os, sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import q_lights_geo as G
    from q_lights_layout import layout
    L = {e['id']: e for lv in ('bareboat-skipper', 'charter-checkin') for e in json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'figure-style', 'questions', lv, 'lights.json')))}
    only = sys.argv[1:]
    for qid, sp in SPECS.items():
        if only and qid not in only: continue
        e = L[qid]; lights = e['figure']['lights']
        lay = layout(sp, lights)
        if not lay: print(qid, sp['kind'], '(special)'); continue
        cam = lay['cam']; pts = lay['points']
        px = {i: G.project(p, cam)[:2] for i, p in pts.items()}
        idx = sorted(px)
        bad = G.check_order([px[i] for i in idx], [(lights[i]['x'], lights[i]['y']) for i in idx])
        errs = [((px[i][0] - lights[i]['x'] * 4) ** 2 + (px[i][1] - lights[i]['y'] * 4) ** 2) ** 0.5 for i in idx]
        print(f"{qid} {sp['kind']:6} lens {G.lens_of_s(cam['s']):5.0f} mm  dist {lay.get('dist', 0):6.0f}  err max {max(errs):4.0f}px  "
              + ' '.join(f"{i}:{lights[i]['c']}({px[i][0]:.0f},{px[i][1]:.0f})/({lights[i]['x']*4},{lights[i]['y']*4})" for i in idx))
        for b in bad: print('   !!', b)
