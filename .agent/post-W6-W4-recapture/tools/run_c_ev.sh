#!/bin/sh
# Phase C EV: Work-tab targets only (batch-17 mk_targets), positive on API 18461, Vite 5187.
cd "$(dirname "$0")/../../.." || exit 1
R=$(pwd); O=.agent/post-W6-W4-recapture; B=.agent/post-W6-audit/batch-17
PY=/c/Users/assef/Bineyame/AssetOpsV1/.venv/Scripts/python.exe
export AUDIT_REVISION=$(git rev-parse --short HEAD) ASSETOPS_CDP_PORT=9451
$PY $B/tools/mk_targets.py positive var/w504a_w4rc/manifest.json $O/tools > /dev/null
$PY -c "import json;f='$O/tools/targets-positive.json';t=[x for x in json.load(open(f)) if x['id'].startswith('ev-work')];json.dump(t,open('$O/tools/targets-ev-positive.json','w'),indent=1);print(len(t))"
rm -f $O/tools/targets-positive.json
(cd frontend && ASSETOPS_API_PORT=18461 exec node node_modules/vite/bin/vite.js --port 5187 --strictPort --host 127.0.0.1) > $O/logs/vite-ev.log 2>&1 &
until curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5187/api/sites | grep -q 200; do sleep 2; done
(cd $B/tools && node capture-b17.mjs "$R/$O/part-ev-positive" "$R/$O/tools/targets-ev-positive.json") > $O/logs/cap-ev-positive.log 2>&1; echo "exit $?" >> $O/logs/cap-ev-positive.log
powershell -c "Get-CimInstance Win32_Process | Where-Object { \$_.CommandLine -match 'vite.js --port 5187' } | ForEach-Object { Stop-Process -Id \$_.ProcessId -Force }"
echo "run_c_ev done"
