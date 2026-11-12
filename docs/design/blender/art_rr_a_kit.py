# Blender side of the racing-rules figures for the articles course, definitions, limits, marks and obstructions
# (art_rr_<article>.py --fig <n> calls main()). The situation comes from art_rr_a_scenes.py, the same description the
# plan views (art_rr_a_plans.py) are drawn from, so boats, marks, zones, lines and obstructions sit exactly where the
# figure puts them: a high drone view from the south (north up the picture, the wind blowing down it), racing yachts
# on their tacks with the boom to leeward, an inflatable mark with its three-length zone as a faint ring on the water,
# the committee boat and pin of a line, the obstructions. The flag figures (course 5 and 7): the committee boat with
# her flags flying, close up from her side.
#   blender --background --factory-startup --python docs/design/blender/art_rr_marks.py -- --fig 2 [--samples 32 --scale 50]
import os, sys, math, random, subprocess, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy, bmesh
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
import common as C, kit as K
import q_encounter_props as P
import art_rr_a_scenes as S

ART = os.path.join(HERE, '..', 'figure-style', 'articles', 'racing-rules')
TEX = os.path.join(ART, 'course', 'tex')
COLS = {'blue': '#1384d6', 'red': '#d62828', None: '#f2f4f5', 'white': '#f2f4f5', 'yellow': '#f2c200'}
def deg(a): return math.radians(a)
def fwd(h): return Vector((math.sin(deg(h)), math.cos(deg(h)), 0.0))
def right(h): return Vector((math.cos(deg(h)), -math.sin(deg(h)), 0.0))
def W(x, y, z=0.0): wx, wy = S.world(x, y); return Vector((wx, wy, z))

# ---------- materials ----------
def alpha_mat(name, color, alpha, emit=0.0, rough=0.6):
    """A flat colour that lets the sea through (alpha), lit a little from within (emit) so it reads in shade."""
    m, nt, b, out = C.new_mat(name)
    tp = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader'); mx.inputs['Fac'].default_value = alpha
    b.inputs['Base Color'].default_value = C.lin(color); b.inputs['Roughness'].default_value = rough
    if emit: b.inputs['Emission Color'].default_value = C.lin(color); b.inputs['Emission Strength'].default_value = emit
    nt.links.new(tp.outputs[0], mx.inputs[1]); nt.links.new(b.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], out.inputs['Surface'])
    return m

def overlay(o):
    o.visible_shadow = False
    try: o.visible_glossy = False
    except Exception: pass
    return o

# ---------- yachts ----------
def race_yacht(name, x, y, hdg, you=False, sails=True, heel=None, wake=True):
    """The Sun Odyssey under main and genoa on the figure's tack: boom and genoa to leeward, heeled to leeward.
    (x, y) is the figure's boat origin, 2 m aft of the mast."""
    t, off = S.tack(hdg), S.off_wind(hdg); ang = S.boom_angle(hdg)
    kb = ang if t == 'starboard' else -ang                      # kit: + boom to port; starboard tack = boom to port
    genoa = None if off > 150 else ('port' if t == 'starboard' else 'starboard')
    yt = K.load_yacht(hull='navy' if you else 'white', name=name, sails={'main': True, 'genoa': genoa, 'boom': kb} if sails else None)
    for o in yt.objs:      # the spinnaker's leftovers (as q_encounter_props.yacht)
        anc, q = [], o.parent
        while q: anc.append(q.name); q = q.parent
        if o.type == 'MESH' and (any(n.startswith('SPINNAKER') for n in anc) or
                                 any(sl.material and sl.material.name.startswith(('[Color_F12]', '[Color_H09]')) for sl in o.material_slots)):
            o.hide_render = True
    if you:     # your boat: dark laminate sails, so she reads from the air
        dark = C.simple('laminate', '#2a2d33', 0.42, coat=0.4)
        for o in bpy.data.objects:
            if o.parent == yt.root and o.name.startswith(('main', 'genoa')) and o.type == 'MESH': o.data.materials[0] = dark
    if heel is None:
        hl = 3 if off < 40 else 12 if off < 60 else 8 if off < 100 else 4 if off < 140 else 0
        heel = hl if t == 'port' else -hl                        # kit: heel to starboard +; port tack heels to starboard
    p = W(x, y) + fwd(hdg) * 2.0
    yt.place(p.x, p.y, heading=hdg, heel=heel)
    if abs(heel) > 60: yt.root.location.z = 1.1      # capsized: she floats high on her side
    if wake and sails: K.wake(yt, 26, 6.5, 0.8)
    return yt

def mast_top(yt, h=19.0): return Vector(yt.world((K.MAST.x, K.MAST.y, h + K.WL)))

