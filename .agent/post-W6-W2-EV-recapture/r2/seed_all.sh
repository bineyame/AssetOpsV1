#!/bin/bash
# Sequential unmodified seed.py runs, each into its own *_test DB (created here; dropped after capture).
cd /c/Users/assef/Bineyame/AssetOpsV1-review5
O=.agent/post-W6-W2-EV-recapture/r2/logs
export ASSETOPS_TEST_TEMPLATE=0 PYTHONPATH="backend;gateway;simulator;contracts;host"
for spec in "$@"; do
  set -- $(echo $spec | tr ':' ' ')
  db=assetops_w2evrc_$3_test
  docker exec assetopsv1-postgres-1 psql -U assetops -d postgres -Atc "create database $db" >/dev/null 2>&1
  export ASSETOPS_TEST_DATABASE_URL=postgresql+psycopg://assetops:assetops-local-dev@127.0.0.1:55432/$db
  s=$(date +%s)
  .venv/Scripts/python.exe .agent/W2-F-evidence/seed.py $1 $2 > $O/seed-$1-$2.log 2>&1
  echo "$1 $2 db=$db exit=$? secs=$(( $(date +%s)-s ))" | tee -a $O/seed.out
done
