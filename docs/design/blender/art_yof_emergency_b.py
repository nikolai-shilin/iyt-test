# Article yachtmaster-offshore/emergency, the figures below decks and close up (3, 4, 6, 10, 11, 12, 13); run by
# art_yof_emergency.py --fig n, in its namespace (T, TA, ADIR, OUT, FIG, SAMPLES, SCALE, deg). Blender space, Z up,
# metres; a bulkhead is the plane y = 0 facing -Y (towards the camera), a table top is z = 0.
#   3  engine-room fire: the alarm panel (95 °C, fans still on, generator running), the fixed-system release box
#   4  flooding: water over the cabin sole, the inflow at a broken seacock under a lifted floorboard, the pump hose
#   6  no charging, at night: the chart table, the battery monitor at 11.9 V and 0 A, only NAV LIGHTS and VHF on,
#      the DR plot in pencil on the paper chart
#   10 the grab bag on the cockpit seat: EPIRB, radar SART, AIS-SART, handheld VHF, flares
#   11 the fixed VHF on 16 under radio silence (art_vhf.py and a spec)
#   12 the deck log open on the chart table: 245°T struck through once, 254°T beside it, initialled
#   13 the policy schedule (limits highlighted, warranties) and the written extension on the chart table
import random
import art_checkin_nps_kit as A
import q_encounter_props as P
from mathutils import Vector, Euler

if FIG == 11:
    spec = {'channel': '16', 'power': 'HI', 'note': 'Silence on channel 16',
            'parts': [['display', 'SEELONCE MAYDAY: distress traffic only', 'red'], ['handset', 'others wait for SEELONCE FEENEE']]}
    sys.argv = [sys.argv[0], '--', '--spec', json.dumps(spec), '--out', OUT, '--samples', str(SAMPLES), '--scale', str(SCALE)]
    exec(compile(open(os.path.join(HERE, 'art_vhf.py')).read(), 'art_vhf.py', 'exec'), {'__name__': '__main__', '__file__': os.path.join(HERE, 'art_vhf.py')})
    sys.exit(0)

C.reset()
M = K.mats()
labels, arrows, note, expo, extra = [], [], None, -0.5, {}

def bulk_quad(name, w, h, path, cx, cz, y=-0.002, emit=0.0, rough=0.4):
    """An image on the bulkhead, facing -Y, centred at (cx, cz)."""
    return A.quad(name, w, h, path, (cx, y, cz), rot=(deg(90), 0, 0), emit=emit, rough=rough)
def on_bulk(cx, cz, w, h, uv, y=-0.004): return Vector((cx + (uv[0] - 0.5) * w, y, cz + (uv[1] - 0.5) * h))
def box(name, dims, loc, mat, r=0.0, rot=(0, 0, 0)):
    o = C.obj(name, C.rbox(name, dims, r, 2), mat, tuple(loc)); o.rotation_euler = rot; return o

def interior(key=8, fill=2.5, at=(0, 0, 0.1), sky=0.06):
    K.day_sky(sun_az=150, sun_el=40, strength=sky)
    KI.area_light((at[0] + 0.6, -1.0, at[2] + 0.7), at, key, 0.8)
    KI.area_light((at[0] - 0.8, -0.9, at[2] + 0.3), at, fill, 1.2, (0.85, 0.9, 1.0))

def table(w=1.3, d=0.8, z=0.0):
    C.obj('table', C.rbox('table', (w, d, 0.03), 0.004, 2), KI.joinery_mat('table-wood'), (0, 0, z - 0.015))

def pen(at, rotz, color='#1d2a55', L=0.13):
    pv = bpy.data.objects.new('pen', None); C.col.objects.link(pv)
    a = C.cyl('pen-body', 0.0055, 0.0055, L, 24, C.simple('pen-' + color, color, 0.3, coat=0.8), (0, 0, 0)); a.parent = pv
    b = C.cyl('pen-tip', 0.0055, 0.0012, 0.02, 24, M['chrome'], (0, 0, L / 2 + 0.01)); b.parent = pv
    pv.rotation_euler = (0, deg(90), deg(rotz)); pv.location = (at[0], at[1], 0.0056)
    return pv

