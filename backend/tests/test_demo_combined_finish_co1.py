"""POLISH PA-3 (Addendum 10): CO-1's Cost-row linkage, `demo_combined_finish.cost_row_action_links`, on row fixtures.
Pure: no database. The linked Action needs its href (text alone never passes), and the Must-not-harm href is the guard
that fails on the board from before LINK-LINEAGE, whose CO-3 `earlier` line already carried the Action href."""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

import demo_combined_finish as finish  # noqa: E402

ACTION, CODE = "8385fb40-aca4-4249-b35a-f6b0f3abeab3", "ACT-000001"
ROW = {
    "issues": [{"kind": "FINDING", "text": "Generator may have been on longer than needed",
                "href": "/sites/KOBO-001/findings/f-1?revision_id=r-1"}],
    "in_hand": [],
    "earlier": [{"text": "ACT-001", "href": f"/sites/KOBO-001/actions/{ACTION}?event_id=e-1",
                 "detail": "Estimated effect of the trial (not money saved): no lower supply cost per kWh."}],
    "options": [{"text": "Trial a lower generator stop setting", "href": "/sites/KOBO-001/findings/f-1/recommendation"}],
    "must_not_harm": {"text": "Reliable service and battery and generator life are checked as safeguards when ACT-001 "
                              "is verified; a gain that harms them does not count",
                      "href": f"/sites/KOBO-001/actions/{ACTION}/verification?event_id=e-1"},
}


def _check(row, state="VERIFIED"):
    return finish.cost_row_action_links(row, ACTION, CODE, state)


def test_a_final_trial_linked_under_earlier_by_href_passes() -> None:
    mnh, linked = _check(ROW)
    assert linked == ["ACT-001"] and mnh is ROW["must_not_harm"]


def test_the_same_row_with_only_the_code_text_and_no_action_href_fails() -> None:
    row = copy.deepcopy(ROW)
    row["earlier"][0].pop("href")
    with pytest.raises(AssertionError):
        _check(row)


def test_the_same_row_without_a_must_not_harm_href_fails() -> None:
    row = copy.deepcopy(ROW)
    row["must_not_harm"].pop("href")
    with pytest.raises(AssertionError):
        _check(row)


def test_an_unfinished_trial_must_be_linked_in_issues_or_in_hand() -> None:
    with pytest.raises(AssertionError):
        _check(ROW, state="PENDING")
    row = copy.deepcopy(ROW)
    row["in_hand"] = row.pop("earlier")
    assert _check(row, state="PENDING")[1] == ["ACT-001"]


def test_the_safeguards_sentence_and_display_code_are_required() -> None:
    for old, new in (("Reliable service and battery and generator life", "Reliable service"), ("ACT-001", "ACT-000001")):
        row = copy.deepcopy(ROW)
        row["must_not_harm"]["text"] = row["must_not_harm"]["text"].replace(old, new)
        with pytest.raises(AssertionError):
            _check(row)


# ---- DATA-6: Kisiwa declares MG-2 and MG-5 (target 0), so CO-6 counts four objective Sites ------------------------

def test_data6_co6_counts_kisiwa_as_an_objective_site() -> None:
    assert finish.expected_objective_site_count(kisiwa=True) == 4
    assert finish.expected_objective_site_count(kisiwa=False) == 3  # a three-Site partial prepare stays green


def test_data6_kisiwa_objectives_are_mg2_and_mg5_at_zero_with_the_kobo_source_note() -> None:
    import json

    doc = json.loads((REPO / "backend" / "conversions" / "demo-objectives.json").read_text(encoding="utf-8"))
    lines = {o["outcome_key"]: o for o in doc["objectives"] if o["site_code"] == "KISIWA-001"}
    kobo = {o["outcome_key"]: o for o in doc["objectives"] if o["site_code"] == "KOBO-001"}
    assert sorted(lines) == ["MG-2", "MG-5"]
    for key in ("MG-2", "MG-5"):
        assert lines[key]["target"] == "0" and lines[key]["measure_key"] == kobo[key]["measure_key"]
        assert (lines[key]["source"], lines[key]["source_note"]) == (kobo[key]["source"], kobo[key]["source_note"])
        assert lines[key]["idempotency_key"] == f"out-d-kisiwa-001-{key.lower()}-v1"
