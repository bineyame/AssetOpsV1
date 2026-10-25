#!/bin/bash
WT=/c/Users/assef/Bineyame/AssetOpsV1-review8
B=$WT/.agent/post-W6-W6-evidence/b19
cd $WT
export PYTHONPATH="C:/Users/assef/Bineyame/AssetOpsV1-review8;C:/Users/assef/Bineyame/AssetOpsV1-review8/backend;C:/Users/assef/Bineyame/AssetOpsV1-review8/contracts;C:/Users/assef/Bineyame/AssetOpsV1-review8/gateway;C:/Users/assef/Bineyame/AssetOpsV1-review8/simulator;C:/Users/assef/Bineyame/AssetOpsV1-review8/host"
PY=/c/Users/assef/Bineyame/AssetOpsV1/.venv/Scripts/python.exe
for pair in detail:detail hist:detail-history linked:detail-linked stress:stress maint:maintenance; do
  t=${pair%%:*}; fx=${pair#*:}
  $PY tools/w601_seed.py --db assetops_w601_w6r19${t}_test --fixture $fx --clock 2026-10-20T12:00:00Z > $B/seed/seed-$fx.json 2> $B/logs/seed-$fx.err
  echo "$fx rc=$?"
done