if FIG == 3:
    # the wheelhouse bulkhead: the engine-room panel in alarm, the red release box beside it, engine stops below
    interior(key=6, fill=2.0, at=(0.05, 0, 0.1))
    KI.wall('bulkhead', -0.6, 0.7, -0.35, 0.55, 0.0, KI.joinery_mat())
    pw, ph = 0.30, 0.193; pcx, pcz = -0.12, 0.17
    box('fp-frame', (pw + 0.02, 0.02, ph + 0.02), (pcx, -0.008, pcz), M['dark'], 0.006)
    bulk_quad('firepanel', pw, ph, T('firepanel'), pcx, pcz, y=-0.0185, emit=0.55); fa = TA('firepanel')
    rw, rh = 0.16, 0.22; rcx, rcz = 0.22, 0.13
    box('rel-box', (rw + 0.01, 0.05, rh + 0.01), (rcx, -0.025, rcz), C.simple('rel-red', '#b5121b', 0.35, coat=0.6), 0.008)
    bulk_quad('release', rw, rh, T('release'), rcx, rcz, y=-0.0505)
    # the pull handle: a red T on a short cable, in front of the PULL square
    hx, hz = rcx, rcz - rh * 0.33
    C.cyl('pull-cable', 0.004, 0.004, 0.05, 12, M['chrome'], (hx, -0.075, hz), (deg(90), 0, 0))
    box('pull-T', (0.07, 0.016, 0.016), (hx, -0.1, hz), C.simple('pull-red', '#d0161c', 0.3, coat=0.8), 0.006)
    # engine and generator stops: red mushroom buttons on a dark strip, the gauge of a running engine
    sx, sz = -0.1, -0.12
    box('stop-strip', (0.42, 0.02, 0.1), (sx, -0.008, sz), M['dark'], 0.006)
    stop = C.simple('stop-red', '#c4161c', 0.3, coat=0.6)
    for i, t in enumerate(('PORT', 'STBD', 'GEN')):
        x = sx - 0.12 + i * 0.12
        C.cyl('stop-btn', 0.022, 0.022, 0.018, 32, stop, (x, -0.027, sz + 0.01), (deg(90), 0, 0))
        A.sphere('stop-dome', 0.022, stop, (x, -0.036, sz + 0.01), scale=(1, 0.4, 1))
        txt = bpy.data.curves.new('t', 'FONT'); txt.body = t + ' STOP'; txt.size = 0.012; txt.align_x = 'CENTER'
        to = bpy.data.objects.new('t', txt); C.col.objects.link(to); to.location = (x, -0.019, sz - 0.035); to.rotation_euler = (deg(90), 0, 0)
        to.data.materials.append(C.simple('label-white', '#e8eaec', 0.5))
    # the engine-room vent low on the bulkhead
    box('vent', (0.18, 0.012, 0.06), (0.45, -0.006, -0.25), C.simple('vent', '#2a2c30', 0.5), 0.004)
    for k in range(5): box('vent-slot', (0.15, 0.004, 0.005), (0.45, -0.013, -0.27 + k * 0.01), C.simple('slot', '#0c0d0e', 0.6))
    K.camera((0.06, -0.72, 0.26), (0.03, 0, 0.1), 32)
    labels = [(tuple(on_bulk(pcx, pcz, pw, ph, (0.3, 0.7), -0.02)), 'fire alarm: engine room 95°C', 'red'),
              (tuple(on_bulk(pcx, pcz, pw, ph, (fa['fans'][0], fa['fans'][1] - 0.1), -0.02)), 'fans on: stop, shut the flaps'),
              (tuple(Vector((hx, -0.1, hz + 0.01))), 'release only when everyone is out', 'red'),
              ((sx, -0.04, sz + 0.04), 'stop engines and generator', 'blue')]
    note = 'Engine-room fire: shut the space'
    extra = {'lines': ['Kept shut for the hold time while you cool the bulkhead']}

