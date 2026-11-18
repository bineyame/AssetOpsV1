"""PIPE-1 review M1: the first-party packages the Python guards import must load from this tree.

The shared VPS venv holds setuptools editable installs that point at the main checkout. In a worktree, a guard that
imports `assetops_backend` or `assetops_contracts` without this tree first on `PYTHONPATH` silently checks main's code
(the D-1 class). `tools/check-all.ps1` sets that `PYTHONPATH` for every guard; this probe fails if it stops holding.

    python tools/checks/import_root_probe.py      # exit 1 and the offending path when a package loads from elsewhere
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKAGES = ("assetops_backend", "assetops_contracts")


def main() -> int:
    bad: list[str] = []
    for name in PACKAGES:
        try:
            module = importlib.import_module(name)
        except Exception as exc:  # noqa: BLE001 - any import failure is a guard failure, never a skip
            bad.append(f"{name}: import failed: {exc!r}")
            continue
        where = Path(module.__file__ or "").resolve()
        if not where.is_relative_to(ROOT):
            bad.append(f"{name} loads from {where}, outside this tree {ROOT}; put this tree's backend and contracts "
                       f"first on PYTHONPATH (tools/check-all.ps1 does)")
    if bad:
        for line in bad:
            print(f"FAIL {line}")
        return 1
    print(f"First-party imports resolve inside this tree: {', '.join(PACKAGES)}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
