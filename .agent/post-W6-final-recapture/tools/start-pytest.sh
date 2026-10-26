#!/bin/sh
# start-pytest.sh <test-file> <logfile> : runs an unmodified pytest-based serve harness from repo root (env vars passed through by the caller)
cd /c/Users/assef/Bineyame/AssetOpsV1-plan2
R=$(pwd -W)
export PYTHONPATH="$R\backend;$R\gateway;$R\simulator;$R\contracts;$R\host" PYTHONUNBUFFERED=1
exec .venv/Scripts/python.exe -m pytest "$1" -s -p no:cacheprovider > "$2" 2>&1
