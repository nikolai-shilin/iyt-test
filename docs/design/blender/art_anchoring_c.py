# Article bareboat-skipper/anchoring, figures 5, 6 and 10, as Blender renders (replacing the Three.js ones):
#   --fig 5   lights at anchor: from our foredeck at night, a yacht at anchor ahead with one all-round white light
#   --fig 6   is she dragging? the anchor-watch chart on a real Raymarine Axiom at the helm, at night
#   --fig 10  mooring buoy: a slip line from the bow cleat, through the buoy's ring and back to the same cleat
# Figure 6 needs its screen image first, drawn by article-figures.html (plotter()); with the figure-style server on
# :5182, run with the system Python:  python3 docs/design/blender/art_anchoring_c.py --prep
# Then, for each figure:
#   blender --background --factory-startup --python docs/design/blender/art_anchoring_c.py -- --fig 6 \
#     --out docs/design/figure-style/articles/bareboat-skipper/anchoring/6-3d.jpg --samples 192
import os, sys, math

HERE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(HERE, 'textures')
SCREEN_PNG = os.path.join(TEX, 'anchoring-6-plotter.png')
FRONT_PNG = os.path.join(TEX, 'axiom-anchor-watch.png')

# ---------- prep: get the plotter screen out of article-figures.html (system Python, not Blender) ----------
CDP_JS = r"""
import { spawn } from 'node:child_process'; import { mkdtempSync, writeFileSync } from 'node:fs'; import { tmpdir } from 'node:os'; import { join } from 'node:path';
const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', PORT = 9347, OUT = process.argv[2];
const chrome = spawn(CHROME, ['--headless=new', '--disable-gpu', '--no-first-run', `--remote-debugging-port=${PORT}`, `--user-data-dir=${mkdtempSync(join(tmpdir(), 'art6-'))}`, 'about:blank'], { stdio: 'ignore' });
const sleep = ms => new Promise(r => setTimeout(r, ms));
try {
  let v; for (let i = 0; i < 50 && !v; i++) { await sleep(200); v = await fetch(`http://127.0.0.1:${PORT}/json/version`).then(r => r.json()).catch(() => null); }
  const tab = await fetch(`http://127.0.0.1:${PORT}/json/new?` + encodeURIComponent('http://localhost:5182/article-figures.html?a=bareboat-skipper/anchoring'), { method: 'PUT' }).then(r => r.json());
  const ws = new WebSocket(tab.webSocketDebuggerUrl); await new Promise(r => ws.addEventListener('open', r, { once: true }));
  let id = 0; const pend = new Map(); ws.addEventListener('message', e => { const m = JSON.parse(e.data); if (pend.has(m.id)) { pend.get(m.id)(m); pend.delete(m.id); } });
  const ev = x => new Promise(r => { const i = ++id; pend.set(i, r); setTimeout(() => r({}), 60000); ws.send(JSON.stringify({ id: i, method: 'Runtime.evaluate', params: { expression: x, returnByValue: true, awaitPromise: true } })); }).then(m => m.result?.result?.value);
  let url; for (let i = 0; i < 120 && !url; i++) { await sleep(500); url = await ev("window.__renders && window.__renders['6'] ? 'y' : ''"); }
  // the page draws the canvas before its web font arrives: wait for Carlito, then draw the screen again
  await ev(`(async () => { await document.fonts.load('700 30px Carlito'); await document.fonts.load('400 26px Carlito'); await document.fonts.ready;
    const d = await (await fetch('article-figs/bareboat-skipper-anchoring.json')).json();
    window.__renders['6'] = plotter(d.figs.find(f => f.n === 6).fig).toDataURL('image/jpeg', 0.95); return 1; })()`);
  const len = await ev("window.__renders['6'].length"); let s = '';
  for (let i = 0; i < len; i += 1 << 20) s += await ev(`window.__renders['6'].slice(${i}, ${i + (1 << 20)})`);
  writeFileSync(OUT, Buffer.from(s.split(',')[1], 'base64')); ws.close(); console.log('saved', OUT);
} finally { chrome.kill(); }
"""

