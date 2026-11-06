# Article charter-checkin/safety, its six figures as Blender renders.
#   1  a 150 N automatic lifejacket opened on the cockpit seat: cylinder, firing-head indicator, service label,
#      crotch strap, light and whistle
#   2  man overboard, sailing on port tack: the horseshoe with its light and the danbuoy already in the water by him
#   3  the saloon looking aft: extinguisher in its bracket by the galley (gauge green), one by the aft cabin door
#      (gauge red), the engine box under the steps with its fire port and an empty bracket
#   4  the liferaft launched over the lee side on its painter, made fast to the yacht; the grab bag in the cockpit
#   5  at anchor, a blow coming: reef in, jackstays rigged, crew in lifejackets clipped on
#   6  the skipper's briefing in the cockpit: the crew round the table, the gear pointed at where it lives
#   blender --background --factory-startup --python docs/design/blender/art_checkin_safety.py -- --fig 1 [--samples 160]
import os, sys, math, random
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import bpy, bmesh
from mathutils import Vector
import common as C, kit as K, kit_instruments as KI, kit_world as KW
from common import lin
import art_checkin_nps_kit as A
import q_encounter_props as P

arg = C.cli(); FIG = arg('--fig', 1); SAMPLES = arg('--samples', 160); SCALE = arg('--scale', 100)
OUT = arg('--out', os.path.join(A.outdir('safety'), f'{FIG}-3d.jpg'))
deg = math.radians
T = lambda n: A.tex('safety', n)

# the cloudy sky of art_weather_a.py, taken from its source (importing it would run its figure)
_src = open(os.path.join(HERE, 'art_weather_a.py')).read()
exec(_src[_src.index('def cloud_sky('):_src.index('def compass(')], globals())

C.reset()
M = K.mats()
labels, arrows, note, expo, extra = [], [], None, -0.5, {}

def flat_tube(name, pts, r, mat, flat=0.3, z=0.0):
    """A tube along pts (x, y) squashed to `flat` of its width, lying on z."""
    P3 = [Vector((x, y, 0.0)) for x, y in pts]
    P3 = C.catmull_centripetal(P3, 16) if len(P3) > 2 else P3
    o = C.tube(name, P3, r, 24, 0.05, mat)
    o.scale = (1, 1, flat); o.location = (0, 0, z + r * flat); return o

def webbing(name, pts, w=0.025, t=0.003, mat=None, z=0.0):
    """A flat strap along pts (x, y, z)."""
    mat = mat or C.simple('webbing', '#151617', 0.7, sheen=0.3)
    for i in range(len(pts) - 1):
        a, b = Vector(pts[i]), Vector(pts[i + 1]); d = b - a
        o = C.obj(name, C.rbox(name, (d.length + w * 0.3, w, t), t / 2, 1), mat, tuple((a + b) / 2 + Vector((0, 0, z))))
        o.rotation_euler = (0, -math.atan2(d.z, math.hypot(d.x, d.y)), math.atan2(d.y, d.x))

def extinguisher(name, at, gauge, rotz=0.0, bracket=True):
    """A 2 kg powder extinguisher standing in a wall bracket: red body, black head and lever, the gauge on the head
    facing -Y. at: the bottom centre. Returns the gauge's centre."""
    at = Vector(at); red = C.simple('ext-red', '#b5121b', 0.3, coat=0.8); blk = C.simple('ext-black', '#141414', 0.5)
    C.cyl(name + '-body', 0.045, 0.045, 0.27, 40, red, at + Vector((0, 0, 0.135)))
    A.sphere(name + '-dome', 0.045, red, at + Vector((0, 0, 0.27)), scale=(1, 1, 0.45))
    C.cyl(name + '-head', 0.018, 0.02, 0.06, 20, blk, at + Vector((0, 0, 0.31)))
    C.obj(name + '-lever', C.rbox(name + '-lever', (0.11, 0.022, 0.008), 0.003, 2), blk, at + Vector((0.03, 0, 0.35))).rotation_euler = (0, deg(-8), 0)
    gm = KI.image_mat(name + '-gauge', T(gauge), 0.2)
    g = KI.disc(name + '-gauge', 0.017, gm, at + Vector((0, -0.024, 0.322)), normal='Y-')
    A.quad(name + '-label', 0.075, 0.13, T('ext-label'), at + Vector((0, -0.0455, 0.14)), rot=(deg(90), 0, 0), rough=0.4)
    C.cyl(name + '-hose', 0.007, 0.007, 0.2, 10, blk, at + Vector((0.05, 0.0, 0.2)))
    if bracket: bracket_at(name, at)
    return at + Vector((0, -0.03, 0.322))