# ---------- marks, zone, lines, tracks ----------
def race_mark(x, y, color='#c44400', k=1.7, lean=6.0):
    """An inflatable racing mark: a fat cylinder with rounded ends, leaning a little downwind, a dark weighted foot."""
    p = W(x, y); mat = C.simple('mark-' + color, color, 0.62)
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=40, radius1=1.05 * k, radius2=1.05 * k, depth=2.4 * k)
    me = bpy.data.meshes.new('mark'); bm.to_mesh(me); bm.free()
    o = C.obj('mark', me, mat, tuple(p + Vector((0, 0, 0.9 * k))))
    bv = o.modifiers.new('round', 'BEVEL'); bv.width = 0.38 * k; bv.segments = 6; bv.limit_method = 'ANGLE'
    for f in me.polygons: f.use_smooth = True
    o.rotation_euler = (deg(-lean), 0, 0)          # its top leans south, downwind
    C.cyl('mark-foot', 1.0 * k, 1.0 * k, 0.35 * k, 40, C.simple('mark-foot', '#2a2d31', 0.6), tuple(p + Vector((0, 0, -0.2 * k))))
    return p + Vector((0, 0, 2.6 * k))

def dashes(pts, dash=3.0, gap=2.4, w=0.45, mat=None, z=0.24):
    """Dashes along a polyline of world points (x, y): flat strips floating on the water."""
    L = [0.0]
    for a, b in zip(pts, pts[1:]): L.append(L[-1] + (Vector(b) - Vector(a)).length)
    def at(s):
        for i in range(len(L) - 1):
            if L[i + 1] >= s:
                t = (s - L[i]) / max(1e-6, L[i + 1] - L[i]); return Vector(pts[i]).lerp(Vector(pts[i + 1]), t)
        return Vector(pts[-1])
    s = 0.0
    while s < L[-1]:
        a, b = at(s), at(min(L[-1], s + dash)); d = b - a
        if d.length > 0.05:
            c = (a + b) / 2; o = C.obj('dash', C.rbox('dash', (d.length, w, 0.06), 0.0, 1), mat, (c.x, c.y, z))
            o.rotation_euler = (0, 0, math.atan2(d.y, d.x)); overlay(o)
        s += dash + gap

def arrow_head(tip, direction, size=3.2, mat=None, z=0.26):
    d = Vector((direction[0], direction[1], 0.0)).normalized(); n = Vector((-d.y, d.x, 0)); tip = Vector((tip[0], tip[1], z))
    a, b = tip - d * size * 1.4 + n * size * 0.8, tip - d * size * 1.4 - n * size * 0.8
    me = bpy.data.meshes.new('head'); me.from_pydata([tuple(tip), tuple(a), tuple(b)], [], [(0, 1, 2)])
    overlay(C.obj('head', me, mat))

def fig_path(d, color, alpha=0.9, arrow=False, w=0.55, dash=3.4, gap=2.2):
    pts = [tuple(W(x, y)) [:2] for x, y in S.path_points(d)]
    mat = alpha_mat('path-' + color, color, alpha, emit=0.5)
    dashes(pts, dash, gap, w, mat)
    if arrow and len(pts) > 2: arrow_head(pts[-1], Vector(pts[-1]) - Vector(pts[-4]), 2.6, mat)
    return pts

def zone_ring(x, y, r_u=S.ZONE_U):
    """The three-length zone: a faint tinted disc and a dashed light ring on the water."""
    c = W(x, y); r = r_u * S.KM
    me = bpy.data.meshes.new('zone'); bm = bmesh.new(); bmesh.ops.create_circle(bm, cap_ends=True, segments=128, radius=r); bm.to_mesh(me); bm.free()
    overlay(C.obj('zone-disc', me, alpha_mat('zone-fill', '#8fd3ff', 0.025, emit=0.1), (c.x, c.y, 0.2)))
    n = 90; mat = alpha_mat('zone-ring', '#e8f6ff', 0.5, emit=0.4)
    for i in range(n):
        a0, a1 = math.tau * i / n, math.tau * (i + 0.55) / n
        dashes([(c.x + r * math.cos(a0), c.y + r * math.sin(a0)), (c.x + r * math.cos((a0 + a1) / 2), c.y + r * math.sin((a0 + a1) / 2)), (c.x + r * math.cos(a1), c.y + r * math.sin(a1))], 99, 0, 0.4, mat, 0.25)
    return c + Vector((0, r, 0.4))

# ---------- flags, the committee boat, the RIB ----------
def flag_png(code):
    p = os.path.join(TEX, f'flag-{code}.png')
    if not os.path.exists(p): subprocess.run(['python3', os.path.join(HERE, 'art_rr_a_flags.py')], check=True)
    return p

