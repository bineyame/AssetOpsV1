"""T028 fix round 1: regressions for Codex review findings R1-R5 (dispatch-2, readiness-3).

Each test reproduces the review's recorded case (`.agent/T028-codex-review.md`)
and asserts the corrected behaviour. Rules: `dispatch_decision_table.md`.
"""

from __future__ import annotations

from dataclasses import replace

from assetops_backend.analytics import dispatch
from assetops_backend.analytics.adapters.json_assessment_store import JsonAssessmentStore
from assetops_backend.analytics.service import AssessmentService
from assetops_backend.evidence.models import AcceptedRecord
from test_t027_ingestion import SITE_ID
from test_t028_dispatch_analytic import (
    NO_SFC, POLICIES, SFC, Store, at, between, classes, const, minigrid, one, override,
    policy, readiness, rec, world,
)


def _service(evidence: Store, tmp_path, clock) -> AssessmentService:
    return AssessmentService(evidence, JsonAssessmentStore(tmp_path), lambda _: minigrid(),
                             lambda: next(clock))


def _clock():
    return iter(f"2026-09-{d:02d}T00:00:00Z" for d in range(23, 30))


def _other(record: AcceptedRecord, value: str) -> AcceptedRecord:
    """The same policy or override from a second gateway, with another value."""
    return replace(record, message_id=record.message_id + "/other", gateway_id="other",
                   normalized_value=value, original_value=value, content_digest=f"d-{value}")


# --- R1: every dependency is in the evidence basis --------------------------------------


def test_r1_late_stop_evidence_appends_a_revision_and_keeps_the_open_one(tmp_path) -> None:
    evidence = Store(world(range(0, 121, 15), running=between(15, 200)))
    clock = _clock()
    (lineage,) = _service(evidence, tmp_path, clock).assess_site(SITE_ID).lineages
    first = lineage.revisions[0].assessment
    assert first["interval"]["open_end"] is True and first["fuel"]["status"] == "UNAVAILABLE"
    # A stop reported after the last running report closes the interval at 02:10.
    evidence.records = evidence.records + [
        rec(*dispatch.GEN_STATUS, 135, "STOPPED", unit="state", interval=False),
        rec(*dispatch.GEN_POWER, 135, "0"),
    ]
    _service(evidence, tmp_path, clock).assess_site(SITE_ID)
    (after,) = JsonAssessmentStore(tmp_path).load_history(SITE_ID).lineages
    assert [r.revision for r in after.revisions] == [1, 2]
    prior, current = after.revisions
    assert prior == lineage.revisions[0], "the open revision is retained unchanged"
    assert prior.basis_digest != current.basis_digest
    assert current.assessment["interval"]["first_stopped_after"] == at(130)
    # The service's Site has no fuel consumption configured, so the fuel stays
    # unavailable, but no longer because the duration is open.
    assert "open" in prior.assessment["fuel"]["reason"]
    assert "open" not in current.assessment["fuel"]["reason"]
    assert one(evidence.records)["fuel"]["status"] == "BOUNDED"
    # The zero mean that places the 02:10 bound is part of the evidence basis.
    assert "generator-controller/ac-power/135/g" in current.assessment["evidence_basis"]["message_ids"]
    # A rerun on the same evidence still adds nothing.
    _service(evidence, tmp_path, clock).assess_site(SITE_ID)
    assert len(JsonAssessmentStore(tmp_path).load_history(SITE_ID).lineages[0].revisions) == 2


def test_r1_alternative_only_evidence_and_the_fuel_basis_change_the_digest() -> None:
    base = world(range(0, 151, 15), running=between(15, 120),
                 policies=[p for p in POLICIES if p.signal_id != "policy-stop-soc-threshold"])
    with_stop = base + [policy(dispatch.POLICY_STOP, "90", "%", "generator-stop-soc-threshold")]
    a, b = one(base), one(with_stop)
    assert classes(a) == classes(b), "the stop policy is context for an alternative only"
    assert a["evidence_basis"]["digest"] != b["evidence_basis"]["digest"]
    assert one(with_stop, NO_SFC)["evidence_basis"]["digest"] != b["evidence_basis"]["digest"]


