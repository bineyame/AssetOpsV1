#!/bin/bash
# usage: w504.sh <prepare|serve|attest|drop>
cd /c/Users/assef/Bineyame/AssetOpsV1-review8
export PYTHONPATH="C:/Users/assef/Bineyame/AssetOpsV1-review8;C:/Users/assef/Bineyame/AssetOpsV1-review8/backend;C:/Users/assef/Bineyame/AssetOpsV1-review8/contracts;C:/Users/assef/Bineyame/AssetOpsV1-review8/gateway;C:/Users/assef/Bineyame/AssetOpsV1-review8/simulator;C:/Users/assef/Bineyame/AssetOpsV1-review8/host"
export W504_API_PORT_BASE=18920
export ASSETOPS_WORK_CURSOR_KEY_HEX=$(python -c "import os;print(os.urandom(32).hex())")
/c/Users/assef/Bineyame/AssetOpsV1/.venv/Scripts/python.exe tools/w504_ev_work_walkthrough.py --work var/w504a_w6r18r --tag w6r18r "$1"
