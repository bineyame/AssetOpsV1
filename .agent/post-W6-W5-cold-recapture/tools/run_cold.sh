#!/bin/sh
# One serial run: for each producer mode API, one Vite (5185), batch-14 then batch-15 target sets, one Chrome at a time.
cd "$(dirname "$0")/../../.." || exit 1
R=$(pwd); O=.agent/post-W6-W5-cold-recapture; A=.agent/post-W6-audit
PY=/c/Users/assef/Bineyame/AssetOpsV1/.venv/Scripts/python.exe
M=var/w502b_w5c/manifest.json
export AUDIT_REVISION=$(git rev-parse --short HEAD) ASSETOPS_CDP_PORT=9451
for ph in ${PHASES:-positive:8971 worstcase:8972 pending:8973 stale:8974 unknown:8975 forbidden:8976 unavailable:8977 links:8971}; do
  p=${ph%%:*}; api=${ph##*:}
  mkdir -p $O/tools/t
  $PY $A/batch-14/tools/mk_targets.py $p $M $O/tools/t > /dev/null && sed -i 's/:5184/:5185/g' $O/tools/t/targets-$p.json && mv $O/tools/t/targets-$p.json $O/tools/targets-b14-$p.json
  [ "$p" != links ] && $PY $A/batch-15/tools/mk_targets.py $p $M $O/tools/t > /dev/null && mv $O/tools/t/targets-$p.json $O/tools/targets-b15-$p.json
  (cd frontend && ASSETOPS_API_PORT=$api exec node node_modules/vite/bin/vite.js --port 5185 --strictPort --host 127.0.0.1) > $O/logs/vite-$p.log 2>&1 &
  VP=$!
  until curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5185/api/sites | grep -q 200; do sleep 2; done
  (cd $A/batch-14/tools && node capture-b14.mjs "$R/$O/b14-$p" "$R/$O/tools/targets-b14-$p.json") > $O/logs/cap-b14-$p.log 2>&1; echo "exit $?" >> $O/logs/cap-b14-$p.log
  if [ "$p" != links ]; then
    (cd $A/batch-15/tools && node capture-b15.mjs "$R/$O/b15-$p" "$R/$O/tools/targets-b15-$p.json") > $O/logs/cap-b15-$p.log 2>&1; echo "exit $?" >> $O/logs/cap-b15-$p.log
  fi
  powershell -c "Stop-Process -Id $VP -Force -ErrorAction SilentlyContinue"
  powershell -c "Get-CimInstance Win32_Process | Where-Object { \$_.CommandLine -match 'vite.js --port 5185' } | ForEach-Object { Stop-Process -Id \$_.ProcessId -Force }"
  sleep 3
done
echo "run_cold done"
