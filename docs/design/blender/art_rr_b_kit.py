# Shared helpers for the Racing Rules article figures (penalties, propulsion, protests, rightofway, starting):
# today's race figure (FIG.race in docs/design/figures.js: a 320 x 200 top view, north up, the wind from `wind`,
# boats at x, y with a heading, the sail to leeward) rebuilt in Blender: racing yachts at the figure's positions,
# headings and tacks, inflatable marks with their zone, the start line between the committee boat and the pin,
# tracks as foam on the water, and the signal flags (drawn by art_rr_b_tex.py) on a committee boat or a backstay.
# Blender space: Z up, sea at z = 0, X east, Y north, headings in compass degrees.
# The figure's units become metres at S: a yacht there is 26.4 units long, here the 14.6 m Sun Odyssey.
import os, sys, math, json, subprocess, random
import bpy, bmesh
from mathutils import Vector, Quaternion
from bpy_extras.object_utils import world_to_camera_view
import common as C, kit as K
import q_encounter_props as P

HERE = os.path.dirname(os.path.abspath(__file__))
ARTS = os.path.join(HERE, '..', 'figure-style', 'articles', 'racing-rules')
S = 14.6 / 26.4                    # metres per figure unit
SCALE = 100                        # render size, per cent (a script's --scale)
MAST_FWD = 1.1                     # the mast stands this far forward of the middle of the hull
def deg(a): return math.radians(a)
def fwd(h): return Vector((math.sin(deg(h)), math.cos(deg(h)), 0.0))
def right(h): return Vector((math.cos(deg(h)), -math.sin(deg(h)), 0.0))
def W(x, y, z=0.0): return Vector(((x - 160) * S, -(y - 100) * S, z))

# topsides by the boat's name in the figure (her label), the rest dark blue as the model came
HULL = {'Grey': '#80878e', 'Blue': '#1f5fb8', 'Red': '#b01c1c', 'Yellow': '#e2b100', 'Green': '#1d7a3e', 'A': '#26303b',
        'starboard': '#1f5fb8', 'port': '#b01c1c', 'windward': '#1f5fb8', 'leeward': '#b01c1c', 'tacking': '#1f5fb8'}

def tex_path(art, name): return os.path.join(ARTS, art, 'tex', name + '.png')

def need_tex(art, names):
    """Draw the textures with the system Python (Pillow) when one is missing."""
    if any(not os.path.exists(tex_path(art, n)) for n in names):
        subprocess.run(['python3', os.path.join(HERE, 'art_rr_b_tex.py'), art, *names], check=True)

# ---------------------------------------------------------------- yachts
def load(name, colour=None, sails=None):
    """The Sun Odyssey (kit.load_yacht) with her topsides in `colour`, the spinnaker leftovers hidden."""
    M = K.mats()
    if colour:
        old = M['navy']; M['navy'] = C.simple('topsides-' + name, colour, 0.28, coat=1.0)
        yt = K.load_yacht(hull='navy', name=name, sails=sails); M['navy'] = old
    else:
        yt = K.load_yacht(name=name, sails=sails)
    for o in yt.objs:
        anc, q = [], o.parent
        while q: anc.append(q.name); q = q.parent
        if o.type == 'MESH' and (any(n.startswith('SPINNAKER') for n in anc) or
                                 any(sl.material and sl.material.name.startswith(('[Color_F12]', '[Color_H09]')) for sl in o.material_slots)):
            o.hide_render = True
    return yt

def trim(hdg, wind=0.0):
    """Boom side (+1 starboard), boom angle, genoa side and heel for a heading in this wind, as FIG.race reads the
    tack: the wind over the port side (0 < hdg - wind < 180) puts the boom to starboard."""
    rel = (hdg - wind) % 360; side = 1 if rel < 180 else -1
    off = abs(((wind - hdg + 540) % 360) - 180)
    if off < 30: return side, 4, None, 0          # head to wind: sails flapping on the centreline
    ang = 12 if off < 60 else 30 if off < 100 else 50 if off < 140 else 68 if off < 165 else 80
    heel = (9 if off < 60 else 6 if off < 100 else 3 if off < 140 else 0) * side
    g = ('starboard' if side > 0 else 'port') if off < 150 else None
    return side, ang, g, heel

