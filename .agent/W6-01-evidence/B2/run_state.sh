#!/usr/bin/env bash
# W6-01b B2/B3 capture driver for one state: seed (unless SEED is empty), start uvicorn on API_PORT against DB, run
# capture.mjs, stop uvicorn. Vite (VITE_PORT, ASSETOPS_API_PORT=API_PORT) runs separately for the whole capture set.
#   STATE=<state> DB=<db> FIXTURE=<fixture|''> CLOCK=<clock> APP_PATH=<path> OUT=<dir> [APPEND=1] bash run_state.sh
set -u
OUT=$(cd "$OUT" && pwd -W)
WT=$(cd "$(dirname "$0")/../../.." && pwd -W)
PY=/c/Users/assef/Bineyame/AssetOpsV1-plan2/.venv/Scripts/python.exe
export PYTHONPATH="$WT;$WT/backend;$WT/contracts;$WT/gateway;$WT/simulator;$WT/host"
SEEDOUT="$OUT/seed-$STATE.json"
if [ -n "${FIXTURE:-}" ]; then
  "$PY" "$WT/tools/w601_seed.py" --db "$DB" --fixture "$FIXTURE" --clock "$CLOCK" > "$SEEDOUT" || { echo "seed failed"; exit 1; }
fi
export DATABASE_URL="postgresql+psycopg://assetops:assetops-local-dev@127.0.0.1:55432/$DB"
export ASSETOPS_WORK_CURSOR_KEY_HEX=$("$PY" -c "import os;print(os.urandom(32).hex())")
(cd "$WT/backend" && exec "$PY" -m uvicorn assetops_backend.main:app --port "$API_PORT" --log-level warning) > "$OUT/uvicorn-$STATE.log" 2>&1 &
UV=$!
for i in $(seq 1 80); do curl -s -o /dev/null "http://127.0.0.1:$API_PORT/api/work/incidents" && break; sleep 0.5; done
EXTRA=()
if [ -n "${APPEND:-}" ]; then EXTRA=(--append "C:/Users/assef/Bineyame/AssetOpsV1-plan2/.venv/Scripts/python.exe $WT/.agent/W6-01-evidence/B2/append_request.py $DB $CLOCK"); fi
MSYS2_ARG_CONV_EXCL="*" node "$WT/.agent/W6-01-evidence/B2/capture.mjs" "$OUT/screenshots" "$STATE" "http://localhost:$VITE_PORT" "$APP_PATH" "${EXTRA[@]}"
kill $UV 2>/dev/null; sleep 1; taskkill //F //T //PID $UV >/dev/null 2>&1
