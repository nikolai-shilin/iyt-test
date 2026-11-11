# Props for q_encounter.py (Bareboat Skipper test questions, figure type "encounter"): the other vessels and things
# a skipper sees on the water, built on kit.py and the models in models/. Blender space: Z up, sea at z = 0,
# headings in compass degrees (0 = +Y north, clockwise). Each builder returns (root, visible meshes, top point).
# Copies (not edits) of a few helpers from the article scripts: vessel() from art_vhf_scenes.py, trawler() and
# ferry() from art_colregs_b.py, rock() and foam_patch() from art_colregs_b.py.
import os, math, random
import bpy, bmesh
from mathutils import Vector, Euler, Matrix
import common as C, kit as K
from common import node, link, setin, math_, ramp, mixc, lin, new_mat, obj_coords, noise, bump_from

def deg(a): return math.radians(a)
def fwd(h): return Vector((math.sin(deg(h)), math.cos(deg(h)), 0.0))
def right(h): return Vector((math.cos(deg(h)), -math.sin(deg(h)), 0.0))

def holder(name, pos, heading, z=0.0):
    """An empty at pos, turned so its local +X points along the compass heading."""
    e = bpy.data.objects.new(name, None); C.col.objects.link(e)
    e.location = (pos[0], pos[1], z); e.rotation_euler = (0, 0, deg(90 - heading))
    return e

def parent(objs, p):
    for o in objs:
        mw = o.matrix_world.copy(); o.parent = p; o.matrix_world = p.matrix_world @ mw if False else mw
    return objs

def top_of(vis):
    bpy.context.view_layer.update(); lo, hi = K.bbox(vis)
    return Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, hi.z))

# ---------- the Sun Odyssey: spinnaker leftovers off (as art_colregs_a.py), cheap clones ----------
def yacht(name, sails=None, boom=None):
    yt = K.load_yacht(name=name, sails=sails, boom=boom)
    for o in yt.objs:
        anc, q = [], o.parent
        while q: anc.append(q.name); q = q.parent
        if o.type == 'MESH' and (any(n.startswith('SPINNAKER') for n in anc) or
                                 any(sl.material and sl.material.name.startswith(('[Color_F12]', '[Color_H09]')) for sl in o.material_slots)):
            o.hide_render = True
    return yt

def clone_yacht(src, name, x, y, heading, heel=0.0):
    """A second yacht sharing the meshes of `src` (no re-import): copies the object tree under its root."""
    mp = {}
    def walk(o):
        c = o.copy(); C.col.objects.link(c); mp[o] = c
        for ch in o.children: walk(ch)
    walk(src.root)
    for o, c in mp.items():
        if o.parent in mp: c.parent = mp[o.parent]
    r = mp[src.root]; r.name = name
    y2 = K.Yacht(r, [mp[o] for o in src.objs if o in mp], mp.get(src.boom_pivot))
    return y2.place(x, y, heading=heading, heel=heel)

def sailing_yacht(name, hdg, wind, boom_sign, x, y, heel_k=1.0, genoa=True):
    """Under sail: the boom to the side the data gives (boom_sign +1 = starboard), its angle and the heel from the
    point of sail (wind = compass direction it blows from; None = a reach)."""
    if wind is None: off = 90.0
    else: off = abs(((wind - hdg + 540) % 360) - 180)
    ang = 12 if off < 60 else (30 if off < 100 else (50 if off < 140 else (68 if off < 165 else 80)))
    kb = -boom_sign * ang                                  # kit: + boom to port
    g = None
    if genoa and off < 165: g = 'starboard' if boom_sign > 0 else 'port'
    yt = yacht(name, sails={'main': True, 'genoa': g, 'boom': kb})
    heel = (12 if off < 60 else 8 if off < 100 else 4 if off < 140 else 0) * boom_sign * heel_k
    return yt.place(x, y, heading=hdg, heel=heel)

def motor_yacht_sun(name, hdg, x, y):
    return yacht(name).place(x, y, heading=hdg)

def yacht_top(yt, h=20.5):
    return yt.world((K.MAST.x, K.MAST.y, h + K.WL))

# ---------- third-party vessels ----------
def vessel(file, pos, heading, length, rule=None, flip=False, draft=0.8, hide=None):
    """(art_vhf_scenes.vessel) A 3D Warehouse vessel: water and ground slabs dropped, its long axis turned to the
    heading, scaled to `length` m, keel `draft` m under the water. flip: the model's bow points along -X."""
    root, objs = K.load_model(file, drop_planes=True)
    for o in objs:
        if o.type == 'MESH' and any(sl.material and ('Water' in sl.material.name or 'water' in sl.material.name) for sl in o.material_slots): o.hide_render = True
        if hide and o.type == 'MESH' and hide(o): o.hide_render = True
    bpy.context.view_layer.update()
    vis = [o for o in objs if o.type == 'MESH' and not o.hide_render]
    lo, hi = K.bbox(vis)
    along_y = (hi.y - lo.y) > (hi.x - lo.x)
    span = max(hi.x - lo.x, hi.y - lo.y); k = length / span
    hold = bpy.data.objects.new(file + '-at', None); C.col.objects.link(hold)
    root.parent = hold; root.location = (-(lo.x + hi.x) / 2, -(lo.y + hi.y) / 2, -lo.z)
    spin = bpy.data.objects.new(file + '-spin', None); C.col.objects.link(spin); hold.parent = spin
    hold.rotation_euler = (0, 0, deg(-90) if along_y else 0.0)
    spin.scale = (k,) * 3
    spin.location = (pos[0], pos[1], -draft)
    spin.rotation_euler = (0, 0, deg(90 - heading) + (math.pi if flip else 0.0))
    if rule: K.recolor(vis, rule)
    for o in vis:
        if not o.data.materials: o.data.materials.append(C.simple('vessel-grey', '#8a8f94', 0.5))
    bpy.context.view_layer.update()
    return spin, vis

def motor_yacht(pos, heading, length=12.0, hull='#1f2d4a'):
    """The 11 m motor yacht: white superstructure, a dark hull below the rubbing strake."""
    navy = C.simple('my-hull', hull, 0.3, coat=0.8)
    spin, vis = vessel('vessel-motor-yacht.glb', pos, heading, length, None, flip=True, draft=K.MOTOR_DRAFT * length)
    bpy.context.view_layer.update(); lo, hi = K.bbox(vis)
    for o in vis:   # the lower hull plating (big, low parts) navy
        l, h = K.bbox([o])
        if h.z < lo.z + 0.42 * (hi.z - lo.z) and (h - l).length > 0.3 * length:
            for sl in o.material_slots:
                c = K.base_color(sl.material)
                if c is not None and sum(c) / 3 > 0.6: sl.material = navy
    return spin, vis, top_of(vis)

