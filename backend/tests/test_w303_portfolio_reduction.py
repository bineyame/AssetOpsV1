"""W3-03 run 1a: closure 5 S4 exact Evidence and Financials reductions (pure, exhaustive class/count tables)."""

from __future__ import annotations

from itertools import product

import pytest

from assetops_backend.estate.portfolio import (
    G, N, U, evidence_unit, finding_unit, money_pending, money_units, reduce_units, settled)

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
    # r1a: UNKNOWN freshness alone does not reject an otherwise selected basis.
    assert settled({**SETTLED, "source_freshness": "UNKNOWN"})
    # r1a2 item 1: a selected-as-of HISTORICAL head is settled despite an outstanding PENDING/FAILED job marker.
    for job in ("PENDING", "FAILED"):
        hist = {**SETTLED, "state": "HISTORICAL", "job_state": job}
        assert settled(hist)
        assert finding_unit("mini_grid", hist) == G and evidence_unit("mini_grid", hist, [row("HISTORICAL")]) == G
        assert money_units("mini_grid", {**hist, "_windows_covered": True}, []) == {
            "CANDIDATE_OPERATING_COST_EXPOSURE": G}
        # Controls: the same marker on a CURRENT basis stays U.
        assert not settled({**SETTLED, "job_state": job}) and finding_unit("mini_grid", {**SETTLED, "job_state": job}) == U
    # An absent as-of head (no selected head), a missing/pending match or a stale source stays U under HISTORICAL.
    for change in ({"job_state": "NONE"}, {"match_state": "MISSING"}, {"match_state": "PENDING"},
                   {"source_freshness": "STALE"}, {"state": "UNKNOWN"}):
        assert not settled({**SETTLED, "state": "HISTORICAL", **change})
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
    # r1a2 item 2: a cold `withheld` result or an EV ERROR_PENDING guard leaves the window uncovered: M is U,
    # PARTIAL beside a known unit, otherwise UNKNOWN; the selected PENDING line marks it as explicit pending work.
    for domain, category in (("cold_chain", "POTENTIAL_PRODUCT_EXPOSURE"), ("ev_charging", "GROSS_TARIFF_SCENARIO")):
        guarded = [{"category": category, "eligibility": "PENDING"}]
        assert money_units(domain, uncovered, guarded) == {category: U}
        assert money_pending(uncovered, guarded) and not money_pending(covered, guarded)
        assert not money_pending(uncovered, [{"category": category, "eligibility": "WITHHELD"}])
        alone = list(money_units(domain, uncovered, guarded).values())
        assert reduce_units(1, alone) == "UNKNOWN"
        assert reduce_units(2, [*alone, *money_units("mini_grid", covered, []).values()]) == "PARTIAL"
    # r1b Q-1b-3: the private `_pending_guard` alone (a cold withheld / EV ERROR_PENDING window with no selected
    # line) is pending work; M stays U for that Site (PARTIAL beside a covered Site) and no line is invented.
    guard_only = {**uncovered, "_pending_guard": True}
    for domain, category in (("cold_chain", "POTENTIAL_PRODUCT_EXPOSURE"), ("ev_charging", "GROSS_TARIFF_SCENARIO")):
        assert money_pending(guard_only, []) and money_units(domain, guard_only, []) == {category: U}
        assert reduce_units(2, [*money_units(domain, guard_only, []).values(),
                                *money_units("mini_grid", covered, []).values()]) == "PARTIAL"
    # r1b3 P-1b-5: R4's independent line branch. An uncovered Site with a selected PENDING line is pending with
    # `_pending_guard` absent or explicitly false (the same value under `.get`); covered and nonpending controls
    # are false. r1b3 P-1b-1/P-1b-4 rest on this table plus the guard-only case above.
    pending_line = [{"category": "POTENTIAL_PRODUCT_EXPOSURE", "eligibility": "PENDING"}]
    for cov in (uncovered, {**uncovered, "_pending_guard": False}):
        assert money_pending(cov, pending_line)
        assert not money_pending({**cov, "_windows_covered": True}, pending_line)
        assert not money_pending(cov, [{**pending_line[0], "eligibility": "ELIGIBLE"}])
    # Uncovered without the guard or a PENDING line is UNKNOWN, not PENDING; a false guard changes nothing.
    assert not money_pending({**uncovered, "_pending_guard": False}, [])
    assert not money_pending(uncovered, [{"category": "GROSS_TARIFF_SCENARIO", "eligibility": "UNPRICED"}])
    # A historical cutoff without a selected head is missing: UNKNOWN for that Site's categories.
    assert set(money_units("mini_grid", {**SETTLED, "state": "UNKNOWN", "_windows_covered": False}, []).values()) \
        == {U}
