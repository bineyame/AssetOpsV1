"""S4-02b phase 1: the pure `fuel-cost-1` quantity, window price selection and consequence basis.

Every case of `conversions/fuel-cost-1-cases-v1.json` (Architect C4 positive and unavailable fixtures) runs
through `quantify`; unavailable cases must carry no numeric high or amount.
"""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from fractions import Fraction
from pathlib import Path

import pytest

from assetops_backend.financials import fuel_cost as fc

BACKEND = Path(__file__).resolve().parents[1]
SPEC = json.loads((BACKEND / "conversions" / "fuel-cost-1-cases-v1.json").read_text(encoding="utf-8"))
DAY = datetime.fromisoformat(SPEC["day"]).replace(tzinfo=timezone.utc)


def at(hhmm: str | None) -> datetime | None:
    if hhmm is None:
        return None
    h, m = hhmm.split(":")
    return DAY + timedelta(hours=int(h), minutes=int(m))


def build(case: dict) -> fc.FindingInput:
    d = SPEC["defaults"]
    segments = tuple(fc.Segment(at(s), at(e), observed, cls) for s, e, cls, observed in case["segments"])
    spans = case.get("spans") or [[s, e] for s, e, cls, observed in case["segments"]
                                  if cls == fc.CANDIDATE and observed]
    readings, in_run = [], set()
    for i, row in enumerate(case["readings"], 1):
        start, end, value = row[:3]
        opts = {**d["reading"], **(row[3] if len(row) > 3 else {})}
        rid = f"r{i}"
        readings.append(fc.PowerReading(rid, d["generator_asset_id"], at(start), at(end), value, opts["unit"],
                                        opts["quality"], f"sha-{rid}", opts["foundation"], opts["binding"]))
        if opts["in_run"]:
            in_run.add(rid)
    foundations = tuple(fc.FoundationRevision(x["id"], at(x["valid_from"]), at(x["valid_to"]),
                                              tuple(tuple(v) for v in x["sfc"]))
                        for x in case.get("foundations", d["foundations"]))
    bindings = tuple(fc.BindingRevision(x["id"], at(x["valid_from"]), at(x["valid_to"]))
                     for x in case.get("bindings", d["bindings"]))
    assessment = fc.AssessmentInput("A1", "RUN1", "INTERVAL", True, d["generator_asset_id"], segments,
                                    frozenset(in_run), frozenset(f.revision_id for f in foundations))
    all_times = [t for s in segments for t in (s.start, s.end)] + [t for r in readings
                                                                    for t in (r.interval_start, r.interval_end)]
    return fc.FindingInput("T", "S", "FIND", "FREV", d["generator_asset_id"], min(all_times + [segments[0].start]),
                           max(all_times + [segments[-1].end]), case.get("lifecycle", d["lifecycle"]),
                           tuple(fc.CandidateSpan(at(s), at(e), "A1") for s, e in spans), (assessment,),
                           tuple(readings), foundations, bindings)


CASES = {c["case_id"]: c for c in SPEC["cases"]}


def test_fixture_pins_the_reviewed_parameter_version() -> None:
    assert SPEC["parameter_sha256"] == fc.PARAMETER_SHA256
    assert fc.MULTIPLIER == Decimal("1.10") and fc.PARAMETER_VERSION["value"] == "1.10"
    assert "not a calibrated" in fc.PARAMETER_VERSION["limitation"]
    assert fc.FORMULA_VERSION == "fuel-cost-1+fuel-cost-1/sfc-upper-multiplier/v1"


def test_fixture_covers_every_architect_case() -> None:
    reasons = {c["expect"].get("reason") for c in SPEC["cases"]}
    assert {"POWER_MISSING", "POWER_COVERAGE_GAP", "INTERVAL_CROSSES_NECESSARY", "INTERVAL_CROSSES_INDETERMINATE",
            "INTERVAL_CROSSES_UNOBSERVED", "INTERVAL_OUTSIDE_FINDING", "POWER_OVERLAP_CONFLICT", "SFC_MISSING",
            "SFC_NONPOSITIVE", "SFC_CONFLICT", "SFC_CHANGES_WITHIN_INTERVAL",
            "BINDING_CHANGES_WITHIN_INTERVAL"} <= reasons
    assert sum(1 for c in SPEC["cases"] if c["expect"]["state"] == "AVAILABLE") >= 3


