"""W2-06 commit 2: pure `ev-session/1` correlation rules over hand-built accepted records.

Authority: `.agent/W2-06-build-spec.md` "Total ordering and state table", "Coverage and JSON", Run 1 rulings
R1-R9, Run 2 rulings Q2-Q7, Q14, Q15 and Run 3 rulings P1-P5.
Every row of the state table is exercised here; the pinned public
vectors are checked separately once `ev-w206-vectors.json` lands.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from itertools import count
from uuid import UUID

import pytest

from assetops_backend.analytics import ev
from assetops_backend.financials.fuel_cost import canonical_json

TENANT = UUID("00000000-0000-4000-8000-000000000001")
SITE = UUID("00000000-0000-4000-8000-000000000002")
CHARGER = UUID("00000000-0000-4000-8000-0000000000c0")
C1 = UUID("00000000-0000-4000-8000-0000000000c1")
C2 = UUID("00000000-0000-4000-8000-0000000000c2")
METER = UUID("00000000-0000-4000-8000-0000000000e1")
FOUNDATION = UUID("00000000-0000-4000-8000-0000000000f0")
BINDING = UUID("00000000-0000-4000-8000-0000000000b0")
OTHER_BINDING = UUID("00000000-0000-4000-8000-0000000000b9")
PROFILE = "simulator-lab-gateway-ev/1"
SOURCE_CLASS = "REGISTERED_SIMULATION"
SOURCE = UUID("00000000-0000-4000-8000-0000000000a1")
S = "S-1"

_ids = count(1)
_IDENTITY = ("binding_revision_id", "binding_set_revision_id", "role", "source_id", "device_id", "signal_id")


def at(minute: int, second: int = 0, micro: int = 0) -> datetime:
    return datetime(2026, 10, 6, 8, 0, tzinfo=timezone.utc) + timedelta(minutes=minute, seconds=second,
                                                                          microseconds=micro)


def _record(**fields) -> ev.EvRecord:
    n = next(_ids)
    base = dict(report_key=None, report_sha256=None, batch_external_id=None, ordinal=None,
                accepted_evidence_id=UUID(int=0x1000 + n), envelope_sha256=f"{n:064x}", interval_start=None,
                interval_end=None, connector_id=None, session_id=None, record_kind=None, measurement=None,
                quality="GOOD", value=None, unit=None, event_id=None, outcome=None, asset_id=C1,
                sequence_epoch=1, clock_attested=True, source_class=SOURCE_CLASS)
    base.update(fields)
    # q3 P2: by default the accepted row's identity is exactly its asset's member of the selected set.
    found = MEMBERS.get(base["asset_id"])
    identity = dict.fromkeys(_IDENTITY) if found is None else dict(
        binding_revision_id=found.binding_revision_id, binding_set_revision_id=BINDING, role=found.role,
        source_id=str(found.source_id), device_id=found.device_id, signal_id=found.signal_id)
    for key, value in identity.items():
        base.setdefault(key, value)
    return ev.EvRecord(**base)


def event(kind: str, t: datetime, session: str | None = S, **kw) -> ev.EvRecord:
    return _record(family="EVENT", record_kind=kind, source_time=t, session_id=session, **kw)


def meter(a: datetime, b: datetime, kwh: str, session: str | None = S, **kw) -> ev.EvRecord:
    return _record(family="MEASUREMENT", measurement="INTERVAL_DELTA", source_time=b, interval_start=a,
                   interval_end=b, value=kwh, unit="kWh", session_id=session, **kw)


def mean(a: datetime, b: datetime, kw_value: str, **kw) -> ev.EvRecord:
    return _record(family="MEASUREMENT", measurement="INTERVAL_MEAN", source_time=b, interval_start=a,
                   interval_end=b, value=kw_value, unit="kW", **kw)


def state(t: datetime, value: str, **kw) -> ev.EvRecord:
    return _record(family="MEASUREMENT", measurement="STATE_AT_INSTANT", source_time=t, value=value,
                   unit="state", **kw)


def connector(asset: UUID) -> ev.EvConnector:
    return ev.EvConnector(asset_id=asset, charger_asset_id=CHARGER, connector_id=None,
                          max_power_kw=Decimal("60.0"), meter_resolution_kwh=Decimal("0.001"),
                          meter_error_bound_kwh=Decimal("0.001"), clock_error_bound_s=Decimal("30.0"),
                          status_cadence_min=Decimal("1.0"), meter_cadence_min=Decimal("5.0"),
                          charger_max_power_kw=Decimal("120.0"))


def member(asset: UUID, n: int, **kw) -> ev.EvBindingMember:
    fields = dict(binding_revision_id=UUID(int=0xB100 + n), binding_set_revision_id=BINDING, role=f"role-{n}",
                  asset_id=asset, source_id=SOURCE, device_id=f"dev-{n}", signal_id=f"sig-{n}",
                  valid_from=at(-120), valid_to=None)
    fields.update(kw)
    return ev.EvBindingMember(**fields)


MEMBERS = {C1: member(C1, 1), C2: member(C2, 2), METER: member(METER, 3)}


def inputs(*records: ev.EvRecord, known_at: datetime | None = None,
           members: tuple[ev.EvBindingMember, ...] | None = None) -> ev.EvInputs:
    return ev.EvInputs(tenant_id=TENANT, site_id=SITE,
                       window=ev.EvWindow(at(0), at(60), known_at or at(60)), records=tuple(records),
                       connectors=(connector(C1), connector(C2)), foundation_revision_id=FOUNDATION,
                       binding_revision_id=BINDING, mapping_profile_id=PROFILE, source_class=SOURCE_CLASS,
                       binding_members=tuple(MEMBERS.values()) if members is None else members)


def run(*records: ev.EvRecord) -> ev.EvAssessment:
    return ev.assess(inputs(*records))


def only(result: ev.EvAssessment) -> ev.EvSession:
    assert len(result.sessions) == 1
    return result.sessions[0]


def use(session: ev.EvSession, record: ev.EvRecord) -> tuple[str, str | None]:
    found = [link for link in session.links if link.evidence_id == record.accepted_evidence_id]
    assert len(found) == 1, f"{record.record_kind or record.measurement} not linked exactly once"
    return found[0].use, found[0].reason


def linked(session: ev.EvSession, record: ev.EvRecord) -> bool:
    return any(link.evidence_id == record.accepted_evidence_id for link in session.links)


def full_meters(start: int, end: int) -> list[ev.EvRecord]:
    return [meter(at(m), at(m + 1), "1") for m in range(start, end)]


# --- state table -----------------------------------------------------------------------------------------------


def test_start_end_with_full_meter_cover_is_completed_and_complete() -> None:
    start, end = event("EV_SESSION_START", at(1)), event("EV_SESSION_END", at(4))
    meters = full_meters(1, 4)
    s = only(run(start, end, *meters))
    assert (s.state, s.start_at, s.end_at) == ("COMPLETED", at(1), at(4))
    assert s.start_bounds == (at(1), at(1)) and s.end_bounds == (at(4), at(4))
    assert (s.supported_kwh, s.energy_complete, s.unknown_meter_seconds, s.reason_codes) == (
        Decimal("3.000"), True, 0, ())
    assert ev.plain(s.supported_kwh) == "3.000"
    assert use(s, start) == use(s, end) == ("SUPPORT", None)
    assert [(i.kwh, i.error_bound_kwh, i.use, i.reason) for i in s.intervals] == [
        (Decimal("1.000"), Decimal("0.002"), "SUPPORT", None)] * 3
    assert s.fault_evidence_id is None and s.finding_support == () and s.finding_support_sha256 is None


def test_start_alone_is_incomplete_with_zero_span() -> None:
    s = only(run(event("EV_SESSION_START", at(1))))
    assert (s.state, s.end_at, s.end_bounds) == ("INCOMPLETE", None, (None, None))
    assert (s.supported_kwh, s.energy_complete, s.unknown_meter_seconds, s.reason_codes) == (
        None, False, 0, ("MISSING_TERMINAL",))


def test_incomplete_span_ends_at_latest_meter_and_counts_inner_gap() -> None:
    start = event("EV_SESSION_START", at(1))
    s = only(run(start, meter(at(1), at(2), "1"), meter(at(3), at(4), "1"), state(at(10), "CHARGING")))
    assert s.state == "INCOMPLETE" and s.end_at is None
    assert (s.supported_kwh, s.unknown_meter_seconds, s.reason_codes) == (
        Decimal("2.000"), 60, ("MISSING_TERMINAL", "METER_GAP"))
    assert s.energy_complete is False


def test_state_after_observed_span_is_not_linked_and_state_inside_is_context() -> None:
    start = event("EV_SESSION_START", at(1))
    inside, after = state(at(1), "CHARGING"), state(at(5), "CHARGING")
    s = only(run(start, meter(at(1), at(2), "1"), inside, after))
    assert use(s, inside) == ("CONTEXT", None) and not linked(s, after)


def test_start_plus_abort_without_fault_is_observed_abort_without_finding() -> None:
    start, abort = event("EV_SESSION_START", at(1)), event("EV_SESSION_ABORT", at(3))
    s = only(run(start, abort, *full_meters(1, 3)))
    assert (s.state, s.end_at, s.reason_codes, s.energy_complete) == ("OBSERVED_ABORT", at(3), (), True)
    assert s.fault_evidence_id is None and not s.qualified_fault_abort and s.finding_support == ()


def test_abort_with_contemporaneous_same_session_fault_supports_a_finding() -> None:
    start, fault, abort = (event("EV_SESSION_START", at(1)), event("EV_CONNECTOR_FAULT", at(3, 20)),
                           event("EV_SESSION_ABORT", at(3)))
    result = run(start, fault, abort, *full_meters(1, 3))
    s = only(result)
    assert s.state == "OBSERVED_ABORT" and s.fault_evidence_id == fault.accepted_evidence_id
    assert use(s, fault) == ("SUPPORT", None)
    support = sorted([str(r.accepted_evidence_id), r.envelope_sha256] for r in (start, fault, abort))
    assert [list(p) for p in s.finding_support] == support
    assert s.finding_support_sha256 == hashlib.sha256(canonical_json(support).encode()).hexdigest()
    assert result.denominator["fault_aborted"] == 1


def test_fault_beyond_the_clock_bound_of_abort_is_context_only() -> None:
    start, fault, abort = (event("EV_SESSION_START", at(1)), event("EV_CONNECTOR_FAULT", at(2)),
                           event("EV_SESSION_ABORT", at(3)))
    s = only(run(start, fault, abort))
    assert use(s, fault) == ("CONTEXT", None) and s.fault_evidence_id is None


def test_fault_on_another_connector_never_associates() -> None:
    start, abort = event("EV_SESSION_START", at(1)), event("EV_SESSION_ABORT", at(3))
    fault = event("EV_CONNECTOR_FAULT", at(3), session=None, asset_id=C2)
    s = only(run(start, abort, fault))
    assert not linked(s, fault) and s.fault_evidence_id is None


def test_pre_start_fault_is_context_connector_mismatch_never_support() -> None:
    fault = event("EV_CONNECTOR_FAULT", at(0))
    start, abort = event("EV_SESSION_START", at(5)), event("EV_SESSION_ABORT", at(6))
    s = only(run(fault, start, abort))
    assert use(s, fault) == ("CONTEXT", "CONNECTOR_MISMATCH")
    assert s.fault_evidence_id is None and "CONNECTOR_MISMATCH" in s.reason_codes


def test_event_straddling_start_inside_clock_bound_is_excluded_and_cannot_close() -> None:
    start, end = event("EV_SESSION_START", at(5)), event("EV_SESSION_END", at(4, 40))
    s = only(run(start, end))
    assert use(s, end) == ("EXCLUDED", "CLOCK_UNATTESTED")
    assert s.state == "INCOMPLETE" and s.end_bounds == (None, None)
    assert s.reason_codes == ("MISSING_TERMINAL", "CLOCK_UNATTESTED")


def test_simultaneous_distinct_terminals_are_contradictory_with_null_quantities() -> None:
    start = event("EV_SESSION_START", at(1))
    end, abort = event("EV_SESSION_END", at(4)), event("EV_SESSION_ABORT", at(4))
    meters = full_meters(1, 4)
    result = run(start, end, abort, *meters)
    s = only(result)
    assert (s.state, s.end_at, s.end_bounds) == ("CONTRADICTORY", None, (at(4), at(4)))
    assert (s.supported_kwh, s.energy_complete, s.unknown_meter_seconds) == (None, None, None)
    assert s.reason_codes == ("CONFLICTING_TERMINAL",)
    assert use(s, end) == use(s, abort) == ("CONTEXT", "CONFLICTING_TERMINAL")
    assert all((i.use, i.reason) == ("EXCLUDED", "CONFLICTING_TERMINAL") for i in s.intervals)
    assert len(s.intervals) == 3 and s.fault_evidence_id is None
    assert result.claim_level == "CONTRADICTORY" and result.status_state == "CONTRADICTORY"


def test_two_ends_are_contradictory_with_min_max_end_bounds() -> None:
    start = event("EV_SESSION_START", at(1))
    s = only(run(start, event("EV_SESSION_END", at(30)), event("EV_SESSION_END", at(31))))
    assert s.state == "CONTRADICTORY" and s.end_bounds == (at(30), at(31))


def test_orphan_abort_is_window_context_without_session_or_start_count() -> None:
    abort = event("EV_SESSION_ABORT", at(3))
    result = run(abort)
    assert result.sessions == () and result.orphan_terminal_ids == (abort.accepted_evidence_id,)
    assert result.denominator["started"] == 0 and result.denominator["orphan"] == 1
    assert result.claim_level == "UNKNOWN" and result.status_state == "NO_SESSIONS_OBSERVED"


def test_fault_only_creates_no_session_and_no_orphan() -> None:
    result = run(event("EV_CONNECTOR_FAULT", at(0), session=None),
                 event("EV_CONNECTOR_CLEAR", at(5), session=None))
    assert result.sessions == () and result.orphan_terminal_ids == ()
    assert result.denominator == {"started": 0, "completed": 0, "observed_abort": 0, "incomplete": 0,
                                  "contradictory": 0, "orphan": 0, "confirmed_delivery": 0, "fault_aborted": 0}


def test_empty_window() -> None:
    result = run()
    assert result.sessions == () and result.claim_level == "UNKNOWN"
    assert result.status_state == "NO_SESSIONS_OBSERVED"
    assert result.assessment_key == "ev-session/1:2026-10-06T08:00:00.000000Z:2026-10-06T09:00:00.000000Z"


def test_zero_delta_covered_interval_is_support_and_numeric_zero() -> None:
    start, end = event("EV_SESSION_START", at(1)), event("EV_SESSION_END", at(2))
    zero = meter(at(1), at(2), "0")
    s = only(run(start, end, zero))
    assert use(s, zero) == ("SUPPORT", None)
    assert (ev.plain(s.supported_kwh), s.energy_complete, s.unknown_meter_seconds) == ("0.000", True, 0)


def test_completed_without_meters_has_null_energy_and_gap() -> None:
    s = only(run(event("EV_SESSION_START", at(1)), event("EV_SESSION_END", at(2))))
    assert (s.supported_kwh, s.energy_complete, s.unknown_meter_seconds, s.reason_codes) == (
        None, False, 60, ("METER_GAP",))


def test_overlapping_deltas_are_both_excluded_and_gap_computed_after_removal() -> None:
    start, end = event("EV_SESSION_START", at(1)), event("EV_SESSION_END", at(4))
    a, b, c = meter(at(1), at(3), "2"), meter(at(2), at(3), "1"), meter(at(3), at(4), "1")
    s = only(run(start, end, a, b, c))
    assert use(s, a) == use(s, b) == ("EXCLUDED", "METER_OVERLAP") and use(s, c) == ("SUPPORT", None)
    assert (s.supported_kwh, s.unknown_meter_seconds) == (Decimal("1.000"), 120)
    assert s.reason_codes == ("METER_GAP", "METER_OVERLAP")


def test_adjacent_deltas_do_not_overlap() -> None:
    start, end = event("EV_SESSION_START", at(1)), event("EV_SESSION_END", at(3))
    s = only(run(start, end, meter(at(1), at(2), "1"), meter(at(2), at(3), "1")))
    assert s.reason_codes == () and s.energy_complete is True


def test_suspect_event_is_context_source_unverified_and_suspect_meter_is_meter_invalid() -> None:
    start, end = event("EV_SESSION_START", at(1)), event("EV_SESSION_END", at(3))
    clear = event("EV_CONNECTOR_CLEAR", at(2), quality="SUSPECT")
    bad = meter(at(1), at(2), "1", quality="SUSPECT")
    s = only(run(start, end, clear, bad, meter(at(2), at(3), "1")))
    assert use(s, clear) == ("CONTEXT", "SOURCE_UNVERIFIED")
    assert use(s, bad) == ("EXCLUDED", "METER_INVALID")
    assert s.reason_codes == ("METER_GAP", "METER_INVALID", "SOURCE_UNVERIFIED")


def test_suspect_terminal_does_not_close() -> None:
    start, end = event("EV_SESSION_START", at(1)), event("EV_SESSION_END", at(3), quality="SUSPECT")
    s = only(run(start, end))
    assert s.state == "INCOMPLETE" and use(s, end) == ("CONTEXT", "SOURCE_UNVERIFIED")


def test_over_power_meter_is_invalid_but_bound_is_inclusive() -> None:
    start, end = event("EV_SESSION_START", at(1)), event("EV_SESSION_END", at(3))
    edge = meter(at(1), at(2), "1.002")      # 60 kW x 1 min = 1.000 + 0.002 error, inclusive
    over = meter(at(2), at(3), "1.003")
    s = only(run(start, end, edge, over))
    assert use(s, edge) == ("SUPPORT", None) and use(s, over) == ("EXCLUDED", "METER_INVALID")


def test_non_multiple_of_resolution_is_invalid_and_never_rounded() -> None:
    start, end = event("EV_SESSION_START", at(1)), event("EV_SESSION_END", at(2))
    odd = meter(at(1), at(2), "0.0005")
    s = only(run(start, end, odd))
    assert use(s, odd) == ("EXCLUDED", "METER_INVALID") and s.supported_kwh is None
    assert [i.kwh for i in s.intervals] == [Decimal("0.0005")]


@pytest.mark.parametrize("value", ["-1", "NaN", "Infinity", "abc"])
def test_negative_or_nonfinite_meter_is_invalid_and_has_no_interval_row(value: str) -> None:
    start, end = event("EV_SESSION_START", at(1)), event("EV_SESSION_END", at(2))
    bad = meter(at(1), at(2), value)
    s = only(run(start, end, bad))
    assert use(s, bad) == ("EXCLUDED", "METER_INVALID") and s.intervals == ()


def test_meter_crossing_start_or_end_is_invalid_not_clipped() -> None:
    start, end = event("EV_SESSION_START", at(2)), event("EV_SESSION_END", at(4))
    before = meter(at(1), at(3), "1", session=S)
    after = meter(at(3), at(5), "1", session=S)
    s = only(run(start, end, before, after))
    assert use(s, before) == use(s, after) == ("EXCLUDED", "METER_INVALID")


def test_ceil_fractional_unknown_seconds() -> None:
    start, end = event("EV_SESSION_START", at(1)), event("EV_SESSION_END", at(2, 0, 500_001))
    s = only(run(start, end, meter(at(1), at(2), "1")))
    assert s.unknown_meter_seconds == 1 and s.reason_codes == ("METER_GAP",)


def test_unattested_clock_meter_and_unbound_records() -> None:
    start, end = event("EV_SESSION_START", at(1)), event("EV_SESSION_END", at(3))
    clock = meter(at(1), at(2), "1", clock_attested=False)
    unbound = meter(at(2), at(3), "1", binding_revision_id=OTHER_BINDING)
    s = only(run(start, end, clock, unbound))
    assert use(s, clock) == ("EXCLUDED", "CLOCK_UNATTESTED")
    assert use(s, unbound) == ("EXCLUDED", "SOURCE_UNVERIFIED")


def test_meter_of_another_session_on_the_right_connector_is_connector_mismatch() -> None:
    start, end = event("EV_SESSION_START", at(1)), event("EV_SESSION_END", at(3))
    foreign = meter(at(1), at(2), "1", session="S-OTHER")
    s = only(run(start, end, foreign, meter(at(2), at(3), "1")))
    assert use(s, foreign) == ("EXCLUDED", "CONNECTOR_MISMATCH")


def test_same_session_meter_on_wrong_connector_is_connector_mismatch() -> None:
    start, end = event("EV_SESSION_START", at(1)), event("EV_SESSION_END", at(2))
    wrong = meter(at(1), at(2), "1", asset_id=C2)
    s = only(run(start, end, wrong))
    assert use(s, wrong) == ("EXCLUDED", "CONNECTOR_MISMATCH")


def test_site_import_and_connector_means_are_context_when_intersecting() -> None:
    start, end = event("EV_SESSION_START", at(1)), event("EV_SESSION_END", at(5))
    site = mean(at(0), at(5), "10", asset_id=METER)
    power = mean(at(0), at(1), "7")            # [08:00,08:01) ends at START: no intersection
    other = mean(at(1), at(5), "7", asset_id=C2)
    s = only(run(start, end, site, power, other, meter(at(1), at(5), "4")))
    assert use(s, site) == ("CONTEXT", None)
    assert not linked(s, power) and not linked(s, other)


def test_start_before_window_is_context_and_its_in_window_end_is_an_orphan() -> None:
    """q3 P5: an orphan is a terminal without a qualifying START in the selected window; a pre-window START is
    context, not a new attempt."""
    early = event("EV_SESSION_START", at(-5))
    end = event("EV_SESSION_END", at(3))
    result = run(early, end)
    assert result.sessions == () and result.orphan_terminal_ids == (end.accepted_evidence_id,)
    assert result.denominator["started"] == 0 and result.denominator["orphan"] == 1
    assert ev.run_input_rows(inputs(early, end), result) == sorted(
        [r.id, r.envelope_sha256, "CONTEXT", None] for r in (early, end))


def test_clear_idle_plugged_and_zero_power_never_synthesize_sessions() -> None:
    result = run(state(at(1), "PLUGGED"), state(at(2), "IDLE"), mean(at(0), at(5), "0"),
                 event("EV_CONNECTOR_CLEAR", at(3), session=None))
    assert result.sessions == ()


def test_late_end_appends_completed_from_previous_incomplete_basis() -> None:
    start, end = event("EV_SESSION_START", at(1)), event("EV_SESSION_END", at(31))
    meters = full_meters(1, 31)
    first = only(run(start, *meters))
    final = only(run(start, end, *meters))
    assert (first.state, first.unknown_meter_seconds, first.reason_codes) == (
        "INCOMPLETE", 0, ("MISSING_TERMINAL",))
    assert first.energy_complete is False and first.supported_kwh == Decimal("30.000")
    assert final.state == "COMPLETED" and final.energy_complete is True
    assert first.basis_sha256 != final.basis_sha256


# --- digests and order -----------------------------------------------------------------------------------------


def _sha(document) -> str:
    return hashlib.sha256(json.dumps(document, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def test_session_basis_is_linked_rows_and_configuration_row() -> None:
    start, end = event("EV_SESSION_START", at(1)), event("EV_SESSION_END", at(2))
    m = meter(at(1), at(2), "1")
    unrelated = event("EV_CONNECTOR_FAULT", at(40), session=None, asset_id=C2)
    s = only(run(start, end, m, unrelated))
    rows = sorted([str(r.accepted_evidence_id), r.envelope_sha256, "SUPPORT", None] for r in (start, end, m))
    config = [str(FOUNDATION), str(BINDING), PROFILE, "ev-session/1", "1", "2026-10-06T08:00:00.000000Z",
              "2026-10-06T09:00:00.000000Z", "2026-10-06T09:00:00.000000Z", SOURCE_CLASS]
    assert s.basis_sha256 == _sha([rows, config])
    changed = ev.assess(ev.EvInputs(**{**inputs(start, end, m).__dict__, "mapping_profile_id": "other/1"}))
    assert changed.sessions[0].basis_sha256 != s.basis_sha256


def test_finding_key_configuration_and_cohort_digests() -> None:
    s = only(run(event("EV_SESSION_START", at(1))))
    assert s.finding_key_sha256 == _sha([str(TENANT), str(SITE), "EV_INTERRUPTION", str(CHARGER), str(C1), S,
                                         str(s.first_start_evidence_id)])
    assert ev.cohort_sha256() == ev.EMPTY_SUPPORT_SHA256 == _sha([])
    selection = inputs()
    policy = {"ev-charger-max-power": "120.0", "ev-connector-max-power": "60.0", "ev-meter-resolution": "0.001",
              "ev-meter-error-bound": "0.001", "ev-clock-error-bound": "30.0", "ev-status-cadence": "1.0",
              "ev-meter-cadence": "5.0"}
    document = {"connectors": {str(C1): policy, str(C2): policy}}
    assert ev.policy_document(selection) == document
    assert ev.configuration_sha256(selection) == _sha([str(FOUNDATION), str(BINDING), PROFILE, SOURCE_CLASS, document])


def test_basis_rows_deduplicate_by_id_and_refuse_two_uses() -> None:
    link = ev.EvLink(UUID(int=5), "a" * 64, "CONTEXT", None)
    assert ev.evidence_rows([link, link]) == [[str(UUID(int=5)), "a" * 64, "CONTEXT", None]]
    with pytest.raises(ValueError):
        ev.evidence_rows([link, ev.EvLink(UUID(int=5), "a" * 64, "SUPPORT", None)])


def test_semantic_order_at_one_instant() -> None:
    rows = [event("EV_SESSION_ABORT", at(3)), event("EV_SESSION_END", at(3)), event("EV_CONNECTOR_FAULT", at(3)),
            meter(at(2), at(3), "1"), event("EV_SESSION_START", at(3))]
    ordered = sorted(rows, key=ev.semantic_order_key)
    assert [r.record_kind or r.measurement for r in ordered] == [
        "EV_SESSION_START", "EV_CONNECTOR_FAULT", "EV_SESSION_END", "EV_SESSION_ABORT", "INTERVAL_DELTA"]


def test_completed_denominator_and_claim_levels() -> None:
    complete = [event("EV_SESSION_START", at(1)), event("EV_SESSION_END", at(2)), meter(at(1), at(2), "1")]
    gap = [event("EV_SESSION_START", at(10), session="S-2"), event("EV_SESSION_END", at(12), session="S-2"),
           meter(at(10), at(11), "1", session="S-2")]
    result = run(*complete, *gap)
    assert result.denominator["completed"] == 2 and result.denominator["confirmed_delivery"] == 1
    assert result.claim_level == "BOUNDED" and result.status_state == "OBSERVED_SESSIONS"
    assert run(*complete).claim_level == "OBSERVED"


def test_module_is_pure() -> None:
    source = open(ev.__file__, encoding="utf-8").read()
    for forbidden in ("sqlalchemy", "psycopg", "assetops_simulator", "datetime.now", "utcnow"):
        assert forbidden not in source


# --- q3 P2: binding membership ---------------------------------------------------------------------------------


@pytest.mark.parametrize("change", [
    {"binding_revision_id": UUID(int=0xB199)},              # missing member
    {"binding_set_revision_id": OTHER_BINDING},             # row names another set revision
    {"role": "other-role"}, {"device_id": "other-dev"}, {"signal_id": "other-sig"},
    {"source_id": "00000000-0000-4000-8000-0000000000a9"},  # another source
    {"binding_revision_id": UUID(int=0xB102)},              # the C2 member on a C1 row: asset mismatch
])
def test_meter_whose_binding_is_not_the_exact_member_is_source_unverified(change: dict) -> None:
    start, end = event("EV_SESSION_START", at(1)), event("EV_SESSION_END", at(3))
    bad = meter(at(1), at(2), "1", **change)
    s = only(run(start, end, bad, meter(at(2), at(3), "1")))
    assert use(s, bad) == ("EXCLUDED", "SOURCE_UNVERIFIED")
    assert "SOURCE_UNVERIFIED" in s.reason_codes and s.supported_kwh == Decimal("1.000")


def test_foreign_or_stale_member_never_verifies_and_start_fails_closed() -> None:
    start, end = event("EV_SESSION_START", at(1)), event("EV_SESSION_END", at(3))
    foreign = (member(C1, 1, binding_set_revision_id=OTHER_BINDING), MEMBERS[C2], MEMBERS[METER])
    assert ev.assess(inputs(start, end, members=foreign)).sessions == ()
    stale = (member(C1, 1, valid_to=at(2)), MEMBERS[C2], MEMBERS[METER])
    s = only(ev.assess(inputs(start, end, members=stale)))   # START at 08:01 valid; END at 08:03 is not
    assert use(s, end) == ("EXCLUDED", "SOURCE_UNVERIFIED") and s.state == "INCOMPLETE"
    later = (member(C1, 1, valid_from=at(2)), MEMBERS[C2], MEMBERS[METER])
    assert ev.assess(inputs(start, end, members=later)).sessions == ()
    with pytest.raises(ev.EvConfigurationRefused):
        ev.assess(inputs(start, end, members=(MEMBERS[C1], MEMBERS[C1])))


def test_selected_set_revision_is_the_basis_binding_and_rows_carry_member_ids() -> None:
    start, end = event("EV_SESSION_START", at(1)), event("EV_SESSION_END", at(2))
    assert start.binding_revision_id == MEMBERS[C1].binding_revision_id != BINDING
    selection = inputs(start, end)
    assert selection.configuration_row()[1] == str(BINDING)
    assert only(ev.assess(selection)).state == "COMPLETED"


# --- q3 P3: whole-run input rows -------------------------------------------------------------------------------


def test_run_input_rows_cover_every_selected_record_with_run_only_context() -> None:
    start, end = event("EV_SESSION_START", at(1)), event("EV_SESSION_END", at(3))
    m = meter(at(1), at(3), "2")
    unlinked = event("EV_CONNECTOR_FAULT", at(40), session=None, asset_id=C2)
    selection = inputs(start, end, m, unlinked)
    result = ev.assess(selection)
    rows = ev.run_input_rows(selection, result)
    assert rows == sorted([[r.id, r.envelope_sha256, "SUPPORT", None] for r in (start, end, m)]
                          + [[unlinked.id, unlinked.envelope_sha256, "CONTEXT", None]])
    config = [str(FOUNDATION), str(BINDING), PROFILE, "ev-session/1", "1", "2026-10-06T08:00:00.000000Z",
              "2026-10-06T09:00:00.000000Z", "2026-10-06T09:00:00.000000Z", SOURCE_CLASS]
    assert ev.run_input_sha256(selection, result) == _sha([rows, config])
    assert ev.run_input_sha256(selection, result) != only(result).basis_sha256


def test_run_rows_doubly_linked_differently_are_context_and_identical_pairs_are_kept() -> None:
    a_start, a_end = event("EV_SESSION_START", at(1), session="A"), event("EV_SESSION_END", at(10), session="A")
    b_start, b_end = event("EV_SESSION_START", at(2), session="B"), event("EV_SESSION_END", at(10), session="B")
    site = mean(at(3), at(4), "10", asset_id=METER)       # CONTEXT/null in both sessions: identical pair kept
    own = meter(at(3), at(4), "1", session="A")           # SUPPORT in A, CONNECTOR_MISMATCH in B
    selection = inputs(a_start, a_end, b_start, b_end, site, own)
    result = ev.assess(selection)
    by_session = {s.external_session_id: s for s in result.sessions}
    assert use(by_session["A"], site) == use(by_session["B"], site) == ("CONTEXT", None)
    assert use(by_session["A"], own) == ("SUPPORT", None)
    assert use(by_session["B"], own) == ("EXCLUDED", "CONNECTOR_MISMATCH")
    rows = {r[0]: r[2:] for r in ev.run_input_rows(selection, result)}
    assert rows[site.id] == ["CONTEXT", None] and rows[own.id] == ["CONTEXT", None]
    assert rows[a_start.id] == ["SUPPORT", None]
    links = {(link.use, link.reason) for s in result.sessions for link in s.links
             if link.evidence_id == own.accepted_evidence_id}
    assert ("CONTEXT", None) not in links      # the run-only pair is never a session link


def test_run_rows_refuse_one_id_with_two_envelope_digests() -> None:
    start = event("EV_SESSION_START", at(1))
    twin = ev.EvRecord(**{**start.__dict__, "envelope_sha256": "f" * 64})
    with pytest.raises(ValueError):
        ev.run_input_rows(inputs(start, twin), ev.assess(inputs(start)))
    with pytest.raises(ValueError):
        ev.run_input_rows(inputs(twin), ev.assess(inputs(start)))


# --- q3 P4: configuration policy -------------------------------------------------------------------------------


def test_policy_keeps_exact_decimal_text_and_refuses_a_missing_required_property() -> None:
    c1 = ev.EvConnector(**{**connector(C1).__dict__, "max_power_kw": Decimal("7.40"),
                           "meter_error_bound_kwh": Decimal("0E-3")})
    selection = ev.EvInputs(**{**inputs().__dict__, "connectors": (c1,)})
    entry = ev.policy_document(selection)["connectors"][str(C1)]
    assert tuple(sorted(entry)) == tuple(sorted(ev.POLICY_KEYS)) and len(entry) == 7
    assert (entry["ev-connector-max-power"], entry["ev-meter-error-bound"]) == ("7.40", "0.000")
    for missing in ("charger_max_power_kw", "status_cadence_min", "meter_cadence_min"):
        broken = ev.EvConnector(**{**connector(C1).__dict__, missing: None})
        with pytest.raises(ev.EvConfigurationRefused):
            ev.configuration_sha256(ev.EvInputs(**{**inputs().__dict__, "connectors": (broken,)}))


# --- q3 P5: ratified readings ----------------------------------------------------------------------------------


def test_straddle_applies_to_events_before_start_not_to_means_or_states_beginning_at_start() -> None:
    start, end = event("EV_SESSION_START", at(5)), event("EV_SESSION_END", at(8))
    at_start = state(at(5), "CHARGING")
    from_start = mean(at(5), at(6), "7")
    early_clear = event("EV_CONNECTOR_CLEAR", at(4, 40))
    s = only(run(start, end, at_start, from_start, early_clear, meter(at(5), at(8), "3")))
    assert use(s, at_start) == use(s, from_start) == ("CONTEXT", None)
    assert use(s, early_clear) == ("EXCLUDED", "CLOCK_UNATTESTED")


def test_two_faults_near_abort_support_nothing_and_open_no_finding() -> None:
    start, abort = event("EV_SESSION_START", at(1)), event("EV_SESSION_ABORT", at(3))
    f1, f2 = event("EV_CONNECTOR_FAULT", at(2, 50)), event("EV_CONNECTOR_FAULT", at(3, 10))
    result = run(start, abort, f1, f2, *full_meters(1, 3))
    s = only(result)
    assert use(s, f1) == use(s, f2) == ("CONTEXT", None)
    assert s.fault_evidence_id is None and s.finding_support == () and s.finding_support_sha256 is None
    assert result.denominator["fault_aborted"] == 0


@pytest.mark.parametrize("quality", ["SUSPECT", "BAD", "UNAVAILABLE"])
def test_non_good_start_creates_no_session_and_its_terminal_is_orphan(quality: str) -> None:
    start, end = event("EV_SESSION_START", at(1), quality=quality), event("EV_SESSION_END", at(3))
    result = run(start, end)
    assert result.sessions == () and result.orphan_terminal_ids == (end.accepted_evidence_id,)


def test_second_start_for_the_session_is_context_conflicting_start() -> None:
    start, again, end = (event("EV_SESSION_START", at(1)), event("EV_SESSION_START", at(2)),
                         event("EV_SESSION_END", at(3)))
    s = only(run(start, again, end))
    assert use(s, again) == ("CONTEXT", "CONFLICTING_START") and "CONFLICTING_START" in s.reason_codes


def test_fault_replay_shape_c1_fault_and_clear_are_run_context_not_a_session() -> None:
    fault, clear = (event("EV_CONNECTOR_FAULT", at(0), session=None),
                    event("EV_CONNECTOR_CLEAR", at(5), session=None))
    start, end = (event("EV_SESSION_START", at(11), asset_id=C2, session="S-2"),
                  event("EV_SESSION_END", at(21), asset_id=C2, session="S-2"))
    selection = inputs(fault, clear, start, end, meter(at(11), at(21), "10", asset_id=C2, session="S-2"))
    result = ev.assess(selection)
    assert [s.connector_asset_id for s in result.sessions] == [C2]
    rows = {r[0]: r[2:] for r in ev.run_input_rows(selection, result)}
    assert rows[fault.id] == rows[clear.id] == ["CONTEXT", None]


# --- q3 P1 (pure side): clock proof is consumed, never inferred ------------------------------------------------


def test_unattested_start_or_terminal_is_clock_unattested() -> None:
    start, end = event("EV_SESSION_START", at(1), clock_attested=False), event("EV_SESSION_END", at(3))
    result = run(start, end)
    assert result.sessions == () and result.orphan_terminal_ids == (end.accepted_evidence_id,)
    start, end = event("EV_SESSION_START", at(1)), event("EV_SESSION_END", at(3), clock_attested=False)
    s = only(run(start, end))
    assert use(s, end) == ("EXCLUDED", "CLOCK_UNATTESTED") and s.state == "INCOMPLETE"