def flag(at, stream, w, h, code):
    """A flag flying from its hoist at `at`, streaming towards compass `stream`, a gentle wave; the texture's alpha
    cuts the swallowtail."""
    f = fwd(stream); verts, faces, uvs = [], [], []; nu, nv = 14, 6
    for j in range(nv + 1):
        for i in range(nu + 1):
            u, v = i / nu, j / nv
            verts.append(tuple(Vector(at) + f * (u * w) + Vector((0, 0, -v * h)) + right(stream) * (0.09 * w * math.sin(u * 5.5) * u) + Vector((0, 0, -0.04 * w * u * u))))
    for j in range(nv):
        for i in range(nu):
            a = j * (nu + 1) + i; faces.append((a, a + 1, a + nu + 2, a + nu + 1))
            uvs += [(i / nu, 1 - j / nv), ((i + 1) / nu, 1 - j / nv), ((i + 1) / nu, 1 - (j + 1) / nv), (i / nu, 1 - (j + 1) / nv)]
    me = bpy.data.meshes.new('flag'); me.from_pydata(verts, [], faces); me.update()
    lay = me.uv_layers.new(name='UVMap'); lay.data.foreach_set('uv', [c for uv in uvs for c in uv])
    for p in me.polygons: p.use_smooth = True
    m, nt, b, out = C.new_mat('flag-' + code)
    tx = nt.nodes.new('ShaderNodeTexImage'); tx.image = bpy.data.images.load(flag_png(code))
    nt.links.new(nt.nodes.new('ShaderNodeUVMap').outputs['UV'], tx.inputs['Vector'])
    nt.links.new(tx.outputs['Color'], b.inputs['Base Color']); nt.links.new(tx.outputs['Alpha'], b.inputs['Alpha'])
    b.inputs['Roughness'].default_value = 0.75; b.inputs['Sheen Weight'].default_value = 0.4
    try: b.inputs['Subsurface Weight'].default_value = 0.0
    except Exception: pass
    o = C.obj('flag-' + code, me, m); sd = o.modifiers.new('s', 'SOLIDIFY'); sd.thickness = 0.008
    return o

STAFF = None
def staff(base, top, r=0.035):
    global STAFF
    STAFF = STAFF or C.simple('staff', '#d9dcdf', 0.3, 0.7)
    C.tube('staff', [Vector(base), Vector(top)], r, 8, 1.0, STAFF)
    C.obj('truck', K._sphere('truck', r * 1.6), STAFF, tuple(Vector(top) + Vector((0, 0, r))))

def hoist(top, codes, w=1.5, h=1.0, stream=180.0):
    """Flags one under the other on a staff whose top is `top`; returns the top."""
    z = 0.0
    for c in codes:
        flag(Vector(top) + Vector((0, 0, -0.08 - z)), stream, w, h, c); z += h + 0.18
    return Vector(top)

def committee_boat(x, y, hdg=0.0, flags=(), L=12.0, staffs=None, fw=1.5):
    """The committee boat (the 11 m motor yacht at 12 m), lying head to wind, a flagstaff on her flybridge with the
    line flag(s). staffs: several hoists along her centreline (the flag figures)."""
    p = W(x, y); root, vis, top = P.motor_yacht((p.x, p.y), hdg + 180, L)
    bpy.context.view_layer.update(); lo, hi = K.bbox(vis)
    tops = []
    hoists = staffs if staffs else ([list(flags)] if flags else [])
    n = len(hoists)
    for i, codes in enumerate(hoists):
        along = (3.0 - i * 2.45) if staffs else -1.2
        base = p + fwd(hdg) * along; base.z = hi.z - 0.6
        tp = Vector((base.x, base.y, hi.z + (1.4 + (len(codes)) * 1.05 * fw / 1.5 if staffs else 3.2)))
        staff(base, tp); hoist(tp, codes, fw if staffs else 2.4, (fw if staffs else 2.4) * 2 / 3); tops.append(tp)
    return Vector((p.x, p.y, hi.z)), tops

def rib_with_flag(x, y, hdg, code, L=7.0):
    p = W(x, y); root, vis, top = P.rib((p.x, p.y), hdg, L)
    base = p - fwd(hdg) * 1.2; base.z = 0.6; tp = base + Vector((0, 0, 3.0))
    staff(base, tp); hoist(tp, [code], 1.6, 1.07)
    return tp

# ---------- obstructions ----------
def extrude(name, poly, z0, z1, mat):
    """A prism over a polygon of world points."""
    bm = bmesh.new(); vs = [bm.verts.new((x, y, z0)) for x, y in poly]; f = bm.faces.new(vs)
    bmesh.ops.extrude_face_region(bm, geom=[f]); top = [v for v in bm.verts if v.co.z == z0 and v not in vs]
    for v in top: v.co.z = z1
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    return C.obj(name, me, mat)

def push_out(pts):
    """Polygon corners on the figure's frame (x 0 or 320, y 0 or 200) pushed far out, so a pier or wall runs on
    beyond the picture."""
    out = []
    for x, y in pts:
        X, Y = x, y
        if x <= 0: X = -400
        if x >= 320: X = 720
        if y <= 0: Y = -400
        if y >= 200: Y = 600
        out.append((X, Y))
    return out

