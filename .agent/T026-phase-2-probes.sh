#!/usr/bin/env bash
# T026 phase 2 guard probes: each introduces one violation, runs the guard
# meant to catch it, reports CAUGHT/MISSED, and restores the file from HEAD.
# Run from the repo root on a clean, committed tree.
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY="$ROOT/.venv/Scripts/python.exe"
cd "$ROOT/host"

probe() {
  local name="$1" file="$2" from="$3" to="$4" tests="$5"
  "$PY" - "$ROOT/$file" "$from" "$to" <<'EOF'
import sys
path, a, b = sys.argv[1:]
s = open(path, encoding="utf-8").read()
assert s.count(a) == 1, f"probe anchor not unique in {path}: {a!r}"
open(path, "w", encoding="utf-8", newline="\n").write(s.replace(a, b))
EOF
  if "$PY" -m pytest $tests -q -x -p no:cacheprovider >/dev/null 2>&1; then
    echo "MISSED  $name"
  else
    echo "CAUGHT  $name"
  fi
  git -C "$ROOT" checkout -- "$file"
}

probe "publication keyed at source time, not release" \
  backend/assetops_backend/simulator_lab_api.py \
  '"publications": "released_offset_minutes",' '"publications": "source_offset_minutes",' \
  "tests/test_lab_history_prefix.py"
probe "new family left unclassified on the wire" \
  backend/assetops_backend/simulator_lab_api.py \
  '    "records": "at_offset_minutes",
' '' \
  "tests/test_lab_history_prefix.py -k classified"
probe "still-held publication recorded early" \
  simulator/assetops_simulator/gateway/publish.py \
  'if window is None or window.end_offset_minutes > reached_offset_minutes:' 'if window is None:' \
  "tests/test_t026_history.py -k still_held"
probe "schema 2 no longer readable" \
  contracts/assetops_contracts/lab_history.py \
  'READABLE_LAB_HISTORY_SCHEMA_VERSIONS = (2, 3)' 'READABLE_LAB_HISTORY_SCHEMA_VERSIONS = (3,)' \
  "tests/test_t026_history.py -k schema_2_artifact"
probe "a held record publication is not recorded"   simulator/assetops_simulator/gateway/publish.py   '        if record.outcome != "REPORTED":
            continue
        note(' '        if True:
            continue
        note('   "tests/test_t026_history.py -k delayed_override"
git -C "$ROOT" status --short -- backend contracts simulator host
