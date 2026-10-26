#!/bin/sh
# seed-all.sh : unmodified tools/w601_seed.py per fixture against assetops_w601_b18<tag>_test
cd /c/Users/assef/Bineyame/AssetOpsV1-plan2
R=$(pwd -W)
export PYTHONPATH="$R;$R\backend;$R\contracts;$R\gateway;$R\simulator;$R\host"
O=.agent/post-W6-final-recapture/batch-18/seed
for spec in inc:incidents:2026-10-21T12:00:00Z maint:maintenance:2026-10-20T12:00:00Z prev:preventive:2026-10-20T12:00:00Z op:operational:2026-10-21T12:00:00Z zero:zero:2026-10-21T12:00:00Z hist:historical:2026-10-21T12:00:00Z stress:stress:2026-10-21T12:00:00Z linked:linked:2026-10-20T12:00:00Z; do
  tag=${spec%%:*}; rest=${spec#*:}; fx=${rest%%:*}; clk=${rest#*:}
  .venv/Scripts/python.exe tools/w601_seed.py --db assetops_w601_b18${tag}_test --fixture $fx --clock $clk > $O/seed-$tag.json 2> $O/seed-$tag.err && echo "seeded $tag" || echo "FAILED $tag"
done
