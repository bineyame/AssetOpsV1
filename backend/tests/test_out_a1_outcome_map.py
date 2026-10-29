"""OUT-A1: outcome catalogue and map (build spec outcome sprint 2026-10-29 §1.1-1.3, rulings A-Q1..Q5)."""
from __future__ import annotations

import ast
import json
import re
from pathlib import Path

from assetops_backend.outcomes import catalogue, outcome_map
from assetops_backend.outcomes.catalogue import CATEGORIES, COLD, EV, MINI, OUTCOME_BY_KEY, SITE_OUTCOMES
from assetops_backend.outcomes.outcome_map import (
    COLD_KIND_MECHANISM, ENTRIES, categories_for, finding_signal_key, outcome_roles)

REPO = Path(__file__).resolve().parents[2]
PACKAGE = REPO / "backend" / "assetops_backend" / "outcomes"


def _shape(categories):
    return [(i["category"], i["role"], tuple(o["key"] for o in i["outcomes"])) for i in categories["items"]]


def _list_form(categories):
    """The list pill form (mock affectsPill): MOVES categories, then CHECKED categories not already moving."""
    moves = [i["category"] for i in categories["items"] if i["role"] == "MOVES"]
    checked = [i["category"] for i in categories["items"] if i["role"] == "CHECKED" and i["category"] not in moves]
    return moves, checked


def test_every_entry_resolves_for_its_domain() -> None:
    domain_of = {"MG": MINI, "CC": COLD, "EV": EV}
    for key, (moves, checked) in ENTRIES.items():
        literal = [k for k in moves + checked if not k.startswith("@")]
        domains = {domain_of[k[:2]] for k in literal} or set(catalogue.DOMAINS)
        for domain in domains:
            linked = ("CC-6", "CC-1") if domain == COLD else ()
            got_moves, got_checked = outcome_roles(key, domain, linked)
            assert got_moves, (key, domain)
            assert all(OUTCOME_BY_KEY[k].domain == domain for k in got_moves + got_checked), (key, domain)
            assert categories_for(key, domain, linked)["state"] == "MAPPED"
    assert outcome_roles("SIGNAL:EVIDENCE_READINESS", EV) == (("EV-7",), ())
    assert outcome_roles("WARNING:REPEATED_MAINTENANCE_NO_RESULT", COLD, ("CC-6", "CC-1")) == (
        ("CC-3",), ("CC-6", "CC-1"))


def test_mock_findings_items_order_and_list_form() -> None:
    f104 = categories_for(finding_signal_key("GENERATOR_SUPPORT_CANDIDATE"), MINI)
    assert _shape(f104) == [("OPTIMIZE_COST", "MOVES", ("MG-2",)), ("PROTECT_ASSET", "CHECKED", ("MG-5", "MG-4"))]
    assert f104["policy_version"] == "outcome-map/1" and f104["state"] == "MAPPED"
    assert f104["items"][1]["label"] == "Protect asset and capital"
    assert f104["items"][1]["outcomes"] == [{"key": "MG-5", "label": "Reliable service"},
                                            {"key": "MG-4", "label": "Battery and generator life"}]
    f118 = categories_for(finding_signal_key("COLD_START_FAILURE"), COLD)
    assert _shape(f118) == [("PROTECT_ASSET", "MOVES", ("CC-6", "CC-1")), ("PROTECT_ASSET", "CHECKED", ("CC-5",)),
                            ("OPTIMIZE_COST", "CHECKED", ("CC-3",))]
    assert _list_form(f118) == (["PROTECT_ASSET"], ["OPTIMIZE_COST"])
    f119 = categories_for(finding_signal_key("COLD_EXCURSION"), COLD)
    assert _shape(f119) == [("PROTECT_ASSET", "MOVES", ("CC-1",))]
    f130 = categories_for(finding_signal_key("EV_INTERRUPTION"), EV)
    assert _shape(f130) == [("PROTECT_ASSET", "MOVES", ("EV-1",)), ("GROW_REVENUE", "MOVES", ("EV-3",)),
                            ("PROTECT_ASSET", "CHECKED", ("EV-4",))]
    assert _list_form(f130) == (["PROTECT_ASSET", "GROW_REVENUE"], [])


def test_not_mapped_cases() -> None:
    expected = {"policy_version": "outcome-map/1", "state": "NOT_MAPPED", "items": []}
    assert finding_signal_key(None) == "FINDING:UNMAPPED"
    assert categories_for(finding_signal_key(None), MINI) == expected
    assert categories_for(finding_signal_key("SOMETHING_NEW"), MINI) == expected
    assert categories_for(finding_signal_key("EV_INTERRUPTION"), MINI) == expected
    assert categories_for(finding_signal_key("GENERATOR_SUPPORT_CANDIDATE"), "not_applicable") == expected
    assert categories_for("WARNING:REPEATED_MAINTENANCE_NO_RESULT", COLD, ("EV-1",)) == expected
    assert outcome_roles("FINDING:UNMAPPED", MINI) == ((), ())


def test_cold_kind_mechanism_equals_store_and_domains_equal_coverage() -> None:
    from assetops_backend.analytics.adapters import postgres_finding_store
    from assetops_backend.estate import coverage
    assert COLD_KIND_MECHANISM == postgres_finding_store.COLD_MECHANISMS
    assert (MINI, COLD, EV) == (coverage.MINI_GRID, coverage.COLD, coverage.EV)


def _vocabulary_patterns() -> list[tuple[str, re.Pattern[str]]]:
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


def test_catalogue_copy_passes_vocabulary() -> None:
    patterns = _vocabulary_patterns()
    copy = (list(catalogue.CATEGORY_LABEL.values()) + list(catalogue.CATEGORY_DEFINITION.values())
            + [o.label for o in SITE_OUTCOMES] + [o.missing_records for o in SITE_OUTCOMES if o.missing_records]
            + list(catalogue.ROW_NOT_MEASURED.values()) + [catalogue.ROW_NOT_MEASURED_PREFIX])
    assert all(text and text.strip() for text in copy)
    hits = [(text, name) for text in copy for name, pattern in patterns if pattern.search(text)]
    assert hits == []
    assert any(p.search("Buses ready to run") for _, p in patterns)  # non-vacuous: the mock label is caught
    assert set(catalogue.CATEGORY_LABEL) == set(CATEGORIES) == set(catalogue.CATEGORY_DEFINITION)
    assert len({o.key for o in SITE_OUTCOMES}) == len(SITE_OUTCOMES)
    assert all(o.measured == (o.missing_records is None) for o in SITE_OUTCOMES)
    assert not OUTCOME_BY_KEY["MG-4"].measured and not OUTCOME_BY_KEY["CC-3"].measured


def test_row_not_measured_sentences() -> None:
    assert catalogue.row_not_measured(COLD, "GROW_REVENUE", OUTCOME_BY_KEY["CC-2"]) == (
        "Needs occupancy, storage contract, income and sales records")
    assert catalogue.row_not_measured(MINI, "GROW_REVENUE", OUTCOME_BY_KEY["MG-6"]) == (
        "Not measured yet · no billing or payment records")


def test_outcomes_package_is_pure() -> None:
    allowed = {"__future__", "dataclasses", "typing", "collections.abc"}
    files = sorted(PACKAGE.glob("*.py"))
    assert files
    for path in files:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            else:
                continue
            for name in names:
                assert name in allowed or name.startswith("assetops_backend.outcomes"), (path.name, name)
    assert outcome_map.POLICY_VERSION == "outcome-map/1"
