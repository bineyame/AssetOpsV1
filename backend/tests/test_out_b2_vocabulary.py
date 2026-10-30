"""OUT-B2 (B1 review): every board and status string a viewer can read passes the product vocabulary scan.

Two sweeps: (1) the copy constants of `outcomes/status.py`, `site_outcomes/board.py` and `site_outcomes/mini.py`;
(2) every text field of boards assembled from the B1 fixtures and the B2 mini composer fixtures, so templated
sentences are scanned with their values filled in."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from assetops_backend.outcomes import status
from assetops_backend.site_outcomes import board, mini
from assetops_backend.site_outcomes.board import assemble

REPO = Path(__file__).resolve().parents[2]
TEXT_KEYS = ("label", "definition", "state_label", "headline", "subline", "not_measured_text", "text",
             "result_label", "earlier_empty_text")


def _patterns() -> list[tuple[str, re.Pattern[str]]]:
    data = json.loads((REPO / "frontend" / "src" / "test" / "productVocabulary.json").read_text(encoding="utf-8"))
    out = []
    for term in data["terms"] + data["w1"]["terms"]:
        body = re.escape(term["phrase"]).replace(r"\ ", r"\s+")
        out.append((term["phrase"], re.compile(rf"(?<![^\W_]){body}(?![^\W_])",
                                               0 if term.get("caseSensitive") else re.IGNORECASE)))
    for code in data["w1"]["codes"]:
        out.append((code, re.compile(rf"(?<!\w){re.escape(code)}(?!\w)")))
    for p in data["w1"]["patterns"]:
        if r"\p{" not in p["source"]:
            out.append((p["name"], re.compile(p["source"])))
    return out


def _texts(node: Any, out: list[str]) -> list[str]:
    if isinstance(node, dict):
        for k, v in node.items():
            if k in TEXT_KEYS and isinstance(v, str):
                out.append(v)
            elif k not in ("href", "key", "category", "state", "tone", "icon", "reason", "kind", "role", "ref"):
                _texts(v, out)
    elif isinstance(node, (list, tuple)):
        for v in node:
            _texts(v, out)
    return out


def _constants() -> list[str]:
    copy = [*status.STATE_LABEL.values()]
    copy += [board.SAFEGUARD_SUFFIX, board.NOT_LINKED_SUFFIX, board.OUTSIDE_VIEW_SUFFIX, board.EARLIER_EMPTY_OPEN,
             board.EARLIER_EMPTY_NONE, board.REQUEST_REPEATED, board.REQUEST_UNVERIFIED,
             board.DECLARED["label"], board.PLAN_RECORD["label"]]
    copy += [*board.ISSUE_KIND_LABEL.values(), *board.WORKFLOW_IN_HAND.values(), *board.CASE_STATE_LABEL.values(),
             *board.ACTION_RESULT.values(), *(label for label, _ in board.READINESS_CONFIDENCE.values())]
    copy += [link[0] for link in board.EVIDENCE_LINK.values() if link]
    copy += list(mini.COPY)
    return [c.strip(" ·") for c in copy]


def _boards() -> list[str]:
    import test_out_b1_board as b1  # pytest puts tests/ on sys.path (rootdir-relative test modules)
    import test_out_b2_mini as b2

    ev = board.SiteFacts(board.EV, "EV-LAB-001", findings=(b1.F130,), readiness="NONE", settled=b1.settled(board.EV))
    facts = [b1.kobo(), b1.kobo(actions=(b1.act048(applied=True),)), b1.cold(), ev]
    facts += [comp.facts for comp in b2.vocabulary_compositions()]
    out: list[str] = []
    for f in facts:
        _texts(assemble(f), out)
    return out


def test_board_and_status_copy_pass_vocabulary() -> None:
    patterns = _patterns()
    copy = _constants() + _boards()
    assert len(copy) > 60 and all(text and text.strip() for text in copy)
    hits = sorted({(text, name) for text in copy for name, pattern in patterns if pattern.search(text)})
    assert hits == []


def test_scan_is_not_vacuous() -> None:
    patterns = _patterns()
    assert any(p.search("Buses ready to run") for _, p in patterns)
    assert any(p.search("PRIMARY_FINDING_OPEN") for _, p in patterns)  # a raw code in copy is caught
