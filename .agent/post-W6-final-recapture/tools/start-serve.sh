#!/bin/sh
# start-serve.sh <script.py> <logfile> [args...] : runs an unmodified producer (serve) from repo root with the standard PYTHONPATH
cd /c/Users/assef/Bineyame/AssetOpsV1-plan2
R=$(pwd -W)
S=$1; L=$2; shift 2
export PYTHONPATH="$R\backend;$R\backend\tests;$R\gateway;$R\simulator;$R\contracts;$R\host" PYTHONUNBUFFERED=1
exec .venv/Scripts/python.exe "$S" "$@" > "$L" 2>&1
