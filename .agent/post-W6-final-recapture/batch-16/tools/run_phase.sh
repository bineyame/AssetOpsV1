#!/bin/sh
# run_phase.sh <NN> <phase>: capture + compare3 vs frozen (Vite on 518<d> must already point at the phase API)
NN=$1; P=$2; D=${NN#1}
cd /c/Users/assef/Bineyame/AssetOpsV1-plan2/.agent/post-W6-final-recapture/batch-$NN
export AUDIT_REVISION=89a11477 ASSETOPS_CDP_PORT=952$D
node tools/capture-b$NN.mjs part-$P targets-$P.json > logs/capture-$P.log 2>&1
tail -1 logs/capture-$P.log; grep FAIL logs/capture-$P.log | cut -c1-160
python ../tools/compare3.py ../../post-W6-audit/batch-$NN/part-$P/evidence.json part-$P/evidence.json > cmp-$P.json
python - <<PY
import json
r=json.load(open('cmp-$P.json'))
print('$P',len(r))
for x in r:
    if x.get('regress') or 'gap' in x: print(x['screen'],x['case'],x['width'],'R:',str(x.get('regress'))[:400],'F:',x.get('fix_signals'))
PY
