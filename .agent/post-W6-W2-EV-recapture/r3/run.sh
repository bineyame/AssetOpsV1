#!/bin/bash
cd /c/Users/assef/Bineyame/AssetOpsV1-review5/.agent/post-W6-W2-EV-recapture
export AUDIT_REVISION=$(git rev-parse --short HEAD) ASSETOPS_CDP_PORT=9561
api() {
  pid=$(netstat -ano | grep ":18478 .*LISTEN" | awk '{print $5}' | head -1)
  [ -n "$pid" ] && taskkill //PID $pid //F > /dev/null
  sleep 2
  (bash r2/api.sh $1 > r3/logs/api-$1.log 2>&1 &)
  for i in $(seq 1 20); do [ "$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:18478/api/sites/EV-LAB-001)" = 200 ] && return 0; sleep 2; done; return 1
}
api i || exit 1
node r2/tools/capture-b8.mjs r3/batch-08/part-interrupted r3/tools/t8-i.json > r3/logs/cap-b8-i.log 2>&1; echo b8i $?
node r2/tools/capture-b9.mjs r3/batch-09/part-interrupted r3/tools/t9-i.json > r3/logs/cap-b9-i.log 2>&1; echo b9i $?
api m || exit 1
node r2/tools/capture-b8.mjs r3/batch-08/part-missing-meter r3/tools/t8-m.json > r3/logs/cap-b8-m.log 2>&1; echo b8m $?