def stone_mat(name, base, dark):
    m, nt, b, _ = C.new_mat(name)
    oc = C.obj_coords(nt)
    c = C.ramp(nt, [(0.3, dark), (0.7, base)]); C.link(nt, C.noise(nt, oc, 0.8, 6.0), c.inputs['Fac'])
    sep = nt.nodes.new('ShaderNodeSeparateXYZ'); C.link(nt, oc, sep.inputs['Vector'])
    wet = C.math_(nt, 'LESS_THAN', sep.outputs['Z'], 0.6)
    col = C.mixc(nt, C.math_(nt, 'MULTIPLY', wet, 0.7), c.outputs['Color'], C.lin('#3b3a35'))
    C.link(nt, col, b.inputs['Base Color']); C.setin(b, 'Roughness', 0.9)
    C.bump_from(nt, b, C.noise(nt, oc, 3.0, 5.0), 0.5, 0.05)
    return m

def quay_like(kind, ob):
    """Pier, sea wall or quay from the figure's rect or path: a stone or concrete block standing out of the water,
    bollards along the edge, running on past the frame; land behind."""
    if 'path' in ob:
        pts = [(float(a), float(b)) for a, b in zip(*[iter([t for t in ob['path'].replace('M', ' ').replace('L', ' ').replace('Z', ' ').split()])] * 2)]
    else:
        x, y, w, h = ob['x'], ob['y'], ob['w'], ob['h']; pts = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
    edge = pts
    pts = push_out(pts)
    poly = [tuple(W(x, y))[:2] for x, y in pts]
    if kind == 'wall':
        mat = stone_mat('wall-stone', '#6f6a60', '#4f4b44'); z1 = 3.4
    else:
        mat = stone_mat('quay-stone', '#7b776f', '#5c5952'); z1 = 2.0
    o = extrude(kind, poly, -3.0, z1, mat)
    # a coping along the top edge and bollards on the water side (the edges inside the frame)
    dark = C.simple('bollard', '#26282b', 0.5, 0.3)
    for (ax, ay), (bx, by) in zip(edge, edge[1:] + edge[:1]):
        inside = not ((ax <= 0 and bx <= 0) or (ax >= 320 and bx >= 320) or (ay <= 0 and by <= 0) or (ay >= 200 and by >= 200))
        if not inside: continue
        a, b = W(ax, ay), W(bx, by); L = (b - a).length; n = int(L / 14)
        nrm = Vector((-(b - a).y, (b - a).x, 0)).normalized()
        for i in range(1, n):
            q = a.lerp(b, i / n)
            for s in (1, -1):
                qq = q + nrm * s * 0.9
                if inside_poly(poly, qq.x, qq.y): C.cyl('bollard', 0.25, 0.3, 0.6, 16, dark, (qq.x, qq.y, z1 + 0.3)); break
    return o

def inside_poly(q, px, py):
    c = False
    for i in range(len(q)):
        (xi, yi), (xj, yj) = q[i], q[i - 1]
        if (yi > py) != (yj > py) and px < (xj - xi) * (py - yi) / (yj - yi) + xi: c = not c
    return c

def shore(ob):
    """The shore of definitions 7: land west of the figure's x + w, a sand beach sloping into the water, scrub
    behind, a few rocks at the waterline."""
    xe = W(ob['x'] + ob['w'], 0).x
    prof = [(xe + 6, -1.5), (xe, 0.35), (xe - 8, 1.3), (xe - 22, 2.6), (xe - 60, 4.5), (xe - 400, 9.0)]
    bm = bmesh.new(); Y0, Y1 = -500, 500; rows = []
    for X, Z in prof: rows.append((bm.verts.new((X, Y0, Z)), bm.verts.new((X, Y1, Z))))
    for (a0, a1), (b0, b1) in zip(rows, rows[1:]): bm.faces.new((a0, a1, b1, b0))
    bmesh.ops.subdivide_edges(bm, edges=[e for e in bm.edges if abs(e.verts[0].co.y - e.verts[1].co.y) > 1], cuts=80)
    me = bpy.data.meshes.new('shore'); bm.to_mesh(me); bm.free()
    m, nt, b, _ = C.new_mat('shore')
    oc = C.obj_coords(nt); sep = nt.nodes.new('ShaderNodeSeparateXYZ'); C.link(nt, oc, sep.inputs['Vector'])
    veg = C.ramp(nt, [(0.35, '#7d7a5c'), (0.55, '#6f7a54'), (0.75, '#4f5d3f')]); C.link(nt, C.noise(nt, oc, 0.15, 6.0), veg.inputs['Fac'])
    sand = C.ramp(nt, [(0.3, '#8c7f5f'), (0.7, '#9a8c69')]); C.link(nt, C.noise(nt, oc, 1.5, 4.0), sand.inputs['Fac'])
    beach = C.math_(nt, 'LESS_THAN', sep.outputs['Z'], 1.15)
    C.link(nt, C.mixc(nt, beach, veg.outputs['Color'], sand.outputs['Color']), b.inputs['Base Color']); C.setin(b, 'Roughness', 0.95)
    C.bump_from(nt, b, C.noise(nt, oc, 2.0, 6.0), 0.4, 0.1)
    o = C.obj('shore', me, m)
    rnd = random.Random(4)
    for i in range(14):
        P.rock('rock', (xe + rnd.uniform(-2, 2), rnd.uniform(-150, 150), 0.0), rnd.uniform(1.0, 2.6), i)
    # scrub: dark bushes on the slope
    bush = C.simple('bush', '#46552f', 0.9)
    for i in range(700):
        X = xe - rnd.uniform(12, 160); Y = rnd.uniform(-200, 200); r = rnd.uniform(0.7, 1.9)
        z = 2.6 + (4.5 - 2.6) * min(1, (xe - 22 - X) / 38) if X < xe - 22 else 2.6
        C.obj('bush', K._sphere('bush', r), bush, (X, Y, z)).scale = (1, 1, 0.6)
    return o

