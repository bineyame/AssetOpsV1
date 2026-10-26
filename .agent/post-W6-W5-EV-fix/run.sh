#!/bin/sh
# usage: run.sh <ev|cold> <api-port>; one Vite on 5197, one capture, stop Vite by PID.
cd /c/Users/assef/Bineyame/AssetOpsV1-review10 || exit 1
O=.agent/post-W6-W5-EV-fix; B=.agent/post-W6-audit/batch-17; k=$1; api=$2
export AUDIT_REVISION=$(git rev-parse --short HEAD) ASSETOPS_CDP_PORT=9451
true
until curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5197/ | grep -q 200; do sleep 2; done
curl -s -o /dev/null http://127.0.0.1:5197/sites/EV-LAB-001/work; sleep 5
R=$(pwd)
(cd $B/tools && node capture-b17.mjs "$R/$O/cap-$k" "$R/$O/targets-$k.json") > $O/logs/cap-$k.log 2>&1; echo "exit $?" >> $O/logs/cap-$k.log
