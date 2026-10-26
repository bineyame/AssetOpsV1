#!/bin/sh
# w403.sh <mode> : unmodified W4-03 walkthrough against the permitted audit DB
cd /c/Users/assef/Bineyame/AssetOpsV1-plan2
R=$(pwd -W)
export PYTHONPATH="$R\backend;$R\backend\tests;$R\gateway;$R\simulator;$R\contracts;$R\host" PYTHONUNBUFFERED=1
exec .venv/Scripts/python.exe tools/w403_mini_decisions_walkthrough.py --db assetops_audit_b12_test --work var/w403_b12 "$@"
