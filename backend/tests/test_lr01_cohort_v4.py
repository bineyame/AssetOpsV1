"""LR-01 phase 1: cohort-4 source-time ordering under clock attestations (pure).

Authority: D-2026-10-15-lr01-source-time-cohort, `.agent/architect-LR-01-answers.md` Q1-Q4 and Follow-up M1.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import timedelta
from uuid import UUID, uuid4

import pytest
from test_s3_dispatch_v3_analytic import (
    ROLES_BY_SET,
    SRC,
    T0,
    WINDOW,
    Feed,
    at,
    bindings,
    controls,
    run_interval,
)

from assetops_backend.analytics import dispatch_v3 as d3
from assetops_backend.analytics.assessment_inputs import CohortMember, EvidenceQuery, EvidenceQueryResult, \
    build_input_set
from assetops_backend.analytics.clock_attestation import (
    SYSTEM_ATTESTER,
    AttestationChange,
    AttestationRefused,
    AttesterPrincipal,
    ClockAttestation,
    effective_as_of,
    next_event,
    validate_change,
)
from assetops_backend.analytics.cohort import select_cohort
from assetops_backend.sites.binding_roles import ROLE_SET_MINIGRID_2

GW = UUID(int=1)


def att(lo, hi, *, src="gen", epoch="e1", error=timedelta(seconds=60), aid=None, version=1, kind="RECORDED",
        recorded=None, proof="SIMULATED") -> ClockAttestation:
    return ClockAttestation(uuid4(), aid or uuid4(), version, kind, SRC[src], epoch, proof, "lab-simulated-clock",
                            "SIMULATED clock attestation (labelled demonstration)", error, lo, hi,
                            recorded or T0 - timedelta(days=1))


def assess(feed: Feed, attestations=(), cohort=None):
    query = EvidenceQuery(UUID(int=7), UUID(int=8), "dispatch", WINDOW, at(23), cohort=cohort)
    result = EvidenceQueryResult(query, tuple(feed.readings), bindings(), controls(), (ROLE_SET_MINIGRID_2,),
                                 attestations=tuple(attestations))
    selection = select_cohort(result.readings, WINDOW, cohort, result.attestations)
    inputs = build_input_set(result, selection, analytic_id=d3.ANALYTIC_ID, model_version=d3.MODEL_VERSION,
                             roles_by_set=ROLES_BY_SET)
    return inputs, d3.assess(inputs)


def power_case(*, late_in_sequence: bool) -> tuple[Feed, object]:
    """The S4-02c shape: 05:00-08:00 generator run with back-to-back 5-minute power means; the 07:00-07:05 mean
    arrives late. Admission-sequenced (run 1): it gets the next sequence on intake. On-time-sequenced: it was
    numbered when taken, so its sequence sits in source order."""
    feed = run_interval(Feed(), 5, 8)
    seq = 1000
    late = None
    t = at(5, 5)
    while t <= at(8):
        seq += 1
        if t == at(7, 5):
            late_seq = seq
        else:
            feed.add("gen", "generator_power", "gen", t, "20", seq=seq)
        t += timedelta(minutes=5)
    late = feed.add("gen", "generator_power", "gen", at(7, 5), "20", seq=late_seq if late_in_sequence else 5000)
    return feed, late


def kinds(inputs, role="generator_power"):
    return [(x.kind, x.clock) for x in inputs.cohort.limits if x.role == role]


class TestRunOneAndOnTimeVariant:
    def test_admission_sequenced_late_mean_without_attestation_is_inverted_and_series_ambiguous(self):
        feed, late = power_case(late_in_sequence=False)
        inputs, window = assess(feed)
        [limit] = [x for x in inputs.cohort.limits if x.role == "generator_power"]
        assert (limit.kind, limit.clock, limit.attestation_refs) == ("SEQUENCE_ORDER_INVERTED", "NO_ATTESTATION", ())
        assert str(late.evidence_id) in limit.evidence_ids
        assert window.claim_level == d3.WINDOW_INDETERMINATE
        assert any(x.startswith("GENERATOR_SERIES_AMBIGUOUS") for x in window.result["limitations"])
        assert any("clock NO_ATTESTATION" in x for x in window.result["limitations"])

    def test_valid_attestation_orders_the_late_arrival_by_source_time(self):
        feed, late = power_case(late_in_sequence=False)
        proof = att(at(0), at(23))
        unattested, _ = assess(feed)
        inputs, window = assess(feed, [proof])
        assert kinds(inputs) == []  # late admission sequence is not an inversion under proof
        assert not any(x.startswith(("GENERATOR_SERIES_AMBIGUOUS", "SEQUENCE_ORDER_INVERTED"))
                       for x in window.result["limitations"])
        assert window.claim_level != d3.WINDOW_INDETERMINATE
        basis = inputs.cohort.payload()["clock_basis"]
        assert [(b["attestation_id"], b["version"], b["event_id"]) for b in basis] == [
            (str(proof.attestation_id), 1, str(proof.event_id))]
        assert inputs.input_sha256 != unattested.input_sha256  # the attestation is pinned in the digest

    def test_on_time_sequenced_late_upload_is_one_series_with_or_without_proof(self):
        feed, _ = power_case(late_in_sequence=True)
        for proofs in ((), (att(at(0), at(23)),)):
            inputs, window = assess(feed, proofs)
            assert kinds(inputs) == []
            assert not any(x.startswith("GENERATOR_SERIES_AMBIGUOUS") for x in window.result["limitations"])

    def test_dense_in_order_attested_five_minute_means_stay_usable(self):
        feed, _ = power_case(late_in_sequence=True)
        inputs, window = assess(feed, [att(at(0), at(23), error=timedelta(seconds=60))])
        assert inputs.cohort.limits == ()  # back-to-back means only touch; placements are 300 s apart
        assert not any(k in x for x in window.result["limitations"]
                       for k in ("REPORTS_OVERLAP", "SEQUENCE_ORDER_INVERTED", "GENERATOR_SERIES_AMBIGUOUS"))


class TestFailClosedClockProof:
    def _late(self, proofs):
        feed, late = power_case(late_in_sequence=False)
        inputs, _ = assess(feed, proofs)
        return [x for x in inputs.cohort.limits if x.role == "generator_power"], late

    def test_proof_whose_validity_ends_before_the_late_mean_keeps_the_inversion(self):
        [limit], _ = self._late([att(at(0), at(7))])
        assert (limit.kind, limit.clock) == ("SEQUENCE_ORDER_INVERTED", "OUTSIDE_VALIDITY")

    def test_conflicting_attestations_keep_the_inversion_and_name_both(self):
        a, b = att(at(0), at(23)), att(at(6), at(9))
        limits, _ = self._late([a, b])
        assert limits and all(x.kind == "SEQUENCE_ORDER_INVERTED" for x in limits)
        assert {x.clock for x in limits} <= {"CONFLICTING_ATTESTATIONS", "CONFLICTING_ATTESTATIONS+OUTSIDE_VALIDITY",
                                             "CONFLICTING_ATTESTATIONS+SPANS_ATTESTATIONS"}
        assert {a.ref, b.ref} <= {r for x in limits for r in x.attestation_refs}

    def test_an_unproved_clock_step_between_attestations_keeps_the_inversion(self):
        # Two proofs meeting at 07:30: the late 07:00-07:05 mean (under A) was admitted after readings under B.
        a, b = att(at(0), at(7, 30)), att(at(7, 30), at(23))
        [limit], _ = self._late([a, b])
        assert (limit.kind, limit.clock) == ("SEQUENCE_ORDER_INVERTED", "CLOCK_STEP_UNPROVED")
        assert set(limit.attestation_refs) == {a.ref, b.ref}

    def test_a_mean_straddling_two_attestations_is_not_ordered(self):
        a, b = att(at(0), at(7, 2)), att(at(7, 2), at(23))
        limits, _ = self._late([a, b])
        assert limits and all(x.kind == "SEQUENCE_ORDER_INVERTED" for x in limits)
        assert any("SPANS_ATTESTATIONS" in x.clock for x in limits)

    def test_simulated_proof_cannot_order_a_live_source(self):
        feed, _ = power_case(late_in_sequence=False)
        feed.readings = [replace(r, source_mode="LIVE") for r in feed.readings]
        inputs, _ = assess(feed, [att(at(0), at(23))])
        [limit] = [x for x in inputs.cohort.limits if x.role == "generator_power"]
        assert limit.clock == "SIMULATED_PROOF_FOR_LIVE_SOURCE"

    def test_proof_above_the_sixty_second_ceiling_is_never_used(self):
        [limit], _ = self._late([att(at(0), at(23), error=timedelta(seconds=61))])
        assert limit.clock == "ERROR_ABOVE_CEILING"

    def test_proof_for_another_epoch_or_source_proves_nothing(self):
        [limit], _ = self._late([att(at(0), at(23), epoch="e2"), att(at(0), at(23), src="bat")])
        assert limit.clock == "NO_ATTESTATION"


class TestOverlapUnderProof:
    def test_genuinely_overlapping_means_stay_overlap_even_in_sequence_order(self):
        feed = run_interval(Feed(), 5, 6)
        a = feed.add("gen", "generator_power", "gen", at(5, 5), "20")
        b = feed.add("gen", "generator_power", "gen", at(5, 8), "20")  # 05:03-05:08 overlaps 05:00-05:05
        inputs, window = assess(feed, [att(at(0), at(23), error=timedelta(seconds=0))])
        [limit] = [x for x in inputs.cohort.limits if x.role == "generator_power"]
        assert (limit.kind, limit.clock) == ("REPORTS_OVERLAP", "ATTESTED")
        assert set(limit.evidence_ids) == {str(a.evidence_id), str(b.evidence_id)}
        assert (limit.start, limit.end) == (at(5, 3), at(5, 5))
        assert window.claim_level == d3.WINDOW_INDETERMINATE

    def test_overlapping_placement_uncertainty_stays_overlap_and_disjoint_does_not(self):
        feed = Feed()
        feed.add("gen", "generator_state", "gen", at(5), "RUNNING", mean=False)
        feed.add("gen", "generator_state", "gen", at(5, 2), "RUNNING", mean=False)  # 120 s <= 2 x 60 s
        feed.add("gen", "generator_state", "gen", at(5, 4) + timedelta(seconds=1), "RUNNING", mean=False)  # 121 s
        inputs, _ = assess(feed, [att(at(0), at(23))])
        spans = [(x.kind, x.start, x.end) for x in inputs.cohort.limits]
        assert spans == [("REPORTS_OVERLAP", at(5), at(5, 2))]

    def test_overlapping_placements_with_disagreeing_sequence_are_not_ordered(self):
        feed = Feed()
        feed.add("gen", "generator_state", "gen", at(5, 1), "RUNNING", mean=False, seq=1)
        feed.add("gen", "generator_state", "gen", at(5), "STOPPED", mean=False, seq=2)
        inputs, _ = assess(feed, [att(at(0), at(23))])
        assert [x.kind for x in inputs.cohort.limits] == ["REPORTS_OVERLAP"]


class TestEpochs:
    def test_default_cohort_never_merges_epochs_by_source_time_even_under_proof(self):
        feed = run_interval(Feed(), 3, 4, )
        run_interval(feed, 9, 10, epoch="e2")
        proofs = [att(at(0), at(23), src=s, epoch=e) for s in SRC for e in ("e1", "e2")]
        inputs, window = assess(feed, proofs)
        assert inputs.cohort.status == "AMBIGUOUS" and window.claim_level == d3.WINDOW_INDETERMINATE

    def test_explicit_cross_epoch_selection_orders_each_epoch_under_its_own_proof(self):
        feed = run_interval(Feed(), 3, 4)
        run_interval(feed, 9, 10, epoch="e2")
        feed.add("gen", "generator_state", "gen", at(9, 20), "RUNNING", mean=False, epoch="e2")  # late, e2
        members = tuple(sorted({r.member for r in feed.readings}))
        only_e1 = [att(at(0), at(23), src=s, epoch="e1") for s in SRC]
        inputs, _ = assess(feed, only_e1, cohort=members)
        assert inputs.cohort.status == "SELECTED_EXPLICIT"
        [limit] = inputs.cohort.limits
        assert (limit.kind, limit.member.sequence_epoch, limit.clock) == (
            "SEQUENCE_ORDER_INVERTED", "e2", "NO_ATTESTATION")
        both = only_e1 + [att(at(0), at(23), src="gen", epoch="e2")]
        inputs, _ = assess(feed, both, cohort=members)
        assert inputs.cohort.limits == ()
        assert {CohortMember(GW, SRC["gen"], "e2")} <= set(inputs.cohort.members)


class TestAttestationEvents:
    def test_effective_proof_is_read_as_of_the_cutoff_and_revocation_removes_it(self):
        aid = uuid4()
        v1 = att(at(0), at(23), aid=aid, recorded=at(1))
        v2 = replace(att(at(0), at(12), aid=aid, version=2, kind="EXPIRED", recorded=at(2)))
        v3 = replace(att(at(0), at(12), aid=aid, version=3, kind="REVOKED", recorded=at(3)))
        assert effective_as_of([v1, v2, v3], at(0)) == ()
        assert effective_as_of([v1, v2, v3], at(1, 30)) == (v1,)
        assert effective_as_of([v3, v1, v2], at(2, 30)) == (v2,)
        assert effective_as_of([v1, v2, v3], at(4)) == ()

    def test_revoked_proof_restores_the_inversion(self):
        feed, _ = power_case(late_in_sequence=False)
        aid = uuid4()
        events = [att(at(0), at(23), aid=aid, recorded=at(1)), att(at(0), at(23), aid=aid, version=2,
                                                                     kind="REVOKED", recorded=at(2))]
        inputs, _ = assess(feed, effective_as_of(events, at(3)))
        assert [x.kind for x in inputs.cohort.limits if x.role == "generator_power"] == ["SEQUENCE_ORDER_INVERTED"]

    def _change(self, **over):
        base = dict(event_kind="RECORDED", source_id=SRC["gen"], sequence_epoch="e1", idempotency_key="k1",
                    channel="SYSTEM_CLI", authority="lab-simulated-clock", label="SIMULATED demo clock",
                    max_utc_error=timedelta(seconds=30), valid_from=at(0), valid_to=at(23))
        return AttestationChange(**{**base, **over})

    @pytest.mark.parametrize("over, principal, code", [
        ({}, AttesterPrincipal("gateway:abc", "bearer credential", "GATEWAY"), "SYSTEM_ATTESTER_REQUIRED"),
        ({}, AttesterPrincipal("user:owner", "client", "SYSTEM"), "SYSTEM_ATTESTER_REQUIRED"),
        ({}, object(), "SYSTEM_ATTESTER_REQUIRED"),
        ({"channel": "HTTP"}, SYSTEM_ATTESTER, "CHANNEL_NOT_SYSTEM"),
        ({"proof_class": "REAL"}, SYSTEM_ATTESTER, "REAL_SOURCE_PROOF_UNAVAILABLE"),
        ({"max_utc_error": timedelta(seconds=61)}, SYSTEM_ATTESTER, "ERROR_ABOVE_CEILING"),
        ({"label": " "}, SYSTEM_ATTESTER, "SIMULATED_LABEL_REQUIRED"),
        ({"authority": ""}, SYSTEM_ATTESTER, "AUTHORITY_REQUIRED"),
        ({"valid_to": at(0)}, SYSTEM_ATTESTER, "VALIDITY_EMPTY"),
        ({"event_kind": "REVOKED", "attestation_id": UUID(int=5), "expected_version": 1}, SYSTEM_ATTESTER,
         "REASON_REQUIRED"),
    ], ids=["gateway", "client-system-lookalike", "no-principal", "channel", "real-proof", "ceiling", "label",
            "authority", "validity", "revoke-reason"])
    def test_validation_refuses_anything_but_the_system_attester_and_a_bounded_simulated_proof(self, over,
                                                                                                principal, code):
        with pytest.raises(AttestationRefused) as refused:
            validate_change(self._change(**over), principal)
        assert refused.value.code == code

    def test_events_version_forward_and_refuse_a_stale_expected_version(self):
        first = next_event(self._change(), None, event_id=uuid4(), attestation_id=uuid4(), recorded_at=at(1))
        assert (first.version, first.event_kind) == (1, "RECORDED")
        expired = next_event(self._change(event_kind="EXPIRED", attestation_id=first.attestation_id,
                                          expected_version=1, valid_to=at(12)), first, event_id=uuid4(),
                             attestation_id=first.attestation_id, recorded_at=at(2))
        assert (expired.version, expired.valid_to, expired.valid_from) == (2, at(12), at(0))
        with pytest.raises(AttestationRefused) as stale:
            next_event(self._change(event_kind="REVOKED", attestation_id=first.attestation_id, expected_version=1,
                                    reason="x"), expired, event_id=uuid4(), attestation_id=first.attestation_id,
                       recorded_at=at(3))
        assert stale.value.code == "VERSION_CONFLICT"