def rib(pos, heading, length=5.0):
    spin, vis = vessel('tender-rib.glb', pos, heading, length, None, flip=RIB_FLIP, draft=K.RIB_DRAFT * length)
    grey = C.simple('rib-tube', '#3b4046', 0.55)
    for o in vis:
        for sl in o.material_slots:
            c = K.base_color(sl.material)
            if c is not None and sum(c) / 3 > 0.8: sl.material = grey
    return spin, vis, top_of(vis)
RIB_FLIP = True

WL_T = K.TRAWLER_WL  # the trawler model's waterline (model z)
YARD = (-1.45, 2.35, 8.25)   # the end of the trawler's crosstree, where her shapes hang (art_colregs_b)
def trawler(pos, heading, booms=True, scale=1.0):
    """(art_colregs_b.trawler) The UK trawler, navy and red, its sea slab dropped."""
    root, objs = K.load_model('vessel-trawler.glb', drop_planes=False)
    bpy.context.view_layer.update()
    meshes = [o for o in objs if o.type == 'MESH']
    lo, hi = K.bbox(meshes); foot = max(hi.x - lo.x, hi.y - lo.y)
    for o in meshes:
        l, h = K.bbox([o])
        if max(h.x - l.x, h.y - l.y) > 0.9 * foot and len(o.data.polygons) <= 40: o.hide_render = True
        elif not booms and (h.z - l.z) < 0.4 and max(h.x - l.x, h.y - l.y) > 8 and h.z < 1.0: o.hide_render = True
    M = K.mats(); red = C.simple('trawler-red', '#9b2a22', 0.45, coat=0.4)
    def rule(c, name):
        if c is None: return None
        l = sum(c) / 3
        if l < 0.2: return M['navy']
        if c[0] > 0.5 and c[1] < 0.3: return red
        return None
    K.recolor(objs, rule)
    root.scale = (scale,) * 3
    root.location = (pos[0], pos[1], -WL_T * scale)
    root.rotation_euler = Euler((0, 0, deg(90 - heading)), 'XYZ')
    bpy.context.view_layer.update()
    K.trawler_paint(objs, scale)                      # dark hull, red boot-top (her planking texture read pale)
    vis = [o for o in meshes if not o.hide_render]
    return root, vis, top_of(vis)

def ferry(pos, heading, length=60.0):
    """(art_colregs_b.ferry) The ferry model, its sea dropped, scaled to `length`."""
    root, objs = K.load_model('vessel-ferry.glb', drop_planes=False)
    bpy.context.view_layer.update()
    meshes = [o for o in objs if o.type == 'MESH']
    for o in meshes:
        l, h = K.bbox([o])
        if (h.y - l.y) > 60: o.hide_render = True
    vis = [o for o in meshes if not o.hide_render]
    lo, hi = K.bbox(vis)
    k = length / (hi.x - lo.x); root.scale = (k,) * 3
    bpy.context.view_layer.update(); lo, hi = K.bbox(vis)
    c = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, 0))
    root.location = Vector(root.location) - c
    piv = bpy.data.objects.new('ferry-pivot', None); C.col.objects.link(piv)
    root.parent = piv; piv.location = (pos[0], pos[1], -K.FERRY_WL * k); piv.rotation_euler = (0, 0, deg(90 - heading) + FERRY_TURN)
    bpy.context.view_layer.update()
    return piv, vis, top_of(vis)
FERRY_TURN = 0.0

def catamaran(pos, heading, length=12.8):
    """The 42 ft catamaran, its striped gennaker and the gennaker's lines dropped."""
    def hide(o):
        for sl in o.material_slots:
            m = sl.material
            if not m: continue
            c = K.base_color(m)
            if c is not None and c[0] > 0.5 and c[1] < 0.3 and c[2] < 0.3: return True     # the red stripes
        return False
    spin, vis = vessel('catamaran-42.glb', pos, heading, length, None, flip=CAT_FLIP, draft=0.6, hide=hide)
    # the gennaker's white panels: big thin parts forward of the mast, high up
    lo, hi = K.bbox(vis); H = hi.z - lo.z
    for o in vis:
        l, h = K.bbox([o])
        if (h.z - l.z) > 0.35 * H and l.z > lo.z + 0.12 * H and max(h.x - l.x, h.y - l.y) > 2.5 and len(o.data.polygons) > 50:
            o.hide_render = True
    vis = [o for o in vis if not o.hide_render]
    for o in vis:
        for sl in o.material_slots:
            c = K.base_color(sl.material)
            if c is not None and sum(c) / 3 > 0.85: sl.material = K.mats()['hull']
    return spin, vis, top_of(vis)
CAT_FLIP = False

# ---------- a merchant ship, built: hull, accommodation aft, masts, containers or tanker deck ----------
def _loft(name, sections, mat, cap0=True, cap1=False):
    """Quads between successive rings (each a list of 3D points, same count); caps the first ring."""
    verts, faces = [], []; n = len(sections[0])
    for s in sections: verts += [tuple(p) for p in s]
    for i in range(len(sections) - 1):
        for j in range(n - 1):
            a = i * n + j; faces.append((a, a + 1, a + n + 1, a + n))
    if cap0: faces.append(tuple(range(n - 1, -1, -1)))
    if cap1: k = (len(sections) - 1) * n; faces.append(tuple(range(k, k + n)))
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    me.shade_smooth(); me.set_sharp_from_angle(angle=deg(40))
    return C.obj(name, me, mat)

def ship_hull_mat(top='#2a2f36'):
    """Topsides above a red bottom, by world height (the ship floats at z = 0 and only turns about Z)."""
    m, nt, b, _ = new_mat('ship-hull-' + top)
    g = node(nt, 'ShaderNodeNewGeometry'); s = node(nt, 'ShaderNodeSeparateXYZ'); link(nt, g.outputs['Position'], s.inputs['Vector'])
    zz = math_(nt, 'MULTIPLY_ADD', s.outputs['Z'], 0.1, 0.5)
    c = ramp(nt, [(0.0, '#7a2a20'), (0.535, '#7a2a20'), (0.54, top), (1.0, top)], 'CONSTANT'); link(nt, zz, c.inputs['Fac'])
    st = ramp(nt, [(0.4, '#ffffff'), (0.8, '#b5b0a8')]); link(nt, noise(nt, obj_coords(nt), 0.4, 4.0), st.inputs['Fac'])
    link(nt, mixc(nt, 1.0, c.outputs['Color'], st.outputs['Color'], 'MULTIPLY'), b.inputs['Base Color'])
    setin(b, 'Roughness', 0.55)
    return m

