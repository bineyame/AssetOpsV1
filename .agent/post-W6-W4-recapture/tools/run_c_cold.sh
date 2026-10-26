#!/bin/sh
# Phase C cold: Work-tab targets only (batch-15 mk_targets), positive on API 8971, worstcase on 8972, one Vite (5185) at a time.
cd "$(dirname "$0")/../../.." || exit 1
R=$(pwd); O=.agent/post-W6-W4-recapture; B=.agent/post-W6-audit/batch-15
PY=/c/Users/assef/Bineyame/AssetOpsV1/.venv/Scripts/python.exe
export AUDIT_REVISION=$(git rev-parse --short HEAD) ASSETOPS_CDP_PORT=9451
for ph in ${PHASES:-positive:8971 worstcase:8972}; do
  p=${ph%%:*}; api=${ph##*:}
  $PY $B/tools/mk_targets.py $p var/w502b_w4rc/manifest.json $O/tools > /dev/null
  $PY -c "import json,sys;f='$O/tools/targets-$p.json';t=[x for x in json.load(open(f)) if x['id'].startswith('cold-work')];json.dump(t,open('$O/tools/targets-cold-$p.json','w'),indent=1);print('$p',len(t))"
  rm -f $O/tools/targets-$p.json
  (cd frontend && ASSETOPS_API_PORT=$api exec node node_modules/vite/bin/vite.js --port 5185 --strictPort --host 127.0.0.1) > $O/logs/vite-cold-$p.log 2>&1 &
  VP=$!
  until curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5185/api/sites | grep -q 200; do sleep 2; done
  (cd $B/tools && node capture-b15.mjs "$R/$O/part-cold-$p" "$R/$O/tools/targets-cold-$p.json") > $O/logs/cap-cold-$p.log 2>&1; echo "exit $?" >> $O/logs/cap-cold-$p.log
  powershell -c "Stop-Process -Id $VP -Force -ErrorAction SilentlyContinue"
  powershell -c "Get-CimInstance Win32_Process | Where-Object { \$_.CommandLine -match 'node_modules/vite/bin/vite.js --port 5185' } | ForEach-Object { Stop-Process -Id \$_.ProcessId -Force }"
  sleep 3
done
echo "run_c_cold done"
