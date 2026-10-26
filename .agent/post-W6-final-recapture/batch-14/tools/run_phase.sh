#!/bin/sh
# run_phase.sh <phase>: targets, capture, compare3 vs frozen (Vite on 5184 must already point at the phase API)
cd /c/Users/assef/Bineyame/AssetOpsV1-plan2/.agent/post-W6-final-recapture/batch-14
export AUDIT_REVISION=89a11477 ASSETOPS_CDP_PORT=9524
python tools/mk_targets.py $1 ../../../var/w502b_b14/manifest.json . 
node tools/capture-b14.mjs part-$1 targets-$1.json > logs/capture-$1.log 2>&1
tail -1 logs/capture-$1.log; grep FAIL logs/capture-$1.log | cut -c1-160
python ../tools/compare3.py ../../post-W6-audit/batch-14/part-$1/evidence.json part-$1/evidence.json > cmp-$1.json
python - <<PY
import json
r=json.load(open('cmp-$1.json'))
print('$1',len(r))
for x in r:
    if x.get('regress') or 'gap' in x: print(x['screen'],x['case'],x['width'],'R:',str(x.get('regress'))[:400],'F:',x.get('fix_signals'))
PY