def box(name, size, at, mat, rot=0.0, r=0.0):
    o = C.obj(name, C.rbox(name, size, r, 2), mat, Vector(at)); o.rotation_euler = (0, 0, rot); return o

def merchant(pos, heading, L=140.0, kind='container', two_masts=True):
    """A merchant ship L m long: kind 'container' (stacks of boxes), 'tanker' (low deck, pipes, a manifold) or
    'cargo' (a few boxes and two cranes). Accommodation and bridge aft, a funnel, a foremast and a radar mast,
    both on the centreline (so they line up seen bow-on). Returns (holder, meshes, top point)."""
    rnd = random.Random(7)
    Bm = L * 0.155; D = L * 0.075 if kind != 'tanker' else L * 0.06; dr = 3.0
    hull_top = {'container': '#1f3550', 'tanker': '#5b1d18', 'cargo': '#24282d'}[kind]
    hm = ship_hull_mat(hull_top)
    secs = []; N = 40
    for i in range(N + 1):
        t = i / N; x = -L / 2 + t * L
        if t < 0.06: hb = 0.82 + 0.18 * (t / 0.06)
        elif t < 0.66: hb = 1.0
        else: u = (t - 0.66) / 0.34; hb = max(0.015, math.cos(u * math.pi / 2) ** 0.85)
        hb *= Bm / 2
        sheer = D + (L * 0.022 * ((t - 0.75) / 0.25) ** 2 if t > 0.75 else 0.0)
        flare = 1.0 + (0.08 * ((t - 0.7) / 0.3) if t > 0.7 else 0.0)
        bot = hb * (0.75 if t > 0.1 else 0.55) * (0.3 if t > 0.93 else 1.0)
        ring = [(x, -hb * flare, sheer), (x, -hb, 0.0), (x, -bot, -dr), (x, bot, -dr), (x, hb, 0.0), (x, hb * flare, sheer)]
        secs.append([Vector(p) for p in ring])
    h = holder('ship', pos, heading)
    objs = [_loft('ship-hull', secs, hm, cap0=True)]
    # deck: a flat plate following the deck edge
    deck = C.simple('ship-deck', '#5f6b62' if kind != 'tanker' else '#6d3b2c', 0.8)
    dv = [Vector((s[0].x, s[0].y * 0.995, s[0].z - 0.05)) for s in secs] + [Vector((s[5].x, s[5].y * 0.995, s[5].z - 0.05)) for s in reversed(secs)]
    me = bpy.data.meshes.new('ship-deck'); me.from_pydata([tuple(v) for v in dv], [], [tuple(range(len(dv)))]); me.update()
    objs.append(C.obj('ship-deck', me, deck))
    white = C.simple('ship-white', '#d8dbd7', 0.5); dark = C.simple('ship-window', '#14181d', 0.15, coat=0.6)
    xa = -L / 2 + 0.03 * L; aw = 0.13 * L                          # accommodation block, aft
    hA = 0.10 * L; zA = D
    objs.append(box('accom', (aw, Bm * 0.86, hA), (xa + aw / 2, 0, zA + hA / 2), white))
    for k in range(3):   # window bands on each tier
        objs.append(box('win', (aw * 1.002, Bm * 0.862, 0.6), (xa + aw / 2, 0, zA + hA * (0.3 + 0.28 * k)), dark))
    zb = zA + hA; hb_ = 0.032 * L
    objs.append(box('bridge', (aw * 0.55, Bm * 1.0, hb_), (xa + aw * 0.72, 0, zb + hb_ / 2), white))
    objs.append(box('bridge-win', (aw * 0.552, Bm * 1.002, hb_ * 0.45), (xa + aw * 0.72, 0, zb + hb_ * 0.55), dark))
    fun = C.simple('funnel', '#b8322a', 0.5); blk = C.simple('funnel-top', '#16181b', 0.5)
    fx = xa + aw * 0.12; fh = 0.06 * L
    objs.append(box('funnel', (aw * 0.28, Bm * 0.3, fh), (fx, 0, zb + fh / 2), fun, r=0.6))
    objs.append(box('funnel-top', (aw * 0.285, Bm * 0.305, fh * 0.2), (fx, 0, zb + fh * 0.92), blk, r=0.3))
    mastm = C.simple('mast', '#e8e6df', 0.5)
    rm_h = 0.07 * L; rx = xa + aw * 0.72
    objs.append(C.cyl('radar-mast', 0.35, 0.3, rm_h, 12, mastm, (rx, 0, zb + hb_ + rm_h / 2)))
    objs.append(box('radar-yard', (0.5, Bm * 0.35, 0.4), (rx, 0, zb + hb_ + rm_h * 0.8), mastm))
    if two_masts:
        fmx = L / 2 - 0.09 * L; fm_h = 0.13 * L
        objs.append(C.cyl('foremast', 0.4, 0.3, fm_h, 12, mastm, (fmx, 0, D + L * 0.02 + fm_h / 2)))
        objs.append(box('fore-yard', (0.4, Bm * 0.25, 0.35), (fmx, 0, D + L * 0.02 + fm_h * 0.85), mastm))
    if kind in ('container', 'cargo'):
        cols = ['#a33a2a', '#2f5d8a', '#c9a227', '#4e7a4a', '#8b8f94', '#d26a2a', '#e2e2dc', '#6b3f7a', '#1f6f73']
        mats = [C.simple('box' + c, c, 0.6) for c in cols]
        bl, bw, bh = 12.2, 2.44, 2.6
        x0, x1 = xa + aw + 2.0, L / 2 - 0.17 * L
        nb = int((x1 - x0) // (bl + 0.6)); rows = int((Bm * 0.92) // bw); tiers = 4 if kind == 'container' else 2
        bms = {i: bmesh.new() for i in range(len(mats))}
        for bi in range(nb):
            if kind == 'cargo' and bi % 3 == 1: continue
            for r in range(rows):
                tt = tiers - (1 if rnd.random() < 0.3 else 0) - (1 if r in (0, rows - 1) else 0)
                for t in range(max(1, tt)):
                    mi = rnd.randrange(len(mats)); bm = bms[mi]
                    cx = x0 + bi * (bl + 0.6) + bl / 2; cy = (r - (rows - 1) / 2) * bw; cz = D + 0.3 + t * bh + bh / 2
                    g = bmesh.ops.create_cube(bm, size=1.0)
                    for v in g['verts']: v.co = Vector((v.co.x * bl + cx, v.co.y * (bw - 0.08) + cy, v.co.z * (bh - 0.06) + cz))
        for i, bm in bms.items():
            if not bm.verts: bm.free(); continue
            me = bpy.data.meshes.new('boxes'); bm.to_mesh(me); bm.free(); objs.append(C.obj('boxes', me, mats[i]))
        if kind == 'cargo':
            crane = C.simple('crane', '#d9a01c', 0.5)
            for cxk in (0.05, 0.3):
                cx = -L / 2 + L * (0.5 + cxk) * 0.75
                objs.append(C.cyl('crane-post', 0.9, 0.8, 12, 12, crane, (cx, Bm * 0.3, D + 6)))
                j = box('jib', (14, 0.7, 0.7), (cx + 5.5, Bm * 0.3, D + 13), crane); j.rotation_euler = (0, deg(-25), 0); objs.append(j)
    else:   # tanker: pipes along the deck, a manifold amidships, a catwalk
        pipe = C.simple('pipe', '#9aa29a', 0.5); grn = C.simple('manifold', '#3f6b4a', 0.5)
        x0, x1 = xa + aw, L / 2 - 0.1 * L
        for yy in (-2.0, -1.2, 0.0, 1.0):
            o = C.cyl('pipe', 0.35, 0.35, x1 - x0, 10, pipe, ((x0 + x1) / 2, yy, D + 0.8)); o.rotation_euler = (0, deg(90), 0); objs.append(o)
        objs.append(box('catwalk', (x1 - x0, 1.2, 0.3), ((x0 + x1) / 2, 2.5, D + 2.2), grn))
        objs.append(box('manifold', (6, Bm * 0.8, 2.4), (-L * 0.05, 0, D + 1.2), grn))
        for k in range(6):
            objs.append(C.cyl('dome', 1.2, 1.0, 1.2, 12, pipe, (x0 + 8 + k * (x1 - x0 - 16) / 5, -Bm * 0.28, D + 0.6)))
    for o in objs:
        o.location = Vector(o.location); mw = o.matrix_world.copy(); o.parent = h
    bpy.context.view_layer.update()
    return h, objs, top_of(objs)

# ---------- people ----------
SKIN = '#c58c6a'
def _limb(name, a, b, r, mat):
    a, b = Vector(a), Vector(b); d = b - a
    o = C.cyl(name, r, r * 0.85, d.length, 10, mat, tuple((a + b) / 2))
    o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = d.to_track_quat('Z', 'Y')
    C.obj(name + '-j', K._sphere(name + '-j', r), mat, tuple(b))
    return o

def person(base, heading, arms='down', top='#c0392b', legs='#2c3e50', sit=False, k=1.0):
    """A plain figure standing (or sitting) at `base` facing `heading`. arms: 'down', 'up' (raised out at 45°),
    'side' (out level), 'wave' (one up)."""
    f, r = fwd(heading), right(heading); up = Vector((0, 0, 1)); b = Vector(base)
    skin = C.simple('skin', SKIN, 0.6); shirt = C.simple('shirt-' + top, top, 0.8); trou = C.simple('trousers-' + legs, legs, 0.8)
    hip = b + up * (0.45 if sit else 0.92) * k
    if sit:
        for s in (-1, 1):
            knee = hip + f * 0.42 * k + r * s * 0.1 * k
            _limb('thigh', hip + r * s * 0.1 * k, knee, 0.075 * k, trou); _limb('shin', knee, knee - up * 0.42 * k + f * 0.05 * k, 0.06 * k, trou)
    else:
        for s in (-1, 1):
            _limb('leg', hip + r * s * 0.1 * k, b + r * s * 0.12 * k, 0.075 * k, trou)
    sh = hip + up * 0.55 * k
    C.obj('torso', K._sphere('torso', 0.2 * k), shirt, tuple(hip + up * 0.27 * k)).scale = (1.0, 0.8, 1.6)
    C.obj('head', K._sphere('head', 0.115 * k), skin, tuple(sh + up * 0.2 * k))
    for s in (-1, 1):
        a = sh + r * s * 0.2 * k
        if arms == 'down' or (arms == 'wave' and s < 0): e = a - up * 0.6 * k + r * s * 0.08 * k
        elif arms == 'side': e = a + r * s * 0.62 * k
        elif arms == 'up' or arms == 'wave': e = a + (r * s * 0.42 + up * 0.45) * k
        else: e = a - up * 0.6 * k
        _limb('arm', a, e, 0.055 * k, shirt)
    return sh + up * 0.4 * k

def in_water(at, kind='mob', heading=0.0, k=1.25):
    """A head in the water: 'mob' in a red-orange lifejacket, one arm up; 'swimmer' with a yellow cap."""
    p = Vector((at[0], at[1], 0.0)); f, r = fwd(heading), right(heading)
    skin = C.simple('skin', SKIN, 0.6)
    C.obj('head', K._sphere('head', 0.12 * k), skin, tuple(p + Vector((0, 0, 0.16 * k))))
    if kind == 'mob':
        jk = C.simple('lifejacket', '#ff4a12', 0.45, coat=0.3)
        bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=12, radius=0.3 * k)
        me = bpy.data.meshes.new('jacket'); bm.to_mesh(me); bm.free(); me.shade_smooth()
        o = C.obj('jacket', me, jk, tuple(p + Vector((0, 0, -0.04)))); o.scale = (1.0, 0.85, 0.42)
        sleeve = C.simple('sleeve', '#26354f', 0.8)
        sh, el_ = p + r * 0.22 * k + Vector((0, 0, 0.06)), p + r * 0.42 * k + Vector((0, 0, 0.3 * k))
        _limb('arm', sh, el_, 0.055 * k, sleeve); _limb('forearm', el_, el_ + r * 0.05 * k + Vector((0, 0, 0.3 * k)), 0.05 * k, sleeve)
        C.obj('hand', K._sphere('hand', 0.065 * k), skin, tuple(el_ + r * 0.05 * k + Vector((0, 0, 0.36 * k))))
    else:
        cap = C.simple('cap', '#ffd21a', 0.4)
        o = C.obj('cap', K._sphere('cap', 0.125 * k), cap, tuple(p + Vector((0, 0, 0.19 * k)))); o.scale = (1, 1, 0.75)
        C.obj('shoulders', K._sphere('shoulders', 0.22 * k), skin, tuple(p + Vector((0, 0, -0.05)))).scale = (1.0, 0.6, 0.3)
    ring_foam(p, 0.45 * k)
    return p + Vector((0, 0, 0.4 * k))

