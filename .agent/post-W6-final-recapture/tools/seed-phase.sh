#!/bin/sh
# seed-phase.sh <db> <kind> <case> : runs the unmodified W2-F seed.py against a permitted *_test DB
cd /c/Users/assef/Bineyame/AssetOpsV1-plan2
R=$(pwd -W)
export PYTHONPATH="$R\backend;$R\gateway;$R\simulator;$R\contracts;$R\host;$R\backend\tests"
export ASSETOPS_TEST_DATABASE_URL="postgresql+psycopg://assetops:assetops-local-dev@127.0.0.1:55432/$1"
export ASSETOPS_TEST_TEMPLATE=0 PYTHONUNBUFFERED=1
.venv/Scripts/python.exe .agent/W2-F-evidence/seed.py "$2" "$3"
