#!/bin/sh
# W5-EV captures: one Vite (5197) per phase, one capture at a time. b16 + b17 target sets (b16 port rewritten) + extras.
cd "$(dirname "$0")/../../.." || exit 1
. .agent/post-W6-W5-EV/tools/env.sh
R=$(pwd); O=.agent/post-W6-W5-EV; B=.agent/post-W6-audit/batch-17
export AUDIT_REVISION=$(git rev-parse --short HEAD) ASSETOPS_CDP_PORT=9451
for ph in ${PHASES:-positive:18461 zero:18462 worstcase:18463 forbidden:18466 unavailable:18467 links:18461}; do
  p=${ph%%:*}; api=${ph##*:}
  $PY -c "
import json
t=[]
for d in ('t16','t17'):
    t+=json.load(open('$O/%s/targets-$p.json'%d))
if '$p'=='positive': t+=json.load(open('$O/targets-extra.json'))
s=json.dumps(t,indent=1).replace('127.0.0.1:5186','127.0.0.1:5197').replace('127.0.0.1:5187','127.0.0.1:5197'); open('$O/targets-run-$p.json','w').write(s); print('$p',len(t))"
  (cd frontend && ASSETOPS_API_PORT=$api exec node node_modules/vite/bin/vite.js --port 5197 --strictPort --host 127.0.0.1) > $O/logs/vite-$p.log 2>&1 &
  VP=$!
  until curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5197/ | grep -q 200; do sleep 2; done
  curl -s -o /dev/null http://127.0.0.1:5197/sites/EV-LAB-001/work; sleep 5
  (cd $B/tools && node capture-b17.mjs "$R/$O/cap-$p" "$R/$O/targets-run-$p.json") > $O/logs/cap-$p.log 2>&1; echo "exit $?" >> $O/logs/cap-$p.log
  powershell -c "Get-CimInstance Win32_Process | Where-Object { \$_.CommandLine -match 'vite.js --port 5197' } | ForEach-Object { Stop-Process -Id \$_.ProcessId -Force -ErrorAction SilentlyContinue }"
  sleep 3
done
echo "run_ev_all done"
