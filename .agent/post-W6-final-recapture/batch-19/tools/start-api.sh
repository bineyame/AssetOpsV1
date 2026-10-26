#!/bin/sh
# start-api.sh <port> <db_test> [app] [C2|C4] : plain uvicorn over an already-seeded *_test DB (or a reviewed TEST-ONLY composition); PID -> logs/api-pids.txt
PORT=$1; DB=$2; APP=${3:-assetops_backend.main:app}; SUB=$4
B='C:\Users\assef\Bineyame\AssetOpsV1-plan2\.agent\post-W6-final-recapture\batch-19'
R='C:\Users\assef\Bineyame\AssetOpsV1-plan2'
EXTRA=""; [ -n "$SUB" ] && EXTRA=",'--app-dir','$R\.agent\W6-01-evidence\$SUB'"
cd /c/Users/assef/Bineyame/AssetOpsV1-plan2/.agent/post-W6-final-recapture/batch-19
powershell.exe -NoProfile -Command "\$env:PYTHONPATH='$R;$R\backend;$R\contracts;$R\gateway;$R\simulator;$R\host'; \$env:DATABASE_URL='postgresql+psycopg://assetops:assetops-local-dev@127.0.0.1:55432/$DB'; \$env:ASSETOPS_WORK_CURSOR_KEY_HEX=-join ((1..32)|%{'{0:x2}' -f (Get-Random -Maximum 256)}); \$p=Start-Process -FilePath '$R\.venv\Scripts\python.exe' -ArgumentList '-m','uvicorn','$APP','--host','127.0.0.1','--port','$PORT','--log-level','warning'$EXTRA -WorkingDirectory '$R\backend' -RedirectStandardOutput '$B\logs\api-$PORT-$DB-${SUB:-prod}.log' -RedirectStandardError '$B\logs\api-$PORT-$DB-${SUB:-prod}.err' -PassThru -WindowStyle Hidden; \$p.Id" | sed "s/^/$PORT $DB $APP pid /" >> logs/api-pids.txt
tail -1 logs/api-pids.txt
for i in $(seq 1 60); do c=$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:$PORT/api/sites); [ "$c" != "000" ] && { echo "api up $c"; break; }; sleep 1; done
