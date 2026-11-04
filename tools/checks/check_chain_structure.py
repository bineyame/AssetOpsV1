"""Structural AST guard for the outcome chain (CH-5a2a, build sheet CH-5a §B8, ruling CH5a2-R R6; design §13).

Outside `backend/assetops_backend/chain/`:

(a) no module imports both a Finding store or index (`analytics.adapters.postgres_finding_store`,
    `analytics.finding_index`) and an Action store or index (`actions.*store*`, `actions.site_index`): the
    Finding-to-Action join belongs to ChainReader alone;
(b) no call to the replaced day and window functions (`REPLACED_CALLS`), and no definition of a function the
    design §5.1 "Replaces" column names (`REPLACED_DEFS`).

Today's violations live in `fixtures/chain_structure_baseline.json`, each with its owner slice. The baseline may
only shrink: a violation missing from it fails, and a baseline entry that no longer occurs fails too (delete it).

Usage: `python tools/checks/check_chain_structure.py [--root DIR] [--baseline FILE]`. Prints one line per failure
and exits 1 on any failure; prints nothing and exits 0 when clean.
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PACKAGE = "assetops_backend"
CHAIN = "chain"
BASELINE = Path(__file__).resolve().parent / "fixtures" / "chain_structure_baseline.json"

FINDING_MODULES = (f"{PACKAGE}.analytics.adapters.postgres_finding_store", f"{PACKAGE}.analytics.finding_index")
ACTION_PREFIX = f"{PACKAGE}.actions."
ACTION_INDEX = f"{PACKAGE}.actions.site_index"
#: §B8 (b): the replaced day and window functions; a call outside `chain/` re-derives a chain rule.
REPLACED_CALLS = frozenset({"_days_block", "_productive_month", "mini_summary_day"})
#: Design §5.1 "Replaces" column: the functions ChainReader and SnapshotBuilder replace.
REPLACED_DEFS = frozenset({"_days_block", "_productive_month", "mini_summary_day", "latest_window",
                           "refresh_chain", "linked_actions", "_action_for"})


def _is_finding(module: str) -> bool:
    return any(module == m or module.startswith(m + ".") for m in FINDING_MODULES)


def _is_action(module: str) -> bool:
    if module == ACTION_INDEX or module.startswith(ACTION_INDEX + "."):
        return True
    return module.startswith(ACTION_PREFIX) and "store" in module[len(ACTION_PREFIX):]


def _imported(tree: ast.Module, dotted: str) -> set[str]:
    """Every module name an import statement can bind: `import a.b`, `from a import b` (both `a` and `a.b`), and a
    relative import resolved against the file's own package."""
    out: set[str] = set()
    package = dotted.rsplit(".", 1)[0]
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            out.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            if node.level:
                parts = package.split(".")
                parts = parts[: len(parts) - (node.level - 1)] if node.level > 1 else parts
                base = ".".join([*parts, *([base] if base else [])])
            out.add(base)
            out.update(f"{base}.{alias.name}" for alias in node.names)
    return out


def _called(node: ast.Call) -> str | None:
    f = node.func
    if isinstance(f, ast.Name):
        return f.id
    if isinstance(f, ast.Attribute):
        return f.attr
    return None


def violations(root: Path) -> list[dict[str, str]]:
    """Every rule (a)/(b) violation under `root/assetops_backend`, outside `chain/`, sorted."""
    base = root / PACKAGE
    out: list[dict[str, str]] = []
    for path in sorted(base.rglob("*.py")):
        rel = path.relative_to(root).as_posix()
        if path.relative_to(base).parts[0] == CHAIN or "__pycache__" in path.parts:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=rel)
        dotted = rel[: -len(".py")].replace("/", ".")
        mods = _imported(tree, dotted)
        finding = sorted(m for m in mods if _is_finding(m))
        action = sorted(m for m in mods if _is_action(m))
        if finding and action:
            out.append({"rule": "a", "path": rel, "name": f"{finding[0]} + {action[0]}"})
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and _called(node) in REPLACED_CALLS:
                out.append({"rule": "b-call", "path": rel, "name": str(_called(node))})
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in REPLACED_DEFS:
                out.append({"rule": "b-def", "path": rel, "name": node.name})
    unique = {(v["rule"], v["path"], v["name"]): v for v in out}
    return [unique[k] for k in sorted(unique)]


def check(root: Path, baseline_path: Path) -> list[str]:
    try:
        baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        return [f"chain structure baseline {baseline_path} unreadable: {error}"]
    failures: list[str] = []
    allowed: set[tuple[str, str, str]] = set()
    for entry in baseline.get("entries", []):
        key = (entry.get("rule"), entry.get("path"), entry.get("name"))
        if not entry.get("owner"):
            failures.append(f"chain structure baseline entry {key} names no owner slice")
        allowed.add(key)  # type: ignore[arg-type]
    found = {(v["rule"], v["path"], v["name"]) for v in violations(root)}
    for rule, path, name in sorted(found - allowed):
        what = {"a": "imports both a Finding store/index and an Action store/index",
                "b-call": "calls a replaced day/window function", "b-def": "defines a function ChainReader replaces"}
        failures.append(f"{path}: {what[rule]} ({name}); outside backend/assetops_backend/chain/ (design §13)")
    for rule, path, name in sorted(allowed - found):
        failures.append(f"chain structure baseline entry ({rule}, {path}, {name}) no longer occurs; delete it "
                        f"(the baseline only shrinks)")
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--root", type=Path, default=REPO / "backend")
    parser.add_argument("--baseline", type=Path, default=BASELINE)
    parser.add_argument("--list", action="store_true", help="print today's violations as JSON and exit 0")
    args = parser.parse_args(argv)
    if args.list:
        print(json.dumps(violations(args.root), indent=2))
        return 0
    failures = check(args.root, args.baseline)
    for line in failures:
        print(line)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