def bracket_at(name, at, empty=False):
    at = Vector(at); st = C.simple('bracket', '#2a2c2e', 0.4, 0.5)
    C.obj(name + '-plate', C.rbox(name + '-plate', (0.05, 0.006, 0.3), 0.002, 1), st, at + Vector((0, 0.05, 0.16)))
    for z in (0.07, 0.22):
        o = C.obj(name + '-strap', KI._torus(0.05, 0.004), st, at + Vector((0, 0, z)))
        if empty: o.scale = (1, 1, 1)
    C.obj(name + '-cup', C.rbox(name + '-cup', (0.09, 0.09, 0.01), 0.004, 2), st, at + Vector((0, 0, 0.005)))

if FIG == 1:
    # the cockpit seat (teak, z = 0), the sea beyond; the lifejacket opened flat, collar away from the camera
    K.sea('calm', center=(0, 0)); K.day_sky(sun_az=210, sun_el=50)
    for o in bpy.data.objects:
        if o.name.startswith(('ocean', 'far-sea')): o.location.z -= 1.4
    C.obj('seat', C.rbox('seat', (2.6, 1.8, 0.04), 0.01, 2), M['teak'], (0, 0.3, -0.02))
    navy = C.simple('jacket-navy', '#1f2b48', 0.75, sheen=0.4); yel = C.simple('bladder', '#f2b705', 0.45, coat=0.3)
    U = [(-0.115, -0.25), (-0.115, -0.06), (-0.11, 0.06), (-0.07, 0.14), (0.0, 0.17), (0.07, 0.14), (0.11, 0.06), (0.115, -0.06), (0.115, -0.25)]
    flat_tube('cover', U, 0.078, navy, 0.14)
    flat_tube('bladder', [(x * 0.92, y + 0.005) for x, y in U[:-1]] + [(0.106, -0.19)], 0.048, yel, 0.42, z=0.018)
    # the firing head and cylinder on the right leg, the green indicator window on top
    grey = C.simple('head-grey', '#3b3f44', 0.4); steel = C.simple('cylinder', '#c9ccd0', 0.18, 1.0)
    fh = Vector((0.112, -0.115, 0.05))
    C.obj('firing-head', C.rbox('fh', (0.042, 0.052, 0.03), 0.008, 3), grey, fh)
    A.quad('indicator', 0.016, 0.016, None, fh + Vector((0, 0.008, 0.0155)), mat=A.glow_mat('indicator-green', '#21c24a', 1.5))
    A.rod('cylinder', fh + Vector((0, -0.03, 0)), fh + Vector((0, -0.125, 0)), 0.0145, 0.0145, steel)
    A.sphere('cyl-end', 0.0145, steel, fh + Vector((0, -0.125, 0)))
    C.tube('toggle-cord', [fh + Vector((0.02, -0.01, 0)), fh + Vector((0.05, -0.02, -0.02)), fh + Vector((0.07, -0.05, -0.035))], 0.0018, 8, 0.01, C.simple('cord', '#c9261c', 0.6))
    A.sphere('toggle', 0.009, C.simple('toggle', '#c9261c', 0.4), fh + Vector((0.075, -0.058, -0.035)), scale=(1, 1, 1.6))
    # the service label on the left leg
    sl = Vector((-0.11, -0.12, 0.048)); A.quad('service-label', 0.075, 0.0375, T('service'), sl, rot=(0, 0, deg(90)), rough=0.5)
    # the waist belt and its buckle, the crotch strap hanging from the back of the belt
    webbing('belt-l', [(-0.115, -0.25, 0.01), (-0.24, -0.27, 0.004), (-0.36, -0.25, 0.003)])
    webbing('belt-r', [(0.115, -0.25, 0.01), (0.22, -0.27, 0.004), (0.33, -0.26, 0.003)])
    C.obj('buckle', C.rbox('buckle', (0.04, 0.035, 0.01), 0.004, 2), C.simple('buckle', '#111111', 0.4), (0.25, -0.27, 0.01))
    webbing('crotch', [(0.0, -0.22, 0.02), (0.0, -0.30, 0.008), (0.01, -0.38, 0.003)], w=0.03)
    C.obj('crotch-buckle', C.rbox('cbuckle', (0.035, 0.03, 0.01), 0.004, 2), C.simple('buckle', '#111111', 0.4), (0.01, -0.39, 0.008))
    # the light on the left lobe, the whistle on its lanyard on the right
    lt = Vector((-0.09, 0.115, 0.05))
    C.cyl('light-body', 0.013, 0.013, 0.03, 20, C.simple('light-orange', '#ff6a00', 0.4), lt)
    A.sphere('light-lens', 0.012, C.simple('lens', '#e8f0f2', 0.05, coat=1.0), lt + Vector((0, 0, 0.017)), scale=(1, 1, 0.8))
    wh = Vector((0.10, 0.12, 0.05))
    C.obj('whistle', C.rbox('whistle', (0.045, 0.014, 0.012), 0.005, 2), C.simple('whistle', '#ff6a00', 0.4), wh).rotation_euler = (0, 0, deg(30))
    C.tube('lanyard', [wh + Vector((-0.02, -0.01, 0)), wh + Vector((-0.04, -0.03, -0.005)), wh + Vector((-0.05, -0.06, -0.01))], 0.0015, 6, 0.01, C.simple('lanyard', '#ff6a00', 0.6))
    KI.area_light((0.3, -0.6, 0.9), (0, -0.05, 0), 25, 1.0)
    K.camera((0.03, -0.92, 0.80), (0.0, -0.04, 0.0), 40)
    labels = [(tuple(fh + Vector((0, -0.08, 0.02))), 'cylinder: screwed in tight'), (tuple(fh + Vector((0, 0.008, 0.02))), 'indicator: green', 'green'),
              (tuple(sl + Vector((0, 0, 0.004))), 'service label: in date'), ((0.005, -0.35, 0.012), 'crotch strap: fitted'),
              (tuple(lt + Vector((0, 0, 0.03))), 'light and whistle', 'blue')]
    note = '150 N lifejacket (ISO 12402), opened'; expo = -0.5

