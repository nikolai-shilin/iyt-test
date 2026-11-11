# Article yachtmaster-offshore/emergency, its fifteen figures as Blender renders (the 3D half of the before/after).
#   1  Scharnow turn from 130°T: a drone view of the whole turn drawn in her wake, hard over at 130°, reversed at 010°,
#      steady on 310°T running back down her own wake towards the casualty
#   2  a high-sided motor yacht stopped upwind of the man overboard, beam-on, propellers still, drifting down onto him
#   3  engine-room fire: the alarm panel (95 °C, fans still on), the fixed-system release box beside it    (_b)
#   4  flooding: water over the cabin sole, the inflow at a broken seacock, the bilge pump's hose        (_b)
#   5  dismasted, 120 M from port: under power with a jury rig, a spinnaker pole for a mast and the storm jib
#   6  no charging: the chart table at night, 11.9 V and 0 A, only NAV LIGHTS and VHF on, the plot on paper (_b)
#   7  cold water: one alone in the HELP position, three more in a huddle, chests together
#   8  helicopter rescue: steady on 070°T, the wind 040°T 30° on the port bow, the helicopter over the port quarter
#   9  GMDSS sea areas from the air: the coast station, A1 (VHF DSC) and A2 (MF DSC) over the sea, our yacht in A2
#   10 the grab bag in the cockpit: EPIRB, radar SART, AIS-SART, handheld VHF                           (_b)
#   11 channel 16 under radio silence: the fixed VHF (art_vhf.py and a spec)                           (_b)
#   12 the deck log: 245°T struck through with one line, 254°T beside it, initialled                   (_b)
#   13 before the passage: the policy schedule (limits, warranties) and the written extension          (_b)
#   14 arriving from abroad: the Q flag under the starboard spreader, the harbour ahead
#   15 salvage: a tug towing the disabled yacht on a salvage agreement
#   blender --background --factory-startup --python docs/design/blender/art_yof_emergency.py -- --fig 1 [--samples 160] [--out x.jpg]
# Textures come from art_yof_emergency_tex.py (system Python) into the article's tex/ folder; the figures marked _b
# live in art_yof_emergency_b.py, run from here.
import os, sys, math, random, subprocess, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import bpy, bmesh
from mathutils import Vector, Euler, Matrix, noise as mnoise
import common as C, kit as K, kit_world as KW, kit_night as N, kit_instruments as KI

arg = C.cli(); FIG = arg('--fig', 1); SAMPLES = arg('--samples', 160); SCALE = arg('--scale', 100)
ADIR = os.path.join(HERE, '..', 'figure-style', 'articles', 'yachtmaster-offshore', 'emergency')
OUT = arg('--out', os.path.join(ADIR, f'{FIG}-3d.jpg'))
def deg(a): return math.radians(a)

def T(name):
    """tex/<name>.png, drawn by art_yof_emergency_tex.py when missing."""
    d = os.path.join(ADIR, 'tex'); p = os.path.join(d, name + '.png')
    if not os.path.exists(p): subprocess.run(['python3', os.path.join(HERE, 'art_yof_emergency_tex.py'), d, name], check=True)
    return p
def TA(name): T(name); return json.load(open(os.path.join(ADIR, 'tex', name + '.json')))

# the helpers of art_vhf_scenes.py (yacht without the spinnaker leftovers, sailing/motoring, helicopter, coast mast,
# domes and dashed rings, foam), taken from its source: importing it would run its figure
_src = open(os.path.join(HERE, 'art_vhf_scenes.py')).read()
C.reset()
exec(_src[_src.index('_load = K.load_yacht'):_src.index("if ART == 'channels' and FIG == 7")], globals())
import q_encounter_props as P

if FIG in (3, 4, 6, 10, 11, 12, 13):
    exec(compile(open(os.path.join(HERE, 'art_yof_emergency_b.py')).read(), 'art_yof_emergency_b.py', 'exec')); sys.exit(0)


