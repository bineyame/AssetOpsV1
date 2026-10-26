#!/bin/sh
cd /c/Users/assef/Bineyame/AssetOpsV1-plan2
R=$(pwd -W)
export PYTHONPATH="$R\backend;$R\backend\tests;$R\gateway;$R\simulator;$R\contracts;$R\host" PYTHONUNBUFFERED=1
.venv/Scripts/python.exe .agent/W4-02-evidence/seed.py