def prep():
    import subprocess, tempfile
    from PIL import Image
    os.makedirs(TEX, exist_ok=True)
    js = os.path.join(tempfile.mkdtemp(), 'art6.mjs'); open(js, 'w').write(CDP_JS)
    full = os.path.join(tempfile.mkdtemp(), 'plotter.jpg')
    subprocess.run(['node', js, full], check=True)
    im = Image.open(full).convert('RGB')
    screen = im.crop((140, 96, 140 + 920, 96 + 610))          # plotter(): the chart screen inside its own bezel
    screen.save(SCREEN_PNG)
    # the model's front texture: the screen glass covers x 70..645, y 72..432 of 828 x 481; put the chart there
    front_src = os.path.join(TEX, 'axiom-front.png')     # the model's own front texture (Image_1), saved from Blender
    front = Image.open(front_src).convert('RGB')
    x0, y0, x1, y1 = 70, 72, 645, 432
    front.paste(screen.resize((x1 - x0, y1 - y0), Image.LANCZOS), (x0, y0))
    front.save(FRONT_PNG); print('wrote', SCREEN_PNG, FRONT_PNG)

if __name__ == '__main__' and '--prep' in sys.argv:
    prep(); sys.exit(0)

# ---------- Blender ----------
sys.path.insert(0, HERE)
import bpy, bmesh
from mathutils import Vector, Euler
import common as C, kit as K, kit_night as N

arg = C.cli(); FIG = arg('--fig', 5); SAMPLES = arg('--samples', 192); SCALE = arg('--scale', 100)
OUT = arg('--out', os.path.join(HERE, '..', 'figure-style', 'articles', 'bareboat-skipper', 'anchoring', f'{FIG}-3d.jpg'))

def deg(a): return math.radians(a)

def sphere(name, r, mat, loc, seg=48):
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=seg // 2, radius=r)
    for f in bm.faces: f.smooth = True
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    return C.obj(name, me, mat, Vector(loc))

def torus(name, R, r, mat, loc, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, major_segments=48, minor_segments=14, location=loc, rotation=rot)
    o = bpy.context.active_object; o.name = name; o.data.materials.append(mat)
    for p in o.data.polygons: p.use_smooth = True
    return o

C.reset()

if FIG == 5:
    # we lie at anchor too, looking forward; the other yacht is anchored ahead, lying to the same breeze (bow to us)
    y = K.load_yacht(); y.place(0, 0, heading=0)
    N.night_scene('calm')
    N.cloth_furled(y)          # at anchor we show no sidelights either: only our own anchor light, out of view above
    bow = y.world((10.5, 0.13, 2.0))
    p = N.at_bearing(bow, 12, 55)
    o = K.load_yacht(name='anchored'); o.place(p.x, p.y, heading=192); N.cloth_furled(o)
    top = o.world((5.06, 0.13, 20.8))
    N.light('anchor-light', top, 'white', strength=12.0, power=40.0, radius=0.16)
    # a faint glow from her cabin and a second boat far off, so the anchorage reads as an anchorage
    q = N.at_bearing(bow, -28, 190)
    far = K.load_yacht(name='far'); far.place(q.x, q.y, heading=170)
    N.light('far-anchor-light', far.world((5.06, 0.13, 20.8)), 'white', strength=6.0, power=10.0, radius=0.12)
    N.foredeck_camera(y, bearing=7, lens=28, pitch=2.5)
    C.render(OUT, SAMPLES, SCALE, 0.8, [(tuple(top + Vector((0, 0, 1.0))), 'all-round white: at anchor')],
             None, space='blender', extra={'bloom': 1.0})

