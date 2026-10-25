#!/bin/bash
# $1 = db suffix. Runs the lab API on 18478 against assetops_w2evrc_$1_test.
cd /c/Users/assef/Bineyame/AssetOpsV1-review5/host
export DATABASE_URL=postgresql+psycopg://assetops:assetops-local-dev@127.0.0.1:55432/assetops_w2evrc_$1_test
export PYTHONPATH="../backend;../contracts;../gateway;../simulator;."
exec ../.venv/Scripts/python.exe -m uvicorn lab_app:app --port 18478