def boat(b, wind=0.0, boom=None, heel=None, genoa=True, name=None):
    """A figure boat {x, y, hdg, label, you}: hull centre at (x, y). boom: (side, angle) to override the trim."""
    h = b.get('hdg', 0); side, ang, g, hl = trim(h, wind)
    if boom: side, ang = boom; g = ('starboard' if side > 0 else 'port') if g else None
    if not genoa: g = None
    colour = None if b.get('you') else HULL.get(b.get('label'), '#1d2c4f')
    yt = load(name or ('you' if b.get('you') else 'b-' + str(b.get('label'))), colour, {'main': True, 'genoa': g, 'boom': -side * ang})
    c = W(b['x'], b['y']) + fwd(h) * MAST_FWD
    yt.place(c.x, c.y, heading=h, heel=hl if heel is None else heel)
    yt.hdg = h; yt.centre = W(b['x'], b['y'])
    return yt

def top(yt, h=19.5): return yt.world((K.MAST.x, K.MAST.y, h + K.WL))
def bow(yt): return yt.centre + fwd(yt.hdg) * 7.4
def stern(yt): return yt.centre - fwd(yt.hdg) * 7.2

def wake(yt, length=34, width=8, strength=0.9): return K.wake(yt, length, width, strength)

# ---------------------------------------------------------------- marks, the line, the committee boat
def mark(x, y, colour='#ffa400', r=1.0, h=2.3):
    """An inflatable racing mark: a fat cylinder with rounded shoulders, a dark weighted foot, its line taut below."""
    p = W(x, y); m = C.simple('mark-skin', colour, 0.45, coat=0.4)
    prof = [(0, h), (r * 0.6, h), (r * 0.9, h - 0.08), (r, h - 0.3), (r, 0.25), (r * 0.94, 0.05), (r * 0.8, -0.2), (0, -0.2)]
    o = C.lathe('mark', [(a, b) for a, b in prof], 48, m); o.location = p
    C.cyl('mark-band', r * 1.01, r * 1.01, 0.18, 48, C.simple('mark-band', '#f2f2ee', 0.5), p + Vector((0, 0, h * 0.62)))
    C.cyl('mark-handle', 0.05, 0.05, 0.4, 12, C.simple('mark-handle', '#202224', 0.5), p + Vector((0, 0, h + 0.15)))
    P.ring_foam(Vector((p.x, p.y, 0)), r * 1.25)
    return p + Vector((0, 0, h))

def _alpha_mat(name, rgb, alpha, rough=0.6, emit=0.0):
    m, nt, b, out = C.new_mat(name)
    b.inputs['Base Color'].default_value = C.lin(rgb); b.inputs['Roughness'].default_value = rough
    if emit: b.inputs['Emission Color'].default_value = C.lin(rgb); b.inputs['Emission Strength'].default_value = emit
    tp = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader'); mx.inputs['Fac'].default_value = alpha
    nt.links.new(tp.outputs[0], mx.inputs[1]); nt.links.new(b.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], out.inputs['Surface'])
    return m

def polygon(name, pts, rgb, alpha, z=0.3):
    """A flat tinted area on the water (a zone, the triangle, a sector)."""
    me = bpy.data.meshes.new(name); me.from_pydata([(p[0], p[1], z) for p in pts], [], [tuple(range(len(pts)))])
    o = C.obj(name, me, _alpha_mat(name, rgb, alpha, emit=0.15)); o.visible_shadow = False; return o

