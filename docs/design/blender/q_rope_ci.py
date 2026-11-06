# Charter Check-in test images, figure type "rope": the scenes q_rope.py renders for the ci-* ids (--level
# charter-checkin). The rope library's own scenes (fig_winch, render_scene's cleat, fig_rail, art_rope_a's quay) are
# run through q_rope's hooks where they fit; the deck fittings a check-in looks at (guardrail and gate, lead blocks,
# genoa car, furling drum, cam cleat, lazyjacks) are built here. Labels and notes come from the figure only.
# specs(R) gets q_rope's globals and returns {id: scene function}.
import os, math, json, random
import bpy, bmesh
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))

def specs(R):
    C, K, G, V, T3 = R['C'], R['K'], R['G'], R['V'], R['T3']
    TEXTS = R['TEXTS']
    def render(labels, exposure=-0.7, space='blender'):
        C.render(R['OUT'], R['SAMPLES'], R['SCALE'], exposure, R['labels_from'](labels), R['NOTE'], space=space)

    # ------------------------------------------------------------------ helpers
    def mat(name, hexs, rough=0.5, metal=0.0, coat=0.0): return C.simple(name, hexs, rough, metal, coat)

    def hairs(name, P, tan, R0, n, length, m, seed=1, curl=0.0, spread=0.03):
        """Loose fibres sticking out of a rope or wire at P (Blender) along `tan`: thin prisms, one mesh."""
        rnd = random.Random(seed); t = Vector(tan).normalized()
        a = t.cross(Vector((0, 0, 1))); a = a.normalized() if a.length > 1e-6 else Vector((1, 0, 0)); b = t.cross(a)
        bm = bmesh.new(); w = R0 * 0.08 + 0.0003
        for _ in range(n):
            ang = rnd.uniform(0, math.tau); s = rnd.uniform(-spread, spread)
            rad = a * math.cos(ang) + b * math.sin(ang)
            base = Vector(P) + t * s + rad * R0 * 0.95
            L = length * rnd.uniform(0.4, 1.0)
            pts = [base]
            d = (rad + t * rnd.uniform(-0.6, 0.6)).normalized()
            for k in range(1, 5):
                d = (d + (t.cross(d)) * curl * rnd.uniform(-1, 1) + Vector((0, 0, -0.15 * curl))).normalized()
                pts.append(pts[-1] + d * L / 4)
            ring = []
            for p in pts:
                ring.append([bm.verts.new(p + a * w), bm.verts.new(p + b * w), bm.verts.new(p - a * w)])
            for k in range(len(ring) - 1):
                for j in range(3):
                    bm.faces.new((ring[k][j], ring[k][(j + 1) % 3], ring[k + 1][(j + 1) % 3], ring[k + 1][j]))
        me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
        return C.obj(name, me, m)

    def sleeve(name, P0, P1, r, m):
        return C.tube(name, [Vector(P0), Vector(P0).lerp(Vector(P1), 0.5), Vector(P1)], r, 16, 1.0, m, caps=True)

    def catm(P, per=10): return C.catmull_centripetal([Vector(p) for p in P], per)

    def sea_and_sky(center=(0, 0), az=210, el=40, state='calm'):
        K.sea(state, center=center); K.day_sky(sun_az=az, sun_el=el); K.darken_visible_sky()

    # ------------------------------------------------------------------ side deck (Blender space, bow +x)
    ZD = 1.1                         # deck top above the water
    YO = -0.62                       # the deck edge (outboard), the side we look at
    def side_deck(x0=-4.0, x1=4.0, yin=1.8):
        M = K.mats()
        C.obj('deck', C.rbox('deck', (x1 - x0, yin - YO, 0.08), 0.01, 2), C.nonskid_mat(), V((x0 + x1) / 2, (yin + YO) / 2, ZD - 0.04))
        C.obj('toerail', C.rbox('toerail', (x1 - x0, 0.045, 0.05), 0.012, 3), C.teak_mat(), V((x0 + x1) / 2, YO + 0.024, ZD + 0.025))
        C.obj('topsides', C.rbox('topsides', (x1 - x0, 0.05, ZD + 0.5), 0.01, 2), M['hull'], V((x0 + x1) / 2, YO - 0.02, (ZD - 0.5) / 2))
        # the coachroof side, inboard
        C.obj('coachroof', C.rbox('coachroof', (x1 - x0, 0.6, 0.42), 0.04, 3), M['hull'], V((x0 + x1) / 2, yin - 0.1, ZD + 0.2))

    SY = YO + 0.07                   # stanchion line
    def stanchion(x, h=0.62, lean=0.0, name='stanchion'):
        steel = mat('stanchion-steel', '#d3d6d8', 0.22, 1.0)
        base = V(x, SY, ZD)
        pl = C.obj(name + '-base', C.rbox(name + '-base', (0.13, 0.085, 0.012), 0.004, 2), steel, base + V(0, 0, 0.006))
        d = V(0, -math.sin(math.radians(lean)), math.cos(math.radians(lean)))
        if lean: pl.rotation_euler.x = math.radians(lean) * 0.5; pl.location.z += 0.004
        C.tube(name + '-socket', [base, base + d * 0.09], 0.018, 20, 1.0, steel, caps=True)
        C.tube(name, [base, base + d * h], 0.0127, 20, 1.0, steel, caps=True)
        C.tube(name + '-top', [base + d * (h - 0.01), base + d * (h + 0.012)], 0.016, 20, 1.0, steel, caps=True)
        return base, d

    def wire(name, pts, r=0.0028):
        return C.tube(name, catm(pts, 6), r, 10, 1.0, mat('lifeline', '#cfd3d6', 0.25, 1.0))

    # ------------------------------------------------------------------ ci-057: guardrail, stanchion, gate
    def guardrail_faults():
        C.reset(); side_deck()
        xs = {1: 2.4, 2: 1.2, 3: 0.0, 'g1': -1.2, 'g2': -2.0, 6: -3.2}
        tops = {}
        for k, x in xs.items():
            lean = 7.0 if k == 3 else 0.0
            b, d = stanchion(x, lean=lean, name=f'stanchion{k}')
            tops[k] = (b + d * 0.6, b + d * 0.32)
        steel = mat('gate-steel', '#d3d6d8', 0.22, 1.0)
        # gate posts: a diagonal brace inboard each
        for k in ('g1', 'g2'):
            x = xs[k]; C.tube(f'brace-{k}', [V(x, SY + 0.32, ZD + 0.01), V(x, SY + 0.01, ZD + 0.42)], 0.01, 16, 1.0, steel, caps=True)
        up = [tops[k][0] for k in (1, 2, 3, 'g1')]; lo = [tops[k][1] for k in (1, 2, 3, 'g1')]
        wire('upper', [up[0] + V(1.4, 0, 0.01)] + up); wire('lower', [lo[0] + V(1.4, 0, 0.0)] + lo)
        wire('upper-aft', [tops['g2'][0], tops[6][0], tops[6][0] + V(-1.2, 0, 0)]); wire('lower-aft', [tops['g2'][1], tops[6][1], tops[6][1] + V(-1.2, 0, 0)])
        # frayed strands on the upper lifeline between #2 and #3
        fr = up[1].lerp(up[2], 0.55)
        hairs('frayed-strands', fr, up[2] - up[1], 0.0028, 14, 0.035, mat('strand', '#d9dcde', 0.3, 1.0), seed=4, curl=0.5, spread=0.012)
        # the gate wires: from the forward gate post to pelican hooks on eyes on the aft one
        for zt, nm in ((0, 'upper'), (1, 'lower')):
            a = tops['g1'][zt]; b = tops['g2'][zt]
            hook0 = b + V(0.11, 0, 0)
            wire(f'gate-{nm}', [a, a.lerp(hook0, 0.5) + V(0, 0, -0.01), hook0])
            # eye on the post
            ring = [b + V(0.022 + 0.012 * math.cos(t), 0, 0.012 * math.sin(t)) for t in [k / 24 * math.tau for k in range(25)]]
            C.tube(f'eye-{nm}', ring, 0.0028, 10, 1.0, steel)
            # pelican hook: the body, the hinged hook through the eye, the slide ring
            C.tube(f'pel-body-{nm}', [hook0, b + V(0.05, 0, 0.0)], 0.0055, 14, 1.0, steel, caps=True)
            hk = [b + V(0.05 - 0.016 * math.sin(t), 0, 0.016 * math.cos(t) - 0.002) for t in [k / 16 * math.pi * 1.15 for k in range(17)]]
            C.tube(f'pel-hook-{nm}', hk, 0.0035, 10, 1.0, steel, caps=True)
            sl = [b + V(0.058, 0.0085 * math.cos(t), 0.0085 * math.sin(t)) for t in [k / 24 * math.tau for k in range(25)]]
            C.tube(f'pel-ring-{nm}', sl, 0.002, 8, 1.0, steel)
            if nm == 'lower':   # its pin and lanyard still in place
                C.cyl('pel-pin', 0.0022, 0.0022, 0.026, 12, steel, b + V(0.064, 0, 0.0), (math.pi / 2, 0, 0))
        sea_and_sky(center=(0, -10), az=230, el=40)
        cam = K.camera((0.35, 1.3, ZD + 1.05), (-0.8, YO, ZD + 0.36), 26); C.focus_on_centre(cam, 11.0)
        b3 = V(xs[3], SY, ZD + 0.03)
        render([b3 + V(0, 0, 0.02), fr + V(0, 0, 0.01), tops['g2'][0] + V(0.06, 0, 0.02)])

    # ------------------------------------------------------------------ ci-121: lead blocks on the stanchion bases
    def lead_blocks():
        C.reset(); side_deck()
        xs = [2.4, 1.2, 0.0, -1.2]; fitted = {2.4, 1.2, -1.2}
        for i, x in enumerate(xs): stanchion(x, name=f'stanchion{i}')
        LY = SY + 0.075; R0 = 0.005
        sheave = {}
        for x in fitted:
            c, ax, h = G.block(V(x - 0.13, LY, ZD), V(1, 0, 0), sheave_r=0.02)
            sheave[x] = c
        pts = [V(3.6, LY, ZD + 0.05)]
        for x in xs:
            if x in fitted:
                c = sheave[x]; top = c.z + 0.02 + R0
                pts += [V(c.x + 0.03, LY, top - 0.004), V(c.x, LY, top), V(c.x - 0.03, LY, top - 0.004)]
            else:   # no block: the line drops and bears on the stanchion's socket
                pts += [V(x + 0.14, LY - 0.03, ZD + 0.025), V(x + 0.02, SY + 0.018 + R0, ZD + 0.05), V(x - 0.02, SY + 0.018 + R0, ZD + 0.05), V(x - 0.14, LY - 0.03, ZD + 0.025)]
        pts += [V(-2.2, LY, ZD + 0.055), V(-3.4, LY + 0.02, ZD + 0.05)]
        C.braid('furling-line', T3(catm(pts, 8)), R0, '#c8161d', '#f0ece2', fine=1.4)
        sea_and_sky(center=(0, -10), az=230, el=42)
        cam = K.camera((0.95, 0.62, ZD + 0.55), (0.3, SY, ZD + 0.04), 24); C.focus_on_centre(cam, 11.0)
        render([sheave[1.2] + V(0, 0, 0.04), V(0.0, SY + 0.02, ZD + 0.08), V(-1.9, LY, ZD + 0.07)])

    # ------------------------------------------------------------------ ci-104: genoa car, pin missing, lashed with cord
    def genoa_car():
        C.reset()
        C.obj('deck', C.rbox('deck', (2.4, 1.6, 0.08), 0.01, 2), C.nonskid_mat(), V(0, 0.2, ZD - 0.04))
        C.obj('toerail', C.rbox('toerail', (2.4, 0.045, 0.05), 0.012, 3), C.teak_mat(), V(0, YO + 0.024, ZD + 0.025))
        C.obj('topsides', C.rbox('topsides', (2.4, 0.05, ZD + 0.5), 0.01, 2), K.mats()['hull'], V(0, YO - 0.02, (ZD - 0.5) / 2))
        ty = -0.25
        alu = mat('track', '#c4c8cc', 0.3, 1.0)
        C.obj('track', C.rbox('track', (2.4, 0.03, 0.014), 0.003, 2), alu, V(0, ty, ZD + 0.007))
        for k in range(-11, 12):     # the pin holes along the track
            C.cyl('track-hole', 0.0042, 0.0042, 0.003, 14, mat('hole', '#141516', 0.6), V(k * 0.1 + 0.05, ty, ZD + 0.0135))
        c, ax, h = G.block(V(0.0, ty, ZD), V(1, 0, 0))
        # the car's plunger housing with its empty socket (the pin is gone)
        C.obj('plunger', C.rbox('plunger', (0.03, 0.03, 0.02), 0.004, 2), mat('plunger', '#cfd2d4', 0.2, 1.0), V(0.07, ty, ZD + 0.018))
        C.cyl('plunger-hole', 0.005, 0.005, 0.004, 14, mat('hole2', '#0d0e0f', 0.7), V(0.07, ty, ZD + 0.0285))
        # cord lashing: turns round the car and the track, its ends tied off forward
        cord = mat('cord', '#2a62b0', 0.7)
        for k, dx in enumerate((-0.035, -0.02, -0.005)):
            loop = [V(dx + 0.002 * math.sin(t), ty + 0.034 * math.cos(t), ZD + 0.012 + 0.03 * math.sin(t)) for t in [j / 20 * math.tau for j in range(21)]]
            for p in loop: p.z = max(p.z, ZD + 0.001)
            C.tube(f'cord{k}', loop, 0.0022, 8, 1.0, cord)
        C.tube('cord-end', catm([V(-0.005, ty + 0.034, ZD + 0.02), V(-0.06, ty + 0.05, ZD + 0.005), V(-0.14, ty + 0.08, ZD + 0.003), V(-0.2, ty + 0.06, ZD + 0.003)], 6), 0.0022, 8, 1.0, cord)
        # the sheet: from the clew (up forward, out of frame) round the sheave and aft to the winch
        R0 = 0.006; top = c.z + 0.032 + R0
        sh = [V(0.9, ty - 0.35, ZD + 1.2), V(0.4, ty - 0.12, ZD + 0.45), V(0.06, ty, top - 0.004), V(0.0, ty, top + 0.001), V(-0.06, ty, top - 0.006),
              V(-0.5, ty + 0.1, ZD + 0.16), V(-1.2, ty + 0.3, ZD + 0.28)]
        C.braid('sheet', T3(catm(sh, 10)), R0, '#e9e5da', '#2b4d8c', shiny=True, fine=1.5)
        sea_and_sky(center=(0, -10), az=210, el=42)
        cam = K.camera((-0.36, 0.42, ZD + 0.32), (0.06, ty - 0.02, ZD + 0.03), 34); C.focus_on_centre(cam, 11.0)
        render([V(0.55, ty, ZD + 0.02), V(0.07, ty, ZD + 0.04)])

    # ------------------------------------------------------------------ ci-102: the furling drum, one turn left
    def furling_drum():
        C.reset()
        C.obj('deck', C.rbox('deck', (3.0, 1.6, 0.08), 0.01, 2), C.nonskid_mat(), V(-1.0, 0.0, ZD - 0.04))
        for s in (-1, 1):
            C.obj('toerail', C.rbox('toerail', (3.0, 0.045, 0.05), 0.012, 3), C.teak_mat(), V(-1.0, s * 0.78, ZD + 0.025))
            C.obj('topsides', C.rbox('topsides', (3.0, 0.05, ZD + 0.5), 0.01, 2), K.mats()['hull'], V(-1.0, s * 0.82, (ZD - 0.5) / 2))
        alu = mat('furler-alu', '#c9ccd0', 0.28, 1.0); dark = mat('furler-dark', '#1b1c1e', 0.4, 0.2, 0.5)
        D = V(0.3, 0.0, ZD)
        C.obj('stemhead', C.rbox('stemhead', (0.3, 0.08, 0.04), 0.01, 2), alu, D + V(0.0, 0, 0.02))
        C.cyl('link', 0.012, 0.012, 0.08, 16, alu, D + V(0, 0, 0.07))
        C.cyl('flange-lo', 0.078, 0.078, 0.008, 48, alu, D + V(0, 0, 0.11))
        C.cyl('drum', 0.05, 0.05, 0.06, 48, dark, D + V(0, 0, 0.144))
        C.cyl('flange-hi', 0.078, 0.078, 0.008, 48, alu, D + V(0, 0, 0.178))
        C.cyl('foil', 0.016, 0.016, 5.0, 24, alu, D + V(0, 0, 0.18 + 2.5))
        # the line guide: an arm off the lower flange with a ring, aft and to starboard
        gd = D + V(-0.11, -0.03, 0.144)
        C.tube('guide-arm', [D + V(-0.07, -0.02, 0.105), gd + V(0, 0, -0.03), gd + V(0, 0, -0.012)], 0.004, 10, 1.0, alu)
        C.tube('guide-ring', [gd + V(0, 0.012 * math.cos(t), 0.012 * math.sin(t)) for t in [k / 24 * math.tau for k in range(25)]], 0.0035, 10, 1.0, alu)
        # the genoa, fully out: its luff on the foil, the foot rising aft (only the tack corner in frame)
        K.sail_surface('genoa', D + V(0, 0, 0.3), D + V(0, 0, 9.0), V(-4.5, -1.6, ZD + 1.3), 0.1, -1, twist=6)
        # the line: one turn on the drum, out through the guide, slack loops on deck, aft to a lead block and the cockpit
        R0 = 0.0045; rr = 0.05 + R0
        a0 = math.atan2(-0.03, -0.11)
        helix = [D + V(rr * math.cos(a0 + t), rr * math.sin(a0 + t), 0.135 + 0.012 * t / math.tau) for t in [k / 24 * math.tau for k in range(25)]]
        sb = V(-1.2, -0.66, ZD)
        G.block(sb + V(0, 0.06, 0), V(1, 0, 0), sheave_r=0.02)
        top = ZD + 0.022 + 0.012 + 0.02 + 0.008 + 0.02 + R0
        deck = ZD + R0
        loops = [gd + V(-0.03, -0.01, -0.03), V(0.02, -0.12, deck + 0.01), V(-0.15, -0.3, deck), V(-0.42, -0.22, deck), V(-0.55, -0.02, deck), V(-0.38, 0.1, deck),
                 V(-0.2, -0.05, deck), V(-0.35, -0.38, deck), V(-0.7, -0.48, deck), V(-0.85, -0.3, deck), V(-0.72, -0.15, deck), V(-0.6, -0.4, deck),
                 V(-0.9, -0.58, deck), V(-1.1, -0.6, top - 0.01), V(-1.2, -0.6, top), V(-1.3, -0.6, top - 0.01), V(-2.0, -0.58, deck + 0.04), V(-2.5, -0.56, deck + 0.04)]
        path = [helix[0] + V(0.05, 0.03, -0.004)] + helix + [gd]
        C.braid('furling-line', T3(path + catm(loops, 8)), R0, '#f0ece2', '#c8161d', fine=1.4)
        sea_and_sky(center=(0, -6), az=200, el=45)
        cam = K.camera((-1.25, 0.75, ZD + 0.95), (-0.35, -0.3, ZD + 0.08), 26); C.focus_on_centre(cam, 11.0)
        render([V(-0.15, -0.3, deck + 0.02), D + V(0, 0, 0.19), V(-1.65, -0.58, deck + 0.05)])

    # ------------------------------------------------------------------ ci-134: mainsheet in a cam cleat, worn teeth
    def cam_cleat():
        C.reset()
        C.obj('deck', C.rbox('deck', (3.0, 3.0, 0.08), 0.01, 2), C.nonskid_mat(), V(0, 0, -0.04))
        black = mat('cam-black', '#17181a', 0.35, 0.2, 0.6); alu = mat('cam-alu', '#c5c9cd', 0.3, 1.0)
        R0 = 0.0055; zl = 0.03
        C.obj('cam-base', C.rbox('cam-base', (0.11, 0.075, 0.012), 0.004, 2), black, V(0.0, 0.0, 0.006))
        for s in (-1, 1):
            c = V(0.005, s * (0.0155 + R0), 0.0)
            C.cyl('cam-post', 0.004, 0.004, 0.03, 12, alu, c + V(0, 0, 0.02))
            C.cyl('cam', 0.0155, 0.0155, 0.026, 40, alu, c + V(0, 0, zl))
            for k in range(16):      # the teeth, worn down to low rounded ridges
                a = k / 16 * math.tau
                o = C.obj('cam-tooth', C.rbox('cam-tooth', (0.0028, 0.0032, 0.024), 0.0012, 2), alu, c + V(math.cos(a) * 0.0158, math.sin(a) * 0.0158, zl))
                o.rotation_euler.z = a
            C.cyl('cam-cap', 0.006, 0.006, 0.004, 16, black, c + V(0, 0, zl + 0.015))
        # a fairlead ahead of the cams
        C.tube('fairlead', [V(0.06, 0.012 * math.cos(t), zl + 0.012 * math.sin(t)) for t in [k / 24 * math.tau for k in range(25)]], 0.004, 10, 1.0, black)
        C.obj('fairlead-post', C.rbox('fl-post', (0.012, 0.012, zl), 0.003, 2), black, V(0.06, 0, zl / 2 - 0.006))
        # the turning block forward, the sheet down from the boom over it
        c, ax, h = G.block(V(0.42, 0.0, 0.0), V(1, 0, 0))
        top = c.z + 0.032 + R0
        sheet = [V(1.6, 0.25, 2.2), V(1.0, 0.12, 1.0), V(0.47, 0.0, top - 0.004), V(0.42, 0.0, top), V(0.37, 0.0, top - 0.006), V(0.18, 0.0, zl + 0.01),
                 V(0.06, 0.0, zl), V(0.0, 0.0, zl), V(-0.06, 0.0, zl - 0.004), V(-0.15, 0.01, R0 + 0.004)]
        cc = V(-0.42, 0.1, R0); coil = []
        for k in range(5):
            rr = 0.14 + 0.012 * k
            for i in range(20):
                a = i / 20 * math.tau + 1.2 + k * 0.4
                coil.append(cc + V(math.cos(a) * rr, math.sin(a) * rr * 0.85, R0 * 1.2 * (k % 2)))
        C.braid('mainsheet', T3(catm(sheet, 10) + catm([V(-0.22, 0.04, R0), coil[0]] + coil, 4)), R0, '#f1eee6', '#2b4d8c', shiny=True, fine=1.5)
        bpy.context.view_layer.update()
        for o in bpy.data.objects:          # the coachroof top at ZD above the water
            if o.parent is None: o.location.z += ZD
        Z = V(0, 0, ZD)
        sea_and_sky(center=(0, 0), az=200, el=50)
        cam = K.camera(V(0.05, -0.95, 0.75) + Z, V(0.02, 0.05, 0.06) + Z, 30); C.focus_on_centre(cam, 11.0)
        render([V(0.62, 0.05, 0.42) + Z, V(0.005, 0.0, zl + 0.02) + Z, coil[30] + V(0, 0, 0.01) + Z])

    # ------------------------------------------------------------------ ci-130: the batten caught on a lazyjack
    def lazyjack():
        C.reset()
        K.sea('calm'); y = K.load_yacht(name='yacht'); y.place(0, 0, heading=0)
        K.coast(distance=700, bearing=250, height=90, town=True)
        WL = K.WL
        tack = Vector((-0.12, 0.0, 5.55 - WL)); head = Vector((-0.1, 0.0, 15.2 - WL)); clew = Vector((-5.3, 0.0, 5.62 - WL))
        K.sail_surface('main', tack, head, clew, 0.05, 1, twist=4, roach=0.05, parent=y.root)
        bpy.context.view_layer.update()
        M = lambda p: y.world(Vector(p) + Vector((K.MAST.x, K.MAST.y, K.WL)))      # mast-relative -> world
        batten = mat('batten', '#3a3d42', 0.5)
        ends = []
        for v in (0.22, 0.45, 0.68, 0.88):
            L = tack.lerp(head, v); E = clew.lerp(head, v)
            E2 = E + (E - L).normalized() * 0.06
            C.tube('batten', [M(L.lerp(E, 0.12) + Vector((0, 0.02, 0))), M(E2 + Vector((0, 0.02, 0)))], 0.012, 10, 1.0, batten, caps=True)
            ends.append(E2)
        # the lazyjacks: from the mast at 11 m, two legs down each side to the boom
        lj = mat('lazyjack', '#2a2c30', 0.6)
        legs = []
        for s in (1, -1):
            top = Vector((-0.25, s * 0.15, 11.5 - WL))
            for bx in (-1.6, -4.0):
                foot = Vector((bx, s * 0.32, 5.75 - WL))
                legs.append((top, foot, s))
        caught = ends[1]
        for top, foot, s in legs:
            pts = [top, top.lerp(foot, 0.5), foot]
            if s == 1 and foot.x < -3:   # this leg runs across the end of the second batten: the batten hooked over it
                pts = [top, caught + Vector((0.04, 0.05, 0.03)), caught + Vector((-0.02, 0.05, -0.04)), foot]
            C.tube('lazyjack', [M(p) for p in catm(pts, 8)], 0.006, 8, 1.0, lj)
        # the main halyard: from the headboard up the mast's aft face to the masthead
        hal = [head + Vector((0.02, 0, 0.05)), Vector((-0.16, 0, 17.5 - WL)), Vector((-0.17, 0, 20.4 - WL))]
        C.tube('main-halyard', [M(p) for p in hal], 0.006, 10, 1.0, mat('halyard', '#e9e3d2', 0.5))
        K.day_sky(sun_az=150, sun_el=45); K.darken_visible_sky()
        eye = M(Vector((-3.6, 13.5, 4.6))); look = M(Vector((-2.6, 0.0, 9.0)))
        cam = K.camera(tuple(eye), tuple(look), 22); C.focus_on_centre(cam, 16.0)
        render([M(hal[0] + Vector((0, 0, 0.8))), M(caught + Vector((0, 0.05, 0.03))), M(legs[0][0].lerp(legs[0][1], 0.7))])

    # ------------------------------------------------------------------ ci-416: the lazy line at the quay ring
    def lazy_line():
        A = R['art_helpers'](); C.reset(); random.seed(5)
        QZ = A['QZ']
        K.sea('calm', center=(0, -10))
        A['quay'](-5.0, 5.0, 4.0)
        y = A['yacht_stern_to'](gap=1.4, x=-1.6)
        ring = G.quay_ring(V(0.9, 0.36, QZ), V(0, -1, 0), R=0.085, r=0.012, lift=28)
        Rr = 0.008
        U = G.u_round_bar(ring, Rr, 40, 320, 16, 1.4)
        slime = mat('slime', '#4a5233', 0.85)
        # made fast round the ring, over the coping, down the wall into the water; a slimy length hauled up and
        # lying in loose loops on the quay beside it
        edge = V(0.95, 0.0, QZ + Rr + 0.004)
        down = [edge + V(0.0, -0.05, -0.05), V(0.97, -0.12, QZ * 0.55), V(0.99, -0.2, 0.05), V(1.0, -0.35, -0.3)]
        lead = [U[0] + ring['out'] * 0.08, edge + V(0, 0.1, 0.0), edge] + down
        loops = [U[-1] + ring['out'] * 0.06, V(1.2, 0.45, QZ + Rr), V(1.55, 0.6, QZ + Rr), V(1.7, 0.95, QZ + Rr), V(1.35, 1.1, QZ + Rr), V(1.15, 0.85, QZ + Rr),
                 V(1.5, 0.7, QZ + Rr + 0.01), V(1.9, 0.75, QZ + Rr), V(2.0, 1.15, QZ + Rr)]
        path = list(reversed(catm(lead, 6))) + G.smooth_join(list(reversed(lead))[-2:], U, 4) + U + catm(loops, 6)
        C.tube('lazy-line', path, Rr, 12, 1.0, slime)
        for k, p in enumerate(catm(loops, 6)[4::9]):
            hairs(f'weed{k}', p, Vector((1, 0.3, 0)), Rr, 10, 0.05, mat('weed', '#3b4a22', 0.9), seed=k, curl=0.6, spread=0.03)
        K.day_sky(sun_az=215, sun_el=40); K.darken_visible_sky()
        cam = K.camera((2.7, 2.6, 2.3), (0.4, -0.6, 0.75), 32); C.focus_on_centre(cam, 11.0)
        render([ring['c'] + V(0, 0, 0.03), V(1.0, -0.15, QZ * 0.5)])

    # ------------------------------------------------------------------ the rope library's scenes re-used
    raw = json.load(open(os.path.join(HERE, 'scenes', 'winch.json')))['ropes'][0]['P']
    def rawp(i): return raw[i]
    def tan3(i): a, b = Vector(raw[i - 10]), Vector(raw[i + 10]); return (b - a).normalized()
    def B(p): return C.B(*p)

    LEAD_Z = -0.055
    def lead_y(x): return 0.026 if x < -0.46 else 0.012     # above the coaming's teak all the way to the clutch
    def halyard_on_winch(P):
        """A halyard along the coaming through the clutch, then onto the winch's turns, jaws and tail."""
        lead = [[x, lead_y(x), LEAD_Z] for x in [-1.6 + 0.1 * k for k in range(12)]]
        j = 1730; a = Vector(lead[-1]); b = Vector(P[j])
        bridge = []
        for k in range(1, 12):
            t = k / 12; q = a.lerp(b, t); q.y = a.y + (b.y - a.y) * t * t; q.z = a.z + (b.z - a.z) * (t ** 1.6)
            bridge.append(list(q))
        return lead + bridge + [list(p) for p in P[j:]]
    def on_lead(x):
        return (x, lead_y(x), LEAD_Z)

    def tape(g):
        x0 = -0.62 - 0.07 - 0.05      # 5 cm short of the clutch's forward end (its mast side)
        for x in (x0, ):
            p0 = B(on_lead(x)); p1 = B(on_lead(x - 0.045))
            sleeve('tape', p0, p1, 0.0092, mat('tape', '#0b0b0c', 0.75))
    def more_clutches(g, lines=True, colours=(('#2b4d8c', '#f0ece2'), ('#c8161d', '#f0ece2'))):
        for k, dz in enumerate((-0.06, 0.06)):
            G.clutch(C.B(-0.62, 0.0, LEAD_Z + dz), V(1, 0, 0), 0.14)
            if lines:
                z = LEAD_Z + dz
                pts = [(x, lead_y(x), z) for x in (-1.6, -1.3, -1.0, -0.8, -0.7, -0.6, -0.5)] + [(-0.42, 0.012, z + 0.02 * (1 if dz > 0 else -1)), (-0.36, 0.01, z + 0.09 * (1 if dz > 0 else -1)), (-0.38, 0.008, z + 0.2 * (1 if dz > 0 else -1))]
                C.braid(f'other-line{k}', [C.V3(p) for p in C.catmull_centripetal([Vector(p) for p in pts], 8)], 0.0055, colours[k][1], colours[k][0], fine=1.4)

    def ci066():
        def more(g):
            more_clutches(g)
            p = B((-0.2, 0.01, 0.15))
            hairs('chafe', p, Vector((0.1, 0, 1)), 0.0062, 40, 0.012, mat('chafe-fibre', '#efeadc', 0.8), seed=3, curl=0.4, spread=0.02)
        R['winch']('E', clutch=True, more=more, labpts=[(-0.2, 0.02, 0.15), (0.03, 0.29, 0.0)])
    def ci081():
        R['winch']('A', labpts=[(-0.62, -0.02, -0.39), (0.035, 0.17, 0.045)])
    def ci108():
        i = 1660; p = rawp(i); t = tan3(i)
        def more(g):
            pB = B(p); tB = B(tuple(t)) - B((0, 0, 0))
            sleeve('core', pB - tB * 0.025, pB + tB * 0.025, 0.0058, mat('core', '#e9dfbd', 0.85))
            hairs('cover-fray', pB, tB, 0.0066, 45, 0.014, mat('cover-fibre', '#f2efe7', 0.8), seed=7, curl=0.4, spread=0.03)
        R['winch']('A', more=more, labpts=[(-0.62, -0.02, -0.39), (p[0], p[1] + 0.012, p[2])])
    def ci109():
        def more(g): more_clutches(g, colours=(('#c8161d', '#f0ece2'), ('#2b4d8c', '#f0ece2')))
        R['winch']('A', clutch=True, rope_more=halyard_on_winch, more=more, labpts=[(-0.4, 0.015, -0.17), (-1.15, 0.015, LEAD_Z)])
    def ci123():
        def more(g): tape(g); more_clutches(g)
        R['winch']('A', clutch=True, rope_more=halyard_on_winch, more=more, labpts=[(-1.0, 0.035, LEAD_Z), (-0.757, 0.04, LEAD_Z), (-0.3, 0.04, -0.06)])
    def ci126():
        def more(g):
            more_clutches(g)
            at = C.B(0.13, 0.05, -0.13)
            C.cyl('button-bezel', 0.021, 0.021, 0.008, 32, mat('bezel', '#d3d6d8', 0.2, 1.0), at + V(0, 0, 0.004))
            C.cyl('button-cap', 0.014, 0.014, 0.008, 32, mat('button', '#1a1b1d', 0.5, 0.0, 0.3), at + V(0, 0, 0.01))
        R['winch']('A', clutch=True, rope_more=halyard_on_winch, more=more, labpts=[(-1.05, 0.02, LEAD_Z), (0.0, 0.3, 0.0), (0.13, 0.065, -0.13)])

    CLEAT_CAM = ((0.5, 0.78, 0.5), (-0.2, 0.0, -0.33), 40)
    def ci413():
        """The cleat hitch with a hardened, kinked line, its cover worn through in one place."""
        orig = C.three_strand
        def strand(name, pts3, R0=0.013, *a, **k):
            C.braid(name, pts3, R0 * 0.85, '#b4ad99', '#6d6656', fine=1.2)
        def kinks(P):
            P = [list(p) for p in P]
            for c in (2300, 2650, 2950, 3200):
                for k in range(-25, 26):
                    if 0 <= c + k < len(P):
                        w = max(0.0, 1 - abs(k) / 25) ** 0.6
                        P[c + k][0] += 0.018 * w * (1 if c % 2 else -1); P[c + k][2] += 0.012 * w
            return P
        def more(g):
            C.three_strand = orig
            wp = (-0.2, 0.012, -0.12)
            hairs('wear', B(wp), Vector((1, 0, 0)), 0.011, 60, 0.012, mat('wear-fibre', '#d9d3c2', 0.85), seed=2, curl=0.3, spread=0.025)
            sleeve('worn-core', B((-0.225, 0.011, -0.125)), B((-0.175, 0.011, -0.115)), 0.0095, mat('worn-core', '#efe9d6', 0.9))
        C.three_strand = strand
        R['cleat']('full', rope_more=kinks, more=more, labpts=[(-0.36, 0.06, -0.42), (-0.2, 0.03, -0.12)], cam=CLEAT_CAM)
    def ci430():
        R['cleat']('full', labpts=[(-0.25, 0.04, -0.27), (-0.41, 0.07, -0.49)], cam=CLEAT_CAM)
    def ci423():
        R['rail'](fender_label=True)
    def ci432():
        R['art6']('rtring', extra_pts=lambda g, st: {TEXTS[1]: st['ring']['tip'].lerp(g['cs'], 0.16)})

    return {
        'ci-057': guardrail_faults, 'ci-121': lead_blocks, 'ci-104': genoa_car, 'ci-102': furling_drum, 'ci-134': cam_cleat,
        'ci-130': lazyjack, 'ci-416': lazy_line,
        'ci-066': ci066, 'ci-081': ci081, 'ci-108': ci108, 'ci-109': ci109, 'ci-123': ci123, 'ci-126': ci126,
        'ci-413': ci413, 'ci-430': ci430, 'ci-423': ci423, 'ci-432': ci432,
    }
