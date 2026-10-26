#!/bin/sh
# start-api.sh <port> <tag> [app]  : plain product API over assetops_w601_b18<tag>_test (or a given *_test db name), PID appended to logs/api-pids.txt
PORT=$1; TAG=$2; APP=${3:-assetops_backend.main:app}
case "$TAG" in *_test) DB=$TAG;; *) DB=assetops_w601_b18${TAG}_test;; esac
B='C:\Users\assef\Bineyame\AssetOpsV1-plan2\.agent\post-W6-final-recapture\batch-18'
R='C:\Users\assef\Bineyame\AssetOpsV1-plan2'
EXTRA=""
case "$APP" in api_empty*) EXTRA=",'--app-dir','$R\.agent\W6-01-evidence\E2'";; esac
powershell.exe -NoProfile -Command "\$env:PYTHONPATH='$R;$R\backend;$R\contracts;$R\gateway;$R\simulator;$R\host'; \$env:DATABASE_URL='postgresql+psycopg://assetops:assetops-local-dev@127.0.0.1:55432/$DB'; \$env:ASSETOPS_WORK_CURSOR_KEY_HEX=-join ((1..32)|%{'{0:x2}' -f (Get-Random -Maximum 256)}); \$p=Start-Process -FilePath '$R\.venv\Scripts\python.exe' -ArgumentList '-m','uvicorn','$APP','--host','127.0.0.1','--port','$PORT','--log-level','warning'$EXTRA -WorkingDirectory '$R\backend' -RedirectStandardOutput '$B\logs\api-$PORT-$TAG.log' -RedirectStandardError '$B\logs\api-$PORT-$TAG.err' -PassThru -WindowStyle Hidden; \$p.Id" | tee -a /dev/null | sed "s/^/$PORT $TAG pid /" >> logs/api-pids.txt
tail -1 logs/api-pids.txt
