"""Test-impact selection for everyday slice checks (PERF-02, C / plan R4).

    python tools/select-tests.py [--base <rev>] [--head <rev>] [--files <path> ...] [--json]

Lists the backend test files a change can affect, and the frontend command for it. The full suite still runs at
every merge (backend/TESTING.md); this is for the slice check before review.

How. Every Python file of the repository's packages and test folders is parsed once (AST, standard library only)
for its imports, including imports inside functions. A backend test file is selected when the change touches it,
or when its transitive imports reach a changed Python file. Some changes cannot be traced through imports and
select the whole suite (ALWAYS_FULL): migrations, the test harness and conftest, shipped configuration and
scenario data, contract and test fixtures, the composition root, the runner and its compose files, dependency
manifests. A changed non-Python file elsewhere under a package (for example a YAML document read at run time)
also selects the whole suite, because the import graph cannot see who reads it. Documentation, .agent and
frontend-only changes select no backend test.

Frontend: changed files under frontend/ give `npx vitest related --run <files>` (vitest's own module graph);
a change to frontend config or test setup gives the full `npx vitest run`.
"""

from __future__ import annotations

import argparse
import ast
import fnmatch
import json
import subprocess
import sys
import warnings
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]  # tools/validate-test-selection.py points it at a historical tree
# Folders whose files are importable by their module path (the sys.path roots of the test runs).
ROOTS = ["backend", "contracts", "simulator", "gateway", "host", "field", "backend/tests", "host/tests",
         "gateway/tests"]
TEST_DIR = "backend/tests"
ALWAYS_FULL = [
    "backend/migrations/*", "backend/alembic.ini", "backend/pyproject.toml", "*/pyproject.toml",
    "backend/tests/conftest.py", "backend/tests/pg_harness.py", "backend/tests/setup_cache.py",
    "backend/tests/scenario_cache.py", "backend/tests/phase_attribution.py", "backend/tests/phase_timing.py",
    "backend/tests/fixtures/*", "host/conftest.py", "config/*", "contract-fixtures/*",
    "backend/assetops_backend/main.py", "backend/db/*", "docker-compose*.yml", "tools/run-backend-suite-in-container.*",
    ".gitattributes",
]
NO_BACKEND = ["*.md", ".agent/*", "Docs/*", "docs/*", "frontend/*", "tasks/*", ".ai/*", "AGENTS.md",
              "tools/*.mjs", "tools/check*.ps1", "tools/checks/*"]
FRONTEND_FULL = ["frontend/package.json", "frontend/package-lock.json", "frontend/vite.config.ts",
                 "frontend/tsconfig*.json", "frontend/src/test/*"]


def matches(path: str, patterns) -> bool:
    return any(fnmatch.fnmatch(path, p) for p in patterns)


def python_files() -> list[Path]:
    seen = set()
    out = []
    for root in ROOTS:
        base = REPO / root
        if not base.is_dir():
            continue
        for p in base.rglob("*.py"):
            if any(part in ("node_modules", ".venv", "__pycache__") for part in p.parts):
                continue
            if p not in seen:
                seen.add(p)
                out.append(p)
    return out


def module_names(path: Path) -> list[str]:
    """Every dotted name `path` is importable as, one per root it sits under."""
    names = []
    rel = path.relative_to(REPO).as_posix()
    for root in ROOTS:
        prefix = root + "/"
        if rel.startswith(prefix):
            sub = rel[len(prefix):-3]
            parts = sub.split("/")
            if parts[-1] == "__init__":
                parts = parts[:-1]
            if parts:
                names.append(".".join(parts))
    return names


def imports_of(path: Path, own: str) -> set[str]:
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError:
        return set()
    found = set()
    package = own.rsplit(".", 1)[0] if "." in own else ""
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                found.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            if node.level:
                parts = own.split(".")
                if path.name != "__init__.py":
                    parts = parts[:-1]
                parts = parts[: len(parts) - (node.level - 1)] if node.level > 1 else parts
                base = ".".join(parts + ([base] if base else []))
            found.add(base)
            for alias in node.names:
                found.add(f"{base}.{alias.name}" if base else alias.name)
    return found


def build_graph():
    files = python_files()
    by_module: dict[str, Path] = {}
    for p in files:
        for name in module_names(p):
            by_module.setdefault(name, p)
    edges: dict[Path, set[Path]] = {}
    for p in files:
        names = module_names(p)
        targets = set()
        for imported in imports_of(p, names[0] if names else p.stem):
            parts = imported.split(".")
            for i in range(len(parts), 0, -1):  # a.b.c, then the packages a.b and a (their __init__)
                hit = by_module.get(".".join(parts[:i]))
                if hit is not None:
                    targets.add(hit)
        edges[p] = targets
    return files, edges


def reaches(start: Path, changed: set[Path], edges, memo) -> bool:
    if start in memo:
        return memo[start]
    memo[start] = False  # cycles
    stack, seen = [start], {start}
    while stack:
        node = stack.pop()
        if node in changed:
            memo[start] = True
            return True
        for nxt in edges.get(node, ()):
            if nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    return False


def changed_files(base: str, head: str) -> list[str]:
    out = subprocess.run(["git", "diff", "--name-only", f"{base}...{head}"], cwd=REPO, capture_output=True,
                         text=True, check=True).stdout
    return [line.strip() for line in out.splitlines() if line.strip()]


def select(changed: list[str], graph=None) -> dict:
    files, edges = graph or build_graph()
    tests = sorted(p for p in files if p.parent == REPO / TEST_DIR and p.name.startswith("test_"))
    full_reasons = sorted(c for c in changed if matches(c, ALWAYS_FULL))
    python_changed = set()
    for c in changed:
        if c.endswith(".py") and not matches(c, NO_BACKEND):
            python_changed.add(REPO / c)
        elif not matches(c, NO_BACKEND) and not matches(c, ALWAYS_FULL) and \
                any(c.startswith(r + "/") for r in ("backend", "host", "gateway", "simulator", "contracts", "field")):
            full_reasons.append(f"{c} (run-time data the import graph cannot trace)")
    frontend = [c for c in changed if c.startswith("frontend/")]
    if full_reasons:
        selected = [t.relative_to(REPO).as_posix() for t in tests]
        mode = "full"
    else:
        memo: dict = {}
        selected = [t.relative_to(REPO).as_posix() for t in tests if reaches(t, python_changed, edges, memo)]
        mode = "selected" if selected else "none"
    if any(matches(c, FRONTEND_FULL) for c in frontend):
        frontend_command = "npx vitest run"
    elif frontend:
        frontend_command = "npx vitest related --run " + " ".join(c[len("frontend/"):] for c in frontend)
    else:
        frontend_command = None
    return {"mode": mode, "full_reasons": full_reasons, "changed": changed, "selected": selected,
            "test_files_total": len(tests), "frontend": frontend_command}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="main")
    parser.add_argument("--head", default="HEAD")
    parser.add_argument("--files", nargs="*")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    changed = args.files if args.files is not None else changed_files(args.base, args.head)
    result = select(changed)
    if args.json:
        print(json.dumps(result, indent=2))
        return
    print(f"mode: {result['mode']} ({len(result['selected'])} of {result['test_files_total']} backend test files)")
    for reason in result["full_reasons"][:20]:
        print(f"  full because: {reason}")
    if result["mode"] == "selected":
        print("backend: tools\\run-backend-suite-in-container.ps1 -Tier fast -Targets '" +
              " ".join(result["selected"]) + "'")
    if result["frontend"]:
        print(f"frontend (in frontend/): {result['frontend']}")


if __name__ == "__main__":
    sys.exit(main())
