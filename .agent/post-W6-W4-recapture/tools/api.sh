#!/bin/sh
# api.sh <db> <port> : host lab_app against a *_test DB (capture-only server).
cd "$(dirname "$0")/../../../host" || exit 1
DATABASE_URL="postgresql+psycopg://assetops:assetops-local-dev@127.0.0.1:55432/$1" PYTHONPATH="../backend;../contracts;../gateway;../simulator;." \
  exec /c/Users/assef/Bineyame/AssetOpsV1/.venv/Scripts/python.exe -m uvicorn lab_app:app --host 127.0.0.1 --port "$2"