def land_behind(y_edge_u):
    """Low land north of a pier or wall, and hills beyond."""
    yn = W(0, y_edge_u).y
    K.coast(distance=yn + 160, bearing=0, length=3000, height=50, town=True)

# ---------- camera ----------
def frame(points, az=180.0, el=58.0, lens=35.0, fill=(0.84, 0.70), lift=0.06):
    """A drone camera on compass bearing az from the scene, el degrees up, framed round the points: they fill
    `fill` of the frame's width / height, nudged down by `lift` (room for the note pill)."""
    pts = [Vector(p) for p in points]
    c = sum(pts, Vector()) / len(pts); c.z = 0.0
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), 0)); hi = Vector((max(p.x for p in pts), max(p.y for p in pts), 0))
    c = (lo + hi) / 2
    D = max(hi.x - lo.x, hi.y - lo.y) * 1.4 + 40
    a, e = deg(az), deg(el)
    sc = bpy.context.scene; sc.render.resolution_x, sc.render.resolution_y = C.W, C.H
    cam = None
    for it in range(8):
        eye = c + Vector((math.sin(a) * math.cos(e), math.cos(a) * math.cos(e), math.sin(e))) * D
        if cam is None: cam = K.camera(tuple(eye), tuple(c), lens)
        else:
            cam.location = eye; cam.rotation_euler = (c - eye).to_track_quat('-Z', 'Y').to_euler()
        bpy.context.view_layer.update()
        q = [world_to_camera_view(sc, cam, p) for p in pts]
        xs, ys = [v.x for v in q], [v.y for v in q]
        sx = (max(xs) - min(xs)) / fill[0]; sy = (max(ys) - min(ys)) / fill[1]
        mx, my = (max(xs) + min(xs)) / 2 - 0.5, (max(ys) + min(ys)) / 2 - (0.5 - lift)
        # recentre on the ground: screen x is the camera's right, screen y its up projected on the ground
        M3 = cam.matrix_world.to_3x3(); rgt = M3 @ Vector((1, 0, 0)); rgt.z = 0; rgt.normalize()
        up = M3 @ Vector((0, 1, 0)); up.z = 0; up.normalize()
        span_w = 2 * D * math.tan(math.atan(18 / lens)); span_h = span_w * C.H / C.W / math.sin(e)
        c = c + rgt * mx * span_w + up * my * span_h
        D *= max(sx, sy) ** 0.85
        if os.environ.get('RR_DEBUG'): print('FRAME', it, round(min(xs), 3), round(max(xs), 3), round(min(ys), 3), round(max(ys), 3), round(D, 1))
    return cam

def ground_at(cam, u, v, z=6.0):
    """The point at height z seen at frame position (u, v) (0..1, v up)."""
    sc = bpy.context.scene; fr = cam.data.view_frame(scene=sc)   # top-right, bottom-right, bottom-left, top-left
    tr, br, bl, tl = [cam.matrix_world @ p for p in fr]
    p = bl + (br - bl) * u + (tl - bl) * v; o = cam.matrix_world.translation; d = (p - o).normalized()
    t = (z - o.z) / d.z; return o + d * t