def ring_foam(p, r):
    """A little white water round something floating."""
    me = bpy.data.meshes.new('ring'); bm = bmesh.new(); bmesh.ops.create_circle(bm, cap_ends=True, segments=32, radius=r * 1.8); bm.to_mesh(me); bm.free()
    m, nt, b, out = new_mat('ring-foam')
    oc = obj_coords(nt); n = noise(nt, oc, 9.0, 6.0)
    sep = node(nt, 'ShaderNodeSeparateXYZ'); link(nt, oc, sep.inputs['Vector'])
    d = math_(nt, 'SQRT', math_(nt, 'ADD', math_(nt, 'MULTIPLY', sep.outputs['X'], sep.outputs['X']), math_(nt, 'MULTIPLY', sep.outputs['Y'], sep.outputs['Y'])))
    rr = math_(nt, 'SUBTRACT', 1.0, math_(nt, 'DIVIDE', d, r * 1.8))
    mask = math_(nt, 'MULTIPLY', math_(nt, 'GREATER_THAN', n, 0.5), math_(nt, 'MINIMUM', math_(nt, 'MULTIPLY', rr, 2.5), 0.8))
    setin(b, 'Base Color', lin('#eef2f2')); setin(b, 'Roughness', 0.8)
    tp = node(nt, 'ShaderNodeBsdfTransparent'); mx = node(nt, 'ShaderNodeMixShader')
    link(nt, mask, mx.inputs['Fac']); link(nt, tp.outputs[0], mx.inputs[1]); link(nt, b.outputs[0], mx.inputs[2]); link(nt, mx.outputs[0], out.inputs['Surface'])
    o = C.obj('ring-foam', me, m, tuple(p + Vector((0, 0, 0.05)))); o.visible_shadow = False

