#!/bin/sh
# Renders every figure-type scene to docs/design/figure-style/blender/types/ and draws its labels.
# Run from the repo root:  sh docs/design/blender/render_types.sh [samples]
set -e
B=docs/design/blender; O=docs/design/figure-style/blender/types; N=${1:-192}
mkdir -p $O
r() { script=$1; out=$2; shift 2; blender --background --factory-startup --python $B/$script -- --out $O/$out.jpg --samples $N "$@" 2>&1 | grep -E "render s|Error|Traceback" || true; }
r fig_sail.py fig-sail
r fig_buoy.py fig-buoy --kind lat-port
r fig_buoy.py fig-buoy-starboard --kind lat-stbd
r fig_buoy.py fig-cardinal-north --kind north
r fig_encounter.py fig-mob --kind mob
r fig_encounter.py fig-dayshape --kind dayshape
for k in tacks overtake headon channel anchored; do r fig_drone.py fig-drone-$k --kind $k; done
r fig_lights.py fig-lights
r fig_night_yacht.py fig-night-yacht
r fig_anchor.py fig-anchor
r fig_bay.py fig-bay
for k in radio panel compass; do r fig_instruments.py fig-$k --kind $k; done
python3 $B/label.py $(ls $O/fig-*.jpg | grep -v -- -labelled) > /dev/null
echo done
