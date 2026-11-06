# Renders the vhf-radio-operator call-script cards with the parametric radio (art_vhf.py --spec):
# the set on the card's channel, DSC screens where the card is a DSC call, the handset lifted for voice calls,
# the card's title and key line as the note. Run from the repo root with system Python.
import json, os, subprocess, sys
OUT = 'docs/design/figure-style/articles/vhf-radio-operator'
H = 'lifted'
CARDS = {
 ('calls', 1): dict(channel='16', handset=H, parts=[['ptt', 'press, then speak'], ['display', 'calling on 16']], note='Blue Star ×3 · this is Aurora ×3 · OVER'),
 ('calls', 4): dict(channel='72', handset=H, parts=[['display', 'agreed: channel 72']], note='Both move from 16 to 72, then talk'),
 ('calls', 5): dict(channel='09', power='LO', handset=H, parts=[['power', 'in port: low power']], note='Vega Marina, this is Aurora: asking for a berth'),
 ('distress', 2): dict(channel='16', cover='open', handset=H, parts=[['ptt', 'MAYDAY ×3, this is Nova ×3', 'red'], ['display', '16, high power']], note='Distress call · call sign and MMSI'),
 ('distress', 3): dict(channel='16', cover='open', handset=H, parts=[['ptt', 'position · holed · 4 persons', 'red']], note='Distress message: MAYDAY Nova · position · nature · help · persons'),
 ('distress', 5): dict(channel='16', lines=['DISTRESS ACK', 'FROM SPLIT RADIO', 'MMSI 002387100'], parts=[['display', 'acknowledged', 'blue']], note='Split Radio: RECEIVED MAYDAY'),
 ('distress', 7): dict(channel='16', handset=H, parts=[['ptt', 'MAYDAY RELAY ×3 · ALL STATIONS ×3', 'red']], note='MAYDAY RELAY: passing on a distress you saw'),
 ('dsc', 2): dict(channel='70', lines=['MMSI 238123450', 'MID 238 · CROATIA'], parts=[['display', 'MID: the flag state']], note='Reading an MMSI · zeros in front: coast station or group'),
 ('dsc', 3): dict(channel='70', lines=['INDIVIDUAL CALL', 'TO 238123450 NOVA', 'ROUTINE · CH 72'], parts=[['display', 'DSC individual call']], note='Acknowledged: both sets switch to 72'),
 ('dsc', 5): dict(channel='16', handset=H, parts=[['ptt', 'ALL STATIONS ×3 · cancel my alert', 'red']], note='Cancelling a false alert, on 16, at once'),
 ('sar', 2): dict(channel='16', handset=H, parts=[['ptt', 'MAYDAY Thalassa · RECEIVED MAYDAY']], note='Aura answers Thalassa, on 16'),
 ('urgency', 1): dict(channel='16', handset=H, parts=[['ptt', 'PAN-PAN ×3 · ALL STATIONS ×3', 'yellow']], note='Urgency: no immediate danger to life'),
 ('urgency', 3): dict(channel='16', handset=H, parts=[['ptt', 'SÉCURITÉ ×3 · ALL STATIONS ×3']], note='Safety call on 16, the warning on a working channel'),
 ('phonetic', 2): dict(channel='16', handset=H, parts=[['ptt', 'three eight degrees, zero four decimal six north']], note='Plotter 38°04.6′N 024°19.5′E, read out digit by digit'),
 ('phonetic', 4): dict(channel='72', handset=H, parts=[['ptt', '"Say again all after pontoon"']], note='A reply lost in noise: ask for the part you missed'),
}
only = sys.argv[1:]
for (art, n), spec in CARDS.items():
    if only and f'{art}/{n}' not in only: continue
    out = f'{OUT}/{art}/{n}-3d.jpg'
    r = subprocess.run(['blender', '--background', '--factory-startup', '--python', 'docs/design/blender/art_vhf.py', '--', '--spec', json.dumps(spec), '--out', out, '--samples', '192'], capture_output=True, text=True)
    ok = [l for l in r.stdout.splitlines() if 'render s' in l or 'Error' in l or 'Traceback' in l]
    subprocess.run(['python3', 'docs/design/blender/label.py', out], capture_output=True)
    print(art, n, ok[-1] if ok else r.stderr[-300:])