# ---------- small craft ----------
def windsurfer(pos, heading, sail_side=1, k=1.0):
    """A board, a raked mast and a bright sail sheeted to `sail_side` (+1 starboard), the sailor to windward."""
    p = Vector((pos[0], pos[1], 0.0)); f, r = fwd(heading), right(heading)
    h = holder('board', pos, heading)
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=10, radius=1.0)
    me = bpy.data.meshes.new('board'); bm.to_mesh(me); bm.free(); me.shade_smooth()
    o = C.obj('board', me, C.simple('board', '#f4f4f0', 0.3, coat=0.8), (p.x, p.y, 0.06)); o.scale = (1.3 * k, 0.33 * k, 0.07 * k); o.rotation_euler = (0, 0, deg(90 - heading))
    foot = p + f * 0.25 * k + Vector((0, 0, 0.12))
    rake = -f * 0.9 + Vector((0, 0, 4.4))                                   # mast raked aft
    head = foot + rake * k
    clew = foot + (-f * 2.2 + r * sail_side * 1.0 + Vector((0, 0, 1.35))) * k
    tack = foot + Vector((0, 0, 0.25)) * k
    smat = C.simple('ws-sail', '#ff6a1a', 0.5); smat2 = C.simple('ws-sail2', '#1d2f6b', 0.5)
    verts = [tuple(tack), tuple(head), tuple(clew), tuple(tack + (clew - tack) * 0.5 + Vector((0, 0, -0.35 * k)))]
    me = bpy.data.meshes.new('ws-sail'); me.from_pydata(verts, [], [(0, 3, 2, 1)]); me.update()
    so = C.obj('ws-sail', me, smat); s = so.modifiers.new('s', 'SOLIDIFY'); s.thickness = 0.01
    # a dark panel in the upper sail
    pv = [tuple(head + (tack - head) * 0.18), tuple(head + (tack - head) * 0.45), tuple(head + (clew - head) * 0.5), tuple(head + (clew - head) * 0.2)]
    me2 = bpy.data.meshes.new('ws-panel'); me2.from_pydata(pv, [], [(0, 1, 2, 3)]); me2.update()
    po = C.obj('ws-panel', me2, smat2); po.location = tuple(r * sail_side * 0.015)
    C.tube('ws-mast', [foot, head], 0.03 * k, 8, 1.0, C.simple('ws-mast', '#222222', 0.4))
    boom_a = foot + (rake * 0.33) * k; C.tube('ws-boom', [boom_a, clew], 0.025 * k, 8, 1.0, C.simple('ws-boom', '#333333', 0.4))
    stand = p - f * 0.35 * k - r * sail_side * 0.25 * k + Vector((0, 0, 0.1))
    person(stand, heading - 90 * sail_side * -1 if False else heading + 90 * sail_side, arms='side', top='#20242a', legs='#20242a', k=k)
    wake_decal((p.x, p.y), heading, 14 * k, 2.0 * k, stern=1.3 * k, strength=0.8)
    return h, [so, o], head + Vector((0, 0, 0.3))

def dinghy_with_person(pos, heading, arms='up'):
    spin, vis, top = rib(pos, heading, 3.6)
    bpy.context.view_layer.update(); lo, hi = K.bbox(vis)
    c = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z + 0.25 + 0.55))
    t = person(c, heading + 180, arms=arms, top='#2563a6', legs='#30343a', sit=True, k=1.15)
    return spin, vis, t + Vector((0, 0, 0.3))