@pytest.mark.parametrize("case_id", sorted(CASES))
def test_case(case_id: str) -> None:
    case = CASES[case_id]
    q = fc.quantify(build(case))
    expect = case["expect"]
    assert q.state == expect["state"], (q.reason, q.detail)
    if expect["state"] == "AVAILABLE":
        assert q.reason is None and q.low == Decimal(0)
        assert q.high == Decimal(expect["quantity_high"])
        assert str(q.high) == expect["quantity_high"] or Decimal(str(q.high)) == Decimal(expect["quantity_high"])
        assert len(q.intervals) == expect["counted"]
        assert len({c.evidence_id for c in q.intervals}) == len(q.intervals)  # each interval once
        if "exact" in expect:
            assert q.high_exact == Fraction(expect["exact"]) and q.high >= q.high_exact
        assert q.high_exact == Fraction(fc.MULTIPLIER) * sum(c.litres for c in q.intervals)
    else:
        assert q.reason == expect["reason"], q.detail
        assert q.high is None and q.low is None and q.high_exact is None and q.intervals == ()
        c = fc.consequence(build(case), q, fc.PriceSelection("PRICED", None, "P", Decimal("1.25"), "USD"))
        assert c.state == "QUANTITY_UNAVAILABLE" and c.amount_low is None and c.amount_high is None
        assert c.price.state == "NOT_EVALUATED"


def test_shared_edge_interval_is_counted_once_and_names_both_spans() -> None:
    q = fc.quantify(build(CASES["P2"]))
    edge = [c for c in q.intervals if len(c.covered_spans) == 2]
    assert len(edge) == 1 and edge[0].duration_seconds == 600
    assert len(edge[0].covered_spans) == CASES["P2"]["expect"]["edge_reading_covers_spans"]


def test_never_max_mean_times_segment_duration() -> None:
    """The mutation `max(mean) x segment minutes` would give 30 x 20/60 x 0.3 x 1.1 = 3.3, not 2.64."""
    q = fc.quantify(build(CASES["P2"]))
    assert q.high == Decimal("2.64") and q.high != Decimal("3.3")


def test_open_interval_never_reads_upper_minutes() -> None:
    assert "upper_minutes" not in {f.name for f in fc.FindingInput.__dataclass_fields__.values()}
    assert "upper_minutes" not in {f for f in fc.AssessmentInput.__dataclass_fields__}
    assert fc.quantify(build(CASES["P3"])).high == Decimal("1.65")


def test_a_non_good_reading_is_not_selected_and_leaves_a_gap() -> None:
    case = json.loads(json.dumps(CASES["P1"]))
    case["readings"][2].append({"quality": "SUSPECT"})
    q = fc.quantify(build(case))
    assert (q.state, q.reason) == ("QUANTITY_UNAVAILABLE", "POWER_COVERAGE_GAP")


def test_a_reading_from_another_generator_is_ignored() -> None:
    f = build(CASES["P1"])
    other = replace(f.readings[0], evidence_id="x", asset_id="gen-2", interval_start=f.readings[0].interval_start,
                    interval_end=f.readings[1].interval_end)
    assert fc.quantify(replace(f, readings=f.readings + (other,))).high == Decimal("3.3")


def test_digests_are_stable_and_input_sensitive() -> None:
    f = build(CASES["P1"])
    q = fc.quantify(f)
    price = fc.PriceSelection("PRICED", None, "P1", Decimal("1.25"), "USD")
    a, b = fc.consequence(f, q, price), fc.consequence(build(CASES["P1"]), fc.quantify(build(CASES["P1"])), price)
    assert a.basis_sha256 == b.basis_sha256 and a.technical_input_sha256 == b.technical_input_sha256
    assert (a.state, a.amount_low, a.amount_high, a.currency) == ("PRICED", Decimal(0), Decimal("4.125"), "USD")
    repriced = fc.consequence(f, q, fc.PriceSelection("PRICED", None, "P4", Decimal("1.28"), "USD"))
    assert repriced.technical_input_sha256 == a.technical_input_sha256 and repriced.basis_sha256 != a.basis_sha256
    moved = replace(f, readings=(replace(f.readings[0], envelope_sha256="other"),) + f.readings[1:])
    assert fc.consequence(moved, fc.quantify(moved), price).technical_input_sha256 != a.technical_input_sha256
    unpriced = fc.consequence(f, q, fc.PriceSelection("UNPRICED", "NO_PRICE"))
    assert (unpriced.state, unpriced.amount_high, unpriced.currency) == ("UNPRICED", None, None)


