#!/bin/bash
cd /c/Users/assef/Bineyame/AssetOpsV1-review5/.agent/post-W6-W2-EV-recapture
export AUDIT_REVISION=$(git rev-parse --short HEAD) ASSETOPS_CDP_PORT=9561
pid=$(netstat -ano | grep ":18478 .*LISTEN" | awk '{print $5}' | head -1); [ -n "$pid" ] && taskkill //PID $pid //F > /dev/null; sleep 2
(bash r2/api.sh k > r2/logs/api-k.log 2>&1 &)
for i in $(seq 1 20); do [ "$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:18478/api/sites/COLD-LAB-001)" = 200 ] && break; sleep 2; done
node r2/tools/capture-b8.mjs r2/reps/part-cold-child r2/tools/targets-cold-child.json > r2/logs/cap-cold-child.log 2>&1; echo "cold exit=$? $(tail -n 1 r2/logs/cap-cold-child.log)"