labels, arrows, note, extra, expo = [], [], None, {}, -0.6
def fwd(h): return Vector((math.sin(deg(h)), math.cos(deg(h)), 0.0))

def foam_ribbon(pts, w0, w1, a0, a1, name='wake', z=0.2):
    """A wake along a path (x, y list, newest last): w0/a0 its width and whiteness at the boat, w1/a1 at the oldest
    end; broken foam (noise) fading out to its edges."""
    P2 = [Vector((x, y, 0)) for x, y in pts]; n = len(P2)
    L = [0.0]
    for i in range(1, n): L.append(L[-1] + (P2[i] - P2[i - 1]).length)
    tot = L[-1]; verts, faces, uvs = [], [], []
    for i, p in enumerate(P2):
        d = (P2[min(n - 1, i + 1)] - P2[max(0, i - 1)]).normalized(); s = Vector((d.y, -d.x, 0))
        age = 1 - L[i] / tot; w = w0 + (w1 - w0) * age
        verts += [tuple(p + s * w / 2 + Vector((0, 0, z))), tuple(p - s * w / 2 + Vector((0, 0, z)))]
    for i in range(n - 1):
        a = 2 * i; faces.append((a, a + 1, a + 3, a + 2))
        age0, age1 = 1 - L[i] / tot, 1 - L[i + 1] / tot
        uvs += [(age0, 0), (age0, 1), (age1, 1), (age1, 0)]
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    me.uv_layers.new(name='UVMap').data.foreach_set('uv', [c for uv in uvs for c in uv])
    m, nt, b, out = C.new_mat(name)
    uvn = C.node(nt, 'ShaderNodeUVMap'); sep = C.node(nt, 'ShaderNodeSeparateXYZ'); C.link(nt, uvn.outputs['UV'], sep.inputs['Vector'])
    fade = C.node(nt, 'ShaderNodeMapRange', in_To_Min=a0, in_To_Max=a1); C.link(nt, sep.outputs['X'], fade.inputs['Value'])
    edge = C.math_(nt, 'MULTIPLY', C.math_(nt, 'MULTIPLY', sep.outputs['Y'], C.math_(nt, 'SUBTRACT', 1.0, sep.outputs['Y'])), 4.0)
    edge = C.math_(nt, 'POWER', edge, 0.6)
    oc = C.obj_coords(nt); nz_ = C.ramp(nt, [(0.35, (0.45, 0.45, 0.45, 1)), (0.65, (1, 1, 1, 1))]); C.link(nt, C.noise(nt, oc, 1.4, 8.0), nz_.inputs['Fac'])
    msk = C.math_(nt, 'MULTIPLY', C.math_(nt, 'MULTIPLY', fade.outputs['Result'], edge), nz_.outputs['Color'])
    C.setin(b, 'Base Color', C.lin('#eef3f4')); C.setin(b, 'Roughness', 0.8)
    tp = C.node(nt, 'ShaderNodeBsdfTransparent'); mx = C.node(nt, 'ShaderNodeMixShader')
    C.link(nt, msk, mx.inputs['Fac']); C.link(nt, tp.outputs[0], mx.inputs[1]); C.link(nt, b.outputs[0], mx.inputs[2]); C.link(nt, mx.outputs[0], out.inputs['Surface'])
    o = C.obj(name, me, m); o.visible_shadow = False
    return o

def furl(yt): N.cloth_furled(yt)

def limb(name, a, b, r, mat): return P._limb(name, a, b, r, mat)
def ball(name, r, mat, loc, scale=(1, 1, 1)):
    o = C.obj(name, K._sphere(name, r), mat, tuple(loc)); o.scale = scale; return o

