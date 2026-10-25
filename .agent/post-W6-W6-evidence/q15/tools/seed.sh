#!/bin/sh
# cap-q15: seed with the unmodified W6 producer. Clocks as batch-18/19.
WT=/c/Users/assef/Bineyame/AssetOpsV1-review8
PY=/c/Users/assef/Bineyame/AssetOpsV1/.venv/Scripts/python.exe
export PYTHONPATH="$WT;$WT/backend;$WT/contracts;$WT/gateway;$WT/simulator;$WT/host"
Q=$WT/.agent/post-W6-W6-evidence/q15
cd $WT
for spec in inc:incidents:2026-10-21T12:00:00Z maint:maintenance:2026-10-20T12:00:00Z prev:preventive:2026-10-20T12:00:00Z op:operational:2026-10-21T12:00:00Z stress:stress:2026-10-21T12:00:00Z stressb:stress:2026-10-20T12:00:00Z detail:detail:2026-10-20T12:00:00Z dhist:detail-history:2026-10-20T12:00:00Z dlinked:detail-linked:2026-10-20T12:00:00Z; do
  tag=${spec%%:*}; rest=${spec#*:}; fx=${rest%%:*}; clk=${rest#*:}
  echo "SEED $tag $fx $clk"
  $PY tools/w601_seed.py --db assetops_w601_w6q15${tag}_test --fixture $fx --clock $clk > $Q/seed/seed-$tag.json 2> $Q/logs/seed-$tag.err; echo "rc=$?"
done