elif FIG == 4:
    # flooding: the saloon sole awash, a floorboard up over the bilge, water pouring in at a broken seacock,
    # the electric pump's discharge hose running up and out
    interior(key=16, fill=5, at=(0, 0.3, 0.0), sky=0.06)
    sole = C.obj('sole', C.rbox('sole', (2.4, 2.0, 0.03), 0.002, 2), M['teak'], (0, 0.3, -0.015))
    KI.wall('bulk-back', -1.2, 1.2, -0.6, 1.4, 1.3, KI.joinery_mat())
    lw = bpy.data.meshes.new('bulk-side'); lw.from_pydata([(-1.2, -0.7, -0.6), (-1.2, 1.3, -0.6), (-1.2, 1.3, 1.4), (-1.2, -0.7, 1.4)], [], [(0, 1, 2, 3)]); C.obj('bulk-side', lw, KI.joinery_mat('j2'))
    # settee along the side
    box('settee', (0.55, 1.6, 0.42), (-0.92, 0.45, 0.21), C.simple('settee-base', '#6a3a1e', 0.5), 0.01)
    box('cushion', (0.5, 1.55, 0.1), (-0.92, 0.45, 0.47), C.fabric_mat('cushion', '#2b3a5a'), 0.03)
    # the bilge under the lifted board: a dark well, the seacock and its broken hose tail, the jet
    hole_c = Vector((0.15, 0.25, 0)); hw, hd = 0.5, 0.6
    sole.modifiers.new('cut', 'BOOLEAN')
    cutter = C.obj('cutter', C.rbox('cut', (hw, hd, 0.2), 0.0, 1), None, (hole_c.x, hole_c.y, 0)); cutter.hide_render = True; cutter.display_type = 'WIRE'
    sole.modifiers['cut'].object = cutter; sole.modifiers['cut'].operation = 'DIFFERENCE'
    well = C.simple('bilge', '#3a3530', 0.8)
    box('bilge', (hw, hd, 0.02), (hole_c.x, hole_c.y, -0.4), well)
    for s in (-1, 1):
        box('bilge-w', (0.02, hd, 0.4), (hole_c.x + s * hw / 2, hole_c.y, -0.2), well); box('bilge-w', (hw, 0.02, 0.4), (hole_c.x, hole_c.y + s * hd / 2, -0.2), well)
    board = box('floorboard', (hw - 0.01, hd - 0.01, 0.025), (hole_c.x + 0.42, hole_c.y + 0.05, 0.25), M['teak'], 0.002, (0, deg(-62), deg(8)))
    bronze = C.simple('bronze', '#8a6a3a', 0.35, 0.9)
    sc = hole_c + Vector((-0.1, 0.1, -0.33))
    C.cyl('seacock', 0.03, 0.03, 0.09, 24, bronze, tuple(sc))
    C.cyl('hose-tail', 0.017, 0.017, 0.07, 16, bronze, tuple(sc + Vector((0, 0, 0.075))))
    # the jet: white water boiling up out of the open hatch from the broken tail
    jm = C.simple('jet', '#eef4f4', 0.35)
    rnd = random.Random(7)
    for k in range(10):
        t = k / 9; A.sphere('jet', 0.02 + 0.012 * t, jm, tuple(sc + Vector((0, 0, 0.1 + 0.4 * t))), scale=(1, 1, 1.8))
    for k in range(90):                      # spray: drops thrown up and out from the column
        t = rnd.uniform(0.3, 1.0); a = rnd.uniform(0, 6.283); r = 0.18 * t * rnd.uniform(0.3, 1.0)
        A.sphere('drop', rnd.uniform(0.006, 0.016), jm, tuple(sc + Vector((math.cos(a) * r, math.sin(a) * r, 0.15 + 0.5 * t - 0.3 * (r / 0.18) ** 2))), seg=8)
    foam_patch((hole_c.x - 0.05, hole_c.y + 0.1), 0.05, 0.45, 0.6, z=0.062, scale=14.0, strength=0.9)
    # the water over the sole: clear, a little green, a gloss on top
    wm, wnt, wb, wout = C.new_mat('flood'); wnt.nodes.remove(wb)
    tp = wnt.nodes.new('ShaderNodeBsdfTransparent'); tp.inputs['Color'].default_value = (0.62, 0.78, 0.72, 1)
    gl = wnt.nodes.new('ShaderNodeBsdfGlossy'); gl.inputs['Roughness'].default_value = 0.04
    mx = wnt.nodes.new('ShaderNodeMixShader'); mx.inputs['Fac'].default_value = 0.22
    wnt.links.new(tp.outputs[0], mx.inputs[1]); wnt.links.new(gl.outputs[0], mx.inputs[2]); wnt.links.new(mx.outputs[0], wout.inputs['Surface'])
    wo = box('flood', (2.38, 1.98, 0.002), (0, 0.3, 0.06), wm); wo.visible_shadow = False
    # the pump hose: grey corrugated, from the bilge up over the settee and out
    hose = C.simple('hose', '#9aa0a5', 0.6)
    hp = [hole_c + Vector((0.15, -0.15, -0.35)), hole_c + Vector((0.1, -0.2, 0.1)), Vector((-0.4, -0.1, 0.3)), Vector((-0.75, 0.0, 0.62)), Vector((-1.15, 0.1, 0.9))]
    C.tube('pump-hose', C.catmull_centripetal([Vector(p) for p in hp], 12), 0.022, 16, 0.05, hose)
    box('pump', (0.12, 0.09, 0.08), hole_c + Vector((0.15, -0.15, -0.36)), C.simple('pump-body', '#1f2a3a', 0.45))
    for i in range(2):
        A.sphere('floater', 0.03, C.simple('float-item', ('#e8e2d0', '#c03020')[i], 0.6), (0.6 + i * 0.25, -0.15 + i * 0.3, 0.075), scale=(2.5, 1.2, 0.5))
    K.camera((0.7, -0.95, 1.45), (0.05, 0.3, 0.05), 32)
    labels = [(tuple(sc + Vector((0.03, 0, 0.8))), 'in: 650 L/min', 'red'), (tuple(Vector((-0.4, -0.1, 0.33))), 'pumps out: 250 L/min', 'blue'),
              ((0.55, 0.75, 0.07), 'net 400 L/min: 15 min left', 'red')]
    note = 'How long have you got?'
    extra = {'lines': ['6,000 L more and she is lost: alert and rafts now']}