# ---- window price selection (packet item 3) -------------------------------------------------------------------

UTC = timezone.utc
W0, W1 = datetime(2026, 10, 6, 8, tzinfo=UTC), datetime(2026, 10, 6, 9, tzinfo=UTC)
REVS = {"v1": {"id": "v1", "unit": "currency/L", "value": Decimal("1.25"), "currency": "USD",
               "assumption_key": "diesel_price_per_litre"},
        "v4": {"id": "v4", "unit": "currency/L", "value": Decimal("1.28"), "currency": "USD",
               "assumption_key": "diesel_price_per_litre"}}


def assign(rev: str, lo: datetime, hi: datetime | None, aid: str = "a") -> dict:
    return {"id": aid, "revision_id": rev, "valid_from": lo, "valid_to": hi}


def test_price_valid_for_the_whole_window_is_selected() -> None:
    s = fc.select_window_price([assign("v1", datetime(2026, 1, 1, tzinfo=UTC), None)], REVS, W0, W1)
    assert (s.state, s.revision_id, s.value, s.currency) == ("PRICED", "v1", Decimal("1.25"), "USD")


def test_half_open_boundaries() -> None:
    assert fc.select_window_price([assign("v1", W1, None)], REVS, W0, W1).reason == "NO_PRICE"
    assert fc.select_window_price([assign("v1", W0 - timedelta(days=1), W0)], REVS, W0, W1).reason == "NO_PRICE"
    assert fc.select_window_price([assign("v1", W0, W1)], REVS, W0, W1).state == "PRICED"


def test_a_price_boundary_inside_the_window_leaves_it_unpriced() -> None:
    mid = W0 + timedelta(minutes=30)
    s = fc.select_window_price([assign("v1", W0 - timedelta(days=1), mid, "a"), assign("v4", mid, None, "b")],
                               REVS, W0, W1)
    assert (s.state, s.reason, s.value) == ("UNPRICED", "PRICE_SPANS_WINDOW", None)
    partial = fc.select_window_price([assign("v1", mid, None)], REVS, W0, W1)
    assert partial.reason == "PRICE_SPANS_WINDOW"


def test_overlapping_assignments_are_a_conflict_and_bad_units_refused() -> None:
    s = fc.select_window_price([assign("v1", W0, None, "a"), assign("v4", W0, None, "b")], REVS, W0, W1)
    assert s.reason == "PRICE_CONFLICT"
    bad = {"v1": {**REVS["v1"], "unit": "currency/kWh"}}
    assert fc.select_window_price([assign("v1", W0, None)], bad, W0, W1).reason == "PRICE_UNIT_MISMATCH"
    assert fc.select_window_price([assign("vX", W0, None)], REVS, W0, W1).reason == "PRICE_REVISION_MISSING"


def test_unpriced_bases_over_different_price_boundaries_differ() -> None:
    """Review of idempotency: UNPRICED(PRICE_SPANS_WINDOW) twice over different boundaries is not one basis."""
    f = build(CASES["P1"])
    q = fc.quantify(f)
    w0, w1 = f.window_start, f.window_end
    mid1, mid2 = w0 + timedelta(minutes=10), w0 + timedelta(minutes=20)
    a = fc.select_window_price([assign("v1", w0, mid1, "a1"), assign("v4", mid1, None, "a2")], REVS, w0, w1)
    b = fc.select_window_price([assign("v1", w0, mid2, "a3"), assign("v4", mid2, None, "a4")], REVS, w0, w1)
    assert a.reason == b.reason == "PRICE_SPANS_WINDOW"
    assert fc.consequence(f, q, a).basis_sha256 != fc.consequence(f, q, b).basis_sha256
