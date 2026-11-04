"""Self-test of the structural chain guard (`check_chain_structure.py`, build sheet CH-5a §B8): each rule fails on a
planted violation, `chain/` is exempt, the baseline admits only its own entries, a stale entry fails, and the
repository is clean against its baseline today."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_chain_structure as cs  # noqa: E402


def _tree(tmp_path: Path, files: dict[str, str]) -> Path:
    for rel, text in files.items():
        p = tmp_path / "assetops_backend" / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    return tmp_path


def _baseline(tmp_path: Path, entries: list[dict]) -> Path:
    p = tmp_path / "baseline.json"
    p.write_text(json.dumps({"entries": entries}), encoding="utf-8")
    return p


BOTH = ("from assetops_backend.analytics.finding_index import touched\n"
        "from assetops_backend.actions.adapters.postgres_action_store import PostgresActionStore\n")


@pytest.mark.parametrize("text,rule", [
    (BOTH, "a"),
    ("from assetops_backend.analytics.adapters import postgres_finding_store\n"
     "import assetops_backend.actions.site_index\n", "a"),
    ("from ..analytics import finding_index\nfrom ..actions.site_index import X\n", "a"),  # relative
    ("from x import _days_block\n_days_block(1)\n", "b-call"),
    ("def f(m):\n    return m.mini_summary_day(1)\n", "b-call"),
    ("def refresh_chain():\n    pass\n", "b-def"),
    ("class A:\n    def _action_for(self):\n        pass\n", "b-def"),
])
def test_each_rule_fails_on_a_planted_violation(tmp_path: Path, text: str, rule: str) -> None:
    root = _tree(tmp_path, {"estate/planted.py": text})
    assert [v["rule"] for v in cs.violations(root)][:1] == [rule]
    failures = cs.check(root, _baseline(tmp_path, []))
    assert len(failures) >= 1 and "estate/planted.py" in failures[0]


def test_one_side_only_and_unrelated_imports_pass(tmp_path: Path) -> None:
    root = _tree(tmp_path, {
        "a.py": "from assetops_backend.analytics.finding_index import touched\nfrom assetops_backend.actions import lifecycle\n",
        "b.py": "from assetops_backend.actions.site_index import X\n",
        "c.py": "def summary_day():\n    pass\nwindow_day(1, 2, 3)\n",
    })
    assert cs.violations(root) == [] and cs.check(root, _baseline(tmp_path, [])) == []


def test_chain_package_is_exempt(tmp_path: Path) -> None:
    root = _tree(tmp_path, {"chain/read.py": BOTH + "def refresh_chain():\n    _days_block(1)\n"})
    assert cs.violations(root) == []


def test_baseline_admits_its_entry_and_fails_when_stale_or_ownerless(tmp_path: Path) -> None:
    root = _tree(tmp_path, {"site_outcomes/board.py": "def linked_actions():\n    pass\n"})
    entry = {"rule": "b-def", "path": "assetops_backend/site_outcomes/board.py", "name": "linked_actions",
             "owner": "CH-6"}
    assert cs.check(root, _baseline(tmp_path, [entry])) == []
    assert any("names no owner" in f for f in cs.check(root, _baseline(tmp_path, [{**entry, "owner": ""}])))
    (root / "assetops_backend" / "site_outcomes" / "board.py").write_text("x = 1\n", encoding="utf-8")
    stale = cs.check(root, _baseline(tmp_path, [entry]))
    assert len(stale) == 1 and "no longer occurs" in stale[0]


def test_repository_is_clean_against_its_baseline() -> None:
    assert cs.check(cs.REPO / "backend", cs.BASELINE) == []
    baseline = json.loads(cs.BASELINE.read_text(encoding="utf-8"))["entries"]
    assert baseline and all(e["owner"] for e in baseline)
