#!/bin/sh
# start-api.sh <db> <port> <logfile>
cd /c/Users/assef/Bineyame/AssetOpsV1-plan2
R=$(pwd -W)
export PYTHONPATH="$R\backend;$R\gateway;$R\simulator;$R\contracts;$R\host"
export DATABASE_URL="postgresql+psycopg://assetops:assetops-local-dev@127.0.0.1:55432/$1" PYTHONUNBUFFERED=1
cd host && exec ../.venv/Scripts/python.exe -m uvicorn lab_app:app --host 127.0.0.1 --port $2 > "../$3" 2>&1
