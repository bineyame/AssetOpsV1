#!/bin/sh
# run_phase.sh <phase> : capture one phase through Vite 5189 + compare3 vs frozen + scroller probe
P=$1
cd /c/Users/assef/Bineyame/AssetOpsV1-plan2/.agent/post-W6-final-recapture/batch-19
export AUDIT_REVISION=89a11477 ASSETOPS_CDP_PORT=9529
node tools/capture-b19.mjs part-$P tools/targets-$P.json > logs/capture-$P.log 2>&1
tail -1 logs/capture-$P.log; grep FAIL logs/capture-$P.log | cut -c1-200
python ../tools/compare3.py ../../post-W6-audit/batch-19/part-$P/evidence.json part-$P/evidence.json > cmp-$P.json
node tools/probe-scrollers.mjs tools/targets-$P.json logs/probe-scrollers-$P.json > logs/probe-$P.out 2>&1
grep -v " 0 unfocusable" logs/probe-$P.out | head
python - <<PY
import json
r=json.load(open('cmp-$P.json'))
print('$P',len(r))
for x in r:
    if x.get('regress') or 'gap' in x: print(x['screen'],x['case'],x['width'],'R:',str(x.get('regress'))[:300],'F:',x.get('fix_signals'))
PY