elif FIG == 2:
    # port tack close reach, heading 045, wind N; the MOB 35 m off on her port quarter, the gear by him
    K.sea('breeze', repeat=10); K.day_sky(sun_az=200, sun_el=40)
    you = P.sailing_yacht('you', 45, 0, +1, 0, 0); K.wake(you, 40, 8, 1.0)
    mob = A.hdg_vec(45 + 200) * 34
    top = P.in_water((mob.x, mob.y), 'mob', heading=60, k=1.6)
    # the horseshoe lifebuoy with its light, a metre from him; the danbuoy two metres off
    hs = Vector((mob.x + 2.4, mob.y - 2.4, 0.05)); yel = C.simple('horseshoe', '#f2c200', 0.5, coat=0.2)
    U = [(math.cos(deg(a)) * 0.33, math.sin(deg(a)) * 0.33) for a in range(30, 331, 15)]
    o = C.tube('horseshoe', [Vector((hs.x + x, hs.y + y, 0.2)) for x, y in U], 0.11, 20, 0.1, yel)
    lp = hs + Vector((-0.45, 0.1, 0.0))
    C.cyl('hs-light', 0.05, 0.05, 0.35, 16, yel, lp + Vector((0, 0, 0.2))); A.sphere('hs-strobe', 0.05, A.glow_mat('strobe', '#f8f4e8', 3.0), lp + Vector((0, 0, 0.4)))
    db = Vector((mob.x - 2.2, mob.y + 3.2, 0)); K.dan_buoy((db.x, db.y))
    wake_start = you.world((-3.8, 0.13, 2.0))
    A.drone(Vector((mob.x * 0.82, mob.y * 0.82, 1.5)), 24, az=232, el=24, lens=30)
    labels = [(tuple(top + Vector((0, 0, 1.9))), 'MOB', 'red'), (tuple(hs + Vector((0, 0, 0.4))), 'horseshoe and light'),
              (tuple(db + Vector((0, 0, 2.5))), 'danbuoy')]
    note = 'Horseshoe, light and danbuoy go over at once'
    extra = {'lines': ['Quick-release clip, never a knot']}; expo = -0.5

