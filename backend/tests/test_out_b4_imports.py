"""OUT-B4 (§B.3 "Dependency direction"): no module in `site_outcomes/` except `composition.py` imports an
`*.adapters` module or another package's `composition`. `tools/checks/` is not touched (§0.2), so this AST test is
the guard. The B2 review asked the B4 review to judge against this test, not the broader §B.3 prose."""
from __future__ import annotations

import ast
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1] / "assetops_backend" / "site_outcomes"
ALLOWED = {"composition.py"}


def _imports(tree: ast.AST) -> list[str]:
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names += [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            names.append(base)
            names += [f"{base}.{a.name}" for a in node.names]  # `from x import adapters` / `composition`
        elif isinstance(node, ast.Call) and getattr(node.func, "attr", getattr(node.func, "id", None)) in (
                "import_module", "__import__") and node.args and isinstance(node.args[0], ast.Constant):
            names.append(str(node.args[0].value))
    return names


def _bad(name: str) -> bool:
    parts = name.split(".")
    return "adapters" in parts or ("composition" in parts and parts[:2] != ["assetops_backend", "site_outcomes"])


def violations(path: Path) -> list[str]:
    return [n for n in _imports(ast.parse(path.read_text(encoding="utf-8"))) if _bad(n)]


def test_package_is_scanned() -> None:
    modules = sorted(p.name for p in PACKAGE.glob("*.py"))
    assert {"board.py", "mini.py", "cold.py", "ev.py", "read.py", "composition.py"} <= set(modules), modules


def test_only_composition_imports_adapters_or_other_compositions() -> None:
    found = {p.name: violations(p) for p in sorted(PACKAGE.glob("*.py")) if p.name not in ALLOWED}
    assert {k: v for k, v in found.items() if v} == {}


def test_the_rule_rejects_each_form(tmp_path: Path) -> None:
    """Non-vacuous: each import form the rule names is caught."""
    for line in ("from assetops_backend.analytics.adapters.postgres_finding_store import X",
                 "import assetops_backend.estate.adapters.postgres_estate_read",
                 "from assetops_backend.analytics import composition",
                 "from assetops_backend.work.composition import build",
                 "importlib.import_module('assetops_backend.actions.composition')"):
        probe = tmp_path / "probe.py"
        probe.write_text(f"import importlib\n{line}\n", encoding="utf-8")
        assert violations(probe), line
    ok = tmp_path / "ok.py"
    ok.write_text("from assetops_backend.site_outcomes.composition import build\n"
                  "from assetops_backend.estate.portfolio import workflow_label\n", encoding="utf-8")
    assert violations(ok) == []
