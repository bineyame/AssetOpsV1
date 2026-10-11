"""S3-01 phase 2: typed input set, cohort selection and the pure `dispatch-3` analytic."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest

from assetops_backend.analytics import dispatch_v3 as d3
from assetops_backend.analytics.assessment_inputs import (
    CONTROL_BATTERY_RESERVE,
    CONTROL_MINIMUM_RUNTIME,
    AcceptedReading,
    CohortMember,
    ControlValue,
    EvidenceQuery,
    EvidenceQueryResult,
    RoleBinding,
    Window,
    build_input_set,
)
from assetops_backend.analytics.cohort import select_cohort
from assetops_backend.sites.binding_roles import ROLE_SET_MINIGRID_1, ROLE_SET_MINIGRID_2, roles_for

T0 = datetime(2026, 10, 2, 0, 0, tzinfo=timezone.utc)
WINDOW = Window(T0, T0 + timedelta(days=1))
GW = UUID(int=1)
SRC = {"gen": UUID(int=11), "bat": UUID(int=12), "pv": UUID(int=13), "meter": UUID(int=14)}
ASSET = {"gen": UUID(int=21), "bat": UUID(int=22), "pv": UUID(int=23), "pcs": UUID(int=24),
         "f1": UUID(int=31), "f2": UUID(int=32), "f3": UUID(int=33)}
FOUNDATION = UUID(int=41)
BSET = UUID(int=42)
ROLES_BY_SET = {s: tuple(roles_for(s)) for s in (ROLE_SET_MINIGRID_1, ROLE_SET_MINIGRID_2)}


def at(h: int, m: int = 0) -> datetime:
    return T0 + timedelta(hours=h, minutes=m)


class Feed:
    """Builds accepted readings with per-stream sequences (one epoch unless named)."""

    def __init__(self) -> None:
        self.readings: list[AcceptedReading] = []
        self.seq: dict[tuple, int] = {}

    def add(self, src: str, role: str, asset: str, when: datetime, value: str, *, mean: bool = True,
            quality: str = "GOOD", epoch: str = "e1", seq: int | None = None) -> AcceptedReading:
        key = (src, epoch)
        self.seq[key] = self.seq.get(key, 0) + 1
        r = AcceptedReading(
            evidence_id=uuid4(), envelope_sha256=f"sha-{len(self.readings)}", batch_id=UUID(int=99),
            gateway_id=GW, source_id=SRC[src], sequence_epoch=epoch, sequence=seq or self.seq[key], role=role,
            asset_id=ASSET[asset], source_time=when, interval_start=when - timedelta(minutes=5) if mean else None,
            interval_end=when if mean else None, published_at=when, received_at=when, accepted_at=when,
            quality=quality, value=value, unit="kW", foundation_revision_id=FOUNDATION,
            binding_set_revision_id=BSET, binding_revision_id=UUID(int=43), source_mode="SIMULATED")
        self.readings.append(r)
        return r

    def instant(self, h: int, m: int, *, state: str | None = "RUNNING", load=("10", "10", "10"),
                pv: str | None = "20", dis: str | None = "20", soc: str | None = "80", epoch: str = "e1") -> None:
        t = at(h, m)
        if state:
            self.add("gen", "generator_state", "gen", t, state, mean=False, epoch=epoch)
        for asset, value in zip(("f1", "f2", "f3"), load):
            self.add("meter", "feeder_demand", asset, t, value, epoch=epoch)
        if pv is not None:
            self.add("pv", "pv_available_power", "pv", t, pv, epoch=epoch)
        if dis is not None:
            self.add("bat", "pcs_discharge_capability", "pcs", t, dis, epoch=epoch)
        if soc is not None:
            self.add("bat", "battery_soc", "bat", t, soc, mean=False, epoch=epoch)


def bindings(role_set: str = ROLE_SET_MINIGRID_2) -> tuple[RoleBinding, ...]:
    pairs = [("generator_state", "gen"), ("generator_power", "gen"), ("feeder_demand", "f1"),
             ("feeder_demand", "f2"), ("feeder_demand", "f3"), ("battery_soc", "bat")]
    if role_set == ROLE_SET_MINIGRID_2:
        pairs += [("pv_available_power", "pv"), ("pcs_discharge_capability", "pcs")]
    return tuple(RoleBinding(role, ASSET[a], T0 - timedelta(days=5), None, BSET, UUID(int=43), role_set)
                 for role, a in pairs)


def controls(reserve: str = "30", runtime: str | None = None) -> tuple[ControlValue, ...]:
    out = [ControlValue(CONTROL_BATTERY_RESERVE, reserve, "%", T0 - timedelta(days=5), None, FOUNDATION, "IMPORT")]
    if runtime:
        out.append(ControlValue(CONTROL_MINIMUM_RUNTIME, runtime, "min", T0 - timedelta(days=5), None,
                                FOUNDATION, "TEMPLATE"))
    return tuple(out)


def run(feed: Feed, *, role_set: str = ROLE_SET_MINIGRID_2, cohort=None, ctrl=None, window: Window = WINDOW):
    query = EvidenceQuery(UUID(int=7), UUID(int=8), "dispatch", window, at(23), cohort=cohort)
    result = EvidenceQueryResult(query, tuple(feed.readings), bindings(role_set), ctrl or controls(),
                                 (role_set,))
    selection = select_cohort(result.readings, window, cohort)
    inputs = build_input_set(result, selection, analytic_id=d3.ANALYTIC_ID, model_version=d3.MODEL_VERSION,
                             roles_by_set=ROLES_BY_SET)
    return inputs, d3.assess(inputs)


def run_interval(feed: Feed, h0: int, h1: int, **values) -> Feed:
    feed.instant(h0 - 1, 45, state="STOPPED", **{k: v for k, v in values.items() if k != "state"})
    for k in range((h1 - h0) * 4 + 1):
        feed.instant(h0 + k // 4, (k % 4) * 15, **values)
    feed.instant(h1, 15, state="STOPPED", **{k: v for k, v in values.items() if k != "state"})
    return feed


def test_two_capability_candidate_is_bounded_to_candidate_segments():
    inputs, result = run(run_interval(Feed(), 5, 6))
    assert inputs.cohort.status == "SELECTED_UNIQUE"
    [interval] = result.intervals
    assert interval.claim_level == d3.CANDIDATE
    assert interval.result["portions_minutes"]["candidate"] == "60"
    assert interval.result["interval"]["upper_minutes"] == "90"
    assert "never the whole interval" in interval.result["candidate_bound"]
    assert result.claim_level == d3.WINDOW_COMPLETE


def test_near_reserve_is_physical_necessary():
    _, result = run(run_interval(Feed(), 5, 6, pv="5", soc="35"))
    [interval] = result.intervals
    assert interval.claim_level == d3.NECESSARY
    assert interval.result["binding_constraints"] == ["BATTERY_NEAR_RESERVE"]


def test_capability_shortfall_is_necessary():
    _, result = run(run_interval(Feed(), 5, 6, pv="5", dis="5", soc="90"))
    assert result.intervals[0].result["binding_constraints"] == ["CAPABILITY_SHORTFALL"]


def test_roles_1_basis_never_gives_candidate_and_names_missing_role():
    feed = run_interval(Feed(), 5, 6, pv=None, dis=None)
    _, result = run(feed, role_set=ROLE_SET_MINIGRID_1)
    [interval] = result.intervals
    assert interval.claim_level == d3.INDETERMINATE
    assert any("missing role" in m for s in interval.result["segments"] for m in s["missing"])
    assert any(x.startswith("MISSING_ROLE: pv_available_power") for x in result.result["limitations"])
    assert result.claim_level == d3.WINDOW_LIMITED


def test_contradictory_same_role_readings_are_indeterminate():
    feed = run_interval(Feed(), 5, 5)
    feed.add("bat", "battery_soc", "bat", at(5), "60", mean=False)  # same channel-time, different value
    _, result = run(feed)
    [interval] = result.intervals
    assert interval.claim_level == d3.INDETERMINATE
    assert any("REPORTS_OVERLAP" in x for x in result.result["limitations"])


def test_minimum_runtime_withholds_candidate_but_claims_no_policy_necessary():
    _, result = run(run_interval(Feed(), 5, 6), ctrl=controls(runtime="30"))
    [interval] = result.intervals
    segments = interval.result["segments"]
    early = [s for s in segments if s["start"] < "2026-10-02T05:30"]
    assert early and all(s["classification"] == d3.INDETERMINATE for s in early)
    assert interval.claim_level == d3.CANDIDATE and interval.result["portions_minutes"]["candidate"] == "30"
    assert d3.NECESSARY not in {s["classification"] for s in segments}


def test_overlapping_epochs_of_one_source_are_ambiguous_and_explicitly_selectable():
    feed = run_interval(Feed(), 5, 6)
    run_interval(feed, 5, 6, epoch="e2", soc="50")
    inputs, result = run(feed)
    assert inputs.cohort.status == "AMBIGUOUS" and not result.intervals
    assert result.claim_level == d3.WINDOW_INDETERMINATE
    assert any(x.startswith("AMBIGUOUS_COHORT") for x in result.result["limitations"])
    chosen = tuple(CohortMember(GW, s, "e2") for s in SRC.values())
    inputs2, result2 = run(feed, cohort=chosen)
    assert inputs2.cohort.status == "SELECTED_EXPLICIT"
    assert {r.sequence_epoch for r in inputs2.readings} == {"e2"}
    assert result2.intervals and ":cohort:" in result2.intervals[0].assessment_key


def test_sequential_epochs_are_one_coherent_stream():
    feed = run_interval(Feed(), 3, 4)
    run_interval(feed, 8, 9, epoch="e2")
    inputs, result = run(feed)
    assert inputs.cohort.status == "SELECTED_UNIQUE" and len(result.intervals) == 2


def test_same_epoch_overlap_is_a_named_cohort_limit():
    feed = run_interval(Feed(), 5, 6)
    run_interval(feed, 5, 6, soc="50")  # a second run on the same epoch: later sequences, same times
    _, result = run(feed)
    assert result.claim_level == d3.WINDOW_INDETERMINATE
    kinds = {x.split(":")[0] for x in result.result["limitations"]}
    assert {"SEQUENCE_ORDER_INVERTED", "REPORTS_OVERLAP"} <= kinds
    assert all(i.claim_level == d3.INDETERMINATE for i in result.intervals)


def test_out_of_order_reading_marks_its_span():
    """The phase-2 fixture shape: a separate epoch whose later source time is sequenced first."""
    feed = run_interval(Feed(), 5, 6)
    first = feed.add("bat", "battery_soc", "bat", at(14, 15), "80", mean=False, epoch="ooo", seq=1)
    second = feed.add("bat", "battery_soc", "bat", at(14, 0), "81", mean=False, epoch="ooo", seq=2)
    inputs, result = run(feed)
    assert inputs.cohort.status == "SELECTED_UNIQUE"  # its span does not overlap epoch e1's
    [limit] = [x for x in inputs.cohort.limits if x.kind == "SEQUENCE_ORDER_INVERTED"]
    assert (limit.start, limit.end) == (at(14, 0), at(14, 15))
    assert set(limit.evidence_ids) == {str(first.evidence_id), str(second.evidence_id)}
    assert result.claim_level == d3.WINDOW_LIMITED
    assert result.intervals[0].claim_level == d3.CANDIDATE  # the 05:00 interval is outside the span


def test_inverted_span_inside_an_interval_makes_that_segment_indeterminate():
    feed = run_interval(Feed(), 5, 6)
    feed.add("bat", "battery_soc", "bat", at(6, 15), "80", mean=False, epoch="e1", seq=10_000)
    feed.add("bat", "battery_soc", "bat", at(5, 50), "80", mean=False, epoch="e1", seq=10_001)
    _, result = run(feed)
    [interval] = result.intervals
    hit = [s for s in interval.result["segments"] if s["classification"] == d3.INDETERMINATE]
    assert hit and all("SEQUENCE_ORDER_INVERTED" in " ".join(s["missing"]) for s in hit)
    assert interval.claim_level == d3.CANDIDATE and interval.result["portions_minutes"]["candidate"] == "45"


def test_bracket_only_stream_is_not_pulled_into_the_cohort():
    feed = run_interval(Feed(), 5, 6)
    feed.add("bat", "battery_soc", "bat", T0 + timedelta(days=1, hours=2), "70", mean=False, epoch="fixture")
    inputs, _ = run(feed)
    assert inputs.cohort.status == "SELECTED_UNIQUE"
    assert "fixture" not in {r.sequence_epoch for r in inputs.readings}


def test_input_hash_covers_digests_not_order_or_cutoff():
    feed = run_interval(Feed(), 5, 6)
    a, _ = run(feed)
    feed.readings.reverse()
    b, _ = run(feed)
    assert a.input_sha256 == b.input_sha256
    feed.readings[0] = replace(feed.readings[0], envelope_sha256="changed")
    c, _ = run(feed)
    assert c.input_sha256 != a.input_sha256
    later = build_input_set(
        EvidenceQueryResult(EvidenceQuery(UUID(int=7), UUID(int=8), "dispatch", WINDOW, at(23) + timedelta(days=3)),
                            tuple(b.readings), bindings(), controls(), (ROLE_SET_MINIGRID_2,)),
        b.cohort, analytic_id=d3.ANALYTIC_ID, model_version=d3.MODEL_VERSION, roles_by_set=ROLES_BY_SET)
    assert later.input_sha256 == b.input_sha256


def test_late_reading_changes_only_the_affected_interval_basis():
    feed = run_interval(Feed(), 3, 4)
    run_interval(feed, 8, 9)
    _, first = run(feed)
    feed.add("bat", "battery_soc", "bat", at(8, 40), "31", mean=False)  # later instant inside interval 2
    _, second = run(feed)
    assert first.intervals[0].basis_sha256 == second.intervals[0].basis_sha256
    assert first.intervals[1].basis_sha256 != second.intervals[1].basis_sha256
    assert first.basis_sha256 != second.basis_sha256


def test_wrong_model_version_is_refused():
    inputs, _ = run(run_interval(Feed(), 5, 6))
    with pytest.raises(ValueError):
        d3.assess(replace(inputs, model_version="dispatch-2"))


def test_window_names_the_span_where_a_capability_role_is_unbound():
    feed = run_interval(Feed(), 14, 15)
    query = EvidenceQuery(UUID(int=7), UUID(int=8), "dispatch", WINDOW, at(23))
    late_bound = tuple(replace(b, valid_from=at(12)) if b.role in ("pv_available_power", "pcs_discharge_capability")
                       else b for b in bindings())
    result = EvidenceQueryResult(query, tuple(feed.readings), late_bound, controls(), (ROLE_SET_MINIGRID_2,))
    inputs = build_input_set(result, select_cohort(result.readings, WINDOW), analytic_id=d3.ANALYTIC_ID,
                             model_version=d3.MODEL_VERSION, roles_by_set=ROLES_BY_SET)
    window = d3.assess(inputs)
    missing = [x for x in window.result["limitations"] if x.startswith("MISSING_ROLE")]
    assert len(missing) == 2 and all("2026-10-02T00:00:00.000000Z..2026-10-02T12:00:00.000000Z" in x for x in missing)
    assert window.intervals[0].claim_level == d3.CANDIDATE  # the 14:00 interval is after the binding


def test_in_interval_capability_gap_makes_window_limited_and_names_it():
    feed = run_interval(Feed(), 5, 7)
    feed.readings = [x for x in feed.readings
                     if not (x.role == "pv_available_power" and at(5, 30) <= x.source_time < at(6, 15))]
    _, result = run(feed)
    [interval] = result.intervals
    assert interval.result["portions_minutes"]["indeterminate"] != "0"
    assert result.claim_level == d3.WINDOW_LIMITED
    assert any(x.startswith("EVIDENCE_GAP:") for x in result.result["limitations"])
