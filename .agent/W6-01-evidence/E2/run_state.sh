#!/usr/bin/env bash
# W6-01e E2 capture driver for one state (adapted from C3): start uvicorn on API_PORT against DB (APP defaults to the
# production composition `assetops_backend.main:app`; empty_scope uses the test-only `api_empty_scope:app`), run
# capture.mjs with any extra flags, stop uvicorn by its PID. Vite (VITE_PORT, ASSETOPS_API_PORT=API_PORT) runs
# separately for the whole set.
#   STATE=<state> DB=<db> APP_PATH=<path> [APP=api_empty_scope:app] [ROOT=..] [LINKS=..] bash run_state.sh [flags]
set -u
HERE=$(cd "$(dirname "$0")" && pwd -W)
WT=$(cd "$(dirname "$0")/../../.." && pwd -W)
PY=/c/Users/assef/Bineyame/AssetOpsV1-plan2/.venv/Scripts/python.exe
export PYTHONPATH="$WT;$WT/backend;$WT/contracts;$WT/gateway;$WT/simulator;$WT/host"
export DATABASE_URL="postgresql+psycopg://assetops:assetops-local-dev@127.0.0.1:55432/$DB"
export ASSETOPS_WORK_CURSOR_KEY_HEX=$("$PY" -c "import os;print(os.urandom(32).hex())")
APP=${APP:-assetops_backend.main:app}
(cd "$WT/backend" && exec "$PY" -m uvicorn "$APP" --app-dir "$HERE" --port "$API_PORT" --log-level warning) > "$HERE/uvicorn-$STATE.log" 2>&1 &
UV=$!
for i in $(seq 1 80); do curl -s -o /dev/null "http://127.0.0.1:$API_PORT/api/work/incidents" && break; sleep 0.5; done
MSYS2_ARG_CONV_EXCL="*" node "$HERE/capture.mjs" "$HERE/screenshots" "$STATE" "http://localhost:$VITE_PORT" "$APP_PATH" "$@"
kill $UV 2>/dev/null; sleep 1; taskkill //F //T //PID $UV >/dev/null 2>&1
exit 0
