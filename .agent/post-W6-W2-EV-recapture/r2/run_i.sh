#!/bin/bash
# Interrupted phase at the current head: batch-08, batch-09, Q29 extras, shared-reach reps, then the inspect/probe.
cd /c/Users/assef/Bineyame/AssetOpsV1-review5/.agent/post-W6-W2-EV-recapture
export AUDIT_REVISION=$(git rev-parse --short HEAD) ASSETOPS_CDP_PORT=9561
T=r2/tools
node $T/capture-b8.mjs r2/batch-08/part-interrupted batch-08/tools/targets-interrupted.json > r2/logs/cap-b8-i.log 2>&1; echo b8 $?
node $T/capture-b9.mjs r2/batch-09/part-interrupted batch-09/tools/targets-interrupted.json > r2/logs/cap-b9-i.log 2>&1; echo b9 $?
node $T/capture-b8.mjs r2/extras/part-interrupted extras/tools/targets-extras.json > r2/logs/cap-x.log 2>&1; echo x $?
node $T/capture-b8.mjs r2/reps/part-ev-foundation-sld reps/tools/targets-ev-foundation-sld.json > r2/logs/cap-r.log 2>&1; echo r $?
node $T/inspect.mjs r2/probe/part-interrupted probe/tools/targets-interrupted.json > r2/logs/inspect-i.log 2>&1; echo probe $?