def seaplane(pos, heading, k=1.0):
    """A single-engine floatplane: fuselage, high wing on struts, two floats, tail, propeller. White and red."""
    h = holder('seaplane', pos, heading)
    white = C.simple('sp-white', '#e9e9e4', 0.35, coat=0.6); red = C.simple('sp-red', '#c4161c', 0.35, coat=0.6)
    dark = C.simple('sp-dark', '#1a1d22', 0.3, coat=0.5); glass = K.mats()['glass']
    objs = []
    def ring(x, rad, z, sy=1.0, sz=1.0, n=16): return [Vector((x, math.cos(a) * rad * sy, z + math.sin(a) * rad * sz)) for a in [j / n * math.tau for j in range(n + 1)]]
    zf = 2.5
    prof = [(4.2, 0.05), (4.0, 0.45), (3.0, 0.62), (1.2, 0.68), (-0.5, 0.62), (-2.5, 0.38), (-4.6, 0.12)]
    secs = [ring(x, r, zf + (0.25 if x < -1 else 0.0) * (-x - 1) / 3.6 * (1 if x < -1 else 0), 0.85, 1.1) for x, r in prof]
    objs.append(_loft('fuselage', secs, white, cap0=True, cap1=True))
    objs.append(box('stripe', (6.5, 1.12, 0.12), (0.6, 0, zf - 0.15), red))
    objs.append(box('windows', (1.6, 1.08, 0.38), (2.0, 0, zf + 0.35), glass, r=0.08))
    objs.append(box('wing', (1.7, 13.0, 0.18), (1.4, 0, zf + 0.95), white, r=0.06))
    for s in (-1, 1): objs.append(box('wingtip', (1.71, 1.2, 0.19), (1.4, s * 6.0, zf + 0.95), red, r=0.06))
    objs.append(box('stab', (1.1, 4.0, 0.12), (-4.2, 0, zf + 0.25 + 0.25), white, r=0.04))
    fin = bpy.data.meshes.new('fin'); fin.from_pydata([(-3.6, 0, zf + 0.6), (-4.8, 0, zf + 0.6), (-4.9, 0, zf + 2.3), (-4.3, 0, zf + 2.3)], [], [(0, 1, 2, 3)]); fin.update()
    fo = C.obj('fin', fin, red); md = fo.modifiers.new('s', 'SOLIDIFY'); md.thickness = 0.12; objs.append(fo)
    for s in (-1, 1):
        fsec = []
        for x, r in [(3.4, 0.05), (3.1, 0.25), (2.0, 0.36), (0.0, 0.36), (-1.6, 0.3), (-3.0, 0.12)]:
            fsec.append(ring(x, r, 0.18, 1.0, 0.8))
        fl = _loft('float', [[Vector((p.x, p.y + s * 1.35, p.z)) for p in sec] for sec in fsec], white, cap0=True, cap1=True); objs.append(fl)
        for x in (1.6, -0.6):
            objs.append(C.tube('strut', [Vector((x, s * 1.35, 0.45)), Vector((x, s * 0.45, zf - 0.55))], 0.05, 8, 1.0, dark))
        objs.append(C.tube('wstrut', [Vector((1.4, s * 0.55, zf - 0.35)), Vector((1.4, s * 3.0, zf + 0.88))], 0.05, 8, 1.0, dark))
    objs.append(C.cyl('spinner', 0.18, 0.02, 0.35, 16, dark, (4.35, 0, zf))); objs[-1].rotation_euler = (0, deg(90), 0)
    pm = C.simple('prop-blur', '#30343a', 0.4)
    pd = C.cyl('prop', 1.0, 1.0, 0.02, 32, pm, (4.25, 0, zf)); pd.rotation_euler = (0, deg(90), 0); objs.append(pd)
    for o in objs: o.parent = h
    h.scale = (k,) * 3
    bpy.context.view_layer.update()
    for s in (-1, 1): wake_decal(tuple(Vector((pos[0], pos[1], 0.0)) + right(heading) * s * 1.35 * k), heading, 16 * k, 1.6 * k, stern=-3.0 * k, strength=0.6)
    return h, objs, top_of(objs)

# ---------- signals ----------
def flag(at, heading, w=1.2, h=1.0, png=None, color=None):
    """A flag flying from `at` (its hoist), streaming aft of `heading` (the way the wind blows it), a gentle wave."""
    f = fwd(heading); verts, faces, uvs = [], [], []; nu, nv = 10, 4
    for j in range(nv + 1):
        for i in range(nu + 1):
            u, v = i / nu, j / nv
            p = Vector(at) + f * (u * w) + Vector((0, 0, -v * h)) + right(heading) * (0.08 * math.sin(u * 5.0) * u)
            verts.append(tuple(p))
    for j in range(nv):
        for i in range(nu):
            a = j * (nu + 1) + i; faces.append((a, a + 1, a + nu + 2, a + nu + 1))
            uvs += [(i / nu, 1 - j / nv), ((i + 1) / nu, 1 - j / nv), ((i + 1) / nu, 1 - (j + 1) / nv), (i / nu, 1 - (j + 1) / nv)]
    me = bpy.data.meshes.new('flag'); me.from_pydata(verts, [], faces); me.update()
    lay = me.uv_layers.new(name='UVMap'); lay.data.foreach_set('uv', [c for uv in uvs for c in uv]); me.shade_smooth()
    m, nt, b, _ = new_mat('flag')
    if png:
        tx = node(nt, 'ShaderNodeTexImage'); tx.image = bpy.data.images.load(png)
        link(nt, node(nt, 'ShaderNodeUVMap').outputs['UV'], tx.inputs['Vector']); link(nt, tx.outputs['Color'], b.inputs['Base Color'])
    else: setin(b, 'Base Color', lin(color or '#ffffff'))
    setin(b, 'Roughness', 0.7)
    o = C.obj('flag', me, m); sd = o.modifiers.new('s', 'SOLIDIFY'); sd.thickness = 0.01
    return o

def red_flare(at, wind_to=0.0, k=1.0):
    """A red hand flare burning: a red core with a red glow round it, a red point light, a thin smoke plume rising
    and drifting downwind."""
    p = Vector(at)
    m, nt, b, out = new_mat('flare'); em = node(nt, 'ShaderNodeEmission'); setin(em, 'Color', (1.0, 0.03, 0.01, 1)); setin(em, 'Strength', 22.0)
    link(nt, em.outputs[0], out.inputs['Surface'])
    C.obj('flare', K._sphere('flare', 0.3 * k), m, tuple(p))
    gm, gnt, gb, gout = new_mat('flare-glow'); gnt.nodes.remove(gb)
    ge = gnt.nodes.new('ShaderNodeEmission'); ge.inputs['Color'].default_value = (1.0, 0.05, 0.02, 1); ge.inputs['Strength'].default_value = 3.0
    tp = gnt.nodes.new('ShaderNodeBsdfTransparent'); mx = gnt.nodes.new('ShaderNodeMixShader'); mx.inputs['Fac'].default_value = 0.35
    gnt.links.new(tp.outputs[0], mx.inputs[1]); gnt.links.new(ge.outputs[0], mx.inputs[2]); gnt.links.new(mx.outputs[0], gout.inputs['Surface'])
    C.obj('flare-glow', K._sphere('flare-glow', 0.75 * k), gm, tuple(p))
    ld = bpy.data.lights.new('flare-light', 'POINT'); ld.energy = 4000 * k; ld.color = (1.0, 0.1, 0.04); ld.shadow_soft_size = 0.2
    lo = bpy.data.objects.new('flare-light', ld); C.col.objects.link(lo); lo.location = p
    sm, snt, sb, sout = new_mat('flare-smoke'); snt.nodes.remove(sb)
    vs = snt.nodes.new('ShaderNodeVolumePrincipled'); vs.inputs['Density'].default_value = 0.35; vs.inputs['Color'].default_value = (0.9, 0.82, 0.82, 1)
    snt.links.new(vs.outputs[0], sout.inputs['Volume'])
    d = fwd(wind_to); rnd = random.Random(3)
    for i in range(8):
        q = p + Vector((0, 0, (0.8 + i * 0.45) * k)) + d * (i * i * 0.12) * k + Vector((rnd.uniform(-.15, .15), rnd.uniform(-.15, .15), 0))
        C.obj('smoke', K._sphere('smoke', (0.22 + i * 0.07) * k), sm, tuple(q))
    return p