elif FIG == 6:
    if not os.path.exists(FRONT_PNG): raise SystemExit('run --prep first (see the header)')
    M = K.mats()
    # the cockpit at 0300: a helm pod in front of the wheel with the plotter on it, the binnacle top, a dark sea
    K.night_sky(moon=0.0, stars=True)
    pod = C.obj('pod', C.rbox('pod', (0.34, 0.16, 0.14), 0.04, 4), M['dark'], (0.0, 0.03, -0.09))
    C.cyl('binnacle', 0.06, 0.07, 0.9, 32, C.simple('binnacle', '#c9cdd1', 0.25, 1.0), (0.0, 0.03, -0.6))
    root, objs = K.load_model('chartplotter-raymarine-axiom.glb', drop_planes=False)
    bpy.context.view_layer.update(); lo, hi = K.bbox([o for o in objs if o.type == 'MESH'])
    k = 0.235 / (hi.x - lo.x); root.scale = (k,) * 3; bpy.context.view_layer.update()
    lo, hi = K.bbox([o for o in objs if o.type == 'MESH'])
    root.location = (root.location.x - (lo.x + hi.x) / 2, root.location.y - (lo.y + hi.y) / 2, root.location.z - lo.z - 0.02)
    root.rotation_euler = (deg(-12), 0, 0)                       # tilted back towards the helmsman
    # the screen: the model's own front texture with the anchor-watch chart pasted onto its glass, glowing
    img = bpy.data.images.load(FRONT_PNG)
    for o in objs:
        for sl in getattr(o, 'material_slots', []):
            if sl.material and sl.material.name.startswith('raymarine--displays'):
                m, nt, b, out = C.new_mat('axiom-screen')
                uv = nt.nodes.new('ShaderNodeUVMap'); tx = nt.nodes.new('ShaderNodeTexImage'); tx.image = img
                nt.links.new(uv.outputs['UV'], tx.inputs['Vector']); b.inputs['Base Color'].default_value = (0.01, 0.01, 0.012, 1)
                nt.links.new(tx.outputs['Color'], b.inputs['Emission Color']); b.inputs['Emission Strength'].default_value = 0.7    # lit from within only
                b.inputs['Roughness'].default_value = 0.08; b.inputs['Coat Weight'].default_value = 1.0
                sl.material = m
    # a wheel rim in the foreground, the coaming behind, a red night light in the cockpit
    bpy.ops.mesh.primitive_torus_add(major_radius=0.55, minor_radius=0.018, location=(0.0, -0.32, -0.25), rotation=(deg(80), 0, 0))
    w = bpy.context.active_object; w.data.materials.append(C.simple('wheel', '#1d1e20', 0.5)); [setattr(p, 'use_smooth', True) for p in w.data.polygons]
    deckm = bpy.data.meshes.new('cockpit'); deckm.from_pydata([(-3, -3, -1.0), (3, -3, -1.0), (3, 3, -1.0), (-3, 3, -1.0)], [], [(0, 1, 2, 3)])
    C.obj('cockpit', deckm, M['teak'])
    K.sea('breeze', color='#050d14', foam=False)
    for o in bpy.data.objects:
        if o.name.startswith(('ocean', 'far-sea')): o.location.z -= 2.4
    ld = bpy.data.lights.new('red-night', 'AREA'); ld.energy = 18.0; ld.size = 0.6; ld.color = (1.0, 0.2, 0.1)
    lo_ = bpy.data.objects.new('red-night', ld); C.col.objects.link(lo_); lo_.location = (0.6, -0.7, 0.4)
    lo_.rotation_euler = (Vector((0, 0.03, -0.1)) - lo_.location).to_track_quat('-Z', 'Y').to_euler()
    bpy.context.view_layer.update(); lo, hi = K.bbox([o for o in objs if o.type == 'MESH'])
    K.camera((0.07, -0.56, 0.24), tuple((lo + hi) / 2 + Vector((0.01, 0, -0.012))), 54)
    C.render(OUT, SAMPLES, SCALE, -0.2, [], 'Plotter, 0300 · wind NW F6', space='blender', extra={'bloom': 0.5})

