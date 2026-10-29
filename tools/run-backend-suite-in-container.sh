#!/bin/sh
# OPS-03: the Linux side of tools/run-backend-suite-in-container.ps1 (the only public command).
# Runs inside the backend-test-runner service from /workspace (the bind-mounted worktree).
set -eu
cd /workspace

run_id="${OPS03_RUN_ID:-}"
case "$run_id" in
  ''|.*|*[!A-Za-z0-9_-]*) echo "OPS03_RUN_ID must be a simple directory name" >&2; exit 2 ;;
esac
out="/workspace/var/test-results/OPS-03/$run_id"
if [ ! -d "$out" ] || [ -e "$out/junit.xml" ]; then
  echo "run directory $out must exist and hold no earlier attempt" >&2
  exit 2
fi
if [ -z "${ASSETOPS_TEST_DATABASE_URL:-}" ]; then
  echo "ASSETOPS_TEST_DATABASE_URL is not set" >&2
  exit 2
fi

venv=/opt/assetops-venv
marker_file="$venv/.assetops-deps-marker"
if [ ! -x "$venv/bin/python" ]; then
  python -m venv "$venv"
fi
marker=$({
  echo "image=python:3.12.7-slim-bookworm"
  "$venv/bin/python" -c 'import sys; print(sys.version)'
  sha256sum backend/pyproject.toml contracts/pyproject.toml simulator/pyproject.toml gateway/pyproject.toml
} | sha256sum | cut -d' ' -f1)
if [ ! -f "$marker_file" ] || [ "$(cat "$marker_file")" != "$marker" ]; then
  echo "installing test dependencies (marker miss)"
  rm -f "$marker_file"
  "$venv/bin/python" -m pip install -q -e '/workspace/backend[dev]' -e /workspace/contracts \
    -e /workspace/simulator -e /workspace/gateway
  echo "$marker" > "$marker_file"
else
  echo "test dependencies cached (marker hit)"
fi

# PERF-01 R9: every AssetOps package must import from this bind-mounted worktree, never from a stale install.
/opt/assetops-venv/bin/python - <<'PY' || exit 2
import importlib, os, sys
bad = []
for name in ("assetops_backend", "assetops_contracts", "assetops_simulator", "assetops_gateway"):
    path = os.path.realpath(importlib.import_module(name).__file__)
    print(f"import origin {name} = {path}")
    if not path.startswith("/workspace/"):
        bad.append(name)
if bad:
    sys.exit(f"REFUSED: {', '.join(bad)} import from outside /workspace (stale editable install)")
PY

# PERF-01 phase 0: per-test set-up / call / teardown times (backend/tests/phase_timing.py).
# PERF-02 T3: the collected node IDs come from the run itself (conftest COLLECTED_ENV, after any tier filter);
# the separate collect-only pass (about 80 s) is gone.
export ASSETOPS_TEST_PHASE_TIMES="$out/phase-times.csv"
export ASSETOPS_TEST_COLLECTED="$out/collected.txt"
# PERF-02 T1/T2: build once, copy per test (backend/tests/setup_cache.py). Saved set-ups live in the named volume
# mounted at /opt/assetops-setup-cache and as assetops_sc_*_test databases on postgres-test, kept between runs.
case "${ASSETOPS_SETUP_CACHE_MODE:-on}" in
  on) export ASSETOPS_SETUP_CACHE_DIR=/opt/assetops-setup-cache ;;
  verify) export ASSETOPS_SETUP_CACHE_DIR=/opt/assetops-setup-cache-verify ASSETOPS_SETUP_CACHE_VERIFY=1 ;;
  off) export ASSETOPS_SETUP_CACHE=0 ;;
  *) echo "ASSETOPS_SETUP_CACHE_MODE must be on, verify or off" >&2; exit 2 ;;
esac
export ASSETOPS_SETUP_CACHE_LOG="$out/setup-cache"
if [ -n "${ASSETOPS_SETUP_CACHE_DIR:-}" ]; then
  /opt/assetops-venv/bin/python /workspace/tools/sweep-setup-cache.py "$ASSETOPS_SETUP_CACHE_DIR" || true
fi
if [ "${ASSETOPS_TEST_ATTRIBUTION_ON:-}" = "1" ]; then
  export ASSETOPS_TEST_ATTRIBUTION="$out/attribution"  # backend/tests/phase_attribution.py
fi

# A focused Docker run may name its own targets (paths or node IDs, space-separated); the default is the suite.
targets="${ASSETOPS_TEST_TARGETS:-backend/tests}"
case "$targets" in
  *[!A-Za-z0-9_/.:\ -]*) echo "ASSETOPS_TEST_TARGETS holds characters outside [A-Za-z0-9_/.: -]" >&2; exit 2 ;;
esac

# PERF-01 R5: the tier filter (-Tier fast -> "not slow", -Tier slow -> "slow"; empty = every test).
markexpr="${ASSETOPS_TEST_MARKEXPR:-}"
case "$markexpr" in
  ''|'not slow'|slow) ;;
  *) echo "ASSETOPS_TEST_MARKEXPR must be empty, 'not slow' or 'slow'" >&2; exit 2 ;;
esac
set -- $targets
if [ -n "$markexpr" ]; then set -- "$@" -m "$markexpr"; fi

date -u +%Y-%m-%dT%H:%M:%SZ > "$out/pytest-started"
start=$(date +%s)
set +e
{
  /opt/assetops-venv/bin/python -m pytest "$@" -n "${ASSETOPS_TEST_WORKERS:-4}" --dist loadfile --no-loadscope-reorder -q \
    --durations=30 --junitxml="/workspace/var/test-results/OPS-03/$run_id/junit.xml"
  echo $? > "$out/exit-code"
} 2>&1 | tee "$out/console.log"
set -e
end=$(date +%s)
rc=$(cat "$out/exit-code")
echo "wall_seconds=$((end - start)) exit_code=$rc" > "$out/wall-time.txt"
cat "$out/wall-time.txt"
exit "$rc"
