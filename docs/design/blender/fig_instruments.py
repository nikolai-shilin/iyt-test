# Instrument and radio figures:
#   --kind radio    the fixed VHF (SIMRAD RS20S model) flush in the nav-station bulkhead, handset in its clip,
#                   the chartplotter beside it; parts labelled as in the radio figure
#   --kind panel    the engine panel in the cockpit: hours 2312.1, 12.6 V, fuel full; key, start and stop
#   --kind compass  the pedestal steering compass seen from the helm, 247 under the lubber line
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector
import common as C, kit as K, kit_instruments as KI

arg = C.cli(); OUT = arg('--out', 'fig-radio.jpg'); SAMPLES = arg('--samples', 192); SCALE = arg('--scale', 100); KIND = arg('--kind', 'radio')
C.reset()
M = K.mats()
labels, note, expo = [], None, -0.4

if KIND == 'radio':
    root, objs = K.load_model('radio-vhf-simrad-rs20s.glb', drop_planes=False)
    for o in objs:   # an untextured white plane the author left over the photographed front panel
        if o.type == 'MESH' and all(sl.material is None for sl in o.material_slots) and len(o.data.polygons) <= 4: o.hide_render = True
    KI.wall('bulkhead', -0.42, 0.40, -0.26, 0.30, 0.004, KI.joinery_mat())
    # a semi-matte front: the SketchUp export made every surface fairly glossy, which washes the panel out
    for o in objs:
        for sl in getattr(o, 'material_slots', []):
            m = sl.material
            if m and m.node_tree:
                b = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
                if b: b.inputs['Roughness'].default_value = 0.62; b.inputs['Specular IOR Level'].default_value = 0.25
    for o in objs:
        if o.type != 'MESH': continue
        names = {sl.material.name for sl in o.material_slots if sl.material}
        if 'Material-7503' in names:          # the photographed front: lift it off the body's coplanar face, and give
            mw = o.matrix_world.copy(); mw.translation.y -= 0.0006; o.matrix_world = mw   # it a clean material:
            old = next(sl.material for sl in o.material_slots if sl.material)        # the export's has alpha and glow
            img = next(n.image for n in old.node_tree.nodes if n.type == 'TEX_IMAGE')
            fm, fnt, fb, _ = C.new_mat('vhf-front'); tx = fnt.nodes.new('ShaderNodeTexImage'); tx.image = img
            uvn = fnt.nodes.new('ShaderNodeUVMap'); fnt.links.new(uvn.outputs['UV'], tx.inputs['Vector'])
            fnt.links.new(tx.outputs['Color'], fb.inputs['Base Color']); fb.inputs['Roughness'].default_value = 0.5
            for sl in o.material_slots: sl.material = fm
        if names & {'Fig30', '[Color M07]', '[Color_007]1'}:    # handset and body: near-black plastic, as on the real set
            for sl in o.material_slots:
                bb = next((n for n in sl.material.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
                if bb and not bb.inputs['Base Color'].is_linked: bb.inputs['Base Color'].default_value = (0.018, 0.019, 0.021, 1)
    K.day_sky(sun_az=150, sun_el=40, strength=0.08)
    KI.area_light((0.5, -0.9, 0.55), (0.05, 0, 0.04), 7, 0.6)               # the porthole, front right
    KI.area_light((-0.6, -0.8, 0.3), (0, 0, 0.04), 2, 1.0, (0.85, 0.9, 1.0))  # fill from the companionway
    K.camera((0.15, -0.40, 0.11), (0.095, 0, 0.05), 50)
    # parts, from the photographed front panel (999 x 531 px over 170 x 90 mm)
    px = lambda u, v: (u / 999 * 0.17, 0.0, (1 - v / 531) * 0.09)
    P = {'display': px(495, 140), 'channel': px(140, 95), 'volume': px(180, 290), 'power': px(122, 420),
         'ch16': px(590, 420), 'distress': px(760, 395), 'mic': (0.20, -0.05, 0.123), 'ptt': (0.182, -0.045, 0.095)}
    names = [('display', 'channel 16'), ('channel', 'channel knob'), ('volume', 'VOL · SQL'), ('distress', 'DISTRESS, under its cover'),
             ('mic', 'microphone'), ('ptt', 'press to talk')]
    labels = [(P[k], t) for k, t in names]
    note = 'Fixed VHF with DSC, channel 16'
elif KIND == 'panel':
    # the engine panel let into the cockpit side, facing aft (-Y)
    gel = M['hull']
    KI.wall('cockpit-side', -0.6, 0.6, -0.4, 0.35, 0.012, gel)
    C.obj('panel', C.rbox('panel', (0.34, 0.012, 0.15), 0.006, 3), M['dark'], (0.0, 0.006, 0.0))
    KI.gauge(KI.face_png('tach', '2312.1'), (-0.075, -0.001, 0.005), 0.05, value_angle=-135)
    v = 12.6; KI.gauge(KI.face_png('volts'), (0.045, -0.001, 0.03), 0.03, value_angle=-60 + (v - 8) / 8 * 120)
    KI.gauge(KI.face_png('fuel'), (0.115, -0.001, 0.03), 0.03, value_angle=60)
    # key switch, start and stop, three warning lamps
    C.obj('key', KI._cyl_y(0.014, 0.01), M['chrome'], (0.045, -0.005, -0.04))
    C.obj('key-bit', C.rbox('kb', (0.006, 0.02, 0.022), 0.002, 2), M['dark'], (0.045, -0.016, -0.04))
    for i, (x, col) in enumerate(((0.09, '#2a8a3a'), (0.125, '#b3261e'))):
        C.obj('button', KI._cyl_y(0.009, 0.008), C.simple('btn%d' % i, col, 0.4, coat=0.5), (x, -0.004, -0.04))
    for i, x in enumerate((-0.105, -0.075, -0.045)):
        C.obj('lamp', KI._cyl_y(0.005, 0.004), C.simple('lamp%d' % i, ('#7a1010', '#806a10', '#7a1010')[i], 0.2, coat=1.0), (x, -0.003, -0.055))
    K.day_sky(sun_az=200, sun_el=35, strength=0.18)
    K.camera((0.06, -0.48, 0.12), (0.02, 0, 0.0), 45)
    labels = [((-0.075, 0, 0.065), 'Hours 2312.1'), ((0.045, 0, 0.068), 'Volts 12.6'), ((0.115, 0, 0.068), 'Fuel 4/4')]
    note = 'Form says: engine hours 2,290'; expo = -0.6
else:  # compass
    # a pedestal compass: black bowl, glass dome, a black card with white figures, the red lubber line forward
    C.lathe('bowl', [(0.0, -0.02), (0.075, -0.02), (0.085, 0.0), (0.083, 0.012), (0.07, 0.016), (0.0, 0.016)], 96, M['dark'])
    C.lathe('pedestal', [(0.0, -0.75), (0.06, -0.75), (0.055, -0.03), (0.07, -0.02), (0.0, -0.02)], 64, C.simple('pedestal', '#cfd2d4', 0.25, 1.0))
    card = KI.disc('card', 0.058, KI.image_mat('card', KI.face_png('card'), 0.45), (0, 0, 0.022), normal='Z+')
    card.rotation_euler = (0, 0, math.radians(247))            # 247 comes to the forward lubber line (+Y)
    C.obj('lubber', C.rbox('lubber', (0.003, 0.004, 0.02), 0.0005, 1), C.simple('lubber', '#e0201a', 0.4, coat=0.5), (0, 0.062, 0.03))
    bm = __import__('bmesh').new(); __import__('bmesh').ops.create_uvsphere(bm, u_segments=64, v_segments=32, radius=0.07)
    for v in list(bm.verts):
        if v.co.z < 0: v.co.z = 0
    me = bpy.data.meshes.new('dome'); bm.to_mesh(me); bm.free(); me.shade_smooth()
    C.obj('dome', me, KI.glass_mat('dome-glass'), (0, 0, 0.016))
    # the cockpit around it: sole, wheel rim behind the camera, the sea
    K.sea('breeze', center=(0, 0)); K.day_sky(sun_az=230, sun_el=45)
    for o in bpy.data.objects:
        if o.name.startswith(('ocean', 'far-sea')): o.location.z -= 1.4
    KI.wall('sole', -1.5, 1.5, -1.5, 1.5, 0, M['teak']).rotation_euler = (0, 0, 0)
    sole = bpy.data.objects['sole']; sole.data.vertices.foreach_set('co', [-1.2, -1.5, -0.75, 1.2, -1.5, -0.75, 1.2, 1.5, -0.75, -1.2, 1.5, -0.75]); sole.data.update()
    K.camera((0.0, -0.46, 0.36), (0, 0.035, -0.02), 40)
    labels = [((0, 0.065, 0.06), 'lubber line · 247°')]
    note = 'No deviation · variation 3° W'
C.render(OUT, SAMPLES, SCALE, expo, labels, note, space='blender')
