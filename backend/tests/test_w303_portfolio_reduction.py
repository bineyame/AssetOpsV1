"""W3-03 run 1a: closure 5 S4 exact Evidence and Financials reductions (pure, exhaustive class/count tables)."""

from __future__ import annotations

from itertools import product

import pytest

from assetops_backend.estate.portfolio import (
    G, N, U, evidence_unit, finding_unit, money_units, reduce_units, settled)

SETTLED = {"state": "CURRENT", "job_state": "SETTLED", "source_freshness": "RECENT", "match_state": "COMPLETE"}


def row(raw="FULL", readiness="FULL", selected=("r1",)):
    return {"raw_state": raw, "readiness": readiness, "selected_revision_ids": list(selected)}


@pytest.mark.parametrize("sites,g,u,n", [(s, g, u, n) for s, g, u, n in product((0, 3), range(3), range(3), range(3))
                                         if s or (g == u == n == 0)])
def test_four_row_reduction_is_exhaustive_and_ignores_n(sites, g, u, n) -> None:
    classes = [G] * g + [U] * u + [N] * n
    expected = ("EMPTY" if sites == 0 else "COMPLETE" if u == 0 else "PARTIAL" if g else "UNKNOWN")
    assert reduce_units(sites, classes) == expected
    assert reduce_units(sites, list(reversed(classes))) == expected  # order-free


@pytest.mark.parametrize("change", [{"state": s} for s in ("PENDING_RECOMPUTE", "STALE_SOURCE", "UNKNOWN",
                                                            "NOT_APPLICABLE")]
                         + [{"job_state": j} for j in ("PENDING", "FAILED", "NONE")]
                         + [{"source_freshness": "STALE"}] + [{"match_state": m} for m in ("MISSING", "PENDING")])
def test_unsettled_inputs_are_u_for_every_root(change) -> None:
    cov = {**SETTLED, **change}
    assert not settled(cov)
    assert finding_unit("mini_grid", cov) == U
    assert evidence_unit("mini_grid", cov, [row()]) == U
    assert set(money_units("cold_chain", {**cov, "_windows_covered": True}, []).values()) == {U}


def test_settled_current_and_historical_bases() -> None:
    for state in ("CURRENT", "HISTORICAL"):
        cov = {**SETTLED, "state": state}
        assert settled(cov) and finding_unit("ev_charging", cov) == G
    assert settled({**SETTLED, "job_state": "NOT_APPLICABLE", "source_freshness": "NOT_APPLICABLE",
                    "match_state": "NOT_APPLICABLE"})
    # An unknown physical configuration is U, never N.
    assert finding_unit("NOT_APPLICABLE", SETTLED) == U
    assert evidence_unit("NOT_APPLICABLE", SETTLED, [row()]) == U
    assert money_units("NOT_APPLICABLE", SETTLED, []) == {"UNPROVED_CONFIGURATION": U}


def test_evidence_table() -> None:
    for readiness in ("FULL", "LIMITED", "NONE"):  # known claim limits, not missing coverage
        assert evidence_unit("cold_chain", SETTLED, [row(readiness, readiness)]) == G
    for readiness in ("UNKNOWN", "CONTRADICTORY"):  # one unresolved capability wins over a selected one
        assert evidence_unit("cold_chain", SETTLED, [row(), row("UNASSESSED", readiness)]) == U
    assert evidence_unit("cold_chain", SETTLED, []) == U  # no inference of non-applicability from absent rows
    # A selected as-of head is settled; a historical row without a selected head is missing.
    hist = {**SETTLED, "state": "HISTORICAL"}
    assert evidence_unit("ev_charging", hist, [row("HISTORICAL", "UNKNOWN")]) == G
    assert evidence_unit("ev_charging", hist, [row("HISTORICAL", "UNKNOWN", selected=())]) == U
    assert evidence_unit("ev_charging", hist, [row("HISTORICAL", "CONTRADICTORY")]) == U
    assert evidence_unit("ev_charging", hist, [row("PENDING_RECOMPUTE", "UNKNOWN")]) == U


def test_money_table() -> None:
    covered = {**SETTLED, "_windows_covered": True}
    # Zero selected heads on a settled, covered applicable category: known empty (NO_LINES), G.
    assert money_units("mini_grid", covered, []) == {"CANDIDATE_OPERATING_COST_EXPOSURE": G}
    assert money_units("ev_charging", covered, []) == {"GROSS_TARIFF_SCENARIO": G}
    # Line eligibility, exclusions and comparison diagnostics never erase a known selection.
    lines = [{"category": "POTENTIAL_PRODUCT_EXPOSURE", "eligibility": e} for e in
             ("UNPRICED", "WITHHELD", "INELIGIBLE", "CONFLICT")]
    assert money_units("cold_chain", covered, lines) == {"POTENTIAL_PRODUCT_EXPOSURE": G}
    # A selected category outside the mock APPLICABLE set is its own unit; other domains' categories are N.
    repair = money_units("cold_chain", covered, [{"category": "RECORDED_REPAIR"}])
    assert repair == {"POTENTIAL_PRODUCT_EXPOSURE": G, "RECORDED_REPAIR": G}
    assert "CANDIDATE_OPERATING_COST_EXPOSURE" not in repair
    # Cold/EV window coverage false (W3-02 UNKNOWN_COVERAGE input) is U even with an eligible line.
    uncovered = {**SETTLED, "_windows_covered": False}
    assert money_units("ev_charging", uncovered, [{"category": "GROSS_TARIFF_SCENARIO"}]) == {
        "GROSS_TARIFF_SCENARIO": U}
    # One covered EV Site beside an uncovered one: PARTIAL, not COMPLETE or UNKNOWN.
    units = [*money_units("ev_charging", covered, []).values(), *money_units("ev_charging", uncovered, []).values()]
    assert reduce_units(2, units) == "PARTIAL"
    # A historical cutoff without a selected head is missing: UNKNOWN for that Site's categories.
    assert set(money_units("mini_grid", {**SETTLED, "state": "UNKNOWN", "_windows_covered": False}, []).values()) \
        == {U}
