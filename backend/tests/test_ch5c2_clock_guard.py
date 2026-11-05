"""CH-5c2 C3 static clock guard (L0, no database; CH5c-R7 C3, CH5c2-R1 Q1/Q5).

Over the stored-composer module set (`config/chain/stored-composer-modules-v1.json`, recorded by the W6 CLI and
changed only by a reviewed diff):

- no Python wall-clock read (`datetime.now`, `datetime.utcnow`, `date.today`, `time.time`, called or passed as a
  default) outside `read_scope.py`;
- no SQL clock function (`now()`, `clock_timestamp()`, ... , the W6 listener's `CLOCK_SQL`) in a string literal
  outside the named allowlist below. Each allowlisted site is a read-instant capture (its value is wrapped in
  `read_scope.read_instant`) or a writer that a stored compose never runs, keyed by (module, enclosing function).

A planted `datetime.now()` and a planted unlisted `now()` each fail the scan (non-vacuity, in this file).
"""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BACKEND = REPO / "backend"
sys.path.insert(0, str(REPO / "tools"))

from chain_watermark_guard import CLOCK_SQL  # noqa: E402

MODULES_FILE = REPO / "config" / "chain" / "stored-composer-modules-v1.json"

#: (module, enclosing function qualname) -> reason. Read-instant captures (CH5c2-R1 Q1, pre-flight §3) and the
#: writers that live in a composer module but never run in a stored compose (CH5c-R7 C3 "not in compose").
SQL_CLOCK_ALLOWLIST: dict[tuple[str, str], str] = {}

#: Python clock reads allowed in composer modules: only the seam itself.
PY_CLOCK_MODULES = frozenset({"assetops_backend.read_scope"})

_PY_CLOCK_ATTRS = {("datetime", "now"), ("datetime", "utcnow"), ("date", "today"), ("time", "time")}


def listed_modules() -> list[str]:
    return json.loads(MODULES_FILE.read_text(encoding="utf-8"))["modules"]


def module_path(module: str) -> Path:
    base = BACKEND.joinpath(*module.split("."))
    return base / "__init__.py" if base.is_dir() else base.with_suffix(".py")


def _owner(node: ast.AST) -> str | None:
    """The trailing name of an attribute's value: `datetime` for `datetime.now` and `dt.datetime.now`."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def scan(source: str, module: str) -> tuple[list[str], list[tuple[str, str, int]]]:
    """(python clock reads as `module:line attr`, SQL clock literals as (module, qualname, line))."""
    tree = ast.parse(source)
    py: list[str] = []
    sql: list[tuple[str, str, int]] = []

    def visit(node: ast.AST, qual: str) -> None:
        for child in ast.iter_child_nodes(node):
            name = qual
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                name = f"{qual}.{child.name}" if qual else child.name
            if isinstance(child, ast.Attribute) and (_owner(child.value), child.attr) in _PY_CLOCK_ATTRS:
                py.append(f"{module}:{child.lineno} {_owner(child.value)}.{child.attr}")
            if isinstance(child, ast.Constant) and isinstance(child.value, str) and CLOCK_SQL.search(child.value):
                # Docstrings and comments-in-strings are prose, not SQL: only literals that look like a statement.
                if any(k in child.value.upper() for k in ("SELECT", "WHERE", "INSERT", "UPDATE", "VALUES", "SET ")):
                    sql.append((module, qual or "<module>", child.lineno))
            visit(child, name)

    visit(tree, "")
    return py, sql


def violations(modules: list[str], sources: dict[str, str] | None = None) -> list[str]:
    out: list[str] = []
    for module in modules:
        source = (sources or {}).get(module)
        if source is None:
            source = module_path(module).read_text(encoding="utf-8")
        py, sql = scan(source, module)
        if module not in PY_CLOCK_MODULES:
            out.extend(f"python clock {hit}" for hit in py)
        out.extend(f"sql clock {m}:{line} in {q}" for m, q, line in sql if (m, q) not in SQL_CLOCK_ALLOWLIST)
    return out


def test_module_list_is_recorded_and_resolves() -> None:
    modules = listed_modules()
    assert modules, "the W6 CLI module list is empty: record it with --modules-out and review the diff"
    assert "assetops_backend.read_scope" in modules
    missing = [m for m in modules if not module_path(m).is_file()]
    assert missing == []


def test_composer_modules_have_no_unaccounted_clock_read() -> None:
    assert violations(listed_modules()) == []


def test_allowlist_has_no_stale_entry() -> None:
    present = set()
    for module in listed_modules():
        present |= {(m, q) for m, q, _ in scan(module_path(module).read_text(encoding="utf-8"), module)[1]}
    assert sorted(set(SQL_CLOCK_ALLOWLIST) - present) == []


def test_planted_python_clock_fails() -> None:
    module = "assetops_backend.chain.response_store"
    planted = module_path(module).read_text(encoding="utf-8") + "\n\ndef _planted():\n    return datetime.now()\n"
    assert any("python clock" in v and "datetime.now" in v for v in violations([module], {module: planted}))
    default = "import datetime\nclass X:\n    def __init__(self, clock=None):\n        self.clock = clock or datetime.datetime.utcnow\n"
    assert violations(["m"], {"m": default}) == ["python clock m:4 datetime.utcnow"]


def test_planted_sql_clock_fails() -> None:
    planted = 'def f(c):\n    return c.execute("SELECT 1 FROM t WHERE t.at <= now()")\n'
    assert violations(["m"], {"m": planted}) == ["sql clock m:2 in f"]
