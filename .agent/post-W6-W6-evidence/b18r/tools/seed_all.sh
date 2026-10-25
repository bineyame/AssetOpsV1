#!/bin/sh
# cap-b18: seed the 8 W6-01 fixtures (producer unmodified) into assetops_w601_w6r18r<tag>_test with the batch-18 clocks.
WT=/c/Users/assef/Bineyame/AssetOpsV1-review8; B=$WT/.agent/post-W6-W6-evidence/b18r
PY=/c/Users/assef/Bineyame/AssetOpsV1/.venv/Scripts/python.exe
W="C:\Users\assef\Bineyame\AssetOpsV1-review8"
export PYTHONPATH="$W;$W\backend;$W\contracts;$W\gateway;$W\simulator;$W\host"
cd $WT
for spec in inc:incidents:2026-10-21 maint:maintenance:2026-10-20 prev:preventive:2026-10-20 op:operational:2026-10-21 zero:zero:2026-10-21 hist:historical:2026-10-21 stress:stress:2026-10-21 linked:linked:2026-10-20; do
  tag=${spec%%:*}; rest=${spec#*:}; fx=${rest%%:*}; day=${rest#*:}
  export ASSETOPS_WORK_CURSOR_KEY_HEX=$(od -An -tx1 -N32 /dev/urandom | tr -d ' \n')
  $PY tools/w601_seed.py --db assetops_w601_w6r18r${tag}_test --fixture $fx --clock ${day}T12:00:00Z > $B/seed/seed-$tag.json 2> $B/logs/seed-$tag.err
  echo "SEED $tag rc=$?"
done
