#!/bin/sh
# Serial capture runner: one Chrome at a time. Waits for the running part-a probe, then A captures, B "one" and w403.
cd "$(dirname "$0")/.." || exit 1
export AUDIT_REVISION=$(git rev-parse --short HEAD) ASSETOPS_CDP_PORT=9451
while tasklist //FI "PID eq 8136" | grep -q node; do sleep 5; done
rm -rf part-a-main part-b-one part-b-w403
node tools/capture.mjs part-a-main tools/targets-main.json > logs/cap-a.log 2>&1; echo "exit $?" >> logs/cap-a.log
node tools/capture.mjs part-b-one tools/targets-one.json > logs/cap-b-one.log 2>&1; echo "exit $?" >> logs/cap-b-one.log
node tools/capture.mjs part-b-w403 tools/targets-w403.json > logs/cap-b-w403.log 2>&1; echo "exit $?" >> logs/cap-b-w403.log
echo serial done
