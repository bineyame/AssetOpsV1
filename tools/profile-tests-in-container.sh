#!/bin/sh
# PERF-01: sample-profile single tests inside the runner with py-spy (all threads, gateway subprocesses, idle time).
# Targets come one per line in ASSETOPS_PROFILE_TARGETS as "<name>|<node id>". Output: <run>/<name>.raw (collapsed
# stacks, 100 Hz) and <name>.log. Used only by tools/profile-tests-in-container.ps1.
set -eu
cd /workspace
out="/workspace/var/test-results/OPS-03/${OPS03_RUN_ID:?}"
[ -d "$out" ] || { echo "no run dir" >&2; exit 2; }
/opt/assetops-venv/bin/python -m pip install -q --target /tmp/pyspy py-spy==0.4.0
spy=/tmp/pyspy/bin/py-spy
echo "$ASSETOPS_PROFILE_TARGETS" | while IFS='|' read -r name node; do
  [ -n "$name" ] || continue
  case "$name" in *[!A-Za-z0-9_-]*) echo "bad name $name" >&2; exit 2 ;; esac
  start=$(date +%s)
  set +e
  # ASSETOPS_PROFILE_IDLE=1 also records blocked samples (the wall-time view); unset = on-CPU samples only.
  idle=""; [ "${ASSETOPS_PROFILE_IDLE:-}" = "1" ] && idle="--idle"
  "$spy" record --subprocesses --threads $idle --rate 100 --format raw -o "$out/$name.raw" -- \
    /opt/assetops-venv/bin/python -m pytest -p no:cacheprovider -q "$node" > "$out/$name.log" 2>&1
  rc=$?
  set -e
  echo "$name rc=$rc wall_s=$(( $(date +%s) - start ))" | tee -a "$out/profile-runs.txt"
done
