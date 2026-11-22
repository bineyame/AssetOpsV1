"""0K4e (`specs/0K4e-candidate-energy/spec.md` §2.5, §3 E12-E14; D-0K4.24): the readers that explain a dispatch-3.3
energy-cover entry render SC-1 statements from its stored codes and figures; role coverage stays per instant. Pure.
Every expected text is a hand literal (W2)."""
from __future__ import annotations

from uuid import UUID

import pytest

import test_0k4e_energy_to_cover as e
from assetops_backend.analytics import claim_limit_read, dispatch_v3 as d3, plain
from assetops_backend.analytics.assessment_inputs import EvidenceQuery, EvidenceQueryResult, build_input_set
from assetops_backend.analytics.cohort import select_cohort
from assetops_backend.analytics.finding_read import MODELLING, RECORD_GAP, UNSTATED, portion_cause
from assetops_backend.i18n import message, render
from assetops_backend.sites.binding_roles import ROLE_SET_MINIGRID_2
from statement_cases import dispatch as cases

COVERED_TEXT = ("The available solar power and battery output were more than the site demand, with battery charge "
                "above its minimum reserve, and the battery's 133 kWh above that reserve covers the 120 kWh needed "
                "until solar power covers site demand with 10% headroom (Estimated and Declared); no reason the "
                "generator was needed was recorded.")
SHORT_TEXT = ("Battery support was not counted: the battery's 95 kWh above its minimum reserve does not cover the "
              "120 kWh needed until solar power covers site demand with 10% headroom (Estimated and Declared).")
GAP_TEXT = ("Battery support was not counted: solar available power has no accepted reading at 2 October 2026, "
            "23:00 UTC, before solar power covers site demand.")
NOT_REACHED_TEXT = ("Battery support was not counted: solar power does not cover site demand before the assessed "
                    "records end at 3 October 2026, 06:00 UTC.")
NOT_CONFIGURED_TEXT = "Battery support was not counted: the Site's Foundation does not give the battery energy capacity."
SHORT_CAUSE = ("the battery's stored energy above its minimum reserve would not have lasted until solar power covered "
               "site demand")


def assessed(night: e.Night, ctrl=None):
    """(segment, evidence map as `claim_limit_read` reads it) for a one-point night."""
    readings = night.readings()
    query = EvidenceQuery(UUID(int=7), UUID(int=8), "dispatch", e.WINDOW, e.at(23), cohort=None)
    result = EvidenceQueryResult(query, readings, e.bindings(), ctrl or e.controls(), (ROLE_SET_MINIGRID_2,))
    inputs = build_input_set(result, select_cohort(readings, e.WINDOW, None), analytic_id=d3.ANALYTIC_ID,
                             model_version=d3.MODEL_VERSION, roles_by_set=e.ROLES_BY_SET)
    [interval] = d3.assess(inputs).intervals
    [segment] = interval.result["segments"]
    evidence = {str(r.evidence_id): {"role": r.role, "at": r.placed_at} for r in readings}
    return segment, evidence


SEGMENTS = {
    "SHORT": lambda: assessed(e.one_point_night(soc="80")),
    "COVERED": lambda: assessed(e.one_point_night(soc="100")),
    "GAP": lambda: assessed(e.one_point_night(soc="100", pv_skip=(e.at(23),))),
    "NOT_REACHED": lambda: assessed(e.one_point_night(soc="100", pv_cover_at=e.at(31))),
    "NOT_CONFIGURED": lambda: assessed(e.one_point_night(soc="100"), e.controls(capacity=None)),
}


@pytest.mark.parametrize("case", cases.CASES, ids=lambda c: f"{c.key}-{c.variant}")
def test_every_dispatch_case_renders_its_hand_literal(case):
    assert render(message(case.key, **case.facts)) == case.english


@pytest.mark.parametrize("state,text", [("SHORT", SHORT_TEXT), ("GAP", GAP_TEXT), ("NOT_REACHED", NOT_REACHED_TEXT),
                                        ("NOT_CONFIGURED", NOT_CONFIGURED_TEXT), ("COVERED", COVERED_TEXT)])
def test_e12_plain_reads_the_entry(state, text):
    segment, _ = SEGMENTS[state]()
    assert segment["energy_cover"][0]["state"] == state
    out = plain._segment(segment)
    assert out["reason"] == text
    assert out["missing"] == []
    assert out["outcome"] == plain.OUTCOMES[segment["classification"]]


def test_e12_a_legacy_record_gap_wins_over_an_entry():
    segment, _ = SEGMENTS["SHORT"]()
    legacy = {**segment, "missing": ["PV available power: no accepted reading"]}
    assert plain._segment(legacy)["reason"].startswith("Records needed to decide are missing or conflicting: ")


def test_e12_the_lead_entry_is_the_record_gap_then_the_earliest():
    segment, _ = SEGMENTS["SHORT"]()
    short = segment["energy_cover"][0]
    gap = {**short, "at": "2026-10-02T18:05:00.000000Z", "state": "GAP", "need_kwh": None,
           "input": "pv_available_power", "problem": "MISSING", "gap_at": "2026-10-02T23:00:00.000000Z"}
    assert plain._segment({**segment, "energy_cover": [short, gap]})["reason"] == GAP_TEXT


def test_e13_findings_name_the_energy_cause():
    short, _ = SEGMENTS["SHORT"]()
    assert portion_cause([], short["energy_cover"]) == (MODELLING, [SHORT_CAUSE])
    for state in ("GAP", "NOT_CONFIGURED"):
        segment, _ = SEGMENTS[state]()
        assert portion_cause([], segment["energy_cover"]) == (RECORD_GAP, [])
    reached, _ = SEGMENTS["NOT_REACHED"]()
    assert portion_cause([], reached["energy_cover"]) == (
        MODELLING, ["solar power did not cover site demand before the assessed records end"])
    assert portion_cause([]) == (UNSTATED, [])          # 3.2's form, unchanged


@pytest.mark.parametrize("state", ["SHORT", "GAP", "NOT_CONFIGURED"])
def test_e14_role_coverage_stays_per_instant(state):
    segment, evidence = SEGMENTS[state]()
    assert segment["classification"] == d3.INDETERMINATE
    roles = claim_limit_read.segment_roles(segment, evidence)
    assert {role: status for role, (status, _, _) in roles.items()} == {
        role: claim_limit_read.COVERED for role in claim_limit_read.REQUIRED_ROLES}
