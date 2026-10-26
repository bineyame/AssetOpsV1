#!/bin/sh
# Phase B remainder: probe "one", producer stock, stocked + late captures and probes. Logs in logs/.
cd "$(dirname "$0")/.." || exit 1
R=../..
PY=/c/Users/assef/Bineyame/AssetOpsV1/.venv/Scripts/python.exe
export AUDIT_REVISION=$(git rev-parse --short HEAD)
W="$PY tools/w403_mini_decisions_walkthrough.py --db w4rc_b_test --work var/w4rc_b"
export PYTHONPATH="backend;backend/tests;contracts;gateway;simulator;host"
(cd $R && $W capture --web http://127.0.0.1:5452 --phase positive) > logs/w403-capture-positive.log 2>&1; echo "exit $?" >> logs/w403-capture-positive.log
$PY tools/mk_targets_b13.py stocked && $PY tools/mk_probe_b.py stocked
ASSETOPS_CDP_PORT=9451 node tools/capture.mjs part-b-stocked tools/targets-stocked.json > logs/cap-b-stocked.log 2>&1; echo "exit $?" >> logs/cap-b-stocked.log
ASSETOPS_CDP_PORT=9451 node tools/inspect.mjs probe/part-b-stocked tools/targets-probe-b-stocked.json > logs/inspect-b-stocked.log 2>&1; echo "exit $?" >> logs/inspect-b-stocked.log
(cd $R && $W replay-late) > logs/w403-replay-late.log 2>&1; echo "exit $?" >> logs/w403-replay-late.log
(cd $R && $W capture --web http://127.0.0.1:5452 --phase late) > logs/w403-capture-late.log 2>&1; echo "exit $?" >> logs/w403-capture-late.log
$PY tools/mk_targets_b13.py late && $PY tools/mk_probe_b.py late
ASSETOPS_CDP_PORT=9451 node tools/capture.mjs part-b-late tools/targets-late.json > logs/cap-b-late.log 2>&1; echo "exit $?" >> logs/cap-b-late.log
ASSETOPS_CDP_PORT=9451 node tools/inspect.mjs probe/part-b-late tools/targets-probe-b-late.json > logs/inspect-b-late.log 2>&1; echo "exit $?" >> logs/inspect-b-late.log
echo "run_b done"
