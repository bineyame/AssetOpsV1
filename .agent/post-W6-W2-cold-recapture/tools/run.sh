#!/bin/bash
# For each DB suffix: restart the lab API (18535, stopped by PID) on assetops_w2coldrc_<s>_test, then capture targets-<s>.json.
#   bash tools/run.sh x n b
cd /c/Users/assef/Bineyame/AssetOpsV1-ops04/.agent/post-W6-W2-cold-recapture
export AUDIT_REVISION=$(git rev-parse --short HEAD) ASSETOPS_CDP_PORT=9595
api() {
  pid=$(netstat -ano | grep ":18535 .*LISTEN" | awk '{print $5}' | head -1)
  [ -n "$pid" ] && taskkill //PID $pid //F > /dev/null
  sleep 2
  (bash tools/api.sh $1 > logs/api-$1.log 2>&1 &)
  for i in $(seq 1 30); do [ "$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:18535/api/sites/$2)" = 200 ] && return 0; sleep 2; done
  echo "api $1 not up"; return 1
}
for s in "$@"; do
  site=COLD-LAB-001; [ "$s" = e ] && site=EV-LAB-001
  api $s $site || continue
  [ -f tools/targets-$s.json ] && { node tools/capture-cold.mjs part-$s tools/targets-$s.json > logs/cap-$s.log 2>&1; echo "cap $s exit=$? $(tail -n 1 logs/cap-$s.log)"; }
  [ -f tools/probe-$s.json ] && { node tools/inspect-cold.mjs probe/part-$s tools/probe-$s.json > logs/inspect-$s.log 2>&1; echo "probe $s exit=$? $(tail -n 1 logs/inspect-$s.log)"; }
done
