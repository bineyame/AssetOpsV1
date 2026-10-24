#!/bin/sh
# Capture-only loop: restarts the unmodified s602b `serve --case` for each test-scoped case, captures, stops it by PID.
cd /c/Users/assef/Bineyame/AssetOpsV1-review6
B=.agent/post-W6-audit/batch-05
declare_case() { :; }
for spec in "target_miss 6a9f1b95-e629-4cb6-b667-f449cc8397e0" "guardrail c1e32234-99e1-47b9-93d5-98563235cd27" "inconclusive 26849529-f152-425b-9f7a-49b6a7f32f98" "withdrawn 1d4ee6a2-f5a4-4fa2-8902-69c1e3104489"; do
  set -- $spec; c=$1; a=$2
  for port in 18502 18503; do pid=$(netstat -ano | grep "127.0.0.1:$port " | grep LISTENING | awk '{print $5}' | head -1); [ -n "$pid" ] && taskkill //PID $pid //F >/dev/null; done
  sleep 2
  .venv/Scripts/python.exe tools/s602b_verification_walkthrough.py --db assetops_s602b_audit --work var/s602b_audit serve --port 18502 --web-port 5185 --case $c > $B/logs/s602b-serve-$c.log 2>&1 &
  until grep -q "TEST-SCOPED examples\|exited\|did not answer" $B/logs/s602b-serve-$c.log; do sleep 2; done
  echo "[{\"id\":\"verification\",\"case\":\"$c\",\"url\":\"http://localhost:5185/sites/KOBO-001/actions/$a/verification\"}]" > $B/tools/targets-s602b-$c.json
  AUDIT_REVISION=73d538ab node $B/tools/capture-b5.mjs $B/part-s602b-cases/$c $B/tools/targets-s602b-$c.json > $B/logs/capture-s602b-$c.log 2>&1
  tail -1 $B/logs/capture-s602b-$c.log
done
for port in 18502 18503; do pid=$(netstat -ano | grep "127.0.0.1:$port " | grep LISTENING | awk '{print $5}' | head -1); [ -n "$pid" ] && taskkill //PID $pid //F >/dev/null; done
echo done