elif FIG == 6:
    # night: the chart table under its red lamp; the DC panel on the bulkhead behind it, the battery monitor
    K.day_sky(sun_az=150, sun_el=-10, strength=0.005)
    table(1.1, 0.7)
    KI.wall('bulkhead', -0.6, 0.6, -0.05, 0.75, 0.35, KI.joinery_mat())
    pw, ph = 0.18, 0.27; pcx, pcz = -0.3, 0.25; by = 0.348
    box('dc-frame', (pw + 0.015, 0.012, ph + 0.015), (pcx, by, pcz), M['dark'], 0.004)
    A.quad('dcpanel', pw, ph, T('dcpanel'), (pcx, by - 0.0065, pcz), rot=(deg(90), 0, 0), emit=1.2)
    lay = json.load(open(os.path.join(ADIR, 'tex', 'dcpanel-layout.json'))); da = TA('dcpanel')
    for i, (name, on) in enumerate(lay['rows']):
        u, v = lay['x'], 1 - (lay['y0'] + i * lay['step'])
        p = Vector((pcx + (u - 0.5) * pw, by - 0.012, pcz + (v - 0.5) * ph))
        lev = box('toggle', (0.012, 0.022, 0.006), p + Vector((0, -0.006, 0.006 if on else -0.006)), C.simple('toggle-%d' % on, '#d8dadc' if on else '#5a5e64', 0.4, 0.6), 0.002)
        lev.rotation_euler = (deg(-35 if on else 35), 0, 0)
    mw, mh = 0.12, 0.08; mcx, mcz = 0.12, 0.33
    box('mon-frame', (mw + 0.014, 0.012, mh + 0.014), (mcx, by, mcz), M['dark'], 0.004)
    A.quad('battmon', mw, mh, T('battmon'), (mcx, by - 0.0065, mcz), rot=(deg(90), 0, 0), emit=1.6)
    # the VHF set on the bulkhead to the right, its display lit
    box('vhf', (0.19, 0.09, 0.075), (0.36, by - 0.045, 0.36), C.simple('vhf-body', '#17181a', 0.45), 0.006)
    A.quad('vhf-lcd', 0.07, 0.035, None, (0.33, by - 0.0905, 0.37), rot=(deg(90), 0, 0), emit=0.0, mat=A.glow_mat('vhf-glow', '#ffb340', 1.2))
    # the chart and the tools
    ch = A.sheet('chart', 0.62, 0.44, T('chartplot'), (0.0, 0.04, 0.0008), rotz=-3, curl=0.003); ca = TA('chartplot')
    pen((0.24, -0.25), 115, '#d9b300', 0.16)
    al = C.simple('dividers', '#c8ccd0', 0.25, 1.0)
    P._limb('div-a', (-0.18, -0.2, 0.004), (-0.08, -0.12, 0.012), 0.0025, al); P._limb('div-b', (-0.08, -0.12, 0.012), (-0.03, -0.24, 0.004), 0.0025, al)
    box('rule', (0.36, 0.06, 0.006), (0.08, 0.12, 0.004), C.simple('rule', '#cfe6e8', 0.15, coat=1.0), 0.002, (0, 0, deg(20)))
    # the red chart-table lamp and the panel glow
    ld = bpy.data.lights.new('red-lamp', 'SPOT'); ld.energy = 14.0; ld.color = (1.0, 0.22, 0.12); ld.spot_size = deg(80); ld.spot_blend = 0.6; ld.shadow_soft_size = 0.05
    lo = bpy.data.objects.new('red-lamp', ld); C.col.objects.link(lo); lo.location = (0.35, 0.15, 0.6); lo.rotation_euler = (Vector((0, -0.02, 0)) - Vector(lo.location)).to_track_quat('-Z', 'Y').to_euler()
    C.cyl('lamp-arm', 0.008, 0.008, 0.3, 12, M['dark'], (0.42, 0.25, 0.55), (deg(50), 0, deg(30)))
    C.cyl('lamp-head', 0.03, 0.025, 0.06, 24, M['dark'], (0.35, 0.15, 0.62))
    KI.area_light((0.0, -0.6, 0.8), (0, 0.2, 0.2), 4.0, 1.0, (0.7, 0.75, 1.0))
    K.camera((0.04, -0.8, 0.62), (-0.02, 0.18, 0.26), 32)
    labels = [(tuple(on_bulk(pcx, pcz, pw, ph, da['VHF'], by - 0.015) + Vector((-0.04, 0, 0))), 'on: nav lights and VHF only', 'green'),
              (tuple(Vector((mcx, by - 0.01, mcz + 0.04))), '11.9 V, alternator 0 A', 'red'),
              (tuple(A.on_sheet(ch, ca['track'][0], ca['track'][1], 0.004)), 'plot on paper: DR every hour')]
    note = 'No charging, 30 h to go'
    extra = {'lines': ['No spare belt: plotter, autopilot, fridge off']}; expo = -0.2