else:  # 10
    M = K.mats()
    y = K.load_yacht(); y.place(0, 0, heading=0)
    K.sea('calm'); K.day_sky(sun_az=210, sun_el=40); K.darken_visible_sky()
    K.coast(distance=900, bearing=20, height=120, town=True)
    # the mooring buoy ahead: a white float with a red band, a galvanised eye and a ring on top
    bow = y.world((10.9, 0.13, 2.0)); bc = Vector((bow.x - 0.3, bow.y + 3.6, 0.0))
    fl = sphere('float', 0.55, C.simple('buoy-float', '#eceae3', 0.45, coat=0.5), (bc.x, bc.y, 0.18)); fl.scale.z = 0.75
    torus('band', 0.535, 0.045, C.simple('buoy-band', '#c8102e', 0.45, coat=0.4), (bc.x, bc.y, 0.24))
    galv = K.mats()['galv']
    C.cyl('eye-post', 0.035, 0.045, 0.2, 16, galv, (bc.x, bc.y, 0.66))
    ring_c = Vector((bc.x, bc.y, 0.86)); ringR, ringr = 0.10, 0.016
    torus('ring', ringR, ringr, galv, tuple(ring_c), rot=(0, deg(90), 0))  # ring stands up, in the YZ plane
    # the line: off the starboard bow cleat, forward over the toe rail by the stem, down through the ring (from the
    # boat's side), back up and onto the same cleat; the two parts lie side by side
    cleat = y.world((8.905, -0.585, 3.575))
    rail = y.world((10.35, -0.22, 3.82)); rail2 = y.world((10.35, -0.08, 3.82))
    R = 0.012                                                       # a 24 mm mooring line
    down = ring_c + Vector((0, -0.05, -ringR + ringr + R))        # bottom of the ring
    def three(p): return (p.x, p.z, -p.y)                          # braid() takes Three.js-space points
    pts = [cleat + Vector((-0.10, 0.0, 0.0)), cleat + Vector((0.0, -0.02, 0.02)), cleat + Vector((0.12, 0.0, 0.03)),
           rail + Vector((0, 0, 0.03)), rail + Vector((0.05, 0.25, 0.0)),
           (rail + Vector((0.05, 0.25, 0))).lerp(down, 0.4) + Vector((0, 0, -0.25)),
           down + Vector((-0.02, -0.12, 0.08)), down, down + Vector((0.02, 0.12, 0.06)),
           ring_c + Vector((0.03, 0.14, 0.12)), (rail2 + Vector((0.05, 0.3, 0))).lerp(down, 0.35) + Vector((0, 0, -0.18)),
           rail2 + Vector((0.05, 0.25, 0.0)), rail2 + Vector((0, 0, 0.03)), cleat + Vector((0.12, 0.05, 0.035)),
           cleat + Vector((0.0, 0.04, 0.045)), cleat + Vector((-0.12, 0.03, 0.04)), cleat + Vector((-0.4, 0.12, 0.012)),
           cleat + Vector((-0.75, 0.3, 0.008))]
    pts = [p if p.z > 0 or i in (7,) else p for i, p in enumerate(pts)]
    C.braid('slipline', [C.V3(three(p)) for p in pts], R, '#1d4f91', '#e3eaf4', shiny=True, whip='#f2eee2', fine=1.4)
    eye = y.world((5.9, -2.2, 6.4)); K.camera(eye, tuple(cleat.lerp(down, 0.5)), 37)
    C.focus_on_centre(bpy.context.scene.camera, 16.0)
    C.render(OUT, SAMPLES, SCALE, -0.6, [(tuple(ring_c + Vector((0, 0, 0.3))), 'buoy ring'),
             (tuple((rail + Vector((0.05, 0.25, 0))).lerp(down, 0.55)), 'your own line'), (tuple(cleat + Vector((0, 0, 0.1))), 'same cleat')],
             'Through the ring and back to the same cleat', space='blender')