# ======================================================================================================== figures
if FIG == 1:
    # the track: in on 130°T, hard to starboard through 240° (radius R), a straight run while the helm goes over,
    # back to port through 60° onto 310°T; the straight is solved so she ends on her own track line
    R = 26.0
    def track(Ls, h0=130.0, x=0.0, y=0.0):
        pts = [(x, y)]; h = h0; marks = {}
        def step(ds, dh):
            nonlocal x, y, h
            h += dh; x += math.sin(deg(h)) * ds; y += math.cos(deg(h)) * ds; pts.append((x, y))
        for i in range(240): step(R * deg(1.0), 1.0)
        marks['rev'] = (x, y)
        for i in range(10): step(Ls / 10, 0.0)
        for i in range(60): step(R * deg(1.0), -1.0)
        marks['steady'] = (x, y)
        return pts, marks
    u = fwd(130)
    lo_, hi_ = 0.0, 80.0
    for _ in range(40):
        mid = (lo_ + hi_) / 2; pts, mk = track(mid); x, y = pts[-1]
        off = x * u.y - y * u.x
        if off > 0: lo_ = mid
        else: hi_ = mid
    pts, mk = track((lo_ + hi_) / 2)
    approach = [(-u.x * s, -u.y * s) for s in range(200, 0, -4)]
    sx, sy = pts[-1]; back = fwd(310)
    run = [(sx + back.x * s, sy + back.y * s) for s in range(4, 18, 4)]
    path = approach + pts + run
    boat = Vector((run[-1][0], run[-1][1], 0))
    K.sea('calm', size=40.0, repeat=12, center=(boat.x, boat.y)); K.day_sky(sun_az=200, sun_el=48)
    foam_ribbon(path, 4.0, 13.0, 0.85, 0.12)
    you = K.load_yacht(name='you').place(boat.x + back.x * 9.0, boat.y + back.y * 9.0, heading=310); furl(you)
    mob_at = Vector((-u.x * 175, -u.y * 175, 0))
    P.in_water(tuple(mob_at), 'mob', 310, k=1.6)
    xs = [q[0] for q in path] + [mob_at.x]; ys = [q[1] for q in path] + [mob_at.y]
    c = Vector(((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, 0)) + fwd(40) * 14
    drone(c, 250, 220, 60, 30)
    labels = [((u.x * 22, u.y * 22, 2), '130°T: wheel hard to starboard'), ((mk['rev'][0], mk['rev'][1], 2), 'at 010°T: wheel hard to port'),
              (tuple(you.world((K.MAST.x, K.MAST.y, 16.0))), 'steady on 310°T', 'blue'),
              (tuple(mob_at + Vector((0, 0, 2.0))), 'search back along the wake', 'red')]
    note = 'Scharnow turn from 130°T'

elif FIG == 2:
    # a 17 m motor yacht stopped beam-on to a westerly, the casualty 26 m to leeward (east); she drifts onto him
    K.sea('breeze', size=36.0, repeat=10); K.day_sky(sun_az=200, sun_el=40)
    spin, vis, tp = P.motor_yacht((0, 0), 180, 17.0)          # the model comes in reversed: 180 puts her bow north
    bpy.context.view_layer.update(); lo, hi = K.bbox(vis)
    mob = Vector((hi.x + 22.0, 0.0, 0))
    P.in_water(tuple(mob), 'mob', 270, k=1.35)
    # a scrambling net hung over her lee side amidships, ready
    net = C.simple('net', '#d9d3c0', 0.8)
    for k in range(9):
        x = hi.x + 0.05; yy = -2.0 + k * 0.5
        limb('net-v', (x, yy, hi.z * 0.42), (x + 0.15, yy, 0.1), 0.02, net)
    for j in range(5):
        z = 0.2 + j * (hi.z * 0.42 - 0.2) / 4
        limb('net-h', (hi.x + 0.05 + 0.15 * (1 - j / 4), -2.0, z), (hi.x + 0.05 + 0.15 * (1 - j / 4), 2.0, z), 0.02, net)
    drone((mob.x * 0.42, 0, 2.0), 40, 165, 21, 30)
    w0 = Vector((-9.5, -8, 4)); w1 = Vector((-2.5, -8, 4))
    arrows = [(tuple(w0), tuple(w1), 'blue'), ((hi.x + 2.5, -6, 0.6), (mob.x - 3, -6, 0.6), 'red')]
    labels = [(tuple(tp + Vector((0, 0, 1.5))), 'stopped upwind, beam-on, props still', 'blue'),
              (tuple(w0 + Vector((0, 0, 1.5))), 'Wind', 'blue'), (tuple(mob + Vector((0, 0, 1.0))), 'MOB', 'red'),
              ((hi.x + 9, -6, 2.2), 'she drifts down onto him')]
    note = 'High freeboard: stop upwind, beam-on'
    extra = {'lines': ['Lift him amidships to leeward, in a net']}

elif FIG == 5:
    # dismasted: the rig cut away, a spinnaker pole stepped as a jury mast with the storm jib, motoring
    K.sea('breeze', size=36.0, repeat=10); K.day_sky(sun_az=230, sun_el=35)
    you = K.load_yacht(name='you')
    bpy.context.view_layer.update()
    for o in you.objs:
        if o.type == 'MESH':
            lo, hi = K.bbox([o])
            if hi.z > 5.2: o.hide_render = True
    you.place(0, 0, heading=40)
    K.wake(you, 34, 7, 0.8)
    al = C.simple('alu', '#c8ccd0', 0.3, 0.9); wire = C.simple('jury-line', '#e8e4d8', 0.6)
    foot = you.world((K.MAST.x, K.MAST.y, 3.55)); head = you.world((K.MAST.x + 0.3, K.MAST.y, 9.6))
    P._limb('jury-mast', foot, head, 0.045, al)
    C.cyl('mast-stump', 0.13, 0.13, 0.35, 16, C.simple('stump', '#b9bcc0', 0.4, 0.7), tuple(foot + Vector((0, 0, 0.1))))
    stem = you.world((10.55, K.MAST.y, 3.95)); shs = [you.world((K.MAST.x - 0.6, K.MAST.y + s * 1.9, 3.65)) for s in (-1, 1)]
    stern = [you.world((-3.2, K.MAST.y + s * 1.6, 3.8)) for s in (-1, 1)]
    for p in [stem] + shs + stern: P._limb('jury-stay', head, p, 0.008, wire)
    # the storm jib on the jury forestay: small, orange
    tack = head.lerp(stem, 0.88); hd = head.lerp(stem, 0.08); clew = you.world((K.MAST.x + 0.4, K.MAST.y - 1.6, 4.4))
    me = bpy.data.meshes.new('storm-jib'); me.from_pydata([tuple(tack), tuple(hd), tuple(clew)], [], [(0, 1, 2)]); me.update()
    sj = C.obj('storm-jib', me, C.simple('storm-jib', '#f06a1a', 0.6)); sj.modifiers.new('s', 'SOLIDIFY').thickness = 0.01
    c = you.world((3.0, 0.13, 3.0))
    drone(c, 30, 170, 22, 32)
    labels = [(tuple(foot.lerp(head, 0.55)), 'jury mast: spinnaker pole, storm jib', 'blue'),
              (tuple(you.world((-3.6, 0.13, 3.0))), 'under power: 72 L usable = 96 M')]
    note = 'Dismasted, 120 M from port'
    extra = {'lines': ['Every line aboard before the propeller turns']}

elif FIG == 7:
    # cold water: one alone in HELP (leaning back in the lifejacket, knees up, arms crossed); three huddled
    K.sea('calm', size=24.0, repeat=10); K.day_sky(sun_az=215, sun_el=34)
    skin = C.simple('skin', P.SKIN, 0.6); jk = C.simple('lifejacket', '#e8500a', 0.5, coat=0.2); hair = C.simple('hair', '#2a2018', 0.8)
    cols = ['#26354f', '#3a4a2a', '#5a2a2a', '#2a3a5a']
    def jacket(at, heading, lean):
        """The inflated lifejacket round the chest, tilted back `lean` degrees; returns (shoulder centre, up, fwd)."""
        f, r = fwd(heading), Vector((math.cos(deg(heading)), -math.sin(deg(heading)), 0))
        up = (Vector((0, 0, 1)) * math.cos(deg(lean)) - f * math.sin(deg(lean))).normalized()
        o = C.obj('jacket', K._sphere('jacket', 0.3), jk, tuple(at)); o.scale = (0.75, 0.95, 0.5)
        o.rotation_euler = Euler((0, deg(-lean), deg(90 - heading)), 'XYZ')
        return f, r, up
    def help_pose(at, heading, sleeve):
        at = Vector(at); f, r, up = jacket(at + Vector((0, 0, -0.05)), heading, 45)
        ball('head', 0.12, skin, at + up * 0.34 - f * 0.05); ball('hair', 0.125, hair, at + up * 0.37 - f * 0.08, (1, 1, 0.7))
        ball('collar', 0.16, jk, at + up * 0.2, (1.1, 1.0, 0.6))
        sl = C.simple('sleeve', sleeve, 0.8)
        for s in (-1, 1):                     # arms crossed over the jacket, hands at the opposite shoulder
            sh = at + up * 0.12 + r * s * 0.2; el_ = at + f * 0.24 + r * s * 0.05 + up * 0.0
            limb('arm', sh, el_, 0.055, sl); limb('forearm', el_, at + up * 0.14 - r * s * 0.14 + f * 0.2, 0.05, sl)
        for s in (-1, 1):                     # knees drawn up to the chest, just under the surface
            hip = at - up * 0.32 + r * s * 0.1; knee = at + f * 0.42 + r * s * 0.12 - Vector((0, 0, 0.02))
            limb('thigh', hip, knee, 0.075, C.simple('legs', '#2c3440', 0.8)); limb('shin', knee, knee - Vector((0, 0, 0.45)) - f * 0.1, 0.06, C.simple('legs', '#2c3440', 0.8))
        foam_patch(at, 0.3, 0.75, 0.9, scale=6.0, strength=0.45)
    def huddle(c, n=3, R=0.42):
        c = Vector(c); heads = []
        for i in range(n):
            a = deg(i * 360 / n + 20); p = c + Vector((math.sin(a) * R, math.cos(a) * R, 0)); h = (math.degrees(a) + 180) % 360
            f = fwd(h); r = Vector((math.cos(deg(h)), -math.sin(deg(h)), 0))
            o = C.obj('jacket', K._sphere('jacket', 0.3), jk, tuple(p + Vector((0, 0, -0.04)))); o.scale = (0.95, 0.8, 0.45); o.rotation_euler = (0, 0, deg(90 - h))
            ball('head', 0.12, skin, p + Vector((0, 0, 0.2)) + f * 0.04); ball('hair', 0.125, hair, p + Vector((0, 0, 0.24)), (1, 1, 0.7))
            heads.append((p, f, r))
        for i, (p, f, r) in enumerate(heads):        # arms round the neighbours' shoulders
            sl = C.simple('sleeve%d' % i, cols[i % 4], 0.8)
            for s in (-1, 1):
                q, fq, rq = heads[(i + s) % n]
                limb('arm', p + r * s * 0.2 + Vector((0, 0, 0.1)), q - fq * 0.1 + Vector((0, 0, 0.14)), 0.05, sl)
        foam_patch(c, 0.6, 1.2, 1.4, scale=6.0, strength=0.45)
    help_pose((0, 0, 0.0), 160, cols[0])
    huddle((3.6, 1.6, 0.0))
    drone((1.8, 0.8, 0.0), 5.6, 196, 36, 35)
    labels = [((0, 0, 0.75), 'alone: HELP, knees up, arms crossed', 'blue'), ((3.6, 1.6, 0.8), 'together: huddle, chests touching', 'blue')]
    note = 'Cold water: 1-10-1'
    extra = {'lines': ['1 min shock · 10 min to swim · 1 h before hypothermia']}

elif FIG == 8:
    # helicopter rescue: we steer 070°T, the wind from 040°T is 30° on the port bow; the helicopter over our port
    # quarter, nose into the wind, the hi-line down to the stern
    K.sea('breeze', size=36.0, repeat=10); K.day_sky(sun_az=150, sun_el=40)
    you = motoring('you', 70, 0, 0); furl(you); K.wake(you, 30, 6, 0.7)
    stern = you.world((-3.4, 1.0, 3.7))
    def rot(x, y, h=70.0):
        a = deg(h); return Vector((x * math.cos(a) + y * math.sin(a), -x * math.sin(a) + y * math.cos(a), 0))
    o_ = rot(-6.0, -8.0); hc = Vector((stern.x + o_.x, stern.y + o_.y, 30.0))
    heli, hook = helicopter(hc, 40)
    for o in heli.children: o.visible_shadow = False
    _rod(hook, stern + Vector((0, 0, 0.3)), 0.025, C.simple('wire', '#b9bcbf', 0.3, 1.0))
    sphere('hook', 0.18, C.simple('hook', '#d8a21a', 0.4, 0.6), stern + Vector((0, 0, 0.45)), 12)
    cc = rot(-3.5, -7.0); drone((cc.x, cc.y, 17.5), 68, 248 + 70, 10, 32)
    u = fwd(40 + 180); wa = rot(-8, 15) + Vector((0, 0, 13))
    arrows = [(tuple(wa), tuple(wa + u * 13), 'blue')]
    labels = [(tuple(wa + Vector((0, 0, 2.5))), 'wind 040°T: 30° on the port bow', 'blue'),
              (tuple(you.world((10.4, 0.13, 6.5))), 'steer 070°T, hold course and speed', 'blue'),
              (tuple(hc + Vector((0, 0, 6.0))), 'rescue helicopter')]
    note = 'Helicopter: steer what the pilot asks'

elif FIG == 9:
    # from the air: a coast with its coast station; A1 (VHF DSC) a dome over the near sea, A2 (MF DSC) far beyond,
    # our yacht in A2. The ranges are drawn much shorter than 30 M and 150 M so both fit in the picture.
    K.sea('breeze', size=40.0, repeat=12, center=(400, -1400)); horizon_sea(); K.day_sky(sun_az=205, sun_el=40)
    def shore(x): return 1500 + 140 * math.sin(x / 520) + 50 * math.sin(x / 140)
    def fn(x, y): return max(land_z(y - shore(x), x, y, hmax=160, rise=0.3, seed=1.0), bump(x, y, 0, 1950, 300, 330, 280) - 3)
    heightfield('land', fn, -40000, 40000, 1000, 40000, 150, aerial_land_mat(9000))
    gz = ground_z(0, 1950); mtop = coast_mast((0, 1950), gz - 3, 160)
    dome((0, 1650), 1700, '#8fd0ff', 0.08, 0.30)
    ring_dashes((0, 1650), 1700, '#f2c200', 80, 50, 14, 95, 265)
    ring_dashes((0, 1650), 4300, '#ff8a3d', 140, 90, 22, 110, 250, name='rim2')
    you = sailing('you', 80, 20, 900, -1700, k=9.0); K.wake(you, 60, 12)
    drone((0, -700, 0), 9000, 182, 30, 30)
    labels = [(tuple(mtop + Vector((0, 0, 120))), 'coast station'), ((0, 480, 300), 'A1 · VHF DSC · ≈ 30 M', 'blue'),
              ((-3000, -1100, 200), 'A2 · MF DSC · ≈ 150 M', 'yellow'), (tuple(top(you, 30)), 'You: in A2, MF DSC', 'blue'),
              ((0, -4600, 100), 'A3 beyond: satellite')]
    note = "Sea areas follow the coast stations' DSC cover"
    bpy.context.scene.camera.data.clip_end = 400000

elif FIG == 14:
    # arriving from abroad: motoring in past the harbour mole, Q flying under the starboard spreader
    K.sea('calm', size=30.0, repeat=14, center=(0, -60)); K.day_sky(sun_az=230, sun_el=38)
    KW.terrain(-700, 700, -250, 900, 6.0); KW.town(cx=40, width=300, n=170); KW.trees(700)
    KW.mole((-260, 70), (-30, 40), width=9.0, height_=2.6)
    you = P.yacht('you').place(30, -20, heading=345); furl(you); K.wake(you, 24, 5, 0.6)
    hoist = you.world((K.MAST.x - 0.1, K.MAST.y - 1.62, 9.3))
    P.flag(hoist, 345 + 180, w=0.75, h=0.55, color='#f5c400')
    P._limb('flag-halyard', you.world((K.MAST.x - 0.1, K.MAST.y - 1.68, 9.38)), you.world((K.MAST.x - 0.05, K.MAST.y - 0.3, 3.7)), 0.004, C.simple('halyard', '#e8e4d8', 0.6))
    ens = you.world((-3.7, K.MAST.y, 4.3))
    P.flag(ens + Vector((0, 0, 1.0)), 345 + 180, w=0.75, h=0.5, color='#2a4fa0')
    C.cyl('ensign-staff', 0.015, 0.015, 1.3, 8, C.simple('staff', '#e8e4d8', 0.5), tuple(ens + Vector((0, 0, 0.5))))
    K.camera(tuple(you.world((5.0, -24.0, 5.5))), tuple(you.world((3.6, -0.5, 7.4))), 35)
    labels = [(tuple(hoist + Vector((0, 0, 0.2))), 'Q under the starboard spreader', 'yellow'),
              (tuple(you.world((-2.6, 0.13, 5.4))), 'skipper lands alone: crew list, passports')]
    note = 'From arrival until you are cleared'

elif FIG == 15:
    # salvage: a tug towing the disabled yacht, sails down, on a long towline from her bow
    K.sea('breeze', size=40.0, repeat=12, center=(0, -40)); K.day_sky(sun_az=210, sun_el=40)
    def hide(o):
        ms = ' '.join(sl.material.name for sl in o.material_slots if sl.material)
        if 'wake' in ms or 'sea' in ms: return True
        lo, hi = K.bbox([o])
        return (hi.y - lo.y) > 11 and lo.z > -3            # the fire-fighting water jets
    tug, tvis = vessel('vessel-tug.glb', (0, 30), 0, 30.0, None, flip=False, draft=K.TUG_DRAFT, hide=hide)
    bpy.context.view_layer.update(); tlo, thi = K.bbox(tvis)
    yt = motoring('casualty', 0, 0, -48); furl(yt); K.wake(yt, 20, 5, 0.5)
    tstern = Vector(((tlo.x + thi.x) / 2, tlo.y + 1.0, 2.2)); bow = yt.world((10.6, K.MAST.y, 4.0))
    pts = [tstern.lerp(bow, i / 16) - Vector((0, 0, 1.4 * math.sin(math.pi * i / 16))) for i in range(17)]
    C.three_strand('towline', [C.V3((p.x, p.z, -p.y)) for p in pts], 0.03, 0.15)
    drone((0, -12, 3), 85, 120, 22, 30)
    labels = [(tuple(Vector(((tlo.x + thi.x) / 2, (tlo.y + thi.y) / 2, thi.z + 2))), 'salvor: no cure, no pay'),
              (tuple(pts[8] + Vector((0, 0, 1.2))), 'her towline'),
              (tuple(yt.world((K.MAST.x, K.MAST.y, 14.0))), 'the master signs the agreement', 'blue')]
    note = 'Salvage: the award never exceeds the value saved'

else:
    raise SystemExit(f'no figure {FIG}')

C.render(OUT, SAMPLES, SCALE, expo, labels, note, space='blender', arrows=arrows, extra=extra)