def cb_cloud(center, r=2200.0, base=900.0, top=9000.0):
    """A thunderstorm cell on the horizon, as lumpy opaque cloud surfaces: a tower of displaced blobs, an anvil,
    a dark flat base and a grey rain shaft, faded into the haze with distance."""
    m, nt, b, out = new_mat('cb')
    g = node(nt, 'ShaderNodeNewGeometry'); sp = node(nt, 'ShaderNodeSeparateXYZ'); link(nt, g.outputs['Position'], sp.inputs['Vector'])
    zr = node(nt, 'ShaderNodeMapRange', in_From_Min=base, in_From_Max=base + (top - base) * 0.45); link(nt, sp.outputs['Z'], zr.inputs['Value'])
    col = ramp(nt, [(0.0, '#3a3f48'), (0.35, '#8d929a'), (1.0, '#f2f3f5')]); link(nt, zr.outputs['Result'], col.inputs['Fac'])
    link(nt, col.outputs['Color'], b.inputs['Base Color']); setin(b, 'Roughness', 1.0)
    setin(b, 'Subsurface Weight', 0.0)
    K.distance_fog(nt, b.outputs[0], out.inputs['Surface'], half=90000.0, color=(0.55, 0.62, 0.72), strength=0.6)
    tex = bpy.data.textures.new('cb-clouds', 'CLOUDS'); tex.noise_scale = 0.35; tex.noise_depth = 3
    c = Vector(center); rnd = random.Random(11); H = top - base
    def blob(name, at, sx, sy, sz, disp=0.35):
        bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=5, radius=1.0)
        me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); me.shade_smooth()
        o = C.obj(name, me, m, tuple(at)); o.scale = (sx, sy, sz)
        md = o.modifiers.new('d', 'DISPLACE'); md.texture = tex; md.strength = disp; md.mid_level = 0.5
        return o
    for i in range(9):   # the tower: lumps stacked up, narrowing
        z = base + H * (0.06 + 0.085 * i)
        rr = r * (1.0 - 0.045 * i)
        blob('cb-tower', c + Vector((rnd.uniform(-.25, .25) * r, rnd.uniform(-.25, .25) * r, z)), rr, rr * 0.95, H * 0.12)
    for k in range(6):   # cauliflower knobs round the sides
        a = rnd.uniform(0, math.tau); z = base + H * rnd.uniform(0.15, 0.7)
        blob('cb-knob', c + Vector((math.cos(a) * r * 0.85, math.sin(a) * r * 0.85, z)), r * 0.45, r * 0.45, r * 0.45)
    blob('cb-anvil', c + Vector((r * 1.2, 0, base + H * 0.93)), r * 3.4, r * 2.4, H * 0.07, 0.25)
    for k in range(7):   # a ragged dark base of low lumps
        a = k / 7 * math.tau; blob('cb-base', c + Vector((math.cos(a) * r * 0.7, math.sin(a) * r * 0.7, base + H * 0.05)), r * 0.6, r * 0.6, H * 0.05, 0.4)
    rm, rnt, rb, rout = new_mat('rain'); rnt.nodes.remove(rb)
    tp = rnt.nodes.new('ShaderNodeBsdfTransparent'); df = rnt.nodes.new('ShaderNodeBsdfDiffuse'); df.inputs['Color'].default_value = (0.25, 0.27, 0.31, 1)
    mx = rnt.nodes.new('ShaderNodeMixShader'); mx.inputs['Fac'].default_value = 0.28
    rnt.links.new(tp.outputs[0], mx.inputs[1]); rnt.links.new(df.outputs[0], mx.inputs[2]); rnt.links.new(mx.outputs[0], rout.inputs['Surface'])
    C.cyl('rain', r * 0.9, r * 1.2, base + 50, 32, rm, tuple(c + Vector((0, 0, base / 2 - 20))))
    return c + Vector((0, 0, top * 0.75))

# ---------- the water ----------
def wake_decal(pos, heading, length=30.0, width=6.0, stern=0.0, strength=1.0, z=0.22):
    """kit.wake's foam V for any vessel: its stern `stern` m behind `pos`, not parented."""
    me = bpy.data.meshes.new('wake'); L, Wd = length, width
    me.from_pydata([(-L, -Wd, 0), (0, -Wd, 0), (0, Wd, 0), (-L, Wd, 0)], [], [(0, 1, 2, 3)])
    me.uv_layers.new(name='UVMap'); me.uv_layers[0].data.foreach_set('uv', [0, 0, 1, 0, 1, 1, 0, 1])
    m, nt, b, out = new_mat('wake')
    uv = node(nt, 'ShaderNodeUVMap'); sep = node(nt, 'ShaderNodeSeparateXYZ'); link(nt, uv.outputs['UV'], sep.inputs['Vector'])
    u = math_(nt, 'SUBTRACT', 1.0, sep.outputs['X'])
    v = math_(nt, 'ABSOLUTE', math_(nt, 'SUBTRACT', math_(nt, 'MULTIPLY', sep.outputs['Y'], 2.0), 1.0))
    arm = math_(nt, 'ABSOLUTE', math_(nt, 'SUBTRACT', v, math_(nt, 'MULTIPLY', u, 0.36)))
    armm = math_(nt, 'MULTIPLY', math_(nt, 'LESS_THAN', arm, math_(nt, 'MULTIPLY_ADD', u, 0.06, 0.015)), math_(nt, 'SUBTRACT', 1.0, u))
    centre = math_(nt, 'MULTIPLY', math_(nt, 'LESS_THAN', v, math_(nt, 'MULTIPLY_ADD', u, 0.12, 0.04)), math_(nt, 'POWER', math_(nt, 'SUBTRACT', 1.0, u), 1.5))
    oc = obj_coords(nt); n1 = noise(nt, oc, 1.5, 8.0, 0.65)
    nr = ramp(nt, [(0.42, (0, 0, 0, 1)), (0.62, (1, 1, 1, 1))]); link(nt, n1, nr.inputs['Fac'])
    mask = math_(nt, 'MULTIPLY', math_(nt, 'MULTIPLY', math_(nt, 'MAXIMUM', armm, centre), nr.outputs['Color']), strength)
    setin(b, 'Base Color', lin('#eef3f4')); setin(b, 'Roughness', 0.8)
    tp = node(nt, 'ShaderNodeBsdfTransparent'); mx = node(nt, 'ShaderNodeMixShader')
    link(nt, mask, mx.inputs['Fac']); link(nt, tp.outputs[0], mx.inputs[1]); link(nt, b.outputs[0], mx.inputs[2]); link(nt, mx.outputs[0], out.inputs['Surface'])
    p = Vector((pos[0], pos[1], z)) - fwd(heading) * stern
    o = C.obj('wake', me, m, tuple(p)); o.rotation_euler = (0, 0, deg(90 - heading)); o.visible_shadow = False
    return o

