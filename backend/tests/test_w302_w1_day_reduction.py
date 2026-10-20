"""W3-02 0b: the W1 day reduction over selected interval projections (build spec closure 4, W1 day source).

Pure: each projection is the `ClaimLimitReadService.claim_limit_on` shape, so no database is needed.
"""
from __future__ import annotations

from assetops_backend.analytics.claim_limit_read import (
    CONTRADICTORY, FULL, HISTORICAL, HISTORICAL_SELECTION_UNAVAILABLE, LIMITED, NONE, UNKNOWN, interval_state,
    reduce_day)
from assetops_backend.analytics.dispatch import CANDIDATE, INDETERMINATE, NECESSARY

STATEMENT = "At most Candidate over 30.0 min (the sum of Candidate segments only, never the whole interval)"


def interval(rid: str, *, state: str = FULL, ceiling: str | None = CANDIDATE, statement: str | None = STATEMENT,
             positive: bool = True, reasons: list | None = None, ids: tuple = ("e1",),
             currentness: str = "CURRENT") -> dict:
    return {"assessment_revision_id": rid, "state": state, "currentness": currentness, "ceiling": ceiling,
            "support": "COMPLETE", "supported_minutes": 30.0, "statement": statement,
            "current_positive_claim": positive, "historical_ceiling": None, "reasons": reasons or [],
            "accepted_evidence_ids": list(ids)}


def day(*intervals: dict, available: bool = True) -> dict:
    return {"day": "2026-10-08", "domain": "dispatch", "available": available, "intervals": list(intervals),
            "window_assessment_revision_id": "w-rev"}


def test_state_precedence_and_zero_intervals() -> None:
    assert reduce_day(day())["state"] == UNKNOWN
    assert reduce_day(day(interval("a"), interval("b")))["state"] == FULL
    assert reduce_day(day(interval("a"), interval("b", state=LIMITED)))["state"] == LIMITED
    assert reduce_day(day(interval("a", state=LIMITED), interval("b", state=NONE)))["state"] == NONE
    assert reduce_day(day(interval("a", state=NONE), interval("b", state=UNKNOWN)))["state"] == UNKNOWN
    assert reduce_day(day(interval("a", state=UNKNOWN), interval("b", state=CONTRADICTORY)))["state"] == CONTRADICTORY


def test_interval_state_mapping() -> None:
    conflict = [{"code": "CONFLICTING", "role": "feeder_demand"}]
    assert interval_state("CURRENT", "COMPLETE", []) == FULL
    assert interval_state("CURRENT", "LIMITED", []) == LIMITED
    assert interval_state("CURRENT", "NONE", []) == NONE
    for status in ("PENDING", "FAILED", "STALE_PROJECTION", "UNASSESSED", HISTORICAL):
        assert interval_state(status, "COMPLETE", []) == UNKNOWN
    assert interval_state("CURRENT", "COMPLETE", conflict) == CONTRADICTORY
    assert interval_state("PENDING", "COMPLETE", conflict) == CONTRADICTORY
    # a window-scope CONFLICTING reason has no role and does not make the interval contradictory
    assert interval_state("CURRENT", "COMPLETE", [{"code": "CONFLICTING", "scope": "WINDOW"}]) == FULL


def test_single_ceiling_only_when_every_interval_agrees() -> None:
    same = reduce_day(day(interval("b", ids=("e2", "e3")), interval("a", ids=("e1", "e2"))))
    assert same["current_ceiling"] == CANDIDATE and same["ceiling_statement"] == STATEMENT
    assert same["ceiling_source"] == "W1_CLAIM_LIMIT"
    # the row cites the sorted union of interval revisions and accepted IDs; the window revision is kept apart
    assert same["assessment_revision_ids"] == ["a", "b"] and same["window_assessment_revision_id"] == "w-rev"
    assert same["accepted_evidence_ids"] == ["e1", "e2", "e3"]
    for other in (interval("b", ceiling=NECESSARY), interval("b", statement=STATEMENT + "; limited"),
                  interval("b", ceiling=INDETERMINATE, positive=False),
                  interval("b", ceiling=None, statement=None, positive=False, state=UNKNOWN)):
        mixed = reduce_day(day(interval("a"), other))
        assert mixed["current_ceiling"] is None and mixed["ceiling_statement"] is None
        assert mixed["ceiling_source"] is None
        # each interval keeps its own ceiling in the disclosure; none is borrowed
        assert [c["ceiling"] for c in mixed["interval_ceilings"]] == [CANDIDATE, other["ceiling"]]


def test_gaps_are_role_tagged_admitted_interval_reasons_only() -> None:
    a = interval("a", state=LIMITED, reasons=[
        {"code": "MISSING_ROLE", "role": "pv_available_power", "text": "x"},
        {"code": "POOR_QUALITY", "role": "feeder_demand", "text": "x"},
        {"code": "OPEN_BOUND", "text": "OPEN_BOUND: no role"},
        {"code": "MODEL_LIMIT", "text": "model"},
        {"code": "CONFIGURATION", "scope": "WINDOW", "text": "window reason, no role"},
        {"code": "MISSING_ROLE", "scope": "WINDOW", "text": "MISSING_ROLE: window-level, no role"},
        {"code": "RULE_BASIS_INCOMPLETE", "role": "feeder_demand", "text": "not an admitted gap code"}])
    b = interval("b", state=LIMITED, reasons=[
        {"code": "MISSING_ROLE", "role": "pv_available_power", "text": "y"},
        {"code": "GENERATOR_UNOBSERVED", "role": "generator_state", "text": "y"}])
    gaps = reduce_day(day(a, b))["gaps"]
    assert [(g["domain"], g["gap_code"], g["missing_role"], g["assessment_revision_ids"]) for g in gaps] == [
        ("dispatch", "GENERATOR_UNOBSERVED", "generator_state", ["b"]),
        ("dispatch", "MISSING_ROLE", "pv_available_power", ["a", "b"]),
        ("dispatch", "POOR_QUALITY", "feeder_demand", ["a"])]


def test_unreconstructable_day_is_unknown_without_ceiling() -> None:
    out = reduce_day(day(interval("a"), available=False))
    assert out["state"] == UNKNOWN and out["current_ceiling"] is None and out["ceiling_source"] is None
    assert out["assessment_revision_ids"] == [] and out["gaps"] == []
    assert [r["code"] for r in out["reasons"]] == [HISTORICAL_SELECTION_UNAVAILABLE]