elif FIG == 3:
    # the saloon looking aft (+Y): the companionway in the middle, the engine box under its steps, the galley to
    # port (left), the aft cabin door to starboard (right)
    sc = bpy.context.scene; w = bpy.data.worlds.new('dim'); sc.world = w
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.02, 0.025, 0.03, 1)
    join = KI.joinery_mat(); white = C.simple('cabinet', '#e9e6df', 0.45, coat=0.3)
    C.obj('sole', C.rbox('sole', (5.0, 4.0, 0.04), 0.0, 1), M['teak'], (0, -1.4, -0.02))
    KI.wall('bulkhead', -2.0, 2.0, 0.0, 2.1, 0.62, join)
    C.obj('deckhead', C.rbox('deckhead', (4.0, 4.0, 0.03), 0.0, 1), C.simple('lining', '#e6e2d8', 0.8), (0, -1.4, 2.12))
    # companionway: the engine box, steps above it rising aft to the bright hatch
    eb = C.obj('engine-box', C.rbox('engine-box', (0.78, 0.5, 0.62), 0.01, 2), join, (0, 0.36, 0.31))
    for i in range(4):
        C.obj(f'step{i}', C.rbox(f'step{i}', (0.66, 0.22, 0.04), 0.01, 2), M['teak'], (0, 0.36 + 0.06 * i, 0.64 + 0.36 * i))
        C.obj(f'stringer{i}', C.rbox('stringer', (0.03, 0.3, 0.38), 0.005, 1), join, (0.35 * (1 if i % 2 else -1), 0.45, 0.82 + 0.36 * (i // 2) * 2))
    C.obj('hatch-dark', C.rbox('hatch', (0.7, 0.02, 1.4), 0.0, 1), C.simple('hatch-void', '#0b0d10', 0.9), (0, 0.615, 1.4))
    sky = C.new_mat('companionway-sky')[0]; nt = sky.node_tree; nt.nodes.clear()
    o_ = nt.nodes.new('ShaderNodeOutputMaterial'); e_ = nt.nodes.new('ShaderNodeEmission'); e_.inputs['Color'].default_value = C.lin('#cfe0ee'); e_.inputs['Strength'].default_value = 5.0
    nt.links.new(e_.outputs[0], o_.inputs['Surface'])
    C.obj('hatch-light', C.rbox('hl', (0.66, 0.02, 0.6), 0.0, 1), sky, (0, 0.6, 1.8))
    KI.area_light((0.0, 0.2, 1.9), (0.0, -1.0, 0.8), 160, 0.7, (0.95, 0.97, 1.0))
    # the fire port in the engine box front: a dark round hole with its red label; the empty bracket beside it
    KI.disc('fire-port', 0.03, C.simple('port-void', '#060606', 0.9), (0.12, 0.105, 0.42), normal='Y-')
    C.obj('fire-port-rim', KI._torus(0.032, 0.005), C.simple('rim', '#1a1a1a', 0.4), (0.12, 0.104, 0.42)).rotation_euler = (deg(90), 0, 0)
    A.quad('fire-port-label', 0.11, 0.035, T('fireport'), (0.12, 0.104, 0.49), rot=(deg(90), 0, 0))
    bracket_at('engine-bracket', (-0.2, 0.06, 0.12), empty=True)
    # the galley to port, its extinguisher on the bulkhead by the way out
    C.obj('counter', C.rbox('counter', (1.2, 0.6, 0.9), 0.01, 2), white, (-1.35, 0.3, 0.45))
    C.obj('worktop', C.rbox('worktop', (1.25, 0.64, 0.04), 0.008, 2), C.simple('worktop', '#c9c3b6', 0.35, coat=0.6), (-1.35, 0.3, 0.92))
    C.obj('hob', C.rbox('hob', (0.55, 0.4, 0.02), 0.005, 2), C.simple('hob-steel', '#b9bcbe', 0.3, 0.9), (-1.45, 0.32, 0.95))
    g1 = extinguisher('galley-ext', (-0.6, 0.55, 1.02), 'gauge-green')
    # the aft cabin door to starboard, open, dark inside; its extinguisher on the bulkhead by the door
    C.obj('door-void', C.rbox('door-void', (0.6, 0.02, 1.75), 0.0, 1), C.simple('cabin-void', '#120f0c', 0.9), (1.15, 0.61, 0.88))
    door = C.obj('door', C.rbox('door', (0.58, 0.03, 1.72), 0.005, 2), join, (0.86, 0.33, 0.87)); door.rotation_euler = (0, 0, deg(-62))
    g2 = extinguisher('cabin-ext', (0.6, 0.55, 0.9), 'gauge-red')
    KI.area_light((0.0, -1.8, 1.9), (0.0, 0.5, 0.9), 70, 1.4, (1.0, 0.93, 0.84))
    KI.area_light((-1.2, -0.5, 1.95), (-1.0, 0.5, 0.9), 20, 0.6, (1.0, 0.93, 0.84))
    K.camera((0.0, -2.35, 1.42), (0.0, 0.4, 0.92), 30)
    labels = [(tuple(g1 + Vector((0, 0, 0.0))), 'galley: gauge green', 'green'), (tuple(g2 + Vector((0, 0, 0.0))), 'aft cabin: gauge red', 'red'),
              ((-0.2, 0.06, 0.33), 'engine: bracket empty', 'red'), ((0.12, 0.1, 0.53), 'fire port')]
    note = 'Each one in its bracket, by a way out'
    extra = {'lines': ['Gauge in the red: replaced before you sign']}; expo = 0.5

elif FIG == 4:
    # wind from the east, heading north: port (west) is the lee side; the raft inflated to leeward on its painter
    K.day_sky(sun_az=210, sun_el=30); K.sea('breeze', repeat=10)
    y = A.yacht('you').place(0, 0, heading=0)
    orange = C.simple('raft-orange', '#b02e00', 0.7); dark = C.simple('raft-floor', '#202428', 0.8)
    rc = Vector((-6.8, -3.4, 0.0))
    A.torus('raft-tube-lo', 1.05, 0.17, orange, rc + Vector((0, 0, 0.12))); A.torus('raft-tube-hi', 1.05, 0.17, orange, rc + Vector((0, 0, 0.44)))
    C.cyl('raft-floor', 1.0, 1.0, 0.05, 48, dark, rc + Vector((0, 0, 0.02)))
    A.torus('raft-arch', 0.95, 0.07, orange, rc + Vector((0, 0, 0.6)), rot=(deg(90), 0, deg(20)))
    can = A.sphere('raft-canopy', 1.0, C.simple('raft-canopy', '#b83800', 0.8), rc + Vector((0, 0, 0.55)), seg=48, scale=(0.96, 0.96, 0.62))
    bm = bmesh.new(); bm.from_mesh(can.data); bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < 0.0 or (v.co.x > 0.55 and v.co.z < 0.65)], context='VERTS'); bm.to_mesh(can.data); bm.free()
    A.torus('raft-band', 1.06, 0.03, C.simple('reflective', '#e8ecef', 0.2, 0.6), rc + Vector((0, 0, 0.62)))
    # the two canister halves floating beside it
    for i, dp in enumerate((Vector((1.4, -1.2, 0.08)), Vector((0.6, -1.6, 0.08)))):
        h = A.sphere(f'canister{i}', 0.32, C.simple('canister', '#e9e7e1', 0.4, coat=0.5), rc + dp, scale=(1.0, 1.0, 0.45))
    # the painter from the port quarter cleat, slack across the water
    cleat = y.world((-2.9, 1.65, 3.62)); p_end = rc + Vector((0.95, 0.35, 0.45))
    d = (p_end - cleat); d.z = 0; d.normalize(); side = Vector((-d.y, d.x, 0))
    pts = [cleat, cleat + d * 0.3 + Vector((0, 0, 0.08)), cleat + d * 0.55 + Vector((0, 0, -0.5)), cleat + d * 0.75 + Vector((0, 0, -1.2))]
    w_ = cleat + d * 1.0; w_.z = 0.03; pts.append(w_)
    for t in (0.2, 0.4, 0.6, 0.8):
        q = w_.lerp(p_end, t) + side * math.sin(t * math.pi) * 0.6; q.z = 0.03; pts.append(q)
    q = p_end.copy(); q.z = 0.06; pts += [q - d * 0.15, p_end]
    A.line('painter', pts, R=0.016, base='#f0ede4', fleck='#c4161c')
    bag = A.sphere('grab-bag', 0.22, C.simple('grab-yellow', '#f2c200', 0.5, coat=0.2), y.world((-1.9, 0.9, 3.85)), scale=(1.0, 0.75, 1.25))
    C.cyl('grab-top', 0.12, 0.12, 0.08, 24, C.simple('grab-black', '#111214', 0.6), y.world((-1.9, 0.9, 4.14)))
    # the empty cradle on the pushpit
    st = C.simple('cradle', '#c9ccd0', 0.25, 1.0); cr = y.world((-3.55, 1.0, 4.2))
    for dx in (-0.25, 0.25): A.rod('cradle-bar', cr + Vector((dx, -0.35, 0)), cr + Vector((dx, 0.35, 0)), 0.015, 0.015, st)
    eye = y.world((-13.5, 10.5, 7.5)); look = y.world((-3.6, 3.8, 2.4))
    K.camera(tuple(eye), tuple(look), 28)
    w0, w1 = rc + Vector((4.8, -8.0, 0.8)), rc + Vector((0.6, -6.2, 0.8)); arrows = [(tuple(w0), tuple(w1), 'blue')]
    labels = [(tuple(rc + Vector((0, 0, 1.55))), 'over the lee side', 'red'), (tuple(w_.lerp(p_end, 0.5) + Vector((0, 0, 0.2))), 'painter made fast to the yacht'),
              (tuple(y.world((-1.9, 0.9, 4.45))), 'grab bag', 'blue'), (tuple(w0 + Vector((0, 0, 1.0))), 'Wind', 'blue')]
    note = 'Launching the liferaft'
    extra = {'lines': ['Pull the painter until it fires · cut it last']}; expo = -0.5

elif FIG == 5:
    # at anchor, bow to a fresh northerly, a dark sky coming; reefed main up, jackstays, two crew clipped on
    cloud_sky(zenith='#4a5561', horizon='#9a978f', dark='#3f4650', light='#767d86', cover=0.85, sharp=0.3, scale=1.6,
              sun=(220, 18, 1.2), strength=1.0, haze=0.12, shade_scale=1.8)
    sea = K.sea('fresh', repeat=8, color='#1e3a44')
    y = A.yacht('you', boom=0).place(0, 0, heading=0)
    P.anchor_chain(y, 0, length=9.0)
    # the reefed main: head 3.5 m down the mast, the reef's bunt along the boom
    K.sail_surface('main-reefed', Vector((-0.12, 0.0, 5.5 - K.WL)), Vector((-0.1, 0.0, 16.5 - K.WL)), Vector((-5.2, 0.0, 5.75 - K.WL)), 0.06, 1, twist=2, roach=0.04, parent=y.root)
    bunt = C.tube('reef-bunt', [y.world((K.MAST.x - 0.3, 0.13, 5.62)), y.world((K.MAST.x - 2.6, 0.13, 5.6)), y.world((K.MAST.x - 5.0, 0.13, 5.62))], 0.09, 16, 0.2, K.mats()['cloth'])
    yel = C.simple('jackstay', '#ffcc00', 0.5)
    for s in (1, -1):
        C.tube('jackstay', [y.world(p) for p in ((9.0, 0.13 + 0.55 * s, 3.62), (7.0, 0.13 + 1.35 * s, 3.56), (4.0, 0.13 + 1.95 * s, 3.56), (1.0, 0.13 + 2.0 * s, 3.56), (-2.0, 0.13 + 1.9 * s, 3.6), (-3.0, 0.13 + 1.7 * s, 3.65))],
               0.014, 8, 0.1, yel)
    crew = []
    for i, (mp, hd, col) in enumerate((((6.2, -1.25, 3.53), 20, '#c0392b'), ((2.6, -1.85, 3.53), 350, '#2c3e50'))):
        base = y.world(mp); h = P.person(base, hd, arms='down', top=col)
        A.torus(f'lifejacket{i}', 0.17, 0.06, C.simple('lj-red', '#d6331f', 0.5, coat=0.3), base + Vector((0, 0, 1.43)))
        tether = [base + Vector((0, 0, 1.2)), base + Vector((0.3, 0.2, 0.7)), y.world((mp[0] + 0.3, mp[1] - 0.45, 3.6))]
        C.tube(f'tether{i}', tether, 0.01, 8, 0.1, C.simple('tether', '#1f4fa0', 0.6)); crew.append(h)
    A.drone(y.world((3.0, 0.13, 7.0)), 23, az=118, el=26, lens=32)
    labels = [(tuple(y.world((K.MAST.x - 1.6, 0.13, 9.5))), 'reef in', 'blue'), (tuple(y.world((0.5, -2.0, 3.65))), 'jackstays rigged'),
              (tuple(crew[0] + Vector((0, 0, 0.35))), 'lifejackets and harnesses on', 'blue')]
    note = 'Before a blow, still at anchor'
    extra = {'lines': ['Washboards in, hatches dogged, loose gear stowed']}; expo = 0.4

elif FIG == 6:
    # the skipper standing at the wheel end of the cockpit, the crew of four seated round the table
    K.sea('calm', repeat=10); K.day_sky(sun_az=250, sun_el=30)
    KW.mole((-200, -60), (60, -60), width=10.0, height_=3.0)
    y = A.yacht('you').place(0, 0, heading=0)
    for i, (mp, hd, col, sit) in enumerate((((-1.0, 1.15, 3.14), 90, '#2c7a3e', True), ((0.0, 1.15, 3.14), 90, '#b33a2a', True),
                                            ((-1.0, -0.9, 3.14), 270, '#2c3e50', True), ((0.0, -0.9, 3.14), 270, '#c9a227', True),
                                            ((-2.3, 0.13, 3.14), 0, '#1f4fa0', False))):
        P.person(y.world(mp), hd + 0, arms=('side' if not sit else 'down'), top=col, sit=sit)
    lb = y.world((-3.55, -1.2, 4.2))
    A.torus('lifebuoy', 0.3, 0.06, C.simple('lifebuoy', '#f25a12', 0.5, coat=0.3), lb, rot=(deg(90), 0, deg(90)))
    lj = y.world((-0.5, 0.13, 3.95))
    for i in range(3):
        A.sphere(f'lj{i}', 0.12, C.simple('lj', '#d6331f', 0.5, coat=0.3), lj + Vector((0.05 * i, 0.12 * i - 0.12, 0.03 * i)), scale=(1.4, 1.0, 0.35))
    A.drone(y.world((-1.2, 0.13, 3.6)), 9.5, az=205, el=40, lens=30)
    labels = [(tuple(lj + Vector((0, 0, 0.25))), 'lifejackets: where, how, when', 'blue'), (tuple(lb + Vector((0, 0, 0.45))), 'man overboard gear', 'red'),
              (tuple(y.world((-3.75, 0.13, 3.3))), 'swimming: engine off, ladder down')]
    note = "Skipper's briefing"
    extra = {'lines': ['Below: gas valve, heads, extinguishers, ways out', 'Every crew member, the experienced ones too']}; expo = -0.4

C.render(OUT, SAMPLES, SCALE, expo, labels, note, space='blender', arrows=arrows, extra=extra)
