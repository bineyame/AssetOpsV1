"""T028 phase 1: the dispatch analytic over hand-built accepted records.

Rules under test are the decision table beside this file
(`dispatch_decision_table.md`). End-to-end runs through commit and ingestion
are in `host/tests/test_t028_dispatch_finding.py`.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from fractions import Fraction
from typing import Callable

from fastapi.testclient import TestClient

from assetops_backend.analytics import dispatch
from assetops_backend.analytics.adapters.json_assessment_store import JsonAssessmentStore
from assetops_backend.analytics.declaration import DECLARATIONS, site_declaration
from assetops_backend.analytics.service import AssessmentService
from assetops_backend.config import FeatureFlags
from assetops_backend.evidence.models import AcceptedRecord, SiteEvidence
from assetops_backend.main import create_app
from run_fixtures import FakeSites
from test_t027_ingestion import SITE_ID, a_site

BASE = datetime(2026, 9, 22, tzinfo=timezone.utc)
SFC = dispatch.FuelBasis(Fraction(3, 10), "test Foundation 0.3 L/kWh")
NO_SFC = dispatch.FuelBasis(None, "none")
Series = Callable[[int], "str | None"]


def at(minute: int) -> str:
    return (BASE + timedelta(minutes=minute)).strftime("%Y-%m-%dT%H:%M:%SZ")


def rec(device: str, signal: str, minute: int, value: str | None, *, unit: str = "kW",
        interval: bool = True, gateway: str = "g", family: str = "MEASUREMENT",
        detail: tuple[tuple[str, str], ...] = (), published: int | None = None) -> AcceptedRecord:
    measurement = None if family != "MEASUREMENT" else (
        "INTERVAL_MEAN" if interval else "STATE_AT_INSTANT")
    good = value is not None
    return AcceptedRecord(
        message_id=f"{device}/{signal}/{minute}/{gateway}", envelope_text="{}",
        content_digest=f"d-{value}", site_id=SITE_ID, source_id="s", gateway_id=gateway,
        device_id=device, signal_id=signal, family=family, measurement=measurement,
        source_time=at(minute), published_at=at(minute if published is None else published),
        received_at=at(minute), batch_id="b", source_mode="SIMULATED", mapping_set_id="m",
        mapping_version=1, foundation_version=1, foundation_valid_from=at(-600),
        original_value=value, original_unit=unit, normalized_value=value, normalized_unit=unit,
        quality=(None if family != "MEASUREMENT" else ("GOOD" if good else "UNAVAILABLE")),
        unavailable_reason=None if good or family != "MEASUREMENT" else "NO_MEASUREMENT",
        interval_start=at(minute - 5) if interval and good and family == "MEASUREMENT" else None,
        interval_end=at(minute) if interval and good and family == "MEASUREMENT" else None,
        record_detail=detail,
    )


def policy(key: tuple[str, str], value: str, unit: str, control: str) -> AcceptedRecord:
    return rec(*key, -600, value, unit=unit, family="POLICY", detail=(
        ("control", control), ("policy_version", "1"), ("policy_source", "FOUNDATION"),
        ("effective_start", at(-600)),
    ))


def override(key: tuple[str, str], value: str, control: str, start: int, end: int) -> AcceptedRecord:
    return rec(*key, start, value, unit="%", family="OPERATIONAL_RECORD", detail=(
        ("control", control), ("effective_start", at(start)), ("effective_end", at(end)),
        ("record_kind", "OVERRIDE_COMMAND"), ("actor", "OPERATOR"),
    ))


POLICIES = [
    policy(dispatch.POLICY_RESERVE, "30", "%", "battery-reserve-state-of-charge"),
    policy(dispatch.POLICY_MIN_RUNTIME, "30", "min", "generator-minimum-runtime"),
    policy(dispatch.POLICY_STOP, "90", "%", "generator-stop-soc-threshold"),
]


def const(value: str | None) -> Series:
    return lambda minute: value


def world(minutes: range, *, running: Series, load: Series = const("20"),
          pv: Series = const("30"), soc: Series = const("60"), dcap: Series = const("30"),
          gen: Series = const("25"), pv_output: Series = const(None),
          policies: list[AcceptedRecord] | None = None) -> list[AcceptedRecord]:
    """Every 15 minutes: status, generator mean, feeders, PV, SOC, discharge capability."""
    records = list(POLICIES if policies is None else policies)
    for m in minutes:
        on = running(m)
        if on is not None:
            records.append(rec(*dispatch.GEN_STATUS, m, on, unit="state", interval=False))
        if on is not None or gen(m) is not None:
            records.append(rec(*dispatch.GEN_POWER, m, gen(m) if on == "RUNNING" else "0"))
        feeder = load(m)
        if feeder is not None:
            third = str(Fraction(feeder) / 3)
            for key in dispatch.FEEDERS:
                records.append(rec(*key, m, third))
        for key, series, interval in (
            (dispatch.PV_AVAILABLE, pv, True), (dispatch.SOC, soc, False),
            (dispatch.DISCHARGE, dcap, True), (("pv-inverter-controller", "ac-power"), pv_output, True),
        ):
            value = series(m)
            if value is not None:
                records.append(rec(*key, m, value, unit="%" if key == dispatch.SOC else "kW",
                                   interval=interval))
    return records


def between(start: int, end: int) -> Series:
    return lambda m: "RUNNING" if start <= m <= end else "STOPPED"


def one(records: list[AcceptedRecord], fuel: dispatch.FuelBasis = SFC) -> dict:
    out = dispatch.assess(records, fuel)
    assert len(out) == 1, [a["summary"] for a in out]
    return out[0]


def classes(assessment: dict) -> list[tuple[str, str, str | None]]:
    return [(s["start"][11:16], s["classification"], s["binding_constraint"])
            for s in assessment["segments"]]


# --- AC1, AC4, AC10: bounds, candidate, hand-calculated fuel ----------------------


def test_hand_calculated_candidate_interval_and_fuel_bound() -> None:
    a = one(world(range(0, 151, 15), running=between(15, 120)))
    assert a["claim_level"] == "CANDIDATE_AVOIDABLE"
    # Minimum runtime (30 min from the 00:15 start) is Necessary, not candidate.
    assert classes(a)[:2] == [("00:15", "NECESSARY", "MINIMUM_RUNTIME"),
                              ("00:30", "NECESSARY", "MINIMUM_RUNTIME")]
    # Low bound: observed running 00:15-02:00 = 105 min. High bound: from the
    # last stopped evidence (00:00) to the first (the zero mean starting 02:10).
    assert a["interval"]["duration_hours"] == {"low": "1.75", "high": "2.17"}
    assert a["interval"]["first_stopped_after"] == at(130)
    # Candidate: 01:00-02:00 (60 min; the 00:45-01:00 segment's start is still
    # inside minimum runtime, so both-ends keeps it Necessary), plus the
    # 10-minute stop uncertainty beside a candidate segment = 70 min.
    assert classes(a)[2] == ("00:45", "NECESSARY", "MINIMUM_RUNTIME")
    assert a["portions_hours"]["CANDIDATE_AVOIDABLE"] == {"low": "1", "high": "1.17"}
    # 1 h x 25 kW x 0.3 L/kWh x 0.9 = 6.75 L; 70/60 h x 25 x 0.3 x 1.1 = 9.625 L.
    fuel = a["fuel"]
    assert (fuel["status"], fuel["low_litres"], fuel["high_litres"]) == ("BOUNDED", "6.8", "9.6")
    assert fuel["basis"] == "modelled" and "not a financial saving" in fuel["statement"]
    assert fuel["inputs"]["specific_fuel_consumption"]["source"] == SFC.source


def test_fuel_is_unavailable_with_its_reason() -> None:
    records = world(range(0, 151, 15), running=between(15, 120))
    assert "specific fuel consumption" in one(records, NO_SFC)["fuel"]["reason"]
    open_end = world(range(0, 121, 15), running=between(15, 200))
    a = one(open_end)
    assert a["interval"]["open_end"] is True and a["interval"]["duration_hours"]["high"] is None
    assert a["fuel"]["status"] == "UNAVAILABLE" and "open" in a["fuel"]["reason"]


def test_a_gap_bounds_duration_instead_of_assuming_operation() -> None:
    records = [r for r in world(range(0, 241, 15), running=between(15, 210))
               if not (r.device_id == "generator-controller" and 90 < _minute(r) < 150)]
    a = one(records)
    # 01:30 -> 02:30 has no generator state: it counts in the high bound only.
    assert a["coverage"]["unobserved_generator_state"] == [
        {"start": at(90), "end": at(150), "minutes": "60"}
    ]
    assert a["interval"]["duration_hours"]["low"] == "2.25"
    assert a["interval"]["duration_hours"]["high"] == "3.67"
    gap = next(s for s in a["segments"] if not s["observed"])
    assert gap["classification"] == "INDETERMINATE"


def _minute(record: AcceptedRecord) -> int:
    t = datetime.strptime(record.source_time, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    return int((t - BASE).total_seconds() // 60)


# --- AC2, AC3, AC5: constraints, no substitutes, named gaps -------------------------


def test_observed_pv_output_never_stands_in_for_available_capability() -> None:
    a = one(world(range(0, 151, 15), running=between(15, 120), pv=const(None),
                  pv_output=const("30")))
    assert a["claim_level"] == "INDETERMINATE"
    assert "PV available power: no record" in a["missing_evidence"]
    signals = {(e["device_id"], e["signal_id"]) for s in a["segments"] for e in s["evidence"]}
    assert ("pv-inverter-controller", "ac-power") not in signals


def test_insufficient_capability_evidence_throughout_is_indeterminate() -> None:
    a = one(world(range(0, 151, 15), running=between(15, 120), pv=const("10"), dcap=const(None)))
    assert a["claim_level"] == "INDETERMINATE"
    assert a["confidence"]["level"] == "NOT_APPLICABLE"
    assert any("Battery discharge capability" in m for m in a["missing_evidence"])
    assert a["fuel"]["status"] == "NOT_APPLICABLE"
    assert a["raises_finding"] is True


def test_reserve_and_capability_shortfall_make_runtime_necessary() -> None:
    at_reserve = one(world(range(0, 151, 15), running=between(15, 120), pv=const("5"), soc=const("30")))
    assert at_reserve["claim_level"] == "NECESSARY" and at_reserve["raises_finding"] is False
    assert "BATTERY_AT_RESERVE" in at_reserve["binding_constraints"]
    near = one(world(range(0, 151, 15), running=between(15, 120), pv=const("5"), soc=const("35")))
    assert "BATTERY_NEAR_RESERVE" in near["binding_constraints"]
    short = one(world(range(0, 151, 15), running=between(15, 120), load=const("60"),
                      pv=const("10"), dcap=const("20")))
    assert "CAPABILITY_SHORTFALL" in short["binding_constraints"]


def test_a_margin_inside_the_declared_headroom_is_indeterminate() -> None:
    # PV 15 + battery 6 = 21 kW against 20 kW load: within the 10 % headroom.
    a = one(world(range(0, 151, 15), running=between(15, 120), pv=const("15"), dcap=const("6")))
    assert a["claim_level"] == "INDETERMINATE"
    assert any("headroom" in r for s in a["segments"] for r in s["reasons"])


def test_one_missing_portion_is_listed_beside_the_candidate() -> None:
    a = one(world(range(0, 241, 15), running=between(15, 210),
                  dcap=lambda m: None if 90 <= m <= 120 else "30"))
    assert a["claim_level"] == "CANDIDATE_AVOIDABLE"
    assert a["portions_hours"]["INDETERMINATE"]["low"] == "1"
    assert a["confidence"]["level"] != "HIGH"
    row = next(r for r in a["coverage"]["inputs"] if r["input"] == "discharge_capability")
    assert row["gaps"] == [{"start": at(75), "end": at(135), "minutes": "60"}]


def test_conflicting_records_are_used_by_nothing() -> None:
    records = world(range(0, 151, 15), running=between(15, 120))
    records += [rec(*dispatch.PV_AVAILABLE, m, "5", gateway="other") for m in range(0, 151, 15)]
    a = one(records)
    assert a["claim_level"] == "INDETERMINATE"
    assert "PV available power: conflicting records" in a["missing_evidence"]


# --- AC7, AC8: override evidence ----------------------------------------------------


def test_an_override_record_is_a_constraint_at_its_effective_time() -> None:
    records = world(range(0, 151, 15), running=between(15, 120))
    records.append(override(dispatch.GEN_OVERRIDE, "95", "generator-stop-soc-threshold", 60, 90))
    a = one(records)
    by_start = {s["start"][11:16]: s for s in a["segments"]}
    assert by_start["01:00"]["binding_constraint"] == "OPERATOR_OVERRIDE"
    assert by_start["01:45"]["classification"] == "CANDIDATE_AVOIDABLE"
    observed = next(x for x in a["alternatives"] if x["id"] == "OPERATOR_OVERRIDE")
    assert observed["status"] == "OBSERVED" and observed["evidence"]
    assert not any(x["id"] == "UNOBSERVED_OVERRIDE" for x in a["alternatives"])


def test_a_reserve_override_changes_the_effective_reserve() -> None:
    records = world(range(0, 151, 15), running=between(15, 120), pv=const("10"))
    records.append(override(dispatch.BATTERY_OVERRIDE, "70", "battery-reserve-state-of-charge", 0, 200))
    a = one(records)
    assert a["claim_level"] == "NECESSARY"
    late = a["segments"][-1]
    assert late["binding_constraint"] == "BATTERY_AT_RESERVE"
    assert late["inputs"]["at_end"]["reserve_source"] == "operator override"


def test_override_absence_is_none_observed_not_proof() -> None:
    a = one(world(range(0, 151, 15), running=between(15, 120)))
    absent = next(x for x in a["alternatives"] if x["id"] == "UNOBSERVED_OVERRIDE")
    assert absent["status"] == "NOT_EXCLUDED"
    assert "No operator-commanded override record observed" in absent["statement"]


# --- AC13: same evidence, same assessment; changed evidence, a retained revision ---


class Store:
    def __init__(self, records: list[AcceptedRecord]) -> None:
        self.records = records

    def load_site(self, site_id: str) -> SiteEvidence:
        return SiteEvidence(site_id=site_id, records=tuple(self.records))


def minigrid():
    return replace(a_site(), site_type="MINIGRID")


def test_the_same_records_give_the_same_payload() -> None:
    records = world(range(0, 151, 15), running=between(15, 120))
    assert dispatch.assess(records, SFC) == dispatch.assess(list(reversed(records)), SFC)


def test_changed_evidence_appends_a_revision_and_keeps_the_prior(tmp_path) -> None:
    evidence = Store(world(range(0, 241, 15), running=between(15, 210),
                           dcap=lambda m: None if 90 <= m <= 120 else "30"))
    clock = iter(["2026-09-23T00:00:00Z", "2026-09-24T00:00:00Z", "2026-09-25T00:00:00Z",
                  "2026-09-26T00:00:00Z"])

    def service() -> AssessmentService:
        return AssessmentService(evidence, JsonAssessmentStore(tmp_path), lambda _: minigrid(),
                                 lambda: next(clock))

    first = service().assess_site(SITE_ID)
    (lineage,) = first.lineages
    assert service().assess_site(SITE_ID) == first, "a rerun adds nothing"
    # Delayed capability evidence arrives for the gap.
    evidence.records = evidence.records + [
        rec(*dispatch.DISCHARGE, m, "30", published=m + 600) for m in (90, 105, 120)
    ]
    service().assess_site(SITE_ID)
    reloaded = JsonAssessmentStore(tmp_path).load_history(SITE_ID)
    (after,) = reloaded.lineages
    assert after.assessment_id == lineage.assessment_id and after.active
    assert [r.revision for r in after.revisions] == [1, 2]
    prior, current = after.revisions
    assert prior == lineage.revisions[0], "the prior assessment is retained unchanged"
    assert prior.basis_digest != current.basis_digest
    assert prior.assessment["portions_hours"]["INDETERMINATE"]["low"] == "1"
    assert current.assessment["portions_hours"]["INDETERMINATE"]["low"] == "0"
    assert prior.assessment["assessed_window"] and prior.model_version == dispatch.MODEL_VERSION


def test_an_interval_no_longer_found_is_retired_not_deleted(tmp_path) -> None:
    evidence = Store(world(range(0, 151, 15), running=between(15, 120)))
    service = AssessmentService(evidence, JsonAssessmentStore(tmp_path), lambda _: minigrid(),
                                lambda: "2026-09-23T00:00:00Z")
    (lineage,) = service.assess_site(SITE_ID).lineages
    evidence.records = world(range(0, 151, 15), running=const("STOPPED"))
    (retired,) = service.assess_site(SITE_ID).lineages
    assert retired.assessment_id == lineage.assessment_id
    assert retired.active is False and retired.revisions == lineage.revisions
    assert service.findings(SITE_ID)["findings"] == []
    assert service.revisions(SITE_ID, lineage.assessment_id)["revisions"]


# --- AC16: the declaration read model -------------------------------------------------


def test_the_declaration_names_finding_type_evidence_and_claim_levels() -> None:
    (declaration,) = DECLARATIONS
    assert declaration.analytic_id == "dispatch" and declaration.site_types == ("MINIGRID",)
    assert [c.label for c in declaration.claim_levels] == [
        "Necessary", "Candidate avoidable", "Indeterminate"
    ]
    required = {(r.device_id, r.signal_id) for r in declaration.required_evidence}
    assert dispatch.PV_AVAILABLE in required and ("pv-inverter-controller", "ac-power") not in required
    served = site_declaration(minigrid(), SiteEvidence(SITE_ID, tuple(POLICIES)))
    (analytic,) = served["analytics"]
    reserve = next(r for r in analytic["required_evidence"] if r["family"] == "POLICY")
    assert reserve["available"] is True
    assert all(not r["available"] for r in analytic["required_evidence"] if r["family"] != "POLICY")
    # Verification rules join at T034; nothing declares them yet.
    assert not any("verification" in key for key in analytic)
    other = replace(a_site(), site_type="OTHER")
    assert site_declaration(other, SiteEvidence(SITE_ID))["analytics"] == []


def test_the_analytics_routes_are_served_with_the_lab_gated_off(tmp_path) -> None:
    from assetops_backend.evidence.adapters.json_evidence_store import JsonEvidenceStore

    client = TestClient(create_app(
        FeatureFlags(simulator_lab_enabled=False),
        site_repository=FakeSites((minigrid(),)),
        evidence_store=JsonEvidenceStore(tmp_path / "evidence"),
        assessment_store=JsonAssessmentStore(tmp_path / "assessments"),
    ))
    base = f"/api/sites/{SITE_ID}"
    declaration = client.get(f"{base}/analytics").json()
    assert [a["analytic_id"] for a in declaration["analytics"]] == ["dispatch"]
    assert client.get(f"{base}/dispatch").json()["assessments"] == []
    assert client.get(f"{base}/findings").json()["findings"] == []
    missing = client.get(f"{base}/assessments/nope/revisions")
    assert missing.status_code == 404 and missing.json()["detail"]["code"] == "ASSESSMENT_NOT_FOUND"
    assert client.get("/api/sites/NOPE/analytics").status_code == 404


# --- AC20: the capability row's readiness, scored by the backend ------------------------


def readiness(records: list[AcceptedRecord]) -> dict:
    """The dispatch row's readiness, scored against these records' own assessments."""
    assessed = [(f"a{i}", a) for i, a in enumerate(dispatch.assess(records, SFC))]
    served = site_declaration(minigrid(), SiteEvidence(SITE_ID, tuple(records)),
                              {dispatch.ANALYTIC_ID: assessed})
    (analytic,) = served["analytics"]
    return analytic["readiness"]


def test_complete_evidence_scores_full_with_the_candidate_ceiling() -> None:
    r = readiness(world(range(0, 151, 15), running=between(15, 120)))
    assert r["level"] == "FULL" and r["label"] == "Full"
    assert r["claim_ceiling"]["claim_level"] == dispatch.CANDIDATE
    assert r["claim_ceiling"]["statement"] == dispatch.CLAIM_CEILINGS[dispatch.CANDIDATE]
    assert r["missing_evidence"] == [] and r["assessed_intervals"] == 1
    assert r["basis_version"] == "readiness-3"
    # Override absence is named as not observed, never as a gap that lowers Full.
    assert {o["role"] for o in r["optional_not_observed"]} >= {"Operator override"}


def test_a_coverage_gap_in_an_assessed_interval_scores_limited_and_names_it() -> None:
    r = readiness(world(range(0, 241, 15), running=between(15, 210),
                        dcap=lambda m: None if 90 <= m <= 120 else "30"))
    assert r["level"] == "LIMITED"
    (gap,) = r["missing_evidence"]
    assert gap["kind"] == "COVERAGE_GAP" and gap["role"] == "Battery discharge capability"
    assert gap["limits_claim"] is True and gap["limiting_segments"] > 0
    assert gap["assessment_ids"] == ["a0"] and 0 < gap["missing_segments"] < gap["evaluated_segments"]
    assert r["claim_ceiling"]["claim_level"] == dispatch.CANDIDATE
    assert "Indeterminate" in r["claim_ceiling"]["statement"]


def test_a_gap_no_classification_needed_is_listed_but_stays_full() -> None:
    # PV alone (30 kW) covers load (20 kW) with headroom, so SOC is not needed.
    r = readiness(world(range(0, 151, 15), running=between(15, 120),
                        soc=lambda m: None if 60 <= m <= 75 else "60"))
    assert r["level"] == "FULL"
    (gap,) = r["missing_evidence"]
    assert gap["role"] == "Battery state of charge" and gap["limits_claim"] is False
    assert "no classification depended on it" in gap["statement"]


def test_capability_never_accepted_caps_the_ceiling_below_candidate() -> None:
    r = readiness(world(range(0, 151, 15), running=between(15, 120), dcap=const(None)))
    assert r["level"] == "LIMITED"
    assert r["claim_ceiling"]["claim_level"] == dispatch.NECESSARY
    assert "Battery capability" in r["claim_ceiling"]["statement"]
    kinds = {(m["kind"], m["role"]) for m in r["missing_evidence"]}
    assert ("NOT_ACCEPTED", "Battery capability") in kinds


def test_no_generator_evidence_scores_none_with_no_claim() -> None:
    records = [r for r in world(range(0, 151, 15), running=between(15, 120))
               if (r.device_id, r.signal_id) not in (dispatch.GEN_STATUS, dispatch.GEN_POWER)]
    r = readiness(records)
    assert r["level"] == "NONE" and r["claim_ceiling"]["claim_level"] is None
    assert {m["role"] for m in r["missing_evidence"]} == {
        "Generator state", "Generator state and output"
    }
    assert r["assessed_intervals"] == 0
    assert "no accepted record of Generator state or Generator state and output" in (
        r["claim_ceiling"]["statement"])


def _without(signal: tuple[str, str], *, minutes: range = range(0, 151, 15)) -> list[AcceptedRecord]:
    return [r for r in world(minutes, running=between(15, 120))
            if (r.device_id, r.signal_id) != signal]


def _assessed(records: list[AcceptedRecord]) -> list:
    return dispatch.assess(records, SFC)


def test_status_only_generator_evidence_reconstructs_and_scores_limited_not_none() -> None:
    records = _without(dispatch.GEN_POWER)
    (assessment,) = _assessed(records)
    assert assessment["segments"], "status-only must reconstruct an interval"
    r = readiness(records)
    assert r["level"] == "LIMITED" and r["assessed_intervals"] == 1
    assert r["claim_ceiling"]["claim_level"] == dispatch.CANDIDATE
    assert [m["role"] for m in r["missing_evidence"] if m["kind"] == "NOT_ACCEPTED"] == [
        "Generator state and output"
    ]


def test_power_only_generator_evidence_reconstructs_and_scores_limited_not_none() -> None:
    records = _without(dispatch.GEN_STATUS)
    (assessment,) = _assessed(records)
    assert assessment["segments"], "power-only must reconstruct an interval"
    r = readiness(records)
    assert r["level"] == "LIMITED" and r["assessed_intervals"] == 1
    assert r["claim_ceiling"]["claim_level"] == dispatch.CANDIDATE
    assert [m["role"] for m in r["missing_evidence"] if m["kind"] == "NOT_ACCEPTED"] == [
        "Generator state"
    ]


def test_readiness_statement_names_scope_meaning_and_limits() -> None:
    text = readiness(world(range(0, 151, 15), running=between(15, 120)))["statement"]
    for needle in ("evidence sufficiency", "site-wide", "not the selected window",
                   "not mean the Site is healthy", "uninterrupted", "interim"):
        assert needle in text, needle


def test_the_readiness_basis_names_only_declared_required_roles() -> None:
    for d in DECLARATIONS:
        roles = {r.role for r in d.required_evidence}
        basis = d.readiness
        assert set(basis.reconstruct_from_any) <= roles and set(basis.top_claim_needs) <= roles
        levels = {c.claim_level for c in d.claim_levels}
        assert {basis.top_claim_level, basis.fallback_claim_level} <= levels
