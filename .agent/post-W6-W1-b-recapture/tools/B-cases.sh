#!/bin/sh
# Capture-only loop (agent B): restart the unmodified s602b `serve --case` per case (replay 18142, case 18143; Vite 5186
# already on ASSETOPS_API_PORT=18143), capture verification, stop the APIs by PID.
cd /c/Users/assef/Bineyame/AssetOpsV1-review7
R=.agent/post-W6-W1-b-recapture
export ASSETOPS_CDP_PORT=9526 AUDIT_REVISION=d960eeee
stop() { for port in 18142 18143; do pid=$(netstat -ano | grep "127.0.0.1:$port " | grep LISTENING | awk '{print $5}' | head -1); [ -n "$pid" ] && taskkill //PID $pid //T //F >/dev/null; done; }
for c in "$@"; do
  stop; sleep 3
  /c/Users/assef/Bineyame/AssetOpsV1/.venv/Scripts/python.exe tools/s602b_verification_walkthrough.py --db assetops_s602b_audit_w1brc --work var/s602b_w1brc serve --case $c --port 18142 --web-port 5186 > $R/batch-05/s602b-serve-$c.log 2>&1 &
  until grep -q "TEST-SCOPED examples\|exited\|did not answer" $R/batch-05/s602b-serve-$c.log; do sleep 2; done
  node .agent/post-W6-audit/batch-05/tools/capture-b5.mjs $R/batch-05/part-s602b-cases/$c $R/batch-05/targets-s602b-$c.json > $R/batch-05/capture-s602b-$c.log 2>&1
  echo "$c: $(tail -n 1 $R/batch-05/capture-s602b-$c.log)"; grep FAIL $R/batch-05/capture-s602b-$c.log | cut -c1-200
  (cd $R && node tools/B-checks.mjs batch-05/targets-s602b-$c.json batch-05/checks-s602b-$c.json | cut -c1-220)
  if [ "$c" = withdrawn ]; then
    sed 's#/verification"#/history"#; s#"verification"#"action-history"#; s#"withdrawn"#"x-withdrawn"#' $R/batch-05/targets-s602b-withdrawn.json > $R/batch-05/targets-extra-withdrawn-history.json
    node .agent/post-W6-audit/batch-05/tools/capture-b5.mjs $R/batch-05/extra-withdrawn-history $R/batch-05/targets-extra-withdrawn-history.json > $R/batch-05/capture-extra-withdrawn-history.log 2>&1
    echo "withdrawn history: $(tail -n 1 $R/batch-05/capture-extra-withdrawn-history.log)"
    (cd $R && node tools/B-checks.mjs batch-05/targets-extra-withdrawn-history.json batch-05/checks-extra-withdrawn-history.json | cut -c1-220)
    (cd $R && node probe/tools/B-viewer.mjs batch-05/viewer-withdrawn batch-05/targets-extra-withdrawn-history.json batch-05/viewer-withdrawn/viewer.json | cut -c1-500)
  fi
done
stop
echo done