def rock(name, p, size, seed):
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1.0)
    rnd = random.Random(seed)
    for v in bm.verts:
        n = v.co.normalized(); v.co = n * (1 + 0.25 * math.sin(n.x * 4 + seed) * math.cos(n.y * 3) + 0.12 * rnd.random())
        v.co = v.co * (1 + 0.3 * (rnd.random() - 0.5)); v.co.z *= 0.6
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); me.shade_smooth()
    m = C.simple('wet-rock', '#4d4840', 0.55)
    o = C.obj(name, me, m, Vector(p)); o.scale = (size, size * (0.7 + rnd.random() * 0.5), size); return o

def foam_patch(p, r, seed=1):
    """Breaking white water: a noise-masked white decal on the sea."""
    me = bpy.data.meshes.new('foam'); bm = bmesh.new(); bmesh.ops.create_circle(bm, cap_ends=True, segments=48, radius=r); bm.to_mesh(me); bm.free()
    m, nt, b, out = new_mat('foam%d' % seed)
    oc = obj_coords(nt); n = noise(nt, oc, 1.6, 8.0, 0.65)
    sep = node(nt, 'ShaderNodeSeparateXYZ'); link(nt, oc, sep.inputs['Vector'])
    rr = math_(nt, 'SUBTRACT', 1.0, math_(nt, 'DIVIDE', math_(nt, 'SQRT', math_(nt, 'ADD', math_(nt, 'MULTIPLY', sep.outputs['X'], sep.outputs['X']), math_(nt, 'MULTIPLY', sep.outputs['Y'], sep.outputs['Y']))), r))
    mask = math_(nt, 'MULTIPLY', math_(nt, 'GREATER_THAN', n, 0.4), math_(nt, 'POWER', math_(nt, 'MAXIMUM', rr, 0.0), 0.35))
    setin(b, 'Base Color', lin('#eef2f2')); setin(b, 'Roughness', 0.8)
    tp = node(nt, 'ShaderNodeBsdfTransparent'); mx = node(nt, 'ShaderNodeMixShader')
    link(nt, mask, mx.inputs['Fac']); link(nt, tp.outputs[0], mx.inputs[1]); link(nt, b.outputs[0], mx.inputs[2]); link(nt, mx.outputs[0], out.inputs['Surface'])
    o = C.obj('foam', me, m, Vector(p)); o.visible_shadow = False; return o

def shoal(center, along, length=120.0, width=30.0, seed=3, rocks=True):
    """Shallow water: a turquoise patch with breaking white water and a few rocks showing, `along` compass deg."""
    c = Vector((center[0], center[1], 0)); f = fwd(along); r = right(along); rnd = random.Random(seed)
    me = bpy.data.meshes.new('shoal'); bm = bmesh.new(); bmesh.ops.create_circle(bm, cap_ends=True, segments=48, radius=1.0); bm.to_mesh(me); bm.free()
    m, nt, b, out = new_mat('shoal-water')
    setin(b, 'Base Color', lin('#2f9e98')); setin(b, 'Roughness', 0.1)
    oc = obj_coords(nt); sep = node(nt, 'ShaderNodeSeparateXYZ'); link(nt, oc, sep.inputs['Vector'])
    d = math_(nt, 'SQRT', math_(nt, 'ADD', math_(nt, 'MULTIPLY', sep.outputs['X'], sep.outputs['X']), math_(nt, 'MULTIPLY', sep.outputs['Y'], sep.outputs['Y'])))
    a = math_(nt, 'MULTIPLY', math_(nt, 'SUBTRACT', 1.0, d), 1.6)
    tp = node(nt, 'ShaderNodeBsdfTransparent'); mx = node(nt, 'ShaderNodeMixShader')
    link(nt, math_(nt, 'MINIMUM', math_(nt, 'MAXIMUM', a, 0.0), 0.75), mx.inputs['Fac']); link(nt, tp.outputs[0], mx.inputs[1]); link(nt, b.outputs[0], mx.inputs[2]); link(nt, mx.outputs[0], out.inputs['Surface'])
    o = C.obj('shoal', me, m, tuple(c + Vector((0, 0, 0.4)))); o.scale = (width / 2, length / 2, 1); o.rotation_euler = (0, 0, deg(-along)); o.visible_shadow = False
    for i in range(int(length / 14)):
        q = c + f * rnd.uniform(-length / 2.4, length / 2.4) + r * rnd.uniform(-width / 4, width / 4)
        foam_patch((q.x, q.y, 0.5), rnd.uniform(3.0, 6.5), 50 + i)
        if rocks and rnd.random() < 0.7: rock('rock', (q.x, q.y, -0.2), rnd.uniform(1.0, 2.0), 60 + i)

def channel(axis_pt, along, half_width=40.0, n=4, spacing=60.0, start=-60.0, side_port_is_left=True):
    """A buoyed channel: red cans and green cones in two lines `along` (compass, the direction of buoyage),
    port hand marks on the left of that direction (IALA A)."""
    p0 = Vector((axis_pt[0], axis_pt[1], 0)); f, r = fwd(along), right(along)
    for i in range(n):
        q = p0 + f * (start + i * spacing)
        a = q - r * half_width; b = q + r * half_width
        K.lateral_buoy('port', topmark=True, light=False, at=(a.x, a.y), scale=1.0)
        K.lateral_buoy('starboard', topmark=True, light=False, at=(b.x, b.y), scale=1.0)

def anchor_chain(yt, heading, length=6.0):
    """(fig_drone anchored) The chain leaving the bow roller into the water ahead."""
    bow = yt.world((10.6, 0.13, 3.9)); f = fwd(heading)
    p1 = bow + f * length + Vector((0, 0, -bow.z - 0.2))
    C.tube('chain', [bow.lerp(p1, t / 10) + Vector((0, 0, -0.4 * math.sin(math.pi * t / 10))) for t in range(11)], 0.02, 8, 1.0, C.simple('chain', '#6b6e70', 0.5, 0.8))

def pontoon(p0, p1, width=2.4):
    p0, p1 = Vector((p0[0], p0[1], 0)), Vector((p1[0], p1[1], 0)); d = p1 - p0
    o = C.obj('pontoon', C.rbox('pontoon', (d.length, width, 0.6), 0.05, 2), C.planks_mat('pontoon-planks'), tuple((p0 + p1) / 2 + Vector((0, 0, 0.25))))
    o.rotation_euler = (0, 0, math.atan2(d.y, d.x)); return o