elif FIG == 10:
    # the grab bag on the cockpit seat, its beacons laid out beside it
    K.sea('calm', center=(0, 0)); K.day_sky(sun_az=210, sun_el=50)
    for o in bpy.data.objects:
        if o.name.startswith(('ocean', 'far-sea')): o.location.z -= 1.4
    C.obj('seat', C.rbox('seat', (2.6, 1.8, 0.04), 0.01, 2), M['teak'], (0, 0.3, -0.02))
    bag = C.fabric_mat('grabbag', '#e0620e', sheen='#ff9a50')
    box('bag', (0.45, 0.28, 0.2), (0.32, 0.25, 0.1), bag, 0.06)
    box('bag-top', (0.44, 0.06, 0.03), (0.32, 0.43, 0.19), bag, 0.02, (deg(-30), 0, 0))
    box('bag-strap', (0.04, 0.3, 0.005), (0.22, 0.25, 0.202), C.simple('strap', '#16171a', 0.7), 0.002)
    yel, blk = C.simple('epirb-yellow', '#e8a800', 0.4, coat=0.5), C.simple('epirb-black', '#16171a', 0.5)
    org = C.simple('sart-orange', '#e04a08', 0.4, coat=0.5)
    def lying(name, r, L, mat, at, rotz):
        return C.cyl(name, r, r, L, 32, mat, at, (0, deg(90), deg(rotz)))
    def label_on(name, path, at, rotz, w, h, r):
        return A.quad(name, w, h, path, (at[0], at[1], at[2] + r + 0.0015), rot=(0, 0, deg(rotz + 90)), rough=0.4)
    # EPIRB: yellow body, black collar and cap, antenna
    e0 = Vector((-0.3, 0.1, 0.06))
    lying('epirb', 0.06, 0.3, yel, e0, 15); label_on('epirb-label', T('epirb'), e0, 15, 0.09, 0.12, 0.06)
    lying('epirb-cap', 0.045, 0.06, blk, e0 + Vector((math.cos(deg(15)) * 0.18, math.sin(deg(15)) * 0.18, 0)), 15)
    P._limb('epirb-ant', e0 + Vector((math.cos(deg(15)) * 0.2, math.sin(deg(15)) * 0.2, 0)), e0 + Vector((math.cos(deg(15)) * 0.55, math.sin(deg(15)) * 0.55, -0.04)), 0.005, blk)
    # radar SART: orange, longer, its pole beside it
    s0 = Vector((-0.12, -0.2, 0.045))
    lying('sart', 0.045, 0.3, org, s0, -10); label_on('sart-label', T('sart'), s0, -10, 0.07, 0.093, 0.045)
    lying('sart-pole', 0.012, 0.5, C.simple('pole', '#d8d8d4', 0.4), s0 + Vector((0, -0.12, -0.03)), -10)
    # AIS-SART: yellow, slim
    a0 = Vector((0.2, -0.22, 0.035))
    lying('ais-sart', 0.035, 0.22, yel, a0, 25); label_on('ais-label', T('aissart'), a0, 25, 0.06, 0.08, 0.035)
    # handheld VHF and two hand flares
    hh = handheld((0.55, -0.1, 0.0), deg(-20))
    for i in range(2): lying('flare', 0.02, 0.25, C.simple('flare-red', '#c4161c', 0.5), Vector((0.62 + i * 0.05, 0.2, 0.02)), 80)
    K.camera((-0.05, -1.25, 1.05), (0.02, -0.02, 0.0), 32)
    labels = [(tuple(e0 + Vector((0, 0, 0.08))), 'EPIRB: registered to you', 'blue'),
              (tuple(A.shift_px(s0 + Vector((0, 0, 0.05)), -90, 0)), 'radar SART: shows on radar'),
              (tuple(A.shift_px(a0 + Vector((0, 0, 0.04)), 60, 110)), 'AIS-SART: on AIS screens'),
              ((0.55, -0.1, 0.16), 'handheld VHF')]
    note = 'In the grab bag'
    extra = {'lines': ['False alert: switch off, tell the MRCC']}

