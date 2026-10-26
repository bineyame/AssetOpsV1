#!/bin/sh
# Phase B end to end, serial: fresh walkthrough DB, serve, Vite B, captures + probes per phase, producer stock and late.
cd "$(dirname "$0")/../../.." || exit 1           # repo root
O=.agent/post-W6-W4-recapture
PY=/c/Users/assef/Bineyame/AssetOpsV1/.venv/Scripts/python.exe
export PYTHONPATH="backend;backend/tests;contracts;gateway;simulator;host" AUDIT_REVISION=$(git rev-parse --short HEAD) ASSETOPS_CDP_PORT=9451
W="$PY tools/w403_mini_decisions_walkthrough.py --db w4rc_b_test --work var/w4rc_b"
$W drop > $O/logs/w403-drop0.log 2>&1
docker exec assetopsv1-postgres-1 createdb -U assetops w4rc_b_test
$W prepare > $O/logs/w403-prepare.log 2>&1 || { echo "prepare failed"; exit 1; }
$W serve > $O/logs/w403-serve.log 2>&1 &
echo "serve pid $!"
(cd $O && ./tools/vite.sh 9761 5452 > logs/vite-b.log 2>&1) &
echo "vite sh pid $!"
until curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:9761/api/sites/MG-W402-001 | grep -q 200; do sleep 2; done
until curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5452/ | grep -q 200; do sleep 2; done
$W replay-positive > $O/logs/w403-replay-positive.log 2>&1
cd $O
rm -rf part-b-* probe/part-b-*
$PY tools/mk_targets_b13.py one && $PY tools/mk_probe_b.py one
cap() { node tools/capture.mjs part-b-$1 tools/targets-$1.json > logs/cap-b-$1.log 2>&1; echo "exit $?" >> logs/cap-b-$1.log; }
ins() { node tools/inspect.mjs probe/part-b-$1 tools/targets-probe-b-$1.json > logs/inspect-b-$1.log 2>&1; echo "exit $?" >> logs/inspect-b-$1.log; }
cap one; cap w403; ins one
(cd ../.. && $W capture --web http://127.0.0.1:5452 --phase positive) > logs/w403-capture-positive.log 2>&1; echo "exit $?" >> logs/w403-capture-positive.log
$PY tools/mk_targets_b13.py stocked && $PY tools/mk_probe_b.py stocked
cap stocked; ins stocked
(cd ../.. && $W replay-late) > logs/w403-replay-late.log 2>&1; echo "exit $?" >> logs/w403-replay-late.log
(cd ../.. && $W capture --web http://127.0.0.1:5452 --phase late) > logs/w403-capture-late.log 2>&1; echo "exit $?" >> logs/w403-capture-late.log
$PY tools/mk_targets_b13.py late && $PY tools/mk_probe_b.py late
cap late; ins late
echo "run_b_full done"
