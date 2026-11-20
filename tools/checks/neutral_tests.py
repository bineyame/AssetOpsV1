"""T2 (DS1b R8; D-T2.1, D-T2.2): simulator/tests and contracts/tests run against this tree's own packages.

The shared VPS venv's editable installs point at the main checkout, so a worktree run that sets only `sys.path` can
silently test main in a child process (the D-1 class). This script puts the tree's package roots first on `sys.path`
and on `PYTHONPATH` (children inherit it), asserts the two neutral packages load from this tree, then runs pytest.

    python tools/checks/neutral_tests.py              # exit 0 only when both folders pass and meet their floors
    python tools/checks/neutral_tests.py --self-test  # the runner fails on a failing, an empty and a below-floor folder
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

for _module in ("pytest", "yaml"):
    try:
        __import__(_module)
    except ImportError:
        print(f"FAIL neutral tests: missing module {_module}")
        sys.exit(1)

import pytest  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
ROOTS = [ROOT / name for name in ("simulator", "contracts", "backend", "gateway", "host", "field")]
PACKAGES = ("assetops_simulator", "assetops_contracts")
# A new package folder with its own tests needs a line here (backend/TESTING.md).
DIRS = ("simulator/tests", "contracts/tests")
# Raise, never lower, only with a deliberate change.
MIN_PASSED = {"simulator/tests": 400, "contracts/tests": 1}


class _Counter:
    """Counts passed call-phase reports per directory. A package's own pyproject can move pytest's rootdir, so the
    directory is matched on the item's absolute path, not on the nodeid prefix."""

    def __init__(self, dirs, cwd) -> None:
        self.dirs = {d: (Path(cwd) / d).resolve() for d in dirs}
        self.passed = {d: 0 for d in dirs}
        self._where: dict[str, Path] = {}

    def pytest_collection_modifyitems(self, items) -> None:
        for item in items:
            self._where[item.nodeid] = Path(str(item.path)).resolve()

    def pytest_runtest_logreport(self, report) -> None:
        if report.when != "call" or not report.passed:
            return
        path = self._where.get(report.nodeid)
        for d, root in self.dirs.items():
            if path is not None and path.is_relative_to(root):
                self.passed[d] += 1


def run(dirs, floors, cwd) -> int:
    counter = _Counter(dirs, cwd)
    previous = Path.cwd()
    os.chdir(cwd)
    try:
        code = int(pytest.main([*dirs, "-q", "-p", "no:cacheprovider"], plugins=[counter]))
    finally:
        os.chdir(previous)
    if code == 5:
        print("FAIL neutral tests: no neutral tests collected")
        return 1
    if code != 0:
        return code
    for d in dirs:
        if counter.passed[d] < floors.get(d, 0):
            print(f"FAIL neutral tests: {d} passed {counter.passed[d]}, below {floors[d]}")
            return 1
    for d in dirs:
        print(f"neutral tests: {d} {counter.passed[d]} passed")
    return 0


def outside_message(name: str, where: Path, root: Path) -> str:
    return f"FAIL neutral tests: {name} loads from {where}, outside this tree {root}"


def set_paths() -> None:
    roots = [str(p) for p in ROOTS]
    sys.path[:0] = roots
    inherited = os.environ.get("PYTHONPATH")
    os.environ["PYTHONPATH"] = os.pathsep.join([*roots, *([inherited] if inherited else [])])
    os.environ.pop("ASSETOPS_TEST_DATABASE_URL", None)


def main() -> int:
    set_paths()
    import importlib
    for name in PACKAGES:
        where = Path(importlib.import_module(name).__file__ or "").resolve()
        if not where.is_relative_to(ROOT):
            print(outside_message(name, where, ROOT))
            return 1
    for d in DIRS:
        if not (ROOT / d).is_dir():
            print(f"FAIL neutral tests: missing {d}")
            return 1
    return run(DIRS, MIN_PASSED, ROOT)


def self_test() -> int:
    bad: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        for name, body in (("failing", "def test_x():\n    assert False\n"),
                           ("passing", "def test_x():\n    assert True\n")):
            (base / name).mkdir()
            (base / name / f"test_t2_{name}.py").write_text(body, encoding="utf-8")
        (base / "empty").mkdir()
        if run(("failing",), {}, base) != 1:
            bad.append("a failing test did not return 1")
        if run(("empty",), {}, base) != 1:
            bad.append("an empty folder did not return 1")
        if run(("passing",), {"passing": 2}, base) != 1:
            bad.append("a folder below its floor did not return 1")
    fake = Path("/elsewhere/simulator/assetops_simulator/__init__.py")
    expected = ("FAIL neutral tests: assetops_simulator loads from /elsewhere/simulator/assetops_simulator/__init__.py, "
                "outside this tree /tree")
    if outside_message("assetops_simulator", fake, Path("/tree")) != expected:
        bad.append("the import-root message has the wrong form")
    if bad:
        print("FAIL neutral tests self-test: " + "; ".join(bad))
        return 1
    print("neutral tests self-test: failing, empty, below-floor and import-root cases hold")
    return 0


if __name__ == "__main__":
    sys.exit(self_test() if "--self-test" in sys.argv[1:] else main())
