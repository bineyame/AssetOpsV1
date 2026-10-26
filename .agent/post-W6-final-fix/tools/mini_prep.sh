#!/bin/sh
cd "$(dirname "$0")/../../.." || exit 1
O=.agent/post-W6-final-fix
PY=/c/Users/assef/Bineyame/AssetOpsV1/.venv/Scripts/python.exe
export PYTHONPATH="backend;backend/tests;contracts;gateway;simulator;host" AUDIT_REVISION=$(git rev-parse --short HEAD)
W="$PY tools/w403_mini_decisions_walkthrough.py --db pwfx_test --work var/pwfx"
$W drop > $O/logs/w403-drop0.log 2>&1
docker exec assetopsv1-postgres-1 createdb -U assetops pwfx_test
$W prepare > $O/logs/w403-prepare.log 2>&1 || { echo "prepare failed"; exit 1; }
echo prepared