def ribbon(name, pts, w, mat, z=0.32):
    """A strip `w` m wide along `pts` on the water, its UV u running 0 to 1 along it."""
    pts = [Vector((p[0], p[1], z)) for p in pts]; L = [0.0]
    for a, b in zip(pts, pts[1:]): L.append(L[-1] + (b - a).length)
    vs, fs, uv = [], [], []
    for i, p in enumerate(pts):
        d = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]); d.z = 0; d.normalize(); n = Vector((-d.y, d.x, 0))
        vs += [p + n * w / 2, p - n * w / 2]
    for i in range(len(pts) - 1): fs.append((2 * i, 2 * i + 1, 2 * i + 3, 2 * i + 2))
    me = bpy.data.meshes.new(name); me.from_pydata([tuple(v) for v in vs], [], fs); lay = me.uv_layers.new(name='UVMap')
    for f in me.polygons:
        for li, vi in zip(f.loop_indices, f.vertices): lay.data[li].uv = (L[vi // 2] / L[-1], vi % 2)
    o = C.obj(name, me, mat); o.visible_shadow = False; return o

def dashes(name, pts, dash=3.0, gap=2.4, w=0.45, rgb='#f4f6f6', alpha=0.85, z=0.34):
    """A dashed line on the water along a polyline."""
    m = _alpha_mat(name, rgb, alpha, 0.5, emit=0.25)
    pts = [Vector((p[0], p[1], z)) for p in pts]
    for a, b in zip(pts, pts[1:]):
        d = b - a; L = d.length; u = d / L; n = 0
        while n * (dash + gap) < L:
            s0 = n * (dash + gap); s1 = min(L, s0 + dash); c = a + u * ((s0 + s1) / 2)
            o = C.obj(name, C.rbox(name, (s1 - s0, w, 0.04), 0.0, 1), m, tuple(c)); o.rotation_euler = (0, 0, math.atan2(u.y, u.x)); o.visible_shadow = False; n += 1

def zone(x, y, r_units=None, lengths=3):
    """The zone round a mark: a faint ring of dashes and a pale tint inside it. r in figure units, or 3 lengths."""
    R = r_units * S if r_units else lengths * 14.6; c = W(x, y); n = 72
    ring = [(c.x + R * math.cos(t / n * math.tau), c.y + R * math.sin(t / n * math.tau)) for t in range(n + 1)]
    me = bpy.data.meshes.new('zone-fill'); me.from_pydata([(p[0], p[1], 0.28) for p in ring[:-1]], [], [tuple(range(n))])
    zo = C.obj('zone-fill', me, _alpha_mat('zone-fill', '#3f9be0', 0.10)); zo.visible_shadow = False
    dashes('zone-ring', ring, 2.6, 2.2, 0.5, '#dff1ff', 0.9)
    return R

def foam_mat(name, strength=0.85):
    """A turned-up foam track: noisy white, fading towards its start (u = 0, the oldest water)."""
    m, nt, b, out = C.new_mat(name)
    uv = nt.nodes.new('ShaderNodeUVMap'); sep = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(uv.outputs['UV'], sep.inputs['Vector'])
    v = C.math_(nt, 'ABSOLUTE', C.math_(nt, 'SUBTRACT', C.math_(nt, 'MULTIPLY', sep.outputs['Y'], 2.0), 1.0))
    edge = C.math_(nt, 'SUBTRACT', 1.0, C.math_(nt, 'POWER', v, 2.5))
    age = C.math_(nt, 'MULTIPLY_ADD', sep.outputs['X'], 0.7, 0.3)
    n1 = C.noise(nt, C.obj_coords(nt), 1.6, 8.0, 0.7); nr = C.ramp(nt, [(0.38, (0.08, 0.08, 0.08, 1)), (0.66, (1, 1, 1, 1))]); C.link(nt, n1, nr.inputs['Fac'])
    mask = C.math_(nt, 'MULTIPLY', C.math_(nt, 'MULTIPLY', edge, age), C.math_(nt, 'MULTIPLY', nr.outputs['Color'], strength))
    b.inputs['Base Color'].default_value = C.lin('#eef3f4'); b.inputs['Roughness'].default_value = 0.8
    tp = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader')
    C.link(nt, mask, mx.inputs['Fac']); nt.links.new(tp.outputs[0], mx.inputs[1]); nt.links.new(b.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], out.inputs['Surface'])
    return m

def svg_path(d, step=1.5):
    """Points (figure units) along an SVG path of M, L and C commands (absolute)."""
    toks = d.replace(',', ' ').replace('M', ' M ').replace('L', ' L ').replace('C', ' C ').split()
    pts, i, cmd, cur = [], 0, None, None
    while i < len(toks):
        if toks[i] in 'MLC': cmd = toks[i]; i += 1; continue
        if cmd == 'M': cur = (float(toks[i]), float(toks[i + 1])); pts.append(cur); i += 2; cmd = 'L'
        elif cmd == 'L':
            nxt = (float(toks[i]), float(toks[i + 1])); i += 2
            L = math.dist(cur, nxt); k = max(1, int(L / step))
            pts += [(cur[0] + (nxt[0] - cur[0]) * t / k, cur[1] + (nxt[1] - cur[1]) * t / k) for t in range(1, k + 1)]; cur = nxt
        elif cmd == 'C':
            c1 = (float(toks[i]), float(toks[i + 1])); c2 = (float(toks[i + 2]), float(toks[i + 3])); e = (float(toks[i + 4]), float(toks[i + 5])); i += 6
            k = 40
            for t in range(1, k + 1):
                t /= k; a = (1 - t) ** 3; b_ = 3 * (1 - t) ** 2 * t; c = 3 * (1 - t) * t * t; dd = t ** 3
                pts.append((a * cur[0] + b_ * c1[0] + c * c2[0] + dd * e[0], a * cur[1] + b_ * c1[1] + c * c2[1] + dd * e[1]))
            cur = e
    return pts

def track(d, w=3.2, strength=0.85, trim_end=0.0, split=None):
    """A figure track as a foam trail on the water. trim_end: metres left off its end (under the boat).
    split: a world point (the boat) where the wake ends: the rest of the track, still to sail, is a dashed course."""
    pts = [W(*p) for p in svg_path(d)]
    if split is not None:
        i = min(range(len(pts)), key=lambda k: (pts[k] - split).length)
        ahead = pts[i:]; pts = pts[:i + 1]
        if len(ahead) > 1:
            q = ahead[0]; keep = [q] + [p for p in ahead[1:] if (p - q).length > 9.0]
            if len(keep) > 1: dashes('course', [p.xy for p in keep], 2.6, 2.0, 0.55, '#ffd21a', 0.95)
    if trim_end:
        while len(pts) > 2 and (pts[-1] - pts[-2]).length < trim_end: trim_end -= (pts[-1] - pts[-2]).length; pts.pop()
    return ribbon('track', [(p.x, p.y) for p in pts], w, foam_mat('track-foam', strength))

def committee_boat(x, y, hdg=0.0, L=14.0, colour='#e9ecee'):
    """The committee boat, at anchor head to wind: the 11 m motor yacht scaled to L, a white hull. Returns
    (root, vis, top, deck) where deck is the height of her aft deck."""
    root, vis, tp = P.motor_yacht(tuple(W(x, y).xy), hdg + 180, L, hull=colour)
    lo, hi = K.bbox(vis)
    return root, vis, tp, lo.z + 0.42 * (hi.z - lo.z)

def pin(x, y):
    """The pin end: a small orange inflatable with a staff and an orange flag."""
    p = W(x, y); m = C.simple('pin-skin', '#ff6a00', 0.45, coat=0.4)
    o = C.lathe('pin', [(0, 1.3), (0.45, 1.3), (0.6, 1.1), (0.6, 0.2), (0.5, -0.2), (0, -0.2)], 40, m); o.location = p
    C.cyl('pin-staff', 0.03, 0.03, 2.2, 8, C.simple('staff', '#d8d8d4', 0.4), p + Vector((0, 0, 2.3)))
    flag_plain('pin-flag', p + Vector((0, 0, 3.35)), 180, 0.75, 0.5, '#ff7a00')
    P.ring_foam(Vector((p.x, p.y, 0)), 0.8)
    return p + Vector((0, 0, 3.4))

def start_line(l, hdg=0.0, cb=True, pin_end=True, dash=True):
    """The line from the pin (x1, y1) to the committee boat (x2, y2): dashes on the water, the boat, the pin."""
    a, b = W(l['x1'], l['y1']), W(l['x2'], l['y2'])
    out = {}
    if dash: dashes('line', [a.xy, (b - (b - a).normalized() * 3).xy], 3.0, 2.6, 0.5, '#f8f8f4', 0.9)
    if cb: out['cb'] = committee_boat(l['x2'], l['y2'], hdg)
    if pin_end: out['pin'] = pin(l['x1'], l['y1'])
    return out

# ---------------------------------------------------------------- flags
def flag_mesh(name, hoist, stream, w, h, tex=None, colour=None, wave=0.07, seed=0, up=Vector((0, 0, 1))):
    """A flag `w` long, `h` deep, its hoist edge running down from `hoist` along -up, flying along `stream`
    (a unit vector), gently waving. tex: an RGBA png (its alpha cuts the shape: swallowtail, pennant)."""
    stream = Vector(stream).normalized(); side = stream.cross(up).normalized(); nu, nv = 24, 10
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap'); V = []
    for j in range(nv + 1):
        v = j / nv
        for i in range(nu + 1):
            u = i / nu
            p = Vector(hoist) - up * (v * h) + stream * (u * w * (1 - 0.04 * u)) + side * (wave * w * u ** 1.2 * math.sin(2 * math.pi * 1.1 * u + seed + 0.6 * v)) - up * (0.05 * h * u * u)
            V.append((bm.verts.new(p), (u, 1 - v)))
    for j in range(nv):
        for i in range(nu):
            a = j * (nu + 1) + i; q = (V[a], V[a + 1], V[a + nu + 2], V[a + nu + 1])
            f = bm.faces.new([t[0] for t in q]); f.smooth = True
            for lp, t in zip(f.loops, q): lp[uvl].uv = t[1]
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    m, nt, b, out = C.new_mat(name)
    b.inputs['Roughness'].default_value = 0.75
    if tex:
        tx = nt.nodes.new('ShaderNodeTexImage'); tx.image = bpy.data.images.load(tex); tx.interpolation = 'Cubic'
        nt.links.new(nt.nodes.new('ShaderNodeUVMap').outputs['UV'], tx.inputs['Vector'])
        hs = nt.nodes.new('ShaderNodeHueSaturation'); hs.inputs['Saturation'].default_value = 1.35; hs.inputs['Value'].default_value = 0.92
        nt.links.new(tx.outputs['Color'], hs.inputs['Color']); nt.links.new(hs.outputs['Color'], b.inputs['Base Color'])
        tp = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader')
        nt.links.new(tx.outputs['Alpha'], mx.inputs['Fac']); nt.links.new(tp.outputs[0], mx.inputs[1]); nt.links.new(b.outputs[0], mx.inputs[2])
        nt.links.new(mx.outputs[0], out.inputs['Surface'])
        # light through the cloth from behind
        b.inputs['Subsurface Weight'].default_value = 0.0
    else:
        b.inputs['Base Color'].default_value = C.lin(colour or '#ffffff')
    o = C.obj(name, me, m); sd = o.modifiers.new('s', 'SOLIDIFY'); sd.thickness = 0.008
    return o

def flag_plain(name, hoist, stream_hdg, w, h, colour):
    return flag_mesh(name, hoist, fwd(stream_hdg), w, h, colour=colour)

def staff(base, height, r=0.03, name='staff'):
    C.cyl(name, r, r * 0.7, height, 10, C.simple('staff', '#d9d9d4', 0.35, coat=0.4), Vector(base) + Vector((0, 0, height / 2)))
    C.obj(name + '-truck', K._sphere(name + '-truck', r * 1.6), C.simple('truck', '#d9d9d4', 0.35), Vector(base) + Vector((0, 0, height)))
    return Vector(base) + Vector((0, 0, height))

def hoist(top_pt, stream, flags, w=1.05, h=0.7, gap=0.16, line=True):
    """Flags one under another on a halyard from `top_pt`: [(tex path, label)]. Returns label anchors (fly ends)."""
    anchors = []; z = 0.12
    for k, (tex, _) in enumerate(flags):
        hp = Vector(top_pt) - Vector((0, 0, z))
        flag_mesh('flag', hp, stream, w, h, tex=tex, seed=k * 1.7)
        anchors.append(hp + Vector(stream).normalized() * (w * 0.5) - Vector((0, 0, h * 0.5)))
        z += h + gap
    if line:
        C.tube('halyard', [Vector(top_pt), Vector(top_pt) - Vector((0, 0, z + 0.3))], 0.006, 6, 1.0, C.simple('halyard', '#ece6d8', 0.8))
    return anchors

def backstay_point(yt, t):
    """A point on the yacht's backstay: t = 0 at the stern, 1 at the masthead."""
    a, b = yt.world((-3.55, 0.13, 4.35)), yt.world((4.95, 0.13, 20.4))
    return a.lerp(b, t)

def backstay_flag(yt, tex=None, colour=None, t=0.27, w=0.75, h=0.55, stream=None):
    """A protest or penalty flag tied into the backstay, flying downwind."""
    p = backstay_point(yt, t); stream = stream if stream is not None else fwd(180)
    up = (backstay_point(yt, 1) - backstay_point(yt, 0)).normalized()
    return flag_mesh('bs-flag', p, stream, w, h, tex=tex, colour=colour, up=up), p - up * h * 0.5 + Vector(stream) * w * 0.5

# ---------------------------------------------------------------- camera and labels
def project(p):
    sc = bpy.context.scene; bpy.context.view_layer.update()
    q = world_to_camera_view(sc, sc.camera, Vector(p)); return Vector((q.x * C.W, (1 - q.y) * C.H, q.z))

def unproject(sx, sy, depth):
    cam = bpy.context.scene.camera; cd = cam.data; bpy.context.view_layer.update()
    tx = math.tan(cd.angle_x / 2); ty = tx * C.H / C.W
    nx, ny = (sx / C.W) * 2 - 1, 1 - (sy / C.H) * 2
    d = cam.matrix_world.to_quaternion() @ Vector((nx * tx, ny * ty, -1.0))
    return cam.matrix_world.translation + d * depth

def drone(points, az=195.0, el=58.0, lens=35.0, box=(80, 175, 1200, 760), sun=None, ground=True):
    """A high drone camera from azimuth `az` (where it stands, seen from the scene) and elevation `el`, its
    distance and aim found so that every point (world) lands inside the screen box (x0, y0, x1, y1)."""
    pts = [Vector(p) for p in points]
    c = sum(pts, Vector()) / len(pts)
    if ground: c.z = 0.0
    a, e = deg(az), deg(el); dirv = Vector((math.sin(a) * math.cos(e), math.cos(a) * math.cos(e), math.sin(e)))
    D = max((p - c).length for p in pts) * 3 + 30
    cam = K.camera(tuple(c + dirv * D), tuple(c), lens)
    sc = bpy.context.scene; sc.render.resolution_x, sc.render.resolution_y = C.W, C.H
    x0, y0, x1, y1 = box
    for _ in range(30):
        q = [project(p) for p in pts]
        mnx, mxx, mny, mxy = min(v.x for v in q), max(v.x for v in q), min(v.y for v in q), max(v.y for v in q)
        k = max((mxx - mnx) / (x1 - x0), (mxy - mny) / (y1 - y0))
        # aim: move the target so the points' box centre sits on the screen box centre
        dx, dy = (x0 + x1) / 2 - (mnx + mxx) / 2, (y0 + y1) / 2 - (mny + mxy) / 2
        g = unproject(C.W / 2 - dx, C.H / 2 - dy, D); r = cam.matrix_world.translation
        if ground:
            hit = r + (g - r) * (r.z / max(1e-3, (r.z - g.z)))     # where that ray meets the sea
            c = Vector((hit.x, hit.y, 0.0))
        else: c = c + (g - unproject(C.W / 2, C.H / 2, D))
        D *= 0.55 + 0.45 * k if k < 1 else k
        cam.location = c + dirv * D; cam.rotation_euler = (-dirv).to_track_quat('-Z', 'Y').to_euler()
        if abs(k - 1) < 0.01 and abs(dx) < 2 and abs(dy) < 2: break
    K.day_sky(sun_az=sun if sun is not None else az + 30, sun_el=50)
    return cam, D

def wind_arrow(arrows, labels, depth, at=(1110, 250), direction=None, px=150, text='Wind', color='blue'):
    """The wind as a fat arrow on the water at screen spot `at`, pointing the way the wind blows."""
    d = direction or fwd(180)
    mid = unproject(at[0], at[1], depth); cam = bpy.context.scene.camera.matrix_world.translation
    mid = cam + (mid - cam) * (cam.z / max(1e-3, cam.z - mid.z)); mid.z = 0.5
    a, b = project(mid - d), project(mid + d); s = px / max(8.0, (a.xy - b.xy).length)
    p0, p1 = mid - d * s, mid + d * s
    arrows.append((tuple(p0), tuple(p1), color))
    labels.append((tuple(p0 + Vector((0, 0, 0.02 * depth))), text, color) if project(p0).y > project(p1).y else (tuple(p0), text, color))

# ---------------------------------------------------------------- a whole race figure
def free_spot(cands, avoid):
    """The screen candidate farthest from every point to avoid (screen x, y)."""
    return max(cands, key=lambda c: min([math.dist(c, a) for a in avoid] or [1e9]))

def race(f, cfg, out, samples=144, expo=-0.6):
    """Build and render FIG.race spec `f`. cfg: note; boats {label or index: {text, color, boom, heel, genoa,
    wake, still, astern, nudge (dx, dy figure units)}}; mark {text, color}; zone; line {text, cb, pin, kind};
    track {w, strength, trim}; cam {az, el, lens}; sea; extra(ctx) adds to the scene before the camera;
    after(ctx) adds labels after it."""
    wind = f.get('wind', 0) or 0
    xs = [b['x'] for b in f.get('boats', [])]; ys = [b['y'] for b in f.get('boats', [])]
    for k in ('mark',):
        if f.get(k): xs.append(f[k]['x']); ys.append(f[k]['y'])
    if f.get('line'): xs += [f['line']['x1'], f['line']['x2']]; ys += [f['line']['y1'], f['line']['y2']]
    cen = W(sum(xs) / len(xs), sum(ys) / len(ys))
    K.sea(cfg.get('sea', 'breeze'), size=36.0, repeat=16, center=(cen.x, cen.y))
    ctx = {'boats': {}, 'labels': [], 'arrows': [], 'pts': [], 'f': f, 'cfg': cfg}
    L, pts = ctx['labels'], ctx['pts']
    for i, b in enumerate(f.get('boats', [])):
        key = b.get('label') if b.get('label') in cfg.get('boats', {}) else i
        bc = dict(cfg.get('boats', {}).get(key, {}))
        bb = dict(b)
        if bc.get('nudge'): bb['x'] += bc['nudge'][0]; bb['y'] += bc['nudge'][1]
        yt = boat(bb, wind, boom=bc.get('boom'), heel=bc.get('heel'), genoa=bc.get('genoa', True), name=f'boat{i}')
        if bc.get('wake', True) and not bc.get('still'):
            if bc.get('astern'): P.wake_decal(tuple(bow(yt).xy), (yt.hdg + 180) % 360, 14, 3.5, stern=-1.0, strength=0.7)
            else: wake(yt, bc.get('wake_len', 34), 8, bc.get('wake_k', 0.9))
        ctx['boats'][key] = yt; ctx['boats'][b.get('label') or i] = yt
        pts += [bow(yt), stern(yt), top(yt)]
        text = bc.get('text', b.get('label') or '')
        if text:
            lab = (tuple(top(yt) + Vector((0, 0, bc.get('lift', 0.0)))), text, bc.get('color', 'blue' if b.get('you') else None))
            L.append(lab + (bc['off'],) if bc.get('off') else lab)
    if f.get('mark'):
        m = f['mark']; mc = cfg.get('mark', {})
        mt = mark(m['x'], m['y'])
        if m.get('zone') or cfg.get('zone'):
            z = m.get('zone'); R_ = zone(m['x'], m['y'], z if isinstance(z, (int, float)) and not isinstance(z, bool) else None)
            zc = W(m['x'], m['y']); pts += [zc + Vector((R_, 0, 0)), zc - Vector((R_, 0, 0)), zc + Vector((0, R_, 0)), zc - Vector((0, R_, 0))]
            if cfg.get('zone_text'): L.append((tuple(zc + Vector((0, R_, 0.5))), cfg['zone_text'], 'blue'))
        pts.append(mt)
        if mc.get('text', m.get('label')): L.append((tuple(mt + Vector((0, 0, 1.0))), mc.get('text', m.get('label')), mc.get('color')))
    if f.get('line'):
        l = f['line']; lc = cfg.get('line', {})
        parts = start_line(l, wind, cb=lc.get('cb', True), pin_end=lc.get('pin', True))
        a, b = W(l['x1'], l['y1']), W(l['x2'], l['y2']); pts += [a, b]
        if 'cb' in parts:
            ctx['cb'] = parts['cb']; pts.append(parts['cb'][2])
            if lc.get('cb_text'): L.append((tuple(parts['cb'][2] + Vector((0, 0, 1.0))), lc['cb_text']))
        if 'pin' in parts and lc.get('pin_text'): L.append((tuple(parts['pin']), lc['pin_text']))
        if lc.get('text', l.get('label')):
            t = lc.get('at', 0.5); p = a.lerp(b, t); L.append((tuple(p + Vector((0, 0, 0.4))), lc.get('text', l.get('label')), lc.get('color')))
    if f.get('obstruction') and cfg.get('obstruction'): cfg['obstruction'](ctx)
    if f.get('track') and cfg.get('track', {}) is not None:
        tc = cfg.get('track') or {}; you = next((y for k, y in ctx['boats'].items() if k == 'You'), None)
        track(f['track'], tc.get('w', 2.2), tc.get('strength', 0.6), tc.get('trim', 0.0), you.centre if (tc.get('split') and you) else None)
        pts += [W(*p) for p in svg_path(f['track'])[::6]]
    if cfg.get('extra'): cfg['extra'](ctx)
    cc = cfg.get('cam', {})
    cam, D = drone(pts + [Vector(l[0]) for l in L], cc.get('az', 192), cc.get('el', 58), cc.get('lens', 35), box=cc.get('box', (170, 215, 1110, 720)))
    if cfg.get('after'): cfg['after'](ctx)
    if cfg.get('wind', True):
        avoid = [tuple(project(p).xy) for p in pts] + [tuple(project(l[0]).xy) for l in L]
        sx, sy = free_spot(cc.get('wind_at') or [(150, 300), (150, 640), (1130, 300), (1130, 620)], avoid)
        wind_arrow(ctx['arrows'], L, D, at=(sx, sy), direction=fwd(wind + 180))
    C.render(out, samples, SCALE, cfg.get('expo', expo), L, cfg.get('note', f.get('note')), space='blender', arrows=ctx['arrows'])
    return ctx

def flags_scene(art, flags, cfg, out, samples=144):
    """A flag figure: the committee boat at anchor, head to wind, her flags on staffs along her side deck, flying
    aft; seen from abeam and a little above, the flags filling the frame. flags: [(code, text, staff group)] —
    flags of one group hang one under another on the same staff ('over'). Each group's top flag is named above
    it, a lower one below it on a leader."""
    K.sea('calm', size=30.0, repeat=10)
    need_tex(art, ['flag-' + c for c, _, _ in flags])
    root, vis, tp, deck = committee_boat(160, 100, 0.0, cfg.get('L', 14.0))
    bpy.context.view_layer.update(); lo, hi = K.bbox(vis)
    groups = []
    for c, t, g in flags:
        if not groups or groups[-1][0] != g: groups.append((g, []))
        groups[-1][1].append((tex_path(art, 'flag-' + c), t))
    n = len(groups); sp = cfg.get('spacing', 2.6); fw, fh = cfg.get('fw', 1.5), cfg.get('fh', 1.0)
    x_side = hi.x - 0.3
    y0 = (lo.y + hi.y) / 2 - (n - 1) * sp / 2 + cfg.get('dy', 1.8)     # the first group furthest aft: read left to right from abeam
    z_top = hi.z + cfg.get('above', 1.4); fl_pts = []; marks = []
    for k, (g, fl) in enumerate(groups):
        base = Vector((x_side, y0 + k * sp, deck)); tipz = z_top + (len(fl) - 1) * (fh + 0.16) + (k % 2) * cfg.get('stagger', 0.0)
        t = staff(base, tipz - deck)
        anchors = hoist(t, fwd(180), fl, fw, fh)
        for j, (a, (_, text)) in enumerate(zip(anchors, fl)):
            fl_pts += [a + Vector((0, fw / 2, fh / 2)), a + Vector((0, -fw / 2, -fh / 2))]
            marks.append((a, text, j))
    c = sum(fl_pts, Vector()) / len(fl_pts); cc = cfg.get('cam', {})
    pts = fl_pts + [p + Vector((0, 0, fh / 2 + 0.9)) for p, _, j in marks if j == 0] + [Vector((c.x, c.y, deck - 1.0))]
    drone(pts, cc.get('az', 95), cc.get('el', 8), cc.get('lens', 40), box=cc.get('box', (150, 200, 1130, 700)), sun=cc.get('sun', 140), ground=False)
    L = []
    for a, text, j in marks:
        if j == 0: L.append((tuple(a + Vector((0, 0, fh / 2 + 0.05))), text))
        else:
            q = project(a + Vector((0, 0, -fh / 2))); L.append((tuple(a + Vector((0, 0, -fh / 2))), text, None, (0, 92)))
    L += cfg.get('labels', [])
    C.render(out, samples, SCALE, cfg.get('expo', -0.5), L, cfg.get('note'), space='blender')
