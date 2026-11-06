"""CH6a3-R2 (review M2): the R7 target note, the row's node selection (`board.row_nodes`) and the lead money head's
mechanism gate (`mini._lead_findings`). Pure: no store, no ports."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from types import SimpleNamespace

from assetops_backend.outcomes.objectives import ObjectiveFact
from assetops_backend.outcomes.status import NO_OBJECTIVE, ON_TRACK, roll_up
from assetops_backend.site_outcomes.board import row_nodes
from assetops_backend.site_outcomes.mini import _lead_findings

DAY = date(2026, 10, 24)
NO_DATA = {"expected": 1, "complete": 0, "partial": 0, "low": 0, "no_data": 1, "pending": 0}
TWO = {"expected": 2, "complete": 2, "partial": 0, "low": 0, "no_data": 0, "pending": 0}


def objective(key: str, measure: str) -> ObjectiveFact:
    return ObjectiveFact(key, measure, "AT_MOST", Decimal(0), True, "t", "DECLARED", "r")


def claim(key: str, value=None, days=None, text="t") -> dict:
    return {"key": key, "value": value, "basis": "COMPLETE" if days else "NOT_KNOWN", "days": days, "text": text}


def facts(nodes: dict, objectives=(), one_day: bool = True, day: date | None = DAY) -> SimpleNamespace:
    return SimpleNamespace(nodes=nodes, objectives=tuple(objectives), day=day, one_day=one_day)


def test_r7_cold_lab_24_oct_is_on_track_with_the_target_note() -> None:
    """Sheet R7 / design A3: the Cold Protect row on 24 Oct, CC-1 and CC-6 on track against their targets and CC-5
    with none. ON_TRACK now outranks NO_OBJECTIVE, and the row says how many outcomes have a target."""
    states = [("CC-1", ON_TRACK), ("CC-6", ON_TRACK), ("CC-5", NO_OBJECTIVE)]
    row_state, lead = roll_up(states)
    assert (row_state, lead) == (ON_TRACK, "CC-1")
    f = facts({"CC-1": {"kpi": claim("verdict.CC-1", "MET", TWO), "earnings": None, "potential": None}},
              [objective("CC-1", "excursion_minutes"), objective("CC-6", "backup_start_failures")])
    out = row_nodes(f, ["CC-1", "CC-6", "CC-5"], lead, row_state, states)
    assert out["target_note"] == "2 of 3 outcomes have a target"
    # every outcome targeted, or a row not ON_TRACK: no note
    assert row_nodes(f, ["CC-1", "CC-6"], lead, row_state, states[:2])["target_note"] is None
    assert row_nodes(f, ["CC-1", "CC-6", "CC-5"], lead, "WATCH", states)["target_note"] is None


def test_row_nodes_selects_the_lead_kpi_and_the_first_money_and_potential() -> None:
    earn, pot = claim("money.estimated_income", {"amount": "3"}, TWO), claim("potential.value", {"low": "1"})
    nodes = {"MG-1": {"kpi": claim("verdict.MG-1", "MET", TWO), "earnings": earn, "potential": pot},
             "MG-2": {"kpi": claim("verdict.MG-2", "MISSED", TWO), "earnings": None, "potential": None}}
    both = [objective("MG-1", "productive_use_kwh"), objective("MG-2", "avoidable_generator_minutes")]
    out = row_nodes(facts(nodes, both), ["MG-1", "MG-2"], "MG-2", "WATCH", [])
    assert out["nodes"]["kpi"] == {**nodes["MG-2"]["kpi"], "days_line": "2 of 2 days checked"}  # the lead's kpi
    assert out["nodes"]["earnings"]["days_line"] == "2 of 2 days checked"
    assert out["nodes"]["potential"]["days_line"] is None and "days_line" not in out
    # the lead has no objective: the first declared outcome's kpi
    out = row_nodes(facts(nodes, both[:1]), ["MG-1", "MG-2"], "MG-2", "WATCH", [])
    assert out["nodes"]["kpi"]["key"] == "verdict.MG-1"


def test_row_nodes_no_target_kpi_gets_the_no_target_days_line() -> None:
    nodes = {"MG-1": {"kpi": claim("verdict.MG-1", None, None, "No target set yet"), "earnings": None,
                      "potential": None}}
    out = row_nodes(facts(nodes), ["MG-1"], "MG-1", "OPPORTUNITY", [])
    assert out["nodes"]["kpi"]["text"] == "No target set yet"
    assert out["nodes"]["kpi"]["days_line"] == "No target, so no days are judged yet"
    assert out["nodes"]["potential"]["text"] == "No potential found yet" and out["nodes"]["potential"]["days_line"] is None
    assert out["nodes"]["earnings"]["text"] == "Not known yet"


def test_row_nodes_fills_a_missing_target_and_gives_each_part_its_own_days_line() -> None:
    """R2b H4: EV-3 has no kpi record: the Target is server-filled; the earnings line is not borrowed by the others."""
    nodes = {"EV-3": {"kpi": None, "earnings": claim("money.x", None, TWO), "potential": None}}
    n = row_nodes(facts(nodes), ["EV-3"], "EV-3", "UNKNOWN", [])["nodes"]
    assert n["kpi"]["text"] == "No target set yet" and n["kpi"]["days_line"] == "No target, so no days are judged yet"
    assert n["earnings"]["days_line"] == "2 of 2 days checked" and n["potential"]["days_line"] is None


def test_row_nodes_dates_a_no_data_day_only_for_a_one_day_window() -> None:
    """CH6a3-R2 M4: "No readings on {day}" names the board day only when the window is that one Site-local day."""
    nodes = {"EV-3": {"kpi": None, "earnings": claim("money.estimated_charging_income", None, NO_DATA),
                      "potential": None}}
    assert row_nodes(facts(nodes), ["EV-3"], "EV-3", "UNKNOWN", [])["nodes"]["earnings"]["days_line"] == "No readings on 24 Oct"
    many = row_nodes(facts(nodes, one_day=False), ["EV-3"], "EV-3", "UNKNOWN", [])["nodes"]["earnings"]["days_line"]
    assert many is not None and "24 Oct" not in many


def test_lead_findings_maps_only_a_generator_support_head() -> None:
    """Review M2 (fix 1): a lead Finding of another mechanism never prices the MG-2 fuel line."""
    gen = SimpleNamespace(finding_id="f1", mechanism="GENERATOR_SUPPORT_CANDIDATE")
    other = SimpleNamespace(finding_id="f2", mechanism="BATTERY_RESERVE_DRIFT")
    assert _lead_findings((gen, other), ("f1", None)) == {"GENERATOR_SUPPORT_CANDIDATE": "f1"}
    assert _lead_findings((gen, other), ("f2", None)) == {}
    assert _lead_findings((gen,), ("f9", None)) == {} and _lead_findings(None, ("f1", None)) == {}
    assert _lead_findings((gen,), None) == {}
