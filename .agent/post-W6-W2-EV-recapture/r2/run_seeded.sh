#!/bin/bash
# Seeded phases: restart the lab API (port 18478, stopped by its PID) on each phase's *_test DB, then capture.
cd /c/Users/assef/Bineyame/AssetOpsV1-review5/.agent/post-W6-W2-EV-recapture
export AUDIT_REVISION=$(git rev-parse --short HEAD) ASSETOPS_CDP_PORT=9561
api() {
  pid=$(netstat -ano | grep ":18478 .*LISTEN" | awk '{print $5}' | head -1)
  [ -n "$pid" ] && taskkill //PID $pid //F > /dev/null
  sleep 2
  (bash r2/api.sh $1 > r2/logs/api-$1.log 2>&1 &)
  for i in $(seq 1 20); do [ "$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:18478/api/sites/EV-LAB-001)" = 200 ] && return 0; sleep 2; done
  echo "api $1 not up"; return 1
}
for spec in "$@"; do
  set -- $(echo $spec | tr ':' ' ')   # suffix phase batch
  api $1 || continue
  tool=r2/tools/capture-b8.mjs; [ "$3" = batch-09 ] && tool=r2/tools/capture-b9.mjs
  node $tool r2/$3/part-$2 $3/tools/targets-$2.json > r2/logs/cap-$3-$2.log 2>&1; echo "$3 $2 exit=$? $(tail -n 1 r2/logs/cap-$3-$2.log)"
done
