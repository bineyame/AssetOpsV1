"""Check tools/select-tests.py against merged slices (PERF-02, C proof).

    python tools/validate-test-selection.py [--count 10] [--out <file.md>]

For each of the last N first-parent merges on main that changed backend, host, gateway, simulator, contracts or
field code, it rebuilds the import graph from that merge's own tree (git archive of the Python roots), selects the
tests for the merge's diff, and checks two things:
  1. every test file the slice itself changed is selected;
  2. every backend test file that the slice's .agent packets record as failing in a full-suite run (an added line
     naming test_*.py together with "fail") is selected, unless the slice selected the full suite anyway.
"""

from __future__ import annotations

import argparse
import importlib.util
import io
import re
import subprocess
import tarfile
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CODE_ROOTS = ("backend", "host", "gateway", "simulator", "contracts", "field")


def git(*args) -> str:
    return subprocess.run(["git", *args], cwd=REPO, capture_output=True, text=True, encoding="utf-8", errors="replace", check=True).stdout


def load_selector():
    spec = importlib.util.spec_from_file_location("select_tests", REPO / "tools" / "select-tests.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def recorded_failures(merge: str) -> set[str]:
    diff = git("diff", f"{merge}^1", merge, "--", ".agent")
    found = set()
    for line in diff.splitlines():
        if line.startswith("+") and re.search(r"fail", line, re.I):
            found.update(re.findall(r"(test_[a-z0-9_]+\.py)", line))
    return found


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=10)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    selector = load_selector()
    merges = git("log", "--first-parent", "--merges", "--format=%h %s", "main", "-60").splitlines()
    rows = []
    for line in merges:
        merge, subject = line.split(" ", 1)
        changed = [c for c in git("diff", "--name-only", f"{merge}^1", merge).splitlines() if c]
        if not any(c.startswith(tuple(r + "/" for r in CODE_ROOTS)) for c in changed):
            continue
        with tempfile.TemporaryDirectory() as tmp:
            present = [r for r in CODE_ROOTS if r in git("ls-tree", "--name-only", merge).split()]
            data = subprocess.run(["git", "archive", "--format=tar", merge, *present], cwd=REPO,
                                  capture_output=True, check=True).stdout
            tarfile.open(fileobj=io.BytesIO(data)).extractall(tmp, filter="data")
            selector.REPO = Path(tmp)
            result = selector.select(changed)
            backend_tests = {p.name for p in (Path(tmp) / "backend" / "tests").glob("test_*.py")}
        selected = {Path(s).name for s in result["selected"]}
        changed_tests = {Path(c).name for c in changed if c.startswith("backend/tests/test_") and c.endswith(".py")}
        missing_changed = sorted(t for t in changed_tests if t in backend_tests and t not in selected)
        failures = sorted(f for f in recorded_failures(merge) if f in backend_tests)
        missing_failures = [f for f in failures if f not in selected]
        rows.append({"merge": merge, "subject": subject[:90], "changed": len(changed), "mode": result["mode"],
                     "selected": len(result["selected"]), "total": result["test_files_total"],
                     "full_reasons": result["full_reasons"][:3], "changed_tests_missing": missing_changed,
                     "recorded_failures": failures, "failures_missing": missing_failures})
        if len(rows) == args.count:
            break
    lines = ["# Test-impact selection against merged slices", "",
             "| merge | slice | files | mode | selected / total | changed tests missed | recorded failures | missed |",
             "| --- | --- | ---: | --- | ---: | --- | --- | --- |"]
    for r in rows:
        lines.append(f"| {r['merge']} | {r['subject']} | {r['changed']} | {r['mode']} | {r['selected']} / {r['total']} | "
                     f"{', '.join(r['changed_tests_missing']) or '-'} | {', '.join(r['recorded_failures']) or '-'} | "
                     f"{', '.join(r['failures_missing']) or '-'} |")
    for r in rows:
        if r["full_reasons"]:
            lines.append(f"\n- {r['merge']} full because: {'; '.join(r['full_reasons'])}")
    text = "\n".join(lines) + "\n"
    if args.out:
        args.out.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