def declutter(labels, cam):
    """Move pills that would cover another pill, the note or the frame edge: up, aside or below their anchor, on
    a leader line (label.py draws it). Pills are measured as label.py draws them (Arial Bold 30 px)."""
    sc = bpy.context.scene; placed = [(28, 20, 640, 82)]
    labels = sorted(labels, key=lambda l: l[1] != 'Wind')     # the wind's pill first, fixed on its arrow
    def px(p): q = world_to_camera_view(sc, cam, Vector(p)); return q.x * C.W, (1 - q.y) * C.H
    out = []
    anchors = [px(l[0]) for l in labels]
    for i, l in enumerate(labels):
        x, y = anchors[i]; w = max(len(l[1]), len(RU.get(l[1], ''))) * 16.8 + 34; h = 52   # room for the Russian too
        def rect(dx, dy):
            cx = max(w / 2 + 12, min(C.W - w / 2 - 12, x + dx)); py = y + dy - 4 - h - 18
            return (cx - w / 2, py, cx + w / 2, py + h)
        if l[1] == 'Wind':
            placed.append(rect(0, 0)); out.append(l); continue
        if len(l) > 3 and l[3]:
            placed.append(rect(*l[3])); out.append(l); continue
        cands = [(0, 0), (w / 2 + 30, 0), (-w / 2 - 30, 0), (0, -48), (w / 2 + 40, -40), (-w / 2 - 40, -40), (0, 96), (w / 2 + 40, 80), (-w / 2 - 40, 80), (0, -100), (0, 150)]
        best, bc = None, 1e18
        for k, (dx, dy) in enumerate(cands):
            r = rect(dx, dy); c = k * 300 + (5e5 if r[1] < 8 or r[3] > C.H - 8 else 0)
            for t in range(1, 10):     # the leader must not cross another pill
                qx, qy = x + dx * t / 10, y + (dy - 7) * t / 10
                if any(o[0] < qx < o[2] and o[1] < qy < o[3] for o in placed[1:]): c += 3000
            for o in placed: c += max(0, min(r[2], o[2]) - max(r[0], o[0])) * max(0, min(r[3], o[3]) - max(r[1], o[1])) * 10
            for j, (ax, ay) in enumerate(anchors):
                if j != i and r[0] - 6 < ax < r[2] + 6 and r[1] - 6 < ay < r[3] + 6: c += 4000
            if c < bc: best, bc = (dx, dy), c
        placed.append(rect(*best))
        col = l[2] if len(l) > 2 else None
        out.append((l[0], l[1], col, best) if best != (0, 0) else ((l[0], l[1], col) if col else (l[0], l[1])))
    return out

def wind_arrow(labels, arrows, at, L=22.0):
    p0 = Vector((at[0], at[1], 6.0)); p1 = p0 - Vector((0, L, 0))
    arrows.append((tuple(p0), tuple(p1), 'blue')); labels.append((tuple(p0 + Vector((0, 0, 1))), 'Wind', 'blue'))

