#!/bin/sh
# one Vite at a time: mode:api:vite
cd "$(dirname "$0")/.." || exit 1
export AUDIT_REVISION=$(git rev-parse --short HEAD) ASSETOPS_CDP_PORT=9451
for ph in positive:8971:5471 forbidden:8976:5476 unavailable:8977:5477; do
  m=${ph%%:*}; r=${ph#*:}; api=${r%%:*}; vp=${r##*:}
  powershell -ExecutionPolicy Bypass -File tools/start.ps1 $api $vp logs/vite-cold-$m.pid logs/vite-cold-$m
  for i in $(seq 1 30); do curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:$vp/ | grep -q 200 && break; sleep 2; done
  node tools/shot.mjs cold-$m tools/targets-cold-$m.json > logs/cap-cold-$m.log 2>&1; echo "exit $?" >> logs/cap-cold-$m.log
  powershell -c "Stop-Process -Id (Get-Content logs/vite-cold-$m.pid) -Force -ErrorAction SilentlyContinue"
  sleep 2
done
echo run_cold done
