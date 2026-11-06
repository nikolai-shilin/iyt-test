#!/bin/zsh
# The Russian copies of an article's figures, then publish: labels through ru.json (label.py --ru), the schematics
# captured with ?lang=ru (needs the figure-style server on :5182), then publish_figs.py.
#   docs/design/blender/make_ru.sh vhf-radio-operator/dsc [...]
cd "$(dirname $0)/../../.."
for a in "$@"; do
  A=docs/design/figure-style/articles/$a
  [ -e $A/ru.json ] || { echo "$a: no ru.json"; continue; }
  python3 docs/design/blender/label.py --ru $A/<->-3d.jpg > /dev/null
  node docs/design/blender/capture_article.mjs $a --ru > /dev/null
  python3 docs/design/blender/publish_figs.py $a
done
