"""DD-1b2b B1 L0: the pure parts of `tools/demo_combined_ex1.py` (tree-form guard, whole-row compare). No database.
Each guard has a case that must fail."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

import demo_combined_ex1 as ex1  # noqa: E402


def _finding(fid: str, text: str = "f") -> dict:
    return {"kind": "FINDING", "text": text, "ref": {"finding_id": fid}}


def _board(read_state: str = "AVAILABLE", **over: object) -> dict:
    rows = [
        {"category": "ASSURE_PERFORMANCE", "headline": "1 verified result", "count": 1, "state": "OK",
         "issues": [], "in_hand": [], "earlier": [], "options": []},
        {"category": "OPTIMIZE_COST", "headline": "h", "state": "OK",
         "issues": [_finding("a"), _finding("b")], "in_hand": [], "earlier": [{"text": "ACT-001"}], "options": []},
    ]
    for r in rows:
        r.update(over.get(r["category"], {}))
    return {"read_state": read_state, "rows": rows}


def _sum(b_s: dict, b_s1: dict | None = None) -> dict:
    return ex1.summarise(b_s, b_s1 or _board())


def test_tree_form_guard_accepts_only_a_backend_under_the_work_tree(tmp_path: Path) -> None:
    work = tmp_path / "var" / "demo3_x"
    inside = work / "tree" / "backend" / "assetops_backend" / "__init__.py"
    assert ex1.tree_form(str(inside), work)
    assert not ex1.tree_form(str(tmp_path / "wt" / "backend" / "assetops_backend" / "__init__.py"), work)  # must fail
    assert not ex1.tree_form(str(work / "backend" / "assetops_backend" / "__init__.py"), work)  # not under tree/


def test_identical_boards_pass_and_findings_are_a_set_per_row() -> None:
    before = _sum(_board())
    reordered = _board(OPTIMIZE_COST={"issues": [_finding("b"), _finding("a")]})
    out = ex1.compare(before, _sum(reordered))
    assert out["unchanged"] and out["passes"] and not out["diff"]


def test_a_read_state_change_is_flagged_and_fails() -> None:
    out = ex1.compare(_sum(_board("PARTIAL")), _sum(_board("AVAILABLE")))
    assert not out["passes"] and "S.read_state" in out["failures"]


def test_a_new_finding_is_flagged_and_fails() -> None:
    after = _board(OPTIMIZE_COST={"issues": [_finding("a"), _finding("b"), _finding("c")]})
    out = ex1.compare(_sum(_board()), _sum(after))
    assert not out["passes"] and out["diff"]["S.new_findings"] == ["c"]


def test_a_changed_item_outside_the_o9_keys_is_recorded_but_does_not_fail() -> None:
    after = _board(OPTIMIZE_COST={"options": [{"text": "an option"}]})  # a new item that is not a trial/ACT line
    out = ex1.compare(_sum(_board()), _sum(after))
    assert not out["unchanged"] and out["passes"] and "S.row.OPTIMIZE_COST" in out["diff"]


def test_a_changed_assure_headline_or_trial_line_fails() -> None:
    out = ex1.compare(_sum(_board()), _sum(_board(ASSURE_PERFORMANCE={"headline": "2 verified results"})))
    assert not out["passes"] and "S.assure_headline" in out["failures"]
    out = ex1.compare(_sum(_board()), _sum(_board(OPTIMIZE_COST={"in_hand": [{"text": "Trial a lower stop"}]})))
    assert not out["passes"] and "S.cost_lines" in out["failures"]