elif FIG == 12:
    # the deck log open on the chart table, a pen beside it
    interior(key=8, fill=2.5, at=(0, 0, 0))
    table(1.0, 0.7)
    box('log-cover', (0.62, 0.44, 0.012), (0.0, 0.0, 0.006), C.simple('log-cover', '#1f3355', 0.5), 0.004)
    lg = A.sheet('logbook', 0.6, 0.42, T('logbook'), (0.0, 0.0, 0.0125), rotz=0, curl=0.003); la = TA('logbook')
    pen((0.36, -0.12), 100)
    K.camera((-0.02, -0.4, 0.4), (-0.06, 0.0, 0.0), 40)
    labels = [(tuple(A.on_sheet(lg, la['struck'][0] + 0.03, la['struck'][1] - 0.045, 0.015)), '245°T struck once, 254°T beside it, initialled', 'blue')]
    note = 'Correcting the log'
    extra = {'lines': ['The old figure stays readable: never erase, never tear out a page']}

elif FIG == 13:
    # the policy schedule and the extension on the chart table
    interior(key=8, fill=2.5, at=(0, 0, 0))
    table(1.0, 0.7)
    po = A.sheet('policy', 0.21, 0.297, T('policy'), (-0.11, 0.0, 0.0008), rotz=-4, curl=0.002); pa = TA('policy')
    ex = A.sheet('extension', 0.21, 0.17, T('extension'), (0.14, -0.04, 0.0014), rotz=7, curl=0.002); ea = TA('extension')
    pen((0.2, -0.18), 120)
    K.camera((0.0, -0.4, 0.5), (0.01, 0.02, 0.0), 34)
    labels = [(tuple(A.on_sheet(po, 0.3, pa['Cruising limits'][1] - 0.05, 0.004)), 'limits: area and season'),
              (tuple(A.on_sheet(po, 0.62, pa['Warranties'][1] - 0.05, 0.004)), "warranties: skipper's certificate, use"),
              (tuple(A.on_sheet(ex, *ea['ext'], 0.004)), 'extension in writing', 'blue')]
    note = 'Before the passage: the policy'
    extra = {'lines': ['Private pleasure only: no paying guests']}

C.render(OUT, SAMPLES, SCALE, expo, labels, note, space='blender', arrows=arrows, extra=extra)
