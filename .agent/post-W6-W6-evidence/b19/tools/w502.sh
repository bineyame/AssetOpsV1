#!/bin/bash
cd /c/Users/assef/Bineyame/AssetOpsV1-review8
export PYTHONPATH="C:/Users/assef/Bineyame/AssetOpsV1-review8;C:/Users/assef/Bineyame/AssetOpsV1-review8/backend;C:/Users/assef/Bineyame/AssetOpsV1-review8/contracts;C:/Users/assef/Bineyame/AssetOpsV1-review8/gateway;C:/Users/assef/Bineyame/AssetOpsV1-review8/simulator;C:/Users/assef/Bineyame/AssetOpsV1-review8/host"
export ASSETOPS_WORK_CURSOR_KEY_HEX=$(python -c "import os;print(os.urandom(32).hex())")
/c/Users/assef/Bineyame/AssetOpsV1/.venv/Scripts/python.exe tools/w502_cold_work_walkthrough.py --work var/w502b_w6r19 --tag w6r19 "$1"
