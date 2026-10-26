#!/bin/sh
# Mini Work regression (R338 shared default): w403 walkthrough (unmodified), batch-13 "one" targets filtered to sitework-*.
cd "$(dirname "$0")/../../.." || exit 1
R=$(pwd); O=.agent/post-W6-W5-cold-recapture; W4=.agent/post-W6-W4-recapture
PY=/c/Users/assef/Bineyame/AssetOpsV1/.venv/Scripts/python.exe
export PYTHONPATH="backend;backend/tests;contracts;gateway;simulator;host" AUDIT_REVISION=$(git rev-parse --short HEAD) ASSETOPS_CDP_PORT=9451 W4RC_WORK=w5cm W4RC_WEB=http://127.0.0.1:5452
W="$PY tools/w403_mini_decisions_walkthrough.py --db w5cm_test --work var/w5cm"
$W drop > $O/logs/w403-drop0.log 2>&1
docker exec assetopsv1-postgres-1 createdb -U assetops w5cm_test
$W prepare > $O/logs/w403-prepare.log 2>&1 || { echo "prepare failed"; exit 1; }
$W serve > $O/logs/w403-serve.log 2>&1 &
(cd $W4/tools && ./vite.sh 9761 5452) > $O/logs/vite-mini.log 2>&1 &
until curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:9761/api/sites/MG-W402-001 | grep -q 200; do sleep 2; done
until curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5452/ | grep -q 200; do sleep 2; done
$W replay-positive > $O/logs/w403-replay-positive.log 2>&1
$PY $W4/tools/mk_targets_b13.py one > /dev/null
node -e "const fs=require('fs');const t=JSON.parse(fs.readFileSync('$W4/tools/targets-one.json')).filter(x=>x.id.startsWith('sitework'));fs.writeFileSync('$O/tools/targets-mini.json',JSON.stringify(t,null,1));console.log(t.length)"
git checkout -- $W4/tools/targets-one.json 2>/dev/null
curl -s -o /dev/null http://127.0.0.1:5452/sites/MG-W402-001/work; sleep 5
(cd $W4/tools && node capture.mjs "$R/$O/mini" "$R/$O/tools/targets-mini.json") > $O/logs/cap-mini.log 2>&1; echo "exit $?" >> $O/logs/cap-mini.log
echo "run_mini done"
