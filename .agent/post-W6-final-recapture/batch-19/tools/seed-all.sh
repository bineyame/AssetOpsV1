#!/bin/sh
# seed-all.sh : unmodified tools/w601_seed.py per fixture against assetops_w601_b19f<tag>_test (frozen fixture clock)
cd /c/Users/assef/Bineyame/AssetOpsV1-plan2
R=$(pwd -W)
export PYTHONPATH="$R;$R\backend;$R\contracts;$R\gateway;$R\simulator;$R\host"
O=.agent/post-W6-final-recapture/batch-19/seed
for spec in detail:detail hist:detail-history linked:detail-linked stress:stress maint:maintenance; do
  tag=${spec%%:*}; fx=${spec#*:}
  .venv/Scripts/python.exe tools/w601_seed.py --db assetops_w601_b19f${tag}_test --fixture $fx --clock 2026-10-20T12:00:00Z > $O/seed-$fx.json 2> $O/seed-$fx.err && echo "seeded $tag" || echo "FAILED $tag"
done
