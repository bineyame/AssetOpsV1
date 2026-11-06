"""OUT-B2 (B1 review): every board and status string a viewer can read passes the product vocabulary scan.

Two sweeps: (1) the copy constants of `outcomes/status.py`, `site_outcomes/board.py` and `site_outcomes/mini.py`;
(2) every text field of boards assembled from the B1 fixtures and the B2 mini composer fixtures, so templated
sentences are scanned with their values filled in."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from assetops_backend.outcomes import credit, status
from assetops_backend.site_outcomes import board, cold, ev, mini
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
        out.append((p["name"], re.compile(_python_source(p["source"]),
                                          re.IGNORECASE if "i" in p.get("flags", "") else 0)))
    return out


#: B2 review L4: the Unicode property classes the w1 patterns use, in Python `re` form (`\w` minus `_` and digits).
_PROPERTY_CLASSES = ((r"[\p{L}\p{N}]", r"[^\W_]"), (r"\p{L}", r"[^\W\d_]"), (r"\p{N}", r"\d"))


def _python_source(source: str) -> str:
    r"""A w1 JavaScript pattern as Python `re`; an untranslated `\p{...}` fails loudly instead of being skipped."""
    for js, py in _PROPERTY_CLASSES:
        source = source.replace(js, py)
    if r"\p{" in source or r"\P{" in source:
        raise AssertionError(f"untranslated Unicode property class in vocabulary pattern: {source}")
    return source


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
    copy += list(mini.COPY) + list(cold.COPY) + list(ev.COPY) + [board.NOT_LOADED_LINK_SUFFIX]
    copy += [board.COST_NOT_CREDITED, board.COST_CHANGE.format(amount="0.042", currency="USD"),
             board.COST_NO_CHANGE]  # POLISH PA-1 L-1
    # CH-3 §5: the four thread lines (formatted), the I-11 scope line and the Portfolio's not-credited money text
    copy += [board.THREAD_BEFORE.format(e="1 Nov")
             + board.THREAD_AFTER_JUDGED.format(state_label=status.STATE_LABEL[status.ON_TRACK], day="3 Nov"),
             board.THREAD_BEFORE.format(e="1 Nov") + board.THREAD_AFTER_NOT_JUDGED.format(e="1 Nov"),
             board.THREAD_MONITORING.format(code="ACT-001", k=7), board.THREAD_CLOSED.format(code="ACT-001", n=7),
             board.THREAD_RECURRED.format(day="3 Nov", code="ACT-001"),
             board.TRIAL_SCOPE.format(start="10:00", end="11:00", day="1 Nov"), credit.MONEY_NOT_CREDITED]
    # CH-5b2: every "Why?" template, formatted with plain sample values, and every measure label.
    from assetops_backend.chain import vocabulary as cv
    sample = {"site": "Kobo", "category": "Grow revenue", "label": "Unused daytime solar", "k": 3, "s": "s",
              "title": "Generator on longer than needed", "n": 2, "first": "6 Oct", "code": "ACT-048",
              "c": 3, "e": 5, "p": 1, "q": 1, "d": "6 Oct", "say": "On track", "days": "6 Oct checked",
              # CH-6a3: the price lines of "Why?" (kWh x price, litres x price)
              "kwh": "168.3", "price": "0.25", "cur": "USD", "lo": "12", "hi": "18"}
    copy += [cv.WHY_TEXT[key].format(**sample) for key in cv.WHY_TEXT] + list(cv.MEASURE_LABEL.values())
    # CH-6a2: every node template (§A4), formatted with plain sample values.
    node = {"amount": "7.50 USD", "k": 3, "m": 5, "p": 1, "n": 1, "lo": "18", "hi": "20", "cur": "USD",
            "day": "1 Nov"}
    copy += [cv.NODE_TEXT[key].format(**node) for key in cv.NODE_TEXT]
    return [c.strip(" ·") for c in copy]


def _boards() -> list[str]:
    import test_out_b1_board as b1  # pytest puts tests/ on sys.path (rootdir-relative test modules)
    import test_out_b2_mini as b2
    import test_out_b3_cold_ev as b3

    ev = board.SiteFacts(board.EV, "EV-LAB-001", findings=(b1.F130,), readiness="NONE", settled=b1.settled(board.EV))
    facts = [b1.kobo(), b1.kobo(actions=(b1.act048(applied=True),)), b1.cold(), ev]
    facts += [comp.facts for comp in b2.vocabulary_compositions() + b3.vocabulary_compositions()]
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


def test_finding_gap_line_strings_are_scanned() -> None:
    """IDX-GAPS U2: the board gap strings are in the scanned set. CH-5a1 (CH5a1-R Q4): the board never withholds
    Findings next to gap days, so the withheld suffix is no longer board copy (the estate keeps its own)."""
    copy = _constants()
    for text in ("23 of the last 31 days have no checked readings yet",
                 "Not available yet · 2 of 31 days are not assessed yet"):
        assert text.strip(" ·") in copy, text
    assert "; Findings next to those days are not shown yet".strip(" ·") not in copy


def test_scan_is_not_vacuous() -> None:
    patterns = _patterns()
    assert any(p.search("Buses ready to run") for _, p in patterns)
    assert any(p.search("PRIMARY_FINDING_OPEN") for _, p in patterns)  # a raw code in copy is caught
    assert any(name == "rule or model version" and p.search("Uses outcome-map-v1 rules")
               for name, p in patterns)  # the translated \p{} pattern is scanned, not skipped (L4)


def test_untranslated_property_class_fails_loudly() -> None:
    import pytest
    with pytest.raises(AssertionError, match="untranslated"):
        _python_source(r"(?<!\p{Lu})x")
