#!/bin/bash
# r3: refused cold cases at the current head. Seeds x (cold excursion) and b (cold backup-failed, for the start-refused-window Finding id).
cd /c/Users/assef/Bineyame/AssetOpsV1-ops04/.agent/post-W6-W2-cold-recapture
export AUDIT_REVISION=$(git rev-parse --short HEAD) ASSETOPS_CDP_PORT=9595
api() {
  pid=$(netstat -ano | grep ":18535 .*LISTEN" | awk '{print $5}' | head -1); [ -n "$pid" ] && taskkill //PID $pid //F > /dev/null; sleep 2
  (bash tools/api.sh $1 > logs/r4-api-$1.log 2>&1 &)
  for i in $(seq 1 30); do [ "$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:18535/api/sites/COLD-LAB-001)" = 200 ] && return 0; sleep 2; done; return 1
}
for s in x b; do api $s || { echo "api $s not up"; continue; }
  node tools/capture-cold.mjs r4-fix/part-$s tools/targets-r3$s.json > logs/r4-cap-$s.log 2>&1; echo "cap $s exit=$? $(tail -n 1 logs/r4-cap-$s.log)"; done
pid=$(netstat -ano | grep ":18535 .*LISTEN" | awk '{print $5}' | head -1); [ -n "$pid" ] && taskkill //PID $pid //F > /dev/null; echo done
