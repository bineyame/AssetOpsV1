"""OUT-A2/A3 golden proof (ruling A-Q6): every regenerated fixture equals its `main` blob once every `categories`
key is deleted. Run from the repository root with the backend venv:  python .agent/OUT-A-golden-equality.py

The S6 Action contract carries per-run UUIDs, digests and action codes (the writer stores a raw run; its test
compares through `s6_action_records.normalise`), so that fixture is compared after the same normaliser. The S6
verification contract is shape-compared by its test, and its writer stores raw `selection_seq` integers that follow
the run's database sequence state; any leaf that differs is listed, and only `selection_seq` leaves are tolerated
there ("equal except selection_seq").
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "backend" / "tests"), str(ROOT / "backend")]

from s6_action_records import normalise  # noqa: E402  (the contract test's own normaliser)

FIXTURES = {
    "backend/tests/fixtures/w3/w301-estate-golden.json": None,
    "backend/tests/fixtures/s6_action_api_contract.json": normalise,
    "backend/tests/fixtures/s6_verification_api_contract.json": "seq",
}
TOLERATED = {"seq": "selection_seq"}


def strip(value):
    if isinstance(value, dict):
        return {k: strip(v) for k, v in value.items() if k != "categories"}
    if isinstance(value, list):
        return [strip(v) for v in value]
    return value


def leaves(a, b, where="$"):
    if isinstance(a, dict) and isinstance(b, dict) and set(a) == set(b):
        for k in sorted(a):
            yield from leaves(a[k], b[k], f"{where}.{k}")
    elif isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        for i, (x, y) in enumerate(zip(a, b)):
            yield from leaves(x, y, f"{where}[{i}]")
    elif a != b:
        yield where, a, b


def count(value) -> int:
    if isinstance(value, dict):
        return ("categories" in value) + sum(count(v) for v in value.values())
    if isinstance(value, list):
        return sum(count(v) for v in value)
    return 0


failed = False
for path, norm in FIXTURES.items():
    old = json.loads(subprocess.run(["git", "show", f"main:{path}"], cwd=ROOT, check=True,
                                    capture_output=True).stdout.decode("utf-8"))
    new = json.loads((ROOT / path).read_text(encoding="utf-8"))
    a, b = strip(old), strip(new)
    how = "raw"
    if callable(norm):
        a, b, how = norm(a), norm(b), "after normalise"
    diffs = list(leaves(a, b))
    tolerated = TOLERATED.get(norm) if isinstance(norm, str) else None
    ok = not diffs or (tolerated is not None and all(w.endswith("." + tolerated) for w, _, _ in diffs))
    if diffs and ok:
        how = f"equal except {len(diffs)} {tolerated} leaves"
    failed |= not ok
    print(f"{'equal' if ok else 'DIFFERENT'} ({how}): {path}  categories keys main={count(old)} new={count(new)}")
    for w, x, y in diffs[:10]:
        print(f"    {w}: main={x!r} new={y!r}")
sys.exit(1 if failed else 0)