def test_r1_a_model_version_change_is_a_retained_revision_not_a_rewrite(tmp_path, monkeypatch) -> None:
    evidence = Store(world(range(0, 151, 15), running=between(15, 120)))
    clock = _clock()
    monkeypatch.setattr(dispatch, "MODEL_VERSION", "dispatch-1")
    (old,) = _service(evidence, tmp_path, clock).assess_site(SITE_ID).lineages
    monkeypatch.undo()
    _service(evidence, tmp_path, clock).assess_site(SITE_ID)
    (lineage,) = JsonAssessmentStore(tmp_path).load_history(SITE_ID).lineages
    assert [(r.revision, r.model_version) for r in lineage.revisions] == [
        (1, "dispatch-1"), (2, "dispatch-2")
    ]
    assert lineage.revisions[0] == old.revisions[0]


# --- R2: commands that take effect between generator reports ----------------------------


def test_r2_an_override_wholly_between_reports_is_assessed_at_its_time() -> None:
    records = world(range(0, 151, 15), running=between(15, 120))
    records.append(override(dispatch.GEN_OVERRIDE, "95", "generator-stop-soc-threshold", 65, 70))
    a = one(records)
    parts = [c for c in classes(a) if c[0] in ("01:00", "01:05", "01:10")]
    assert parts == [("01:00", "CANDIDATE_AVOIDABLE", None),
                     ("01:05", "NECESSARY", "OPERATOR_OVERRIDE"),
                     ("01:10", "CANDIDATE_AVOIDABLE", None)]
    split = next(s for s in a["segments"] if s["start"] == at(65))
    assert split["end"] == at(70) and split["minutes"] == 5
    # No measurement is invented at the split: the parts keep the reports' inputs.
    assert split["inputs"]["at_start"]["soc_pct"] == "60" and "the two reports'" in split["reasons"][-1]
    # 01:00-02:00 was 60 candidate minutes; the 5 overridden minutes are not candidate.
    assert a["portions_hours"]["CANDIDATE_AVOIDABLE"]["low"] == "0.92"
    assert a["fuel"]["inputs"]["duration_hours"]["low"] == "0.92"
    alt = next(x for x in a["alternatives"] if x["id"] == "OPERATOR_OVERRIDE")
    assert "at its effective time" in alt["statement"]


def test_r2_a_reserve_override_between_reports_binds_its_part_only() -> None:
    records = world(range(0, 151, 15), running=between(15, 120), pv=const("10"))
    records.append(override(dispatch.BATTERY_OVERRIDE, "70", "battery-reserve-state-of-charge", 95, 100))
    a = one(records)
    parts = [c for c in classes(a) if c[0] in ("01:30", "01:35", "01:40")]
    assert parts == [("01:30", "CANDIDATE_AVOIDABLE", None),
                     ("01:35", "NECESSARY", "BATTERY_AT_RESERVE"),
                     ("01:40", "CANDIDATE_AVOIDABLE", None)]


def test_r2_an_override_in_the_stop_edge_is_not_counted_as_candidate_time() -> None:
    # Last running report 02:00, first stopped evidence 02:10 (the zero mean).
    records = world(range(0, 151, 15), running=between(15, 120))
    records.append(override(dispatch.GEN_OVERRIDE, "95", "generator-stop-soc-threshold", 122, 128))
    a = one(records)
    # Without it the high bound is 60 + 10 = 70 min; the 6 overridden minutes leave 64.
    assert a["portions_hours"]["CANDIDATE_AVOIDABLE"] == {"low": "1", "high": "1.07"}
    alt = next(x for x in a["alternatives"] if x["id"] == "OPERATOR_OVERRIDE")
    assert alt["status"] == "OBSERVED" and "start/stop uncertainty" in alt["statement"]
    assert "included in the constraint assessment" not in alt["statement"]


# --- R3: SOC headroom before battery support counts -------------------------------------


def _after_runtime(a: dict) -> set[str]:
    return {s["classification"] for s in a["segments"] if s["start"] >= at(60)}


def test_r3_pv_at_load_with_soc_at_reserve_is_not_candidate() -> None:
    a = one(world(range(0, 151, 15), running=between(15, 120), pv=const("20"), soc=const("30")))
    assert _after_runtime(a) == {"INDETERMINATE"} and a["claim_level"] == "INDETERMINATE"
    assert a["fuel"]["status"] == "NOT_APPLICABLE"
    reason = a["segments"][-1]["reasons"][0]
    assert "battery support is not counted" in reason and "more than" not in reason.split(":")[0]


def test_r3_pv_inside_headroom_needs_soc_more_than_ten_points_above_reserve() -> None:
    for pv, soc, expected in (("21", "35", "INDETERMINATE"), ("21.9", "40", "INDETERMINATE"),
                              ("20", "40", "INDETERMINATE"), ("21", "41", "CANDIDATE_AVOIDABLE")):
        a = one(world(range(0, 151, 15), running=between(15, 120), pv=const(pv), soc=const(soc)))
        assert _after_runtime(a) == {expected}, (pv, soc)


