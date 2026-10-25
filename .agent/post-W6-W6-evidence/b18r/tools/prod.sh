#!/bin/sh
# cap-b18: run an unmodified W502/W504 producer command. usage: prod.sh w502|w504 <subcommand...>
WT=/c/Users/assef/Bineyame/AssetOpsV1-review8
PY=/c/Users/assef/Bineyame/AssetOpsV1/.venv/Scripts/python.exe
W="C:\Users\assef\Bineyame\AssetOpsV1-review8"
export PYTHONPATH="$W;$W\backend;$W\contracts;$W\gateway;$W\simulator;$W\host"
export ASSETOPS_WORK_CURSOR_KEY_HEX=$(od -An -tx1 -N32 /dev/urandom | tr -d ' \n')
cd $WT
p=$1; shift
if [ "$p" = w504 ]; then export W504_API_PORT_BASE=18920; exec $PY tools/w504_ev_work_walkthrough.py --work var/w504a_w6r18r --tag w6r18r "$@"; fi
exec $PY tools/w502_cold_work_walkthrough.py --work var/w502b_w6r18r --tag w6r18r "$@"
