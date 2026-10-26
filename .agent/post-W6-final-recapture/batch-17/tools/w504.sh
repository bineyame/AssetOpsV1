#!/bin/sh
cd /c/Users/assef/Bineyame/AssetOpsV1-plan2
export W504_API_PORT_BASE=18700
exec .venv/Scripts/python.exe tools/w504_ev_work_walkthrough.py --work var/w504a_b17 --tag b17 "$@"
