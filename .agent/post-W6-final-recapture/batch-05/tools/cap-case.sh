#!/bin/sh
# cap-case.sh <case> <actionId>: capture-only for one test-scoped case (Vite 5185 -> API 18503 already running)
cd /c/Users/assef/Bineyame/AssetOpsV1-plan2; B=.agent/post-W6-final-recapture/batch-05
echo "[{\"id\":\"verification\",\"case\":\"$1\",\"url\":\"http://localhost:5185/sites/KOBO-001/actions/$2/verification\"}]" > $B/tools/targets-s602b-$1.json
AUDIT_REVISION=89a11477 node $B/tools/capture-b5.mjs $B/s602b-case-$1 $B/tools/targets-s602b-$1.json > $B/logs/capture-s602b-$1.log 2>&1
tail -1 $B/logs/capture-s602b-$1.log; grep -c FAIL $B/logs/capture-s602b-$1.log
