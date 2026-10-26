#!/bin/sh
# EV Work regression (R338 shared default): batch-17 Work-tab targets, one Vite (5187), one phase at a time.
cd "$(dirname "$0")/../../.." || exit 1
R=$(pwd); O=.agent/post-W6-W5-cold-recapture; B=.agent/post-W6-audit/batch-17
PY=/c/Users/assef/Bineyame/AssetOpsV1/.venv/Scripts/python.exe
export AUDIT_REVISION=$(git rev-parse --short HEAD) ASSETOPS_CDP_PORT=9451
for ph in ${PHASES:-positive:18461 zero:18462 worstcase:18463 forbidden:18466 unavailable:18467}; do
  p=${ph%%:*}; api=${ph##*:}; mkdir -p $O/tools/t
  $PY $B/tools/mk_targets.py $p var/w504a_w5c/manifest.json $O/tools/t > /dev/null
  $PY -c "import json;f='$O/tools/t/targets-$p.json';t=[x for x in json.load(open(f)) if x['id'].startswith('ev-work')];json.dump(t,open('$O/tools/targets-ev-$p.json','w'),indent=1);print('$p',len(t))"
  (cd frontend && ASSETOPS_API_PORT=$api exec node node_modules/vite/bin/vite.js --port 5187 --strictPort --host 127.0.0.1) > $O/logs/vite-ev-$p.log 2>&1 &
  until curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5187/ | grep -q 200; do sleep 2; done
  curl -s -o /dev/null http://127.0.0.1:5187/sites/EV-LAB-001/work; sleep 5
  (cd $B/tools && node capture-b17.mjs "$R/$O/ev-$p" "$R/$O/tools/targets-ev-$p.json") > $O/logs/cap-ev-$p.log 2>&1; echo "exit $?" >> $O/logs/cap-ev-$p.log
  powershell -c "Get-CimInstance Win32_Process | Where-Object { \$_.CommandLine -match 'vite.js --port 5187' } | ForEach-Object { Stop-Process -Id \$_.ProcessId -Force }"
  sleep 3
done
echo "run_ev done"