# ---------- a race figure ----------
def build_race(article, n, a):
    sp = S.spec(article, n); fig = sp['fig']; labels, arrows, fitp = [], [], []
    K.day_sky(sun_az=a.get('sun', 215), sun_el=48)
    def lab(p, text, color=None, off=None):
        if not text: return
        t = (tuple(p), text, color) if color else (tuple(p), text)
        if off: t = (tuple(p), text, color, off)
        labels.append(t)
    offs = sp.get('offs3d', {})
    # obstruction first (the sea is laid round the scene afterwards)
    ob = fig.get('obstruction'); kind = sp.get('kind')
    if ob and kind in ('pier', 'wall', 'quay'):
        quay_like(kind, ob); land_behind(-60)
        if 'path' in ob: lp = W(ob.get('lx', 260), ob.get('ly', 45), 2.5)
        else: lp = W(ob['x'] + ob['w'] / 2, ob['y'] + ob['h'] * 0.75, 3.0)
        lab(lp, sp.get('obstruction'), None, offs.get('obstruction'))
        if 'path' in ob:
            tk = ob['path'].replace('M', ' ').replace('L', ' ').replace('Z', ' ').split(); q = [(float(a_), float(b_)) for a_, b_ in zip(tk[::2], tk[1::2])]
        else: q = [(ob['x'], ob['y']), (ob['x'] + ob['w'], ob['y'] + ob['h']), (ob['x'], ob['y'] + ob['h']), (ob['x'] + ob['w'], ob['y'])]
        if 'path' not in ob: q = [q[0], q[3], q[1], q[2]]
        fitp += [W(*S.near_on(q, b['x'], b['y'])) for b in sp['boats']]
        if 'lx' in ob: fitp.append(W(ob['lx'], ob['ly']))
    elif ob and kind == 'shore':
        shore(ob); lp = W(ob['x'] + ob['w'] - 8, 120, 2.0); lab(lp, sp.get('obstruction'), None, offs.get('obstruction')); fitp.append(W(ob['x'] + ob['w'] - 18, 100))
    elif ob and kind == 'moored':
        c = W(ob['x'] + ob['w'] / 2, ob['y'] + ob['h'] / 2)
        root, vis, top = P.motor_yacht((c.x, c.y), 90 + 180, ob['w'] * S.KM, hull='#1f2d4a')
        lab(top + Vector((0, 0, 1)), sp.get('obstruction'), None, offs.get('obstruction'))
        fitp += [W(ob['x'], ob['y']), W(ob['x'] + ob['w'], ob['y'] + ob['h'])]
    elif ob:    # course 8: the RIB showing M, at the middle of the figure's box
        tp = rib_with_flag(ob['x'] + ob['w'] / 2, ob['y'] + ob['h'] / 2, 0, 'M')
        lab(tp + Vector((0, 0, 0.6)), sp.get('rib'), 'red' if False else None, offs.get('obstruction')); fitp.append(tp)
    # boats
    yts = []
    for i, b in enumerate(sp['boats']):
        cap = sp.get('capsized') == i
        yt = race_yacht(f'boat{i}', b['x'], b['y'], b['hdg'], you=b.get('you', False), sails=not cap, heel=95 if cap else None)
        yts.append(yt)
        name, col = sp['names'][i] if i < len(sp['names']) else (None, None)
        top = mast_top(yt) if not cap else Vector(yt.world((K.MAST.x, K.MAST.y, 3.0 + K.WL))) + Vector((0, 0, 2.5))
        if cap:
            for k, (dx, dy) in enumerate(((-2.5, -3.5), (1.5, -4.2))):
                q = W(b['x'], b['y']) + Vector((dx, dy, 0)); P.in_water((q.x, q.y), 'mob', heading=0, k=1.2)
        lab(top, name, col, offs.get(i))
        if cap: fitp += [W(b['x'], b['y']) + right(b['hdg']) * 20]
        fitp += [W(b['x'], b['y']) + fwd(b['hdg']) * 10, W(b['x'], b['y']) - fwd(b['hdg']) * 9, top]
    # mark and zone
    m = fig.get('mark')
    if m:
        tp = race_mark(m['x'], m['y'])
        lab(tp + Vector((0, 0, 0.5)), sp.get('mark', m.get('label')), None, offs.get('mark')); fitp.append(tp)
        if m.get('zone'):
            zt = zone_ring(m['x'], m['y'])
            if sp.get('zone_label'): lab(zt, sp['zone_label'], 'blue', offs.get('zone'))
            r = S.ZONE_U * S.KM; c = W(m['x'], m['y']); fitp += [c + Vector((r, 0, 0)), c - Vector((r, 0, 0)), c + Vector((0, r, 0)), c - Vector((0, r, 0))]
    if sp.get('gate'):
        gx, gy, gl = sp['gate']; tp = race_mark(gx, gy); lab(tp + Vector((0, 0, 0.5)), gl, None, offs.get('gate')); fitp.append(tp)
        dashes([tuple(W(gx, gy))[:2], tuple(W(m['x'], m['y']))[:2]], 2.0, 2.0, 0.3, alpha_mat('gate', '#f4f6f7', 0.55, 0.4))
    # the line: pin and committee boat
    ln = fig.get('line')
    if ln:
        pin = race_mark(ln['x1'], ln['y1'], '#c44400', 1.1) if not m or (ln['x1'], ln['y1']) != (m['x'], m['y']) else None
        top, tops = committee_boat(ln['x2'], ln['y2'], ln.get('hdg', 0), sp.get('rc_flags', []))
        lab(tops[0] + Vector((0, 0, 0.3)) if tops else top, sp.get('rc'), None, offs.get('rc'))
        if pin is not None: lab(pin + Vector((0, 0, 0.4)), 'pin', None, offs.get('pin'))
        a_, b_ = W(ln['x1'], ln['y1']), W(ln['x2'], ln['y2'])
        dashes([tuple(a_.lerp(b_, 0.012))[:2], tuple(a_.lerp(b_, 0.97))[:2]], 2.2, 2.2, 0.32, alpha_mat('line', '#f4f6f7', 0.6, 0.4))
        if sp.get('line'): lab(a_.lerp(b_, sp.get('line_at', 0.5)) + Vector((0, 0, 0.5)), sp['line'], None, offs.get('line'))
        fitp += [a_, b_ + Vector((0, 0, 6))]
    # the figure's track, and our own extra courses
    if fig.get('track'):
        if sp.get('line_abeam'):
            pts = fig_path(fig['track'], '#f4f6f7', 0.7, w=0.4, dash=2.2, gap=2.0)
            q = S.path_points(fig['track']); lab(W(*q[len(q) // 5], 0.5), sp['line_abeam'], None, offs.get('track'))
        else:
            pts = fig_path(fig['track'], '#f2c200', 0.9)
        if sp.get('track_fit', True): fitp += [Vector((p[0], p[1], 0)) for p in pts[::6]]
    for d, col, arr in sp.get('paths', []):
        pts = fig_path(d, COLS[col], 0.9, arr); fitp += [Vector((p[0], p[1], 0)) for p in pts[::6]]
    for x, y, text, col in sp.get('pts', []):
        lab(W(x, y, 0.5), text, col, offs.get(text)); fitp.append(W(x, y))
    fitp += [Vector(p) for p in sp.get('fit3d', [])]
    # sea centred on the scene
    lo = Vector((min(p.x for p in fitp), min(p.y for p in fitp), 0)); hi = Vector((max(p.x for p in fitp), max(p.y for p in fitp), 0))
    c = (lo + hi) / 2
    K.sea(wind=6.0, wave_scale=0.2, chop=1.1, size=36.0, repeat=int(max(hi.x - lo.x, hi.y - lo.y) * 2.2 / 36) + 4, center=(c.x, c.y))
    cam = frame(fitp, az=sp.get('az', a.get('az', 180.0)), el=sp.get('el', a.get('el', 52.0)), lens=35.0, fill=sp.get('fill', (0.78, 0.60)))
    # wind: an arrow in the top right of the frame (north-east of the scene)
    wa = sp.get('wind3d')
    if wa: wa = W(*wa)
    elif sp.get('wind_uv'): wa = ground_at(cam, *sp['wind_uv'])
    else:     # the free corner: farthest from everything shown and labelled
        sc = bpy.context.scene
        busy = [world_to_camera_view(sc, cam, Vector(p)) for p in fitp] + [world_to_camera_view(sc, cam, Vector(l[0])) for l in labels]
        best, bd = None, -1
        for u, v in ((0.93, 0.80), (0.07, 0.74), (0.93, 0.56), (0.07, 0.52), (0.5, 0.80)):
            d = min(math.hypot((q.x - u) * 1.6, q.y - (v - 0.06)) for q in busy)
            if d > bd + 0.04: best, bd = (u, v), d
        wa = ground_at(cam, *best)
    if not sp.get('wind3d'):    # a steady size on screen: the arrow's tail a seventh of the frame below its head
        u, v = sp.get('wind_uv') or best; wb = ground_at(cam, u, v - 0.14)
        arrows.append((tuple(wa), tuple(wb), 'blue')); labels.append((tuple(wa + Vector((0, 0, 1))), 'Wind', 'blue'))
    else: wind_arrow(labels, arrows, wa, 22 if not sp.get('wind_len') else sp['wind_len'])
    return declutter(labels, cam), arrows, sp['note']

# ---------- a flag figure ----------
def build_flags(article, n, a):
    F = S.FLAG_FIGS[(article, n)]; labels = []
    K.day_sky(sun_az=230, sun_el=40)
    K.sea(wind=6.0, wave_scale=0.18, chop=1.0, size=30.0, repeat=10, center=(0, 0))
    top, tops = committee_boat(160, 100, 0, staffs=F['hoists'], fw=1.6)
    pts = []
    for tp, codes in zip(tops, F['hoists']):
        pts += [tp + Vector((0, 0, 0.4)), tp + Vector((0, -1.7, -len(codes) * 1.25)), tp - Vector((0, 0, 2.6))]
    pts += [Vector((top.x, top.y + 6.5, 1.0)), Vector((top.x, top.y - 6.5, 1.0))]
    zt = max(tp.z for tp in tops); my = sum(tp.y for tp in tops) / len(tops) - 0.8; cx = top.x
    D = 17.0 if len(tops) > 2 else 13.0; vis_h = 2 * D * (18 / 40) * C.H / C.W
    look = Vector((cx, my, zt - (0.5 - 0.2) * vis_h)); eye = Vector((cx - D, my - 1.5, look.z + 0.6))
    cam = K.camera(tuple(eye), tuple(look), 40); bpy.context.view_layer.update(); sc = bpy.context.scene
    # each name on a pill in the open water below, one row each, on a leader from the foot of its hoist
    for i, (tp, codes, text) in enumerate(zip(tops, F['hoists'], F['labels'])):
        foot = tp + Vector((0.0, -0.75, -0.08 - len(codes) * 1.07 - 0.15 * (len(codes) - 1)))
        q = world_to_camera_view(sc, cam, foot); ax, ay = q.x * C.W, (1 - q.y) * C.H
        row = C.H * (0.66 + 0.09 * i)
        labels.append((tuple(foot), text, None, (0.0, row - ay)))
    # a racing yacht beyond, for the scene
    race_yacht('beyond', 230, 40, 315, sails=True)
    return labels, [], F['note']

RU = {}
def main(article):
    global RU
    try: RU = json.load(open(os.path.join(ART, article, 'ru.json')))
    except Exception: RU = {}
    arg = C.cli(); FIG = arg('--fig', 1); SAMPLES = arg('--samples', 144); SCALE = arg('--scale', 100)
    OUT = arg('--out', os.path.join(ART, article, f'{FIG}-3d.jpg'))
    a = {'az': arg('--az', 180.0), 'el': arg('--el', 52.0)}
    C.reset(); K.mats()
    if (article, FIG) in S.FLAG_FIGS: labels, arrows, note = build_flags(article, FIG, a)
    else: labels, arrows, note = build_race(article, FIG, a)
    C.render(OUT, SAMPLES, SCALE, -0.55, labels, note, space='blender', arrows=arrows)