# --- R4: equal-rank contradictory policy and override records ---------------------------


def test_r4_conflicting_reserve_policies_are_not_resolved_by_order() -> None:
    reserve = POLICIES[0]
    records = world(range(0, 151, 15), running=between(15, 120), pv=const("10"),
                    policies=[*POLICIES, _other(reserve, "70")])
    a = one(records)
    assert a["claim_level"] == "INDETERMINATE"
    assert "Battery reserve policy: conflicting records" in a["missing_evidence"]
    late = a["segments"][-1]
    assert late["inputs"]["at_end"]["reserve_pct"] is None
    assert {reserve.message_id, reserve.message_id + "/other"} <= set(
        a["evidence_basis"]["message_ids"])
    r = readiness(records)
    assert r["level"] == "LIMITED"
    assert any(m["role"] == "Battery reserve policy" and m["limits_claim"]
               for m in r["missing_evidence"])


def test_r4_a_conflict_that_does_not_change_the_outcome_is_named_not_hidden() -> None:
    # PV alone (30 kW) covers 20 kW load: the reserve does not decide it.
    records = world(range(0, 151, 15), running=between(15, 120),
                    policies=[*POLICIES, _other(POLICIES[0], "70")])
    a = one(records)
    assert a["claim_level"] == "CANDIDATE_AVOIDABLE"
    assert any("conflict does not decide it" in r for r in a["segments"][-1]["reasons"])


def test_r4_identical_records_from_two_gateways_do_not_conflict() -> None:
    records = world(range(0, 151, 15), running=between(15, 120), pv=const("10"),
                    policies=[*POLICIES, _other(POLICIES[0], "30")])
    assert one(records)["claim_level"] == "CANDIDATE_AVOIDABLE"


def test_r4_conflicting_overrides_and_runtime_policies_are_named() -> None:
    gen = override(dispatch.GEN_OVERRIDE, "95", "generator-stop-soc-threshold", 60, 90)
    a = one(world(range(0, 151, 15), running=between(15, 120)) + [gen, _other(gen, "50")])
    assert "Operator override (generator): conflicting records" in a["missing_evidence"]
    assert {c[1] for c in classes(a) if c[0] in ("01:00", "01:15")} == {"INDETERMINATE"}
    runtime = POLICIES[1]
    b = one(world(range(0, 151, 15), running=between(15, 120),
                  policies=[*POLICIES, _other(runtime, "60")]))
    assert "Minimum runtime policy: conflicting records" in b["missing_evidence"]
    # 30 vs 60 min from the 00:15 start disagree at the 01:00 and 01:15 reports,
    # so the two segments touching them are Indeterminate; both agree elsewhere.
    assert classes(b)[2:6] == [("00:45", "NECESSARY", "MINIMUM_RUNTIME"),
                               ("01:00", "INDETERMINATE", None), ("01:15", "INDETERMINATE", None),
                               ("01:30", "CANDIDATE_AVOIDABLE", None)]


def test_r4_conflicting_stop_policies_are_not_quoted_as_effective() -> None:
    stop = POLICIES[2]
    a = one(world(range(0, 151, 15), running=between(15, 120),
                  policies=[*POLICIES, _other(stop, "60")]))
    alt = next(x for x in a["alternatives"] if x["id"] == "POLICY_CONSTRAINT")
    assert "Conflicting generator stop policy records" in alt["statement"]
    assert len(alt["evidence"]) == 2


# --- R5: generator-state gaps lower readiness -------------------------------------------


def test_r5_a_generator_state_gap_scores_limited_and_is_named() -> None:
    records = [r for r in world(range(0, 241, 15), running=between(15, 210))
               if not (r.device_id == "generator-controller"
                       and at(90) < r.source_time < at(150))]
    r = readiness(records)
    assert r["basis_version"] == "readiness-3"
    assert r["level"] == "LIMITED"
    (gap,) = [m for m in r["missing_evidence"] if m["role"] == "Generator state"]
    assert gap["kind"] == "COVERAGE_GAP" and gap["limits_claim"] is True
    assert gap["statement"].startswith("Generator state: not observed for 60 min in 1 assessed interval")
    assert r["claim_ceiling"]["claim_level"] == dispatch.CANDIDATE
